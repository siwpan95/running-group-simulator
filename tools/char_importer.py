#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
角色卡 Excel 导入器 — Mirror of the Lost v3.1
=============================================
从 character.xlsx（5 Sheet）读取填好的角色卡 → 输出 character.json。

用法：
    # 导入单个角色卡
    python char_importer.py templates/characters/character.xlsx -o characters/my_char.json

    # 导入预置角色卡
    python char_importer.py templates/characters/预置-调查记者.xlsx

    # 批量导入目录下所有 .xlsx
    python char_importer.py templates/characters/ --all

    # 验证（只校验不导出）
    python char_importer.py templates/characters/character.xlsx --validate
"""

import json
import os
import sys
import argparse
from typing import Dict, List, Optional, Any
from openpyxl import load_workbook

# 项目根目录
_PT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CharImporter:
    """Excel 角色卡 → JSON 导入器"""

    # 技能难度到花费的映射（GURPS 标准）
    DIFFICULTY_COST = {"Easy": 1, "Avg": 2, "Hard": 4, "VH": 8}

    def __init__(self, budget: int = 100, verbose: bool = False):
        self.budget = budget
        self.verbose = verbose
        self.warnings: List[str] = []
        self.errors: List[str] = []

    # ─── 读取 Sheet 1: 属性 ───
    def _read_attributes(self, ws) -> Dict[str, Any]:
        """从属性 Sheet 读取键值对"""
        data = {}
        for row in ws.iter_rows(min_row=4, max_col=2, values_only=True):
            if row[0] is None:
                continue
            key = str(row[0]).strip()
            val = row[1]
            # 跳过空行和标题行
            if key.startswith("───") or key == "":
                continue
            data[key] = val

        result = {
            "name": data.get("角色名", "未命名角色"),
            "character_id": data.get("角色ID", "unnamed"),
            "st": int(data.get("ST (力量)", 10) or 10),
            "dx": int(data.get("DX (敏捷)", 10) or 10),
            "iq": int(data.get("IQ (智力)", 10) or 10),
            "ht": int(data.get("HT (体质)", 10) or 10),
            "focus_max": int(data.get("专注点上限", 3) or 3),
            "luck_max": int(data.get("幸运点上限", 2) or 2),
        }
        # 衍生值
        result["hp_max"] = int(data.get("HP 上限", result["st"]) or result["st"])
        result["fp_max"] = int(data.get("FP 上限", result["ht"]) or result["ht"])
        result["will"] = int(data.get("意志 Will", result["iq"]) or result["iq"])
        result["per"] = int(data.get("感知 Per", result["iq"]) or result["iq"])
        result["dodge"] = (result["dx"] + 2) // 2

        if self.verbose:
            print(f"  [属性] {result['name']}: ST{result['st']}/DX{result['dx']}/IQ{result['iq']}/HT{result['ht']}")

        return result

    # ─── 读取 Sheet 2: 技能 ───
    def _read_skills(self, ws) -> List[Dict[str, Any]]:
        """从技能 Sheet 读取技能列表"""
        skills = []
        for row in ws.iter_rows(min_row=4, max_col=6, values_only=True):
            if row[0] is None or str(row[0]).strip() == "":
                continue
            name = str(row[0]).strip()
            if name.startswith("───"):
                continue

            difficulty = str(row[1]).strip() if row[1] else "Avg"
            base_attr = str(row[2]).strip() if row[2] else "IQ"
            level = int(row[3]) if row[3] else 10
            points = int(row[4]) if row[4] else 0
            desc = str(row[5]) if row[5] else ""

            skills.append({
                "name": name,
                "difficulty": difficulty,
                "base_attribute": base_attr,
                "level": level,
                "points_spent": points,
                "description": desc,
            })

        if self.verbose:
            print(f"  [技能] 共 {len(skills)} 项: {', '.join(s['name'] for s in skills)}")
        return skills

    # ─── 读取 Sheet 3: 优劣势 ───
    def _read_advantages(self, ws) -> tuple:
        """从优劣势 Sheet 读取优势和劣势"""
        advantages = []
        disadvantages = []
        for row in ws.iter_rows(min_row=4, max_col=5, values_only=True):
            if row[1] is None or str(row[1]).strip() == "":
                continue
            ad_type = str(row[0]).strip() if row[0] else ""
            name = str(row[1]).strip()
            if name.startswith("───"):
                continue

            if ad_type == "优势":
                advantages.append(name)
            elif ad_type == "劣势":
                disadvantages.append(name)
            # 跳过汇总行

        if self.verbose:
            print(f"  [优劣势] 优势 {len(advantages)} 项, 劣势 {len(disadvantages)} 项")
        return advantages, disadvantages

    # ─── 读取 Sheet 4: 特征 ───
    def _read_features(self, ws) -> List[Dict[str, Any]]:
        """从特征 Sheet 读取特征列表"""
        features = []
        for row in ws.iter_rows(min_row=4, max_col=8, values_only=True):
            if row[0] is None or str(row[0]).strip() == "":
                continue
            name = str(row[0]).strip()
            if name.startswith("───"):
                continue

            features.append({
                "name": name,
                "trigger_condition": str(row[1]) if row[1] else "",
                "cost": int(row[2]) if row[2] else 1,
                "effect": str(row[3]) if row[3] else "",
                "per_scene_limit": int(row[4]) if row[4] else 1,
                "used_this_scene": 0,
            })

        if self.verbose:
            print(f"  [特征] 共 {len(features)} 项")
        return features

    # ─── 读取 Sheet 5: 装备 ───
    def _read_equipment(self, ws) -> List[Dict[str, Any]]:
        """从装备 Sheet 读取装备列表"""
        equipment = []
        for row in ws.iter_rows(min_row=4, max_col=9, values_only=True):
            if row[0] is None or str(row[0]).strip() == "":
                continue
            name = str(row[0]).strip()
            if name.startswith("───"):
                continue

            effects_raw = str(row[6]) if row[6] else "[]"
            # 尝试解析 JSON 格式的效果，失败则保持字符串
            try:
                effects = json.loads(effects_raw.replace("'", '"'))
            except (json.JSONDecodeError, TypeError):
                effects = []

            equipment.append({
                "name": name,
                "type": str(row[1]) if row[1] else "tool",
                "slot": str(row[2]) if row[2] else "backpack",
                "dr": int(row[3]) if row[3] else 0,
                "dr_location": str(row[4]) if row[4] else "",
                "damage": str(row[5]) if row[5] else "",
                "effects": effects,
                "uses": int(row[7]) if row[7] else -1,
                "description": str(row[8]) if row[8] else "",
            })

        if self.verbose:
            print(f"  [装备] 共 {len(equipment)} 项")
        return equipment

    # ─── 读取 Sheet 6: 锚点（可选）───
    def _read_anchors(self, ws) -> List[str]:
        """从锚点 Sheet 读取锚点列表"""
        anchors = []
        for row in ws.iter_rows(min_row=4, max_col=1, values_only=True):
            if row[0] is None or str(row[0]).strip() == "":
                continue
            name = str(row[0]).strip()
            if name.startswith("───"):
                continue
            anchors.append(name)

        if self.verbose:
            print(f"  [锚点] 共 {len(anchors)} 项")
        return anchors

    # ─── 导入入口 ───
    def import_xlsx(self, xlsx_path: str) -> Optional[Dict[str, Any]]:
        """从 Excel 文件导入角色卡，返回 JSON 兼容的 dict"""
        xlsx_path = os.path.abspath(xlsx_path)
        if not os.path.exists(xlsx_path):
            self.errors.append(f"文件不存在: {xlsx_path}")
            return None

        wb = load_workbook(xlsx_path, data_only=True)
        sheet_names = wb.sheetnames

        if self.verbose:
            print(f"\n导入: {os.path.basename(xlsx_path)}")

        # Sheet 1: 属性（必须）
        attrs = self._read_attributes(wb[sheet_names[0]])

        # Sheet 2: 技能（必须）
        skills = []
        if len(sheet_names) > 1:
            skills = self._read_skills(wb[sheet_names[1]])

        # Sheet 3: 优劣势
        advantages, disadvantages = [], []
        if len(sheet_names) > 2:
            advantages, disadvantages = self._read_advantages(wb[sheet_names[2]])

        # Sheet 4: 特征
        features = []
        if len(sheet_names) > 3:
            features = self._read_features(wb[sheet_names[3]])

        # Sheet 5: 装备
        equipment = []
        if len(sheet_names) > 4:
            equipment = self._read_equipment(wb[sheet_names[4]])

        # Sheet 6: 锚点（可选）
        anchors = []
        if len(sheet_names) > 5:
            anchors = self._read_anchors(wb[sheet_names[5]])

        wb.close()

        # 组装 JSON
        char_json = {
            "character_id": attrs["character_id"],
            "name": attrs["name"],
            "version": 1,
            "attributes": {
                "ST": attrs["st"], "DX": attrs["dx"], "IQ": attrs["iq"], "HT": attrs["ht"]
            },
            "secondary": {
                "HP": attrs["hp_max"], "FP": attrs["fp_max"],
                "Will": attrs["will"], "Per": attrs["per"]
            },
            "skills": skills,
            "advantages": advantages,
            "disadvantages": disadvantages,
            "features": features,
            "anchors": anchors,
            "equipment": equipment,
            "focus_max": attrs["focus_max"],
            "luck_max": attrs["luck_max"],
            "xp_log": [],
            "total_xp": 0,
        }

        # 预算校验
        self._validate_budget(attrs, skills, advantages, disadvantages)

        return char_json

    def _validate_budget(self, attrs, skills, advantages, disadvantages):
        """校验角色点数预算"""
        # 属性花费
        attr_cost = (
            (attrs["st"] - 10) * 10 +
            (attrs["dx"] - 10) * 20 +
            (attrs["iq"] - 10) * 20 +
            (attrs["ht"] - 10) * 10
        )
        # 技能花费
        skill_cost = sum(sk["points_spent"] for sk in skills)
        # 优劣净花费（简单估算）
        ad_cost = len(advantages) * 5 - len(disadvantages) * 5

        total = attr_cost + skill_cost + ad_cost

        if self.verbose:
            print(f"  [预算] 属性 {attr_cost} + 技能 {skill_cost} + 优劣 {ad_cost} = 总计 {total} (预算 {self.budget})")

        if total > self.budget:
            self.warnings.append(f"预算超支: {total}/{self.budget}")

    def export_json(self, char_json: Dict[str, Any], output_path: str):
        """导出为 JSON 文件"""
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(char_json, f, ensure_ascii=False, indent=2)
        if self.verbose:
            print(f"  ✅ 已导出: {output_path}")


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="角色卡 Excel 导入器 — Excel → character.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python char_importer.py templates/characters/character.xlsx -o characters/my_char.json
  python char_importer.py templates/characters/预置-调查记者.xlsx
  python char_importer.py templates/characters/ --all
  python char_importer.py templates/characters/character.xlsx --validate
        """,
    )
    parser.add_argument("path", help="Excel 文件路径或目录")
    parser.add_argument("-o", "--output", help="输出 JSON 路径")
    parser.add_argument("--all", action="store_true", help="批量导入目录下所有 .xlsx")
    parser.add_argument("--validate", action="store_true", help="仅校验不导出")
    parser.add_argument("--budget", type=int, default=100, help="点数预算（默认 100）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()
    importer = CharImporter(budget=args.budget, verbose=args.verbose)

    if args.all and os.path.isdir(args.path):
        # 批量导入
        xlsx_files = sorted(
            f for f in os.listdir(args.path) if f.endswith(".xlsx") and not f.startswith("~")
        )
        count = 0
        for fname in xlsx_files:
            xlsx_path = os.path.join(args.path, fname)
            char_json = importer.import_xlsx(xlsx_path)
            if char_json:
                out_name = fname.replace(".xlsx", ".json")
                out_path = os.path.join(_PT_DIR, "characters", out_name) if not args.validate else None
                if out_path and not args.validate:
                    importer.export_json(char_json, out_path)
                count += 1
        print(f"\n✅ 批量导入完成: {count}/{len(xlsx_files)} 个角色")

    elif args.path.endswith(".xlsx"):
        # 单个文件
        char_json = importer.import_xlsx(args.path)
        if char_json:
            if args.validate:
                print(f"\n✅ 校验通过: {char_json['name']} ({len(importer.warnings)} 警告)")
                if importer.warnings:
                    for w in importer.warnings:
                        print(f"  ⚠ {w}")
            else:
                out_path = args.output
                if not out_path:
                    base = os.path.splitext(os.path.basename(args.path))[0]
                    out_path = os.path.join(_PT_DIR, "characters", f"{base}.json")
                importer.export_json(char_json, out_path)
        else:
            print(f"❌ 导入失败: {importer.errors}")
            sys.exit(1)

    else:
        print("❌ 请指定 .xlsx 文件或使用 --all 批量导入目录")
        sys.exit(1)


if __name__ == "__main__":
    main()
