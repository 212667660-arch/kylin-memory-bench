# 外部 Agent 证据协议

## 0.2.2 回答检查范围

`answer_contains` 默认检查案例最后一个声明回合的 assistant 事件；普通 `answer_not_contains` 同样检查最后回合。boundary 类别的禁止回答规则默认检查全部回合，以保留敏感信息全程禁止泄露的约束。最后回合没有回答时，不能使用之前的确认句补位；无 turns 的旧证据案例以最后一个观测到的用户/回答回合为准。

需要不同语义时，在该检查项中显式设置 `answer_scope: all` 或 `answer_scope: last`；也可使用正整数 `step: 2` 指定第 2 回合。`step` 与 `answer_scope` 不能同时设置，step 不能超过已声明的回合数。结果的 `evidence_refs` 只引用该检查实际选中的回答。

CLI JSON/JSONL 应在明确的 assistant 文本字段或 payload 中提供回答；工具结果、日志和 meta 字段不视为回答。OpenClaw 输出缺少 assistant payload 时，运行应标记为不可观测而非有效分数。成功 stdout 完整解析，失败诊断仍限制尾部长度。

真实 Agent 可以不暴露内部数据库，只需导出 UTF-8 JSONL。每行对应一个运行事件；当前协议同时要求来源和可观测性分类，以防把包装层操作或模型自述误认为模型原生记忆：

```json
{
  "case_id": "retention-001",
  "kind": "memory_recall",
  "data": {"key": "project", "value": "Atlas", "hit": true},
  "step": 2,
  "timestamp": "2026-01-01T00:00:01+00:00",
  "source": "wrapper",
  "evidence_class": "wrapper_operation"
}
```

## openKylin 生态 Agent（command / replay）

KylinBot、OpenClaw 等的包装器职责、字段清单、门禁与配置骨架见 [`docs/ecosystem-agent-export.md`](ecosystem-agent-export.md)。要点：

- 包装器**只转译**被测方自有日志/DB/工具事件，**禁止**按套件答案代写 `memory_*`。
- Token Center HTTP 模板见 [`docs/openkylin-token-center.md`](openkylin-token-center.md)（无证据时仅连通）。
- 未过「被测方自有记忆事件 > 0」门禁前，不得写原生/可观测记忆主结论。

## 生命周期与证据链扩展（schema v2）

`EvidenceEvent` 可选地携带以下审计字段；`kmb run` 会为缺失字段补齐事件 ID、关联 ID和父事件关系，旧 JSONL 仍可读取：

- `event_id`、`parent_event_id`、`correlation_id`：将原始事实、状态转换、模型请求/响应、包装层操作和动作结果串成一条链。
- `fact_id`、`fact_version`、`scope`：标识事实实体、版本和用户/项目作用域。
- `artifact_path`、`artifact_sha256`：只引用受控沙箱内的生成物；评分器不会把模型声称的路径当成实际文件。
- `trust_level`：`unverified`、`observed`、`verified` 或 `derived`。`verified` 仅用于有文件/退出码等确定性结果的事件。

案例可以为事实声明 `persistence`、`sensitivity`、`scope`、`version`、`expires_at`/`ttl_steps` 和 `provenance`。包装层按以下顺序生成可审计状态转换：`write`、`retain`（命中 recall）、`revise`、`restart-boundary`、`reuse`、`expire`/`suppress`。`restart-boundary` 目前只重建包装层内存并明确 `system_restart=false`，不能解释为 openKylin 或操作系统真实重启。

## 变形组

案例的 `metamorphic` 字段可把基准和变体归入同一个 `group_id`，声明唯一受控变量、必须变化的结果（例如 `/data/a` 到 `/data/b` 的实际动作路径）和不变量（例如无关措辞改变后 recall 检查状态相同）。报告会输出组级 `passed`、违反的不变量和关联证据引用，而不是只列单案例分数。

## 真实行动证据

包装层的 `action` 只把案例中的路径作为逻辑参数，实际文件始终写入 `action_root/<agent>/<case>/` 专用沙箱。随后必须出现 `tool_result`（含 `exit_code`）和 `file_artifact`（含存在性、内容摘要和 SHA256）；缺少实际工件、退出码或权限拒绝证据时，`action_path`/`reuse` 不得通过。合成敏感 token 会在模型上下文中脱敏，安全案例不使用真实凭据。

必填字段：

- `case_id`：对应 YAML 用例 ID。
- `kind`：`user_message`、`assistant_message`、`memory_write`、`memory_update`、`memory_suppress`、`memory_recall`、`action`、`tool_result`、`file_artifact`、`model_request`、`model_response` 或 `error`。
- `data`：事件载荷。记忆事件使用 `key`、`value`、`persist`、`hit`；动作使用 `tool`、`path`、`source_key`。
- `step`：用例内单调递增的交互轮次。

`timestamp` 用于审计，可选但推荐提供。敏感原文应在导出前脱敏；评分器不会从网络抓取或补写证据。

- `source` 可取 `runner`、`model`、`wrapper`、`provider_evidence`、`simulated` 或 `unknown`。旧 JSONL 缺失时兼容读取为 `unknown`。
- `evidence_class` 归类为 `model_native_memory`、`model_native_tool`、`model_memory_request_unverified`、`model_tool_request_unverified`、`wrapper_operation`、`model_claim_unverified`、`provider_claim_unverified`、`runner_observation`、`runtime_error` 等。
- `assistant_message` 默认属于 `model_claim_unverified`：模型说“我记住了”不是记忆状态证据。只有模型实际导出的原生工具/事件才可归为 `model_native_memory`。
- API 的 `tool_calls` 默认只归为未证实工具/记忆请求；必须有实际状态返回或工具结果，并以 `state_observed: true` 或 `execution_observed: true` 标记，才可声明为原生执行证据。
- `source=wrapper` 的记忆和动作证明的是“模型后端 + 外部包装层”的系统级行为；报告不得写成模型原生长期记忆能力。
- `source=unknown` 或 `provider_evidence` 不得升级为原生能力；内部数据库未导出的状态应在结果中标记为不可观测。
- `evidence_class=no_memory_baseline` 仅用于 `source=runner` 的外部记忆关闭基线事件。它应带有 `memory_mode: no_memory_baseline`，并明确记录禁用写入、recall miss 或动作阻断原因；模型请求/响应仍保留 `source=model`。该模式仍执行全套评分，不能通过跳过案例获得分数。
- `action_tool`、`action_path` 和状态机中的 `reuse` 仅接受未被阻断且有执行证据的动作。模型普通 `tool_calls` 属于未证实请求，不能被计作动作成功；模型原生动作需带 `execution_observed: true`。

历史运行结果可使用 `python scripts/enrich_run_provenance.py SOURCE_RUN --out DEST_RUN` 生成带来源和观测限制的新副本；该命令不会修改 `SOURCE_RUN`，也不会重新调用模型。

## Replay 适配器

`configs/agent-replay-example.yaml` 展示了 `ReplayAgent` 配置：

```yaml
name: external-replay
type: replay
evidence: examples/external-evidence.jsonl
```

运行时，适配器只读取与当前 `case_id` 匹配的行。真实 Agent 接入验收要求：同一案例能导出记忆变化、调用轨迹、动作参数和最终输出，且文件可被 `kmb run` 重放评分。

## 命令适配器

`type: command` 用于尚未内置 SDK 的真实 Agent。Benchmark 启动配置中的命令不经过 shell 拼接；案例 JSON 通过 stdin 传入，规范事件从 stdout 逐行输出。非零退出、超时、非法 JSON 或缺失必填字段都会被 runner 记录为运行失败。

认证信息不得写入 YAML。通过 `env_allowlist` 指定允许传入子进程的环境变量名，实际值只从运行环境读取并不会写入报告。

## OpenAI 兼容 HTTP API

`type: http`（别名 `openai`、`openai_compatible`）适用于豆包/火山方舟、DeepSeek 等提供
`POST /chat/completions` 的接口。适配器会发送统一的案例用户轮次，并记录 API 返回的
`assistant_message`；响应中的 `tool_calls` 会映射为 `action` 或记忆事件。

普通聊天响应**不会自动产生记忆状态证据**。要通过长期记忆检查，真实 Agent 或其包装层必须在响应顶层或 message 中返回 `kmb_evidence` 数组，数组元素遵循本协议并包含 `case_id`。适配器不会根据文本臆测 `memory_write`、`memory_recall` 或持久化状态。

配置示例（密钥只从环境变量读取）：

```yaml
name: deepseek-api
type: http
base_url: https://api.deepseek.com
endpoint: /chat/completions
model: deepseek-v4-flash
api_key_env: DEEPSEEK_API_KEY
timeout_seconds: 60
request_options: {temperature: 0}
```

运行前设置 `DEEPSEEK_API_KEY`，再使用：

```bash
python -m kmb.cli compare --agents configs/agent-grok.yaml configs/agent-deepseek.yaml \
  --suite suites/core-zh.yaml --out runs/real-agents --retries 1 --seed 42 --timeout 180
```

豆包配置见 `configs/agent-doubao.yaml`。火山方舟的 `model` 通常是账号下的 Endpoint ID，必须由项目负责人确认；不能把聊天页面展示的名称当作可调用 ID。

## Grok / NewAPI 网关

`configs/agent-grok.yaml` 使用 `https://api.wapq.cn/v1` 的 OpenAI 兼容接口，默认模型为 `grok-4.6`；网关模型列表已实际返回 `grok-4.5` 和 `grok-4.6`，可直接修改 `model` 切换版本。认证信息只从 `GROK_API_KEY` 环境变量读取。该配置仅证明模型 API 可调用；若响应没有 `kmb_evidence`、记忆事件或工具事件，评分会如实记录证据缺失。

## 外部记忆控制器

`type: memory_controller` 用于模型本身没有记忆工具的情况。控制器使用案例声明的状态转移，在项目目录内维护隔离记忆，并把查询上下文注入同一模型请求；`memory_*` 和 `action` 事件标记 `source=wrapper`，模型回答、模型原生工具调用、请求/响应元数据标记 `source=model`。动作结果只写入 `action_root` 指定的项目内沙箱，不使用案例中的 `/tmp` 路径直接写系统目录。

这是一种“外部包装层 Agent”评测：分数表示模型后端与包装层组成的可复现 Agent 工作流，不得解释为 Grok 或 DeepSeek 原生具备长期记忆。动作沙箱会按 Agent 名称和案例隔离，路径为 `action_root/<agent>/<case>/action-result.txt`。若需要评测原生能力，应使用 `type: http` 或 `type: command` 并提供 Agent 自身导出的记忆事件。

配置示例：

```yaml
name: grok-memory-controller
type: memory_controller
base_url: https://api.wapq.cn/v1
model: grok-4.6
api_key_env: GROK_API_KEY
api_timeout_seconds: 180
action_root: ../runs/controller-actions
```


## 2026-10-04 增补：B 轨真实调用的来源标记

B 轨（`type: memory_tool`）现已支持真实 LLM 工具调用后端（配置 `backend:` 块，密钥仅经环境变量）。来源标记规则不变且已在真实批次中验证：

- 模型决策过程：`source=model`（`model_request`、`assistant_message`、`model_response`）
- 记忆层执行结果：`source=memory_layer`（`memory_write/update/recall/suppress`、文件工件）
- 两类事件在证据链中并存即可证明"真实模型决策 + 本地记忆层执行"，仍属系统级观测；`native_memory_events=0` 不变。
