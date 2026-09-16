# KylinMemoryBench

KylinMemoryBench 是面向 openKylin 的智能体长期记忆自动化评测 Benchmark。它不是聊天机器人或 RAG 产品，而是通过统一适配器收集真实运行事件，并以可审计的确定性规则评估六类能力：长期保持、记忆调用、动态更新、相近区分、边界识别、任务复用。

## 快速开始

需要 Python 3.9+ 和 PyYAML 6。评审可先跑**无云凭据离线闭环**（约 5 分钟，说明见 [docs/judge-reproduction-card.md](docs/judge-reproduction-card.md)）：

```bash
bash scripts/run_offline_demo.sh runs/offline-demo
```

该 demo 使用 **reference** 与 **kylinbot-process**（openKylin 生态进程适配器，本机 stand-in）双侧真实评测后输出对比与雷达图；另含 reference vs flawed 对照。无需 API Key。

或逐步执行：

```bash
python -m unittest discover -s tests -v
python -m kmb.cli validate --strict --suite suites/core-zh.yaml
python -m kmb.cli validate --strict --suite suites/core-zh-expanded.yaml
python -m kmb.cli validate --strict --suite suites/adversarial/extended.yaml
python -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-kylinbot-process.yaml \
  --suite suites/core-zh.yaml --out runs/compare --seed 42 --retries 0 --timeout 30
```

现代 pip 可使用 `python -m pip install .` 安装 CLI。**本阶段结论以本机开发与测试为准**；openKylin 实机迁移验收后置。仓库中 `runs/openkylin-validation-*`、`runs/deb-lifecycle-*` 与 `0.2.0+release7` 为历史归档记录，迁移后需在目标机重跑验收命令，详见 `docs/release-freeze.md` 与 `tasks/todo.md`。

输出包括：

- `evidence.jsonl`：每个用户消息、记忆写入/更新/抑制、记忆调用、助手输出、任务动作、工具/文件结果、模型请求/响应和异常事件。
- `result.json` / `result.md`：逐案例检查、失败类型、理由、六维指标和总分。
- `radar.svg`：六维雷达图；对比命令还生成 `comparison.json`、`comparison.md`。
- `comparison.html`：离线可打开的跨 Agent 报告，可折叠查看每个案例、失败类型和证据引用。

本地浏览器工作台（CLI 仍保持完整可用）：

```bash
python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .
```

打开 `http://127.0.0.1:8765/` 后，可从真实 `configs/` 选择两个 Agent、运行相同套件并查看 `runs/` 中的结果、证据和失败下钻。工作台默认突出 Grok 与 DeepSeek 两个云端提供商，同时支持在“API 配置”页新增其他 OpenAI-compatible Chat Completions API 档案；标准 API、记忆开启和无记忆基线是同一提供商的不同运行模式。本地服务会在启动或刷新时安全读取 `~/.config/kmb/credentials.env`（仅接受权限 `600` 的文件），包括新增档案 `api_key_env` 引用的变量；API Key 不进入浏览器、配置 YAML 或结果文件。Windows 服务不会自动读取 openKylin VM 的凭据，需在 VM 内启动或通过受控 SSH 隧道访问；详细页面、白名单和复现方式见 [`docs/workbench.md`](docs/workbench.md)。

生命周期与安全边界扩展套件：

```bash
python -m kmb.cli validate --strict --suite suites/lifecycle/innovation.yaml
python -m kmb.cli run --agent configs/agent-reference.yaml --suite suites/lifecycle/innovation.yaml --out runs/lifecycle-innovation
```

该套件在统一包装层下检查事实的 `persistence`、`sensitivity`、`scope`、`version`、TTL 和 `provenance`，并覆盖受控 `restart-boundary`、路径/措辞/相似实体/token/作用域变形组。动作评分要求沙箱文件、内容、SHA256 和退出码等真实工件证据；模型文本声明不能替代动作结果。报告中的变形组会列出基准/变体、不变量和违反证据。

套件校验与查看：

```bash
python -m kmb.cli validate --strict --suite suites/core-zh.yaml
python -m kmb.cli list-cases --suite suites/adversarial/core.yaml
```

项目内还提供结构一致的英文套件：`suites/core-en.yaml` 和
`suites/adversarial/core-en.yaml`。套件案例和 Prompt 为本项目重新编写，
不等同于参考项目数据集或 Prompt 的授权。

Linux/openKylin 可执行演示：

```bash
bash scripts/run_demo.sh
```

赛事环境预检与结果校验：

```bash
python scripts/env_probe.py --json
python scripts/verify_run.py runs/demo/reference --strict
```

openKylin 或其他 Debian 系环境可使用脚本管理本地虚拟环境（脚本不会下载 Agent，也不会保存凭据）：

```bash
bash scripts/install_local.sh
bash scripts/uninstall_local.sh
```

离线环境需先在与目标 openKylin 架构、Python ABI 相同的准备机上生成 wheelhouse，再复制到目标机：

```bash
bash scripts/build_offline_wheelhouse.sh /path/to/offline-wheelhouse python3
KMB_OFFLINE_WHEELHOUSE=/path/to/offline-wheelhouse bash scripts/install_local.sh python3
```

离线 wheelhouse 的兼容性需要在目标机实测，不能由 Windows 或其他 Linux 的构建结果推断。

正式接入两款真实 Agent 后，使用：

```bash
bash scripts/run_acceptance.sh configs/agent-a.yaml configs/agent-b.yaml
```

对于 Grok/NewAPI 与 DeepSeek 的 OpenAI 兼容 API，可参考：

```bash
# Windows PowerShell
$env:GROK_API_KEY = "从控制台获取的新密钥"
$env:DEEPSEEK_API_KEY = "从控制台获取的新密钥"
python -m kmb.cli compare --agents configs/agent-grok.yaml configs/agent-deepseek.yaml --suite suites/core-zh.yaml --out runs/real-agents --retries 1 --seed 42 --timeout 180
```

HTTP 适配器只记录 API 返回的可观察证据；普通文本回答不能被推断成记忆写入或读取。若 Agent 没有导出记忆轨迹，请先用 wrapper 转换为 `docs/evidence-protocol.md` 中的 `kmb_evidence` JSONL/数组。

生命周期扩展的 `restart-boundary` 只表示受控 Agent/包装层重建检查点，不表示真实系统重启；用户切换、离线切换和系统级权限变化需要独立的受控 openKylin 执行器，当前 CLI 不会用普通进程重建冒充这些验证。

Grok/NewAPI 配置见 `configs/agent-grok.yaml`。运行前设置 `$env:GROK_API_KEY`，默认调用 `grok-4.6`；将配置中的 `model` 改为 `grok-4.5` 可切换版本。

模型没有原生记忆工具时，使用透明包装层配置：

```bash
python -m kmb.cli compare --agents configs/agent-grok-memory.yaml configs/agent-deepseek-memory.yaml --suite suites/core-zh.yaml --out runs/controller-compare --timeout 180 --retries 1 --seed 42
```

包装层事件和模型事件带有不同 `source` 与 `evidence_class` 标记；结果和报告会列出“观测模式、原生记忆事件、包装层记忆事件、未证实模型自述”。包装层分数只能表述为“模型后端 + 外部控制器”的系统级长期记忆行为，不能表述为模型原生长期记忆能力。动作结果只写入项目内 `runs/controller-actions/<agent>/<case>/`，不同 Agent 不会互相覆盖。

如需加入同一真实后端的无记忆对照，可使用 `type: memory_disabled` 配置。它仍逐案例调用真实 API 并参加评分，但不保存外部记忆、不执行依赖记忆的动作，并记录 `no_memory_baseline` 事件、recall miss 和阻断原因：

```bash
python -m kmb.cli compare \
  --agents configs/agent-grok-memory.yaml configs/agent-grok-no-memory.yaml \
  --suite suites/core-zh.yaml --out runs/grok-wrapper-vs-no-memory \
  --run-id wrapper-vs-no-memory --seed 42 --retries 1 --timeout 180
```

这条对照的得分描述为“真实模型后端 + 启用/关闭外部包装层”的系统级差异，不能作为模型原生长期记忆能力证明。

## Debian 发布包

在 openKylin 或 Debian 构建机执行 `bash scripts/build_deb.sh dist`，生成
`dist/kylin-memory-bench_<version>_all.deb`。包中包含 CLI、默认配置、核心/对抗套件和最小报告能力，明确排除 API Key、虚拟环境、缓存、研究仓库和 `runs/`。生命周期命令：

```bash
bash scripts/install_deb.sh dist/kylin-memory-bench_0.2.0_all.deb
bash scripts/verify_deb.sh /tmp/kmb-deb-smoke
bash scripts/upgrade_deb.sh dist/kylin-memory-bench_<new-version>_all.deb
bash scripts/uninstall_deb.sh
```

`verify_deb.sh` 先运行包内最小离线测试，再使用 reference/flawed 校验包内 CLI/评分链路，不是正式真实 Agent 结果。当前项目级 LICENSE 尚未由负责人选择，`.deb` 在完成许可证决策前仅作为技术验收包使用，详见 `docs/deb-release.md`。

具备 `sudo/root` 的 openKylin 终端可用 `bash scripts/record_deb_lifecycle.sh` 一次性记录安装、升级、验证、卸载和残留检查。桌面演示录屏命令见 `docs/demo-script.md`；无图形会话时不得把脚本预检当作已录制视频。

重复运行稳定性可用只读聚合工具生成：

```bash
python scripts/aggregate_repeats.py runs/openkylin-validation-20260906/grok-no-memory-repeats --out runs/openkylin-validation-20260906/grok-no-memory-repeats/summary.json
```

两个真实后端的重复批次可只读汇总为 JSON、Markdown、HTML 和 SVG：

```bash
python scripts/aggregate_stability.py \
  --grok-summary runs/openkylin-validation-20260906/grok-no-memory-repeats/summary.json \
  --deepseek-summary runs/openkylin-validation-20260908/deepseek-no-memory-repeats/summary.json \
  --out runs/openkylin-validation-20260908/stability/dual-agent-stability.json
```

创新套件 memory-enabled 的 Grok/DeepSeek 五批统计和系统级边界检查见
[`docs/innovation-stability-report.md`](docs/innovation-stability-report.md)。创新统计会保留
真实 runtime error 批次，并输出变形组通过率、生命周期状态转换正确率、实际动作成功率、
证据链完整率和安全相关失败类型；这些指标仍只描述“模型后端 + 外部包装层”的系统级行为。创新套件 no-memory 五批双 Agent 对照见 `runs/openkylin-validation-20260909/innovation-no-memory/`，Grok 的连接拒绝/超时失败样本也保留并纳入统计。

## 接入其他智能体

实现 `kmb.agents.AgentAdapter` 的 `run(case) -> List[EvidenceEvent]`，把智能体的对话、记忆存取、工具调用和文件结果映射为统一事件即可。真实 Agent 的外部 API、进程或 GUI 操作应在适配器内完成；评分器不读取模型内部状态，也不依赖 LLM 裁判。

**openKylin 生态进程适配器（本机已跑通）**：

```bash
python -m kmb.cli run \
  --agent configs/agent-kylinbot-process.yaml \
  --suite suites/core-zh.yaml \
  --out runs/kylinbot-demo --seed 42 --retries 0 --timeout 30
```

配置类型 `command`：以子进程启动 `scripts/openkylin_ecosystem_agent.py`（stdin 案例 JSON → stdout 证据 JSONL，`source=process`）。迁入 openKylin 时只需把 `command` 指向原生 KylinBot/kylin-agent 包装，证据协议保持不变。

## 当前边界

内置 `reference` 和 `flawed` 是离线、确定性的演示基线，用于验证 Benchmark 能区分正确行为与错误持久化/混淆/复用。它们不是赛事最终指定的两款真实 Agent，结果会标为 `simulated_baseline`。`kylinbot-process` 是本机已跑通的 openKylin 生态**进程适配器**（`source=process`，系统级）。历史目录 `runs/openkylin-validation-*` 记录过 VM 上的 Grok/DeepSeek 与 wrapper/no-memory 对比；两款云 API 未导出原生记忆状态，结论只能表述为系统级行为。桌面演示视频尚未录制；openKylin 实机迁移验收后置。

详细流程、评分规则和复现说明见 [`docs/solution.md`](docs/solution.md)。
外部 Agent 的 JSONL 证据格式见 [`docs/evidence-protocol.md`](docs/evidence-protocol.md)。
真实 Agent 信息和待确认字段见 [`docs/agent-candidates.md`](docs/agent-candidates.md)。
许可证审计见 [`docs/license-audit.md`](docs/license-audit.md)，数据与 Prompt 来源声明见 [`docs/dataset-provenance.md`](docs/dataset-provenance.md)，openKylin 实机执行清单见 [`docs/openkylin-validation-runbook.md`](docs/openkylin-validation-runbook.md)。
项目级许可证尚待负责人/法务确认，候选方案与落地检查见 [`docs/license-decision.md`](docs/license-decision.md) 和 `LICENSE-MIT-CANDIDATE.txt`；根目录 `NOTICE` 不授予再分发权利，第三方边界见 `THIRD_PARTY_NOTICES.md`。
发布版本、哈希、权威运行目录和最终非视频命令见 [`docs/release-freeze.md`](docs/release-freeze.md)。
历史运行的来源重建命令见 `scripts/enrich_run_provenance.py`；它只读复制证据并生成新报告，不覆盖原始运行目录。
