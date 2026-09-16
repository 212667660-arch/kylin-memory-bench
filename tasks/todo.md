# KylinMemoryBench 任务清单

> 状态基线以 `docs/release-freeze.md`（2026-09-09）与本文为准。openKylin VM / `.deb` 已完成；视频与项目级 LICENSE 仍待办。

## 必须完成

- [x] T1 数据模型与六类最小用例（`kmb/models.py`、`suites/core-zh.yaml`）
- [x] T2 双 Agent 适配器（`kmb/agents.py`，含 HTTP / wrapper / replay / no-memory）
- [x] T3 执行、证据与确定性评分（`kmb/runner.py`、`kmb/scoring.py`）
- [x] T4 CLI 与报告（run/compare/validate/list-cases/serve；JSON/MD/HTML/SVG）
- [x] T5 测试与回归（当前 59 项 unittest 全绿）
- [x] T6 openKylin 运行说明与方案文档（VM 2.0 SP2 实测记录）

## 建议完成

- [x] T7a 对抗用例（`suites/adversarial/`）
- [x] T7b HTML 报告、失败统计、证据下钻
- [x] T7d 扩展中文套件（`suites/core-zh-expanded.yaml`，每类 +3，共 18 案例）
- [x] T7e 无凭据离线一键 demo（`scripts/run_offline_demo.sh`）
- [x] T7f 评委复现卡（`docs/judge-reproduction-card.md`）
- [ ] T7c 证据图谱可视化（可选增强）
- [ ] T8 项目级 LICENSE 定稿（`LICENSE-MIT-CANDIDATE.txt` 已备选）

## 真实 Agent 与 openKylin

- [x] Q2 真实后端：Grok `grok-4.6` + DeepSeek `deepseek-v4-flash`；原生 API 与透明包装层均已运行并分轨标注
- [x] B2 openKylin 2.0 SP2 VM：源码安装、双 Agent 运行、`.deb` release7 生命周期与包审计完成（见 `runs/openkylin-validation-20260909/`、`runs/deb-lifecycle-authorized-20260908-rerun6/`）
- [ ] B3 桌面演示视频 3–5 分钟（脚本：`docs/demo-script.md`；无 DISPLAY 时未录）
- [ ] B4 接入 1 个 openKylin 原生生态 Agent 进程适配器（可选提分项）

## 表述边界（发布材料强制）

- reference/flawed → `simulated_baseline`，只证明流水线
- `source=wrapper` → 系统级「模型后端 + 外部控制器」
- 真实 API 轨道 `native_memory_events=0` → **不得**写成模型原生长期记忆

## 下一步（负责人）

1. 确认并落地根目录 `LICENSE`（MIT 候选或其它）
2. 在 openKylin 桌面录制 3–5 分钟视频（按 `docs/demo-script.md`）
3. （可选）指定原生生态 Agent，便于接入统一证据协议
