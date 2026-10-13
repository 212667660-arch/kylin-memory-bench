# 修改台账（mimo.md）

> 路径固定：`docs/mimo.md`。面向本仓库所有 AI / 协作会话。

## 2026-10-13 视频镜头外准备（项目侧完成，正式视频由负责人录制）

- 意图：按负责人要求完成录制前可自动执行的准备，留下明确的镜头内操作入口。
- 范围：`docs/demo-script.md`、新增 `docs/video-preparation-20261013.md`、本台账；`runs/video-prep-20261013/`、`dist/video-ready-20261013/` 的准备脚本、状态与稿件；VM 普通用户工作区中的预检、录制目录和快捷入口，以及工作台浏览器临时选择。
- 边界：保持原 openKylin 3.0 与冻结 0.2.2 二进制，不改日常 Agent 记忆；不提前运行镜头内正式评测，不制作正式视频，不发送材料。设备读写测试只做短时空输出探测，不保存桌面/声音内容。
- 验收：两款 Agent 只读预检 ready、blocked 为空、turns_started=0；既有 0.2.2 有效预演 strict 通过并可在工作台回溯；桌面/音频源和编码工具可用；入口脚本语法与只读检查通过；录制说明明确剩余的人声、隐私画面与实际视频操作。
- 实际结果：20:36（北京时间）全部项目侧准备检查通过；新目录 `runs/video-real-20261013-203622/` 仅有预检，正式对话未开始。工作台两款参与者选择、六维预演、案例与证据入口已在浏览器逐项核对；旧搜索将清空以免误选预演。入口 `--check` 及后续 verifier 对既有预演实测通过，不消耗新的真实对话额度。
- 录屏调整：实机是 Wayland，旧 X11 捕获的单帧统计约 99.98% 黑色；只保存像素统计、不保存画面或声音。负责人说明有其他录屏软件，已停止替代工具调查与配置。麦克风源存在、未静音，人声回放和负责人录制画面仍须亲自检查。
- 材料与限制：生成镜头外清单、准备状态和镜头内单命令入口，当前系统 3.0 与冻结 0.2.2 不变。备课说明精确区分禁词规则、目标键检查、原始 conversation 持久化与不可观测模型状态；没有把旧预演冒充新现场结果。正式视频与作品提交未完成。
- 交付核对：20 项准备检查全通过；脚本语法、正常预演校验及无效批次拒绝检查通过。准备 PDF 2 页、分镜/口播 PDF 4 页均渲染检查通过；`dist/video-ready-20261013/` 提供稿件、已部署脚本、状态与界面截图，ZIP SHA-256 为 `6c64091c7047380ea8092a098273b353026d641ea13ec6e8d3ec7e63aeae1e55`。VM 准备目录同步稿件，浏览器预演筛选已清空，正式新目录仍未启动；本轮仅同步文档，不改发布标签或二进制。

## 2026-10-13 回答评分与 CLI 解析修复（完成，v0.2.2 已发布）

- 意图：修复视频深审复现的两个 P1 问题，补充语义回归，并交付修正后的可复现版本。
- 范围：`kmb/scoring.py`、`kmb/runner.py`、`kmb/agent_adapters/base.py`/`openclaw.py`、对应测试；版本与 CI、证据协议/审计/README/视频稿/发布说明；本台账及本轮 runs/dist 证据。
- 方法：普通回答检查默认末回合；boundary 的禁止回答检查保留全程，显式 `answer_scope` 或 `step` 可限定检查范围。JSON 只提取已识别的 assistant 文本，成功输出完整解析，元数据不能充作答复。
- 补充范围：`scripts/build_deb.sh` 的 CRLF 版本元数据兼容，以及 CI 默认版本构建回归；实机打包复现尾部 CR 字符导致合法 0.2.2 被误拒绝。
- 边界：只修项目软件，保持原 openKylin 3.0；历史证据和旧包不覆盖；真实复测使用临时 HOME 和空白记忆副本，不改日常 Agent 状态。
- 验收：先重现失败测试，再修复并跑全量单测、源码/安装包离线验收和新的真实双 Agent 批次；同步 GitHub、更新录制材料与版本/哈希。

- 实际结果：新增 18 项回归从失败到通过；Windows/openKylin 各 176 项通过；三项代码 CI success。项目包在原 openKylin 3.0 中完成 0.2.1→0.2.2 升级，安装后离线验收与工作台通过。第一批 KylinBot 网关错误使该侧无效并保留，第二批六案例两侧有效、错误 0、strict 通过（KylinBot 22.22、OpenClaw 30.56）。未覆盖完整 49 条真实矩阵，不宣称原生记忆或长期稳定。
- 文档：同步 README、当前环境、修复报告、历史审阅/完成度审计、作品介绍、录制稿、发布冻结和未发送邮件草稿；新材料位于 `dist/submission-0.2.2-20261013/`，旧包与证据保留。GitHub main 已同步，v0.2.2 冻结于 1c4aadf；main CI 三项全通过。最终 deb 安装后 18 项回归、离线验收与工作台全部通过；最终 wheel 在源码外安装验收通过。496 文件交付 manifest、源码审计和材料凭据扫描通过，四份 PDF 渲染检查通过（1/6/4/4 页）。新发布含 9 项附件，匿名下载全部成功并逐项匹配 SHA-256；旧 v0.2.1 标签/二进制保留。非视频 ZIP SHA-256 为 a5e2f32189f1feda1a6ac1e25ec1b6d25e81dac1a73dfd939a9e5603b863b8a0。

## 2026-10-13 视频方案深度复核（审阅与稿件完成，两个 P1 待修）

- 意图：依据当前 0.2.1 代码、openKylin 3.0 实机与命题 PDF，给出可照着操作和朗读的录制稿。
- 范围：`docs/demo-script.md`、`docs/video-review-20261013.md`、`docs/completion-audit-20261013.md` 的追加复核说明、README 的录制前提示、本台账，以及 `dist/video-script-20261013/` 中的 PDF/口播文本；旧稿和探针证据保存在本轮 `runs/` 中。
- 边界：保持原操作系统版本；不修改评分器、案例、Agent 适配器或已发布二进制；本轮只读预检不启动真实 Agent 对话、不消耗模型 Token，不录制或伪造视频。
- 验收：逐项核对 PDF 交付 e、六类 quick 案例、实际 UI 标签、隔离入口及报告路径；核实两款 Agent 预检阻断列表，检查文档命令参数、PDF 排版和 GitHub 同步。
- 实际结果：只读预检两款 Agent 均 ready、blocked 为空、turns_started=0；工作台成功载入历史双 Agent comparison，读取 quick-update 的 7 条事件。语义探针复现更新误扣分（2/3）、最终回答错误却通过（1.0）及 CLI 正确答复被解析为 edit，证据见 `runs/video-script-review-20261013/review-probes.json`。
- 稿件：分镜与实际操作、约 828 汉字照读口播、失败/通过案例分支和录后清单已完成；PDF 4 页、审阅 PDF 3 页，页面渲染检查通过。
- 当前边界：两个 P1 未作代码修复，本次未跑新的付费真实评分；README 与先前完成度审计已追加修正项，旧材料和原始分数保留。正式录制应先修复并使用新的真实批次。

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

### [2026-09-23] 真实 Agent 快速对比隔离与赛题非视频验收
- **状态**: 已完成（非视频交付；视频与许可证仍后置）
- **意图**: 在不污染用户日常记忆的临时 Agent HOME 中，用重新可用的 Token 复测 KylinBot/OpenClaw 六维快速对比，并按 PDF 交付项校正完成口径。
- **改动点**:
  - `kmb/agent_adapters/openclaw.py` — 为每个案例生成独立会话键；支持显式本地隔离模式并将子进程 HOME 指向适配器 HOME
  - `tests/test_agent_adapters.py` — 验证会话隔离、临时 HOME 与本地模式
  - `docs/requirements-traceability.md`、`docs/release-freeze.md`、`tasks/todo.md`、`docs/Zcode-agent对比方案.md`、`docs/mimo.md` — 按新鲜验证与真实 Agent 结果更新状态
- **接入层级**: KylinBot/OpenClaw 真实系统级 Agent 行为，可观测记忆事件；不声称模型原生记忆
- **保留/禁止**: 使用空白临时记忆库与副本配置；不修改原 Agent 记忆/配置；Token 不回显、不入库
- **验收**: 全量 104+ unittest、隔离 VM 六案例双 Agent quick-compare、各结果 `verify_run.py --strict`；证据路径写入追踪清单
- **结果**: VM `/home/Cisyam/kmb-agent-validation-20260923/runs/quick-compare-isolated-20260924/`；KylinBot `63.89`、OpenClaw `13.89`；两侧 `score_valid=true`，strict 退出码 0（51/34 条证据）；新 Token `/v1/models` 返回 200，未再出现 402
- **边界**: 结果为系统级外部记忆/动作控制器行为，`native_memory_events=0`；Hermes 本轮未重跑，KylinAgent 仍不可自动驱动；视频与 LICENSE 仍后置
- **本次是否已同步本台账**: 是

### [2026-09-18] 测试修复 + A 轨门禁口径 + KylinBot 导出器（历史快照，已由 2026-09-22 门禁条目替代）
- **状态**: 已完成（门禁实验已跑；案例得分与 strict 限制如实记录）
- **意图**: 修 test_memory_tool；A 门禁改为 Agent 自有可观测记忆事件；实现 KylinBot 导出器
- **改动点**:
  - `docs/native-memory-compare.md` — §2 门禁口径修正 + §2b 门禁计数 + §11 实验状态
  - `tests/test_memory_tool.py` — 重写（KV/相似/B 骨架/门禁计数）
  - `scripts/export_kylinbot_evidence.py` — brain.db → kmb_evidence JSONL
  - `scripts/kylinbot_command_wrapper.py` — CommandAgent 协议包装
  - `configs/agent-kylinbot-command.yaml` — command 指向导出器（保留 stand-in 配置）
  - `suites/native/kylinbot-gate.yaml` — 单案例门禁套件
  - `kmb/agents.py` — CommandAgent subprocess `errors=replace`（Windows UTF-8）
  - `docs/mimo.md` — 本条
- **门禁口径**: A 轨 = Agent 自有记忆事件（`source=process/memory_layer/wrapper` 的 memory_*）；**不要求** `native_memory_events>0`；原生轨单独记录
- **A 轨实验**:
  - VM openKylin 3.0 `192.168.141.128:22`；`brain.db` 真实拷贝 `_migrate_stage/kylinbot-brain.db`
  - 历史实现曾把全库行计为 **agent_owned_memory_events=3**；2026-09-21 复核后已撤销该口径，当前 case 只保留精确键的 snapshot recall
  - `native_memory_events=0`
  - overall 0.0：DB 键 `project_codename/Atals` vs 案例 `project=Atlas`（烟测数据，如实 omission）
  - `verify --strict` 失败：单案例套件仅 retention（非导出器伪造）
- **当时标签**: `A: snapshot-only / gate-pending`；`B: skeleton-only`；`C: wrapper-only`
- **git**: 已 `git add` 关键文件；**未 commit**（待负责人授权）
- **保留/禁止**: stand-in/wrapper 未删；无密钥入库；未宣称四 Agent 正式评测完成
- **验收**: 2026-09-21 `unittest discover` **78 tests OK**；VM `python3` + 真实 `brain.db` 快照烟测通过，正式会话门禁未通过
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







### [2026-09-22] KylinBot 真实 CLI 门禁通过与证据归档
- **状态**: 已完成（A 轨最小门禁通过）
- **意图**: 在已启动的 openKylin 3.0 VM 中核对真实会话驱动，区分快照/stand-in 与当前 Agent 自有记忆事件。
- **改动点**:
  - `scripts/kylinbot_command_agent.py` — 逐轮调用 `kylin-bot agent --message`，复用临时 session state，读取 `brain.db` 前后差异并输出真实事件
  - `configs/agent-kylinbot-command.yaml` — 从只读快照 exporter 切换为真实 CLI 驱动
  - `suites/native/kylinbot-gate.yaml` — 自然语言 remember/recall 门禁
  - `README.md`、`docs/Zcode-agent对比方案.md`、`docs/native-memory-compare.md`、`docs/ecosystem-agent-export.md` — 更新当前门禁口径
- **VM**: openKylin 3.0 (huanghe)，`Cisyam@192.168.141.128:22`；`kylin-bot` 可执行；用户级 OpenClaw 与 Kylin-Agent runtime 服务 `active`。
- **结果**: `runs/kylinbot-gate-20260922/result.json`，`overall=100.0`；`evidence.jsonl` 含 `source=process` 的 `memory_write`、精确 `memory_recall` 命中 Atlas 和两轮 assistant 输出。
- **观测口径**: `system_level_wrapper_assisted`，`wrapper_memory_events=4`，`native_memory_events=0`；可标记 `A: ready(agent-memory-observable)`，不可宣称模型原生记忆。
- **清理**: 仅删除本轮新增 `benchmark_alias` 与两条关联 `user_msg_*`；既有烟测数据保留。
- **回归**: `.venv-kmb-system\Scripts\python.exe -m unittest discover -s tests -v`，**83 tests OK**；`verify_run.py runs/kylinbot-gate-20260922` 退出码 0。该单案例门禁的 `--strict` 按设计因缺少其余五个维度退出码 2。
- **本次是否已同步本台账**: 是

### [2026-09-22] 四 Agent 快速对比代码整改与 openKylin 3.0 验收
- **状态**: 已完成（代码、本地回归、VM 快速对比）
- **意图**: 将用户流程收敛为“发现已有 Agent → 选择两个 → 一次点击”，保留证据边界，不自动下载 Agent。
- **代码**: 新增 `kmb/agent_registry.py`、四个原生 Agent 适配器、`kmb/quick_compare.py`、`suites/quick.yaml`；工作台新增 `GET /api/agents`、`POST /api/quick-compare` 和总览页快速对比面板。
- **本地回归**: `.venv-kmb-system\\Scripts\\python.exe -m unittest discover -s tests -v`，**94 tests OK**；`node --check kmb/web/app.js` 通过；快速套件严格校验通过。
- **VM**: openKylin 3.0 (huanghe)，`Cisyam@192.168.141.128:22`；KylinBot、Hermes、OpenClaw 自动适配可用；KylinAgent 已安装但因 GUI/服务级证据限制标记为不可自动驱动。
- **VM 结果**: `~/kmb-quick-compare-20260922/runs/openkylin-validation-20260922/quick-compare/kylinbot-hermes/` 与 `kylinbot-openclaw/`；两组均生成六案例双 Agent结果、`comparison.*`、`quick-compare.json`，四份 `result/evidence` 通过 `scripts/verify_run.py --strict`。
- **观测结论**: KylinBot + Hermes 总分分别 `63.89`、`22.22`；KylinBot + OpenClaw 分别 `41.67`、`27.78`。失败项保留为真实 omission/stale_update/confusion/runtime_error/erroneous_reuse，不把网关账单拒绝或模型文本自述计为通过。
- **安全**: 未复制 Agent 数据库、密钥或原始凭据到仓库；VM 结果目录位于 `runs/`（gitignored），只记录脱敏路径和摘要。
- **本次是否已同步本台账**: 是


