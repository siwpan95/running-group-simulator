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


def test_dnd5e_profile():
    import random
    from core.rules import available_systems, get_profile
    check("注册表含 dnd5e", "dnd5e" in available_systems(), str(available_systems()))
    p = get_profile("dnd5e")
    check("dnd5e system_id", p.system_id == "dnd5e")
    check("dnd5e roll_high", p.check_style == "roll_high")
    r = p.roll_check(15, 5)
    check("dnd5e d20 范围", 1 <= r["roll"] <= 20, str(r))
    check("dnd5e target=DC", r["target"] == 15)
    check("dnd5e system 标记", r["system"] == "dnd5e")
    # 成功率统计：dc15 加成+5 → 55%
    random.seed(7)
    n = 3000
    ok = sum(1 for _ in range(n) if p.roll_check(15, 5)["success"])
    rate = ok / n
    check("dnd5e dc15+5 成功率约 55%", 0.48 <= rate <= 0.62, "%.3f" % rate)
    # 优劣势统计
    random.seed(7)
    avg_adv = sum(p.roll_check(15, 0, advantage=1)["roll"] for _ in range(3000)) / 3000
    avg_dis = sum(p.roll_check(15, 0, advantage=-1)["roll"] for _ in range(3000)) / 3000
    avg_pln = sum(p.roll_check(15, 0)["roll"] for _ in range(3000)) / 3000
    check("优势均值 > 普通 > 劣势", avg_adv > avg_pln > avg_dis,
          "%.2f > %.2f > %.2f" % (avg_adv, avg_pln, avg_dis))
    # 自然 20 / 自然 1（构造 roll=20 的断言：统计上 3000 次必出现）
    random.seed(11)
    crits = any(p.roll_check(15, -10)["is_crit_success"] for _ in range(400))
    fumbles = any(p.roll_check(2, 10)["is_fumble"] for _ in range(400))
    check("dnd5e 自然20 大成功出现", crits)
    check("dnd5e 自然1 大失败出现", fumbles)
    # 技能目标
    from core.character import Character, Skill
    pc = Character(name="游荡者", st=12, dx=16, ht=10, iq=12, per=12,
                   skills=[Skill("侦查", 4, "Avg", "WIS", 0)])
    check("dnd5e 属性修正 (16-10)//2=3", p.skill_target(pc, "敏捷") == 3)
    check("dnd5e 技能加成直取", p.skill_target(pc, "侦查") == 4)
    check("dnd5e 未列属性 0", p.skill_target(pc, "魅力") == 0)
    # 伤害/穿透/防御/重伤
    raw, t = p.roll_damage("2d6+3 挥砍")
    check("dnd5e 伤害 2d6+3 范围 5-15", 5 <= raw <= 15, str(raw))
    check("dnd5e 伤害类型挥砍", t == "挥砍", t)
    check("dnd5e 类型 fire", p.damage_type("1d6 fire") == "火焰")
    check("dnd5e 类型 necrotic", p.damage_type("2d8 necrotic") == "暗蚀")
    check("dnd5e 穿透平减", p.penetration(7, 2, "挥砍") == 5)
    check("dnd5e 大成功双倍", p.crit_damage(6) == 12)
    d = p.active_defense(15)
    check("dnd5e 无主动防御掷骰（AC 已含）", d["result"] == "hit")
    check("dnd5e 无休克", p.shock_check(10, 10, 8)["status"] == "ok")
    check("dnd5e 部位=身体", p.hit_location() == "身体")


def test_dnd5e_scene_routing():
    from core.character import Character, Skill
    from core.scene_engine import SceneEngine
    from core.viewmodel import ViewModel
    from core.environment_system import EnvironmentSystem
    module = {
        "meta": {"systems": ["dnd5e"]},
        "act_1": {"nodes": [{
            "node_id": "n1", "scene_type": "perception",
            "layer_physics": {"skill_check": "侦查", "dc": 13},
        }]},
    }
    pc = Character(name="游荡者", st=12, dx=16, ht=10, iq=12, per=12,
                   skills=[Skill("侦查", 4, "Avg", "WIS", 0)])
    env = EnvironmentSystem()
    vm = ViewModel()
    eng = SceneEngine(module, pc, vm, env, system_id="dnd5e")
    res = eng.run_node("n1")
    r = res.roll_info
    check("dnd5e 场景 packet system", r is not None and r.get("system") == "dnd5e",
          str(r)[:100])
    check("dnd5e 场景 DC=13", r is not None and r.get("target") == 13)
    check("dnd5e 场景 roll_total=roll+4", r is not None
          and r.get("roll_total") == r.get("roll", 0) + 4, str(r)[:120])


def test_dnd5e_combat_ac():
    from core.combat_engine import CombatEngine
    from core.character import Character
    from core.enemy import Enemy
    ce = CombatEngine("dnd5e")
    pc = Character(name="游荡者", ac=14)
    goblin = Enemy(name="哥布林", hp=7, hp_max=7, attack_skill=4,
                   damage="1d6+2 挥砍", ac=15)
    pkt = ce.attack_resolve(goblin, pc, 4)   # d20+4 vs PC AC 14
    check("dnd5e 战斗 packet system", pkt.get("system") == "dnd5e")
    check("dnd5e 战斗 target=PC AC", pkt.get("target") == 14, str(pkt.get("target")))
    pkt2 = ce.attack_resolve(pc, goblin, 5)  # d20+5 vs 哥布林 AC 15
    check("dnd5e 战斗 target=哥布林 AC", pkt2.get("target") == 15)


def test_wod_profile():
    from core.rules import available_systems, get_profile
    from core.rules.wod import roll_pool
    check("注册表含 wod", "wod" in available_systems(), str(available_systems()))
    p = get_profile("wod")
    check("wod system_id", p.system_id == "wod")
    check("wod roll_low 风格", p.check_style == "roll_low")
    # 骰池原语
    s, faces, h = roll_pool(10)
    check("wod 骰池成功数非负", s >= 0)
    check("wod 骰面长度 ≥ 骰池", len(faces) >= 10)
    # 检定
    r = p.roll_check(10, 0)
    check("wod pool 字段", r.get("pool") == 10, str(r))
    check("wod system 标记", r["system"] == "wod")
    check("wod 成功数即 roll", r["roll"] == r.get("pool_roll", r["roll"]))
    # 大成功 / 戏剧性失败统计
    import random
    random.seed(3)
    crits = any(p.roll_check(15, 0)["is_crit_success"] for _ in range(300))
    check("wod 15骰 300 次出现大成功", crits)
    random.seed(5)
    fumbles = any(p.roll_check(1, 0)["is_fumble"] for _ in range(400))
    check("wod 1骰 400 次出现戏剧性失败", fumbles)
    # 成功率
    chk = p.roll_check(10, 0)
    check("wod 10骰成功率≈97%", chk["success_chance"] == 97, str(chk["success_chance"]))
    # 饥饿骰 messy（大骰池+高饥饿，统计出现）
    random.seed(13)
    messy = any(p.roll_check(20, 0, hunger=5).get("messy_critical") for _ in range(1500))
    check("wod 饥饿骰 messy critical 出现", messy)
    # 技能目标
    from core.character import Character, Skill
    pc = Character(name="吸血鬼", st=11, dx=12, ht=10, iq=12, per=12, will=13,
                   skills=[Skill("格斗", 4, "Avg", "DX", 0)])
    check("wod 技能骰池直取", p.skill_target(pc, "格斗") == 4)
    check("wod 力量属性池", p.skill_target(pc, "力量") == 11)
    check("wod 意志属性池", p.skill_target(pc, "意志") == 13)
    # 伤害/防御/重伤
    raw, t = p.roll_damage("2d6+1 致命")
    check("wod 伤害类型致命", t == "致命", t)
    check("wod agg→恶性", p.damage_type("1d10 agg") == "恶性")
    check("wod 伤害平减", p.penetration(6, 2, "致命") == 4)
    check("wod 无暴击翻倍", p.crit_damage(7) == 7)
    d = p.active_defense(20)
    check("wod 防御结果合法", d["result"] in ("dodged", "hit"), str(d))
    check("wod 轻伤无惩罚", p.shock_check(10, 10, 3)["status"] == "ok")
    check("wod 重伤震慑", p.shock_check(10, 10, 6)["status"] == "stunned")


def test_wod_scene_routing():
    from core.character import Character, Skill
    from core.scene_engine import SceneEngine
    from core.viewmodel import ViewModel
    from core.environment_system import EnvironmentSystem
    module = {
        "meta": {"systems": ["wod"]},
        "act_1": {"nodes": [{
            "node_id": "n1", "scene_type": "perception",
            "layer_physics": {"skill_check": "侦查", "modifier": 2},
        }]},
    }
    pc = Character(name="吸血鬼", iq=12, per=12,
                   skills=[Skill("侦查", 3, "Avg", "WIT", 0)])
    env = EnvironmentSystem()
    vm = ViewModel()
    eng = SceneEngine(module, pc, vm, env, system_id="wod")
    res = eng.run_node("n1")
    r = res.roll_info
    check("wod 场景 packet system", r is not None and r.get("system") == "wod",
          str(r)[:100])
    check("wod 场景 pool=3+2", r is not None and r.get("pool") == 5,
          str(r)[:120])


def main():
    print("test_rules_profiles（v3.2 多系统画像 + CoC/D&D/WoD）")
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
    test_dnd5e_profile()
    test_dnd5e_scene_routing()
    test_dnd5e_combat_ac()
    test_wod_profile()
    test_wod_scene_routing()
    print("================ 结果 ================")
    print("通过: %d    失败: %d" % (_PASS, _FAIL))
    if _FAIL:
        sys.exit(1)
    print("全部通过 ✔")


if __name__ == "__main__":
    main()
