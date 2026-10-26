# -*- coding: utf-8 -*-
"""
内容目录 schema 校验器（v3.6 内容目录工程化）。

用法：
    python tools/validate_catalogs.py [--json 输出 JSON 结果]
退出码 0 = 全部通过；1 = 有目录缺失/字段缺项。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")


def _req(e, fields):
    # 用“键是否存在 + 是否为空值”判定，避免把合法的 0（如 WoD 的 dr=0）误判为缺字段
    miss = [f for f in fields if f not in e or e.get(f) in (None, "", {})]
    return miss


def validate_coc7(path):
    errors = []
    try:
        c = json.load(open(path, encoding="utf-8"))
    except Exception as ex:
        return ["读取失败: %s" % ex]
    if c.get("schema") != "coc7-catalog-v1":
        errors.append("schema 版本不符: %s" % c.get("schema"))
    creatures = c.get("creatures") or []
    for i, e in enumerate(creatures):
        miss = _req(e, ("name", "name_en", "class", "stats"))
        if miss:
            errors.append("creatures[%d](%s) 缺字段 %s" % (i, e.get("name"), miss))
    if not creatures:
        errors.append("creatures 为空")
    return errors


def validate_dnd5e(path):
    errors = []
    try:
        c = json.load(open(path, encoding="utf-8"))
    except Exception as ex:
        return ["读取失败: %s" % ex]
    if c.get("schema") != "dnd5e-catalog-v1":
        errors.append("schema 版本不符: %s" % c.get("schema"))
    for key, fields in (("monsters", ("name", "ac", "hp", "stats")),
                        ("spells", ("name", "level_school")),
                        ("items", ("name", "spec"))):
        for i, e in enumerate(c.get(key) or []):
            miss = [f for f in fields if e.get(f) in (None, "", {})]
            if miss:
                errors.append("%s[%d](%s) 缺字段 %s"
                              % (key, i, e.get("name"), miss))
    if not (c.get("monsters") or c.get("spells") or c.get("items")):
        errors.append("三个目录均为空")
    return errors


def validate_wod(path):
    errors = []
    try:
        c = json.load(open(path, encoding="utf-8"))
    except Exception as ex:
        return ["读取失败: %s" % ex]
    if c.get("schema") != "wod-catalog-v1":
        errors.append("schema 版本不符: %s" % c.get("schema"))
    creatures = c.get("creatures") or []
    for i, e in enumerate(creatures):
        miss = _req(e, ("name", "hp", "attack", "dodge", "dr"))
        if miss:
            errors.append("creatures[%d](%s) 缺字段 %s" % (i, e.get("name"), miss))
            continue
        atk = e.get("attack") or {}
        if _req(atk, ("pool", "damage")):
            errors.append("creatures[%d](%s) attack 缺字段 %s"
                          % (i, e.get("name"), _req(atk, ("pool", "damage"))))
    if not creatures:
        errors.append("creatures 为空")
    return errors


def main():
    catalogs = {
        "coc7": ("data/coc7/catalog.json", validate_coc7),
        "dnd5e": ("data/dnd5e/catalog.json", validate_dnd5e),
        "wod": ("data/wod/catalog.json", validate_wod),
    }
    result = {}
    fails = 0
    for system, (rel, fn) in catalogs.items():
        p = os.path.join(HERE, rel)
        if not os.path.exists(p):
            result[system] = {"ok": False, "errors": ["目录文件缺失: " + rel]}
            fails += 1
            continue
        errors = fn(p)
        result[system] = {"ok": not errors, "errors": errors,
                          "path": rel, "entries": _count(p)}
        if errors:
            fails += 1
    if "--json" in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for system, r in result.items():
            print("[%s] %s %s" % (system, "OK " if r["ok"] else "FAIL",
                                  r.get("entries", "")))
            for e in r.get("errors", []):
                print("      -", e)
    return 1 if fails else 0


def _count(path):
    c = json.load(open(path, encoding="utf-8"))
    return "creatures=%d" % len(c.get("creatures") or []) if "creatures" in c \
        else "monsters=%d spells=%d items=%d" % (
            len(c.get("monsters") or []), len(c.get("spells") or []),
            len(c.get("items") or []))


if __name__ == "__main__":
    sys.exit(main())
