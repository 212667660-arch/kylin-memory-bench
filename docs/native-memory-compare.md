# 原生 / 可观测记忆对比设计（A+B）与证据门禁

> 本文为赛题主结论路径的设计规格。  
> **门禁未通过前，不得对外输出 A/B 正式主结论或「原生记忆已验收」。**  
> 现有 wrapper / register / no-memory / HTTP 能力**保留**，叙事降为 **C 轨对照**（R0）。

---

## 0. R0 口径（强制）

| 保留 | 降级表述 |
|------|----------|
| `type: memory_controller` / `memory_disabled` | 不是赛题主结论 |
| `register-agent` / 工作台三件套 | 配置接入 + C 轨对照工具 |
| `configs/agent-*-memory.yaml`、历史 `runs/` | 系统级「后端 + 外部控制器」证据 |
| offline reference/flawed、无凭据 demo | 流水线与评分器校验 |

**评审问答标准句**：  
包装轨（如 Grok-memory × DeepSeek-memory）总分相同，是因为测的是**同一包装控制器主导的系统级行为**；「不同智能体长期记忆差异」须在 **A/B 轨**（被测方自有记忆事件）讨论。

**禁止**：删除包装/注册能力；用 C 轨结果冒充 A/B 主结论。

---

## 1. 双轨分工

| 轨道 | 对比什么 | 结论可写 | 不可写 |
|------|----------|----------|--------|
| **A** | 两款 openKylin 生态 Agent 的记忆行为（首个对象已选 KylinBot，第二对象待门禁） | 智能体长期记忆**系统级行为**差异 | 模型原生记忆排名 |
| **B** | 同一 LLM + 两种真实记忆实现 | 不同长期记忆**机制**的行为差异 | 两个聊天模型谁记性好 |
| **C** | HTTP / wrapper / no-memory / reference / flawed | 可观测文本、包装系统流、边际价值、评分器区分度 | 用 C 冒充 A/B 主结论 |

对外材料必须 **A+B 并排**，且每侧带状态标签（见 §4）。

---

## 2. 证据门禁（执行时强制）

1. 记忆 `write` / `update` / `suppress` / **拒写**决策来自**被测 Agent 或其记忆模块**，KMB 与适配器不代劳。  
2. 证据由被测方产生；适配器只采集/转译；**禁止**按案例「标准答案」代写 op（reference 对照组除外，且须标明 `simulated` / `reference`）。  
3. 优先 `state_observed: true`；仅模型自述「记住了」而无事件/状态 → **不得**标模型原生记忆。  
4. 仅有黑盒回答 → `native_memory_events=0`，对应维度 miss，**禁止**推测补写。  
5. 被测方自有事件与 wrapper 代执行事件必须可区分（`source` / `evidence_class`）。  
6. **硬信号（A/B 轨）**：正式轨需出现 **被测方自有可观测记忆事件 > 0**（见下方「门禁计数」）且决策非预写，方可进入可观测记忆行为评测叙事。  
   - **`native_memory_events > 0` 不是 A 轨 exporter 的唯一否决项**；`source=process/memory_layer/wrapper` 的记忆事件在 `classify_evidence` 下不计入 `native_memory_events`（后者只认 `model_native_memory`）。  
   - 模型原生记忆作为**额外加分/原生轨**单独记录。

未通过门禁：状态标 `gate-failed`，**禁止**主结论。

---

## 2b. 门禁计数（强制口径）

| 门禁 | 计数对象 | 可用指标（示例） | 不可用 |
|------|----------|------------------|--------|
| **A 轨**：Agent 自有可观测记忆事件 | 被测 Agent/其存储导出的事件 | `source=process`（或等价 Agent 系统级 source）的 `memory_*` 事件计数；或文档标明来自被测存储的事件 | **不要求** `native_memory_events>0` |
| **模型原生记忆**（原生轨） | 模型自身 | `native_memory_events` / `model_native_memory` + `state_observed` | 不能用 process/memory_layer 代写事件冒充 |
| **B 轨**：记忆层自有事件 | `source=memory_layer` 的记忆事件 | 记忆层事件 > 0 且决策非案例预写库 | 不得写成「模型原生记忆」 |

**A 轨主结论**：不同智能体系统级长期记忆**行为**差异。  
**状态标签**：`A: snapshot-only` / `A: exporter-pending` / `A: ready(agent-memory-observable)` / `C: wrapper-only` / `B: skeleton-only` 等。
`native_memory_events>0` 为原生轨加分项，不是 A 轨 ready 的唯一标准。

**计数示例（导出 JSONL / result.json）**：

```text
agent_owned_memory_events =
  count(e.source in {process, memory_layer, wrapper}
        and e.kind in {memory_write, memory_update, memory_recall, memory_suppress}
        and e.data.agent_owned != False)

# A 轨门禁：agent_owned_memory_events > 0 且事件来自被测存储（非 stand-in 代写）
```

---

## 3. A 侧选型标准（首个候选：KylinBot）

KylinBot 已作为首个候选。2026-09-22 在 openKylin 3.0 VM 通过真实 CLI 最小门禁，当前状态为 `A: ready(agent-memory-observable)`；该状态表示 Agent 自有存储事件可观测，不等于模型原生记忆已被证明。

- openKylin 可安装 / 已有包，可脚本化（stdin / CLI / HTTP 任一）。  
- 可无人工逐步聊天跑完案例。  
- 至少一种可审计轨迹：记忆 DB/文件、工具日志或官方 memory API。  
- 仅有最终回答、无记忆侧信道 → **不作为**记忆主结论对象。

未选定的第二个 A 轨对象状态仍为：`A: candidate-pending`。

---

## 4. 状态标签（并排报告必用）

| 标签 | 含义 |
|------|------|
| `A: candidate-pending` | 尚无合格被测 Agent |
| `A: exporter-pending` | 有对象但无可审计记忆导出 |
| `A: snapshot-only` | 可读取被测存储快照，但没有当前用例的驱动与写入时序证据 |
| `A/B: gate-failed` | 门禁硬信号未满足 |
| `A: ready` / `B: ready` | 门禁通过，可进入正式叙事 |
| `C: wrapper-only` | 仅包装/HTTP/离线对照 |

**门禁前不得写 `A: ready` / `B: ready` 或正式主雷达结论。**

---

## 5. 适配器导出规格（command / replay）

### 5.1 应导出（字段级；本轮不强制写代码）

- `case_id`
- `user_message`
- `assistant_text`（可选 tool 调用）
- `memory_write`（key / 值摘要 / 时间）
- `memory_update`（旧 → 新）
- `memory_suppress` 或 `refuse_persist`
- `memory_recall`（查询 / 命中 / miss）
- 动作层：路径 / 参数 / 退出码 / 工件 hash
- `state_observed`、`source`、`evidence_class`
- 失败 / 超时事件

### 5.2 禁止导出

- 按标准答案预生成的 write/update（非 reference 对照）
- 无日志时的启发式「像记住了」
- 把 B 固定脚手架写库标成模型/Agent **原生**记忆

### 5.3 层级 L1–L4

| 层 | 内容 |
|----|------|
| L1 | 事件流水 |
| L2 | 内部决策（save / update / refuse / recall） |
| L3 | 任务行为与工件 |
| L4 | 抗扰（噪声 / 相近实体 / 边界） |

**正式结论应主要来自 L2–L4**，不能只有 L1 人话回答。

---

## 6. 套件防送分规格（正式 A/B）

现有 wrapper 向套件（`suites/core-zh.yaml` 等含 `memory: {op:...}`）**保留**，供 C 轨 / 评分器校验，**不承担** A/B 主结论。

正式 A/B 案例原则：

1. **输入只给人话**（如「记住项目叫 Atlas」「默认输出目录是 X」「目录改成 Y」），**不写** `memory: {op: write,...}` 让包装层执行。  
2. 六维决策点（输入 vs 期望被测方自己做到）：

| 能力 | 人话输入示例 | 期望被测方 |
|------|----------------|------------|
| 长期保持 | 记住 project=Atlas | 自行持久化并在后续可用 |
| 记忆调用 | 创建报表时用我的默认目录 | 自行检索并使用 |
| 动态更新 | 会议室改成 B | 自行覆盖旧值 |
| 相近区分 | 同时记住 owner_main 与 owner_bak | 查询时不串 |
| 边界识别 | 验证码只用一次、别存 | 自行拒写/不持久化 |
| 任务复用 | 按记住的目录写文件 | 动作层使用正确路径 |

3. **区分度门禁**：reference 高、flawed 明显低；no-memory 在保持/调用/复用系统性偏低；真实 A/B 六维不应无说明地完全重合。  
4. 若新增 YAML，建议路径：`suites/native/decision-core.yaml`（规格/人话输入），**不覆盖** wrapper 用途套件。

---

## 7. B 轨机制规格（同一 LLM + 两种记忆）

- **骨架**：同一后端 LLM（可复用现有 HTTP 适配器作对话后端）。  
- **记忆甲**：精确 KV / 字典类存储，策略偏「可写尽写」（边界能力弱或无）。  
- **记忆乙**：相似检索记忆层 + **可拒绝敏感/一次性信息持久化**。  
- **决策**：模型/Agent 根据人话决定是否 save / recall / update / delete；记忆模块执行存取。  
- **禁止**：两侧都「按案例 YAML 直接写库」。  
- **结论句式**：不同长期记忆机制在同一智能体骨架下的行为差异；**不得**写成模型记忆强弱。

若后续实现代码：仅允许 B 的**真实两套记忆实现 + 工具接口 + 事件导出**骨架与测试（决策来自模型调用工具）；结果目录中区分记忆层事件与 runner 事件。

---

## 8. 最小验证实验 Runbook（门禁）

1. 选定一款有文件/DB/工具记忆的对象（无则写明「待选型」，标 `candidate-pending`）。  
2. 仅 **1** 案例：记住 `project=Atlas` → 后续依赖该事实的动作。  
3. **人工核对**真实写入与读取（看存储/日志，不只看回答）。  
4. 转 `kmb_evidence` JSONL，`source` 指向 **Agent/记忆层自身**。  
5. `type: replay`（或 `command`）评分；检查 `native_memory_events` 或 B 侧记忆层自有事件是否 **> 0**。  
6. 通过 → 允许组 1（A 或 B ready 叙事）；不通过 → 标 `gate-failed`，**禁止**主结论。

---

## 9. 并排报告模板

| 字段 | 内容 |
|------|------|
| 轨道 | A / B / C |
| 对象/机制 | 名称或「待选型」 |
| 状态标签 | 见 §4 |
| suite / seed / retries / timeout | 例：`core-zh` / 42 / 1 / 180（A/B 双侧必须相同） |
| overall + 六维 | 来自真实 result.json |
| `native_memory_events` / 包装层事件 | 门禁关键 |
| 可写结论 | 一句，符合轨道分工 |
| 禁止表述 | 一句 |

**引用现有 wrapper 结果时**：状态标 `C: wrapper-only`，**不进**主结论。

统一参数建议（与仓库惯例一致）：

```bash
--seed 42 --retries 1 --timeout 180
```

---

## 10. 与现有仓库的关系（保护清单）

| 保留 | 用途 |
|------|------|
| `kmb/agents.py` 全适配器类型 | C 轨与后续 A/B 接入 |
| `kmb/register.py`、`register-agent`、工作台三件套 | 配置接入 |
| `configs/agent-*-memory.yaml` 等 | 历史 C 轨证据 |
| `runs/**` 历史目录 | 审计，不删 |
| offline demo / reference / flawed | 流水线校验 |

**不修改**：评分协议语义、`verify_run.py`、已有 CLI 子命令集合。

---

## 11. 当前门禁状态（截至本文）

| 轨道 | 状态 | 说明 |
|------|------|------|
| A · KylinBot | **`A: ready(agent-memory-observable)`** | 2026-09-22 VM 真实 CLI 门禁通过；`source=process` 的写入、回忆和 assistant 输出均有逐轮证据。系统级 wrapper-assisted，不等于模型原生记忆 |
| A · 其他生态 | `exporter-pending` / `candidate-pending` | OpenClaw/Hermes/kylin-agent 尚无本轮正式导出器 |
| B | **`B: skeleton-only`** | `DecisionTextBackend` 非真实 LLM 工具决策 |
| C | **`C: wrapper-only`** | HTTP/wrapper/no-memory 仅对照 |

### A 轨门禁实验（2026-09-18 取证，2026-09-21 复核）

| 项 | 结果 |
|----|------|
| VM | `E:\openkylin\Ubuntu 64-bit.vmx`，openKylin **3.0 (huanghe)**，`Cisyam@192.168.141.128:22` |
| 记忆库 | `/home/Cisyam/.kylinbot/workspace/memory/brain.db`（只读拷贝至宿主 `_migrate_stage/kylinbot-brain.db`） |
| DB 内容 | 门禁前已有烟测数据保留；门禁新增的 `benchmark_alias` 与两条关联 `user_msg_*` 已在门禁后清理 |
| 驱动与导出 | `configs/agent-kylinbot-command.yaml` + `scripts/kylinbot_command_agent.py`；逐轮调用 `kylin-bot agent --message` 并观察 `brain.db` 差异 |
| 评分 | `runs/kylinbot-gate-20260922/result.json`，overall **100.0**；套件为单案例最小门禁，不替代完整六维套件 |
| Agent 自有记忆事件 | `source=process`：`memory_write`（`benchmark_alias`）、精确 `memory_recall` 命中 Atlas，以及两轮 `assistant_message` |
| `native_memory_events` | **0**（符合协议：process ≠ model_native） |
| 观测模式 | `system_level_wrapper_assisted`；`wrapper_memory_events=4`，可证明 KylinBot Agent 记忆行为，不可证明模型原生长期记忆 |
| 非 stand-in | 事件来自真实 KylinBot **brain.db** 行和 CLI stdout，非 `openkylin_ecosystem_agent.py` |

**表述**：A 轨最小门禁已通过，当前可标记为 **`A: ready(agent-memory-observable)`**。该结论来自 VM 内真实 CLI 会话与 `brain.db` 增量，不把旧快照或 stand-in 事件计入当前案例；正式报告仍须把 `system_level_wrapper_assisted` 与 `native_memory_events=0` 一并展示。

### 与 stand-in / C 轨边界

- `configs/agent-kylinbot-process.yaml` 仍为 **stand-in**，**不是**真实 KylinBot。  
- process 记忆事件 ≠ 模型原生记忆。  
- C 轨 wrapper 结果非赛题主结论。

---

## 计划中

（空）


## 2026-10-04 增补：B 轨真实 LLM 工具调用证据

B 轨两套记忆机制已由**真实模型**（openKylin Token 网关 `deepseek-v4-flash`，标准 OpenAI tool-calling）驱动完成正式轨运行，替代此前"离线规则后端仅模拟"的状态：

| 机制 | 得分 | 有效性 | 关键证据 |
|---|---|---|---|
| KV（甲） | 94.44 | `score_valid=true`，strict valid（79 事件） | 跨轮写 6、召回 3、更新 1、动作 1（文件工件含 SHA-256） |
| similar（乙） | 77.78 | `score_valid=true`，strict valid（80 事件） | 相近实体区分与敏感拒绝路径由真实模型决策触发 |

- 决策真实性：工具调用由模型在 `tool_choice=auto` 下自主发起（`source=model` 的 `model_request/assistant_message`），记忆层执行事件为 `source=memory_layer`，决策非案例预写。
- 边界不变：B 轨证明的是"**真实模型 + 外部记忆层**"协同，`native_memory_events=0`，**不得写成模型原生长期记忆**。
- 顺带修复：`OpenAICompatibleToolBackend` 在模型纯文本回答时向历史写入空 `tool_calls` 数组，被 DashScope 系后端 400 拒绝（`runs/b-track-real-20261004/` 保留失败证据）；已修复并由 `tests.test_memory_tool` 回归锁定。
- 证据：`runs/b-track-kv-real-20261004/`、`runs/b-track-similar-real-20261004/`；配置 `configs/agent-b-memory-{kv,similar}-real.yaml`（密钥仅经环境变量注入）。
