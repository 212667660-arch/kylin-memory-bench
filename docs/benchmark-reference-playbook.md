# “忆衡”Benchmark 借鉴实施指南

> 用途：后续开发前的参考清单。本文只提取已核查项目中的公开工程思路，并将其重新映射到“忆衡”的接口和目录；不构成第三方代码、数据、Prompt、图表或结果的复制授权。
> 详细仓库事实见：[GitHub 技术景观研究](E:/上海开源软件应用创新大赛/docs/github-memory-benchmark-landscape.md)。许可证判断不是法律意见。

## 1. 使用原则

### 1.1 可以借鉴什么

- 公开的评测思想、抽象接口、数据字段设计方向、评分维度、批量执行策略和报告组织方式。
- 重新设计后的等价实现，使用“忆衡”自己的 `EvidenceEvent`、案例、Prompt 和评分规则。
- MIT/Apache-2.0 项目的代码，只有在逐文件确认许可证、保留版权/许可证/NOTICE、记录修改并审查依赖后才考虑复用。

### 1.2 不可以直接拿来用什么

- 第三方数据集、Prompt、生成内容、论文结果、图表、截图或模型输出；这些内容不能因为代码许可证宽松就默认可复用。
- HaluMem 的 CC BY-NC-ND 内容、kylinOS-agent-memory 的 All Rights Reserved 内容。
- 未确认许可证的文件。GitHub API 显示 `NOASSERTION` 时，应视为“许可证尚未确认”，而不是可自由复制。
- `openkylin/llm-agent` 的 AGPL-3.0 代码，除非完成独立法律审查并明确网络服务和衍生作品义务。

### 1.3 “忆衡”不能被改变的边界

- 仍然是长期记忆自动化评测 Benchmark，不是聊天机器人、RAG 产品或单模型测试脚本。
- 六类能力必须完整保留：长期保持、记忆调用、动态更新、相近区分、边界识别、任务复用。
- 分数必须来自真实运行证据；模型自述不能替代工具结果、记忆状态或文件产物。
- 外部包装层事件必须标记 `source=wrapper`，模型原生事件标记 `source=model`，不能混为一谈。

## 2. 参考项目到“忆衡”的借鉴地图

| 来源项目 | 建议借鉴 | 映射到“忆衡” | 优先级 | 直接复制限制 |
|---|---|---|---|---|
| GateMem | checkpoint、外部 predictions、上下文泄漏检查、resume/sweep、continue-on-error | `suites/` 检查点、`kmb/runner.py` 批量恢复、`kmb/scoring.py` 证据分层 | P0 | 代码虽为 MIT，数据、攻击样本和 Prompt 需另审 |
| GoodAI LTM | 极简有状态 Agent 接口、等待/时间推进、断点保存、HTML 比较报告 | `kmb/agents.py` 适配器、runner 元数据、`kmb/report.py` | P0 | 代码虽为 MIT，部分数据/生成内容用途受限 |
| HaluMem | extraction/update/QA 分解、Correct/Hallucination/Omission 分类、weighted recall/F1 | `kmb/scoring.py` 失败类型和记忆操作指标 | P1 | CC BY-NC-ND，不复制代码、数据、Prompt、图表 |
| MemEval | 系统注册表、公平比较、per-category mean/std、token/cost 统计 | Agent 配置注册、`compare` 汇总、运行成本元数据 | P1 | Apache-2.0 代码需保留 LICENSE/NOTICE；外部数据另审 |
| MemoryAgentBench | 多任务能力划分、inject-once/query-many、上下文/问题/答案元数据 | 六类套件设计、跨轮次案例和 `case_id` 元数据 | P1 | MIT 代码需保留归属；Hugging Face/第三方数据不能直接带入 |
| kylinOS-agent-memory | Linux/Kylin 环境探针、trace/idempotency、敏感/遗忘/冲突计数、真实工具结果与模型自述分离 | `scripts/env_probe.py`、EvidenceEvent 扩展、openKylin 适配记录 | P1 | All Rights Reserved，不复制代码、契约、案例或文案 |
| openkylin/llm-agent | 服务型 Agent 的 HTTP/WebSocket 接入形态、会话/文件证据来源 | `type=command/http` 外部 Agent 适配器、文件 Artifact 事件 | P2 | AGPL-3.0；优先独立进程协议接入，不并入源码 |

## 3. 可直接指导编码的模式

### 3.1 Agent 适配器：采用“小接口 + 统一 runner”

**参考来源**：GoodAI 的 `ChatSession`，MemEval 的系统注册模板，GateMem 的 `MemoryAgent` Protocol。

**“忆衡”落地**：

- 保持 `AgentAdapter` 为唯一 runner 依赖，适配器只负责初始化、执行案例和返回事件。
- 每个适配器至少明确 `name`、`backend`、`version`、`reset_case`、`send_turn`、`close` 和能力声明。
- HTTP、command、replay、memory_controller 继续共用同一个 `run_suite` 和评分器。
- Agent 配置只放模型、端点、超时和环境变量名；密钥只从进程环境读取。
- 适配器不能根据普通文本臆测 `memory_write` 或 `memory_recall`。缺少事件时必须记录证据缺失。

**建议验收**：同一案例分别运行两个 Agent，输入、提示模板、seed、超时和评分器完全一致；输出中能区分 `backend` 与 `wrapper`。

### 3.2 数据集：采用“案例 + 轮次 + 检查点”

**参考来源**：MemoryAgentBench 的 context/questions/metadata，GateMem 的 episode/checkpoint，GoodAI 的脚本和等待条件。

**“忆衡”落地**：

- `suites/*.yaml` 保持顶层 `id`、`capability`、`turns`、`checks`。
- 长任务拆成显式轮次：事实写入、干扰/等待、查询、更新、抑制或任务动作。
- 对需要在某一历史状态验证的场景增加 `checkpoint_id`、`as_of_step` 和不可见评分字段。
- 数据中区分 Agent 可见字段与 scorer-only 字段，避免把答案或攻击目标泄露给 Agent。
- 每类能力至少保留一个最小案例，再通过参数化方式扩展语言、实体、时间、噪声和任务领域。

**建议验收**：`kmb validate --strict` 能拒绝缺少 `case_id`、能力名、检查项或非法事件类型的案例。

### 3.3 证据：采用事件链，而不是只保存最终答案

**参考来源**：GateMem 的 `used_record_ids` 和 prompt-context 泄漏检查；kylinOS-agent-memory 的 trace/idempotency/Tool/Turn 事件设计。

**“忆衡”落地**：

- 继续使用 JSONL，一行一个 `EvidenceEvent`，至少有 `agent`、`case_id`、`kind`、`data`、`step`、`timestamp`、`source`。
- `kind` 至少覆盖 `user_message`、`assistant_message`、`memory_write`、`memory_update`、`memory_recall`、`memory_suppress`、`action`、`tool_result`、`file_artifact`、`error`。
- `data` 保存事件发生时的 key/value、persist、hit、工具参数、路径、退出码、摘要和脱敏引用；不要保存密钥。
- 为每次请求、响应、记忆操作和动作增加 `trace_id` 或 `parent_event_id`，使评分理由能定位到事件。
- 明确证据来源：模型原生工具调用、包装层执行、外部服务返回、runner 运行元数据分别标记。
- 对提示上下文、检索记录和删除/敏感记忆进行泄漏扫描，但不能把“模型说自己记住了”当作实际写入。

**建议验收**：每条分数都能列出 `evidence_refs`；缺失事件、非法 JSON、超时和非零退出均有 `error` 事件及失败类型。

### 3.4 评分：采用“规则优先 + 操作分类 + 多维聚合”

**参考来源**：HaluMem 的 extraction/update/QA 分类和 weighted recall；GateMem 的 answer/context/e2e 泄漏层次；MemEval 的类别聚合和 mean/std。

**“忆衡”落地**：

- 保持事实状态机：`write`、`retain`、`revise`、`suppress`、`reuse`。
- 每个 check 输出 `passed`、`score`、`reason`、`failure_type`、`evidence_refs`，失败类型至少包含 `omission`、`confusion`、`stale_update`、`erroneous_persistence`、`erroneous_reuse`、`runtime_error`、`evidence_missing`。
- 分层统计：案例分、六类能力分、证据完整度、失败类型计数、运行异常数、平均/标准差和总分。
- 对边界识别增加三层检查：最终回答泄漏、注入上下文泄漏、任务动作/end-to-end 泄漏。
- LLM judge 只能作为可选辅助；规则结果和 judge 结果分开保存，不覆盖确定性规则分数。
- 比较两个 Agent 时使用同一套件和同一评分版本，输出差异而不是只输出单一排行榜。

**建议验收**：修改一个证据事件后，只有引用该事件的 check 发生变化；同一 seed 和配置重复运行得到一致规则分数。

### 3.5 运行可靠性：采用“可恢复、可批量、不中断”

**参考来源**：GoodAI 的 `load/save` 和交错调度，GateMem 的 resume/sweep，HaluMem 的并发和缓存。

**“忆衡”落地**：

- 每次运行生成 `run_id`、配置摘要、套件版本、Agent 后端、模型版本、seed、开始/结束时间和依赖版本。
- 失败案例写入 `error` 事件并继续下一案例；最终结果区分成功、失败、超时、重试耗尽和证据缺失。
- 重试只针对可配置的网络/服务错误；不重复伪造或补写已缺失的记忆事件。
- 为批量运行保留每个 Agent/案例独立目录，支持从结果目录恢复，避免覆盖已有运行证据。
- 提供 `--timeout`、`--retries`、`--seed`、`--run-id`、`--resume` 和并发上限，记录实际尝试次数。

**建议验收**：单个案例超时不会中断双 Agent 批量运行；恢复运行不重复已完成案例，重复运行结果可比较。

### 3.6 报告：采用“细节报告 + 比较报告”

**参考来源**：GoodAI 的详细/比较 HTML，MemEval 的 aggregate summary 和图表，GateMem 的 predictions/scores/summary 分离。

**“忆衡”落地**：

- 保持现有 JSON、Markdown、SVG、HTML 四类产物。
- 单 Agent 报告展示案例、六类能力、每条 check、失败理由、证据引用和事件统计。
- 双 Agent 报告展示同一套件下的维度对比、标准差、证据完整度、失败类型和后端/包装层标记。
- 原始 `evidence.jsonl`、`result.json`、`comparison.json` 必须独立保存，HTML 只是可视化，不是唯一证据。
- 报告中显示评分器版本、套件哈希和运行命令，便于复现。

**建议验收**：删除或移动 HTML 后，仍可凭 JSONL 和 JSON 重建评分；报告不显示 API 密钥。

### 3.7 openKylin 适配：采用“探针 + 离线安装 + 记录模板”

**参考来源**：kylinOS-agent-memory 的环境检查和分层验收思路。

**“忆衡”落地**：

- 使用 `scripts/env_probe.py` 检查系统、架构、Python、磁盘、网络和依赖，并提供 `--require-openkylin` 门禁。
- Linux/openKylin 运行只使用 `scripts/install_local.sh`、`run_demo.sh`、`run_acceptance.sh` 和卸载脚本；不要把 Windows 结果当作兼容性结论。
- 环境矩阵记录 `uname -a`、`/etc/os-release`、Python/pip、依赖版本、安装/运行/卸载退出码和结果文件哈希。
- 若 Agent 使用 UDS、文件、工具或桌面服务，单独记录连接方式、权限、超时、取消和回滚事件。
- 在没有真实 openKylin 介质时，只能交付探针、脚本和记录模板，状态写为“未验证”。

## 4. 分阶段实施清单

### P0：下一次代码迭代前必须完成

- [ ] 冻结 `EvidenceEvent` schema 和 `source` 语义，增加 `trace_id`/`evidence_refs` 约定。
- [ ] 在六类案例中补充 checkpoint、评分字段隔离和失败类型覆盖。
- [ ] 检查 `run`/`compare` 是否对两个真实 Agent 使用完全相同的套件、seed、超时和评分版本。
- [ ] 为 `evidence_missing`、`timeout`、`invalid_json`、`nonzero_exit` 增加可测试的错误收敛路径。

### P1：赛事可验收版本增强

- [ ] 增加批量 `resume`、重复运行摘要、mean/std、成本和证据完整度统计。
- [ ] 把 answer/context/end-to-end 泄漏检查纳入边界识别案例。
- [ ] 增加 HTML 报告中的事件折叠、证据引用和失败类型过滤。
- [ ] 用独立进程适配至少一种 openKylin Agent/工具事件来源，不把其源码并入 Benchmark。

### P2：发布和合规

- [ ] 对拟复用的 MIT/Apache 文件建立 `THIRD_PARTY_NOTICES`，记录来源 URL、提交、文件、许可证和修改。
- [ ] 对数据集、Prompt、图表、模型 API 和依赖单独建立许可审计表。
- [ ] 制作 openKylin 干净环境安装/卸载记录和 3-5 分钟双 Agent 演示材料。

## 5. 许可证与来源记录模板

任何拟复用内容都必须先填表，未填不得提交到主代码：

| 字段 | 必填内容 |
|---|---|
| 来源项目 | 仓库名称和 URL |
| 固定版本 | 分支、tag 或 commit |
| 文件范围 | 精确到文件路径和行/函数范围 |
| 内容类型 | 代码、数据、Prompt、图表、文档或思想 |
| 许可证 | LICENSE/NOTICE 原文确认结果；`NOASSERTION` 不能作为许可 |
| 处理方式 | 仅参考、重新实现、原样复用或不采用 |
| 保留事项 | 版权、许可证、NOTICE、修改声明、署名 |
| 依赖影响 | 新增依赖及其许可证 |
| 审核人 | 项目负责人/法务确认状态 |

当前默认处理：

- MemoryAgentBench、GoodAI、GateMem：只考虑在满足 MIT 条件且完成文件级审计后复用代码。
- MemEval：只考虑在满足 Apache-2.0、保留 NOTICE/修改声明且完成依赖审计后复用代码。
- HaluMem、kylinOS-agent-memory：仅参考公开思想，不复制内容。
- openkylin/llm-agent：优先通过独立进程或 HTTP/command 协议作为被测对象，不复制 AGPL 源码。

## 6. 不同参考项目之间的冲突处理

- **最终回答 vs 运行证据**：采用“证据事件优先”；回答只能作为一类事件，不能替代记忆或工具事件。
- **LLM judge vs 确定性规则**：规则分数为主，judge 作为独立字段，不覆盖原始证据。
- **RAG 检索上下文 vs 记忆状态**：检索上下文只能证明被注入的上下文，不自动证明已持久化或应当复用。
- **治理指标 vs 六类能力**：GateMem 的 utility/privacy/forgetting 可作为边界扩展，但不能压缩或替换“忆衡”六类能力。
- **麒麟系统 vs openKylin**：银河麒麟 V11 的经验只能作为 Linux/OS 适配参考，不能替代 openKylin 实机验证。
- **代码许可证 vs 数据许可证**：始终按最小文件范围和内容类型分别审查。

## 7. 编码时的快速检查

提交涉及评测流程的代码前，逐项确认：

- [ ] 是否仍覆盖六类能力？
- [ ] 是否使用统一案例、输入、seed、超时和评分器比较 Agent？
- [ ] 每个分数是否有 `reason`、`failure_type` 和 `evidence_refs`？
- [ ] 是否区分 `source=model`、`source=wrapper` 和外部工具结果？
- [ ] 普通文本是否被错误解释成记忆写入或调用？
- [ ] 异常、超时、非法 JSON、缺失证据是否继续收敛而不中断批量？
- [ ] 是否保存可复现的 run 元数据和原始 JSONL？
- [ ] 是否把 Windows/Linux 理论可移植性误写成 openKylin 已验证？
- [ ] 是否引入了第三方代码、数据或 Prompt？若有，是否完成来源和许可证记录？
- [ ] 是否把参考项目名称或结果写成“忆衡”自己的能力？

## 8. 当前结论

这些项目可以作为“忆衡”的技术参考，但应以 GateMem 的证据/批量思想、GoodAI 的 Agent 接口/报告、HaluMem 的操作级失败分类、MemEval 的公平比较和 MemoryAgentBench 的任务组织为主要输入，重新实现为“忆衡”的 EvidenceEvent 和状态机。

当前不应直接复制 HaluMem、kylinOS-agent-memory 或 `openkylin/llm-agent` 的代码和内容；MIT/Apache 项目也必须逐文件审计后再决定是否复用。后续每次代码迭代都应先对照本指南的 P0/P1 清单和许可证记录模板。

