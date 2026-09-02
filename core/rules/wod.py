# -*- coding: utf-8 -*-
"""
迷失之镜 — 黑暗世界系统画像（core/rules/wod.py）

WoD / 新黑暗世界（Storytelling System）裁决原语（v3.5，取材自资源库
trow_books 40+ 部 WoD 成书，社区翻译，仅作规则取材校对）：
  - 骰池：属性+技能 d10 骰池；每骰 ≥8 记 1 成功（nWoD 定难度），
    10 再掷（10-again）；
  - 大成功：成功数 ≥5（exceptional success）；戏剧性失败：0 成功且出现 1；
  - 饥饿/绝望骰（V5 变体）：以 hunger 骰替换骰池（参数 hunger=0..5），
    大成功且饥饿骰出 10 → messy critical（混乱大成功）；
  - 伤害：成功数 + 武器修正 − 护甲平减；无部位表；无暴击翻倍；
  - 防御：防御骰池（8+ 成功闪避）；受伤惩罚抽象为重伤半血判定。
"""
import random
import re

from core.rules import register_profile
from core.rules.base import SystemProfile

_DAMAGE_RE = re.compile(r"(\d+)d(\d+)([+-]\d+)?")


def roll_pool(n, hunger=0):
    """掷 n 个 d10 骰池（10-again 一次）。返回 (成功数, 骰面列表, 饥饿骰面列表)。"""
    n = max(0, int(n))
    hunger = max(0, min(hunger, n))
    dice = [random.randint(1, 10) for _ in range(n)]
    successes = 0
    faces = list(dice)
    for i, d in enumerate(dice):
        if d >= 8:
            successes += 1
        if d == 10:  # 10-again：再掷一次
            r = random.randint(1, 10)
            faces.append(r)
            if r >= 8:
                successes += 1
    hunger_faces = dice[:hunger] if hunger else []
    return successes, faces, hunger_faces


class WoDProfile(SystemProfile):
    """黑暗世界（新 WoD / Storytelling System）：d10 骰池。"""

    system_id = "wod"
    display_name = "黑暗世界（Storytelling System）"
    dice_desc = "d10 骰池（≥8 成功，10-again；≥5 成功大成功；0 成功且出 1 戏剧性失败；V5 饥饿骰）"

    def roll_check(self, skill_level, modifier=0, advantage=0, hunger=0) -> dict:
        pool = skill_level + modifier
        successes, faces, hunger_faces = roll_pool(pool, hunger)
        crit = successes >= 5
        fumble = successes == 0 and 1 in faces
        messy = crit and 10 in hunger_faces
        chance = round(max(5, (1 - 0.7 ** max(0, pool)) * 100))
        return {
            "roll": successes,                    # 成功数（兼容 int roll 通道）
            "pool": pool,
            "target": 1,                          # 基本要求：1 成功
            "success": successes >= 1,
            "margin": successes - 1,
            "is_crit_success": crit,
            "is_fumble": fumble,
            "messy_critical": messy,
            "success_chance": chance,
            "system": self.system_id,
        }

    @staticmethod
    def skill_target(character, skill_name: str):
        """WoD 骰池基准 = 技能等级或属性值（属性+技能由模组拆分或技能自带）。"""
        name = (skill_name or "").strip()
        level = character.get_skill_level(name)
        if level is not None:
            return level
        attr = {
            "力量": character.st, "敏捷": character.dx,
            "体质": character.ht, "智力": character.iq,
            "感知": character.per, "意志": character.will,
        }.get(name)
        return attr if attr is not None else 2   # 未列属性按 2 骰兜底

    def roll_damage(self, damage_str) -> tuple:
        m = _DAMAGE_RE.match(damage_str or "")
        if not m:
            return 1, "冲击"
        count, sides = int(m.group(1)), int(m.group(2))
        modifier = int(m.group(3) or 0)
        total = sum(random.randint(1, sides) for _ in range(count))
        return max(0, total + modifier), self.damage_type(damage_str)

    @staticmethod
    def damage_type(damage_str) -> str:
        s = (damage_str or "").lower()
        if "agg" in s or "恶性" in damage_str or "aggravated" in s:
            return "恶性"
        if "lethal" in s or "致命" in damage_str:
            return "致命"
        return "冲击"

    def hit_location(self) -> str:
        return "身体"

    def penetration(self, raw, dr, dtype) -> int:
        return max(0, raw - dr)     # 伤害平减护甲

    @staticmethod
    def location_effects(penetrated, location) -> dict:
        return {}

    def active_defense(self, dodge) -> dict:
        pool = max(1, min(10, dodge))
        successes, _, _ = roll_pool(pool)
        if successes >= 1:
            return {"result": "dodged",
                    "narrative": "你侧身闪避——攻击落了空。",
                    "roll": successes, "dodge": dodge}
        return {"result": "hit",
                "narrative": "闪避不及——攻击命中！",
                "roll": successes, "dodge": dodge}

    @staticmethod
    def crit_damage(raw) -> int:
        return raw      # WoD 无暴击翻倍

    def shock_check(self, ht, hp_max, damage_taken) -> dict:
        """受伤惩罚抽象：单次 ≥ 最大 HP/2 → 震慑（-10 检定惩罚）。"""
        threshold = max(1, hp_max // 2)
        if damage_taken < threshold:
            return {"status": "ok"}
        return {"status": "stunned", "penalty": -10,
                "duration": "scene", "note": "受伤惩罚"}


register_profile(WoDProfile)
