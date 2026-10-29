# -*- coding: utf-8 -*-
"""
迷失之镜 — 龙与地下城 5 版系统画像（core/rules/dnd5e.py）

D&D 5e 裁决原语（v3.4，取材自资源库 5thsrd SRD 5.1，CC BY 4.0 合法授权）：
  - 检定：d20 + 总加成 vs DC（roll-high）；自然 20 大成功 / 自然 1 大失败；
  - 优势/劣势：双骰取高/取低（advantage=1/-1）；
  - 伤害：XdY±Z，伤害类型全套（挥砍/穿刺/钝击/火焰/寒冷/闪电/强酸/雷鸣/
    力场/心灵/毒素/光耀/暗蚀）；
  - 部位：无部位表（返回"身体"）；AC 已在命中判定内，无主动防御掷骰；
  - 大成功伤害骰翻倍（crit_damage ×2）；
  - 无 GURPS 式休克：0 HP 昏迷由引擎生命检查处理（shock_check 恒 ok）。
"""
import random
import re

from core.rules import register_profile
from core.rules.base import SystemProfile

_DAMAGE_RE = re.compile(r"(\d+)d(\d+)([+-]\d+)?")

_DAMAGE_TYPES = (
    ("挥砍", ("slashing", "挥砍")),
    ("穿刺", ("piercing", "穿刺")),
    ("钝击", ("bludgeoning", "钝击")),
    ("火焰", ("fire", "火焰")),
    ("寒冷", ("cold", "寒冷")),
    ("闪电", ("lightning", "闪电")),
    ("强酸", ("acid", "强酸")),
    ("雷鸣", ("thunder", "雷鸣")),
    ("力场", ("force", "力场")),
    ("心灵", ("psychic", "心灵")),
    ("毒素", ("poison", "毒素")),
    ("光耀", ("radiant", "光耀")),
    ("暗蚀", ("necrotic", "暗蚀")),
)


class Dnd5eProfile(SystemProfile):
    """龙与地下城 5 版：d20 roll-high vs DC。"""

    system_id = "dnd5e"
    display_name = "龙与地下城 5 版"
    dice_desc = "d20 + 加成 vs DC（自然 20 大成功 / 自然 1 大失败；优劣势双骰取高低）"
    check_style = "roll_high"

    def roll_check(self, skill_level, modifier=0, advantage=0) -> dict:
        """skill_level=DC；modifier=总加成。"""
        r1 = random.randint(1, 20)
        if advantage > 0:
            roll = max(r1, random.randint(1, 20))
        elif advantage < 0:
            roll = min(r1, random.randint(1, 20))
        else:
            roll = r1
        total = roll + modifier
        success = total >= skill_level
        # 成功率：d20+mod ≥ DC 的概率（5% 步进，截断 5-95）
        need = max(1, min(20, skill_level - modifier))
        chance = max(5, min(95, (21 - need) * 5))
        return {
            "roll": roll,
            "roll_total": total,
            "target": skill_level,          # DC
            "success": success,
            "margin": total - skill_level,
            "is_crit_success": roll == 20,
            "is_fumble": roll == 1,
            "success_chance": chance,
            "system": self.system_id,
        }

    @staticmethod
    def skill_target(character, skill_name: str):
        """D&D 技能目标 = 技能总加成（角色技能 level 字段）或属性修正 (attr-10)//2。"""
        name = (skill_name or "").strip()
        level = character.get_skill_level(name)
        if level is not None:
            return level
        attr = {
            "力量": character.st, "敏捷": character.dx,
            "体质": character.ht, "智力": character.iq,
            "感知": character.per,
            # 意志 ≈ 5e 的魅力/意志豁免：跨系统模组常用「意志」检定，
            # 没有映射会退化成 +0，等于白检定。
            "意志": character.will,
        }.get(name)
        if attr is not None:
            return (attr - 10) // 2
        return 0        # 未列属性（如魅力）按 +0

    def roll_damage(self, damage_str) -> tuple:
        m = _DAMAGE_RE.match(damage_str or "")
        if not m:
            return 1, "钝击"
        count, sides = int(m.group(1)), int(m.group(2))
        modifier = int(m.group(3) or 0)
        total = sum(random.randint(1, sides) for _ in range(count))
        return max(0, total + modifier), self.damage_type(damage_str)

    @staticmethod
    def damage_type(damage_str) -> str:
        s = (damage_str or "").lower()
        for zh, keys in _DAMAGE_TYPES:
            if any(k in s for k in keys):
                return zh
        return "钝击"

    def hit_location(self) -> str:
        return "身体"

    def penetration(self, raw, dr, dtype) -> int:
        return max(0, raw - dr)     # 5e 基础无 DR；抗性/易伤由目录/模组另行处理

    @staticmethod
    def location_effects(penetrated, location) -> dict:
        return {}

    def active_defense(self, dodge) -> dict:
        # 5e 无主动防御掷骰：AC 已计入命中判定
        return {"result": "hit",
                "narrative": "攻击命中判定已包含护甲等级（AC）。",
                "roll": None, "dodge": dodge}

    @staticmethod
    def crit_damage(raw) -> int:
        return raw * 2        # 5e 大成功：伤害骰翻倍

    def shock_check(self, ht, hp_max, damage_taken) -> dict:
        return {"status": "ok"}   # 5e 无休克；0 HP 昏迷由引擎生命检查处理


register_profile(Dnd5eProfile)
