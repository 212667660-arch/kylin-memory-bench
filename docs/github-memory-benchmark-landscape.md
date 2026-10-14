# “忆衡”长期记忆 Benchmark 技术景观研究

> 研究对象：面向 openKylin 的智能体长期记忆自动化评测 Benchmark“忆衡”。
> 本文依据官方任务书、项目上下文包，以及截至 2026-09-02 对指定 GitHub 仓库 README、源码、许可证和可见运行说明的核查结果编写。
> “未发现”表示在已检查范围内没有找到；“未验证”表示不能从静态材料推出运行结论。许可证判断不是法律意见。

## 1. 研究范围与证据规则

### 1.1 官方最终目标

官方任务书（本地提取文本：`.tmp-github-research/official-taskbook.txt`，原 PDF：`<user-home>\Downloads\ai_open_kylin_open_kylin_benchmark_XaCQyZepC8.pdf`）要求：

| 硬要求 | 对“忆衡”的约束 |
|---|---|
| 评测对象 | 必须是通用智能体长期记忆自动化评测 Benchmark，不是聊天机器人、RAG 产品或单一模型脚本。 |
| 证据 | 统一组织对话、记忆记录、行动轨迹、文件及其他运行产物，评分必须能回指真实证据。 |
| 能力 | 覆盖长期保持、记忆调用、动态更新、相近区分、边界识别、任务复用六类能力。 |
| 比较 | 至少接入两款智能体，使用统一输入、评分和可比证据。 |
| 工具化 | 在 openKylin 上以 CLI 或 GUI 封装，官方建议 `.deb`。 |
| 可复现 | 自动、低人工、稳定、可批量追踪；需提供样例数据、结果、代码和运行说明。 |
| 演示 | 需要真实 openKylin 桌面环境下至少两款智能体的完整录屏和多维对比结果。 |

官方评审权重为：通用性 15%、数据设计 25%、自动评分 25%、稳定性与复现 15%、指标完整性 10%、创新性与工程落地 10%。

### 1.2 研究证据等级

- **代码/协议事实**：来自仓库当前可见的 README、源码、配置、数据卡或许可证文本。
- **运行事实**：只有仓库明确提供运行日志/结果，或本项目 `runs/` 中实际生成的文件，才称为运行证据。
- **未验证事实**：仅凭依赖声明、目标平台文字或理论可移植性，不能推出 openKylin 兼容。
- **许可证**：以仓库 LICENSE/NOTICE 文本为准；GitHub API 的 `NOASSERTION` 不能当作许可证结论。代码、数据、Prompt、论文图表和第三方依赖分别审查。

### 1.3 当前“忆衡”基线

当前项目已有 `kmb/agents.py`、`models.py`、`runner.py`、`scoring.py`、`cli.py`、`report.py`，支持 `AgentAdapter`、HTTP/命令/回放/透明记忆控制器、JSONL `EvidenceEvent`、`source=model|wrapper`、状态机 `write/retain/revise/suppress/reuse`，以及 `run`、`compare`、`validate`、`list-cases`、JSON/Markdown/SVG/HTML 输出。

已存在的真实 API 运行记录：

- 原生 HTTP 文本响应：`runs/real-compare-v2/`，Grok 4.6 总分 30.56、DeepSeek v4 flash 总分 38.89；两者均没有原生 `memory_*` 或 `action` 事件，评分如实反映证据缺失。
- 透明外部控制器：`runs/controller-compare-v3/`，Grok 4.6 + controller 86.11、DeepSeek v4 flash + controller 94.44；`memory_*`/`action` 事件标记为 `source=wrapper`，不能解释为模型原生记忆能力。

## 2. 七个项目逐项分析

### 2.1 HUST-AI-HYZ/MemoryAgentBench

**定位与核心能力**

- 面向具备记忆能力的 LLM Agent，采用“inject once, query multiple times”。
- 主要任务是 Accurate Retrieval、Test-Time Learning、Long-Range Understanding、Conflict Resolution，并包含 EventQA、FactConsolidation 等任务。

**数据集格式**

- 主要从 Hugging Face `ai-hyz/MemoryAgentBench` 加载，split 包括 `Accurate_Retrieval`、`Test_Time_Learning`、`Long_Range_Understanding`、`Conflict_Resolution`。
- 样本可见字段包括 `context`、`questions`、`answers`、`metadata.source`、`metadata.question_ids`、`metadata.question_types`、`question_dates`、`previous_events`、`qa_pair_ids`；也支持本地 JSON 问答与文本上下文。

**Agent 接入方式**

- 通过 `AgentWrapper` 和 `agent_name` 选择长上下文、Mem0、Cognee、LeTTA、RAG 等实现。
- `send_message(message, memorizing, query_id, context_id)` 返回输出、输入/输出长度、记忆构建耗时和查询耗时等字段。

**证据采集方式**

- 保存回答、token/字符长度、时间，部分 RAG 路径保存 `retrieval_context`。
- 未发现统一的 `memory_write`、`memory_update`、`memory_recall`、`memory_suppress`、`action` 事件模型或证据图，因此无法从其默认输出证明内部记忆状态。

**评分指标与实现**

- `exact_match`、`substring_exact_match`、token-level F1、ROUGE；EventQA 有元素召回比例，RULER memory merging 有 recall。
- 可选 LongMemEval/InfBench 的 LLM judge；主流程仍以最终回答为中心，而非完整状态机。

**CLI、批量与报告**

- `main.py` 使用 argparse，支持 Agent/数据集配置、强制重跑和查询数量限制；另有 shell 运行脚本和 JSON 结果。
- 未发现成熟的 HTML 跨 Agent 报告或证据链浏览器。

**真实运行证据与 openKylin**

- 能记录真实回答、耗时、token 和部分检索上下文；未证明能导出工具调用、动作参数或内部记忆变化。
- README 要求 Python 3.10.16、PyTorch/CUDA 及多个重量级依赖；未发现 openKylin 版本、实机日志或专门适配，不能据此推出 openKylin 兼容。

**可借鉴与复用风险**

- 可借鉴能力分类、上下文/问题/答案/元数据组织、inject-once/query-many 流程、数据集配置和基础回答指标。
- 仓库 `LICENSE` 已确认为 MIT，代码复用需保留版权和许可证；其 Hugging Face 数据及致谢的外部数据集需单独核查，不应直接复制数据、Prompt 或结果。

### 2.2 GoodAI/goodai-ltm-benchmark

**定位与核心能力**

- 长对话、超长上下文、动态维护和信息整合的长期记忆 Benchmark，支持多个 LLM、LTM Agent、MemGPT 和人工模型。

**数据集格式**

- 核心抽象是 `TestExample`，`.def.json` 保存 `script`、`is_question`、`expected_responses`、`waits`、`can_be_interleaved`、`uses_callback`、`is_temporal`、`example_id`。
- YAML benchmark 配置指定 `run_name`、`memory_span`、`dataset_examples`、数据集名和交错不兼容项；数据集包括 delayed recall、prospective memory、restaurant、shopping、trigger response 等。

**Agent 接入方式**

- `ChatSession` 抽象要求 `reply(message)`、`reset()`、`load()`、`save()`；`reply` 返回字符串，状态由 Agent 自己维护。
- 预置 OpenAI、Anthropic、Gemini、GoodAI LTM、MemGPT、HuggingFace、human、litellm 等接口，并可声明 token 长度、消息上限、成本或本地运行。

**证据采集方式**

- runner 记录消息、回答、时间、任务日志、filler/interleaving、token/字符记忆跨度及 master log；`load/save` 支持断点恢复。
- 未发现通用内部记忆状态、工具调用、文件产物的 EvidenceEvent 协议。

**评分指标与实现**

- 数据集实现 `evaluate_correct`，可选 `evaluate_correct_gpt`；多数问题为 0-1 正确率，部分 callback 可持续评分，并可附 reasoning 文本。
- GPT judge 的确定性和证据范围需要按配置审计，不能替代运行轨迹。

**CLI、批量与报告**

- runner 典型入口为 `python run_benchmark.py -c ... -a ... -m ...`；支持恢复、并发/交错、时间跳转和 token filler。
- `runall_bench.py` 支持批量运行；详细 HTML 报告和 comparative report 可展示多个 Agent 的雷达图及原始指标。

**真实运行证据与 openKylin**

- 能记录真实 `reply`、时间、成本和可持久化 Agent 的运行记录，但仍主要是对话证据。
- Python 3.10+、click/yaml/tiktoken/API 等依赖理论上较易移植；未发现 openKylin 实机或虚拟机验证，不能宣称兼容。

**可借鉴与复用风险**

- 可借鉴极简有状态 Agent 接口、等待/时间模拟、断点恢复、动态 callback、批量调度和 HTML/比较报告。
- 仓库 LICENSE 文本已确认 MIT；README 明确部分 GPT 生成数据不适合商业用途、SallyAnne 当时未授权，TriviaQA/ChapterBreak 等有独立许可。代码许可证不自动覆盖数据。

### 2.3 ProsusAI/MemEval

**定位与核心能力**

- 面向 Agent memory 的公平评测框架，统一 LLM、embedding、judge、token 和成本统计；支持 LoCoMo、LongMemEval 及多个记忆系统。

**数据集格式**

- LoCoMo 对话按 `conversation.session_N` 和 `session_N_date_time` 组织，每轮含 `speaker`、`text`、`dia_id`；QA 含 `question`、`answer`、`category`、`question_id`。
- LongMemEval 使用专用 split/格式，也支持自定义 JSON。

**Agent 接入方式**

- 通过 `SYSTEMS` 注册表接入；系统适配器负责初始化、`ingest(dialogues)` 和 `answer(question)`，框架统一评分。
- `systems/_template.py` 给出自定义系统模板，仓库附带 PropMem、OpenClaw、Full Context、Hindsight、Graphiti、SimpleMem、Mem0、Memory-R1、MemU 等系统。

**证据采集方式**

- 统一结果包括最终预测回答和 token 使用（calls、prompt_tokens、completion_tokens、模型分项）；部分系统另有检索上下文。
- 未发现跨系统通用的写入、更新、抑制、工具或文件证据事件协议。

**评分指标与实现**

- token-level F1；LoCoMo 按 Factual、Temporal、Inferential、Multi-hop、Adversarial 分类汇总。
- LongMemEval 使用 binary judge；LLM judge 可输出 relevant、complete、accurate 三维，以及 overall mean/std、按会话/类别和 token usage。

**CLI、批量与报告**

- `scripts/run_full_benchmark.py` 支持 benchmark/split/systems/样本数/model/skip-judge/output-dir/data-file 等参数，多系统循环和 JSON aggregate summary。
- 有图表脚本；未发现独立 HTML 报告系统。

**真实运行证据与 openKylin**

- 可记录真实系统调用、回答、token 和 judge API 结果，但不能统一证明内部记忆状态。
- `pyproject.toml` 要求 Python >=3.11，完整运行可能要求 Python 3.13，且依赖多个向量库/外部服务；未发现 openKylin 验证。

**可借鉴与复用风险**

- 可借鉴系统注册接口、公平比较所需统一模型/embedding/judge、成本统计、per-category mean/std 和扩展机制。
- 代码 LICENSE 已确认 Apache-2.0，并有 NOTICE；复用代码需保留 LICENSE、NOTICE、版权和修改声明。LoCoMo/LongMemEval 与第三方系统、数据仍需单独审查。

### 2.4 MemTensor/HaluMem

**定位与核心能力**

- 专门评估记忆系统操作级幻觉，而不是通用长期记忆排行榜。
- 将流程拆为 Memory Extraction、Memory Update、Memory Question Answering。

**数据集格式**

- 用户对象包含 `uuid`、`persona_info`、`sessions`；session 含起止时间、轮数、`dialogue`、`memory_points`、`questions`、token 长度。
- memory point 含 `index`、`memory_content`、`memory_type`、`memory_source`、`is_update`、`original_memories`、`importance`、`timestamp`；QA 含 `question`、`answer`、`evidence`、`difficulty`、`question_type`。

**Agent 接入方式**

- 不是通用 Agent SDK；评测脚本分别适配 Mem0、Memobase、MemOS、Supermemory、Zep 等系统。
- 一般流程为 ingest dialogue、提取记忆、检索上下文、询问 LLM、保存结果。

**证据采集方式**

- 保存 extracted memories、retrieved context、系统回答、时间和更新查询结果；部分适配器直接读取外部数据库/API。
- README 明确某些系统（如 Zep）缺少 Get Dialogue Memory API，导致 extraction 指标无法计算；这说明证据可得性本身需要纳入评测。

**评分指标与实现**

- Memory Integrity：recall(all)、recall(valid)、weighted recall。
- Memory Accuracy：target accuracy、weighted accuracy、interference accuracy。
- Extraction F1；Update/QA 按 Correct、Hallucination、Omission、Other 分类；另有 FMR、耗时和 memory type 统计。
- 评分主要通过结构化 JSON 的 LLM judge，并有并发、缓存和无效结果标记。

**CLI、批量与报告**

- Poetry 环境；典型入口为 `python eval_memzero.py` 或 `python evaluation.py --frame memzero --version default`。
- 多系统脚本、ProcessPool 并发、JSONL 中间结果和 JSON 汇总；未发现成熟 HTML/跨 Agent 报告。

**真实运行证据与 openKylin**

- 连接真实 memory service 时可记录提取/检索/更新结果，但依赖服务 API 能力，不能自动得到通用工具、动作、文件事件。
- 未发现 openKylin 适配或验证；依赖 Poetry、数据库和云服务，不能宣称可直接运行。

**可借鉴与复用风险**

- 可借鉴 extraction/update/QA 分解、Correct/Hallucination/Omission 分类、memory source/importance/original 链接、weighted recall/F1、并发缓存。
- `LICENSE.txt` 已确认 CC BY-NC-ND 4.0。该许可限制商业使用和衍生作品，不适合直接复制代码、数据、Prompt、图表或改造后并入赛事项目；只能参考公开思想，复用前必须取得明确授权。

### 2.5 rzhub/GateMem

**定位与核心能力**

- 多主体共享记忆环境下的 memory governance Benchmark，关注 Utility、Access Control、Active Forgetting。
- 覆盖 medical、office、education、household 四个合成领域。

**数据集格式**

- 每个领域有 `episodes.jsonl` 和 `checkpoints.jsonl`。
- episode 含 `episode_id`、`domain`、`entities.principals`、`entities.relationships`、`turns`；turn 含 speaker/principal、text、timestamp 和可选 `memory_ops`。
- checkpoint 含 `checkpoint_id`、`episode_id`、`as_of_turn_id`、`asker`、`query_text`、`query_type`、`attack_type`、`expected_action`、`judge_spec`、`leak_targets`；评分字段不展示给 Agent。

**Agent 接入方式**

- `MemoryAgent` Protocol 要求 `reset(episode)`、`ingest(turn)`、`query(checkpoint)`；`BaseMemoryAgent` 提供 prompt/LLM helper。
- 支持 long_context、rag_naive、rag_policy、a_mem、mem0、remem、example，也支持外部 predictions JSONL，无需集成源码。

**证据采集方式**

- predictions 至少包含 `checkpoint_id`、`action`、`answer`、`answer_structured`、`used_record_ids`；新格式可附 `memory_audit.prompt_context.text`、检索记忆、native/debug 结构。
- 评分分别检查 answer-level、prompt-context 和 end-to-end 泄漏，包括敏感记忆和已删除记忆泄漏。

**评分指标与实现**

- action accuracy、utility accuracy、privacy leakage rate、deletion leakage rate、over-refusal rate；治理指标 `MGS = U * (1-A) * (1-F)`。
- 同时报告 answer/context/e2e 三层泄漏，可选 LLM judge 与规则评分并存。

**CLI、批量与报告**

- `bench/scripts/run_eval.py`、`score_predictions.py` 支持数据目录、agent、provider/model、输出目录、run name、resume、score-only、并发和日志。
- `scripts/sweep.py` 支持批量 sweep；输出 predictions/scores/judge_scores JSONL 和 summary JSON。未见本地 HTML 报告生成器。

**真实运行证据与 openKylin**

- 可记录真实回答、检索上下文、used_record_ids、token/时间，并检查提示上下文泄漏；仍不是统一写入/更新/抑制事件流。
- 代码为 Python/API/embedding 依赖，未发现 openKylin 实机验证，理论可移植不等于已兼容。

**可借鉴与复用风险**

- 可借鉴 checkpoint-at-turn、外部 predictions 接口、隐藏评分字段、prompt-context 泄漏检测、answer/context/e2e 分层、resume/sweep/continue-on-error 和输出约定。
- `LICENSE` 已确认 MIT，代码复用需保留版权/许可证；数据卡、第三方依赖和合成数据的再分发条件仍需分别审查。不能把 GateMem 的三类治理指标直接替代“忆衡”六类能力。

### 2.6 Kylin-Agent-Competition/kylinOS-agent-memory

**定位与核心能力**

- 面向“银河麒麟桌面操作系统 V11 x86_64”的 Agent 多源融合偏好与知识记忆服务，包含 SQLite 真源、Vector 索引、Unix Domain Socket、Python memory service、C++/Qt/QML 客户端及 Hook/Tool/Turn 集成设计。
- 它是记忆系统/OS 集成项目，不是 Benchmark；README 多处标明生产接入 blocked/untested。

**数据与协议格式**

- `MemoryContext` 示例字段包括 `schema_version`、`event_id`、`trace_id`、`user_id`、`session_id`、`turn_id`、时间、`source_reference`、`idempotency_key`、`query_id`、`selected_memory_ids`、`context_version`、token 预算/实际数、敏感/遗忘/冲突排除计数、`injection_status`。
- 设计还提出 ToolExecutionEvent、TurnFinalizedEvent 和配置事件。Gate0 JSON 是设计/验收案例，不是 runtime 证据。

**Agent 接入方式**

- 目标是官方 AI 助手 Hook；当前可见内容主要是候选契约、示例和测试，生产 Hook、MemoryClient 和真实宿主映射仍未完成。

**证据采集方式**

- 强调区分真实 Tool Result 与模型自述，设计了记忆上下文、工具执行和 turn finalized 事件。
- 文档明确很多条目为 BLOCKED/UNTESTED，不能把契约示例当作实际运行证据。

**评分、CLI、批量与报告**

- 没有完整 Benchmark scorer；Gate0 主要描述工具成功/失败/取消/超时、回滚、幂等、授权和模型自述等验收预期。
- 有 `scripts/check_kylin_environment.sh` 和 systemd/packaging 说明，但没有完成的 Benchmark CLI、批量执行或报告系统。

**openKylin 与许可证**

- 目标系统是银河麒麟 V11，不是 openKylin；有 VirtualBox VM 和环境探针说明，但仓库未提供可替代的 openKylin 验证。
- `LICENSE` 已确认为 Copyright 2026 项目团队、All Rights Reserved；未经书面许可不得复制、再发布或商业使用。只能参考架构思路和公开接口意图，不能直接复制代码、协议、案例或文案。

**可借鉴内容**

- Linux/Kylin 环境探针、UDS/SQLite 分层、事件中的 trace/idempotency/敏感过滤/版本字段、真实工具结果与模型自述的分离，以及分层验收记录方式。

### 2.7 openkylin/llm-agent

**定位与核心能力**

- 通用 LLM Agent 应用/框架，支持多轮对话、模型调用、场景、RAG、工具/系统交互以及 HTTP/WebSocket 服务；不是长期记忆 Benchmark。

**数据集与 Agent 接入**

- SQLite 保存 session、record、cache；记录含 session_id、type、content、date。RAG 文件位于用户目录 `~/.llm_agent/rag`，支持 txt/pdf/docx 等。
- `main.py` 启动 WebSocket `localhost:6683` 和 Flask HTTP `localhost:8888`，JSON 消息包含 session_id 等；模型/分发在 `distributor.py` 等模块。

**证据、评分、CLI 与报告**

- 可提供真实会话记录、工具/命令处理和文件路径，但未发现标准 EvidenceEvent、专门记忆写入/更新/调用/抑制轨迹、六类评分器、批量 Benchmark CLI、报告或跨 Agent 比较。
- 运行入口为 `python main.py`，偏服务型应用而非评测工具。

**openKylin 与许可证**

- README 提到 CUDA 11.8、cuDNN、conda、PyTorch、kylin-actuator；requirements 包含 GPU、Chroma、LangChain、Milvus 等较重依赖。未发现具体 openKylin 版本或实机验证，不能宣称兼容。
- `LICENSE` 文件实际为 AGPL-3.0，README 中的“GPL-3.0”描述与许可证不一致，应以 LICENSE 为准。复制或形成网络服务衍生作品前必须处理源码公开、许可证告知和依赖边界；不建议直接并入“忆衡”，可在独立进程/协议边界上作为被测 Agent 候选，仍需法律审查。

## 3. 横向对比

| 项目 | 主要对象 | 数据/协议成熟度 | 运行证据范围 | 评分重点 | CLI/报告 | openKylin 状态 |
|---|---|---|---|---|---|---|
| MemoryAgentBench | 记忆型 LLM Agent | 多任务 JSON/HF | 回答、token、部分检索上下文 | EM/F1/ROUGE/召回 | argparse、JSON | 未验证，依赖重 |
| GoodAI LTM | 长期对话 Agent | `.def.json` + YAML 脚本 | 对话、时间、成本、持久化日志 | 0-1 正确率/GPT judge | 批量、恢复、HTML/比较 | 未验证，理论较易移植 |
| MemEval | 多记忆系统公平评测 | LoCoMo/LongMemEval JSON | 回答、token、部分检索上下文 | F1、分类、LLM judge | 多系统 JSON 汇总 | 未验证，Python 要求较新 |
| HaluMem | 记忆操作幻觉 | 用户/session/memory point/QA JSON | 提取、检索、更新查询、回答 | recall/F1/Correct-Hallucination-Omission | 并发、JSONL/JSON | 未验证，依赖服务 |
| GateMem | 共享记忆治理 | episode/checkpoint JSONL | 回答、prompt context、record IDs、泄漏 | utility/privacy/deletion/MGS | resume、sweep、JSONL | 未验证 |
| kylinOS-agent-memory | 麒麟 OS 记忆服务 | MemoryContext/事件契约 | 设计中的 Tool/Turn/Memory 事件 | 无完整 scorer | 环境探针、systemd | 麒麟 V11 目标，非 openKylin；未完成 |
| openkylin/llm-agent | 通用 Agent 应用 | SQLite 会话/RAG 文件 | 对话、工具/文件路径 | 无 Benchmark 评分 | HTTP/WebSocket | 未验证，依赖重 |
| 忆衡（当前） | 六类长期记忆 Benchmark | YAML 案例 + EvidenceEvent JSONL | 模型请求/响应、wrapper/native、记忆、动作、文件 | 状态机、证据引用、失败类型 | CLI、批量、JSON/MD/SVG/HTML | Windows 预检通过，openKylin 未验证 |

## 4. 技术参考优先级

1. **GateMem**：优先参考 checkpoint、外部 predictions、提示上下文泄漏检查、resume/sweep 和 continue-on-error；其治理指标只作为边界/隐私扩展，不能替代六类能力。
2. **GoodAI LTM Benchmark**：参考最小有状态 Agent 接口、等待/时间调度、断点恢复和 HTML/比较报告。
3. **HaluMem**：参考 extraction/update/QA 操作拆分与遗漏/幻觉分类；仅参考思想，不复制受限内容。
4. **MemEval**：参考系统注册、统一 judge/token 成本、分类汇总和多系统循环。
5. **MemoryAgentBench**：参考多任务能力组织、inject-once/query-many 和数据配置。
6. **kylinOS-agent-memory**：参考 Linux/Kylin 环境探针、事件字段和 OS 集成分层；许可证禁止直接复用。
7. **openkylin/llm-agent**：仅作为可能的被测 Agent/服务形态参考，不作为 Benchmark 核心。

该顺序是工程参考优先级，不是对项目质量或竞赛成绩的判定。

## 5. 合法复用边界与许可证风险

### 5.1 相对清晰的代码复用候选

- MemoryAgentBench：仓库 LICENSE 已确认 MIT；保留版权、许可证和修改说明。
- GoodAI：仓库 LICENSE 已确认 MIT；代码可按 MIT 条件复用，但数据/生成内容另审。
- GateMem：仓库 LICENSE 已确认 MIT；保留版权/许可证，数据卡和第三方依赖另审。
- MemEval：代码 LICENSE 已确认 Apache-2.0；保留 LICENSE、NOTICE、版权和修改声明。

### 5.2 不建议直接复用

- HaluMem：CC BY-NC-ND 4.0，非商业且禁止衍生，代码、数据、Prompt、图表均不直接并入。
- kylinOS-agent-memory：All Rights Reserved，未经书面授权不复制代码、协议、案例或文案。
- openkylin/llm-agent：AGPL-3.0；复制/衍生及网络服务边界会触发开源和告知义务，不建议直接并入。

### 5.3 统一注意事项

- GitHub API `NOASSERTION` 只表示 API 未确认许可证，不是“无许可证”或“可自由使用”。
- 数据集、Prompt、生成文本、论文结果、图标和第三方依赖不能沿用代码许可证推断。
- 赛事发布或商业分发前，应由项目负责人/法务逐项确认许可证、数据再分发和云 API 使用条款。

## 6. “忆衡”如何避免同质化

1. **从回答正确率升级为证据链评测**：每个案例以 JSONL `EvidenceEvent` 保存 `model request/response`、外部包装层记忆操作、模型原生工具调用、工具结果、动作参数、文件产物和时间戳，并保留事件引用。
2. **明确来源边界**：`source=model` 表示模型请求、回答或原生工具事件；`source=wrapper` 表示透明记忆控制器执行的写入/更新/抑制/调用和动作。包装层分数只能称为“模型后端 + 外部控制器”。
3. **保持六类能力完整**：长期保持、记忆调用、动态更新、相近区分、边界识别、任务复用均要有案例、证据、分项分数和失败原因。
4. **采用可审计状态机**：`write / retain / revise / suppress / reuse` 对应遗漏、混淆、旧值残留、错误持久化、错误复用和运行异常；规则评分优先，LLM judge 只能作为可选辅助。
5. **加入 OS 级证据**：适配 openKylin Agent/Tool/Turn 事件，记录文件、命令、权限、超时、取消、回滚和环境元数据，形成区别于普通 QA/RAG 的落地价值。
6. **公平双 Agent**：统一套件、提示模板、随机种子、超时/重试策略和评分器；结果中同时展示后端、包装层、证据完整度和失败类型。

## 7. 建议优先实现的 MVP

1. 稳定并版本化 EvidenceEvent JSONL schema，提供 schema 校验和脱敏规则。
2. 六类能力各保留至少一个可复现案例，增加冲突更新、相似实体、敏感/临时信息、提示注入和任务动作参数。
3. 保持两个真实 Agent adapter：HTTP/OpenAI-compatible、command/replay；没有原生记忆工具时使用透明包装层并显式标注来源。
4. 规则优先评分：状态机、证据引用、失败类型、缺失事件和超时/异常均结构化写入结果。
5. CLI 提供 `run`、`compare`、`validate`、`list-cases`，支持 seed、run-id、timeout、retry、resume、continue-on-error。
6. 输出 JSON、Markdown、SVG/HTML 对比报告，展示六维指标、证据计数、失败统计和跨 Agent 差异。
7. 完成 openKylin 环境探针、离线安装/卸载脚本和干净环境执行清单；最终必须在真实 openKylin 实机或虚拟机完成一次完整 CLI 验证和录屏。

## 8. 未确认事项与研究限制

- 本研究没有替任何仓库运行完整 Benchmark；对仓库“能运行”的判断仅来自可见代码、README 和依赖声明。
- 七个仓库均未提供可替代的 openKylin 实机验证；`kylinOS-agent-memory` 的目标是银河麒麟 V11，不等同于 openKylin。
- “忆衡”当前真实 Grok/DeepSeek 运行已生成证据和分数，但原生 API 仅返回普通文本；记忆事件来自透明 wrapper 时，不能作为模型原生能力结论。
- 豆包 Endpoint ID、正式参评 Agent 名称/版本、云 API 赛事使用政策、openKylin 版本/架构/介质仍待项目负责人确认。
- 许可证判断不是法律意见；所有第三方数据、Prompt、模型和依赖在发布前需单独审计。

## 9. 来源与提交信息

| 项目 | URL | 核查提交/分支 | 许可证核查 |
|---|---|---|---|
| MemoryAgentBench | https://github.com/HUST-AI-HYZ/MemoryAgentBench | `main` / `fe1735d` | 仓库 LICENSE：MIT |
| GoodAI LTM Benchmark | https://github.com/GoodAI/goodai-ltm-benchmark | `main` | 仓库 LICENSE：MIT；GitHub API 为 NOASSERTION |
| MemEval | https://github.com/ProsusAI/MemEval | `main` / `807ae6d` | Apache-2.0 + NOTICE |
| HaluMem | https://github.com/MemTensor/HaluMem | `main` / `eef0666` | CC BY-NC-ND 4.0 |
| GateMem | https://github.com/rzhub/GateMem | `main` / `603f9f4` | MIT |
| kylinOS-agent-memory | https://github.com/Kylin-Agent-Competition/kylinOS-agent-memory | `main` / `188e761` | All Rights Reserved |
| openkylin/llm-agent | https://github.com/openkylin/llm-agent | `develop` / `24578ff` | LICENSE：AGPL-3.0 |

本地研究材料位于 `E:\上海开源软件应用创新大赛\.tmp-github-research`；已有“忆衡”协议、环境和 Agent 文档位于 `docs/evidence-protocol.md`、`docs/environment-matrix.md`、`docs/agent-candidates.md`、`docs/solution.md`。
