# KylinMemoryBench 任务清单

## 必须完成（按依赖排序）

- [x] **T1 数据模型与六类最小用例**
  - 目标：建立声明式案例和统一证据结构，覆盖长期保持、记忆调用、动态更新、相近区分、边界识别、任务复用。
  - 输入：项目上下文包第 2、3、7 节。
  - 产物：`kmb/models.py`、`suites/core-zh.yaml`、`pyproject.toml`。
  - 验收：YAML 可加载；六类能力各至少 1 案例；字段可校验。
  - 风险：范围膨胀；MVP 仅保留必要字段。

- [x] **T2 双 Agent 适配器**
  - 目标：统一 `AgentAdapter`，提供可重复的参考 Agent 与缺陷 Agent 基线。
  - 输入：T1 用例模型。
  - 产物：`kmb/agents.py`。
  - 验收：同输入轨迹稳定；产生对话、记忆、动作证据。
  - 风险：演示基线不等于最终参赛 Agent，需在文档中明确。

- [x] **T3 执行、证据和确定性评分**
  - 目标：执行案例、保存 JSONL 证据、按检查项给出六维分数和失败类型。
  - 输入：T1、T2。
  - 产物：`kmb/runner.py`、`kmb/scoring.py`。
  - 验收：评分仅基于运行事件；理由可追溯；异常/超时可记录。
  - 风险：规则遗漏；每个案例使用显式 checks。

- [x] **T4 CLI 与报告**
  - 目标：实现 `kmb run`、`kmb compare`，输出 JSON、Markdown、SVG 雷达图。
  - 输入：T3。
  - 产物：`kmb/cli.py`、`kmb/report.py`。
  - 验收：一条命令对比两个 Agent，生成多维结果和证据路径。
  - 风险：减少依赖，使用 argparse 和标准库绘图。

- [x] **T5 测试与回归**
  - 目标：自动测试覆盖模型、Agent、评分；CLI 和错误路径执行手动回归。
  - 输入：T1-T4。
  - 产物：`tests/`、测试输出记录。
  - 验收：`python -m unittest discover -s tests` 全绿，CLI/异常路径有实际运行记录。
  - 风险：测试环境差异；避免依赖 pytest。

- [x] **T6 openKylin 运行说明与方案文档**
  - 目标：提供 Debian 系 openKylin 的安装、运行、复现实验说明，记录未实机验证项。
  - 输入：实际命令输出、上下文包硬要求。
  - 产物：`README.md`、`docs/solution.md`、`scripts/run_demo.sh`、样例结果。
  - 验收：新环境可按文档运行；不虚构 openKylin 实机结论。
  - 风险：版本/介质待确认。

## 建议完成

- [x] **T7a** 扩展 adversarial 用例（依赖 T1-T6）。
- [x] **T7b** 增加 HTML 报告、失败统计和证据引用查看（依赖 T1-T6）。
- [ ] **T7c** 证据图谱可视化（当前已有事件引用，尚未实现图谱视图）。
- [ ] **T8** `.deb` 打包、许可证和 CI（依赖 openKylin 版本与仓库决策）。

## 待确认

- [ ] **Q1** openKylin 版本、实体机/虚拟机/官方镜像。
- [x] **Q2** 两款真实参赛模型后端已确定为 Grok 4.6 与 DeepSeek v4 flash；原生 API 与透明包装层证据协议均已运行，包装层来源明确标记。
- [ ] **Q3** 云 API 使用、开源许可证、首版案例规模与语言范围。

## 检查点

- [x] Checkpoint A（T1-T3）：六类案例可执行，证据 JSONL 和逐项评分可生成。
- [x] Checkpoint B（T4-T6）：`run/compare` 闭环可复现，文档和样例结果齐全。

## 赛事可验收推进状态（本阶段）

- [x] R1 扩展对抗数据：新增 `suites/adversarial/core.yaml`，六类能力各 1 个额外案例。
- [x] R2 强化评分：证据引用、状态序列 `write/revise/retain/suppress/reuse`、失败统计。
- [x] R3 重复性与批量执行：运行 ID、时间、seed、重试、失败尝试证据、异常收敛。
- [x] R4 CLI 完善：`validate`、`list-cases`、Replay Agent 配置、参数校验。
- [x] R5 报告增强：离线 HTML 折叠证据、失败明细、跨 Agent 对比雷达图。
- [x] R6 赛事材料：证据协议、环境矩阵、贡献指南、变更记录、演示流程。
- [ ] B1 真实 Agent 接入：Grok/DeepSeek 已完成 API 与透明包装层运行；仍需赛事确认“外部包装层 Agent”是否符合参评定义，以及是否要求模型原生记忆证据。
- [ ] B2 openKylin 实机验证与打包：当前主机未发现可用 openKylin 设备、镜像或虚拟化后端，必须在外部 openKylin 环境完成。

## 本轮阻塞推进记录

- [x] A1 盘点现有 Agent 接口、证据模型、配置和可用运行工具。
- [x] A2 增加 `CommandAgent`、配置校验、外部 Agent 模板和证据协议说明。
- [x] A3 增加环境探针、结果校验、安装/卸载/正式验收脚本。
- [x] A4 完成当前 Windows 本地预检和 CLI 产物校验。
- [x] A5 完成外部事件协议校验、正式验收脚本防误用和本地回归。
- [x] B1 真实 Agent 实际运行：Grok 4.6 与 DeepSeek v4 flash 已完成统一套件真实运行；原生 API 结果在 `runs/real-compare-v2/`，透明包装层结果在 `runs/controller-compare-v2/`。
- [ ] B2 openKylin 实机/虚拟机运行：仍需提供指定版本、架构、镜像或设备；本机探测已确认无法启动。

## 本轮（真实 Agent/API 与 openKylin 阻塞）

- [x] A6 新增 OpenAI 兼容 HTTP 适配器：支持豆包/火山方舟、DeepSeek 等 `/chat/completions` 接口；记录对话、工具调用和 Agent 主动返回的 `kmb_evidence`。
- [x] A7 新增 API 配置模板：`configs/agent-doubao.yaml`、`configs/agent-deepseek.yaml`；认证只从环境变量读取，不写入仓库或报告。
- [x] A8 补充 HTTP 证据协议、接入说明和本地 mock API 回归测试。
- [x] A9 CLI 增加 `--timeout`，允许云端 Agent 按案例设置合理的整体超时，避免把网关延迟误判为行为失败。
- [x] A10 Grok/NewAPI 真实双 Agent 对比：使用统一核心套件、seed 42、重试 1、每案例 180 秒超时，生成 `runs/real-compare/` 并完成严格校验。
- [x] A11 修订动态更新案例输入：明确写出从 Room A 改为 Room B，并在 `runs/real-compare-v2/` 重新完成双 Agent 对比；旧目录保留审计。
- [x] A12 透明长期记忆包装层：统一外部记忆状态机、动作沙箱、模型请求/响应元数据和 `source=wrapper/model` 证据标记。
- [x] A13 包装层双 Agent 真实运行：Grok 4.6 与 DeepSeek v4 flash 各 6 案例、70 条事件，结果位于 `runs/controller-compare-v3/` 并通过严格校验；总分分别 86.11/94.44，wrapper/model 来源明确区分，动作目录按 Agent 隔离。
- [x] A14 项目内虚拟环境与路径隔离：创建 `.venv-kmb-system`，PyYAML 位于虚拟环境 site-packages；新增 `scripts/install_local.ps1`，Linux 脚本固定 TMP/PIP 缓存到项目目录。
- [x] A15 虚拟化能力探测：确认无 QEMU/VirtualBox/VMware/Podman，WSL 仅有停止的 docker-desktop，Docker daemon 未运行；更新环境矩阵和 openKylin 执行清单。
- [x] A16 安装/卸载脚本回归：`install_local.ps1` 在项目内创建临时 venv、CLI 严格校验通过，`uninstall_local.ps1` 已清理临时 venv；正式 `.venv-kmb-system` 保留。
- [ ] B1-HTTP 真实云端运行：原生 API 对比已完成（总分 30.56/38.89）；透明外部记忆控制器对比也已完成（Grok 86.11、DeepSeek 94.44，70 条事件/Agent），但后者的 `memory_*`/`action` 是 wrapper 执行并已显式标记，不能解释为模型原生长期记忆。
- [ ] B2-OKY 实机验证：仍阻塞于 openKylin 版本、架构、设备或镜像，以及 Python/系统包安装权限；本机未发现可用虚拟化后端或 openKylin 介质。

### 当前需要项目负责人提供

1. Grok/NewAPI 参评版本确认（当前默认 `grok-4.6`，可切换 `grok-4.5`）。
2. DeepSeek `deepseek-v4-flash` 已确认可用；无需另行提供模型 ID，除非希望改测其他模型。
3. 两个 Agent 是否能输出记忆写入、更新、抑制、读取事件；若不能，提供 wrapper 或脱敏 JSONL。
4. 轮换已在聊天中暴露的 DeepSeek API Key，并仅在本机设置 `DOUBAO_API_KEY`、`DEEPSEEK_API_KEY` 环境变量。
5. openKylin 版本、x86_64/ARM64、实体机/虚拟机、远程访问或镜像位置，以及安装权限。

### 下一步执行顺序

1. 收到上述信息后填充两个 HTTP 配置并执行 `kmb compare`（统一套件、seed、重试参数）。
2. 校验两份 `evidence.jsonl`、`result.json` 和六维评分；若只有普通文本，标记记忆证据缺失，不补写事件。
3. 在指定 openKylin 环境执行 `scripts/env_probe.py`、安装、`scripts/run_acceptance.sh` 和 `scripts/verify_run.py --strict`。
4. 将真实运行命令、退出码、结果路径和环境矩阵写回 `docs/environment-matrix.md` 与本清单。
