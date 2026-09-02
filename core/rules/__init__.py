# -*- coding: utf-8 -*-
"""
迷失之镜 — 多系统裁决规则画像注册表（v3.2 内核抽象）

每个「系统画像」（SystemProfile）封装一个规则书的裁决原语：
掷骰 / 检定 / 伤害 / 部位 / 主动防御 / 休克等。引擎（SceneEngine /
CombatEngine）只做编排与状态应用，规则细节一律问画像。

新增系统三步：① 在 core/rules/ 下实现 SystemProfile 子类 →
② register_profile() 注册 → ③ config/systems.json 声明元信息。
GURPS 4e 是首个画像（参考实现），行为与 v3.1 完全一致。
"""
from typing import Dict, Type

_REGISTRY: Dict[str, Type] = {}


def register_profile(profile_cls) -> None:
    """注册系统画像类（幂等）。"""
    if not getattr(profile_cls, "system_id", None):
        raise ValueError("SystemProfile 缺少 system_id")
    _REGISTRY[profile_cls.system_id] = profile_cls


def get_profile(system_id: str):
    """按系统 ID 取画像实例；未知系统抛 KeyError（含可用清单）。"""
    cls = _REGISTRY.get(system_id)
    if cls is None:
        raise KeyError("未知规则系统 '%s'，可用: %s" % (
            system_id, sorted(_REGISTRY) or ["（未注册）"]))
    return cls()


def available_systems():
    """已注册系统 ID 列表。"""
    return sorted(_REGISTRY)


# 注册内置画像
from core.rules import gurps  # noqa: E402,F401  （导入即注册）
from core.rules import coc7   # noqa: E402,F401
