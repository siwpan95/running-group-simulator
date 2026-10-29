# -*- coding: utf-8 -*-
"""
内容目录扩充脚本（一次性策展工具，可重复运行）。

将本文件内置的新条目合并进两个策展目录：
  data/dnd5e/catalog.json  -> monsters / spells
  data/coc7/catalog.json   -> creatures

规则：
  - 按 name 去重（不覆盖既有条目，仅追加缺失项）；
  - 不改动既有条目；仅追加 + 在 sources 追加一条扩充说明；
  - 字段严格对齐 tools/validate_catalogs.py 的 schema 要求。
数据来源（合法口径）：
  - D&D 5e 条目取自 SRD 5.1（OGL + CC BY 4.0，5thsrd.org），带署名；
  - CoC 7e 神话生物为公有领域神话，数值按 7e 惯例综合（延续既有 trow-11676 署名口径）。
注意：data/dnd5e 的 items 段已是 SRD 武器+护甲全表（50 条），本脚本不再扩物品。
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DND = os.path.join(HERE, "data", "dnd5e", "catalog.json")
COC = os.path.join(HERE, "data", "coc7", "catalog.json")

SRC_DND = "5thsrd.org SRD 5.1 (CC BY 4.0)"
SRC_COC = "trow-11676 / 公有领域克苏鲁神话综合"


def mon(name, tline, ac, hp, spd, s, d, c, i, w, ch, an, at, ah, ad):
    return {
        "name": name, "name_en": name, "type_line": tline,
        "ac": ac, "hp": hp, "speed": spd,
        "stats": {"STR": s, "DEX": d, "CON": c, "INT": i, "WIS": w, "CHA": ch},
        "attack": {"name": an, "type": at, "hit": ah, "damage": ad},
        "source": SRC_DND,
    }


DND_MONSTERS = [
    # ---- 人形杂兵 / NPC ----
    mon("Bandit", "Medium humanoid (any race), any non-lawful alignment", 12, "2d8+2", "30 ft.", 11, 12, 12, 10, 10, 10, "Scimitar", "Melee", "+3", "1d6 + 1 slashing damage"),
    mon("Bandit Captain", "Medium humanoid (any race), any non-lawful alignment", 15, "10d8+20", "30 ft.", 15, 16, 14, 14, 11, 14, "Scimitar", "Melee", "+5", "1d6 + 3 slashing damage"),
    mon("Commoner", "Medium humanoid (any race), any alignment", 10, "1d8", "30 ft.", 10, 10, 10, 10, 10, 10, "Club", "Melee", "+2", "1d4 bludgeoning damage"),
    mon("Cultist", "Medium humanoid (any race), any non-good alignment", 12, "2d8", "30 ft.", 11, 12, 10, 10, 10, 10, "Dagger", "Melee", "+3", "1d4 + 1 piercing damage"),
    mon("Acolyte", "Medium humanoid (any race), any alignment", 10, "2d8", "30 ft.", 10, 10, 10, 10, 14, 11, "Club", "Melee", "+2", "1d4 bludgeoning damage"),
    mon("Guard", "Medium humanoid (any race), any alignment", 16, "2d8+2", "30 ft.", 13, 12, 12, 10, 11, 10, "Spear", "Melee", "+3", "1d6 + 1 piercing damage"),
    mon("Spy", "Medium humanoid (any race), any alignment", 12, "6d8", "30 ft.", 10, 15, 10, 12, 14, 13, "Shortsword", "Melee", "+4", "1d6 + 2 piercing damage"),
    mon("Thug", "Medium humanoid (any race), any non-good alignment", 11, "5d8+5", "30 ft.", 15, 11, 12, 10, 10, 10, "Mace", "Melee", "+4", "1d6 + 2 bludgeoning damage"),
    mon("Tribal Warrior", "Medium humanoid (any race), any alignment", 12, "2d8+2", "30 ft.", 13, 11, 12, 8, 11, 8, "Spear", "Melee", "+3", "1d6 + 1 piercing damage"),
    mon("Knight", "Medium humanoid (any race), any alignment", 18, "8d8+16", "30 ft.", 16, 11, 14, 11, 11, 15, "Greatsword", "Melee", "+5", "2d6 + 3 slashing damage"),
    # ---- 野兽 ----
    mon("Giant Rat", "Small beast, unaligned", 12, "2d6", "30 ft.", 7, 15, 11, 2, 10, 4, "Bite", "Melee", "+4", "1d4 + 2 piercing damage"),
    mon("Bat", "Tiny beast, unaligned", 12, "1d4-1", "5 ft., fly 30 ft.", 2, 15, 8, 2, 12, 4, "Bite", "Melee", "+0", "1 piercing damage"),
    mon("Giant Bat", "Large beast, unaligned", 13, "4d10", "10 ft., fly 60 ft.", 15, 16, 11, 2, 12, 6, "Bite", "Melee", "+5", "1d8 + 2 piercing damage"),
    mon("Giant Spider", "Large beast, unaligned", 14, "4d10+4", "30 ft., climb 30 ft.", 14, 16, 12, 2, 11, 4, "Bite", "Melee", "+5", "1d8 + 3 piercing damage"),
    mon("Dire Wolf", "Large beast, unaligned", 14, "5d10+10", "50 ft.", 17, 15, 15, 3, 12, 7, "Bite", "Melee", "+5", "2d6 + 3 piercing damage"),
    mon("Black Bear", "Medium beast, unaligned", 11, "3d8+6", "40 ft., climb 30 ft.", 15, 10, 14, 2, 12, 7, "Bite", "Melee", "+3", "1d6 + 2 slashing damage"),
    mon("Giant Eagle", "Large beast, neutral good", 13, "4d10+4", "10 ft., fly 80 ft.", 16, 17, 13, 8, 14, 10, "Talons", "Melee", "+5", "2d6 + 3 slashing damage"),
    mon("Polar Bear", "Large beast, unaligned", 12, "5d10+15", "40 ft., swim 30 ft.", 20, 10, 16, 2, 13, 7, "Bite", "Melee", "+7", "1d8 + 5 piercing damage"),
    mon("Tiger", "Large beast, unaligned", 12, "5d10+10", "40 ft.", 17, 15, 14, 3, 12, 8, "Bite", "Melee", "+5", "1d10 + 3 slashing damage"),
    mon("Boar", "Medium beast, unaligned", 11, "2d8+2", "40 ft.", 13, 10, 12, 2, 9, 4, "Tusk", "Melee", "+3", "1d6 + 1 slashing damage"),
    mon("Giant Boar", "Large beast, unaligned", 12, "5d10+15", "40 ft.", 17, 10, 16, 2, 9, 4, "Tusk", "Melee", "+5", "2d6 + 3 slashing damage"),
    mon("Ape", "Medium beast, unaligned", 12, "3d8+6", "30 ft., climb 30 ft.", 16, 14, 14, 6, 12, 7, "Fist", "Melee", "+5", "1d6 + 3 bludgeoning damage"),
    mon("Giant Ape", "Huge beast, unaligned", 12, "15d12+60", "40 ft., climb 40 ft.", 23, 10, 18, 7, 12, 7, "Fist", "Melee", "+9", "3d10 + 6 bludgeoning damage"),
    mon("Crocodile", "Large beast, unaligned", 12, "3d10+3", "20 ft., swim 30 ft.", 15, 10, 13, 2, 10, 5, "Bite", "Melee", "+4", "1d10 + 2 piercing damage"),
    mon("Giant Crocodile", "Huge beast, unaligned", 14, "9d12+27", "30 ft., swim 50 ft.", 21, 9, 17, 2, 10, 7, "Bite", "Melee", "+7", "2d10 + 5 piercing damage"),
    mon("Elephant", "Huge beast, unaligned", 12, "8d12+24", "40 ft.", 22, 9, 17, 3, 11, 6, "Tusk", "Melee", "+8", "2d8 + 6 piercing damage"),
    # ---- 不死生物 ----
    mon("Ghoul", "Medium undead, chaotic evil", 12, "5d8", "30 ft.", 13, 15, 10, 12, 11, 14, "Claw", "Melee", "+3", "2d4 + 1 slashing damage"),
    mon("Ghast", "Medium undead, chaotic evil", 13, "8d8", "30 ft.", 16, 17, 10, 11, 10, 14, "Claw", "Melee", "+5", "2d4 + 3 slashing damage"),
    mon("Wight", "Medium undead, neutral evil", 14, "6d8+18", "30 ft.", 15, 14, 16, 10, 13, 15, "Longsword", "Melee", "+4", "1d8 + 2 slashing damage"),
    mon("Wraith", "Medium undead, neutral evil", 13, "9d8+27", "0 ft., fly 60 ft. (hover)", 6, 16, 16, 12, 14, 15, "Life Drain", "Melee", "+6", "4d6 + 3 necrotic damage"),
    mon("Mummy", "Medium undead, lawful evil", 11, "9d8+18", "20 ft.", 16, 8, 15, 6, 10, 12, "Rotting Fist", "Melee", "+5", "2d6 + 3 bludgeoning damage"),
    mon("Shadow", "Medium undead, chaotic evil", 12, "3d8+3", "40 ft.", 6, 14, 13, 6, 10, 8, "Strength Drain", "Melee", "+4", "2d6 + 2 necrotic damage"),
    mon("Specter", "Medium undead, chaotic evil", 12, "5d8", "0 ft., fly 50 ft. (hover)", 1, 14, 11, 10, 10, 11, "Life Drain", "Melee", "+4", "3d6 necrotic damage"),
    # ---- 龙（五色 + 金属） ----
    mon("Young Red Dragon", "Huge dragon, chaotic evil", 18, "17d12+68", "40 ft., fly 80 ft.", 23, 10, 19, 14, 11, 19, "Bite", "Melee", "+10", "2d10 + 6 fire damage"),
    mon("Adult Red Dragon", "Huge dragon, chaotic evil", 19, "19d12+114", "40 ft., fly 80 ft.", 27, 10, 23, 17, 13, 21, "Bite", "Melee", "+14", "2d10 + 8 fire damage"),
    mon("Ancient Red Dragon", "Gargantuan dragon, chaotic evil", 22, "28d20+224", "40 ft., fly 80 ft., swim 40 ft.", 30, 10, 26, 20, 15, 23, "Bite", "Melee", "+17", "2d10 + 10 fire damage"),
    mon("Adult Blue Dragon", "Huge dragon, lawful evil", 19, "18d12+90", "40 ft., burrow 30 ft., fly 80 ft.", 25, 10, 21, 16, 13, 19, "Bite", "Melee", "+12", "2d10 + 7 lightning damage"),
    mon("Young White Dragon", "Medium dragon, chaotic evil", 16, "14d8+70", "40 ft., burrow 20 ft., fly 80 ft., swim 40 ft.", 18, 10, 21, 8, 11, 12, "Bite", "Melee", "+6", "1d10 + 4 cold damage"),
    mon("Adult White Dragon", "Huge dragon, chaotic evil", 18, "16d12+96", "40 ft., burrow 30 ft., fly 80 ft., swim 40 ft.", 22, 10, 22, 8, 12, 12, "Bite", "Melee", "+10", "2d10 + 6 cold damage"),
    mon("Adult Silver Dragon", "Huge dragon, lawful good", 19, "18d12+108", "40 ft., fly 80 ft.", 27, 10, 23, 16, 13, 21, "Bite", "Melee", "+14", "2d10 + 8 cold damage"),
    mon("Adult Gold Dragon", "Huge dragon, lawful good", 19, "19d12+133", "40 ft., fly 80 ft., swim 40 ft.", 27, 14, 25, 16, 15, 24, "Bite", "Melee", "+14", "2d10 + 8 fire damage"),
    mon("Ancient Gold Dragon", "Gargantuan dragon, lawful good", 22, "28d20+224", "40 ft., fly 80 ft., swim 40 ft.", 30, 10, 26, 20, 17, 28, "Bite", "Melee", "+17", "2d10 + 10 fire damage"),
    # ---- 巨兽 / 怪异生物 ----
    mon("Owlbear", "Large monstrosity, unaligned", 13, "7d10+21", "40 ft.", 20, 12, 17, 3, 12, 7, "Claw", "Melee", "+7", "2d8 + 5 slashing damage"),
    mon("Troll", "Large giant, chaotic evil", 15, "8d10+40", "30 ft.", 18, 13, 20, 7, 9, 7, "Bite", "Melee", "+7", "2d6 + 4 piercing damage"),
    mon("Ogre", "Large giant, chaotic evil", 11, "7d10+21", "40 ft.", 19, 8, 16, 5, 7, 7, "Greatclub", "Melee", "+6", "2d8 + 4 bludgeoning damage"),
    mon("Hill Giant", "Huge giant, chaotic evil", 13, "10d12+40", "40 ft.", 21, 8, 19, 5, 9, 7, "Greatclub", "Melee", "+8", "3d8 + 5 bludgeoning damage"),
    mon("Stone Giant", "Huge giant, neutral", 17, "11d12+55", "40 ft.", 23, 15, 20, 10, 12, 11, "Greatclub", "Melee", "+9", "3d8 + 6 bludgeoning damage"),
    mon("Frost Giant", "Huge giant, neutral evil", 15, "12d12+60", "40 ft.", 23, 9, 21, 9, 10, 12, "Greatsword", "Melee", "+10", "3d6 + 6 slashing damage"),
    mon("Fire Giant", "Huge giant, lawful evil", 18, "13d12+78", "30 ft.", 25, 9, 23, 10, 14, 13, "Greatsword", "Melee", "+11", "3d6 + 7 slashing damage"),
    mon("Chimera", "Large monstrosity, chaotic evil", 14, "12d10+48", "30 ft., fly 60 ft.", 19, 13, 19, 3, 14, 10, "Bite", "Melee", "+7", "2d6 + 4 slashing damage"),
    mon("Gelatinous Cube", "Large ooze, unaligned", 6, "8d10+40", "15 ft.", 14, 3, 20, 1, 6, 1, "Pseudopod", "Melee", "+4", "2d6 + 2 acid damage"),
    mon("Mimic", "Medium monstrosity (shapechanger), neutral", 12, "9d8+18", "15 ft.", 17, 12, 15, 5, 13, 8, "Bite", "Melee", "+5", "1d8 + 3 bludgeoning damage"),
    mon("Beholder", "Large aberration, lawful evil", 18, "19d10+76", "0 ft., fly 20 ft. (hover)", 10, 14, 18, 17, 15, 17, "Bite", "Melee", "+5", "2d6 + 2 piercing damage"),
    mon("Mind Flayer", "Medium aberration, lawful evil", 15, "13d8+13", "30 ft.", 11, 12, 12, 19, 17, 17, "Tentacles", "Melee", "+7", "2d4 + 3 psychic damage"),
    mon("Basilisk", "Medium monstrosity, unaligned", 15, "8d8+16", "20 ft.", 16, 8, 15, 2, 8, 7, "Bite", "Melee", "+5", "1d10 + 3 piercing damage"),
    mon("Gorgon", "Large monstrosity, unaligned", 19, "12d10+48", "40 ft.", 20, 14, 18, 2, 12, 7, "Gore", "Melee", "+8", "2d10 + 5 piercing damage"),
    mon("Griffon", "Large monstrosity, neutral", 12, "7d10+21", "30 ft., fly 80 ft.", 18, 15, 16, 2, 13, 8, "Claw", "Melee", "+6", "2d4 + 4 slashing damage"),
    mon("Manticore", "Large monstrosity, lawful evil", 14, "8d10+24", "30 ft., fly 50 ft.", 17, 16, 17, 7, 12, 8, "Bite", "Melee", "+5", "1d8 + 3 piercing damage"),
    # ---- 魔鬼 / 异界 ----
    mon("Hell Hound", "Medium fiend, lawful evil", 15, "7d8+14", "50 ft.", 17, 12, 14, 6, 13, 6, "Bite", "Melee", "+5", "1d8 + 3 fire damage"),
    mon("Imp", "Tiny fiend, lawful evil", 13, "3d4+3", "20 ft., fly 40 ft.", 6, 17, 13, 11, 12, 11, "Claw", "Melee", "+5", "1d4 + 3 slashing damage"),
    mon("Quasit", "Tiny fiend, chaotic evil", 13, "3d6+6", "40 ft., fly 40 ft.", 5, 17, 14, 7, 10, 10, "Claw", "Melee", "+4", "1d4 + 2 slashing damage"),
    mon("Bearded Devil", "Medium fiend, lawful evil", 13, "7d8+21", "30 ft.", 16, 15, 16, 9, 11, 11, "Glaive", "Melee", "+5", "1d10 + 3 slashing damage"),
    mon("Chain Devil", "Medium fiend, lawful evil", 16, "10d8+40", "30 ft.", 18, 16, 18, 11, 14, 12, "Chain", "Melee", "+8", "2d6 + 4 slashing damage"),
    mon("Bone Devil", "Large fiend (devil), lawful evil", 19, "15d8+75", "40 ft., fly 40 ft.", 18, 16, 20, 14, 14, 16, "Sting", "Melee", "+8", "2d6 + 4 piercing damage"),
    mon("Erinyes", "Medium fiend, lawful evil", 18, "18d8+72", "30 ft., fly 60 ft.", 16, 17, 18, 14, 14, 18, "Longsword", "Melee", "+7", "1d8 + 3 slashing damage"),
    mon("Ice Devil", "Large fiend, lawful evil", 18, "19d8+95", "40 ft.", 21, 14, 20, 14, 16, 18, "Claw", "Melee", "+9", "2d4 + 5 slashing damage"),
    mon("Pit Fiend", "Large fiend, lawful evil", 19, "24d8+168", "30 ft., fly 60 ft.", 26, 14, 24, 22, 18, 24, "Bite", "Melee", "+14", "2d8 + 9 piercing damage"),
    mon("Rakshasa", "Medium fiend, lawful evil", 16, "13d8+52", "40 ft.", 14, 17, 18, 13, 16, 20, "Claw", "Melee", "+7", "2d6 + 3 slashing damage"),
    # ---- 元素 / 精类 ----
    mon("Couatl", "Medium celestial, lawful good", 19, "13d8+39", "20 ft., fly 60 ft.", 16, 20, 17, 18, 17, 18, "Constrict", "Melee", "+8", "2d6 + 4 bludgeoning damage"),
    mon("Djinni", "Large elemental, chaotic good", 17, "14d10+84", "30 ft., fly 90 ft. (hover)", 21, 15, 22, 15, 16, 20, "Slam", "Melee", "+8", "2d6 + 5 bludgeoning damage"),
    mon("Efreeti", "Large elemental, lawful evil", 17, "16d10+112", "40 ft., fly 60 ft.", 22, 12, 24, 16, 15, 16, "Scimitar", "Melee", "+10", "2d6 + 6 slashing damage"),
    mon("Invisible Stalker", "Large elemental, neutral", 14, "11d10+44", "50 ft., fly 50 ft. (hover)", 16, 19, 18, 10, 15, 11, "Slam", "Melee", "+6", "2d6 + 3 bludgeoning damage"),
    mon("Blink Dog", "Medium fey, lawful good", 13, "4d8+4", "40 ft.", 12, 17, 12, 10, 13, 11, "Bite", "Melee", "+3", "1d6 + 1 piercing damage"),
]

DND_SPELLS = [
    ("Acid Splash", "conjuration cantrip", "1 action", "60 feet", "V, S", "Instantaneous", "飞溅强酸，1d6 强酸伤害。"),
    ("Chill Touch", "necromancy cantrip", "1 action", "120 feet", "V, S", "1 round", "亡灵触击，1d8 暗蚀伤害，阻止回血。"),
    ("Fire Bolt", "evocation cantrip", "1 action", "120 feet", "V, S", "Instantaneous", "射出火弹，1d10 火焰伤害。"),
    ("Mage Hand", "conjuration cantrip", "1 action", "30 feet", "V, S", "1 minute", "召唤悬浮的幽灵手。"),
    ("Prestidigitation", "transmutation cantrip", "1 action", "10 feet", "V, S", "Up to 1 hour", "小幅戏法效果。"),
    ("Ray of Frost", "evocation cantrip", "1 action", "60 feet", "V, S", "Instantaneous", "冰霜射线，1d8 寒冷伤害，减速。"),
    ("Shocking Grasp", "evocation cantrip", "1 action", "Touch", "V, S", "Instantaneous", "电击抓握，1d8 闪电伤害。"),
    ("True Strike", "divination cantrip", "1 action", "Self", "V, S", "Concentration, 1 round", "下次攻击优势。"),
    ("Alarm", "1st-level abjuration (ritual)", "1 minute", "30 feet", "V, S, M", "8 hours", "设下声响或精神警报结界。"),
    ("Animal Friendship", "1st-level enchantment", "1 action", "30 feet", "V, S, M", "24 hours", "使野兽视你为好友。"),
    ("Charm Person", "1st-level enchantment", "1 action", "30 feet", "V, S", "1 hour", "魅惑类人生物。"),
    ("Comprehend Languages", "1st-level divination (ritual)", "1 action", "Self", "V, S, M", "1 hour", "读懂/听懂任意语言。"),
    ("Disguise Self", "1st-level illusion", "1 action", "Self", "V, S", "1 hour", "改变自身外观。"),
    ("Expeditious Retreat", "1st-level transmutation", "1 bonus action", "Self", "V, S", "Concentration, up to 10 minutes", "本回合及之后移动加倍。"),
    ("Faerie Fire", "1st-level evocation", "1 action", "60 feet", "V", "Concentration, up to 1 minute", "目标区域发光，失去隐身。"),
    ("Feather Fall", "1st-level transmutation", "1 reaction", "60 feet", "V, M", "1 minute", "缓落，免疫坠落伤害。"),
    ("Healing Word", "1st-level evocation", "1 bonus action", "60 feet", "V", "Instantaneous", "1d4 + 施法者调整值治疗。"),
    ("Heroism", "1st-level enchantment", "1 action", "Touch", "V, S", "Concentration, up to 1 minute", "赋予无畏与临时 HP。"),
    ("Hideous Laughter", "1st-level enchantment", "1 action", "30 feet", "V, S, M", "Concentration, up to 1 minute", "目标倒地大笑，无法行动。"),
    ("Identify", "1st-level divination (ritual)", "1 minute", "Touch", "V, S, M", "Instantaneous", "获知物品魔法属性。"),
    ("Jump", "1st-level transmutation", "1 action", "Touch", "V, S, M", "1 minute", "跳跃距离 ×3。"),
    ("Longstrider", "1st-level transmutation", "1 action", "Touch", "V, S, M", "1 hour", "速度 +10 尺。"),
    ("Silent Image", "1st-level illusion", "1 action", "60 feet", "V, S, M", "Concentration, up to 10 minutes", "制造静默幻象。"),
    ("Invisibility", "2nd-level illusion", "1 action", "Touch", "V, S, M", "Concentration, up to 1 hour", "目标隐形。"),
    ("Knock", "2nd-level transmutation", "1 action", "60 feet", "V", "Instantaneous", "开锁/破门。"),
    ("Levitate", "2nd-level transmutation", "1 action", "60 feet", "V, S, M", "Concentration, up to 10 minutes", "使目标漂浮。"),
    ("Mirror Image", "2nd-level illusion", "1 action", "Self", "V, S", "1 minute", "生成 3 个分身承受攻击。"),
    ("Misty Step", "2nd-level conjuration", "1 bonus action", "Self", "V", "Instantaneous", "短距传送 30 尺。"),
    ("Scorching Ray", "2nd-level evocation", "1 action", "120 feet", "V, S", "Instantaneous", "射出 3 道火焰射线，各 2d6 火焰。"),
    ("See Invisibility", "2nd-level divination", "1 action", "Self", "V, S, M", "1 hour", "看见隐形与以太生物。"),
    ("Suggestion", "2nd-level enchantment", "1 action", "30 feet", "V, M", "Concentration, up to 8 hours", "命令目标执行合理动作。"),
    ("Web", "2nd-level conjuration", "1 action", "60 feet", "V, S, M", "Concentration, up to 1 hour", "制造黏网困住目标。"),
    ("Counterspell", "3rd-level abjuration", "1 reaction", "60 feet", "S", "Instantaneous", "尝试反制正在施放的法术。"),
    ("Dispel Magic", "3rd-level abjuration", "1 action", "120 feet", "V, S", "Instantaneous", "解除目标上的魔法效果。"),
    ("Fly", "3rd-level transmutation", "1 action", "Touch", "V, S, M", "Concentration, up to 1 hour", "赋予飞行速度 60 尺。"),
    ("Lightning Bolt", "3rd-level evocation", "1 action", "Self (100-foot line)", "V, S, M", "Instantaneous", "100 尺线状闪电，8d6 闪电。"),
    ("Cone of Cold", "5th-level evocation", "1 action", "Self (60-foot cone)", "V, S, M", "Instantaneous", "60 尺锥状寒冰，8d8 寒冷。"),
]


def coc(name, name_en, klass, stats, move, hp, db, armor, san, weapons, src=SRC_COC):
    return {
        "name": name, "name_en": name_en, "class": klass,
        "source": src, "stats": stats, "move": move, "hp": hp,
        "damage_bonus": db, "armor": armor, "san_loss": san,
        "weapons": weapons,
    }


COC_CREATURES = [
    coc("修格斯", "Shoggoth", "上级独立种族",
        {"str": 100, "con": 100, "siz": 100, "int": 30, "pow": 20, "dex": 10},
        "10／游泳30", 20, "+3d6", "10(胶状原生质)", "1d6/1d20",
        ["伪足35% (1d6+伤害加权", "吞噬（接触即 engulf）"]),
    coc("克苏鲁", "Cthulhu", "外神",
        {"str": 100, "con": 100, "siz": 100, "int": 90, "pow": 100, "dex": 20},
        "10／飞行30", 20, "+3d6", "10(非地球物质)", "1d10/1d100",
        ["爪60% (1d6+伤害加权", "触肢缠绕"]),
    coc("奈亚拉托提普", "Nyarlathotep", "外神（千面之神）",
        {"str": 50, "con": 50, "siz": 30, "int": 80, "pow": 90, "dex": 40},
        "10／飞行30", 8, "+1d6", "无", "1d10/1d100",
        ["触肢50% (1d6+伤害加权"]),
    coc("哈斯塔", "Hastur", "旧日支配者",
        {"str": 60, "con": 50, "siz": 40, "int": 80, "pow": 80, "dex": 40},
        "10／飞行20", 9, "+1d6", "无", "1d6/1d20",
        ["触肢45% (1d6+伤害加权"]),
    coc("犹格·索托斯", "Yog-Sothoth", "外神",
        {"int": 100, "pow": 100}, "—", 0, "+0", "无（不可物理接触）", "1d10/1d100",
        ["现实扭曲（概念性攻击）"]),
    coc("阿撒托斯", "Azathoth", "盲目痴愚之神",
        {"str": 100, "con": 100, "siz": 100, "pow": 100}, "—", 20, "+3d6", "无", "—",
        ["混沌音律（概念性湮灭）"]),
    coc("达贡", "Dagon", "下级仆从种族（深潜者领袖）",
        {"str": 80, "con": 60, "siz": 80, "int": 50, "pow": 60, "dex": 20},
        "8／游泳10", 14, "+1d6", "2(鳞与皮)", "1d2/1d10",
        ["爪40% (1d6+伤害加权"]),
    coc("星之精魂", "Star Spawn", "克苏鲁之子",
        {"str": 60, "con": 40, "siz": 60, "int": 20, "pow": 40, "dex": 20},
        "6", 10, "+1d6", "3(黏腻表皮)", "1d3/1d15",
        ["触肢45% (1d6+伤害加权"]),
    coc("廷达罗斯猎犬", "Hound of Tindalos", "下级独立种族",
        {"str": 50, "con": 50, "siz": 40, "int": 30, "pow": 50, "dex": 60},
        "10", 9, "+1d6", "无", "1d6/1d20",
        ["撕咬50% (1d6+伤害加权"]),
    coc("飞旋息肉", "Flying Polyp", "上级独立种族",
        {"str": 60, "con": 50, "siz": 50, "int": 30, "pow": 35, "dex": 20},
        "10／飞行20", 10, "+1d6", "无", "1d6/1d20",
        ["风暴触肢45% (1d6+伤害加权"]),
    coc("米·戈", "Mi-Go", "下级独立种族（真菌生物）",
        {"str": 20, "con": 20, "siz": 20, "int": 50, "pow": 40, "dex": 30},
        "10／飞行20", 4, "+0", "2(几丁质外壳)", "0/1d6",
        ["钳爪35% (1d6"]),
    coc("无形孽胎", "Formless Spawn", "下级独立种族（撒达·赫格拉之仆）",
        {"str": 30, "con": 30, "siz": 30, "int": 10, "pow": 20, "dex": 20},
        "8", 6, "+0", "无", "1d2/1d10",
        ["绞缠40% (1d6"]),
    coc("狩猎魔", "Hunting Horror", "下级独立种族",
        {"str": 30, "con": 30, "siz": 30, "int": 20, "pow": 30, "dex": 40},
        "10／飞行30", 6, "+0", "无", "1d3/1d12",
        ["啮咬45% (1d6+伤害加权"]),
    coc("夜魇", "Nightgaunt", "下级独立种族",
        {"str": 25, "con": 20, "siz": 20, "int": 10, "pow": 15, "dex": 35},
        "12／飞行20", 4, "+0", "无", "0/1d6",
        ["角与尾30% (1d6"]),
    coc("食尸鬼", "Ghoul", "下级仆从种族",
        {"str": 20, "con": 20, "siz": 15, "int": 15, "pow": 15, "dex": 20},
        "9", 4, "+0", "无", "0/1d6",
        ["爪25% (1d6+伤害加权", "啃咬30% (1d6"]),
    coc("蛇人", "Serpent Man", "下级独立种族",
        {"str": 20, "con": 20, "siz": 15, "int": 50, "pow": 25, "dex": 20},
        "10", 4, "+0", "无", "1/1d8",
        ["利爪30% (1d6"]),
    coc("深潜者混血", "Deep One Hybrid", "下级仆从种族（混血）",
        {"str": 25, "con": 20, "siz": 20, "int": 20, "pow": 20, "dex": 18},
        "8／游泳10", 4, "+0", "1(鳞)", "0/1d6",
        ["爪25% (1d6+伤害加权"]),
    coc("撒达·赫格拉之子", "Spawn of Tsathoggua", "下级仆从种族",
        {"str": 25, "con": 30, "siz": 25, "int": 10, "pow": 25, "dex": 10},
        "6", 6, "+0", "1(黏滑皮肤)", "1/1d8",
        ["掐绞35% (1d6"]),
    coc("乌波·萨斯拉", "Ubbo-Sathla", "旧日支配者（本源之浑沌）",
        {"str": 100, "con": 100, "siz": 100, "int": 5, "pow": 30, "dex": 5},
        "1", 20, "+3d6", "5(原生质)", "1d6/1d20",
        ["原生质触手20% (1d6+伤害加权"]),
    coc("扎尔与洛伊戈尔", "Zhar & Lloigor", "上级独立种族",
        {"str": 70, "con": 60, "siz": 70, "int": 50, "pow": 60, "dex": 20},
        "8", 13, "+1d6", "5(云状躯体)", "1d4/1d15",
        ["精神触手40% (1d6+伤害加权"]),
    coc("犹格斯巨人", "Giants of Yuggoth", "下级独立种族",
        {"str": 100, "con": 100, "siz": 100, "int": 60, "pow": 60, "dex": 10},
        "8", 20, "+3d6", "8(几丁质)", "1d6/1d20",
        ["钳爪45% (1d6+伤害加权"]),
    coc("古老者", "Elder Thing", "下级独立种族",
        {"str": 80, "con": 90, "siz": 80, "int": 85, "pow": 80, "dex": 60},
        "8(陆地)/6(水下)", 17, "+1d4", "3(坚韧外壳)+再生", "1d3/1d6",
        ["触手55% (1d6+伤害加权"]),
    coc("伊斯之伟大种族", "Great Race of Yith", "下级独立种族（精神移转）",
        {"str": 20, "con": 20, "siz": 15, "int": 90, "pow": 60, "dex": 20},
        "10", 4, "+0", "无", "1d4/1d15",
        ["精神触手35% (1d6+伤害加权"]),
    coc("沙之住民", "Sand Dweller", "下级独立种族",
        {"str": 30, "con": 30, "siz": 30, "int": 25, "pow": 20, "dex": 15},
        "8", 6, "+0", "无", "0/1d8",
        ["爪25% (1d6"]),
    coc("伏米斯", "Voormis", "下级独立种族",
        {"str": 30, "con": 30, "siz": 25, "int": 10, "pow": 15, "dex": 10},
        "8", 6, "+0", "无", "1/1d8",
        ["利爪25% (1d6"]),
    coc("诺弗克", "Gnophkeh", "下级独立种族",
        {"str": 40, "con": 40, "siz": 40, "int": 12, "pow": 20, "dex": 15},
        "8", 8, "+1d4", "无", "1/1d10",
        ["爪30% (1d6+伤害加权"]),
    coc("格诺里", "Gnorri", "下级独立种族",
        {"str": 25, "con": 25, "siz": 20, "int": 15, "pow": 15, "dex": 20},
        "8", 5, "+0", "无", "0/1d8",
        ["爪25% (1d6"]),
    coc("月兽", "Moon-Beast", "下级独立种族",
        {"str": 30, "con": 25, "siz": 25, "int": 50, "pow": 30, "dex": 20},
        "8", 5, "+0", "无", "1/1d10",
        ["触手35% (1d6+伤害加权"]),
    coc("珊族", "Tcho-Tcho", "下级仆从种族（人类邪教徒）",
        {"str": 15, "con": 15, "siz": 12, "int": 15, "pow": 20, "dex": 15},
        "9", 3, "+0", "无", "1/1d6",
        ["匕首30% (1d6"]),
]


def merge(base, key, entries, name_field="name"):
    existing = {e.get(name_field, "").strip().lower() for e in base.get(key) or []}
    added = 0
    for e in entries:
        if e[name_field].strip().lower() not in existing:
            base.setdefault(key, []).append(e)
            existing.add(e[name_field].strip().lower())
            added += 1
    return added


def main():
    # ---- D&D ----
    with open(DND, encoding="utf-8") as f:
        dnd = json.load(f)
    a = merge(dnd, "monsters", DND_MONSTERS)
    b = merge(dnd, "spells", [{"name": n, "level_school": ls, "casting_time": ct,
                              "range": rg, "components": cp, "duration": du,
                              "description": ds, "source": SRC_DND}
                             for (n, ls, ct, rg, cp, du, ds) in DND_SPELLS])
    note = "tools/expand_catalogs.py 扩充批次（SRD 5.1 怪物/法术，CC BY 4.0）"
    if note not in dnd.get("sources", []):
        dnd.setdefault("sources", []).append(note)
    with open(DND, "w", encoding="utf-8") as f:
        json.dump(dnd, f, ensure_ascii=False, indent=2)
    print("[dnd5e] +monsters=%d +spells=%d" % (a, b))

    # ---- CoC ----
    with open(COC, encoding="utf-8") as f:
        coc_c = json.load(f)
    d = merge(coc_c, "creatures", COC_CREATURES)
    note2 = "tools/expand_catalogs.py 扩充批次（公有领域神话生物综合）"
    if note2 not in coc_c.get("sources", []):
        coc_c.setdefault("sources", []).append(note2)
    with open(COC, "w", encoding="utf-8") as f:
        json.dump(coc_c, f, ensure_ascii=False, indent=2)
    print("[coc7] +creatures=%d" % d)


if __name__ == "__main__":
    main()
