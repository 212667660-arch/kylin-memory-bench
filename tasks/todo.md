# KylinMemoryBench 任务清单

> 口径与 `docs/release-freeze.md`、README 一致。**本机 P1 已完成；openKylin 实机迁移验收后置，不在本阶段宣称「实机已验证」。**

## 必须完成（本机）

- [x] T1 数据模型与六类最小用例
- [x] T2 双 Agent 适配器（deterministic / HTTP / wrapper / replay / command / process）
- [x] T3 执行、证据与确定性评分
- [x] T4 CLI 与报告（含 serve 本地工作台）
- [x] T5 测试与回归（59 项 unittest）
- [x] T6 方案与 openKylin 运行说明文档

## P1 提分项（本机，2026-09-16）

- [x] **扩大套件**
  - `suites/core-zh-expanded.yaml`：每类 +3，共 18
  - `suites/adversarial/extended.yaml`：冲突 / 相近实体 / 噪声 / 敏感 / 跨任务，每类 3 条，共 15
- [x] **接入 1 个 openKylin 生态 Agent（进程适配器）**
  - `configs/agent-kylinbot-process.yaml` + `scripts/openkylin_ecosystem_agent.py`
  - 协议：CommandAgent（stdin case JSON → stdout JSONL evidence，`source=process`）
  - 本机 `kmb run/compare` 已跑通；实机可将 command 指到原生 KylinBot/kylin-agent 包装
- [x] **无凭据一键 replay/对比 demo**
  - `bash scripts/run_offline_demo.sh runs/offline-demo`
  - reference × kylinbot-process（核心 / 扩展 / 对抗扩展）+ reference × flawed 对照
  - 双侧均完成评测后才校验 `comparison.html` 与两侧 radar
- [x] **文档口径统一**
  - `tasks/todo.md` / README / `docs/release-freeze.md` 对齐本机完成态与表述边界

## 历史记录（非本阶段完成定义）

- openKylin 2.0 SP2 VM 与 `.deb` 生命周期曾有归档证据（见 release-freeze）；**迁入实机验收不在本次 P1 完成定义内**。
- 桌面演示视频仍待录（`docs/demo-script.md`）。
- 项目级 LICENSE 仍待负责人确认。

## 表述边界（强制）

| 来源 | 可写 | 不可写 |
|------|------|--------|
| `simulated`（reference/flawed） | 流水线可区分正确/错误记忆行为 | 真实模型能力 |
| `process` / `wrapper` | 系统级进程/控制器行为 | 模型原生长期记忆 |
| 真实云 API（native_memory_events=0） | 可观察文本与请求 | 原生记忆能力 |

## 下一步

1. 在 openKylin 实机执行 `scripts/run_offline_demo.sh` 与真实 Agent 验收（迁移）
2. （可选）将 process 适配器 command 切换为真实 KylinBot 二进制
3. LICENSE 与 3–5 分钟桌面视频
