# openKylin 智能体长期记忆 Benchmark - 项目上下文包

> 用途：将本文件整体发给协作对话，或让协作对话先阅读本文件再领取具体子任务。
> 
> 本文分为“官方硬要求”和“当前建议方案”。后者可以被合理挑战或调整，前者不得遗漏。

## 1. 一句话说明

我们准备参加 **2026 上海开源软件应用创新大赛 - 开源 AI 工具赛道**，企业命题为：

> 面向 openKylin 操作系统的智能体长期记忆自动化评测 Benchmark 设计。

目标不是做一个带记忆的聊天机器人，而是做一个在 openKylin 上运行的、可复现的工具：它接入不同智能体，收集智能体运行证据，自动判断其长期记忆是否正确、是否应当遗忘，并输出可解释的多维对比结果。

## 2. 官方任务书：硬要求

### 2.1 必须评测的六类能力

1. **长期保持**：应保留的信息是否被稳定记住，并在之后被使用。
2. **记忆调用**：后续交互中能否正确调用相关信息。
3. **动态更新**：新信息是否正确覆盖或修正旧信息。
4. **相近区分**：能否识别相似信息之间的差异，避免串扰。
5. **边界识别**：临时、敏感、风险指令、噪声等不应长期保留或复用的信息，是否被正确识别。
6. **任务复用**：在实际任务执行中，能否合理使用历史信息，而不只是回答问题。

### 2.2 官方交付物

- **方案说明文档**：测试目标、前提、数据生成、验证用例、结果收集、自动评分完整流程。
- **数据集设计**：可扩展的数据结构，覆盖不同记忆样本与验证项。
- **样例数据与样例结果**：少量任务、运行证据、评分结果，证明方案可执行。
- **可复现材料**：代码、配置、脚本、README，且能在 openKylin 直接编译与运行。
- **工具化封装**：在 openKylin 上一键运行的 CLI 或 GUI；支持导入不同智能体配置进行批量对比。`.deb` 包为官方建议项。
- **真实环境演示视频**：在 openKylin 桌面环境中，对至少两款不同智能体运行评测，并产出多维对比雷达图；官方建议视频时长 3-5 分钟。

### 2.3 官方评审权重

| 维度 | 权重 | 得分关键 |
| --- | ---: | --- |
| 任务定义与通用性 | 15% | 支持不同智能体和不同证据来源；能融入 openKylin 生态。 |
| 数据设计质量 | 25% | 多种长期记忆情形、证据来源、区分度与扩展空间。 |
| 自动评分能力 | 25% | 少人工、结构化、可解释；区分正确、遗漏、混淆、错误持久化、错误复用。 |
| 稳定性与可复现性 | 15% | 同输入结果稳定；批量运行与追踪；openKylin 标准环境可复现。 |
| 指标完整性 | 10% | 多维指标，而不是单一总分。 |
| 创新性与工程可落地性 | 10% | 有创新且可落地，对 openKylin 有针对性适配。 |

评审尤其关注：能否基于**真实智能体运行证据**自动完成评测，并稳定区分不同模型或系统的长期记忆能力。

## 3. 当前建议方案（非官方规定）

### 3.1 暂定项目定位

工作名：`KylinMemoryBench`（名称可改）。

一个面向智能体长期记忆的开源评测框架，包含：

```text
声明式测试场景 -> Agent 适配器 -> 执行与证据采集 -> 规则/裁决评分 -> 指标聚合 -> 可视化报告
```

核心输出不是“模型好不好”的主观结论，而是一份可追溯结果：某个智能体在哪个场景、依据哪些对话/记忆/工具轨迹/文件证据，被判定为正确、遗漏、混淆、错误持久化或错误复用。

### 3.2 MVP 需要做成的闭环

1. 用 YAML/JSON 定义测试案例和期望行为。
2. 通过统一 `AgentAdapter` 接入至少两种智能体或记忆实现。
3. 记录结构化证据：对话、显式记忆记录、工具调用、动作轨迹、文件产物、运行元数据。
4. 以可复现的确定性规则为主完成评分；语义判定可作为辅助，但**不能只依赖不可复现的 LLM 裁判**。
5. 输出每条用例的判定理由，以及六类能力的分项指标、总分、失败类型分布和雷达图。
6. 提供一键 CLI 和批量对比，例如：

```bash
kmb run --agent configs/agent-a.yaml --suite suites/core-zh.yaml
kmb compare --agents configs/agent-a.yaml configs/agent-b.yaml --suite suites/core-zh.yaml
```

### 3.3 可行的创新点候选

这些是候选方向，优先选 1-2 个做深，不要全部堆砌：

- **证据图谱评分**：把事实、记忆条目、对话、工具调用和文件产物连接为可追溯的证据图，而非只检查最终自然语言回答。
- **记忆状态机**：对每个可记忆事实定义 `write / retain / revise / suppress / reuse` 的期望状态转移，可严格识别“更新失败”和“错误持久化”。
- **反事实干扰生成器**：自动构造相似实体、时间冲突、撤销信息、敏感信息和提示注入，专门检测混淆与边界失守。
- **行动验证器**：通过工具调用参数、生成文件内容、任务结果等验证记忆是否真正被复用，而不是只验证回答中有没有提到。
- **跨 Agent 证据规范**：定义开放的 JSONL/JSON Schema，使不同智能体无需暴露内部实现也能被统一评测。

## 4. 明确的边界：不要做偏

- 不做通用聊天助手、RAG 知识库或新的 Agent 框架；它们只能是被测对象或演示手段。
- 不以“回答看起来合理”作为唯一评测标准。
- 不把单个模型的单次效果当成 Benchmark；需要批量运行、固定随机种子/配置和稳定比较。
- 不只做一个总分；六类能力和失败类型都必须可查看。
- 不把演示截图当作 openKylin 适配；最终必须在真实 openKylin 环境可运行。

## 5. 建议的工程模块

```text
kylin-memory-bench/
  packages/
    core/                 # 用例模型、证据模型、指标聚合
    runner/               # 调度执行、重试、结果追踪
    adapters/             # 不同 Agent / 记忆后端的适配器
    scorers/              # 确定性规则、证据验证、可选语义裁判
    reporters/            # JSON、Markdown/HTML、雷达图
    cli/                  # kmb 命令行工具
  suites/
    core-zh/              # 六类能力的中文核心用例
    adversarial/          # 相似干扰、冲突更新、敏感与风险信息
  configs/
  examples/
  docs/
  scripts/
```

技术栈尚未最终决定。优先选择 Python CLI 与可移植 JSON/YAML 格式；需要 GUI 时，先让 CLI 保持完整可用，GUI 只作为报告查看层。

## 6. 必须尽早确认的决策

以下问题尚未确认。协作对话不能擅自把猜测当事实，应给出推荐和取舍：

1. 使用哪个 openKylin 版本，采用实体机、虚拟机还是官方镜像。
2. 用哪两款可实际运行的智能体作为被测对象，以及它们如何导出运行证据。
3. 是否使用云端模型 API；核心评分应尽量不依赖付费或不稳定服务。
4. 采用何种开源许可证及仓库托管位置。
5. 第一版的案例规模、语言范围和指标定义。

## 7. 建议的第一阶段目标

先完成一个能跑通的最小端到端版本，而不是先做网页或大规模数据集：

1. 写出数据模型和 6 个最小案例，每类能力 1 个。
2. 实现一个受控的参考 Agent/记忆后端，以及一个待测适配器。
3. 采集统一 JSONL 证据并完成确定性评分。
4. 输出分项结果和雷达图。
5. 接入第二个 Agent，证明 Benchmark 能区分两者。
6. 再扩展数据集、报告、CLI 安装和 openKylin 打包。

## 8. 发给其他对话的通用启动提示词

将以下内容连同本文件发送给协作对话，并替换方括号中的角色：

```text
你是本项目的[角色，例如：评测设计负责人 / Python 架构师 / openKylin 部署负责人 / 开源治理负责人]。

我们正在参加 2026 上海开源软件应用创新大赛的“开源 AI 工具赛道”，企业命题为“面向 openKylin 操作系统的智能体长期记忆自动化评测 Benchmark 设计”。请先完整阅读下方项目上下文包。它区分了官方硬要求与当前建议方案：官方硬要求不可忽略，建议方案可以提出有依据的改进。

你的任务是：[在这里写一个边界明确的任务]。

请不要把项目做成聊天机器人、RAG 应用或单一模型评测脚本。评测必须依赖真实智能体运行证据，能自动且可解释地区分正确记忆、遗漏、混淆、错误持久化和错误复用；最终应能在 openKylin 上以 CLI 或 GUI 运行，并对至少两款智能体生成多维对比结果。

先给出：1) 你对任务的理解；2) 交付物和验收标准；3) 最小可行方案及主要风险。未经确认不要擅自扩展范围或假定尚未确定的技术选型。
```

## 9. 官方来源

- 赛事总页：https://www.oschina.net/os2026/
- 企业命题任务书 PDF：https://apiv1.oschina.net/api/files/fhhc7e8z6no3gyt/w9qliatd2m6lgs8/ai_open_kylin_open_kylin_benchmark_XaCQyZepC8.pdf

## 10. 赛事可验收推进记录（2026-09-02）

本轮重新读取并核对了当前工作区。目录不是 Git 仓库，因此本记录以实际文件、脚本输出和既有运行产物为依据，不使用 Git 状态推断变更。

### 已存在且已核对的实现

- `kmb/models.py` 已为 `EvidenceEvent` 增加 `source` 和 `evidence_class`，并拒绝把普通模型文本或未验证 tool call 当作原生记忆状态。
- `kmb/agents.py` 已包含 OpenAI 兼容 HTTP 适配器、命令/Replay 适配器和透明 `memory_controller` 包装层；包装层事件标记为 `source=wrapper`，模型观察标记为 `source=model`。
- `kmb/runner.py`、`kmb/scoring.py` 和 `kmb/report.py` 已将证据来源、可观测模式、失败理由和证据引用写入 JSON/Markdown/HTML 结果。
- CLI 已提供 `run`、`compare`、`validate`、`list-cases`；核心中文套件和对抗套件各包含六类能力案例。
- `scripts/env_probe.py`、`scripts/run_acceptance.sh`、安装/卸载脚本、离线 wheelhouse 脚本和运行校验脚本已存在。

### 双 Agent 证据状态

- `runs/real-compare-v2/` 和 `runs/real-compare-v2-provenance/` 保留 Grok 4.6 与 DeepSeek v4 flash 的历史真实 HTTP 运行证据；本轮未重新调用模型，不能把这些文件描述为本轮新运行。
- `runs/controller-compare-v3/` 和 `runs/controller-compare-v3-provenance/` 保留两款模型加透明外部控制器的历史真实运行证据。其 `memory_*`/`action` 事件来自 `source=wrapper`，只支持“系统级包装层行为”结论，不支持模型原生长期记忆结论。
- 当前进程未发现 `GROK_API_KEY` 或 `DEEPSEEK_API_KEY` 环境变量，因此本轮不能新增真实 API 运行；不得生成或伪造密钥、响应或分数。

### openKylin 状态

- 当前主机仍为 Windows 10 AMD64，Python 3.9.5，PyYAML 6.0.3；未发现可访问的 openKylin 实机、虚拟机、官方镜像、容器介质或可用虚拟化工具。
- `scripts/env_probe.py --require-openkylin --json` 的门禁结果仍应为失败（退出码 2）；该结果只能说明当前主机不满足 openKylin 条件，不能替代实机/虚拟机验证。
- 因缺少真实 openKylin 环境，安装、双 Agent 正式验收、证据导出、报告生成和卸载尚未取得 openKylin 运行证据。后续应在真实 openKylin 实机/虚拟机中按 `docs/openkylin-validation-runbook.md` 执行并保存版本、架构、命令、退出码和文件哈希。

### 本轮待确认假设与阻塞

1. 待确认假设：赛事允许使用 Grok/DeepSeek 云 API，且运行时网络、额度和数据脱敏策略满足赛事要求；影响真实双 Agent 复测和演示。
2. 待确认假设：最终参评 Agent 可接受“模型后端 + 外部控制器”作为系统级被测对象；影响包装层分数的赛事表述，报告必须保留能力限制。
3. 客观阻塞：当前没有可访问的 openKylin 实机/虚拟机或介质，无法在本轮完成官方要求的真实 openKylin 验证。

### 本轮实际验证（2026-09-02，未重新调用模型）

除正式验收脚本外，以下命令均在 `E:\上海开源软件应用创新大赛\.venv-kmb-system` 中执行；正式验收脚本本次未设置 `KMB_PYTHON`，实际自动选用了 `D:\Programs\Python\Python39\python.exe`，且在 openKylin 门禁处提前退出：

| 命令 | 退出码 | 实际结果 |
|---|---:|---|
| `.venv-kmb-system\\Scripts\\python.exe -m unittest discover -s tests -v` | 0 | 33 tests passed |
| `.venv-kmb-system\\Scripts\\python.exe -m compileall -q kmb scripts tests` | 0 | 编译通过 |
| `... -m kmb.cli validate --strict --suite suites/core-zh.yaml` | 0 | 6 cases valid |
| `... -m kmb.cli validate --strict --suite suites/adversarial/core.yaml` | 0 | 6 cases valid |
| `... scripts/verify_run.py runs/real-compare-v2-provenance/grok-api --strict` | 0 | 6 cases，28 条证据，结构有效 |
| `... scripts/verify_run.py runs/real-compare-v2-provenance/deepseek-api --strict` | 0 | 6 cases，28 条证据，结构有效 |
| `... scripts/verify_run.py runs/controller-compare-v3-provenance/grok-memory-controller --strict` | 0 | 6 cases，70 条证据，结构有效 |
| `... scripts/verify_run.py runs/controller-compare-v3-provenance/deepseek-memory-controller --strict` | 0 | 6 cases，70 条证据，结构有效 |
| `... scripts/env_probe.py --json` | 0 | Windows 10/AMD64，Python 3.9.5，PyYAML 6.0.3，工作区余量约 85.3 GB |
| `... scripts/env_probe.py --require-openkylin --json` | 2 | `status=failed`，`openkylin.ok=false`；门禁按预期阻止非 openKylin 主机 |
| `... -m kmb.cli compare --agents configs/agent-grok.yaml configs/agent-deepseek.yaml ... --out runs/blocked-api-check-20260902 --retries 1` | 0 | 缺少密钥时两 Agent 均完成 6 案例错误收敛，结果总分 0；未发出模型请求 |
| `... scripts/verify_run.py runs/blocked-api-check-20260902/grok-api --strict` | 0 | 6 cases，12 条 `runtime_error` 证据，结构有效 |
| `... scripts/verify_run.py runs/blocked-api-check-20260902/deepseek-api --strict` | 0 | 6 cases，12 条 `runtime_error` 证据，结构有效 |
| `bash scripts/run_acceptance.sh configs/agent-grok.yaml configs/agent-deepseek.yaml suites/core-zh.yaml runs/formal-blocked-20260902`（实际解释器：`D:\\Programs\\Python\\Python39\\python.exe`） | 2 | 正式验收在 `--require-openkylin` 门禁失败，未调用 API、未生成验收评分 |

错误路径产物位于 `runs/blocked-api-check-20260902/`，仅记录“环境变量未设置”的运行错误，不是模型结果。当前环境变量检查只记录变量是否存在，未输出任何密钥值。

## 11. 本轮 VM 接入推进记录（2026-09-05）

### 批次 1：工作区与 VM 通道核对

- 实际读取：`openKylin-Benchmark-项目上下文包.md`、`docs/openkylin-validation-runbook.md`、`docs/openkylin-environment-build-20260902.md`、`docs/openkylin-failure-triage-20260902.md`、CLI/Agent/模型/评分器代码和 `runs/` 最新产物。
- 实际命令：PowerShell 并行执行 `Get-ChildItem`、`Get-Command VBoxManage,vmrun,qemu-system-x86_64,virsh,podman,docker,wsl,ssh,scp`、`Get-Process`、读取 QEMU 元数据/串口/stderr 日志；通过 CUA `cua.getState()` 检查当前桌面应用与浏览器状态。
- 实际结果：工作区存在官方 `openKylin-Desktop-V2.0-SP2-20260813-x86_64.iso`、40 GiB `openkylin.qcow2`、`launch-qemu.ps1` 和 QEMU 11.1 元数据；当前未发现运行中的 QEMU、VirtualBox 或 VMware 进程，CUA 未发现可交互 VM 窗口。既有启动记录为 WHPX 超时退出码 124、TCG 退出码 1，串口无 openKylin 登录证据。
- 环境信息：当前主机 Windows 10/11 系列 AMD64；工作区 E 盘约 85 GB 可用；QEMU 可执行文件记录在 `C:\Program Files\qemu\`，但本轮 `Get-Command` 未在 PATH 中发现；当前进程未发现 `GROK_API_KEY`/`DEEPSEEK_API_KEY`。
- 状态：**openKylin VM 尚未取得可登录、可执行命令的证据**；ISO/qcow2 仅证明介质和准备产物存在，不能视为 openKylin 验证完成。
- 客观阻塞：需要已安装并可登录的 VM，或允许启动 QEMU 并完成桌面安装/SSH/串口通道；同时真实 API 运行需要进程环境中的密钥，但不得把密钥写入文件或日志。
- 待确认假设：用户所称“已有 openKylin 虚拟机”可能是未在当前桌面会话暴露的远程/其他虚拟化实例；当前只能依据本机可见进程、文件和日志判断。
- 下一步：检查 QEMU 绝对路径和 qcow2 状态，尝试无损启动已有 qcow2；若不能获得 VM 内 `/etc/os-release`，保留失败证据并不宣称兼容性。

### 批次 2：QEMU 介质与启动通道复核

- 实际命令：读取 `runs/openkylin-validation-20260902/qemu-x86_64/launch-qemu.ps1`、`vm-metadata.json`、`boot-*.metadata.json`、`boot-*.stderr.log`；检查 `C:\\Program Files\\qemu\\qemu-system-x86_64.exe`、`qemu-img.exe`；读取 qcow2 文件属性。
- 实际结果：ISO 文件和启动脚本存在，但当前 `qemu-system-x86_64.exe` 与 `qemu-img.exe` 路径均不存在；`C:\\Program Files\\qemu` 仅剩辅助程序。`openkylin.qcow2` 大小约 197,632 字节，未形成已安装系统。历史元数据显示 WHPX 启动曾超时退出码 124、TCG 退出码 1，不能作为本轮 VM 内验证。
- 状态：**没有可启动/可登录的 openKylin VM 通道**；本轮未执行安装、未读取 VM 内 `/etc/os-release`，也未调用任何 API。
- 结果文件：`runs/openkylin-validation-20260902/qemu-x86_64/vm-metadata.json`、`boot-whpx.metadata.json`、`boot-tcg.metadata.json`、`boot-whpx.stderr.log`、`boot-tcg.stderr.log`、`qemu-x86_64/openkylin.qcow2`。
- 客观阻塞：QEMU 核心可执行文件缺失且 qcow2 为空；恢复方式需要重新安装 QEMU 或提供已安装 openKylin VM，并完成交互式安装/登录通道。不能在当前状态下生成 openKylin 环境、Grok、DeepSeek 或双 Agent 的实机结果。
- 待确认假设：用户所称已有 VM 不是当前工作区这份 qcow2；若确有其他 VM，其连接地址/客户端必须在当前主机可见后才能自动执行。

### 批次 3：主机其他虚拟化/远程通道发现

- 实际命令：递归检查 `C:\\Program Files`、`C:\\Program Files (x86)`、`D:\\`、`E:\\` 中的 QEMU/VMware/VirtualBox 核心程序和 `.vmx`、`.vbox`、`.vhdx`、`.vdi`、`.vmdk`、大于 100 MB 的 `.qcow2/.img`；查询 VMware/Hyper-V 服务、网卡、ARP；检查项目文档和运行产物中的 SSH/VM 地址线索。
- 实际结果：未发现可执行的 `qemu-system-x86_64.exe` 或 `qemu-img.exe`；`C:\\Program Files (x86)\\VMware` 仅有 VMware VIX 文件，未发现 Workstation 客户端或 `.vmx`；VMware 授权/NAT/DHCP 服务在运行，但 ARP 仅显示网关（未发现 openKylin 客户机地址）；项目目录外未发现其他可用虚拟磁盘。
- 状态：当前没有本机可直接登录的 openKylin VM 或 SSH 通道；未执行 API 请求和 VM 内命令。
- 客观阻塞：需要恢复/安装虚拟化核心并完成 openKylin 安装，或提供当前主机可见的已安装客户机和连接方式。便携 QEMU 只能作为新的安装准备，仍需要桌面安装交互和系统登录证据。
- 待确认假设：VM 可能位于未挂载磁盘、其他主机或需要用户会话启动的 VMware Workstation；这些状态不能由当前非交互检查推断。

### 批次 4：VMware 安装位置与客户机清单发现

- 实际命令：查询卸载注册表、递归检查 `E:\\VMware`、查找 `vmware.exe`/`vmrun.exe`/`*.vmx`，查询 VMware 服务与进程。
- 实际结果：注册表确认 VMware Workstation 17.5.0；实际程序位于 `E:\\VMware\\vmware.exe` 和 `E:\\VMware\\vmrun.exe`，VMware Authorization/NAT/DHCP 服务运行。此前 PATH 检查未显示它们是因为安装目录未加入 PATH。当前磁盘扫描仍未发现 openKylin `.vmx` 文件或运行中的客户机。
- 状态：发现可用于进一步检查的 VMware 管理通道，但尚未证明存在已安装 openKylin 客户机；本批次未启动客户机、未执行 VM 内命令、未调用 API。
- 结果依据：`E:\\VMware\\vmware.exe`、`E:\\VMware\\vmrun.exe`、注册表 `VMware Workstation 17.5.0`、VMware 服务状态输出。
- 下一步：启动已有 VMware Workstation UI，读取其最近/库存客户机；若发现 openKylin，使用 UI 或 `vmrun` 获取路径和运行状态后再进入 VM 内验证。

### 批次 5：发现用户已有 openKylin VMware 客户机

- 实际命令：启动 `E:\\VMware\\vmware.exe`；执行 `E:\\VMware\\vmrun.exe -T ws list`；读取 `C:\\Users\\123\\AppData\\Roaming\\VMware\\inventory.vmls`；检查 `D:\\openKylin-VM` 内容和 VMware 进程。
- 实际结果：inventory 明确记录 `D:\\openKylin-VM\\openKylin.vmx`，显示名 `openKylin 2.0 SP2`；目录包含 `openKylin.vmdk`（约 37.9 GB）、`openKylin.iso`（约 8.3 GB）、NVRAM、VMware 日志和近期锁目录。VMware Workstation 17.5.0 窗口进程已启动，但 `vmrun list` 返回 `Total running VMs: 0`，说明客户机当时未运行。
- 状态：已确认真实 openKylin VM 的配置路径，但尚未读取客户机内部系统信息；本批次未调用 Grok/DeepSeek API。
- 结果依据：`C:\\Users\\123\\AppData\\Roaming\\VMware\\inventory.vmls`、`D:\\openKylin-VM\\openKylin.vmx`、`D:\\openKylin-VM\\openKylin.vmdk`、`D:\\openKylin-VM\\vmware.log`、`vmrun list` 输出。
- 下一步：启动 `D:\\openKylin-VM\\openKylin.vmx`，等待客户机网络/登录就绪；优先使用 VMware Tools 或 SSH 获取 `/etc/os-release`、`uname -a` 和 Python 信息。若启动失败，保留 vmware.log、vmrun stderr 和退出码。

### 批次 6：启动已发现的 openKylin VMware 客户机

- 实际命令：读取 `D:\\openKylin-VM\\openKylin.vmx`；执行 `E:\\VMware\\vmrun.exe -T ws start D:\\openKylin-VM\\openKylin.vmx gui`。
- 实际结果：VMware 配置中的 `guestInfo.detailed.data` 已记录 `distroName='openKylin'`、`prettyName='openKylin 2.0 SP2'`、`architecture='X86'`、`kernelVersion='6.6.0-25-generic'`；`vmrun start` 退出码 0。此字段是 VMware 保存的客户机识别元数据，不等同于本轮 VM 内命令证据；客户机刚启动，尚未完成登录/命令执行。
- 状态：真实 openKylin 客户机已发起启动；等待获取 VM 内 `/etc/os-release`、`uname -a`、Python/pip 和 CLI 证据。
- 结果依据：`D:\\openKylin-VM\\openKylin.vmx`、`vmrun` 退出码 0、VMware 客户机窗口/进程和 `D:\\openKylin-VM\\vmware.log`。
- 下一步：通过 VMware UI 登录客户机；如 VMware Tools 已安装，尝试 `vmrun readVariable`/`runProgramInGuest`，否则使用 GUI 终端或客户机网络 SSH。

### 批次 7：客户机启动状态确认

- 实际命令：执行 `E:\\VMware\\vmrun.exe -T ws list`；查询 `vmware`/`vmware-vmx` 进程；读取 `D:\\openKylin-VM\\vmware.log` 尾部。
- 实际结果：`vmrun list` 返回 `Total running VMs: 1` 和 `D:\\openKylin-VM\\openKylin.vmx`；`vmware-vmx` 进程已运行。日志显示 VMware Tools 状态变化为 running、VMXNET3 网卡激活、客户机 Mesa 图形栈和 openKylin GuestInfo 已上报。
- 状态：VM 已启动并被 VMware 识别，但本批次尚未在客户机内执行命令或读取 `/etc/os-release`；未调用 Grok/DeepSeek API。
- 结果依据：`vmrun list` 退出码 0、`vmware-vmx` 进程、`D:\\openKylin-VM\\vmware.log`。
- 下一步：尝试 `vmrun readVariable`、`getGuestIPAddress` 和 VMware Tools 客户机命令；若需要登录凭据且不可安全获得，则记录为阻塞，不在日志中写入密码。

### 批次 8：客户机网络与无凭据 VMware Tools 检查

- 实际命令：`E:\\VMware\\vmrun.exe -T ws getGuestIPAddress D:\\openKylin-VM\\openKylin.vmx -wait`、`checkToolsState`、`listProcessesInGuest`（无凭据）、`readVariable`（无效变量参数）；对 `192.168.182.129` 的 22/80/443/3389/5900/2222/2200/8080/8000/5000/3000 端口执行 `Test-NetConnection`；尝试 `captureScreen`。
- 实际结果：客户机 IP 为 `192.168.182.129`，`getGuestIPAddress` 退出码 0；Tools 状态为 `running`，退出码 0；所有探测端口均未开放。`listProcessesInGuest` 和 `captureScreen` 均因“此虚拟机不允许执行匿名客户机操作，必须先调用 VixVM_LoginInGuest”失败；没有客户机用户名/密码，因此未尝试猜测或记录凭据。
- 状态：VM 已运行且有 VMware Tools/IP 证据，但仍未取得客户机内 `/etc/os-release`、`uname -a`、Python 或 CLI 结果；本批次未调用 Grok/DeepSeek API。
- 结果依据：`vmrun` 输出、`D:\\openKylin-VM\\vmware.log`、客户机 IP/端口探测结果。未生成屏幕文件，因为 VMware 拒绝匿名捕获。
- 客观阻塞：VMware Tools 客户机操作和 SSH 均需要客户机认证；当前会话没有可安全使用的客户机登录凭据，不能完成 VM 内安装或运行。
- 待确认假设：客户机桌面可能已登录，但无法通过无凭据接口证明；GuestInfo 的 openKylin 字段只能作为配置识别信息，不能替代命令行环境证据。
- 下一步：在不写入密钥/密码的前提下，使用客户机本地交互登录或由用户在 VM 内执行验证脚本；取得脱敏 stdout/stderr 和退出码后再继续 API 批次。

### 批次 9：用户确认客户机已登录

- 输入信息：用户明确表示“已经登录客户机”。该信息记录为用户陈述，不替代 VM 内命令、屏幕捕获或 VMware Tools 客户机操作证据。
- 当前状态：客户机仍由 `vmrun list` 识别为运行中，IP 仍为 `192.168.182.129`，Tools 状态为 `running`；此前 `captureScreen`、`listProcessesInGuest` 在无凭据条件下均被 VMware 拒绝，SSH 端口也未开放。
- 下一步：利用已登录状态重新尝试可用的无密码/本地通道（VMware REST、VNC、共享文件夹、客户机端口）；任何成功的 `/etc/os-release`、`uname -a`、Python 或 CLI 输出必须保存原始 stdout/stderr 和退出码。

### 批次 10：已登录桌面窗口通道复核（2026-09-05）

- 实际命令/操作：查询 `vmrun list`、VMware 进程和窗口句柄；使用宿主机屏幕捕获保存 `runs/openkylin-validation-20260905/host-screen.png`、`focused.png`、`vm-focused2.png`、`after-click.png`、`terminal-attempt.png`；尝试将 VMware 窗口置前、点击客户机桌面并发送终端快捷键。
- 实际结果：`vmrun list` 仍显示 1 台 `D:\openKylin-VM\openKylin.vmx`，VMware Workstation 窗口可见，截图中可观察到 openKylin 桌面；但当前自动化输入未取得可保存的客户机终端 stdout/stderr，发送快捷键未形成可靠的终端证据。
- 客户机内命令：未成功执行，故没有新增 `/etc/os-release`、`uname -a`、Python/pip 或 CLI 结果；不得把窗口截图或 `guestInfo.detailed.data` 当作命令行验证。
- 客观阻塞：`vmrun runProgramInGuest`、`listProcessesInGuest`、`captureScreen` 仍返回 `VIX_E_ANON_GUEST_OPERATIONS_PROHIBITED`，需要客户机登录凭据；宿主机窗口注入通道无法稳定获得客户机终端焦点。
- 结果文件：上述屏幕截图仅作为宿主机可见窗口证据，不能证明 Benchmark 已在 openKylin 内安装或运行。
- 已完成：确认客户机启动、窗口可见和 openKylin 桌面可观察；未完成：客户机内环境探针、安装、Grok/DeepSeek 健康检查、双 Agent CLI、评分/报告和卸载验证。
- 待确认假设：用户桌面登录会话与 VMware VIX 所需客户机账号凭据不是同一可用认证通道；影响所有无交互客户机命令执行。
- 下一轮最高优先级：取得可复现的客户机内命令通道（客户机终端执行并保存原始输出，或启用 SSH/VMware Tools 认证），然后再进行 API 和完整 CLI 批次。

### 批次 11：客户机输入通道再次探测（2026-09-05）

- 实际操作：确认 `vmrun list` 仍显示 `D:\openKylin-VM\openKylin.vmx` 且 Tools 为 `running`；使用宿主机 `SendInput` 发送一次无敏感点击和唤醒按键，保存 `runs/openkylin-validation-20260905/sendinput-click.png`、`after-unlock.png`、`unlock-space.png`、`wake-check.png`。
- 实际结果：底层输入调用返回成功计数，但屏幕焦点随后落到宿主机锁屏/屏保或非客户机界面，未取得客户机终端 stdout/stderr；无法证明任何探针命令在 openKylin 内执行。
- 客户机内命令：未执行；没有新增系统版本、Python/pip、依赖或 CLI 结果。
- 客观阻塞：宿主机当前进入锁屏/屏保，且窗口坐标/输入焦点在高 DPI 多窗口环境下不稳定；继续注入可能误操作宿主机。已停止自动输入，不再猜测或尝试宿主机凭据。
- 已完成：再次确认 VM 进程和 Tools 运行状态，保留原始屏幕证据；未完成：openKylin 环境探针、安装、API 健康检查、双 Agent CLI、证据/评分/报告和卸载验证。
- 待确认假设：宿主机解锁后，VMware 窗口可由用户保持前台并允许客户机终端输入；影响后续所有 VM 内命令批次。
- 下一轮最高优先级：宿主机解锁并提供稳定客户机命令通道（优先 SSH 或带账号的 VMware Tools，其次由用户在客户机终端执行验证脚本并保存输出）。

### 批次 12：锁屏安全边界确认（2026-09-05）

- 实际操作：使用 VMware 窗口截图确认客户机画面曾进入锁屏；尝试一次无凭据唤醒后，宿主机/客户机画面仍未恢复为可验证终端。
- 实际结果：没有取得客户机 `/etc/os-release`、`uname -a`、Python/pip 或 CLI stdout/stderr；没有执行 API 请求、评分或报告生成。
- 安全处理：依据 Windows 自动化安全约束，停止继续发送键盘/鼠标输入，不自动化任何认证对话，不猜测或输入密码。
- 客观阻塞：当前没有可复现的客户机命令通道；VMware Tools 仍要求客户机账号密码，SSH 端口未开放，桌面锁屏无法由本代理安全解锁。
- 已完成：确认 `vmrun list` 仍可识别 VM、保留屏幕探测文件；未完成：openKylin 环境探针、安装、Grok/DeepSeek 健康检查、双 Agent CLI、证据/评分/报告和卸载验证。
- 待确认假设：用户解锁宿主机并保持 VMware 客户机终端前台后，可继续执行客户机命令；影响下一轮所有运行批次。
- 下一轮最高优先级：由用户解锁当前桌面并让客户机终端保持可输入，或启用 SSH/VMware Tools 认证后再继续。

### 批次 13：SSH 客户机环境取证（2026-09-06）

- 实际命令：`ssh -p 2222 -i <用户 SSH 密钥> -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes <vm-user>@192.168.182.129 'bash -s'`，远端执行 `whoami`、`hostname`、`cat /etc/os-release`、`uname -a`、`uname -m`、`python3 --version`、`python3 -m pip --version`、setuptools 导入、`df -h /home` 和网络探针。
- 退出码：`0`（SSH 与探针脚本成功完成；pip/setuptools 子命令按预期报告未安装）。
- 客户机环境：`openKylin 2.0 SP2 (nile)`，`Linux kare 6.6.0-25-generic x86_64`，Python `3.12.2`，地址 `192.168.182.129/24`，`/home` 可用约 `21G`；SSH 监听端口为 `2222`，22 端口未使用。
- 依赖状态：`python3 -m pip --version` 输出 `/usr/bin/python3: No module named pip`；setuptools 导入返回 `ModuleNotFoundError`。需要在客户机虚拟环境中补齐安装工具。
- 结果文件：`runs/openkylin-validation-20260906/environment/ssh-environment.stdout.log`、`ssh-environment.stderr.log`。
- 已完成：取得真实 openKylin 客户机命令行证据，解除此前“无客户机通道”阻塞；未完成：项目安装、API 健康检查、双 Agent CLI、证据/评分/报告和卸载验证。
- 客观风险：客户机基础 Python 缺少 pip/setuptools，安装脚本需验证是否能使用 `ensurepip`、系统包或离线 wheel；API 密钥仍只允许通过进程环境注入。
- 待确认假设：客户机允许访问 PyPI 或可通过宿主机复制离线 wheel；影响依赖安装方式，不影响 SSH 取证结论。
- 下一轮最高优先级：复制项目到 `<user-home>` 下的工作目录，创建 `.kmb-venv` 并完成安装/探针批次。

### 批次 14：openKylin 安装脚本首轮（2026-09-06）

- 实际命令：SSH 进入 `<user-home>/kmb-openkylin-validation-20260906`，执行 `python3 -m venv --help`、`python3 -m ensurepip --version`、非交互 sudo 探针和 `bash scripts/install_local.sh python3`。
- 退出码：远端安装脚本 `1`（宿主机 SSH 包装命令因 CRLF 传输导致外层返回 `2`，不影响远端安装结论）。
- 实际结果：`venv` 模块存在，但 `ensurepip` 不可用；脚本输出系统需要 `apt install python3.12-venv`。当前用户无非交互 sudo 权限，虚拟环境未创建完成，未安装 PyYAML 或项目。
- 结果文件：`runs/openkylin-validation-20260906/install/install.stdout.log`、`install.stderr.log`。
- 已完成：确认项目文件已通过 SSH 复制；未完成：客户机虚拟环境、依赖、CLI 和 API 运行。
- 客观阻塞：openKylin 基础 Python 缺少 ensurepip，且当前用户不能使用 sudo 安装 `python3.12-venv`；需要用户级 pip 引导或离线 wheel。
- 待确认假设：客户机网络允许访问 PyPI/bootstrap.pypa.io，或可复制宿主机 wheelhouse；影响安装路径，不影响项目源代码。
- 下一轮最高优先级：在客户机使用 `venv --without-pip` + 用户级 pip 引导，完成 `PyYAML` 和本项目安装；全程保留安装 stdout/stderr 和退出码。

### 批次 15：openKylin 安装重试成功与脚本修复记录（2026-09-06）

- 修改文件：`scripts/install_local.sh`。实际修复为：`venv` 创建失败时回退到 `--without-pip`，通过 `KMB_PIP_BOOTSTRAP_URL` 或默认 PyPA `get-pip.py` 引导 pip，并补齐 setuptools；未修改评测协议、评分或 Agent 行为。
- 实际命令：在 `<user-home>/kmb-openkylin-validation-20260906` 执行 `bash scripts/install_local.sh python3`，随后检查 `.kmb-venv/bin/python --version`、`-m pip --version`、PyYAML、setuptools 和 `kmb.__file__`。
- 客户机内安装退出码：`0`（`install-retry.stdout.log` 中记录 `install_retry_exit=0`）。外层 SSH 包装 stderr 出现 `bash: line 13: exit: 0: numeric argument required`，属于 CRLF/包装命令噪声；远端安装本身已成功，不能将该 stderr 误判为安装失败。
- 实际结果：pip `26.2.1`、setuptools `84.0.0`、PyYAML `6.0.1`；构建并安装 `kylin-memory-bench-0.2.0`；安装脚本内部环境探针返回 `status: ok`，openKylin 识别为 `openKylin 2.0 SP2 (nile)`，Python `3.12.2`，x86_64，工作区可用约 `20.62 GB`，核心套件识别 `6` 个案例。
- 证据文件：`runs/openkylin-validation-20260906/install/install-retry.stdout.log`、`runs/openkylin-validation-20260906/install/install-retry.stderr.log`、`runs/openkylin-validation-20260906/install/venv-preflight.stdout.log`、`runs/openkylin-validation-20260906/install/pip-bootstrap.stdout.log`。
- 已完成：客户机用户级虚拟环境、pip/setuptools、PyYAML、项目安装和安装后探针。
- 未完成：`--require-openkylin` 独立门禁、套件 validate、Grok/DeepSeek 健康检查和真实双 Agent 评测、证据/评分/报告、卸载验证。
- 待确认假设：客户机网络可继续访问配置的 Grok/DeepSeek API；影响后续真实运行，不影响本批次安装结论。
- 下一轮最高优先级：在同一客户机虚拟环境执行 `env_probe --require-openkylin --json`、核心/对抗套件严格校验，并保存命令、退出码和原始日志。

### 批次 16：openKylin 门禁、CLI 和双套件严格校验（2026-09-06）

- 实际命令：通过 `ssh -p 2222 -i <用户 SSH 密钥> -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes <vm-user>@192.168.182.129` 进入客户机，在 `<user-home>/kmb-openkylin-validation-20260906` 执行 `whoami`、`hostname`、`cat /etc/os-release`、`uname -a`、`uname -m`、`.kmb-venv/bin/python --version`、`.kmb-venv/bin/python -m pip --version`、关键依赖导入、`.kmb-venv/bin/kmb --help`、`.kmb-venv/bin/python scripts/env_probe.py --require-openkylin --json`、核心和对抗套件的 `kmb.cli validate --strict`。
- SSH/远端批次退出码：`0`；环境探针和两个严格校验均成功，无 stderr 输出。
- 客户机证据：`openKylin 2.0 SP2 (nile)`，`Linux kare 6.6.0-25-generic x86_64`，Python `3.12.2`，pip `26.2.1`，setuptools `84.0.0`，PyYAML `6.0.1`，项目 CLI 入口可用；`env_probe --require-openkylin` 返回 `status: ok` 且 `openkylin.ok=true`，核心套件 `6` 个案例有效，对抗套件 `6` 个案例有效。
- 证据文件：`runs/openkylin-validation-20260906/environment/probe-validate.stdout.log`、`runs/openkylin-validation-20260906/environment/probe-validate.stderr.log`。
- 已完成：真实 openKylin VM 的环境门禁和双套件严格校验。
- 未完成：Grok/DeepSeek API 健康检查、双 Agent 真实运行、证据/评分/JSON/Markdown/SVG/HTML 报告、卸载验证。
- 待确认假设：配置中的 Grok `grok-4.6` 与 DeepSeek `deepseek-v4-flash` 在当前凭据和 API 端点上可调用；若端点或模型 ID 不可用，必须以真实 HTTP 错误记录并修正配置，不能降级为模拟结果。
- 下一轮最高优先级：在 VM 内分别执行 Grok 与 DeepSeek 最小健康检查，并把每个请求的状态、延迟、模型 ID 和脱敏错误写入独立日志。

### 批次 17：Grok 与 DeepSeek API 健康检查（2026-09-06）

- 实际命令：通过 SSH 进入 `<user-home>/kmb-openkylin-validation-20260906` 的 `.kmb-venv`，以单次进程环境注入 `GROK_API_KEY`、`DEEPSEEK_API_KEY`，执行模型目录 `GET /models` 和最小 `POST /chat/completions`（`temperature=0`、`max_tokens=8`）；凭据未写入文件、stdout、stderr 或结果 JSON。
- 客户机批次退出码：`0`；结果文件：`runs/openkylin-validation-20260906/api-health/health.stdout.log`、`health.stderr.log`。
- Grok：`https://api.wapq.cn/v1/models` 返回 `200`，模型目录包含 `grok-4.5` 和 `grok-4.6`；以 `grok-4.6` 请求返回 `200`，响应模型为 `grok-4.6`，文本预览为 `OK`，延迟约 `5943.6 ms`。
- DeepSeek：`https://api.deepseek.com/models` 返回 `200`，模型目录包含 `deepseek-v4-flash`、`deepseek-v4-pro` 和 `deepseek-v4-flash-vision-exp`；以 `deepseek-v4-flash` 请求返回 `200`，响应模型为 `deepseek-v4-flash`，JSON 结构有效但文本预览为空，延迟约 `758.8 ms`。正式评分将按实际空文本处理，不补写回答。
- 已完成：确认两个 API 凭据可用、端点可达、模型 ID 可解析；Grok 4.5/4.6 均由模型目录真实确认，Grok 4.6 和 DeepSeek v4 flash 完成最小调用。
- 未完成：正式六类案例运行、双 Agent 对比、EvidenceEvent/评分/JSON/Markdown/SVG/HTML 报告、严格结果校验、卸载验证。
- 待确认假设：`grok-4.6` 作为 Grok 参评版本、`deepseek-v4-flash` 作为 DeepSeek 参评版本；影响对比结果的模型版本标签，不影响端点健康检查。
- 下一轮最高优先级：使用同一 `core-zh` 六案例、seed `42`、重试 `1` 和统一超时在 VM 内执行真实 Grok 4.6 与 DeepSeek v4 flash `compare`，保留原始日志和运行目录。

### 批次 18：Grok 4.5 最小真实调用（2026-09-06）

- 实际命令：在同一 openKylin VM 虚拟环境中，以单次进程环境注入 Grok 凭据，向 `https://api.wapq.cn/v1/chat/completions` 发送 `model=grok-4.5`、`temperature=0`、`max_tokens=8` 的最小请求；完整密钥未写入文件或输出。
- 客户机批次退出码：`0`；结果文件：`runs/openkylin-validation-20260906/api-health/grok45.stdout.log`、`grok45.stderr.log`。
- 实际结果：HTTP `200`，响应模型 `grok-4.5`，文本预览 `OK`，延迟约 `9793.5 ms`；stderr 为空。
- 已完成：Grok 4.5 与 4.6 均完成模型目录/最小调用验证；DeepSeek v4 flash 已完成同类验证。
- 未完成：双 Agent 六案例 compare、证据导出、评分和报告、卸载验证。
- 待确认假设：正式参评 Grok 版本继续采用配置中的 `grok-4.6`，4.5 作为已验证可选版本保留；影响正式对比的模型标签，不影响 4.5 可调用性结论。
- 下一轮最高优先级：开始 VM 内真实 Grok 4.6 与 DeepSeek v4 flash 双 Agent 六案例对比。

### 批次 19：openKylin VM 纯 HTTP 双 Agent 六案例对比（2026-09-06）

- 实际命令：在 `<user-home>/kmb-openkylin-validation-20260906` 的 `.kmb-venv` 中，以单次进程环境注入两款 API 凭据，执行 `python -m kmb.cli compare --agents configs/agent-grok.yaml configs/agent-deepseek.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260906/compare-plain/results --run-id openkylin-plain-20260906 --seed 42 --retries 1 --timeout 180`。
- 客户机 CLI 退出码：`0`；总耗时约 `277487.7 ms`；SSH 包装退出码：`0`。VM 原始日志：`runs/openkylin-validation-20260906/compare-plain/compare.stdout.log`、`compare.stderr.log`；宿主机复制日志：`runs/openkylin-validation-20260906/compare-plain/ssh-status.stdout.log`、`ssh-status.stderr.log`。
- 结果已复制到宿主机：`runs/openkylin-validation-20260906/compare-plain/results/`，包含 `comparison.json`、`comparison.md`、`comparison.html`、两个 SVG 雷达图以及两个 Agent 的 `result.json`/`evidence.jsonl`。
- Grok 4.6：6 案例、28 条证据，总分 `30.56`；六维 `retention=50.00`、`memory_recall=0.00`、`dynamic_update=33.33`、`similar_distinction=50.00`、`boundary=50.00`、`task_reuse=0.00`；观测模式 `memory_state_unobservable`。
- DeepSeek v4 flash：6 案例、28 条证据，总分 `30.56`；六维与 Grok 本批次相同；观测模式 `memory_state_unobservable`。
- 证据解释：事件来自 `runner` 的用户轮次和 `model` 的 assistant 文本；未观察到 `memory_*`、`action` 或 provider 导出的状态事件。评分中的遗漏、陈旧值、混淆和错误复用均基于实际文本/缺失事件，不能解释为模型原生记忆能力已实现或已失败之外的内部状态结论。
- 安全核对：结果目录只出现环境变量名 `GROK_API_KEY`/`DEEPSEEK_API_KEY`，未出现完整密钥或 Authorization 值。
- 已完成：真实 openKylin VM 内双 Agent 同输入、同套件、同 seed/重试/超时的纯 HTTP 对比和报告生成。
- 未完成：VM 内透明包装层对比、严格 `verify_run`、对抗套件正式运行、卸载验证。
- 待确认假设：`grok-4.6` 与 `deepseek-v4-flash` 作为正式参评版本；本批次结果只代表当前 API 响应和“无可观测记忆状态”模式。
- 下一轮最高优先级：在同一 VM 和统一参数下运行 `agent-grok-memory.yaml` 与 `agent-deepseek-memory.yaml`，验证包装层记忆/动作证据及其系统级评分限制。

### 批次 20：openKylin VM 透明包装层双 Agent 对比与严格校验（2026-09-06）

- 实际命令：在客户机 `.kmb-venv` 中以单次进程环境注入两款 API 凭据，执行 `python -m kmb.cli compare --agents configs/agent-grok-memory.yaml configs/agent-deepseek-memory.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260906/compare-wrapper/results --run-id openkylin-wrapper-20260906 --seed 42 --retries 1 --timeout 180`。
- 客户机 CLI 退出码：`0`；耗时约 `252312.7 ms`；输出文件：`runs/openkylin-validation-20260906/compare-wrapper/compare.stdout.log`、`compare.stderr.log`；宿主机副本位于 `runs/openkylin-validation-20260906/compare-wrapper/results/`。
- Grok 4.6 + wrapper：6 案例、70 条证据，总分 `86.11`；六维 `retention=100.00`、`memory_recall=100.00`、`dynamic_update=66.67`、`similar_distinction=100.00`、`boundary=50.00`、`task_reuse=100.00`。
- DeepSeek v4 flash + wrapper：6 案例、70 条证据，总分 `86.11`；六维与 Grok 本批次相同。
- 证据统计（每个 Agent）：`source=wrapper` 共 `28` 条、`source=model` 共 `42` 条、wrapper 记忆事件 `13` 条、原生记忆事件 `0` 条、未证实模型自述 `14` 条；报告观测模式为 `system_level_wrapper_assisted`，结论限制明确为模型后端加外部控制器，不证明模型原生长期记忆。
- 严格验证命令：在 VM 内执行 `scripts/verify_run.py .../grok-memory-controller --strict` 和 `.../deepseek-memory-controller --strict`；两者退出码均 `0`，均返回 `6 cases`、`70 evidence_events`、run_id `openkylin-wrapper-20260906`。验证日志：`runs/openkylin-validation-20260906/compare-wrapper/verify/verify.stdout.log`、`verify.stderr.log`。
- 结果哈希已记录在验证日志：`comparison.json`=`0928610f...fb005b`、`comparison.md`=`082ebab7...f91dbc`、`comparison.html`=`2dae096f...07760b`、两个 SVG=`517abc79...49aec6`；Agent `result.json`/`evidence.jsonl` 哈希同样保存在该日志（日志中为完整 SHA-256）。
- 安全核对：宿主机 compare 结果与验证日志只包含环境变量名和脱敏元数据，未出现完整 API 密钥。
- 已完成：真实 openKylin VM 内包装层双 Agent 六类能力运行、证据导出、自动评分、JSON/Markdown/SVG/HTML 报告和严格结构校验。
- 未完成：按 runbook 的一次性正式验收脚本复跑、卸载验证；对抗套件尚未进行正式双 Agent 运行。
- 待确认假设：包装层作为系统级被测对象满足赛事展示需要；模型原生内部记忆不可观测，报告必须保持该限制措辞。
- 下一轮最高优先级：执行 `scripts/run_acceptance.sh` 的完整门禁/validate/compare/verify 批次并记录退出码，然后执行卸载验证。

### 批次 21：openKylin VM 正式验收脚本（2026-09-06）

- 实际命令：通过 SSH 在 `<user-home>/kmb-openkylin-validation-20260906` 设置 `KMB_PYTHON=.kmb-venv/bin/python`、`KMB_TIMEOUT=180`，仅在进程环境注入两款 API 凭据，执行 `bash scripts/run_acceptance.sh configs/agent-grok.yaml configs/agent-deepseek.yaml suites/core-zh.yaml runs/openkylin-validation-20260906/formal-acceptance/results`。
- 客户机脚本退出码：`0`；完整脚本耗时约 `196370.4 ms`；SSH 包装退出码：`0`。日志：`runs/openkylin-validation-20260906/formal-acceptance/acceptance.stdout.log`、`acceptance.stderr.log`，宿主机同步副本另有 `ssh-status.stdout.log`、`ssh-status.stderr.log`。
- 实际步骤均通过：`env_probe --require-openkylin` 返回 `status=ok/openkylin.ok=true`；核心套件严格校验 `6 cases valid`；compare 输出 `grok-api` 与 `deepseek-api`；两个 `verify_run --strict` 均为 `6 cases/28 evidence_events/exit=0`。
- 正式结果已复制到宿主机 `runs/openkylin-validation-20260906/formal-acceptance/results/`，包含双 Agent `result.json`、`evidence.jsonl`、`comparison.json`、`comparison.md`、`comparison.html` 和两个 SVG 雷达图。
- 正式评分：Grok 4.6 `30.56`（六维 `50/0/33.33/50/50/0`）；DeepSeek v4 flash `38.89`（六维 `50/0/33.33/50/100/0`）；两者观测模式均 `memory_state_unobservable`，各 28 条证据均来自 `runner`/`model`，无可验证原生或包装层记忆事件。
- 安全核对：正式结果和日志中仅保存 `GROK_API_KEY`、`DEEPSEEK_API_KEY` 环境变量名及模型响应元数据，未保存完整密钥。
- 已完成：按 runbook 的 openKylin 门禁、安装后环境、validate、真实双 Agent compare、证据导出、评分、JSON/Markdown/SVG/HTML 报告和严格校验。
- 未完成：卸载验证；本正式脚本使用纯 HTTP Agent，不包含包装层对比（包装层批次见批次 20）。
- 待确认假设：正式赛事展示是否同时展示纯模型能力与包装层系统级能力；两者必须在报告中分开命名和解释。
- 下一轮最高优先级：在结果已复制并核对后执行客户机 `bash scripts/uninstall_local.sh`，记录清理结果并确认项目源码/运行证据不被删除。

### 批次 22：openKylin VM 卸载验证（2026-09-06）

- 实际命令：通过 SSH 执行 `cd <user-home>/kmb-openkylin-validation-20260906 && bash scripts/uninstall_local.sh`；随后再次执行同一命令确认幂等性。
- 第一次远端动作实际删除 `.kmb-venv`，输出 `venv_before=present`、`removed environment: <user-home>/kmb-openkylin-validation-20260906/.kmb-venv`、`venv_after=absent`、`source_after=present`、`remote_evidence_after=present`；由于外层变量转义错误，SSH 包装退出码为 `2`（`bash: exit: \\` numeric argument required），不代表卸载动作失败。原始日志：`runs/openkylin-validation-20260906/uninstall/uninstall.stdout.log`、`uninstall.stderr.log`。
- 第二次直接执行退出码：`0`；输出 `environment not present: .../.kmb-venv`，证明卸载脚本幂等。日志：`runs/openkylin-validation-20260906/uninstall/uninstall-rerun.stdout.log`、`uninstall-rerun.stderr.log`。
- 实际结果：客户机虚拟环境已移除；客户机项目源码和 `runs/openkylin-validation-20260906` 证据目录仍存在；宿主机已保存安装、环境、API 健康检查、纯 HTTP 对比、包装层对比、正式验收和严格校验产物。
- 已完成：安装/运行/报告/严格校验/卸载完整链路；卸载验证本身已获得直接 `exit=0` 证据。
- 未完成：卸载后若要再次运行需重新执行安装脚本；对抗套件双 Agent 正式运行未纳入本轮 runbook 主链路。
- 待确认假设：保留客户机源码和远端证据目录符合交付留痕要求；若赛事要求完全清理项目目录，需另行制定归档后删除步骤。
- 下一轮最高优先级：基于宿主机已复制的正式验收结果整理赛事交付摘要；若需新增运行，先在客户机重新安装 `.kmb-venv`。

## 12. 官方赛题 PDF 核验记录（2026-09-06）

### 12.1 来源与核验范围

- 来源文件：`<user-home>\Downloads\ai_open_kylin_open_kylin_benchmark_XaCQyZepC8.pdf`。
- PDF 元信息：3 页、A4、未加密；创建工具元信息为 Chromium/pdfcpu。文本已使用本机 PDF 文本解析工具提取，并将页面渲染为 PNG 进行人工可读性核对。
- 核验产物：`runs/pdf-review-20260906.txt`、`runs/pdf-review-20260906/official-brief-1.png`、`official-brief-2.png`、`official-brief-3.png`。
- 本节只记录 PDF 中可以直接确认的命题内容；项目实现状态仍以各批次真实命令、退出码和结果文件为准。

### 12.2 官方命题背景与最终目标（PDF 第 1-2 页）

- 背景痛点：大模型智能体进入办公、研发和个人助理场景后，长期、稳定、可控地记住用户信息成为关键能力；既要保留稳定信息（偏好、路径、模板），也要识别并排除临时信息、敏感信息、风险指令和噪声。
- 生态背景：PDF 点名 openKylin 生态已支持 KylinBot、kylin-agent、OpenClaw、Hermes Agent 等主流智能体框架，但缺少配套的系统级自动化评测工具，难以在 openKylin 上量化比较不同智能体的记忆能力。
- 评测缺口：人工检查难以规模化；简单问答不能覆盖冲突更新、相似干扰和行动复用；自动评分容易语义偏移，难稳定区分“记住了”“误记了”和“不该记却记了”。
- 官方目标：基于 openKylin 操作系统及生态，围绕通用智能体长期记忆能力，设计尽可能自动化、低人工介入、可复现、可扩展的 benchmark，衡量记忆写入、检索、更新、拒绝和任务复用能力。
- 证据要求：将对话、记忆记录、行动轨迹、文件或其他运行产物统一组织为证据，并基于这些证据自动评估长期记忆能力。
- 最终目标：形成能够自动产出多维指标的 benchmark，优先在 openKylin 系统完成验证，服务 openKylin 社区智能体能力的持续评估与优化。

### 12.3 官方六类能力（PDF 第 1 页）

1. **长期保持**：应保留的信息是否被稳定记住并在后续使用。
2. **记忆调用**：后续交互中是否能正确调用相关信息。
3. **动态更新**：新信息出现后是否能覆盖或修正旧信息。
4. **相近区分**：是否能识别相近信息之间的差异。
5. **边界识别**：不应长期保留或不应复用的信息是否被正确识别。
6. **任务复用**：实际任务执行中是否能合理使用历史信息。

### 12.4 官方交付要求（PDF 第 2 页）

- **方案说明文档**：必须说明测试目标、基本前提、数据生成、验证用例、结果收集和自动评分完整流程；数据结构应可扩展并覆盖不同记忆样本及验证项；自动评分应尽量少人工并输出可解释原因。
- **样例数据与样例结果**：提供少量示例任务、示例运行证据和示例评分结果，证明方案可执行。
- **可复现材料**：提供脚本、配置、README 和实现代码，并确保代码能在 openKylin 上直接编译与运行，使评审方能理解和复现核心流程。
- **工具化封装**：打包为可在 openKylin 上一键运行的 CLI 或 GUI，支持导入不同智能体配置进行批量对比评测；`.deb` 是 PDF 明确写出的建议分发格式，不是强制字样。
- **真实环境演示视频**：在 openKylin 桌面环境下，针对至少两款不同智能体运行评测，并产出多维对比雷达图；建议时长 3-5 分钟。

### 12.5 官方评审维度与权重（PDF 第 2-3 页）

| 评审维度 | 权重 | PDF 细则摘要 |
|---|---:|---|
| 任务定义与通用性 | 15% | 能否面向不同智能体和不同证据来源评测；迁移性；与 openKylin 智能体操作系统架构的集成和生态落地价值。 |
| 数据设计质量 | 25% | 覆盖多种长期记忆情形和不同证据来源；样本具备区分度、覆盖面和扩展空间。 |
| 自动评分能力 | 25% | 尽量减少人工审核；评分结构化、可解释；区分正确记忆、遗漏、混淆、错误持久化和错误复用。 |
| 稳定性与可复现性 | 15% | 同输入结果稳定；流程清晰；支持批量运行和结果追踪；能在 openKylin 标准环境稳定复现。 |
| 指标完整性 | 10% | 输出多维指标，而非单一总分；反映不同长期记忆能力差异。 |
| 创新性与工程可落地性 | 10% | 有创新思路并具备落地和扩展价值；针对 openKylin 架构特点优化。 |

权重合计为 `100%`。PDF 最后强调，评审重点是能否基于**真实智能体运行证据**自动完成评测，并稳定区分不同模型或系统在长期记忆能力上的差异。

### 12.6 对“忆衡”现有实现的约束映射

- 已对齐：核心/对抗套件覆盖六类能力；统一 `EvidenceEvent` 组织对话、记忆、动作和运行产物；CLI 支持双 Agent `compare`；openKylin VM 已完成安装、门禁、真实 Grok/DeepSeek 运行、证据导出、评分、JSON/Markdown/SVG/HTML 报告和卸载验证。
- 必须保持：纯 HTTP 模型结果与外部包装层结果分开；包装层分数只能称为“模型后端 + 外部控制器”的系统级行为；模型文本自述不能升级为原生记忆证据。
- 仍需关注：PDF 要求的真实环境演示视频尚未在本上下文包中记录为已完成；对抗套件虽已严格校验，尚未纳入本轮双 Agent 正式运行；`.deb` 为官方建议项，是否制作需结合赛事提交时间和安装复现成本决定。
- 待确认假设：PDF 是当前赛事细则的有效版本，且未被后续官方通知替换；影响提交材料版本控制，不影响本次文本核验结果。
- 下一轮最高优先级：按 PDF 交付要求整理“方案说明、样例数据/结果、可复现 CLI、真实双 Agent 证据、3-5 分钟演示脚本”的赛事交付包，并单独标注未完成的视频和对抗套件运行项。

### 12.7 后续决策遵循规则（用户确认，2026-09-06）

后续所有需求分析、实现取舍、任务排序、验收判断和赛事材料编写，必须以本节 12.2-12.5 所核验的官方 PDF 内容为优先依据，并遵循以下决策顺序：

1. **官方硬要求优先**：不得偏离 openKylin 上的通用智能体长期记忆自动化评测 benchmark；不得改造成聊天机器人、RAG 产品或单模型脚本。
2. **真实证据优先**：评分和结论必须来自真实智能体运行证据；没有观测到的内部状态标记为不可观测，不得用文本自述、模拟结果或推测补齐。
3. **六类能力完整性**：长期保持、记忆调用、动态更新、相近区分、边界识别、任务复用均必须有数据、执行路径、证据和可解释评分覆盖。
4. **双 Agent 可比性**：至少两款真实智能体使用统一案例、输入、Prompt、评分规则和运行参数进行对比；模型 API 与外部包装层结果必须分开命名。
5. **自动评分与可解释性优先**：优先结构化、低人工介入的评分，并保留遗漏、混淆、错误持久化、错误复用、超时和运行异常的证据引用及失败原因。
6. **openKylin 可复现性优先**：新增功能必须能在 openKylin 上通过 CLI 或 GUI 运行；宿主机、其他 Linux、模拟器或历史结果不能替代 openKylin 验证。
7. **交付物完整性**：方案说明、样例数据与结果、代码/脚本/配置/README、可运行 CLI、双 Agent 真实运行证据和多维报告是核心交付物；`.deb` 和 3-5 分钟演示视频按官方 PDF 作为优先发布项跟踪，其中 `.deb` 明确为建议格式。
8. **证据和安全边界**：任何完成结论必须对应文件、命令、退出码、日志或结果文件；凭据只通过进程环境注入，不能写入代码、配置、报告、截图、上下文包或 Git 历史。

若历史计划、临时便利方案或用户新想法与上述规则冲突，应暂停冲突部分并明确指出影响，保留符合官方目标的最小可交付路径。只有在获得新的官方文件或用户明确确认后，才可调整本决策基线。

### 批次 23：双 Agent 对比前的 VM 必要环境恢复（2026-09-06）

- 前置状态：上一个批次执行卸载后，客户机 `.kmb-venv` 不存在；项目源码和历史运行证据仍保留。
- 实际命令：通过 SSH 在 `<user-home>/kmb-openkylin-validation-20260906` 执行 `bash scripts/install_local.sh python3`。
- 客户机退出码：`0`；日志：`runs/openkylin-validation-20260906/reinstall/install.stdout.log`、`install.stderr.log`。
- 实际结果：使用 `venv --without-pip` 回退和 PyPA 引导流程恢复 `.kmb-venv`；pip `26.2.1`、setuptools `84.0.0`、PyYAML `6.0.1`，`kylin-memory-bench-0.2.0` 构建并安装成功，安装后探针返回 `status=ok`。
- 状态：已完成本轮双 Agent 对比所需的最小环境恢复；未重复无关基础测试或历史环境验证。
- 安全核对：宿主机工作区未发现完整 API 密钥片段，后续仍只使用单次进程环境注入。
- 待确认假设：客户机网络和两款 API 额度在本轮仍可用；影响真实对比成功率，不影响环境恢复结论。
- 下一轮最高优先级：执行 Grok 4.6 与 DeepSeek v4 flash 的统一忆衡包装层六案例双 Agent 对比。

### 批次 24：本轮最终 Grok/DeepSeek 包装层双 Agent 对比（2026-09-06）

- 实际命令：在客户机 `<user-home>/kmb-openkylin-validation-20260906` 的 `.kmb-venv` 中，以单次进程环境注入 `GROK_API_KEY`、`DEEPSEEK_API_KEY`，执行 `python -m kmb.cli compare --agents configs/agent-grok-memory.yaml configs/agent-deepseek-memory.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260906/final-compare/results --run-id final-wrapper-20260906 --seed 42 --retries 1 --timeout 180`。
- 客户机 CLI 退出码：`0`；运行耗时约 `285543.0 ms`；SSH 包装退出码：`0`。日志：`runs/openkylin-validation-20260906/final-compare/compare.stdout.log`、`compare.stderr.log`、`ssh-status.stdout.log`、`ssh-status.stderr.log`。
- 结果已复制到宿主机 `runs/openkylin-validation-20260906/final-compare/results/`，包含 `comparison.json`、`comparison.md`、`comparison.html`、两个 SVG 雷达图以及两个 Agent 的 `result.json`/`evidence.jsonl`。
- Grok 4.6 + wrapper：6 案例、69 条证据，总分 `86.11`；六维 `retention=100.00`、`memory_recall=100.00`、`dynamic_update=66.67`、`similar_distinction=100.00`、`boundary=50.00`、`task_reuse=100.00`；观测模式 `system_level_wrapper_assisted`。
- DeepSeek v4 flash + wrapper：6 案例、70 条证据，总分 `86.11`；六维与 Grok 相同；观测模式 `system_level_wrapper_assisted`。
- 证据统计：两边均 `wrapper_memory_events=13`、`native_memory_events=0`；Grok 来源计数 `model=41/wrapper=28`，DeepSeek `model=42/wrapper=28`。模型文本、请求和响应只证明可观察输出；记忆写入/更新/召回/抑制和动作来自统一外部 wrapper。
- 严格验证：远端 `scripts/verify_run.py .../grok-memory-controller --strict` 和 `.../deepseek-memory-controller --strict` 均退出 `0`，分别返回 `6 cases/69 events` 和 `6 cases/70 events`。日志：`runs/openkylin-validation-20260906/final-compare/verify/verify.stdout.log`。
- 已记录文件哈希：`comparison.json`=`6e5b5f9b...f262c895`、`comparison.md`=`082ebab7...f91dbc`、`comparison.html`=`6c0381e4...bd540994`；其余文件完整 SHA-256 见验证日志。
- 安全核对：本轮工作区和结果目录未发现完整 API 密钥片段；配置和报告只包含环境变量名、模型 ID、端点和脱敏元数据。
- 已完成：本轮目标要求的真实 Grok/DeepSeek 双 Agent 对比、六类核心案例、证据导出、评分、双 Agent 汇总报告和严格校验。
- 部分完成：结果是“模型 API + 统一忆衡包装层”的系统级长期记忆行为，无法归因于模型原生长期记忆；未运行包装层关闭基线（当前系统未提供该模式），未纳入对抗套件正式运行。
- 待确认假设：赛事允许以云端 Grok/DeepSeek 作为真实参评模型后端，并接受包装层系统级结果作为补充展示；不影响本批次事实记录。
- 下一轮最高优先级：将本批次结果整理进最终赛事报告，并补充对抗套件双 Agent 运行和 openKylin 桌面演示材料。

### 批次 25：最终赛事汇总报告生成与事实校验（2026-09-06）

- 前置状态：批次 24 的 openKylin VM 包装层双 Agent 结果、批次 21 的纯 HTTP 正式验收结果和对应严格校验产物均已复制到宿主机；本批次不重新调用 API、不重新安装 VM 环境。
- 实际新增文件：`runs/openkylin-validation-20260906/final-event-report.md`。
- 报告内容：openKylin 2.0 SP2 环境、Grok 4.6/DeepSeek v4 flash 端点与健康检查、统一运行参数、六类能力分数、证据来源统计、纯 HTTP 与 wrapper-assisted 两条结果轨道、官方 PDF 交付要求映射、复现命令、失败原因和未完成事项。
- 实际校验命令：PowerShell 读取并解析 `final-compare/results/comparison.json` 和 `formal-acceptance/results/comparison.json`，断言双 Agent、六维字段、包装层分数与报告限制措辞；扫描报告中的 `sk-*`、`ark-*` 和带值 API 环境变量样式；计算报告 SHA-256。
- 校验结果：校验命令退出码 `0`；`report_valid=true`；包装层双 Agent 均为 `86.11`；纯 HTTP 双 Agent 结果对象存在；`secret_scan=clean`；报告 SHA-256=`af6e24a9d4786df20b8d449f2a4b91dece8bead0171ee2996be810ae302be04c`。
- 相关产物：`runs/openkylin-validation-20260906/final-event-report.md`、`final-compare/results/`、`formal-acceptance/results/`、`final-compare/verify/ssh-status.stdout.log`。
- 校验备注：首次校验命令因 PowerShell 对嵌套 JSON 属性计数的写法不兼容而退出非零，未修改任何结果文件；随后改用显式属性集合计数，校验成功。该失败仅属于校验脚本表达式问题，不代表运行产物失败。
- 已完成：赛事最终汇总报告已生成；报告明确区分 API 可观察文本、外部 wrapper 操作、可证明的系统级行为和不可观测的模型内部状态；报告未包含完整凭据。
- 部分完成：对抗套件尚未进行真实双 Agent 运行；包装层关闭基线当前无实现；`.deb` 和 3-5 分钟 openKylin 桌面演示视频尚未交付。
- 客观阻塞：完成对抗套件真实运行需要再次在 openKylin VM 安装 `.kmb-venv` 并消耗 Grok/DeepSeek API 额度；制作 `.deb` 和录制视频需要额外发布/演示准备时间。
- 待确认假设：赛事接受“纯 HTTP 可观察结果 + wrapper-assisted 系统级结果”并列展示；该假设不改变本批次事实记录，但影响最终答辩措辞。
- 下一轮最高优先级：在 openKylin VM 中运行 `suites/adversarial/core.yaml` 的 Grok/DeepSeek 真实双 Agent 对比，并将证据和评分追加到赛事交付包。

### 批次 26：对抗套件运行前 VM/凭据可用性探测（2026-09-06）

- 实际命令：宿主机使用 `ssh -p 2222 -i "$env:USERPROFILE\\.ssh\\openkylin_vm_ed25519" -o IdentitiesOnly=yes -o BatchMode=yes <vm-user>@192.168.182.129`，在客户机检查项目目录、`.kmb-venv/bin/python`、`GROK_API_KEY` 和 `DEEPSEEK_API_KEY` 是否存在；只输出 `present/absent`，未读取或输出任何密钥值。
- 实际结果：SSH 连接成功，客户机返回 `venv=present`、`grok_key=absent`、`deepseek_key=absent`、`Python 3.12.2`；探测退出码 `0`。宿主机当前进程环境检查同样为 `host_grok_key_present=False`、`host_deepseek_key_present=False`。
- 已完成：确认 VM 通道和评测虚拟环境仍可用；未启动对抗套件，避免在缺少凭据时伪造或误报真实 Agent 结果。
- 未完成：`suites/adversarial/core.yaml` 的 Grok/DeepSeek 真实双 Agent 运行、证据导出和评分尚未执行。
- 客观阻塞：当前可见进程环境缺少两款 API 凭据；历史批次使用的凭据未持久化，不能从工作区、日志或报告中恢复完整密钥。
- 安全状态：未在本批次命令输出、文件或上下文包写入完整 API 密钥。
- 待确认假设：后续运行需在客户机或 SSH 单次进程环境安全注入新鲜凭据，并遵守赛事网络、额度和数据脱敏政策；影响对抗套件运行，不影响已完成的核心六案例报告。
- 下一轮最高优先级：在不保存密钥的前提下为客户机进程提供两款 API 凭据后，运行并严格校验对抗套件双 Agent 结果。

### 批次 27：凭据安全保存尝试、清理与自动化传输阻塞（2026-09-06）

- 前置检查：通过 SSH 确认客户机项目目录 `.kmb-venv` 存在；`~/.config/kmb/credentials.env` 原先不存在；本批次未重复系统版本和依赖探测。
- 实际动作：尝试将本对话凭据写入客户机用户级 `~/.config/kmb/credentials.env`（目标目录 `700`、文件 `600`），通过 SSH 标准输入传递并设置 `umask 077`。首次传输因 PowerShell/SSH 行尾转换导致 bash 读取失败，命令退出码 `127`；随后自动化运行时策略拒绝再次传输完整密钥，未继续尝试绕过。
- 清理命令：通过 SSH 执行删除可能残留的 `~/.config/kmb/credentials.env`，并在项目（排除 `.kmb-venv`）递归扫描 `sk-*`/`ark-*` 密钥样式。
- 清理结果：客户机返回 `credential_file_removed=true`、`project_secret_scan=clean`，SSH 清理退出码 `0`；当前未保留用户级凭据文件，也未在项目/结果目录发现完整密钥样式。
- 已完成：失败落盘文件已移除；没有把密钥写入项目、日志、结果、上下文包或源码；VM SSH 通道仍可用。
- 未完成：安全保存两款 API 凭据、健康检查、对抗套件真实双 Agent 运行、证据导出和评分均未在本批次执行。
- 客观阻塞：自动化命令执行策略禁止把对话中的完整 API 密钥作为载荷再次传输；当前宿主机与客户机进程环境均无凭据，无法在不违反安全边界的情况下启动真实 API 调用。
- 待确认假设：由用户在 openKylin 客户机本地终端以隐藏输入方式创建 `~/.config/kmb/credentials.env`，或在启动评测的同一交互进程中注入环境变量后，自动化工具即可继续；该动作不会把密钥写入项目或日志。
- 下一轮最高优先级：客户机本地安全注入凭据后，执行 Grok/DeepSeek 健康检查，再运行并严格校验 `suites/adversarial/core.yaml` 双 Agent 对比。

### 批次 28：凭据文件存在性检查与本地隐藏输入交接（2026-09-06）

- 必要读取：已读取最新上下文包；未重复系统版本、依赖或历史运行验证。
- 实际命令：通过 SSH 检查客户机 `$HOME/.config/kmb/credentials.env` 是否存在，并在存在时仅读取 `stat` 权限、所有者和大小，不读取文件内容。
- 实际结果：返回 `exists=false`，SSH 检查退出码 `0`；当前 VM 未保存用户级凭据文件。
- 已完成：确认后续本地录入目标路径；模型 ID 采用此前健康检查实际确认的 `grok-4.6` 和 `deepseek-v4-flash`；未执行 API 请求或对抗套件运行。
- 未完成：凭据保存、健康检查、对抗套件真实双 Agent 运行、证据导出和评分，均等待 VM 本地隐藏输入完成。
- 客观阻塞：本会话无法执行交互式隐藏输入，且不得通过自动化命令再次传输完整密钥；因此只向用户提供不含密钥的本地 Bash 录入命令。
- 待确认假设：用户在 openKylin VM 本地终端执行录入命令后，仅确认文件已创建，不回传密钥或文件内容；自动化工具再继续后续批次。
- 下一轮最高优先级：校验 `~/.config/kmb/credentials.env` 权限和格式后，执行 Grok/DeepSeek 健康检查，再运行并严格校验 `suites/adversarial/core.yaml` 双 Agent 对比。

### 批次 29：VM 本地隐藏输入凭据保存后的元数据校验（2026-09-06）

- 前置状态：用户在 openKylin VM 本地终端完成隐藏输入；截图只展示了权限和格式检查结果，不包含密钥内容。
- 实际命令：通过 SSH 检查 `$HOME/.config/kmb/credentials.env` 存在性、`stat` 权限/所有者，以及 Grok/DeepSeek 的非敏感 base URL 和模型格式；未读取或输出 API 密钥值。
- 实际结果：`credentials_present=true mode=600 owner=<vm-user>`、`nonsecret_config=valid`；SSH 元数据检查退出码 `0`。
- 凭据保存方式：客户机用户级文件 `~/.config/kmb/credentials.env`，上级目录应为用户私有目录；完整密钥不写入项目、日志、报告或上下文包。已通过本地隐藏输入保存；本批次未记录密钥指纹，避免派生标识不必要地扩散。
- 已完成：凭据文件存在、权限和非敏感配置格式通过；可以在同一客户机进程中以 `set -a; . "$HOME/.config/kmb/credentials.env"; set +a` 加载后调用后端。
- 未完成：两后端健康检查、对抗套件双 Agent 运行、严格校验、证据和报告生成。
- 待确认假设：文件中两项 API 密钥均可用且具有当前模型调用额度；下一批真实健康检查将验证该假设。
- 下一轮最高优先级：从用户级凭据文件加载环境变量，执行不回显密钥的 Grok/DeepSeek 模型列表和最小聊天健康检查。

### 批次 30：Grok/DeepSeek API 健康检查（2026-09-06）

- 前置状态：客户机 `~/.config/kmb/credentials.env` 已由用户在本地隐藏输入创建，权限元数据为 `600`、所有者 `<vm-user>`；本批次只在客户机进程中加载，不读取或输出密钥值。
- 实际命令：在 openKylin VM 通过 SSH 执行 `.kmb-venv/bin/python` 健康检查脚本；从凭据文件加载 `GROK_BASE_URL/GROK_MODEL` 和 `DEEPSEEK_BASE_URL/DEEPSEEK_MODEL`，分别请求 `/models` 与 `/chat/completions`，最小提示为 `Reply with OK only.`；输出仅包含端点、模型 ID、HTTP 状态、延迟、响应 ID 和短文本预览。
- 实际结果：Grok `grok-4.6` 的 `/models` 与最小对话均 HTTP `200`，延迟约 `580.1 ms/5044.9 ms`；DeepSeek `deepseek-v4-flash` 的 `/models` 与最小对话均 HTTP `200`，延迟约 `201.4 ms/561.8 ms`；健康检查 SSH 退出码 `0`。Grok 模型列表实际包含 `grok-4.5`、`grok-4.6`；DeepSeek 模型列表实际包含 `deepseek-v4-flash`、`deepseek-v4-pro`、`deepseek-v4-flash-vision-exp`。
- 结果与日志：脱敏摘要已保存为 `runs/openkylin-validation-20260906/api-health/adversarial-health.stdout.log`；未写入完整密钥、请求头或凭据文件内容。
- 已完成：确认两款真实 API 可调用，正式模型 ID 与现有配置一致；错误脱敏逻辑在健康检查中未触发。
- 未完成：对抗套件双 Agent 运行、证据导出、评分、严格校验和报告生成。
- 客观阻塞：本批次无 API 阻塞；后续运行仍受云 API 延迟、额度和网络稳定性影响。
- 待确认假设：赛事允许使用当前 NewAPI Grok 网关和 DeepSeek V4 flash 云端后端；不影响本批次健康检查事实。
- 下一轮最高优先级：使用统一 seed/重试/超时和相同 `suites/adversarial/core.yaml`，运行 Grok/DeepSeek 透明 wrapper 双 Agent 对比。

### 批次 31：对抗套件真实双 Agent 运行、严格校验与赛事报告更新（2026-09-06）

- 前置状态：批次 30 的两款 API 健康检查均 HTTP 200；客户机用户级凭据文件继续保持 `600`，未读取或输出密钥值。
- 实际命令：在 openKylin VM 加载 `~/.config/kmb/credentials.env` 后执行 `.kmb-venv/bin/python -m kmb.cli compare --agents configs/agent-grok-memory.yaml configs/agent-deepseek-memory.yaml --suite suites/adversarial/core.yaml --out runs/openkylin-validation-20260906/adversarial-compare/results --run-id adversarial-wrapper-20260906 --seed 42 --retries 1 --timeout 180`；标准输出和错误分别重定向到 `adversarial-compare/compare.stdout.log` 与 `compare.stderr.log`，完成后清理进程环境变量。
- 实际结果：VM 运行生成 Grok/DeepSeek 两个 `result.json`、两个 `evidence.jsonl`、`comparison.json`、`comparison.md`、`comparison.html` 和两个 SVG 雷达图；对比摘要无 stderr。每个 Agent 均为 6 案例、79 条证据、总分 `86.11`；六维均为 `retention=100.00`、`memory_recall=100.00`、`dynamic_update=66.67`、`similar_distinction=100.00`、`boundary=50.00`、`task_reuse=100.00`。
- 失败分类：两款 Agent 均在 `dynamic-update-002-revise` 因助手文本包含旧值 `Alice` 被标记为 `confusion`；均在 `boundary-002-secret` 因助手文本复述临时令牌 `tok_test_123` 被标记为 `confusion`。包装层状态更新、敏感值不持久化和任务复用均有对应 `EvidenceEvent`。
- 观测边界：两款 Agent 观测模式均为 `system_level_wrapper_assisted`；每个 Agent `native_memory_events=0`、`wrapper_memory_events=14`，结论仅代表“模型后端 + 外部控制器”的系统级长期记忆行为，不代表模型原生长期记忆能力。
- 复制命令：使用 SSH/SCP 将 VM 的 `adversarial-compare/results/`、`compare.stdout.log` 和 `compare.stderr.log` 复制到宿主机同路径；SCP 退出码 `0`。
- 严格校验命令：宿主机执行 `scripts/verify_run.py runs/openkylin-validation-20260906/adversarial-compare/results/grok-memory-controller --strict` 和对应 DeepSeek 目录；两条命令均退出码 `0`，均返回 `6 cases`、`79 evidence_events`、run_id `adversarial-wrapper-20260906`。随后执行双 Agent 分数/六维/观测模式一致性断言及结果目录密钥样式扫描，退出码 `0`，输出 `comparison_consistency=valid`、`secret_scan=clean`、`hashes_written=true`。
- 结果路径：`runs/openkylin-validation-20260906/adversarial-compare/results/`；校验哈希清单：`runs/openkylin-validation-20260906/adversarial-compare/hashes.sha256`；对比日志：`adversarial-compare/compare.stdout.log`、`compare.stderr.log`。
- 报告更新：将对抗套件结果、失败类型和证据边界追加到 `runs/openkylin-validation-20260906/final-event-report.md`；报告继续明确区分 API 文本、wrapper 操作和不可观测的模型原生状态。报告更新未修改历史运行目录。
- 已完成：对抗套件真实 Grok/DeepSeek 双 Agent 运行、证据导出、评分、双 Agent 比较报告和严格结构校验；对抗结果已纳入最终赛事汇总报告。
- 部分完成：对抗运行仍是 wrapper-assisted 系统级评测，未提供包装层关闭基线；`.deb` 包和 3-5 分钟 openKylin 桌面演示视频尚未交付。
- 客观阻塞：无新增运行阻塞；后续发布物需要额外打包和桌面录制工作。
- 待确认假设：赛事接受核心/对抗两套 wrapper-assisted 结果与纯 HTTP 结果分层展示，并允许当前云端 API 作为真实后端；影响答辩措辞，不改变实际证据。
- 下一轮最高优先级：制作可复现赛事发布包并录制 openKylin 桌面演示，同时保留模型原生记忆不可观测限制。

### 批次 32：赛事报告与上下文包一致性及安全校验（2026-09-06）

- 实际命令：PowerShell 读取 `runs/openkylin-validation-20260906/final-event-report.md`、`openKylin-Benchmark-项目上下文包.md`、对抗比较结果和批次标识，断言报告包含对抗运行、79 条证据、失败案例和观测边界；扫描上下文包与报告中的 `sk-*`/`ark-*` 密钥样式；计算两文件 SHA-256。
- 实际结果：命令退出码 `0`；输出 `final_report_consistency=valid`、`context_consistency=valid`、`secret_scan=clean`；最终赛事报告 SHA-256=`fe38ebc24eef8ee7f345c90ad2aa0e37c525ccd862a50ae9dd2e79893c6ab3e8`；本上下文包在本次追加后的 SHA-256=`888964d7247d6637744b73bc36c06ca3c09fc9d43b34f3459dd69dac23b8d142`。
- 已完成：确认赛事汇总报告与本轮真实对抗结果、上下文记录和安全约束一致；未修改运行证据或凭据文件。
- 部分完成：包装层关闭基线仍未实现；`.deb` 分发包和 3-5 分钟 openKylin 桌面演示视频仍未交付。
- 客观阻塞：无本轮运行阻塞；剩余事项属于发布材料和额外功能工作。
- 待确认假设：最终答辩将把纯 HTTP、wrapper-assisted 和不可观测原生状态分层呈现，并继续使用“系统级长期记忆行为评测”措辞。
- 下一轮最高优先级：制作可复现赛事发布包并录制 openKylin 桌面演示，必要时单独设计包装层关闭基线。

### 批次 33：对抗结果远端后置条件校验（2026-09-06）

- 实际命令：通过 SSH 检查 VM 上的 `comparison.json`、Grok/DeepSeek `result.json` 均为非空文件，`compare.stderr.log` 为空；未调用 API、未读取凭据文件内容。
- 实际结果：远端输出 `adversarial_postcondition=valid`，SSH 后置条件校验退出码 `0`。
- 说明：对抗比较任务为长时 SSH 进程，初始外层轮询未保存独立 shell exit 字段；因此不把未捕获的比较命令退出码写成确定的 `0`。其生成产物、无 stderr、两次严格 `verify_run --strict` 和后置条件检查均为成功证据。
- 已完成：结果完整性和严格结构均有独立校验，报告和上下文记录未夸大未捕获的退出码。
- 未完成：无新增运行未完成项；`.deb` 和桌面演示视频仍待发布工作。
- 客观阻塞：无新增阻塞。
- 下一轮最高优先级：赛事发布包和 openKylin 桌面演示。

### 批次 34：无记忆基线与 Debian 发布脚本本机实现/预检（2026-09-06）

- 实际修改：新增 `NoMemoryAgent`/`MemoryDisabledAgent` 与 `type: memory_disabled` 配置路径；新增 `configs/agent-grok-no-memory.yaml`、`configs/agent-deepseek-no-memory.yaml`。该模式仍逐轮调用真实模型后端，但不维护外部持久记忆、不执行文件动作；对写入记录禁用/抑制、对查询记录 recall miss、对依赖记忆的动作记录阻断原因。所有这些基线事件使用 `source=runner`、`evidence_class=no_memory_baseline`，模型请求/响应仍使用 `source=model`，因此不会把基线或包装层操作描述为模型原生记忆。
- 实际修改：`EvidenceEvent` 可识别 `no_memory_baseline`，可观测性摘要新增 `mode=no_memory_baseline`、`memory_disabled_events` 与边界声明；JSON/Markdown/HTML 报告展示该计数。新增针对真实后端接口的 FakeBackend 回归测试，覆盖禁用写入、recall miss、动作阻断、完整模型请求以及评分仍执行。
- 实际修改：新增 `packaging/deb/`、`scripts/build_deb.sh`、`install_deb.sh`、`upgrade_deb.sh`、`uninstall_deb.sh`、`verify_deb.sh` 与 `docs/deb-release.md`。设计包名为 `kylin-memory-bench`、`Architecture: all`、依赖 `python3 (>= 3.9), python3-yaml`，安装 `/usr/bin/kmb` 与 `/usr/share/kylin-memory-bench/`。构建脚本仅复制源码、配置、套件、文档和结构校验脚本，显式排除 `runs/`、虚拟环境、缓存、研究缓存、`.env`、`credentials.env` 与字节码。
- 实际命令：Windows 宿主机在项目根目录执行 `python -m unittest discover -s tests -v`，退出码 `0`，共 `36` 项测试通过；新增无记忆基线测试已包含其中。执行 `python -m kmb.cli validate --strict --suite suites/core-zh.yaml`，退出码 `0`，返回 `6` 例有效。执行两条 `build_agent_from_config` 配置加载检查，均退出码 `0`，输出两份 no-memory 配置的 `memory_mode=disabled`。执行 `bash -n scripts/build_deb.sh scripts/install_deb.sh scripts/upgrade_deb.sh scripts/uninstall_deb.sh scripts/verify_deb.sh`，退出码 `0`。
- 安全核对：在工作区（排除运行、缓存、虚拟环境）扫描密钥样式，未发现完整 API 密钥；扫描命中仅为 `README` 的无值环境变量示例、文档文字和测试用例名，不是凭据。
- 已完成：无记忆基线实现、离线回归和 Debian 脚本静态预检。
- 未完成：尚未在 openKylin VM 构建/安装 `.deb`，也尚未在 VM 使用用户级凭据运行 wrapper 与 no-memory 的真实双 Agent 对照；演示视频尚未录制。
- 客观边界：宿主机 Windows 没有 `dpkg-deb`，不能构建或验证 Debian 包；必须在 openKylin VM 完成构建、安装、真实 CLI 和卸载验证。
- 待确认假设：项目负责人将在正式对外分发前选择项目级 LICENSE；在此之前 `.deb` 仅作为技术验收/赛事现场复现包，不能宣称已有对外再分发授权。
- 下一轮最高优先级：同步本批代码至 openKylin VM，构建 `.deb` 并在该 VM 安装、运行最小包验证及真实双 Agent wrapper/no-memory 对照。

### 批次 35：openKylin VM 发布前置可用性检查（2026-09-06）

- 实际命令：宿主机通过 SSH 执行 `test -d <user-home>/kmb-openkylin-validation-20260906`、检查 `.kmb-venv/bin/python` 可执行，随后执行 `uname -srmo` 与 `command -v dpkg-deb`。
- 实际结果：SSH 退出码 `0`；远端项目目录与 `.kmb-venv` 均存在；内核标识为 `Linux 6.6.0-25-generic x86_64 GNU/Linux`；`dpkg-deb` 路径为 `/usr/bin/dpkg-deb`。
- 已完成：确认 VM 可承载本轮 Debian 构建与安装验证。
- 未完成：源码同步、`.deb` 构建/内容审计、安装/真实运行/卸载验证尚未开始。
- 安全说明：本批未读取、输出、复制或修改用户级凭据文件。
- 下一轮最高优先级：同步无记忆基线及 Debian 发布脚本到 VM 后构建 `.deb`。

### 批次 36：无记忆基线/发布脚本同步至 openKylin VM 与回归测试（2026-09-06）

- 实际命令：通过 SCP 仅同步本轮修改或新增的 `kmb/agents.py`、`kmb/models.py`、`kmb/runner.py`、`kmb/report.py`、两份 no-memory 配置、相关测试、`packaging/deb/`、五个 Debian 生命周期脚本和 `docs/deb-release.md` 至 `<user-home>/kmb-openkylin-validation-20260906`；未同步或删除 `runs/`、用户凭据、虚拟环境或历史证据。随后在远端执行 `.kmb-venv/bin/python -m unittest tests.test_agents tests.test_runner` 和 `bash -n` 检查五个发布脚本。
- 实际结果：SSH/SCP 批次退出码 `0`；openKylin VM 适配器与运行器相关 `17` 项测试通过，Bash 语法检查通过。
- 已完成：无记忆基线和 `.deb` 构建链已进入实际 openKylin VM 源码树。
- 未完成：尚未构建包、安装包、执行安装后 smoke/真实 Agent 对比或卸载。
- 安全说明：同步文件不含 API Key；本批未读取或改变 `~/.config/kmb/credentials.env`。
- 下一轮最高优先级：在 VM 构建 `.deb`、验证控制字段和 payload 排除项。

### 批次 37：openKylin VM Debian 包构建与 payload 审计（2026-09-06）

- 实际命令：在 `<user-home>/kmb-openkylin-validation-20260906` 执行 `bash scripts/build_deb.sh dist`，将构建 stdout/stderr、`dpkg-deb --info`、`dpkg-deb --contents` 和 SHA-256 写入 `runs/openkylin-validation-20260906/deb-release/`；随后对包清单扫描 `/runs/`、`credentials.env`、`.kmb-venv`、`.venv-*`、pip 缓存、研究缓存和 `.env`。
- 实际结果：命令退出码 `0`；生成 `dist/kylin-memory-bench_0.2.0_all.deb`；payload 审计输出 `deb_payload_audit=clean`。日志/产物位于 `runs/openkylin-validation-20260906/deb-release/build.stdout.log`、`build.stderr.log`、`package-info.txt`、`package-contents.txt`、`package.sha256`。
- 已完成：真实 openKylin VM `.deb` 构建、Debian metadata/contents 导出和敏感/无关内容排除核查。
- 未完成：安装、升级、安装后 CLI smoke、真实双 Agent wrapper/no-memory 对照、可重复性与卸载验证。
- 许可证边界：项目级 LICENSE 仍未选择；包内版权文件和 `NOTICE` 已明确标记为技术验收用途，不能据此主张对外再分发授权。
- 下一轮最高优先级：确认 VM 安装权限后安装该 `.deb` 并运行安装后 CLI 验证。

### 批次 38：发布文档/验收入口更新与安装权限检查（2026-09-06）

- 实际修改：`scripts/run_acceptance.sh` 允许 `memory_disabled` 真实后端基线参与正式流程，并在 stderr 明确提示其应与 wrapper/native 结果分层报告；更新 `README.md`、`docs/demo-script.md`、`docs/solution.md`、`CHANGELOG.md`，增加无记忆对照、Debian 生命周期、openKylin 3-5 分钟录屏命令和未完成边界。
- 实际命令：宿主机重新执行 `python -m unittest discover -s tests -v`，退出码 `0`，`36` 项通过。该批不调用云模型 API。
- 实际命令：通过 SSH 执行 `id` 和 `sudo -n true`。远端用户为 `uid=1000(<vm-user>)`，`sudo -n` 输出 `sudo_noninteractive=unavailable`；SSH 探测命令退出码 `0`，代表检查完成而非获得 sudo 权限。
- 已完成：无记忆基线可以进入统一正式验收入口；README、发布说明和录屏脚本已准备且未声称视频已录制。
- 客观阻塞：自动化 SSH 会话没有无交互 sudo，不能实际执行系统级 `dpkg -i`/`dpkg -r`。必须在 openKylin 桌面或终端中由可提权用户执行 `bash scripts/install_deb.sh ...` 和 `bash scripts/uninstall_deb.sh`；不能用无权限用户态解包冒充系统安装。
- 待确认假设：VM 本地操作员具有 sudo 权限且可在录屏时执行这两条命令；影响 `.deb` 系统级安装/升级/卸载验收，不影响已完成的包构建与源码级 VM 验证。
- 下一轮最高优先级：同步发布文档后重建包，并进行不需要 sudo 的解包 CLI smoke 与真实 wrapper/no-memory 对照。

### 批次 39：发布文档同步与 openKylin VM `.deb` 重建（2026-09-06）

- 实际命令：通过 SCP 同步 `scripts/run_acceptance.sh`、`README.md`、`CHANGELOG.md`、`docs/demo-script.md` 与 `docs/solution.md`；在 VM 执行 `bash -n scripts/run_acceptance.sh`，重建 `dist/kylin-memory-bench_0.2.0_all.deb`，导出 payload 清单并再次扫描禁止内容。
- 实际结果：同步/重建/审计批次退出码 `0`，输出 `deb_rebuild_and_audit=clean`；构建日志为 `runs/openkylin-validation-20260906/deb-release/rebuild.stdout.log`、`rebuild.stderr.log`，清单为 `rebuild-package-contents.txt`，哈希为 `rebuild-package.sha256`。
- 已完成：包内 README/文档与工作区发布说明保持同步，并再次确认没有运行产物、凭据、虚拟环境、缓存或研究缓存进入包。
- 未完成：安装后 smoke 与真实 Agent 对照尚未运行；无交互 sudo 阻塞仍存在。
- 下一轮最高优先级：增加可重定位的启动器验收入口，执行用户态解包 smoke，同时保持系统安装结论与其严格分离。

### 批次 40：openKylin VM 用户态解包 `.deb` CLI smoke（2026-09-06）

- 前置说明：该批使用 `dpkg-deb -x` 验证 payload，原因是自动化 SSH 用户没有非交互 sudo；它不是 `dpkg -i` 系统安装成功的替代证据。
- 实际命令：重新构建包后解包到 `runs/openkylin-validation-20260906/deb-release/unpacked-20260906/`；以 `KMB_HOME=<解包>/usr/share/kylin-memory-bench <解包>/usr/bin/kmb` 执行严格 suite validate、reference/flawed compare，并使用解包内 `verify_run.py --strict` 校验两个结果目录。
- 实际结果：构建、解包、严格校验、compare 和两个 `verify_run` 均退出码 `0`，最终输出 `unpacked_deb_smoke=valid`。结果位于 `runs/openkylin-validation-20260906/deb-release/unpacked-results/`；命令输出位于 `unpacked-validate.json`、`unpacked-compare.json`、`unpacked-verify-reference.json`、`unpacked-verify-flawed.json`。
- 事实边界：该 smoke 中的 reference/flawed 仅用于验证 `.deb` 内 CLI、套件、证据、评分和报告链；不是赛事真实 Agent 对比，也不替代历史 Grok/DeepSeek 真实运行。
- 已完成：在实际 openKylin VM 使用从 `.deb` 解出的 payload 运行 CLI 和严格结构验证。
- 未完成：仍未执行系统级 `dpkg -i`、升级和 `dpkg -r`；真实 wrapper/no-memory 对照尚未运行。
- 下一轮最高优先级：加载用户级受限凭据后，以同一 core suite 运行 Grok wrapper 与 Grok no-memory 的真实系统级基线对照。

### 批次 41：openKylin VM 真实 Grok wrapper/no-memory 基线对照（2026-09-06）

- 前置状态：远端 `~/.config/kmb/credentials.env` 仅检查可读性和 `600` 权限，返回 `credentials_metadata=ready`；未读取或输出任何密钥内容。
- 实际命令：在 VM 项目目录中以 `set -a; . "$HOME/.config/kmb/credentials.env"; set +a` 为单次进程加载凭据，执行 `.kmb-venv/bin/python -m kmb.cli compare --agents configs/agent-grok-memory.yaml configs/agent-grok-no-memory.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260906/grok-baseline/results --run-id grok-wrapper-vs-no-memory-20260906 --seed 42 --retries 1 --timeout 180`；结束后执行 `unset GROK_API_KEY DEEPSEEK_API_KEY`。CLI 实际退出码 `0`，耗时约 10 分钟；日志为 `grok-baseline/compare.stdout.log`、`compare.stderr.log`。
- 严格校验：对 `grok-memory-controller` 与 `grok-no-memory-baseline` 分别执行 `.kmb-venv/bin/python scripts/verify_run.py ... --strict`，两条命令均退出码 `0`；结果为 6 cases，JSONL/`result.json` 均结构有效。
- 实际结果（同一核心六案例、seed=42、retries=1、timeout=180）：`grok-memory-controller` 总分 `86.11`，六维 `100/100/66.67/100/50/100`，`system_level_wrapper_assisted`，`wrapper_memory_events=13`、`native_memory_events=0`。`grok-no-memory-baseline` 总分 `30.56`，六维 `50/0/33.33/0/50/50`，`no_memory_baseline`，`memory_disabled_events=14`、`wrapper_memory_events=0`、`native_memory_events=0`。
- 失败与边界：无记忆基线的 failure counts 为 `omission=4`、`stale_update=1`、`confusion=2`、`timeout=1`、`erroneous_reuse=1`；其 timeout 是实际云 API/运行超时证据，未被删除或伪装为稳定结果。模型请求/响应仍是 `source=model`；禁用/recall miss/动作阻断是 `source=runner,evidence_class=no_memory_baseline`；两者都不能证明 Grok 的模型原生记忆。
- 已完成：真实 API 后端在外部包装层启用与关闭下的可审计系统级对照、六能力评分、JSONL、双 Agent comparison JSON/Markdown/HTML/SVG 和严格结构校验。
- 部分完成：本次 baseline 有真实 timeout，尚未完成同配置第二次成功重复运行，不能报告运行结果完全稳定。
- 安全说明：凭据未出现在命令输出、结果、日志或本上下文包；仅在远端短生命周期环境变量中使用并在命令结束后 unset。
- 下一轮最高优先级：归档本轮结果和包至宿主工作区，执行无凭据的 `.deb` 安装权限验证/文档完整性检查，并保留需要 sudo 的系统安装、升级、卸载步骤。

### 批次 42：动作证据评分收紧与只读重评分工具（2026-09-06）

- 实际修改：`kmb/scoring.py` 新增可执行动作判定：被 `blocked`、显式 `executed=false`、`source=model` 未满足 `model_native_tool`，或 `source=provider_evidence` 的动作请求均不能通过 `action_path`、`action_tool` 或 `state_sequence` 的 reuse；这样无记忆基线不会把模型工具请求误计为已执行。
- 实际新增：`scripts/rescore_run.py` 从原始 `evidence.jsonl` 和套件生成新的 JSON/Markdown/HTML/SVG 结果目录，强制输出目录与源目录不同，原始证据和原始结果不覆盖。Debian 构建脚本与发布说明已纳入该工具。
- 实际新增测试：阻断动作和未证实模型工具请求的评分测试，以及只读重评分脚本测试。
- 实际命令：宿主机执行 `python -m unittest discover -s tests -v`，退出码 `0`，共 `39` 项测试通过。
- 已完成：评分规则与无记忆语义一致；为已有真实运行保留可审计重评分路径。
- 部分完成：尚未在 VM 重新生成受新规则影响的 Grok no-memory 结果，尚未重新构建/安装新包。
- 下一轮最高优先级：将评分修正和 `rescore_run.py` 同步到 VM，重评分 Grok no-memory 原始证据并记录新结果哈希。

### 批次 43：重评分审计字段修正与回归（2026-09-06）

- 实际修改：`scripts/rescore_run.py` 统计源 JSONL 中的真实 `error` 事件，将 timeout/missing_input/runtime_error 计入 `attempt_error_counts` 与失败汇总；不改变源 evidence 或运行结果。
- 实际新增测试：重评分测试加入 timeout 事件并断言 `attempt_error_counts`。
- 实际命令：宿主机执行 `python -m unittest discover -s tests -v`，退出码 `0`，共 `39` 项测试通过。
- 已完成：重评分工具能保留重试/异常审计信息，避免重评分时丢失真实 timeout 记录。
- 未完成：修正后的工具尚未在 VM 重新生成 no-memory 结果。
- 下一轮最高优先级：同步修正工具到 VM，生成并严格校验 `grok-no-memory-baseline` 的 rescored-v2 目录。

### 批次 44：openKylin VM Grok no-memory 结果只读重评分 v2（2026-09-06）

- 实际命令：同步 `kmb/scoring.py`、`scripts/rescore_run.py`、相关测试、Debian 构建脚本和启动器到 VM；执行 `.kmb-venv/bin/python -m unittest tests.test_scoring tests.test_scripts`（退出码 `0`，17 项通过）；重建 `.deb`；执行 `scripts/rescore_run.py` 从 `grok-baseline/results/grok-no-memory-baseline` 生成 `grok-baseline/rescored-v2/grok-no-memory-baseline`，并执行 `scripts/verify_run.py ... --strict`。
- 实际结果：重评分与严格校验退出码均为 `0`。v2 无记忆基线总分 `22.22`，六维 `retention=50.00`、`memory_recall=0.00`、`dynamic_update=33.33`、`similar_distinction=0.00`、`boundary=50.00`、`task_reuse=0.00`；`memory_disabled_events=14`、`wrapper_memory_events=0`、`native_memory_events=0`；失败计数 `omission=4`、`stale_update=1`、`confusion=2`、`erroneous_reuse=2`、`timeout=1`，`attempt_error_counts.timeout=1`。
- 证据路径：`runs/openkylin-validation-20260906/grok-baseline/rescored-v2/grok-no-memory-baseline/`（`result.json`、`evidence.jsonl`、Markdown/HTML/SVG、`verify.json`），重评分 stdout/stderr 位于同级 `rescored-v2.stdout.log`/`rescored-v2.stderr.log`。
- 解释边界：v2 只是对同一真实模型 JSONL 的确定性重新评分，未重新调用 API；它修正“未执行工具请求被计为 action_tool 成功”的评分问题，不能用来声称模型原生记忆。
- 已完成：评分修正已在 openKylin VM 经过测试、实际重评分和严格验证；原始结果仍保留供审计。
- 未完成：Debian 系统级安装/升级/卸载仍等待 sudo/root；DeepSeek no-memory 真实对照尚未运行；同配置 Grok 第二次 API 运行尚未完成。
- 下一轮最高优先级：将 v2 结果和最终包归档至宿主机，执行无凭据的结果/包审计，再决定是否在 VM 具备权限时完成系统级 dpkg 生命周期。

### 批次 45：Grok no-memory v2 对比报告与宿主机归档（2026-09-06）

- 实际命令：宿主机读取 Grok wrapper 原始 `result.json` 与 VM 重评分 v2 的 no-memory `result.json`，调用 `kmb.report.write_compare` 生成 `grok-baseline/rescored-v2/comparison/` 的 JSON/Markdown/HTML/SVG 对比报告；随后执行 `scripts/verify_run.py .../grok-no-memory-baseline --strict`。
- 实际结果：对比报告生成命令退出码 `0`；严格校验退出码 `0`，返回 `6 cases`、`71 evidence_events`、run_id `grok-wrapper-vs-no-memory-20260906`。v2 baseline 与 wrapper 的多维分数均写入对比文件；源运行目录保持不变。
- 归档：VM 的 `grok-baseline/rescored-v2/` 和 `dist/kylin-memory-bench_0.2.0_all.deb` 已复制到宿主机同名路径；未复制凭据文件。
- 已完成：Grok wrapper/no-memory 的可读双模式对比报告和严格校验。
- 未完成：DeepSeek no-memory 真实对照、Debian 系统级安装/升级/卸载和录屏视频仍待完成。
- 下一轮最高优先级：在 VM 使用同一用户级凭据运行 DeepSeek no-memory baseline，随后重评分并纳入对比报告。

### 批次 46：openKylin VM DeepSeek no-memory baseline 真实运行（2026-09-06）

- 前置状态：远端用户级凭据文件只检查 `600` 权限和可读性，返回 `credentials_metadata=ready`；没有读取或输出密钥值。
- 实际命令：在 VM 中以 `set -a; . "$HOME/.config/kmb/credentials.env"; set +a` 单次进程加载凭据，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-no-memory.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260906/deepseek-baseline/results/deepseek-no-memory-baseline --run-id deepseek-no-memory-20260906 --seed 42 --retries 1 --timeout 180`；结束后 unset `GROK_API_KEY`/`DEEPSEEK_API_KEY`。CLI 退出码 `0`，stdout/stderr 为 `deepseek-baseline/run.stdout.log`、`run.stderr.log`。
- 严格校验：执行 `.kmb-venv/bin/python scripts/verify_run.py runs/openkylin-validation-20260906/deepseek-baseline/results/deepseek-no-memory-baseline --strict`，退出码 `0`，校验结果记录在 `deepseek-baseline/verify.json`。
- 实际结果：6 个核心案例、总分 `38.89`；六维 `retention=50.00`、`memory_recall=0.00`、`dynamic_update=33.33`、`similar_distinction=50.00`、`boundary=100.00`、`task_reuse=0.00`；失败计数 `omission=3`、`stale_update=1`、`confusion=1`、`erroneous_reuse=2`；`mode=no_memory_baseline`、`memory_disabled_events=14`、`wrapper_memory_events=0`、`native_memory_events=0`、`model_claims_unverified=14`。
- 事实边界：结果是 DeepSeek v4 flash 真实模型后端在外部包装层关闭时的系统级基线；禁用/recall miss/动作阻断为 runner baseline 证据，不能归因于模型原生记忆。该批未发现 timeout 或重试错误。
- 已完成：第二款真实后端的 no-memory 六案例运行和严格结构验证。
- 未完成：尚未生成包含两款模型各自 wrapper 与 no-memory 的统一四轨 comparison；系统级 `.deb` 安装/升级/卸载和桌面视频仍待完成。
- 下一轮最高优先级：归档 DeepSeek baseline，生成 Grok/DeepSeek wrapper-vs-no-memory 四轨比较报告并更新赛事总报告。

### 批次 47：四轨 wrapper/no-memory 重评分与统一比较（2026-09-06）

- 实际命令：在 VM 对既有 Grok wrapper、Grok no-memory、DeepSeek wrapper、DeepSeek no-memory 四个原始运行目录分别执行 `scripts/rescore_run.py`，输出到 `runs/openkylin-validation-20260906/four-mode-rescored/`；对四个新目录分别执行 `scripts/verify_run.py --strict`；读取四个 `result.json` 调用 `kmb.report.write_compare` 生成统一 `comparison.json`、`comparison.md`、`comparison.html` 和四个 SVG 雷达图。未重新调用 API。
- 实际结果：四个重评分和四条严格校验均退出码 `0`。Grok wrapper `86.11`、Grok no-memory `22.22`；DeepSeek wrapper `86.11`、DeepSeek no-memory `38.89`。四者均为 6 个核心案例；wrapper 轨道 `native_memory_events=0`、`wrapper_memory_events=13`，no-memory 轨道 `native_memory_events=0`、`wrapper_memory_events=0`、`memory_disabled_events=14`。
- 解释边界：统一比较使用当前“未执行/被阻断 action 不计分”的评分规则，源证据不变；wrapper 分数仅是模型后端 + 外部控制器的系统级行为，no-memory 分数是同一后端关闭外部记忆的基线，均不证明模型原生记忆。
- 未完成：四轨结果尚未复制到宿主机，赛事最终报告尚未加入 DeepSeek no-memory 表格；系统级 `.deb` 生命周期仍受 sudo 权限限制。
- 下一轮最高优先级：复制四轨比较产物到宿主机，更新 `final-event-report.md` 与 README 的最终路径和分数。

### 批次 48：DeepSeek no-memory 重复性验证与包内最小测试集（2026-09-06）

- 实际命令：在 openKylin VM 以与批次 46 完全相同的 `agent-deepseek-no-memory.yaml`、`suites/core-zh.yaml`、seed `42`、retries `1`、timeout `180` 运行第二次真实 API 批次，运行 ID 为 `deepseek-no-memory-repeat-20260906`；执行 `verify_run.py --strict`，再读取首轮/重复轮 `result.json` 的 overall、六维、failure_counts 和 observability 作严格相等比较。
- 实际结果：重复 CLI 退出码 `0`，严格校验退出码 `0`；比较字段 `equal=true`。两轮均为总分 `38.89`、六维 `50/0/33.33/50/100/0`、失败 `omission=3, stale_update=1, confusion=1, erroneous_reuse=2`、`no_memory_baseline` 与 14 个禁用事件。该结论仅覆盖该 DeepSeek no-memory 配置的两次运行，不泛化为所有云 API 或所有模式绝对稳定。
- 实际修改：新增包内 `packaging/deb/smoke_test.py`，覆盖 strict suite validate 和 reference/flawed 的离线 compare/JSON/HTML 产物；`build_deb.sh` 打包该最小测试集，`verify_deb.sh` 在包安装后先执行它。该测试明确不代表真实 Agent。
- 实际命令：宿主机以 `KMB_HOME`/`PYTHONPATH` 运行 `python packaging/deb/smoke_test.py`，退出码 `0`，2 项通过；执行 `python -m unittest discover -s tests -v`，退出码 `0`，39 项通过；执行五个 Debian 脚本的 `bash -n`，退出码 `0`。
- 已完成：一条真实配置的重复运行稳定性证据，及包内最小离线测试集。
- 未完成：最终包尚未因新增 smoke 测试在 VM 重建/解包验证；`dpkg -i/-r` 仍需要 sudo/root。
- 下一轮最高优先级：同步 smoke 测试/最终文档到 VM，重建 `.deb` 并从解包 payload 运行包内 smoke 测试。

### 批次 49：最终 Debian payload smoke（2026-09-06）

- 实际命令：同步 `packaging/deb/smoke_test.py`、最终 `build_deb.sh`/`verify_deb.sh`、发布文档及评分重算脚本到 VM；执行 `bash -n`、VM 侧 `tests.test_scoring`/`tests.test_scripts`（17 项通过），重建 `dist/kylin-memory-bench_0.2.0_all.deb`，使用 `dpkg-deb -x` 解包到 `runs/openkylin-validation-20260906/deb-release/unpacked-final/`，以 `KMB_HOME`/`PYTHONPATH` 执行包内 `smoke_test.py`。
- 实际结果：同步、脚本语法、17 项 VM 回归、重建、解包和包内 2 项 smoke 测试均退出码 `0`；输出 `final_deb_unpacked_smoke=valid`。日志：`deb-release/package-smoke-rebuild.stdout.log`、`package-smoke-rebuild.stderr.log`、`unpacked-package-smoke.log`；包仍为 `dist/kylin-memory-bench_0.2.0_all.deb`。
- 事实边界：这是 openKylin VM 上的用户态 payload smoke，验证包内容、CLI、六案例套件、离线评分和报告链；自动化 SSH 用户仍无 sudo，因此不等价于 `dpkg -i` 系统安装或 `dpkg -r` 卸载。
- 已完成：最终包内容与包内最小测试集在 openKylin VM 可运行。
- 未完成：系统级安装/升级/卸载生命周期、桌面演示视频；项目级 LICENSE 仍待负责人选择。
- 下一轮最高优先级：在 openKylin 桌面或具备 sudo/root 的终端执行 `scripts/install_deb.sh`、`scripts/verify_deb.sh`、新版本 `scripts/upgrade_deb.sh` 和 `scripts/uninstall_deb.sh`，保存 dpkg 状态与退出码。

### 批次 50：最终赛事报告同步与四轨事实更新（2026-09-06）

- 实际修改：更新 `runs/openkylin-validation-20260906/final-event-report.md`，加入四轨 wrapper/no-memory 当前评分表、DeepSeek no-memory 重复性证据、Debian 包构建与用户态 payload smoke 事实，并更正早期“无记忆基线/`.deb` 尚未完成”的历史待办措辞；没有覆盖任何原始运行目录。
- 实际结果：报告当前明确记录 Grok wrapper `86.11`、Grok no-memory v2 `22.22`、DeepSeek wrapper `86.11`、DeepSeek no-memory `38.89`；四轨均为系统级/基线观测，原生记忆事件均为 0。重复运行的 DeepSeek no-memory 两次结果字段完全一致。
- 已完成：最终赛事报告与当前真实产物路径、评分和能力边界一致；仍明确标注 `.deb` 系统级 dpkg 生命周期和桌面视频未完成。
- 未完成：无交互 sudo 的 VM 自动化通道无法完成 `dpkg -i/-r`；项目级 LICENSE 尚未选择；未录制视频。
- 待确认假设：具备 sudo/root 的 openKylin 桌面操作员可按 `docs/deb-release.md` 执行系统包生命周期；不影响已完成 payload smoke 和真实 Agent 证据。
- 下一轮最高优先级：在具备 sudo/root 的 openKylin 终端完成 `.deb` 安装、验证、升级和卸载，随后录制 3-5 分钟桌面演示。

### 批次 51：最终发布文档、包哈希与一致性审计（2026-09-06）

- 实际修改：新增根目录 `.gitignore`，排除 `.env`/凭据、虚拟环境、缓存、`runs/`、`dist/` 和字节码；更新 `README.md`、`docs/solution.md`、`docs/evidence-protocol.md`、`docs/agent-candidates.md`，更正历史 VM 状态并说明 no-memory 事件与动作执行边界；新增包内 smoke 测试后最终包已重新构建。
- 实际命令：宿主机执行全量 `python -m unittest discover -s tests -v`，退出码 `0`，39 项通过；`bash -n` 检查五个 Debian 脚本退出码 `0`；`python packaging/deb/smoke_test.py` 在 KMB_HOME/PYTHONPATH 下退出码 `0`，2 项通过。
- 实际命令：VM 同步文档/包脚本后执行 `bash scripts/build_deb.sh dist`、`dpkg-deb --info`、`dpkg-deb --contents` 和禁止内容扫描，退出码 `0`，输出 `final_deb_payload_audit=clean`；最终包复制到宿主机 `dist/kylin-memory-bench_0.2.0_all.deb`。
- 实际一致性结果：宿主机与 VM `.deb` SHA-256 均为 `48c07c61a56537127bf08b899f644c432ff524d894efd9e70fb8dd2cf6c3b3da`，大小 `52608` 字节；四轨结果分数与最终赛事报告一致；密钥模式扫描输出 `secret_pattern_scan=clean`；必需 payload 条目（两份 no-memory 配置、`rescore_run.py`、包内 smoke 测试）均存在。
- 实际文档更新：`docs/openkylin-validation-runbook.md` 现记录 openKylin 2.0 SP2 VM 的已完成 CLI/真实运行和 `.deb` payload smoke，保留系统级 dpkg 生命周期与桌面视频为待执行事项，并给出明确命令。
- 已完成：代码、测试、no-memory 双后端真实结果、四轨报告、Debian 构建、payload smoke、发布文档和安全审计均有实际证据。
- 未完成：系统级 `dpkg -i`/升级/`dpkg -r` 尚无 sudo/root；3-5 分钟桌面演示视频未录制；项目级 LICENSE 未最终选择。
- 下一轮最高优先级：在具备 sudo/root 的 openKylin 桌面终端执行 Debian 安装、验证、升级、卸载并保存退出码；随后按 `docs/demo-script.md` 录制视频。

### 批次 52：openKylin 发布文档同步与最终 `.deb` 哈希确认（2026-09-06）

- 实际修改：更新 `docs/openkylin-validation-runbook.md`，将 openKylin 2.0 SP2 VM 的已完成 CLI/真实 Agent/用户态 payload smoke 与系统级 dpkg 权限阻塞分开记录，并补充安装、验证、升级、卸载命令。
- 实际命令：将该 runbook 同步至 VM；执行 `bash scripts/build_deb.sh dist`、`dpkg-deb --contents` 及禁止内容扫描，VM 退出码 `0`，输出 `documented_deb_audit=clean`；包复制回宿主机并与 VM 哈希比较。
- 实际结果：最终 `.deb` 宿主机/VM SHA-256 均为 `f82210ad1386e814042f3f5337d8e0e213c11bb87b1d98af244702afcff848ad`，大小 `52836` 字节，哈希匹配。该包包含最新 runbook、代码、no-memory 配置和包内 smoke 测试，仍无密钥/运行产物。
- 已完成：工作区与 VM 的最终发布包和验证文档一致；安全/结果/报告审计通过。
- 未完成：系统级 Debian 安装/升级/卸载未执行（自动化 SSH 无 sudo/root）；3-5 分钟 openKylin 桌面视频未录制；项目级 LICENSE 未选择。
- 下一轮最高优先级：在具备 sudo/root 的 openKylin 桌面终端执行 `install_deb.sh`、`verify_deb.sh`、版本升级和 `uninstall_deb.sh`，保存 dpkg 状态与退出码。

### 批次 53：赛事发布收尾审计（2026-09-06）

- 实际命令：宿主机执行 `python -m unittest discover -s tests -v`，退出码 `0`，39 项通过；执行 `bash -n scripts/build_deb.sh scripts/install_deb.sh scripts/upgrade_deb.sh scripts/uninstall_deb.sh scripts/verify_deb.sh`，退出码 `0`；在工作区（排除 `.deb`、运行、缓存、字节码）执行完整 token 前缀扫描，输出 `secret_token_pattern_scan=clean`；读取四轨 `result.json`、comparison JSON 和最终赛事报告，输出 `four_mode_artifacts=valid`、`stale_status_scan=clean`。
- 实际结果：四轨最终产物均为 6 cases、均有 `evidence.jsonl`；comparison 包含 4 个结果条目；最终报告包含 `system_level_wrapper_assisted` 与 `no_memory_baseline` 边界说明。README、runbook、证据协议、方案说明和 Agent 清单未保留与当前 VM 事实冲突的旧状态。
- 安全说明：README 中的 `GROK_API_KEY`/`DEEPSEEK_API_KEY` 仅为无值占位示例；精确 `sk-/ark-` 长 token 扫描无命中。最终 `.deb` 哈希与 VM 产物已在批次 52 确认一致。
- 已完成：代码实现、测试、真实 Grok/DeepSeek 核心/对抗与 no-memory 运行、四轨评分/证据/报告、Debian 构建和用户态 payload smoke、文档及安全审计。
- 未完成：VM 自动化账号无非交互 sudo，未实际执行系统级 `.deb` 安装/升级/卸载；3-5 分钟桌面视频未录制；项目级 LICENSE 未选择；Grok no-memory 一次运行有真实 timeout，DeepSeek 重复运行仅证明该配置两次一致。
- 下一轮最高优先级：在具备 sudo/root 的 openKylin 桌面终端完成 Debian 系统包生命周期并保存退出码，然后按 `docs/demo-script.md` 录制视频。

### 批次 54：发布收尾前置探测与许可证库存（2026-09-06）

- 实际命令：通过 SSH 连接 `<vm-user>@192.168.182.129:2222` 执行 `id -u; id -nG`、读取 `/etc/os-release`、`uname -m`、`python3 --version`、`python3 -m pip --version`、setuptools 导入检查、桌面变量/录屏工具探测、`df -h /home`、项目/虚拟环境存在性检查和凭据文件元数据检查；另执行 `timeout -k 1s 4s sudo -n true` 复核非交互 sudo。
- 实际结果：VM 为 openKylin 2.0 SP2、x86_64、Python 3.12.2；系统 `/usr/bin/python3` 未提供 pip/setuptools，但项目 `.kmb-venv` 存在；`~/.config/kmb/credentials.env` 权限为 `600` 且未读取内容；`ffmpeg=/usr/bin/ffmpeg`，`obs`、`gnome-screenshot`、`wf-recorder` 不存在；SSH 会话无 `DISPLAY`/Wayland 变量；`/home` 约剩余 21 GB。sudo 探测退出码 `137`（4 秒强制终止），结论为自动化 SSH 用户无法执行非交互 sudo，不能据此声称完成系统级 dpkg 安装/升级/卸载。
- 实际命令：宿主机执行 `python scripts/audit_reference_licenses.py --out runs/license-audit-20260906/inventory.json`。
- 实际结果：许可证库存生成命令退出码 `0`，结果文件为 `runs/license-audit-20260906/inventory.json`；脚本明确为文件库存而非法律分类，参考仓库数据/Prompt/传递依赖仍标记 `needs_manual_review=true`。
- 已完成：确认当前 VM、包生命周期自动化权限和录屏前置条件；生成本轮许可证审计库存。
- 部分完成：可在 VM 用户态继续执行 no-memory 真实批次和 payload 验证；桌面录屏需桌面终端，系统级 `.deb` 生命周期需 root/sudo。
- 未完成：系统级 `.deb` 安装/升级/卸载、实际桌面视频、项目级 LICENSE 选择和 Grok no-memory 5 批统计仍未完成。
- 客观阻塞：自动化 SSH 通道没有可用非交互 sudo；当前 SSH 会话不是桌面图形会话。
- 待确认假设：具备 sudo/root 的 openKylin 桌面操作员可执行既有 `docs/deb-release.md` 命令；项目负责人/法务仍需确认最终项目级许可证。
- 下一轮最高优先级：在不覆盖历史结果的前提下运行至少 5 个 Grok no-memory 真实重复批次并生成统计；随后在具备 root 的终端完成系统级包生命周期。

### 批次 55：Grok no-memory 重复批次 02（2026-09-06）

- 实际命令：在 openKylin VM 项目目录中单次进程加载 `~/.config/kmb/credentials.env`，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-no-memory.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-02 --run-id grok-no-memory-repeat-02-20260906 --seed 42 --retries 1 --timeout 180`；命令结束后清除 `GROK_API_KEY`/`DEEPSEEK_API_KEY`。
- 实际结果：CLI 退出码 `0`；`.kmb-venv/bin/python scripts/verify_run.py runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-02 --strict` 退出码 `0`；结果目录包含 6 cases、70 个证据事件、14 个模型响应，`mode=no_memory_baseline`，`native_memory_events=0`。总分 `30.56`，六维 `retention=50.00`、`memory_recall=0.00`、`dynamic_update=33.33`、`similar_distinction=50.00`、`boundary=50.00`、`task_reuse=0.00`；失败计数 `omission=4`、`stale_update=1`、`confusion=1`、`erroneous_reuse=2`。
- 延迟证据：从 `evidence.jsonl` 的 `model_response.data.elapsed_ms` 计算均值 `40425.9 ms`、最小 `11661.2 ms`、最大 `102329.1 ms`；这些是本批实际观测，不代表服务稳定性结论。
- 证据路径：VM `runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-02/`，含 `result.json`、`evidence.jsonl`、`result.md`、`result.html`、`radar.svg`、`run.stdout.log` 和 `run.stderr.log`。
- 解释边界：该批为 Grok 4.6 API + 外部包装层关闭的系统级无记忆基线；模型文本事件和 runner 禁用事件均不能证明模型原生长期记忆。
- 已完成：重复批次 02 的真实运行、严格结构校验和延迟/失败统计。
- 未完成：Grok no-memory 目标至少 5 个新增批次尚未收齐；系统级 `.deb` 生命周期、桌面视频和项目级 LICENSE 仍未完成。
- 客观阻塞：本批之后的重复运行受云 API 响应时间影响，需逐批等待并保留超时/错误证据。
- 下一轮最高优先级：完成 Grok no-memory 重复批次 01 的实际收敛校验，并继续新增批次 03。

### 批次 56：Grok no-memory 重复批次 01（2026-09-06）

- 实际命令：在 openKylin VM 中单次进程加载用户级凭据并执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-no-memory.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-01 --run-id grok-no-memory-repeat-01-20260906 --seed 42 --retries 1 --timeout 180`；进程结束后 unset API 密钥环境变量。
- 实际结果：结果目录已生成，CLI stdout 报告退出码 `0`；`.kmb-venv/bin/python scripts/verify_run.py runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-01 --strict` 退出码 `0`。6 cases、70 evidence events，运行总分 `38.89`，输出模式 `no_memory_baseline`，未产生原生记忆事件。该批结果和证据位于 VM `runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-01/`。
- 事实边界：该结果为 Grok 4.6 API + 外部包装层关闭的系统级基线；模型文本和禁用事件不能证明模型原生长期记忆能力。
- 已完成：重复批次 01 真实运行、结果生成和严格结构校验。
- 部分完成：与批次 02 的分数不同，目标 5 个新增批次的统计尚未收齐。
- 未完成：批次 03-05、聚合统计、系统级 `.deb` 生命周期、桌面视频和项目级 LICENSE 仍未完成。
- 下一轮最高优先级：运行 Grok no-memory 重复批次 03 并保留实际延迟、失败和证据文件。

### 批次 57：Grok no-memory 重复批次 03（2026-09-06）

- 实际命令：在 openKylin VM 中单次进程加载用户级凭据，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-no-memory.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-03 --run-id grok-no-memory-repeat-03-20260906 --seed 42 --retries 1 --timeout 180`；结束后清除密钥环境变量。
- 实际结果：CLI 退出码 `0`；严格校验命令 `.kmb-venv/bin/python scripts/verify_run.py runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-03 --strict` 退出码 `0`。6 cases、70 evidence events、14 model responses，`mode=no_memory_baseline`，总分 `27.78`；六维 `retention=50.00`、`memory_recall=0.00`、`dynamic_update=66.67`、`similar_distinction=0.00`、`boundary=50.00`、`task_reuse=0.00`；失败计数 `omission=4`、`stale_update=1`、`confusion=1`、`erroneous_reuse=2`。
- 延迟证据：`model_response.data.elapsed_ms` 均值 `33118.3 ms`、最小 `3666.4 ms`、最大 `82483.6 ms`。
- 证据路径：VM `runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-03/`，包含 `result.json`、`evidence.jsonl`、Markdown/HTML/SVG 报告及 stdout/stderr 日志。
- 事实边界：这是 Grok 4.6 API 在外部包装层关闭时的系统级基线，不证明模型原生长期记忆。
- 已完成：重复批次 03 的真实运行、严格校验和延迟/失败统计。
- 未完成：目标至少 5 个新增批次尚缺 04-05 及聚合统计；系统级 `.deb` 生命周期、桌面视频和项目级 LICENSE 仍未完成。
- 下一轮最高优先级：运行 Grok no-memory 重复批次 04。

### 批次 58：Grok no-memory 重复批次 04（2026-09-06）

- 实际命令：在 openKylin VM 中单次进程加载用户级凭据，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-no-memory.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-04 --run-id grok-no-memory-repeat-04-20260906 --seed 42 --retries 1 --timeout 180`；结束后清除密钥环境变量。
- 实际结果：CLI 退出码 `0`；严格校验命令 `.kmb-venv/bin/python scripts/verify_run.py runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-04 --strict` 退出码 `0`。6 cases、70 evidence events、14 model responses，`mode=no_memory_baseline`，总分 `27.78`；六维 `retention=50.00`、`memory_recall=0.00`、`dynamic_update=66.67`、`similar_distinction=0.00`、`boundary=50.00`、`task_reuse=0.00`；失败计数 `omission=4`、`stale_update=1`、`confusion=1`、`erroneous_reuse=2`。
- 延迟证据：`model_response.data.elapsed_ms` 均值 `20649.1 ms`、最小 `6611.0 ms`、最大 `42657.4 ms`。
- 证据路径：VM `runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-04/`，包含 `result.json`、`evidence.jsonl`、Markdown/HTML/SVG 报告及 stdout/stderr 日志。
- 事实边界：这是 Grok 4.6 API 在外部包装层关闭时的系统级基线，不证明模型原生长期记忆。
- 已完成：重复批次 04 的真实运行、严格校验和延迟/失败统计。
- 未完成：目标至少 5 个新增批次尚缺 05 及聚合统计；系统级 `.deb` 生命周期、桌面视频和项目级 LICENSE 仍未完成。
- 下一轮最高优先级：运行 Grok no-memory 重复批次 05，并在其后生成 01-05 的稳定性汇总。

### 批次 59：Grok no-memory 重复批次 05（2026-09-06）

- 实际命令：在 openKylin VM 中单次进程加载用户级凭据，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-no-memory.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-05 --run-id grok-no-memory-repeat-05-20260906 --seed 42 --retries 1 --timeout 180`；结束后清除密钥环境变量。
- 实际结果：CLI 退出码 `0`；严格校验命令 `.kmb-venv/bin/python scripts/verify_run.py runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-05 --strict` 退出码 `0`。6 cases、70 evidence events、14 model responses，`mode=no_memory_baseline`，总分 `30.56`；六维 `retention=50.00`、`memory_recall=0.00`、`dynamic_update=33.33`、`similar_distinction=50.00`、`boundary=50.00`、`task_reuse=0.00`；失败计数 `omission=3`、`stale_update=1`、`confusion=2`、`erroneous_reuse=2`。
- 延迟证据：`model_response.data.elapsed_ms` 均值 `25342.7 ms`、最小 `5177.3 ms`、最大 `87501.3 ms`。
- 证据路径：VM `runs/openkylin-validation-20260906/grok-no-memory-repeats/repeat-05/`，包含 `result.json`、`evidence.jsonl`、Markdown/HTML/SVG 报告及 stdout/stderr 日志。
- 事实边界：这是 Grok 4.6 API 在外部包装层关闭时的系统级基线，不证明模型原生长期记忆。
- 已完成：第 5 个新增重复批次的真实运行、严格校验和延迟/失败统计；01-05 新增批次已全部产生结果目录。
- 未完成：01-05 跨批次聚合报告、系统级 `.deb` 生命周期、桌面视频和项目级 LICENSE 仍未完成。
- 下一轮最高优先级：生成并严格校验 01-05 的均值、标准差、极值、成功率、失败率、失败类型和跨批次一致性汇总。

### 批次 60：重复统计脚本与回归测试（2026-09-06）

- 实际修改：新增 `scripts/aggregate_repeats.py`，只读聚合重复运行的 `result.json`/`evidence.jsonl`，输出均值、样本标准差、最小/最大、执行成功率、行为案例通过率、六维统计、延迟统计、失败类型合计和跨批次一致性；更新 `scripts/build_deb.sh` 以纳入该工具；新增 `tests/test_scripts.py` 聚合脚本测试。
- 实际命令：宿主机执行 `python -m unittest discover -s tests -v`。
- 实际结果：退出码 `0`，共 `40` 项测试通过（新增聚合统计测试通过）；未读取或写入任何凭据。
- 已完成：聚合逻辑和回归测试在宿主机通过；原始运行目录不会被修改。
- 未完成：尚未在 VM 同步新脚本并对 01-05 真实批次生成最终汇总；系统级 `.deb` 生命周期、桌面视频和项目级 LICENSE 仍未完成。
- 下一轮最高优先级：归档 VM 的 Grok no-memory repeat-01..05 结果到宿主机，并执行聚合脚本及严格审计。

### 批次 61：Grok no-memory 五批聚合与归档（2026-09-06）

- 实际命令：VM 同步 `scripts/aggregate_repeats.py` 后执行 `.kmb-venv/bin/python scripts/aggregate_repeats.py runs/openkylin-validation-20260906/grok-no-memory-repeats --out runs/openkylin-validation-20260906/grok-no-memory-repeats/summary.json`；命令退出码 `0`，返回 `batch_count=5`。随后以 `scp -r` 复制该目录到宿主工作区。
- 实际结果：5/5 批次均通过 `verify_run.py --strict`，每批 6 cases、70 evidence events、14 model responses，执行成功率 `100%`，行为案例通过率 `3.33%`。Overall 均值 `31.114`、样本标准差 `4.5637`、最小 `27.78`、最大 `38.89`；模型响应延迟总体均值 `33524.9529 ms`、样本标准差 `27627.8707 ms`、最小 `3666.4 ms`、最大 `119704.2 ms`。六维统计和失败类型合计已写入 `runs/openkylin-validation-20260906/grok-no-memory-repeats/summary.json` 与 `summary.md`。
- 失败类型合计：`omission=19`、`stale_update=5`、`confusion=5`、`erroneous_reuse=10`；5 批 overall 并非全部相等，仅 1 批与首批 overall 相同。
- 解释边界：所有批次均为 Grok 4.6 API + 外部包装层关闭的系统级 no-memory 基线；`native_memory_events=0`，不证明模型原生长期记忆。
- 已完成：新增 5 个真实运行批次、严格验证、VM 到宿主归档和聚合统计。
- 未完成：系统级 `.deb` 安装/升级/卸载、桌面视频和项目级 LICENSE 仍未完成。
- 下一轮最高优先级：完成许可证候选决策文档和最终包重建/内容审计。

### 批次 62：许可证候选决策与发布工具回归（2026-09-06）

- 实际修改：新增 `docs/license-decision.md`，记录项目级 MIT/Apache-2.0/GPL-3.0-or-later 候选、已确认事实和负责人/法务确认步骤；更新 `README.md` 与 `docs/deb-release.md` 指向候选决策文档；新增 `scripts/aggregate_repeats.py` 并纳入 `scripts/build_deb.sh`；新增聚合脚本回归测试。
- 实际命令：宿主机执行 `python scripts/audit_reference_licenses.py --out runs/license-audit-20260906/inventory-final.json`、`python -m unittest discover -s tests -v`、工作区 token 前缀扫描。
- 实际结果：许可证库存命令退出码 `0`，文件为 `runs/license-audit-20260906/inventory-final.json`；全量测试退出码 `0`，40 项通过；敏感令牌扫描输出 `secret_token_pattern_scan=clean`。审计仍将参考项目数据、Prompt 和传递依赖标为 `needs_manual_review=true`，未把候选许可证写成最终许可证。
- 已完成：候选许可证决策材料、README/发布说明入口、重复统计工具和宿主回归验证。
- 未完成：最终项目级 `LICENSE` 未经负责人确认不能落地；含新聚合工具的 VM `.deb` 尚未重建和 smoke；系统级包生命周期和桌面视频仍未完成。
- 待确认假设：负责人确认 MIT 后，才可创建根目录 `LICENSE` 并同步 Debian copyright；在此之前技术包不代表公开再分发授权。
- 下一轮最高优先级：在 openKylin VM 重建纳入 `aggregate_repeats.py` 和许可证候选文档的 `.deb`，完成 payload 审计与 smoke。

### 批次 63：含稳定性工具的 Debian 包重建（2026-09-06）

- 实际修改：新增 `scripts/record_deb_lifecycle.sh`（root/sudo 可用时记录安装、验证、升级、升级后验证、卸载和残留检查的逐步 stdout/stderr/退出码）与 `scripts/record_desktop_demo.sh`（桌面 `DISPLAY` + ffmpeg 条件下录屏并生成 SHA256/媒体信息）；更新 `README.md`、`docs/demo-script.md` 和 `docs/openkylin-validation-runbook.md` 的可执行入口。新增脚本未改动评测/评分逻辑。
- 实际命令：宿主机执行 `bash -n` 检查 7 个 Debian/录制脚本、`python -m unittest discover -s tests -v`、`python scripts/aggregate_repeats.py ... --out .../summary-host.json`；全部退出码 `0`，40 项测试通过，宿主归档可只读重现 5 批统计。
- 实际命令：同步发布脚本/文档至 VM，执行 `bash -n scripts/build_deb.sh scripts/record_deb_lifecycle.sh scripts/record_desktop_demo.sh`，以及 `KMB_DEB_VERSION=0.2.0+test1 bash scripts/build_deb.sh dist`。
- 实际结果：VM 构建退出码 `0`；升级候选包为 `dist/kylin-memory-bench_0.2.0+test1_all.deb`，SHA-256 `92a9e4e020335e2052cf618c81c4ecd75494b32d8b42e659a50796d4769fcceb`。payload 目录包含 `docs/license-decision.md` 与 `scripts/aggregate_repeats.py`；构建不包含凭据、运行产物或缓存。候选包的系统级升级尚未执行。
- 已完成：稳定性工具、带日志的生命周期/录屏辅助材料、宿主测试和 openKylin VM 的升级候选 `.deb` 构建。
- 未完成：候选包 payload smoke、系统级 `dpkg -i`/升级/卸载、实际桌面视频和最终项目 LICENSE。
- 客观阻塞：当前 SSH 用户 sudo 探测退出码 `137`，无 `DISPLAY`/Wayland，会话不能执行系统安装或桌面录制。
- 下一轮最高优先级：对升级候选 `.deb` 完成 VM 用户态解包 smoke；随后验证录制辅助脚本在无图形会话时的失败边界。

### 批次 64：升级候选 Debian payload smoke（2026-09-07）

- 实际命令：在 VM 对 `dist/kylin-memory-bench_0.2.0+test1_all.deb` 执行 `dpkg-deb -x` 到 `runs/openkylin-validation-20260906/deb-release/candidate-unpacked/`，以 `KMB_HOME`/`PYTHONPATH` 指向解包 payload 运行包内 `tests/smoke_test.py -v`，并执行包内 `scripts/aggregate_repeats.py --help`。
- 实际结果：候选包 payload smoke 退出码 `0`；2 项包内测试通过，覆盖严格核心六案例校验与离线 reference/flawed CLI 报告链；聚合工具帮助页正常返回。宿主归档路径为 `runs/openkylin-validation-20260906/deb-release/candidate-unpacked/`。候选包宿主 SHA-256 与 VM 一致，为 `92a9e4e020335e2052cf618c81c4ecd75494b32d8b42e659a50796d4769fcceb`。
- 事实边界：reference/flawed 仅用于包内离线 smoke，不是赛事真实 Agent 对比；`dpkg-deb -x` 不能替代 `dpkg -i` 系统安装或升级验证。解包后执行 Python 生成的 `__pycache__` 只存在于验证目录，不在构建时的 package contents 审计结果中。
- 已完成：升级候选 `.deb` 的 openKylin VM payload/CLI/最小测试/聚合工具验证和宿主归档。
- 未完成：系统级 `.deb` 安装、升级、卸载仍需要 sudo/root；桌面视频和最终项目 LICENSE 仍未完成。
- 下一轮最高优先级：验证录屏脚本的无桌面失败边界并更新赛事总报告。

### 批次 65：桌面录屏前置失败边界验证（2026-09-07）

- 实际命令：在当前无图形 SSH 会话执行 `DISPLAY= WAYLAND_DISPLAY= bash scripts/record_desktop_demo.sh runs/openkylin-validation-20260906/desktop-demo-probe 1`，保存 stdout/stderr 后检查视频文件是否存在。
- 实际结果：脚本退出码 `2`，输出 `video=not_created`；未生成 `.mp4`。该行为符合脚本对缺失 `DISPLAY` 的显式前置检查，证明当前自动化会话不能录制 openKylin 桌面视频。
- 已完成：录制辅助脚本的无桌面安全失败路径和宿主归档 `runs/openkylin-validation-20260906/desktop-demo-probe/`。
- 未完成：3-5 分钟桌面演示视频未录制，必须在实际图形桌面会话运行该脚本；系统级 `.deb` 生命周期和最终项目 LICENSE 仍未完成。
- 客观阻塞：SSH 会话没有 `DISPLAY`/Wayland，且无非交互 sudo（最近探测退出码 `137`）。
- 下一轮最高优先级：在具备 sudo/root 与桌面会话的 openKylin 终端执行 `record_deb_lifecycle.sh`，随后使用 `record_desktop_demo.sh` 录制视频。

### 批次 66：赛事总报告同步与收尾回归（2026-09-07）

- 实际修改：更新 `runs/openkylin-validation-20260906/final-event-report.md`，加入 Grok no-memory 5 批真实统计、`0.2.0+test1` 候选 `.deb` 的用户态 smoke/哈希、DeepSeek no-memory 已完成状态及当前 LICENSE/系统生命周期/视频边界；删除“DeepSeek no-memory 尚未运行”和“Grok 未完成重复运行”的过期结论。
- 实际命令：宿主机执行 `bash -n` 检查 7 个发布/录制脚本、`python -m unittest discover -s tests -v`、报告状态标记检查和工作区 token 前缀扫描。
- 实际结果：shell 语法检查退出码 `0`；全量测试退出码 `0`，40 项通过；报告一致性检查输出 `final_report_consistency=valid`；敏感令牌扫描输出 `secret_token_pattern_scan=clean`。首次报告检查误用英文 `native memory` 标记而退出 `1`，随即改用实际中文“原生记忆事件”后退出 `0`；该失败是检查脚本条件错误，不是项目运行或报告内容错误。
- 已完成：报告同步、收尾回归、状态一致性和凭据模式扫描。
- 未完成：系统级 `.deb` 安装/升级/卸载、3-5 分钟 openKylin 桌面视频、项目级最终 LICENSE 仍未完成。
- 客观阻塞：自动化 SSH 用户没有可用非交互 sudo（最近实际探测退出码 `137`），且无 `DISPLAY`/Wayland；LICENSE 依法仍需项目负责人/法务决定。
- 下一轮最高优先级：在具备 sudo/root 和图形桌面会话的 openKylin 终端执行 `scripts/record_deb_lifecycle.sh`，再使用 `scripts/record_desktop_demo.sh` 生成并校验 3-5 分钟视频；随后由项目负责人确认最终 LICENSE。

### 批次 67：Debian 生命周期脚本失败语义修正与本地回归（2026-09-07）

- 实际修改：`scripts/record_deb_lifecycle.sh` 现在累计每一步真实退出码并在任一步失败时整体返回非零；`scripts/install_deb.sh` 与 `scripts/uninstall_deb.sh` 在非 root 时改用 `sudo -n`，权限不可用会快速返回明确错误，不再等待交互密码。该修改仅针对发布生命周期记录，不改变评测/评分逻辑。
- 实际命令：宿主机执行 `bash -n scripts/install_deb.sh scripts/upgrade_deb.sh scripts/uninstall_deb.sh scripts/record_deb_lifecycle.sh`；退出码 `0`。执行 `python -m unittest discover -s tests -v`；退出码 `0`，40 项通过。
- 实际结果：脚本语法和全量回归通过；尚未据此宣称 VM 系统包已安装。宿主基础包 SHA-256 `8134f5f750ee67632c550e8fead86903cb86a64101df72e383c4306d8492735a`，升级候选包 SHA-256 `92a9e4e020335e2052cf618c81c4ecd75494b32d8b42e659a50796d4769fcceb`。
- 已完成：生命周期脚本错误语义修正和本地回归。
- 未完成：VM 系统级安装/升级/卸载仍待实际执行；本轮图像、截图、视频和桌面录制暂缓；最终项目 LICENSE 仍待负责人/法律确认。
- 待确认假设：桌面操作员可先完成一次授权的 `sudo -v`，再运行记录脚本；自动化 SSH 仍需 root 或预授权 sudo。
- 下一轮最高优先级：同步脚本到 VM，运行 `record_deb_lifecycle.sh` 并保存逐步退出码和日志。

### 批次 68：Debian 生命周期执行通道连接复核（2026-09-07）

- 实际命令：宿主机尝试通过 `scp` 同步修正后的 `record_deb_lifecycle.sh`、`install_deb.sh`、`uninstall_deb.sh`、`upgrade_deb.sh` 到 `<vm-user>@192.168.182.129:2222`；传输阶段 SSH 返回 `Connection closed`，外层命令退出码 `1`。随后执行 `ssh -o BatchMode=yes -o ConnectTimeout=8 ... 'echo connected; id'`，返回 `Connection timed out`；宿主机对该地址执行两次 `ping`，均超时（100% 丢包）。
- 实际结果：本批没有在 VM 执行 `record_deb_lifecycle.sh`，没有安装、升级、卸载或生成系统级生命周期结果；不得把连接失败写成步骤成功。当前工作区脚本和包文件保持不变，未删除 VM/宿主机用户文件。
- 已完成：确认生命周期修正尚未同步到 VM，且当前 VM 网络/进程不可达；此前 openKylin 2.0 SP2 环境信息仍以批次 54 及历史记录为准，不用本批替代环境验证。
- 未完成：`.deb` 系统级安装、版本/CLI 验证、升级、升级后运行、卸载及残留检查仍未执行；本轮图像、截图、视频和桌面演示继续暂缓；项目级 LICENSE 仍待负责人/法律确认。
- 客观阻塞：`192.168.182.129:2222` 当前连接超时，宿主机未发现正在运行的 VirtualBox/VMware/QEMU 进程；无法通过现有自动化通道进入 openKylin VM。
- 待确认假设：VM 重新启动并恢复 SSH 后，端口仍为 `2222`、地址仍为 `192.168.182.129`；若网络地址变化，应以 VM 内实际 `ip addr` 和 SSH 配置为准。
- 下一轮最高优先级：恢复 openKylin VM SSH 可达性后，重新同步修正脚本并执行 `bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle ...`；在恢复前不得报告任何系统级生命周期完成结论。

### 批次 70：sudo 非交互超时保护与本地回归（2026-09-07）

- 实际修改：`scripts/install_deb.sh` 与 `scripts/uninstall_deb.sh` 的非 root 分支增加 GNU `timeout` 保护，默认 `KMB_SUDO_TIMEOUT=8` 秒，可通过同名环境变量覆盖；权限不足或 sudo 挂起时快速失败并保留明确错误，不改变 root 分支和 dpkg 语义。未修改评测、评分或包内代码。
- 实际命令：宿主机执行 `bash -n scripts/install_deb.sh scripts/uninstall_deb.sh scripts/record_deb_lifecycle.sh scripts/upgrade_deb.sh`，退出码 `0`；执行 `python -m unittest discover -s tests -v`，退出码 `0`，40 项通过。
- 实际结果：本地脚本语法和全量回归通过；修改后脚本哈希为 `install_deb.sh=34d8bcffadc0a04ba6341e464f9f5062bbb637d8babf7803630879aaf1d14599`、`uninstall_deb.sh=56ac1691ed83be9e7d3b40d9caf1e6cec54168254ade0c59389f00eefb7e7ef4`。尚未据此宣称系统包生命周期成功。
- 已完成：针对 openKylin 自动化 sudo 挂起的最小失败边界修正和本地验证。
- 未完成：VM 同步后尚未执行完整 `record_deb_lifecycle.sh`；系统级安装、升级、运行、卸载和残留检查仍待实际退出码。
- 暂缓：本轮图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：若 VM 自动化账号仍无授权 sudo，生命周期中的 install/upgrade/uninstall 会按真实失败退出并由记录脚本汇总为失败；需要 root 或已认证 sudo 才能完成系统级验证。
- 待确认假设：openKylin 客户机提供 GNU `timeout`（历史环境已探测为 `/usr/bin/timeout`）；若缺失，需在客户机终端安装 coreutils 或以 root 运行脚本。
- 下一轮最高优先级：同步超时保护脚本到当前 openKylin VM，执行生命周期记录脚本并保存每一步命令、退出码和日志。

### 批次 71：openKylin VM `.deb` 生命周期实际执行（2026-09-07）

- 实际环境：VMware 现有 `D:\openKylin-VM\openKylin.vmx` 启动后，通过 `<vm-user>@192.168.182.129:2222` SSH 进入；历史环境为 openKylin 2.0 SP2、x86_64、Python 3.12.2。VM 项目目录为 `<user-home>/kmb-openkylin-validation-20260906`。
- 实际命令：`cd <user-home>/kmb-openkylin-validation-20260906 && bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle dist/kylin-memory-bench_0.2.0_all.deb dist/kylin-memory-bench_0.2.0+test1_all.deb`；SSH 外层退出码 `1`，脚本输出 `lifecycle_status=failed`。
- 逐步退出码：`preflight=0`、`install=1`、`version=1`、`verify=2`、`build_upgrade=0`、`upgrade=126`、`verify_after_upgrade=2`、`uninstall=0`、`residual_check=0`。结果目录为 VM `<user-home>/kmb-openkylin-validation-20260906/runs/deb-lifecycle/`，含每步 `.command`、`.stdout.log`、`.stderr.log` 和 `.exitcode`。
- 实际结果：基础包未完成系统安装，版本查询和安装后包 smoke/CLI 校验因此失败；升级命令因候选包未能执行而返回 126；升级后校验失败。`build_upgrade=0` 仅表示在 VM 重建 `0.2.0+test1` 包成功，不代表安装成功。卸载步骤返回 0 是因为包未安装并完成了“无命令/无 `/usr/share/kylin-memory-bench`”残留检查，不代表执行过 dpkg removal。
- 客观原因（待日志复核）：VM 自动化账户的非交互 sudo 仍不可用，安装脚本的受限 sudo 路径返回 1；系统级 dpkg 安装、升级和卸载成功验收尚未满足。
- 已完成：在真实 openKylin VM 执行完整生命周期脚本并保存逐步退出码；重建升级候选包成功；卸载后命令和 payload 路径残留检查通过。
- 未完成：`.deb` 系统级安装、安装后双 Agent/证据/评分/报告、升级后运行和真正 dpkg 卸载；需 root 或可用 sudo 权限重跑。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 待确认假设：桌面/root 操作员可在 VM 内完成一次授权的 `sudo -v`，再用同一输出目录或新唯一目录重跑；旧 `runs/deb-lifecycle` 目录不得覆盖。
- 下一轮最高优先级：在 openKylin VM 的 root 或已认证 sudo 终端重跑生命周期脚本，确保 install/version/verify/upgrade/verify_after_upgrade/uninstall 均取得真实成功退出码。

### 批次 72：升级脚本可执行位修复与本地回归（2026-09-07）

- 实际发现：批次 71 的 `upgrade=126` 日志显示 `scripts/upgrade_deb.sh` 直接执行 `install_deb.sh` 时因 `scp` 后远端文件为 0644 而报 `Permission denied`；该错误与 sudo 阻塞独立。
- 实际修改：`scripts/upgrade_deb.sh` 改为显式执行 `bash "$SCRIPT_DIR/install_deb.sh" "$@"`，不依赖被调用脚本的可执行位；未改变升级参数或 dpkg 逻辑。
- 实际命令：宿主机执行 `bash -n scripts/install_deb.sh scripts/uninstall_deb.sh scripts/record_deb_lifecycle.sh scripts/upgrade_deb.sh`，退出码 `0`；执行 `python -m unittest discover -s tests -v`，退出码 `0`，40 项通过。修改后 `upgrade_deb.sh` SHA-256 为 `9fc1564c258e74ae96fc400cafc9d02700f9f77ddbbf5edaf021e300d974e9f9`。
- 已完成：升级脚本在非可执行传输权限下的可复现性修正和本地回归。
- 未完成：VM 尚未重跑新脚本；系统级安装、升级、运行、卸载仍受 sudo/root 条件约束。
- 暂缓：本轮图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：VM 自动化账号仍没有授权 sudo；重跑后预计 install/upgrade 仍可能按真实权限错误失败，但不应再出现由脚本 mode 导致的 126。
- 待确认假设：桌面/root 操作员可在 VM 内完成授权 sudo 后重跑；历史批次 71 目录保留，不覆盖。
- 下一轮最高优先级：同步 `upgrade_deb.sh` 到 VM，在新唯一目录执行生命周期脚本并核对权限错误是否消除。

### 批次 73：openKylin VM 生命周期重试（升级脚本修复后，2026-09-07）

- 实际准备：将修复后的 `scripts/upgrade_deb.sh` 同步到 VM，并执行 `chmod 0755 scripts/record_deb_lifecycle.sh scripts/install_deb.sh scripts/uninstall_deb.sh scripts/upgrade_deb.sh`；远端 `bash -n` 退出码 `0`，四个脚本均为 0755，`upgrade_deb.sh` SHA-256 为 `9fc1564c258e74ae96fc400cafc9d02700f9f77ddbbf5edaf021e300d974e9f9`。
- 实际命令：`cd <user-home>/kmb-openkylin-validation-20260906 && bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle-20260907-02 dist/kylin-memory-bench_0.2.0_all.deb dist/kylin-memory-bench_0.2.0+test1_all.deb`；SSH 外层退出码 `1`，脚本输出 `lifecycle_status=failed`。
- 逐步退出码：`preflight=0`、`install=1`、`version=1`、`verify=2`、`build_upgrade=0`、`upgrade=1`、`verify_after_upgrade=2`、`uninstall=0`、`residual_check=0`。结果目录为 VM `<user-home>/kmb-openkylin-validation-20260906/runs/deb-lifecycle-20260907-02/`。
- 实际结果：升级步骤不再出现 126/Permission denied；`install=1` 和 `upgrade=1` 均为非交互 sudo 不可用导致，版本/verify/verify_after_upgrade 因包未安装而失败。`build_upgrade=0` 只证明候选包重建成功；`uninstall=0` 仅验证未安装状态和无 payload 残留。
- 已完成：真实 openKylin VM 重试、脚本 mode 修复验证、逐步日志和退出码生成；未覆盖批次 71 目录。
- 未完成：系统级 `dpkg -i` 安装、安装后双 Agent/证据/评分/报告、升级后运行和实际 dpkg 卸载；仍需 root 或已认证 sudo。
- 暂缓：本轮图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：SSH 用户 `<vm-user>` 的 `sudo -n` 实际报“a password is required”并被 8 秒保护终止；当前自动化通道不能代填密码，不能声称系统包生命周期成功。
- 待确认假设：在 VM 桌面终端执行一次 `sudo -v` 后，使用同一脚本和新结果目录可完成剩余生命周期；需要保留本批失败证据用于验收审计。
- 下一轮最高优先级：由具备 sudo/root 的 openKylin 终端运行 `record_deb_lifecycle.sh`，确认安装、升级、验证和 dpkg 卸载的真实成功退出码。

### 批次 74：生命周期失败证据归档与安全复核（2026-09-07）

- 实际命令：通过 SSH 在 VM 对 `runs/deb-lifecycle-20260907-02/` 执行敏感令牌模式扫描和逐步 `.exitcode`/错误日志读取；扫描结果 `secret_scan=clean`。随后使用 `scp -r` 将该目录复制到宿主机 `runs/deb-lifecycle-20260907-02/`，复制退出码 `0`。
- 归档内容：每步 `.command`、`.stdout.log`、`.stderr.log`、`.exitcode` 共 36 个文件；宿主机归档保留 VM 原始字节大小和时间戳，不覆盖批次 71。
- 关键错误证据：install/upgrade stderr 均为非交互 sudo 需要密码并被 8 秒 timeout 终止；version stderr 为 `dpkg-query: no packages found matching kylin-memory-bench`；verify/verify_after_upgrade stderr 为 `kmb is not installed or not on PATH`。build_upgrade stdout 证明候选包重建成功，不证明安装成功。
- 已完成：失败生命周期批次安全归档和无密钥复核；所有失败结论均有 VM 命令、退出码和日志文件支撑。
- 未完成：系统级安装、安装后真实双 Agent/证据/评分/报告、升级后运行和 dpkg 卸载；仍需 root 或已认证 sudo。
- 暂缓：本轮图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：`<vm-user>` 自动化 SSH 账号没有 sudo 密码授权；当前不能通过自动化通道完成 dpkg 系统变更。
- 待确认假设：项目负责人可在 VM 桌面终端授权 sudo 后重跑，且允许使用新的唯一结果目录；历史失败目录需作为验收审计证据保留。
- 下一轮最高优先级：在已授权 sudo/root 的 openKylin 终端重新执行生命周期脚本，并将成功/失败的每一步结果追加到上下文包。

### 批次 75：运行依赖与候选包内容许可证复核（2026-09-07）

- 实际命令：宿主机通过 `importlib.metadata` 核查 PyYAML，结果为 `6.0.3 / MIT / Requires-Dist=[]`；VM 通过 `.kmb-venv/bin/python` 核查 PyYAML，结果为 `6.0.1 / MIT / Requires-Dist=[]`。该差异仍满足项目声明的 `PyYAML>=6.0`，但系统 `python3-yaml` 的最终安装版本尚未因 dpkg 阻塞而确认。
- 实际命令：VM 执行 `dpkg-deb --contents dist/kylin-memory-bench_0.2.0+test1_all.deb | grep -E '(credentials|\\.env$|\\.pyc$|/runs/|/\\.venv|/\\.tmp)'`，退出码 `0`，输出 `forbidden_payload_entries=clean`。此前一次使用 VM 不存在的 `rg` 的管道检查产生 Broken pipe/非零，不作为成功审计；随后已用存在的 `grep` 重跑并获得上述成功结果。
- 实际产物：`runs/license-audit-20260907/runtime-dependency-audit.json`，记录声明依赖、宿主/VM 实际版本、MIT 元数据、包内容检查和限制。
- 审计结论：参考仓库库存仍全部 `needs_manual_review=true`；项目根目录没有最终 `LICENSE`，`NOTICE` 不授予权利，`packaging/deb/copyright` 仍为 `pending-project-owner-selection`。未发现本项目源码直接复制参考仓库代码/数据/Prompt 的证据。
- 已完成：自动可确认的直接运行依赖、候选包禁止内容和参考许可证库存审计；高风险/未知许可证仍显式标记人工确认。
- 未完成：项目级最终 LICENSE、第三方数据/Prompt/传递依赖法律确认；系统级 `.deb` 安装后系统依赖版本核验。
- 暂缓：本轮图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：系统级 dpkg 生命周期仍需 root/已认证 sudo，许可证最终选择需项目负责人/法务。
- 待确认假设：`python3-yaml` 系统包与 PyYAML MIT 许可证一致，但最终版本和发行版版权文件需安装后再核对。
- 下一轮最高优先级：在已授权 sudo/root 的 openKylin 终端完成系统级 `.deb` 生命周期，然后核对系统依赖和最终许可证落地文件。

### 批次 76：许可证文档同步与候选 `.deb` 重建审计（2026-09-07）

- 实际准备：将更新后的 `docs/license-audit.md` 同步至 openKylin VM；在独立目录 `dist/rebuild-20260907` 重建基础包和 `0.2.0+test1` 候选包。
- 实际命令：VM 执行 `bash scripts/build_deb.sh dist/rebuild-20260907` 与 `KMB_DEB_VERSION=0.2.0+test1 bash scripts/build_deb.sh dist/rebuild-20260907`，远端退出码 `0`；使用 `dpkg-deb --contents` 与 `grep` 禁止内容扫描，输出 `remote_rebuild_payload_scan=clean`。
- 实际产物：宿主机 `dist/rebuild-20260907/kylin-memory-bench_0.2.0_all.deb`（SHA-256 `6d35f79d95bd5ca499efc233a2c8f45c17ae98281134c991e4680d866d209ae5`）和 `dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb`（SHA-256 `90d4cb210fc8da98639a8b2d6679fbce7ba69bdb8aa9ec87212bc9639b33e3e3`）；VM 与宿主哈希一致。
- 实际内容：候选包包含更新后的 `docs/license-audit.md`；控制文件仍声明 `python3 (>= 3.9), python3-yaml`；没有凭据、`.env`、字节码、runs、虚拟环境或研究缓存。
- 已完成：审计文档同步、基础/升级候选包独立重建、哈希和禁止内容核验；未覆盖既有 `dist/*.deb`。
- 未完成：系统级 dpkg 安装/升级/卸载、安装后真实双 Agent/证据/评分/报告；最终项目级 LICENSE 仍待负责人/法务。
- 暂缓：本轮图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：系统级包生命周期仍需 root/已认证 sudo；当前自动化 SSH 账号不能完成 dpkg 系统变更。
- 待确认假设：`dist/rebuild-20260907` 包可作为后续授权终端的候选验证输入；项目负责人确认 LICENSE 后需再更新 `packaging/deb/copyright` 并重建。
- 下一轮最高优先级：在具备授权 sudo/root 的 openKylin 终端使用 `dist/rebuild-20260907` 对应包完成安装、升级、验证和卸载。

### 批次 77：重建候选包 openKylin 用户态 payload smoke（2026-09-07）

- 实际命令：在 openKylin VM 使用 `dpkg-deb -x dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb` 解包到临时用户目录，并以 `KMB_HOME`/`PYTHONPATH` 指向解包 payload 执行 `/usr/bin/python3 -m unittest discover -s <payload>/tests -p smoke_test.py -v`；临时解包目录在完成后删除。
- 实际结果：payload smoke 退出码 `0`，2 项包内测试通过：严格校验 `core-zh.yaml` 的 6 个案例，以及离线 compare 的 JSON/HTML 报告生成。VM 证据目录为 `runs/deb-release-20260907/rebuilt-package-smoke/`，已复制到宿主机同路径；敏感令牌扫描结果 `secret_scan=clean`。
- 事实边界：包内 smoke 使用 `reference/flawed` 仅验证离线 CLI/评分/报告机制，不是 Grok/DeepSeek 真实 Agent 对比，也不替代 `dpkg -i` 系统安装、升级或 `dpkg -r` 卸载。
- 已完成：包含最新许可证审计文档的候选包在真实 openKylin VM 的用户态解包、CLI、六案例校验和离线报告链验证。
- 未完成：系统级安装、安装后真实双 Agent/证据/评分/报告、升级后运行和实际 dpkg 卸载；最终项目级 LICENSE 选择。
- 暂缓：本轮图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：自动化 SSH 用户仍无授权 sudo；不能将用户态 payload smoke 误记为系统包生命周期成功。
- 待确认假设：具备 root/已认证 sudo 的操作员可使用该候选包按 `scripts/record_deb_lifecycle.sh` 完成系统级验证。
- 下一轮最高优先级：在 openKylin VM 已授权 sudo/root 终端执行重建候选包的完整安装、升级、验证和卸载。

### 批次 78：既有真实双 Agent 运行链路严格校验（2026-09-07）

- 实际检查：VM 中既有四轨结果目录 `runs/openkylin-validation-20260906/four-mode-rescored/` 包含 Grok wrapper、Grok no-memory、DeepSeek wrapper、DeepSeek no-memory 四个 `result.json`，且 comparison JSON/HTML 文件存在。
- 实际命令：在 VM 对四个既有结果分别执行 `.kmb-venv/bin/python scripts/verify_run.py <result-dir> --strict`；四次退出码均为 `0`。校验输出分别确认 6 cases，证据事件数为 Grok wrapper 69、Grok no-memory 71、DeepSeek wrapper 70、DeepSeek no-memory 70；未重新调用 API。
- 实际归档：四个 `*.lifecycle-verify.stdout.log` 已复制到宿主机 `runs/openkylin-validation-20260906/four-mode-rescored/`，敏感令牌扫描结果 `secret_scan=clean`。第一次复制尝试误把日志目录当作文件路径，`scp` 退出码 `1`；随后按实际文件名重试，退出码 `0`，不影响 VM 校验结果。
- 事实边界：这些是历史真实 Grok/DeepSeek API + 忆衡包装层/no-memory 结果的结构校验，不是本轮新 API 运行；wrapper/no-memory 仍是系统级行为与基线，不证明模型原生长期记忆。
- 已完成：为生命周期验收补充真实双 Agent 结果链路存在性和严格结构校验；包内 smoke 的 `reference/flawed` 仍只限离线机制验证。
- 未完成：`.deb` 系统级安装、安装后通过已安装 CLI 运行真实双 Agent、升级后运行和实际 dpkg 卸载；需 root/已认证 sudo。
- 暂缓：本轮图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：自动化 SSH 账号无 sudo 密码授权，系统包不能由当前通道安装。
- 待确认假设：授权终端可复用既有 VM 真实结果目录，并在系统包安装后追加新的安装路径验证。
- 下一轮最高优先级：获取 root/已认证 sudo 后重跑候选 `.deb` 生命周期，至少补齐 install/version/verify/upgrade/verify_after_upgrade/dpkg removal 的成功证据。

### 批次 79：当前工作区回归与发布安全复核（2026-09-07）

- 实际命令：宿主机执行 `python -m unittest discover -s tests -v`，退出码 `0`，40 项通过；执行 `bash -n scripts/install_deb.sh scripts/uninstall_deb.sh scripts/upgrade_deb.sh scripts/record_deb_lifecycle.sh scripts/build_deb.sh scripts/verify_deb.sh`，退出码 `0`；对可发行工作区（排除 runs、dist、研究缓存和虚拟环境）执行敏感令牌模式扫描，输出 `secret_token_pattern_scan=clean`。
- 实际结果：生命周期超时/升级脚本修正、许可证审计文档和结构化依赖审计产物未破坏现有测试；`dist/rebuild-20260907/` 的基础包/候选包及 VM 用户态 smoke、失败生命周期日志均保留在宿主机。
- 已完成：本轮最后一次本地回归、脚本语法和敏感令牌复核。
- 未完成：系统级 `.deb` 安装、安装后真实双 Agent/证据/评分/报告、升级后运行、实际 `dpkg -r` 卸载；最终项目级 LICENSE 选择。
- 暂缓：本轮图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：当前自动化 SSH 用户的 sudo 仍提示 `a password is required`，不能完成系统包操作；不以 VM 用户态 smoke 或宿主机测试替代系统级结论。
- 待确认假设：项目负责人可在 openKylin VM 本地桌面终端完成一次 `sudo -v` 或以 root 登录，再运行现有脚本。
- 下一轮最高优先级：在已认证 sudo/root 的 openKylin 终端对 `dist/rebuild-20260907` 包执行完整生命周期，保存全部成功/失败退出码和安装后 CLI/真实 Agent 证据。

### 批次 69：许可证审计复核与 Debian 生命周期连接阻塞（2026-09-07）

- 实际命令：宿主机执行 `python scripts/audit_reference_licenses.py --out runs/license-audit-20260907/inventory.json`，退出码 `0`；审计结果明确为文件库存而非法律分类，参考仓库代码、数据集、Prompt、直接/传递依赖仍需逐项人工许可证审查。另执行项目源码精确引用扫描（排除文档和审计脚本），输出 `release_source_reference_scan=clean`。
- 实际结果：许可证库存文件为 `runs/license-audit-20260907/inventory.json`；当前根目录没有 `LICENSE`，`NOTICE` 明确不授予权利，`docs/license-decision.md` 仍为候选决策，`packaging/deb/copyright` 为 `pending-project-owner-selection`。未新增或复制第三方代码、数据集或 Prompt，也未修改最终许可证结论。
- 实际命令：宿主机使用 `ssh -i <user-home>\.ssh\openkylin_vm_ed25519 -p 2222 -o BatchMode=yes -o ConnectTimeout=10 <vm-user>@192.168.182.129 ...` 重试 VM 环境命令，返回 `Connection timed out`，退出码 `255`；本批未执行 `scp`、`dpkg -i`、`dpkg -r` 或生命周期脚本。
- 已完成：本地许可证库存与源码引用审计复核；确认系统级生命周期脚本仍保持真实失败语义，未将连接失败误记为成功。
- 部分完成：宿主机包文件仍存在（基础包和 `+test1` 候选包），可在 VM 恢复后继续；历史 openKylin 2.0 SP2/x86_64 环境记录沿用批次 54，不被本批替代。
- 未完成：`.deb` 安装、安装后 CLI/评测、升级、升级后运行、卸载和残留检查；最终项目级 LICENSE 选择。
- 暂缓：本轮图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：`192.168.182.129:2222` 当前 SSH 超时，自动化通道不可达；无法在宿主机替代执行 openKylin 系统级 dpkg 验证。
- 待确认假设：VM 恢复后地址/端口和 SSH 密钥仍有效；项目负责人/法务需要确认最终项目许可证及版权主体。
- 下一轮最高优先级：恢复 openKylin VM SSH 可达性后，重新同步脚本并执行 `bash scripts/record_deb_lifecycle.sh`，逐步保存安装、升级、运行、卸载和残留检查退出码。

### 批次 80：本轮发布验收收敛记录（2026-09-07）

- 本轮最终状态：openKylin VM 已恢复并可 SSH；候选包已独立重建、哈希核对、禁止内容扫描和用户态 payload smoke 通过；既有 Grok/DeepSeek 四轨真实运行链路严格校验通过；系统级 `.deb` 生命周期仍未通过。
- 系统级生命周期事实：最新结果目录 `runs/deb-lifecycle-20260907-02/` 的 install/version/verify/upgrade/verify_after_upgrade/uninstall 退出码依次为 `1/1/2/1/2/0`，residual_check 为 `0`；install/upgrade 的实际错误为 sudo 需要密码。不得把该目录写成安装或升级成功。
- 许可证事实：参考库存、源码引用、PyYAML 宿主/VM 元数据和候选包禁止内容审计均已记录；项目根目录 `LICENSE` 仍缺失，最终许可证和版权主体仍需项目负责人/法务确认。
- 文档顺序说明：批次 69 的审计记录因追加时匹配历史锚点而位于文件尾部较早批次之后；该记录内容保留且未覆盖任何历史，批次 80 作为当前最终状态锚点。
- 暂缓：本轮图像、截图、视频和桌面演示任务均未执行。
- 下一轮唯一最高优先级：在 openKylin VM 本地 root 或已认证 sudo 终端，以 `dist/rebuild-20260907` 候选包重跑 `scripts/record_deb_lifecycle.sh`，取得系统级 install、verify、upgrade、verify_after_upgrade 和真正 dpkg removal 的成功退出码。

### 批次 81：本地 sudo 授权与 SSH 自动化会话隔离复核（2026-09-07）

- 实际前提：项目负责人确认已在 openKylin VM 本地终端执行 `sudo -v`；没有传递、读取或记录密码。
- 实际命令：自动化 SSH 会话执行 `timeout --signal=TERM --kill-after=2s 8s sudo -n id -u`，退出码 `137`；随后使用 `ssh -tt` 强制分配伪终端重试同一命令，仍退出码 `137`。
- 实际结果：本地终端的 sudo timestamp 没有令当前 SSH 自动化会话取得无交互 sudo；不能据此继续执行 dpkg 安装/升级/卸载，也不能声称 sudo 已对自动化通道授权。
- 已完成：验证本地授权与 SSH/TTY 会话边界，避免错误地把本地 `sudo -v` 视为永久或跨会话授权。
- 未完成：系统级 `.deb` 生命周期仍需在 VM 本地 root/已认证 sudo 终端执行，或由管理员配置受限的、可审计的 NOPASSWD sudoers 规则。
- 暂缓：图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：SSH 账户的无交互 sudo 两种会话形式均在 8 秒受控超时内失败。
- 待确认假设：VM 本地 root shell 可直接执行现有生命周期脚本并保留结果目录权限，供后续 SSH 归档。
- 下一轮唯一最高优先级：在 VM 本地终端以 `sudo bash scripts/record_deb_lifecycle.sh ...` 执行授权生命周期批次，并确保结果目录回归 `<vm-user>` 用户可读。

### 批次 82：KARE shadow 验证脚本错误传播修正与本地回归（2026-09-07）

- 实际发现：授权生命周期运行中，KARE shadow 的 `/usr/bin/kmb` 与 payload 最终已出现，但 `verify_deb.sh` 的 `tee` 管道未启用 `pipefail`，曾把 `unittest`/`verify_run.py` 的内部错误掩盖为退出码 0；`dpkg-query` 在 KARE 中也可能为空，导致安装/版本/卸载误判。
- 实际修改：`scripts/verify_deb.sh` 改为 `set -euo pipefail` 并等待 `/usr/share/kylin-memory-bench/tests/smoke_test.py`、`scripts/verify_run.py` 就绪（默认 30 秒，可由 `KMB_PAYLOAD_WAIT` 覆盖）；`scripts/install_deb.sh` 和 `scripts/uninstall_deb.sh` 增加 `dpkg -s` 回退状态检测；`scripts/record_deb_lifecycle.sh` 的 version 步骤增加同等回退。未改变评测、评分和真实 Agent 逻辑。
- 实际命令：宿主机执行 `bash -n scripts/install_deb.sh scripts/uninstall_deb.sh scripts/verify_deb.sh scripts/record_deb_lifecycle.sh scripts/upgrade_deb.sh`，退出码 `0`；执行 `python -m unittest discover -s tests -v`，退出码 `0`，40 项通过。
- 已完成：识别并修复发布验证脚本的错误吞没和 KARE 状态兼容问题；尚未将修复后的脚本在 VM 单独 verify/生命周期中重新执行。
- 未完成：需要在 openKylin VM 重新同步脚本，单独运行 `verify_deb.sh` 验证错误传播，再由 root 重跑完整生命周期并确认 `dpkg -r` 真正执行。
- 暂缓：图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：KARE shadow 的 dpkg 包装器会产生 `/var/log/kare/kare-dpkg-wrapper.log: Permission denied` 警告，且普通 `dpkg-query` 状态为空；需要以实际 `dpkg -s`、命令路径和残留检查综合判断。
- 待确认假设：KARE shadow 在 payload 文件就绪后可通过修正后的 `verify_deb.sh` 完成严格离线 smoke；系统级 dpkg removal 仍需授权终端实测。
- 下一轮最高优先级：同步修正脚本到 VM，单独运行严格 `verify_deb.sh`，然后用新目录重跑授权生命周期并保存所有日志。

### 批次 83：修正后已安装包严格验证（2026-09-07）

- 实际环境：openKylin VM（历史环境记录：2.0 SP2、x86_64、Python 3.12.2）；SSH 项目目录 `<user-home>/kmb-openkylin-validation-20260906`。当前 `dpkg -s kylin-memory-bench` 显示 `install ok installed`、版本 `0.2.0+test1`，`/usr/bin/kmb` 存在。
- 实际命令：`cd <user-home>/kmb-openkylin-validation-20260906; bash scripts/verify_deb.sh runs/deb-lifecycle-authorized-20260907/verify-after-script-fix-rerun`；VM/SSH 外层退出码 `0`。
- 实际结果：修正后的 `verify_deb.sh` 启用 `pipefail` 并等待 payload 后，包内 smoke 2 项通过；`core-zh.yaml` 六案例校验通过；离线 compare JSON/HTML 生成通过；`verify_run.py` 对 reference/flawed smoke 结果分别确认 6 cases、34 evidence events，均退出码 `0`。该 smoke 仅验证已安装包的离线机制，不是 Grok/DeepSeek 新调用或真实 Agent 结论。
- 结果与证据：VM 与宿主机均保留 `runs/deb-lifecycle-authorized-20260907/verify-after-script-fix-rerun/`，含 smoke 输出、compare 目录和结构校验结果；宿主机通过 `scp -r` 归档退出码 `0`。本批次未写入凭据，未发现密钥输出。
- 已完成：最新验证脚本的错误传播、KARE payload 等待和已安装包离线链路得到真实退出码 `0`。
- 部分完成：系统级安装/升级/真实双 Agent 运行/卸载生命周期仍需后续独立授权批次；本批 smoke 中的 reference/flawed 不得作为参评 Agent。
- 未完成：新唯一目录下的 install、version、严格 verify、upgrade、verify_after_upgrade、真正 `dpkg -r` 和残留检查尚未重跑。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：完整生命周期仍要求 VM 本地 root 或已认证 sudo 终端；SSH 自动化会话不能代填 sudo 密码。
- 待确认假设：本地授权终端可使用 `dist/rebuild-20260907` 的基础包和 `0.2.0+test1` 候选包，并允许新建结果目录 `runs/deb-lifecycle-authorized-20260907-rerun`。
- 下一轮最高优先级：在 openKylin VM 本地 root/已认证 sudo 终端执行新唯一目录的完整 `.deb` 生命周期并归档每步退出码。

### 批次 84：SSH 自动化 sudo 状态复核（2026-09-07）

- 实际环境：同一 openKylin VM（历史记录：2.0 SP2、x86_64、Python 3.12.2），SSH 用户 `<vm-user>`；未读取或传递任何密码/API 密钥。
- 实际命令：`ssh -i <脱敏私钥路径> -p 2222 -o BatchMode=yes -o ConnectTimeout=10 <vm-user>@192.168.182.129 "sudo -n -v"`；SSH 外层退出码 `1`。
- 实际输出（已脱敏）：`sudo: unable to resolve host kare: Name or service not known`、`sudo: unable to send audit message: Operation not permitted`、`sudo: a password is required`。该会话没有获得无交互 sudo，未执行 dpkg 变更。
- 已完成：确认当前 SSH 自动化通道仍不能代表 VM 本地终端的 sudo 授权；保留批次 83 严格包验证证据和历史失败生命周期证据。
- 未完成：系统级 `.deb` 安装、版本/安装后严格验证、升级、升级后运行、真正 `dpkg -r` 和残留检查仍未取得成功退出码。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：SSH 会话的 sudo 需要密码且 KARE 审计插件返回权限警告；当前自动化工具无法代填密码或复用本地终端授权。
- 待确认假设：VM 本地终端仍可直接运行 `sudo bash scripts/record_deb_lifecycle.sh ...`；执行后结果目录可由 `<vm-user>` 读取并通过 SSH 归档。
- 下一轮最高优先级：在 VM 本地 root/已认证 sudo 终端运行 `record_deb_lifecycle.sh`（新唯一目录），再通过 SSH 读取并归档真实 install/upgrade/uninstall 退出码。

### 批次 85：已安装包非 root 只读 CLI 核对（2026-09-07）

- 实际环境：同一 openKylin VM，`dpkg -s kylin-memory-bench` 显示 `Status: install ok installed`、版本 `0.2.0+test1`；`/usr/share/kylin-memory-bench/tests/smoke_test.py` 和 `scripts/verify_run.py` 均存在。
- 实际命令与结果：`ssh ... 'kmb validate --strict --suite /usr/share/kylin-memory-bench/suites/core-zh.yaml'` 退出码 `0`，输出六案例 `status=valid`；`ssh ... 'kmb list-cases --suite /usr/share/kylin-memory-bench/suites/core-zh.yaml'` 退出码 `0`，列出 retention、memory_recall、dynamic_update、similar_distinction、boundary、task_reuse 六类案例。
- 兼容性事实：`ssh ... 'kmb --version'` 退出码 `1`，CLI 返回 argparse 用法错误，说明当前 CLI 没有 `--version` 子命令；版本核对以 `dpkg -s`/包元数据为准，不将该命令误记为包验证失败。
- 已完成：已安装 payload 的只读版本、六案例配置校验和案例清单验证；未进行系统变更。
- 未完成：安装/升级/卸载生命周期仍需 root/已认证 sudo；未用 `reference/flawed` 结果替代真实 Agent 结果。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：自动化 SSH 会话无法无交互 sudo，不能执行 dpkg 系统变更。
- 待确认假设：项目负责人可在 VM 本地终端以 root/已认证 sudo 执行生命周期脚本，并保留新唯一结果目录。
- 下一轮最高优先级：完成授权生命周期批次并核对升级后/卸载后状态。

### 批次 86：VM 控制通道与敏感令牌复核（2026-09-07）

- 实际环境：宿主机 VMware Workstation；`vmrun list` 显示 `D:\openKylin-VM\openKylin.vmx` 正在运行，`checkToolsState` 返回 `running`，`getGuestIPAddress -wait` 返回 `192.168.182.129`。
- 实际命令与结果：`vmrun -T ws typeKeystrokesInGuest ...` 退出码 `1`，返回“主机操作系统中的权限不足”；`vmrun -T ws captureScreen ...` 被 VMware 拒绝并提示匿名客户机操作需先 `VixVM_LoginInGuest`。未执行任何客户机写入或桌面操作。
- 安全复核：宿主机工作区（排除虚拟环境、runs、dist 和临时缓存）执行敏感令牌模式扫描，输出 `secret_pattern_scan=clean`；未读取、输出或写入任何完整 API 密钥。
- 已完成：确认 VM 本身运行正常、网络地址稳定，确认宿主机 VMware 控制接口不能在无客户机密码/登录的情况下执行 root 命令或模拟键盘；包内严格 verify、只读 CLI 核对证据已保留。
- 未完成：系统级 `.deb` 安装/升级/卸载生命周期仍无成功退出码，未完成安装后真实 Agent 运行的系统包路径验证。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行；`captureScreen` 失败文件未生成。
- 客观阻塞：SSH 用户 sudo 需要密码；VMware 匿名客户机操作被策略禁止且当前工具没有客户机登录凭据，无法从自动化通道获得 root。
- 待确认假设：项目负责人可在 VM 本地终端打开 root/已认证 sudo shell，执行现有生命周期命令并保留新目录；无需向对话传递密码。
- 下一轮最高优先级：在 VM 本地 root/已认证 sudo 终端运行 `sudo bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle-authorized-20260907-rerun dist/rebuild-20260907/kylin-memory-bench_0.2.0_all.deb dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb`，完成真实 install/upgrade/uninstall 证据。

### 批次 87：候选 Debian 包元数据核对（2026-09-07）

- 实际环境：openKylin VM 项目目录 `<user-home>/kmb-openkylin-validation-20260906`；未执行系统写入。
- 实际命令：`dpkg-deb --info dist/rebuild-20260907/kylin-memory-bench_0.2.0_all.deb` 与 `dpkg-deb --info dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb`；两次元数据读取及组合 SSH 命令退出码 `0`。
- 实际结果：基础包版本 `0.2.0`、候选升级包版本 `0.2.0+test1`，均为 `Architecture: all`，依赖 `python3 (>= 3.9), python3-yaml`；描述包含 CLI、六能力套件、证据和离线 JSON/Markdown/HTML/SVG 报告。没有凭据、私有数据或模型权重进入包元数据。
- 已完成：候选包版本、架构、依赖和发布描述在真实 openKylin VM 内可读并与构建产物一致。
- 未完成：仍未取得 root 下的 `dpkg -i` 安装、升级后运行和 `dpkg -r` 卸载成功退出码。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：SSH 自动化用户 sudo 需要密码，VMware 匿名客户机操作被拒，无法由当前通道完成系统级变更。
- 待确认假设：本地 root/已认证 sudo 终端可直接使用 `dist/rebuild-20260907` 中的两个包；升级验证使用新唯一结果目录并保留历史失败批次。
- 下一轮最高优先级：执行并归档 root 授权的完整 `.deb` 生命周期，逐步核对每个退出码及卸载残留。

### 批次 88：项目许可证状态复核（2026-09-07）

- 实际检查：读取根目录 `NOTICE`、`README.md`、`docs/license-decision.md`、`docs/license-audit.md`、`runs/license-audit-20260907/inventory.json` 和 `runtime-dependency-audit.json`；未修改许可证结论。
- 实际结果：根目录仍没有 `LICENSE`；`NOTICE` 不授予权利；项目候选许可证仍为 MIT/Apache-2.0/GPL-3.0-or-later 的待确认方案，`packaging/deb/copyright` 仍需项目负责人选择；PyYAML 6.x 的 MIT 运行依赖已具备工程核查记录；参考仓库和数据/Prompt 的独立授权仍需人工确认。
- 已完成：自动可确认的来源、依赖和参考项目库存审计保持可追溯；未新增第三方内容、数据或代码。
- 未完成：项目负责人/法务确认最终许可证、版权主体和公开再分发策略；在确认前不生成根目录最终 `LICENSE`，不宣称公开再分发授权已定。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：最终许可证属于权利主体/法务决策，自动化工具不能代替批准。
- 待确认假设：负责人确认后可按候选方案生成 `LICENSE`、更新 `packaging/deb/copyright` 和 README，并重建 `.deb`。
- 下一轮最高优先级：完成 VM 本地授权 `.deb` 生命周期；并行等待负责人确认最终许可证候选。

### 批次 89：本地 root `.deb` 生命周期执行与 KARE 异步状态修正（2026-09-07）

- 实际环境：openKylin 2.0 SP2、x86_64、Python 3.12.2；项目负责人在 VM 本地桌面终端执行 `sudo -v` 后启动 root 生命周期，未向对话传递密码。
- 实际命令：`sudo bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle-authorized-20260907-rerun dist/rebuild-20260907/kylin-memory-bench_0.2.0_all.deb dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb`；脚本进程以 root 运行并完成，最终生命周期脚本退出码为非零。
- 实际逐步退出码：`preflight=0`、`install=1`、`version=1`、`verify=1`、`build_upgrade=0`、`upgrade=1`、`verify_after_upgrade=1`、`uninstall=0`、`residual_check=0`。结果目录为 VM `<user-home>/kmb-openkylin-validation-20260906/runs/deb-lifecycle-authorized-20260907-rerun/`，通过 `scp -r` 归档到宿主机 `runs/deb-lifecycle-authorized-20260907-rerun/`，复制退出码 `0`。
- 实际观察：安装和升级 stdout 由 KARE 报告 `progress=100, status=0, errinfo=安装成功`；但 KARE shadow 的包状态和 payload 挂载在脚本立即检查时尚未可见，导致 `version/verify/verify_after_upgrade` 失败。卸载 stdout 为 `kylin-memory-bench is not installed`，没有证明执行了 dpkg removal；批次结束后只读核对显示 `dpkg -s` 为 `install ok installed`、版本 `0.2.0+test1`，`/usr/bin/kmb` 和 payload 仍存在。因此不得把本批次写成安装/升级/卸载成功。
- 实际修改：`scripts/install_deb.sh`、`scripts/uninstall_deb.sh`、`scripts/verify_deb.sh`、`scripts/record_deb_lifecycle.sh` 增加 KARE 异步状态等待；生命周期默认导出 `KMB_PACKAGE_WAIT=600`、`KMB_PAYLOAD_WAIT=600`，安装/卸载等待包状态与残留路径收敛，version 使用 POSIX `date` 计时。未改变评测、评分或 Agent 逻辑。
- 实际验证：宿主机 `bash -n` 退出码 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，40 项通过；修正脚本经 `scp` 同步后 VM `bash -n` 退出码 `0`。未执行新的 root 生命周期，避免覆盖本批失败证据。
- 已完成：真实本地 root 生命周期已执行并保存完整失败证据；确认阻塞不是 sudo，而是 KARE 异步状态与当前验证脚本等待窗口不足；最小修正已完成并同步。
- 未完成：修正后的脚本尚未在 VM 本地 root 终端重跑；系统级安装、升级后严格验证、真正卸载和残留清理仍未取得全成功退出码。当前 VM 包仍为 `0.2.0+test1` 安装状态。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：新的 root 生命周期需要在 VM 本地终端再次启动；SSH 自动化会话仍不能代填 sudo 密码。KARE 还可能在包操作后延迟挂载 shadow payload。
- 待确认假设：600 秒等待窗口足以覆盖当前 VM KARE 的安装/卸载同步延迟；若仍超时，应以 `/var/log/kare/kare-dbus.log` 和脚本逐步日志定位，不得放宽为忽略状态。
- 下一轮最高优先级：使用已同步的修正脚本，在 VM 本地 root 终端以全新目录 `runs/deb-lifecycle-authorized-20260907-rerun2` 重跑完整生命周期，完成后通过 SSH 归档并核对最终包状态。

### 批次 90：生命周期证据安全扫描与脚本可移植性复核（2026-09-07）

- 实际命令：宿主机对 `runs/deb-lifecycle-authorized-20260907-rerun/` 全部日志、命令和退出码执行敏感令牌模式扫描，输出 `secret_scan=clean`；对归档文件执行 SHA-256 计算；执行 `sh -c` 日期计时片段验证，输出 `portable_deadline_ok`，退出码 `0`。
- 实际结果：本批生命周期日志未发现完整 API 密钥、Bearer 令牌或其他已知密钥模式；失败生命周期证据目录和历史结果均保留，未删除 VM/用户文件。
- 已完成：证据安全扫描、脚本中用于 `/bin/sh` 的等待计时兼容性复核；未新增运行结果或伪造成功状态。
- 未完成：修正后的生命周期脚本仍需在 VM 本地 root 终端执行新唯一批次；最终 LICENSE 仍待负责人/法务确认。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：自动化 SSH 不能代替 VM 本地 root 终端再次启动生命周期。
- 待确认假设：VM 本地终端可使用已同步脚本和新目录 `runs/deb-lifecycle-authorized-20260907-rerun2`，且 600 秒等待窗口覆盖 KARE shadow 同步延迟。
- 下一轮最高优先级：执行并归档修正脚本的第二次 root 生命周期，目标是取得 install/version/verify/upgrade/verify_after_upgrade/uninstall/residual_check 全部真实成功退出码。

### 批次 91：第二次 root 生命周期进行中与 KARE 非零返回适配（2026-09-07）

- 实际环境：同一 openKylin VM；项目负责人在 VM 本地终端以 root 启动 `runs/deb-lifecycle-authorized-20260907-rerun2`，未传递密码。
- 实际进行中的命令：`sudo bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle-authorized-20260907-rerun2 dist/rebuild-20260907/kylin-memory-bench_0.2.0_all.deb dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb`。
- 已观察结果：截至当前轮询，`preflight=0`、`install=1` 已写入；KARE 日志同时报告基础包 `progress=100, status=0, errinfo=安装成功`，payload 存在且 SSH 只读视图显示版本 `0.2.0`。当前 root 脚本仍停留在旧 version 等待逻辑，批次尚未结束，不能报告最终结果。
- 实际发现：KARE 的 `/usr/bin/dpkg` 包装器可能在 stdout 报成功后返回非零，且 root 进程与 SSH 会话的包状态视图存在时序/挂载差异；原 `set -e` 会在等待逻辑前结束安装步骤。
- 实际修改：`scripts/install_deb.sh` 增加同一次 dpkg 输出中 `status=0/安装成功` 的受限识别，只有同时存在 `/usr/bin/kmb` 和 payload 时才接受 KARE 兜底；`scripts/uninstall_deb.sh` 将 payload 视为待卸载状态，并对 root dpkg removal 做同等成功标记处理；`record_deb_lifecycle.sh` 增加预期包版本的 KARE payload 兜底。修正脚本已同步 VM，VM `bash -n` 退出码 `0`。
- 实际验证：宿主机 `python -m unittest discover -s tests -v` 退出码 `0`，40 项通过；宿主机和 VM 脚本语法均通过。未覆盖当前正在运行的旧脚本进程。
- 已完成：确认 root 权限已经可用；定位 KARE 非零返回根因；完成最小、受限脚本修正并同步。
- 未完成：第二次生命周期尚未结束；修正后的第三次 root 生命周期尚未启动；最终安装/升级/卸载全成功仍未证明。
- 暂缓：图像、截图、视频和桌面演示任务不执行。
- 客观阻塞：当前旧批次需要等待其 600 秒旧 version 超时后才能结束，或由 VM 本地操作员中止；自动化通道不能修改已加载的 shell 代码。
- 待确认假设：KARE stdout 的 `status=0, 安装成功` 与 payload 同时存在可作为系统级包装层安装成功的有限证据；仍需新脚本全生命周期和最终残留检查验证。
- 下一轮最高优先级：当前批次结束后使用已同步新脚本，以 `rerun3` 新目录执行完整生命周期，并核对每步日志、包版本和真实卸载状态。

### 批次 92：第二次生命周期中止/超时证据归档（2026-09-07）

- 实际结果：VM 批次 `runs/deb-lifecycle-authorized-20260907-rerun2/` 已结束，归档到宿主机同名目录，`scp -r` 退出码 `0`。目录只生成 `preflight`、`install`、`version` 三步文件；未生成 verify、upgrade 或 uninstall 步骤文件。
- 实际退出码：`preflight=0`、`install=1`、`version=1`；`version.stderr.log` 为 `dpkg did not report kylin-memory-bench as installed within 600s.`。但批次结束后的 SSH 只读视图显示 `dpkg -s` 为 `install ok installed`、版本 `0.2.0`，`/usr/bin/kmb` 和 payload 存在，说明 root 脚本视图与 SSH shadow 视图仍不一致。
- 事实边界：该批次不是完整生命周期成功，不能把安装、升级、验证或卸载写成完成；未删除 VM/用户文件。
- 已完成：第二批失败证据安全归档；确认 600 秒等待仍无法在 root 进程视图中获得 dpkg 状态；新脚本已加入 KARE stdout 成功标记与 payload 受限兜底，并已同步 VM。
- 未完成：新脚本第三批 root 生命周期尚未启动；仍未取得完整 install/version/verify/upgrade/verify_after_upgrade/uninstall/residual_check 全成功退出码。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：VM 本地终端需要重新启动新脚本；当前自动化通道不能代替本地 root 会话，也不能修改已加载的旧 shell 代码。
- 待确认假设：同一次 KARE dpkg 输出中明确的 `status=0, 安装成功` 且 payload 存在，可以作为受限安装成功判定；第三批需通过后续严格验证和残留检查确认。
- 下一轮最高优先级：在 VM 本地终端执行新脚本第三批 `runs/deb-lifecycle-authorized-20260907-rerun3`，完成后立即归档全部退出码和日志。

### 批次 93：第三次生命周期进行中、KARE namespace 排查与脚本最小修正（2026-09-07）

- 实际环境：同一 openKylin VM；通过工作区已有 SSH 私钥只读连接 `<vm-user>@192.168.182.129:2222`，未读取或输出任何凭据内容。
- 实际启动命令（由 VM 本地已授权 root 终端启动）：`sudo bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle-authorized-20260907-rerun3 dist/rebuild-20260907/kylin-memory-bench_0.2.0_all.deb dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb`。
- 已观察结果：`preflight.exitcode=0`；安装日志包含 KARE `progress=100, status=0, errinfo=安装成功`，SSH 只读视图中 `dpkg-query` 显示 `kylin-memory-bench 0.2.0 install ok installed`，且 `/usr/bin/kmb` 与 `/usr/share/kylin-memory-bench/kmb/__init__.py` 存在。由于 root 生命周期进程与 SSH 会话处于不同 mount namespace，安装步骤最终写入 `install.exitcode=1`，版本步骤随后写入 `version.exitcode=1`，当前已进入旧 `verify-before-upgrade` 等待，完整生命周期尚未完成。不得将该批次写成成功。
- 实际错误/阻塞证据：SSH 普通用户执行 `nsenter -t <sshd-pid> -m` 返回 `Operation not permitted`；root 生命周期进程可见能力与普通 SSH 会话不同。KARE 日志还记录 `fix_depends.py` 缺少 `elftools`、若干资源目录不存在和安全库缺失，但 KARE 最终记录安装退出码 `0`。
- 实际修改：新增 `scripts/kare_namespace.sh`；更新 `scripts/install_deb.sh`、`scripts/verify_deb.sh`、`scripts/uninstall_deb.sh`、`scripts/record_deb_lifecycle.sh`，增加 KARE session namespace 探测、payload/残留检查和 root 生命周期兼容路径；未修改 Agent、评测、评分或数据集逻辑。
- 实际验证：宿主机及 VM 同步后的五个脚本均通过 `bash -n`，远端 `bash -n` 退出码 `0`。当前修改不影响已运行的旧 shell 进程；新脚本尚未启动新的 root 生命周期批次。
- 已完成：定位第三批卡住的主要边界为 KARE mount namespace 与 root/SSH 视图不一致；修正脚本已同步 VM；保留第三批进行中证据。
- 未完成：第三批 `verify/upgrade/verify_after_upgrade/uninstall/residual_check` 尚未取得退出码；不能报告完整 `.deb` 生命周期成功。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：当前 root 进程尚在旧 verifier 的 600 秒等待；自动化 SSH 用户无法终止 root 进程或进入其 namespace。KARE 的 dpkg wrapper/overlay 行为仍需在 root 本地终端重跑新脚本验证。
- 待确认假设：root 进程执行 `kare_namespace.sh` 时具备进入 SSH 会话 mount namespace 的权限，并可使 verifier/卸载检查看到 KARE payload；若不成立，需要在 VM 本地 root shell 使用 KARE 官方管理接口执行验证，不能以 host namespace 文件视图代替。
- 下一轮最高优先级：等待 `rerun3` 自然结束并归档其全部真实退出码；若仍因 namespace 失败，停止继续延长等待，在 VM 本地 root 终端以新目录执行修正脚本并记录最小失败条件。

### 批次 94：第三次生命周期失败证据归档与本地回归（2026-09-07）

- 实际环境：宿主机工作区 `E:\上海开源软件应用创新大赛`；openKylin VM `<user-home>/kmb-openkylin-validation-20260906`。VM 只读最终状态为 `kylin-memory-bench 0.2.0 install ok installed`，`/usr/bin/kmb` 和 `/usr/share/kylin-memory-bench` 仍存在；生命周期进程已结束。
- 实际命令：`scp -r -i ~/.ssh/openkylin_vm_ed25519 -P 2222 <vm-user>@192.168.182.129:<user-home>/kmb-openkylin-validation-20260906/runs/deb-lifecycle-authorized-20260907-rerun3/. runs/deb-lifecycle-authorized-20260907-rerun3/`；复制退出码 `0`。
- 实际退出码：`preflight=0`、`install=1`、`version=1`、`verify=1`；`build_upgrade`、`upgrade`、`verify_after_upgrade`、`uninstall`、`residual_check` 没有生成步骤文件。`install.stderr.log` 和 `version.stderr.log` 均为 `dpkg did not report kylin-memory-bench as installed within 600s.`；`verify.stderr.log` 为 `installed payload is not ready: /usr/share/kylin-memory-bench`。
- 结果路径：宿主机 `runs/deb-lifecycle-authorized-20260907-rerun3/`，VM 原始目录同路径；已保留命令、退出码、stdout/stderr 日志。该批次不是完整生命周期成功，不得用于证明升级或卸载完成。
- 实际本地验证：`bash -n scripts/kare_namespace.sh scripts/install_deb.sh scripts/verify_deb.sh scripts/uninstall_deb.sh scripts/record_deb_lifecycle.sh` 退出码 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，40 项通过；敏感令牌扫描输出 `secret_scan=clean`；对归档文件执行 SHA-256 计算。
- 已完成：第三批真实失败证据归档；本地回归和证据安全扫描通过；确认 VM 中安装包残留，未进行任何未经授权的清理。
- 未完成：修正脚本尚未在新的 root 生命周期批次验证；完整 `.deb` 安装、升级、升级后运行、卸载和残留检查仍未取得全成功退出码。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：SSH 用户的 `sudo -n id -u` 经 3 秒超时返回 `137`，普通用户 `nsenter` 返回 `Operation not permitted`；无法通过当前自动化会话启动 root 新批次或终止旧 root 进程。VM 本地终端仍需项目负责人执行新脚本。
- 待确认假设：新脚本在 root 权限下可使用 `nsenter` 进入 KARE SSH mount namespace；若权限模型仍拒绝，需采用 KARE 官方状态接口或在 KARE session 内完成验证。
- 下一轮最高优先级：在 VM 本地已认证 root/sudo 终端使用已同步修正脚本启动全新目录 `runs/deb-lifecycle-authorized-20260907-rerun4`，并取得全部步骤真实退出码。

### 批次 95：生命周期脚本继续执行修正与 VM 同步（2026-09-07）

- 实际修改：`scripts/record_deb_lifecycle.sh` 入口显式 `set +e`，确保单个步骤失败后继续记录后续步骤；`scripts/kare_namespace.sh` 扩大 SSH/tini 候选探测并使用 shell payload 测试；`scripts/install_deb.sh` 接受精确 KARE `status=0/安装成功` 输出后检查本地或 session payload；`scripts/verify_deb.sh`、`scripts/uninstall_deb.sh` 和 `scripts/record_deb_lifecycle.sh` 增加 session payload、版本和残留检查；修正版本查询的 shell 转义。
- 实际命令：宿主机五个脚本 `bash -n`，退出码均为 `0`；使用 `scp -i ~/.ssh/openkylin_vm_ed25519 -P 2222` 同步到 VM，`scp` 退出码 `0`；VM 五个脚本 `bash -n` 退出码 `0`。宿主机与 VM 脚本 SHA-256 一致，新增 helper 哈希为 `a292f7dc15ca0ef502cd386380eb18a610ec5afd97d14520ef84d498d40b40e8`。
- 已完成：最小脚本修正和远端同步；未改变 Agent、数据集、评分、证据协议或报告逻辑。
- 未完成：未启动新的 root 生命周期，不得把修正视为已验证；最终 LICENSE 仍待项目负责人/法务确认。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：需要 VM 本地 root/sudo 终端执行新批次；SSH 自动化会话不能代替认证或进入 KARE namespace。
- 待确认假设：root shell 具备 `nsenter` 所需能力且 KARE SSH namespace 在运行期间存在；影响新生命周期的安装后验证、升级和卸载判定。
- 下一轮最高优先级：执行并归档 `rerun4` 全生命周期；若 namespace 仍不可用，保留失败证据并转为 KARE 官方管理接口验证，不放宽验收标准。

### 批次 96：KARE upper payload 包内 smoke 验证（2026-09-07）

- 实际环境：openKylin VM `<user-home>/kmb-openkylin-validation-20260906`；通过 SSH 普通用户只读访问 KARE upper overlay，未使用或输出任何 API 凭据。
- 实际发现：`bash scripts/kare_namespace.sh --upper` 返回 `/opt/kare-applications/shadow/upper`；`dpkg-query --admindir=/opt/kare-applications/shadow/upper/var/lib/dpkg -W -f='${Package} ${Version} ${Status}\\n' kylin-memory-bench` 返回 `kylin-memory-bench 0.2.0 install ok installed`；upper payload 中存在 `/usr/bin/kmb`、`/usr/share/kylin-memory-bench` 和包内测试/脚本。
- 实际命令：`bash scripts/verify_deb.sh runs/kare-upper-verify-20260907`，退出码 `0`；另以 `KMB_HOME=/opt/kare-applications/shadow/upper/usr/share/kylin-memory-bench PATH=/opt/kare-applications/shadow/upper/usr/bin:$PATH bash scripts/verify_deb.sh runs/kare-upper-forced-verify-20260907` 执行，退出码 `0`。
- 实际结果：两项包内 smoke 测试通过；六案例 `core-zh.yaml` 校验通过；包内离线 `reference/flawed` smoke compare 生成 JSON/证据/报告并通过 `verify_run --strict`。这些是包机制验证，不是真实 Agent 结果，未纳入真实 Agent 结论。
- 结果路径：VM `runs/kare-upper-verify-20260907/`、`runs/kare-upper-forced-verify-20260907/`；使用 `scp -r -i ~/.ssh/openkylin_vm_ed25519 -P 2222` 归档到宿主机 `runs/kare-upper-verify-20260907/` 和 `runs/kare-upper-forced-verify-20260907/`，两次复制退出码均为 `0`。归档包含 JSON、JSONL、Markdown、HTML、SVG 和 smoke 日志。
- 实际修改：更新 `scripts/kare_namespace.sh` 增加 KARE upper root 探测；更新 `scripts/install_deb.sh`、`scripts/verify_deb.sh`、`scripts/uninstall_deb.sh`、`scripts/record_deb_lifecycle.sh`，优先使用 upper payload/status，verifier 支持 `KMB_HOME` 指向 upper；未修改 Agent、评分、数据集或证据协议。
- 本批次回归：宿主机五个脚本 `bash -n` 退出码均为 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，40 项通过；修正脚本通过 `scp` 同步到 VM，VM 端 `bash -n` 退出码 `0`。
- 已完成：发现并验证不依赖 `nsenter` 的 KARE upper 读取路径；包内 CLI、六案例校验和离线报告链在 upper payload 上实际可运行。
- 未完成：未取得新的 root install/upgrade/uninstall/residual_check 全成功退出码；现有 `rerun3` 仍是失败批次，VM 安装包仍残留；最终 LICENSE 仍待确认。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：SSH 用户 `sudo -n` 仍超时，不能从自动化通道启动 root 生命周期；需要 VM 本地已认证 root/sudo 终端执行 `rerun4`。
- 待确认假设：KARE upper 目录在安装、升级和卸载期间持续可读，且 `/var/lib/dpkg/status` 可作为 KARE 包状态的只读证据；若卸载后 upper 目录清理策略不同，需以真实路径检查结果为准。
- 下一轮最高优先级：VM 本地 root/sudo 终端执行新脚本 `runs/deb-lifecycle-authorized-20260907-rerun4`，完成全生命周期并归档结果。

### 批次 97：KARE upper 卸载状态检查补强（2026-09-07）

- 实际修改：`scripts/uninstall_deb.sh` 的 `package_is_installed` 增加对 KARE upper `/var/lib/dpkg/status` 的查询；卸载等待和最终残留判断同时覆盖 upper payload。未改变 dpkg remove 命令、评分、Agent 或数据集。
- 实际命令：宿主机 `bash -n scripts/uninstall_deb.sh` 退出码 `0`；使用 `scp -i ~/.ssh/openkylin_vm_ed25519 -P 2222` 同步到 VM，复制退出码 `0`；VM `bash -n scripts/uninstall_deb.sh` 退出码 `0`。
- 已完成：补强卸载状态可观测性并同步；未执行新的 root 卸载，不能把修改写成已验证。
- 未完成：完整 `rerun4` install/upgrade/verify/uninstall/residual_check 仍待 VM 本地 root/sudo 终端执行；最终 LICENSE 待确认。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：SSH `sudo -n` 无法认证且超时；普通用户没有系统级 dpkg remove 权限。
- 待确认假设：KARE 卸载后 upper status 文件会删除或将包标记为非 installed；脚本会以实际状态为准，不忽略残留。
- 下一轮最高优先级：在 VM 本地已认证 root/sudo 终端执行 `rerun4` 全生命周期并归档每一步退出码。

### 批次 98：第四次 `.deb` 生命周期验证与卸载残留定位（2026-09-08）

- 实际环境：openKylin 2.0 SP2 VM，项目目录 `<user-home>/kmb-openkylin-validation-20260906`；宿主机通过 `vmrun -T ws list` 确认 VM 正在运行，`getGuestIPAddress` 返回 `192.168.182.129`。
- 实际启动命令（VM 本地授权终端）：`sudo bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle-authorized-20260907-rerun4 dist/rebuild-20260907/kylin-memory-bench_0.2.0_all.deb dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb`。
- 实际退出码：`preflight=0`、`install=0`、`version=0`、`verify=0`、`build_upgrade=0`、`upgrade=0`、`verify_after_upgrade=0`、`uninstall=1`、`residual_check=1`。结果目录已通过 `scp -r` 退出码 `0` 归档到宿主机 `runs/deb-lifecycle-authorized-20260907-rerun4/`。
- 安装/升级/验证结果：基础包安装、版本检查、包内 smoke、六案例校验、升级构建、升级和升级后包验证均有命令、日志及结果文件支撑，均为真实退出码 `0`。包内 smoke 使用 `reference/flawed` 仅验证发布包机制，不能作为真实 Agent 参评结果。
- 卸载结果：KARE stdout 为 `卸载成功，软件包已从kare shadow环境中移除`；upper dpkg 状态查询不再找到 `kylin-memory-bench`，`/usr/bin/kmb` 已不存在。但严格残留检查发现 `/usr/share/kylin-memory-bench` 仍存在，目录内实际只有 root-owned `kmb/__pycache__/*.pyc` 和 `tests/__pycache__/*.pyc`，因此不得报告卸载成功。
- 实际修改：`scripts/verify_deb.sh` 导出 `PYTHONDONTWRITEBYTECODE=1` 并在 Python 调用处显式禁写字节码；`scripts/uninstall_deb.sh` 增加只清理该包目录内 `__pycache__`/`.pyc` 的逻辑；未修改 Agent、评分、数据集或真实运行结果。
- 本地验证：五个生命周期脚本 `bash -n` 退出码均为 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，40 项通过；工作区敏感令牌扫描 `secret_scan=clean`；修正脚本已通过 `scp` 同步 VM，VM `bash -n` 退出码 `0`。
- 结果边界：`rerun4` 是当前最完整的真实 openKylin `.deb` 证据，但不是全生命周期通过批次；安装/升级/验证通过，卸载残留失败。未删除项目外用户文件，也未清理 VM 当前残留。
- 已完成：完整 install/version/verify/build-upgrade/upgrade/verify-after-upgrade 真实验证；失败卸载证据归档；残留根因确认；禁写字节码和卸载清理修正已完成并同步 VM。
- 未完成：修正后的 `rerun5` 尚未执行，不能宣称卸载/残留检查已通过；最终 LICENSE 仍待项目负责人/法务确认；桌面演示视频仍暂缓。
- 客观阻塞：SSH 用户 `sudo -n` 认证超时，无法自动启动新的 root 批次；需要 VM 本地已认证 root/sudo 终端执行新目录批次。
- 待确认假设：重新安装后验证脚本不再生成 `.pyc`，卸载清理会使 KARE upper 的包目录、命令和 dpkg 状态全部消失；若 KARE 固定保留空目录，需将残留判定细化为“非空 payload 残留”并记录原因，不能直接放宽验收。
- 下一轮最高优先级：在 VM 本地 root/sudo 终端用已同步修正脚本执行 `rerun5`，取得 `uninstall=0` 和 `residual_check=0`，或保存新的客观失败证据。

### 批次 99：卸载残留修正同步、文档补充与回归（2026-09-08）

- 实际修改：`scripts/verify_deb.sh` 在所有包内 Python 验证前导出 `PYTHONDONTWRITEBYTECODE=1`；`scripts/uninstall_deb.sh` 卸载后仅清理 `/usr/share/kylin-memory-bench` 及 KARE upper 同名包目录内的 `__pycache__`、`.pyc` 和空目录；`docs/openkylin-validation-runbook.md`、`docs/deb-release.md` 补充 KARE shadow overlay、upper dpkg 状态和 KARE 成功日志不能替代完整生命周期的说明。未修改 Agent、数据集、评分或真实运行证据。
- 实际命令：宿主机五个生命周期脚本 `bash -n` 退出码均为 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，40 项通过；敏感令牌扫描输出 `secret_scan=clean`。`scp -i ~/.ssh/openkylin_vm_ed25519 -P 2222` 将最新 `verify_deb.sh`、`uninstall_deb.sh` 同步到 VM，复制退出码 `0`；VM 端脚本语法检查退出码 `0`。
- 实际证据归档：VM `runs/deb-lifecycle-authorized-20260907-rerun4/` 已归档到宿主机同名目录，包含 64 个文件、约 203,848 字节；为避免动态生成校验文件被自身锁定，未把不完整的 `SHA256SUMS.txt` 作为验收依据。`rerun4` 逐步退出码仍为 `preflight=0`、`install=0`、`version=0`、`verify=0`、`build_upgrade=0`、`upgrade=0`、`verify_after_upgrade=0`、`uninstall=1`、`residual_check=1`。
- 已完成：卸载失败原因已由实际 upper payload listing 确认为 root-owned Python 字节码残留；修正已同步并通过本地回归；文档已明确真实边界。
- 未完成：修正后的 `rerun5` 尚未在 VM 本地 root/sudo 终端执行，不能报告 `uninstall=0` 或 `residual_check=0`；最终 LICENSE 仍待项目负责人/法务确认；桌面演示仍暂缓。
- 暂缓：本轮未执行图像、截图、视频或桌面环境配置。
- 客观阻塞：SSH 用户 `sudo -n` 仍超时，无法从自动化通道启动 root 生命周期或删除 root-owned KARE upper 残留；VM 本地已认证终端是当前唯一可执行入口。
- 待确认假设：新验证脚本禁写字节码后，KARE 新安装不会重新产生包外 `.pyc`；卸载清理函数可在 root 进程内删除旧残留且不会触及用户结果目录。若 KARE 保留空目录，需按实际目录内容和官方包清单解释，不可无证据放宽。
- 下一轮最高优先级：在 VM 本地 root/sudo 终端执行 `rerun5` 全生命周期并归档；目标是取得卸载和残留检查真实 `0`，失败则记录最小客观原因。

### 批次 100：文档重复说明清理与最终本地回归（2026-09-08）

- 实际修改：删除 `docs/openkylin-validation-runbook.md` 和 `docs/deb-release.md` 中重复插入的 KARE overlay 说明，各保留一份；未改变技术内容。
- 实际命令：五个生命周期脚本 `bash -n` 退出码均为 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，40 项通过；工作区敏感令牌扫描输出 `secret_scan=clean`。
- 已完成：文档重复项清理，当前修正保持最小范围；`rerun4` 证据及失败边界仍完整保留。
- 未完成：`rerun5` 尚未在 VM 本地 root/sudo 终端执行；因此卸载和残留检查仍不能报告通过。最终 LICENSE 待项目负责人/法务确认；桌面演示仍暂缓。
- 客观阻塞：SSH 用户 `sudo -n` 认证超时，无法自动启动 root 生命周期；不能删除 root-owned KARE upper 残留。
- 待确认假设：下一次 root 生命周期使用已同步脚本后，验证不会产生新的字节码残留，卸载清理可以完成；若失败，保留实际 KARE 日志与残留文件清单。
- 下一轮最高优先级：在 VM 本地已认证 root/sudo 终端执行 `rerun5`，取得完整 install/upgrade/verify/uninstall/residual_check 真实退出码。

### 批次 101：生命周期证据清单修复与虚拟机访客权限探测（2026-09-08）

- 实际探测：宿主机 `E:\VMware\vmrun.exe -T ws list` 退出码 `0`，确认 `D:\openKylin-VM\openKylin.vmx` 正在运行；`vmrun getGuestIPAddress` 返回 `192.168.182.129`。`vmrun fileExistsInGuest` 在未提供访客用户名/密码时返回 `Error: Command requires valid user name and password for the guest OS`，退出码 `-1`；未尝试猜测或记录密码。
- 实际处理：首次重建 `runs/deb-lifecycle-authorized-20260907-rerun4/SHA256SUMS.txt` 的 PowerShell 相对路径表达式失败，未覆盖原始生命周期文件；随后改用绝对路径截取重建，生成 64 行 ASCII SHA-256 清单，排除清单自身。清单验证命令逐行重新计算哈希并输出 `manifest_verify=ok`。
- 结果路径：`runs/deb-lifecycle-authorized-20260907-rerun4/SHA256SUMS.txt`；原始 `rerun4` 命令、退出码和日志未被删除或覆盖。
- 已完成：证据清单格式和完整性修复；VM 运行状态和无凭据访客操作能力已实际记录。
- 未完成：修正后的 `rerun5` 尚未在 VM 本地 root/sudo 终端执行；完整卸载和残留检查仍未取得成功退出码。
- 暂缓：本轮未执行图像、截图、视频或桌面环境配置。
- 客观阻塞：`vmrun` 访客操作需要用户名和密码；SSH 用户的 `sudo -n` 认证仍超时，无法从自动化通道完成 root 生命周期。
- 待确认假设：项目负责人可在 VM 本地已认证 root/sudo 终端执行新批次；不需要把访客密码传入对话或自动化日志。
- 下一轮最高优先级：在 VM 本地 root/sudo 终端执行已同步修正脚本的 `rerun5`，并归档全量退出码、卸载残留清单和哈希。

### 批次 102：修正脚本 VM 端最终语法复核（2026-09-08）

- 实际命令：通过现有 SSH 私钥只读连接执行 `cd <user-home>/kmb-openkylin-validation-20260906; for f in scripts/kare_namespace.sh scripts/install_deb.sh scripts/verify_deb.sh scripts/uninstall_deb.sh scripts/record_deb_lifecycle.sh; do bash -n "$f"; rc=$?; printf "%s=%s\\n" "$f" "$rc"; done`。
- 实际结果：五个 VM 脚本语法检查均输出 `=0`；未执行系统写入、dpkg 操作或残留清理。
- 已完成：确认宿主机和 VM 同步脚本语法一致可解析。
- 未完成：`rerun5` 完整生命周期仍未执行；卸载和残留检查仍未取得成功退出码。
- 暂缓：本轮未执行图像、截图、视频或桌面环境配置。
- 客观阻塞：SSH 用户无可用非交互 sudo，VMware `vmrun` 访客命令需要未提供的访客密码；只能由 VM 本地已认证 root/sudo 终端启动生命周期。
- 待确认假设：VM 本地终端仍可访问 `<user-home>/kmb-openkylin-validation-20260906` 和 `dist/rebuild-20260907`，且新脚本已覆盖到该目录。
- 下一轮最高优先级：在 VM 本地 root/sudo 终端执行 `rerun5`，并将结果归档回宿主机后再报告最终生命周期状态。

### 批次 103：`rerun5` 本地 sudo 认证等待状态（2026-09-08）

- 实际环境：openKylin 2.0 SP2、x86_64；VMX `D:\openKylin-VM\openKylin.vmx` 正在运行；SSH 只读入口为 `<vm-user>@192.168.182.129:2222`。
- 实际命令：VM 本地终端已输入 `sudo bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle-authorized-20260908-rerun5 dist/rebuild-20260907/kylin-memory-bench_0.2.0_all.deb dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb`。
- 实际观察：通过 SSH 观察到外层进程 `sudo bash ...rerun5` 仍存在，VM 截图显示终端停在 `[sudo] <vm-user> 的密码:` 提示；`runs/deb-lifecycle-authorized-20260908-rerun5` 尚未在 SSH 普通用户视图中出现，未生成可读取的步骤退出码、日志或结果文件。因此本批次尚未开始可验收的生命周期步骤。
- 安全边界：未读取、回显、记录或传输 sudo 密码；未启动第二个生命周期批次；未删除或覆盖任何项目/用户文件。
- 已完成：确认当前阻塞是 VM 本地 sudo 认证等待，而不是安装、升级或卸载结果；保留现有进程和历史证据。
- 未完成：`rerun5` 的安装、版本检查、包内验证、升级、升级后验证、卸载和残留检查均无退出码，不能报告任何一步成功。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：需要项目负责人在 VM 本地终端完成 sudo 隐藏输入并按 Enter；SSH 自动化通道没有可用非交互 sudo，不能代填密码。
- 待确认假设：完成 sudo 认证后，当前终端会继续执行已输入的同一条命令；若认证失败，应只重试同一批次，不启动重复目录。
- 下一轮最高优先级：等待 `rerun5` 完成 sudo 认证并自然结束，随后通过 SSH/归档读取全部真实步骤退出码和日志。

### 批次 104：`rerun5` openKylin `.deb` 生命周期实际执行与归档（2026-09-08）

- 实际环境：openKylin 2.0 SP2、x86_64；VMX `D:\openKylin-VM\openKylin.vmx`；项目目录 `<user-home>/kmb-openkylin-validation-20260906`；Python 3.12.2、pip 26.2.1。sudo 由项目负责人在 VM 本地终端完成隐藏输入，密码未传入对话、日志或文件。
- 实际命令：`sudo bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle-authorized-20260908-rerun5 dist/rebuild-20260907/kylin-memory-bench_0.2.0_all.deb dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb`；VM 本地 root 生命周期脚本最终自然结束，宿主机通过 `scp -r -i ~/.ssh/openkylin_vm_ed25519 -P 2222` 归档，scp 退出码 `0`。
- 实际逐步退出码：`preflight=0`、`install=0`、`version=0`、`verify=0`、`build_upgrade=0`、`upgrade=0`、`verify_after_upgrade=0`、`uninstall=1`、`residual_check=1`；生命周期总体为失败，不能报告完整安装/升级/卸载验收通过。
- 安装与升级证据：KARE stdout 实际报告 `progress=100, status=0, errinfo=安装成功`，脚本随后确认 upper payload；版本日志为 `kylin-memory-bench 0.2.0 install ok installed`；升级包为 `0.2.0+test1`，升级后包内 smoke 验证和六案例 suite 校验均通过。包内 smoke 仅使用 `reference/flawed` 验证 CLI/报告机制，不是真实 Agent 结果，也未用于真实 Agent 结论。
- 卸载与残留事实：卸载 stdout 实际报告 KARE shadow 移除成功，但脚本 stderr 为 `package payload remains after removal: /usr/share/kylin-memory-bench`；SSH 只读核对显示 KARE upper dpkg 状态和 `/usr/bin/kmb` 已移除，但 root/upper 仍仅剩 `kmb/__pycache__/*.pyc`、`tests/__pycache__/*.pyc` 及目录。因此卸载和残留检查分别为 `1`，未删除项目目录外文件。
- 结果路径：VM 原始目录 `<user-home>/kmb-openkylin-validation-20260906/runs/deb-lifecycle-authorized-20260908-rerun5/`；宿主机归档目录 `runs/deb-lifecycle-authorized-20260908-rerun5/`，包含命令、stdout/stderr、逐步退出码、verify 前后 smoke 结果和 `SHA256SUMS.txt`。宿主机清单包含 64 个文件，实际校验输出 `manifest_entries=64`、`manifest_verify=ok`。
- 实际安全检查：对本批次日志和证据执行密钥/令牌模式扫描，输出 `secret_scan=clean`；未记录完整 API 密钥、密码或令牌。
- 已完成：在真实 openKylin VM 中完成 `.deb` 安装、版本检查、包内验证、升级构建、升级和升级后验证；全部证据已归档并生成哈希清单。
- 部分完成：KARE 包状态和命令卸载成功，但包外验证生成的字节码残留未被当前 root/KARE 清理路径移除，导致严格卸载验收失败。
- 未完成：完整 `uninstall=0` 与 `residual_check=0` 尚未取得；真实 Grok/DeepSeek 双 Agent 结果不在本生命周期 smoke 中，不能以 `reference/flawed` 替代。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：KARE root/SSH mount namespace 中的 upper payload 清理路径仍存在差异；当前脚本能识别并报告残留，但尚未证明可在 root 生命周期中删除 root-owned `__pycache__`。自动化 SSH 无非交互 sudo，不能自行启动下一次 root 批次。
- 待确认假设：KARE 卸载后保留的仅字节码目录可由 KARE 官方清理接口或下一版脚本在 root 进程 namespace 中安全清理；在取得实际命令和退出码前，不得放宽残留验收标准。
- 下一轮最高优先级：定位并修正 KARE root/upper 字节码清理路径后，在 VM 本地已认证 root 终端启动唯一新批次，目标是取得 `uninstall=0`、`residual_check=0`，并重新归档退出码和哈希。

### 批次 105：卸载清理覆盖 KARE session/upper 的修复与 VM 同步（2026-09-08）

- 残留根因：第 5 批实际残留为 `/usr/share/kylin-memory-bench` 及 KARE upper 中由包内 Python 验证生成的 `__pycache__/*.pyc`；原逻辑仅在卸载后清理宿主/upper 路径一次，未在已探测的 KARE session mount namespace 中清理，也未在卸载前后双阶段执行。
- 实际修改：`scripts/uninstall_deb.sh` 新增 `cleanup_tree_bytecode`，只接受 `/usr/share/kylin-memory-bench`、`/opt/kare-applications/shadow/upper/usr/share/kylin-memory-bench` 和 `/opt/kare/shadow/upper/usr/share/kylin-memory-bench`；新增 KARE session `nsenter` 清理；卸载前后均执行清理；路径不存在、重复执行和清理失败均不扩大到包目录外，最终残留检查仍硬失败。
- 实际测试：宿主机 `bash -n scripts/uninstall_deb.sh` 退出码 `0`；新增最小回归 `test_uninstall_cleanup_is_scoped_and_covers_kare_views` 通过；`python -m unittest discover -s tests -v` 退出码 `0`，41 项通过。
- 实际同步：`scp -i ~/.ssh/openkylin_vm_ed25519 -P 2222 scripts/uninstall_deb.sh ...` 退出码 `0`；VM `bash -n scripts/uninstall_deb.sh` 输出 `vm_bash_n=0`。未执行系统写入、dpkg 操作或残留清理。
- 已完成：残留清理修复代码、路径限制和本地回归；修复已同步 VM。
- 未完成：修复后的真实 openKylin 生命周期尚未执行，不能宣称卸载或残留检查已通过。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：SSH 普通用户没有可用非交互 sudo，新的 root 生命周期必须由 VM 本地已认证终端启动。
- 待确认假设：root 生命周期进程可访问并清理 KARE session mount namespace；若 `nsenter` 被 KARE 权限模型拒绝，需以实际日志为准，不放宽残留标准。
- 下一轮最高优先级：在 VM 本地已认证 root/sudo 终端执行唯一新批次 `rerun6`，再通过 SSH 归档并核对全部退出码和最终 payload listing。

### 批次 106：第六次 `.deb` 生命周期验证通过（2026-09-08）

- 实际环境：openKylin 2.0 SP2、x86_64；VM 项目目录 `<user-home>/kmb-openkylin-validation-20260906`；sudo 由项目负责人在 VM 本地终端完成，密码未传入对话、日志或文件。
- 实际命令：`sudo bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle-authorized-20260908-rerun6 dist/rebuild-20260907/kylin-memory-bench_0.2.0_all.deb dist/rebuild-20260907/kylin-memory-bench_0.2.0+test1_all.deb`；VM 批次自然结束；通过 `scp -r -i ~/.ssh/openkylin_vm_ed25519 -P 2222` 归档，scp 退出码 `0`。
- 实际逐步退出码：`preflight=0`、`install=0`、`version=0`、`verify=0`、`build_upgrade=0`、`upgrade=0`、`verify_after_upgrade=0`、`uninstall=0`、`residual_check=0`；生命周期总体成功。
- 修复验证：卸载 stdout 实际包含 `卸载成功，软件包已从kare shadow环境中移除` 和 `package removal verified`；卸载后 KARE upper `dpkg-query` 未找到 `kylin-memory-bench`，`/opt/kare-applications/shadow/upper/usr/share/kylin-memory-bench`、`/usr/share/kylin-memory-bench` 和 `kmb` 命令均不存在；未发现 `__pycache__` 或 `.pyc`。
- 包内验证：安装和升级后包内 smoke 测试各 2 项通过；六案例 suite 校验通过。包内 smoke 使用 `reference/flawed` 仅验证 CLI/报告机制，不是真实 Agent 结果，也未用于真实 Agent 结论。
- 结果路径：VM 原始目录 `<user-home>/kmb-openkylin-validation-20260906/runs/deb-lifecycle-authorized-20260908-rerun6/`；宿主机归档目录 `runs/deb-lifecycle-authorized-20260908-rerun6/`，包含命令、stdout/stderr、逐步退出码、验证子目录和 `SHA256SUMS.txt`。
- 证据完整性与安全：归档清单包含 64 个文件，实际输出 `manifest_entries=64`、`manifest_verify=ok`；批次文件敏感令牌扫描输出 `secret_scan=clean`。
- 已完成：第六次真实 openKylin 生命周期的安装、版本检查、CLI/六案例验证、升级包构建、升级、升级后验证、卸载和严格残留检查全部通过；此前字节码残留修复得到真实验证。
- 部分完成：本批次证明 `.deb` 生命周期和包内离线报告机制可验收；包内 smoke 仍不等同于 Grok/DeepSeek 真实 Agent 评测。
- 未完成：最终项目 LICENSE 仍需项目负责人/法务确认；真实 Agent 双对比需使用其独立运行证据，不能由包内 `reference/flawed` 替代。
- 暂缓：图像、截图、视频和桌面演示任务本轮不执行。
- 客观阻塞：无新的生命周期阻塞；自动化 SSH 仍无非交互 sudo，后续需要 root 写操作时须由 VM 本地已认证终端执行。
- 待确认假设：KARE 在相同版本和权限模型下保持本批次清理行为；跨 VM/版本发布仍需独立复验，不以本批次替代其他环境验证。
- 下一轮最高优先级：将 `rerun6` 全成功证据纳入赛事发布验收材料，并处理最终 LICENSE 负责人确认；不重复前 6 次生命周期验证。

### 批次 107：PDF 要求完成度审计（2026-09-08）

- 审计对象：`<user-home>\Downloads\ai_open_kylin_open_kylin_benchmark_XaCQyZepC8.pdf`；使用 PDF 文本提取逐页读取 3 页正文、命题目标、交付要求和评分表，未把示例命令/历史计划当作完成事实。
- 审计文档：`docs/pdf-compliance-audit.md`；保留既有文件/历史记录，本次为新增审计文档。
- PDF 要求总数：19 条（背景/目标、六类能力、交付要求、评审维度和评审重点均编号追踪）。按 PDF 条目统计：已完成 11 条（含范围有限项）、部分完成 7 条、明确未完成 1 条；独立列出的证据不足项为 0，但 wrapper 原生归因、稳定性和跨环境兼容性均在矩阵中标为有限/谨慎证据；许可证与发布决策另标待确认。
- 实际检查文件：`README.md`、`docs/solution.md`、`docs/evidence-protocol.md`、`docs/openkylin-validation-runbook.md`、`docs/deb-release.md`、`docs/demo-script.md`、`docs/agent-candidates.md`、`docs/dataset-provenance.md`、`docs/license-audit.md`、`docs/license-decision.md`、`NOTICE`、`CONTRIBUTING.md`、`kmb/`、`configs/`、`suites/`、`scripts/`、`tests/`、`dist/`、`runs/`。
- 实际验证命令及结果：`python -m unittest discover -s tests -v` 退出码 `0`，41 项通过；核心和对抗 suite `kmb.cli validate --strict` 均退出码 `0`；核心/对抗 Grok 与 DeepSeek wrapper 结果 `verify_run --strict` 均退出码 `0`；Grok no-memory 5 批聚合 `valid_batch_count=5`、执行成功率 100%，但 `overall_all_equal=false`；工作区媒体文件计数为 `0`；根目录 `LICENSE` 不存在；`.deb` `rerun6` 结果目录九步骤退出码均为 `0`。
- 已确认完成：Benchmark 定位、EvidenceEvent/评分/报告链、六类案例结构、真实 openKylin VM CLI、Grok/DeepSeek 真实 API、包装层和 no-memory 轨道、`.deb` 第六批完整生命周期。
- 部分完成/证据边界：每类案例数量小；真实 wrapper 结果是系统级行为，四条真实轨道 `native_memory_events=0` 且内部状态不可观测；Grok 重复分数有波动，DeepSeek 重复批次少；尚无 openKylin 原生 Agent 独立进程适配证据；部分 README/runbook/report 保留历史状态文字。
- 明确未完成：PDF 要求的 openKylin 桌面 3-5 分钟双 Agent 演示视频，当前媒体文件计数为 0。
- 许可证状态：根目录 `LICENSE` 缺失；`NOTICE` 不授予权利；项目级许可证、云 API 使用/展示、数据/Prompt/依赖再分发仍需项目负责人/法务确认。
- 最高优先级缺口：录制并保存脱敏 openKylin 桌面双 Agent 视频及 SHA256/时长元数据；随后完成许可证确认和发布文档状态统一。
- 未执行事项：本批次未修改产品代码、未重跑 API、未重跑生命周期、未录制视频/截图；仅执行只读审计和文档写入。
- 待确认假设：PDF 的“至少两款不同智能体”允许云 API 后端 + 统一 wrapper 作为系统级评测对象；若赛事要求 openKylin 原生 Agent，需额外完成独立进程适配。该假设不影响当前缺口判定。
- 下一轮唯一最高优先级：完成 PDF-12 的 openKylin 桌面双 Agent 3-5 分钟录制，并保存视频元数据、SHA256 和脱敏复现命令。

### 批次 108：许可证候选、数据集扩展与本地回归（2026-09-08）

- 本轮范围：按 PDF 审计收尾非视频事项；未执行桌面录制、截图、图像处理、`.deb` 生命周期或历史 Agent 基础运行。
- 实际许可证审计：执行 `python scripts/audit_reference_licenses.py --out runs/license-audit-20260908/inventory.json`，退出码 `0`；生成 7 个参考仓库的只读文件清单。该清单不是法律意见，所有数据、Prompt、图表、模型输出和传递依赖仍标记需人工确认。
- 实际修改：新增 `LICENSE-MIT-CANDIDATE.txt`（非生效 MIT 候选）、`THIRD_PARTY_NOTICES.md`；更新 `NOTICE`、`CONTRIBUTING.md`、`docs/license-decision.md`、`README.md`、`docs/openkylin-validation-runbook.md`、`docs/solution.md`、`docs/deb-release.md`、`docs/dataset-provenance.md`、`scripts/build_deb.sh`。根目录仍无生效 `LICENSE`，候选文本不能作为负责人/法务批准的替代。
- 数据集修改：新增 `suites/core-en.yaml`、`suites/adversarial/core-en.yaml`；将 `suites/adversarial/core.yaml` 从 6 个案例扩展为 12 个，新增冲突噪声、多键调用、版本修订、相似实体、提示注入边界和跨任务复用案例。案例/Prompt 均为项目重新编写，未复制参考仓库数据或 Prompt。
- 实际本地验证：`python -m unittest discover -s tests -v` 退出码 `0`（41 项通过）；`python -m kmb.cli validate --strict --suite suites/core-zh.yaml`、`suites/adversarial/core.yaml`、`suites/core-en.yaml`、`suites/adversarial/core-en.yaml` 均退出码 `0`，案例数分别为 6、12、6、6；`python -m compileall -q kmb scripts tests` 退出码 `0`；发布材料存在性检查退出码 `0`；工作区敏感令牌模式扫描输出 `secret_scan=clean`，退出码 `0`。
- 文档状态修正：README、runbook、solution 与 deb release 已改为引用 `runs/deb-lifecycle-authorized-20260908-rerun6/` 的九步骤全 `0` 事实；仍明确该结论只覆盖已记录的 VM/KARE 版本。所有文档继续明确 wrapper/no-memory 为系统级行为、`native_memory_events=0` 不能证明模型原生长期记忆。
- 已完成：可确认的许可证/发布边界材料、英文结构一致套件、中文对抗案例扩展、本地测试与严格套件校验、已知 `.deb` 历史状态统一。
- 部分完成：许可证仍待项目负责人/法务确认；新增案例尚未完成 Grok 与 DeepSeek 的真实 openKylin 运行；双 Agent 稳定性仍缺少可比 DeepSeek 5 批统计。
- 暂缓：桌面视频、图像和截图严格暂缓，待所有非视频发布事项完成后统一执行。
- 客观阻塞：宿主机仅能通过 SSH 访问 VM，真实重复运行依赖 VM 中安全凭据文件和网络；不读取、不回显或写入凭据。若 API/网络失败，以实际日志为准。
- 待确认假设：MIT 候选适合原创代码与 MIT 运行依赖，但需要负责人确认版权主体、贡献来源、云 API 展示条款和赛事发布策略；若不同意，删除候选并按最终决定生成根目录 `LICENSE`。
- 下一轮唯一最高优先级：在 openKylin VM 以相同核心套件、seed、超时、重试和 no-memory 配置补齐 DeepSeek 至少 5 个真实重复批次，并生成与现有 Grok 5 批可比的统计和证据。

### 批次 109：DeepSeek 五批重复运行与双 Agent 稳定性汇总（2026-09-08）

- 实际环境：openKylin 2.0 SP2、x86_64 VM；凭据从 `~/.config/kmb/credentials.env` 加载，VM 内权限检查为 `600`，未读取或输出密钥值。
- 实际命令：在 VM 项目目录执行 5 个独立命令：` .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-no-memory.yaml --suite suites/core-zh.yaml --out runs/openkylin-validation-20260908/deepseek-no-memory-repeats/repeat-<NN> --run-id deepseek-no-memory-repeat-<NN>-20260908 --seed 42 --retries 1 --timeout 180`；每批 stdout/stderr 和退出码单独保存；5 批 CLI 退出码均为 `0`。随后执行 ` .kmb-venv/bin/python scripts/aggregate_repeats.py runs/openkylin-validation-20260908/deepseek-no-memory-repeats --out .../summary.json`，退出码 `0`。
- 真实运行结果：DeepSeek 5/5 批均为 6 cases、70 evidence events，`verify_run.py --strict` 五批均退出码 `0`；执行成功率 `100%`；Overall 均值 `37.224`、样本标准差 `3.7253`、最小 `30.56`、最大 `38.89`；行为案例通过率 `13.33%`；`overall_all_equal=false`；原生记忆事件合计 `0`。失败类型合计 `confusion=6`、`erroneous_reuse=10`、`omission=15`、`stale_update=5`。
- 结果路径：`runs/openkylin-validation-20260908/deepseek-no-memory-repeats/`，含 5 个批次的 `result.json`、`evidence.jsonl`、HTML/Markdown/SVG、命令 stdout/stderr、退出码和 `summary.json/summary.md`。宿主机归档路径与 VM 相对路径一致。
- 实际修改：新增 `scripts/aggregate_stability.py`，只读合并 Grok 既有 5 批与 DeepSeek 本批 5 批，生成 `runs/openkylin-validation-20260908/stability/dual-agent-stability.json`、`.md`、`.html` 和 `stability-radar.svg`；新增 `tests/test_scripts.py::test_aggregate_stability_writes_all_report_formats`；`scripts/build_deb.sh` 纳入新脚本。
- 实际验证：`python scripts/aggregate_stability.py --grok-summary ... --deepseek-summary ...` 退出码 `0`，四类报告文件均生成；`python -m unittest discover -s tests -v` 退出码 `0`，42 项通过；DeepSeek repeat-01/repeat-05 严格校验退出码均为 `0`（5 批已全部执行同一校验）。
- 已完成：DeepSeek 至少 5 批真实重复证据、与 Grok 5 批的同配置描述性汇总、JSON/Markdown/HTML/SVG 稳定性报告、报告边界声明和单元测试。
- 部分完成：两 Agent 两组 no-memory 结果均不完全一致，不能宣称绝对稳定；统计仍是关闭外部包装层的系统级行为，不能归因模型原生长期记忆。
- 未完成：新增英文/对抗案例尚未完成两 Agent 真实运行；最终项目 LICENSE 和桌面视频仍待完成。
- 暂缓：桌面视频、图像和截图仍严格暂缓。
- 客观阻塞：云 API 网络、额度和模型服务波动可能影响后续真实运行；现有批次证据已保存，不用模拟结果填补。
- 待确认假设：Grok 2026-09-06 与 DeepSeek 2026-09-08 的模型端点和服务版本可作为同配置描述性比较，但时间不同，不应推断严格同时段公平性。
- 下一轮唯一最高优先级：固定发布版本、套件/评分器/CLI 哈希和最终非视频复现清单，并统一剩余文档中的历史状态。

### 批次 110：英文对抗套件路径部署失败（2026-09-08）

- 实际命令：VM 中执行双 Agent 对比命令 ` .kmb-venv/bin/python -m kmb.cli compare --agents configs/agent-grok-memory.yaml configs/agent-deepseek-memory.yaml --suite suites/adversarial/core-en.yaml --out runs/openkylin-validation-20260908/adversarial-en-compare --run-id adversarial-en-compare-20260908 --seed 42 --retries 1 --timeout 180`。
- 实际结果：CLI 退出码 `1`；stderr 为 `FileNotFoundError: suites/adversarial/core-en.yaml`。此前套件同步命令将顶层和子目录来源混用，未在 VM 目标路径创建 `suites/adversarial/core-en.yaml`；未生成 Agent 结果、评分或证据，不能计为评测成功。
- 归档路径：`runs/openkylin-validation-20260908/adversarial-en-compare/`，保存 `cli.stdout.log`、`cli.stderr.log` 和 `cli.exitcode`。
- 已完成：真实失败原因和退出码已确认并保留；未修改评分或 Agent 逻辑。
- 未完成：英文对抗套件真实双 Agent 运行待修正路径后重试。
- 暂缓：桌面视频、图像和截图仍严格暂缓。
- 客观阻塞：无产品逻辑阻塞；仅需在 VM 中补齐套件文件的正确子目录同步。
- 待确认假设：正确同步后，英文对抗 YAML 与本地已通过严格校验的内容一致；重试使用相同 seed、超时、重试和包装层配置。
- 下一轮最高优先级：修正 VM 套件路径并重跑英文对抗双 Agent，取得真实退出码和严格证据校验结果。

### 批次 111：openKylin 发布候选 `.deb` 构建与包内容审计（2026-09-08）

- 本轮范围：不重复第六批已通过的 `.deb` 安装/升级/卸载生命周期；仅在同一 openKylin VM 构建新的发布候选并审计包内容，未执行视频、截图或图像任务。
- 实际环境：openKylin 2.0 SP2、x86_64；VM 项目目录 `<user-home>/kmb-openkylin-validation-20260906`；通过已有 SSH 用户通道执行，无需 sudo/root。
- 实际命令：`KMB_DEB_VERSION=0.2.0+release1 bash scripts/build_deb.sh dist/release-20260908`；随后执行 `dpkg-deb --info dist/release-20260908/kylin-memory-bench_0.2.0+release1_all.deb`、`dpkg-deb --contents ...` 和包内容禁止项扫描；构建日志、命令退出码和源文件哈希写入 `runs/openkylin-validation-20260908/release-build/`，并通过 `scp` 归档到宿主机。
- 实际退出码：VM 构建 `0`；`dpkg-deb --info` `0`；`dpkg-deb --contents` `0`；禁止内容审计 `0`；日志复制 `0`；`.deb` 文件复制首次因宿主机目标目录不存在返回 `1`，创建目标目录后重试复制返回 `0`，未影响构建结果。
- 发布产物：`dist/release-20260908/kylin-memory-bench_0.2.0+release1_all.deb`，包版本 `0.2.0+release1`，架构 `all`，依赖 `python3 (>= 3.9), python3-yaml`，本地 SHA-256 `E5C0991E7641B6A92A4A71AF667F5E7592D3D1FC67F6305B900A349D8D1E8BAC`；包清单 68 行。
- 包内容审计：未发现 `credentials.env`、`.env`、`.kmb-venv`、`.tmp-github-research`、`runs/`、`__pycache__` 或 `.pyc`；包内包含 CLI、配置、四套件、报告/校验脚本、README/NOTICE/第三方 Notice 和非生效许可证候选文本。根目录生效 `LICENSE` 仍不存在，候选文件不得视为最终授权。
- 已完成：发布候选构建、版本/依赖核对、包清单和敏感/缓存内容审计；保留 VM 原始日志和本地归档。
- 部分完成：本批次只证明发布候选可构建且内容边界合规，未重新执行已通过的第六批生命周期；包仍受项目许可证待确认限制。
- 未完成：最终项目级 `LICENSE` 尚待项目负责人/法务确认；非视频最终 CLI/套件/结果结构/敏感扫描和文档路径检查尚未完成；英文对抗真实运行待同步路径修正后的成功证据仍需以已有后续批次为准。
- 暂缓：桌面视频、截图、图像和桌面录制脚本本轮不执行，按项目安排最后统一录制。
- 客观阻塞：许可证决策和云 API 使用/展示条款需要负责人/法务确认；跨 VM/版本兼容性不能由当前一次发布候选构建推断。
- 待确认假设：VM 当前工作区与宿主机冻结清单的源文件一致；发布候选内容审计未发现禁止项，但最终分发仍需项目级许可证确认。
- 下一轮最高优先级：完成最终非视频 CLI、套件、结果结构、敏感信息、文档路径和发布材料复核，生成最终复现清单并更新冻结哈希；视频仍只能在所有非视频事项完成后录制。

### 批次 112：最终非视频 CLI、套件、结果和发布材料检查（2026-09-08）

- 本轮范围：仅执行最终非视频检查；未调用云 API，未重复 `.deb` 第六批生命周期，未录制视频、截图或处理图像。
- 实际命令与退出码：`python -m unittest discover -s tests -v` `0`（42 项通过）；`python -m compileall -q kmb scripts tests` `0`；`python -m kmb.cli --help` `0`；四套件 `python -m kmb.cli validate --strict --suite ...`（`core-zh`、`adversarial/core`、`core-en`、`adversarial/core-en`）均为 `0`；中文核心和中文对抗 `list-cases` 均为 `0`；离线 `reference` `run` 和 `reference/flawed` `compare` 均为 `0`；`scripts/verify_run.py --strict` 对离线 run、reference、flawed 三份结果均为 `0`。
- 离线 smoke 边界：`runs/final-nonvideo-20260908/offline-run/` 产生 6 cases、34 events、JSON/JSONL/Markdown/HTML/SVG；`offline-compare/` 产生两 Agent 对比报告；这些仅验证 CLI/评分/报告机制，`reference/flawed` 标记为模拟基线，不计入真实 Agent 结果。
- 结果结构检查：要求的 8 个文件均存在，结构检查 `0`；退出码文件共 18 个且 `bad_count=0`。结果目录：`runs/final-nonvideo-20260908/`，包含每条命令的 stdout/stderr/exitcode。
- 安全与发布检查：敏感信息扫描输出 `secret_scan=clean`、退出码 `0`；文档/结果/证据/发布包必需路径检查 `required_paths=21`、退出码 `0`；发布候选包内容审计 `forbidden_payload=none`、退出码 `0`，包 SHA-256 为 `E5C0991E7641B6A92A4A71AF667F5E7592D3D1FC67F6305B900A349D8D1E8BAC`。
- 环境：上述命令在宿主机工作区执行；openKylin VM 的发布候选构建和包审计证据已记录于批次 111，真实 Agent 和 `.deb` 生命周期沿用既有 openKylin 证据，不以本地主机 smoke 替代。
- 已完成：最终本地测试、编译、四套件严格校验、CLI 辅助命令、离线 run/compare、严格结果结构校验、敏感扫描、文档路径检查和发布包内容复核；冻结清单所需的非视频命令均可复现。
- 部分完成：离线 smoke 不代表真实 Agent；英文/扩展套件的真实运行以既有 openKylin 结果目录为准；项目级许可证仍未生效。
- 未完成：根目录生效 `LICENSE` 仍待项目负责人/法务确认；跨 VM/版本复现和最终桌面视频尚未完成。
- 暂缓：3-5 分钟 openKylin 桌面双 Agent 视频、截图、图像和桌面录制脚本继续暂缓，必须在代码、文档、许可证、稳定性、数据集、报告和最终验收均完成后再录制。
- 客观阻塞：许可证主体/版权、云 API 服务条款及赛事展示授权没有工程侧可验证批准记录；视频需要可用的 openKylin 桌面会话和脱敏录制条件。
- 待确认假设：当前工作区与 VM 发布候选源文件一致；历史运行目录保留且路径检查通过，但不能据此宣称所有历史文档中的旧状态已被覆盖。
- 下一轮最高优先级：由项目负责人确认并落地根目录项目级许可证（或书面决定继续技术验收包状态）；确认后再冻结最终发布材料，最后统一录制并核验桌面视频。

### 批次 113：发布文档与历史状态统一复核（2026-09-08）

- 实际修改文件：`docs/solution.md`、`docs/environment-matrix.md`、`docs/deb-release.md`、`docs/agent-candidates.md`、`docs/pdf-compliance-audit.md`、`runs/openkylin-validation-20260906/final-event-report.md`、`docs/release-freeze.md`。均保留历史记录，仅追加或改写容易误读的当前状态；未修改评分、Agent、套件或运行证据。
- 状态统一内容：当前 openKylin 2.0 SP2 VM、Grok 4.6、DeepSeek v4 flash、DeepSeek/Grok 各 5 批 no-memory、中文/英文/对抗真实运行、第六批 `.deb` 九步骤全 `0`、`0.2.0+release1` 发布候选和非视频检查均已在现行章节明确；wrapper/no-memory 与模型原生能力边界继续明确为系统级行为，`native_memory_events=0`。
- 实际命令与退出码：`python -m kmb.cli validate --strict --suite suites/core-zh.yaml` `0`；必需文档/结果/包路径检查 `0`（18 项）；冻结清单 8 个源文件 SHA-256 核对 `0`；当前文档过时状态扫描 `stale_status_check=clean`、退出码 `0`；敏感信息扫描 `secret_scan=clean`、退出码 `0`。
- 证据目录：`runs/final-doc-unification-20260908/`，保存每项 stdout/stderr/exitcode；冻结哈希和状态扫描日志均可复核。
- 已完成：发布说明、Agent 接入说明、环境矩阵、方案说明、PDF 审计附录、最终报告当前状态更正和发布冻结清单统一；历史“系统级 dpkg 待验证”“DeepSeek 仅两批”等文字只保留在历史段落并由当前更正覆盖。
- 部分完成：历史报告不能删除，读者需以当前状态更正和批次 106-113 为准；多 VM/多版本兼容性未外推。
- 未完成：根目录生效 `LICENSE`、云 API/模型输出展示和数据/Prompt 再分发授权仍待负责人/法务确认；openKylin 桌面双 Agent 视频尚未录制；openKylin 原生 Agent 独立适配仍非当前两款云 API。
- 暂缓：视频、截图、图像和桌面录制脚本本轮不执行。
- 客观阻塞：许可证主体/版权和云服务条款无工程侧批准记录；视频需要可用桌面会话和最终授权后的脱敏演示材料。
- 待确认假设：发布候选源文件与 VM 同步工作区一致；当前冻结哈希只约束列出的文件，新增发布修改必须重新生成哈希。
- 下一轮最高优先级：完成项目负责人/法务对根目录许可证和云 API 展示条款的书面确认；确认后再进行最后发布冻结和桌面视频录制。

### 批次 114：英文/扩展套件成功运行证据只读核对（2026-09-08）

- 本批次为只读证据核对，未重新调用 API、未改写运行目录；用于补充批次 110 首次英文对抗路径失败后的成功重试事实。
- 实际检查目录：`runs/openkylin-validation-20260908/core-en-compare-rerun2/`、`adversarial-en-compare-rerun2/`、`adversarial-expanded-compare/`。
- 实际退出码：三目录 `cli.exitcode=0`；每目录 `grok-memory-controller.verify.exitcode=0`、`deepseek-memory-controller.verify.exitcode=0`；每目录 `comparison.json`、`comparison.md`、`comparison.html` 均存在。检查命令退出码 `0`。
- 结果核对：英文核心两 Agent 各 6 cases、70 events、Overall `86.11`；英文对抗两 Agent 各 6 cases、79 events，Grok Overall `86.11`、DeepSeek Overall `94.44`；三目录观测模式为 `system_level_wrapper_assisted`，`native_memory_events=0`。中文扩展对抗目录两 Agent 均有 6 cases、79 events，strict verify 通过。
- 证据边界：首次英文对抗 Grok HTTP 503 失败目录 `adversarial-en-compare-rerun/` 保留且不纳入成功统计；成功重试目录才纳入发布材料。所有 wrapper 分数仍只能表述为系统级行为。
- 已完成：修正上下文中“英文对抗仍未成功”“扩展套件缺少真实结果”的状态歧义；未改变任何原始证据。
- 未完成：最终项目级 `LICENSE`、云 API/模型输出展示授权、openKylin 原生 Agent 独立适配和桌面视频仍未完成或待确认。
- 暂缓：视频、截图和图像任务继续暂缓。
- 待确认假设：上述已归档结果目录未被后续工具覆盖；其 `result.json`、`evidence.jsonl` 和 strict verify 日志是权威证据。
- 下一轮最高优先级：完成根目录许可证/云 API 展示条款书面确认；之后才进入最终发布冻结和桌面录制。

### 批次 115：最终复现清单与机器可读发布 manifest（2026-09-08）

- 实际新增：`docs/final-reproduction-checklist.md`；`runs/openkylin-validation-20260908/release-manifest/release-manifest.json` 及其生成/校验日志。manifest 不含 API Key、密码、模型权重或私有数据。
- 固定内容：项目版本 `0.2.0`、发布候选 `0.2.0+release1`、openKylin 2.0 SP2 x86_64、Python/pip/setuptools/PyYAML 版本、Grok `grok-4.6`、DeepSeek `deepseek-v4-flash`、seed `42`、retries `1`、timeout `180s`、8 个源文件 SHA-256、候选包 SHA-256 和权威运行目录。
- 实际命令与退出码：manifest 生成 `0`；JSON 解析/字段校验 `0`；敏感字段扫描 `secret_scan=clean`，校验退出码 `0`。日志目录：`runs/openkylin-validation-20260908/release-manifest/`。
- 文档链接：`docs/release-freeze.md` 已链接最终复现清单和 manifest；未修改运行代码或历史证据。
- 已完成：发布版本、套件/评分器/CLI/脚本哈希、运行参数、结果目录、证据边界和最终非视频命令已具备 Markdown 与 JSON 两种清单。
- 未完成：项目级根目录 `LICENSE` 和云 API/模型输出展示授权仍待项目负责人/法务确认；桌面视频仍暂缓；跨 VM/版本兼容性未外推。
- 暂缓：本轮不录制视频、截图或处理图像。
- 待确认假设：manifest 中列出的哈希和目录在负责人确认许可证后仍保持不变；任何发布修改都必须重新生成 manifest。
- 下一轮最高优先级：取得项目负责人/法务对许可证和云 API 展示条款的书面确认，然后执行最终发布冻结与桌面视频录制前检查。

### 批次 116：生命周期/变形/行动证据实现第一批回归（2026-09-08）

- 本轮任务：按创新定位 `KylinMemBench：面向 openKylin 的长期记忆生命周期、安全边界与真实行动证据 Benchmark`，增量实现生命周期事实元数据、事件证据链、变形组 schema 和沙箱行动证据；未执行视频、截图、媒体或既有 `.deb` 生命周期。
- 实际修改文件：`kmb/models.py`、`kmb/scoring.py`、`kmb/runner.py`、`kmb/agents.py`、`kmb/report.py`、`suites/lifecycle/innovation.yaml`。
- 主要实现：事实元数据包含 `persistence/sensitivity/scope/version/expires_at/ttl_steps/provenance`；`EvidenceEvent` 支持事件 ID、父事件、关联 ID、事实版本、作用域、工件路径/SHA256、可信等级和 `restart_boundary`；runner 为事件建立可追溯关联并汇总证据链；评分器新增 TTL 过期、作用域隔离、敏感信息拒绝、版本、重建边界、工件存在/内容/退出码、证据链和变形组规则；包装层只在项目内 action sandbox 写入文件，记录实际文件、SHA256、tool result 和退出码，重建边界明确 `system_restart=false`。
- 新套件：`suites/lifecycle/innovation.yaml` 共 13 个案例，覆盖完整生命周期、TTL、合成敏感 token、作用域隔离、版本更新，以及路径变化、无关措辞、相似实体、token 边界、作用域变化五类变形关系。套件未使用真实敏感值。
- 实际命令与退出码：`python -c "import yaml; ... innovation.yaml ..."` `0`（13 cases 可解析）；`python -m py_compile kmb/models.py kmb/scoring.py kmb/runner.py kmb/agents.py kmb/report.py` `0`；`python -m unittest discover -s tests -v` `0`（42 项通过）。
- 结果与证据：本批次为代码/协议/离线回归批次，未调用 Grok/DeepSeek；未生成真实 Agent 运行分数。既有历史真实结果仍只能解释为模型后端加外部包装层的系统级行为，不能证明模型原生记忆。
- 已完成：第一批 schema、包装层和评分增量通过既有测试，旧案例/旧评分引用兼容；事件链字段和工件证据代码已落地。
- 部分完成：新套件尚未执行 CLI 严格校验、生命周期离线运行、变形组报告和专门新测试；`NoMemoryAgent` 尚未针对所有新元数据提供等价动作证据；真实 Grok/DeepSeek 新案例运行尚未执行。
- 未完成/暂缓：系统级真实重启、用户切换、离线、权限变更仍需受控 openKylin 执行器；视频、截图和媒体继续暂缓；项目许可证和云 API 展示授权仍按批次 115 待确认。
- 客观阻塞：当前宿主机未在本批次重新调用云 API，不能将离线回归写成真实双 Agent 新结果。
- 待确认假设：变形组 `must_change/invariants` 字段采用本批次 schema，后续若赛事数据格式有额外要求需在不破坏旧字段的情况下扩展。
- 下一轮最高优先级：完成 `innovation.yaml` 严格校验、包装层生命周期/变形/工件专项单元测试和离线 CLI 运行，修复实际失败后再更新报告与文档。

### 批次 117：生命周期/变形/行动证据专项测试与作用域修复（2026-09-08）

- 实际问题：首次包装层专项测试发现 `memory_recall` 的元数据合并顺序会用事实原作用域覆盖请求作用域，导致跨作用域拒绝事件无法被确定性评分；已在 `kmb/agents.py` 修正 payload 合并顺序。
- 实际新增测试：`tests/test_lifecycle_innovation.py`，覆盖旧案例元数据迁移、包装层完整生命周期、TTL、敏感 token、作用域隔离、重建边界、沙箱工件和 SHA256、runner 证据链与变形组。
- 实际命令与退出码：`python -m unittest tests.test_lifecycle_innovation -v` 首次退出 `1`（作用域事件合并顺序问题），修复后重跑退出 `0`（4 项通过）；`python -m unittest discover -s tests -v` 退出 `0`（46 项通过）。
- 套件验证：`python -m kmb.cli validate --strict --suite suites/lifecycle/innovation.yaml` 退出 `0`，当前 15 cases、六类能力齐全。
- 离线 CLI 证据：`python -m kmb.cli run --agent configs/agent-reference.yaml --suite suites/lifecycle/innovation.yaml --out runs/innovation-offline-20260908 --run-id innovation-offline --seed 42 --retries 0 --timeout 30` 退出 `0`；`python -m kmb.cli compare --agents configs/agent-reference.yaml configs/agent-flawed.yaml --suite suites/lifecycle/innovation.yaml --out runs/innovation-compare-offline-20260908 --run-id innovation-compare --seed 42 --retries 0 --timeout 30` 退出 `0`。两者仅验证 CLI/评分/变形报告机制，`reference/flawed` 仍明确为模拟基线，不是真实参评 Agent。
- 结果路径：`runs/innovation-offline-20260908/`、`runs/innovation-compare-offline-20260908/`；结果已包含 `evidence_schema_version=2`、事件关联覆盖率、变形组结果、JSON/Markdown/HTML/SVG 报告。离线参考 Agent 因不执行包装层重建/沙箱工件而被相应规则判失败，未被冒充为成功。
- 已完成：新套件解析和严格校验、包装层专项测试、作用域评分修复、旧回归保持通过、离线 CLI run/compare 和组级报告生成。
- 部分完成：真实 Grok/DeepSeek 尚未运行本套件；`NoMemoryAgent` 的系统级新生命周期扩展未单独实现；变形组目前以声明式关系和确定性规则为主。
- 未完成/暂缓：真实系统重启、用户切换、离线和权限变更仍需受控 openKylin 执行器；视频、截图、媒体继续暂缓；最终许可证和云 API 展示授权仍待确认。
- 客观阻塞：本批次未从 VM 读取凭据或调用云 API，不能把离线 fixture/模拟 Agent 结果写成真实双 Agent 新结果。
- 待确认假设：`wrapper_rebuild` 是受控内存/控制器重建检查点，不等价于 OS 重启；沙箱中的 `/data/*` 仅作为逻辑目标，实际文件始终写入项目内专用 action root。
- 下一轮最高优先级：对新增生命周期套件执行 `verify_run`/证据 JSONL 严格结构校验，检查报告内容和文件工件哈希，再评估是否具备在 VM 凭据可用时运行新增案例的条件。

### 批次 118：生命周期协议与复现文档更新、离线结果严格校验（2026-09-08）

- 实际修改文件：`docs/evidence-protocol.md`、`docs/solution.md`、`docs/openkylin-validation-runbook.md`、`README.md`；新增内容说明 schema v2 事件链字段、事实生命周期元数据、变形组规则、沙箱行动工件和系统级重启边界。
- 实际命令与退出码：`python -m kmb.cli validate --strict --suite suites/lifecycle/innovation.yaml` `0`（15 cases）；`python -m kmb.cli run --agent configs/agent-reference.yaml --suite suites/lifecycle/innovation.yaml --out runs/innovation-offline-20260908 --run-id innovation-offline-v2 --seed 42 --retries 0 --timeout 30` `0`；`python -m kmb.cli compare --agents configs/agent-reference.yaml configs/agent-flawed.yaml --suite suites/lifecycle/innovation.yaml --out runs/innovation-compare-offline-20260908 --run-id innovation-compare-v2 --seed 42 --retries 0 --timeout 30` `0`。
- 证据严格校验：`python scripts/verify_run.py runs/innovation-offline-20260908 --strict` `0`（15 cases、90 events）；`python scripts/verify_run.py runs/innovation-compare-offline-20260908/reference --strict` `0`；`python scripts/verify_run.py runs/innovation-compare-offline-20260908/flawed --strict` `0`。结果包含 JSON/JSONL、Markdown、HTML、SVG；`evidence_schema_version=2`、关联覆盖率 `1.0`、变形组和失败理由均已写入。
- 结果边界：离线 `reference/flawed` 只验证 CLI、评分、报告和变形组输出，报告明确标记 `simulated_baseline`；reference 缺少包装层重建/沙箱工件时被确定性规则判失败，不能作为真实 Agent 结果。包装层专项 fake-backend 的真实工件、退出码和 SHA256 已由批次 117 的单元测试验证，但未冒充云模型运行。
- 已完成：协议、方案、README 和 openKylin runbook 的创新层说明已统一；新增套件的离线输出可由严格校验器读取。
- 部分完成：release manifest 的源文件哈希尚未因本轮代码/文档修改重新冻结；真实 Grok/DeepSeek 尚未运行新增套件；系统级测试边界仍需 VM 控制器。
- 未完成/暂缓：视频、截图、媒体继续暂缓；最终项目许可证和云 API 展示/留存授权仍待确认。
- 客观阻塞：本批次无 API 凭据调用，不能报告新增案例的真实双 Agent 分数。
- 待确认假设：现有发布候选 `.deb` 不包含本轮新增代码/套件，若要将创新层纳入分发包需重新在 openKylin 构建并做包内容审计。
- 下一轮最高优先级：执行本轮新增代码/文档的完整非视频回归（compileall、46 项测试、四套件加创新套件校验、敏感信息扫描、路径检查），并重新生成发布 manifest 哈希；API 可用时再单独运行新增真实双 Agent 批次。

### 批次 119：创新层最终非视频回归与证据结构检查（2026-09-08）

- 实际命令与退出码：`python -m unittest discover -s tests -v` `0`（46 项通过）；`python -m compileall -q kmb scripts tests` `0`；`python -m kmb.cli --help` `0`；`python -m kmb.cli validate --strict --suite suites/core-zh.yaml` `0`（6）、`suites/adversarial/core.yaml` `0`（12）、`suites/core-en.yaml` `0`（6）、`suites/adversarial/core-en.yaml` `0`（6）、`suites/lifecycle/innovation.yaml` `0`（15）。
- 创新套件重新运行：`python -m kmb.cli run --agent configs/agent-reference.yaml --suite suites/lifecycle/innovation.yaml --out runs/innovation-offline-20260908 --run-id innovation-offline-v3 --seed 42 --retries 0 --timeout 30` `0`；`python -m kmb.cli compare --agents configs/agent-reference.yaml configs/agent-flawed.yaml --suite suites/lifecycle/innovation.yaml --out runs/innovation-compare-offline-20260908 --run-id innovation-compare-v3 --seed 42 --retries 0 --timeout 30` `0`。
- 严格结构校验：三个输出目录 `python scripts/verify_run.py ... --strict` 均退出 `0`；reference 单 run `15 cases/90 events`；结果 `evidence_schema_version=2`、`metamorphic_groups=5`、证据链关联覆盖率 `1.0`。必需 JSON/JSONL/Markdown/HTML/SVG 路径检查输出 `required_paths=0`。
- 安全检查：内容型敏感令牌扫描输出 `secret_scan=clean`、退出码 `0`；未输出或写入完整 API 密钥。工作区中若出现 `token`/`secret` 文件名均来自已隔离的参考仓库或依赖源代码，不代表凭据。
- 已完成：创新层代码、协议、套件、专项测试、全量回归、CLI/报告生成和严格证据结构校验。
- 部分完成：本轮 run/compare 使用 `reference/flawed` 仅做离线机制验证；真实 Grok/DeepSeek 尚未运行创新套件，因此没有新增真实双 Agent 分数。`dist/release-20260908` 发布候选和批次 115 manifest 未包含本轮修改，需重新构建/审计/冻结后才能把创新层纳入发布包。
- 未完成/暂缓：真实系统重启、用户切换、离线、系统权限变化仍需受控 openKylin 执行器；视频、截图、媒体继续暂缓；根目录项目 LICENSE 和云 API 展示/留存授权仍待负责人/法务确认。
- 客观阻塞：本批次未从 VM 读取安全凭据、未调用 Grok/DeepSeek，不能用离线基线替代真实双 Agent 结果。
- 待确认假设：项目负责人将接受 `restart-boundary` 的受控包装层重建作为生命周期内检查点，同时把系统级重启能力单独标记为待受控环境执行。
- 下一轮最高优先级：重新构建并审计包含本轮创新层的 openKylin `.deb`，更新 release manifest 哈希；若 VM 凭据/网络可用，再运行创新套件的 Grok/DeepSeek wrapper 双 Agent 实例并严格归档证据。

### 批次 120：变形组对比报告补充与最终结构复核（2026-09-08）

- 实际修改：`kmb/report.py` 的 `comparison.md` 增加变形组汇总，列出每个 Agent 的组级 PASS/FAIL；未改变评分或历史运行目录之外的生命周期证据。
- 实际命令与退出码：`python -m kmb.cli compare --agents configs/agent-reference.yaml configs/agent-flawed.yaml --suite suites/lifecycle/innovation.yaml --out runs/innovation-compare-offline-20260908 --run-id innovation-compare-v4 --seed 42 --retries 0 --timeout 30` `0`；`python -m unittest tests.test_lifecycle_innovation tests.test_cli_report -v` `0`（9 项通过）；两个 compare 子目录 `python scripts/verify_run.py ... --strict` 均 `0`（15 cases、90 events）。
- 报告证据：`runs/innovation-compare-offline-20260908/comparison.md` 已包含 `path-update`、`scope-isolation`、`similar-entity-no-confusion`、`token-boundary`、`wording-invariance` 五个组级结果；JSON/HTML 同步保留变形组、证据链和观测边界。
- 已完成：变形组结果在单 Agent 和双离线对比报告中均可见，严格校验仍通过。
- 部分完成：仍未执行真实 Grok/DeepSeek 创新套件；离线 reference/flawed 只作机制基线；发布候选和 release manifest 尚未重新构建以纳入本轮修改。
- 未完成/暂缓：系统级重启/用户切换/离线/权限执行器、最终许可证确认、桌面视频继续未完成或暂缓。
- 下一轮最高优先级：更新发布包与 manifest（包含本轮创新代码/套件/文档）并在 openKylin VM 进行包内容审计；凭据和网络可用时执行真实双 Agent 创新批次。

### 批次 121：openKylin VM Grok 创新套件真实运行（2026-09-08）

- 环境：openKylin 2.0 SP2 x86_64 VM，项目目录 `<user-home>/kmb-openkylin-validation-20260906`，`.kmb-venv`；凭据文件仅确认存在且权限为 `600`，通过本地 shell 加载，未读取、回显或写入上下文包。
- 同步：`scp` 同步 `kmb/models.py`、`kmb/scoring.py`、`kmb/runner.py`、`kmb/agents.py`、`kmb/report.py` 和 `suites/lifecycle/innovation.yaml`；六个文件 SHA256 与宿主工作区一致；VM 套件严格校验 `0`（15 cases），Python 编译 `0`。
- 安全处理：一次同步命令误将本地私钥路径列入 `scp` 源参数，可能创建 VM 项目内同名副本；已立即执行 `rm -f` 删除并验证 `private_key_copy_absent`，未读取或输出私钥内容。该安全事件不影响项目凭据文件，后续同步命令已移除该参数。
- 实际运行命令（VM）：加载 `~/.config/kmb/credentials.env` 后执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260908/innovation-grok-wrapper --run-id innovation-grok-wrapper-20260908 --seed 42 --retries 1 --timeout 180`。CLI stdout 返回 `agent=grok-memory-controller`、`overall=97.78`、退出路径生成完整结果；严格校验命令 `.kmb-venv/bin/python scripts/verify_run.py ... --strict` 退出 `0`。
- 真实结果：15 cases、192 evidence events、`evidence_schema_version=2`、5 个变形组、`native_memory_events=0`、`wrapper_memory_events=34`；宿主归档目录 `runs/openkylin-validation-20260908/innovation-grok-wrapper/` 含 `evidence.jsonl`、`result.json`、`result.md`、`result.html`、`radar.svg`、CLI/verify 日志和退出码，宿主再次 strict verify `0`。
- 退出码记录说明：首次远程收尾命令因 PowerShell 对 `$?` 的转义错误返回 `1`，但 API CLI 已写出结果；原始异常记录保留为 `cli.exitcode.recorder-error`，通过独立 strict verify `0` 后将 `cli.exitcode` 修正记录为 `0`。不得把收尾命令 `1` 误报为 CLI 评测失败。
- 结论边界：本批次是 Grok 4.6 配置下“模型后端 + 外部包装层”的真实系统级行为结果；原生记忆事件为 `0`，不能表述为 Grok 原生长期记忆能力。
- 已完成：Grok 创新套件真实 VM 运行、证据导出、评分、变形组/证据链报告和严格结构校验。
- 未完成：DeepSeek 创新套件尚未运行；双 Agent 新套件对比报告尚未生成；发布包/manifest 尚未纳入本轮代码。
- 暂缓：视频、截图、媒体继续不执行。
- 客观阻塞：无本批次 API 阻塞；首次收尾命令转义错误已隔离并保留记录。
- 待确认假设：`credentials.env` 的非敏感配置仍与已确认的 Grok 4.6 模型配置一致；仅以 CLI 结果和报告中的模型元数据为证，不读取凭据值。
- 下一轮最高优先级：使用相同 seed、重试、超时和套件运行 DeepSeek wrapper，严格校验后再生成双 Agent 新套件 compare 报告。

### 批次 122：创新套件双 Agent 结果、证据哈希与安全记录补齐（2026-09-08）

- 本批次用途：补齐批次 121 后已实际产生但尚未写入上下文包的 DeepSeek、双 Agent 汇总、证据结构和安全扫描记录；不重复运行已通过的基础套件或 `.deb` 生命周期。
- 实际检查的真实结果：`runs/openkylin-validation-20260908/innovation-grok-wrapper/` 与 `innovation-deepseek-wrapper/` 均为 15 cases、192 events；两份 `verify.stdout.log` 均报告 `status=valid`，对应 `verify.exitcode=0`。
- Grok 结果：模型 `grok-4.6`，Overall `97.78`；维度为 task_reuse `100.0`、boundary `100.0`、similar_distinction `100.0`、dynamic_update `66.67`、retention `100.0`、memory_recall `100.0`；5 个变形组均通过；`native_memory_events=0`、`wrapper_memory_events=34`、证据链覆盖率 `1.0`、9 个工件事件均带 `trust_level=verified`。
- DeepSeek 结果：模型 `deepseek-v4-flash`，Overall `97.78`；维度与 Grok 相同；5 个变形组均通过；`native_memory_events=0`、`wrapper_memory_events=34`、证据链覆盖率 `1.0`、9 个工件事件均带 `trust_level=verified`。
- 双 Agent 汇总：`runs/openkylin-validation-20260908/innovation-dual-compare/` 含 `comparison.json`、`comparison.md`、`comparison.html` 和两份雷达图；两 Agent 均列为 `system_level_wrapper_assisted`，没有原生记忆事件，不能据此证明模型原生长期记忆能力。
- 证据结构：两份 `evidence.jsonl` 各 192 行，事件包含 schema v2、父事件/关联 ID、来源类别、事实版本/作用域及沙箱工件路径和 SHA256；双 Agent comparison 中 `link_coverage=1.0`、`artifact_events=9`。
- 安全记录：凭据未被读取、回显或写入上下文包；批次 121 中误传的私钥同名副本已删除并验证 `private_key_copy_absent`。本批次未发现新的完整密钥输出。
- 实际命令与退出码：宿主机读取并核对两份 `.kmb` 结果的严格校验记录均为 `0`；结果目录中的 CLI `cli.exitcode` 均为 `0`；双 Agent comparison 文件存在性检查为 `0`。
- 已完成：真实 DeepSeek 创新套件证据、双 Agent 组级报告、证据链/工件字段和安全边界记录补齐。
- 部分完成：本批次仅核对已归档真实运行，不新增 API 调用；创新套件多批稳定性仍未单独统计，现有稳定性统计仍以 no-memory 五批为主。
- 未完成：发布候选 `.deb` 和 release manifest 尚未纳入本轮创新代码/套件/文档；系统级真实重启、用户切换、离线和权限变更仍需受控 openKylin 执行器；根目录项目级 LICENSE 与云 API 展示授权仍待负责人/法务确认。
- 暂缓：视频、截图、图像和媒体任务继续不执行。
- 客观阻塞：当前 VM 可通过 SSH `2222` 用户通道访问；若打包需要 root 写入系统目录，仍需 VM 内已认证终端，不在本批次擅自请求或记录密码。
- 待确认假设：已归档的创新双 Agent结果目录未被后续命令覆盖；其 `result.json`、`evidence.jsonl` 和严格校验日志为当前权威证据。
- 下一轮最高优先级：在 openKylin VM 重新构建并审计纳入创新层的 `.deb`，随后重新生成发布 manifest 和源文件哈希；不重复第六批生命周期。

### 批次 123：纳入创新层的 openKylin `.deb` 重建与包内容审计（2026-09-08）

- 本批次范围：将当前 `kmb/`、四类套件、`suites/lifecycle/innovation.yaml`、文档和打包脚本同步到已有 openKylin VM，构建新的发布候选并执行包内容、创新套件和离线 smoke 审计；不重复第六批安装/升级/卸载生命周期，不执行视频或媒体任务。
- VM 环境：openKylin 2.0 SP2、x86_64；项目 `<user-home>/kmb-openkylin-validation-20260906`；通过用户 SSH `192.168.182.129:2222` 访问；未读取或输出凭据。
- 实际同步：`scp -P 2222` 同步 `kmb configs suites docs scripts packaging pyproject.toml setup.py README.md CHANGELOG.md NOTICE THIRD_PARTY_NOTICES.md LICENSE-MIT-CANDIDATE.txt`，退出码 `0`；同步内容不含 `runs`、虚拟环境或凭据文件。
- 构建命令：`KMB_DEB_VERSION=0.2.0+release2 bash scripts/build_deb.sh dist/release-20260908-release2`，VM 退出码 `0`；日志和退出码见 `runs/openkylin-validation-20260908/release-build-innovation/build.stdout.log`、`build.stderr.log`、`build.exitcode`。
- 发布产物：`dist/release-20260908-release2/kylin-memory-bench_0.2.0+release2_all.deb`，大小 `78036` bytes，SHA-256 `ef3e308a135351099f527d1d3d379c86e15fc2ad95e31fb378563a9c4ca911c1`。
- 包审计命令：`dpkg-deb --info`、`dpkg-deb --contents`、禁止内容扫描、临时目录解包后的 `python3 -m kmb.cli validate --strict --suite suites/lifecycle/innovation.yaml`、核心套件校验和 `tests/smoke_test.py`；审计退出码 `0`，创新套件 `15 cases`，核心套件 `6 cases`，smoke `2 tests` 通过；`forbidden_payload=none`。审计记录见 `runs/openkylin-validation-20260908/release-build-innovation/audit.stdout.log`、`audit.stderr.log`、`audit.exitcode`。
- 包内容确认：包含最新 `kmb/agents.py`、`models.py`、`runner.py`、`scoring.py`、`report.py` 和 `suites/lifecycle/innovation.yaml`；未包含 credentials、`.env`、虚拟环境、缓存、`runs/`、`__pycache__` 或 `.pyc`。
- 已完成：创新层已纳入新的 openKylin `.deb` 发布候选并通过内容边界、创新套件和离线 smoke 审计。
- 部分完成：本批次只构建/审计包，未重新执行已通过的第六批系统生命周期；对外再分发仍受项目级 LICENSE 和云 API 展示授权待确认限制。
- 未完成：release manifest 尚未更新到 `release2` 及创新层哈希；系统级重启、用户切换、离线和权限变化仍需受控执行器；桌面视频继续暂缓。
- 客观阻塞：无新的构建或包审计阻塞；VM root 生命周期不在本批次范围内。
- 待确认假设：VM 同步后的源文件与宿主工作区一致，包内容审计覆盖当前发布候选；任何后续发布文件修改都必须重新构建并重新计算 manifest。
- 下一轮最高优先级：生成包含 `release2` 包、创新套件、代码/文档 SHA-256 和权威真实创新运行目录的发布 manifest，并通过 JSON/敏感字段校验。

### 批次 124：发布文档同步后的 `release2` 最终重建与审计（2026-09-08）

- 本批次原因：发布冻结、最终复现清单和 `.deb` 说明已改为引用 manifest 中的最终包哈希，避免包内文档与包自身哈希形成循环；同步三份文档后重新构建同一 `release2` 版本。
- 实际同步命令：通过 `scp -P 2222` 同步 `docs/release-freeze.md`、`docs/final-reproduction-checklist.md`、`docs/deb-release.md` 到 VM，退出码 `0`。
- 实际构建命令：`KMB_DEB_VERSION=0.2.0+release2 bash scripts/build_deb.sh dist/release-20260908-release2`，openKylin VM 退出码 `0`；构建日志见 `runs/openkylin-validation-20260908/release-build-innovation-final/`。
- 最终包：`dist/release-20260908-release2/kylin-memory-bench_0.2.0+release2_all.deb`，大小 `78440` bytes；当前 SHA-256 `f5aefb7a014b48f953b421d766bfbae53b8b778536d4950121828706520ad151`。
- 最终审计：`dpkg-deb --info`、`dpkg-deb --contents`、禁止内容扫描、解包后的创新套件严格校验（15 cases）、核心套件校验（6 cases）和包内 `tests/smoke_test.py`（2 tests）均退出码 `0`；输出 `forbidden_payload=none`。审计日志见 `runs/openkylin-validation-20260908/release-build-innovation-final/audit.stdout.log`、`audit.stderr.log`、`audit.exitcode`。
- 包内容确认：创新层代码、`suites/lifecycle/innovation.yaml`、更新后的发布文档均已进入包；未包含凭据、虚拟环境、缓存、`runs/`、`__pycache__` 或 `.pyc`。
- 已完成：发布文档与创新层同步后的最终 `release2` 包构建和包级验证。
- 部分完成：本批次仍未重复第六批系统生命周期；项目级 LICENSE、云 API 展示授权、系统级重启/用户切换/离线/权限变化执行器和桌面视频仍未完成或待确认。
- 暂缓：视频、截图、图像和媒体任务继续不执行。
- 客观阻塞：无新的构建或包审计阻塞；`release2` 仍仅作为技术验收候选，外部分发受许可证确认限制。
- 待确认假设：本批次之后不再修改被打包的代码/文档；如有任何发布文件变更，必须重新构建并更新 manifest。
- 下一轮最高优先级：生成并校验最终 release manifest，纳入 `release2` 包哈希、创新套件和代码/文档哈希及创新真实运行证据。

### 批次 125：release manifest 首次生成与结构/敏感字段校验（2026-09-08）

- 实际产物：`runs/openkylin-validation-20260908/release-manifest-final/release-manifest.json`，记录 `release2` 候选包、openKylin 环境、Grok/DeepSeek 模型、统一参数、18 个源文件 SHA-256、创新双 Agent 真实运行目录和包装层能力边界。
- 首次生成时记录的包 SHA-256：`f5aefb7a014b48f953b421d766bfbae53b8b778536d4950121828706520ad151`；生成退出码 `0`。
- 校验命令：JSON 解析、必需字段、两 Agent、包哈希、18 个源文件哈希、`full_keys_in_manifest=False` 和敏感模式扫描；校验退出码 `0`，日志见 `runs/openkylin-validation-20260908/release-manifest-final/generate.stdout.log`、`generate.exitcode`、`validate.stdout.log`、`validate.exitcode`。
- 说明：随后发现发布文档引用旧 manifest 路径，已将引用统一改为本目录并准备重新构建；本批次 manifest 作为历史中间记录保留，不作为最终冻结哈希。
- 已完成：manifest 字段结构、哈希核对和敏感字段门禁逻辑已验证。
- 部分完成：文档路径变更会改变包内容，最终包哈希和 manifest 需下一批重新生成。
- 未完成：最终 release2 包/manifest 尚未在文档路径固定后重新冻结；许可证、系统级执行器和视频仍待确认/暂缓。
- 下一轮最高优先级：同步固定 manifest 路径文档，重新构建并审计 release2，再生成最终 manifest。

### 批次 126：固定 manifest 目录后的 `release2` 再构建与包审计（2026-09-08）

- 实际同步：将三份发布文档改为引用 `runs/openkylin-validation-20260908/release-manifest-final/release-manifest.json`，通过 `scp -P 2222` 同步到 openKylin VM，退出码 `0`。
- 实际构建：`KMB_DEB_VERSION=0.2.0+release2 bash scripts/build_deb.sh dist/release-20260908-release2`，VM 构建退出码 `0`；日志目录 `runs/openkylin-validation-20260908/release-build-innovation-final2/`。
- 包审计：`dpkg-deb --info`、`dpkg-deb --contents`、禁止内容扫描、创新套件严格校验（15 cases）、核心套件校验（6 cases）和包内 smoke（2 tests）均退出码 `0`，`forbidden_payload=none`。
- 当前包：`dist/release-20260908-release2/kylin-memory-bench_0.2.0+release2_all.deb`，大小 `78452` bytes，SHA-256 `1d63bd1139fa48863c8e1a862c5a68f5af48ebd2cafc3fda15041f28f667bfad`。
- 已完成：固定目录文档版本对应的包级构建、创新套件校验和敏感内容审计。
- 部分完成：为避免覆盖批次 125 中间 manifest，最终 manifest 将使用新文件名；包哈希会随文档路径最后一次变更后重新计算。
- 未完成/暂缓：最终 manifest 文件名固定、项目级 LICENSE、系统级执行器和视频仍待确认或暂缓；不重复第六批生命周期。
- 下一轮最高优先级：将文档引用切换到新的 `release-manifest-release2.json`，最后重建包并生成/校验最终 manifest。

### 批次 127：最终 `release2` 发布包与机器可读 manifest 冻结（2026-09-08）

- 实际同步：将三份发布文档切换为 `release-manifest-final/release-manifest-release2.json`，通过 `scp -P 2222` 同步到 openKylin VM，退出码 `0`。
- 最终构建命令：`KMB_DEB_VERSION=0.2.0+release2 bash scripts/build_deb.sh dist/release-20260908-release2`，openKylin VM 构建退出码 `0`；日志目录 `runs/openkylin-validation-20260908/release-build-innovation-final3/`。
- 最终包：`dist/release-20260908-release2/kylin-memory-bench_0.2.0+release2_all.deb`，大小 `78456` bytes，SHA-256 `af7d6148512da83d5ab57a4c37ffd846d2669ef8a3c2d1da70a025d8abeb8b81`。
- 最终包审计：`dpkg-deb --info`、`dpkg-deb --contents`、禁止内容扫描、创新套件严格校验（15 cases）、核心套件校验（6 cases）和包内 smoke（2 tests）均退出码 `0`，输出 `forbidden_payload=none`。
- 最终 manifest：`runs/openkylin-validation-20260908/release-manifest-final/release-manifest-release2.json`；生成退出码 `0`，包含 18 个源文件 SHA-256、最终包哈希、openKylin 环境、Grok/DeepSeek 模型、创新真实运行目录、wrapper 原生能力边界和系统级测试限制。
- manifest 校验：JSON/必需字段/双 Agent/包哈希/18 个源哈希/`full_keys_in_manifest=False`/敏感模式扫描均为退出码 `0`；日志 `runs/openkylin-validation-20260908/release-manifest-final/validate-release2.stdout.log`、`validate-release2.exitcode`。
- 已完成：创新层纳入 openKylin 发布候选，最终包、文档引用和 manifest 哈希已冻结；未重复第六批生命周期。
- 部分完成：该发布候选只完成包级审计，不等价于新一轮系统安装/升级/卸载；稳定性统计仍以 no-memory 五批为主。
- 未完成：项目级根目录 LICENSE 和云 API 展示授权仍待负责人/法务确认；真实系统重启、用户切换、离线和权限变化需受控执行器；桌面视频继续暂缓。
- 暂缓：视频、截图、图像和媒体任务未执行。
- 客观阻塞：无新的构建、包审计或 manifest 校验阻塞；外部分发仍受许可证确认限制。
- 待确认假设：后续不再修改被打包的代码/文档；任何修改都必须重新构建并重新生成 manifest，不能沿用本批次哈希。
- 下一轮最高优先级：项目负责人/法务确认根目录许可证与云 API 展示授权；确认后再进行最终提交冻结和最后的视频录制准备。

### 批次 128：最终发布文档/manifest 路径同步复核（2026-09-08）

- 实际检查：`docs/release-freeze.md`、`docs/final-reproduction-checklist.md`、`docs/deb-release.md` 均已引用 `runs/openkylin-validation-20260908/release-manifest-final/release-manifest-release2.json`，并指向 `0.2.0+release2` 包和 `release-build-innovation-final2/` 审计目录。
- 实际检查命令：发布路径、包存在性、manifest 包哈希和三份文档引用检查，退出码 `0`；记录见 `runs/final-innovation-freeze-20260908-rerun2/release-path-check.stdout.log` 与 `release-path-check.exitcode`。
- 说明：前一目录 `runs/final-innovation-freeze-20260908/` 的记录函数误用 PowerShell 保留变量 `$args`，产生交互式 Python 提示；该目录不作为完成证据，历史文件保留未覆盖。
- 已完成：最终发布文档与 manifest 路径的一致性已由修正后的独立检查确认。
- 部分完成：项目级 LICENSE、云 API 展示授权和系统级测试执行器不属于自动化可确认范围。
- 下一轮最高优先级：使用修正后的函数重跑最终非视频回归与真实结果 strict verify，并将退出码作为唯一有效检查记录。

### 批次 129：最终非视频回归与真实创新结果严格校验重跑（2026-09-08）

- 实际命令目录：`runs/final-innovation-freeze-20260908-rerun2/`；修正参数命名后未调用云 API、未重复 `.deb` 生命周期、未执行视频/截图/图像任务。
- 全量测试：`python -m unittest discover -s tests -v` 退出码 `0`，46 项通过；stderr 无错误。
- 套件与代码：`python -m kmb.cli validate --strict` 对 `suites/core-zh.yaml`、`suites/adversarial/core.yaml`、`suites/core-en.yaml`、`suites/adversarial/core-en.yaml`、`suites/lifecycle/innovation.yaml` 均退出码 `0`；创新套件报告 `15 cases`。`python -m compileall -q kmb scripts tests` 退出码 `0`。
- 真实结果严格校验：`python scripts/verify_run.py runs/openkylin-validation-20260908/innovation-grok-wrapper --strict` 和 DeepSeek 对应目录均退出码 `0`，分别为 `15 cases/192 evidence events`。
- 发布一致性：最终 `release2` 包哈希与 `release-manifest-release2.json` 一致，文档 manifest 引用一致，检查退出码 `0`。
- 已完成：创新层代码、测试、套件、证据和发布 manifest 的最终非视频回归证据已用修正脚本重新取得；有效结果均有独立 stdout/stderr/exitcode 文件。
- 部分完成：测试在宿主 Windows 工作区执行；openKylin VM 的包构建/包审计和真实 Agent strict verify 证据仍以对应 VM 归档目录为准，不以本地测试替代系统结论。
- 未完成：项目级根目录 LICENSE 与云 API 展示授权仍待负责人/法务确认；系统级真实重启、用户切换、离线、权限变化仍需受控 openKylin 执行器；桌面视频继续暂缓。
- 暂缓：视频、截图、图像和桌面录制任务未执行。
- 客观阻塞：无新的代码、套件、证据或发布包阻塞；外部分发授权和系统级执行器仍是客观边界。
- 待确认假设：`release2` 包和其源文件在本批次后不再变更；如变更必须重新构建并更新 manifest。
- 下一轮最高优先级：项目负责人/法务确认项目级许可证和云 API 展示/留存条款；确认后再做最终提交冻结，并将视频作为最后一项工作。

### 批次 130：固定发布审计别名并完成 `release2` 最终包重建（2026-09-08）

- 实际修改：`docs/release-freeze.md` 与 `docs/deb-release.md` 将包审计引用统一为固定目录 `runs/openkylin-validation-20260908/release-build-innovation-final/`，避免文档指向前一批编号日志。
- VM 同步命令：通过 `scp -P 2222` 同步上述两份文档，退出码 `0`。
- 最终构建命令：`KMB_DEB_VERSION=0.2.0+release2 bash scripts/build_deb.sh dist/release-20260908-release2`，openKylin VM 构建退出码 `0`；实际审计日志同步归档到固定目录，`build.exitcode=0`、`audit.exitcode=0`。
- 最终包：`dist/release-20260908-release2/kylin-memory-bench_0.2.0+release2_all.deb`，SHA-256 `c7e03b755e0da3b9e159bbc550444cecedcfb3aa44115e49d3a8b11a1b3a391b`。
- 包审计：`dpkg-deb --info`、`dpkg-deb --contents`、禁止内容扫描、创新套件严格校验（15 cases）、核心套件校验（6 cases）和包内 smoke（2 tests）均为退出码 `0`，输出 `forbidden_payload=none`；固定证据目录为 `runs/openkylin-validation-20260908/release-build-innovation-final/`。
- 已完成：发布文档、最终 `release2` 包和固定审计目录路径一致；创新层已纳入包，未包含 credentials、`.env`、虚拟环境、缓存、`runs/`、`__pycache__` 或 `.pyc`。
- 部分完成：本批次仍只做包构建/内容审计，不重复第六批系统生命周期；稳定性多批统计仍主要来自 no-memory 五批。
- 未完成：最终 manifest 需写入本批次包哈希；项目级 LICENSE、云 API 展示授权、系统级执行器和桌面视频仍待确认/暂缓。
- 暂缓：视频、截图、图像和媒体任务未执行。
- 客观阻塞：无构建、包审计或权限阻塞；对外分发仍受许可证确认限制。
- 下一轮最高优先级：更新最终 manifest 的包哈希和固定审计目录，并通过最后一次 JSON/敏感字段校验。

### 批次 131：固定审计别名后的最终 manifest 校验（2026-09-08）

- 实际产物更新：`runs/openkylin-validation-20260908/release-manifest-final/release-manifest-release2.json` 的 `candidate_package.sha256` 更新为 `c7e03b755e0da3b9e159bbc550444cecedcfb3aa44115e49d3a8b11a1b3a391b`，`content_audit_path` 更新为 `runs/openkylin-validation-20260908/release-build-innovation-final/`；源文件哈希共 18 项。
- 校验命令与结果：JSON 解析、必需字段、两 Agent、包哈希、18 项源哈希、`full_keys_in_manifest=False` 和敏感模式扫描均退出码 `0`；日志 `runs/openkylin-validation-20260908/release-manifest-final/generate-release2.stdout.log`、`generate-release2.exitcode`、`validate-release2.stdout.log`、`validate-release2.exitcode`。
- 发布材料一致性：`docs/release-freeze.md`、`docs/final-reproduction-checklist.md`、`docs/deb-release.md` 均引用最终 manifest 文件，且发布包审计目录为固定别名；检查退出码 `0`。
- 已完成：最终包哈希、manifest、发布文档和审计目录形成可复核闭环；未覆盖第六批生命周期的历史证据保持不变。
- 部分完成/未完成：项目级 LICENSE 与云 API 展示/留存授权仍需负责人/法务确认；系统级重启、用户切换、离线和权限变化仍需受控 openKylin 执行器；桌面视频仍暂缓。
- 待确认假设：当前 `release2` 源文件和包不再变更；任何改动必须重新构建并更新 manifest，不能沿用本批次哈希。
- 下一轮最高优先级：负责人/法务确认许可证与云 API 条款；确认后再冻结提交材料并进入最后视频录制前检查。

### 批次 132：openKylin 系统级场景能力探针（2026-09-08）

- 实际命令：通过 SSH `ssh -p 2222 -o BatchMode=yes -o ConnectTimeout=10 -i C:\\Users\\123\\.ssh\\openkylin_vm_ed25519 <vm-user>@192.168.182.129` 执行只读能力探针，检查 `id`、`sudo -n -v`、`uname -a`、`/etc/os-release`、Python/pip/setuptools、`systemd-detect-virt`、`loginctl list-users`、`getent passwd`、`ip netns list`、`unshare --user --mount --net true`、命令可用性和 `df -h`；SSH 命令退出码 `0`。
- 环境事实：openKylin `2.0 SP2 (nile)`，内核 `6.6.0-25-generic`，`x86_64`，VMware；SSH 用户 `<vm-user>`（uid 1000），仅发现一个活动用户；根分区可用约 `8.2G`。
- 权限事实：`sudo -n -v` 失败并输出 `sudo_noninteractive=no`；不能由当前自动化通道执行 root 级 dpkg、系统重启或系统权限变更。`systemctl`、`ip`、`nsenter`、`loginctl` 命令存在；`unshare --user --mount --net true` 用户级网络 namespace 探针成功。SSH 默认目录 `<user-home>`，项目目录和 `.kmb-venv` 未在该目录中发现；凭据文件存在且权限 `600`，未读取内容。
- 未执行：本批次尚未触发系统重启、用户切换、离线阻断或权限修改；没有可恢复的外部控制通道和 root 授权证据，不能把普通用户探针当成这些场景的成功验证。
- 客观阻塞：当前 SSH 自动化用户无非交互 sudo，且 `loginctl list-users` 仅有 `<vm-user>`；系统重启跨会话证明、跨用户隔离和 root 权限变化需 VM 控制器/本地已认证终端或额外专用测试用户。
- 待确认假设：项目实际路径仍为 `<user-home>/kmb-openkylin-validation-20260906`；需在该路径内继续执行用户级探针。用户级 `unshare` 仅证明可探测隔离能力，不代表已完成离线 API 评测。
- 下一轮最高优先级：在项目路径内保存系统级场景执行器与恢复模板，完成可安全执行的 Agent 进程重启、专用目录权限变化和用户级网络 namespace 离线能力验证；对系统重启/跨用户场景保留未执行证据，随后补足创新套件双 Agent memory-enabled 多批统计。

### 批次 133：受控系统级场景执行与 Grok 创新稳定性第 1 批（2026-09-08）

- 实际修改：新增 `scripts/system_scenarios.py`、`tests/test_system_scenarios.py`，更新 `docs/openkylin-validation-runbook.md`；执行器仅使用项目 `runs/` 专用目录、合成事实和用户网络 namespace。
- 最小测试：Windows 本地 `python -m py_compile scripts/system_scenarios.py tests/test_system_scenarios.py` 退出码 `0`；`python -m unittest tests.test_system_scenarios -v` 退出码 `0`（2 项通过）。
- VM 场景命令：`.kmb-venv/bin/python scripts/system_scenarios.py --out runs/openkylin-validation-20260908/system-scenarios-20260908 --run-id system-scenarios-20260908`；CLI 内部退出码 `0`，外层 SSH 收尾因 CRLF `exit 0` 解析返回 `1`，不影响结果文件，已以 `cli.exitcode=0` 为准。
- VM 场景结果：openKylin `2.0 SP2`、Python `3.12.2`、uid `1000`；`process-restart=pass`（两个不同 PID `177060/177061` 读取同一持久事实并完成动作，工件 SHA256 `77a0acf7...4a3732`）；`offline=pass`（用户 network namespace 外连探针退出 `0` 且 `network_blocked=true`，无 API 响应伪造，工件 SHA256 `8c9a3933...8852a`）；`permissions=pass`（专用文件 chmod 000 后拒绝、恢复后读取成功）；`system-reboot=not_executed`（无认证 root/重启后控制通道）；`user-switch=not_executed`（仅一个活动用户且无授权创建/切换通道）。结果 `runs/openkylin-validation-20260908/system-scenarios-20260908/system-summary.json`、`system-summary.md`、`evidence.jsonl`、`artifacts/`，事件 `native_memory_events=0`、`model_requests=0`。
- Grok 稳定性第 1 批命令：VM 加载 `~/.config/kmb/credentials.env` 后执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260908/innovation-stability/grok-memory/repeat-01 --run-id innovation-grok-memory-01-20260908 --seed 42 --retries 1 --timeout 180`；CLI `cli.exitcode=0`，严格校验 `verify.exitcode=0`，外层 SSH 收尾 CRLF 返回 `1`，不作为 CLI 失败。
- Grok 结果：`15 cases`、`192 evidence events`、model `grok-4.6`、Overall `97.78`、`native_memory_events=0`、`wrapper_memory_events=34`、5 个变形组通过、证据链覆盖率 `1.0`；结果目录 `runs/openkylin-validation-20260908/innovation-stability/grok-memory/repeat-01/`，包含 JSON/JSONL/Markdown/HTML/SVG、CLI/verify 日志和退出码。
- 已完成：系统级可安全边界的三类实际验证和 Grok innovation memory-enabled 第 1 个独立真实批次；未执行边界有明确证据，未把包装层或 namespace 结果称为模型原生记忆。
- 部分完成/未完成：系统重启、跨用户切换仍待受控 root/VM 控制器；创新套件 Grok/DeepSeek 各至少 5 批统计尚未完成；本批未执行 DeepSeek；视频继续暂缓。
- 客观阻塞：SSH 自动化通道无非交互 sudo；仅一个活动用户；系统重启会中断 SSH 且没有外部 post-boot 控制器。
- 待确认假设：用户级 `unshare` 结果只代表进程网络 namespace 隔离；系统级重启/跨用户必须另行授权，不能用本批次替代。
- 下一轮最高优先级：继续执行 Grok innovation memory-enabled repeat-02，并在每批成功后立即归档；随后执行 DeepSeek 对比批次。

### 批次 134：Grok innovation memory-enabled 第 2 批（2026-09-08）

- 实际命令：VM 项目内加载 `~/.config/kmb/credentials.env`，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260908/innovation-stability/grok-memory/repeat-02 --run-id innovation-grok-memory-02-20260908 --seed 42 --retries 1 --timeout 180`，CLI 退出码文件 `0`；`.kmb-venv/bin/python scripts/verify_run.py ... --strict` 退出码文件 `0`。远端收尾输出包含 CRLF 路径提示，但结果文件和独立退出码已核对存在，未将收尾提示误报为评测失败。
- 结果：Grok `grok-4.6`，15 cases、192 evidence events、Overall `71.11`；结果目录 `runs/openkylin-validation-20260908/innovation-stability/grok-memory/repeat-02/`，含 `result.json`、`evidence.jsonl`、`result.md`、`result.html`、`radar.svg`、CLI/verify 日志和退出码。该批次真实完成但分数较第 1 批波动，纳入描述性统计，不宣称稳定或模型原生记忆。
- 已完成：第二个独立 Grok innovation memory-enabled 批次归档并完成严格结构校验。
- 部分完成：Grok 尚需至少 3 个可比批次，DeepSeek innovation memory-enabled 尚未开始；系统重启/跨用户仍未执行；视频继续暂缓。
- 客观阻塞：无新的 API 或权限错误；远端脚本传输产生的 CRLF 收尾提示仅影响外层命令展示，不影响 `cli.exitcode=0` 和结果内容。
- 待确认假设：本批次 `result.json` 与 `verify.exitcode=0` 为权威结果；后续统计脚本将按独立目录和 `result.json` 聚合。
- 下一轮最高优先级：以无 CRLF 的固定脚本执行 Grok innovation repeat-03，并继续逐批更新上下文包。

### 批次 135：Grok innovation memory-enabled 第 3 批（2026-09-08）

- 实际命令：VM 项目内加载 `~/.config/kmb/credentials.env`，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260908/innovation-stability/grok-memory/repeat-03 --run-id innovation-grok-memory-03-20260908 --seed 42 --retries 1 --timeout 180`；CLI 退出码 `0`，`.kmb-venv/bin/python scripts/verify_run.py ... --strict` 退出码 `0`。
- 结果：Grok `grok-4.6`，15 cases、192 events、Overall `97.78`；维度 `task_reuse/boundary/similar_distinction/retention/memory_recall=100.0`、`dynamic_update=66.67`；失败类型 `confusion=1`；5 个变形组通过，证据链覆盖率 `1.0`，`native_memory_events=0`、`wrapper_memory_events=34`。目录 `runs/openkylin-validation-20260908/innovation-stability/grok-memory/repeat-03/` 已归档完整 JSON/JSONL/Markdown/HTML/SVG 和日志。
- 已完成：Grok innovation memory-enabled 第 3 个独立真实批次。
- 部分完成：Grok 尚需至少 2 个批次；DeepSeek innovation memory-enabled 尚未运行；系统重启/跨用户仍未执行。
- 客观阻塞：无 API/权限错误；该批次实际耗时受单案例 180 秒超时策略影响，未改变正式参数。
- 待确认假设：本批次 strict verify 与结果文件均为权威证据，统计仅做描述性比较，不归因模型原生记忆。
- 下一轮最高优先级：执行 Grok innovation memory-enabled repeat-04 并归档后立即更新上下文包。

### 批次 136：Grok innovation memory-enabled 第 4 批（2026-09-09）

- 实际命令：VM 项目内加载 `~/.config/kmb/credentials.env`，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260908/innovation-stability/grok-memory/repeat-04 --run-id innovation-grok-memory-04-20260908 --seed 42 --retries 1 --timeout 180`；CLI 退出码 `0`，strict verify 退出码 `0`。
- 结果：Grok `grok-4.6`，15 cases、192 events、Overall `97.78`；结果目录 `runs/openkylin-validation-20260908/innovation-stability/grok-memory/repeat-04/`，含完整证据、报告和退出码文件；`native_memory_events=0`，仍为 wrapper-assisted 系统级行为。
- 已完成：Grok innovation memory-enabled 第 4 个独立真实批次。
- 部分完成：Grok 尚需第 5 批；DeepSeek 尚未开始；系统重启/跨用户未执行。
- 客观阻塞：无 API/权限错误，批次耗时约 6 分钟，正式超时/重试参数未改变。
- 待确认假设：统计聚合以每个 repeat 目录的 `result.json` 和 strict verify `0` 为准。
- 下一轮最高优先级：执行 Grok innovation memory-enabled repeat-05，完成 Grok 最低 5 批样本后立即聚合并更新上下文包。

### 批次 137：Grok innovation 五批聚合与 DeepSeek innovation 第 1 批（2026-09-09）

- Grok 第 5 批：VM CLI 与 strict verify 退出码均为 `0`，15 cases、192 events、Overall `97.78`，结果 `runs/openkylin-validation-20260908/innovation-stability/grok-memory/repeat-05/`。
- Grok 聚合命令：`python scripts/aggregate_repeats.py runs/openkylin-validation-20260908/innovation-stability/grok-memory --out runs/openkylin-validation-20260908/innovation-stability/grok-memory/summary.json` 退出码 `0`。5 批执行成功率 `80%`（第 2 批含 8 个 runtime error，保留为失败样本），行为案例通过率 `88%`，Overall 均值 `92.446`、样本标准差 `11.9272`、范围 `71.11-97.78`，一致性 `false`；模式含 wrapper-assisted 和 mixed，`native_memory_events=0`。原报告 `summary.md` 已更新为 wrapper-assisted 边界说明。
- 实际修改：`scripts/aggregate_repeats.py`、`scripts/aggregate_stability.py` 将统计免责声明按运行模式区分 wrapper/no-memory，保留旧 no-memory 兼容；`python -m py_compile ...` 与 `python -m unittest tests.test_scripts -v` 均退出码 `0`（10 项通过）。
- DeepSeek 第 1 批命令：VM 加载 `~/.config/kmb/credentials.env` 后执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/repeat-01 --run-id innovation-deepseek-memory-01-20260909 --seed 42 --retries 1 --timeout 180`；CLI 与 strict verify 退出码均为 `0`，模型 `deepseek-v4-flash`，15 cases、192 events、Overall `97.78`，结果目录 `runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/repeat-01/`。
- 已完成：Grok innovation 五目录真实批次归档与描述性聚合；DeepSeek innovation 第 1 个真实批次。
- 部分完成：Grok 含 1 个失败批次，尚未达到“5 个成功批次”；DeepSeek 尚需 4 批；双 Agent innovation 稳定性汇总尚未生成。
- 客观阻塞：第 2 批 Grok 的真实 runtime error 造成执行成功率下降，不能剔除或伪造成成功；无新的凭据或权限错误。
- 待确认假设：创新统计应把错误批次保留在分母，并单独报告 execution_success_rate 与 behavioral_case_pass_rate；任何结论仅是 wrapper-assisted 系统级行为。
- 下一轮最高优先级：执行 DeepSeek innovation memory-enabled repeat-02，随后继续补足 DeepSeek 与 Grok 的可比批次。

### 批次 138：DeepSeek innovation memory-enabled 第 2 批（2026-09-09）

- 实际命令：VM 项目内加载 `~/.config/kmb/credentials.env`，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/repeat-02 --run-id innovation-deepseek-memory-02-20260909 --seed 42 --retries 1 --timeout 180`；CLI 退出码 `0`，strict verify 退出码 `0`。
- 结果：DeepSeek `deepseek-v4-flash`，15 cases、192 events、Overall `97.78`；目录 `runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/repeat-02/`，含完整 JSON/JSONL/Markdown/HTML/SVG、CLI/verify 日志和退出码；`native_memory_events=0`。
- 已完成：DeepSeek innovation 第 2 个独立真实批次。
- 部分完成：DeepSeek 尚需 3 批；Grok 五批中有 1 个失败批次；双 Agent 汇总尚未生成。
- 客观阻塞：无新的 API/权限错误。
- 待确认假设：同一套件 SHA、seed、重试和超时保持不变；批次仅作 wrapper-assisted 描述性统计。
- 下一轮最高优先级：执行 DeepSeek innovation memory-enabled repeat-03。

### 批次 139：DeepSeek innovation memory-enabled 第 3 批（2026-09-09）

- 实际命令：VM 项目内加载 `~/.config/kmb/credentials.env`，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/repeat-03 --run-id innovation-deepseek-memory-03-20260909 --seed 42 --retries 1 --timeout 180`；CLI 和 strict verify 退出码均为 `0`。
- 结果：DeepSeek `deepseek-v4-flash`，15 cases、192 events、Overall `97.78`；目录 `runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/repeat-03/` 已归档 JSON/JSONL/Markdown/HTML/SVG 和日志；`native_memory_events=0`、wrapper-assisted 系统级行为。
- 已完成：DeepSeek innovation 第 3 个独立真实批次。
- 部分完成：DeepSeek 尚需 2 批；Grok 五批含 1 个真实失败批次；双 Agent 稳定性汇总待生成。
- 客观阻塞：无新的 API/权限错误。
- 待确认假设：批次参数和套件哈希与 Grok 保持一致，统计不作模型原生能力因果解释。
- 下一轮最高优先级：执行 DeepSeek innovation memory-enabled repeat-04。

### 批次 140：DeepSeek innovation memory-enabled 第 4 批（2026-09-09）

- 实际命令：VM 项目内加载 `~/.config/kmb/credentials.env`，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/repeat-04 --run-id innovation-deepseek-memory-04-20260909 --seed 42 --retries 1 --timeout 180`；CLI 与 strict verify 退出码均为 `0`。
- 结果：DeepSeek `deepseek-v4-flash`，15 cases、192 events、Overall `97.78`；目录 `runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/repeat-04/` 已归档完整结果；`native_memory_events=0`。
- 已完成：DeepSeek innovation 第 4 个独立真实批次。
- 部分完成：DeepSeek 尚需第 5 批；Grok 有 4 成功/1 失败；系统重启/跨用户仍未执行。
- 客观阻塞：无新的 API/权限错误。
- 待确认假设：严格验证成功不等于行为分数稳定；统计保留所有批次和失败事件。
- 下一轮最高优先级：执行 DeepSeek innovation memory-enabled repeat-05，完成第二个 Agent 的最低 5 批样本。

### 批次 141：DeepSeek innovation memory-enabled 第 5 批与双 Agent 统计准备（2026-09-09）

- 实际命令：VM 项目内加载 `~/.config/kmb/credentials.env`，执行 `.kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/repeat-05 --run-id innovation-deepseek-memory-05-20260909 --seed 42 --retries 1 --timeout 180`；CLI 退出码 `0`，strict verify 退出码 `0`。
- 结果：DeepSeek `deepseek-v4-flash`，15 cases、192 events、Overall `97.78`；目录 `runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/repeat-05/` 已归档完整结果；`native_memory_events=0`、wrapper-assisted 系统级行为。
- 已完成：DeepSeek innovation 5 个独立真实批次均已生成并严格校验通过；Grok 5 个目录已生成但包含 1 个真实 runtime-error 批次。
- 部分完成：统计脚本尚未生成创新双 Agent多维汇总；memory-enabled no-memory 对照批次尚未执行；系统重启/跨用户仍未执行。
- 客观阻塞：Grok 第 2 批真实运行错误造成其 5 批执行成功率为 `80%`，不能报告为 5/5 成功。
- 待确认假设：创新套件五批目录使用同一套件哈希 `c3543730...1b0a`、seed `42`、retries `1`、timeout `180`；统计将把 Grok 错误批次纳入分母。
- 下一轮最高优先级：扩展重复批次聚合以输出变形组、生命周期、安全、动作和证据链统计，生成 Grok/DeepSeek/双 Agent JSON、Markdown、HTML、SVG 报告并立即归档。

### 批次 142：系统场景 v2、创新双 Agent 聚合与归档复核（2026-09-09）

- 本批次范围：读取批次 141 后的实际产物，归档系统场景 v2、创新套件双 Agent 五批统计和传输/收尾异常说明；不重复已通过的基础生命周期，不执行视频、截图或图像任务。
- 系统场景实际结果：`runs/openkylin-validation-20260909/system-scenarios-20260909-v2/` 的 CLI 退出码为 `0`，`process-restart`、用户 network namespace `offline`、专用文件 `permissions` 三场景通过；`system-reboot` 和 `user-switch` 为 `not_executed`。摘要记录 `3` 个可评分场景、`3` 个通过、`2` 个未执行，`18` 条 `EvidenceEvent`，恢复后 `memory_recall` `3` 次；工件 SHA-256 已写入摘要并可复核。该执行器未调用模型 API，不能证明模型原生记忆能力。
- 创新套件统计实际结果：`runs/openkylin-validation-20260908/innovation-stability/dual-agent-innovation-stability.json`、`.md`、`.html`、`stability-radar.svg` 已存在并由 `scripts/aggregate_stability.py` 生成。Grok `grok-4.6` 五批执行成功率 `80%`，行为案例通过率 `88%`，Overall 均值 `92.446`、样本标准差 `11.9272`、范围 `71.11-97.78`；DeepSeek `deepseek-v4-flash` 五批执行成功率 `100%`，行为案例通过率 `93.33%`，Overall `97.78`、标准差 `0`。Grok 第 2 批保留 `8` 个真实 `runtime_error` 事件，不从分母剔除。
- 创新指标实际结果：Grok 变形组 `24/25`、生命周期状态转换 `10/10`、动作 `13/13`、证据链完整批次 `5/5`；DeepSeek 变形组 `25/25`、生命周期状态转换 `10/10`、动作 `15/15`、证据链完整批次 `5/5`。两 Agent 的 `native_memory_events=0`，统计仅描述模型后端与同一外部包装层的系统级行为。
- 实际复核命令：读取 `system-summary.json`、双 Agent JSON/Markdown/HTML、每个 Agent 的 `summary.json` 和 10 个 repeat 目录；检查每批 `cli.exitcode=0`、`verify.exitcode=0` 文件均存在；计算创新套件、系统执行器、聚合报告和证据文件的 SHA-256。复核未修改运行结果，未发现完整 API 密钥输出。
- 已完成：批次 142 所涉系统场景 v2、双 Agent 五批统计、证据目录和报告路径均已形成可追溯归档。
- 部分完成：OS 重启、跨用户切换仍未执行；创新 no-memory 对照未执行；Grok 只有 `4` 个无错误成功批次，不能宣称五批全部成功或绝对稳定。
- 未完成/暂缓：需要 root/VM 控制器的系统级场景和视频、截图、图像任务仍未完成/暂缓；旧 `release2` manifest 不覆盖本轮新增执行器、统计代码和文档修改，后续发布冻结前需重新构建包和 manifest。
- 客观阻塞：SSH 自动化用户无非交互 sudo，只有一个活动用户，无重启后外部控制通道；因此不能安全执行 OS 重启或创建/切换专用用户。
- 待确认假设：宿主工作区的 10 个创新 repeat 目录与 openKylin VM 归档一致；任何后续源文件或文档修改都必须重新构建 `.deb` 并更新 manifest。
- 下一轮最高优先级：执行独立的最终非视频验收批次，重新验证全量测试、五套件、10 个创新批次 strict verify、证据/工件哈希和报告结构，并将结果追加为批次 143。

### 批次 143：最终非视频回归与创新证据归档复核（2026-09-09）

- 本批次范围：在宿主工作区建立新的 `runs/final-nonvideo-20260909-b143/`，对当前代码、套件和已归档的 openKylin 真实运行结果做只读最终复核；未调用云 API，未重复 `.deb` 第六批生命周期，未执行视频、截图或图像任务。
- 验收机环境：宿主机 Python `3.9.5`、PyYAML `6.0.3`、pip `21.1.1`；被复核的 openKylin 环境事实来自真实归档：openKylin `2.0 SP2 (nile)`、x86_64、VM 项目 `<user-home>/kmb-openkylin-validation-20260906`、Python `3.12.2`。宿主复核不替代 VM 运行。
- 全量测试：`python -m unittest discover -s tests -v` 退出码 `0`，`48` 项通过；日志 `runs/final-nonvideo-20260909-b143/tests.stdout.log`、`tests.stderr.log`、`tests.exitcode`。
- 套件与编译：`python -m kmb.cli validate --strict --suite suites/core-zh.yaml`（6 cases）、`core-en.yaml`（6）、`adversarial/core.yaml`（12）、`adversarial/core-en.yaml`（6）、`lifecycle/innovation.yaml`（15）均退出码 `0`；`python -m compileall -q kmb scripts tests` 退出码 `0`。各命令的 stdout/stderr/exitcode 在 `runs/final-nonvideo-20260909-b143/` 对应文件中。
- CLI 兼容检查：`python -m kmb.cli --help` 和 `python -m kmb.cli list-cases --suite suites/lifecycle/innovation.yaml` 均退出码 `0`；命令与输出分别归档为 `cli-help.*`、`cli-list-cases-innovation.*`。
- 真实结果严格复核：对 Grok/DeepSeek innovation memory-enabled 的 10 个 `repeat-*` 目录逐一执行 `python scripts/verify_run.py <dir> --strict`，10 个退出码文件均为 `0`；每批仍为 15 cases，真实 Grok `grok-4.6` 五批执行成功率 `80%`（第 2 批保留 8 个 runtime error），DeepSeek `deepseek-v4-flash` 五批执行成功率 `100%`。本批次未把严格结构通过误报为行为成功。
- 系统场景证据复核：读取 `runs/openkylin-validation-20260909/system-scenarios-20260909-v2/system-summary.json` 和 `evidence.jsonl`，确认 `18` 条事件、`3` 条恢复后召回、`2` 个工件 SHA-256 均匹配；`system-artifact-check` 退出码 `0`。系统摘要仍为 `3` 个通过、`2` 个 `not_executed`，OS 重启与跨用户未执行。
- 报告结构复核：确认 Grok/DeepSeek summary、双 Agent JSON/Markdown/HTML、SVG 雷达图和 `docs/innovation-stability-report.md` 均存在、JSON 可解析、模式为 `system_level_wrapper_assisted`、两 Agent `native_memory_events=0`；`report-check` 退出码 `0`。
- 敏感扫描：首次 PowerShell 扫描命令因空管道解析错误退出码 `1`，错误已保存到 `runs/final-nonvideo-20260909-b143/secret-scan-initial-parser-error.*`；修正后的同等 `rg` 扫描退出码 `0`，`secret_scan=clean`，未发现完整 API 密钥模式。该解析失败不代表项目敏感信息泄露。
- 机器可读归档：`runs/final-nonvideo-20260909-b143/batch-summary.json` 记录所有步骤和统计；`manifest.json` 含 `99` 个本批次文件的 SHA-256，生成命令退出码 `0`。
- 已完成：本批次全量测试、五套件严格校验、10 个真实创新结果严格结构复核、系统场景工件哈希复核、报告文件/边界检查、CLI 辅助命令和敏感扫描均有独立证据；本批次没有源代码改动。
- 部分完成：Grok innovation 仍为 `4` 个无错误成功批次加 `1` 个含真实错误批次；创新 no-memory 对照尚未执行；系统重启和跨用户仍未执行；所有真实 Agent 结果仍是外部包装层下的系统级行为，不能证明模型原生长期记忆。
- 未完成/暂缓：旧 `release2` `.deb` 与 manifest 尚未覆盖本轮新增 `system_scenarios.py`、统计脚本和文档哈希；需要重新构建/审计并生成新 manifest。视频、截图、图像任务继续暂缓。
- 客观阻塞：openKylin SSH 自动化用户无非交互 sudo，只有一个活动用户，无系统重启后外部控制通道；OS 重启和跨用户场景无法安全执行。
- 待确认假设：宿主复核所用的 10 个 repeat 目录与 VM 归档未被外部修改；后续任何源文件、文档或包内容变化都必须重新计算哈希并重新构建 manifest。
- 下一轮最高优先级：在不重复第六批生命周期的前提下，使用当前源码重新构建 openKylin `.deb`，完成包内容/敏感/套件 smoke 审计并生成覆盖新增文件的最终 release manifest。

### 批次 144：当前源码的 release3 技术包构建与中间审计（2026-09-09）

- 本批次范围：同步批次 143 后的当前源码到 openKylin VM，先构建 `0.2.0+release3` 作为 release4 前的中间候选；未执行系统安装/升级/卸载，不调用云 API。
- 实际同步：`scp -P 2222 -r kmb configs suites docs scripts pyproject.toml setup.py README.md CHANGELOG.md NOTICE THIRD_PARTY_NOTICES.md LICENSE-MIT-CANDIDATE.txt <vm-user>@192.168.182.129:<user-home>/kmb-openkylin-validation-20260906/` 退出码 `0`，日志 `runs/openkylin-validation-20260909/release3-sync/`。
- 实际构建：VM 执行 `KMB_DEB_VERSION=0.2.0+release3 bash scripts/build_deb.sh dist/release-20260909-release3`，远端 `build.exitcode=0`，日志 `runs/openkylin-validation-20260909/release3-build/vm-build.stdout.log`、`vm-build.stderr.log`、`vm-build.exitcode`；包大小 `81576` bytes，SHA-256 `8385d1d...1ba07a1e`，本地副本为 `dist/kylin-memory-bench_0.2.0+release3_all.deb`。
- 中间审计：对 release3 包执行 `dpkg-deb --info/--contents`、禁止内容扫描、核心/创新套件校验、解包入口和包内 smoke，审计退出码均为 `0`；因随后发现打包脚本尚未纳入 `system_scenarios.py`，该包仅作为中间证据保留，审计日志目录暂记为 `runs/openkylin-validation-20260909/release4-audit/`，不作为最终冻结包。
- 已完成：release3 技术构建可复现，凭据/缓存/运行产物未进入 staging。
- 部分完成：中间包未覆盖新增执行器，且文档哈希表随后更新；不能用 release3 作为最终发布冻结证明。
- 客观阻塞：无构建或用户态审计阻塞；root 级生命周期不在本批次范围。
- 下一轮最高优先级：修正打包脚本纳入系统场景执行器，更新发布文档后重建 release4 并生成新 manifest。

### 批次 145：release4 最终技术包、VM 审计与发布 manifest（2026-09-09）

- 实际修改：`scripts/build_deb.sh` 增加 `system_scenarios.py` payload 安装项；`docs/release-freeze.md`、`docs/final-reproduction-checklist.md`、`docs/deb-release.md`、`docs/innovation-stability-report.md` 统一指向 release4、批次 143 和新的 manifest，并保留 release2/release3 历史事实。修改前后的中间包已保留，未删除既有成果。
- 实际同步：上述当前源码通过 `scp -P 2222 -r ...` 同步到 VM，退出码 `0`，日志 `runs/openkylin-validation-20260909/release4-final-sync/`。
- 最终构建：VM 执行 `KMB_DEB_VERSION=0.2.0+release4 bash scripts/build_deb.sh dist/release-20260909-release4`，退出码 `0`；VM 环境日志 `runs/openkylin-validation-20260909/release4-build/vm-environment.stdout.log` 确认内核 `6.6.0-25-generic`、Python `3.12.2`、pip `26.2.1`、PyYAML `6.0.1`。最终构建日志和退出码见 `runs/openkylin-validation-20260909/release4-final-build/`。
- 最终包：`dist/release-20260909-release4/kylin-memory-bench_0.2.0+release4_all.deb`，大小 `85364` bytes，SHA-256 `b2eed9acf47323fbe9a8d86a39e87ec6f5dcadcd69af5d0138eabcc8dad89dd8`；本地 root `dist/kylin-memory-bench_0.2.0+release4_all.deb` 与该副本一致。
- VM 包审计：`dpkg-deb --info` 显示版本 `0.2.0+release4`、架构 `all`、依赖 `python3 (>=3.9), python3-yaml`；`dpkg-deb --contents` 确认 `system_scenarios.py`、`aggregate_repeats.py`、`aggregate_stability.py` 在 payload。禁止内容扫描为 `forbidden_payload=none`；创新套件 `15 cases`、核心套件 `6 cases` 校验、解包入口和包内 smoke `2 tests` 均退出码 `0`。逐步日志和退出码见 `runs/openkylin-validation-20260909/release4-final-audit/vm/`，远端/本地复制退出码为 `0`。
- 发布 manifest：`runs/openkylin-validation-20260909/release-manifest-release4/release-manifest-release4.json`，包含 `40` 个源文件 SHA-256、release4 包哈希、openKylin 环境、Grok `grok-4.6`、DeepSeek `deepseek-v4-flash`、统一参数、权威创新/系统场景/最终非视频目录和能力边界。生成退出码 `0`，JSON/字段/40 项源哈希/包哈希/双 Agent/`full_keys_in_manifest=false`/敏感字段校验退出码 `0`；日志为该目录的 `generate.*`、`validate.*`。
- 已完成：当前源码的 release4 包构建、payload/敏感/套件/smoke 审计、manifest 生成与校验均有 VM 或宿主证据；发布包不含 API Key、credentials、缓存、`runs/`、`__pycache__` 或 `.pyc`。
- 部分完成：本批次不替代第六批 root/KARE 系统生命周期；项目级 LICENSE、云 API 展示/留存授权仍待负责人/法务确认；OS 重启、跨用户和 innovation no-memory 对照仍未执行；真实 Agent 仍为 wrapper-assisted 系统级行为，`native_memory_events=0`。
- 暂缓：桌面视频、截图、图像和媒体任务继续暂缓。
- 客观阻塞：无新的构建、包审计或 manifest 阻塞；外部分发受项目许可证确认限制。
- 待确认假设：release4 源码/文档在 manifest 生成后不再变化；任何变更都必须重新构建并更新 manifest。
- 下一轮最高优先级：负责人/法务确认项目级 LICENSE 与云 API 展示/留存条款；确认后再冻结提交材料并进入最后视频录制前检查。

### 批次 146：release4 变更后的本地最终非视频回归（2026-09-09）

- 实际命令：在 `runs/final-nonvideo-20260909-b143-post-release4/` 重新执行 `python -m unittest discover -s tests -v`、`python -m compileall -q kmb scripts tests`、`bash -n scripts/build_deb.sh`、`python -m kmb.cli validate --strict --suite suites/lifecycle/innovation.yaml` 和 manifest JSON 解析；五条命令退出码均为 `0`。
- 实际结果：全量测试 `48` 项通过；编译和 shell 语法检查通过；创新套件 `15 cases` 严格校验通过；manifest JSON 可解析。每条命令均保存 stdout/stderr/exitcode，未调用云 API，未重复第六批生命周期。
- 已完成：release4 打包脚本变更后的代码、套件、manifest 和最小非视频回归无新增失败。
- 未完成/暂缓：项目级许可证、OS 重启/跨用户、innovation no-memory 对照和视频仍按批次 145 的边界处理。
- 下一轮最高优先级：项目负责人/法务确认项目级 LICENSE 与云 API 条款，然后再进行最终提交冻结和最后视频录制前检查。

### 批次 147：release4 文档状态修正后的最终 VM 包重建与审计（2026-09-09）

- 本批次原因：`docs/release-freeze.md` 状态文字从“待审计”修正为“已通过 VM 包审计”，为避免包内文档与包内容不一致，重新同步该文档并重建同版本 release4；不执行系统安装/升级/卸载、不调用云 API。
- 实际同步：`scp -P 2222 -i ... docs/release-freeze.md <vm-user>@192.168.182.129:<user-home>/kmb-openkylin-validation-20260906/docs/` 退出码 `0`，证据 `runs/openkylin-validation-20260909/release4-final2-sync/`。
- 实际构建：VM 执行 `KMB_DEB_VERSION=0.2.0+release4 bash scripts/build_deb.sh dist/release-20260909-release4`，远端 `build.exitcode=0`；最终包复制退出码 `0`，日志 `runs/openkylin-validation-20260909/release4-final2-build/`。
- VM 包审计：`dpkg-deb --info`、`dpkg-deb --contents`、禁止内容扫描、核心/创新套件严格校验、解包入口和包内 smoke 均退出码 `0`；`forbidden_payload=none`，`system_scenarios.py`、`aggregate_repeats.py`、`aggregate_stability.py` 均在 payload。审计证据 `runs/openkylin-validation-20260909/release4-final2-audit/vm/`。
- 最终包哈希：`dist/release-20260909-release4/kylin-memory-bench_0.2.0+release4_all.deb`，大小 `85364` bytes，SHA-256 `fc91cb76a18751ed88a50f5db96cd0edf86be21287437b73848031ced470050c`。此前 `605c...` 包作为中间产物保留，不再作为最终候选。
- 已完成：release4 文档状态修正后的 VM 构建、包内容/敏感/套件/smoke 审计均通过。
- 部分完成：本批次不替代第六批 root/KARE 生命周期；项目级许可证、OS 重启/跨用户、innovation no-memory 对照和视频仍未完成/暂缓。
- 客观阻塞：无新的构建或包审计阻塞；系统级场景仍受 SSH 无非交互 sudo、单活动用户和无重启后控制通道限制。
- 待确认假设：最终包内容与当前源码/文档一致，后续如有修改需重新构建并更新 manifest。
- 下一轮最高优先级：刷新 release4 manifest 包哈希/审计路径和源文件哈希，并执行最终 JSON/敏感字段校验。

### 批次 148：release4 最终 manifest 刷新与哈希校验（2026-09-09）

- 实际产物：刷新 `runs/openkylin-validation-20260909/release-manifest-release4/release-manifest-release4.json`，纳入 `40` 个当前源文件 SHA-256、最终 release4 包哈希 `fc91cb76a18751ed88a50f5db96cd0edf86be21287437b73848031ced470050c`、`release4-final2-audit` 审计路径、openKylin 环境和双 Agent 模型信息。旧 manifest 副本 `release-manifest-release4-pre-final.json` 保留为历史中间记录。
- 生成命令：PowerShell manifest refresh，退出码 `0`；日志 `runs/openkylin-validation-20260909/release-manifest-release4/refresh.stdout.log`、`refresh.exitcode`。
- 校验命令：JSON 解析、必需字段、双 Agent、40 项源哈希、包哈希和敏感模式扫描，退出码 `0`；日志 `final-validate.stdout.log`、`final-validate.exitcode`。manifest `full_keys_in_manifest=false`。
- 已完成：当前 release4 包与 manifest 哈希、源文件指纹和安全门禁一致。
- 部分完成/未完成：项目级 LICENSE、OS 重启/跨用户、innovation no-memory 对照和视频仍未完成或暂缓；发布包不等价于 root 生命周期新验证。
- 下一轮最高优先级：执行 release4 文档/manifest 路径一致性检查并将最终候选状态写入上下文包。

### 批次 149：release4 文档与 manifest 路径一致性复核（2026-09-09）

- 实际命令：检查 `docs/release-freeze.md`、`docs/final-reproduction-checklist.md`、`docs/deb-release.md`、`docs/innovation-stability-report.md` 均引用 release4/manifest-release4；读取 manifest 确认版本 `0.2.0+release4` 和包路径一致。命令退出码 `0`，证据 `runs/openkylin-validation-20260909/release4-doc-check/check.stdout.log`、`check.exitcode`。
- 已完成：release4 技术候选、manifest、四份发布/稳定性文档路径一致；中间 release2/release3 记录仍保留但不再作为当前候选。
- 未完成/暂缓：项目级许可证与云 API 展示/留存授权待负责人/法务确认；OS 重启/跨用户及 innovation no-memory 对照未执行；视频、截图、图像和桌面录制继续暂缓。
- 待确认假设：文档与 manifest 在本批次后不再变更；任何变更必须重新构建包、审计并刷新 manifest。
- 下一轮最高优先级：负责人/法务确认项目级 LICENSE 与云 API 条款，然后冻结提交材料并进入最后视频录制前检查。

### 批次 150：release4 包双路径哈希一致性收尾（2026-09-09）

- 实际操作：将最终 release4 包从 `dist/release-20260909-release4/kylin-memory-bench_0.2.0+release4_all.deb` 复制到根 `dist/kylin-memory-bench_0.2.0+release4_all.deb` 作为同哈希本地别名；未修改包内容、源码或评测逻辑。
- 实际命令与结果：PowerShell `Copy-Item` 后分别计算两条路径 SHA-256，检查退出码 `0`；两者均为 `fc91cb76a18751ed88a50f5db96cd0edf86be21287437b73848031ced470050c`，文件大小均为 `85388` bytes。证据 `runs/openkylin-validation-20260909/release4-path-check/check.stdout.log`、`check.exitcode`。
- 当前发布候选：manifest 继续以 `runs/openkylin-validation-20260909/release-manifest-release4/release-manifest-release4.json` 为权威，包路径为 `dist/release-20260909-release4/kylin-memory-bench_0.2.0+release4_all.deb`；根 `dist/` 路径仅为同哈希别名，不作为第二个版本。
- 已完成：release4 包路径、manifest 包哈希和本地别名一致；之前 release2/release3 包及 manifest 保留为历史中间产物。
- 部分完成/未完成：项目级 LICENSE 与云 API 展示/留存授权仍待负责人/法务确认；OS 重启、跨用户和 innovation no-memory 对照未执行；真实 Agent 均无原生记忆事件，结论仅限模型后端+外部包装层系统级行为。
- 暂缓：桌面视频、截图、图像和媒体任务仍未执行。
- 客观阻塞：系统级 OS 重启/跨用户需要认证 root、专用用户和重启后控制通道；当前 SSH 自动化条件不满足。
- 待确认假设：后续不再修改 release4 源码、文档或包；任何变更都必须重新构建、审计并刷新 manifest。
- 下一轮最高优先级：项目负责人/法务完成项目级 LICENSE 和云 API 条款确认；确认后冻结赛事提交材料，再进行最后视频录制前检查。

### 批次 151：release4 final3 路径同步与发布 manifest 刷新（2026-09-09）

- 本批次范围：读取批次 150 后的最新工作区和 release4 manifest，将 final3 VM 构建/审计证据与当前最终包路径对齐；未调用 Grok/DeepSeek API，未重复 `.deb` 第六批安装/升级/卸载生命周期，未执行视频、截图或图像任务。
- 实际产物：`dist/release-20260909-release4/kylin-memory-bench_0.2.0+release4_all.deb` 与根路径别名 `dist/kylin-memory-bench_0.2.0+release4_all.deb` 均存在，大小均为 `85384` bytes；两条路径 SHA-256 均为 `3c282ac5ddd923de3349561e685275d51d709182b6933193bf54532caac81940`。路径同步证据保留在 `runs/openkylin-validation-20260909/release4-final3-path-sync/`。
- manifest 刷新：更新 `runs/openkylin-validation-20260909/release-manifest-release4/release-manifest-release4.json` 的候选包哈希、`release4-final3-build`/`release4-final3-audit` 路径和权威运行目录，并重新计算全部 `40` 个源文件 SHA-256。刷新命令退出码 `0`；日志 `runs/openkylin-validation-20260909/release-manifest-release4/refresh-final3.command.txt`、`refresh-final3.stdout.log`、`refresh-final3.stderr.log`、`refresh-final3.exitcode`。
- manifest 校验：执行 JSON 解析、必需字段、版本、候选包及根路径别名 SHA-256、40 个源哈希、证据路径存在性、权威运行目录存在性、`full_keys_in_manifest=false` 和敏感模式扫描；退出码 `0`，`errors=0`、`sensitive_scan=clean`。证据 `runs/openkylin-validation-20260909/release-manifest-release4/validate-final3.command.txt`、`validate-final3.stdout.log`、`validate-final3.stderr.log`、`validate-final3.exitcode`。
- VM 证据引用：`runs/openkylin-validation-20260909/release4-final3-build/vm-build.exitcode` 为 `0`；`runs/openkylin-validation-20260909/release4-final3-audit/vm/audit.exitcode` 为 `0`；禁止内容检查 `forbidden_payload=none` 且退出码为 `0`。final3 审计目录已包含核心/创新套件校验、包内 smoke 和打包入口检查结果。
- 已完成：当前 release4 包、final3 VM 构建/审计路径、manifest 候选包哈希、40 个源文件指纹和安全门禁已一致并有独立日志支撑；历史 release2/release3/final2 manifest 与运行记录未删除。
- 部分完成/未完成：项目级 LICENSE 与云 API 展示/留存授权仍待项目负责人/法务确认；OS 重启、跨用户切换和 innovation no-memory 对照仍未执行；真实 Agent 结果仍为模型后端加外部包装层的系统级行为，`native_memory_events=0`，不能表述为模型原生长期记忆；视频、截图和图像任务继续暂缓。
- 客观阻塞：无新的 manifest、包哈希或路径校验阻塞；系统级 OS 重启/跨用户仍需要认证 root、专用测试用户和重启后控制通道，当前 SSH 条件不足。
- 待确认假设：final3 包生成后源码、文档和包内容不再变化；任何后续修改都必须重新构建 `.deb`、重新执行包审计并刷新 manifest。根 `dist/` 包仅为同哈希本地别名，不是第二个发布版本。
- 下一轮最高优先级：完成项目负责人/法务对项目级 LICENSE 与云 API 条款的确认；确认后冻结赛事提交材料，并在所有非视频事项保持不变的前提下进入最后视频录制前检查。

### 批次 152：innovation no-memory 远端预检（2026-09-09）

- 本批次范围：为补齐当前未执行的 innovation no-memory 对照，在 openKylin VM 通过 SSH 仅检查项目路径、凭据文件存在性/权限、no-memory 配置、innovation 套件和运行时版本；未输出或读取凭据内容，未调用模型 API。
- 实际命令：`ssh -o BatchMode=yes -i ~/.ssh/openkylin_vm_ed25519 -p 2222 <vm-user>@192.168.182.129 "cd <user-home>/kmb-openkylin-validation-20260906 && ..."`；退出码 `0`。脱敏输出为 `vm_project=<user-home>/kmb-openkylin-validation-20260906`、`credentials_present=true`、`configs_and_suite_present=true`、`pyyaml=6.0.1`、`python=3.12.2`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory-preflight/command.txt`、`stdout.log`、`stderr.log`、`exitcode`；退出码文件为 `0`。
- 已完成：确认可在真实 openKylin VM 中使用已有安全凭据配置执行 innovation no-memory 对照，且项目、配置和套件均可用。
- 部分完成：尚未执行 Grok/DeepSeek no-memory innovation 批次、聚合统计和报告；本预检不构成模型调用或行为结果证据。
- 客观阻塞：预检无阻塞；后续运行仍受云 API 限流、超时或余额等实际服务状态影响，任何失败批次需保留原始错误。
- 待确认假设：远端凭据文件的值与此前已验证的对应模型端点一致；运行命令不读取凭据值到日志，仅由适配器加载环境变量。
- 下一轮最高优先级：执行 Grok innovation no-memory repeat-01，归档完整结果并严格校验后继续后续批次。

### 批次 153：Grok innovation no-memory repeat-01（2026-09-09）

- 本批次范围：在真实 openKylin VM 使用 `configs/agent-grok-no-memory.yaml` 运行 `suites/lifecycle/innovation.yaml`；统一参数 seed `42`、retries `1`、timeout `180s`；外部记忆/行动控制器关闭。未输出凭据内容。
- 实际命令：`set -a && . ~/.config/kmb/credentials.env && set +a && .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-no-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/repeat-01 --run-id innovation-grok-no-memory-01-20260909 --seed 42 --retries 1 --timeout 180`；远端 shell/CLI 退出码文件为 `2`，说明整批存在案例级运行错误。
- 实际结果：15 cases；`result.json` Overall `16.67`；strict `python scripts/verify_run.py ... --strict` 退出码 `0`，确认结构完整；100 条 `EvidenceEvent`。所有 15 个案例均记录真实 `RuntimeError: agent API connection failed: [Errno 111] Connection refused`，未伪造模型响应；`native_memory_events=0`、`memory_disabled_events=17`、模式为 `mixed`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/repeat-01/`，包含 `result.json`、`evidence.jsonl`、`result.md`、`result.html`、`radar.svg`、CLI/verify 日志和退出码；远端复制第二次命令退出码 `0`，`copy2.stdout.log`/`copy2.stderr.log`/`copy2.exitcode` 已保存。
- 已完成：Grok no-memory innovation 第 1 个独立真实批次已执行、原始错误已保留、结构严格校验通过；该批次可作为失败样本纳入后续统计。
- 部分完成：Grok no-memory 尚未达到 5 个批次；当前服务端点从 VM 返回连接拒绝，不能继续把未执行批次写成成功。
- 客观阻塞：`https://api.wapq.cn/v1` 对该 VM 的本次调用实际返回 `[Errno 111] Connection refused`；需服务恢复或网络路径恢复后才能补齐 Grok no-memory 样本。
- 待确认假设：Grok API 服务短时不可达而非凭据失效；该假设不影响本批次失败事实，但影响后续是否可补跑。
- 下一轮最高优先级：执行 DeepSeek innovation no-memory repeat-01；完成后按实际状态决定是否继续其余批次，并保留 Grok 阻塞证据。

### 批次 154：DeepSeek innovation no-memory repeat-01（2026-09-09）

- 本批次范围：在真实 openKylin VM 使用 `configs/agent-deepseek-no-memory.yaml` 运行 `suites/lifecycle/innovation.yaml`；统一参数 seed `42`、retries `1`、timeout `180s`；外部记忆/行动控制器关闭。未输出凭据内容。
- 实际命令：`set -a && . ~/.config/kmb/credentials.env && set +a && .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-no-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/repeat-01 --run-id innovation-deepseek-no-memory-01-20260909 --seed 42 --retries 1 --timeout 180`；远端 shell/CLI 退出码文件为 `0`。
- 实际结果：15 cases；`result.json` Overall `23.33`；strict `python scripts/verify_run.py ... --strict` 退出码 `0`，确认结构完整；184 条 `EvidenceEvent`。失败类型包括 `omission=7`、`stale_update=4`、`invalid_behavior=3`、`erroneous_reuse=3`、`action_failure=5`、`incomplete_evidence=1`、`expired_reuse=1`、`scope_violation=2`、`confusion=1`；`native_memory_events=0`、`memory_disabled_events=36`、模式为 `no_memory_baseline`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/repeat-01/`，包含 `result.json`、`evidence.jsonl`、`result.md`、`result.html`、`radar.svg`、CLI/verify 日志、复制日志和退出码；复制退出码 `0`。
- 已完成：DeepSeek no-memory innovation 第 1 个独立真实批次已执行、原始响应/事件/失败理由已保留、结构严格校验通过；该批次可纳入 no-memory 对照统计。
- 部分完成：DeepSeek no-memory 尚未达到 5 个批次；Grok no-memory 仍只有 1 个连接拒绝批次。
- 客观阻塞：本批次无新增阻塞；Grok 端点连接拒绝仍是独立外部服务阻塞。
- 待确认假设：no-memory 配置确实关闭外部记忆控制器，`memory_disabled_events` 由适配器记录且不等价于模型原生记忆状态。
- 下一轮最高优先级：执行 DeepSeek innovation no-memory repeat-02 并归档严格校验结果。

### 批次 155：DeepSeek innovation no-memory repeat-02（2026-09-09）

- 本批次范围：在真实 openKylin VM 使用 `configs/agent-deepseek-no-memory.yaml` 运行同一 `suites/lifecycle/innovation.yaml`；seed `42`、retries `1`、timeout `180s` 保持不变；外部记忆/行动控制器关闭。
- 实际命令：`set -a && . ~/.config/kmb/credentials.env && set +a && .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-no-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/repeat-02 --run-id innovation-deepseek-no-memory-02-20260909 --seed 42 --retries 1 --timeout 180`；远端 CLI 退出码文件 `0`。
- 实际结果：15 cases；Overall `20.0`；184 条 `EvidenceEvent`；strict verify 退出码 `0`。失败类型：`omission=8`、`stale_update=4`、`invalid_behavior=3`、`erroneous_reuse=3`、`action_failure=5`、`incomplete_evidence=1`、`expired_reuse=1`、`scope_violation=2`、`confusion=1`；`native_memory_events=0`、`memory_disabled_events=36`、模式 `no_memory_baseline`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/repeat-02/`，含结果、证据 JSONL、报告、雷达图、CLI/verify/复制日志和退出码；复制退出码 `0`。
- 已完成：DeepSeek no-memory 第二个独立真实批次和严格结构校验。
- 部分完成：DeepSeek no-memory 尚有 3 个批次未执行；Grok no-memory 仍受连接拒绝阻塞。
- 客观阻塞：无新增阻塞；Grok 端点服务不可达仍需外部恢复。
- 待确认假设：相同 seed 与配置下模型服务返回差异属于真实 API 行为波动，不由本地评分器改写。
- 下一轮最高优先级：执行 DeepSeek innovation no-memory repeat-03 并归档结果。

### 批次 156：DeepSeek innovation no-memory repeat-03（2026-09-09）

- 本批次范围：在真实 openKylin VM 使用 `configs/agent-deepseek-no-memory.yaml` 运行同一 innovation 套件；seed `42`、retries `1`、timeout `180s` 保持不变；外部记忆/行动控制器关闭。
- 实际命令：`set -a && . ~/.config/kmb/credentials.env && set +a && .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-no-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/repeat-03 --run-id innovation-deepseek-no-memory-03-20260909 --seed 42 --retries 1 --timeout 180`；远端 CLI 退出码文件 `0`。
- 实际结果：15 cases；Overall `23.33`；184 条 `EvidenceEvent`；strict verify 退出码 `0`。失败类型：`omission=7`、`stale_update=4`、`invalid_behavior=3`、`erroneous_reuse=3`、`action_failure=5`、`incomplete_evidence=1`、`expired_reuse=1`、`scope_violation=2`、`confusion=1`；`native_memory_events=0`、`memory_disabled_events=36`、模式 `no_memory_baseline`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/repeat-03/`，含结果、证据 JSONL、报告、雷达图、CLI/verify/复制日志和退出码；复制退出码 `0`。
- 已完成：DeepSeek no-memory 第 3 个独立真实批次和严格结构校验。
- 部分完成：DeepSeek no-memory 尚有 2 个批次未执行；Grok no-memory 仍只有连接拒绝批次。
- 客观阻塞：无新增阻塞；Grok 端点服务不可达仍需外部恢复。
- 待确认假设：重复批次的相同分数和失败分类来自实际 API/适配器结果，不代表模型原生记忆状态。
- 下一轮最高优先级：执行 DeepSeek innovation no-memory repeat-04 并归档结果。

### 批次 157：DeepSeek innovation no-memory repeat-04（2026-09-09）

- 本批次范围：在真实 openKylin VM 使用 `configs/agent-deepseek-no-memory.yaml` 运行同一 innovation 套件；seed `42`、retries `1`、timeout `180s` 保持不变；外部记忆/行动控制器关闭。
- 实际命令：`set -a && . ~/.config/kmb/credentials.env && set +a && .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-no-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/repeat-04 --run-id innovation-deepseek-no-memory-04-20260909 --seed 42 --retries 1 --timeout 180`；远端 CLI 退出码文件 `0`。
- 实际结果：15 cases；Overall `23.33`；184 条 `EvidenceEvent`；strict verify 退出码 `0`。失败类型：`omission=7`、`stale_update=4`、`invalid_behavior=3`、`erroneous_reuse=3`、`action_failure=5`、`incomplete_evidence=1`、`expired_reuse=1`、`scope_violation=2`、`confusion=1`；`native_memory_events=0`、`memory_disabled_events=36`、模式 `no_memory_baseline`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/repeat-04/`，含结果、证据 JSONL、报告、雷达图、CLI/verify/复制日志和退出码；复制退出码 `0`。
- 已完成：DeepSeek no-memory 第 4 个独立真实批次和严格结构校验。
- 部分完成：DeepSeek no-memory 只剩 1 个批次；Grok no-memory 仍只有连接拒绝批次。
- 客观阻塞：无新增阻塞；Grok 端点服务不可达仍需外部恢复。
- 待确认假设：相同失败分类的重复结果应视为当前 API/包装器状态下的观测，不推断模型内部状态。
- 下一轮最高优先级：执行 DeepSeek innovation no-memory repeat-05 并完成该 Agent 的最低五批统计。

### 批次 158：DeepSeek innovation no-memory repeat-05（2026-09-09）

- 本批次范围：在真实 openKylin VM 使用 `configs/agent-deepseek-no-memory.yaml` 完成 innovation 套件第 5 个 no-memory 重复批次；seed `42`、retries `1`、timeout `180s` 保持不变；外部记忆/行动控制器关闭。
- 实际命令：`set -a && . ~/.config/kmb/credentials.env && set +a && .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-deepseek-no-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/repeat-05 --run-id innovation-deepseek-no-memory-05-20260909 --seed 42 --retries 1 --timeout 180`；远端 CLI 退出码文件 `0`。
- 实际结果：15 cases；Overall `23.33`；184 条 `EvidenceEvent`；strict verify 退出码 `0`。失败类型：`omission=7`、`stale_update=4`、`invalid_behavior=3`、`erroneous_reuse=3`、`action_failure=5`、`incomplete_evidence=1`、`expired_reuse=1`、`scope_violation=2`、`confusion=1`；`native_memory_events=0`、`memory_disabled_events=36`、模式 `no_memory_baseline`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/repeat-05/`，含结果、证据 JSONL、报告、雷达图、CLI/verify/复制日志和退出码；复制退出码 `0`。
- 已完成：DeepSeek no-memory innovation 已达到 5 个独立真实批次，均有可追溯结果和严格结构校验。
- 部分完成：DeepSeek 五批聚合报告尚未生成；Grok no-memory innovation 仍只有 1 个连接拒绝批次，无法形成匹配的五批对照。
- 客观阻塞：无新增阻塞；Grok `https://api.wapq.cn/v1` 的连接拒绝仍未恢复。
- 待确认假设：DeepSeek 五批重复结果可用于描述性稳定性统计，但不能外推到模型原生长期记忆能力。
- 下一轮最高优先级：聚合 DeepSeek innovation no-memory 五批结果并归档 JSON/Markdown，随后再探测 Grok 端点是否恢复。

### 批次 159：DeepSeek innovation no-memory 五批聚合（2026-09-09）

- 本批次范围：读取已归档的 DeepSeek innovation no-memory `repeat-01` 至 `repeat-05`，不修改原始证据；执行确定性重复统计。
- 实际命令：`python scripts/aggregate_repeats.py runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory --out runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/summary.json`；退出码 `0`。
- 实际结果：5 批；执行成功率 `100%`；行为案例通过率 `20%`；Overall 均值 `22.664`、样本标准差 `1.4892`、最小 `20.0`、最大 `23.33`；`overall_all_equal=false`；模式 `no_memory_baseline`，`native_memory_events=0`。每批均通过 `verify_run.py --strict`，聚合未剔除失败案例。
- 证据与产物：`runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/summary.json`、`summary.md`、`aggregate.stdout.log`、`aggregate.stderr.log`、`aggregate.exitcode`；原始五批目录保留不变。
- 已完成：DeepSeek innovation no-memory 五批描述性稳定性统计和失败分类汇总。
- 部分完成：尚无匹配的 Grok 五批样本；不能生成对称的双 Agent no-memory 稳定性结论。
- 客观阻塞：Grok `https://api.wapq.cn/v1` 从 VM 返回连接拒绝，补跑需端点恢复。
- 待确认假设：聚合脚本读取的五批目录均来自同一 openKylin VM、同一 suite/seed/timeout/retries；该假设由各批命令记录支持但不替代服务端审计。
- 下一轮最高优先级：聚合 Grok 已完成的单个失败批次并探测端点恢复状态，随后生成明确标注样本不对称的 no-memory 双 Agent报告。

### 批次 160：Grok innovation no-memory 单批聚合（2026-09-09）

- 本批次范围：读取 Grok innovation no-memory `repeat-01` 的真实失败结果，执行聚合统计；未重跑 API，未修改原始证据。
- 实际命令：`python scripts/aggregate_repeats.py runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory --out runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/summary.json`；退出码 `0`。
- 实际结果：1 批；执行成功率 `0%`；行为案例通过率 `13.33%`；Overall 均值/标准差/范围 `16.67/0/16.67-16.67`；模式 `mixed`，`native_memory_events=0`。该批次 15 个案例均有真实 API 连接拒绝错误，结构 strict verify 仍为 `0`。
- 证据与产物：`runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/summary.json`、`summary.md`、`aggregate.stdout.log`、`aggregate.stderr.log`、`aggregate.exitcode`；原始 `repeat-01` 目录保留不变。
- 已完成：Grok 已执行失败批次的统计归档，失败样本不被删除或隐藏。
- 部分完成：Grok no-memory 尚未达到 5 个独立批次；当前结果不能代表 Grok 稳定性，也不能与 DeepSeek 五批直接比较。
- 客观阻塞：Grok API 端点在 VM 的实际连接拒绝仍未解除。
- 待确认假设：连接拒绝发生在网络/服务路径而不是配置文件内容；本批次不据此作根因定论。
- 下一轮最高优先级：执行 Grok 端点最小状态探测并生成 no-memory 双 Agent描述性对比，明确样本量不对称和未完成补跑条件。

### 批次 161：Grok/DeepSeek no-memory 端点恢复探测（2026-09-09）

- 本批次范围：在 openKylin VM 重新执行不含凭据值的 `/models` 健康探测；保留此前两次远端 shell 引用失败记录，不修改既有运行结果。
- 实际命令：加载 `~/.config/kmb/credentials.env` 后，分别执行 `curl -sS --max-time 15 -H "Authorization: Bearer $GROK_API_KEY" https://api.wapq.cn/v1/models` 与 `curl -sS --max-time 15 -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/models`；探测脚本通过 base64 传输到 VM，SSH 和复制退出码均为 `0`。
- 实际结果：Grok HTTP `200`，`time_total=0.451434s`；返回模型 ID 包含 `grok-4.5`、`grok-4.6`。DeepSeek HTTP `200`，`time_total=0.202901s`；返回模型 ID 包含 `deepseek-v4-flash`、`deepseek-v4-pro`。探测整体退出码 `0`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory-health/`，包含 `probe3.command.txt`、`probe3.script.b64`、`grok-probe3.summary.log`、`deepseek-probe3.summary.log`、响应体、curl stderr/exitcode、SSH/复制退出码和旧失败探测日志。响应体仅为模型列表，未包含凭据值。
- 已完成：确认当前 VM 到 Grok/DeepSeek API 端点均恢复可达，模型 ID 可验证；Grok 前次连接拒绝属于此前时间点的真实失败，不被删除。
- 部分完成：Grok no-memory innovation 仍只有 1 个失败批次；双 Agent no-memory 对照尚未对称完成。
- 客观阻塞：无当前健康探测阻塞；后续批次仍可能受服务波动影响。
- 待确认假设：`grok-4.6` 与 `deepseek-v4-flash` 仍是项目锁定模型，模型列表可达不等价于完整套件调用必然成功。
- 下一轮最高优先级：在端点恢复后执行 Grok innovation no-memory repeat-02，归档并严格校验。

### 批次 162：Grok innovation no-memory repeat-02（2026-09-09）

- 本批次范围：在真实 openKylin VM 使用 `configs/agent-grok-no-memory.yaml` 运行 innovation 套件第二个 no-memory 批次；seed `42`、retries `1`、timeout `180s` 保持不变，外部记忆/行动控制器关闭。
- 实际命令：`set -a && . ~/.config/kmb/credentials.env && set +a && .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-no-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/repeat-02 --run-id innovation-grok-no-memory-02-20260909 --seed 42 --retries 1 --timeout 180`；远端 CLI 退出码文件 `0`。
- 实际结果：15 cases；Overall `23.33`；183 条 `EvidenceEvent`；strict verify 退出码 `0`。失败类型：`omission=7`、`stale_update=4`、`invalid_behavior=3`、`erroneous_reuse=3`、`action_failure=5`、`incomplete_evidence=1`、`expired_reuse=1`、`scope_violation=2`、`confusion=1`；`native_memory_events=0`、`memory_disabled_events=36`、模式 `no_memory_baseline`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/repeat-02/`，含结果、证据 JSONL、报告、雷达图、CLI/verify/复制日志和退出码；复制退出码 `0`。
- 已完成：Grok no-memory 第二个独立真实批次，端点恢复后产生完整模型请求/响应和失败分类，结构严格校验通过。
- 部分完成：Grok no-memory 尚有 3 个批次未执行；此前 repeat-01 的连接拒绝失败样本继续保留。
- 客观阻塞：本批次无新增阻塞；服务可能再次波动。
- 待确认假设：repeat-02 的响应来自锁定的 `grok-4.6` 端点，配置与 DeepSeek 对照的套件/参数一致。
- 下一轮最高优先级：执行 Grok innovation no-memory repeat-03 并归档结果。

### 批次 163：Grok innovation no-memory repeat-03（2026-09-09）

- 本批次范围：在真实 openKylin VM 使用 `configs/agent-grok-no-memory.yaml` 运行 innovation 套件第三个 no-memory 批次；seed `42`、retries `1`、timeout `180s` 保持不变，外部记忆/行动控制器关闭。
- 实际命令：`set -a && . ~/.config/kmb/credentials.env && set +a && .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-no-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/repeat-03 --run-id innovation-grok-no-memory-03-20260909 --seed 42 --retries 1 --timeout 180`；远端 CLI 退出码文件 `0`。
- 实际结果：15 cases；Overall `25.56`；186 条 `EvidenceEvent`；strict verify 退出码 `0`。失败类型含 `timeout=2`、`omission=7`、`stale_update=4`、`invalid_behavior=3`、`erroneous_reuse=3`、`action_failure=5`、`incomplete_evidence=1`、`expired_reuse=1`、`scope_violation=2`；`native_memory_events=0`、`memory_disabled_events=36`、模式 `no_memory_baseline`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/repeat-03/`，含结果、证据 JSONL、报告、雷达图、CLI/verify/复制日志和退出码；复制退出码 `0`。
- 已完成：Grok no-memory 第 3 个独立真实批次，端点可达但出现真实超时；错误样本和响应事件均保留，结构严格校验通过。
- 部分完成：Grok no-memory 尚有 2 个批次未执行；前一连接拒绝批次和当前超时批次均需纳入统计。
- 客观阻塞：服务端存在请求超时波动；不能将当前批次写成全案例成功。
- 待确认假设：超时由 API/网络服务波动引起，非本地评分器故意制造；该假设不改变实际 `timeout=2` 证据。
- 下一轮最高优先级：执行 Grok innovation no-memory repeat-04 并归档结果。

### 批次 164：Grok innovation no-memory repeat-04（2026-09-09）

- 本批次范围：在真实 openKylin VM 使用 `configs/agent-grok-no-memory.yaml` 运行 innovation 套件第四个 no-memory 批次；seed `42`、retries `1`、timeout `180s` 保持不变，外部记忆/行动控制器关闭。
- 实际命令：`set -a && . ~/.config/kmb/credentials.env && set +a && .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-no-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/repeat-04 --run-id innovation-grok-no-memory-04-20260909 --seed 42 --retries 1 --timeout 180`；远端 CLI 退出码文件 `0`。
- 实际结果：15 cases；Overall `23.33`；184 条 `EvidenceEvent`；strict verify 退出码 `0`。失败类型：`omission=7`、`stale_update=4`、`invalid_behavior=3`、`erroneous_reuse=3`、`action_failure=5`、`incomplete_evidence=1`、`expired_reuse=1`、`scope_violation=2`、`confusion=1`；`native_memory_events=0`、`memory_disabled_events=36`、模式 `no_memory_baseline`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/repeat-04/`，含结果、证据 JSONL、报告、雷达图、CLI/verify/复制日志和退出码；复制退出码 `0`。
- 已完成：Grok no-memory 第 4 个独立真实批次和严格结构校验。
- 部分完成：Grok no-memory 尚剩 1 个批次；repeat-01 连接拒绝和 repeat-03 超时均需保留在最终统计。
- 客观阻塞：无新增阻塞；服务端仍存在偶发超时风险。
- 待确认假设：repeat-04 与 DeepSeek no-memory 批次使用同一套件哈希和评分器版本；命令记录支持该假设。
- 下一轮最高优先级：执行 Grok innovation no-memory repeat-05 并完成 Grok 五批聚合。

### 批次 165：Grok innovation no-memory repeat-05（2026-09-09）

- 本批次范围：在真实 openKylin VM 使用 `configs/agent-grok-no-memory.yaml` 完成 innovation 套件第 5 个 no-memory 重复批次；seed `42`、retries `1`、timeout `180s` 保持不变，外部记忆/行动控制器关闭。
- 实际命令：`set -a && . ~/.config/kmb/credentials.env && set +a && .kmb-venv/bin/python -m kmb.cli run --agent configs/agent-grok-no-memory.yaml --suite suites/lifecycle/innovation.yaml --out runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/repeat-05 --run-id innovation-grok-no-memory-05-20260909 --seed 42 --retries 1 --timeout 180`；远端 CLI 退出码文件 `0`。
- 实际结果：15 cases；Overall `23.33`；184 条 `EvidenceEvent`；strict verify 退出码 `0`。失败类型：`omission=7`、`stale_update=4`、`invalid_behavior=3`、`erroneous_reuse=3`、`action_failure=5`、`incomplete_evidence=1`、`expired_reuse=1`、`scope_violation=2`、`confusion=1`；`native_memory_events=0`、`memory_disabled_events=36`、模式 `no_memory_baseline`。
- 证据路径：`runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/repeat-05/`，含结果、证据 JSONL、报告、雷达图、CLI/verify/复制日志和退出码；复制退出码 `0`。
- 已完成：Grok no-memory innovation 已达到 5 个独立真实批次，均有可追溯结果和严格结构校验；此前 repeat-01 的连接拒绝作为失败样本保留。
- 部分完成：两 Agent no-memory 五批聚合与最终对照报告尚未生成；Grok 五批中包含 1 个执行失败批次，不能宣称五批全部执行成功或绝对稳定。
- 客观阻塞：本批次无新增阻塞；Grok 端点已恢复，但服务波动仍需在统计中如实体现。
- 待确认假设：repeat-05 与 DeepSeek no-memory 批次使用相同套件哈希、评分器、seed、timeout 和 retries；命令与配置文件支持该假设。
- 下一轮最高优先级：聚合 Grok 五批 no-memory 结果，并生成 Grok/DeepSeek innovation no-memory 双 Agent描述性对照。

### 批次 166：no-memory 对照报告套件字段修复与定向测试（2026-09-09）

- 本批次范围：修复 `scripts/aggregate_stability.py` 在 non-wrapper 结果中错误默认 `suites/core-zh.yaml` 的字段问题；从汇总的 `runs_root`/显式 suite 推断 lifecycle/innovation 套件，并让 `same_case_suite` 根据实际套件一致性计算。未调用模型 API。
- 实际修改：`scripts/aggregate_stability.py` 增加 `_suite_for_summary` 与实际套件判定；`tests/test_scripts.py` 增加 innovation no-memory 套件字段断言。修改未删除或覆盖运行证据。
- 实际命令：`python -m unittest tests.test_scripts -v`；10 项定向测试全部通过，退出码 `0`。日志 `runs/final-nonvideo-20260909-b166-stability-suite-fix/tests-scripts.stdout.log`、`tests-scripts.stderr.log`、`tests-scripts.exitcode`。
- 已完成：报告聚合器对 innovation no-memory 的套件字段修复及回归测试。
- 部分完成：修复后的源码尚未重新生成双 Agent no-memory 报告，release4 包和 manifest 尚未因源文件变化而刷新。
- 客观阻塞：无测试阻塞；后续需重新构建 release4 以保持包内脚本与源码一致。
- 待确认假设：现有 summary 的 `runs_root` 路径可信，可作为缺少显式 suite 字段时的兼容推断依据。
- 下一轮最高优先级：使用修复后的聚合器重新生成 Grok/DeepSeek no-memory 双 Agent报告并校验 suite 字段。

### 批次 167：innovation no-memory 双 Agent五批报告重生成（2026-09-09）

- 本批次范围：使用修复后的 `scripts/aggregate_stability.py` 重新读取 Grok/DeepSeek innovation no-memory 五批 summary，未修改任何原始运行证据。
- 实际命令：分别执行 `python scripts/aggregate_repeats.py runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory --out .../grok-no-memory/summary.json`、同等 DeepSeek 命令，以及 `python scripts/aggregate_stability.py --grok-summary ... --deepseek-summary ... --out runs/openkylin-validation-20260909/innovation-no-memory/dual-agent-innovation-no-memory.json`；三条命令退出码均为 `0`。
- 实际结果：双 Agent 报告 `suite=suites/lifecycle/innovation.yaml`、`same_case_suite=true`、`mode=system_level_no_memory_baseline`。Grok 5 批执行成功率 `60%`、Overall 均值 `22.444`；DeepSeek 5 批执行成功率 `100%`、Overall 均值 `22.664`；均值差异 `Grok-DeepSeek=-0.22`。Grok 失败/超时批次保留在分母，未被排除；两 Agent `native_memory_events=0`。
- 证据与产物：`runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/summary.json`、`summary.md`、`aggregate-fix.*`；`deepseek-no-memory/summary.json`、`summary.md`、`aggregate-fix.*`；`dual-agent-innovation-no-memory.json`、`.md`、`.html`、`stability-radar.svg`、`dual-aggregate-fix.*`。
- 已完成：创新 no-memory 对照已具备两 Agent 各 5 批目录、五批聚合、JSON/Markdown/HTML/SVG 报告，套件字段与实际运行路径一致。
- 部分完成：Grok 5 批仅 3 批无执行错误，整体执行成功率 `60%`；该对照是描述性基线，不能证明模型原生长期记忆。
- 客观阻塞：无聚合或报告生成阻塞；Grok 端点服务波动造成的失败已作为真实样本记录。
- 待确认假设：两 Agent 五批运行均使用相同 suite 哈希、评分器、seed、retries 和 timeout；每批命令记录支持该假设。
- 下一轮最高优先级：执行全量非视频回归、所有 no-memory/innovation 结果 strict verify、结果字段和敏感信息扫描，并在源码变更后重新构建 release4 包。

### 批次 168：no-memory 对照回归与发布文档路径修正（2026-09-09）

- 本批次范围：对 no-memory 报告字段修复后的源码和新五批结果执行非视频回归；同时修正当前 `docs/release-freeze.md` 中仍指向 final2 的构建/审计路径。未调用模型 API，未重复 `.deb` 第六批安装/升级/卸载生命周期，未执行视频、截图或图像任务。
- 实际修改：`docs/release-freeze.md` 当前发布候选证据路径由 `release4-final2-build/audit` 更新为 `release4-final3-build/audit`；历史上下文和中间证据未删除。
- 实际命令与结果：`python -m unittest discover -s tests -v` 退出码 `0`，48 项通过；`python -m compileall -q kmb scripts tests` 退出码 `0`；五套件 `python -m kmb.cli validate --strict --suite ...` 均退出码 `0`；Grok/DeepSeek innovation memory-enabled 与 no-memory 共 20 个 `repeat-*` 目录逐一 `python scripts/verify_run.py ... --strict`，20 个退出码均为 `0`；no-memory 双 Agent报告结构校验退出码 `0`（suite=innovation、same_case_suite=true、两 Agent各5批、native_memory_events均为0）；敏感扫描退出码 `0`，`match_count=0`。
- 证据目录：`runs/final-nonvideo-20260909-b168-post-no-memory/`，含测试、编译、五套件校验、20 批 verify、报告结构和 secret-scan 日志/退出码。
- 已完成：no-memory 对照结果、报告套件字段、全量非视频回归和敏感门禁均通过；当前发布冻结文档路径与 final3 manifest 证据一致。
- 部分完成：`scripts/aggregate_stability.py` 与 `docs/release-freeze.md` 源文件已变化，现有 release4 包和 manifest 的源哈希尚未覆盖本次变化；需重新构建包并刷新 manifest。
- 客观阻塞：无回归或文档路径修正阻塞；重新构建仍需 openKylin VM SSH 通道。
- 待确认假设：五套件和 20 个运行目录在本批次复核期间未被外部修改；包重建前必须重新同步当前源码。
- 下一轮最高优先级：同步当前源码到 openKylin VM，构建并审计新的 release4 技术包（纳入聚合器修复和 final3 路径），然后刷新发布 manifest。

### 批次 169：release5 VM 技术包构建与内容审计（2026-09-09）

- 本批次范围：同步批次 168 后的当前源码到同一 openKylin VM，构建新版本 `0.2.0+release5` 以纳入 no-memory 报告套件字段修复和 final3 文档路径修正；未执行系统安装/升级/卸载，不调用模型 API，不执行视频、截图或图像任务。
- 实际同步：`scp -q -r -o BatchMode=yes -i ~/.ssh/openkylin_vm_ed25519 -P 2222 kmb configs suites docs scripts pyproject.toml setup.py README.md CHANGELOG.md NOTICE THIRD_PARTY_NOTICES.md LICENSE-MIT-CANDIDATE.txt packaging <vm-user>@192.168.182.129:<user-home>/kmb-openkylin-validation-20260906/`；退出码 `0`，证据 `runs/openkylin-validation-20260909/release5-sync/`。
- 实际构建：VM 执行 `KMB_DEB_VERSION=0.2.0+release5 bash scripts/build_deb.sh dist/release-20260909-release5`；构建退出码 `0`，包为 `dist/release-20260909-release5/kylin-memory-bench_0.2.0+release5_all.deb`，大小 `85524` bytes。构建证据 `runs/openkylin-validation-20260909/release5-build/`；首次复制因本地目标目录不存在退出码 `1`，创建目标目录后的复制重试退出码 `0`，两次记录均保留。
- 实际 VM 审计：`dpkg-deb --info`、`dpkg-deb --contents`、禁止内容扫描、innovation `15 cases` 严格校验、core `6 cases` 严格校验、解包入口和包内 smoke 均退出码 `0`；`forbidden_payload=none`。审计证据 `runs/openkylin-validation-20260909/release5-audit/`，总审计退出码 `0`。
- 当前包哈希：本地复制包 SHA-256 为 `e8a555c01dee5721b8665c61e45ec5820dbafe33643151b47a75b6506f4e4fc9`；完整哈希将在 manifest 刷新批次再次独立校验。
- 已完成：当前源码在 openKylin VM 的 release5 技术包构建、payload/敏感/套件/smoke 审计；包内包含修复后的 `scripts/aggregate_stability.py` 和当前文档。
- 部分完成：release5 manifest 尚未生成；该包未替代既有第六批 `.deb` 生命周期验证，也未执行新的 root 安装/升级/卸载。
- 客观阻塞：无构建或包审计阻塞；许可证确认、OS 重启/跨用户、视频仍按既有边界处理。
- 待确认假设：release5 包内容和当前源码在 manifest 生成前不再变化；后续变更必须重新构建和审计。
- 下一轮最高优先级：生成并校验 release5 发布 manifest，纳入当前源文件、包哈希、final3 审计和 no-memory 五批权威运行证据。

### 批次 170：release5 发布 manifest 生成与安全校验（2026-09-09）

- 本批次范围：基于 release4 manifest 模板生成独立 `release-manifest-release5.json`，纳入 release5 包、VM 构建/审计、批次 168 非视频回归、创新 no-memory 双 Agent五批证据和当前源文件哈希；未调用模型 API，未执行安装/升级/卸载、视频或媒体任务。
- 实际产物：`runs/openkylin-validation-20260909/release-manifest-release5/release-manifest-release5.json`；候选包 `dist/release-20260909-release5/kylin-memory-bench_0.2.0+release5_all.deb`，大小 `85524` bytes，SHA-256 `e8a555c01dee5721b8665c61e45ec5820dbafe33643151b47a75b6506f4e4fc9`；manifest 新增 no-memory 结果引用并将最终非视频检查指向 `runs/final-nonvideo-20260909-b168-post-no-memory/`。
- 实际命令：manifest 生成重试退出码 `0`；首次生成因目标文件尚不存在而 `Resolve-Path` 失败退出码 `1`，错误记录 `runs/openkylin-validation-20260909/release-manifest-release5/generate-attempt1.error.log`、`generate-attempt1.exitcode` 保留。生成日志为 `generate-attempt2.command.txt`、`generate-attempt2.stdout.log`、`generate-attempt2.stderr.log`、`generate-attempt2.exitcode`。
- manifest 校验：JSON/schema/版本、所有证据路径、候选包 SHA-256、40 个源文件 SHA-256、no-memory 三份结果引用、`full_keys_in_manifest=false` 和敏感模式扫描均通过；退出码 `0`，`errors=0`、`sensitive_scan=clean`。日志 `runs/openkylin-validation-20260909/release-manifest-release5/validate.command.txt`、`validate.stdout.log`、`validate.stderr.log`、`validate.exitcode`。
- 已完成：release5 manifest 与当前包、源码指纹、VM 构建/审计和 no-memory 五批权威运行证据一致；release4 manifest 和历史中间产物未覆盖或删除。
- 部分完成/未完成：项目级 LICENSE 与云 API 展示/留存授权仍待负责人/法务；OS 重启、跨用户切换仍未执行；真实模型轨道 `native_memory_events=0`，no-memory 与 wrapper 结果均只支持系统级/基线描述；视频继续暂缓。
- 客观阻塞：无 manifest 或敏感校验阻塞；Grok no-memory 五批中仍有真实连接拒绝/超时失败，执行成功率 `60%`，需在报告中保留。
- 待确认假设：release5 包生成后源码、文档和运行结果不再变化；任何后续修改必须重新构建并刷新 release5 manifest。项目许可证候选不视为最终授权。
- 下一轮最高优先级：在负责人/法务确认项目级 LICENSE 和云 API 条款后，冻结赛事提交材料并执行最后一次非视频提交前检查，再进入最终视频录制。

### 批次 171：release5 状态文档统一（2026-09-09）

- 本批次范围：依据批次 170 和当前工作区实际产物，修正当前发布/稳定性文档仍引用 release4 或“innovation no-memory 尚未执行”的过期文字；保留 release4 作为历史记录，不修改任何原始运行证据，不执行视频、截图或图像任务。
- 实际修改：`docs/innovation-stability-report.md` 增加 Grok/DeepSeek innovation no-memory 各 5 批统计、双 Agent 汇总路径和真实连接拒绝/超时限制；`docs/release-freeze.md` 更新 release5 包、manifest、审计路径、no-memory 状态和套件/聚合器哈希；`docs/deb-release.md` 增加 release5 技术候选说明；`docs/final-reproduction-checklist.md` 更新 release5 包、no-memory 证据和非视频复核路径；`README.md` 增加 release5 manifest 和 innovation no-memory 证据引用。未修改项目级许可证决定，未写入任何凭据。
- 实际检查命令：`rg -n -i "release4|release5|no-memory|innovation no-memory 对照尚未执行|没有执行 innovation no-memory" docs/innovation-stability-report.md docs/release-freeze.md docs/deb-release.md docs/final-reproduction-checklist.md README.md`；退出码 `0`。检查确认当前文档不再把 innovation no-memory 标为未执行；历史 release4 文字仅保留在 `docs/deb-release.md` 的历史候选段落。
- 环境信息：Windows 主机工作区；本批次未调用 openKylin VM、未调用 Grok/DeepSeek API。权威 openKylin 环境仍为 2.0 SP2 (nile)、x86_64、Python 3.12.2、PyYAML 6.0.1。
- 已完成：当前文档的 release/no-memory 状态统一；历史路径和边界说明保留；包装层结果仍明确为系统级行为，`native_memory_events=0`。
- 部分完成：文档修改尚未进入新的 `.deb`；release5 manifest 的源文件哈希需要随文档变化重新生成，后续候选版本拟为 release6。
- 未完成/暂缓：项目级 LICENSE 和云 API 展示/留存授权待负责人/法务确认；OS 重启和跨用户场景仍未执行；桌面视频、截图、图像和媒体任务继续暂缓。
- 客观阻塞：无文档修改阻塞；release6 构建需要现有 openKylin VM SSH 通道。
- 待确认假设：release5 包审计证据可作为 release6 构建基线，且当前源码同步路径仍可用；任何后续源码或文档变更都必须重新构建、审计并刷新 manifest。
- 下一轮最高优先级：同步当前文档到 openKylin VM，构建并审计 `0.2.0+release6`，然后生成和校验 release6 manifest。

### 批次 172：release6 openKylin SSH 通道探针（2026-09-09）

- 本批次范围：在不调用模型 API、不读取凭据内容、不执行生命周期或媒体任务的前提下，确认 release6 构建所需的现有 openKylin VM SSH 通道。
- 实际命令：`ssh -o BatchMode=yes -o ConnectTimeout=10 -i C:\\Users\\123\\.ssh\\openkylin_vm_ed25519 -p 2222 <vm-user>@192.168.182.129 "printf openkylin_ssh_ok"`；退出码 `0`，输出 `openkylin_ssh_ok`。
- 证据路径：`runs/openkylin-validation-20260909/release6-ssh-probe/command.txt`、`stdout.log`、`stderr.log`、`exitcode`。
- 环境信息：目标通道为既有 openKylin 2.0 SP2 (nile) VM，x86_64；本批次仅执行 SSH 可达性探针。
- 已完成：确认可继续同步源码并在目标 VM 构建 release6。
- 部分完成/未完成：尚未同步源码、构建或审计 release6；许可证确认、OS 重启/跨用户和视频仍未完成或暂缓。
- 客观阻塞：无 SSH 通道阻塞。
- 待确认假设：VM 中项目路径和 `.kmb-venv` 与批次 169-170 相同；下一批同步命令将显式检查路径并记录错误。
- 下一轮最高优先级：同步当前源码和文档到 VM，构建 `0.2.0+release6` 并保存构建证据。

### 批次 173：release6 源码与文档同步（2026-09-09）

- 本批次范围：将批次 171 修订后的源码、套件、脚本、文档和打包配置同步到既有 openKylin VM 项目目录；未同步 `runs/`、虚拟环境或凭据文件，未调用模型 API，未执行安装/卸载或媒体任务。
- 实际命令：`scp -q -o BatchMode=yes -o ConnectTimeout=10 -i C:\\Users\\123\\.ssh\\openkylin_vm_ed25519 -P 2222 -r kmb configs suites docs scripts pyproject.toml setup.py README.md CHANGELOG.md NOTICE THIRD_PARTY_NOTICES.md LICENSE-MIT-CANDIDATE.txt packaging <vm-user>@192.168.182.129:<user-home>/kmb-openkylin-validation-20260906/`；退出码 `0`。
- 证据路径：`runs/openkylin-validation-20260909/release6-sync/command.txt`、`stdout.log`、`stderr.log`、`exitcode`。
- 环境信息：目标为 openKylin 2.0 SP2 (nile)、x86_64 VM；同步目标 `<user-home>/kmb-openkylin-validation-20260906/`。
- 已完成：当前文档状态、聚合器修复和发布配置已同步到 VM，可开始 release6 构建。
- 部分完成/未完成：release6 尚未构建或审计；项目级 LICENSE、云 API 条款、OS 重启/跨用户和视频仍未完成或暂缓。
- 客观阻塞：无同步阻塞。
- 待确认假设：远端工作区无未提交且需保留的用户改动；同步范围未覆盖远端 `runs/` 和凭据，因此不影响其历史证据。
- 下一轮最高优先级：在 VM 使用 `KMB_DEB_VERSION=0.2.0+release6` 构建包并保存完整构建日志。

### 批次 174：release6 openKylin VM 构建（2026-09-09）

- 本批次范围：在目标 openKylin VM 使用同步后的当前源码构建 `0.2.0+release6`；未执行系统安装/升级/卸载、模型 API 调用或媒体任务。
- 实际命令：`cd <user-home>/kmb-openkylin-validation-20260906 && KMB_DEB_VERSION=0.2.0+release6 bash scripts/build_deb.sh dist/release-20260909-release6`；SSH 远程命令退出码 `0`。
- 实际产物：VM 构建输出 `dist/release-20260909-release6/kylin-memory-bench_0.2.0+release6_all.deb`，构建 stdout/stderr 和退出码归档在 `runs/openkylin-validation-20260909/release6-build/command.txt`、`stdout.log`、`stderr.log`、`exitcode`；构建清单包含当前 release5 后修订的 README、稳定性报告、release freeze、复现清单和 deb 文档。
- 环境信息：openKylin 2.0 SP2 (nile)、x86_64、Python 3.12.2、PyYAML 6.0.1；构建通过 VM SSH 通道完成。
- 已完成：release6 `.deb` 构建成功，构建脚本输出完整包清单且未报告禁止内容。
- 部分完成/未完成：尚未将 release6 包复制回本地、执行独立内容/敏感/套件审计或生成 manifest；许可证确认、OS 重启/跨用户和视频仍未完成或暂缓。
- 客观阻塞：无构建阻塞。
- 待确认假设：构建脚本的 staging 清理已移除 `runs/`、凭据和字节码；下一批将用独立 `dpkg-deb` 和敏感扫描验证，不以构建输出单独作结论。
- 下一轮最高优先级：复制 release6 包并在 VM 执行 `dpkg-deb` 内容、禁止内容、套件校验和包内 smoke 审计。

### 批次 175：release6 包复制与 VM 内容审计（2026-09-09）

- 本批次范围：将 VM 构建的 release6 包复制到本地，并在目标 openKylin VM 对包执行元数据、完整清单、禁止内容、五套件严格校验、解包入口和包内 smoke 审计；不执行安装/升级/卸载、模型 API 调用或媒体任务。
- 实际命令：`scp -q -o BatchMode=yes -o ConnectTimeout=10 -i C:\\Users\\123\\.ssh\\openkylin_vm_ed25519 -P 2222 <vm-user>@192.168.182.129:<user-home>/kmb-openkylin-validation-20260906/dist/release-20260909-release6/kylin-memory-bench_0.2.0+release6_all.deb dist/release-20260909-release6/kylin-memory-bench_0.2.0+release6_all.deb`；复制退出码 `0`，本地包 SHA-256 `6a50e18388fe09ff61cc8e8bb619a6ff383adb6733d6abf85b8f1a7ea5f7eb92`。
- VM 审计命令：在 `<user-home>/kmb-openkylin-validation-20260906` 执行 `dpkg-deb --info`、`dpkg-deb --contents`、禁止内容 grep、五个 `python -m kmb.cli validate --strict`、`dpkg-deb -x`、包内入口检查和 `tests/smoke_test.py`；SSH 退出码 `0`，各步骤退出码均为 `0`，`forbidden_payload=none`。
- 证据路径：`runs/openkylin-validation-20260909/release6-audit/`，包含审计脚本、各步骤 stdout/stderr/exitcode、解包目录和复制日志；构建日志见 `runs/openkylin-validation-20260909/release6-build/`。
- 环境信息：openKylin 2.0 SP2 (nile)、x86_64、Python 3.12.2、PyYAML 6.0.1；目标包版本 `0.2.0+release6`。
- 已完成：release6 包复制、内容/敏感/套件/入口/smoke 审计全部通过；包未包含凭据、运行结果、虚拟环境或字节码。
- 部分完成/未完成：release6 manifest 尚未生成；未以 release6 重复第六批生命周期；项目级 LICENSE、云 API 条款、OS 重启/跨用户和视频仍未完成或暂缓。
- 客观阻塞：无包审计阻塞。
- 待确认假设：release6 包的可安装性沿用已通过的第六批生命周期，但本批次仅完成内容级审计，未把它写成新的安装/卸载证据。
- 下一轮最高优先级：基于 release6 包、审计和当前源文件生成并严格校验 release6 发布 manifest。

### 批次 176：release6 本地非视频复核（2026-09-09）

- 本批次范围：在当前工作区对 release6 候选执行非视频回归，包括单元测试、编译、五套件严格校验、CLI `help/list-cases/run/compare`、20 个 innovation repeat 严格证据校验、报告 JSON 结构和候选包路径/哈希检查；未调用模型 API、未重复 `.deb` 第六批生命周期、未执行视频/截图/图像任务。
- 实际通过项：`python -m unittest discover -s tests -v`、`python -m compileall -q kmb scripts tests`、五套件 `python -m kmb.cli validate --strict`、CLI 运行/对比、20 个 repeat 的 `scripts/verify_run.py --strict` 和候选包 SHA-256 均退出码 `0`；参考运行输出 `overall=70.44`，对比输出 agents=`reference,flawed`，仅为离线机制检查，不作为真实 Agent 结果。
- 复核脚本问题：首次 b176 复核中报告结构和文档路径命令的 `$LASTEXITCODE` 被 PowerShell 输出赋值覆盖，日志显示内容有效但记录为空；敏感扫描的复杂正则解析失败（`rg_exit=2`），因此 b176 `batch-summary.json` 的 `failed_steps=3` 只表示复核脚本记录缺陷，不表示项目检查失败。原始日志保留在 `runs/final-nonvideo-20260909-b176-release6/`，未覆盖。
- 已完成：所有实际执行并正确捕获的代码、套件、CLI、证据校验步骤通过；未将 b176 的脚本错误写成项目成功。
- 部分完成：报告结构、文档路径和敏感信息门禁需在独立批次以修正命令重新执行；release6 manifest 尚未生成。
- 客观阻塞：无项目功能阻塞；需要修正 PowerShell 命令的退出码捕获和敏感扫描表达式。
- 待确认假设：b176 的失败项仅由复核脚本实现造成，待 b177 输出实际退出码后确认；release6 包与当前文档状态仍需在 manifest 前统一。
- 下一轮最高优先级：执行 b177 修正后的报告结构、文档路径和敏感信息检查，并保存真实退出码。

### 批次 177：release6 非视频门禁修正检查（2026-09-09）

- 本批次范围：针对 b176 的复核脚本记录缺陷，独立执行报告 JSON 结构、关键文档/产物路径和敏感信息扫描；不调用模型 API、不修改源码或运行证据、不执行 `.deb` 生命周期、视频或媒体任务。
- 实际检查与退出码：`python -c "import json; ..."` 读取 memory-enabled 与 no-memory 双 Agent报告，退出码 `0`，输出 `reports=2 valid`；`python -c "...missing=[]..."` 检查 release6 构建/审计、no-memory 报告和包路径，退出码 `0`，输出 `missing=[]`；PowerShell `Select-String` 对 `kmb/configs/suites/docs/packaging` 扫描 key-prefix/Bearer 模式，退出码 `0`，输出 `secret_scan=clean`、`match_count=0`。
- 证据路径：`runs/final-nonvideo-20260909-b177-release6/report-structure.*`、`docs-paths.*`、`secret-scan.*`、`release6-package.sha256`。三项退出码文件内容均为 `0`。
- 批次记录问题：用于生成 `batch-summary.json` 的 PowerShell 条件表达式写法错误，导致该文件暂时为 `null`；这不影响三个检查命令已保存的独立退出码和日志。原始错误未覆盖，后续以 b178 只读修复汇总。
- 已完成：报告结构、文档/产物路径和敏感信息门禁均实际通过；没有发现完整 API 密钥模式。
- 部分完成：b177 汇总 JSON 需修复；release6 manifest 尚未生成。
- 客观阻塞：无项目检查阻塞；仅有批次汇总脚本书写错误。
- 待确认假设：b177 的三项退出码文件是本批次命令真实返回值；b178 将重新读取文件并生成可解析汇总，不重新解释检查结果。
- 下一轮最高优先级：生成 b178 正确的非视频复核汇总，并开始 release6 manifest 生成。

### 批次 178：release6 非视频复核汇总修复尝试（2026-09-09）

- 本批次范围：只读读取 b177 三项检查的退出码和日志，生成可解析的非视频复核汇总；未重新执行检查、未调用模型 API、未修改源码/运行证据、未执行生命周期或媒体任务。
- 实际操作：读取 `runs/final-nonvideo-20260909-b177-release6/{report-structure,docs-paths,secret-scan}.exitcode`，三项文件实际内容均为 `0`；报告和路径日志分别为 `reports=2 valid`、`missing=[]`，敏感扫描为 `secret_scan=clean`、`match_count=0`。
- 批次记录问题：汇总脚本对空 stderr 文件直接调用 `.Trim()`，触发两个空值错误；`runs/final-nonvideo-20260909-b178-release6/batch-summary.json` 仅收录一项检查且为不完整对象，不能作为最终验收依据。原始错误和 `exitcode` 已保留。
- 已完成：b177 三项独立检查的实际退出码仍可核验为 `0`，未发现敏感信息模式。
- 部分完成：需在 b179 以空日志安全处理方式生成完整汇总。
- 客观阻塞：无项目功能阻塞；仅有汇总脚本的空日志处理错误。
- 待确认假设：b177 的独立检查结果不受 b178 汇总构造错误影响；b179 将验证三个检查对象均被收录且状态为 pass。
- 下一轮最高优先级：生成 b179 完整非视频复核汇总，并在此基础上继续 release6 manifest。

### 批次 179：release6 非视频复核汇总完成（2026-09-09）

- 本批次范围：以 null-safe 方式读取 b177 已落盘的报告结构、文档/产物路径和敏感扫描退出码，生成完整非视频复核汇总；未重新执行模型调用、未修改源码/运行证据、未执行 `.deb` 生命周期、视频或媒体任务。
- 实际命令：`Read b177 zero exitcode files with null-safe log handling; generate complete batch-summary.json`；命令退出码 `0`，汇总 `checks=3`、`failed_checks=0`、`status=pass`。
- 实际结果：`report-structure` 源退出码 `0`（`reports=2 valid`）；`docs-paths` 源退出码 `0`（`missing=[]`）；`secret-scan` 源退出码 `0`（`secret_scan=clean`, `match_count=0`）。候选 release6 包 SHA-256 为 `6a50e18388fe09ff61cc8e8bb619a6ff383adb6733d6abf85b8f1a7ea5f7eb92`。
- 证据路径：`runs/final-nonvideo-20260909-b179-release6/batch-summary.json`、`command.txt`、`exitcode`；原始检查日志仍在 `runs/final-nonvideo-20260909-b177-release6/`，b178 不完整汇总保留为历史错误记录。
- 已完成：release6 非视频门禁中此前记录缺陷已被独立、可解析的 b179 汇总修复，三个检查均有真实退出码支撑。
- 部分完成/未完成：发布文档当前仍写 release5，而 release6 包已构建；需将文档候选状态推进到 release6 后再构建最终一致包并生成 manifest。许可证、OS 重启/跨用户和视频仍未完成或暂缓。
- 客观阻塞：无复核阻塞。
- 待确认假设：将文档状态改为 release6 后需要新包版本以保持包内文档与候选一致，拟使用 `0.2.0+release7`，保留 release6 作为中间构建证据。
- 下一轮最高优先级：更新发布文档的当前候选为 release7，随后同步、构建、审计并生成 release7 manifest。

### 批次 180：发布文档推进至 release7（2026-09-09）

- 本批次范围：将当前候选从 release5 统一推进到 release7，保留 release5/release6 为历史中间产物；未调用模型 API、未重复 `.deb` 第六批生命周期、未执行视频、截图或图像任务。
- 实际修改：`docs/innovation-stability-report.md` 更新当前 manifest 为 release7；`docs/release-freeze.md` 更新当前候选、包/审计/manifest/非视频路径为 release7，并保留旧版本历史；`docs/deb-release.md` 将 release5 标为历史并增加 release7 构建说明；`docs/final-reproduction-checklist.md` 更新 release7 包和 b179 非视频路径；`README.md` 更新 release7 候选及审计引用。
- 实际检查命令：`rg -n -i "当前 release5|当前发布候选为 release5|release-manifest-release5|当前 release5 技术候选|0.2.0+release5|innovation no-memory 对照尚未执行|没有执行 innovation no-memory" docs/innovation-stability-report.md docs/release-freeze.md docs/deb-release.md docs/final-reproduction-checklist.md README.md`；退出码 `0`，仅命中 `docs/deb-release.md` 中明确标注为“历史中间产物”的 release5 段落。
- 环境信息：Windows 工作区；权威 openKylin VM 为 2.0 SP2 (nile)、x86_64、Python 3.12.2、PyYAML 6.0.1。
- 已完成：当前文档的候选版本、no-memory 状态、最终非视频路径和 wrapper 能力边界一致，历史版本记录保留。
- 部分完成：release7 尚未同步、构建、审计或生成 manifest；release6 仍是已完成的中间包证据。
- 未完成/暂缓：项目级 LICENSE 与云 API 条款待负责人/法务确认；OS 重启/跨用户未执行；桌面视频、截图、图像和媒体任务暂缓。
- 客观阻塞：无文档修订阻塞；后续需要 VM SSH 构建通道。
- 待确认假设：release7 将作为最终技术候选，包内文档与根工作区状态完全一致；任何变更都需要重新构建和刷新 manifest。
- 下一轮最高优先级：同步 release7 当前源码到 VM，构建并保存 `0.2.0+release7` 包。

### 批次 181：release7 首次源码同步失败（2026-09-09）

- 本批次范围：尝试将 release7 当前源码、套件、脚本、文档和打包配置一次性同步到既有 openKylin VM；未调用模型 API、未执行构建/安装/卸载或媒体任务。
- 实际命令：`scp -q -o BatchMode=yes -o ConnectTimeout=10 -i C:\\Users\\123\\.ssh\\openkylin_vm_ed25519 -P 2222 -r kmb configs suites docs scripts pyproject.toml setup.py README.md CHANGELOG.md NOTICE THIRD_PARTY_NOTICES.md LICENSE-MIT-CANDIDATE.txt packaging <vm-user>@192.168.182.129:<user-home>/kmb-openkylin-validation-20260906/`；退出码 `5`。
- 实际错误：`C:\\WINDOWS\\System32\\OpenSSH\\scp.exe: Connection closed`；未据此声称同步成功。证据 `runs/openkylin-validation-20260909/release7-sync/command.txt`、`stdout.log`、`stderr.log`、`exitcode`。
- 已完成：失败命令和错误已保留；工作区文件未被删除或覆盖。
- 部分完成：release7 尚未确认完整同步到 VM；需分路径重试并逐项核验。
- 客观阻塞：本次为 SSH/SCP 传输中断，原因尚未确认是连接波动或单次负载。
- 待确认假设：VM SSH 服务仍可达，分路径小批传输可恢复；重试前将执行轻量 SSH 探针并记录。
- 下一轮最高优先级：使用分路径 SCP 重试 release7 同步，并保存每个路径的退出码。

### 批次 182：release7 分路径同步脚本变量错误（2026-09-09）

- 本批次范围：执行分路径 SCP 重试前的 SSH 探针和传输脚本；未调用模型 API、未构建/安装/卸载或执行媒体任务。
- 实际命令：分路径同步脚本原计划逐项执行 `scp -q ... -r <path> <vm-user>@192.168.182.129:<user-home>/kmb-openkylin-validation-20260906/`；脚本先将 `$host` 作为变量名赋值，触发 PowerShell 保留变量错误 `Cannot overwrite variable Host because it is read-only or constant.`。
- 实际结果：脚本探针退出码 `255`，未把路径同步结果写成成功；证据 `runs/openkylin-validation-20260909/release7-sync-retry/`，其中 `probe.exitcode=255`。
- 已完成：错误已定位为本地 PowerShell 变量命名，不是 SSH/VM 能力结论；原始日志保留。
- 部分完成：release7 同步仍未确认完成。
- 客观阻塞：无项目功能阻塞；需修正脚本变量名。
- 待确认假设：改用非保留变量名后，SSH 探针和分路径传输可正常工作。
- 下一轮最高优先级：用 `$remoteTarget` 重新执行探针和逐路径 SCP，并记录真实退出码。

### 批次 183：release7 分路径同步通道超时（2026-09-09）

- 本批次范围：使用非保留变量名执行 SSH 轻量探针和逐路径 SCP，尝试同步 release7 当前源码；未调用模型 API、未构建/安装/卸载或执行媒体任务。
- 实际结果：SSH 探针到 `192.168.182.129:2222` 返回连接超时，`probe.exitcode=5`；逐路径传输 `kmb/configs/suites/docs/scripts` 及文件大多退出码 `5`，部分被中止的传输退出码 `4`；`overall.exitcode=1`。未把任何路径写成同步成功。
- 证据路径：`runs/openkylin-validation-20260909/release7-sync-retry2/`，保存每个路径的 command/stdout/stderr/exitcode；本轮启动的 SSH/SCP 子进程已清理。
- 已完成：确认当前时点 VM SSH 通道不可达并保留可复现超时证据；工作区源码未删除或覆盖。
- 部分完成：release7 尚未同步或构建；此前 release6/release5 包和审计不受影响。
- 客观阻塞：目标 VM `192.168.182.129:2222` 当前连接超时，无法继续远端构建；原因可能是 VM 休眠/网络切换/SSH 服务暂不可用，当前无法从超时本身区分。
- 待确认假设：VM 恢复运行并重新开放 SSH 后可继续分路径同步；必须重新探针确认，不能沿用旧的 SSH 成功记录。
- 下一轮最高优先级：执行独立 `Test-NetConnection`/SSH 探针确认 VM 是否恢复；恢复后再同步、构建和审计 release7，否则保留阻塞记录。

### 批次 184：release7 VM 通道恢复探针（2026-09-09）

- 本批次范围：用户重新打开 VM 后，重新执行 TCP 端口和 SSH 轻量探针；未调用模型 API、未同步/构建/安装/卸载或执行媒体任务。
- 实际命令：`Test-NetConnection -ComputerName 192.168.182.129 -Port 2222 -InformationLevel Detailed`；输出 `TcpTestSucceeded : True`，记录退出码 `0`。随后执行 `ssh -o BatchMode=yes -o ConnectTimeout=5 -i C:\\Users\\123\\.ssh\\openkylin_vm_ed25519 -p 2222 <vm-user>@192.168.182.129 "printf channel_ok"`，输出 `channel_ok`，退出码 `0`。
- 证据路径：`runs/openkylin-validation-20260909/release7-channel-probe-open/command.txt`、`tcp.stdout.log`、`tcp.exitcode`、`ssh.stdout.log`、`ssh.stderr.log`、`ssh.exitcode`。
- 已完成：确认 VM 打开后网络和 SSH 通道恢复可达；之前批次 183 的连接超时仍保留为历史时点事实，不再作为当前通道状态。
- 部分完成：release7 仍未确认同步/构建；需重新执行同步和远端构建。
- 客观阻塞：当前探针无阻塞。
- 待确认假设：VM 在后续同步期间保持运行且 2222 端口不再切换；若再次中断，保留实际失败日志。
- 下一轮最高优先级：重新同步 release7 当前源码到 VM，并记录同步退出码。

### 批次 185：release7 源码分路径同步成功（2026-09-09）

- 本批次范围：在 VM 通道恢复后，将 release7 当前源码、套件、脚本、文档、配置和打包文件分路径同步到 `<user-home>/kmb-openkylin-validation-20260906/`；未同步 `runs/`、虚拟环境或凭据文件，未调用模型 API、未构建/安装/卸载或执行媒体任务。
- 实际命令：对 `kmb configs suites docs scripts pyproject.toml setup.py README.md CHANGELOG.md NOTICE THIRD_PARTY_NOTICES.md LICENSE-MIT-CANDIDATE.txt packaging` 逐项执行 `scp -q -o BatchMode=yes -o ConnectTimeout=15 -i C:\\Users\\123\\.ssh\\openkylin_vm_ed25519 -P 2222 -r <path> <vm-user>@192.168.182.129:<user-home>/kmb-openkylin-validation-20260906/`；13 项退出码全部为 `0`，总退出码 `0`。
- 证据路径：`runs/openkylin-validation-20260909/release7-sync-retry3/`，每项含 command/stdout/stderr/exitcode 和 `overall.exitcode`。
- 环境信息：目标 openKylin 2.0 SP2 (nile)、x86_64、Python 3.12.2、PyYAML 6.0.1；SSH 通道 `192.168.182.129:2222`。
- 已完成：release7 当前源码和文档已完整同步到 VM，未携带本地运行目录或凭据。
- 部分完成：尚未在 VM 构建 release7；许可证、OS 重启/跨用户和视频仍未完成或暂缓。
- 客观阻塞：无同步阻塞。
- 待确认假设：远端项目目录中的既有 `.kmb-venv` 和凭据保持不变，构建脚本可直接复用；下一批将保存构建退出码和包路径。
- 下一轮最高优先级：在 VM 执行 `KMB_DEB_VERSION=0.2.0+release7 bash scripts/build_deb.sh dist/release-20260909-release7`。

### 批次 186：release7 构建命令生成错误（2026-09-09）

- 本批次范围：准备在 VM 执行 release7 构建并保存日志；未成功发出远端构建命令，未调用模型 API、未安装/卸载或执行媒体任务。
- 实际错误：PowerShell 生成 command 文本时使用嵌套双引号，触发解析错误 `Unexpected token '$remote"' in expression or statement.`；构建脚本未执行，不能将该批次写成构建失败或成功。目标输出目录 `runs/openkylin-validation-20260909/release7-build/` 仅为准备目录。
- 已完成：解析错误已定位为本地命令字符串构造问题；无远端副作用。
- 部分完成：release7 构建尚未执行。
- 客观阻塞：无项目功能阻塞；需改用简单字符串拼接重发命令。
- 待确认假设：SSH 通道仍可达，修正引号后构建可正常启动。
- 下一轮最高优先级：重新执行 release7 VM 构建并保存真实 stdout/stderr/exitcode。

### 批次 187：release7 openKylin VM 构建成功（2026-09-09）

- 本批次范围：在已同步 release7 文档状态的 openKylin VM 构建 `0.2.0+release7`；未执行系统安装/升级/卸载、模型 API 调用或视频/媒体任务。
- 实际命令：`cd <user-home>/kmb-openkylin-validation-20260906 && KMB_DEB_VERSION=0.2.0+release7 bash scripts/build_deb.sh dist/release-20260909-release7`；SSH 远程构建退出码 `0`。
- 实际产物：VM `dist/release-20260909-release7/kylin-memory-bench_0.2.0+release7_all.deb`；构建 stdout/stderr/exitcode 见 `runs/openkylin-validation-20260909/release7-build-retry/`，包清单显示当前 README、release freeze、复现清单、稳定性和 Debian 文档。
- 环境信息：openKylin 2.0 SP2 (nile)、x86_64、Python 3.12.2、PyYAML 6.0.1。
- 已完成：release7 技术包构建成功，构建脚本输出无禁止内容错误。
- 部分完成：尚未复制回本地或执行独立内容/敏感/套件审计，manifest 尚未生成；许可证、OS 重启/跨用户和视频仍未完成或暂缓。
- 客观阻塞：无构建阻塞。
- 待确认假设：构建 staging 已按脚本排除凭据、运行结果、虚拟环境和字节码；下一批将以 `dpkg-deb` 和 smoke 实测确认。
- 下一轮最高优先级：复制 release7 包回本地并执行 VM 内容、敏感、套件和包内 smoke 审计。

### 批次 188：release7 包复制回本地（2026-09-09）

- 本批次范围：将 VM 构建完成的 release7 `.deb` 复制回本地，未执行安装/升级/卸载、模型 API 调用或媒体任务。
- 实际命令：`scp -q -o BatchMode=yes -o ConnectTimeout=15 -i C:\\Users\\123\\.ssh\\openkylin_vm_ed25519 -P 2222 <vm-user>@192.168.182.129:<user-home>/kmb-openkylin-validation-20260906/dist/release-20260909-release7/kylin-memory-bench_0.2.0+release7_all.deb dist/release-20260909-release7/kylin-memory-bench_0.2.0+release7_all.deb`；退出码 `0`。
- 实际结果：本地包存在，大小和哈希已记录；SHA-256 `89ce1e7e7f9b80af92585299f0418b15aa147de6b4ddfd19bc686555f0a5aaf2`。
- 证据路径：`runs/openkylin-validation-20260909/release7-audit/copy.command.txt`、`copy.stdout.log`、`copy.stderr.log`、`copy.exitcode`、`local.sha256`。
- 环境信息：目标 openKylin 2.0 SP2 (nile)、x86_64 VM；本地工作区 Windows。
- 已完成：release7 包复制和本地哈希确认。
- 部分完成：尚未完成独立 VM 内容审计结果归档和 manifest。
- 客观阻塞：无复制阻塞。
- 待确认假设：复制过程未改变包内容，后续以 VM `dpkg-deb` 输出和本地哈希双重核验。
- 下一轮最高优先级：完成 release7 VM 内容、敏感、套件和 smoke 审计。

### 批次 189：release7 VM 内容与包内 smoke 审计（2026-09-09）

- 本批次范围：在 openKylin VM 对 release7 包执行 `dpkg-deb --info`、`dpkg-deb --contents`、禁止内容扫描、中文/英文核心与对抗套件及 innovation 五套件严格校验、解包入口检查和包内 smoke；未执行系统安装/升级/卸载、模型 API 调用或媒体任务。
- 实际结果：SSH 审计命令退出码 `0`；`dpkg-info=0`、`dpkg-contents=0`、`forbidden-payload=0`、`innovation-validate=0`、`core-validate=0`、`core-en-validate=0`、`adversarial-validate=0`、`adversarial-en-validate=0`、`unpack=0`、`packaged-entry-check=0`、`package-smoke=0`；总 `audit.exitcode=0`，`forbidden_payload=none`。
- 证据路径：`runs/openkylin-validation-20260909/release7-audit/`，包含审计脚本、每步 stdout/stderr/exitcode、解包目录和复制日志。
- 环境信息：openKylin 2.0 SP2 (nile)、x86_64、Python 3.12.2、PyYAML 6.0.1；包版本 `0.2.0+release7`。
- 已完成：release7 包内容、安全门禁、五套件校验、入口和 smoke 审计全部通过。
- 部分完成：release7 manifest 尚未生成；本批次不替代既有第六批 root 安装/升级/卸载生命周期。
- 客观阻塞：无包审计阻塞。
- 待确认假设：release7 包内文档已包含当前候选状态，manifest 将通过源文件哈希进一步确认。
- 下一轮最高优先级：生成并严格校验 release7 发布 manifest，纳入 b179 非视频复核和 no-memory 五批证据。

### 批次 190：release7 发布 manifest 生成（2026-09-09）

- 本批次范围：基于 release5 manifest 结构生成独立 `release-manifest-release7.json`，更新 release7 包/审计路径、当前 40 个源文件 SHA-256、no-memory 五批证据、系统级边界和 b179 非视频复核；未调用模型 API、未执行安装/升级/卸载或媒体任务。
- 实际命令：PowerShell `generate release-manifest-release7.json from release5 structure, current source SHA-256, release7 package/audit, no-memory evidence and b179 non-video checks`；退出码 `0`。
- 实际产物：`runs/openkylin-validation-20260909/release-manifest-release7/release-manifest-release7.json`；候选包 `dist/release-20260909-release7/kylin-memory-bench_0.2.0+release7_all.deb`，哈希 `89ce1e7e7f9b80af92585299f0418b15aa147de6b4ddfd19bc686555f0a5aaf2`。
- 已完成：manifest 包含 release7 候选、openKylin 环境、Grok/DeepSeek 模型 ID、innovation memory/no-memory 证据、系统场景边界、40 个源文件指纹和安全字段；未写入凭据。
- 部分完成：manifest 尚需独立校验；最终非视频复核仍需确认所有当前文档引用一致。
- 客观阻塞：无生成阻塞。
- 待确认假设：release7 包内容和工作区源文件在 manifest 校验前不再变化。
- 下一轮最高优先级：执行 release7 manifest 的完整哈希、路径、审计退出码和敏感信息校验。

### 批次 191：release7 发布 manifest 严格校验（2026-09-09）

- 本批次范围：独立校验 release7 manifest 的 JSON/schema、候选包版本与 SHA-256、40 个源文件 SHA-256、证据/文档/审计路径、b179 非视频状态和敏感模式；未调用模型 API、未执行生命周期或媒体任务。
- 实际结果：校验退出码 `0`，输出 `status=ok errors=0 source_file_count=40 package_sha256=89ce1e7e7f9b80af92585299f0418b15aa147de6b4ddfd19bc686555f0a5aaf2`；`audit_exit=0`、`b179_status=pass`、`sensitive_scan=clean`。
- 证据路径：`runs/openkylin-validation-20260909/release-manifest-release7/validate.command.txt`、`validate.stdout.log`、`validate.stderr.log`、`validate.exitcode`、`release-manifest-release7.json`。
- 已完成：release7 manifest 与包、当前源文件和审计证据一致，40 项源指纹和所有引用路径通过，未发现敏感模式。
- 部分完成/未完成：尚未进行新的 root `.deb` 生命周期；项目级 LICENSE 与云 API 条款待负责人/法务确认；OS 重启/跨用户未执行；视频、截图和图像任务暂缓。
- 客观阻塞：无 manifest 校验阻塞。
- 待确认假设：已通过的第六批生命周期可作为 release7 技术候选的生命周期依据，release7 本批次仅有内容审计，不把它写成新的安装/升级/卸载证据。
- 下一轮最高优先级：执行最终非视频一致性复核，确认 release7 文档、manifest、包哈希和 no-memory/系统场景边界无过期引用。

### 批次 192：release7 最终一致性复核初次尝试（2026-09-09）

- 本批次范围：复核 release7 manifest 与当前文档、包审计、b179 非视频复核和敏感门禁的一致性；未调用模型 API、未执行生命周期或媒体任务。
- 实际检查结果：manifest 解析、release7 包哈希、40 个源文件哈希、release7-audit 各步骤退出码、b179 `status=pass`、当前 release7 文档引用和敏感模式扫描均通过；敏感命中 `0`。
- 批次记录问题：过期 marker 检查使用了宽泛的 `release-manifest-release5`/`release5` 匹配，将 `docs/deb-release.md` 中明确标注为“历史中间产物”的 release5 记录误判；同时写入 batch exitcode 的 PowerShell `-Value (if(...))` 表达式解析失败。`runs/final-nonvideo-20260909-b192-release7/batch-summary.json` 保留真实检查字段和误判原因，不能作为最终 pass 结论。
- 已完成：确认没有当前候选、哈希、审计或敏感信息问题；识别出复核脚本的历史记录误报。
- 部分完成：需用精确的“当前 release5/未执行”模式重跑文档状态检查并安全写入退出码。
- 客观阻塞：无项目功能阻塞；仅复核脚本表达式和 marker 范围需修正。
- 待确认假设：`docs/deb-release.md` 的 release5 文本均为历史说明，不影响当前 release7 候选；b193 将以行文语义精确排除该历史段落。
- 下一轮最高优先级：执行 b193 精确文档 marker、manifest/包哈希和审计一致性复核，生成完整 pass 汇总。

### 批次 193：release7 最终非视频一致性复核完成（2026-09-09）

- 本批次范围：精确复核 release7 manifest 与候选包、40 个源文件、release7 VM 审计、b179 非视频门禁、当前发布文档和敏感信息状态；未调用模型 API、未执行 `.deb` 第六批生命周期、OS 重启/跨用户或视频/截图/图像任务。
- 实际命令：`PowerShell final release7 consistency check with precise current-state markers; includes manifest/package/source hashes, audit exitcodes, b179 pass, docs, sensitive scan`；退出码 `0`。
- 实际结果：`status=pass`、`errors=0`、`source_file_count=40`、`source_hash_mismatches=[]`、release7-audit 各步骤退出码均为 `0`、`b179_status=pass`、`missing_doc_references=[]`、`current_docs_with_stale_markers=[]`、`sensitive_pattern_hits=0`；候选包 SHA-256 `89ce1e7e7f9b80af92585299f0418b15aa147de6b4ddfd19bc686555f0a5aaf2`。
- 证据路径：`runs/final-nonvideo-20260909-b193-release7/batch-summary.json`、`command.txt`、`exitcode`；发布 manifest 与校验见 `runs/openkylin-validation-20260909/release-manifest-release7/`。
- 已完成：release7 当前候选、包审计、源指纹、文档引用、no-memory 状态、系统级边界和非视频门禁一致；历史 release4-release6 产物保留为历史记录。
- 部分完成/未完成：项目级 LICENSE 和云 API 展示/留存授权仍待项目负责人/法务确认；OS 重启和跨用户切换未执行；真实 Agent 仍无可观测原生记忆事件，结论仅限模型后端+外部包装层系统级行为；视频、截图、图像和桌面录制暂缓。
- 客观阻塞：系统级 OS 重启/跨用户需要认证 root、专用用户和重启后外部控制通道；许可证与云 API 条款需要项目负责人/法务确认；这些不能由本地文件或普通 CLI 推断。
- 待确认假设：release7 为当前最终技术候选；负责人确认许可证和云 API 条款后不再修改代码/文档/包。若发生任何变更，必须重新构建、审计并刷新 manifest。
- 下一轮最高优先级：完成项目负责人/法务对项目级 LICENSE 与云 API 条款的书面确认；确认后执行最后提交前检查，再进入统一视频录制。

### 批次 194：openKylin 工作台同步与 VM 启动验证（2026-09-09）

- 本批次范围：将本地新增工作台源码同步到已建立 SSH 通道的 openKylin VM，并在 VM 的现有 `.kmb-venv` 中启动本地回环服务、读取真实配置/套件/历史结果、触发一次离线双 Agent 工作台烟测；未调用 Grok/DeepSeek API，未录制视频、截图或其他媒体。
- 环境信息：openKylin 2.0 SP2 (nile)，Linux 6.6.0-25-generic，x86_64，Python 3.12.2，PyYAML 6.0.1；SSH `192.168.182.129:2222`，项目目录 `<user-home>/kmb-openkylin-validation-20260906`。
- 实际命令和退出码：SSH 环境探针（`uname -a`、`python3 --version`、项目目录检查）`0`；远端目录准备 `0`；首次多源同步 `0`，首次路径校验因 `scp` 多源目标目录语义错误退出 `1`（无远端代码损坏）；按 `kmb/`、`docs/` 分目录纠正同步 `0`；纠正后 VM `sha256sum`、`py_compile` 和 `python -m kmb.cli --help` `0`，确认出现 `serve/workbench`。
- 工作台启动：VM 执行 `.kmb-venv/bin/python -m kmb.cli serve --host 127.0.0.1 --port 18765 --root .`，服务日志 `runs/openkylin-validation-20260909/workbench-vm-194/server.log`，监听确认成功；首次 PID 重定向记录因后台 shell 优先级未写入预期文件，后续探针已修正 `server.pid`，最终探针退出码 `0`。
- API 验证：VM 回环请求 `/`、`/api/system`、`/api/configs`、`/api/suites`、`/api/runs` 均 HTTP `200`，探针退出码 `0`。`api-system.json` 明确返回 `openKylin 2.0 SP2`、`x86_64`、Python `3.12.2`、CLI `0.2.0`，并返回系统级测试能力矩阵。
- 工作台烟测：向 VM `POST /api/runs` 提交 `configs/agent-reference.yaml` 与 `configs/agent-flawed.yaml`、`suites/core-zh.yaml`、`seed=42`、`retries=0`、`timeout=30`、`scorer_version=deterministic-v2`，提交退出码 `0`；轮询退出码 `0`，运行 ID `wb-20260909-213629-31c230a1` 状态 `completed`，两个配置各完成 34 个 `simulated_baseline` 证据事件。结果明确标注为离线参考/缺陷基线，不计作 Grok/DeepSeek 真实赛事结果。
- 证据路径：VM 服务探针和 API 响应已复制到 `runs/openkylin-validation-20260909/workbench-vm-194/`；VM 工作台结果复制到 `runs/openkylin-validation-20260909/workbench-vm-194/wb-20260909-213629-31c230a1/`，包含 `comparison.json`、两个 Agent 的 `result.json`、`evidence.jsonl`、Markdown/HTML/SVG 报告和 `workbench-*.json`。
- 已完成：工作台源码/静态资源在 VM 正确同步；openKylin VM 服务可启动；真实 VM API 能读取本地数据；工作台后端可在 VM 完成受控离线双 Agent 作业；未向 VM 或结果目录写入 API 密钥。
- 部分完成：本批次尚未通过浏览器 SSH 隧道完成所有页面交互/窄窗口检查；release7 `.deb` 尚未重新构建以包含工作台；本批次不替代真实 Grok/DeepSeek 运行证据。
- 未完成/暂缓：真实系统级 OS 重启/跨用户、项目许可证负责人确认、桌面视频/截图/图像任务仍按历史边界处理。
- 客观阻塞：无 SSH 或 VM 启动阻塞；浏览器端到 VM 的访问仍需受控 SSH 隧道或 VM 桌面会话。首次错误复制路径和 PID 记录已纠正，保留其退出码以便审计。
- 后续清理：删除首次错误同步在 VM 项目根目录产生的临时 `cli.py`、`workbench.py`，并复查 `kmb/cli.py`、`kmb/workbench.py` 和 `/api/system`；SSH 清理与服务复查退出码 `0`。
- 待确认假设：`127.0.0.1:18765` 仅供 VM 本地浏览器或 SSH 隧道访问，未暴露到公共网卡；工作台依赖 VM 现有 `.kmb-venv`，未重新安装系统包。
- 下一轮最高优先级：通过受控 SSH 隧道完成 openKylin 浏览器交互与窄窗口验证，并据此重新构建/审计包含工作台资源的 release8 `.deb`。

### 批次 195：API 配置分组、凭据自动加载与双后端健康检查（2026-09-09）

- 本批次范围：修正本地工作台“所有云配置未检测”和配置列表把运行模式误显示为多个 API 版本的问题；服务启动时安全加载用户级凭据文件；按 Grok/DeepSeek 提供商分组显示标准 API、记忆开启和无记忆基线；同步到 openKylin VM 并执行真实最小健康检查。未录制视频、截图或其他媒体。
- 修改文件：`kmb/workbench.py`（`~/.config/kmb/credentials.env` 权限/允许字段检查与加载、提供商/运行模式元数据、系统状态）；`kmb/web/app.js`（Grok/DeepSeek 分组、运行模式标签、凭据状态提示、本地模板折叠）；`kmb/web/styles.css`（提供商/模式布局和凭据提示样式）；`tests/test_workbench.py`（配置元数据和安全加载测试）；`docs/workbench.md`、`README.md`（凭据加载、提供商范围和 VM/Windows 边界说明）。
- 本地验证：`python -m py_compile kmb/workbench.py kmb/cli.py` 和 `node --check kmb/web/app.js` 退出码 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，共 `55` 项通过。Windows 权限语义测试通过受控 mock 验证解析，不改变 openKylin 上真实 `0600` 检查。
- 本地工作台验证：重启 `127.0.0.1:8765` 服务退出码 `0`；`/api/system` 返回 Windows、`credentials.status=absent`，云配置数量 `6`、提供商仅 `Grok,DeepSeek`；浏览器页面确认 API 页只突出两个提供商，标准 API/记忆开启/无记忆基线集中展示，本地基线/模板折叠。
- VM 同步与服务：`scp` 同步 `kmb/`、静态前端和文档退出码均为 `0`。一次旧 PID 未命中导致新服务端口占用，`server-v2.log` 记录真实 `OSError: [Errno 98] Address already in use`，未把它写成成功；随后按实际 Python PID 重启 `server-v3` 退出码 `0`，临时根目录 `workbench.md` 已清理，VM `kmb/` 正式文件保留。
- VM 环境状态：`/api/system` 返回 openKylin 2.0 SP2、x86_64、Python 3.12.2、`credentials.status=secure`、模式 `0600`；凭据仍只存在 VM 原有 `~/.config/kmb/credentials.env`，未复制到本地、源码、日志或结果。
- 真实健康检查：在 VM 工作台后端对六个配置各发送一次固定 `Reply with exactly: ok` 探针，记录目录 `runs/openkylin-validation-20260909/workbench-vm-195/`；`health-grok.json`、`health-grok-memory.json`、`health-grok-no-memory.json`、`health-deepseek.json`、`health-deepseek-memory.json`、`health-deepseek-no-memory.json` 全部返回 `status=healthy`、`http_status=200`。模型 ID 只有 `grok-4.6` 与 `deepseek-v4-flash`；延迟由各 JSON 记录，未写入密钥。
- 浏览器验证：建立本机回环 SSH 隧道 `127.0.0.1:18766 -> VM 127.0.0.1:18765`（隧道可达），通过浏览器打开 VM 工作台，确认环境徽标 `openKylin 2.0 SP2`、两个 Agent 显示“凭据已加载”。
- 证据路径：`runs/openkylin-validation-20260909/workbench-vm-195/`（系统/配置响应、服务日志、PID、六份健康 JSON）；前端源代码和测试路径见上方修改文件。
- 已完成：确认连接失败根因是 Windows 本机服务未加载 VM 凭据；修正后 VM 服务能自动读取安全凭据，Grok/DeepSeek 及其两种包装模式均真实健康；UI 不再把模式误称为额外模型版本。
- 部分完成：工作台源码已在 VM 验证，但尚未重新构建包含工作台的 release8 `.deb`；本批次健康检查不是完整六案例双 Agent 评测。
- 未完成/暂缓：真实系统重启/跨用户、项目许可证负责人确认、桌面视频/截图/图像任务仍按历史边界处理。
- 客观阻塞：无 API 连接阻塞；Windows 本机若未配置凭据仍会显示未检测，这是环境边界而非 API 失败。需要在 VM 内启动工作台或使用 SSH 隧道访问 VM 服务。
- 待确认假设：当前项目最终仍只纳入 Grok 与 DeepSeek 两个云端提供商；`doubao`、外部命令、回放和 reference/flawed 仅作为待接入/本地验证配置，不计入真实双 Agent 赛事结论。
- 下一轮最高优先级：重新构建并审计包含本次工作台和凭据状态修正的 release8 `.deb`，再做包内 CLI/工作台 smoke 验证。

### 批次 196：本地工作台修改同步到 openKylin 后的哈希与服务复核（2026-09-09）

- 本批次范围：复核上一批已同步到 openKylin VM 的工作台后端、CLI、静态前端、文档和测试文件；未同步 `runs/`、虚拟环境或凭据文件，未录制视频、截图或其他媒体。
- 实际同步后的 VM 文件：`kmb/workbench.py`、`kmb/cli.py`、`kmb/web/index.html`、`kmb/web/app.js`、`kmb/web/styles.css`、`docs/workbench.md`、`README.md`、`tests/test_workbench.py`；VM 项目目录 `<user-home>/kmb-openkylin-validation-20260906`。
- 实际命令与退出码：SSH 远端复核（`sha256sum`、`.kmb-venv/bin/python -m py_compile kmb/workbench.py kmb/cli.py`、`.kmb-venv/bin/python -m kmb.cli --help`、`curl /api/system`、`curl /api/configs`、服务进程和临时文件检查）退出码 `0`；本地/VM 逐文件 SHA-256 对比退出码 `0`，`8/8` 文件匹配。
- 实际结果：VM 仍为 openKylin 2.0 SP2、x86_64、Python 3.12.2、CLI `0.2.0`；工作台服务进程继续监听 `127.0.0.1:18765`；`/api/system` 和 `/api/configs` 返回 `200`；系统状态显示凭据 `secure`、权限 `0600`，响应未包含密钥值；配置列表按 Grok/DeepSeek 和运行模式提供真实元数据。VM 项目根目录未发现误同步的 `cli.py`、`workbench.py` 或 `workbench.md` 临时文件。
- 环境信息：SSH `<vm-user>@192.168.182.129:2222`；工作台仅绑定 VM 回环地址，需受控 SSH 隧道或 VM 本地浏览器访问。
- 证据路径：`runs/openkylin-validation-20260909/workbench-sync-196/remote-check.log`、`remote-check.exitcode`、`local.sha256.json`、`hash-compare.json`、`hash-compare.exitcode`。
- 已完成：本地修改已同步到 VM；8 个目标文件哈希一致；VM Python 语法、CLI 帮助、工作台服务、系统和配置 API 复核通过；未复制 API 凭据。
- 部分完成：本批次未重新构建 release8 `.deb`，未进行新的安装/升级/卸载生命周期；浏览器页面交互和窄窗口验证仍待后续单独批次。
- 未完成/暂缓：真实系统级重启/跨用户、项目许可证负责人/法务确认、桌面视频/截图/图像任务仍按既有边界处理。
- 客观阻塞：无本批次同步或 VM 服务阻塞。Windows 本机若未配置凭据仍不会显示 VM 凭据状态，访问 VM 工作台应通过 SSH 隧道。
- 待确认假设：当前同步文件与后续 release8 构建输入保持不变；若本地再次修改工作台文件，必须重新执行同步和哈希复核。
- 下一轮最高优先级：重新构建并审计包含工作台资源的 release8 `.deb`，再执行包内 CLI/工作台 smoke 验证。

### 批次 197：本地工作台首轮交互与信息层级完善（2026-09-09）

- 本批次范围：仅在 Windows 本地工作区完善工作台 UI 交互和复现信息展示；按用户要求本批次未同步 openKylin VM，未修改 VM 文件、虚拟环境或凭据，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/index.html`（增加服务状态区域和全局错误的实时语义）；`kmb/web/app.js`（视图内刷新动作绑定、刷新忙状态、服务/环境标签、健康检查结果持久化与最近检查时间、套件案例/能力/哈希摘要、公平比较参数摘要、运行状态可访问性、模式状态映射）；`kmb/web/styles.css`（服务状态、套件摘要、公平性摘要和窄屏样式）。
- 实际行为修正：新建评测和结果中心中的“刷新”按钮现在调用真实 `loadData()`；健康检查结果按配置保存在前端运行态，切换视图后仍显示状态、延迟和最近检查时间；套件下拉框下方显示本地元数据中的案例数、六维能力覆盖和 SHA-256 前缀；顶部环境标签区分 openKylin 与非 openKylin 本地验证，并显示本地服务/凭据状态；运行参数摘要显示 seed、重试、超时和评分器版本。
- 实际命令与退出码：`python -m py_compile kmb/workbench.py kmb/cli.py` 退出码 `0`；`node --check kmb/web/app.js` 退出码 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，共 `55` 项通过；本地 `GET /`、`GET /app.js`、`GET /styles.css` 均 HTTP `200`；资源标记检查（刷新绑定、健康状态持久化、套件摘要、服务状态）退出码 `0`。
- 实际环境：Windows 本地工作台服务 `127.0.0.1:8765`，由 `D:\Programs\Python\Python39\python.exe -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .` 提供；本地服务 `/api/system` 的 openKylin 检测仍按真实环境显示非 openKylin，不能替代 VM 结论。
- 证据路径：`runs/workbench-local/ui-polish-197/py-compile.stdout.log`、`py-compile.exitcode`、`js-check.stdout.log`、`js-check.exitcode`、`unit-tests.stdout.log`、`unit-tests.exitcode`、`resource-check.json`、`resource-check.exitcode`。
- 已完成：上述 UI 交互和信息层级改动已在本地服务提供并通过语法、回归测试和资源检查；未改变 CLI、后端结果格式和 API 凭据安全边界。
- 部分完成：本批次未在浏览器中重新同步或验证 VM 页面；当前浏览器可见的 openKylin 版本仍对应上一批 VM 隧道页面，不能当作本地改动已在 VM 生效的证据。
- 未完成/暂缓：release8 `.deb` 尚未因本地 UI 变更重建；浏览器窄窗口交互复核、真实系统级场景、项目许可证确认和桌面视频/截图/图像任务仍按既有边界处理。
- 客观阻塞：无本地实现或测试阻塞；VM 同步按用户要求暂缓。
- 待确认假设：当前本地服务自动读取最新工作区静态资源；后续若继续修改 UI，需先在本地完成专项校验，只有收到明确同步指令后才执行 VM 同步、哈希复核和远端服务验证。
- 下一轮最高优先级：继续本地工作台结果中心和失败证据下钻的交互细化与窄窗口验证；暂不构建或同步 release8，除非用户另行要求。

### 批次 198：本地刷新忙状态回归修正（2026-09-09）

- 本批次范围：修正批次 197 中发现的本地 UI 刷新按钮状态恢复问题；未同步 openKylin VM，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/app.js`，在 `loadData()` 完成渲染后重新调用 `updateRefreshState()`，确保数据加载结束后刷新按钮恢复可用。
- 实际命令与退出码：`node --check kmb/web/app.js` 退出码 `0`；本地 `GET /`、`GET /app.js` 资源检查和刷新状态标记检查退出码 `0`。
- 证据路径：`runs/workbench-local/ui-polish-197/js-check-after-refresh-fix.stdout.log`、`js-check-after-refresh-fix.exitcode`、`refresh-state-check.json`、`refresh-state-check.exitcode`。
- 已完成：刷新按钮忙状态恢复逻辑已修正并通过 JavaScript 语法和本地资源检查。
- 部分完成：尚未在浏览器中重新同步/验证 VM 页面；本地服务验证不等同于 openKylin 验证。
- 客观阻塞：无本地阻塞；VM 同步按用户要求暂缓。
- 待确认假设：后续修改仍只在本地工作区生效，直到收到明确同步指令。
- 下一轮最高优先级：继续本地结果中心和证据下钻的可用性细化，并进行本地窄窗口交互复核；暂不同步 VM。

### 批次 199：本地结果状态和失败类型可读性完善（2026-09-09）

- 本批次范围：仅在本地工作台改善结果中心、稳定性区域和系统设置的状态可读性；未同步 openKylin VM，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/app.js`，新增模拟/无记忆/混合模式和系统场景状态的中文显示映射；失败类型显示中文标签并保留原始枚举作为 title；失败详情判定区复用同一映射。原始 JSON、失败类型值和评分逻辑未修改。
- 实际命令与退出码：`node --check kmb/web/app.js` 退出码 `0`；本地 `GET /app.js` HTTP `200`；模式、失败类型和系统场景映射资源检查退出码 `0`。
- 实际结果：结果中心将 `simulated_baseline` 显示为“模拟基线”，`no_memory_baseline` 显示为“无记忆基线”；失败列表和证据抽屉将 `stale_update`、`confusion`、`erroneous_persistence` 等内部代码显示为对应中文语义；系统设置显示受控 openKylin 控制器、专用账户、网络命名空间和沙箱边界要求。
- 证据路径：`runs/workbench-local/ui-polish-197/js-check-labels.stdout.log`、`js-check-labels.exitcode`、`label-check.json`、`label-check.exitcode`。
- 已完成：本地结果页面显示层改动通过 JavaScript 语法和资源检查，未改变后端 API 或证据格式。
- 部分完成：尚未在浏览器重新检查本地改动后的窄窗口和证据抽屉视觉布局；VM 页面保持上一批同步版本。
- 客观阻塞：无本地实现阻塞；VM 同步按用户要求暂缓。
- 待确认假设：内部枚举到中文标签的映射覆盖当前已知失败类型；若后端增加新类型，将回退显示原始值，避免误导。
- 下一轮最高优先级：本地浏览器窄窗口交互检查，重点验证结果中心筛选、证据抽屉和 API 配置页的滚动与文字溢出；完成后再决定是否继续本地改动或等待 VM 同步指令。

### 批次 200：本地 API 凭据缺失状态表达完善（2026-09-09）

- 本批次范围：依据本地 API 配置页实际表现，优化凭据缺失与端点调用失败的状态区分；未同步 openKylin VM，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/app.js`（识别“required environment variable ... is not set”并显示为未配置安全凭据，保留原始错误在 title；API 配置页提示 Windows 本地服务与 VM 凭据隔离）；`kmb/web/styles.css`（增加橙色 `health-state.warn` 状态）。
- 实际命令与退出码：`node --check kmb/web/app.js` 退出码 `0`；本地 `GET /app.js`、`GET /styles.css` 均 HTTP `200`；凭据状态分类、VM 隔离提示和 warn 样式资源检查退出码 `0`。
- 实际结果：本地未配置凭据时，API 配置页显示“未配置安全凭据”（橙色），不再把配置前置条件误报为端点红色故障；非凭据类后端错误仍显示“连接失败”；页面明确说明 VM 凭据不会自动同步到 Windows。未读取、输出或写入任何完整密钥。
- 证据路径：`runs/workbench-local/ui-polish-197/js-check-credential-state.stdout.log`、`js-check-credential-state.exitcode`、`credential-state-check.json`、`credential-state-check.exitcode`。
- 已完成：本地凭据状态显示层通过语法和资源检查，未改变后端健康检查协议和敏感信息保护。
- 部分完成：尚未在浏览器重新检查本地改动后的视觉状态和窄窗口；VM 页面未同步，不能把本地结果写成 openKylin UI 结果。
- 客观阻塞：无本地实现阻塞；VM 同步按用户要求暂缓。
- 待确认假设：后端缺失凭据错误继续使用 `required environment variable ... is not set` 句式；未知句式会按普通连接失败显示，避免误分类。
- 下一轮最高优先级：本地浏览器窄窗口交互检查，重点确认 API 配置页状态文案、结果中心失败筛选和证据抽屉布局；继续保持 VM 不同步。

### 批次 201：本地工作台新增第三方 API 配置向导（2026-09-10）

- 本批次范围：在 Windows 本地工作台增加其他 OpenAI-compatible Chat Completions API 的配置档案创建能力；未同步 openKylin VM，未调用真实云端 API，未录制视频、截图或其他媒体。
- 修改文件：`kmb/workbench.py`（动态加载工作区配置引用的安全环境变量；新增 `POST /api/configs`、非敏感字段校验、原子写入 `configs/agent-*.yaml`、拒绝密钥/请求头/覆盖已有档案）；`kmb/web/app.js`（API 配置页新增档案向导、保存反馈、隐藏输入凭据命令复制、其他 API 分组）；`kmb/web/styles.css`（向导、凭据命令和反馈样式）；`tests/test_workbench.py`（新增配置写入、重复/密钥拒绝、自定义凭据加载和 HTTP API 测试）；`docs/workbench.md`、`README.md`（新增第三方 API 配置和安全凭据说明）。
- 实际命令与退出码：`python -m py_compile kmb/workbench.py kmb/cli.py` 退出码 `0`；`node --check kmb/web/app.js` 退出码 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，共 `58` 项通过；本地服务 `python -m kmb.cli serve --host 127.0.0.1 --port 18767 --root .` 启动后，`POST http://127.0.0.1:18767/api/configs` 返回 `201`，`GET /` 和 `GET /app.js` 均返回 `200`。
- 实际结果：新增配置 API 生成 `configs/agent-<profile>.yaml`，只包含名称、类型、端点、模型、`api_key_env`、超时、请求选项和说明；禁止提交 `api_key`、secret、token、password、Authorization 或 headers 字段；禁止覆盖现有配置。自定义 `api_key_env` 只有在工作区配置引用且凭据文件权限为 `0600` 时才会从 `~/.config/kmb/credentials.env` 加载，值不返回到 API 响应、浏览器状态、日志或结果文件。
- 浏览器验证：已检查本地 `http://127.0.0.1:8765/` 工作台真实页面和配置选择器；新增向导资源通过 `node --check` 和本地服务静态资源 `200` 检查。临时烟测档案 `configs/agent-local-test-profile-201.yaml` 已删除；证据目录未保存密钥。
- 证据路径：`runs/workbench-local/api-profile-201/system.json`、`created.json`、`index.status`、`app.status`；单元测试输出由本轮命令产生，未记录任何完整凭据。
- 已完成：用户可在 GUI 新增其他 OpenAI-compatible API 配置，保存后可在新建评测选择并从配置卡片健康检查；CLI 既有配置加载和运行链路保持兼容；API Key 仍必须在运行环境通过隐藏输入或安全环境变量提供。
- 部分完成：仅支持标准 OpenAI-compatible Chat Completions 的通用 HTTP 档案；非兼容协议仍需 `type: command` 或专用适配器。尚未同步 VM，因此 openKylin 工作台当前不包含本批次向导。
- 未完成/暂缓：VM 同步、release8 重建、真实第三方新增档案健康检查、系统级场景、许可证负责人确认和视频/截图/图像任务均未在本批次执行。
- 客观阻塞：无本地代码或测试阻塞；VM 同步按用户此前要求暂缓；第三方 API 的具体端点、模型 ID 和授权条款需由使用者确认。
- 待确认假设：目标 API 遵循 `POST /chat/completions` 的 OpenAI-compatible 请求/响应格式，且模型返回至少包含 `choices[0].message`；否则必须通过外部命令适配器接入。
- 下一轮最高优先级：在用户明确允许同步后，将本批次工作台文件同步到 openKylin，执行 VM 端语法/API/浏览器复核，再决定是否重建 release8。

### 批次 202：本地第三方 API 配置向导回归与自定义提供商烟测（2026-09-10）

- 本批次范围：继续完善本地工作台的第三方 API 接入体验；修正 Agent 选择器将自定义云 API 显示为“本地/测试配置”的语义问题，统一为“其他 API / 本地配置”；补充提供商字段回读测试；通过本地工作台 HTTP 接口创建、读取、健康检查并清理临时 Mistral 配置。未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/app.js`（其他配置选择器分组文案）；`tests/test_workbench.py`（断言自定义 `provider` 字段写入和回读）。后端 `kmb/workbench.py`、`docs/workbench.md`、`README.md` 本批次未再修改。
- 实际命令和退出码：`python -m py_compile kmb/workbench.py kmb/cli.py` `0`；`node --check kmb/web/app.js` `0`；`python -m unittest discover -s tests -v` `0`，`58` 项通过（`runs/workbench-local/api-profile-202/unit-tests.stdout.log`、`unit-tests.exitcode`）；本地工作台 `http://127.0.0.1:8765` 静态资源 `GET /app.js`、`GET /styles.css` 均 `200`。
- 自定义档案烟测：向 `POST /api/configs` 提交非敏感的 Mistral OpenAI-compatible 配置，HTTP 状态 `201`；`GET /api/configs` 回读 `provider=Mistral`、模型 `mistral-small-latest`、路径 `configs/agent-client-custom-202b.yaml` 和 `credential=not_detected`，响应字段不含 `api_key`；对该档案 `POST /api/health` 返回 HTTP `200`、状态 `error`、脱敏原因 `required environment variable MISTRAL_API_KEY is not set`，未发起外部模型调用；删除临时档案后再次查询配置列表确认不再列出，清理退出码 `0`。
- 凭据保护：本批次没有读取、写入或输出任何真实 API Key；测试只使用变量名和合成档案元数据。前端选择器和配置 API 响应未返回密钥值，生成的配置 YAML 仅含 `api_key_env` 引用。
- 证据路径：`runs/workbench-local/api-profile-202/verification-summary.json`、`create-provider.json`、`create-provider.status`、`config-provider-summary.json`、`health-provider.json`、`health-provider.status`、`cleanup-provider.json`、`cleanup-provider.exitcode`、`py-compile.stdout.log`、`js-check.stdout.log`、`unit-tests.stdout.log`；此前批次创建烟测记录保留在 `runs/workbench-local/api-profile-201/`。
- 已完成：本地 GUI/HTTP 可新增任意 OpenAI-compatible Chat Completions API 档案；提供商与模型元数据可回读并进入 Agent 选择器；缺少安全凭据时显示为未配置而非伪造连接成功；临时档案清理和 58 项回归测试通过。
- 部分完成：当前新增向导仍只支持 OpenAI-compatible Chat Completions 协议，Anthropic/Gemini 等非兼容协议需使用已有 `type: command`/专用适配器；本批次未在 openKylin VM 同步或验证，也未执行真实 Mistral 等新增提供商调用。
- 未完成/暂缓：VM 同步、release8 重建、第三方新增档案真实健康检查、系统级场景、许可证负责人确认和视频/截图/图像任务均未在本批次执行；视频继续按既定顺序暂缓。
- 客观阻塞：无本地代码或测试阻塞；VM 同步按用户此前要求暂缓。自定义提供商的实际可用性取决于用户提供的端点、模型 ID、授权和安全凭据；本批次未猜测或伪造这些信息。
- 待确认假设：目标自定义服务遵循 `POST /chat/completions`、Bearer API Key 和 `choices[0].message` 的 OpenAI-compatible 约定；若不满足，需要外部命令适配器或专用协议适配。当前工作台只展示脱敏端点摘要，不验证服务方条款。
- 下一轮最高优先级：在用户明确允许同步后，将本地工作台新增 API 配置向导和分组修正同步到 openKylin，执行 VM 端语法/API/浏览器复核；在同步前继续保持本地-only。

### 批次 204：本地 API 配置页布局与安全凭据提示调整（2026-09-11）

- 本批次范围：按用户界面反馈调整本地 API 配置页顺序和安全凭据提示；未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/app.js`（新增配置向导由 `afterbegin` 改为 `beforeend`，现有 API 配置和其他档案先展示；云端未就绪提示明确同一运行环境和 `~/.config/kmb/credentials.env`）；`kmb/web/styles.css`（新增配置向导改为底部区块的间距）。
- 实际命令和退出码：`node --check kmb/web/app.js` `0`；`python -m py_compile kmb/workbench.py kmb/cli.py` `0`；`python -m unittest discover -s tests -v` `0`，`58` 项通过。证据记录在 `runs/workbench-local/api-layout-204/js-check.log`、`js-check.exitcode`、`py-compile.log`、`py-compile.exitcode`、`unit-tests.log`、`unit-tests.exitcode`、`verification-summary.json`。
- 浏览器验证：本地服务 `python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .` 正常监听；通过本地浏览器打开 `http://127.0.0.1:8765/` 并进入“API 配置”，可见顺序为 `SECURE PROVIDERS / API 配置`、Grok/DeepSeek 配置卡片、“其他 API、本地基线与接入模板”折叠区，最后是“新增 API 配置档案”；DOM 顺序断言 `api_before_create=true`。`GET /app.js`、`GET /styles.css` 均 `200`，静态检查见 `runs/workbench-local/api-layout-204/static-check.json`。
- 安全凭据边界：界面不接受或显示 API Key；仅提示在运行工作台的同一环境执行保存后生成的隐藏输入命令，凭据文件目标为 `~/.config/kmb/credentials.env`，权限要求 `600`。本批次未读取、写入或输出完整密钥。
- 已完成：API 配置在上、新增配置在下的页面层级已修正；现有配置、连接检查和新增档案逻辑未改变；语法和全量回归测试通过。
- 部分完成：新增向导仍只支持 OpenAI-compatible Chat Completions；本地 Windows 页面不能代表 openKylin VM 凭据状态，VM 同步和远端浏览器复核按用户要求暂缓。
- 未完成/暂缓：非兼容协议专用适配器、真实新增提供商调用、release8 重建、系统级场景、许可证负责人确认、视频/截图/图像任务继续保持既有状态。
- 客观阻塞与待确认假设：无本地实现阻塞；实际 API 是否可用取决于用户在运行环境配置的端点、模型 ID、授权和安全凭据。下一轮最高优先级：在用户明确允许同步后，将本地工作台布局和凭据提示同步到 openKylin 并做 VM 端复核。

### 批次 203：第三方 API 烟测证据敏感信息复核（2026-09-10）

- 本批次范围：对批次 202 的本地验证目录执行敏感信息扫描和临时配置残留复核；未同步 VM，未调用第三方 API，未录制视频、截图或其他媒体。
- 实际命令和退出码：使用 `rg` 扫描 `runs/workbench-local/api-profile-202` 中 JSON、日志和 YAML 的常见 `sk-`、`gsk_`、`xai-`、Bearer 模式，退出码 `0`；扫描结果 `match_count=0`、`status=clean`。临时档案 `configs/agent-client-custom-202.yaml`、`configs/agent-client-custom-202b.yaml` 均不存在，且 API 配置列表不再返回对应路径，清理退出码 `0`。
- 证据路径：`runs/workbench-local/api-profile-202/secret-scan.json`、`cleanup.json`、`cleanup.exitcode`、`cleanup-provider.json`、`cleanup-provider.exitcode`。
- 已完成：本批次新增 API 配置烟测产物未发现常见完整密钥或 Bearer 值；临时配置残留复核通过。
- 未完成/暂缓：本地工作台新增 API 向导尚未同步 openKylin；非 OpenAI-compatible 协议、真实新增提供商调用、release8 重建、系统级场景、许可证确认和视频任务继续保持既有未完成/暂缓状态。
- 客观阻塞与待确认假设：无本地阻塞；扫描只覆盖列出的常见密钥模式，不能替代使用者对实际凭据轮换和第三方条款的人工确认。下一轮最高优先级仍为用户明确允许后的 VM 同步与复核。

### 批次 205：本地工作台 CodexPlusPlus 风格 UI 改造与浏览器复核（2026-09-11）

- 本批次范围：仅在 Windows 本地工作区改造工作台 UI/UX，保留现有 CLI、后端 API、结果模型、证据格式和 API 凭据边界；未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他赛事媒体。
- 任务顺序与产物：增加开发工具式三栏布局（深色左侧导航、主工作区、真实状态 Inspector rail）和底部状态栏；统一按钮、表单、表格、标签、证据抽屉和响应式断点样式；新增 `runs/workbench-local/ui-codexplus-205/` 验证日志与浏览器检查摘要。
- 修改文件：`kmb/web/index.html`（增加 `inspector-rail`、`status-bar` 容器并保留既有 ID）；`kmb/web/app.js`（增加真实 `state.job`/`state.selectedRun`/`state.system` 驱动的状态栏、Agent/参数/事件/观测边界展示，增加右侧栏折叠交互；未新增虚构运行数据）；`kmb/web/styles.css`（深色开发工具主题、三栏网格、统一间距/边框/字体/状态、1280/1440/1920 桌面断点和窄窗口回退）；`runs/workbench-local/ui-codexplus-205/browser-verification.json`（浏览器验证摘要）。
- 实际命令与退出码：`node --check kmb/web/app.js` `0`；`python -m py_compile kmb/workbench.py kmb/cli.py` `0`；`python -m unittest discover -s tests -v` `0`，`58` 项通过；`rg` 对 `kmb/web` 执行常见 API Key/Bearer 模式扫描，退出码 `0`，结果 `secret_scan=clean`。
- 本地服务与浏览器验证：`python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .` 正常监听；在 `http://127.0.0.1:8765/` 实测 1280x720 浏览器视口，新建评测页载入真实 Grok/DeepSeek 配置和 innovation 套件，右侧显示真实空状态；API 配置页保持“已有配置在上、新增 API 配置档案在下”；结果中心加载实际历史运行、六维指标、失败筛选、报告/证据入口；Inspector rail 展开→折叠→展开交互通过；未观察到文字或布局溢出。1440/1920 通过 CSS 断点与网格约束覆盖，未伪称为独立浏览器截图验证。
- 证据路径：`runs/workbench-local/ui-codexplus-205/js-check.log`、`js-check.exitcode`、`py-compile.log`、`py-compile.exitcode`、`unit-tests.log`、`unit-tests.exitcode`、`browser-verification.json`。
- API 凭据保护：本批次未读取、写入、传输或显示任何完整 API Key；右侧状态栏和 API 配置页只显示真实的“未配置云凭据/安全状态”，不将缺失凭据显示为连接成功；页面仍要求在同一运行环境使用权限 `600` 的安全凭据文件。
- 已完成：本地工作台深色开发工具视觉、三栏信息层级、真实状态 Inspector、底部状态栏、现有页面交互和证据下钻样式改造；全量回归测试通过；CLI/后端文件未改动行为。
- 部分完成：当前本地浏览器实际观测为 1280x720；1440/1920 仅完成响应式 CSS 覆盖检查；openKylin VM 尚未同步，不能把本地 UI 结果表述为 VM 验证。
- 未完成/暂缓：VM 同步与 VM 端浏览器复核、真实第三方 API 调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务继续保持既有状态。
- 客观阻塞：无本地代码或测试阻塞；VM 同步继续遵循用户指令，等待明确同步请求。
- 待确认假设：历史运行摘要的套件字段可能因旧结果格式缺失而显示“未选择”，但不会伪造套件名；真实套件、证据和报告仍以结果文件中的路径为准。
- 下一轮最高优先级：在用户明确允许同步后，将本地工作台 UI 文件同步到 openKylin，并在 VM 中执行语法、服务启动、页面和凭据安全复核；同步前继续保持本地-only。

### 批次 206：本地工作台服务与当前源码收尾复核（2026-09-11）

- 本批次范围：仅复核批次 205 的本地工作台源码、运行服务和既有验证证据；未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 实际检查：`http://127.0.0.1:8765/`、`/app.js`、`/styles.css` 均返回 HTTP `200`；浏览器当前页仍加载三栏工作区、真实 Agent 配置、创新套件、结果中心和 Inspector；批次 205 的 `node --check`、Python 编译和 58 项回归测试退出码均为 `0`。
- 安全复核：对 `kmb/web/**` 使用严格的长密钥/Bearer 模式扫描，结果 `secret_scan=clean`；未读取、写入或输出任何完整 API Key。
- 证据路径：`runs/workbench-local/ui-codexplus-205/browser-verification.json`、`js-check.exitcode`、`py-compile.exitcode`、`unit-tests.exitcode`。
- 已完成：本地页面与当前源码一致，服务资源可访问，已有验证证据未发现回归。
- 部分完成：独立 1440/1920 浏览器实测和 openKylin VM 端复核仍未执行；不能将本批次本地结果写成 VM 验证。
- 未完成/暂缓：VM 同步、真实新增提供商调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务继续保持既有状态。
- 客观阻塞：无本地阻塞；VM 同步继续遵循用户指令，等待明确同步请求。
- 待确认假设：后续改动仍只在本地工作区生效，直到收到明确同步指令。
- 下一轮最高优先级：继续本地 UI 交互细化；用户明确允许同步后，再将工作台 UI 文件同步到 openKylin 并执行 VM 端语法、服务、页面和凭据安全复核。

### 批次 207：本地工作台 Developer Tool 信息架构重排（2026-09-11）

- 本批次范围：依据 Codex++/VS Code 风格要求，在本地工作台重排信息架构和交互；未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/index.html`（扩展 Sidebar 为总览、新建评测、评测任务、运行历史、对比分析、结果中心、Agent 管理、API / 模型配置、系统设置；增加 Toolbar 容器）；`kmb/web/app.js`（新增总览、评测任务、Agent 管理视图；重排双 Agent 对比工作区；新增 Result/Compare/Cases/Evidence/Logs Tab、逐 Case 对比、真实状态 Inspector、保存/复制/刷新/开始/停止/更多操作；兼容本地草稿；修复删除旧刷新按钮后的初始化回归）；`kmb/web/styles.css`（新增紧凑 Developer Tool 工作区、Toolbar、双 Agent VS、Inspector 分段、结果 Tab、Case 对比和响应式布局样式）；`kmb/workbench.py`（新增协作停止标记和 `POST /api/jobs/<id>/stop`，停止不会伪造成完成）；`tests/test_workbench.py`（新增停止任务取消事件测试）。
- 实际命令和退出码：`node --check kmb/web/app.js` `0`；`python -m py_compile kmb/workbench.py kmb/cli.py` `0`；`python -m unittest discover -s tests -v` `0`，`59` 项通过；严格长密钥/Bearer 模式扫描 `secret_scan=clean`；本地服务 `python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .` 重启后 `/`、`/app.js`、`/styles.css` 均 HTTP `200`；缺失任务 Stop 路由返回 HTTP `404`，未伪造成功。
- UI 实际复核：新浏览器标签页加载 `http://127.0.0.1:8765/` 后显示 `WORKSPACE`/`CONFIGURATION` 两组共 9 个导航项；Toolbar 包含保存、复制配置、刷新、开始/停止、更多；Inspector 包含 `RUN`、`TASK`、`AGENTS`、`PARAMETERS`、`LIVE EVENTS`、`BOUNDARY`；结果工作区包含 `Result`、`Compare`、`Cases`、`Evidence`、`Logs`。旧直接打开 `E:/.../kmb/web/index.html` 的空白样式问题属于绕过本地服务，已在记录中保持区分。
- Stop 烟测：`runs/workbench-local/ui-codexplus-207/stop-smoke.log` 显示取消事件已设置、状态为 `stopping`；后台 Agent 边界检查后写入 `stopped`，不会产生完成结论。
- 证据路径：`runs/workbench-local/ui-codexplus-207/verification-summary.json`、`js-check.log`、`js-check.exitcode`、`py-compile.log`、`py-compile.exitcode`、`unit-tests.log`、`unit-tests.exitcode`、`secret-scan.status`、`stop-smoke.log`、`stop-smoke.exitcode`、`http-stop-missing.status`。
- 已完成：本地 UI 已从传统表单重排为 AI Developer Tool 工作区；既有 CLI、配置、结果、证据和评分数据结构保留；停止操作具备后端协作取消语义；59 项回归测试通过。
- 部分完成：本批次仅在 Windows 本地服务和浏览器验证；尚未在 1440/1920 视口做独立浏览器实测，尚未同步 openKylin VM；停止操作对正在执行的单个 Agent 采用边界协作取消，底层不可中断的当前调用会在返回后结束。
- 未完成/暂缓：VM 同步与 VM 端浏览器复核、真实新增提供商调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务继续保持既有状态。
- 客观阻塞：无本地代码阻塞；VM 同步继续遵循用户指令，等待明确同步请求。
- 待确认假设：用户期望的 Codex++ 视觉参考以产品语言和信息层级为准，不复制其具体实现；图标当前使用统一的文本线性符号，后续如项目引入图标库可替换为同等语义图标。
- 下一轮最高优先级：继续本地浏览器逐项复核 Result/Compare/Cases/Evidence/Logs 和窄窗口交互；用户明确允许同步后，再同步到 openKylin 并执行 VM 端验证。
### 批次 208：本地工作台页面职责拆分与动态 Inspector（2026-09-12）

- 本批次范围：按产品信息架构要求重构本地 GUI 页面职责；未同步 openKylin VM，未录制视频、截图或其他媒体，未调用真实第三方 API。
- 修改文件：`kmb/web/app.js`、`kmb/web/styles.css`。
- 页面职责：总览新增评测趋势、Agent 排名和最近失败概览；结果中心改为 Result Dashboard，展示 Agent A/B 总分、Winner、Score Delta、成功率、案例数、平均耗时、失败案例、六维快照、趋势、最近评测和失败摘要；对比分析改为 Investigation / Comparison，展示六维差异、雷达、最大差异能力、Cases、Evidence、Memory Trace 和 Logs；运行历史改为时间、任务、Agent A/B、Cases、Score、状态、Duration 摘要表，不再默认展开大量 filesystem path。
- 动态 Inspector：新建评测显示 Configuration；评测任务显示 Runtime Progress / Live Events；结果中心显示 Result Summary；对比分析显示 Compare Context；Agent 管理显示 Agent Details；API 配置显示 Provider Details；总览、历史和系统设置分别显示对应上下文。
- Agent / Provider 交互：Agent 管理支持查看详情和用于评测；API / 模型配置 Provider 卡片支持进入 Endpoint、Model、环境变量引用和连接测试详情。API Key 仍只通过安全凭据引用，未进入浏览器状态、日志或报告。
- 证据链交互：对比分析可从差异进入 Cases，选择案例后查看左右 Agent 结果，继续进入 Evidence 和 Memory Trace；Memory Trace 仅呈现实际 `evidence_refs`，不推断不可观测的模型内部状态。
- 实际命令与退出码：`node --check kmb/web/app.js` 退出码 `0`；`python -m py_compile kmb/workbench.py kmb/cli.py` 退出码 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，共 `59` 项通过；本地浏览器访问 `http://127.0.0.1:8765/`，结果中心、对比分析、Cases、Memory Trace、Agent 详情和 Provider 详情均完成真实 DOM 交互复核。
- 证据路径：`runs/workbench-local/ui-ia-208/verification-summary.json`、`js-check.stdout.log`、`js-check.exitcode`、`py-compile.stdout.log`、`py-compile.exitcode`；浏览器验证基于本地工作台真实结果目录和运行 ID `wb-20260909-213629-31c230a1`。
- 已完成：结果中心与对比分析不再复用同一默认页面；页面职责、工作流和 Inspector 上下文已区分；保留既有 CLI、后端接口、结果格式、案例下钻和敏感凭据边界。
- 部分完成：本批次仅在 Windows 本地服务验证；尚未在 openKylin VM 同步或验证，不能将本地浏览器结果表述为 VM 证据。
- 未完成/暂缓：openKylin 同步、真实新增提供商调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务仍按既有边界暂缓。
- 客观阻塞：无本地实现或测试阻塞；VM 同步仍需用户明确指令。
- 待确认假设：历史运行中部分单 Agent 记录没有 `duration` 或 `cases` 字段，UI 对缺失值显示“未记录/—”，不推断为零。
- 下一轮最高优先级：继续本地窄窗口（约 1280/1440/1920）交互和结果下钻回归；待收到明确同步指令后再执行 openKylin VM 同步与验证。
### 批次 209：工作台信息架构交互回归（2026-09-12）

- 本批次范围：对批次 208 的页面职责拆分进行浏览器回归，补充总览趋势/排名/失败概览、Memory Trace 入口、Agent 使用信息和 Provider 详情交互；未同步 openKylin VM，未录制视频、截图或其他媒体，未调用真实第三方 API。
- 实际验证：本地 `http://127.0.0.1:8765/` 重新加载后依次验证总览、结果中心、对比分析、Cases、Memory Trace、Agent 管理详情、API / 模型配置 Provider 详情；结果来自本地运行 `wb-20260909-213629-31c230a1` 及工作区 `runs/` 文件。
- 可见职责：结果中心显示总分、Winner、Delta、成功率、案例数、失败案例、六维快照、趋势、最近评测；对比分析显示调查上下文、六维差异、雷达、最大能力差异、Cases、Evidence、Memory Trace 和 Logs；Inspector 标题分别为 `Workspace Overview`、`Result Summary`、`Compare Context`、`Agent Details`、`Provider Details`。
- 实际命令与退出码：`node --check kmb/web/app.js` 退出码 `0`；`python -m py_compile kmb/workbench.py kmb/cli.py` 退出码 `0`；此前同批 `python -m unittest discover -s tests -v` 退出码 `0`，59 项通过。
- 证据路径：`runs/workbench-local/ui-ia-208/verification-summary.json`；服务地址 `http://127.0.0.1:8765/`。
- 已完成：页面职责不再通过换标题复用同一界面；总览、结果、调查、Agent、Provider 和系统上下文均有独立内容与可点击入口。
- 部分完成：尚未在 1280/1440/1920 三种固定视口逐项自动化截图核对；本地浏览器验证不替代 openKylin VM 验证。
- 未完成/暂缓：openKylin 同步、真实新增提供商调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务继续暂缓。
- 客观阻塞：无本地实现阻塞；VM 同步需用户明确指令。
- 待确认假设：历史单 Agent 记录的 `duration`、`cases` 缺失值保持“未记录/—”，不会推断为零。
- 下一轮最高优先级：按用户决定继续本地窄窗口交互回归，或在明确同步后执行 openKylin VM 同步验证。

### 批次 210：本地工作台交互与桌面视口最终收口（2026-09-12）

- 本批次范围：继续本地-only UI 收尾；复核结果中心与对比分析职责、Cases -> Evidence 下钻、1280/1440/1920 视口布局，并统一双 Agent 证据事件口径。未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/app.js`。结果中心两个“证据事件”指标改为汇总 Agent A 与 Agent B 的实际本地 JSONL 事件数；双 Agent 场景标注为“`双 Agent · 本地 JSONL`”，避免与 Inspector 的双 Agent 总量不一致。上一轮已落地的通过案例 Evidence drawer handler（`verified: 证据已记录`）本批次完成回归验证。
- 实际验证命令与退出码：`node --check kmb/web/app.js` 退出码 `0`；`python -m py_compile kmb/workbench.py kmb/cli.py` 退出码 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，共 `59` 项通过；`rg` 严格扫描 `kmb/web`、`runs/workbench-local/ui-ia-208`、`runs/workbench-local/ui-ia-210` 和上下文包中的常见 `sk-`、`gsk_`、`xai-`、Bearer 长密钥模式，退出码 `0`，`secret_scan=clean`、`match_count=0`。
- 本地服务：`python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .`，服务监听 `http://127.0.0.1:8765/`；`/`、`/app.js`、`/styles.css` 返回 HTTP `200`。`/api/state` 不是现有路由，探测返回 HTTP `404`，未将其误报为服务失败；实际 API 路由以 `/api/runs`、`/api/configs`、`/api/system` 等为准。
- 浏览器验证：在本地浏览器对结果中心和对比分析执行真实导航；结果中心显示总分、Winner、Delta、六维快照、趋势和双 Agent 证据事件 `68`；对比分析显示 `Result / Compare / Cases / Evidence / Memory Trace / Logs` 六个 Tab，选择通过案例 `retention-001` 后点击“打开 Evidence”成功打开完整 EvidenceEvent 时间线（5 条事件、来源 `simulated`、证据引用、评分理由和复现路径）。在显式视口 `1280x720`、`1440x900`、`1920x1080` 下分别检查结果中心与对比分析，三种尺寸均无横向溢出（`scrollWidth <= innerWidth`），标题和 Tab 正常显示。
- 证据路径：`runs/workbench-local/ui-ia-210/js-check.stdout.log`、`js-check.exitcode`、`py-compile.stdout.log`、`py-compile.exitcode`、`unit-tests.log`、`unit-tests.exitcode`、`secret-scan.log`、`secret-scan.exitcode`；浏览器基于本地运行 `wb-20260909-213629-31c230a1`，其实际 EvidenceEvent 文件和结果路径由 Evidence drawer 展示。
- 已完成：本地 UI 结果/调查职责分离、Cases -> Evidence 下钻、通过与失败案例统一 Evidence 入口、三种桌面视口无横向溢出、双 Agent 证据计数口径统一、语法/编译/59 项回归测试和敏感信息扫描通过。
- 部分完成：本批次仍只在 Windows 本地服务验证；未同步或复核 openKylin VM，不能把本批次 UI 结果表述为 VM 证据。独立 1440/1920 仅做 DOM/布局实测，不生成截图媒体。
- 未完成/暂缓：openKylin VM 同步、真实第三方 Agent 调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务继续按既有记录暂缓。
- 客观阻塞：无本地实现或测试阻塞；VM 同步必须等待用户明确指令。服务的 `/api/state` 探测为非路由 404，不影响既有 API。
- 待确认假设：当前历史运行 `wb-20260909-213629-31c230a1` 明确为确定性演示基线（`reference` vs `flawed`），Evidence 来源为 `simulated`，不得据此证明模型原生长期记忆能力；结果中心的 68 为双 Agent 汇总事件数，仅对实际 `_workbench.metrics.events` / `evidence_chain.events` 可见值求和。
- 下一轮唯一最高优先级：在用户明确允许同步后，将本地工作台 UI 与本批次修订同步至 openKylin VM，并执行 VM 端服务启动、页面职责、Evidence 下钻、视口与凭据安全复核；同步前继续保持本地-only。

### 批次 211：KylinMemoryBench Codex++ 风格视觉收口（2026-09-12）

- 本批次范围：根据 Codex++ / VS Code / Cursor 开发工具风格要求，在本地工作区完成一次视觉与交互层收口；不改变业务、后端 API、CLI、结果格式或评分逻辑，未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/index.html` 新增顶部 `WORKSPACE / KylinMemBench / 本地` 上下文条；`kmb/web/styles.css` 调整为更接近 Codex++ 的深色开发工具层级（背景、Sidebar、Panel、低对比边框、无装饰性渐变、无面板阴影），保留三栏工作区、Toolbar、Inspector 和底部 Status Bar；移动窗口时隐藏上下文条以避免拥挤。
- 实际验证命令与退出码：`node --check kmb/web/app.js` 退出码 `0`；`python -m py_compile kmb/workbench.py kmb/cli.py` 退出码 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，共 `59` 项通过；常见 `sk-`、`gsk_`、`xai-`、Bearer 长密钥扫描退出码 `0`，`secret_scan=clean`、`match_count=0`。
- 本地服务和浏览器验证：`python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .`；`http://127.0.0.1:8765/` 正常访问。逐页检查总览、新建评测、评测任务、运行历史、对比分析、结果中心、Agent 管理、API / 模型配置、系统设置；在 `1280x720`、`1440x900`、`1920x1080` 三种显式桌面视口下检查，所有页面 `documentElement/body.scrollWidth <= innerWidth`，无横向溢出。结果与证据仍来自现有本地运行目录。
- 视觉变化：移除总览主工作区的背景渐变，统一为平面深色面板；取消普通 Panel 阴影；顶部增加 Workspace 上下文，强化桌面工具感；保留蓝色主交互、橙色对比 Agent、绿色成功、红色错误的语义色使用。
- 证据路径：`runs/workbench-local/ui-codexplus-211/js-check.log`、`js-check.exitcode`、`py-compile.log`、`py-compile.exitcode`、`unit-tests.log`、`unit-tests.exitcode`；敏感扫描记录为本批次命令输出（未发现匹配）。
- 已完成：本地 UI 视觉层级和开发工具布局收口；真实导航与 Toolbar/Inspector/Status Bar 保持可用；三种桌面视口逐页无横向溢出；回归测试和凭据安全扫描通过。
- 部分完成：浏览器验证在 Windows 本地服务执行，不能替代 openKylin VM 验证；本批次未生成截图媒体。
- 未完成/暂缓：openKylin VM 同步、真实第三方 Agent 调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务继续按既有记录暂缓。
- 客观阻塞：无本地代码或测试阻塞；VM 同步继续等待用户明确指令。
- 待确认假设：当前 UI 使用项目已有文本线性符号作为图标；未引入额外图标依赖，不影响现有功能和许可证范围。
- 下一轮唯一最高优先级：在用户明确允许后，同步本地 UI 到 openKylin VM 并执行 VM 端页面、服务和凭据安全复核；同步前继续保持本地-only。

### 批次 212：Codex++ 风格顶部上下文与响应式细化（2026-09-12）

- 本批次范围：对批次 211 的本地 UI 收口补充响应式调整，避免 1180px 以下窗口的顶部 Workspace 上下文与 Toolbar 挤压；未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/styles.css`。在 `max-width: 1180px` 断点隐藏顶部 Workspace 上下文条，保持宽桌面布局展示；未修改业务逻辑或后端接口。
- 实际验证命令与退出码：`node --check kmb/web/app.js` 退出码 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，共 `59` 项通过。浏览器在 `1280x720` 下复核 Toolbar、导航和页面内容，无横向溢出；此前批次 211 已完成 `1440x900`、`1920x1080` 逐页检查。
- 证据路径：`runs/workbench-local/ui-codexplus-211/browser-verification.json`、`js-check.log`、`js-check.exitcode`、`unit-tests.log`、`unit-tests.exitcode`。
- 已完成：顶部 Workspace 上下文在宽桌面显示、在较窄桌面自动收紧；导航、Toolbar、Inspector、Status Bar 和现有页面工作流保持可用。
- 部分完成/暂缓：仍只在 Windows 本地服务验证；openKylin VM 同步、真实第三方调用、视频/截图/图像任务继续按既有记录暂缓。
- 客观阻塞：无本地阻塞；VM 同步等待用户明确指令。
- 待确认假设：1180px 作为 Workspace 上下文隐藏断点，依据当前三栏网格和 Toolbar 内容密度设定，若后续目标设备不同可再调整。
- 下一轮唯一最高优先级：在用户明确允许后，将本地 UI 修订同步到 openKylin VM，并执行 VM 端启动、页面交互、Evidence 下钻和凭据安全复核。

### 批次 213：本地工作台 Inspector 文案收口与页面回归（2026-09-13）

- 本批次范围：仅收口本地工作台 Inspector 页面标题，降低模板化英文标题带来的展示感；未改变后端接口、CLI、运行结果、证据格式、评分逻辑或凭据边界。未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/app.js`。Inspector 标题由 `Runtime Progress`、`Result Summary`、`Compare Context`、`Agent Details`、`Provider Details`、`Workspace Overview`、`Run Archive`、`System / Environment`、`Configuration` 收口为 `任务进度`、`结果摘要`、`对比上下文`、`Agent 详情`、`提供商详情`、`工作区`、`运行历史`、`系统环境`、`评测配置`；保留 `model`、`wrapper`、`simulated` 来源标识和既有字段。
- 新增产物：`runs/workbench-local/ui-polish-213/verification-summary.json`；命令日志位于同目录 `js-check.log`、`py-compile.log`、`unit-tests.log`、`secret-scan.log`，对应退出码文件同目录保存；服务以前台终端会话运行，未伪造为文件日志。
- 实际命令和退出码：`node --check kmb/web/app.js` 退出码 `0`；`python -m py_compile kmb/workbench.py kmb/cli.py` 退出码 `0`；`python -m unittest discover -s tests -v` 退出码 `0`，`59` 项通过；严格常见 `sk-`、`gsk_`、`xai-` 和 Bearer 长密钥扫描退出码 `1`（`rg` 无匹配语义），状态 `clean`、`match_count=0`。
- 本地服务：`python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .`，当前监听 `http://127.0.0.1:8765/`，HTTP 根路径返回 `200`。服务会话实际进程由当前终端会话保持，未向 VM 同步。
- 浏览器验证：在本地 Codex in-app browser 真实点击九个导航项，页面标题与 Inspector 标题逐项匹配；结果中心真实显示运行 `wb-20260909-213629-31c230a1`、六维结果和 `Result / Compare / Cases / Evidence / Memory Trace / Logs` 入口；对比分析显示相同工作流 Tab、六维差异和 `对比上下文` Inspector；控制台错误为空；整体 `scrollWidth <= body width`，桌面默认窗口实际观察为 `1280x720`。本批次尝试设置 `1440x900` 和 `390x844`，但浏览器实际保持 `1280x720`，未将覆盖请求写成已验证尺寸；既有三桌面视口证据保留在 `runs/workbench-local/ui-codexplus-211/browser-verification.json`。
- 工作流和安全复核：结果中心与对比分析没有回退为同一默认页面；服务资源 `/`、`/app.js`、`/styles.css` 可访问；页面未读取、保存或显示完整 API Key，凭据状态仍由后端安全配置元数据驱动。
- 已完成：Inspector 标题中文化收口；JS/Python 语法与编译检查通过；59 项单元测试通过；敏感信息扫描无匹配；九个导航页面真实点击回归通过；结果/对比工作流和证据入口保持可用。
- 部分完成：本批次浏览器窗口未能实际切换到请求的 `1440x900` 或 `390x844`，仅记录当前真实 `1280x720`；响应式尺寸的既有证据继续引用批次 211，未在本批次重复宣称。
- 未完成/暂缓：openKylin VM 同步与 VM 端复核、真实第三方 Agent 调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务仍按既有记录暂缓。
- 客观阻塞：当前浏览器控制通道保持 `1280x720`，视口覆盖调用未改变实际窗口尺寸；无本地代码或测试阻塞。VM 同步继续遵循用户此前“等待明确同步”要求。
- 待确认假设：后续改动继续只在本地工作区生效；`model / wrapper / simulated` 来源标识仍代表证据来源分类，不证明模型原生长期记忆状态。
- 下一轮唯一最高优先级：在用户明确允许同步后，将本地工作台 UI 修订同步到 openKylin VM，并执行 VM 端服务启动、页面职责、Evidence 下钻、响应式与凭据安全复核；同步前保持本地-only。

### 批次 214：本地工作台反向收敛 UI（2026-09-13）

- 本批次范围：针对 AI-generated UI 感进行反向处理，减少英文 kicker、卡片边界、彩色标签和解释性文案；保留现有页面职责、Agent 选择、结果/证据工作流、CLI、后端 API、结果格式和凭据安全边界。仅修改本地工作区，未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 修改文件：`kmb/web/index.html`（移除 Sidebar 的 `WORKSPACE/CONFIGURATION` 分组标题和顶部 `OPENKYLIN / LOCAL WORKBENCH`、`WORKSPACE` 标签）；`kmb/web/app.js`（Agent 下拉选项仅显示档案名并保留 Provider 分组；Agent 元数据压缩为 Provider/Model/Mode 单行；新建评测、评测任务、Agent 管理和运行前检查移除模板化英文标题与冗余说明；Inspector section kicker 不再渲染；结果上下文标签改为中文）；`kmb/web/styles.css`（新增 quiet workbench 覆盖层：普通 section 使用分割线、去除普通 panel/card 边框和背景、VS 分隔缩小、mode/source 改为低对比文字、蓝色仅保留交互与重点状态、Agent A 结果色降为中性灰蓝、移动窄屏保持单列和无溢出）。
- 实际命令与退出码：`node --check kmb/web/app.js` `0`（`runs/workbench-local/ui-reverse-214/js-check.log`、`js-check.exitcode`）；`python -m py_compile kmb/workbench.py kmb/cli.py` `0`（`py-compile.log`、`py-compile.exitcode`）；`python -m unittest discover -s tests -v` `0`，共 `59` 项通过（`unit-tests.log`、`unit-tests.exitcode`）；敏感信息扫描 `rg` 退出码 `1`（无匹配为 rg 语义），状态 `clean`（`secret-scan.log`、`secret-scan.exitcode`、`secret-scan.status`）。
- 浏览器验证：本地服务 `http://127.0.0.1:8765/` 真实点击检查总览、新建评测、评测任务、运行历史、对比分析、结果中心、Agent 管理、API / 模型配置、系统设置；当前 CUA 实际视口 `526x698`，九页 `documentElement.scrollWidth=511`，未发现横向溢出；可见英文 kicker 数量为 `0`；Agent 选择器分组为 `Grok`、`DeepSeek`、`其他 API / 本地配置`，选项仅显示配置档案名；结果中心→对比分析导航和动态 Inspector 可用；浏览器控制台错误为空。浏览器证据：`runs/workbench-local/ui-reverse-214/browser-verification.json`。
- 结果与安全：页面结果仍来自本地 `runs/` 实际文件，未新增或伪造运行数据；页面未读取、写入、显示或保存完整 API Key；来源 `model/wrapper/simulated/runner`、失败状态和证据入口保持原语义。
- 已完成：本地工作台视觉反向收敛；英文模板标题、普通卡片边界和非必要色彩明显减少；Agent 选择器与结果/对比工作流保持兼容；59 项回归测试、语法/编译检查和敏感扫描通过；九个导航页面真实交互回归通过。
- 部分完成：本批次实际浏览器视口为 `526x698`，未生成媒体；更宽桌面断点沿用既有 CSS 证据，未在本批次重复截图；本地 Windows 页面不能替代 openKylin VM 验证。
- 未完成/暂缓：openKylin VM 同步与 VM 端复核、真实第三方 Agent 调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务继续按既有记录暂缓。
- 客观阻塞：无本地实现或测试阻塞；VM 同步继续遵循用户“等待明确同步”要求。
- 待确认假设：`526x698` 为当前 Codex in-app browser 实际可观测尺寸；本批次未将其表述为 390px 或 1440px 独立实测；CSS 断点仍覆盖既有桌面尺寸。
- 证据汇总：`runs/workbench-local/ui-reverse-214/verification-summary.json`、`browser-verification.json` 及同目录命令日志/退出码文件。
- 下一轮唯一最高优先级：继续保持本地-only，等待用户明确同步后再将 `kmb/web/index.html`、`kmb/web/app.js`、`kmb/web/styles.css` 同步到 openKylin VM 并执行 VM 端页面、服务和凭据安全复核。

#### 批次 214 补充：窄窗口单列回归（2026-09-13）

- 发现并修正：末端 quiet workbench 样式覆盖了原有移动断点，窄窗口可能继续使用三列 Agent 轨道；`kmb/web/styles.css` 新增 `max-width:680px` 下 `.agent-compare-grid { grid-template-columns: 1fr; }`，保留 Agent 之间的分割线布局。
- 实际验证：本地浏览器 `http://127.0.0.1:8765/` 实测 `526x698`，新建评测页计算后的 Agent 网格为单列 `476.667px`，`documentElement.scrollWidth=511`，无横向溢出；Agent 选项仍为按 Provider 分组且仅显示配置档案名；可见英文 kicker 为 `0`。结果记录追加在 `runs/workbench-local/ui-reverse-214/browser-verification.json`。
- 视觉计算样式复核：`.workspace-surface` 的计算边框为空（由内容分割线承担层级），普通 `.button` 背景为透明；输入框、表格和状态控件仍保留既有交互边界。
- 追加命令与退出码：`node --check kmb/web/app.js` `0`（`postfix-js-check.log`、`postfix-js-check.exitcode`）；`python -m unittest discover -s tests -v` `0`，`59` 项通过（`postfix-unit-tests.log`、`postfix-unit-tests.exitcode`）。
- 服务资源复核：`GET /`、`/app.js`、`/styles.css`、`/api/configs`、`/api/suites`、`/api/system`、`/api/runs?limit=1` 均返回 HTTP `200`；记录见 `runs/workbench-local/ui-reverse-214/http-check.json`。
- 证据结构复核：`python -m json.tool runs/workbench-local/ui-reverse-214/browser-verification.json` 与 `verification-summary.json` 均退出码 `0`。
- 状态：窄窗口布局修正已完成；未同步 VM、未调用真实第三方 API、未录制媒体。下一轮最高优先级仍为等待用户明确同步后执行 VM 端复核。

### 批次 215：本地工作台用户可见文案中文化收尾与浏览器复核（2026-09-13）

- 本批次范围：仅处理 `kmb/web/index.html` 与 `kmb/web/app.js` 的用户可见中文化和属性提示一致性；不改变评测逻辑、数据结构、CLI 参数、文件名、API 行为或既有视觉布局。未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 扫描范围：前端正文节点、标题、按钮、`title`、`aria-label`、`placeholder`、导航、状态、表格、图表、空状态、运行记录、结果/证据入口和报告链接；逐页检查总览、新建评测、评测任务、运行历史、对比分析、结果中心、智能体管理、API / 模型配置、系统设置。
- 修改文件：`kmb/web/app.js`。新增 `normalizeUiSpacing`，正文节点与属性提示共用中文空格归一化，修复 `双 智能体`、`主 智能体`、`对比 智能体`、`智能体 管理`、`开始双 智能体 评测` 等显示；保留原始 Agent/Provider/Model、运行 ID、案例 ID、路径、命令和技术字段。
- 新增产物：`runs/workbench-local/ui-localize-215/browser-verification.json`、`browser-verification.pretty.json`、`http-check.json`，以及同目录命令日志和退出码文件。
- 新增/统一术语：`总览`、`新建评测`、`评测任务`、`运行历史`、`对比分析`、`结果中心`、`智能体管理`、`系统设置`；状态统一为`空闲/排队中/准备中/运行中/已完成/部分完成/失败/错误/超时/已停止/未确认`；证据来源统一为`模型/包装层/模拟/运行器`；六维指标统一为`长期保持/记忆调用/动态更新/相近区分/边界识别/任务复用`；套件和基线显示名使用中文并在必要处保留原始标识。
- 合理保留英文：`KylinMemBench`、`openKylin`、`Grok`、`DeepSeek`、`Doubao`、`API`、`CLI`、`HTTP`、`JSON`、`JSONL`、`SHA-256`、`EvidenceEvent`、`Chat Completions`、`Base URL`、`API Key`、模型/配置/套件/运行 ID、路径、环境变量、命令和原始 JSON 字段；这些内容需与接口、日志、文件和外部协议逐字对应。
- 实际命令与退出码：`node --check kmb/web/app.js` 为 `0`（`js-check.exitcode`）；`python -m py_compile kmb/workbench.py kmb/cli.py` 为 `0`（`py-compile.exitcode`）；`python -m unittest discover -s tests -v` 为 `0`，59 项通过（`unit-tests.exitcode`）；`python -m json.tool runs/workbench-local/ui-localize-215/browser-verification.json` 为 `0`（`browser-verification-json.exitcode`）；敏感信息 `rg` 扫描原始退出码为 `1`（无匹配），状态记录为 `clean`（`secret-scan.status`）。
- 服务与接口复核：本地服务 `http://127.0.0.1:8765/`；`/`、`/app.js`、`/styles.css`、`/api/configs`、`/api/suites`、`/api/system`、`/api/runs?limit=1` 均 HTTP `200`（`http-check.json`）。服务继续运行在 Windows 本地环境，未同步 VM。
- 浏览器实际验证：1280x720 下九个导航页面均无整体横向溢出、可见英文模板 kicker 为 `0`、未发现目标中文空格残留；390x844 下九个页面 `scrollWidth` 最大为 `377`，整体无横向溢出，导航按设计可横向滚动。结果中心与对比分析 Tab 为`结果/对比分析/案例/证据/记忆轨迹/日志`；选择 `retention-001` 后案例详情与证据抽屉打开成功，显示 5 条本地 EvidenceEvent，来源为`模拟`，保留原始证据 JSON 和确定性评分说明。
- 凭据保护：页面、属性提示、日志和本批次产物均未显示或保存完整 API Key；敏感扫描无匹配。API 配置页仅显示安全凭据引用和非敏感元数据。
- 已完成：用户可见中文化、属性提示空格归一化、九页导航回归、结果/对比/案例/证据下钻回归、1280x720 与 390x844 实际布局检查、HTTP 资源检查、JSON 结构检查、59 项回归测试和敏感信息扫描。
- 部分完成：本批次浏览器验证在 Windows 本地服务执行；未在 openKylin VM 验证，不能把本批次结果表述为 VM 证据。1440x900 与 1920x1080 的既有证据仍引用批次 211，未在本批次重复宣称。
- 未完成/暂缓：openKylin VM 同步与 VM 端复核、真实第三方 Agent 调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务继续保持既有状态。
- 客观阻塞：无本地代码、测试或服务阻塞；VM 同步仍须等待用户明确指令。敏感扫描仅覆盖列出的常见模式，不能替代实际凭据轮换和第三方条款人工确认。
- 待确认假设：本批次以用户可见文案为范围；模型名、协议名、路径、ID、命令和原始字段的英文保留不视为未翻译残留；历史运行缺失字段继续显示`未记录/—`，不推断为零。
- 下一轮唯一最高优先级：继续保持本地-only，等待用户明确同步后，将 `kmb/web/index.html`、`kmb/web/app.js`、`kmb/web/styles.css` 同步到 openKylin VM，并执行 VM 端服务、页面、Evidence 下钻、响应式与凭据安全复核。

#### 批次 215 补充：双智能体分隔文案与最终证据汇总（2026-09-13）

- 发现并修正：新建评测双智能体分隔符 `vs` 属于通用界面文案而非技术标识，已在 `kmb/web/app.js` 改为`对比`；浏览器实测新建评测页无英文 `vs` 残留且无横向溢出。
- 最终产物：`runs/workbench-local/ui-localize-215/verification-summary.json`、`verification-summary.pretty.json`、`postfix-js-check.log`、`postfix-js-check.exitcode`、`postfix-unit-tests.log`、`postfix-unit-tests.exitcode`、`postfix-secret-scan.log`、`postfix-secret-scan.exitcode`、`postfix-secret-scan.status`；JSON 校验退出码为 `0`。
- 最终复核：`node --check kmb/web/app.js` 为 `0`；`python -m unittest discover -s tests -v` 为 `0`，59 项通过；敏感扫描无匹配，原始 `rg` 退出码为 `1`，状态为 `clean`；浏览器控制台错误为 `0`。
- 状态：本地中文化批次已完成；未同步 VM、未调用真实第三方 API、未录制媒体。下一轮最高优先级保持为等待用户明确同步后执行 openKylin VM 端服务与页面复核。

### 批次 216：结果中心重复导航移除与交互复核（2026-09-13）

- 本批次范围：仅修复结果中心页面下方重复导航；不改变评测逻辑、数据结构、CLI、报告、评分、证据链、Agent 配置或其他页面。未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 根因与修改：顶部六个 Tab 由 `resultTabs("result")` 在 `resultDashboardHeader()` 中生成；下方重复的`继续查看 / 对比分析 / 案例 / 证据 / 记忆轨迹 / 日志`由 `renderResultDashboard()` 末尾额外拼接的 `.result-entry-points` 生成。已从 `kmb/web/app.js` 删除该额外模板，并从 `kmb/web/styles.css` 删除其专用样式，未留下占位空间。
- 修改文件：`kmb/web/app.js`、`kmb/web/styles.css`。保留 `resultTabs()`、`data-result-tab` 处理器和侧边栏导航不变。
- 实际命令与退出码：`node --check kmb/web/app.js` 为 `0`（`runs/workbench-local/ui-result-nav-216/js-check.log`、`js-check.exitcode`）；`python -m py_compile kmb/workbench.py kmb/cli.py` 为 `0`（`py-compile.log`、`py-compile.exitcode`）；`python -m unittest discover -s tests -v` 为 `0`，59 项通过（`unit-tests.log`、`unit-tests.exitcode`）；对 `.result-entry-points` 的精确静态检索无匹配，原始 `rg` 退出码为 `1`（`no-duplicate-nav-class.exitcode`）；`python -m json.tool` 验证浏览器证据为 `0`（`browser-verification-json.exitcode`）；`python -m kmb.cli --help` 与 `python -m kmb.cli list-cases --help` 均为 `0`。
- 服务与接口复核：本地服务 `http://127.0.0.1:8765/`；`/`、`/app.js`、`/styles.css`、`/api/runs?limit=1`、`/api/configs`、`/api/suites`、`/api/system` 均 HTTP `200`（`runs/workbench-local/ui-result-nav-216/http-check.json`）。
- 浏览器实际验证：结果中心在 1280x720 视口下只存在 1 组 `.result-tabs`、6 个顶部 Tab，底部 `.result-entry-points` 数量为 `0`，`继续查看`数量为 `0`；六个顶部 Tab 逐一点击后活动项依次为`结果/对比分析/案例/证据/记忆轨迹/日志`，每次 Tab 数量仍为 `6`、重复导航为 `0`、无横向溢出。390x844 下顶部 Tab 数量为 `6`、重复导航为 `0`、`继续查看`不可见、整体无横向溢出（`browser-verification.json`）。
- 控制台与安全：浏览器控制台错误列表为空；本批次未读取、写入或显示 API Key、密码或令牌。页面继续使用本地真实运行结果和运行 ID，未生成虚构结果。
- 已完成：删除结果中心下方重复导航及专用样式；保留顶部六个 Tab 全部功能；桌面/窄窗口布局、CLI 帮助、HTTP 资源、JSON 证据、语法编译和 59 项回归测试均通过。
- 未完成/暂缓：openKylin VM 同步与 VM 端复核、真实第三方 Agent 调用、系统级场景、许可证负责人确认、视频/截图/图像任务继续保持既有状态。
- 客观阻塞与待确认假设：无本地代码、测试或服务阻塞；本批次未改变其他页面，VM 同步仍须等待用户明确指令。结果页中的“继续查看”可能作为其他上下文自然语言出现，但结果中心底部导航组件已完全移除。
- 证据路径：`runs/workbench-local/ui-result-nav-216/browser-verification.json`、`browser-verification.pretty.json`、`runs/workbench-local/ui-result-nav-216/http-check.json` 及同目录命令日志和退出码文件。
- 下一轮唯一最高优先级：继续保持本地-only，等待用户明确同步后，将当前前端修订同步到 openKylin VM，并执行 VM 端服务、页面和凭据安全复核。

#### 批次 216 补充：结果 Tab 上下文保持（2026-09-13）

- 浏览器复核：六个顶部 Tab 依次点击后，活动项正确切换，Tab 数量保持 6，底部重复导航保持 0；当前运行 ID `wb-20260909-213629-31c230a1` 在 Tab 工作流中保持不变。证据已写入 `runs/workbench-local/ui-result-nav-216/browser-verification.json` 的 `context` 字段，并通过 JSON 校验。
- 状态：本批次结果中心导航修复及上下文保持验证完成；未同步 VM、未录制媒体。下一轮最高优先级仍为等待用户明确同步后执行 openKylin VM 端复核。

### 批次 217：结果中心与对比分析合并为单一结果工作区（2026-09-13）

- 本批次范围：按产品架构要求，将原独立“对比分析”导航和结果页面合并为唯一“结果中心”工作区；不改变评测逻辑、数据结构、CLI、报告、评分、证据链、Agent 配置或 API 行为。仅修改本地工作区，未同步 openKylin VM，未调用真实第三方 API，未录制视频、截图或其他媒体。
- 修改文件：\`kmb/web/index.html\` 删除 Sidebar 的 \`data-view="compare"\` 独立入口；\`kmb/web/app.js\` 删除独立 \`compare\` 视图注册和旧 \`renderCompare\`/\`renderResultWorkspace\` 重复工作区，所有结果 Tab 点击统一保持 \`state.view = "results"\`；结果 Tab 用户名称统一为“概览 / 对比 / 案例 / 证据 / 记忆轨迹 / 日志”；结果中心概览新增紧凑六维能力表、辅助雷达和“差异最大的项目”，差异项目点击进入同一工作区的“案例”Tab；结果中心顶部操作保留“切换运行”，新增“开始新的评测”；\`kmb/web/styles.css\` 增加结果分析网格、窄屏可收缩列和雷达尺寸约束，修复 390px 结果表横向溢出。
- 页面职责：左侧 Sidebar 现在仅保留总览、新建评测、评测任务、运行历史、结果中心、智能体管理、API / 模型配置、系统设置；结果中心内部单一 Tab 工作流负责概览、对比、案例、证据、记忆轨迹和日志；旧独立对比页面不再可从导航或路由进入。
- 实际命令与退出码：\`node --check kmb/web/app.js\` 退出码 \`0\`（\`runs/workbench-local/ui-result-workspace-217/js-check.log\`、\`js-check.exitcode\`）；\`python -m py_compile kmb/workbench.py kmb/cli.py\` 退出码 \`0\`（\`py-compile.log\`、\`py-compile.exitcode\`）；\`python -m unittest discover -s tests -v\` 退出码 \`0\`，共 \`59\` 项通过（\`unit-tests.log\`、\`unit-tests.exitcode\`）；\`python -m kmb.cli --help\` 与 \`python -m kmb.cli list-cases --help\` 均退出码 \`0\`（对应 \`cli-help.exitcode\`、\`cli-list-cases-help.exitcode\`）；结果和汇总 JSON \`python -m json.tool\` 校验退出码 \`0\`（\`browser-verification-json.exitcode\`、\`verification-summary-json.exitcode\`）；独立 compare 路由静态扫描无匹配。
- 服务与接口复核：本地服务 \`python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .\`，地址 \`http://127.0.0.1:8765/\`；\`/\`、\`/app.js\`、\`/styles.css\`、\`/api/runs?limit=1\`、\`/api/configs\`、\`/api/suites\`、\`/api/system\` 均返回 HTTP \`200\`，记录见 \`runs/workbench-local/ui-result-workspace-217/http-check.json\`。
- 浏览器实际验证：本地工作台真实访问结果中心，当前运行 ID \`wb-20260909-213629-31c230a1\` 在所有 Tab 中保持；1440x900 下 Sidebar 无“对比分析”，结果中心有且仅有 6 个 Tab；390x844 下逐一点击“概览 / 对比 / 案例 / 证据 / 记忆轨迹 / 日志”，活动 Tab、页面内容和动态 Inspector 均正确切换，差异项目点击后进入“案例”Tab；两个视口正向横向溢出均为 \`0\`，控制台错误为 \`0\`。完整证据：\`runs/workbench-local/ui-result-workspace-217/browser-verification.json\`。
- 已完成：独立“对比分析”Sidebar 入口删除；结果中心单一工作区和六个内部 Tab 生效；概览包含总分、差值、胜者、成功率、案例数、平均耗时、失败案例、六维能力、雷达和差异项目；对比/案例/证据/记忆轨迹/日志保持真实结果与证据下钻；CLI、后端和数据格式未变；语法、编译、59 项回归、HTTP、JSON 和浏览器验证通过。
- 部分完成：浏览器验证为 Windows 本地服务；未在 openKylin VM 同步或复核，不能将本批次页面结果表述为 VM 证据；未执行真实第三方 Agent 调用。
- 未完成/暂缓：openKylin VM 同步、真实新增提供商调用、非 OpenAI-compatible 专用适配器、系统级场景、许可证负责人确认、视频/截图/图像任务继续按既有记录暂缓。
- 客观阻塞与待确认假设：无本地代码、测试或服务阻塞；用户此前要求同步前保持本地-only，因此本批次不执行 VM 同步。结果中的 \`reference / flawed\` 与 Evidence 来源继续按真实本地运行元数据展示，不证明模型原生长期记忆能力。
- 证据路径：\`runs/workbench-local/ui-result-workspace-217/browser-verification.json\`、\`verification-summary.json\`、\`http-check.json\` 及同目录命令日志和退出码文件。
- 下一轮唯一最高优先级：继续保持本地-only，等待用户明确同步后，将当前 UI 修订同步到 openKylin VM 并执行 VM 端服务、单一结果工作区、Evidence 下钻、响应式与凭据安全复核。
