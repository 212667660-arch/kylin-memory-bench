# 真实 Agent 接入信息清单

## 当前盘点结论

当前已确认两款真实模型后端：Grok 4.6（NewAPI OpenAI 兼容端点）与 DeepSeek v4 flash（DeepSeek OpenAI 兼容端点）。两者均在 openKylin 2.0 SP2 VM 通过用户级、权限为 600 的凭据文件完成真实 API 调用、核心/对抗套件和严格证据校验；配置分别为 `configs/agent-grok*.yaml` 与 `configs/agent-deepseek*.yaml`。历史探测记录和早期豆包候选仍保留在下文，不能覆盖本节当前状态。

两款 API 都没有导出原生 memory_write/memory_recall 状态。正式结果应分为纯 HTTP 可观察轨道、透明 wrapper 系统级轨道和 no-memory 基线轨道；原生记忆事件均为 0。四轨当前评分和证据路径见 `runs/openkylin-validation-20260906/final-event-report.md`。

用户已提供一组豆包/火山方舟访问标识和一组 DeepSeek API Key。完整密钥没有写入仓库，也没有在本地命令中使用；由于密钥已经在聊天中暴露，建议项目负责人立即轮换 DeepSeek Key。

## 历史待确认项与扩展接入要求

| 字段 | Agent A | Agent B |
|---|---|---|
| 名称与版本 | 待确认 | 待确认 |
| 运行方式 | 待确认（本地命令/API/GUI） | 待确认 |
| 安装包或源码位置 | 待确认 | 待确认 |
| Python/Node/系统依赖 | 待确认 | 待确认 |
| 认证方式 | 待确认；只提供环境变量名 | 待确认；只提供环境变量名 |
| 对话证据 | 待确认 | 待确认 |
| 记忆写入/读取证据 | 待确认 | 待确认 |
| 工具调用与动作参数 | 待确认 | 待确认 |
| 文件产物或任务结果 | 待确认 | 待确认 |
| 脱敏限制 | 待确认 | 待确认 |

### 当前建议配置

已增加 `configs/agent-doubao.yaml` 和 `configs/agent-deepseek.yaml`。它们使用 `type: http`，从 `DOUBAO_API_KEY`/`DEEPSEEK_API_KEY` 环境变量读取认证；豆包模型从 `DOUBAO_MODEL` 读取，DeepSeek 已固定为本账号验证通过的模型。运行前仍需确认：

- 豆包访问标识对应的可用 `ep-...` Endpoint ID，以及对应地域 Base URL；
- DeepSeek `deepseek-v4-flash` 已在本账号完成 API 烟雾测试和核心套件真实运行；
- 两个 Agent 是否实际提供记忆读写/抑制事件，或需增加外部 wrapper 导出 `kmb_evidence`；
- 是否允许将云 API 作为赛事真实 Agent，及其网络、额度和数据脱敏限制。

### 已完成的真实 API 运行

DeepSeek 使用 `https://api.deepseek.com/chat/completions` 和 `deepseek-v4-flash` 完成了 `suites/core-zh.yaml` 六个案例的真实运行，产物位于 `runs/real-deepseek-config/`（另有首次烟雾运行于 `runs/real-deepseek/`）。配置级运行结果：总分 `33.33`，证据事件 `28` 条，六维为 retention 50、memory_recall 0、dynamic_update 0、similar_distinction 50、boundary 100、task_reuse 0；结果已通过严格结构校验。该运行只得到聊天响应，没有 `memory_*` 或 `action` 事件，因此评分如实反映“没有可观察长期记忆/工具证据”，不能视为完整长期记忆 Agent 已验收。

2026-09-08 在同一 openKylin VM 使用 `configs/agent-deepseek-no-memory.yaml`、seed `42`、重试 `1`、超时 `180s` 对核心六案例完成 5 个独立重复批次。每批 6 cases、70 events，CLI 和严格证据校验均为退出码 `0`；Overall 均值 `37.224`、样本标准差 `3.7253`、范围 `30.56-38.89`，`native_memory_events=0`。详细 JSON/Markdown/HTML/SVG 汇总见 `runs/openkylin-validation-20260908/deepseek-no-memory-repeats/` 和 `runs/openkylin-validation-20260908/stability/`。该统计说明执行链路可重复完成，但行为分数并非完全一致。

豆包凭据已通过 `/api/v3/models` 鉴权探测，但使用模型目录中的模型名调用均返回 `404 ModelNotOpen` 或 `InvalidEndpointOrModel.NotFound`；当前需要在 Ark 控制台开通模型，或提供该账号的 `ep-...` Endpoint ID。未生成豆包运行结果，也未将其宣称为通过。

### Grok / DeepSeek 双 Agent 真实对比

使用修订后的 `suites/core-zh.yaml`、seed `42`、重试 `1`、每案例超时 `180` 秒完成：

| Agent | 总分 | retention | recall | update | similar | boundary | reuse | 证据事件 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Grok 4.6 (`grok-api`) | 30.56 | 50.00 | 0.00 | 33.33 | 50.00 | 50.00 | 0.00 | 28 |
| DeepSeek v4 flash (`deepseek-api`) | 38.89 | 50.00 | 0.00 | 33.33 | 50.00 | 100.00 | 0.00 | 28 |

完整产物位于 `runs/real-compare-v2/`；旧版不可推断输入的审计记录保留在 `runs/real-compare/`。每个 Agent 的 `result.json`、`evidence.jsonl`、Markdown/HTML 报告均已生成并通过 `scripts/verify_run.py --strict`。两者当前只输出文本，没有结构化记忆或工具事件；分数是基于真实文本证据和超时/失败记录的可解释结果，不代表已具备完整长期记忆系统。

### 透明包装层双 Agent 运行

为解除“模型 API 没有记忆工具”的工程阻塞，已使用同一外部控制器包装 Grok 4.6 和 DeepSeek v4 flash，产物位于 `runs/controller-compare-v3/`。两边各 6 个案例、70 条事件，包含 28 条 `source=wrapper`（记忆状态和动作）与 42 条 `source=model`（请求、响应和模型回答）事件：

| Agent | 总分 | retention | recall | update | similar | boundary | reuse |
|---|---:|---:|---:|---:|---:|---:|---:|
| Grok 4.6 + controller | 86.11 | 100.00 | 100.00 | 66.67 | 100.00 | 50.00 | 100.00 |
| DeepSeek v4 flash + controller | 94.44 | 100.00 | 100.00 | 66.67 | 100.00 | 100.00 | 100.00 |

结果已通过严格校验。该分数表示“模型后端 + 透明包装层”的完整工作流；`memory_*` 与 `action` 事件明确来自 wrapper，不能宣称为模型原生长期记忆。当前 EvidenceEvent 还会写入 `source` 与 `evidence_class`：模型回答是未证实自述，模型发出的 tool call 是未证实请求，只有返回实际状态/执行结果并显式标记时才可称为原生事件。

## 已准备的接入路径

1. HTTP 适配器：配置 type: http，调用 OpenAI 兼容的 `/chat/completions` 端点。
2. 命令适配器：配置 type: command，进程从 stdin 接收案例 JSON，stdout 输出 JSONL 事件。
3. Replay 适配器：真实 Agent 先导出 JSONL，再使用 type: replay 重放和评分。
4. 三种路径都使用同一 EvidenceEvent、同一套件和同一评分器；未提供真实证据时，运行结果只能作为失败或缺失证据，不能补写。

候选信息齐全后，复制 configs/agent-external-template.yaml 为两个配置，填入真实命令、版本、环境变量白名单和证据导出方式，再运行 scripts/run_acceptance.sh。

正式验收脚本接受 `type: http`、`command`、`replay`、`memory_controller` 与 `memory_disabled`，会拒绝 deterministic 演示基线。wrapper 和 no-memory 配置会输出明确提示，避免被误用为模型原生记忆结论。

本轮已验证：向 `scripts/run_acceptance.sh` 传入 `configs/agent-reference.yaml` 和 `configs/agent-flawed.yaml` 会在执行前拒绝 `type: deterministic`，退出码为 2；未生成正式验收结果。

## 2026-09-08 发布状态

- Grok 4.6 与 DeepSeek v4 flash 在 openKylin 2.0 SP2 VM 的中文核心/对抗、英文核心/对抗套件均有真实 wrapper 运行；权威结果目录为 `runs/openkylin-validation-20260908/adversarial-expanded-compare/`、`core-en-compare-rerun2/` 和 `adversarial-en-compare-rerun2/`。英文对抗首次 Grok HTTP 503 失败批次保留在 `adversarial-en-compare-rerun/`，不能当作成功结果。
- Grok no-memory 与 DeepSeek no-memory 均已完成 5 个核心六案例重复批次；双 Agent 汇总见 `runs/openkylin-validation-20260908/stability/dual-agent-stability.json`、`.md`、`.html`。统计为描述性稳定性证据，不能宣称绝对一致或模型原生记忆。
- 所有真实轨道的 `native_memory_events=0`；`source=wrapper` 只表示外部控制器事件，报告结论必须使用“模型后端 + 外部控制器的系统级长期记忆行为评测”。
