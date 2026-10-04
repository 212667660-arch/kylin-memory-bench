# 修改台账（mimo.md）

> 路径固定：`docs/mimo.md`。面向本仓库所有 AI / 协作会话。

## 协作原则（强制）

1. **本文件职责**  
   项目修改台账：登记「已经修改的」与「将要修改的」；写清改了哪里；供其他 AI 核对。

2. **改完必更新（强制）**  
   任何 AI / 协作会话，**只要对本仓库有任何写入修改**（代码、文档、配置、脚本、测试），**在向用户交付/结束前必须更新本文件**。  
   - 将本次「计划中」更新为实际状态，并写清**改动点路径**。  
   - 若只计划未执行，只维护「计划中」。  
   - **禁止**交付时台账仍停留在改动前状态。  
   - 无仓库写入的任务可标注「本次不适用」，但不得删除既有条目。

3. **先登记再动手**  
   动手前写「计划中」（意图、路径、边界、验收）；紧急修复可在同一交付内补登记，不得省略。

4. **只改已登记范围**  
   未写明的模块默认未授权，不得擅自扩大。

5. **需求与实现分离**  
   「意图」= 目标；「改动点」= 文件/函数/选择器级落点。

6. **可核对**  
   验收写命令、现象或截图路径；禁止只写「更好了」。

7. **不替代其他文档**  
   本台账 ≠ `CHANGELOG.md` ≠ `docs/release-freeze.md` ≠ `tasks/todo.md`。

8. **历史只增不删**  
   作废用状态标记，不覆盖原文。

9. **表述边界强制**  
   登记 Agent / 配置 / 评测相关改动时必须按「表述边界」分类，禁止夸大（见下节）。

---

## 表述边界（强制）

### 两层能力

**A. 只为了「能调用 API」——通常够用：**

- `base_url`（如 `https://api.deepseek.com`）
- API Key（**只放环境变量，不进仓库**）
- `model`（如 `grok-4.6` / `deepseek-flash`）
- 接口路径（一般 `/chat/completions`）

可跑通 HTTP 适配器，得到对比和雷达图。

**B. 为了「按文档评长期记忆」——只有 key + base_url 不够：**

PDF/文档要求基于**真实运行证据**自动评分，并覆盖六类记忆能力。纯 API 只能看到回答文本：

- 看不到是否真的 **写入 / 更新 / 调用 / 抑制** 记忆
- 当前真实 HTTP 轨道 `native_memory_events=0`
- **普通文本不能推断成记忆写入或读取**

还需要至少一种**可观测证据**：

| 方式 | 说明 |
|------|------|
| 包装层 / memory controller | 外部记忆状态机 + 沙箱动作，事件标 `source=wrapper` |
| 进程 Agent | 子进程按协议吐 JSONL（如 `kylinbot-process`） |
| Agent 原生导出 | 对方给出记忆/工具轨迹，映射为统一 `EvidenceEvent` |

### 结论表

| 目标 | 只给 key + base_url？ |
|------|------------------------|
| 连通、跑通 CLI、出雷达图 | 可以 |
| 符合「长期记忆自动化评测」验收 | **不行**，还差记忆证据 |

文档里的「导入不同智能体配置」= **配置接入 + 证据协议**；Key/Base URL 只是配置接入的第一步。

### 登记规则

- 凡登记涉及 Agent / API / 评测接入的条目，必须标明属于：**仅连通** 还是 **具备可观测记忆证据**（并写 source 类型）。
- 禁止：仅有 key + base_url 时写成「已验收长期记忆评测」或「已证明模型原生长期记忆」。
- 雷达图 / CLI 跑通不能替代证据验收表述。

---

## 状态与模板

状态：`计划中` | `进行中` | `已完成` | `作废` | `回滚`

```markdown
### [YYYY-MM-DD] 简短标题
- **状态**: 计划中 | 进行中 | 已完成 | 作废 | 回滚
- **意图**: 一句话
- **改动点**:
  - `路径/文件` — 改了什么
- **接入层级**（若涉及 Agent/API/评测）: 仅连通 | 具备可观测证据（source=…） | 不适用
- **保留/禁止**: 可选
- **验收**: 如何确认
- **本次是否已同步本台账**: 是 | 否 | 不适用（有仓库写入时交付前必须为「是」）
```

---

## 台账条目（只增不删）

### [2026-09-16] 建立修改台账 docs/mimo.md
- **状态**: 已完成
- **意图**: 固定协作登记入口，强制改完必更新与表述边界
- **改动点**:
  - `docs/mimo.md` — 新建/更新本文件（原则、表述边界、模板、历史）
- **接入层级**: 不适用
- **保留/禁止**: 不改业务代码；不建 `AGENTS.md`；不改 CHANGELOG / release-freeze / todo
- **验收**: 本文件存在且含文首强制原则与表述边界专节
- **本次是否已同步本台账**: 是

### [2026-09-16] 本会话既往写入（回溯登记）
- **状态**: 已完成
- **意图**: 将本会话已落盘的仓库修改登记入台账；后续交付仍须先写「计划中」再动手
- **改动点**:
  - `kmb/web/styles.css` — UI Token/布局/边界/下拉；Codex++ 对齐深色工作台
  - `kmb/web/index.html` — 侧栏分组、Topbar（标题+副标题+状态芯片）
  - `kmb/web/app.js` — 页面 chrome、自定义 select（fixed 浮层）、Provider 列表等
  - `kmb/models.py` — 证据来源增加 `process`（系统级分类）
  - `suites/core-zh-expanded.yaml` — 新建，六类扩展 18 案例
  - `suites/adversarial/extended.yaml` — 新建，冲突/相近/噪声/敏感/跨任务各 3 条
  - `scripts/openkylin_ecosystem_agent.py` — 新建，进程适配器
  - `configs/agent-kylinbot-process.yaml` — 新建，command 配置
  - `scripts/run_offline_demo.sh` — 新建/更新，无凭据双 Agent 对比 demo
  - `scripts/register_openai_agent.py` — 新建，按 key 环境变量 + base_url + model 生成包装配置（脚本已写；CLI 子命令是否接线：待核实）
  - `docs/judge-reproduction-card.md` — 新建/更新评委复现卡
  - `tasks/todo.md` / `README.md` / `docs/release-freeze.md` — 口径对齐（本机 P1；实机后置）
- **接入层级**:
  - `kylinbot-process`：具备可观测证据（source=process，系统级，非模型原生记忆）
  - reference/flawed：离线基线（source=simulated）
- **保留/禁止**: 密钥不入库；不夸大「已验收长期记忆」
- **验收**: 曾通过 unittest 59、`run_offline_demo` 退出码 0 等（以当时交付说明为准）
- **本次是否已同步本台账**: 是

### [2026-09-16] 真实 API 连通与核心套件对比（运行记录）
- **状态**: 已完成
- **意图**: 使用环境变量密钥做本机真实双 Agent 对比
- **改动点**:
  - 运行目录 `runs/real-api-20260916/` — Grok `grok-4.6` vs DeepSeek（`deepseek-v4-flash`→映射 `deepseek-flash`），seed 42
  - 密钥仅进程环境变量，未写入仓库
- **接入层级**: 仅连通（HTTP 文本可观测；`native_memory_events=0`，非长期记忆验收）
- **验收**: `verify_run --strict` 两侧通过；`comparison.html`/雷达存在；结果内无密钥
- **本次是否已同步本台账**: 是

### [2026-09-16] 工作台新增 API 配置自动生成三件套
- **状态**: 已完成
- **意图**: 提交 profile 后写出 http / memory_controller / memory_disabled 三份 YAML，与 `scripts/register_openai_agent.py` 对齐
- **改动点**:
  - `kmb/workbench.py` — `create_config`：三路径预检、原子写三份、失败回滚；响应含 `configs`/`generated`/`note`
  - `kmb/web/app.js` — 成功提示列出三件套与「http 仅连通；memory/no-memory 包装轨」边界
  - `tests/test_workbench.py` — 断言三文件与 type、generated 类型集合
  - `docs/workbench.md` — 三件套表与接入层级
  - `docs/mimo.md` — 本条
- **接入层级**: http=仅连通；memory_controller/no-memory=具备可观测证据（source=wrapper）
- **保留/禁止**: 不写密钥；不覆盖已有文件
- **验收**: `python -m unittest discover -s tests` 59 OK；HTTP POST `/api/configs` 返回 201 且三份 YAML type 正确；重复 POST 409；烟测文件已删
- **本次是否已同步本台账**: 是

### [2026-09-16] Grok-memory × DeepSeek-memory 包装轨真实对比（core-zh）
- **状态**: 已完成
- **意图**: 真实双 API + 包装层跑核心六类套件并归档
- **改动点**:
  - 运行目录 `runs/real-api-wrapper-20260916/results/` — comparison、两侧 result/evidence/雷达
  - 旁路 `runs/real-api-wrapper-20260916/compare.stdout.log`、`cli.exitcode`（0）
- **接入层级**: 具备可观测证据（source=wrapper；native_memory_events=0；mode=system_level_wrapper_assisted）
- **保留/禁止**: 不得写成「模型原生长期记忆已验证」；密钥仅环境变量
- **验收**: compare 退出码 0；两侧 strict 通过（各 72 事件）；wrapper_memory_events=13；总分均 86.11；归档无明文密钥
- **本次是否已同步本台账**: 是

### [2026-09-16] CLI register-agent 接线（与脚本共用实现）
- **状态**: 已完成
- **意图**: `python -m kmb.cli register-agent` 生成三件套，避免与脚本两套逻辑
- **改动点**:
  - `kmb/register.py` — 新建公共实现
  - `kmb/cli.py` — 新增 register-agent
  - `scripts/register_openai_agent.py` — 调用 kmb.register
  - `tests/test_register_agent.py` — 5 项用例
  - `README.md` / `docs/workbench.md`
- **接入层级**: 不适用（注册工具）
- **验收**: `--help` 可用；全量 unittest 64 OK
- **本次是否已同步本台账**: 是

### [2026-09-16] A+B 原生/可观测记忆对比设计 + R0 口径降级
- **状态**: 已完成
- **意图**: 文档化 A/B/C 轨、门禁、选型、导出规格、防送分、B 轨机制、runbook、并排模板；包装叙事降为 C 轨
- **改动点**:
  - `docs/native-memory-compare.md` — 新建完整设计与门禁；§11 当前 A=`candidate-pending`，正式主结论未开放
  - `README.md` — R0：包装/三件套为 C 轨，主结论走 A+B 门禁
  - `docs/workbench.md` / `docs/judge-reproduction-card.md` — R0 与标准句
  - `tasks/todo.md` — A+B 门禁任务与 R0 说明
  - `docs/release-freeze.md` — wrapper runs 保留为 C 轨，非主结论
  - `docs/mimo.md` — 本条
- **接入层级**: C 轨 wrapper 保留；A/B 门禁前不写 ready
- **保留/禁止**: 未删 wrapper/register/no-memory/configs/历史 runs；未伪造 A 轨 Agent 或 native_memory_events>0
- **验收**: 设计文档完整；相关配置文件仍在；`unittest discover` 退出码 0
- **本次是否已同步本台账**: 是

### [2026-09-16] B 轨实现：两套记忆模块 + 工具决策 + 证据导出
- **状态**: 已完成
- **意图**: 落地 B 轨骨架；决策归工具层；甲/乙策略可区分
- **改动点**:
  - `kmb/memory_modules.py` — ExactKVMemory / SimilarityMemory
  - `kmb/agents.py` — MemoryToolAgent、DecisionTextBackend、type `memory_tool`
  - `kmb/models.py` — source `memory_layer`
  - `configs/agent-b-memory-kv.yaml`、`configs/agent-b-memory-similar.yaml`
  - `suites/native/decision-core.yaml` — 人话套件
  - `tests/test_memory_tool.py` — 模块/Agent/配置/套件用例
  - `docs/native-memory-compare.md` §11 — B 骨架状态
- **接入层级**: B 骨架（memory_layer 可观测）；非 A/B 正式主结论 ready
- **保留/禁止**: wrapper 未删；未按 suite YAML 预写记忆库
- **验收**: unittest 通过；compare 冒烟 KV 91.67 vs Similar 100.0（边界维可区分）；`memory_layer` 事件存在
- **本次是否已同步本台账**: 是

### [2026-09-18] 迁入 openKylin VM + 无 API 验收
- **状态**: 已完成（含 1 项 unittest 平台失败，已如实记录）
- **意图**: Windows 仓库同步到 VM 数据盘新目录，install_local + 探针/单测/validate（无云 API）
- **改动点**:
  - 远端 `REMOTE_ROOT=/data/usershare/kylin-memory-bench-20260918`（`/dev/sda4` → `/data`，非系统盘）
  - 打包 `kmb-src-20260918.tar.gz`，SHA256 `926AF68E7BA50A8918530D593A60D39FDBD2F36A63A890B60932B53C11399E23`
  - 排除 `runs/`、`.venv*`、`__pycache__`、密钥
  - 宿主归档 `docs/migrate-openkylin-20260918/`（含 SUMMARY.md 与日志）
  - `tasks/todo.md` — 迁入无 API 验收说明
  - `docs/mimo.md` — 本条
- **接入层级**: 不适用（迁移验收）；非真实 API / 非 A/B 主结论
- **SSH（脱敏）**: `Cisyam@192.168.182.129:2222`，密钥 `~/.ssh/openkylin_vm_ed25519`
- **验收退出码**:
  - env_probe --require-openkylin：**0**，`checks.openkylin.ok=true`（openKylin 2.0 SP2）
  - install_local.sh：**0**，`.kmb-venv` 在项目内，import kmb 成功
  - validate --strict core-zh：**0**
  - unittest：**1**（71 项，1 失败：`test_safe_executor_records_real_and_unexecuted_boundaries`，posix 期望 recalls>=3 实测 2，平台/KARE 场景）
- **保留/禁止**: 未覆盖历史 validation 目录；未迁 runs/；未调用云 API；未删 wrapper
- **本次是否已同步本台账**: 是

### [2026-09-18] Token Center 配置模板 + 生态 Agent 导出规格
- **状态**: 已完成
- **意图**: openKylin Token Center http 模板；KylinBot/OpenClaw command 导出字段与门禁口径
- **改动点**:
  - `configs/agent-openkylin-token.yaml` — http 模板，无密钥，`OPENKYLIN_TOKEN_API_KEY`
  - `configs/agent-kylinbot-command.yaml.example` / `agent-openclaw-command.yaml.example` — exporter 占位
  - `docs/openkylin-token-center.md` — URL/模型/申领/额度未公开/run 示例/调研链接
  - `docs/ecosystem-agent-export.md` — 级别对照、command 职责、字段清单、门禁、skills/MCP 口径
  - `docs/evidence-protocol.md` / `README.md` — 交叉引用
  - `tests/test_openkylin_ecosystem_configs.py`
  - `docs/mimo.md` — 本条
- **接入层级**: Token http=仅连通设计；command 包装=exporter-pending（stand-in 未删）
- **调研**: `research/openkylin-agent-ecosystem/REPORT.md`
- **保留/禁止**: 未实测 Token Center/KylinBot；未删 wrapper/stand-in；无密钥入库；未编造额度
- **验收**: 相关 unittest 通过；discover 退出码 0
- **本次是否已同步本台账**: 是

### [2026-09-18] openKylin 3.0 AgentOS VM 安装与安装级验收
- **状态**: 作废/阻塞（安装未完成）
- **意图**: 核对 ISO/VM → 启动 → 安装 → 客户机验收（不迁项目）
- **改动点**:
  - `D:\openKylin-VM-3.0-AgentOS\openKylin-3.0-AgentOS.vmx` — 修正错误路径（`D:\\\\`→`D:\`）、`scsi-hardDisk`、固件 `efi`→`bios`；备份 `.bak-paths`
  - `docs/openkylin-3.0-vm-setup-20260918.md` — 阻塞与解除步骤
  - `docs/mimo.md` — 本条
- **ISO**: 大小 7435438080，CD001 已核验
- **硬件配置**: 4 vCPU / 8GB / 系统盘 80GB sparse / 数据盘 60GB sparse（未安装、未挂载验收）
- **验收结果**: ISO/VMX 文件就绪；**power-on 失败**（日志 `IOPL_Init: Hyper-V detected by CPUID`；`vmrun list` 仍为 0）
- **SSH**: 无（系统未装成）
- **保留/禁止**: 未迁项目；未把 2.0 冒充 3.0；无密码/私钥入库
- **口径**: **仅**配置校正；**不得**称 3.0 安装完成或评测已验收
- **后续**: 管理员关闭 Hyper-V/VirtualMachinePlatform 并重启后，再执行 `vmrun start ... gui` 与安装向导
- **本次是否已同步本台账**: 是

### [2026-09-18] openKylin 3.0 AgentOS VM 安装与安装级验收（续）
- **状态**: 进行中（power-on 成功；GUI 安装待人工完成）
- **意图**: 解除 Hyper-V/vmx 阻塞并启动 3.0 安装环境
- **改动点**:
  - 关闭 VirtualMachinePlatform / HypervisorPlatform（用户管理员操作 + 重启）
  - `openKylin-3.0-AgentOS.vmx` — 路径修复、重建 vmdk、**virtualHW 18**、2 vCPU/4GB、`guestOS=ubuntu-64`、单系统盘启动
  - `docs/openkylin-3.0-vm-setup-20260918.md` — 状态更新
- **验收**: `vmrun list`=1；日志显示 BIOS + 80G SCSI + 720x400；**尚未**进入已安装系统
- **口径**: 仅「安装环境已启动」；未迁项目、未跑评测
- **本次是否已同步本台账**: 是

### [2026-09-18] 删除本机 openKylin 3.0 下载与虚拟机
- **状态**: 已完成
- **意图**: 清除本任务下载/创建的 3.0 安装介质与 VM 配置
- **改动点**:
  - 删除 `D:\openKylin-VM-3.0-AgentOS\`（vmx、vmdk、install.iso 副本、日志等）
  - 删除 `D:\ISOs\openKylin-Desktop-V3.0-AgentOS-20260905-x86_64.iso`
- **保留/禁止**: 未删除宿主项目仓库；未改业务代码；历史 2.0 目录此前已不存在
- **验收**: 删除后 `Test-Path` VM 目录为 False；`E:\上海开源软件应用创新大赛\README.md` 仍存在
- **口径**: 3.0 安装验收未完成；本次仅为介质/VM 清理，不计入「已验证」
- **本次是否已同步本台账**: 是

---

## 计划中

### [2026-09-18] 测试修复 + A 轨门禁口径 + KylinBot 导出器
- **状态**: 计划中
- **意图**: 修 test_memory_tool；门禁改为「Agent 自有可观测记忆事件」；实现 export_kylinbot_evidence.py；最小门禁实验
- **改动点**:
  - `docs/native-memory-compare.md` — 门禁计数专节
  - `tests/test_memory_tool.py` — 修复
  - `scripts/export_kylinbot_evidence.py` — 新建
  - `configs/agent-kylinbot-command.yaml` — 指向导出器
  - `docs/mimo.md` / 文档口径
- **接入层级**: A 轨=agent-owned observable（process 等）；native_memory_events 单独记录
- **保留/禁止**: 不删 stand-in/wrapper/C 轨；不 commit 除非授权；无密钥
- **验收**: unittest 无 IndentationError；导出器存在；门禁实验结果如实记录
- **本次是否已同步本台账**: 是


---

### [2026-09-19] 补录本轮台账并清理 review 烟测产物
- **状态**: 已完成
- **意图**: 修复本次审阅发现的台账缺失：将 2026-09-19 会话写入同步到 docs/mimo.md，并清理 review 过程产生的临时配置。
- **改动点**:
  - docs/mimo.md — 补录本轮条目并更新为已交付
  - configs/agent-openrouter*.yaml — 删除 review 烟测产物
- **接入层级**: 不适用
- **保留/禁止**: 不删除既有台账历史；不触碰其他业务文件
- **验收**: git status --short 中不再出现 gent-openrouter*.yaml；docs/mimo.md 含本轮登记
- **本次是否已同步本台账**: 是








