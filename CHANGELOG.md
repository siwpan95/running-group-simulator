# Changelog

本项目所有值得注意的变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [3.6.0] - 2026-09-02

### Added

- 发行版重做：v3.6.0 Windows onedir zip（50.4 MB），四系统（GURPS 4e / CoC 7e /
  D&D 5e / WoD）示例模组随包；PyInstaller spec 补齐 datas（config/modules/
  characters/data/templates）与 alloy 内核 hiddenimports；真实冒烟通过
  （模组选择→角色选择→主循环→退出，stderr 无 Traceback）。
- 旧版 v1.0.0 release 保留（资产保全）；里程碑 tags v3.2~v3.6。

## [Unreleased]

### Changed

- **v3.6 内容目录工程化**（2026-09-02，多系统裁决中间件化收官）：
  - 新增 `services/catalog_service.py`：统一加载/检索各系统策展目录（`find_creature/find_spell/find_item`，支持全局或按系统查找）；
  - 新增 `tools/validate_catalogs.py`：目录 schema 校验器（coc7-catalog-v1 / dnd5e-catalog-v1，字段缺项即报错，退出码 0/1）；
  - `data/dnd5e/catalog.json` 装备目录补全为全表 50 条（weapons+armor）；
  - 新增 `tests/test_catalog_service.py` 12 项（加载/检索/校验器），四套件全绿（主 546 + Excel 53 + 画像 115 + 目录 12）。

- **v3.5 WoD 系统画像**（2026-09-02）：
  - 新增 `core/rules/wod.py`：d10 骰池（≥8 成功、10-again 再掷）、成功数 ≥5 大成功、0 成功且出 1 戏剧性失败、V5 饥饿骰（hunger 参数，大成功且饥饿骰出 10 → messy critical）、伤害平减护甲（冲击/致命/恶性）、无暴击翻倍、重伤半血震慑（受伤惩罚抽象）、防御骰池。
  - **示例模组**：`modules/wod_sample/`《夜之血约》（血族政治三幕：侦查/追踪/战斗/意志抉择）。
  - 测试：`test_rules_profiles.py` 扩至 115 项（骰池原语/大成功与戏剧性失败统计/饥饿骰 messy/成功率/场景 pool 路由）；三套件全绿。

- **v3.4 D&D 5e 系统画像**（2026-09-02）：
  - 新增 `core/rules/dnd5e.py`：d20 roll-high vs DC（自然 20 大成功/自然 1 大失败）、优势/劣势（双骰取高/低）、属性修正 `(attr-10)//2` 与技能加成（`skill_target`）、全套伤害类型（挥砍/穿刺/钝击/火焰/寒冷/闪电/强酸/雷鸣/力场/心灵/毒素/光耀/暗蚀）、大成功伤害翻倍、无主动防御掷骰（AC 已含）与无 GURPS 式休克。
  - `SystemProfile` 增 `check_style`（roll_low/roll_high）；场景引擎 roll_high 分支（节点 `dc` 字段=难度等级，修正链并入加成）；战斗引擎 roll_high 分支（d20+命中加成 vs 防御方 AC）；`Character`/`Enemy` 增 `ac` 字段（0=未启用，GURPS 零影响）。
  - **内容目录**：`data/dnd5e/catalog.json` 怪物 15 / 法术 10 / 装备 16（SRD 5.1，CC BY 4.0，attribution 入条），`tools/make_dnd5e_catalog.py` 策展提取。
  - **示例模组**：`modules/dnd_sample/`《哥布林洞窟》（dc/advantage/AC 战斗三幕）。
  - 测试：`test_rules_profiles.py` 扩至 91 项（dnd5e 成功率统计/优劣势均值/场景 DC 路由/AC 战斗）；三套件全绿。

- **v3.3 CoC 7e 系统画像**（2026-09-02）：
  - 新增 `core/rules/coc7.py`：d100 roll-low（01/五分之一大成功；100 大失败；技能<50 时 96-99 大失败）、奖励/惩罚骰（`roll_d100(bonus_dice)`）、技能目标=技能值或属性×5（`skill_target`）、护甲平减、重伤检定（单次 ≥ HP/2 → CON×5 失败失去意识）、大成功不翻倍。
  - `SystemProfile` 增 `skill_target`/`crit_damage` 扩展点；`shock_check` 阈值下沉画像（GURPS HP/3、CoC HP/2）。
  - **SAN 理智系统**：`Character` 增 `san/san_max/san_loss_log/insanity_state`（san_max=0 不启用，GURPS 角色零影响）；单次损失 ≥5 临时疯狂、≥ HP 上限 1/5 不定期疯狂；节点 `layer_physics.san_loss` 配置失败扣 SAN，疯狂发作注入叙事与标签。
  - `mirror_mvp._resolve_system_id()`：按 `meta.systems` 首个 → `compatible_core` 映射 → 默认 gurps 路由场景+战斗画像。
  - **内容目录**：`data/coc7/catalog.json` 首批 35 条神话生物（均值能力/耐久/伤害加权/武器/装甲/理智丧失/来源 trow-11676），由 `tools/make_coc7_catalog.py` 半自动提取+人工抽核（巨噬蠕虫 1d100×10=505 等与原文核对）。
  - **示例模组**：`modules/coc_sample/`《旧宅的低语》（d100 调查 + SAN 损失 + 疯狂发作三幕）。
  - 测试：`test_rules_profiles.py` 扩至 63 项（coc7 画像/d100 统计倾向/SAN/场景路由）；三套件全绿。
- **规则书资源库整体迁入**（2026-09-02，用户拍板）：`F:\novel\规则书\trpg_rulebooks` → 项目内 `规则书/trpg_rulebooks`（robocopy 175,620 文件 / 2.786 GB，0 失败；`.gitignore` 排除 `/规则书/`，不入 git，版权归各出版方）；库内 README/交接报告/汇编脚本路径引用同步更新。

- **v3.2 多系统裁决内核抽象**（2026-09-02，拓展规划见 `docs/拓展规划-2026-09-02.md`）：
  - 新增 `core/rules/`：`SystemProfile` 画像基类 + 注册表（`get_profile/register_profile/available_systems`）+ **GURPS 4e 参考实现**（`core/rules/gurps.py`，检定/伤害/部位/穿透/主动防御/休克原语自 `combat_engine`/`scene_engine` 原样迁移，行为零变化）。
  - `CombatEngine`/`SceneEngine` 增加 `system_id` 参数，规则细节委托画像（引擎只做编排与实体状态应用）；静态接口（`roll_damage`/`get_damage_type`/`roll_hit_location`/`HIT_LOCATIONS`）保留导出兼容。
  - `ResolutionPacket` 新增 `system` 字段；`mirror_mvp.physical_resolve` 改委托画像。
  - 新增 `config/systems.json`（默认系统与画像元信息声明）；模组建议改用 `meta.systems: ["gurps", ...]` 声明可用系统（`compatible_core` 保留向后兼容）。
  - 测试：新增 `tests/test_rules_profiles.py` 35 项（注册表/画像原语/引擎委托/场景检定 system 字段）；既有套件全绿（主套件 546 + Excel 53）。

- **R2 反向重构：GURPS 规则原语接入 alloy 内核**（2026-08-27）：
  - 新增 `core/dice.py` 规则原语接入层：3d6 掷骰与 GURPS 成功率表不再仓内重复实现，单一事实来源为统一引擎 alloy 的 `alloy.trpg.dice`（规则内核自 D20 并入 alloy，R2）；本仓接口保持 `roll_3d6() -> int`（内核签名适配）。
  - `core/combat_engine.py` / `mirror_mvp.py` / `core/scene_engine.py` 三处内联 3d6 实现全部改为委托内核。
  - 检定包（`ResolutionPacket`）新增 `success_chance` 字段（GURPS 3d6 roll-low 成功率），嵌套检定逐项附带；`ViewModelResult.roll_info` 直通检定明细，终端渲染显示「成功率 N%」。
  - 本仓专有规则（部位表/穿透倍率/附庸阈值/休克阈值/XP 定价）保留仓内；引擎 GURPS 4e 角色模型（ST/DX/IQ/HT）与 alloy.trpg 的 D&D 六属性模型异构，不强行映射（行为钉住 + MVVM 三层不变）。
  - 测试 +11（`test_rule_kernel`：内核同种子同值/成功率表/引擎接入面/roll_info 直通），套件 546 项全绿；Excel 生态验证 53 项不变。

### Removed

- 移除误跟踪的 `__pycache__/*.pyc`（47 个历史构建产物，跨 Python 3.13/3.14）；`.gitignore` 重写为 Python 口径并补齐 `__pycache__/`、`build/`、`dist/`、`*.spec`（spec 含本地路径不入库）；删除本地备份 `CHANGELOG.md.local-bak-*`。

### Added

- 规划文档 `docs/拓展规划-2026-09-02.md`：多系统裁决中间件化路线图（v3.3 CoC 7e → v3.4 D&D 5e → v3.5 WoD → v3.6 内容目录工程化），资源库 `F:\novel\规则书\trpg_rulebooks` 为取材来源。

## [1.0.0] - 2026-08-27

### Added

- 首个发行版：Windows 可执行程序（PyInstaller，Python 3.14）。
- 发布面：gitee [siwpan/running-group-simulator](https://gitee.com/siwpan/running-group-simulator) release `v1.0.0`（镜中之失 v1.0.0）。