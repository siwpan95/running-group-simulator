# -*- coding: utf-8 -*-
"""
迷失之镜 — GURPS 规则原语接入层 (Model 层 · R2 反向重构 2026-08-27)

本仓不再重复实现 3d6 掷骰与 GURPS 成功率表：单一事实来源为统一引擎
alloy 的 TRPG 规则内核（alloy.trpg.dice，规则内核自 D20 并入 alloy 的 R2 产物）。

    - roll_3d6()：内核返回 (各骰结果, 总和)，本仓接口为 int 总和 → 签名适配；
    - gurps_success_chance(target)：3d6 roll-low 成功率近似表（GURPS Basic Set）。

本仓专有规则（部位表 / 伤害穿透倍率 / 附庸阈值 / 休克阈值 / XP 定价）保留在
core/combat_engine.py 与 services/xp_system.py，不进引擎。

借鉴必记账：3d6 掷骰 + GURPS 成功率表 ← alloy.trpg.dice（自 D20 并入，R2）。
"""
from alloy.trpg.dice import gurps_success_chance, roll_3d6 as _alloy_roll_3d6


def roll_3d6() -> int:
    """GURPS 主检定 3d6：返回三骰总和（alloy 内核 roll_3d6 的签名适配）。"""
    return _alloy_roll_3d6()[1]


__all__ = ["roll_3d6", "gurps_success_chance"]
