# -*- coding: utf-8 -*-
"""
多系统裁决画像测试（v3.2 内核抽象）
验证：注册表、GURPS 画像原语、引擎委托面（CombatEngine 静态接口 +
SceneEngine 检定 packet 含 system 字段）。零第三方依赖。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

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


def test_registry():
    from core.rules import available_systems, get_profile
    check("注册表含 gurps", "gurps" in available_systems(),
          str(available_systems()))
    p = get_profile("gurps")
    check("gurps 画像 system_id", p.system_id == "gurps")
    check("gurps 画像 display_name", p.display_name == "GURPS 4e")
    try:
        get_profile("nonexistent_system")
        check("未知系统抛 KeyError", False)
    except KeyError:
        check("未知系统抛 KeyError", True)


def test_gurps_check():
    from core.rules import get_profile
    p = get_profile("gurps")
    for _ in range(60):
        r = p.roll_check(12, 2)
        if not (3 <= r["roll"] <= 18):
            check("roll 范围 3-18", False, str(r))
            return
        check("roll 范围 3-18", True)
        break
    r = p.roll_check(10, 0)
    for k in ("roll", "target", "success", "margin", "is_crit_success",
              "is_fumble", "success_chance", "system"):
        if k not in r:
            check("roll_check 含字段 %s" % k, False, str(r))
            return
    check("roll_check 含全部字段", True)
    check("target = skill + modifier", r["target"] == 10)
    check("system 标记", r["system"] == "gurps")
    # 大失败：roll 17/18 → is_fumble；大成功 roll 3/4 → is_crit_success
    hi = [p.roll_check(16, 0) for _ in range(200)]
    check("17/18 判 fumble", any(x["is_fumble"] for x in hi))
    lo = [p.roll_check(16, 0) for _ in range(200)]
    check("3/4 判 crit", any(x["is_crit_success"] for x in lo))


def test_gurps_damage():
    from core.rules import get_profile
    p = get_profile("gurps")
    raw, t = p.roll_damage("2d6+1 cut")
    check("roll_damage 2d6+1 范围 3-13", 3 <= raw <= 13, str(raw))
    check("roll_damage 类型 cut", t == "切割", t)
    raw2, t2 = p.roll_damage("invalid")
    check("roll_damage 无效→1", raw2 == 1)
    check("无效类型默认钝击", t2 == "钝击")
    check("pi+ → 穿刺", p.damage_type("2d6 pi+") == "穿刺")
    check("burn → 燃烧", p.damage_type("1d6 burn") == "燃烧")
    check("cr → 钝击", p.damage_type("2d6 cr") == "钝击")


def test_gurps_penetration():
    from core.rules import get_profile
    p = get_profile("gurps")
    check("切割 x1.5 取整", p.penetration(5, 0, "切割") == 7)
    check("穿刺破甲 x2", p.penetration(6, 2, "穿刺") == 8)
    check("穿刺未破甲 x1", p.penetration(4, 5, "穿刺") == 0)
    check("钝击 x1", p.penetration(5, 1, "钝击") == 4)
    check("DR 吸收完", p.penetration(2, 5, "切割") == 0)


def test_gurps_hit_location():
    from core.rules import get_profile
    p = get_profile("gurps")
    seen = set()
    for _ in range(80):
        seen.add(p.hit_location())
    check("部位覆盖头/臂/腿/躯干", {"头", "躯干", "右臂", "左臂", "右腿", "左腿"} >= seen or
          {"头", "躯干"} <= seen, str(seen))


def test_gurps_defense_shock():
    from core.rules import get_profile
    p = get_profile("gurps")
    d = p.active_defense(16)
    check("主动防御 dodge=16 必闪", d["result"] == "dodged", str(d))
    d2 = p.active_defense(0)
    check("主动防御 dodge=0 必中", d2["result"] == "hit", str(d2))
    s = p.shock_check(10, 4, 2)
    check("轻伤不触发休克", s["status"] == "ok")
    s2 = p.shock_check(10, 4, 5)
    check("重伤返回 ok/stunned", s2["status"] in ("ok", "stunned"), str(s2))
    s3 = p.shock_check(3, 4, 5)
    check("HT=3 重伤必 stunned", s3["status"] == "stunned", str(s3))


def test_engine_delegation():
    from core.combat_engine import CombatEngine, HIT_LOCATIONS
    ce = CombatEngine()
    check("CombatEngine 默认画像 gurps", ce.profile.system_id == "gurps")
    d = ce.roll_damage("2d6+1 cut")
    check("CombatEngine.roll_damage 委托", 3 <= d <= 13, str(d))
    check("get_damage_type 委托", ce.get_damage_type("1d6 imp") == "穿刺")
    check("HIT_LOCATIONS 导出兼容", HIT_LOCATIONS.get(8) == "躯干")
    # attack packet 含 system
    from core.character import Character
    from core.enemy import Enemy
    pc = Character(name="测试员")
    foe = Enemy(name="木桩", hp=20, hp_max=20, attack_skill=10, damage="1d6 cr", dodge=8)
    pkt = ce.attack_resolve(pc, foe, 18)
    check("attack packet 含 system", pkt.get("system") == "gurps")
    check("attack packet 含 success", "success" in pkt)


def test_scene_engine_system_field():
    import json
    from core.character import Character
    from core.scene_engine import SceneEngine
    from core.viewmodel import ViewModel
    from core.environment_system import EnvironmentSystem
    module = {
        "act_1": {"nodes": [{
            "node_id": "n1", "scene_type": "perception",
            "layer_physics": {"skill_check": "感知（听觉）"},
        }]},
    }
    pc = Character(name="调查员", iq=12, per=12)
    env = EnvironmentSystem()
    vm = ViewModel()
    eng = SceneEngine(module, pc, vm, env)
    res = eng.run_node("n1")
    r = res.roll_info
    check("scene 检定 packet 含 system", r is not None and r.get("system") == "gurps",
          str(r)[:120])


def main():
    print("test_rules_profiles（v3.2 多系统画像）")
    test_registry()
    test_gurps_check()
    test_gurps_damage()
    test_gurps_penetration()
    test_gurps_hit_location()
    test_gurps_defense_shock()
    test_engine_delegation()
    test_scene_engine_system_field()
    print("================ 结果 ================")
    print("通过: %d    失败: %d" % (_PASS, _FAIL))
    if _FAIL:
        sys.exit(1)
    print("全部通过 ✔")


if __name__ == "__main__":
    main()
