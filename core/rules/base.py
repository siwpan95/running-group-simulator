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
    check_style = "roll_low"   # roll_low（掷低成功，GURPS/CoC）| roll_high（掷高成功，D&D 5e）

    # ---- 通用检定（技能/属性检定） ----
    def roll_check(self, skill_level, modifier=0, advantage=0) -> dict:
        """执行一次检定。返回 ResolutionPacket 字段：
        {roll, target, success, margin, is_crit_success, is_fumble,
         success_chance, system}
        advantage: 1=优势（双骰取优）/ -1=劣势（取劣），roll_low 系忽略。
        roll_high 系（D&D 5e）语义：skill_level=DC，modifier=总加成。"""
        raise NotImplementedError

    def skill_target(self, character, skill_name: str):
        """从角色折算技能目标值（系统各自的属性映射/倍率）。返回 int 或 None。"""
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

    def crit_damage(self, raw) -> int:
        """大成功时的伤害处理（GURPS 双倍 / CoC 不变等）。"""
        raise NotImplementedError

    # ---- 防御 / 状态 ----
    def active_defense(self, dodge) -> dict:
        """主动防御判定，返回 {"result": "dodged"|"hit", "roll":..., ...}"""
        raise NotImplementedError

    def shock_check(self, ht, hp_max, damage_taken) -> dict:
        """受创震荡判定（阈值由各系统自算：GURPS HP/3、CoC HP/2 等）。
        返回 {"status": "ok"|"stunned", ...}"""
        raise NotImplementedError
