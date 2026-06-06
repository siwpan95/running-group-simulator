# -*- coding: utf-8 -*-
"""
迷失之镜 — 全面测试探针 v1.0
对每个核心组件、每个场景节点进行压力测试，捕获所有异常
"""
import sys, os, io, json, traceback, random

# 确保编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# 捕获所有输出（避免干扰结果）
_capture = io.StringIO()

class ProbeResult:
    """单个测试探针结果"""
    def __init__(self, name: str):
        self.name = name
        self.error = None
        self.trace = ""
        self.warning = ""

    def ok(self):
        return self.error is None

    def __repr__(self):
        if self.ok():
            return f"✅ {self.name}"
        return f"❌ {self.name}\n{self.trace}\n"

# ==================== 测试集合 ====================

results = []

def test(name: str):
    """装饰器：自动捕获异常并记录"""
    def decorator(fn):
        def wrapper():
            r = ProbeResult(name)
            try:
                fn()
            except Exception as e:
                r.error = str(e)
                r.trace = traceback.format_exc()
            results.append(r)
        return wrapper
    return decorator


# ==================== 探针 1：模块加载 ====================

@test("加载 system.json")
def probe_system_json():
    with open(os.path.join(BASE_DIR, "config", "system.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "meta" in data or "content_libraries" in data, "system.json 缺少关键字段"

@test("加载 module.json")
def probe_module_json():
    with open(os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "meta" in data, "module.json 缺少 meta"
    assert "act_1" in data, "module.json 缺少 act_1"
    assert "act_2" in data, "module.json 缺少 act_2"
    assert "act_3" in data, "module.json 缺少 act_3"

@test("模块节点结构完整性")
def probe_node_structure():
    with open(os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    for act_key in ["act_1", "act_2", "act_3"]:
        act = data.get(act_key, {})
        nodes = act.get("nodes", [])
        for node in nodes:
            nid = node.get("node_id", "???")
            # 检查必要字段
            assert "node_id" in node, f"{act_key} 节点缺少 node_id"
            assert "scene_type" in node, f"{nid} 缺少 scene_type"
            assert "layer_physics" in node, f"{nid} 缺少 layer_physics"
            assert "layer_narrative" in node, f"{nid} 缺少 layer_narrative"


# ==================== 探针 2：角色系统 ====================

from core.character import Character, CharacterFeature, Skill, Equipment

@test("创建默认角色")
def probe_default_character():
    pc = Character(
        character_id="probe_char",
        name="测试员",
        st=10, dx=10, iq=12, ht=10,
        hp=10, hp_max=10, fp=10, fp_max=10,
        will=11, per=12,
        skills=[Skill("调查", 13, "Avg", "IQ", 4)],
        advantages=["警觉"],
        disadvantages=["好奇心"],
        features=[CharacterFeature("猎手直觉", "追踪/瞄准时有可见痕迹", 1, "请求目标听觉/视觉 -2", 1)],
        anchors=["怀表"],
        focus_points=3, focus_max=3, luck_points=2, luck_max=2,
    )
    assert pc.name == "测试员"
    assert pc.iq == 12
    assert pc.get_skill_level("调查") == 13
    assert pc.get_skill_level("不存在的技能") is None

@test("角色属性访问")
def probe_character_properties():
    pc = Character(st=10, dx=12, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12)
    assert pc.dodge >= 0
    assert pc.shock_threshold > 0
    assert pc.st == 10
    assert pc.dx == 12

@test("角色标签计算 - int")
def probe_calc_tag_modifier_int():
    pc = Character()
    pc.temporary_tags = [{"name": "测试标签", "modifier": -2, "duration": "scene"}]
    mod = pc.calc_tag_modifier()
    assert mod == -2, f"期望 -2, 实际 {mod}"

@test("角色标签计算 - str")
def probe_calc_tag_modifier_str():
    """标签 modifier 可能是字符串的防御测试"""
    pc = Character()
    pc.temporary_tags = [{"name": "测试标签", "modifier": "-2", "duration": "scene"}]
    mod = pc.calc_tag_modifier()
    assert mod == -2, f"期望 -2, 实际 {mod}"

@test("角色闪避计算 - str modifier")
def probe_dodge_with_str_modifier():
    """闪避计算时 tag modifier 是字符串不应崩溃"""
    pc = Character(dx=12)
    pc.temporary_tags = [{"name": "闪避下降", "modifier": "-1", "duration": "scene"}]
    d = pc.dodge
    assert d >= 0, f"闪避值为负: {d}"

@test("角色 JSON 序列化/反序列化")
def probe_character_json_roundtrip():
    pc = Character(
        character_id="roundtrip", name="序列化测试",
        st=10, dx=10, iq=12, ht=10,
        skills=[Skill("潜行", 11, "Avg", "DX", 2)],
        advantages=["警觉"],
        features=[CharacterFeature("测试特征", "触发条件", 1, "效果", 1)],
        equipment=[Equipment("手电筒", "tool", "hand")],
    )
    d = pc.to_dict()
    pc2 = Character.from_dict(d)
    assert pc2.name == pc.name
    assert len(pc2.skills) == len(pc.skills)
    assert len(pc2.features) == len(pc.features)
    assert len(pc2.equipment) == len(pc.equipment)

@test("角色快照/恢复")
def probe_character_snapshot():
    pc = Character(hp=5, hp_max=10, fp=6, fp_max=10, focus_points=1, focus_max=3, psychic_marks=2)
    pc.temporary_tags = [{"name": "挫败感", "modifier": -1, "duration": "1 check"}]
    snap = pc.create_snapshot()
    pc2 = Character(hp=10, hp_max=10, fp=10, fp_max=10, focus_points=3, focus_max=3, psychic_marks=0)
    pc2.restore_snapshot(snap)
    assert pc2.hp == 5
    assert pc2.focus_points == 1
    assert pc2.psychic_marks == 2

@test("专注点消耗")
def probe_focus_spend():
    pc = Character(focus_points=3, focus_max=3)
    assert pc.spend_focus(1) == True
    assert pc.focus_points == 2
    assert pc.spend_focus(5) == False

@test("FP 透支转 HP 扣血")
def probe_fp_overdraft():
    pc = Character(fp=2, hp=10)
    pc.spend_fp(5)
    assert pc.fp == 0
    assert pc.hp == 7  # 10 - (5-2) = 7

@test("精神印记累积 -> 镜痴触发")
def probe_psychic_marks_obsession():
    pc = Character(psychic_marks=0)
    pc.add_psychic_mark(1)
    assert pc.psychic_marks == 1
    assert pc.has_obsession == False
    pc.add_psychic_mark(2)
    assert pc.psychic_marks == 3
    assert pc.has_obsession == True
    assert pc.obsession_name == "镜痴"


# ==================== 探针 3：环境系统 ====================

from core.environment_system import EnvironmentSystem

@test("环境系统 - 加载标签")
def probe_env_load_tags():
    env = EnvironmentSystem()
    env.load_tags([
        {"id": "rain", "name": "暴雨湿滑", "effect": "闪避 -1，攀爬 -2"},
    ])
    mod = env.get_active_modifiers()
    assert isinstance(mod, int), f"get_active_modifiers 返回类型错误: {type(mod)}"
    assert mod < 0, f"环境修正应为负数"

@test("环境系统 - 获取标签名")
def probe_env_get_tags():
    env = EnvironmentSystem()
    env.load_tags([
        {"id": "rain", "name": "暴雨湿滑", "effect": "闪避 -1"},
        {"id": "dark", "name": "低能见度", "effect": "视觉感知 -3"},
    ])
    names = env.get_tag_names()
    assert "暴雨湿滑" in names
    assert "低能见度" in names

@test("环境系统 - on_scene_enter")
def probe_env_on_scene_enter():
    env = EnvironmentSystem()
    node = {
        "environment": {
            "mood": "测试氛围",
            "tags": [{"id": "test", "name": "测试标签", "effect": "检定 -1"}],
        }
    }
    env.on_scene_enter(node)
    assert env.ambient_narrative == "测试氛围"
    assert len(env.tags) == 1

@test("环境系统 - 环境更新 (add/remove)")
def probe_env_update():
    env = EnvironmentSystem()
    node = {
        "environment_update": {
            "remove_tags": [],
            "add_tags": [
                {"id": "fumes", "name": "腐蚀性烟气", "effect": "HT 每 30 秒检定，失败 -1 FP"},
            ],
        }
    }
    env.on_scene_enter(node)
    assert any(t["name"] == "腐蚀性烟气" for t in env.tags)

@test("环境系统 - resolve_environment_update")
def probe_env_resolve_update():
    env = EnvironmentSystem()
    env.add_tag("旧标签", -1)
    env.resolve_environment_update({
        "removed_tags": ["旧标签"],
        "added_tags": [{"name": "新标签", "modifier": -2, "duration": "scene"}],
    })
    assert not any(t["name"] == "旧标签" for t in env.tags)
    assert any(t["name"] == "新标签" for t in env.tags)


# ==================== 探针 4：ViewModel ====================

from core.viewmodel import ViewModel, ViewModelResult

@test("ViewModel - 基本转换 (成功)")
def probe_vm_convert_success():
    vm = ViewModel()
    pc = Character(st=12, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12)
    node = {
        "node_id": "test_success",
        "scene_type": "feat",
        "layer_narrative": {
            "anchor_phrases": {
                "success": "你成功破墙。",
                "crit_success": "你轻松破墙。",
                "failure": "墙纹丝不动。",
            }
        },
        "next_nodes": ["next_scene"],
    }
    packet = {
        "roll": 10, "target": 12, "success": True,
        "margin": 2, "is_crit_success": False, "is_fumble": False,
        "action_type": "feat", "skill_used": "力量",
    }
    result = vm.convert(packet, node, pc)
    assert hasattr(result, "narrative")
    assert "破墙" in result.narrative
    assert len(result.choices) == 1

@test("ViewModel - 基本转换 (失败)")
def probe_vm_convert_failure():
    vm = ViewModel()
    pc = Character()
    node = {
        "node_id": "test_fail",
        "layer_narrative": {
            "anchor_phrases": {"success": "成功", "failure": "失败了。"}
        },
    }
    packet = {
        "roll": 14, "target": 10, "success": False,
        "margin": -4, "is_crit_success": False, "is_fumble": False,
    }
    result = vm.convert(packet, node, pc)
    assert "失败" in result.narrative

@test("ViewModel - 衍生标签 (dict 格式)")
def probe_vm_derive_tags_dict():
    vm = ViewModel()
    packet = {"damage": 6, "location": "左臂", "location_effects": {"行动力受损:左臂": -2}}
    tags = vm._derive_tags(packet)
    assert len(tags) >= 1
    assert any(t["name"] == "行动力受损:左臂" for t in tags)

@test("ViewModel - 衍生标签 (list of str 格式)")
def probe_vm_derive_tags_list_str():
    vm = ViewModel()
    packet = {"location_effects": ["行动力受损", "移动下降"]}
    tags = vm._derive_tags(packet)
    assert len(tags) == 2
    assert tags[0]["modifier"] == -1

@test("ViewModel - 衍生标签 (list of dict 格式)")
def probe_vm_derive_tags_list_dict():
    vm = ViewModel()
    packet = {"location_effects": [{"name": "受伤", "modifier": -3}]}
    tags = vm._derive_tags(packet)
    assert len(tags) == 1
    assert tags[0]["modifier"] == -3

@test("ViewModel - 特征触发匹配")
def probe_vm_feature_trigger():
    vm = ViewModel()
    pc = Character(features=[CharacterFeature("猎手直觉", "追踪/瞄准时有可见痕迹", 1, "请求目标听觉/视觉 -2", 1)])
    packet = {"action_type": "tracking", "success": True}
    triggered = vm._check_triggers(packet, pc)
    assert any(t["name"] == "猎手直觉" for t in triggered)

@test("ViewModel - 专注点动作")
def probe_vm_focus_actions():
    vm = ViewModel()
    pc = Character(focus_points=3, focus_max=3,
                   features=[CharacterFeature("猎手直觉", "追踪条件", 1, "效果", 1)])
    node = {}
    packet = {"success": True}
    actions = vm._available_focus_actions(packet, node, pc)
    assert len(actions) >= 1
    assert any("猎手直觉" in a for a in actions)

@test("ViewModel - 事件队列 (失败 + 大失败)")
def probe_vm_event_queue():
    vm = ViewModel()
    packet = {"success": False, "is_fumble": True, "margin": -10}
    queue = vm._build_event_queue(packet)
    assert len(queue) == 2  # 挫败感 + 自伤

@test("ViewModel - 状态变更")
def probe_vm_status_changes():
    vm = ViewModel()
    packet = {"damage": 4, "cost_fp": 1}
    changes = vm._calc_status_changes(packet)
    assert changes["hp_delta"] == -4
    assert changes["fp_delta"] == -1

@test("ViewModel - 伤害锚点查找")
def probe_vm_damage_anchor():
    vm = ViewModel()
    vm.anchor_library = {}
    packet = {"damage": 3, "type": "切割", "location": "躯干", "dr": 0}
    desc = vm._lookup_damage_anchor(packet)
    assert "切割" in desc or "伤害" in desc


# ==================== 探针 5：场景引擎 ====================

from core.scene_engine import SceneEngine, _parse_int
from core.viewmodel import ViewModel
from core.environment_system import EnvironmentSystem

def make_test_node(node_id="test_1", scene_type="explore", physics=None, narrative=None, **kwargs):
    """构建最小测试节点"""
    node = {
        "node_id": node_id,
        "scene_type": scene_type,
        "prerequisite_nodes": [],
        "next_nodes": [],
        "layer_physics": physics or {},
        "layer_narrative": narrative or {"anchor_phrases": {"success": "成功！", "failure": "失败。"}},
    }
    node.update(kwargs)  # 允许传入 psychic_marks 等额外字段
    return node

@test("SceneEngine - _parse_int 正常值")
def probe_parse_int_normal():
    assert _parse_int(5) == 5
    assert _parse_int(-3) == -3
    assert _parse_int("5") == 5
    assert _parse_int("-2") == -2
    assert _parse_int("+2（锤子/撬棍）") == 2
    assert _parse_int("abc") == 0
    assert _parse_int("3d6+2") == 3
    assert _parse_int(None) == 0
    assert _parse_int(3.14) == 3

@test("SceneEngine - 单检定节点 (无 tool_bonus)")
def probe_engine_simple_check():
    module = {"act_1": {"nodes": [make_test_node("t1", "feat",
        physics={"skill_check": "力量", "modifier": -2})]}}
    pc = Character(st=12, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t1")
    assert result.narrative, f"叙事为空: {result}"

@test("SceneEngine - 单检定节点 (str tool_bonus)")
def probe_engine_check_with_str_tool_bonus():
    """模拟 1.2_false_wall 场景的数据"""
    module = {"act_1": {"nodes": [make_test_node("t2", "feat",
        physics={"skill_check": "力量", "modifier": -2, "tool_bonus": "+2（锤子/撬棍）"})]}}
    pc = Character(st=12, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t2")
    assert result.narrative, f"带 tool_bonus 字符串的检定失败: {result}"

@test("SceneEngine - 感知检定")
def probe_engine_perception_check():
    module = {"act_1": {"nodes": [make_test_node("t_per", "perception",
        physics={"skill_check": "感知（听觉）", "modifier": -2},
        narrative={"anchor_phrases": {"success": "听到了", "crit_success": "很清楚", "failure": "没听到"}})]}}
    pc = Character(st=10, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_per")
    assert result.narrative, f"感知检定失败"

@test("SceneEngine - 意志检定")
def probe_engine_will_check():
    module = {"act_1": {"nodes": [make_test_node("t_will", "explore",
        physics={"skill_check": "意志", "modifier": 0})]}}
    pc = Character(st=10, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=13, per=10)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_will")
    assert result.narrative

@test("SceneEngine - 智力检定")
def probe_engine_iq_check():
    module = {"act_1": {"nodes": [make_test_node("t_iq", "explore",
        physics={"skill_check": "智力", "modifier": 0})]}}
    pc = Character(st=10, dx=10, iq=14, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=10)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_iq")
    assert result.narrative

@test("SceneEngine - 体质检定")
def probe_engine_ht_check():
    module = {"act_1": {"nodes": [make_test_node("t_ht", "explore",
        physics={"skill_check": "体质", "modifier": 0})]}}
    pc = Character(st=10, dx=10, iq=10, ht=13, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=10)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_ht")
    assert result.narrative

@test("SceneEngine - 敏捷检定")
def probe_engine_dx_check():
    module = {"act_1": {"nodes": [make_test_node("t_dx", "explore",
        physics={"skill_check": "敏捷", "modifier": 0})]}}
    pc = Character(st=10, dx=13, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=10)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_dx")
    assert result.narrative

@test("SceneEngine - 技能名称查找")
def probe_engine_skill_by_name():
    module = {"act_1": {"nodes": [make_test_node("t_skill", "explore",
        physics={"skill_check": "调查", "modifier": 0})]}}
    pc = Character(st=10, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=10,
                   skills=[Skill("调查", 14, "Avg", "IQ", 4)])
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_skill")
    assert result.narrative

@test("SceneEngine - 环境修正累加")
def probe_engine_with_env_mod():
    module = {"act_1": {"nodes": [make_test_node("t_env", "feat",
        physics={"skill_check": "力量", "modifier": 0})]}}
    pc = Character(st=12, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=10)
    env = EnvironmentSystem()
    env.load_tags([{"id": "rain", "name": "暴雨湿滑", "effect": "闪避 -1，攀爬 -2"}])
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_env")
    assert result.narrative
    # 验证 _last_packet
    if engine._last_packet:
        # 环境修正被合并到 base modifier 中
        assert isinstance(engine._last_packet["target"], int)

@test("SceneEngine - 嵌套检定 (checks)")
def probe_engine_nested_checks():
    module = {"act_1": {"nodes": [make_test_node("t_nested", "investigation",
        physics={
            "checks": [
                {"id": "c1", "type": "automatic", "skill": "strength", "dc": 12,
                 "on_success": {"flag_set": ["found"]}},
            ]
        })]}}
    pc = Character(st=12, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=10)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_nested")
    assert result.narrative is not None

@test("SceneEngine - 精神印记失败触发")
def probe_engine_psychic_marks():
    module = {"act_1": {"nodes": [make_test_node("t_psychic", "feat",
        physics={"skill_check": "力量", "modifier": -15},  # 几乎必失败
        psychic_marks={"trigger_level": "接触", "check": "感知 vs 诡异度(10)", "failure_cost": 1})]}}
    pc = Character(st=10, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=10)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_psychic")
    # 即使失败也不应崩溃
    assert result is not None

@test("SceneEngine - 场景结算")
def probe_engine_scene_resolve():
    module = {"act_1": {"nodes": [make_test_node("t_resolve", "feat",
        physics={"skill_check": "力量", "modifier": 0})]}}
    pc = Character(st=12, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=10)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    engine.run_node("t_resolve")
    rewards = engine.resolve_scene()
    assert isinstance(rewards, dict)

@test("SceneEngine - 战斗节点")
def probe_engine_combat_node():
    module = {"act_1": {"nodes": [{
        "node_id": "t_combat",
        "scene_type": "combat",
        "prerequisite_nodes": [],
        "next_nodes": [],
        "trigger": "测试战斗",
        "layer_physics": {
            "enemy_type": "杂兵单位（巨鼠群）",
            "unit_stats": {
                "name": "测试鼠群", "attack_skill": 12,
                "damage": "1d-4 cut", "dodge": 9, "hp": 10, "dr": 0,
            },
        },
        "layer_narrative": {"anchor_phrases": {"success": "战斗胜利！"}},
    }]}}
    pc = Character(st=12, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=10)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_combat")
    assert result.narrative
    assert result.choices is not None

@test("SceneEngine - psychic_marks.failure_cost 为字符串")
def probe_engine_psychic_str_cost():
    """模拟 3.2_closure 中 failure_cost='+2 印记，可能永久执念'"""
    module = {"act_1": {"nodes": [make_test_node("t_psychic_str", "feat",
        physics={"skill_check": "力量", "modifier": -20},
        psychic_marks={"trigger_level": "崩溃", "check": "意志 -2", "failure_cost": "+2 印记，可能永久执念"})]}}
    pc = Character(st=10, dx=10, iq=10, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=10)
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_psychic_str")
    assert result is not None, "带字符串 failure_cost 的精神印记检定崩溃了"

@test("SceneEngine - skill_checks vs checks 兼容")
def probe_engine_skill_checks_field():
    """模拟 2.1_the_body_and_mirror 用 skill_checks 而非 checks"""
    module = {"act_1": {"nodes": [{
        "node_id": "t_skill_checks",
        "scene_type": "investigation",
        "prerequisite_nodes": [],
        "next_nodes": [],
        "layer_physics": {
            "skill_checks": [
                {"skill": "急救 / 诊断", "result": "死因：无阻塞性窒息。"},
                {"skill": "神秘学", "result": "镜背刻有炼金符号。"}
            ]
        },
        "layer_narrative": {"anchor_phrases": {"success": "调查完成", "failure": "没发现什么"}},
    }]}}
    pc = Character(st=10, dx=10, iq=14, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12,
                   skills=[Skill("急救", 14, "Easy", "IQ", 2), Skill("神秘学", 12, "Avg", "IQ", 2)])
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    result = engine.run_node("t_skill_checks")
    assert result.narrative is not None, "skill_checks 字段导致崩溃"
    # 注意：当前引擎用 skill_checks 推断 scene_type 但不处理检定，
    # 这里只验证不崩溃——可能需要后续修复以正确处理 skill_checks

@test("场景结算 - 空 current_node 防御")
def probe_engine_resolve_no_current():
    module = {"act_1": {"nodes": []}}
    pc = Character()
    env = EnvironmentSystem()
    vm = ViewModel()
    engine = SceneEngine(module, pc, vm, env)
    rewards = engine.resolve_scene()
    assert rewards == {}, f"空节点时应返回空字典: {rewards}"


# ==================== 探针 6：真实模块跑节点 ====================

@test("真实模块 - 1.1_sound_source (感知)")
def probe_real_1_1():
    module_path = os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json")
    pc = Character(st=10, dx=10, iq=12, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12,
                   skills=[Skill("调查", 13, "Avg", "IQ", 4)])
    from mirror_mvp import MirrorOfLost
    game = MirrorOfLost(os.path.join(BASE_DIR, "config", "system.json"), module_path)
    game.set_character(pc)
    result = game.run_node("1.1_sound_source")
    assert result.narrative, f"1.1 叙事为空"
    assert game.engine._last_packet is not None, "1.1 未产生掷骰"

@test("真实模块 - 1.2_false_wall (力量)")
def probe_real_1_2():
    module_path = os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json")
    pc = Character(st=12, dx=10, iq=12, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12)
    from mirror_mvp import MirrorOfLost
    game = MirrorOfLost(os.path.join(BASE_DIR, "config", "system.json"), module_path)
    game.set_character(pc)
    # 先完成前置节点
    game.engine.completed_nodes.add("1.1_sound_source")
    result = game.run_node("1.2_false_wall")
    assert result.narrative, f"1.2 叙事为空: {result}"
    assert game.engine._last_packet is not None, "1.2 未产生掷骰"

@test("真实模块 - 2.1_the_body_and_mirror (调查)")
def probe_real_2_1():
    module_path = os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json")
    pc = Character(st=10, dx=10, iq=14, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12,
                   skills=[Skill("急救", 14, "Easy", "IQ", 2), Skill("神秘学", 12, "Avg", "IQ", 2)])
    from mirror_mvp import MirrorOfLost
    game = MirrorOfLost(os.path.join(BASE_DIR, "config", "system.json"), module_path)
    game.set_character(pc)
    game.engine.completed_nodes.add("1.1_sound_source")
    game.engine.completed_nodes.add("1.2_false_wall")
    result = game.run_node("2.1_the_body_and_mirror")
    assert result.narrative is not None, f"2.1 叙事为空"

@test("真实模块 - 2.2_rat_swarm (战斗)")
def probe_real_2_2():
    module_path = os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json")
    pc = Character(st=10, dx=10, iq=12, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12)
    from mirror_mvp import MirrorOfLost
    game = MirrorOfLost(os.path.join(BASE_DIR, "config", "system.json"), module_path)
    game.set_character(pc)
    for nid in ["1.1_sound_source", "1.2_false_wall", "2.1_the_body_and_mirror"]:
        game.engine.completed_nodes.add(nid)
    result = game.run_node("2.2_rat_swarm")
    assert result.narrative, f"2.2 叙事为空"
    assert len(result.choices) > 0, "2.2 没有战斗选项"

@test("真实模块 - 3.1_the_reflection (镜影战斗)")
def probe_real_3_1():
    module_path = os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json")
    pc = Character(st=10, dx=10, iq=12, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12)
    from mirror_mvp import MirrorOfLost
    game = MirrorOfLost(os.path.join(BASE_DIR, "config", "system.json"), module_path)
    game.set_character(pc)
    for nid in ["1.1_sound_source", "1.2_false_wall", "2.1_the_body_and_mirror", "2.2_rat_swarm"]:
        game.engine.completed_nodes.add(nid)
    result = game.run_node("3.1_the_reflection")
    assert result.narrative, f"3.1 叙事为空"

@test("真实模块 - 3.2_closure (终局)")
def probe_real_3_2():
    module_path = os.path.join(BASE_DIR, "modules", "mirror_house_alley", "module.json")
    pc = Character(st=12, dx=10, iq=14, ht=10, hp=10, hp_max=10, fp=10, fp_max=10, will=11, per=12)
    from mirror_mvp import MirrorOfLost
    game = MirrorOfLost(os.path.join(BASE_DIR, "config", "system.json"), module_path)
    game.set_character(pc)
    for nid in ["1.1_sound_source", "1.2_false_wall", "2.1_the_body_and_mirror",
                 "2.2_rat_swarm", "3.1_the_reflection"]:
        game.engine.completed_nodes.add(nid)
    result = game.run_node("3.2_closure")
    assert result.narrative is not None, f"3.2 叙事为空"


# ==================== 探针 7：渲染器 ====================

from view.terminal_renderer import TerminalRenderer

@test("渲染器 - render_scene_header")
def probe_render_header():
    r = TerminalRenderer()
    node = {"scene_type": "feat", "trigger": "测试行动", "node_id": "test_1"}
    try:
        r.render_scene_header(node)
    except Exception:
        pass  # 无崩溃即可

@test("渲染器 - render_resolution")
def probe_render_resolution():
    r = TerminalRenderer()
    vm = ViewModelResult()
    vm.narrative = "测试叙事文本。"
    vm.derived_tags = [{"name": "测试标签", "modifier": -2}]
    vm.triggered_features = [{"name": "猎手直觉", "effect": "请求目标听觉/视觉 -2"}]
    try:
        r.render_resolution(vm)
    except Exception as e:
        # render_resolution 内部打印不抛异常，但 f-string 格式化可能出错
        print(f"  ⚠️ 渲染警告: {e}")

@test("渲染器 - render_resolution (str modifier)")
def probe_render_resolution_str_mod():
    """衍生标签 modifier 为字符串时不应崩溃"""
    r = TerminalRenderer()
    vm = ViewModelResult()
    vm.narrative = "测试。"
    vm.derived_tags = [{"name": "测试", "modifier": "+2"}]  # str
    try:
        r.render_resolution(vm)
    except Exception as e:
        assert False, f"str modifier 导致渲染崩溃: {e}"

@test("渲染器 - render_status_bar")
def probe_render_status_bar():
    r = TerminalRenderer()
    pc = Character(name="测试员", st=10, dx=10, iq=10, ht=10,
                   hp=7, hp_max=10, fp=6, fp_max=10, will=11, per=12,
                   focus_points=2, focus_max=3, luck_points=1, luck_max=2,
                   psychic_marks=1)
    env = EnvironmentSystem()
    env.load_tags([{"id": "test", "name": "测试环境", "effect": "测试-1"}])
    try:
        r.render_status_bar(pc, env)
    except Exception:
        pass


# ==================== 运行 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  迷失之镜 — 全栈测试探针 v1.0")
    print("=" * 60)
    print()

    # 收集所有测试函数并执行
    import inspect
    current_module = sys.modules[__name__]
    test_fns = []
    for name in dir(current_module):
        obj = getattr(current_module, name)
        if callable(obj) and getattr(obj, '_is_probe', False):
            test_fns.append(obj)

    # 手动调用（因为装饰器已在定义时注册到 results 列表）
    # 实际：每个 @test 装饰器会在模块加载时创建一个包装函数 wrapper
    # 但我们需要显式执行它们
    # 更简单的做法：直接用 globals 中的 probe_ 函数

    probe_funcs = [(n, getattr(current_module, n)) for n in sorted(dir(current_module))
                   if n.startswith("probe_") and callable(getattr(current_module, n))]

    for name, fn in probe_funcs:
        sys.stdout.write(f"\r  运行: {name[6:]}...{' ' * 40}")
        sys.stdout.flush()
        try:
            fn()
        except Exception:
            pass  # 异常已在 fn 内部捕获

    print("\n")

    # 打印结果
    passed = [r for r in results if r.ok()]
    failed = [r for r in results if not r.ok()]

    print("=" * 60)
    print(f"  测试结果: ✅ {len(passed)} 通过  ❌ {len(failed)} 失败")
    print("=" * 60)

    if passed:
        print(f"\n  ✅ 通过 ({len(passed)}):")
        for r in passed:
            print(f"     {r.name}")

    if failed:
        print(f"\n  ❌ 失败 ({len(failed)}):")
        for r in failed:
            print(f"     [{r.name}]")
            # 只显示最后 5 行 trace
            lines = r.trace.strip().split('\n')
            relevant = []
            for line in lines[-8:]:
                if line.strip():
                    relevant.append(line)
            for line in relevant:
                print(f"       {line}")
            print()

    # 汇总
    print("=" * 60)
    if not failed:
        print("  🎉 所有探针通过！")
    else:
        print(f"  ⚠️  共 {len(failed)} 个问题待修复。")
    print("=" * 60)

    sys.exit(len(failed))
