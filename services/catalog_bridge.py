# -*- coding: utf-8 -*-
"""
目录→实体桥接服务（v3.6 内容目录消费方）

把 data/<system>/catalog.json 的策展条目转换为引擎可直接使用的 Model 实体
（当前：怪物 / 神话生物 → core.enemy.Enemy），让扩充后的内容真正进入战斗与场景。

这是 CatalogService 之外的第二个消费方：CatalogService 只负责「检索」，
本服务负责「落地为可战斗实体」，并由场景引擎战斗节点 / MVP 调用。

字段映射原则：输出“原生系统数值”——由战斗引擎按模块 meta 自动路由到对应
系统画像（dnd5e→roll_high、coc7→d100、wod→d10 骰池）来解释，因此：
  · D&D 敌人：attack_skill = 命中加值(hit)、ac = 护甲等级、dodge 仅作 gurps 回退；
  · CoC 敌人：attack_skill = 武器百分比、dodge = DEX×2（CoC 闪避）、dr = 护甲值；
  · WoD 敌人：attack_skill = 攻击骰池、dodge = 闪避骰池、dr = 伤害平减（均为 Storytelling 池数值）；
  · GURPS 敌人：attack_skill = 3d6 技能目标、dodge = 闪避、dr = 伤害抗力、damage 含 cut/imp/cr 类型（原生 GURPS 数值，引擎默认 gurps 画像解释）。

依赖：services.catalog_service.CatalogService（统一检索）、core.enemy.Enemy。
"""
import re
from typing import List, Optional

from core.enemy import Enemy
from services.catalog_service import CatalogService


_SVC = CatalogService()

# D&D 5e 伤害类型（与 core/rules/dnd5e.py 的 _DAMAGE_TYPES 对齐，用于从伤害串提取类型词）
_DND_DMG_TYPES = (
    "slashing", "piercing", "bludgeoning", "fire", "cold", "lightning",
    "acid", "thunder", "force", "psychic", "poison", "radiant", "necrotic",
)


def _parse_int(value, default=0):
    """从 '+4' / '25%' / '10' / 10 等取值。"""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        m = re.search(r'([+-]?\d+)', value)
        if m:
            return int(m.group(1))
    return default


def _dice_avg(expr):
    """计算 '2d8+20' 的平均取整（把目录的 HP 骰表达式落到整数 HP）。"""
    m = re.match(r'\s*(\d+)d(\d+)\s*([+-]\d+)?', str(expr))
    if not m:
        return 10
    n, d, mod = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    return n * (d + 1) // 2 + mod


def _dnd_damage(dmg: str) -> str:
    """'1d6 + 2 slashing damage' → '1d6+2 slashing'（供 dnd5e 画像伤害解析）。"""
    dmg = (dmg or "").strip()
    m = re.match(r'(\d+)d(\d+)\s*([+-]\s*\d+)?', dmg)
    if not m:
        return "1d6 slashing"
    base = "%sd%s" % (m.group(1), m.group(2))
    if m.group(3):
        base += m.group(3).replace(" ", "")
    dtype = "slashing"
    low = dmg.lower()
    for t in _DND_DMG_TYPES:
        if t in low:
            dtype = t
            break
    return "%s %s" % (base, dtype)


def _dnd_enemy_type(name: str) -> str:
    if "Ancient" in name:
        return "boss"
    if "Dragon" in name or name.startswith("Young"):
        return "wildcard"
    return "elite"


def _coc_stat(stats: dict, key: str) -> int:
    """CoC 目录 stats 用小写键（str/con/siz/int/pow/dex），
    此处对大小写都兼容，避免键名风格不一致导致取到 0。"""
    return _parse_int(stats.get(key, stats.get(key.upper(), 0)), 0)


def _coc_best_skill(weapons: List[str]) -> int:
    """从全部武器里取最高的百分比作为攻击技能（原生 CoC 数值）。"""
    best = 0
    for w in (weapons or []):
        m = re.search(r'(\d+)%', str(w))
        if m:
            best = max(best, int(m.group(1)))
    return best or 25


def _coc_best_damage(weapons: List[str]) -> str:
    """从全部武器里取第一个 'XdY' 作为伤害骰。"""
    for w in (weapons or []):
        m = re.search(r'(\d+)d(\d+)', str(w))
        if m:
            return "%s cut" % m.group(0)
    return "1d6 cut"


def _coc_dr(armor) -> int:
    m = re.search(r'(\d+)', str(armor or ""))
    return int(m.group(1)) if m else 0


def build_enemy_from_catalog(name: str, system: Optional[str] = None) -> Optional[Enemy]:
    """按中文名/英文名从目录查怪物并转为 Enemy；找不到返回 None。

    system 可限定 'coc7' / 'dnd5e'，省略则全局查找。
    返回的 Enemy 携带原生系统数值，配合战斗引擎按模块 meta 自动路由的
    对应系统画像（dnd5e / coc7）使用。
    """
    entry = _SVC.find_creature(name, system)
    if not entry:
        return None
    sys_id = entry.get("_system")
    if sys_id == "dnd5e":
        return _dnd_enemy(entry)
    if sys_id == "coc7":
        return _coc_enemy(entry)
    if sys_id == "wod":
        return _wod_enemy(entry)
    if sys_id == "gurps":
        return _gurps_enemy(entry)
    return None


def _dnd_enemy(e: dict) -> Enemy:
    stats = e.get("stats", {})
    atk = e.get("attack", {})
    name = e.get("name", "未知怪物")
    ac = _parse_int(e.get("ac", 10))
    hit = _parse_int(atk.get("hit", "+0"))
    dex = _parse_int(stats.get("DEX", stats.get("Dexterity", 10)))
    hp = _dice_avg(e.get("hp", "2d6"))
    return Enemy(
        name=name,
        # D&D 原生：attack_skill = 命中加值，ac = 护甲等级
        enemy_type=_dnd_enemy_type(name),
        st=_parse_int(stats.get("STR", stats.get("Strength", 10))),
        dx=dex,
        iq=_parse_int(stats.get("INT", stats.get("Intelligence", 10))),
        ht=_parse_int(stats.get("CON", stats.get("Constitution", 10))),
        hp=hp, hp_max=hp,
        attack_skill=hit,
        damage=_dnd_damage(atk.get("damage", "1d6")),
        dodge=3 + dex // 2,            # gurps 回退用
        dr=0,                          # D&D 用 AC 而非 DR
        ac=ac,
        special_abilities=[] if not atk.get("name") else [
            {"name": atk.get("name", "攻击"), "effect": atk.get("damage", ""), "trigger": "attack"}],
        description=e.get("type_line", ""),
    )


def _coc_enemy(e: dict) -> Enemy:
    stats = e.get("stats", {})
    name = e.get("name", "未知生物")
    hp = _parse_int(e.get("hp", 10))
    dex = _coc_stat(stats, "dex")
    return Enemy(
        name=name,
        # CoC 原生：attack_skill = 武器百分比，dodge = DEX×2，dr = 护甲值
        enemy_type="wildcard",         # 神话生物多为完整追踪的单体威胁
        st=_coc_stat(stats, "str"),
        dx=dex,
        iq=_coc_stat(stats, "int"),
        ht=_coc_stat(stats, "con"),
        hp=hp, hp_max=hp,
        attack_skill=_coc_best_skill(e.get("weapons", [])),
        damage=_coc_best_damage(e.get("weapons", [])),
        dodge=max(1, dex * 2),         # CoC 闪避默认 DEX×2
        dr=_coc_dr(e.get("armor", "")),
        ac=0,
        special_abilities=[{"name": "武器", "effect": "; ".join(e.get("weapons", [])), "trigger": "attack"}],
        description=e.get("class", ""),
    )


def _wod_enemy(e: dict) -> Enemy:
    """WoD（Storytelling System / nWoD）目录条目 → Enemy。

    WoD 画像用 d10 骰池：attack_skill / dodge 均为“骰池大小”（成功数 ≥1 即命中），
    dr 为伤害平减，damage 串含“致命/恶性/冲击”类型词（wod 画像以此区分伤害类别）。
    """
    atk = e.get("attack", {})
    name = e.get("name", "未知存在")
    hp = _parse_int(e.get("hp", 10))
    return Enemy(
        name=name,
        enemy_type="wildcard",         # WoD 单体威胁多为完整追踪
        st=10, dx=_parse_int(e.get("dodge", 6)), iq=10, ht=10,
        hp=hp, hp_max=hp,
        attack_skill=_parse_int(atk.get("pool", 7)),
        damage=atk.get("damage", "1d10 致命"),
        dodge=_parse_int(e.get("dodge", 6)),
        dr=_parse_int(e.get("dr", 0)),
        ac=0,                          # WoD 用闪避骰池，不用 AC
        special_abilities=[],
        description=e.get("archetype", ""),
    )


def _gurps_enemy(e: dict) -> Enemy:
    """GURPS 4e 目录条目 → Enemy（原生 GURPS 数值）。

    attack_skill = 3d6 技能目标、dodge = 闪避、dr = 伤害抗力、
    damage 串含 cut/imp/cr 等 GURPS 伤害类型词；引擎默认 gurps 画像解释。
    enemy_type 取自条目（mook / elite / wildcard / boss），驱动附庸/精英行为。
    """
    name = e.get("name", "未知敌人")
    hp = _parse_int(e.get("hp", 10))
    return Enemy(
        name=name,
        enemy_type=e.get("enemy_type", "mook"),
        st=10, dx=10, iq=10, ht=10,
        hp=hp, hp_max=hp,
        attack_skill=_parse_int(e.get("attack_skill", 12)),
        damage=e.get("damage", "1d6 cut"),
        dodge=_parse_int(e.get("dodge", 8)),
        dr=_parse_int(e.get("dr", 0)),
        ac=0,                          # GURPS 用 DR 而非 AC
        special_abilities=[],
        description=e.get("archetype", ""),
    )
