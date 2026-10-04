# Brief: openKylin 智能体生态核实（截至 2026-09）

## Refined question
截至 **2026-09-18**，系统核实 openKylin 生态中已支持/适配/可运行的主流 Agent 与 Agent 框架、Token Center、MCP/Skill 体系；严格区分「官方支持 / 社区生态 / 仅 Linux 理论可运行」；并对照 KylinMemoryBench 现有适配能力，指出**当前项目可直接测试 vs 需包装 vs 暂不可测**的对象。

## Audience
上海开源软件应用创新大赛「忆衡/KylinMemoryBench」负责人；用于选型与评测接入，不是营销软文。

## Time frame
优先 2025–2026-09 信息；结论标注信息日期。今天：2026-09-18。

## Scope in
- openKylin 官方/生态 Agent：KylinBot、OpenClaw、WorkBuddy、Raccoon Work/小浣熊、AgentOS、openKylin-skills、Astron Agent
- 框架：LangChain、LangGraph、AgentScope(2.0)、Qwen-Agent、AutoGen、CrewAI
- openKylin Token Center（OpenAI-compatible、额度、接入）
- openKylin MCP/Skill 与 Agent 调用关系
- 总表字段：官方支持级别、安装、地址、License、免费、API/MCP/Skill/Memory/多Agent/本地模型、是否适合 KMB Benchmark

## Scope out
- 未在 openKylin 有公开信息的闭源产品细节臆测
- 不把「pip 能装」写成「openKylin 官方适配」
- 不执行真实 API 付费调用

## Assumptions
- 信息可能冲突或缺失：优先官方源；无官方源则标 community / 未验证
- 免费安装 ≠ 免费调用模型
- KMB 可测性依据仓库内适配器：`http` / `command` / `replay` / `memory_controller` / `memory_disabled` + 证据协议（需 Agent 自有记忆事件才可谈原生记忆）

## Depth
**standard**（4 个并行子代理，每代理最多 6 次检索）

## Angles
1. **F1** openKylin 官方/商店侧 Agent：KylinBot、WorkBuddy、Raccoon、AgentOS 概览（预装/版本/安装/地址/免费）
2. **F2** OpenClaw + openKylin-skills + openKylin MCP：安装、调用、与 KylinBot/框架关系
3. **F3** openKylin Token Center + Astron Agent：OpenAI API、Base URL、Key、额度/签到、接入链路；Astron 安装与 MCP/Skillhub
4. **F4** 六大 Agent 框架：GitHub/文档/License/安装、MCP/Memory/多Agent/本地模型、openKylin 是否官方适配 vs 仅 Linux 可运行

## KMB 可测性对照（本地事实，不依赖外网）
- 已有：reference/flawed（离线）、kylinbot-process stand-in（command）、Grok/DeepSeek http 与 wrapper/no-memory、replay 示例
- 可测条件：OpenAI-compatible → `type: http`（无原生记忆事件则记忆维 miss）；可脚本化 stdin→JSONL → `type: command`；先导出证据 → `type: replay`
- 不可直接测：仅有 GUI、无日志/API、无法导出 kmb_evidence 的产品

## Deliverable path
`E:\上海开源软件应用创新大赛\research\openkylin-agent-ecosystem\REPORT.md`
