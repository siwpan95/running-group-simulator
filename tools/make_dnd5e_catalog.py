# -*- coding: utf-8 -*-
"""
从 5thsrd SRD 5.1（CC BY 4.0）策展 D&D 5e 内容目录 → data/dnd5e/catalog.json。

怪物/法术/装备各取首批代表性条目（人工选定文件名 + 脚本解析 + 抽核）。
5thsrd.org SRD 为 CC BY 4.0，入库需保留 attribution（见 catalog.sources）。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRD = os.path.join(HERE, "规则书", "trpg_rulebooks", "5thsrd")
OUT = os.path.join(HERE, "data", "dnd5e", "catalog.json")

MONSTERS = ["goblin", "orc", "kobold", "skeleton", "zombie", "wolf",
            "giant_rat", "bandit", "cultist", "gnoll", "hobgoblin",
            "ogre", "troll", "owl", "spider"]
SPELLS = ["fireball", "magic_missile", "cure_wounds", "shield", "mage_armor",
          "burning_hands", "sleep", "bless", "detect_magic", "thunderwave"]
ITEMS = ["longsword", "dagger", "shortbow", "quarterstaff", "shield",
         "leather_armor", "chain_mail", "potion_of_healing"]


def read(name):
    p = os.path.join(SRD, name + ".md")
    if not os.path.exists(p):
        return None
    return open(p, encoding="utf-8", errors="replace").read()


def parse_monster(txt):
    title = re.search(r"^title:\s*(.+)$", txt, re.M)
    name = title.group(1).strip() if title else "?"
    i = txt.find("title:")
    start = txt.find("---", i)
    body = txt[start + 3:] if start >= 0 else txt
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    while lines and ("5thsrd.org" in lines[0] or "Looking for" in lines[0]):
        lines.pop(0)
    name2 = lines[0] if lines else name
    type_line = lines[1] if len(lines) > 1 else ""
    ac = re.search(r"Armor Class\s*(\d+)", txt)
    hp = re.search(r"Hit Points\s*(\d+)\s*\((\d+d\d+(?:[+-]\d+)?)", txt)
    speed = re.search(r"Speed\s*([^\n]+)", txt)
    stats = {}
    for line in lines:
        nums = re.findall(r"(\d+)\s*\([−\-+]\d+\)", line)
        if len(nums) == 6:
            stats = {"STR": int(nums[0]), "DEX": int(nums[1]),
                     "CON": int(nums[2]), "INT": int(nums[3]),
                     "WIS": int(nums[4]), "CHA": int(nums[5])}
            break
    # 首个攻击
    attack = None
    am = re.search(r"(\w[\w ]*?)\.\s*[^\n]*?(Melee|Ranged)[^\n]*?\+(\d+) to hit[^\n]*?(\d+d\d+(?:[+-]\d+)?[^\n]*?damage)", txt)
    if am:
        attack = {"name": am.group(1).strip(), "type": am.group(2),
                  "hit": "+" + am.group(3), "damage": am.group(4).strip()}
    return {
        "name": name2, "name_en": name if name != "?" else name2,
        "type_line": type_line,
        "ac": int(ac.group(1)) if ac else None,
        "hp": hp.group(2) if hp else None,
        "speed": speed.group(1).strip() if speed else "",
        "stats": stats,
        "attack": attack,
        "source": "5thsrd.org/monsters/" + name.lower() + " (CC BY 4.0)",
    }


def parse_spell(txt):
    title = re.search(r"^title:\s*(.+)$", txt, re.M)
    name = title.group(1).strip() if title else "?"
    i = txt.find("title:")
    start = txt.find("---", i)
    body = txt[start + 3:] if start >= 0 else txt
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    while lines and ("5thsrd.org" in lines[0] or "Looking for" in lines[0]):
        lines.pop(0)
    lvl = lines[1] if len(lines) > 1 else ""
    fields = {}
    for key in ("Casting Time", "Range", "Components", "Duration"):
        m = re.search(key + r":\s*([^\n]+)", txt)
        if m:
            fields[key.lower().replace(" ", "_")] = m.group(1).strip()
    desc = ""
    for i, l in enumerate(lines):
        if l.startswith(("Casting", "Range", "Components", "Duration")):
            desc = " ".join(x for x in lines[i + 1:i + 3] if x)[:260]
            break
    return {
        "name": name, "level_school": lvl, **fields,
        "description": desc,
        "source": "5thsrd.org/spells/" + name.lower().replace(" ", "-") + " (CC BY 4.0)",
    }


def parse_item(txt):
    title = re.search(r"^title:\s*(.+)$", txt, re.M)
    name = title.group(1).strip() if title else "?"
    body = txt[txt.find("---", txt.find("---") + 3) + 3:]
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    while lines and ("5thsrd.org" in lines[0] or "Looking for" in lines[0]):
        lines.pop(0)
    dmg = re.search(r"(\d+d\d+(?:[+-]\d+)?)\s+(\w+)\s+damage", txt)
    return {
        "name": name,
        "props": " | ".join(lines[1:4])[:200],
        "damage": dmg.group(0).strip() if dmg else None,
        "source": "5thsrd.org/items/ (CC BY 4.0)",
    }


def parse_items_tables():
    """从 weapons.md / armor.md 聚合表提取首批装备条目。"""
    items = []
    for fn, kind in (("weapons", "weapon"), ("armor", "armor")):
        txt = read(fn)
        if not txt:
            continue
        for line in txt.splitlines():
            row = re.match(r"\|\s*([A-Za-z][^|]{1,40}?)\s*\|\s*([^|]+?)\s*\|\s*"
                           r"([^|]+?)\s*\|\s*[^|]*?\s*\|\s*([^|]*?)\s*\|", line)
            if not row or row.group(1).strip().lower() in ("name", "armor", "weapon"):
                continue
            spec = row.group(3).strip().lower()
            if spec in ("damage", "cost", "ac", "armor class (ac)"):
                continue    # 表头行
            items.append({
                "name": row.group(1).strip(),
                "cost": row.group(2).strip(),
                "spec": row.group(3).strip(),     # 武器=伤害，护甲=AC 计算
                "properties": row.group(4).strip(),
                "kind": kind,
                "source": "5thsrd.org/%s (CC BY 4.0)" % fn.replace(".md", ""),
            })
    return items


def main():
    monsters, spells = [], []
    for m in MONSTERS:
        txt = read(m)
        if txt:
            monsters.append(parse_monster(txt))
        else:
            print("[warn] 缺怪物文件:", m)
    for s in SPELLS:
        txt = read(s)
        if txt:
            spells.append(parse_spell(txt))
        else:
            print("[warn] 缺法术文件:", s)
    items = parse_items_tables()

    catalog = {
        "schema": "dnd5e-catalog-v1",
        "generated_by": "tools/make_dnd5e_catalog.py（人工选定条目 + 解析 + 抽核）",
        "sources": ["5thsrd.org SRD 5.1（CC BY 4.0，attribution 见各条 source）"],
        "monsters": monsters,
        "spells": spells,
        "items": items,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print("[done] 怪物 %d / 法术 %d / 装备 %d -> %s"
          % (len(monsters), len(spells), len(items), OUT))
    for m in monsters[:4]:
        print("  ", m["name"], m.get("ac"), m.get("hp"), m.get("stats"))


if __name__ == "__main__":
    main()
