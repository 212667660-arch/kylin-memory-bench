# 数据集与 Prompt 来源声明

## 当前发布范围

- `suites/core-zh.yaml`、`suites/core-en.yaml`、`suites/adversarial/core.yaml`、`suites/adversarial/core-en.yaml`、`examples/*.jsonl` 为“忆衡”项目内的案例与协议示例，用于六类长期记忆评测。中英文套件保持相同的六类能力和检查结构；对抗套件额外覆盖冲突、噪声、相似实体、敏感/注入边界和跨任务复用。
- 当前项目没有将 MemoryAgentBench、GoodAI、MemEval、HaluMem、GateMem、kylinOS-agent-memory 或 openkylin/llm-agent 的数据集、Prompt、图表或模型输出原样复制到 `kmb/`、`suites/`、`examples/`。
- `.tmp-github-research/` 仅用于研究核查，禁止作为发行物内容。其文件来源、许可证和再分发条件不因留在本地缓存而发生变化。

## Prompt 与模型输出

- HTTP/命令适配器的提示由案例和项目协议组成；若后续引入第三方 Prompt，必须记录来源、版本、许可证和修改。
- `runs/` 中的模型请求/响应、工具事件和文件路径是运行证据，可能涉及云 API 条款、个人信息或敏感路径；对外展示前应脱敏并确认服务条款。
- 不得把模型文本中的“我已记住”当作记忆写入证据。只有工具/状态/文件等可观察事件才进入相应评分。

## 发布前检查

1. 列出每个外部数据、Prompt、图表、模型输出和依赖的来源与许可证。
2. 对不可商用、禁止衍生、无许可证或用途不明的内容执行替换、隔离或书面授权。
3. 将发行包排除 `.tmp-github-research/`、虚拟环境、pip 缓存和未经脱敏的 `runs/`。
4. 由项目负责人确认项目级 LICENSE；当前 `NOTICE` 不替代许可证。
