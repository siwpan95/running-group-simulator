# -*- coding: utf-8 -*-
"""
迷失之镜 — 克苏鲁的呼唤 7 版系统画像（core/rules/coc7.py）

CoC 7e 裁决原语（v3.3，取材自资源库 coc_pdf 三宝书 + trow CoC 扩展帖）：
  - 检定：d100 roll-low；01 或 ≤ 技能/5 为大成功；100 为大失败
    （96-99 在技能 <50 时同样视为大失败，7 版规则）；
  - 奖励/惩罚骰：多掷一枚十位骰，取更优/更差十位；
  - 伤害：XdY±Z 平减护甲（无伤害类型倍率）；
  - 部位：默认无部位表（可选规则，v3.3 不启用，返回"身体"）；
  - 防御：闪避 = 敏捷值一半（画像只接收折算后的 dodge 值）；
  - 重伤（Major Wound）：单次 ≥ 最大 HP/2 → CON×5 检定失败则失去意识。
"""
import random
import re

from core.rules import register_profile
from core.rules.base import SystemProfile

_DAMAGE_RE = re.compile(r"(\d+)d(\d+)([+-]\d+)?")


def roll_d100(bonus_dice: int = 0) -> int:
    """掷 d100（1-100）。bonus_dice>0 奖励骰（取更优十位），<0 惩罚骰（取更劣十位）。"""
    tens = random.randint(0, 9)
    ones = random.randint(0, 9)
    extra = [random.randint(0, 9) for _ in range(abs(bonus_dice))]
    if bonus_dice > 0:
        tens = min([tens] + extra)          # 奖励骰：十位取小
    elif bonus_dice < 0:
        tens = max([tens] + extra)          # 惩罚骰：十位取大
    return tens * 10 + ones if tens * 10 + ones > 0 else 100  # 00 → 100


class Coc7Profile(SystemProfile):
    """克苏鲁的呼唤 7 版：d100 roll-low。"""

    system_id = "coc7"
    display_name = "克苏鲁的呼唤 7 版"
    dice_desc = "d100 roll-low（目标值 ≤ 技能；01/五分之一为大成功，100 为大失败；支持奖励/惩罚骰）"

    def roll_check(self, skill_level, modifier=0, bonus_dice=0) -> dict:
        target = max(1, min(100, skill_level + modifier))
        roll = roll_d100(bonus_dice)
        success = roll <= target
        crit = roll <= max(1, target // 5) or roll == 1
        fumble = roll == 100 or (roll >= 96 and target < 50)
        return {
            "roll": roll,
            "target": target,
            "success": success,
            "margin": target - roll,
            "is_crit_success": crit,
            "is_fumble": fumble,
            "success_chance": target,       # d100 成功率即目标值
            "system": self.system_id,
        }

    # ---- 技能目标折算：CoC 技能为 0-99；裸属性检定 = 属性 × 5 ----
    @staticmethod
    def skill_target(character, skill_name: str):
        """从角色取技能目标值；未掌握技能回退属性×5（CoC 惯例）。"""
        level = character.get_skill_level(skill_name)
        if level is not None and level <= 99:
            return level
        attr = {
            "力量": character.st, "敏捷": character.dx,
            "智力": character.iq, "体质": character.ht,
            "意志": character.will, "感知": character.per,
        }.get(skill_name.strip(), None)
        if attr is not None:
            return attr * 5
        return None

    def roll_damage(self, damage_str) -> tuple:
        m = _DAMAGE_RE.match(damage_str or "")
        if not m:
            return 1, "物理"
        count, sides = int(m.group(1)), int(m.group(2))
        modifier = int(m.group(3) or 0)
        total = sum(random.randint(1, sides) for _ in range(count))
        return max(0, total + modifier), "物理"

    @staticmethod
    def damage_type(damage_str) -> str:
        return "物理"

    def hit_location(self) -> str:
        return "身体"      # CoC 7e 部位为可选规则，默认不掷部位

    def penetration(self, raw, dr, dtype) -> int:
        return max(0, raw - dr)     # CoC 护甲平减，无倍率

    @staticmethod
    def crit_damage(raw) -> int:
        return raw                  # CoC 7e 大成功不翻倍（穿刺武器可贯通，v3.3 简化）

    @staticmethod
    def location_effects(penetrated, location) -> dict:
        return {}

    def active_defense(self, dodge) -> dict:
        roll = roll_d100()
        if roll <= dodge:
            return {"result": "dodged",
                    "narrative": "你侧身闪开——攻击落了空。",
                    "roll": roll, "dodge": dodge}
        return {"result": "hit",
                "narrative": "闪避不及——攻击命中！",
                "roll": roll, "dodge": dodge}

    def shock_check(self, ht, hp_max, damage_taken) -> dict:
        """CoC 重伤检定：单次伤害 ≥ 最大 HP/2 → CON×5 检定，失败失去意识。"""
        threshold = max(1, hp_max // 2)
        if damage_taken < threshold:
            return {"status": "ok"}
        roll = roll_d100()
        if roll > ht * 5:
            return {"status": "stunned", "penalty": -20,
                    "duration": "1 round", "note": "失去意识"}
        return {"status": "ok"}


register_profile(Coc7Profile)
