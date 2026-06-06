#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Excel 生态体系 — 回验证脚本"""
import os, sys, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from services.data_importer import DataImporter
from tools.char_importer import CharImporter

di = DataImporter()
passed = 0
failed = 0

def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name} {detail}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

print("=" * 60)
print("  Excel 生态体系 — 回验证")
print("=" * 60)

# 1. 角色卡导入（Excel → dict）
print("\n📋 1. 角色卡 Excel 导入")
ci = CharImporter(verbose=False)
char_dir = os.path.join(BASE, "templates", "characters")

for fname in ["预置-调查记者.xlsx", "预置-退役军警.xlsx", "预置-神秘学学者.xlsx", "预置-街头混混.xlsx"]:
    path = os.path.join(char_dir, fname)
    char_json = ci.import_xlsx(path)
    check(f"导入 {fname}", char_json is not None and char_json.get("name"))
    if char_json:
        attrs = char_json["attributes"]
        check(f"  属性完整 {fname}", all(k in attrs for k in ["ST","DX","IQ","HT"]))
        check(f"  技能非空 {fname}", len(char_json["skills"]) > 0,
              f"({len(char_json['skills'])} 项: {', '.join(s['name'] for s in char_json['skills'])})")
        check(f"  特征非空 {fname}", len(char_json["features"]) > 0,
              f"({len(char_json['features'])} 项)")

# 2. 敌人 Excel 导入
print("\n🖥️ 2. 敌人 Excel 导入")
gm_dir = os.path.join(BASE, "templates", "gm-data")
enemy_xlsx = os.path.join(gm_dir, "enemy_builder.xlsx")
enemies = di.import_enemies_from_xlsx(enemy_xlsx)
check("导入 enemy_builder.xlsx", len(enemies) > 0, f"({len(enemies)} 个敌人)")
for e in enemies:
    check(f"  敌人 {e['name']}", all(k in e for k in ["name","enemy_type","hp","attack_skill","damage","dodge","dr"]))

# 3. 物品 Excel 导入
print("\n🖥️ 3. 物品 Excel 导入")
item_xlsx = os.path.join(gm_dir, "item_builder.xlsx")
items = di.import_items_from_xlsx(item_xlsx)
check("导入 item_builder.xlsx", len(items) > 0, f"({len(items)} 个物品)")
for k, v in items.items():
    check(f"  物品 {k}", "name" in v and "type" in v,
          f"({v.get('name','?')} / {v.get('type','?')})")

# 4. 陷阱/遭遇/战利品/NPC反应
print("\n🖥️ 4. 遭遇/战利品/NPC反应表")
for fname, method, label in [
    ("trap_builder.xlsx", "import_traps_from_xlsx", "陷阱"),
    ("encounter_table.xlsx", "import_encounters_from_xlsx", "遭遇"),
    ("loot_table.xlsx", "import_loot_from_xlsx", "战利品"),
    ("npc_reaction.xlsx", "import_reactions_from_xlsx", "NPC反应"),
]:
    xlsx_path = os.path.join(gm_dir, fname)
    data = getattr(di, method)(xlsx_path)
    check(f"导入 {fname}", len(data) > 0, f"({len(data)} 条 > 0)")

# 5. 场景构建表
print("\n📝 5. 场景构建 Excel 导入")
module_dir = os.path.join(BASE, "templates", "gm-module")
scene_xlsx = os.path.join(module_dir, "scene_builder.xlsx")
module = di.import_scenes_from_xlsx(scene_xlsx)
for act_key in ["act_1", "act_2", "act_3"]:
    act = module.get(act_key, {})
    nodes = act.get("nodes", [])
    check(f"  {act_key}", len(nodes) > 0, f"({len(nodes)} 个节点)")
    for n in nodes:
        check(f"    节点 {n['node_id']}", n.get("scene_type") is not None,
              f"(type={n.get('scene_type','?')})")

# 6. 模组元信息
print("\n📝 6. 模组元信息")
meta_xlsx = os.path.join(module_dir, "module_meta.xlsx")
if os.path.exists(meta_xlsx):
    print("  ✅ module_meta.xlsx 存在（手工填写用，不自动导入）")

# 7. 网格地图
print("\n🗺️ 7. 网格地图")
map_xlsx = os.path.join(module_dir, "map_grid.xlsx")
check("map_grid.xlsx 存在", os.path.exists(map_xlsx))

# 8. 对比：Excel导出 vs 现有JSON
print("\n🔬 8. Excel → JSON 对比现有数据")
# 取调查记者做对比
char_xlsx = os.path.join(char_dir, "预置-调查记者.xlsx")
char_from_excel = ci.import_xlsx(char_xlsx)
existing_json_path = os.path.join(BASE, "characters", "预置-调查记者.json")
if os.path.exists(existing_json_path):
    with open(existing_json_path, "r", encoding="utf-8") as f:
        char_from_json = json.load(f)

    # 关键字段对比
    check("角色ID一致", char_from_excel["character_id"] == char_from_json["character_id"])
    check("名称不空", char_from_excel["name"] and len(char_from_excel["name"]) > 0,
          f"(Excel名={char_from_excel['name']} ≠ JSON角色真名={char_from_json['name']}—设计如此:Excel用角色类型标签)")
    excel_attrs = char_from_excel["attributes"]
    json_attrs = char_from_json["attributes"]
    for a in ["ST", "DX", "IQ", "HT"]:
        check(f"  属性 {a}", excel_attrs[a] == json_attrs[a],
              f"(Excel={excel_attrs[a]} JSON={json_attrs[a]})")
    check("技能数量一致", len(char_from_excel["skills"]) == len(char_from_json["skills"]),
          f"(Excel={len(char_from_excel['skills'])} JSON={len(char_from_json['skills'])})")
    check("特征数量一致", len(char_from_excel["features"]) == len(char_from_json["features"]))
    check("优势数量一致", len(char_from_excel["advantages"]) == len(char_from_json["advantages"]))
    check("劣势数量一致", len(char_from_excel["disadvantages"]) == len(char_from_json["disadvantages"]))
    check("装备数量一致", len(char_from_excel["equipment"]) == len(char_from_json["equipment"]))

# summary
print(f"\n{'=' * 60}")
print(f"  结果: {passed} PASS / {failed} FAIL")
print(f"{'=' * 60}")
