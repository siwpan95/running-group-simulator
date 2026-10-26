# Mirror of the Lost（镜中之失）

> 仓库：<https://gitee.com/siwpan/running-group-simulator> ｜ 许可：MIT-0（MIT No Attribution）（见 [LICENSE](LICENSE)）
> 注：文中 <PATH> 为路径占位符，请替换为你本机实际的目录 / 可执行文件路径。

> 基于 GURPS 4e 的三层 MVVM 架构 TRPG 终端引擎 — 让 GM 专注于叙事，让引擎处理裁决。

---

## 项目概述

Mirror of the Lost 是一个 **终端驱动** 的 TRPG（桌上角色扮演游戏）中间件引擎。它不替代 GM——它替代骰子、规则查询和状态追踪，让 GM 从机械劳动中解放出来，专注于讲故事。

### 设计哲学

| 层 | 来源 | 职责 | 红线 |
|---|------|------|------|
| **Model（物理层）** | GURPS 4e | 属性/技能/伤害/环境物理。确定性状态管理。 | 不可输出叙事文本 |
| **ViewModel（叙事层）** | Fate Core | 裁决包→叙事转换。锚点查表。玩家宣告。 | 不可修改物理值 |
| **View（节奏层）** | Savage Worlds | 终端渲染。先攻抽牌。流程控制。 | 不直接读 Model |

核心接口是两个结构体：
- `ResolutionPacket`（物理层产出）→ 骰子/伤害/部位/穿透
- `ViewModelResult`（叙事层产出）→ 叙事文本/标签/专注点动作/事件队列

### 特色机制

- **数据驱动场景引擎** — module.json 的 `nodes[]` 数组驱动所有游戏逻辑，支持 5 种场景类型（perception/investigation/feat/combat/explore）
- **锚点查表** — 27 条扩展锚点短语（9 部位×3 伤害等级×3 伤害类型），实现"裁决包→叙事"的自动化转换
- **双币制** — 专注点（改情境/加标签/触发特征）vs 幸运点（重掷骰子），互不交叉
- **环境即第一 NPC** — EnvironmentSystem 持续产出标签，玩家可花专注点改变环境
- **附庸阈值系统** — ≥6 伤害立即移除，2-5 丧失行动力，<2 轻微干扰——切掉 GURPS 打群架的数学爆炸
- **休克系统** — HP/3 阈值，HT 检定失败则震慑 1 回合（-4 惩罚）
- **部位伤害** — 3d6 掷部位表，头/臂/腿/躯干各有不同效应标签
- **XP 成长** — 属性购买价格 ST/HT=10, DX/IQ=20

---

## 目录结构

```
pt/
├── README.md                    ← 本文件
├── requirements.txt             ← 依赖清单（纯标准库，仅记录 Python 版本）
├── mirror_launcher.py           ← 启动入口（游戏主循环）
├── mirror_mvp.py                ← 核心引擎（MVVM 集成中心）
│
├── config/                      ← 项目配置
│   ├── system.json              │  系统配置（规则引擎、内容库、架构描述）
│   └── systems.json             │  多系统画像注册声明（v3.2，default_system）
│
├── core/                        ← Model + ViewModel 层
│   ├── character.py             │  GURPS 角色数据模型（四属性/衍生/技能/特征/装备）
│   ├── dice.py                  │  规则原语接入层（3d6 掷骰 + GURPS 成功率表 → alloy 内核，R2）
│   ├── rules/                   │  多系统裁决画像（v3.2）：base 接口 + 注册表 + gurps 参考实现
│   ├── enemy.py                 │  敌人模型（mook/elite/wildcard/boss）
│   ├── scene_engine.py          │  数据驱动场景引擎（module.json → 节点执行）
│   ├── combat_engine.py         │  战斗引擎（先攻/攻击/防御/休克/部位）
│   ├── viewmodel.py             │  ResolutionPacket → ViewModelResult 转换管线
│   └── environment_system.py    │  环境标签系统（加载/进化/玩家交互）
│
├── services/                    ← 辅助服务层
│   ├── item_system.py           │  物品运行时（装备/消耗品/效果查询）
│   ├── xp_system.py             │  XP 计算/成长/升级选项
│   ├── save_manager.py          │  存档管理（角色快照 + 进度 JSON）
│   ├── scene_resolver.py        │  场景结算（专注回复/印记消减/执念检查）
│   └── data_importer.py         │  统一数据导入器
│
├── view/                        ← View 层（终端渲染）
│   ├── terminal_renderer.py     │  所有终端输出收拢模块
│   └── character_sheet.py       │  角色卡渲染（完整/紧凑模式）
│
├── data/                        ← 游戏数据
│   ├── enemies.json             │  敌人库
│   └── items.json               │  物品库
│
├── characters/                  ← 玩家角色卡（JSON，7 张预置）
│   ├── 预置-调查记者.json
│   ├── 预置-退役军警.json
│   ├── 预置-神秘学学者.json
│   ├── 预置-街头混混.json
│   ├── 预置-急诊医生.json          │  IQ 13，急救/诊断/药学
│   ├── 预置-自由黑客.json          │  IQ 14，计算机/电子/情报分析
│   └── 预置-古董商.json            │  IQ 13，鉴赏/神秘学/历史
│
├── modules/                     ← 模组（每个模组一个子目录，5 个示例）
│   ├── mirror_house_alley/      ← 镜屋巷（GURPS 4e，3 幕）
│   ├── coc_sample/              ← 旧宅的低语（CoC 7e，3 幕）
│   ├── dnd_sample/              ← 哥布林洞窟（D&D 5e，3 幕）
│   ├── wod_sample/              ← 夜之血约（WoD，3 幕）
│   └── coc_saltmarsh/          ← 盐沼低语（CoC 7e，3 幕，引用扩充目录神话生物）
│
├── templates/                   ← 内容创作模板
│   ├── characters/              │  角色卡 Excel 模板
│   │   ├── character.xlsx       │  │  空白角色卡
│   │   ├── 预置-调查记者.xlsx    │  │  IQ 13 调查记者
│   │   ├── 预置-退役军警.xlsx    │  │  ST 13 退役军警
│   │   ├── 预置-神秘学学者.xlsx  │  │  IQ 14 神秘学学者
│   │   └── 预置-街头混混.xlsx    │  │  DX 13 街头混混
│   ├── gm-data/                 │  GM 数据 Excel 模板
│   │   ├── enemy_builder.xlsx   │  │  敌人构建器
│   │   ├── item_builder.xlsx    │  │  物品构建器
│   │   ├── trap_builder.xlsx    │  │  陷阱构建器
│   │   ├── encounter_table.xlsx │  │  遭遇表
│   │   ├── loot_table.xlsx      │  │  战利品表
│   │   └── npc_reaction.xlsx    │  │  NPC 反应表
│   ├── gm-module/               │  GM 模组 Excel 模板
│   │   ├── scene_builder.xlsx   │  │  场景构建器
│   │   ├── module_meta.xlsx     │  │  模组元信息
│   │   └── map_grid.xlsx        │  │  网格地图
│   └── json-templates/          │  JSON 空白模板
│       ├── character_template.json
│       ├── enemy_template.json
│       ├── item_template.json
│       ├── module_template.json
│       └── scene_node_template.json
│
├── saves/                       ← 存档目录（自动创建）
│
├── tools/                       ← 工具脚本
│   ├── make_templates.py        │  一键生成 Excel 模板
│   └── char_importer.py         │  角色卡 Excel → JSON 导入器
│
├── tests/                       ← 测试套件
│   ├── test_comprehensive.py     │  546 项全覆盖测试
│   ├── test_excel_roundtrip.py  │  Excel 生态回验证
│   └── test_rules_profiles.py   │  多系统裁决画像测试（v3.2，35 项）
```

---

## 快速开始

### 环境要求

- Python 3.10+
- 依赖 **alloy**（统一引擎规则内核；零第三方库）：

```bash
pip install -e <PATH>
```

### 运行游戏

```bash
cd pt
python mirror_launcher.py
```

启动后将看到：
1. Splash 画面 → 2. 模组选择 → 3. 角色选择（4 预置 + 快速创建） → 4. 游戏主循环

### 快捷键

| 按键 | 功能 |
|------|------|
| `C` | 查看完整角色卡 |
| `S` | 保存进度 |
| `H` | 帮助菜单 |
| `Q` | 退出（主菜单） |

### 运行测试

```bash
cd pt
python tests/test_comprehensive.py
python tests/test_excel_roundtrip.py
python tests/test_rules_profiles.py      # v3.2 多系统画像
python tests/test_catalog_service.py     # v3.6 内容目录服务
python tests/test_catalog_bridge.py       # v3.6 目录→实体桥接（内容目录消费方）
python tools/validate_catalogs.py        # 内容目录 schema 校验
```

546 项测试覆盖 16 个模块，验证核心路径与边缘情况；Windows GBK 控制台
下建议 `set PYTHONUTF8=1`（否则套件末尾的 ✔/emoji 输出会报 UnicodeEncodeError）。

### Excel 生态验证

```bash
cd pt
python tests/test_excel_roundtrip.py
```

53 项回验证确保 Excel → JSON 转换完整性。

---

## 内容创作指南

### 创建角色

1. 复制 `templates/json-templates/character_template.json` 到 `characters/`
2. 填写属性（ST/DX/IQ/HT）、技能、特征、装备
3. 文件即角色——放在 `characters/` 目录下即被自动发现

**属性说明**：
- `ST`（力量）— 近战伤害、负重、HP
- `DX`（敏捷）— 命中、闪避、精细操作
- `IQ`（智力）— 技能、感知、意志
- `HT`（体质）— 生命值、抗性、疲劳

**特征格式**（触发-响应模式）：
```json
{
  "name": "特征名",
  "trigger_condition": "自然语言触发条件",
  "cost": 1,
  "effect": "效果描述",
  "per_scene_limit": 2
}
```

### 创建模组

1. 在 `modules/` 下新建子目录
2. 复制 `templates/json-templates/module_template.json` 为 `module.json`
3. 填写 meta 信息 → 定义 act_1/act_2/act_3 → 填充 nodes[]

**场景类型**：

| scene_type | 说明 | 核心配置 |
|------------|------|----------|
| `perception` | 感知检定 | `skill_check` + `modifier` |
| `investigation` | 调查节点 | `skill_checks[]`（嵌套检定） |
| `feat` | 壮举/挑战 | `skill_check` + `tool_bonus` |
| `combat` | 战斗 | `unit_stats` + `special_mechanic` |
| `explore` | 纯叙事 | `auto_success: true` |

**节点门控**：
- `prerequisite_nodes` — 前置节点列表（必须全部完成）
- `next_nodes` — 解锁的后续节点
- ViewModel 自动产出 `queued_events` 驱动流程推进

### 创建敌人

添加到 `data/enemies.json` 的 `enemies[]` 数组。

| enemy_type | 说明 |
|------------|------|
| `mook` | 杂兵——附庸阈值系统，不追踪单个体 |
| `elite` | 精英——完整追踪 HP，有属性 |
| `wildcard` | 特殊——有复杂特殊机制 |
| `boss` | Boss——完整属性 + 多阶段 |

### 从内容目录引用敌人（推荐）

战斗节点里无需手写属性——直接引用已扩充的目录条目，由 `services/catalog_bridge` 落地为可战斗实体：

```json
{
  "node_id": "2.2_ambush",
  "scene_type": "combat",
  "layer_physics": {
    "catalog_ref": { "name": "深潜者", "system": "coc7" }
  }
}
```

`catalog_ref` 也接受纯字符串（如 `"Goblin"`）。引擎按模块 `meta.systems` 自动选用对应系统画像解释数值。详见 `tests/test_catalog_bridge.py`。

### 创建物品

添加到 `data/items.json` 对象中（以物品 ID 为键）。

| type | 说明 | 示例 |
|------|------|------|
| `weapon` | 武器 | `damage: "2d6 pi+"` |
| `armor` | 护甲 | `dr: 4, dr_location: "躯干"` |
| `tool` | 工具 | `tool_bonus: +2` |
| `consumable` | 消耗品 | `uses: 1, restore_hp: "1d6"` |
| `key_item` | 关键道具 | 剧情相关 |

---

## 规则速查

### 3d6 裁决

| 掷骰 | 结果 |
|------|------|
| 3-4 | 大成功（Crit Success） |
| 5 ~ 目标值 | 成功 |
| 目标值+1 ~ 16 | 失败 |
| 17-18 | 大失败（Fumble） |

### 部位表（3d6）

| 掷骰 | 部位 |
|------|------|
| 3-5 | 头 |
| 6-7 | 右臂/左臂 |
| 8-13 | 躯干 |
| 14-16 | 右腿/左腿 |
| 17-18 | 头 |

### 伤害类型

| 类型 | 穿透倍率 |
|------|----------|
| 切割（cut） | ×1.5 |
| 穿刺（imp/pi+）| ×2 |
| 钝击（cr） | ×1.0 |
| 燃烧（burn） | ×1.0 + 持续 |

### 双币制

| | 专注点 | 幸运点 |
|---|--------|--------|
| 作用 | 改情境（标签/特征） | 改骰子（重掷） |
| 默认值 | 3/3 | 2/2 |
| 回复 | 场景结算 / 安全节点 | 模组结束 |
| 消耗 | 1-2 点/次 | 1 点/次 |

### 附庸阈值

| 伤害 | 效果 |
|------|------|
| ≥6 | 立即移除 |
| 2-5 | 丧失行动力 / 溃逃 |
| <2 | 轻微干扰 |

---

## 规则原语接入（R2 · 2026-08-27）

3d6 掷骰与 GURPS 成功率表**不在本仓重复实现**：单一事实来源为统一引擎 alloy 的
`alloy.trpg.dice`（TRPG 规则内核，自 D20 并入 alloy，R2），经 `core/dice.py`
签名适配后供全仓调用。检定包 `success_chance` 字段与终端「成功率 N%」显示即来自
该内核数据。

**保留仓内**（引擎专有规则，不进引擎）：部位表（3d6）、伤害穿透倍率、附庸阈值、
休克阈值、XP 定价（ST/HT=10、DX/IQ=20）与 GURPS 4e 角色模型（ST/DX/IQ/HT 四属性
——与 alloy.trpg 的 D&D 六属性模型异构，按「行为钉住 + MVVM 三层不变」不强行映射）。

借鉴必记账：3d6 掷骰 + GURPS 成功率表 ← alloy.trpg.dice（自 D20 并入，R2）；
接入测试见 `tests/test_comprehensive.py` §16（内核同种子同值/成功率表/引擎接入面）。

## 规则书资源库（2026-09-02）

本项目收集的 TRPG 规则书库位于**项目内 `规则书/trpg_rulebooks/`**（约 17.6 万文件
/ 2.8 GB，已整体迁入本仓目录但**不入 git**——见 .gitignore，版权归各出版方；
明细见库内 `README.md` 与 `manifest.json`），是本引擎的**参考资源库**：

- **GURPS 直接相关**：`TRPGrepo/其他规则/` 泛统基本集整合 PDF、泛统第四版基本集_角色
  PDF；`trow_books/GURPS4_Basic`（第四版基本规则中译 13 章）、`GURPS4_Characters`
  （基本集角色篇）、`GURPS_Extensions`（第三版扩展：龙/克苏鲁朋克/技术法师/超人太空/
  半人马座阿尔法/基础设定，145.8 万字符）；`trow_rulebooks/forum_62` 泛统散帖。
- **取材与校对用途**：引擎数值（成功率表、部位表、伤害类型、附庸阈值）的规则依据
  在此库核对；后续扩展（魔法/超自然/科幻世设）可从 GURPS 扩展册取材。
- 库内 T.R.O.W. 论坛内容为社区翻译（GPL-2.0 vendored 口径，见库内说明），
  规则本体版权归 Steve Jackson Games，仅作个人研究参考，不随本仓分发。

> 归属：该资源库为**本项目配套资源**（用户 2026-09-02 明确），不是独立项目；
> 库本身尚未建立版本控制，如需入仓另行规划。

## 内容规模（2026-10-26 扩充）

结合联网核对（SRD 5.1 以 OGL + CC BY 4.0 双重许可发布，可带署名转载；克苏鲁神话本体已进入公有领域）对内容目录做了大幅扩充，**全部通过 `tools/validate_catalogs.py` 校验**：

| 内容 | 扩充前 | 扩充后 |
|------|--------|--------|
| `data/dnd5e/catalog.json` 怪物 | 15 | **83** |
| `data/dnd5e/catalog.json` 法术 | 10 | **47** |
| `data/dnd5e/catalog.json` 物品（SRD 武器+护甲全表） | 50 | 50（本就全表，未重复） |
| `data/coc7/catalog.json` 神话生物 | 35 | **57** |
| 玩家预置角色卡 | 4 | **7** |
| 敌人库 / 物品库 / 示例模组 | — | 各新增若干（敌人 +4、物品 +4、模组 +1《盐沼低语》） |

扩充脚本 `tools/expand_catalogs.py`（目录）与 `tools/expand_content.py`（角色/敌人/物品）均按 `name` 去重、不覆盖既有条目，可重复运行追加。

### 内容目录消费方（v3.6 · 解决“只扩充不消费”）

目录里的怪物 / 神话生物现在**真正接入引擎**，不再只是被 `CatalogService` 检索：

1. **`services/catalog_bridge.py`（新增，`build_enemy_from_catalog(name, system)`）**：把 `data/<system>/catalog.json` 的策展条目落地为 `core.enemy.Enemy`。D&D 输出原生数值（`attack_skill`=命中加值、`ac`=护甲等级），CoC 输出原生数值（`attack_skill`=武器百分比、`dodge`=DEX×2、`dr`=护甲值），由战斗引擎按模块 `meta.systems` 自动路由到对应系统画像解释。
2. **场景引擎战斗节点**：`core/scene_engine.py._handle_combat_node` 支持 `layer_physics.catalog_ref`（字符串或 `{name, system}`）。命中目录时由 bridge 生成敌人，未命中则回退内联 `unit_stats`。
3. **MVP 便捷入口**：`mirror_mvp.MirrorOfLost.spawn_enemy_from_catalog / start_combat_from_catalog`。
4. **示例模组接线**：`modules/coc_saltmarsh` 的 `2.2_ambush` 战斗节点已用 `catalog_ref: {name: "深潜者", system: "coc7"}` 真正引用目录条目（而非仅文字提及）。

测试：`tests/test_catalog_bridge.py`（21 项，零第三方依赖）。

## 多系统裁决中间件（v3.2 · 2026-09-02）

裁决规则从「GURPS 硬编码」重构为**可插拔系统画像**（`core/rules/`）：

- `SystemProfile` 接口 = 检定 / 伤害 / 部位 / 穿透 / 主动防御 / 休克；
  GURPS 4e 是首个参考实现（`core/rules/gurps.py`，行为与 v3.1 完全一致）；
- `CombatEngine` / `SceneEngine` 以 `system_id` 路由画像，`ResolutionPacket`
  携带 `system` 字段；ViewModel（锚点叙事）与 View（终端渲染）保持系统无关；
- 模组声明可用系统：`meta.systems: ["gurps"]`（`compatible_core` 向后兼容）。

**路线图**（详见 `docs/拓展规划-2026-09-02.md`）：v3.2 内核抽象 ✅ → v3.3 CoC 7e ✅
→ v3.4 D&D 5e ✅ → v3.5 WoD ✅ → v3.6 内容目录工程化 ✅（`CatalogService` 统一
加载/检索 + `tools/validate_catalogs.py` schema 校验）——**多系统裁决中间件化全线完成**。
规则取材与校对来源：项目内资源库 `规则书/trpg_rulebooks`（见「规则书资源库」节）。

## 发行版（Windows）

- **v3.6.0**（2026-09-02）：PyInstaller onedir 打包 zip（50.4 MB），config/modules/
  characters/data/templates 与 alloy 内核随包，解压双击 `running-group-simulator.exe`
  即玩（含 CoC/D&D/WoD/GURPS 四系统示例模组）。本地留存
  `installer/running-group-simulator-v3.6.0-win64.zip`（git 忽略）。
- 旧版 v1.0.0（2026-08-27，GURPS 单系统）release 页面保留在 gitee，不删除。
- 冒烟协议：调试构建 + 真实冒烟（cmd 重定向 stdin 走完 模组选择→角色选择→主循环→退出，
  stderr 无 Traceback）。

## 开发指南

### 架构红线（不可违反）

1. Model 不输出叙事 — 只产出 ResolutionPacket
2. ViewModel 不修改物理值 — 只产出叙事标签
3. View 不绕过 VM 直接读 Model 原始数据
4. 战斗引擎攻击链路：`attack_resolve()` → `active_defense()` → `shock_check()` → `apply_damage()`，不可跳步

### 添加新子系统

1. 确定层级归属（core / services / view）
2. 创建模块文件
3. 在 `mirror_mvp.py` 的 `__init__` 中集成
4. 更新 `config/system.json` 的 `architecture.layers`
5. 写测试 → `tests/test_comprehensive.py`

### 添加新模组

1. 在 `modules/` 下新建目录
2. 复制 `templates/json-templates/module_template.json`
3. 确保 `module_id` 唯一，`system_name` = "Mirror of the Lost"
4. 遵循 scene_type 规范（perception/investigation/feat/combat/explore）
5. 定义完整的 prerequisite_nodes / next_nodes 门控图

---

## 许可证

概念框架：CC BY-NC-SA 4.0  
规则基础：GURPS 4e（Steve Jackson Games）

---

## 版本历史

| 版本 | 日期 | 里程碑 |
|------|------|--------|
| v1.0 | — | 基础架构，脚本驱动 |
| v2.0 | 2026-06-06 | MVVM 三层重构，数据驱动，15 模块，535 测试 |
| v3.1 | 2026-06-06 | 完整角色系统、战斗引擎、VM 管线、XP 成长 |
| v3.2 | 2026-09-02 | 多系统裁决内核抽象（SystemProfile + 注册表 + GURPS 参考实现，行为零变化） |
| v3.3 | 2026-09-02 | CoC 7e 系统画像（d100/奖励惩罚骰/SAN 理智+疯狂发作）+ 生物目录 35 条 + 示例模组 |
| v3.4 | 2026-09-02 | D&D 5e 系统画像（d20 vs DC/优劣势/AC 战斗）+ SRD 目录 41 条 + 示例模组 |
| v3.5 | 2026-09-02 | WoD 系统画像（d10 骰池/10-again/戏剧性失败/饥饿骰）+ 示例模组 |
| v3.6 | 2026-09-02 | 内容目录工程化（CatalogService + schema 校验器 + 目录测试 12 项） |

---

*"镜子从不撒谎——它只是展现一个方向。"*
