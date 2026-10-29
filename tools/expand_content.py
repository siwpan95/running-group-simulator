# -*- coding: utf-8 -*-
"""
配套内容扩充脚本（一次性，可重复运行）。

向以下文件合并原创 GURPS 内容（按 name 去重，不覆盖既有条目）：
  data/enemies.json  -> enemies[]
  data/items.json    -> (以物品名为键的对象)
数据均为本项目原创设定，不引用任何第三方版权文本。
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENEMIES = os.path.join(HERE, "data", "enemies.json")
ITEMS = os.path.join(HERE, "data", "items.json")

NEW_ENEMIES = [
    {
        "name": "镜螨",
        "enemy_type": "mook",
        "hp": 6, "hp_max": 6,
        "attack_skill": 10, "damage": "1d-3 cut",
        "dodge": 11, "dr": 0,
        "description": "铜镜碎屑凝成的小型爬虫，外壳是一面面凸面小镜。",
        "flavor_text": "它转身时，你看见镜面里站着的不是自己。",
        "minion_threshold": {">=6": "立即碎裂", "2-5": "蜷缩逃窜", "<2": "暂时畏缩"},
        "special_abilities": [
            {"name": "镜面反射", "effect": "受光属性攻击减半", "trigger": "hit"}
        ],
    },
    {
        "name": "锈影",
        "enemy_type": "wildcard",
        "hp": 14, "hp_max": 14, "fp": 12,
        "st": 10, "dx": 13, "iq": 9, "ht": 11,
        "attack_skill": 13, "damage": "2d6 cut",
        "dodge": 11, "dr": 1,
        "description": "由废弃机械与执念糅合而成的畸变体，表面覆满会缓慢爬动的锈斑。",
        "flavor_text": "每走一步，地面就多一道褐红色的锈痕。",
        "special_abilities": [
            {"name": "锈蚀触摸", "effect": "命中后目标金属装备 -1 DR（可叠加）", "trigger": "attack"},
            {"name": "自我修复", "effect": "每轮恢复 1 HP，被火/电克制", "trigger": "always"}
        ],
    },
    {
        "name": "钟楼石像",
        "enemy_type": "elite",
        "hp": 20, "hp_max": 20,
        "attack_skill": 12, "damage": "2d6+1 cr",
        "dodge": 7, "dr": 3,
        "description": "镇中心钟楼顶端的滴水石像，被某种意志唤醒后自行脱落。",
        "flavor_text": "它的眼里嵌着两枚还在走的齿轮。",
        "special_abilities": [
            {"name": "钟鸣震慑", "effect": "每 3 轮一次，10m 内所有目标 Will-3 对抗", "trigger": "every_3_rounds"}
        ],
    },
    {
        "name": "低语者",
        "enemy_type": "mook",
        "hp": 8, "hp_max": 8,
        "attack_skill": 11, "damage": "1d6 aff",
        "dodge": 9, "dr": 0,
        "description": "雾中浮现的人形轮廓，没有脸，只有持续不断的耳语。",
        "flavor_text": "它说的每个字，都让你更想放下武器。",
        "minion_threshold": {">=6": "立即消散", "2-5": "退入雾中", "<2": "声息减弱"},
        "special_abilities": [
            {"name": "耳语", "effect": "命中后目标下次检定 -1（意志对抗可免疫）", "trigger": "attack"}
        ],
    },
]

NEW_ITEMS = {
    "信号枪": {
        "name": "信号枪",
        "type": "weapon",
        "slot": "hand",
        "damage": "1d6 burn",
        "effects": [{"tag_mod": "add:照明", "range": "30m"}],
        "uses": 3,
        "description": "一发红色信号弹，能照亮大片区域，也能吓退畏光之物。"
    },
    "夜视仪": {
        "name": "夜视仪",
        "type": "tool",
        "slot": "head",
        "effects": [{"tag_mod": "remove:低能见度", "range": "self"}],
        "uses": -1,
        "description": "军用级微光夜视仪，让黑暗不再成为阻碍。"
    },
    "防毒面具": {
        "name": "防毒面具",
        "type": "armor",
        "slot": "face",
        "dr": 0,
        "effects": [{"tag_mod": "resist:毒气"}],
        "penalty": {"per": -1},
        "uses": -1,
        "description": "活性炭滤罐，能滤过大部分瓦斯与孢子。"
    },
    "撬锁工具组": {
        "name": "撬锁工具组",
        "type": "tool",
        "slot": "backpack",
        "effects": [{"tool_bonus": 3, "skill": "撬锁"}],
        "uses": -1,
        "description": "一套精密的撬锁钩与扭力扳手，老练的手指能用它打开大多数机械锁。"
    },
}


def merge_enemies(base, entries):
    existing = {e.get("name", "").strip().lower() for e in base.get("enemies") or []}
    added = 0
    for e in entries:
        if e["name"].strip().lower() not in existing:
            base.setdefault("enemies", []).append(e)
            existing.add(e["name"].strip().lower())
            added += 1
    return added


def merge_items(base, entries):
    added = 0
    for k, v in entries.items():
        if k not in base:
            base[k] = v
            added += 1
    return added


def main():
    with open(ENEMIES, encoding="utf-8") as f:
        en = json.load(f)
    a = merge_enemies(en, NEW_ENEMIES)
    with open(ENEMIES, "w", encoding="utf-8") as f:
        json.dump(en, f, ensure_ascii=False, indent=2)

    with open(ITEMS, encoding="utf-8") as f:
        it = json.load(f)
    b = merge_items(it, NEW_ITEMS)
    with open(ITEMS, "w", encoding="utf-8") as f:
        json.dump(it, f, ensure_ascii=False, indent=2)

    print("[enemies] +%d  [items] +%d" % (a, b))


if __name__ == "__main__":
    main()
