# -*- coding: utf-8 -*-
"""
内容目录工程化测试（v3.6）：CatalogService 加载/检索 + schema 校验器。
零第三方依赖。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_PASS = 0
_FAIL = 0


def check(name, ok, detail=""):
    global _PASS, _FAIL
    if ok:
        _PASS += 1
        print("  [PASS] %s" % name)
    else:
        _FAIL += 1
        print("  [FAIL] %s %s" % (name, detail))


def test_catalog_service():
    from services.catalog_service import CatalogService
    svc = CatalogService()
    avail = svc.available()
    check("目录服务可用系统含 coc7/dnd5e", "coc7" in avail and "dnd5e" in avail,
          str(avail))
    coc = svc.load("coc7")
    check("coc7 目录 schema", coc.get("schema") == "coc7-catalog-v1")
    check("coc7 生物 ≥30", len(coc.get("creatures") or []) >= 30)
    deep = svc.find_creature("深潜者")
    check("查找 深潜者", deep is not None and deep.get("name_en") == "Deep One",
          str(deep)[:80] if deep else "None")
    check("查找 深潜者 带系统标记", deep is not None and deep.get("_system") == "coc7")
    check("查找 不存在的生物 → None", svc.find_creature("不存在的生物") is None)
    dnd = svc.load("dnd5e")
    check("dnd5e 目录 schema", dnd.get("schema") == "dnd5e-catalog-v1")
    check("dnd5e 怪物 ≥10", len(dnd.get("monsters") or []) >= 10)
    fb = svc.find_spell("Fireball")
    check("查找 Fireball 法术", fb is not None
          and fb.get("level_school", "").startswith("3rd"), str(fb)[:80] if fb else "None")
    ls = svc.find_item("Longsword")
    check("查找 Longsword 装备", ls is not None and ls.get("_system") == "dnd5e",
          str(ls)[:80] if ls else "None")
    gob = svc.find_creature("Goblin", system="dnd5e")
    check("按系统查 Goblin", gob is not None and gob.get("ac") == 15,
          str(gob)[:80] if gob else "None")


def test_validator():
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "validate_catalogs.py")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace")
    check("校验器退出码 0", r.returncode == 0, r.stdout[-200:])


def main():
    print("test_catalog_service（v3.6 内容目录工程化）")
    test_catalog_service()
    test_validator()
    print("================ 结果 ================")
    print("通过: %d    失败: %d" % (_PASS, _FAIL))
    if _FAIL:
        sys.exit(1)
    print("全部通过 ✔")


if __name__ == "__main__":
    main()
