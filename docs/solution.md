# 方案说明

## 1. 目标与范围

本工具评测智能体在跨轮次任务中的长期记忆行为。每条用例声明交互轮次与期望检查项，Agent 适配器执行后返回结构化事件；评分器只依据事件判定，不把最终回答的主观合理性作为唯一标准。

## 2. 数据与证据

案例字段为 `id`、`capability`、`turns`、`checks`。轮次可以声明 `memory`（write/update/suppress）、`query` 和 `action`。事件至少包含：`agent`、`case_id`、`kind`、`data`、`step`、`timestamp`。`data` 保存 key/value、持久化标记、工具参数和动作路径，因而能追溯评分依据。

## 3. 六类能力映射

| 能力 | 核心检查 |
|---|---|
| retention | 历史事实被持久化、后续 recall 命中且回答包含期望值 |
| memory_recall | 指定 key 产生命中事件，可校验 value |
| dynamic_update | 最新值覆盖旧值，回答不再出现旧值 |
| similar_distinction | 相似 key 的 recall 与回答必须对应正确实体 |
| boundary | `persist: false` 的临时/敏感信息不得写入或命中 |
| task_reuse | 工具名称与从记忆解析出的动作参数必须正确 |

失败类型包括 `omission`（遗漏）、`confusion`（混淆）、`stale_update`（更新失败）、`erroneous_persistence`（错误持久化）、`erroneous_reuse`（错误复用）和 `runtime_error`。

## 4. 执行与评分

`run_suite` 为每个案例调用一次适配器，逐事件写入 JSONL；异常会写入 `error` 事件并将案例标记为 `error`、得分 0。每条 check 得分为 0/1，案例分为通过检查数/检查总数，能力分为该能力案例平均分，总分为所有案例平均分。所有理由写入 `result.json` 与 Markdown，支持审计和稳定复现。

运行可指定 `--run-id`、`--seed` 和 `--retries`。每次失败尝试都会写入 `error` 事件；最终结果记录尝试次数、失败类型统计和运行时间元数据。批量执行不会因单个案例异常中断。

### 4.1 生命周期、变形与行动证据

扩展案例在不改变六类能力定义的前提下，为事实增加 `persistence`、`sensitivity`、`scope`、`version`、TTL/`expires_at` 和 `provenance`。包装层按 `write -> recall -> revise -> restart-boundary -> reuse -> expire/suppress` 记录状态转换；其中 `restart-boundary` 是包装层重建检查点，`system_restart=false`，不能替代 openKylin 的真实重启测试。

`suites/lifecycle/innovation.yaml` 包含路径更新、无关措辞、相似实体、合成一次性 token 和作用域隔离的变形组。runner 在单案例得分之外输出 `metamorphic_groups`，用确定性规则检查必须变化的结果和不变量，列出违反项及证据引用。

动作不以助手文本为依据：包装层只在项目内专用沙箱写入受控文件，并记录 `action`、`tool_result`、`file_artifact`、退出码、内容和 SHA256。路径、版本、TTL、作用域、敏感信息和工件规则由确定性评分器判断；模型文本最多属于未证实声明。

每次运行结果的 `evidence_schema_version=2` 会为事件补齐 `event_id`、`parent_event_id`、`correlation_id`、事实版本、作用域、工件摘要和可信等级，形成“原始事实 -> 状态转换 -> 检索 -> 请求/响应 -> 包装层操作 -> 动作 -> 工件 -> 规则判定”的可追溯链。

### 4.2 证据可观测性边界

每个 `EvidenceEvent` 现在同时保存 `source` 和 `evidence_class`。`source=model` 仅表示模型请求、回答或模型发起的工具调用；普通回答归为 `model_claim_unverified`，模型发出的 memory/tool call 默认归为 `model_memory_request_unverified` 或 `model_tool_request_unverified`。只有事件同时带有真实状态/执行结果标记（`state_observed: true` 或 `execution_observed: true`）才允许归类为 `model_native_memory`/`model_native_tool`。

`source=wrapper` 的记忆、动作和文件事件归为 `wrapper_operation`，分数解释为“模型后端 + 外部控制器”的系统级长期记忆行为；`source=provider_evidence` 只表示供应商导出的未独立验证证据；`source=simulated` 只用于离线演示基线。内部数据库未导出的状态始终在结果的 `observability.unobservable_internal_state` 中标记，不能从文本推断。

## 5. 双 Agent 对比样例

使用 `suites/core-zh.yaml` 的六个案例运行得到的、针对内置演示基线的真实本地运行证据（见 `runs/demo/`）：

| Agent | 总分 | retention | recall | update | similar | boundary | reuse |
|---|---:|---:|---:|---:|---:|---:|---:|
| reference | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 |
| flawed | 41.67 | 100.00 | 100.00 | 0.00 | 0.00 | 0.00 | 50.00 |

缺陷 Agent 的每项失败均可在对应 `result.json` 的 `reason` 和 `evidence.jsonl` 中定位。该样例证明评分链路能够区分行为，而非伪造单一模型分数。

## 6. openKylin 适配与复现

当前实机为 **openKylin 3.0（huanghe）**，使用原有系统开展验收，系统版本保持不动。项目软件版本为 0.2.1；当前结果见 [本轮审计](completion-audit-20261013.md) 和 [环境说明](current-environment.md)。以下 2026 年 9 月 Grok/DeepSeek、2.0 SP2 与 release7 结果属于历史记录。

在 Debian 系 openKylin 的 Python 3.9+ 环境中执行：安装 Python、PyYAML，复制仓库后运行 README 中的命令或 `bash scripts/run_demo.sh`。历史批次已在 openKylin VM 完成源码安装、CLI、真实 Grok/DeepSeek 双 Agent 运行、证据导出、评分、报告和卸载验证；`.deb` 第六批已在同一 VM 完成系统级安装、升级、验证、卸载和残留检查。Grok 和 DeepSeek 的真实 no-memory 基线均已完成 5 批统计，汇总位于 `runs/openkylin-validation-20260908/stability/`；两组结果均存在云 API 行为波动，不能宣称绝对稳定。系统级生命周期结论仅适用于已记录的 openKylin VM/KARE 版本。

真实环境的安装、双 Agent、证据导出、校验和卸载命令见 `docs/openkylin-validation-runbook.md`。当前 Windows 预检结果不能替代 openKylin 验证。

## 7. 历史决策与待确认事项（2026-09）

当时的 openKylin 2.0 SP2 x86_64 VM、Grok 4.6、DeepSeek v4 flash、证据导出方式和四套件已通过实际运行记录确认；真实 API 未导出原生记忆状态，因此结果只能表述为“统一包装层下的系统级长期记忆行为评测”。当时列出的许可证与第三方条款事项保留为历史；当前项目级 MIT 许可证已生效，实际第三方使用边界见 `THIRD_PARTY_NOTICES.md`。这些历史记录不定义当前 3.0 系统的版本或配置。
