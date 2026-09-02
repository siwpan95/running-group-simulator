# -*- coding: utf-8 -*-
"""
迷失之镜 — 系统规则画像基类（core/rules/base.py）

SystemProfile = 一个规则书的裁决原语集合。引擎只调这些方法，
方法内部如何掷骰、判成功、算伤害，完全由各系统自决。

新增系统的画像必须实现以下全部方法；行为以各自规则书为准，
由 tests/test_rules_profiles.py 用固定种子钉住。
"""


class SystemProfile:
    """规则系统画像抽象基类。"""

    system_id = ""          # 注册表键名（如 "gurps" / "coc7" / "dnd5e"）
    display_name = ""       # 人类可读名
    dice_desc = ""          # 骰系描述（供 UI/文档）

    # ---- 通用检定（技能/属性检定） ----
    def roll_check(self, skill_level, modifier=0) -> dict:
        """执行一次检定。返回 ResolutionPacket 字段：
        {roll, target, success, margin, is_crit_success, is_fumble,
         success_chance, system}"""
        raise NotImplementedError

    # ---- 伤害 ----
    def roll_damage(self, damage_str) -> tuple:
        """掷伤害骰，返回 (raw 伤害值, 伤害类型名)。"""
        raise NotImplementedError

    def hit_location(self) -> str:
        """随机命中部位（无部位表的系统返回整体描述）。"""
        raise NotImplementedError

    def penetration(self, raw, dr, dtype) -> int:
        """护甲穿透：raw 伤害 - DR 后按类型倍率修正。"""
        raise NotImplementedError

    # ---- 防御 / 状态 ----
    def active_defense(self, dodge) -> dict:
        """主动防御判定，返回 {"result": "dodged"|"hit", "roll":..., ...}"""
        raise NotImplementedError

    def shock_check(self, ht, threshold, damage_taken) -> dict:
        """受创震荡判定，返回 {"status": "ok"|"stunned", ...}"""
        raise NotImplementedError
