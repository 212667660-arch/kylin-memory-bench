# openKylin 生态 Agent 证据导出规格（command / replay）

> 调研：`research/openkylin-agent-ecosystem/REPORT.md`（2026-09-18）  
> 协议：`docs/evidence-protocol.md`  
> 本文件为**接入设计规格**；不要求本机已安装 KylinBot/OpenClaw，**不**伪造评测结果。

## 1. 接入级别对照

| 对象 | openKylin 口径 | KMB 状态标签 | 备注 |
|------|----------------|--------------|------|
| **KylinBot** | **官方明确**：3.0 原生智能体；技能 `~/.kylinbot/workspace/skills/` | `A: ready(agent-memory-observable)` | 2026-09-22 已在 VM 通过真实 `kylin-bot agent` CLI 最小门禁；证据为 Agent 自有 `brain.db` 增量与 stdout，仍不等于模型原生记忆 |
| **OpenClaw** | 官方新闻「3.0 可完整运行」+ **独立 MIT 开源**（社区本体） | `exporter-pending` | 非 openKylin 官方开发；Linux `install.sh` |
| WorkBuddy / Raccoon / AutoClaw | 官方商店适配 | 默认**不**作记忆主被测 | GUI 无审计导出则不能进评分主结论 |
| LangChain 等六框架 | **仅 Linux/Python 可运行** | 无官方适配声明 | 禁止写成 openKylin 官方支持 |
| `agent-kylinbot-process.yaml` | 本机 **stand-in** | 非真实 Bot | **保留**，实机改 command 即可 |

## 2. `type: command` 包装器职责（强制）

1. **输入**：stdin 一行 `BenchmarkCase` JSON（与 `CommandAgent` 一致）。  
2. **输出**：stdout 按行 `kmb_evidence` JSONL；非法 JSON / 非零退出 / 超时由 runner 记失败。  
3. **只转译**被测 Agent **自身**日志 / DB / 工具事件。  
4. **禁止**按套件「标准答案」代写 `memory_write/update/suppress`（reference 对照除外，须标 `simulated`）。  
5. **`env_allowlist`**：仅密钥/模型等**变量名**；YAML **不**写密钥值。  
6. **`source`**：Agent 自有记忆/工具与 wrapper 代执行必须可区分；不得冒充 `model_native_memory`，除非协议要求（如 `state_observed`）。

## 3. 导出事件字段清单

与 `SUPPORTED_EVENT_KINDS` / `docs/evidence-protocol.md` 对齐。

| 类别 | 事件 | 必选字段 |
|------|------|----------|
| 对话 | `user_message` | `case_id`, `data.text`, `source`, 时间戳（若协议要求） |
| 对话 | `assistant_message` | 同上（可选 tool 文本） |
| 记忆 | `memory_write` | `key`, `value`（可摘要）, `persist`, `source`, `state_observed`（可核验才 true） |
| 记忆 | `memory_update` | `key`, `old_value`, `value` |
| 记忆 | `memory_recall` | `key`, `hit`, `value` 或 miss 标记 |
| 记忆 | `memory_suppress` / 拒写 | `key`, `refused_reason`, `persist:false` |
| 动作 | `action` / `tool_result` | `tool`, `path`/参数, 退出码, 工件 hash（L3 检查时） |
| 元数据 | — | `evidence_class`, `source`（如 Agent 自有 vs wrapper） |
| 失败 | `error` 或运行失败 | timeout / crash / missing evidence **如实**记录，禁止补写 |

**L1–L4**：L1 事件 → L2 决策 → L3 行为 → L4 抗扰；正式结论应主要来自 L2–L4（见 `docs/native-memory-compare.md`）。

## 4. 最小验收门禁

1. 单案例：人话「记住 project=Atlas」→ 后续 recall / 依赖动作。  
2. 人工核对被测方**真实**写入/读取（存储或日志）。  
3. 导出 JSONL 中 **被测方自有** 记忆事件 **> 0**（或文档标明 unobservable）。  
4. 命令：

```bash
python -m kmb.cli run --agent configs/agent-<name>-command.yaml \
  --suite suites/native/decision-core.yaml \
  --out runs/<name>-gate --seed 42 --retries 1 --timeout 180
python scripts/verify_run.py runs/<name>-gate --strict
```

5. **未过门禁**：标 `gate-failed` / `snapshot-only` / `exporter-pending`，**不得**写「原生/可观测记忆主结论」。已过门禁的 Agent 仍须标注观测模式（例如 `system_level_wrapper_assisted`）并区分 `native_memory_events`。

## 5. 配置骨架

| 文件 | 用途 |
|------|------|
| `configs/agent-kylinbot-command.yaml` | KylinBot 真实 CLI 驱动（已通过最小门禁） |
| `configs/agent-kylinbot-command.yaml.example` | KylinBot 只读快照 exporter 示例；不代表当前正式驱动配置 |
| `configs/agent-openclaw-command.yaml.example` | OpenClaw exporter 占位 |
| `configs/agent-kylinbot-process.yaml` + `scripts/openkylin_ecosystem_agent.py` | **本机 stand-in，保留** |

实机：只改 `command` 指向真实 exporter，**协议不变**。YAML 示例：

```yaml
type: command
command: ["python3", "scripts/export_kylinbot_evidence.py"]
timeout_seconds: 120
env_allowlist: ["OPENKYLIN_TOKEN_API_KEY"]
```

`replay`：在导出 JSONL 后用 `type: replay` + `evidence:` 路径离线评分（仍须门禁核验自有事件）。

## 6. openkylin-skills 与 MCP

| 项 | 事实 |
|----|------|
| 仓库 | `https://gitee.com/openkylin/openkylin-skills`（官方 org + **社区维护**） |
| 安装 | `curl -fsSL https://gitee.com/openkylin/openkylin-skills/raw/master/install.sh \| bash -s -- --agent openclaw` |
| KylinBot 技能路径 | `~/.kylinbot/workspace/skills/` |
| OpenClaw 技能路径 | `~/.openclaw/skills/` |
| MCP | **skills 仓 README 未文档化 MCP Server**；3.0「智能体经 MCP 调桌面」与 OpenClaw `mcp.servers` **分属不同层** |
| **禁止**表述 | 「openkylin-skills = 官方 MCP 注册表」；六框架 = openKylin 官方适配 |

## 7. 与 C 轨 / R0

- Token Center `type: http` 见 `docs/openkylin-token-center.md`（仅连通设计）。  
- wrapper / register / no-memory **保留**，叙事为 C 轨对照。  
- KylinBot command 驱动已通过最小门禁并可进入 A 轨 ready；扩展到完整套件前仍需保留逐轮证据，并禁止把 `source=process` 写成模型原生记忆。
