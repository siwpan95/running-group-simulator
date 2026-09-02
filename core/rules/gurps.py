# -*- coding: utf-8 -*-
"""
迷失之镜 — GURPS 4e 系统画像（core/rules/gurps.py）

多系统内核抽象的首个参考实现：把 v3.1 时期散在 CombatEngine /
SceneEngine 里的 GURPS 裁决原语收拢于此，行为与 v3.1 完全一致
（546+53 测试全绿为重构安全网）。

本画像只含「纯规则」：掷骰/判成功/伤害/部位/穿透倍率/防御/休克。
实体应用（Character/Enemy 的 HP 扣减、标签）仍由引擎编排。
3d6 掷骰与成功率表走 core/dice.py（alloy.trpg.dice，R2，借鉴必记账）。
"""
import random
import re

from core.dice import gurps_success_chance, roll_3d6
from core.rules import register_profile
from core.rules.base import SystemProfile

# 命中部位表（3d6；与 v3.1 CombatEngine.HIT_LOCATIONS 完全一致）
HIT_LOCATIONS = {
    3: "头", 4: "头", 5: "头",
    6: "右臂", 7: "左臂",
    8: "躯干", 9: "躯干", 10: "躯干", 11: "躯干",
    12: "右腿", 13: "左腿",
    14: "躯干", 15: "躯干", 16: "躯干",
    17: "头", 18: "头",
}

_DAMAGE_RE = re.compile(r"(\d+)d(\d+)([+-]\d+)?")


class GurpsProfile(SystemProfile):
    """GURPS 4e：3d6 roll-low 裁决。"""

    system_id = "gurps"
    display_name = "GURPS 4e"
    dice_desc = "3d6 roll-low（目标值 ≤ 技能+修正）；3-4 大成功，17-18 大失败"

    def roll_check(self, skill_level, modifier=0) -> dict:
        roll = roll_3d6()
        target = skill_level + modifier
        success = roll <= target
        return {
            "roll": roll,
            "target": target,
            "success": success,
            "margin": target - roll,
            "is_crit_success": roll <= 4,
            "is_fumble": roll >= 17,
            "success_chance": gurps_success_chance(target),
            "system": self.system_id,
        }

    def roll_damage(self, damage_str) -> tuple:
        m = _DAMAGE_RE.match(damage_str or "")
        if not m:
            return 1, "钝击"
        count, sides = int(m.group(1)), int(m.group(2))
        modifier = int(m.group(3) or 0)
        total = sum(random.randint(1, sides) for _ in range(count))
        return max(1, total + modifier), self.damage_type(damage_str)

    @staticmethod
    def damage_type(damage_str) -> str:
        s = (damage_str or "").lower()
        if "cut" in s or "切割" in damage_str:
            return "切割"
        if "imp" in s or "穿刺" in damage_str or "pi" in s:
            return "穿刺"
        if "cr" in s or "钝击" in damage_str:
            return "钝击"
        if "burn" in s or "燃烧" in damage_str:
            return "燃烧"
        return "钝击"

    def hit_location(self) -> str:
        return HIT_LOCATIONS.get(roll_3d6(), "躯干")

    def penetration(self, raw, dr, dtype) -> int:
        penetrated = max(0, raw - dr)
        if dtype == "切割":
            penetrated = int(penetrated * 1.5)
        elif dtype == "穿刺" and raw > dr:
            penetrated = penetrated * 2
        return penetrated

    @staticmethod
    def location_effects(penetrated, location) -> dict:
        """部位效应（≥阈值伤害附加修正）。"""
        effects = {}
        if "头" in location and penetrated >= 2:
            effects["shock"] = -4
        if "臂" in location and penetrated >= 3:
            effects["weapon_grip"] = -2
        if "腿" in location and penetrated >= 3:
            effects["movement"] = -2
        return effects

    def active_defense(self, dodge) -> dict:
        roll = roll_3d6()
        if roll <= dodge:
            return {"result": "dodged",
                    "narrative": "侧身闪过——攻击擦过衣角。",
                    "roll": roll, "dodge": dodge}
        return {"result": "hit",
                "narrative": "闪避失败——攻击命中！",
                "roll": roll, "dodge": dodge}

    def shock_check(self, ht, threshold, damage_taken) -> dict:
        if damage_taken < threshold:
            return {"status": "ok"}
        roll = roll_3d6()
        if roll > ht:
            return {"status": "stunned", "penalty": -4, "duration": "1 round"}
        return {"status": "ok"}


register_profile(GurpsProfile)
