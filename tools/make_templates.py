#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Excel 模板生成器 — Mirror of the Lost v3.1
===========================================
一键生成全部 12 个 Excel 模板到 templates/ 目录。

用法：
    python make_templates.py          # 生成全部模板
    python make_templates.py --list   # 仅列出会生成哪些文件
"""

import os
import sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from copy import copy

# ============================================================
# 样式常量
# ============================================================
HEADER_FONT = Font(name="Microsoft YaHei", bold=True, size=11, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="16213E", end_color="16213E", fill_type="solid")
SUBHEADER_FILL = PatternFill(start_color="0F3460", end_color="0F3460", fill_type="solid")
LABEL_FONT = Font(name="Microsoft YaHei", bold=True, size=10)
BODY_FONT = Font(name="Microsoft YaHei", size=10)
FORMULA_FONT = Font(name="Consolas", size=10, color="E94560")
WARN_FILL = PatternFill(start_color="FFE0E0", end_color="FFE0E0", fill_type="solid")
OK_FILL = PatternFill(start_color="E0FFE0", end_color="E0FFE0", fill_type="solid")
TITLE_FONT = Font(name="Microsoft YaHei", bold=True, size=14, color="E94560")
THIN_BORDER = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)
BODY_FILL = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
ALT_FILL = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
CHAR_DIR = os.path.join(TEMPLATES_DIR, "characters")
GM_DATA_DIR = os.path.join(TEMPLATES_DIR, "gm-data")
GM_MODULE_DIR = os.path.join(TEMPLATES_DIR, "gm-module")
JSON_TEMPLATE_DIR = os.path.join(TEMPLATES_DIR, "json-templates")
os.makedirs(CHAR_DIR, exist_ok=True)
os.makedirs(GM_DATA_DIR, exist_ok=True)
os.makedirs(GM_MODULE_DIR, exist_ok=True)
os.makedirs(JSON_TEMPLATE_DIR, exist_ok=True)


# ============================================================
# 工具函数
# ============================================================
def _style_header(ws, row, ncols, fill=HEADER_FILL):
    """给标题行统一上色"""
    for col in range(1, ncols + 1):
        c = ws.cell(row=row, column=col)
        c.font = HEADER_FONT
        c.fill = fill
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = THIN_BORDER


def _style_body(ws, start_row, end_row, ncols):
    """给数据行统一样式"""
    for r in range(start_row, end_row + 1):
        fill = ALT_FILL if r % 2 == 0 else BODY_FILL
        for col in range(1, ncols + 1):
            c = ws.cell(row=r, column=col)
            c.font = BODY_FONT
            c.border = THIN_BORDER
            c.alignment = Alignment(vertical="center", wrap_text=True)
            if c.fill == PatternFill():  # 不覆盖已有 fill
                c.fill = fill


def _auto_width(ws, min_w=10, max_w=40):
    """自动列宽"""
    for col_cells in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col_cells[0].column)
        for cell in col_cells:
            if cell.value:
                # 估算中文字符宽度
                val_str = str(cell.value)
                char_len = sum(2 if ord(c) > 127 else 1 for c in val_str)
                max_len = max(max_len, char_len)
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, min_w), max_w)


def _add_title(ws, title, ncols):
    """在第一行写入 Sheet 类型标识 + 大标题"""
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(row=1, column=1, value=title)
    c.font = TITLE_FONT
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32


# ============================================================
# 1. 角色卡模板（5 Sheet）
# ============================================================
def make_character_template():
    """生成 character.xlsx — 5 Sheet 角色卡"""
    wb = openpyxl.Workbook()

    # ── Sheet 1: 属性 ──
    ws = wb.active
    ws.title = "属性"

    _add_title(ws, "#character_attributes    │    空白角色卡", 10)

    # A1 标识
    ws.cell(row=2, column=1, value="#character_attributes").font = Font(
        color="999999", size=8)

    headers = ["字段", "值", "花费点数", "说明", "自动计算", "公式", "", "", "", ""]
    for i, h in enumerate(headers, 1):
        ws.cell(row=3, column=i, value=h)
    _style_header(ws, 3, 5)

    # 属性数据行
    attrs = [
        ("角色名", "", "", "填写角色名字", "", ""),
        ("角色ID", "", "", "英文标识符，如 investigator_liming", "", ""),
        ("ST (力量)", 10, 0, "基础：10，每+1 花费 10 点", "", ""),
        ("DX (敏捷)", 10, 0, "基础：10，每+1 花费 20 点", "", ""),
        ("IQ (智力)", 10, 0, "基础：10，每+1 花费 20 点", "", ""),
        ("HT (体质)", 10, 0, "基础：10，每+1 花费 10 点", "", ""),
        ("", "", "", "", "", ""),
        ("─── 衍生值（自动计算）───", "", "", "", "", ""),
        ("HP 上限", "", "", "=ST（可单独购买±30%）", "=B5", "HP = ST"),
        ("FP 上限", "", "", "=HT", "=B8", "FP = HT"),
        ("基础速度", "", "", "=(DX+HT)/4", "=(B6+B8)/4", "Basic Speed"),
        ("基础移动", "", "", "=基础速度 取整", "=INT(B13)", "Basic Move"),
        ("闪避", "", "", "=(DX+2)/2", "=INT((B6+2)/2)", "Dodge"),
        ("意志 Will", "", "", "=IQ（可±30%）", "=B7", "Will = IQ"),
        ("感知 Per", "", "", "=IQ（可±30%）", "=B7", "Per = IQ"),
        ("", "", "", "", "", ""),
        ("─── 资源池 ───", "", "", "", "", ""),
        ("专注点上限", 3, "", "默认 3", "", ""),
        ("幸运点上限", 2, "", "默认 2", "", ""),
        ("", "", "", "", "", ""),
        ("─── 预算 ───", "", "", "", "", ""),
        ("可用点数", 100, "", "标准 100 点建卡", "", ""),
        ("属性花费", "", "", "ST 差值×10 + DX/IQ 差值×20 + HT 差值×10", "", ""),
        ("技能花费", "", "", "从 Sheet:技能 汇总", "", ""),
        ("优劣花费", "", "", "从 Sheet:优劣势 汇总", "", ""),
        ("剩余点数", "", "", "=可用-属性-技能-优劣", "=B24-B25-B26-B27", ""),
    ]
    for i, row_data in enumerate(attrs):
        r = i + 4
        for j, val in enumerate(row_data):
            ws.cell(row=r, column=j + 1, value=val)
    _style_body(ws, 4, 3 + len(attrs), 6)

    # ── Sheet 2: 技能 ──
    ws2 = wb.create_sheet("技能")
    _add_title(ws2, "#character_skills", 8)
    ws2.cell(row=2, column=1, value="#character_skills").font = Font(color="999999", size=8)

    skill_headers = ["技能名", "难度", "基础属性", "等级", "花费点数", "说明", "难度代码", "单价"]
    for i, h in enumerate(skill_headers, 1):
        ws2.cell(row=3, column=i, value=h)
    _style_header(ws2, 3, 8)

    # 预置示例行
    sample_skills = [
        ("调查", "Avg", "IQ", 14, 4, "核心调查技能", "E=1 A=2 H=4 VH=8", 2),
        ("潜行", "Avg", "DX", 11, 2, "隐匿移动", "", 2),
        ("话术", "Avg", "IQ", 13, 2, "交涉/说服", "", 2),
        ("", "", "", "", "", "", "", ""),
    ]
    for i, row_data in enumerate(sample_skills):
        r = i + 4
        for j, val in enumerate(row_data):
            ws2.cell(row=r, column=j + 1, value=val)
    _style_body(ws2, 4, 3 + len(sample_skills) + 10, 8)

    # 下拉：难度
    dv_skill_diff = DataValidation(type="list", formula1='"Easy,Avg,Hard,VH"', allow_blank=True)
    dv_skill_diff.prompt = "选择技能难度"
    ws2.add_data_validation(dv_skill_diff)
    dv_skill_diff.add(f"B4:B{3+len(sample_skills)+10}")

    # ── Sheet 3: 优劣势 ──
    ws3 = wb.create_sheet("优劣势")
    _add_title(ws3, "#character_ads", 7)
    ws3.cell(row=2, column=1, value="#character_ads").font = Font(color="999999", size=8)

    ad_headers = ["类型", "名称", "点数（优势+/劣势-）", "等级", "说明", "上限检查", ""]
    for i, h in enumerate(ad_headers, 1):
        ws3.cell(row=3, column=i, value=h)
    _style_header(ws3, 3, 6)

    sample_ads = [
        ("优势", "警觉", 5, 1, "Per +1", "", ""),
        ("优势", "快速反应", 15, 1, "所有先攻+1", "", ""),
        ("劣势", "好奇心（强烈）", -5, 1, "抵抗难度的自控检定", "劣势 ≥ -40", ""),
        ("劣势", "失眠", -10, 1, "HT-2 对抗失眠", "", ""),
        ("", "", "", "", "", "", ""),
        ("─── 汇总 ──", "", "", "", "", "", ""),
        ("优势合计", "", "", "", "", "", ""),
        ("劣势合计", "", "", "", "", "", ""),
        ("净花费", "=B8+B9", "", "", "", "", ""),
    ]
    for i, row_data in enumerate(sample_ads):
        r = i + 4
        for j, val in enumerate(row_data):
            ws3.cell(row=r, column=j + 1, value=val)
    _style_body(ws3, 4, 3 + len(sample_ads) + 5, 6)

    dv_ad_type = DataValidation(type="list", formula1='"优势,劣势"', allow_blank=True)
    ws3.add_data_validation(dv_ad_type)
    dv_ad_type.add(f"A4:A{3+len(sample_ads)+5}")

    # ── Sheet 4: 特征 ──
    ws4 = wb.create_sheet("特征")
    _add_title(ws4, "#character_features", 8)
    ws4.cell(row=2, column=1, value="#character_features").font = Font(color="999999", size=8)

    feat_headers = ["特征名", "触发条件", "专注点花费", "效果", "每场景上限", "已用次数", "永久执念", "来源"]
    for i, h in enumerate(feat_headers, 1):
        ws4.cell(row=3, column=i, value=h)
    _style_header(ws4, 3, 8)

    sample_feats = [
        ("记者的鼻子", "调查异常现象时", 1, "请求额外线索 / -2 对方对抗", 2, 0, "否", "记者"),
        ("经验直觉", "进入危险区域前", 1, "感知威胁方向/性质", 1, 0, "否", "记者"),
        ("可靠同伴", "同伴行动失败时", 1, "给同伴 +2 下次检定", 1, 0, "否", "记者"),
        ("", "", "", "", "", "", "", ""),
    ]
    for i, row_data in enumerate(sample_feats):
        r = i + 4
        for j, val in enumerate(row_data):
            ws4.cell(row=r, column=j + 1, value=val)
    _style_body(ws4, 4, 3 + len(sample_feats) + 5, 8)

    # ── Sheet 5: 装备 ──
    ws5 = wb.create_sheet("装备")
    _add_title(ws5, "#character_equipment", 9)
    ws5.cell(row=2, column=1, value="#character_equipment").font = Font(color="999999", size=8)

    equip_headers = ["装备名", "类型", "槽位", "DR", "DR部位", "伤害", "效果", "使用次数", "描述"]
    for i, h in enumerate(equip_headers, 1):
        ws5.cell(row=3, column=i, value=h)
    _style_header(ws5, 3, 9)

    sample_equip = [
        ("手电筒", "tool", "hand", 0, "", "", "移除:低能见度", -1, "老式手电筒"),
        ("笔记本", "key_item", "backpack", 0, "", "", "", -1, "浸水但还能用的笔记本"),
        ("", "", "", "", "", "", "", "", ""),
    ]
    for i, row_data in enumerate(sample_equip):
        r = i + 4
        for j, val in enumerate(row_data):
            ws5.cell(row=r, column=j + 1, value=val)
    _style_body(ws5, 4, 3 + len(sample_equip) + 5, 9)

    dv_equip_type = DataValidation(
        type="list", formula1='"weapon,armor,tool,consumable,key_item"', allow_blank=True)
    ws5.add_data_validation(dv_equip_type)
    dv_equip_type.add(f"B4:B{3+len(sample_equip)+5}")

    # 保存
    path = os.path.join(CHAR_DIR, "character.xlsx")
    _auto_width(ws); _auto_width(ws2); _auto_width(ws3); _auto_width(ws4); _auto_width(ws5)
    wb.save(path)
    return path


# ============================================================
# 2. 敌人构建器
# ============================================================
def make_enemy_template():
    """生成 enemy_builder.xlsx"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "敌人"

    _add_title(ws, "#enemy_builder    │    敌人/NPC 属性模板", 14)
    headers = [
        "敌人名", "类型", "HP", "HP上限", "FP", "ST", "DX", "IQ", "HT",
        "近战技能", "伤害", "闪避", "DR", "描述", "风味文字",
        "特殊能力—名称", "特殊能力—效果", "特殊能力—触发",
        "附庸阈值—>=6", "附庸阈值—2-5", "附庸阈值—<2",
    ]
    for i, h in enumerate(headers, 1):
        ws.cell(row=3, column=i, value=h)
    _style_header(ws, 3, len(headers))

    sample = [
        ("巨鼠群", "mook", 10, 10, "", "", "", "", "",
         12, "1d-4 cut", 9, 0, "变异鼠群", "眼睛泛银光",
         "群扑", "Deceptive Attack -2防御", "attack",
         "立即移除", "丧失行动力/溃逃", "轻微干扰"),
        ("镜中倒影", "wildcard", 12, 12, 12, 11, 12, 10, 12,
         14, "2d6 cut", 10, 2, "镜像体，动作左右相反", "微笑上下颠倒",
         "镜像反转", "攻击被反射", "always",
         "", "", ""),
        ("镜中守卫", "mook", 10, 10, "", "", "", "", "",
         11, "1d6 cut", 8, 1, "从镜中伸出的苍白手臂", "非实体——铜镜的碎片",
         "", "", "",
         "立即消散", "缩回镜中", "暂时畏缩"),
    ]
    for i, row_data in enumerate(sample):
        r = i + 4
        for j, val in enumerate(row_data):
            ws.cell(row=r, column=j + 1, value=val)
    _style_body(ws, 4, 3 + len(sample) + 15, len(headers))

    dv_enemy_type = DataValidation(type="list", formula1='"mook,elite,wildcard,boss"', allow_blank=True)
    ws.add_data_validation(dv_enemy_type)
    dv_enemy_type.add(f"B4:B{3+len(sample)+15}")

    path = os.path.join(GM_DATA_DIR, "enemy_builder.xlsx")
    _auto_width(ws)
    wb.save(path)
    return path


# ============================================================
# 3. 物品构建器
# ============================================================
def make_item_template():
    """生成 item_builder.xlsx"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "物品"

    _add_title(ws, "#item_builder    │    物品/装备属性模板", 12)
    headers = [
        "物品ID", "名称", "类型", "槽位", "DR", "DR部位", "伤害",
        "效果1—类型", "效果1—值", "使用次数", "描述", "备注"
    ]
    for i, h in enumerate(headers, 1):
        ws.cell(row=3, column=i, value=h)
    _style_header(ws, 3, len(headers))

    sample = [
        ("手电筒", "手电筒", "tool", "hand", 0, "",
         "", "tag_mod", "remove:低能见度", -1, "老式手电筒，电池还很足", "范围5m"),
        ("急救包", "急救包", "consumable", "backpack", 0, "",
         "", "restore_hp", "1d6", 1, "绷带和消毒液", ""),
        ("防弹背心", "防弹背心", "armor", "body", 4, "躯干",
         "", "penalty", "dx:-1", -1, "轻型防弹背心", "影响灵活性"),
        ("手枪", "手枪", "weapon", "hand", 0, "",
         "2d6 pi+", "", "", -1, "标准9mm半自动手枪", ""),
        ("撬棍", "撬棍", "tool", "hand", 0, "",
         "1d6+1 cr", "tool_bonus", "ST:+2", -1, "破门破墙", "兼作武器"),
        ("铜镜", "铜镜", "key_item", "hand", 0, "",
         "", "psychic_resistance", "-1", -1, "直径20cm古铜镜", "镜背有倒转炼金符号"),
    ]
    for i, row_data in enumerate(sample):
        r = i + 4
        for j, val in enumerate(row_data):
            ws.cell(row=r, column=j + 1, value=val)
    _style_body(ws, 4, 3 + len(sample) + 10, len(headers))

    dv_item_type = DataValidation(
        type="list", formula1='"weapon,armor,tool,consumable,key_item"', allow_blank=True)
    ws.add_data_validation(dv_item_type)
    dv_item_type.add(f"C4:C{3+len(sample)+10}")

    path = os.path.join(GM_DATA_DIR, "item_builder.xlsx")
    _auto_width(ws)
    wb.save(path)
    return path


# ============================================================
# 4. 陷阱构建器
# ============================================================
def make_trap_template():
    """生成 trap_builder.xlsx"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "陷阱"

    _add_title(ws, "#trap_builder    │    陷阱/机关模板", 10)
    headers = [
        "陷阱ID", "名称", "触发条件", "察觉检定", "DC",
        "伤害/效果", "伤害掷骰", "解除检定", "解除DC", "备注"
    ]
    for i, h in enumerate(headers, 1):
        ws.cell(row=3, column=i, value=h)
    _style_header(ws, 3, len(headers))

    sample = [
        ("trap_silver_wire", "银丝绊线", "穿过门框时触碰", "Per-2", 12,
         "银丝割伤——银对镜中生物有额外腐蚀", "1d6+1 cut + 镜中生物额外1d6", "DX-2 (拆除陷阱)", 14,
         "可用镜子反射发现银光"),
        ("trap_mirror_shard", "镜片雨", "触碰铜镜时", "Per", 10,
         "天花板镜片倾泻而下", "1d6 imp", "无（触发型）", 0,
         "可提前用Per-2发现天花板裂缝"),
    ]
    for i, row_data in enumerate(sample):
        r = i + 4
        for j, val in enumerate(row_data):
            ws.cell(row=r, column=j + 1, value=val)
    _style_body(ws, 4, 3 + len(sample) + 10, len(headers))

    path = os.path.join(GM_DATA_DIR, "trap_builder.xlsx")
    _auto_width(ws)
    wb.save(path)
    return path


# ============================================================
# 5. 随机遭遇表
# ============================================================
def make_encounter_template():
    """生成 encounter_table.xlsx"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "遭遇"

    _add_title(ws, "#encounter_table    │    随机遭遇表", 9)
    headers = [
        "区域", "掷骰下限", "掷骰上限", "遭遇内容", "敌人引用",
        "难度", "数量", "战利品", "备注"
    ]
    for i, h in enumerate(headers, 1):
        ws.cell(row=3, column=i, value=h)
    _style_header(ws, 3, len(headers))

    sample = [
        ("镜屋走廊", 1, 30, "无事发生", "", "", "", "", ""),
        ("镜屋走廊", 31, 55, "诡异低语——Per 检定或 Will-2", "", "中", "", "", "精神干扰"),
        ("镜屋走廊", 56, 80, "巨鼠群（3-6只）", "巨鼠群", "低", "1d3+2", "随机杂物×1d3", ""),
        ("镜屋走廊", 81, 95, "镜中守卫（1-2）", "镜中守卫", "中", "1d2", "铜镜碎片×1d2", ""),
        ("镜屋走廊", 96, 100, "镜中倒影", "镜中倒影", "高", 1, "镜之记忆（关键物品）", "Boss 级别"),
        ("", "", "", "", "", "", "", "", ""),
        ("鏡屋大厅", 1, 40, "空荡大厅", "", "", "", "", ""),
        ("鏡屋大厅", 41, 70, "镜中低语——IQ检定", "", "低", "", "", ""),
        ("鏡屋大厅", 71, 100, "镜中守卫（2-4）", "镜中守卫", "中高", "2d2", "", ""),
    ]
    for i, row_data in enumerate(sample):
        r = i + 4
        for j, val in enumerate(row_data):
            ws.cell(row=r, column=j + 1, value=val)
    _style_body(ws, 4, 3 + len(sample) + 10, len(headers))

    path = os.path.join(GM_DATA_DIR, "encounter_table.xlsx")
    _auto_width(ws)
    wb.save(path)
    return path


# ============================================================
# 6. 战利品表
# ============================================================
def make_loot_template():
    """生成 loot_table.xlsx"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "战利品"

    _add_title(ws, "#loot_table    │    战利品表", 8)
    headers = [
        "敌人/来源", "掷骰下限", "掷骰上限", "掉落物品ID", "数量",
        "品质", "描述", "备注"
    ]
    for i, h in enumerate(headers, 1):
        ws.cell(row=3, column=i, value=h)
    _style_header(ws, 3, len(headers))

    sample = [
        ("巨鼠群", 1, 50, "无", "", "", "", "鼠尸没什么价值"),
        ("巨鼠群", 51, 85, "随机杂物", "1d2", "普通", "旧钥匙/硬币/碎布", ""),
        ("巨鼠群", 86, 100, "小急救包", 1, "普通", "恢复 1d3 HP", ""),
        ("镜中守卫", 1, 60, "铜镜碎片", "1d2", "普通", "可合成修复铜镜", ""),
        ("镜中守卫", 61, 100, "银质反光粉", "1d3", "优良", "投掷降低镜中生物2闪避", ""),
        ("镜中倒影", 1, 100, "镜之记忆", 1, "关键物品", "镜中倒影消失后残留的银色结晶", "主线物品"),
    ]
    for i, row_data in enumerate(sample):
        r = i + 4
        for j, val in enumerate(row_data):
            ws.cell(row=r, column=j + 1, value=val)
    _style_body(ws, 4, 3 + len(sample) + 10, len(headers))

    path = os.path.join(GM_DATA_DIR, "loot_table.xlsx")
    _auto_width(ws)
    wb.save(path)
    return path


# ============================================================
# 7. NPC 反应表
# ============================================================
def make_reaction_template():
    """生成 npc_reaction.xlsx"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "NPC反应"

    _add_title(ws, "#npc_reaction    │    NPC 反应表（GURPS 反应规则）", 7)
    headers = [
        "反应掷骰结果", "态度", "行为描述", "交涉修正", "战斗意愿", "帮助意愿", "备注"
    ]
    for i, h in enumerate(headers, 1):
        ws.cell(row=3, column=i, value=h)
    _style_header(ws, 3, len(headers))

    sample = [
        ("≤0", "灾难", "立即攻击或背叛", "不可交涉", "必定", "否", "除非有特殊理由"),
        ("1-3", "很差", "敌视、拒绝合作", "严厉 -2", "很可能", "否", ""),
        ("4-6", "较差", "冷淡、不情愿", "态度 -1", "可能", "需条件", ""),
        ("7-9", "中立", "按常理行事", "无修正", "视情况", "视情况", "默认态度"),
        ("10-12", "较好", "友善、愿意帮忙", "态度 +1", "否", "微小帮助", ""),
        ("13-15", "很好", "热情、主动协助", "态度 +2", "否", "显著帮助", ""),
        ("16+", "极好", "忠诚、全力以赴", "态度 +3", "否", "全力帮助", "罕见"),
    ]
    for i, row_data in enumerate(sample):
        r = i + 4
        for j, val in enumerate(row_data):
            ws.cell(row=r, column=j + 1, value=val)
    _style_body(ws, 4, 3 + len(sample), len(headers))

    path = os.path.join(GM_DATA_DIR, "npc_reaction.xlsx")
    _auto_width(ws)
    wb.save(path)
    return path


# ============================================================
# 8. 场景构建表（最核心的主持人工具）
# ============================================================
def make_scene_builder_template():
    """生成 scene_builder.xlsx — 每个 Sheet = 一幕，每行 = 一个节点"""
    wb = openpyxl.Workbook()

    scene_headers = [
        "场景ID", "场景类型", "触发描述", "前置节点", "后续节点",
        "检定技能", "修正值", "成功叙事", "失败叙事", "大成功叙事",
        "嵌套检定—技能", "嵌套检定—结果", "嵌套检定—flag",
        "敌人类型", "敌人名", "近战技能", "伤害", "闪避", "HP", "DR",
        "特殊机制—名", "特殊机制—效果", "特殊机制—反制",
        "印记触发等级", "印记检定", "印记失败花费", "印记失败效果",
        "flag设置", "flag清除", "环境标签—增", "环境标签—删",
        "先攻规则", "时间压力", "用时(秒)", "备注"
    ]

    # ── Act 1: 镜屋初探 ──
    ws1 = wb.active
    ws1.title = "Act1_镜屋初探"
    _add_title(ws1, "#scene_builder_Act1    │    第一幕：镜屋初探", len(scene_headers))

    for i, h in enumerate(scene_headers, 1):
        ws1.cell(row=3, column=i, value=h)
    _style_header(ws1, 3, len(scene_headers))

    act1_nodes = [
        ("1.1_arrival", "perception", "站在镜屋胡同入口——你听到了什么？",
         "", "1.2_investigate",
         "感知（听觉）", -2, "隐约传来镜面摩擦声和轻微啜泣", "只有风声", "清晰分辨出'救救我'的低语+来源方向",
         "", "", "", "", "", "", "", "", "", "", "", "",
         "", "", "", "", "", "", "", "进入镜屋胡同", "", 30, ""),
        ("1.2_investigate", "investigation", "满地碎镜片——发现线索？",
         "1.1_arrival", "1.3_feat|2.1_rats",
         "调查", -1, "角落捡到浸水的笔记本——记录着陈叔的最后一次巡视日期", "只找到碎镜片", "找到笔记本+一张褪色全家福",
         "摄影", "拍下碎裂图案——镜片排列成某种符号", "found_clue",
         "", "", "", "", "", "", "", "", "", "", "",
         "", "接触", "感知 vs 诡异度(10)", 1, "微弱的镜中视线注视着你——心理印记+1",
         "", "", "", "", "", 45, ""),
        ("1.3_feat", "feat", "铁门生锈卡死——用力撞开？",
         "1.2_investigate", "2.1_rats",
         "力量", -3, "砰！铁门撞开", "肩膀撞疼了但门没动（可重试/HP-1）", "铁门直接飞出去+震慑镜后生物1回合",
         "", "", "",
         "", "", "", "", "", "", "", "", "", "",
         "", "", "", "", "", "", "打开通路", "", "", "", 15, "撬棍/斧头可降低修正"),
    ]
    for i, row_data in enumerate(act1_nodes):
        r = i + 4
        for j, val in enumerate(row_data):
            ws1.cell(row=r, column=j + 1, value=val)
    _style_body(ws1, 4, 3 + len(act1_nodes) + 5, len(scene_headers))

    dv_scene_type = DataValidation(
        type="list", formula1='"perception,investigation,feat,combat,explore"', allow_blank=True)
    ws1.add_data_validation(dv_scene_type)
    dv_scene_type.add(f"B4:B{3+len(act1_nodes)+5}")

    # ── Act 2: 镜中深处 ──
    ws2 = wb.create_sheet("Act2_镜中深处")
    _add_title(ws2, "#scene_builder_Act2    │    第二幕：镜中深处", len(scene_headers))
    for i, h in enumerate(scene_headers, 1):
        ws2.cell(row=3, column=i, value=h)
    _style_header(ws2, 3, len(scene_headers))

    act2_nodes = [
        ("2.1_rats", "combat", "暗处窸窣——巨鼠群围上来！",
         "1.2_investigate|1.3_feat", "2.2_mirror",
         "", 0, "鼠群四散", "被咬了好几口", "",
         "", "", "",
         "mook", "巨鼠群", 12, "1d-4 cut", 9, 10, 0,
         "群扑", "Deceptive Attack -2 防御", "后退靠墙可消除",
         "", "", "", "", "", "", "", "", "", 60, "附庸规则：≥6伤立即移除"),
        ("2.2_mirror", "perception", "走廊尽头——一面巨大的铜镜",
         "2.1_rats", "3.1_boss",
         "感知（视觉）", 0, "镜面浮现模糊人形轮廓", "什么也没看到", "清晰看到镜中倒影的下一步动作",
         "", "", "", "", "", "", "", "", "", "", "", "",
         "", "对峙", "意志 vs 诡异度(12)", 2, "镜中凝视渗透意识——心理印记+1",
         "", "", "低能见度:镜光", "", "", 30, ""),
    ]
    for i, row_data in enumerate(act2_nodes):
        r = i + 4
        for j, val in enumerate(row_data):
            ws2.cell(row=r, column=j + 1, value=val)
    _style_body(ws2, 4, 3 + len(act2_nodes) + 5, len(scene_headers))

    dv_scene_type2 = DataValidation(
        type="list", formula1='"perception,investigation,feat,combat,explore"', allow_blank=True)
    ws2.add_data_validation(dv_scene_type2)
    dv_scene_type2.add(f"B4:B{3+len(act2_nodes)+5}")

    # ── Act 3: 终局 ──
    ws3 = wb.create_sheet("Act3_终局")
    _add_title(ws3, "#scene_builder_Act3    │    第三幕：终局", len(scene_headers))
    for i, h in enumerate(scene_headers, 1):
        ws3.cell(row=3, column=i, value=h)
    _style_header(ws3, 3, len(scene_headers))

    act3_nodes = [
        ("3.1_boss", "combat", "镜中倒影——一模一样的面孔从镜面走出来",
         "2.2_mirror", "3.2_ending",
         "", 0, "倒影碎裂消散", "被弱点打击", "",
         "", "", "",
         "wildcard", "镜中倒影", 14, "2d6 cut", 10, 12, 2,
         "镜像反转+反伤", "攻击被反射(IQ/战术逆转)；直接攻击镜子=自身受同等伤害。",
         "用镜子反射→逆转攻击；必须先破镜再攻击。",
         "崩溃", "意志 vs 诡异度(15)", 3, "镜中倒影的绝望渗透——心理印记+2",
         "", "", "终止", "", "", 120, "Boss战——多阶段（镜像反转+直接反伤两层机制）"),
        ("3.2_ending", "explore", "铜镜恢复平静——作出选择",
         "3.1_boss", "",
         "", 0, "选择：封印铜镜 / 带走铜镜 / 打碎铜镜", "", "",
         "", "", "", "", "", "", "", "", "", "", "", "", "",
         "", "", "", "", "", "", "", "", "", "", 30, "三结局分支"),
    ]
    for i, row_data in enumerate(act3_nodes):
        r = i + 4
        for j, val in enumerate(row_data):
            ws3.cell(row=r, column=j + 1, value=val)
    _style_body(ws3, 4, 3 + len(act3_nodes) + 5, len(scene_headers))

    dv_scene_type3 = DataValidation(
        type="list", formula1='"perception,investigation,feat,combat,explore"', allow_blank=True)
    ws3.add_data_validation(dv_scene_type3)
    dv_scene_type3.add(f"B4:B{3+len(act3_nodes)+5}")

    for ws in [ws1, ws2, ws3]:
        _auto_width(ws, min_w=12, max_w=45)

    path = os.path.join(GM_MODULE_DIR, "scene_builder.xlsx")
    wb.save(path)
    return path


# ============================================================
# 9. 模组元信息表
# ============================================================
def make_module_meta_template():
    """生成 module_meta.xlsx"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "模组信息"

    _add_title(ws, "#module_meta    │    模组全局元信息", 5)
    headers = ["字段", "值", "说明", "示例", ""]
    for i, h in enumerate(headers, 1):
        ws.cell(row=3, column=i, value=h)
    _style_header(ws, 3, 5)

    fields = [
        ("module_id", "", "英文标识符", "mirror_house_alley"),
        ("system_name", "Mirror of the Lost", "系统名（固定）", "Mirror of the Lost"),
        ("module_title", "", "模组中文标题", "镜屋胡同"),
        ("version", "2.0", "模组版本", "2.0"),
        ("author", "", "作者", "全哥"),
        ("playstyle", "", "风格标签", "都市恐怖"),
        ("estimated_duration", "", "预计时长", "2-4小时"),
        ("player_count", "", "建议玩家数", "2-4人"),
        ("synopsis", "", "一句话简介", "被废弃的镜屋胡同传来求救声..."),
        ("base_xp", 3, "基础 XP 奖励", "3"),
        ("", "", "", ""),
        ("─── NPC 清单 ───", "", "", ""),
        ("NPC名1", "", "角色描述/作用/位置", "陈叔——失踪的老更夫"),
        ("NPC名2", "", "", ""),
        ("", "", "", ""),
        ("─── 关键物品清单 ───", "", "", ""),
        ("铜镜", "", "来源/用途", "终局关键物品"),
        ("笔记本", "", "", "陈叔的调查笔记"),
        ("", "", "", ""),
        ("─── 结局分支 ───", "", "", ""),
        ("封印结局", "", "条件/描述", "破解镜像反转→封印铜镜"),
        ("带走结局", "", "条件/描述", "意志对抗成功→带走铜镜"),
        ("打碎结局", "", "条件/描述", "直接破坏铜镜（后果未知）"),
        ("", "", "", ""),
        ("─── 时间线 ───", "", "", ""),
        ("第一幕", "镜屋初探", "约30分钟", "感知→调查→壮举"),
        ("第二幕", "镜中深处", "约45分钟", "战斗→探索→对峙"),
        ("第三幕", "终局", "约30分钟", "Boss战→结局选择"),
    ]
    for i, row_data in enumerate(fields):
        r = i + 4
        for j, val in enumerate(row_data):
            ws.cell(row=r, column=j + 1, value=val)
    _style_body(ws, 4, 3 + len(fields), 5)

    path = os.path.join(GM_MODULE_DIR, "module_meta.xlsx")
    _auto_width(ws, min_w=15)
    wb.save(path)
    return path


# ============================================================
# 10. 网格地图
# ============================================================
def make_map_grid_template():
    """生成 map_grid.xlsx — 用 Excel 格子画地图"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "镜屋胡同地图"

    _add_title(ws, "#map_grid    │    镜屋胡同 — 用 Excel 格子画地图", 20)

    # 图例
    legend = [
        ("", "", "", "🗺️ 图例", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
        ("", "", "", "■ 深灰 = 墙壁/障碍", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
        ("", "", "", "□ 白 = 可通行区域", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
        ("", "", "", "● 红 = 玩家起始位置", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
        ("", "", "", "🔵 蓝 = 场景节点", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
        ("", "", "", "🟡 黄 = 遭遇触发区", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
        ("", "", "", "🟢 绿 = 安全节点", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
        ("", "", "", "⬜ 边框 = 区域边界", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ]
    for i, row_data in enumerate(legend):
        r = i + 3
        for j, val in enumerate(row_data):
            ws.cell(row=r, column=j + 1, value=val)

    # 地图网格 (12×18)
    map_data = [
        "■■■■■■■■■■■■■■■■■■",
        "■  □  □  □  ■  □  □  ■",
        "■  □  □  □  ■  □  □  ■",
        "■  □  🔵 □  □  □  □  ■",
        "■■■■  ■■■■■■■■■  ■■■",
        "■  □  □  □  □  □  □  ■",
        "■  □  🟡 □  □  🟡 □  ■",
        "■  □  □  □  □  □  □  ■",
        "■■■■■■■  ■■■■■■■■■■■",
        "■  □  □  ■  □  □  □  ■",
        "■  ●  □  ■  □  □  □  ■",
        "■  □  □  ■  □  □  🔵 ■",
        "■■■■■■■■■■■■■■■■■■",
    ]

    # Color coding
    WALL_FILL = PatternFill(start_color="555555", end_color="555555", fill_type="solid")
    FLOOR_FILL = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
    START_FILL = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
    NODE_FILL = PatternFill(start_color="4DA6FF", end_color="4DA6FF", fill_type="solid")
    ENCOUNTER_FILL = PatternFill(start_color="FFD93D", end_color="FFD93D", fill_type="solid")

    for ri, row_str in enumerate(map_data):
        r = ri + 12  # start below legend
        for ci, ch in enumerate(row_str):
            cell = ws.cell(row=r, column=ci + 1, value=ch)
            cell.alignment = Alignment(horizontal="center", vertical="center")

            if ch == "■":
                cell.fill = WALL_FILL
                cell.font = Font(color="555555", size=10)
            elif ch == "●":
                cell.fill = START_FILL
                cell.font = Font(color="FFFFFF", bold=True, size=10)
            elif ch == "🔵":
                cell.fill = NODE_FILL
                cell.font = Font(size=10)
            elif ch == "🟡":
                cell.fill = ENCOUNTER_FILL
                cell.font = Font(size=10)
            else:
                cell.fill = FLOOR_FILL

    # 设置行高列宽为正方形
    for col in range(1, 21):
        ws.column_dimensions[get_column_letter(col)].width = 3.5
    for row in range(12, 12 + len(map_data)):
        ws.row_dimensions[row].height = 20

    # 场景节点标注
    annotations = [
        ("🔵1", "节点 1.1 — 胡同入口（Perception 感知检定）"),
        ("🟡1", "遭遇触发 — 巨鼠群（Combat）"),
        ("🟡2", "遭遇触发 — 镜中守卫（Combat）"),
        ("🔵2", "节点 3.1 — Boss 战：镜中倒影"),
    ]
    for i, (label, desc) in enumerate(annotations):
        ws.cell(row=12 + len(map_data) + 2 + i, column=1, value=label).font = Font(bold=True, size=10)
        ws.cell(row=12 + len(map_data) + 2 + i, column=2, value=desc).font = Font(size=10)

    path = os.path.join(GM_MODULE_DIR, "map_grid.xlsx")
    wb.save(path)
    return path


# ============================================================
# 11-14. 预置角色卡 Excel（4 个）
# ============================================================
def make_preset_character_xlsx(name, char_id, attrs_data, skills, advantages, disadvantages, features, equipment, anchors, base_dir=CHAR_DIR):
    """生成单个预置角色卡的 Excel 文件"""
    wb = openpyxl.Workbook()

    # ── Sheet 1: 属性 ──
    ws = wb.active
    ws.title = "属性"

    _add_title(ws, f"#character_attributes    │    {name}", 7)
    headers = ["字段", "值", "说明", "花费点数", "自动计算", "公式", ""]
    for i, h in enumerate(headers, 1):
        ws.cell(row=3, column=i, value=h)
    _style_header(ws, 3, 7)

    st, dx, iq, ht = attrs_data
    hp = st
    fp = ht
    will = iq
    per = iq

    attr_rows = [
        ("角色名", name, "预置角色", "", "", ""),
        ("角色ID", char_id, "英文标识符", "", "", ""),
        ("ST (力量)", st, "力量", (st - 10) * 10, "", f"=(B4-10)*10"),
        ("DX (敏捷)", dx, "敏捷", (dx - 10) * 20, "", f"=(B5-10)*20"),
        ("IQ (智力)", iq, "智力", (iq - 10) * 20, "", f"=(B6-10)*20"),
        ("HT (体质)", ht, "体质", (ht - 10) * 10, "", f"=(B7-10)*10"),
        ("", "", "", "", "", ""),
        ("─── 衍生值 ───", "", "", "", "", ""),
        ("HP 上限", hp, "=ST", "", "", ""),
        ("FP 上限", fp, "=HT", "", "", ""),
        ("闪避", (dx + 2) // 2, "=(DX+2)/2", "", "", ""),
        ("意志 Will", will, "=IQ", "", "", ""),
        ("感知 Per", per, "=IQ", "", "", ""),
        ("", "", "", "", "", ""),
        ("专注点上限", 3, "默认3", "", "", ""),
        ("幸运点上限", 2, "默认2", "", "", ""),
    ]
    for i, row_data in enumerate(attr_rows):
        r = i + 4
        for j, val in enumerate(row_data):
            ws.cell(row=r, column=j + 1, value=val)
    _style_body(ws, 4, 3 + len(attr_rows), 7)

    # ── Sheet 2: 技能 ──
    ws2 = wb.create_sheet("技能")
    _add_title(ws2, f"#character_skills    │    {name}", 8)
    skill_headers = ["技能名", "难度", "基础属性", "等级", "花费点数", "说明", "难度代码", "单价"]
    for i, h in enumerate(skill_headers, 1):
        ws2.cell(row=3, column=i, value=h)
    _style_header(ws2, 3, 8)

    for i, sk in enumerate(skills):
        r = i + 4
        ws2.cell(row=r, column=1, value=sk["name"])
        ws2.cell(row=r, column=2, value=sk.get("difficulty", "Avg"))
        ws2.cell(row=r, column=3, value=sk.get("base_attribute", "IQ"))
        ws2.cell(row=r, column=4, value=sk.get("level", 10))
        ws2.cell(row=r, column=5, value=sk.get("points_spent", 0))
        ws2.cell(row=r, column=6, value=sk.get("description", ""))
        ws2.cell(row=r, column=7, value="E=1 A=2 H=4 VH=8")
        ws2.cell(row=r, column=8, value=sk.get("points_spent", 0))
    _style_body(ws2, 4, 3 + len(skills) + 5, 8)

    # ── Sheet 3: 优劣势 ──
    ws3 = wb.create_sheet("优劣势")
    _add_title(ws3, f"#character_ads    │    {name}", 6)
    ad_headers = ["类型", "名称", "点数", "等级", "说明", ""]
    for i, h in enumerate(ad_headers, 1):
        ws3.cell(row=3, column=i, value=h)
    _style_header(ws3, 3, 6)

    row_offset = 4
    for adv in advantages:
        ws3.cell(row=row_offset, column=1, value="优势")
        ws3.cell(row=row_offset, column=2, value=adv)
        ws3.cell(row=row_offset, column=5, value="")
        row_offset += 1
    for dis in disadvantages:
        ws3.cell(row=row_offset, column=1, value="劣势")
        ws3.cell(row=row_offset, column=2, value=dis)
        ws3.cell(row=row_offset, column=5, value="")
        row_offset += 1
    _style_body(ws3, 4, row_offset + 5, 6)

    # ── Sheet 4: 特征 ──
    ws4 = wb.create_sheet("特征")
    _add_title(ws4, f"#character_features    │    {name}", 8)
    feat_headers = ["特征名", "触发条件", "专注点花费", "效果", "每场景上限", "已用次数", "永久执念", "来源"]
    for i, h in enumerate(feat_headers, 1):
        ws4.cell(row=3, column=i, value=h)
    _style_header(ws4, 3, 8)

    for i, ft in enumerate(features):
        r = i + 4
        ws4.cell(row=r, column=1, value=ft.get("name", ""))
        ws4.cell(row=r, column=2, value=ft.get("trigger_condition", ""))
        ws4.cell(row=r, column=3, value=ft.get("cost", 1))
        ws4.cell(row=r, column=4, value=ft.get("effect", ""))
        ws4.cell(row=r, column=5, value=ft.get("per_scene_limit", 1))
        ws4.cell(row=r, column=6, value=0)
        ws4.cell(row=r, column=7, value="否")
        ws4.cell(row=r, column=8, value=ft.get("source", ""))
    _style_body(ws4, 4, 3 + len(features) + 5, 8)

    # ── Sheet 5: 装备 ──
    ws5 = wb.create_sheet("装备")
    _add_title(ws5, f"#character_equipment    │    {name}", 9)
    equip_headers = ["装备名", "类型", "槽位", "DR", "DR部位", "伤害", "效果", "使用次数", "描述"]
    for i, h in enumerate(equip_headers, 1):
        ws5.cell(row=3, column=i, value=h)
    _style_header(ws5, 3, 9)

    for i, eq in enumerate(equipment):
        r = i + 4
        ws5.cell(row=r, column=1, value=eq.get("name", ""))
        ws5.cell(row=r, column=2, value=eq.get("type", ""))
        ws5.cell(row=r, column=3, value=eq.get("slot", ""))
        ws5.cell(row=r, column=4, value=eq.get("dr", 0))
        ws5.cell(row=r, column=5, value=eq.get("dr_location", ""))
        ws5.cell(row=r, column=6, value=eq.get("damage", ""))
        ws5.cell(row=r, column=7, value=str(eq.get("effects", "")))
        ws5.cell(row=r, column=8, value=eq.get("uses", -1))
        ws5.cell(row=r, column=9, value=eq.get("description", ""))
    _style_body(ws5, 4, 3 + len(equipment) + 5, 9)

    # ── Sheet 6: 锚点 ──
    ws6 = wb.create_sheet("锚点")
    _add_title(ws6, f"#character_anchors    │    {name}", 3)
    ws6.cell(row=3, column=1, value="锚点").font = HEADER_FONT
    ws6.cell(row=3, column=1).fill = HEADER_FILL
    ws6.cell(row=3, column=2, value="说明").font = HEADER_FONT
    ws6.cell(row=3, column=2).fill = HEADER_FILL

    for i, anchor in enumerate(anchors):
        r = i + 4
        ws6.cell(row=r, column=1, value=anchor)
        ws6.cell(row=r, column=2, value="角色锚点——与角色背景深度绑定的物品/记忆")

    for ws in [ws, ws2, ws3, ws4, ws5, ws6]:
        _auto_width(ws)

    safe_name = name.replace(" ", "_").replace("·", "-")
    path = os.path.join(base_dir, f"{safe_name}.xlsx")
    wb.save(path)
    return path


def make_all_preset_characters():
    """生成 4 个预置角色 Excel"""
    presets = [
        {
            "name": "预置-调查记者",
            "char_id": "investigator_liming",
            "attrs_data": (10, 10, 13, 9),
            "skills": [
                {"name": "调查", "difficulty": "Avg", "base_attribute": "IQ", "level": 14, "points_spent": 4, "description": "核心调查技能"},
                {"name": "潜行", "difficulty": "Avg", "base_attribute": "DX", "level": 11, "points_spent": 2, "description": "隐匿移动"},
                {"name": "话术", "difficulty": "Avg", "base_attribute": "IQ", "level": 13, "points_spent": 2, "description": "交涉/说服"},
                {"name": "摄影", "difficulty": "Easy", "base_attribute": "IQ", "level": 12, "points_spent": 1, "description": "拍摄/取证"},
                {"name": "驾驶", "difficulty": "Avg", "base_attribute": "DX", "level": 11, "points_spent": 2, "description": "驾驶车辆"},
                {"name": "近战", "difficulty": "Avg", "base_attribute": "DX", "level": 10, "points_spent": 1, "description": "近身格斗"},
            ],
            "advantages": ["警觉", "快速反应"],
            "disadvantages": ["好奇心（强烈）", "失眠"],
            "features": [
                {"name": "记者的鼻子", "trigger_condition": "调查异常现象/线索时有可辨识信息", "cost": 1, "effect": "请求GM给出一条额外线索或-2对方对抗检定", "per_scene_limit": 2, "source": "记者"},
                {"name": "经验直觉", "trigger_condition": "进入危险区域之前", "cost": 1, "effect": "感知到潜在威胁的大致方向或性质", "per_scene_limit": 1, "source": "记者"},
                {"name": "可靠的同伴", "trigger_condition": "同伴行动失败时", "cost": 1, "effect": "给予同伴+2下一次检定", "per_scene_limit": 1, "source": "记者"},
            ],
            "equipment": [
                {"name": "手电筒", "type": "tool", "slot": "hand", "dr": 0, "effects": [{"tag_mod": "remove:低能见度"}], "uses": -1, "description": "老式手电筒"},
                {"name": "笔记本", "type": "key_item", "slot": "backpack", "dr": 0, "effects": [], "uses": -1, "description": "浸水但还能用的笔记本"},
            ],
            "anchors": ["父亲的怀表", "被烧毁的报社照片"],
        },
        {
            "name": "预置-退役军警",
            "char_id": "veteran_zhang",
            "attrs_data": (13, 10, 10, 11),
            "skills": [
                {"name": "近战", "difficulty": "Avg", "base_attribute": "DX", "level": 14, "points_spent": 8, "description": "格斗训练"},
                {"name": "手枪", "difficulty": "Avg", "base_attribute": "DX", "level": 13, "points_spent": 4, "description": "射击训练"},
                {"name": "战术", "difficulty": "Hard", "base_attribute": "IQ", "level": 11, "points_spent": 4, "description": "战斗策略"},
                {"name": "威吓", "difficulty": "Avg", "base_attribute": "IQ", "level": 11, "points_spent": 2, "description": "威慑/审问"},
                {"name": "急救", "difficulty": "Avg", "base_attribute": "IQ", "level": 10, "points_spent": 1, "description": "战场急救"},
                {"name": "驾驶", "difficulty": "Avg", "base_attribute": "DX", "level": 10, "points_spent": 1, "description": "驾驶车辆"},
            ],
            "advantages": ["战斗反射", "高度痛觉忍受"],
            "disadvantages": ["噩梦症", "过度保护本能"],
            "features": [
                {"name": "战斗直觉", "trigger_condition": "进入战斗时", "cost": 1, "effect": "获得+1先攻和+1第一次攻击", "per_scene_limit": 1, "source": "军警"},
                {"name": "掩护同伴", "trigger_condition": "同伴受到攻击时", "cost": 1, "effect": "代替同伴承担本次伤害（需在相邻位置）", "per_scene_limit": 1, "source": "军警"},
                {"name": "老兵的眼神", "trigger_condition": "NPC说谎或隐藏信息时", "cost": 1, "effect": "感知检定+3检测欺骗", "per_scene_limit": 1, "source": "军警"},
            ],
            "equipment": [
                {"name": "警棍", "type": "weapon", "slot": "hand", "dr": 0, "damage": "1d6+1 cr", "effects": [], "uses": -1, "description": "退役时留下的纪念品"},
                {"name": "急救包", "type": "consumable", "slot": "backpack", "dr": 0, "effects": [{"restore_hp": "1d6"}], "uses": 1, "description": "标准急救包"},
            ],
            "anchors": ["旧勋章", "战友的照片"],
        },
        {
            "name": "预置-神秘学学者",
            "char_id": "occultist_wang",
            "attrs_data": (9, 10, 14, 9),
            "skills": [
                {"name": "神秘学", "difficulty": "Hard", "base_attribute": "IQ", "level": 16, "points_spent": 8, "description": "超自然知识"},
                {"name": "研究", "difficulty": "Avg", "base_attribute": "IQ", "level": 15, "points_spent": 4, "description": "文献/资料检索"},
                {"name": "历史", "difficulty": "Hard", "base_attribute": "IQ", "level": 13, "points_spent": 4, "description": "历史知识"},
                {"name": "话术", "difficulty": "Avg", "base_attribute": "IQ", "level": 12, "points_spent": 1, "description": "说服/辩驳"},
                {"name": "急救", "difficulty": "Avg", "base_attribute": "IQ", "level": 12, "points_spent": 1, "description": "基础急救"},
            ],
            "advantages": ["直觉预感", "语言天赋（古汉语/拉丁语）"],
            "disadvantages": ["体弱（ST-1）", "偏执"],
            "features": [
                {"name": "神秘感知", "trigger_condition": "面对超自然现象时", "cost": 1, "effect": "感知检定+2，可辨识现象来源/性质", "per_scene_limit": 2, "source": "学者"},
                {"name": "驱邪仪式", "trigger_condition": "与镜中生物对峙时", "cost": 2, "effect": "意志对抗→驱散一只镜中生物2回合", "per_scene_limit": 1, "source": "学者"},
                {"name": "学术引证", "trigger_condition": "调查/研究检定时", "cost": 1, "effect": "提供历史/神秘学关联信息，给同伴+1下次检定", "per_scene_limit": 2, "source": "学者"},
            ],
            "equipment": [
                {"name": "古籍手抄本", "type": "key_item", "slot": "backpack", "dr": 0, "effects": [{"tool_bonus": 2, "skill": "神秘学"}], "uses": -1, "description": "祖传的镜面妖异调查报告"},
                {"name": "银质护符", "type": "key_item", "slot": "neck", "dr": 0, "effects": [{"psychic_resistance": +1}], "uses": -1, "description": "刻有辟邪符文的银牌"},
            ],
            "anchors": ["古籍手抄本", "银质护符"],
        },
        {
            "name": "预置-街头混混",
            "char_id": "street_punk_ahao",
            "attrs_data": (11, 13, 9, 11),
            "skills": [
                {"name": "潜行", "difficulty": "Avg", "base_attribute": "DX", "level": 14, "points_spent": 4, "description": "隐匿行动"},
                {"name": "撬锁", "difficulty": "Avg", "base_attribute": "DX", "level": 14, "points_spent": 4, "description": "开锁/破解"},
                {"name": "近战", "difficulty": "Avg", "base_attribute": "DX", "level": 13, "points_spent": 2, "description": "街头格斗"},
                {"name": "话术", "difficulty": "Avg", "base_attribute": "IQ", "level": 11, "points_spent": 4, "description": "讨价还价/骗人"},
                {"name": "攀爬", "difficulty": "Avg", "base_attribute": "DX", "level": 13, "points_spent": 2, "description": "爬墙/翻越"},
                {"name": "察觉", "difficulty": "Avg", "base_attribute": "IQ", "level": 10, "points_spent": 2, "description": "街头警觉"},
            ],
            "advantages": ["灵活", "快速反应"],
            "disadvantages": ["有案底", "穷困", "冲动"],
            "features": [
                {"name": "街头直觉", "trigger_condition": "进入陌生城区/暗巷时", "cost": 1, "effect": "感知检定+2，获知最佳逃生路线", "per_scene_limit": 1, "source": "混混"},
                {"name": "危急应变", "trigger_condition": "HP降至一半以下时", "cost": 1, "effect": "下回合闪避+2", "per_scene_limit": 1, "source": "混混"},
                {"name": "话术达人", "trigger_condition": "交涉/欺骗检定时", "cost": 1, "effect": "话术检定+2（一次）", "per_scene_limit": 1, "source": "混混"},
            ],
            "equipment": [
                {"name": "撬棍", "type": "tool", "slot": "hand", "dr": 0, "damage": "1d6+1 cr", "effects": [{"tool_bonus": 2, "skill": "ST"}], "uses": -1, "description": "破门破墙+应急武器"},
                {"name": "弹弓", "type": "weapon", "slot": "hand", "dr": 0, "damage": "1d-2 cr", "effects": [], "uses": 10, "description": "自制弹弓，石子当弹药"},
            ],
            "anchors": ["刻有名字的打火机", "欠条——一笔还不清的债"],
        },
    ]

    paths = []
    for preset in presets:
        p = make_preset_character_xlsx(**preset)
        paths.append(p)
    return paths


# ============================================================
# 主入口
# ============================================================
def main():
    print("=" * 60)
    print("  Mirror of the Lost — Excel 模板生成器")
    print("=" * 60)

    if "--list" in sys.argv:
        print("\n将生成以下模板文件：\n")
        templates = [
            ("玩家侧", "character.xlsx", "空白角色卡（5 Sheet）"),
            ("玩家侧", "预置-调查记者.xlsx", "IQ 13 调查记者"),
            ("玩家侧", "预置-退役军警.xlsx", "ST 13 退役军警"),
            ("玩家侧", "预置-神秘学学者.xlsx", "IQ 14 神秘学学者"),
            ("玩家侧", "预置-街头混混.xlsx", "DX 13 街头混混"),
            ("主持人侧", "enemy_builder.xlsx", "敌人/NPC 属性模板"),
            ("主持人侧", "item_builder.xlsx", "物品/装备属性模板"),
            ("主持人侧", "trap_builder.xlsx", "陷阱/机关模板"),
            ("主持人侧", "encounter_table.xlsx", "随机遭遇表"),
            ("主持人侧", "loot_table.xlsx", "战利品表"),
            ("主持人侧", "npc_reaction.xlsx", "NPC 反应表"),
            ("主持人侧", "scene_builder.xlsx", "场景构建表（3 Act）"),
            ("主持人侧", "module_meta.xlsx", "模组全局元信息"),
            ("主持人侧", "map_grid.xlsx", "网格地图"),
        ]
        for side, fname, desc in templates:
            print(f"  [{side}]  {fname:<28s} {desc}")
        print(f"\n共 {len(templates)} 个模板文件")
        return

    count = 0

    # 玩家侧
    print("\n📋 玩家侧 — 角色卡")
    p = make_character_template()
    print(f"  ✅ {os.path.basename(p)}")
    count += 1

    for p in make_all_preset_characters():
        print(f"  ✅ {os.path.basename(p)}")
        count += 1

    # 主持人侧 — 数据
    print("\n🖥️ 主持人侧 — 数据制造")
    for func in [make_enemy_template, make_item_template, make_trap_template,
                 make_encounter_template, make_loot_template, make_reaction_template]:
        p = func()
        print(f"  ✅ {os.path.basename(p)}")
        count += 1

    # 主持人侧 — 模组
    print("\n📝 主持人侧 — 模组制造")
    for func in [make_scene_builder_template, make_module_meta_template]:
        p = func()
        print(f"  ✅ {os.path.basename(p)}")
        count += 1

    # 主持人侧 — 地图
    print("\n🗺️ 主持人侧 — 地图")
    p = make_map_grid_template()
    print(f"  ✅ {os.path.basename(p)}")
    count += 1

    print(f"\n{'=' * 60}")
    print(f"  ✅ 全部完成！共生成 {count} 个 Excel 模板")
    print(f"  输出目录: {TEMPLATES_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
