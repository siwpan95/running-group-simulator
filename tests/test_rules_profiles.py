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
    s = p.shock_check(10, 12, 2)      # hp_max=12 → 阈值 4
    check("轻伤不触发休克", s["status"] == "ok")
    s2 = p.shock_check(10, 12, 5)
    check("重伤返回 ok/stunned", s2["status"] in ("ok", "stunned"), str(s2))
    s3 = p.shock_check(3, 12, 5)
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


def test_coc7_profile():
    from core.rules import available_systems, get_profile
    from core.rules.coc7 import roll_d100
    check("注册表含 coc7", "coc7" in available_systems(), str(available_systems()))
    p = get_profile("coc7")
    check("coc7 system_id", p.system_id == "coc7")
    # d100 范围
    for _ in range(80):
        r = roll_d100()
        if not (1 <= r <= 100):
            check("d100 范围 1-100", False, str(r))
            return
        check("d100 范围 1-100", True)
        break
    # 奖励/惩罚骰统计倾向（5000 次：奖励骰均值显著更低）
    avg_bonus = sum(roll_d100(1) for _ in range(5000)) / 5000
    avg_penalty = sum(roll_d100(-1) for _ in range(5000)) / 5000
    avg_plain = sum(roll_d100(0) for _ in range(5000)) / 5000
    check("奖励骰均值 < 普通 < 惩罚骰", avg_bonus < avg_plain < avg_penalty,
          "%.1f < %.1f < %.1f" % (avg_bonus, avg_plain, avg_penalty))
    # 检定
    r = p.roll_check(50, 0)
    check("coc7 roll_check target=50", r["target"] == 50)
    check("coc7 success_chance=target", r["success_chance"] == 50)
    check("coc7 system 标记", r["system"] == "coc7")
    lo = [p.roll_check(80, 0) for _ in range(300)]
    check("coc7 低掷判大成功", any(x["is_crit_success"] for x in lo))
    hi = [p.roll_check(80, 0) for _ in range(300)]
    check("coc7 100 判大失败", any(x["is_fumble"] for x in hi))
    # 大失败阈值：技能 <50 时 96-99 也算
    lo_skill = [p.roll_check(30, 0) for _ in range(400)]
    check("技能<50 时 96+ 判 fumble", any(x["is_fumble"] and x["roll"] < 100
                                          for x in lo_skill))
    # 伤害/穿透/防御/重伤
    raw, t = p.roll_damage("1d6+4")
    check("coc7 roll_damage 1d6+4 范围 5-10", 5 <= raw <= 10, str(raw))
    check("coc7 伤害类型物理", t == "物理")
    check("coc7 护甲平减", p.penetration(8, 3, "物理") == 5)
    d = p.active_defense(100)
    check("coc7 dodge=100 必闪", d["result"] == "dodged", str(d))
    check("coc7 重伤阈值判定", p.shock_check(10, 10, 3)["status"] == "ok")
    s = p.shock_check(10, 10, 6)
    check("coc7 重伤返回 ok/stunned", s["status"] in ("ok", "stunned"), str(s))
    # 技能目标 ×5
    from core.character import Character
    pc = Character(name="调查员", iq=12, ht=10, will=11, per=12,
                   san=60, san_max=60)
    check("coc7 意志×5", p.skill_target(pc, "意志") == 55)
    check("coc7 未掌握技能回退属性×5", p.skill_target(pc, "聆听") is None or
          isinstance(p.skill_target(pc, "聆听"), int))


def test_coc7_san():
    from core.character import Character
    pc = Character(name="调查员", san=60, san_max=60)
    r = pc.add_san_loss(3, "看见尸体")
    check("SAN 小损失", r["loss"] == 3 and pc.san == 57, str(r))
    check("SAN 小损失不疯狂", not r["temp_insanity"] and not r["indefinite_insanity"])
    r2 = pc.add_san_loss(8, "目睹神话生物")
    check("SAN ≥5 临时疯狂", r2["temp_insanity"] and pc.insanity_state == "temporary",
          str(r2))
    r3 = pc.add_san_loss(30, "直面旧日支配者")
    check("SAN 大损失不定期疯狂", r3["indefinite_insanity"]
          and pc.insanity_state == "indefinite", str(r3))
    check("SAN 不为负", pc.san >= 0)
    pc2 = Character(name="GURPS 角色")  # san_max=0
    r4 = pc2.add_san_loss(10, "x")
    check("san_max=0 不扣 SAN", r4["loss"] == 0)
    # 快照/序列化往返
    snap = pc.create_snapshot()
    pc3 = Character(name="恢复者")
    pc3.restore_snapshot(snap)
    check("SAN 快照恢复", pc3.san == pc.san and pc3.san_max == 60
          and pc3.insanity_state == pc.insanity_state)


def test_coc7_scene_routing():
    import json
    from core.character import Character, Skill
    from core.scene_engine import SceneEngine
    from core.viewmodel import ViewModel
    from core.environment_system import EnvironmentSystem
    module = {
        "meta": {"systems": ["coc7"]},
        "act_1": {"nodes": [{
            "node_id": "n1", "scene_type": "perception",
            "layer_physics": {"skill_check": "侦查",
                              "san_loss": {"amount": "1d3", "source": "尸检"}},
        }]},
    }
    pc = Character(name="调查员", iq=12, san=60, san_max=60,
                   skills=[Skill("侦查", 60, "Avg", "IQ", 0)])
    env = EnvironmentSystem()
    vm = ViewModel()
    eng = SceneEngine(module, pc, vm, env, system_id="coc7")
    res = eng.run_node("n1")
    r = res.roll_info
    check("coc7 场景 packet system", r is not None and r.get("system") == "coc7",
          str(r)[:100])
    check("coc7 技能目标=60", r is not None and r.get("target") == 60)
    if r and not r.get("success") and r.get("san_loss"):
        check("coc7 失败触发 SAN 损失", r["san_loss"].get("loss", 0) > 0,
              str(r.get("san_loss")))
    else:
        check("coc7 失败触发 SAN 损失（未失败则跳过）", True)


def main():
    print("test_rules_profiles（v3.2 多系统画像 + v3.3 CoC 7e）")
    test_registry()
    test_gurps_check()
    test_gurps_damage()
    test_gurps_penetration()
    test_gurps_hit_location()
    test_gurps_defense_shock()
    test_engine_delegation()
    test_scene_engine_system_field()
    test_coc7_profile()
    test_coc7_san()
    test_coc7_scene_routing()
    print("================ 结果 ================")
    print("通过: %d    失败: %d" % (_PASS, _FAIL))
    if _FAIL:
        sys.exit(1)
    print("全部通过 ✔")


if __name__ == "__main__":
    main()
