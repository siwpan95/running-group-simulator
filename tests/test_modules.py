# -*- coding: utf-8 -*-
"""
模组完整性测试（v3.7 新增模组工程化门禁）。

对 modules/*/module.json 逐个校验：
  1. JSON 可解析、meta 必备字段齐全（module_id / systems / base_xp …）；
  2. 三幕结构完整（act_1/2/3），节点 id 全局唯一；
  3. 节点图自洽：prerequisite_nodes / next_nodes 指向真实存在的节点；
  4. 战斗节点的 catalog_ref 能在对应系统目录里查到（不许手写没被消费的敌人）；
  5. 每个模块都能被场景引擎加载，且战斗节点能经 catalog_ref 生成敌人；
  6. layer_physics 的检定字段合法（单次检定 / 嵌套检定 / 战斗三类之一）。

零第三方依赖（不依赖 alloy）。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

MODULES_DIR = os.path.join(ROOT, "modules")

_PASS = 0
_FAIL = 0
_FAILURES = []


def check(name, ok, detail=""):
    global _PASS, _FAIL
    if ok:
        _PASS += 1
        print("  [PASS] %s" % name)
    else:
        _FAIL += 1
        _FAILURES.append(name)
        print("  [FAIL] %s %s" % (name, detail))


def module_files():
    if not os.path.isdir(MODULES_DIR):
        return []
    out = []
    for name in sorted(os.listdir(MODULES_DIR)):
        p = os.path.join(MODULES_DIR, name, "module.json")
        if os.path.isfile(p):
            out.append((name, p))
    return out


def nodes_of(mod):
    """产出 (act_key, node) 列表。"""
    for ak in ("act_1", "act_2", "act_3"):
        for n in mod.get(ak, {}).get("nodes", []) or []:
            yield ak, n


def test_modules():
    from services.catalog_service import CatalogService
    svc = CatalogService()
    files = module_files()
    check("存在模组文件", len(files) >= 9, "找到 %d 个" % len(files))

    for mod_name, path in files:
        print("--- %s ---" % mod_name)
        try:
            mod = json.load(open(path, encoding="utf-8"))
        except Exception as ex:
            check("%s JSON 可解析" % mod_name, False, str(ex))
            continue
        check("%s JSON 可解析" % mod_name, True)

        meta = mod.get("meta") or {}
        miss = [f for f in ("module_id", "module_title", "systems", "compatible_core",
                            "base_xp", "synopsis") if not meta.get(f)]
        check("%s meta 字段齐全" % mod_name, not miss, str(miss))
        check("%s module_id 与目录名一致" % mod_name,
              meta.get("module_id") == mod_name, "%s != %s" % (meta.get("module_id"), mod_name))
        systems = meta.get("systems") or []
        check("%s systems 均为已注册系统" % mod_name,
              all(s in svc.available() for s in systems),
              "%s / 可用=%s" % (systems, svc.available()))

        # 三幕 + 节点唯一性
        acts_ok = all(mod.get(ak) for ak in ("act_1", "act_2", "act_3"))
        check("%s 三幕结构完整" % mod_name, acts_ok)
        all_nodes = list(nodes_of(mod))
        ids = [n.get("node_id") for _, n in all_nodes]
        check("%s 节点 id 唯一" % mod_name, len(ids) == len(set(ids)),
              str([i for i in ids if ids.count(i) > 1]))
        check("%s 节点 id 非空" % mod_name, all(ids) and all(ids))

        # 节点图自洽
        bad_refs = []
        for _, n in all_nodes:
            for key in ("prerequisite_nodes", "next_nodes"):
                for ref in n.get(key, []) or []:
                    if ref not in ids:
                        bad_refs.append("%s.%s->%s" % (n.get("node_id"), key, ref))
        check("%s 节点引用自洽" % mod_name, not bad_refs, str(bad_refs))

        # 战斗节点 → catalog_ref 可解析
        from services.catalog_bridge import build_enemy_from_catalog
        combat_nodes = [(ak, n) for ak, n in all_nodes
                        if n.get("scene_type") == "combat"]
        check("%s 至少一个战斗节点" % mod_name, bool(combat_nodes))
        for ak, n in combat_nodes:
            lp = n.get("layer_physics", {})
            ref = lp.get("catalog_ref")
            check("%s/%s 战斗节点有 catalog_ref" % (mod_name, n.get("node_id")), bool(ref),
                  "仍靠内联 unit_stats")
            if ref:
                ref = ref if isinstance(ref, dict) else {"name": ref}
                entry = svc.find_creature(ref.get("name"), ref.get("system"))
                check("%s/%s catalog_ref 命中目录" % (mod_name, n.get("node_id")),
                      entry is not None, str(ref))
                enemy = build_enemy_from_catalog(ref.get("name"), ref.get("system"))
                check("%s/%s 目录条目可转成 Enemy" % (mod_name, n.get("node_id")),
                      enemy is not None and enemy.hp > 0,
                      str(ref))

        # layer_physics 合法形态
        shape_bad = []
        for _, n in all_nodes:
            lp = n.get("layer_physics") or {}
            has_single = "skill_check" in lp
            has_nested = bool(lp.get("checks"))
            is_combat = n.get("scene_type") == "combat"
            if is_combat:
                if not (lp.get("catalog_ref") or lp.get("unit_stats")):
                    shape_bad.append("%s 战斗节点缺敌人来源" % n.get("node_id"))
            elif not (has_single or has_nested):
                shape_bad.append("%s 非战斗节点缺检定" % n.get("node_id"))
            if has_single and has_nested:
                shape_bad.append("%s 同时用了两种检定" % n.get("node_id"))
        check("%s layer_physics 形态合法" % mod_name, not shape_bad, str(shape_bad))


def test_scene_engine_loads_modules():
    """场景引擎能加载每个模组，并跑通其第一个战斗节点。"""
    from core.character import Character
    from core.environment_system import EnvironmentSystem
    from core.scene_engine import SceneEngine
    from core.viewmodel import ViewModel

    for mod_name, path in module_files():
        mod = json.load(open(path, encoding="utf-8"))
        system_id = (mod.get("meta", {}).get("systems") or ["gurps"])[0]
        pc = Character(character_id="t", name="PC", st=10, dx=10, iq=12, ht=10,
                       hp=10, hp_max=10, fp=10, fp_max=10)
        try:
            eng = SceneEngine(mod, pc, ViewModel(), EnvironmentSystem(), system_id)
        except Exception as ex:
            check("%s 场景引擎可加载" % mod_name, False, str(ex))
            continue
        check("%s 场景引擎可加载" % mod_name, True)
        combat = [n for _, n in nodes_of(mod) if n.get("scene_type") == "combat"]
        if combat:
            try:
                vmr = eng._handle_combat_node(combat[0])
                enemy = vmr.choices[0]["enemy"]
                ok = bool(enemy.get("name")) and enemy.get("hp_max", 0) > 0
            except Exception as ex:
                ok, enemy = False, str(ex)
            check("%s 首个战斗节点可生成敌人" % mod_name, ok, str(enemy))


def main():
    print("== 模组完整性测试 ==")
    test_modules()
    test_scene_engine_loads_modules()
    print("\n结果: %d passed, %d failed" % (_PASS, _FAIL))
    if _FAILURES:
        print("失败项: %s" % "; ".join(_FAILURES))
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
