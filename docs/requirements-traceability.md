# 赛题非视频要求追踪清单

本清单逐项对应 `ai_open_kylin_open_kylin_benchmark_XaCQyZepC8.pdf` 的交付要求；按项目要求，真实环境桌面视频单独排除，不在本清单中伪称完成。

## A. 案例说明文档

| 目标 | 实现位置 | 验证方式 | 状态 |
|---|---|---|---|
| 说明长期记忆评测目标、前提、数据组织、证据采集和评分流程 | `docs/solution.md`、`docs/benchmark-reference-playbook.md`、`docs/evidence-protocol.md` | 文档审查；`python3 -m kmb.cli validate --strict ...` | 已实现 |
| 覆盖长期保持、记忆调用、动态更新、相近区分、边界识别、任务复用六类能力 | `suites/core-zh.yaml`、`suites/core-en.yaml`、`kmb/runner.py`、`kmb/scoring.py` | 全部核心/英文/扩展/对抗/生命周期套件严格校验 | 已实现 |
| 证据能组织对话、记忆记录、动作轨迹和文件产物 | `kmb/models.py`、`kmb/agents.py`、`kmb/runner.py`、`EvidenceEvent` schema v2 | `scripts/verify_run.py --strict`；JSONL 事件链检查 | 已实现 |

## B. 样例数据与样例结果

| 目标 | 实现位置 | 验证方式 | 状态 |
|---|---|---|---|
| 提供少量可运行示例任务 | `suites/quick.yaml`、`suites/core-zh.yaml`、`suites/native/kylinbot-gate.yaml` | 套件 validate；native gate 使用非 strict 校验，因为它是单案例门禁 | 已实现 |
| 提供扩展、对抗和生命周期样例 | `suites/core-zh-expanded.yaml`、`suites/adversarial/*.yaml`、`suites/lifecycle/innovation.yaml` | 每个套件均通过 `validate --strict` | 已实现 |
| 案例覆盖、语言、风险标签和版本可审计 | `scripts/coverage_report.py`、`suites/coverage/manifest.yaml` | `python scripts/coverage_report.py --suites suites/core-zh.yaml suites/core-zh-expanded.yaml suites/adversarial/extended.yaml --out runs/coverage-report --manifest suites/coverage/manifest.yaml` | 已实现（39 案例；报告列明六类能力、标签和 suite SHA-256） |
| 提供可审计样例结果、雷达图和比较报告 | `scripts/run_offline_demo.sh`；`runs/verification-offline-20260923/` | Windows 离线 demo 与 openKylin VM `verification-openkylin-20260923-v2` 均生成 4 组对比、8 份 agent 结果；所有结果通过 `verify_run.py --strict` | 已实现 |

## C. 可复现材料

| 目标 | 实现位置 | 验证方式 | 状态 |
|---|---|---|---|
| README、配置、脚本和源代码齐全 | `README.md`、`configs/`、`scripts/`、`kmb/`、`tests/` | Windows 本机：`.venv-kmb-system\\Scripts\\python.exe -m unittest discover -s tests -v`（104 项）；openKylin 3.0 VM 已复核核心链路 | 已实现 |
| 同一输入下可复现、可批量、不中断并保留失败证据 | `kmb/runner.py`、`scripts/run_acceptance.sh`、`scripts/aggregate_repeats.py` | 重试、超时、错误分类、evidence JSONL 回归测试 | 已实现 |
| 结果包含 JSON/JSONL、Markdown、HTML、SVG | `kmb/report.py`、`kmb/cli.py`、`kmb/workbench.py` | offline demo 产物检查；前端 `node --check kmb/web/app.js` | 已实现 |
| 当前已有 Agent 可一键发现、预检和双 Agent 对比 | `kmb/agent_registry.py`、`kmb/quick_compare.py`、`docs/quick-start.md` | 工作台 `/api/agents`、`POST /api/quick-compare`；无 Agent 时安全阻断 | 已实现 |

## D. CLI/GUI 封装与 openKylin 落地

| 目标 | 实现位置 | 验证方式 | 状态 |
|---|---|---|---|
| CLI 一键运行、批量比较和严格验证 | `kmb/cli.py`、`scripts/run_acceptance.sh` | validate、compare、verify 命令已执行 | 已实现 |
| 图形化工作台展示发现、任务、结果、证据和失败下钻 | `kmb/workbench.py`、`kmb/web/`、`docs/workbench.md` | 本地服务首页、`/api/agents`、`/api/runs`、快速对比阻断接口均已实测 | 已实现 |
| Debian/openKylin 技术包与生命周期脚本 | `scripts/build_deb.sh`、`scripts/install_deb.sh`、`scripts/verify_deb.sh`、`packaging/deb/` | openKylin 3.0 amd64：构建、解包、包内 smoke、validate、compare、strict verify 均通过；**2026-10-04 完整生命周期矩阵**（install release6 → verify → upgrade release7 → verify → uninstall → 残留检查，七步全 0）见 `runs/deb-lifecycle-3.0vm-20261004/` | 已实现 |
| 至少两类真实 Agent 适配与统一证据协议 | `kmb/agent_adapters/`、`scripts/kylinbot_command_agent.py`、`docs/ecosystem-agent-export.md` | openKylin 3.0 VM 隔离 HOME：KylinBot/OpenClaw 六案例真实快速对比完成；两侧 `verify_run.py --strict` 退出码 0；Hermes 已发现但未纳入本轮批次，KylinAgent 仍因 GUI/服务级证据安全阻断 | 已验证（KylinBot/OpenClaw） |

## 当前验证汇总

- `131 tests` 全部通过（2026-09-28 回归：基线 123 + 工作台一键对比 3 + 覆盖报告 3 + 快速对比预检 2；新增不变量测试锁死敏感案例抑制门禁与 core 案例 ID 不变，另补 `--preflight-only` 契约测试确保预检不发起任何 Agent 回合）。
- `quick-compare --preflight-only`：**2026-09-28 才真正实现**。此前该命令虽写入计划任务 4 步骤 4 的验证清单，但代码中从未存在；现已支持，并在 openKylin VM 上以零 token（`turns_started=0`、无评测产物）验证 kylinbot/hermes 预检 `ready`。
- 套件覆盖报告：49 个案例（39 基础 + 2026-09-27 增补 4 中文对抗案例与 6 英文多语言案例），六类能力均有 7–10 个案例；语言维度 en 6/mixed 19/zh 24；标签统计包括敏感 9、明确风险 2、噪声 7、相似实体 8、跨任务 8、抑制 10；套件 SHA-256 见 `suites/coverage/manifest.yaml`。2026-09-28 将 5 个存量敏感/风险案例（`sensitive-ext-001~003`、`boundary-101-otp-suffix`、`boundary-102-risk-cmd`）的 `memory_absent` 升级为 `sensitive_not_persisted`，全库敏感/风险门禁统一要求 `memory_suppress` 抑制证据。
- `node --check kmb/web/app.js` 通过。
- `suites/quick.yaml`、核心、英文、扩展、对抗、生命周期和 native gate 均可校验；native gate 是单案例门禁，正确命令是不加 `--strict`。
- `scripts/run_offline_demo.sh runs/verification-offline-20260923` 成功，四组比较和所有 agent 结果均通过严格证据校验；最新 openKylin VM 批次为 `/tmp/kmb-verification/runs/verification-openkylin-20260923-v2`。
- openKylin 3.0 VM（`192.168.141.128:22`）已复核离线四组比较、`.deb` 包内 smoke/strict verify、工作台 HTTP 接口，并发现四个生态 Agent；KylinAgent：2026-10-05 已实现隔离实例无头驱动（`scripts/kylinagent_driver.py`，hermes-agent 引擎 + 结构化 memory_recall 证据提取），批次受 openKylin 网关挂死 bug 阻断（证据 `runs/kylinagent-real-20261005/`），维持安全阻断直至官方修复。
- 最新真实批次：`/home/Cisyam/kmb-agent-validation-20260923/runs/quick-compare-isolated-20260924/`。在空白临时记忆库与独立 HOME 中运行 KylinBot/OpenClaw 六案例，KylinBot `63.89`、OpenClaw `13.89`，均 `score_valid=true`；两侧 strict 校验分别为 51/34 条证据、退出码 0。结果是系统级外部记忆/动作控制器行为，均 `native_memory_events=0`，不能解释为模型原生记忆能力。
- 本轮新 Token 的 `/v1/models` 连通性返回 HTTP 200；真实 Agent 调用未再出现 402。临时副本不修改用户日常记忆，Token 未写入仓库或结果文件。
- 桌面视频未纳入本清单，按用户要求后置。

## 最新非视频收口状态（2026-09-25）

本节是当前交付判断，覆盖历史审计中的旧状态文字，但不删除历史证据：

| 项目 | 当前判断 | 当前证据 |
|---|---|---|
| 官方最短路径 | 已具备 | `python -m kmb.cli official-acceptance --out runs/official-final-20260925-r2 --mode offline`，退出码 `0` |
| 官方自评分 | 100/100 | `runs/official-final-20261004/scorecard/scorecard.json`（2026-10-04；PDF-16 依据 VM 真实双 Agent 2 批全有效） |
| 本轮全量回归 | 已通过 | `python -m unittest discover -s tests -v`：129 项通过；`compileall`、`node --check`、`git diff --check` 均通过 |
| 覆盖报告 | 已具备 | 49 个案例（含英文多语言套件），六类能力、语言、风险、噪声、相似实体和跨任务标签均有统计 |
| 重复批次 | 部分完成 | 最新真实批次 `runs/official-installed-20261001-r2/`（2026-10-01 VM）：两 Agent 各 2/3 批有效分（66.67%），KylinBot 均值 40.28/标准差 9.82，OpenClaw 27.78/±0；第 3 批因网关余额耗尽 402 无效，保留在分母；早期批次 `runs/official-repeat-vm-20260924-fixed/` 与 429 受扰的 `runs/official-installed-20261001/` 均原样保留；不能宣称完全稳定 |
| B 轨记忆工具 | 框架已具备 | KV/similar 离线 strict 结果可复核；离线规则后端必须标记为模拟，不替代真实 LLM 工具调用 |
| 发布包 | 已具备 | `dist/official-bundle-final-20260925-official/` 严格脱敏审计通过；Debian 包在 openKylin VM 临时副本中构建、解包 smoke、核心套件 strict validate 和评分脚本检查均通过 |
| 原生记忆结论 | 不可观测 | 真实 KylinBot/OpenClaw 批次 `native_memory_events=0`，只报告系统级行为 |
| PDF-12 视频 | 未处理 | 按用户要求排除 |
| 项目级 `LICENSE` | 未处理 | 按用户要求排除，候选文件不等于生效许可 |

当前评审结论：非视频代码、验收入口、证据链、评分器和脱敏发布材料已形成可复核闭环；PDF-16 受真实 billing/timeout 批次影响只给部分分，视频和 `LICENSE` 不在本轮工作范围内。
