# Implementation Plan: KylinMemoryBench MVP

## Overview

构建一个 Python 3.9+、证据驱动的长期记忆 Benchmark 最小闭环：声明式 YAML 用例由统一 Agent 适配器执行，运行事件以 JSONL 保存，确定性检查器输出六类能力分数、失败分类和可解释理由，CLI 支持单 Agent 运行与双 Agent 对比。

## Architecture Decisions

- 使用标准库 `argparse`、`dataclasses` 和 PyYAML，避免 GUI/云服务依赖阻塞 openKylin 部署。
- `AgentAdapter` 只暴露 `run(case) -> EvidenceEvent[]`，外部真实 Agent 可通过同一协议接入；内置两个确定性基线仅用于演示评分区分度。
- 检查项采用 `answer_contains`、`answer_not_contains`、`memory_recall`、`memory_absent`、`action_path` 等可解释规则，禁止把 LLM 裁判作为唯一依据。
- 运行结果保留事件序号、时间戳、案例/Agent 标识和检查理由，便于审计与复现。

## Task List

### Phase 1: Foundation

- [x] T1 数据模型与六类最小用例
- [x] T2 双 Agent 适配器
- [x] T3 执行、证据和确定性评分

### Checkpoint A

- [x] 六类案例可执行并生成 JSONL 证据
- [x] 单案例评分具备逐项理由

### Phase 2: CLI and Reporting

- [x] T4 CLI 与报告
- [x] T5 测试与回归（自动测试 + CLI/异常手动回归）
- [x] T6 openKylin 运行说明与方案文档

### Checkpoint B

- [x] `run` 与 `compare` 对两个 Agent 产生可复现结果
- [x] 文档、样例数据和运行命令齐全

## Risks and Mitigations

| 风险 | 影响 | 缓解 |
|---|---|---|
| 尚未确定真实 Agent | 高 | 适配器协议开放；内置基线只作为演示并明确标注 |
| 无 openKylin 实机 | 高 | 仅声明 Python 兼容路径，记录待实机验证，不虚构结果 |
| 规则覆盖不足 | 中 | 六类能力各有显式 checks，并测试失败/异常路径 |
| 依赖不可用 | 中 | 仅依赖 PyYAML；CLI 和报告使用标准库 |

## Open Questions

- 赛事指定的 openKylin 版本和镜像是什么？
- 最终纳入对比的两款 Agent 如何导出记忆与工具轨迹？
- 仓库许可证和首版数据集规模由谁确认？

## 赛事可验收推进记录

- 已完成对抗套件、证据引用、状态序列检查、重试/运行元数据、Replay 适配器、CLI 校验命令和离线 HTML 报告。
- 对抗套件与 HTML 报告已完成；真正的证据图谱视图仍列为 T7c 未完成。
- 真实 Agent 和 openKylin 实机仍是外部阻塞，不能用内置基线或当前 Windows 环境替代验收结论。

## Current Blocker Progress (2026-09-02)

- [x] Added `OpenAICompatibleAgent` (`type: http`, aliases `openai`/`openai_compatible`) for providers such as Doubao/Ark and DeepSeek.
- [x] Added `configs/agent-doubao.yaml` and `configs/agent-deepseek.yaml`; API keys are referenced by environment-variable name only.
- [x] Added HTTP evidence mapping for assistant messages, tool calls, and provider/wrapper-supplied `kmb_evidence`; no memory state is inferred from plain text.
- [x] Added mock HTTP regression coverage and updated the external evidence protocol.
- [ ] Real Agent run: blocked until model/Endpoint IDs, rotated credentials, network/quota, and memory-evidence export are confirmed.
- [ ] openKylin validation: blocked until target version, architecture, image/device access, and package-install permissions are provided.

### Latest execution record

- Grok 4.6 and DeepSeek v4 flash were each run through the transparent `MemoryControllerAgent` in `runs/controller-compare-v2/` using the same six-case suite, seed 42, retry 1, and 300-second case timeout.
- Each run contains 70 validated events: wrapper memory/action events are distinct from model request/response and assistant events. Scores: Grok 86.11; DeepSeek 94.44.
- A project-local environment `.venv-kmb-system` was created and used for CLI validation. No project dependency or result was intentionally placed under `C:`; temporary pip paths are pinned to project-local `.tmp-pip`/`.pip-cache` by the provided install scripts.
- openKylin remains unverified because this Windows host has no openKylin VM/image and no available QEMU, VirtualBox, VMware, Podman, Hyper-V cmdlet, or running Docker daemon.
