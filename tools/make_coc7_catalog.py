# -*- coding: utf-8 -*-
"""
从 T.R.O.W. CoC 神话生物帖（trow_rulebooks/forum_69/69_11676）半自动提取
CoC 7e 生物目录条目 → data/coc7/catalog.json（v3.3 首批内容目录）。

产出 schema：creatures[]（名称/英文名/阶级/均值能力/耐久/移动/伤害加权/
武器/装甲/理智值丧失/来源）。数值取自规则书译文的「平均值」列。
本脚本为策展辅助：生成后人工抽核，不直接当事实源。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 仓库根
_SRC_NEW = os.path.join(HERE, "规则书", "trpg_rulebooks",
                        "trow_rulebooks", "forum_69",
                        "69_11676_[CoC TRPG] 神话生物.md")
_SRC_OLD = r"F:\novel\规则书\trpg_rulebooks\trow_rulebooks\forum_69\69_11676_[CoC TRPG] 神话生物.md"
SRC = _SRC_NEW if os.path.exists(_SRC_NEW) else _SRC_OLD
OUT = os.path.join(HERE, "data", "coc7", "catalog.json")


def classify(line1):
    """阶级行分类：上级/下级 + 独立种族/仆从种族/旧日支配者/外神/旧神。"""
    prefix = ""
    if line1.startswith("上级"):
        prefix = "上级"
    elif line1.startswith("下级"):
        prefix = "下级"
    body = line1[len(prefix):]
    if "仆从" in body:
        return (prefix + "仆从种族") if prefix else "仆从种族"
    if "独立" in body:
        return (prefix + "独立种族") if prefix else "独立种族"
    if "旧日" in body:
        return "旧日支配者"
    if "外神" in body:
        return "外神"
    if "旧神" in body:
        return "旧神"
    if "神格" in body or "神" in body:
        return "神格存在"
    return None


def parse_stats(text):
    """解析能力值块：{stat: avg} 与耐久/移动/伤害加权/装甲/理智丧失/武器。

    多阶段生物（如钻地魔虫成长六期）含多个能力值块——取耐久最大的
    （成熟体）作为条目数据。"""
    best = None
    for m in re.finditer(r"能力值", text):
        seg = text[m.start():m.start() + 900]
        hp_m = re.search(r"耐久：\s*(\d+)", seg)
        hp = int(hp_m.group(1)) if hp_m else -1
        if best is None or hp > best[0]:
            best = (hp, seg)
    seg = best[1] if best else text[:900]
    stats = {}
    for key, pat in (
        ("str", r"力量：\s*[\d+d\-×xX]+\s*(\d+)"),
        ("con", r"体质：\s*[\d+d\-×xX]+\s*(\d+)"),
        ("siz", r"体型：\s*[\d+d\-×xX]+\s*(\d+)"),
        ("int", r"智力：\s*[\d+d\-×xX]+\s*(\d+)"),
        ("pow", r"意志：\s*[\d+d\-×xX]+\s*(\d+)"),
        ("dex", r"敏捷：\s*[\d+d\-×xX]+\s*(\d+)"),
    ):
        m = re.search(pat, text)
        if m:
            stats[key] = int(m.group(1))
    out = {"stats": stats}
    m = re.search(r"移动：\s*([^\n]+)", text)
    if m:
        out["move"] = m.group(1).strip()
    m = re.search(r"耐久：\s*(\d+)", text)
    if m:
        out["hp"] = int(m.group(1))
    m = re.search(r"平均伤害加权：\s*([^\n]+)", text)
    if m:
        out["damage_bonus"] = m.group(1).strip()
    m = re.search(r"装甲：\s*([^\n]+)", text)
    if m:
        out["armor"] = m.group(1).strip()
    m = re.search(r"理智值丧失：\s*([^\n]+)", text)
    if m:
        out["san_loss"] = m.group(1).strip()
    weapons = re.findall(r"武器：\s*([^\n]+)", text)
    if weapons:
        out["weapons"] = [w.strip() for w in weapons[0].split(")") if w.strip()]
    return out


def main():
    if not os.path.exists(SRC):
        print("[warn] 源文件缺失:", SRC)
        sys.exit(1)
    text = open(SRC, encoding="utf-8").read()
    # 找生物标题行（中文名(English) 独立成行，下一行是阶级）
    header_re = re.compile(
        r"^([\u4e00-\u9fff··，、\s]{2,20})\(([A-Za-z][A-Za-z'\- ]+)\)\s*$",
        re.M)
    blocks = []
    matches = list(header_re.finditer(text))
    for idx, m in enumerate(matches):
        name, en = m.group(1).strip(), m.group(2).strip()
        if len(name) < 2:
            continue
        line1 = text[m.end():m.end() + 120].lstrip().splitlines()[0].strip()
        cls = classify(line1)
        if not cls:
            continue   # 下一行不是阶级行（普通文字段落，跳过）
        # 条目正文：从本标题到下一条目标题（封顶 8000 字符）
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        seg = text[m.start():min(end, m.start() + 8000)]
        blocks.append((name, en, cls, seg))

    seen = set()
    creatures = []
    for name, en, cls, seg in blocks:
        if name in seen:
            continue
        entry = {"name": name, "name_en": en, "class": cls, "source": "trow-11676"}
        entry.update(parse_stats(seg))
        if entry.get("stats"):
            seen.add(name)   # 仅解析出数据的条目占去重位（表1 清单行会被正文覆盖）
            creatures.append(entry)

    catalog = {
        "schema": "coc7-catalog-v1",
        "generated_by": "tools/make_coc7_catalog.py（半自动提取，人工抽核）",
        "sources": [
            "T.R.O.W. 最深的地下城 版块69 tid11676《[CoC TRPG] 神话生物》"
            "（玖羽/Frend 译，2009）",
        ],
        "creatures": creatures,
        "tomes": [],
        "spells": [],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print("[done] 提取生物 %d 条 -> %s" % (len(creatures), OUT))
    for c in creatures[:8]:
        print("  ", c["name"], c["name_en"], c["class"], c.get("stats"))


if __name__ == "__main__":
    main()
