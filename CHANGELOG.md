# Changelog

本项目所有值得注意的变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Changed

- **R2 反向重构：GURPS 规则原语接入 alloy 内核**（2026-08-27）：
  - 新增 `core/dice.py` 规则原语接入层：3d6 掷骰与 GURPS 成功率表不再仓内重复实现，单一事实来源为统一引擎 alloy 的 `alloy.trpg.dice`（规则内核自 D20 并入 alloy，R2）；本仓接口保持 `roll_3d6() -> int`（内核签名适配）。
  - `core/combat_engine.py` / `mirror_mvp.py` / `core/scene_engine.py` 三处内联 3d6 实现全部改为委托内核。
  - 检定包（`ResolutionPacket`）新增 `success_chance` 字段（GURPS 3d6 roll-low 成功率），嵌套检定逐项附带；`ViewModelResult.roll_info` 直通检定明细，终端渲染显示「成功率 N%」。
  - 本仓专有规则（部位表/穿透倍率/附庸阈值/休克阈值/XP 定价）保留仓内；引擎 GURPS 4e 角色模型（ST/DX/IQ/HT）与 alloy.trpg 的 D&D 六属性模型异构，不强行映射（行为钉住 + MVVM 三层不变）。
  - 测试 +11（`test_rule_kernel`：内核同种子同值/成功率表/引擎接入面/roll_info 直通），套件 546 项全绿；Excel 生态验证 53 项不变。

## [1.0.0] - 2026-08-27

### Added

- 首个发行版：Windows 可执行程序（PyInstaller，Python 3.14）。
- 发布面：gitee [siwpan/running-group-simulator](https://gitee.com/siwpan/running-group-simulator) release `v1.0.0`（镜中之失 v1.0.0）。