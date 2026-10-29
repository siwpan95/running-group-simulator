# -*- coding: utf-8 -*-
"""
迷失之镜 — 数据驱动场景引擎 (Model 层 · 阶段 1)
读取 module.json nodes[] → 解析 scene_type → 驱动检定 → 调用 ViewModel → 状态变更
"""
import json
import os
import re
from typing import Dict, List, Optional, Tuple, Any
from core.character import Character
from core.dice import gurps_success_chance, roll_3d6
from core.environment_system import EnvironmentSystem
from core.viewmodel import ViewModel, ViewModelResult
from core.combat_engine import CombatEngine
from core.enemy import Enemy
from core.rules import get_profile
from services.scene_resolver import SceneResolver


def _parse_int(value, default=0):
    """从 JSON 值中提取整数，兼容 '+2（锤子/撬棍）' 等含注释的字符串"""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        m = re.match(r'([+-]?\d+)', value.strip())
        if m:
            return int(m.group(1))
    return default


def _parse_dice_amount(value, default=1):
    """解析伤害/损失数额：int 或 'XdY' / 'XdY±Z' 骰子表达式。

    另支持 CoC 常用的双值写法 'a/b'（如 '0/1d6'、'1/1d6'、'1d6/1d20'）：
    取两种情形中较重的一个（worst case）。此前 '0/1d6' 会被正则在起始处
    匹配成 0，导致这类 SAN 损失整条失效。
    """
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, str):
        text = value.strip()
        if "/" in text:
            parts = [p for p in text.split("/") if p.strip()]
            vals = [_parse_dice_amount(p, 0) for p in parts]
            return max(vals) if vals else default
        m = re.match(r'(\d+)?d(\d+)([+-]\d+)?', text)
        if m:
            import random
            count = int(m.group(1) or 1)
            sides = int(m.group(2))
            mod = int(m.group(3) or 0)
            return max(0, sum(random.randint(1, sides) for _ in range(count)) + mod)
        m2 = re.match(r'([+-]?\d+)', text)
        if m2:
            return max(0, int(m2.group(1)))
    return default


def _act_num(key: str) -> int:
    """'act_3' → 3（用于幕的排序，act_10 排在 act_9 之后）。"""
    m = re.search(r'(\d+)$', key or "")
    return int(m.group(1)) if m else 999


class SceneEngine:
    """
    数据驱动场景引擎
    核心原则：模组 = JSON 数据包，引擎解释 JSON 就能跑任何模组
    """

    def __init__(self, module_data: Dict, pc: Character, view_model: ViewModel,
                 env_system: EnvironmentSystem, system_id: str = "gurps"):
        self.module = module_data
        self.pc = pc
        self.vm = view_model
        self.env = env_system
        self.profile = get_profile(system_id)   # v3.2：检定规则委托系统画像
        self.combat = CombatEngine(system_id)
        self.resolver = SceneResolver()

        # v3.7：多系统模组支持——节点/幕可声明各自的系统画像，运行到哪一幕就切到哪套规则
        self.base_system_id = system_id
        self.current_system_id = system_id

        # 追踪上一次掷骰（给 View 层读取）
        self._last_packet: Optional[Dict] = None

        # 游戏进度
        self.completed_nodes: set = set()
        self.flags: Dict[str, Any] = {}
        self.choices_log: List[str] = []
        self.current_node: Optional[Dict] = None

        # 构建节点索引
        self._node_index: Dict[str, Dict] = {}
        self._act_of_node: Dict[str, str] = {}
        self._build_node_index()

    def _act_keys(self) -> List[str]:
        """模组内的幕列表（act_1、act_2…，按数字排序，兼容 3 幕以上）。"""
        keys = [k for k, v in self.module.items()
                if isinstance(v, dict) and k.startswith("act") and "nodes" in v]
        return sorted(keys, key=lambda k: (_act_num(k), k))

    def _build_node_index(self):
        """构建 node_id → node 的快速查找索引"""
        for act_key in self._act_keys():
            act = self.module.get(act_key, {})
            for node in act.get("nodes", []):
                nid = node.get("node_id", "")
                if nid:
                    # 补充 scene_type（如果没有的话）
                    if "scene_type" not in node:
                        node["scene_type"] = self._infer_scene_type(node)
                    # 补充默认字段
                    node.setdefault("prerequisite_nodes", [])
                    node.setdefault("next_nodes", [])
                    node.setdefault("unlocks_flags", [])
                    self._node_index[nid] = node
                    self._act_of_node[nid] = act_key

    def system_for_node(self, node: Dict) -> str:
        """解析该节点生效的系统画像。

        优先级：node.system > 所在幕 act.systems[0] > 模组 meta.systems[0] > 构造时默认。
        这让「一个模组跨多套规则」成为可能（每幕各用一套系统画像）。
        """
        sys_id = node.get("system")
        if not sys_id:
            act_key = self._act_of_node.get(node.get("node_id", ""), "")
            act = self.module.get(act_key, {}) or {}
            acts = act.get("systems")
            if acts:
                sys_id = acts[0] if isinstance(acts, list) else acts
        if not sys_id:
            meta = self.module.get("meta", {}) or {}
            acts = meta.get("systems")
            if acts:
                sys_id = acts[0] if isinstance(acts, list) else acts
        return str(sys_id or self.base_system_id)

    def _apply_system(self, node: Dict) -> str:
        """若该节点所属幕声明了别的系统画像，则就地切换（并重建战斗引擎）。"""
        sys_id = self.system_for_node(node)
        if sys_id != self.current_system_id:
            self.current_system_id = sys_id
            self.profile = get_profile(sys_id)
            self.combat = CombatEngine(sys_id)
        return sys_id

    def _infer_scene_type(self, node: Dict) -> str:
        """从节点内容推断场景类型"""
        physics = node.get("layer_physics", {})
        if physics.get("enemy_type"):
            return "combat"
        if physics.get("skill_checks"):
            for c in physics["skill_checks"]:
                if "急救" in c.get("skill", "") or "诊断" in c.get("skill", ""):
                    return "investigation"
        skill = physics.get("skill_check", "")
        if "感知" in skill or "Perception" in skill:
            return "perception"
        if "力量" in skill or "ST" in skill:
            return "feat"
        return "explore"

    # === 核心：运行节点 ===

    def get_available_nodes(self) -> List[Dict]:
        """获取当前可用的节点列表"""
        available = []
        for nid, node in self._node_index.items():
            if nid in self.completed_nodes:
                continue
            if self._can_access(node):
                available.append(node)
        return available

    def _can_access(self, node: Dict) -> bool:
        """检查节点是否可访问"""
        prerequisites = node.get("prerequisite_nodes", [])
        for prereq in prerequisites:
            if prereq not in self.completed_nodes:
                return False

        # 检查 flag 条件
        required_flags = node.get("required_flags", [])
        for flag in required_flags:
            if flag not in self.flags:
                return False

        return True

    def run_node(self, node_id: str, player_choice: str = None) -> ViewModelResult:
        """运行指定节点，返回 ViewModelResult"""
        node = self._node_index.get(node_id)
        if not node:
            vm_result = ViewModelResult()
            vm_result.narrative = f"错误：找不到节点 {node_id}"
            return vm_result

        self.current_node = node
        scene_type = node.get("scene_type", "explore")

        # v3.7：按幕/按节点切换系统画像（多系统模组）
        self._apply_system(node)

        # 进入场景 → 更新环境
        self.env.on_scene_enter(node)

        # 根据场景类型分发
        if scene_type == "combat":
            return self._handle_combat_node(node)

        # 通用检定节点
        return self._handle_check_node(node, player_choice)

    def _handle_check_node(self, node: Dict, player_choice: str = None) -> ViewModelResult:
        """处理通用检定节点（支持嵌套检定）"""
        physics = node.get("layer_physics", {})

        # 检查是否有 checks 数组（嵌套检定模式）
        checks = physics.get("checks", [])

        if checks:
            return self._handle_nested_checks(checks, node)

        # 单检定模式
        skill_check = physics.get("skill_check", "")
        modifier = _parse_int(physics.get("modifier", 0))
        tool_bonus = _parse_int(physics.get("tool_bonus", 0))

        # 环境修正
        env_mod = self.env.get_active_modifiers()
        modifier += env_mod

        # 查找技能等级（v3.2 起委托系统画像的技能目标折算）
        skill_level = self.profile.skill_target(self.pc, skill_check)
        if skill_level is None:
            skill_level = 10

        # 角色标签修正
        tag_mod = self.pc.calc_tag_modifier()
        modifier += tag_mod

        # v3.2：掷骰/判成功委托系统画像；v3.4 roll_high 系（D&D 5e）分支——
        # 节点 dc 字段=难度等级，修正链（环境/标签/工具）全部并入加成
        if getattr(self.profile, "check_style", "roll_low") == "roll_high":
            dc = _parse_int(physics.get("dc", 15))
            bonus = (skill_level if skill_level is not None else 0) + modifier + tool_bonus
            packet = self.profile.roll_check(dc, bonus,
                                             advantage=_parse_int(physics.get("advantage", 0)))
        else:
            packet = self.profile.roll_check(skill_level, modifier + tool_bonus)
        packet["action_type"] = node.get("scene_type", "check")
        packet["skill_used"] = skill_check
        packet["modifiers"] = {"base": modifier, "env": env_mod, "tag": tag_mod, "tool": tool_bonus}

        # 记录最后一次掷骰（给 View 层读取）
        self._last_packet = packet

        # 失败时可能触发精神印记
        psychic = node.get("psychic_marks")
        if psychic and not packet["success"]:
            self.pc.add_psychic_mark(_parse_int(psychic.get("failure_cost", 1)))

        # ViewModel 转换
        vm_result = self.vm.convert(packet, node, self.pc)
        vm_result.roll_info = packet  # 检定明细供 View 层渲染（R2：成功率显示）

        # 失败时 SAN 损失（v3.3 · CoC 7e；节点 layer_physics.san_loss 配置）
        san_cfg = physics.get("san_loss")
        if san_cfg and not packet["success"] and self.pc.san_max > 0:
            loss = _parse_dice_amount(san_cfg.get("amount", 1))
            r = self.pc.add_san_loss(loss, san_cfg.get("source", skill_check))
            packet["san_loss"] = r
            if r["indefinite_insanity"]:
                vm_result.derived_tags.append(
                    {"name": "不定期疯狂", "modifier": -20, "duration": "permanent"})
                vm_result.narrative += " 理智之堤彻底崩塌——你被卷入不定期疯狂。"
            elif r["temp_insanity"]:
                vm_result.derived_tags.append(
                    {"name": "临时疯狂", "modifier": -20, "duration": "scene"})
                vm_result.narrative += " 精神防线崩塌——你陷入了短暂的疯狂！"

        # 应用状态变更
        self._apply_status_changes(vm_result.status_changes)

        # 应用衍生标签
        for tag in vm_result.derived_tags:
            self.pc.add_tag(tag["name"], tag.get("modifier", 0), tag.get("duration", "scene"))

        # 应用环境更新
        self.env.resolve_environment_update(vm_result.environment_update)

        # 标记完成
        self.completed_nodes.add(node["node_id"])
        self.choices_log.append(f"节点 {node['node_id']}: success={packet['success']}")

        return vm_result

    def _handle_nested_checks(self, checks: List[Dict], node: Dict) -> ViewModelResult:
        """处理嵌套检定序列"""
        all_results = []
        final_success = True

        for check in checks:
            check_type = check.get("type", "automatic")

            if check_type == "choice":
                # 需要玩家选择（由 View 层处理）
                vm_result = ViewModelResult()
                vm_result.narrative = check.get("prompt", "")
                vm_result.choices = []
                for opt in check.get("options", []):
                    vm_result.choices.append({
                        "label": opt["label"],
                        "action": "check_choice",
                        "check_data": {
                            "skill": opt.get("skill", "ST"),
                            "dc": opt.get("dc", 10),
                            "on_success": opt.get("on_success", {}),
                            "on_failure": opt.get("on_failure", {}),
                        },
                    })
                return vm_result

            else:
                # 自动检定
                skill_name = check.get("skill", "ST")
                dc = _parse_int(check.get("dc", 10))
                skill_map = {"strength": self.pc.st, "agility": self.pc.dx,
                             "dexterity": self.pc.dx, "intelligence": self.pc.iq,
                             "health": self.pc.ht, "perception": self.pc.per}
                skill_level = skill_map.get(skill_name, self.pc.get_skill_level(skill_name) or 10)

                target = skill_level
                roll = roll_3d6()
                success = roll <= dc

                result = {"check_id": check.get("id", ""), "success": success,
                          "roll": roll, "dc": dc,
                          "success_chance": gurps_success_chance(dc)}
                all_results.append(result)

                if success:
                    on_success = check.get("on_success", {})
                    for flag in on_success.get("flag_set", []):
                        self.flags[flag] = True
                    # 如果 on_success 有 next，继续；否则结束
                    if not on_success.get("next"):
                        break
                else:
                    on_failure = check.get("on_failure", {})
                    damage = _parse_int(on_failure.get("damage", 0))
                    if damage:
                        self.pc.hp -= damage
                    final_success = False
                    break

        # 构建最终结果
        packet = {
            "success": final_success,
            "nested_results": all_results,
            "action_type": "nested_check",
        }

        vm_result = self.vm.convert(packet, node, self.pc)
        self.completed_nodes.add(node["node_id"])
        return vm_result

    def _handle_combat_node(self, node: Dict) -> ViewModelResult:
        """处理战斗节点"""
        physics = node.get("layer_physics", {})

        # 优先从内容目录生成敌人（v3.6 内容目录消费方）
        # catalog_ref: "深潜者" 或 {"name": "深潜者", "system": "coc7"}
        catalog_ref = physics.get("catalog_ref")
        enemy = None
        if catalog_ref:
            try:
                from services.catalog_bridge import build_enemy_from_catalog
                ref = catalog_ref if isinstance(catalog_ref, dict) else {"name": catalog_ref}
                enemy = build_enemy_from_catalog(ref.get("name"), ref.get("system"))
            except Exception:  # pragma: no cover - 目录缺失时回退内联
                enemy = None
        if enemy is None:
            enemy = self._build_inline_enemy(node, physics)

        # 特殊机制（目录与内联两条路径都适用）
        special = physics.get("special_mechanic", {})
        if special:
            enemy.special_abilities.append(special)

        # 直面恐怖 → SAN 损失（v3.7：战斗节点此前会丢弃 san_loss，
        # 导致 CoC 7e 模组最该掉理智的场合反而不掉）
        san_cfg = physics.get("san_loss")
        if san_cfg and self.pc.san_max > 0:
            loss = _parse_dice_amount(san_cfg.get("amount", 1))
            r = self.pc.add_san_loss(loss, san_cfg.get("source", enemy.name))
            if r.get("indefinite_insanity"):
                self.pc.add_tag("不定期疯狂", modifier=-20, duration="permanent")
            elif r.get("temp_insanity"):
                self.pc.add_tag("临时疯狂", modifier=-20, duration="scene")

        vm_result = ViewModelResult()
        vm_result.narrative = node.get("layer_narrative", {}).get("anchor_phrases", {}).get("success", "战斗开始！")
        vm_result.choices = [{
            "label": "⚔️ 进入战斗",
            "action": "start_combat",
            "enemy": enemy.to_dict(),
            "node_id": node["node_id"],
        }]

        self.completed_nodes.add(node["node_id"])
        return vm_result

    def _build_inline_enemy(self, node: Dict, physics: Dict) -> "Enemy":
        """从 layer_physics.unit_stats 内联构造敌人（catalog_ref 未命中时的回退）。"""
        enemy_type = physics.get("enemy_type", "mook")
        stats = physics.get("unit_stats", {})
        enemy_name = node.get("title", node.get("trigger", "未知敌人"))
        return Enemy(
            name=enemy_name,
            enemy_type="wildcard" if "wildcard" in enemy_type.lower() else "mook",
            hp=stats.get("hp", 10),
            hp_max=stats.get("hp", 10),
            attack_skill=stats.get("attack_skill", 12),
            damage=stats.get("damage", "1d6 cut"),
            dodge=stats.get("dodge", 8),
        )

    # === 状态管理 ===

    def _apply_status_changes(self, changes: Dict):
        """应用 ViewModel 产出的状态变更"""
        if changes.get("hp_delta"):
            self.pc.hp = max(0, self.pc.hp + changes["hp_delta"])
        if changes.get("fp_delta"):
            self.pc.fp = max(0, self.pc.fp + changes["fp_delta"])

    def resolve_scene(self, is_safe: bool = False) -> Dict:
        """当前节点完成后的场景结算"""
        if not self.current_node:
            return {}
        node_result = {"is_safe_node": is_safe, "is_major_challenge": True}
        return self.resolver.resolve(node_result, self.pc, self.current_node)

    # === 进度追踪 ===

    def is_act_complete(self, act_key: str) -> bool:
        """检查某幕是否完成"""
        act = self.module.get(act_key, {})
        nodes = act.get("nodes", [])
        if not nodes:
            return False
        return all(n["node_id"] in self.completed_nodes for n in nodes)

    def is_story_complete(self) -> bool:
        """全部幕（不限幕数）均已完成 → 主线结束。"""
        acts = self._act_keys()
        return bool(acts) and all(self.is_act_complete(a) for a in acts)

    def get_progress_summary(self) -> Dict:
        """获取进度摘要"""
        total = len(self._node_index)
        done = len(self.completed_nodes)
        acts = self._act_keys()
        current_act = acts[-1] if acts else "act_1"
        for ak in acts:
            if not self.is_act_complete(ak):
                current_act = ak
                break

        return {
            "total_nodes": total,
            "completed_nodes": done,
            "current_act": current_act,
            "current_system": self.current_system_id,
            "flags": dict(self.flags),
        }
