# 2026-10-13 非视频工程收口

- 0.2.1：Windows/openKylin 158 项测试通过；跨平台 wheel 和 Debian 生命周期 CI 全绿。
- openKylin 隔离真实 dpkg：release9→0.2.1 安装/升级/完整验收/卸载/残留检查九步全 0；主系统包数据库未变。
- 修复同步 GitHub main；最终源码、wheel、`.deb`、PDF、样例证据与哈希见 `dist/submission-nonvideo-20261013/`。
- 用户明确排除视频；仓库实际私有，公开/评委授权方式待用户确认；正式提交还缺参赛身份与报名确认邮件指引，邮件草稿已备。
- 详细当前判断见 `docs/completion-audit-20261013.md`。下文为此前阶段记录。

# KylinMemoryBench 任务清单

> 口径与 `docs/release-freeze.md`、README 一致。**PDF a-d 的代码、CLI/GUI、样例与真实双 Agent 快速对比已复核；桌面视频（e）待录制；项目级 LICENSE 已生效（MIT，2026-10-05）。**

## 必须完成（本机）

- [x] T1 数据模型与六类最小用例
- [x] T2 双 Agent 适配器（deterministic / HTTP / wrapper / replay / command / process）
- [x] T3 执行、证据与确定性评分
- [x] T4 CLI 与报告（含 serve 本地工作台）
- [x] T5 测试与回归（104 项 unittest）
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

## 实机复核记录

- openKylin 3.0 VM（`192.168.141.128:22`）已完成离线闭环、`.deb` 包内 smoke/strict verify、工作台 HTTP 和 Agent 发现；本轮在独立 HOME 中完成 KylinBot/OpenClaw 六案例真实快速对比。
- 最新批次：`~/kmb-agent-validation-20260923/runs/quick-compare-isolated-20260924`；KylinBot `63.89`、OpenClaw `13.89`，两侧 `score_valid=true`，strict 校验通过。Token Center `/v1/models` 返回 200，未再出现 402；结果仍按系统级外部记忆证据解释，`native_memory_events=0`。
- 桌面演示视频仍待录（`docs/demo-script.md`）。
- 项目级 LICENSE 已生效（MIT，2026-10-05 负责人确认）。

## 表述边界（强制）

| 来源 | 可写 | 不可写 |
|------|------|--------|
| `simulated`（reference/flawed） | 流水线可区分正确/错误记忆行为 | 真实模型能力 |
| `process` / `wrapper` | 系统级进程/控制器行为 | 模型原生长期记忆 |
| 真实云 API（native_memory_events=0） | 可观察文本与请求 | 原生记忆能力 |

## 主结论路径（A+B，门禁后）

设计规格：[`docs/native-memory-compare.md`](docs/native-memory-compare.md)。

- [x] **A** openKylin 生态 Agent：KylinBot 已在 openKylin 3.0 VM 通过真实 CLI 最小门禁；状态 `A: ready(agent-memory-observable)`（系统级 wrapper-assisted，`native_memory_events=0`）
- [x] **B 骨架**：`memory_tool` + 甲 KV / 乙 similar + `suites/native/decision-core.yaml` + `source=memory_layer`；冒烟可区分边界维（非正式 ready）
- [x] **B 正式**：接入真实 LLM 工具调用后端 + runbook 门禁（2026-10-04 完成：openKylin 网关 deepseek-v4-flash 经标准 tool-calling 驱动 KV/similar 两套记忆层，`runs/b-track-kv-real-20261004/`（94.44）与 `runs/b-track-similar-real-20261004/`（77.78）均 strict valid，跨轮写/召回/更新/assistant 输出门禁全中；顺带修复空 `tool_calls` 历史 400 的真实 bug）
- [x] **门禁**：KylinBot 最小实验已出现 `source=process` 的 `memory_write`/`memory_recall` 与 assistant 输出；A 轨可写入 Agent 行为结论，但仍不得写成模型原生记忆
- [x] **R0**：wrapper / register / no-memory **保留**，叙事降为 C 轨对照（见 README、native-memory-compare）

组 2 对照（wrapper/HTTP/no-memory/offline）仍用于评分器与边界说明，**不冒充** A/B 主结论。

## 2026-09-27 轮次增量（ZCode）

- PDF-16 真实稳定性：VM 恢复可达后两轮三批重复验收均因 Token 网关 402 余额不足保持 partial（r2 中 KylinBot repeat-01 有效 52.78 分，52 条证据）；失败批次保留在 `runs/official-installed-20260927{,-r2}/`，90/100 基线与 PDF-16=5/15 结论不变。恢复条件：余额 ≥ 数百万 token 后换新目录重跑。
- Hermes 已于 2026-10-04 纳入真实对比：`runs/quick-compare-hermes-20261004/` Hermes 22.22（valid，34 事件）vs KylinBot 47.22（valid，51 事件），双侧 strict valid——四 Agent 矩阵的生态侧补全（KylinAgent 仍安全阻断）。
- 案例覆盖 39→49（新增 6 条英文多语言案例 + 4 条中文对抗案例；敏感/风险案例要求 `sensitive_not_persisted` 抑制证据）；`suites/coverage/manifest.yaml` 已重生成。
- 工作台支持一键选择两个 runnable Agent 并启动对比（阻断项显示原因与修复条件）。
- 原生记忆导出协议已在 VM 真实 brain.db 验证（41 条 `source=process` 快照事件，`runs/native-memory-export-20260927/`）。
- deb 安装/升级/卸载矩阵在 3.0 VM 待执行：被 VM `sudo 需要密码` 阻断，工具脚本已就绪（见 `tasks/zcode-完成项.md` 第 3-C 节）。
- 全量回归 127 项通过。

## 2026-10-04 里程碑：官方自评分 100/100

- **PDF-16 补齐**：openKylin 3.0 VM 真实双 Agent 重复批次 `runs/official-installed-20261004/`（--repeats 2，独立 HOME/清空记忆表）两批双 Agent 全部 `score_valid=true`（KylinBot 63.89/61.11 σ1.97；OpenClaw 22.22/22.22 σ0），strict verify 通过；官方评分重生成 `runs/official-final-20261004/scorecard/` = **100/100**（PDF-16 15/15 pass）。桌面视频仍待录制（脚本/工具就绪）；LICENSE 已生效（MIT）。
- 附加产出：环境指纹工具 `scripts/agent_env_fingerprint.py`（跨日批次环境同一性哈希背书，今日指纹与 10-01 一致）；`--preflight-only` 零消耗预检命令；prompt-caching 实测结论（后端 89% 命中但网关全价扣费，已形成官方改进建议）。
- 执行波动史（429 一次、402 三次）全部保留在分母与归档目录，未用重跑替换失败批。

## 下一步

1. 四 Agent 矩阵：KylinBot/OpenClaw/Hermes 已有真实分数；KylinAgent 已解锁驱动（`scripts/kylinagent_driver.py`，hermes-agent 引擎+memory_recall 证据提取）但批次受 openKylin 网关挂死 bug 阻断（`runs/kylinagent-real-20261005/`，官方修复后重跑即可）
2. LICENSE 与 3–5 分钟桌面视频
