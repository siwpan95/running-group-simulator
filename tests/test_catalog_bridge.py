# -*- coding: utf-8 -*-
"""
目录→实体桥接测试（v3.6 内容目录消费方）：
验证 catalog_bridge.build_enemy_from_catalog 能把目录条目落地为可战斗 Enemy，
并覆盖 D&D / CoC 两套 schema 的字段映射与 round-trip。

零第三方依赖（不依赖 alloy；core.enemy 与 services.catalog_service 均为纯逻辑）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_PASS = 0
_FAIL = 0


def check(name, ok, detail=""):
    global _PASS, _FAIL
    if ok:
        _PASS += 1
        print("  [PASS] %s" % name)
    else:
        _FAIL += 1
        print("  [FAIL] %s %s" % (name, detail))


def test_bridge_basics():
    from core.enemy import Enemy
    from services.catalog_bridge import build_enemy_from_catalog

    # --- D&D 怪物：Goblin（原生数值：attack_skill=命中加值, ac=护甲等级）---
    goblin = build_enemy_from_catalog("Goblin")
    check("D&D Goblin 命中目录", goblin is not None, "返回 None")
    if goblin:
        check("  Goblin 是 Enemy 实例", isinstance(goblin, Enemy))
        check("  Goblin ac=15", goblin.ac == 15, "ac=%s" % goblin.ac)
        check("  Goblin attack_skill=+4 命中加值", goblin.attack_skill == 4, "as=%s" % goblin.attack_skill)
        check("  Goblin damage 含 1d6", "1d6" in goblin.damage, goblin.damage)
        check("  Goblin damage 含 slashing", "slashing" in goblin.damage, goblin.damage)
        check("  Goblin hp>0", goblin.hp > 0, "hp=%s" % goblin.hp)
        # round-trip
        goblin2 = Enemy.from_dict(goblin.to_dict())
        check("  Goblin round-trip 一致", goblin2.name == goblin.name and goblin2.ac == goblin.ac)

    # 限定系统查找
    check("D&D Goblin(system=dnd5e) 命中", build_enemy_from_catalog("Goblin", "dnd5e") is not None)
    check("D&D Goblin(system=coc7) 落空", build_enemy_from_catalog("Goblin", "coc7") is None)

    # --- CoC 生物：深潜者（原生数值：attack_skill=百分比, dodge=DEX×2, dr=护甲值）---
    deep = build_enemy_from_catalog("深潜者")
    check("CoC 深潜者 命中目录", deep is not None, "返回 None")
    if deep:
        # 从目录取真实 DEX 以校验 dodge=DEX×2（不写死数值，避免与目录漂移）
        from services.catalog_service import CatalogService
        raw = CatalogService().find_creature("深潜者", "coc7") or {}
        raw_dex = (raw.get("stats") or {}).get("dex") or (raw.get("stats") or {}).get("DEX") or 0
        check("  深潜者 是 Enemy 实例", isinstance(deep, Enemy))
        check("  深潜者 enemy_type=wildcard", deep.enemy_type == "wildcard", deep.enemy_type)
        check("  深潜者 dodge=DEX×2", deep.dodge == max(1, raw_dex * 2), "dodge=%s raw_dex=%s" % (deep.dodge, raw_dex))
        check("  深潜者 attack_skill=25 (武器%)", deep.attack_skill == 25, "as=%s" % deep.attack_skill)
        check("  深潜者 dr=1 (鳞甲)", deep.dr == 1, "dr=%s" % deep.dr)
        check("  深潜者 hp=13", deep.hp == 13, "hp=%s" % deep.hp)
        check("  深潜者 damage 含 1d6", "1d6" in deep.damage, deep.damage)
        deep2 = Enemy.from_dict(deep.to_dict())
        check("  深潜者 round-trip 一致", deep2.name == deep.name and deep2.dodge == deep.dodge)

    # 英文名查找
    check("CoC 深潜者(英文名 Deep One)", build_enemy_from_catalog("Deep One") is not None)

    # --- 落空 ---
    check("未知名称返回 None", build_enemy_from_catalog("不存在的怪物XYZ") is None)


def main():
    print("== catalog_bridge 测试 ==")
    test_bridge_basics()
    print("\n结果: %d passed, %d failed" % (_PASS, _FAIL))
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
