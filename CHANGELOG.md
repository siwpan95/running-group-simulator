# Changelog

本项目所有值得注意的变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Changed

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