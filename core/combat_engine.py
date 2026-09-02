# -*- coding: utf-8 -*-
"""
迷失之镜 — 战斗引擎 (Model 层 · 阶段 4)
倡议抽牌 + 附庸 + Wildcard + FP 休克 + 主动防御 + 部位伤害

v3.2（2026-09-02）：纯规则（掷骰/伤害/部位/穿透/防御/休克）已收拢到
core/rules/gurps.py 系统画像，本引擎只做战斗编排与实体状态应用。
"""
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from core.character import Character
from core.dice import roll_3d6 as kernel_roll_3d6
from core.enemy import Enemy
from core.rules import get_profile
from core.rules.gurps import HIT_LOCATIONS  # noqa: F401  （兼容旧导出）

# 默认画像实例（静态方法委托用；引擎实例用 self.profile，可切系统）
_GURPS = get_profile("gurps")


@dataclass
class CombatState:
    """单轮战斗状态"""
    round_num: int = 0
    participants: List[Dict] = field(default_factory=list)  # [{"name":..., "entity":..., "card":...}]
    initiative_order: List[str] = field(default_factory=list)
    current_actor_idx: int = 0
    combat_log: List[str] = field(default_factory=list)


class CombatEngine:
    """战斗引擎（v3.2 起规则细节委托系统画像，可经 system_id 切换）"""

    def __init__(self, system_id: str = "gurps"):
        self.profile = get_profile(system_id)
        self.state: Optional[CombatState] = None

    @staticmethod
    def roll_3d6() -> int:
        """GURPS 3d6（委托 alloy 规则内核，R2）。"""
        return kernel_roll_3d6()

    @staticmethod
    def roll_damage(damage_str: str) -> int:
        """掷伤害骰。格式: '1d6 cut' / '2d6+1 imp'（委托 GURPS 画像）"""
        raw, _ = _GURPS.roll_damage(damage_str)
        return raw

    @staticmethod
    def get_damage_type(damage_str: str) -> str:
        """从伤害字符串提取类型（委托 GURPS 画像）"""
        return _GURPS.damage_type(damage_str)

    @staticmethod
    def roll_hit_location() -> str:
        """掷部位表（委托 GURPS 画像）"""
        return _GURPS.hit_location()

    # === 倡议 ===

    def draw_initiative(self, participants: List[Tuple[str, object]]) -> List[str]:
        """抽牌决定行动顺序"""
        cards = []
        for name, _ in participants:
            card = random.randint(1, 54)  # 模拟54张牌
            cards.append((name, card))
        cards.sort(key=lambda x: x[1], reverse=True)  # 高牌先动
        return [name for name, _ in cards]

    # === 战斗轮 ===

    def init_combat(self, pc: Character, enemies: List[Enemy]) -> CombatState:
        """初始化战斗"""
        state = CombatState(round_num=0)

        # 参与者：PC + 所有敌人
        participants = [("PC", pc)]
        for i, enemy in enumerate(enemies):
            tag = "Wildcard" if enemy.is_wildcard else "Mook"
            participants.append((f"{enemy.name}#{i+1}", enemy))

        state.participants = [
            {"name": name, "entity": ent, "card": random.randint(1, 54)}
            for name, ent in participants
        ]
        state.initiative_order = self.draw_initiative(participants)
        self.state = state
        return state

    def start_round(self):
        """开始新回合"""
        if not self.state:
            return
        self.state.round_num += 1
        # 重新抽牌
        participants = [(p["name"], p["entity"]) for p in self.state.participants
                        if self._entity_alive(p["entity"])]
        self.state.initiative_order = self.draw_initiative(participants)
        self.state.current_actor_idx = 0
        self.state.combat_log.append(f"--- 第 {self.state.round_num} 回合 ---")

    # === 攻击裁决 ===

    def attack_resolve(self, attacker, defender, attacker_skill: int,
                       is_reverse: bool = False) -> Dict:
        """
        攻击裁决（v3.2：掷骰/部位/穿透委托系统画像）
        返回裁决数据包: {success, roll, target, margin, damage, location, type, dr, penetrated}
        """
        chk = self.profile.roll_check(attacker_skill, 0)
        is_crit = chk["is_crit_success"]
        is_fumble = chk["is_fumble"]

        result = {
            "success": chk["success"],
            "roll": chk["roll"],
            "target": chk["target"],
            "margin": chk["margin"],
            "is_crit": is_crit,
            "is_fumble": is_fumble,
            "damage": 0,
            "raw_damage": 0,
            "location": "躯干",
            "type": "钝击",
            "dr": 0,
            "penetrated": 0,
            "defender_name": getattr(defender, "name", "目标"),
            "system": self.profile.system_id,
        }

        if not result["success"] or is_fumble:
            return result

        # 命中部位
        location = self.profile.hit_location()
        result["location"] = location

        # 伤害
        if isinstance(attacker, Character):
            weapons = attacker.get_equipped_weapons()
            damage_str = weapons[0].damage if weapons else "1d6 cut"
        elif isinstance(attacker, Enemy):
            damage_str = attacker.damage
        else:
            damage_str = "1d6 cut"

        raw, dtype = self.profile.roll_damage(damage_str)

        # 暴击伤害处理（v3.3 委托画像：GURPS 双倍 / CoC 不变）
        if is_crit:
            raw = self.profile.crit_damage(raw)

        result["raw_damage"] = raw
        result["type"] = dtype

        # 防御方 DR
        if isinstance(defender, Character):
            dr = defender.get_total_dr(location)
        elif isinstance(defender, Enemy):
            dr = defender.dr
        else:
            dr = 0

        result["dr"] = dr
        penetrated = self.profile.penetration(raw, dr, dtype)
        result["damage"] = penetrated
        result["penetrated"] = penetrated

        # 部位效应
        result["location_effects"] = self.profile.location_effects(penetrated, location)

        return result

    def active_defense(self, defender, attack_packet: Dict) -> Dict:
        """
        主动防御判定（闪避，v3.2 委托系统画像）
        返回: {"result": "dodged"|"hit", "narrative": "..."}
        """
        if isinstance(defender, Character):
            dodge = defender.dodge
        elif isinstance(defender, Enemy):
            dodge = defender.dodge
        else:
            dodge = 8
        return self.profile.active_defense(dodge)

    # === 休克检定 ===

    def shock_check(self, entity, damage_taken: int) -> Dict:
        """受创震荡检定（v3.2 委托系统画像；阈值由画像按系统自算）"""
        if isinstance(entity, Character):
            ht, hp_max = entity.ht, entity.hp_max
        elif isinstance(entity, Enemy):
            ht, hp_max = entity.ht, entity.hp_max
        else:
            return {"status": "ok"}
        return self.profile.shock_check(ht, hp_max, damage_taken)

    # === 应用伤害 ===

    def apply_damage(self, target, packet: Dict, is_mook: bool = False) -> str:
        """应用伤害到目标，返回结果描述"""
        damage = packet["damage"]

        if isinstance(target, Character):
            target.hp -= damage
            # 休克检查
            shock = self.shock_check(target, damage)
            if shock["status"] == "stunned":
                target.add_tag("震慑", modifier=-4, duration="1 round")
                return "stunned"
            # 部位标签
            for effect_name, modifier in packet.get("location_effects", {}).items():
                target.add_tag(f"{effect_name}", modifier=modifier, duration="scene")
            return "damaged"

        elif isinstance(target, Enemy):
            if is_mook:
                result = target.resolve_minion_damage(damage)
                if result == "removed":
                    target.hp = 0
                elif result == "disabled":
                    target.hp = max(0, target.hp - damage)
                else:
                    target.hp = max(0, target.hp - min(damage, 2))
                return result
            else:
                target.hp -= damage
                shock = self.shock_check(target, damage)
                if shock["status"] == "stunned":
                    return "stunned"
                return "damaged"

        return "unknown"

    # === 辅助 ===

    def _entity_alive(self, entity) -> bool:
        if isinstance(entity, Character):
            return entity.hp > 0
        if isinstance(entity, Enemy):
            return entity.hp > 0
        return True

    def is_combat_over(self) -> bool:
        """检查战斗是否结束"""
        if not self.state:
            return True
        alive_pc = True
        alive_enemies = False
        for p in self.state.participants:
            if p["name"] == "PC":
                alive_pc = self._entity_alive(p["entity"])
            else:
                if self._entity_alive(p["entity"]):
                    alive_enemies = True
        return not alive_pc or not alive_enemies

    def get_pc_wins(self) -> Optional[bool]:
        """返回 PC 是否获胜 (None=还在进行)"""
        if not self.state:
            return None
        if not self.is_combat_over():
            return None
        for p in self.state.participants:
            if p["name"] == "PC" and self._entity_alive(p["entity"]):
                return True
        return False
