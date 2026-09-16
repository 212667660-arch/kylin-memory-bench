# 参考项目许可证审计清单

> 状态截至 2026-09-02。该清单是工程审计记录，不是法律意见。代码、数据集、Prompt、图表、论文结果、模型和依赖分别判断，不能用代码 LICENSE 推断全部内容。

## 本轮核查范围

- 已读取指定参考仓库的可见根目录 `LICENSE`/`NOTICE`、数据卡、README 和可用依赖清单；本地研究缓存中实际发现了 MemoryAgentBench `requirements.txt`、MemEval `pyproject.toml`/`NOTICE`、GateMem `requirements.txt`/`DATASET_CARD.md`、kylinOS-agent-memory `memory-service/requirements.txt`、llm-agent `requirements.txt`。
- 已对本项目可发行代码、套件、示例、脚本、配置、README、NOTICE 进行参考项目名称扫描，未发现上述七个项目名称，符合“当前没有复制其代码/数据/Prompt”的声明。
- 没有逐个解析参考仓库的全部传递依赖，也没有把它们安装为“忆衡”依赖；这些传递依赖的许可证状态为“需人工确认”，不能从顶层仓库许可证推断。
- 可用 `python scripts/audit_reference_licenses.py --out runs/license-audit-20260902/inventory.json` 重新生成研究缓存的文件级清单；脚本只读扫描许可证文件、依赖清单和 data/prompt/third_party 路径，不复制内容，也不作法律分类。

## 审计结论

| 来源 | 固定版本 | 可见许可证 | 本项目处理 | 风险/后续 |
|---|---|---|---|---|
| HUST-AI-HYZ/MemoryAgentBench | `main` / `fe1735d` | 仓库 `LICENSE` 已确认 MIT | 仅参考；若复用代码，保留版权和许可证 | Hugging Face 数据、致谢数据和第三方依赖需逐项审查 |
| GoodAI/goodai-ltm-benchmark | `main` | 仓库 LICENSE 文本已确认 MIT；GitHub API 曾为 `NOASSERTION` | 仅参考；不复制其数据/Prompt | README 标记部分 GPT 生成数据、SallyAnne、TriviaQA/ChapterBreak 存在独立用途/授权限制 |
| ProsusAI/MemEval | `main` / `807ae6d` | Apache-2.0，含 `NOTICE` | 仅参考；代码若复用须保留 LICENSE、NOTICE、版权和修改声明 | LoCoMo/LongMemEval、第三方 memory system 和依赖另审 |
| MemTensor/HaluMem | `main` / `eef0666` | CC BY-NC-ND 4.0 | 不复制代码、数据、Prompt、图表；重新实现公开思想 | 非商业、禁止衍生，赛事发布/商业分发风险高 |
| rzhub/GateMem | `main` / `603f9f4` | MIT | 仅参考；若复用代码须保留版权和许可证 | 合成数据、攻击样本、Prompt、third_party 目录另审 |
| Kylin-Agent-Competition/kylinOS-agent-memory | `main` / `188e761` | All Rights Reserved | 不复制代码、契约、案例、文案 | 如需复用必须取得书面授权；目标系统也不是 openKylin |
| openkylin/llm-agent | `develop` / `24578ff` | `LICENSE` 实际为 AGPL-3.0 | 不并入源码；优先独立进程/HTTP 协议作为被测对象 | 网络服务、衍生作品、许可证告知和源码公开义务需法律审查；README 描述与 LICENSE 不一致 |

## 本项目自身来源

- `docs/benchmark-reference-playbook.md` 和 `docs/github-memory-benchmark-landscape.md` 为本项目原创整理文档，引用仓库 URL、版本和事实性描述。
- 当前 `suites/` 案例、`examples/` JSONL、评分器和报告代码为本项目实现；没有把上述第三方数据或 Prompt 原样复制进主代码。
- `.tmp-github-research/` 是研究缓存，不应打包进发行物；其中的完整仓库、数据和 Prompt 不等于获得再分发许可。
- 当前运行产物 `runs/` 仅保存本项目执行产生的模型请求/响应和事件；发布前需审查云 API 服务条款、隐私和脱敏范围。

## 直接运行依赖

| 依赖 | 当前声明/核查版本 | 许可证证据 | 发布处理 |
|---|---|---|---|
| PyYAML | `pyproject.toml`：`PyYAML>=6.0`；宿主开发环境：6.0.3；openKylin VM `.kmb-venv`：6.0.1 | 两个环境均通过 `importlib.metadata`/`pip show` 实际核查为 MIT；元数据未报告传递依赖；发行包声明 `python3-yaml` | 在发行包/离线 wheelhouse 中保留其许可证与版权信息，并随依赖版本更新复核；最终 openKylin 系统包版本仍需安装后记录 |

当前 `pyproject.toml` 未声明其他运行时第三方依赖。虚拟环境中出现的其他包不是“忆衡”发行依赖，不应因为当前开发环境存在而加入发布物。

## 执行规则

1. 拟复用第三方代码前，先记录仓库 URL、commit、文件范围、许可证、版权/NOTICE、修改内容和新增依赖。
2. 拟使用第三方数据、Prompt、图表或模型输出前，单独确认商业/赛事展示、再分发和衍生限制；未知时标记“需人工确认”并隔离。
3. 不将 `NOASSERTION` 解释为可使用，不将公开仓库解释为公共领域。
4. 发布前由项目负责人或法务确认高风险项；本文件的“可参考”不构成授权。

## 待人工确认

- 赛事是否允许云 API 作为参评 Agent，以及模型请求/响应的脱敏和展示范围。
- 所有拟新增 Hugging Face 或论文数据的再分发许可。
- `.deb`/离线包发布时的依赖许可证、AGPL 隔离边界和第三方 NOTICE 打包策略。
