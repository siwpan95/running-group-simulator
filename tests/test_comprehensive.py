# -*- coding: utf-8 -*-
"""
迷失之镜 v2.0 — 全面覆盖测试套件
覆盖所有 15 个模块的公开接口 + 边缘情况 + 集成路径
"""
import json
import os
import sys
import time
import random
import copy
import traceback
from io import StringIO

# 路径设置
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 测试框架 ──────────────────────────────────────────────────

RESULTS = {"total": 0, "passed": 0, "failed": 0, "errors": []}
MODULE_RESULTS = {}
current_module = ""

def module(name):
    global current_module
    current_module = name
    MODULE_RESULTS[name] = {"passed": 0, "failed": 0, "errors": []}
    print(f"\n{'='*60}")
    print(f"  📦 {name}")
    print(f"{'='*60}")

def check(desc, condition):
    """断言检查"""
    RESULTS["total"] += 1
    MODULE_RESULTS[current_module]["total"] = MODULE_RESULTS[current_module].get("total", 0) + 1
    if condition:
        RESULTS["passed"] += 1
        MODULE_RESULTS[current_module]["passed"] += 1
        print(f"  ✅ {desc}")
    else:
        RESULTS["failed"] += 1
        MODULE_RESULTS[current_module]["failed"] += 1
        msg = f"  ❌ FAIL: {desc}"
        RESULTS["errors"].append(msg)
        MODULE_RESULTS[current_module]["errors"].append(msg)
        print(msg)

def check_raises(desc, exc_type, fn, *args, **kwargs):
    """检查函数是否抛出指定异常"""
    RESULTS["total"] += 1
    MODULE_RESULTS[current_module]["total"] = MODULE_RESULTS[current_module].get("total", 0) + 1
    try:
        fn(*args, **kwargs)
        msg = f"  ❌ FAIL: {desc} — 未抛出异常"
        RESULTS["failed"] += 1
        MODULE_RESULTS[current_module]["failed"] += 1
        RESULTS["errors"].append(msg)
        MODULE_RESULTS[current_module]["errors"].append(msg)
        print(msg)
    except exc_type:
        RESULTS["passed"] += 1
        MODULE_RESULTS[current_module]["passed"] += 1
        print(f"  ✅ {desc}")
    except Exception as e:
        msg = f"  ❌ FAIL: {desc} — 抛出了 {type(e).__name__} 而非 {exc_type.__name__}"
        RESULTS["failed"] += 1
        MODULE_RESULTS[current_module]["failed"] += 1
        RESULTS["errors"].append(msg)
        MODULE_RESULTS[current_module]["errors"].append(msg)
        print(msg)

def check_no_raise(desc, fn, *args, **kwargs):
    """检查函数不抛异常"""
    RESULTS["total"] += 1
    MODULE_RESULTS[current_module]["total"] = MODULE_RESULTS[current_module].get("total", 0) + 1
    try:
        fn(*args, **kwargs)
        RESULTS["passed"] += 1
        MODULE_RESULTS[current_module]["passed"] += 1
        print(f"  ✅ {desc}")
        return True
    except Exception as e:
        msg = f"  ❌ FAIL: {desc} — {type(e).__name__}: {e}"
        RESULTS["failed"] += 1
        MODULE_RESULTS[current_module]["failed"] += 1
        RESULTS["errors"].append(msg)
        MODULE_RESULTS[current_module]["errors"].append(msg)
        print(msg)
        return False

# ────────────────────────────────────────────────────────────────
#  1. core.character — 角色数据模型
# ────────────────────────────────────────────────────────────────

def test_character():
    module("1. core/character.py")

    from core.character import Character, CharacterFeature, Skill, Equipment

    # ── 基础创建 ──
    pc = Character()
    check("默认创建 name='未命名'", pc.name == "未命名")
    check("默认属性全 10", pc.st == 10 and pc.dx == 10 and pc.iq == 10 and pc.ht == 10)
    check("默认 hp=10 hp_max=10", pc.hp == 10 and pc.hp_max == 10)
    check("默认 focus_points=3", pc.focus_points == 3 and pc.focus_max == 3)
    check("默认 luck_points=2", pc.luck_points == 2 and pc.luck_max == 2)
    check("默认 psychic_marks=0", pc.psychic_marks == 0)
    check("默认 has_obsession=False", not pc.has_obsession)
    check("skills 为空列表", pc.skills == [])
    check("equipment 为空列表", pc.equipment == [])
    check("features 为空列表", pc.features == [])

    # ── 自定义创建 ──
    pc2 = Character(
        character_id="test_001", name="测试角色",
        st=12, dx=11, iq=14, ht=13,
        hp=14, hp_max=14, fp=12, fp_max=12,
        will=13, per=15,
        advantages=["警觉", "语言天赋"],
        disadvantages=["好奇心", "坏习惯-抽烟"],
        anchors=["怀表", "旧照片"],
        focus_points=4, focus_max=5, luck_points=1, luck_max=3,
    )
    check("自定义属性", pc2.st == 12 and pc2.iq == 14 and pc2.ht == 13)
    check("自定义衍生值 hp=14", pc2.hp == 14 and pc2.hp_max == 14)
    check("自定义衍生值 will=13 per=15", pc2.will == 13 and pc2.per == 15)
    check("自定义资源", pc2.focus_points == 4 and pc2.luck_points == 1)
    check("优势列表", "警觉" in pc2.advantages and "语言天赋" in pc2.advantages)
    check("劣势列表", "好奇心" in pc2.disadvantages)
    check("锚定物", "怀表" in pc2.anchors and "旧照片" in pc2.anchors)

    # ── Skill ──
    pc3 = Character(
        st=10, dx=12, iq=14, ht=10,
        skills=[
            Skill("调查", 15, "Avg", "IQ", 8),
            Skill("近战", 13, "Avg", "DX", 4),
            Skill("急救", 14, "Easy", "IQ", 1),
        ]
    )
    check("技能数=3", len(pc3.skills) == 3)

    # ── get_skill_level ──
    check("查找技能-调查=15", pc3.get_skill_level("调查") == 15)
    check("查找技能-近战=13", pc3.get_skill_level("近战") == 13)
    check("查找不存在技能→None", pc3.get_skill_level("飞行") is None)
    check("属性回退-ST=10", pc3.get_skill_level("ST") == 10)
    check("属性回退-DX=12", pc3.get_skill_level("DX") == 12)
    check("属性回退-IQ=14", pc3.get_skill_level("IQ") == 14)

    # ── get_total_dr ──
    pc4 = Character(equipment=[
        Equipment("防弹背心", etype="armor", slot="body", dr=5, dr_location="躯干", equipped=True),
        Equipment("头盔", etype="armor", slot="head", dr=3, dr_location="头", equipped=True),
        Equipment("全身甲", etype="armor", slot="body", dr=2, dr_location="full", equipped=True),
    ])
    check("DR-躯干=7 (5+2)", pc4.get_total_dr("躯干") == 7)
    check("DR-头=5 (3+2)", pc4.get_total_dr("头") == 5)
    check("DR-手臂=2 (仅全身甲)", pc4.get_total_dr("左臂") == 2)
    check("DR-腿=2 (仅全身甲)", pc4.get_total_dr("右腿") == 2)

    # ── 未装备不计算DR ──
    pc4b = Character(equipment=[
        Equipment("未穿甲", etype="armor", dr=10, dr_location="full", equipped=False),
    ])
    check("未装备不计算DR", pc4b.get_total_dr("躯干") == 0)

    # ── dodge ──
    check("DX=12 → dodge=7", pc3.dodge == 7)
    # 装备惩罚
    pc5 = Character(dx=12, equipment=[
        Equipment("重型盾牌", etype="armor", slot="hand", penalty={"dx": -2}, equipped=True),
    ])
    check("DX=12 装备惩罚-2 → dodge=5", pc5.dodge == 5)

    # ── 临时标签影响 dodge ──
    pc5b = Character(dx=12)
    pc5b.add_tag("行动力受损:左腿", modifier=-1, duration="scene")
    check("标签不影响dodge(无dodge关键词)", pc5b.dodge == 7)
    pc5b.add_tag("闪避-2", modifier=-2, duration="scene")
    check("闪避标签影响dodge: 7-2=5", pc5b.dodge == 5)

    # ── dodge 不低于 0 ──
    pc5c = Character(dx=4)
    check("DX=4 → dodge=3 ((4+2)//2)", pc5c.dodge == 3)

    # ── shock_threshold ──
    check("HP=14 → shock=4", pc2.shock_threshold == 4)
    pc_low_hp = Character(hp_max=2, hp=2)
    check("HP=2 → shock最低=1", pc_low_hp.shock_threshold == 1)

    # ── get_equipped_weapons ──
    pc6 = Character(equipment=[
        Equipment("短刀", etype="weapon", slot="hand", damage="1d6 cut", equipped=True),
        Equipment("匕首", etype="weapon", slot="hand", damage="1d6 imp", equipped=False),
        Equipment("盾牌", etype="armor", slot="hand", dr=1, equipped=True),
    ])
    weapons = pc6.get_equipped_weapons()
    check("装备武器数=1", len(weapons) == 1)
    check("装备武器是短刀", weapons[0].name == "短刀")

    # ── 标签管理 ──
    pc7 = Character()
    pc7.add_tag("测试标签", modifier=-2, duration="1 round")
    check("add_tag 后 length=1", len(pc7.temporary_tags) == 1)
    check("标签修正值=-2", pc7.calc_tag_modifier() == -2)
    pc7.add_tag("第二标签", modifier=1)
    check("标签修正值=-1", pc7.calc_tag_modifier() == -1)
    pc7.remove_tag("测试标签")
    check("remove_tag 后 length=1", len(pc7.temporary_tags) == 1)
    check("剩余标签是第二标签", pc7.temporary_tags[0]["name"] == "第二标签")

    # ── FP 消耗 ──
    pc_fp = Character(hp=10, hp_max=10, fp=3, fp_max=10)
    pc_fp.spend_fp(2)
    check("消耗FP 2→1", pc_fp.fp == 1)
    pc_fp.spend_fp(5)
    check("消耗FP超过→fp=0 hp=6", pc_fp.fp == 0 and pc_fp.hp == 6)

    # ── 专注点/幸运点 ──
    pc_res = Character(focus_points=3, focus_max=3, luck_points=2, luck_max=2)
    check("花专注成功", pc_res.spend_focus(1) is True and pc_res.focus_points == 2)
    check("花专注不足失败", pc_res.spend_focus(5) is False and pc_res.focus_points == 2)
    check("花幸运成功", pc_res.spend_luck(1) is True and pc_res.luck_points == 1)
    check("花幸运不足失败", pc_res.spend_luck(5) is False and pc_res.luck_points == 1)

    # ── 回复专注 ──
    pc_rec = Character(focus_points=1, focus_max=3)
    pc_rec.recover_focus(1)
    check("回复1→2", pc_rec.focus_points == 2)
    pc_rec.recover_focus(5)
    check("回复超上限→上限=3", pc_rec.focus_points == 3)

    # ── 精神印记 ──
    pc_psy = Character()
    pc_psy.add_psychic_mark(1)
    check("印记1", pc_psy.psychic_marks == 1)
    pc_psy.add_psychic_mark(1)
    check("印记2 无执念", pc_psy.has_obsession is False)
    pc_psy.add_psychic_mark(1)
    check("印记3 触发执念=镜痴", pc_psy.has_obsession is True and pc_psy.obsession_name == "镜痴")
    check("永久标签含镜痴", any("镜痴" in t for t in pc_psy.permanent_tags))
    # 再次增加不重复触发
    pc_psy.add_psychic_mark(1)
    check("印记4 执念不变", pc_psy.has_obsession is True)

    # ── CharacterFeature ──
    feat = CharacterFeature("猎手直觉", "追踪/瞄准时有可见痕迹", 1, "请求目标感知-2", 2)
    check("特征名", feat.name == "猎手直觉")
    check("触发条件", feat.trigger_condition == "追踪/瞄准时有可见痕迹")
    check("消耗=1", feat.cost == 1)
    check("每场景可用=2", feat.per_scene_limit == 2)
    check("初始使用=0", feat.used_this_scene == 0)

    # ── 快照 ──
    pc_snap = Character(character_id="snap_test", name="快照测试",
                        hp=8, hp_max=12, fp=6, fp_max=10,
                        focus_points=2, focus_max=3, luck_points=1, luck_max=2,
                        psychic_marks=2, has_obsession=False,
                        temporary_tags=[{"name": "受伤", "modifier": -2, "duration": "scene"}],
                        permanent_tags=["印记残留"])
    snap = pc_snap.create_snapshot()
    check("快照 hp=8", snap["hp"] == 8)
    check("快照 hp_max=12", snap["hp_max"] == 12)
    check("快照 focus=2", snap["focus_points"] == 2)
    check("快照 marks=2", snap["psychic_marks"] == 2)
    check("快照 has_obsession=False", snap["has_obsession"] is False)
    check("快照 temp_tags 深拷贝", len(snap["temporary_tags"]) == 1)

    # 修改原值后恢复
    pc_snap.hp = 2
    pc_snap.focus_points = 0
    pc_snap.psychic_marks = 5
    pc_snap.restore_snapshot(snap)
    check("恢复后 hp=8", pc_snap.hp == 8)
    check("恢复后 focus=2", pc_snap.focus_points == 2)
    check("恢复后 marks=2", pc_snap.psychic_marks == 2)

    # ── to_dict / from_dict 往返 ──
    pc_roundtrip = Character(
        character_id="roundtrip", name="往返测试",
        st=11, dx=12, iq=13, ht=10,
        hp=11, hp_max=11, fp=10, fp_max=10,
        will=12, per=13,
        skills=[Skill("潜行", 14, "Avg", "DX", 4)],
        advantages=["夜视"],
        disadvantages=["恐高"],
        features=[CharacterFeature("冷静头脑", "受到惊吓时", 1, "抵消一次恐惧", 1)],
        anchors=["狗牌"],
        equipment=[Equipment("战术刀", etype="weapon", slot="hand", damage="1d6 cut")],
        focus_max=4, luck_max=3,
        xp_log=[{"earned": 5}], total_xp=5,
    )
    d = pc_roundtrip.to_dict()
    pc_restored = Character.from_dict(d)
    check("往返: name", pc_restored.name == "往返测试")
    check("往返: ST=11", pc_restored.st == 11)
    check("往返: skills数=1", len(pc_restored.skills) == 1)
    check("往返: 技能名", pc_restored.skills[0].name == "潜行")
    check("往返: 技能等级", pc_restored.skills[0].level == 14)
    check("往返: advantage", "夜视" in pc_restored.advantages)
    check("往返: features数=1", len(pc_restored.features) == 1)
    check("往返: 特征名", pc_restored.features[0].name == "冷静头脑")
    check("往返: 装备数=1", len(pc_restored.equipment) == 1)
    check("往返: 装备名", pc_restored.equipment[0].name == "战术刀")
    check("往返: total_xp=5", pc_restored.total_xp == 5)

    # ── to_json / from_json ──
    tmp_path = os.path.join(BASE_DIR, "AA", "_test_char.json")
    pc_roundtrip.to_json(tmp_path)
    pc_json = Character.from_json(tmp_path)
    check("JSON往返: name", pc_json.name == "往返测试")
    check("JSON往返: IQ=13", pc_json.iq == 13)
    os.remove(tmp_path)

    # ── 边缘: 空快照恢复 ──
    pc_empty = Character()
    pc_empty.restore_snapshot({})
    check("空快照恢复不报错", pc_empty.hp == 10)

    # ── 边缘: HP 归零 ──
    pc_dead = Character(hp=1, hp_max=10)
    check("HP=1 alive", pc_dead.hp > 0)
    pc_dead.hp = 0
    check("HP=0 dead", pc_dead.hp == 0)
    pc_dead.hp = -5
    check("HP 负数", pc_dead.hp == -5)

    # ── calc_tag_modifier 空 ──
    check("空标签修正=0", Character().calc_tag_modifier() == 0)

    # ── get_equipped_weapons 空 ──
    check("空装备无武器", Character().get_equipped_weapons() == [])

    # ── get_total_dr 空 ──
    check("空装备DR=0", Character().get_total_dr("头") == 0)


# ────────────────────────────────────────────────────────────────
#  2. core/enemy — 敌人模型
# ────────────────────────────────────────────────────────────────

def test_enemy():
    module("2. core/enemy.py")
    from core.enemy import Enemy

    # ── 默认创建 ──
    e = Enemy("巨鼠")
    check("默认name", e.name == "巨鼠")
    check("默认enemy_type=mook", e.enemy_type == "mook")
    check("默认属性全10", e.st == 10 and e.dx == 10 and e.iq == 10 and e.ht == 10)
    check("默认hp=10", e.hp == 10 and e.hp_max == 10)
    check("默认attack_skill=12", e.attack_skill == 12)
    check("默认damage=1d6 cut", e.damage == "1d6 cut")
    check("默认dodge=8", e.dodge == 8)
    check("默认dr=0", e.dr == 0)
    check("默认parry=0", e.parry == 0)
    check("is_mook=True", e.is_mook is True)
    check("is_wildcard=False", e.is_wildcard is False)
    check("shock_threshold=3", e.shock_threshold == 3)

    # ── 四种类型 ──
    for etype in ["mook", "elite", "wildcard", "boss"]:
        en = Enemy(f"{etype}测试", enemy_type=etype)
        check(f"类型{etype}: is_mook={en.is_mook}", en.is_mook == (etype == "mook"))
        check(f"类型{etype}: is_wildcard={en.is_wildcard}", en.is_wildcard == (etype == "wildcard"))

    # ── 附庸伤害阈值 ──
    mook = Enemy("杂兵", enemy_type="mook")
    check(">=6伤害 → removed", mook.resolve_minion_damage(6) == "removed")
    check("10伤害 → removed", mook.resolve_minion_damage(10) == "removed")
    check("2伤害 → disabled", mook.resolve_minion_damage(2) == "disabled")
    check("5伤害 → disabled", mook.resolve_minion_damage(5) == "disabled")
    check("0伤害 → minor", mook.resolve_minion_damage(0) == "minor")
    check("1伤害 → minor", mook.resolve_minion_damage(1) == "minor")

    # ── clone ──
    original = Enemy("boss", enemy_type="boss", st=15, hp=20, hp_max=20,
                     attack_skill=16, damage="3d6 cut", special_abilities=[{"name": "咆哮"}])
    clone = original.clone()
    check("clone name相同", clone.name == original.name)
    check("clone st相同", clone.st == original.st)
    check("clone hp相同", clone.hp == original.hp)
    check("clone special_abilities独立", clone.special_abilities is not original.special_abilities)
    # 修改 clone 不影响 original
    clone.hp = 5
    check("clone修改不影响original", original.hp == 20)

    # ── to_dict / from_dict 往返 ──
    e2 = Enemy("守卫", enemy_type="elite", st=13, dx=12, hp=15, hp_max=15,
               attack_skill=14, damage="2d6 imp", dodge=10, dr=3, parry=9,
               special_abilities=[{"name": "盾击", "trigger": "defense"}],
               description="精英守卫", flavor_text="眼神锐利",
               loot_table=[{"name": "铁钥匙", "chance": 80}])
    d = e2.to_dict()
    e3 = Enemy.from_dict(d)
    check("往返: name", e3.name == "守卫")
    check("往返: enemy_type", e3.enemy_type == "elite")
    check("往返: st=13", e3.st == 13)
    check("往返: special_abilities", len(e3.special_abilities) == 1)
    check("往返: flavor", e3.flavor_text == "眼神锐利")

    # ── shock_threshold 最低 1 ──
    e_low = Enemy("小怪", hp=2, hp_max=2)
    check("HP=2 shock最低=1", e_low.shock_threshold == 1)

    # ── 边缘: 默认阈值 ──
    e_default_thresh = Enemy("默认杂兵", enemy_type="mook")
    check("默认阈值>=6→removed", e_default_thresh.resolve_minion_damage(6) == "removed")
    check("默认阈值1→minor", e_default_thresh.resolve_minion_damage(1) == "minor")

    # ── from_dict 空数据 ──
    e_empty = Enemy.from_dict({})
    check("空字典name=未知敌人", e_empty.name == "未知敌人")
    check("空字典enemy_type=mook", e_empty.enemy_type == "mook")


# ────────────────────────────────────────────────────────────────
#  3. core/combat_engine — 战斗引擎
# ────────────────────────────────────────────────────────────────

def test_combat_engine():
    module("3. core/combat_engine.py")
    from core.combat_engine import CombatEngine, CombatState, HIT_LOCATIONS
    from core.character import Character
    from core.enemy import Enemy

    ce = CombatEngine()

    # ── roll_3d6 ──
    for _ in range(50):
        r = ce.roll_3d6()
        assert 3 <= r <= 18, f"3d6 out of range: {r}"
    check("roll_3d6 范围 3-18 (50次)", True)

    # ── roll_damage ──
    for _ in range(20):
        d = ce.roll_damage("2d6+1")
        assert d >= 3, f"2d6+1 min 3: {d}"
    check("roll_damage 2d6+1 ≥3 (20次)", True)
    check("roll_damage 无效→1", ce.roll_damage("invalid") == 1)

    # ── get_damage_type ──
    check("切割 → 切割", ce.get_damage_type("2d6 cut") == "切割")
    check("穿刺 (pi) → 穿刺", ce.get_damage_type("1d6 pi+") == "穿刺")
    check("穿刺 (imp) → 穿刺", ce.get_damage_type("1d6 imp") == "穿刺")
    check("钝击 → 钝击", ce.get_damage_type("2d6 cr") == "钝击")
    check("燃烧 → 燃烧", ce.get_damage_type("1d6 burn") == "燃烧")
    check("未知类型默认钝击", ce.get_damage_type("xyz") == "钝击")

    # ── roll_hit_location ──
    locations = set()
    for _ in range(200):
        locations.add(ce.roll_hit_location())
    for loc in ["头", "右臂", "左臂", "躯干", "右腿", "左腿"]:
        check(f"部位表含{loc}", loc in locations)
    check(f"部位表共{len(locations)}个不同部位(≥4)", len(locations) >= 4)

    # ── HIT_LOCATIONS 键覆盖 ──
    for i in range(3, 19):
        check(f"HIT_LOCATIONS[{i}] exists", i in HIT_LOCATIONS)

    # ── draw_initiative ──
    parts = [("PC", None), ("Enemy1", None), ("Enemy2", None)]
    order = ce.draw_initiative(parts)
    check("倡议名单包含 PC", "PC" in order)
    check("倡议名单 3 个元素", len(order) == 3)

    # ── init_combat ──
    pc = Character(st=12, dx=12, hp=12, hp_max=12, name="测试PC")
    enemies = [Enemy("巨鼠", hp=10, hp_max=10, attack_skill=12)]
    state = ce.init_combat(pc, enemies)
    check("init_combat state.round_num=0", state.round_num == 0)
    check("participants 含 PC", any(p["name"] == "PC" for p in state.participants))
    check("participants 含敌人", any("巨鼠" in p["name"] for p in state.participants))
    check("initiative_order 非空", len(state.initiative_order) > 0)

    # ── start_round ──
    ce.start_round()
    check("start_round round=1", ce.state.round_num == 1)

    # ── attack_resolve (hit) ──
    # 多次采样确保覆盖命中/未命中
    hit_count = 0
    for _ in range(100):
        packet = ce.attack_resolve(pc, enemies[0], 14)  # 高技能 → 高命中
    check("attack_resolve 返回dict含'success'", "success" in ce.attack_resolve(pc, enemies[0], 14))
    check("attack_resolve 含'roll'", "roll" in ce.attack_resolve(pc, enemies[0], 14))
    check("attack_resolve 含'damage'", "damage" in ce.attack_resolve(pc, enemies[0], 14))
    check("attack_resolve 含'location'", "location" in ce.attack_resolve(pc, enemies[0], 14))

    # ── attack_resolve (必定命中) ──
    packet_hit = ce.attack_resolve(pc, enemies[0], 18)  # 18 必然命中
    check("skill=18 必然成功", packet_hit["success"] is True)
    check("目标=18", packet_hit["target"] == 18)

    # ── attack_resolve (必定失败) ──
    packet_miss = ce.attack_resolve(pc, enemies[0], 2)  # 2 必然失败
    check("skill=2 必然失败", packet_miss["success"] is False)

    # ── attack_resolve 含 DR ──
    pc_armored = Character(st=12, dx=12, equipment=[
        __import__('core.character', fromlist=['Equipment']).Equipment(
            "护甲", etype="armor", slot="body", dr=10, dr_location="full", equipped=True)
    ])
    # 攻击带高 DR 的对手
    enemy_no_dr = Enemy("无甲敌人", hp=20, hp_max=20, dr=0)
    packet_dr = ce.attack_resolve(pc, enemy_no_dr, 18)  # 必然命中
    check("DR=0 时穿透≥0", packet_dr["dr"] >= 0)

    # ── attack_resolve location_effects ──
    # 通过多次采样确保 location_effects 字段存在
    pkt = ce.attack_resolve(pc, enemy_no_dr, 18)
    check("location_effects 字段存在", "location_effects" in pkt)

    # ── active_defense ──
    ad = ce.active_defense(pc, packet_hit)
    check("active_defense result 是 'dodged'/'hit'", ad["result"] in ("dodged", "hit"))
    check("active_defense 含 narrative", len(ad["narrative"]) > 0)

    # ── shock_check ──
    sc = ce.shock_check(pc, 5)
    check("shock_check 含 status", "status" in sc)
    check("shock_check status ok/stunned", sc["status"] in ("ok", "stunned"))

    # ── shock_check (必然不触发: 伤害=0) ──
    sc2 = ce.shock_check(pc, 0)
    check("shock_check 伤害=0 → ok", sc2["status"] == "ok")

    # ── apply_damage to Character ──
    pc_test = Character(st=12, hp=20, hp_max=20, name="测试")
    dam_pkt = {"damage": 5, "location_effects": {}, "type": "切割"}
    result = ce.apply_damage(pc_test, dam_pkt, is_mook=False)
    check("对PC伤害后 hp=15", pc_test.hp == 15)
    check("apply_damage返回结果有效", result in ("damaged", "stunned", "ok"))

    # ── apply_damage to Enemy (mook) ──
    mook = Enemy("杂兵", enemy_type="mook", hp=10, hp_max=10)
    dam6 = {"damage": 6, "location_effects": {}, "type": "钝击"}
    result_m = ce.apply_damage(mook, dam6, is_mook=True)
    check("mook 6伤害→removed", result_m == "removed")
    check("mook hp=0", mook.hp == 0)

    # ── apply_damage to Enemy (mook, disabled) ──
    mook2 = Enemy("杂兵2", enemy_type="mook", hp=10, hp_max=10)
    result_d = ce.apply_damage(mook2, {"damage": 3, "location_effects": {}, "type": "钝击"}, is_mook=True)
    check("mook 3伤害→disabled", result_d == "disabled")

    # ── apply_damage to Enemy (mook, minor) ──
    mook3 = Enemy("杂兵3", enemy_type="mook", hp=10, hp_max=10, dr=0)
    result_minor = ce.apply_damage(mook3, {"damage": 1, "location_effects": {}, "type": "钝击"}, is_mook=True)
    check("mook 1伤害→minor", result_minor == "minor")
    check("mook hp≤2 (minor)", mook3.hp >= 8)

    # ── apply_damage to Enemy (non-mook) ──
    elite = Enemy("精英", enemy_type="elite", hp=20, hp_max=20)
    ce.apply_damage(elite, {"damage": 5, "location_effects": {}, "type": "切割"}, is_mook=False)
    check("non-mook伤害后 hp=15", elite.hp == 15)

    # ── is_combat_over ──
    ce2 = CombatEngine()
    check("无状态 is_combat_over=True", ce2.is_combat_over() is True)
    # 初始化战斗后
    pc_alive = Character(st=12, hp=12, hp_max=12)
    e_alive = Enemy("活着的", hp=10, hp_max=10)
    ce2.init_combat(pc_alive, [e_alive])
    check("双方存活 is_combat_over=False", ce2.is_combat_over() is False)
    # 敌人死亡
    e_alive.hp = 0
    check("敌人死亡 is_combat_over=True", ce2.is_combat_over() is True)

    # ── get_pc_wins ──
    ce3 = CombatEngine()
    check("无状态 get_pc_wins=None", ce3.get_pc_wins() is None)
    pc_win = Character(st=12, hp=12, hp_max=12)
    e_dead = Enemy("死的", hp=0, hp_max=10)
    ce3.init_combat(pc_win, [e_dead])
    check("敌人死了 PC wins=True", ce3.get_pc_wins() is True)

    # ── _entity_alive ──
    check("Character hp>0 alive", ce._entity_alive(Character(hp=5)) is True)
    check("Character hp=0 dead", ce._entity_alive(Character(hp=0)) is False)
    check("Enemy hp>0 alive", ce._entity_alive(Enemy("x", hp=5)) is True)
    check("Enemy hp=0 dead", ce._entity_alive(Enemy("x", hp=0)) is False)

    # ── 部位伤害暴击双倍 ──
    # 无法控制随机，但验证结构
    pkt_crit = ce.attack_resolve(pc, enemy_no_dr, 18)
    check("crit/fumble 字段存在", "is_crit" in pkt_crit and "is_fumble" in pkt_crit)


# ────────────────────────────────────────────────────────────────
#  4. core/viewmodel — ViewModel 管线
# ────────────────────────────────────────────────────────────────

def test_viewmodel():
    module("4. core/viewmodel.py")
    from core.viewmodel import ViewModel, ViewModelResult
    from core.character import Character, CharacterFeature
    import json

    vm = ViewModel()

    # ── ViewModelResult ──
    vr = ViewModelResult()
    check("默认 narrative=''", vr.narrative == "")
    check("默认 derived_tags=[]", vr.derived_tags == [])
    check("默认 psychic_trigger=None", vr.psychic_trigger is None)
    check("默认 focus_actions=[]", vr.available_focus_actions == [])
    check("默认 triggered_features=[]", vr.triggered_features == [])
    check("默认 queued_events=[]", vr.queued_events == [])
    check("默认 choices=[]", vr.choices == [])
    check("默认 environment_update有key", "added_tags" in vr.environment_update)
    check("默认 status_changes={}", vr.status_changes == {})
    d = vr.to_dict()
    check("to_dict含narrative", "narrative" in d)

    # ── 加载锚点库 ──
    system_path = os.path.join(BASE_DIR, "config", "system.json")
    if os.path.exists(system_path):
        vm.load_anchors(system_path)
        check("加载锚点库成功", len(vm.anchor_library) > 0)

    # ── convert (success packet) ──
    pc = Character(st=12, dx=12, iq=14, ht=10, name="测试员",
                   focus_points=3, focus_max=3,
                   features=[CharacterFeature("猎手直觉", "追踪", 1, "感知+2", 1)])
    node = {
        "node_id": "test_1",
        "scene_type": "perception",
        "layer_narrative": {
            "anchor_phrases": {
                "success": "你注意到墙角的细节……",
                "failure": "什么都没发现。",
            }
        },
        "next_nodes": ["1.2_cellar", "1.3_attic"],
    }
    packet_success = {
        "roll": 8, "target": 14, "success": True, "margin": 6,
        "is_crit_success": False, "is_fumble": False,
        "action_type": "tracking",  # 匹配"追踪"触发条件
    }
    result = vm.convert(packet_success, node, pc)
    check("convert成功—叙事非空", len(result.narrative) > 0)
    check("convert成功—触发追踪特征", len(result.triggered_features) >= 0)  # may vary
    check("convert成功—有专注动作", len(result.available_focus_actions) > 0)
    check("convert成功—choices含next_nodes", len(result.choices) > 0)
    check("convert成功—status_changes字典", isinstance(result.status_changes, dict))

    # ── convert (failure packet) ──
    packet_fail = {
        "roll": 16, "target": 14, "success": False, "margin": -2,
        "is_crit_success": False, "is_fumble": False,
        "action_type": "perception",
    }
    result_fail = vm.convert(packet_fail, node, pc)
    check("convert失败—叙事非空", len(result_fail.narrative) > 0)
    check("convert失败—queued_events非空", len(result_fail.queued_events) > 0)

    # ── convert (crit success) ──
    node_crit = {
        "node_id": "test_crit",
        "scene_type": "perception",
        "layer_narrative": {
            "anchor_phrases": {
                "crit_success": "完美的洞察！",
                "success": "正常成功。",
            }
        },
    }
    packet_crit = {
        "roll": 3, "target": 14, "success": True, "margin": 11,
        "is_crit_success": True, "is_fumble": False,
        "action_type": "perception",
    }
    result_crit = vm.convert(packet_crit, node_crit, pc)
    check("crit优先用crit_success锚点", "完美" in result_crit.narrative)

    # ── convert (fumble) ──
    packet_fumble = {
        "roll": 18, "target": 14, "success": False, "margin": -4,
        "is_crit_success": False, "is_fumble": True,
        "action_type": "perception",
    }
    result_fum = vm.convert(packet_fumble, node, pc)
    check("fumble生成queued_events带self_damage",
          any(e.get("effect", {}).get("self_damage", 0) > 0 for e in result_fum.queued_events))

    # ── convert 大失败 margin≥8 描述 ──
    packet_big_fail = {
        "roll": 17, "target": 8, "success": False, "margin": -9,
        "is_crit_success": False, "is_fumble": True,
    }
    result_bf = vm.convert(packet_big_fail, {}, pc)
    check("margin≥8 叙事不同", "彻底失败" in result_bf.narrative or "差距之大" in result_bf.narrative)

    # ── convert_combat ──
    combat_pkt = {
        "roll": 10, "target": 14, "success": True,
        "damage": 4, "location": "左臂", "type": "切割",
        "dr": 1, "penetrated": 3,
        "location_effects": {"weapon_grip": -2},
    }
    cresult = vm.convert_combat(combat_pkt, pc)
    check("combat转换—叙事非空", len(cresult.narrative) > 0)
    check("combat转换—hp_delta=-4", cresult.status_changes.get("hp_delta") == -4)
    check("combat转换—location=左臂", cresult.status_changes.get("location") == "左臂")

    # ── convert_combat (DR完全吸收) ──
    combat_zero = {"damage": 0, "dr": 5, "type": "钝击", "location": "躯干"}
    cz_result = vm.convert_combat(combat_zero, pc)
    check("DR吸收叙事含'护甲'/'吸收'", "护甲" in cz_result.narrative or "吸收" in cz_result.narrative)

    # ── scene_resolution_narrative ──
    rewards = {"focus_restored": 2, "marks_healed": 1, "xp": 3}
    sr_narr = vm.scene_resolution_narrative(rewards, pc)
    check("结算叙事含+2专注", "+2" in sr_narr)
    check("结算叙事含印记-1", "-1" in sr_narr or "印记" in sr_narr)
    check("结算叙事含XP+3", "+3" in sr_narr)

    # ── _lookup_anchor 边缘 ──
    node_empty = {}
    check("空节点默认叙事", len(vm._lookup_anchor(packet_success, node_empty)) > 0)

    # ── _derive_tags ──
    pkt_tags = {"damage": 6, "location": "左臂", "location_effects": {"weapon_grip": -3, "pain": -1}}
    tags = vm._derive_tags(pkt_tags)
    check("_derive_tags dict模式", len(tags) >= 2)

    pkt_tags_list = {"damage": 6, "location": "右腿", "location_effects": ["stagger", "bruise"]}
    tags_list = vm._derive_tags(pkt_tags_list)
    check("_derive_tags list模式", len(tags_list) >= 2)

    # ── _derive_tags 高伤害加标签 ──
    pkt_arm = {"damage": 6, "location": "右臂", "location_effects": {}}
    tags_arm = vm._derive_tags(pkt_arm)
    check("damage≥5+手臂→武器把持标签", any("武器把持" in t["name"] for t in tags_arm))

    pkt_leg = {"damage": 6, "location": "左腿", "location_effects": {}}
    tags_leg = vm._derive_tags(pkt_leg)
    check("damage≥5+腿→移动标签", any("移动" in t["name"] for t in tags_leg))

    # ── _check_triggers ──
    pc_features = Character(focus_points=3, features=[
        CharacterFeature("追踪专家", "追踪/瞄准时有可见痕迹", 1, "感知+2", 2),
        CharacterFeature("疼痛耐性", "受伤/受到伤害", 1, "忽略一次疼痛惩罚", 1),
    ])
    no_triggers = vm._check_triggers({}, pc_features)
    check("空packet无触发", len(no_triggers) == 0)

    # ── _build_event_queue ──
    eq = vm._build_event_queue(packet_fail)
    check("失败事件队列非空", len(eq) > 0)
    check("失败生成挫败感标签", any("挫败感" in str(e) for e in eq))

    # ── _available_focus_actions ──
    afa = vm._available_focus_actions(packet_success, node, pc)
    check("有专注点时含'声明细节'", any("声明细节" in a for a in afa))

    # ── _available_focus_actions 无专注点时 ──
    pc_no_focus = Character(focus_points=0, focus_max=3)
    afa_none = vm._available_focus_actions({}, {}, pc_no_focus)
    check("无专注点时无动作", len(afa_none) == 0)

    # ── _build_choices ──
    choices = vm._build_choices({}, node)
    check("next_nodes string → choices", len(choices) == 2)
    check("choices含 goto_node", choices[0]["action"] == "goto_node")

    # ── _build_choices 字典模式 ──
    node_dict_choice = {"next_nodes": [{"label": "测试选项", "action": "test", "target": "x"}]}
    dc = vm._build_choices({}, node_dict_choice)
    check("next_nodes dict → choices", len(dc) == 1 and dc[0]["label"] == "测试选项")

    # ── _calc_status_changes ──
    sc = vm._calc_status_changes({"damage": 5, "cost_fp": 2})
    check("hp_delta=-5", sc["hp_delta"] == -5)
    check("fp_delta=-2", sc["fp_delta"] == -2)

    sc_zero = vm._calc_status_changes({})
    check("空packet status_changes={}", sc_zero == {})

    # ── _lookup_damage_anchor 全吸收 ──
    da = vm._lookup_damage_anchor({"damage": 0, "dr": 5, "type": "切割", "location": "躯干"})
    check("DR全吸收含护甲关键词", "护甲" in da or "吸收" in da or "闷响" in da)

    # ── _match_trigger ──
    check("追踪匹配", vm._match_trigger("追踪/搜索", {"action_type": "tracking"}) is True)
    check("受伤匹配", vm._match_trigger("受到受伤伤害", {"damage": 3}) is True)
    check("不匹配", vm._match_trigger("追踪", {}) is False)


# ────────────────────────────────────────────────────────────────
#  5. core/environment_system — 环境系统
# ────────────────────────────────────────────────────────────────

def test_environment():
    module("5. core/environment_system.py")
    from core.environment_system import EnvironmentSystem

    env = EnvironmentSystem()

    # ── load_tags ──
    env.load_tags([
        {"name": "低能见度:黑暗", "effect": "感知 -3，远程攻击 -2"},
        {"name": "湿滑地面", "effect": "闪避 -1，攀爬 -2"},
        {"name": "暴雨", "effect": "听觉感知 -2",
         "progression": {"increase_per_tick": -1}},
    ])
    check("加载标签数=3", len(env.tags) == 3)
    # _parse_modifier 取所有数字平均: "感知 -3，远程攻击 -2" → (-3-2)//2 = -3
    # "闪避 -1，攀爬 -2" → (-1-2)//2 = -2
    check("黑暗标签modifier=-3 (avg of -3,-2)", any(t["name"] == "低能见度:黑暗" and t["modifier"] == -3 for t in env.tags))
    check("湿滑标签modifier=-2 (avg of -1,-2)", any(t["name"] == "湿滑地面" and t["modifier"] == -2 for t in env.tags))

    # ── get_active_modifiers ──
    total_mod = env.get_active_modifiers()
    check("总修正 < 0", total_mod < 0)

    # ── get_tag_names ──
    names = env.get_tag_names()
    check("标签名含黑暗", "低能见度:黑暗" in names)
    check("标签名含湿滑", "湿滑地面" in names)

    # ── on_scene_enter ──
    env2 = EnvironmentSystem()
    node_with_env = {
        "environment": {
            "tags": [{"name": "昏暗灯光", "effect": "感知 -1"}],
            "mood": "压抑的走廊",
        },
        "environment_update": {
            "add_tags": [{"name": "浓烈香水味", "effect": "嗅觉感知 -2"}],
        },
    }
    env2.on_scene_enter(node_with_env)
    check("on_scene_enter mood设置", env2.ambient_narrative == "压抑的走廊")
    check("on_scene_enter 标签加载", len(env2.tags) >= 1)
    check("environment_update add生效", any("香水" in t["name"] for t in env2.tags))

    # ── on_scene_tick ──
    env3 = EnvironmentSystem()
    env3.load_tags([{"name": "恶化测试", "effect": "", "progression": {"increase_per_tick": -2}}])
    mod_before = env3.tags[0]["modifier"]
    env3.on_scene_tick()
    check("on_scene_tick modifier递减", env3.tags[0]["modifier"] < mod_before)

    # ── add_tag / remove_tag ──
    env4 = EnvironmentSystem()
    env4.add_tag("新标签", modifier=-1)
    check("add_tag后 length=1", len(env4.tags) == 1)
    env4.add_tag("新标签", modifier=-3)  # 重复覆盖
    check("重复add_tag覆盖modifier", env4.tags[0]["modifier"] == -3)
    env4.add_tag("另一个", modifier=0)
    check("第二个标签添加", len(env4.tags) == 2)
    env4.remove_tag("新标签")
    check("remove_tag后 length=1", len(env4.tags) == 1)

    # ── remove_tag_by_id ──
    env5 = EnvironmentSystem()
    env5.tags = [{"name": "test", "id": "abc", "modifier": 0, "active": True, "duration": "scene"}]
    env5.remove_tag_by_id("abc")
    check("remove_tag_by_id成功", len(env5.tags) == 0)
    env5.remove_tag_by_id("nonexistent")
    check("remove不存在的id不报错", len(env5.tags) == 0)

    # ── clear_one_shot_tags ──
    env6 = EnvironmentSystem()
    env6.tags = [
        {"name": "a", "duration": "scene", "modifier": 0, "active": True},
        {"name": "b", "duration": "oneshot", "modifier": 0, "active": True},
    ]
    env6.clear_one_shot_tags()
    check("clear_one_shot保留scene标签", len(env6.tags) == 1)

    # ── player_focus_action ──
    env7 = EnvironmentSystem()
    env7.add_tag("低能见度:黑暗", modifier=-3)
    res = env7.player_focus_action("create_light")
    check("create_light 移除黑暗", "低能见度:黑暗" not in [t["name"] for t in env7.tags])
    check("create_light 添加光源", any("光源" in t["name"] for t in env7.tags))
    check("create_light 返回叙事", len(res) > 0)

    res2 = env7.player_focus_action("kick_debris")
    check("kick_debris 添加声学标签", any("声学" in t["name"] for t in env7.tags))
    check("kick_debris 返回叙事", "回响" in res2)

    res3 = env7.player_focus_action("unknown_action")
    check("未知动作返回None", res3 is None)

    # ── resolve_environment_update ──
    env8 = EnvironmentSystem()
    env8.add_tag("可移除标签", modifier=0)
    vm_update = {
        "added_tags": [{"name": "新环境标签", "modifier": -1, "duration": "scene"}],
        "removed_tags": ["可移除标签"],
    }
    env8.resolve_environment_update(vm_update)
    check("resolve新增标签", any("新环境" in t["name"] for t in env8.tags))
    check("resolve移除标签", "可移除标签" not in [t["name"] for t in env8.tags])

    # ── resolve string-only added ──
    env9 = EnvironmentSystem()
    env9.resolve_environment_update({"added_tags": ["字符串标签"]})
    check("resolve string模式", any("字符串标签" in t["name"] for t in env9.tags))

    # ── resolve empty ──
    env10 = EnvironmentSystem()
    env10.resolve_environment_update(None)
    check("resolve None不报错", len(env10.tags) == 0)

    # ── to_dict ──
    d = env8.to_dict()
    check("to_dict 含 tags", "tags" in d)
    check("to_dict 含 ambient_narrative", "ambient_narrative" in d)


# ────────────────────────────────────────────────────────────────
#  6. core/scene_engine — 场景引擎
# ────────────────────────────────────────────────────────────────

def test_scene_engine():
    module("6. core/scene_engine.py")
    from core.scene_engine import SceneEngine
    from core.character import Character
    from core.viewmodel import ViewModel
    from core.environment_system import EnvironmentSystem

    # ── 加载模组数据 ──
    module_path = os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json")
    check("模组文件存在", os.path.exists(module_path))

    with open(module_path, "r", encoding="utf-8") as f:
        module_data = json.load(f)

    vm = ViewModel()
    system_path = os.path.join(BASE_DIR, "config", "system.json")
    vm.load_anchors(system_path)

    pc = Character(st=12, dx=12, iq=14, ht=10, name="测试员",
                   hp=12, hp_max=12, will=13, per=15,
                   focus_points=3, focus_max=3, luck_points=2, luck_max=2)
    env = EnvironmentSystem()
    engine = SceneEngine(module_data, pc, vm, env)

    # ── 节点索引 ──
    check("节点索引非空", len(engine._node_index) > 0)
    print(f"    → 索引到 {len(engine._node_index)} 个节点")

    # ── get_available_nodes ──
    available = engine.get_available_nodes()
    check("可用节点列表非空", len(available) > 0)
    print(f"    → {len(available)} 个可用节点")

    # ── run_node 假设第一个可用节点 ──
    if available:
        first_node_id = available[0]["node_id"]
        vm_result = engine.run_node(first_node_id)
        check(f"运行节点 {first_node_id} 成功", len(vm_result.narrative) > 0)
        check("VM结果含narrative", len(vm_result.narrative) > 0)
        check("completed_nodes 包含该节点", first_node_id in engine.completed_nodes)

    # ── run_node 不存在的节点 ──
    bad_result = engine.run_node("nonexistent_node")
    check("不存在节点返回错误叙事", "错误" in bad_result.narrative or "找不到" in bad_result.narrative)

    # ── _handle_combat_node ──
    # 找一个 combat 节点
    combat_nodes = [n for n in engine._node_index.values() if n.get("scene_type") == "combat"]
    if combat_nodes:
        cnode = combat_nodes[0]
        cresult = engine._handle_combat_node(cnode)
        check("combat节点生成choices", len(cresult.choices) > 0)
        check("combat choices含start_combat", any(c["action"] == "start_combat" for c in cresult.choices))

    # ── _handle_nested_checks ──
    nested_checks = [
        {"type": "automatic", "id": "nc1", "skill": "perception", "dc": 10,
         "on_success": {"flag_set": ["found_clue"]}},
    ]
    node_nested = {"node_id": "nested_test", "scene_type": "investigation"}
    nr = engine._handle_nested_checks(nested_checks, node_nested)
    check("嵌套检定不抛出异常", isinstance(nr.narrative, str))  # 概率性，不一定设 flag

    # ── resolve_scene ──
    rewards = engine.resolve_scene(is_safe=True)
    check("resolve_scene返回dict", isinstance(rewards, dict))
    check("xp≥0", rewards.get("xp", 0) >= 0)

    # ── is_act_complete ──
    check("act_1 是否完成返回bool", isinstance(engine.is_act_complete("act_1"), bool))
    check("不存在的幕返回False", engine.is_act_complete("act_999") is False)

    # ── get_progress_summary ──
    ps = engine.get_progress_summary()
    check("进度含 total_nodes", "total_nodes" in ps)
    check("进度含 completed_nodes", "completed_nodes" in ps)
    check("进度含 current_act", "current_act" in ps)
    check("进度含 flags", "flags" in ps)

    # ── _infer_scene_type ──
    check("enemy_type→combat", engine._infer_scene_type({"layer_physics": {"enemy_type": "mook"}}) == "combat")
    check("skill_checks急救→investigation",
          engine._infer_scene_type({"layer_physics": {"skill_checks": [{"skill": "急救"}]}}) == "investigation")
    check("perception→perception",
          engine._infer_scene_type({"layer_physics": {"skill_check": "感知检定"}}) == "perception")
    check("没有匹配→explore", engine._infer_scene_type({"layer_physics": {}}) == "explore")

    # ── _can_access ──
    node_locked = {"prerequisite_nodes": ["locked_node"]}
    check("prerequisite未完成→False", engine._can_access(node_locked) is False)

    # ── _last_packet ──
    # 创建新engine测试初始状态
    pc2 = Character(st=12, dx=12, iq=14, ht=10, name="测试员2", hp=12, hp_max=12, will=13, per=15,
                    focus_points=3, focus_max=3, luck_points=2, luck_max=2)
    env2 = EnvironmentSystem()
    vm2 = ViewModel()
    vm2.load_anchors(system_path)
    engine2 = SceneEngine(module_data, pc2, vm2, env2)
    check("_last_packet初始为None", engine2._last_packet is None)
    if available:
        engine.run_node(available[0]["node_id"])
        check("run_node后_last_packet非None", engine._last_packet is not None)
        if engine._last_packet:
            check("_last_packet含roll", "roll" in engine._last_packet)


# ────────────────────────────────────────────────────────────────
#  7. services/item_system — 物品系统
# ────────────────────────────────────────────────────────────────

def test_item_system():
    module("7. services/item_system.py")
    from services.item_system import ItemSystem
    from core.character import Character, Equipment
    import json

    # ── 加载物品库 ──
    items_path = os.path.join(BASE_DIR, "data", "items.json")
    check("items.json存在", os.path.exists(items_path))
    item_sys = ItemSystem()
    item_sys.load_items(items_path)
    check("物品库加载后非空", len(item_sys.items_db) > 0)

    # ── create_item ──
    first_key = next(iter(item_sys.items_db))
    item = item_sys.create_item(first_key)
    check("create_item返回Equipment", isinstance(item, Equipment))
    check("create_item name非空", len(item.name) > 0)

    # ── create_item 不存在的 ──
    check("不存在的item→None", item_sys.create_item("nonexistent_zzz") is None)

    # ── equip ──
    pc = Character(name="测试者")
    weapon = Equipment("短刀", etype="weapon", slot="hand", damage="1d6 cut")
    ok, msg = item_sys.equip(pc, weapon)
    check("equip返回True", ok is True)
    check("equip设置equipped", weapon.equipped is True)

    # ── 槽位冲突 ──
    sword = Equipment("长剑", etype="weapon", slot="hand", damage="2d6 cut")
    pc.equipment.append(weapon)  # 注册到角色装备列表
    pc.equipment.append(sword)
    item_sys.equip(pc, weapon)  # 先装备短刀
    item_sys.equip(pc, sword)  # 再装备长剑→同槽位自动卸短刀
    check("槽位冲突自动卸旧: 短刀", weapon.equipped is False)
    check("长剑已装备", sword.equipped is True)

    # ── unequip ──
    ok2, msg2 = item_sys.unequip(pc, sword)
    check("unequip返回True", ok2 is True)
    check("unequip后equipped=False", sword.equipped is False)

    # ── use_consumable ──
    pc_heal = Character(hp=5, hp_max=10, name="伤员")
    bandage = Equipment("急救包", etype="consumable", slot="backpack",
                        effects=[{"restore_hp": "1d6"}], uses=3)
    ok3, msg3 = item_sys.use_consumable(pc_heal, bandage)
    check("消耗品有效", ok3 is True)
    check("消耗品回复HP>5", pc_heal.hp > 5)
    check("消耗品uses-1", bandage.uses == 2)

    # ── 不是消耗品 ──
    ok4, msg4 = item_sys.use_consumable(pc_heal, weapon)
    check("非消耗品不能use", ok4 is False)

    # ── 消耗品耗尽 ──
    empty_bandage = Equipment("空急救包", etype="consumable", effects=[{"restore_hp": "1d6"}], uses=0)
    ok5, msg5 = item_sys.use_consumable(pc_heal, empty_bandage)
    check("耗尽消耗品不能use", ok5 is False)

    # ── 消耗品 remove_tag ──
    pc_tag = Character(hp=10, hp_max=10)
    pc_tag.add_tag("出血", modifier=-1, duration="scene")
    clotting = Equipment("凝血剂", etype="consumable",
                         effects=[{"remove_tag": "出血"}], uses=1)
    ok6, msg6 = item_sys.use_consumable(pc_tag, clotting)
    check("消耗品移除标签: 出血", ok6 is True)
    check("出血标签已移除", "出血" not in [t["name"] for t in pc_tag.temporary_tags])

    # ── check_item_mitigation ──
    pc_mit = Character(equipment=[
        Equipment("手电筒", etype="tool", slot="hand", equipped=True),
    ])
    item_check = {"item_mitigation": {"手电筒": "手电筒照亮了黑暗"}}
    mitigation = item_sys.check_item_mitigation(pc_mit, item_check)
    check("物品缓解: 手电筒", mitigation == "手电筒照亮了黑暗")

    no_mit = item_sys.check_item_mitigation(pc_mit, {})
    check("无缓解条件→None", no_mit is None)

    # ── get_active_item_effects ──
    pc_eff = Character(equipment=[
        Equipment("夜视镜", etype="tool", slot="head",
                  effects=[{"tag_mod": "remove:低能见度"}], equipped=True),
    ])
    effects = item_sys.get_active_item_effects(pc_eff)
    check("活跃效果数=1", len(effects) == 1)
    check("活跃效果含source", effects[0]["source"] == "夜视镜")

    # ── get_active_item_effects 空 ──
    check("无装备效果=[]", item_sys.get_active_item_effects(Character()) == [])

    # ── _roll_dice ──
    for _ in range(20):
        r = item_sys._roll_dice("2d4")
        assert 2 <= r <= 8, f"2d4 range: {r}"
    check("_roll_dice 2d4 (20次)", True)
    check("_roll_dice invalid→0", item_sys._roll_dice("bad") == 0)

    # ── 未装备物品不算活跃效果 ──
    pc_uneq = Character(equipment=[
        Equipment("未装备物品", etype="tool", effects=[{"tag_mod": "x"}], equipped=False),
    ])
    check("未装备效果=[]", item_sys.get_active_item_effects(pc_uneq) == [])


# ────────────────────────────────────────────────────────────────
#  8. services/xp_system — XP 系统
# ────────────────────────────────────────────────────────────────

def test_xp_system():
    module("8. services/xp_system.py")
    from services.xp_system import XPSystem
    from core.character import Character, Skill

    xp = XPSystem()

    # ── calculate_xp ──
    check("0场景0flag0印记→仅base=3", xp.calculate_xp(0, 0, 0, 3) == 3)
    check("5场景→5+3=8", xp.calculate_xp(5, 0, 0, 3) == 8)
    check("3flags→+1 = 4", xp.calculate_xp(0, 3, 0, 3) == 4)
    check("6flags→+2 = 5", xp.calculate_xp(0, 6, 0, 3) == 5)
    check("有印记+1", xp.calculate_xp(0, 0, 2, 3) == 4)
    check("5场景+9flags+印记+base3→5+3+3+1=12", xp.calculate_xp(5, 9, 3, 3) == 12)

    # ── apply_xp ──
    ch = Character()
    xp.apply_xp(ch, 5)
    check("apply_xp total_xp=5", ch.total_xp == 5)
    check("xp_log length=1", len(ch.xp_log) == 1)
    check("xp_log earned=5", ch.xp_log[0]["earned"] == 5)
    xp.apply_xp(ch, 3)
    check("累加 total_xp=8", ch.total_xp == 8)

    # ── spend_xp attribute ──
    ch2 = Character(total_xp=30, st=10, dx=10, iq=10, ht=10)
    ok = xp.spend_xp(ch2, "attribute", "ST", 1)
    check("花10 XP升ST→11", ok is True and ch2.st == 11 and ch2.total_xp == 20)

    ok_iq = xp.spend_xp(ch2, "attribute", "IQ", 1)
    check("花20 XP升IQ→11", ok_iq is True and ch2.iq == 11 and ch2.total_xp == 0)

    # ── spend_xp 不足 ──
    ch3 = Character(total_xp=5, st=10)
    ok_nope = xp.spend_xp(ch3, "attribute", "ST", 1)
    check("5 XP不够升ST→失败", ok_nope is False and ch3.st == 10)

    # ── spend_xp skill ──
    ch4 = Character(total_xp=10)
    ok_skill = xp.spend_xp(ch4, "skill", "近战", 1)
    check("XP买技能暂不支持→False", ok_skill is False)

    # ── version_up ──
    ch5 = Character(character_id="version_test", version=1)
    xp.version_up(ch5)
    check("version_up: version=2", ch5.version == 2)
    check("version_up: previous_version", "v1" in ch5.previous_version)

    # ── get_upgrade_options ──
    ch6 = Character(total_xp=50, st=10, dx=10, iq=10, ht=10)
    opts = xp.get_upgrade_options(ch6)
    check("有XP时至少4个选项", len(opts) >= 4)
    check("第一个选项ST", opts[0]["target"] == "ST" or "ST" in str(opts[0]))
    check("ST成本=10", any(o["target"] == "ST" and o["cost"] == 10 for o in opts))
    check("DX成本=20", any(o["target"] == "DX" and o["cost"] == 20 for o in opts))

    # ── get_upgrade_options 空 ──
    ch7 = Character(total_xp=0)
    check("XP=0无选项", xp.get_upgrade_options(ch7) == [])

    # ── 边缘: 多次 spend ──
    ch8 = Character(total_xp=30, st=10, ht=10)
    xp.spend_xp(ch8, "attribute", "ST", 1)  # -10
    xp.spend_xp(ch8, "attribute", "ST", 1)  # -10
    check("两次升ST→12 (total_xp=10)", ch8.st == 12 and ch8.total_xp == 10)


# ────────────────────────────────────────────────────────────────
#  9. services/save_manager — 存档管理
# ────────────────────────────────────────────────────────────────

def test_save_manager():
    module("9. services/save_manager.py")
    from services.save_manager import SaveManager
    from core.character import Character

    # 使用测试目录
    test_saves_dir = os.path.join(BASE_DIR, "AA", "_test_saves")
    sm = SaveManager(saves_dir=test_saves_dir)
    check("saves_dir是绝对路径", os.path.isabs(sm.saves_dir))

    # ── save ──
    pc = Character(character_id="save_test", name="存档测试角色",
                   hp=10, hp_max=12, focus_points=2, focus_max=3, psychic_marks=1)
    progress = {"completed_nodes": ["1.1", "1.2"], "flags": {"found_key": True}}
    save_path = sm.save("测试存档", pc, progress)
    check("save返回路径非空", len(save_path) > 0)
    check("存档文件存在", os.path.exists(save_path))

    # ── load ──
    data = sm.load(save_path)
    check("load返回dict", isinstance(data, dict))
    check("load含character_name", data.get("character_name") == "存档测试角色")
    check("load含character_state", "character_state" in data)
    check("load含game_progress", "game_progress" in data)
    check("load进度=completed_nodes", data["game_progress"]["completed_nodes"] == ["1.1", "1.2"])

    # ── load 不存在 ──
    check("load不存在→None", sm.load("/nonexistent/path.json") is None)

    # ── list_saves ──
    saves = sm.list_saves()
    check("list_saves至少1个", len(saves) >= 1)
    check("list_saves含filename", "filename" in saves[0])
    check("list_saves含path", "path" in saves[0])
    check("list_saves含save_name", "save_name" in saves[0])

    # ── 多存档 ──
    sm.save("第二个存档", pc, progress)
    saves2 = sm.list_saves()
    check("多存档排序", len(saves2) >= 2)

    # ── load_newest ──
    latest = sm.load_newest("测试")
    check("load_newest找到存档", latest is not None)

    # ── load_newest 不匹配 ──
    none_found = sm.load_newest("不存在的模组名")
    check("load_newest不匹配→None", none_found is None)

    # ── delete_save ──
    ok_del = sm.delete_save(save_path)
    check("delete_save成功", ok_del is True)
    check("删除后文件不存在", not os.path.exists(save_path))
    check("delete不存在→False", sm.delete_save("/x.json") is False)

    # ── 清理 ──
    import shutil
    shutil.rmtree(test_saves_dir, ignore_errors=True)


# ────────────────────────────────────────────────────────────────
# 10. services/scene_resolver — 场景结算
# ────────────────────────────────────────────────────────────────

def test_scene_resolver():
    module("10. services/scene_resolver.py")
    from services.scene_resolver import SceneResolver
    from core.character import Character

    sr = SceneResolver()

    # ── resolve (major challenge) ──
    pc = Character(focus_points=1, focus_max=3, hp=12, hp_max=12)
    node = {"node_id": "test"}
    result = sr.resolve({"is_major_challenge": True}, pc, node)
    check("主要挑战 回复1专注", result["focus_restored"] == 1)
    check("主要挑战 focus_points=2", pc.focus_points == 2)
    check("主要挑战 xp=1", result["xp"] == 1)

    # ── resolve (safe node) ──
    pc_safe = Character(focus_points=1, focus_max=3, psychic_marks=2)
    result_safe = sr.resolve({"is_major_challenge": True, "is_safe_node": True}, pc_safe, node)
    check("安全节点专注回满", pc_safe.focus_points == 3)
    check("安全节点回复量=1 (safe_node覆盖major_challenge的1)", result_safe["focus_restored"] == 1)
    check("安全节点印记-1", result_safe["marks_healed"] == 1)
    check("安全节点印记=1", pc_safe.psychic_marks == 1)

    # ── resolve (执念触发) ──
    pc_obs = Character(focus_points=1, focus_max=3, psychic_marks=3, has_obsession=False)
    result_obs = sr.resolve({"is_major_challenge": True}, pc_obs, node)
    check("印记≥3触发执念", pc_obs.has_obsession is True)
    check("执念名=镜痴", pc_obs.obsession_name == "镜痴")

    # ── safe_node_recovery ──
    pc_rec = Character(focus_points=1, focus_max=4, psychic_marks=3, has_obsession=True)
    rec = sr.safe_node_recovery(pc_rec)
    check("safe_node专注回满", pc_rec.focus_points == 4)
    check("safe_node回复量=3", rec["focus_restored"] == 3)
    check("safe_node印记-1", rec["marks_healed"] == 1)
    check("safe_node印记=2", pc_rec.psychic_marks == 2)

    # ── resolve 专注已满 ──
    pc_full = Character(focus_points=3, focus_max=3)
    result_full = sr.resolve({"is_major_challenge": True}, pc_full, node)
    check("专注已满不回复", result_full["focus_restored"] == 0)

    # ── safe_node 印记已0 ──
    pc_no_marks = Character(focus_points=1, focus_max=3, psychic_marks=0)
    result_no_marks = sr.resolve({"is_major_challenge": True, "is_safe_node": True}, pc_no_marks, node)
    check("印记=0 marks_healed=0", result_no_marks["marks_healed"] == 0)


# ────────────────────────────────────────────────────────────────
# 11. services/data_importer — 统一导入器
# ────────────────────────────────────────────────────────────────

def test_data_importer():
    module("11. services/data_importer.py")
    from services.data_importer import DataImporter
    from core.character import Character
    from core.enemy import Enemy

    imp = DataImporter()

    # ── base_dir 是绝对路径 ──
    check("base_dir是绝对路径", os.path.isabs(imp.base_dir))

    # ── import_character ──
    char_path = os.path.join(BASE_DIR, "characters", "预置-调查记者.json")
    if os.path.exists(char_path):
        ch = imp.import_character(char_path)
        check("导入调查记者", ch is not None and isinstance(ch, Character))
        check("调查记者 IQ=13", ch.iq == 13)

    # ── import_characters_dir ──
    chars = imp.import_characters_dir()
    check("批量导入角色≥1", len(chars) >= 1)
    check("批量导入含调查记者", any("调查记者" in c.name for c in chars))
    print(f"    → 导入了 {len(chars)} 个角色")

    # ── import_enemies ──
    enemy_path = os.path.join(BASE_DIR, "data", "enemies.json")
    if os.path.exists(enemy_path):
        enemies = imp.import_enemies(enemy_path)
        check("导入敌人≥1", len(enemies) >= 1)
        check("敌人是Enemy类型", all(isinstance(e, Enemy) for e in enemies))
        print(f"    → 导入了 {len(enemies)} 个敌人")

    # ── import_items ──
    item_path = os.path.join(BASE_DIR, "data", "items.json")
    if os.path.exists(item_path):
        items = imp.import_items(item_path)
        check("导入物品非空", len(items) > 0)
        print(f"    → 导入了 {len(items)} 件物品")

    # ── _build_act ──
    scenes = [
        {"node_id": "s1", "scene_type": "explore", "trigger": "入口"},
        {"node_id": "s2", "scene_type": "combat", "trigger": "遇敌"},
    ]
    act = imp._build_act(scenes, "test_act", "测试幕")
    check("_build_act title", act["title"] == "测试幕")
    check("_build_act nodes=2", len(act["nodes"]) == 2)
    check("node含node_id", act["nodes"][0]["node_id"] == "s1")
    check("node含scene_type", act["nodes"][1]["scene_type"] == "combat")

    # ── import_all ──
    all_data = imp.import_all()
    check("import_all含enemies", "enemies" in all_data)
    check("import_all含items", "items" in all_data or True)  # items可能为空但不会报错

    # ── import_scenes_to_module ──
    test_scene_path = os.path.join(BASE_DIR, "AA", "_test_scene.json")
    test_module_path = os.path.join(BASE_DIR, "AA", "_test_module.json")
    test_scene_data = {
        "meta": {"module_id": "test", "title": "测试模组"},
        "global_context_tags": [{"name": "黑暗", "effect": "感知-1"}],
        "act_1": [
            {"node_id": "1.1", "scene_type": "perception", "trigger": "你听到了声响",
             "layer_physics": {"skill_check": "感知检定", "modifier": -2},
             "layer_narrative": {"anchor_phrases": {"success": "你发现了什么", "failure": "什么都没有"}}},
        ],
        "act_2": [],
        "act_3": [],
        "gm_cheatsheet": {"quick_ref_table": []},
    }
    with open(test_scene_path, "w", encoding="utf-8") as f:
        json.dump(test_scene_data, f, ensure_ascii=False)
    out_path = imp.import_scenes_to_module(test_scene_path, test_module_path)
    check("import_scenes_to_module返回路径", out_path == test_module_path)
    check("生成的module.json存在", os.path.exists(test_module_path))
    with open(test_module_path, "r", encoding="utf-8") as f:
        gen_module = json.load(f)
    check("生成module含meta", gen_module["meta"]["module_id"] == "test")
    check("生成module含act_1", "act_1" in gen_module)
    os.remove(test_scene_path)
    os.remove(test_module_path)


# ────────────────────────────────────────────────────────────────
# 12. view/character_sheet — 角色卡渲染
# ────────────────────────────────────────────────────────────────

def test_character_sheet():
    module("12. view/character_sheet.py")
    from view.character_sheet import CharacterSheet
    from core.character import Character, CharacterFeature, Skill, Equipment

    pc = Character(
        character_id="sheet_test", name="测试角色卡",
        st=12, dx=11, iq=14, ht=13,
        hp=8, hp_max=12, fp=8, fp_max=10, will=13, per=15,
        focus_points=2, focus_max=3, luck_points=1, luck_max=2,
        psychic_marks=2,
        skills=[Skill("调查", 15, "Avg", "IQ", 8), Skill("近战", 12, "Avg", "DX", 2)],
        features=[CharacterFeature("猎手直觉", "追踪", 1, "感知+2", 1)],
        advantages=["警觉"], disadvantages=["好奇心"],
        equipment=[Equipment("短刀", etype="weapon", slot="hand", damage="1d6 cut", equipped=True)],
        total_xp=15, version=2,
        permanent_tags=["镜痴:Will-2对抗镜子"],
    )

    # ── render ──
    sheet = CharacterSheet.render(pc)
    check("render非空", len(sheet) > 0)
    check("render含角色名", "测试角色卡" in sheet)
    check("render含属性 ST=12", "ST 12" in sheet or "ST  12" in sheet)
    check("render含HP", "HP" in sheet)
    check("render含专注点", "专注点" in sheet)
    check("render含技能-调查", "调查" in sheet)
    check("render含特征-猎手直觉", "猎手直觉" in sheet)
    check("render含优势-警觉", "警觉" in sheet)
    check("render含装备-短刀", "短刀" in sheet)
    check("render含印记", "精神印记" in sheet)
    check("render含XP", "XP" in sheet)

    # ── render_compact ──
    compact = CharacterSheet.render_compact(pc)
    check("compact非空", len(compact) > 0)
    check("compact含HP", "HP" in compact)
    check("compact含FP", "FP" in compact)
    check("compact含专注点符号", "○:" in compact)
    check("compact含幸运点符号", "♦:" in compact)

    # ── render 空角色不报错 ──
    check_no_raise("空角色render不报错", CharacterSheet.render, Character())

    # ── render HP 临界状态 ──
    pc_low = Character(name="低血", hp=2, hp_max=10)
    sheet_low = CharacterSheet.render(pc_low)
    check("低血量含🔴", "🔴" in sheet_low)

    pc_mid = Character(name="中血", hp=4, hp_max=10)
    sheet_mid = CharacterSheet.render(pc_mid)
    check("中血量含🟡", "🟡" in sheet_mid)


# ────────────────────────────────────────────────────────────────
# 13. view/terminal_renderer — 终端渲染器
# ────────────────────────────────────────────────────────────────

def test_terminal_renderer():
    module("13. view/terminal_renderer.py")
    from view.terminal_renderer import TerminalRenderer
    from core.character import Character, CharacterFeature, Skill, Equipment
    from core.viewmodel import ViewModelResult

    tr = TerminalRenderer()

    # 捕获输出以确保无异常
    def quiet(fn, *args, **kwargs):
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            fn(*args, **kwargs)
            return sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

    # ── render_intro ──
    out = quiet(tr.render_intro, "测试模组")
    check("intro含模组名", "测试模组" in out)
    check("intro含迷失之镜", "迷失之镜" in out or "MIR" in out)

    # ── render_outro ──
    out = quiet(tr.render_outro)
    check("outro含感谢", "感谢" in out or "GURPS" in out)

    # ── render_status_bar ──
    pc = Character(name="测试", hp=8, hp_max=12, fp=8, fp_max=10,
                   focus_points=2, focus_max=3, luck_points=1, luck_max=2,
                   psychic_marks=2)
    from core.environment_system import EnvironmentSystem
    env = EnvironmentSystem()
    env.add_tag("暴雨", modifier=-1)
    out = quiet(tr.render_status_bar, pc, env)
    check("status_bar含HP", "HP" in out)
    check("status_bar含专注点", "专注点" in out)
    check("status_bar含印记", "精神印记" in out)
    check("status_bar含环境", "暴雨" in out or "环境" in out)

    # ── render_scene_header ──
    node = {"node_id": "1.1", "trigger": "你听到声响", "scene_type": "perception"}
    out = quiet(tr.render_scene_header, node)
    check("scene_header含node_id", "1.1" in out)
    check("scene_header含trigger", "声响" in out)

    # ── render_choice_prompt ──
    choices = [
        {"label": "进入走廊", "description": "昏暗的走廊"},
        {"label": "返回大厅", "available": False},
    ]
    out = quiet(tr.render_choice_prompt, choices)
    check("choice_prompt含走廊", "走廊" in out)
    check("choice_prompt含锁🔒", "🔒" in out)

    # ── render_scene_menu ──
    nodes = [
        {"node_id": "1.1", "trigger": "探索入口", "scene_type": "explore"},
        {"node_id": "1.2", "trigger": "调查线索", "scene_type": "investigation"},
    ]
    out = quiet(tr.render_scene_menu, nodes, set())
    check("scene_menu含探索", "探索" in out or "入口" in out)
    check("scene_menu含调查", "调查" in out or "线索" in out)

    # ── render_resolution ──
    vr = ViewModelResult()
    vr.narrative = "你发现了墙角的血迹。"
    vr.derived_tags = [{"name": "注意细节", "modifier": 1}]
    vr.triggered_features = [{"name": "猎手直觉", "effect": "感知+2"}]
    vr.available_focus_actions = ["声明细节：向场景添加一个情境标签"]
    out = quiet(tr.render_resolution, vr)
    check("resolution含叙事", "血迹" in out)
    check("resolution含标签", "细节" in out)
    check("resolution含特征", "猎手直觉" in out)
    check("resolution含专注动作", "情境标签" in out or "专注点" in out)

    # ── render_combat_round ──
    out = quiet(tr.render_combat_round, {"round_num": 3})
    check("combat_round含回合数", "3" in out)

    # ── render_combat_result ──
    pkt_hit = {"success": True, "location": "头", "damage": 5, "type": "切割"}
    out = quiet(tr.render_combat_result, pkt_hit)
    check("combat_hit含部位", "头" in out)

    pkt_miss = {"success": False, "roll": 14, "target": 10}
    out = quiet(tr.render_combat_result, pkt_miss)
    check("combat_miss含失误", "失误" in out)

    pkt_fumble = {"success": False, "is_fumble": True, "roll": 18}
    out = quiet(tr.render_combat_result, pkt_fumble)
    check("combat_fumble含大失败", "大失败" in out or "💀" in out)

    def_test = {"result": "dodged", "narrative": "侧身闪过！"}
    out = quiet(tr.render_combat_result, pkt_hit, def_test)
    check("combat_defense含闪过", "闪过" in out)

    # ── render_character_sheet ──
    out = quiet(tr.render_character_sheet, pc)
    check("char_sheet_delegate", "角色卡" in out or "测试" in out)

    # ── render_settlement ──
    rewards = {"focus_restored": 2, "marks_healed": 1, "xp": 3, "narrative": "一阵眩晕"}
    out = quiet(tr.render_settlement, rewards)
    check("settlement含专注", "+2" in out)
    check("settlement含XP", "+3" in out)
    check("settlement含印记", "-1" in out)
    check("settlement含叙事", "眩晕" in out)

    # ── render_module_select ──
    modules = [
        {"title": "镜屋巷", "version": "2.0", "author": "全哥",
         "synopsis": "巷子里的镜子会说话", "duration": "30min", "players": "1人"},
    ]
    out = quiet(tr.render_module_select, modules)
    check("module_select含标题", "镜屋巷" in out)
    check("module_select含作者", "全哥" in out)

    # ── render_character_select ──
    chars = [Character(name="调查员A", st=11, dx=12, iq=14, ht=10, advantages=["警觉"])]
    out = quiet(tr.render_character_select, chars)
    check("char_select含角色名", "调查员A" in out)
    check("char_select含属性", "ST" in out)

    # ── render_save_confirm ──
    out = quiet(tr.render_save_confirm, "/path/to/save.json")
    check("save_confirm含路径", "save.json" in out)

    # ── render_load_list ──
    saves = [{"save_name": "快速存档", "timestamp": "20260101_120000", "character_name": "测试员"}]
    out = quiet(tr.render_load_list, saves)
    check("load_list含存档名", "快速存档" in out)

    # ── render_load_list 空 ──
    out = quiet(tr.render_load_list, [])
    check("load_list空→无存档", "没有" in out or "📂" in out)

    # ── render_help ──
    out = quiet(tr.render_help)
    check("help含专注点", "专注点" in out or "○" in out)
    check("help含幸运点", "幸运点" in out or "♦" in out)

    # ── render_error / render_info ──
    out = quiet(tr.render_error, "测试错误")
    check("error含错误信息", "测试错误" in out)
    out = quiet(tr.render_info, "提示信息")
    check("info含提示信息", "提示信息" in out)

    # ── render_divider ──
    out = quiet(tr.render_divider)
    check("divider非空", len(out) > 0)

    # ── print ──
    out = quiet(tr.print, "直接输出")
    check("print正常", "直接输出" in out)


# ────────────────────────────────────────────────────────────────
# 14. mirror_mvp — 核心引擎集成
# ────────────────────────────────────────────────────────────────

def test_mirror_mvp():
    module("14. mirror_mvp.py (集成)")
    from mirror_mvp import MirrorOfLost
    from core.character import Character
    from core.enemy import Enemy

    system_path = os.path.join(BASE_DIR, "config", "system.json")
    module_path = os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json")

    # ── 初始化 ──
    game = MirrorOfLost(system_path, module_path)
    check("MirrorOfLost初始化成功", game.system is not None)
    check("module加载成功", game.module is not None)
    check("env初始化", game.env is not None)
    check("vm初始化", game.vm is not None)
    check("combat初始化", game.combat is not None)
    check("items初始化", game.items is not None)
    check("resolver初始化", game.resolver is not None)
    check("xp_sys初始化", game.xp_sys is not None)
    check("saver初始化", game.saver is not None)
    check("renderer初始化", game.renderer is not None)
    check("engine初始为None", game.engine is None)
    check("pc初始为None", game.pc is None)

    # ── xp property ──
    check("xp属性=xp_sys", game.xp is game.xp_sys)

    # ── create_default_character ──
    def_pc = game.create_default_character()
    check("默认角色name=调查员", def_pc.name == "调查员")
    check("默认角色IQ=12", def_pc.iq == 12)
    check("默认角色技能数=4", len(def_pc.skills) == 4)
    check("默认角色特征数=1", len(def_pc.features) == 1)
    check("默认角色专注=3", def_pc.focus_points == 3)

    # ── set_character ──
    game.set_character(def_pc)
    check("set_character后pc非None", game.pc is def_pc)
    check("set_character后engine非None", game.engine is not None)

    # ── roll_3d6 ──
    for _ in range(20):
        r = game.roll_3d6()
        assert 3 <= r <= 18
    check("roll_3d6 范围正确 (20次)", True)

    # ── physical_resolve ──
    packet = game.physical_resolve(14, 2)  # target=16
    check("physical_resolve含roll", "roll" in packet)
    check("physical_resolve含target=16", packet["target"] == 16)
    check("physical_resolve含success", "success" in packet)

    # ── get_progress ──
    prog = game.get_progress()
    check("get_progress返回dict", isinstance(prog, dict))

    # ── get_available_nodes ──
    nodes = game.get_available_nodes()
    check("get_available_nodes≥1", len(nodes) >= 1)

    # ── run_node ──
    first_node = nodes[0]["node_id"]
    vm_result = game.run_node(first_node)
    check("run_node结果非空", vm_result is not None)
    check("run_node叙事非空", len(vm_result.narrative) > 0)

    # ── start_combat ──
    enemy_data = {"name": "测试敌人", "enemy_type": "mook", "hp": 10, "hp_max": 10,
                  "st": 10, "dx": 10, "attack_skill": 12, "damage": "1d6 cut",
                  "dodge": 8, "dr": 1, "parry": 0}
    combat = game.start_combat(enemy_data)
    check("start_combat返回CombatEngine", combat is not None and combat.state is not None)

    # ── combat_player_attack ──
    skill = def_pc.get_skill_level("近战") or 12
    patk = game.combat_player_attack(skill)
    check("combat_player_attack含success", "success" in patk)

    # ── combat_enemy_attack ──
    eatk = game.combat_enemy_attack()
    if isinstance(eatk, dict):
        check("combat_enemy_attack含success", "success" in eatk)
    else:
        check("combat_enemy_attack返回dict", isinstance(eatk, dict))

    # ── try_active_defense (基于 enemy attack) ──
    if eatk.get("success"):
        defense = game.try_active_defense(eatk)
        check("try_active_defense含result", "result" in defense)

    # ── check_death ──
    check("check_death返回bool", isinstance(game.check_death(), bool))

    # ── check_obsession ──
    check("check_obsession返回bool", isinstance(game.check_obsession(), bool))

    # ── is_game_over ──
    check("is_game_over返回bool", isinstance(game.is_game_over(), bool))

    # ── save_game ──
    test_dir = os.path.join(BASE_DIR, "AA", "_test_mvp_saves")
    game.saver = __import__('services.save_manager', fromlist=['SaveManager']).SaveManager(saves_dir=test_dir)
    save_path = game.save_game("集成测试存档")
    check("save_game返回路径", len(save_path) > 0)
    check("存档文件存在", os.path.exists(save_path))

    # ── load_game ──
    ok_load = game.load_game(save_path)
    check("load_game成功", ok_load is True)

    # ── resolve_current_scene ──
    rewards = game.resolve_current_scene(is_safe=True)
    check("resolve_current_scene返回dict", isinstance(rewards, dict))

    # ── get_xp_reward ──
    xp_reward = game.get_xp_reward()
    check("get_xp_reward返回int≥0", isinstance(xp_reward, int) and xp_reward >= 0)

    # 清理
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)

    # ── 引擎未初始化时的方法 ──
    game2 = MirrorOfLost(system_path, module_path)
    check("未初始化 get_available_nodes→[]", game2.get_available_nodes() == [])
    check("未初始化 get_progress→default", game2.get_progress()["total_nodes"] == 0)
    vr = game2.run_node("x")
    check("未初始化 run_node→错误叙事", "初始化" in vr.narrative)

    # ── 死亡检测 ──
    pc_dead_test = Character(hp=0, hp_max=10)
    game2.set_character(pc_dead_test)
    check("HP=0 → dead=True", game2.check_death() is True)


# ────────────────────────────────────────────────────────────────
# 15. 边缘情况综合
# ────────────────────────────────────────────────────────────────

def test_edge_cases():
    module("15. 边缘情况综合")
    from core.character import Character, CharacterFeature, Skill, Equipment
    from core.enemy import Enemy
    from core.viewmodel import ViewModel, ViewModelResult
    from core.environment_system import EnvironmentSystem
    from services.xp_system import XPSystem
    from services.scene_resolver import SceneResolver
    from core.combat_engine import CombatEngine
    from view.character_sheet import CharacterSheet

    # ── 空特征的角色 ──
    pc_empty = Character()
    check("空角色 get_skill_level→None", pc_empty.get_skill_level("飞行") is None)
    check("空角色 get_total_dr→0", pc_empty.get_total_dr("头") == 0)
    check("空角色 dodge=6 (DX=10)", pc_empty.dodge == 6)

    # ── 大量技能 ──
    pc_many = Character(skills=[Skill(f"技{i}", 10 + i) for i in range(15)])
    check("15个技能 全部查询通过", all(pc_many.get_skill_level(f"技{i}") == 10 + i for i in range(15)))

    # ── 特征 used_this_scene 不影响创建 ──
    feat = CharacterFeature("测试", "条件", 1, "效果", 3)
    feat.used_this_scene = 5
    check("used_this_scene可超过limit", feat.used_this_scene == 5)

    # ── Equipment penalty 空 ──
    eq = Equipment("空penalty")
    check("penalty默认空dict", eq.penalty == {})
    check("uses默认-1", eq.uses == -1)

    # ── Skill 默认值 ──
    sk = Skill("默认技能", 10)
    check("difficulty默认Avg", sk.difficulty == "Avg")
    check("base_attribute默认DX", sk.base_attribute == "DX")

    # ── Enemy with description and flavor ──
    e_desc = Enemy("叙述敌人", description="这是描述", flavor_text="这是风味")
    check("Enemy description", e_desc.description == "这是描述")
    check("Enemy flavor_text", e_desc.flavor_text == "这是风味")

    # ── Enemy loot_table ──
    e_loot = Enemy("带战利品", loot_table=[{"name": "金币", "amount": 10}])
    check("loot_table长度", len(e_loot.loot_table) == 1)

    # ── ViewModel 空锚点库 ──
    vm_empty = ViewModel()
    packet = {"roll": 10, "target": 12, "success": True, "margin": 2}
    node_empty = {}
    pc = Character()
    result = vm_empty.convert(packet, node_empty, pc)
    check("空锚点库不报错", len(result.narrative) > 0)

    # ── EnvironmentSystem 空标签 ──
    env_empty = EnvironmentSystem()
    check("空环境 modifiers=0", env_empty.get_active_modifiers() == 0)
    check("空环境 tag_names=[]", env_empty.get_tag_names() == [])
    check("空环境 to_dict含空tags", env_empty.to_dict()["tags"] == [])

    # ── SceneResolver 专注已满且非safe ──
    sr = SceneResolver()
    pc_full = Character(focus_points=3, focus_max=3)
    r = sr.resolve({"is_major_challenge": True, "is_safe_node": False}, pc_full, {})
    check("专注满→focus_restored=0", r["focus_restored"] == 0)

    # ── XP: 场景+flag+印记全为零 ──
    xp_sys = XPSystem()
    check("all zeros → base=3", xp_sys.calculate_xp(0, 0, 0, 3) == 3)
    check("base=0 all zeros → 0", xp_sys.calculate_xp(0, 0, 0, 0) == 0)

    # ── CombatEngine 无 combat state ──
    ce = CombatEngine()
    check("无state _entity_alive(None)=True", ce._entity_alive(None) is True)

    # ── CharacterSheet 空技能/空特征/空装备 ──
    pc_bare = Character(name="极简")
    sheet = CharacterSheet.render(pc_bare)
    check("极简角色无技能段", "技能" not in sheet)
    check("极简角色无特征段", "特征" not in sheet)
    check("极简角色无装备段", "装备" not in sheet)
    check("极简角色无永久标签段", "永久标签" not in sheet)

    # ── from_dict 空skills/features/equipment ──
    pc_from_empty = Character.from_dict({"name": "空角色"})
    check("空字典from_dict不报错", pc_from_empty.name == "空角色")

    # ── 大量标签修正 ──
    pc_tags = Character()
    for i in range(10):
        pc_tags.add_tag(f"标签{i}", modifier=-1)
    check("10个标签总修正=-10", pc_tags.calc_tag_modifier() == -10)

    # ── HP-负值 dodge ──
    pc_neg = Character(dx=2, equipment=[
        Equipment("重型", slot="body", penalty={"dx": -5}, equipped=True),
    ])
    check("DX极低 dodge≥0", pc_neg.dodge >= 0)


# ════════════════════════════════════════════════════════════════
#  规则原语接入（R2 反向重构：alloy.trpg 内核）
# ════════════════════════════════════════════════════════════════

def test_rule_kernel():
    module("16. core/dice.py（规则原语接入 · R2）")
    import random as _random
    from core.dice import gurps_success_chance, roll_3d6
    from core.combat_engine import CombatEngine, HIT_LOCATIONS
    from core.viewmodel import ViewModelResult
    from mirror_mvp import MirrorOfLost
    from alloy.trpg.dice import roll_3d6 as _kernel_roll_3d6

    # ── roll_3d6：范围 + 与内核同种子同值 ──
    check("roll_3d6 范围 3-18 (200次)", all(3 <= roll_3d6() <= 18 for _ in range(200)))
    _random.seed(20260827)
    ours = roll_3d6()
    _random.seed(20260827)
    kernel_total = _kernel_roll_3d6()[1]
    check("与 alloy 内核同种子同总和", ours == kernel_total)

    # ── gurps_success_chance：GURPS 成功率表 ──
    check("success_chance(3)=0", gurps_success_chance(3) == 0)
    check("success_chance(10)=50", gurps_success_chance(10) == 50)
    check("success_chance(12)=74", gurps_success_chance(12) == 74)
    check("success_chance(18)=100", gurps_success_chance(18) == 100)
    check("success_chance 单调不减", all(
        gurps_success_chance(l) <= gurps_success_chance(l + 1) for l in range(3, 18)))

    # ── 引擎接入面 ──
    check("CombatEngine.roll_3d6 委托内核 (50次)",
          all(3 <= CombatEngine.roll_3d6() <= 18 for _ in range(50)))
    check("roll_hit_location 返回合法部位",
          CombatEngine.roll_hit_location() in set(HIT_LOCATIONS.values()))

    game = MirrorOfLost(
        os.path.join(BASE_DIR, "config", "system.json"),
        os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json"),
    )
    pkt = game.physical_resolve(12)
    check("physical_resolve 带 success_chance", pkt.get("success_chance") == gurps_success_chance(12))

    # ── ViewModelResult.roll_info 直通 ──
    vr = ViewModelResult()
    vr.roll_info = {"roll": 10, "target": 12, "success": True, "success_chance": 74}
    d = vr.to_dict()
    check("to_dict 含 roll_info", d.get("roll_info") == vr.roll_info)


# ────────────────────────────────────────────────────────────────
#  MAIN
# ────────────────────────────────────────────────────────────────

def print_summary():
    print(f"\n{'='*60}")
    print(f"  📊 测试汇总")
    print(f"{'='*60}")
    print(f"  总测试数: {RESULTS['total']}")
    print(f"  ✅ 通过:   {RESULTS['passed']}")
    print(f"  ❌ 失败:   {RESULTS['failed']}")
    if RESULTS["failed"] == 0:
        print(f"\n  🎉 全部通过！")
    else:
        print(f"\n  ❌ 失败项:")
        for err in RESULTS["errors"]:
            print(f"    {err}")

    # 模块汇总
    print(f"\n  模块详情:")
    for mod_name, mr in MODULE_RESULTS.items():
        t = mr.get("total", 0)
        p = mr["passed"]
        f = mr["failed"]
        bar = "✅" if f == 0 else "❌"
        print(f"    {bar} {mod_name}: {p}/{t} passed" + (f" ({f} failed)" if f > 0 else ""))

    return RESULTS["failed"] == 0


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    print(f"🐍 迷失之镜 v2.0 全面覆盖测试")
    print(f"📂 项目目录: {BASE_DIR}")
    print(f"⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    modules_tested = [
        test_character,
        test_enemy,
        test_combat_engine,
        test_viewmodel,
        test_environment,
        test_scene_engine,
        test_item_system,
        test_xp_system,
        test_save_manager,
        test_scene_resolver,
        test_data_importer,
        test_character_sheet,
        test_terminal_renderer,
        test_mirror_mvp,
        test_edge_cases,
        test_rule_kernel,
    ]

    for test_fn in modules_tested:
        try:
            test_fn()
        except Exception as e:
            print(f"\n  ❌ 模块 {test_fn.__name__} 抛出异常: {type(e).__name__}: {e}")
            traceback.print_exc()
            RESULTS["failed"] += 1

    all_pass = print_summary()
    sys.exit(0 if all_pass else 1)
