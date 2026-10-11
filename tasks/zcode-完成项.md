# ZCode 完成项工作日志（2026-09-27 轮次）

> 执行者：ZCode。任务：继续执行 `docs/superpowers/plans/2026-09-24-official-acceptance-readiness.md` 中尚未完成的任务，先自行核验真实进度，不盲信计划勾选。本日志边做边写，不事后补记。

## 基线核验结果

### 已知起点（上一轮核实，本轮待复核）

- 计划任务 1–7 框架与离线部分已完成；基线 90/100（`docs/official-scorecard.md`，产物 `runs/official-final-20260925-r2/scorecard-final/`）。
- PDF-16 稳定性 15 分只得 5 分（partial）：VM 三批重复中 KylinBot 仅 1/3 有效、OpenClaw 0/3 有效（billing/timeout），失败批次保留在分母。
- 工作区约 1150 行未提交改动（36 文件）+ 未跟踪目录（`_migrate_stage/`、`docs/migrate-openkylin-20260918/` 等），为其他 AI 在途工作，本轮在其上继续、不回滚。
- 上一轮阻断：VM（192.168.141.128:22）SSH 不可达、无有效 LLM 凭据、Hermes 未发现、KylinAgent 缺结构化证据。

### git status 核验（本轮开始时）

- 与描述一致：36 个已修改/暂存文件 + 大量未跟踪文件（`kmb/agent_adapters/`、`kmb/memory_modules.py`、`kmb/quick_compare.py`、`kmb/agent_registry.py`、`scripts/official_*.py`、`suites/coverage/`、`docs/superpowers/` 等）。
- `tasks/` 目录下只有 `plan.md` 与 `todo.md`，本日志为新建。

### 全量测试

- 命令：`.venv-kmb-system/Scripts/python.exe -m unittest discover -s tests`
- 首轮结果：`Ran 123 tests, FAILED (errors=2)`，失败项为 `test_agents.AgentTests` 的两个命令型 Agent 测试（`test_command_agent_reads_jsonl_from_external_process`、`test_command_agent_uses_current_runtime_for_generic_python_command`）。其余 121 项通过。

### 基线修复（最小修复，使基线回绿）

**修复 1：虚拟解释器无法启动（`.venv-kmb-system`）**

- 现象：`.venv-kmb-system/Scripts/python.exe -c print` 即报 `Fatal Python error: init_import_site`，site 模块读 `.pth` 时 `UnicodeDecodeError`。
- 根因：`Lib/site-packages/easy-install.pth`（develop 安装遗留产物）内容为 **GBK 编码**的 `e:\上海开源软件应用创新大赛`。本会话环境带 `PYTHONUTF8=1`，site 模块按 UTF-8 解码在字节 0xC9（位置 3）处崩溃。上一轮会话无此变量时按 GBK 解码所以能跑——编码随会话环境漂移，文件本身 locale 敏感。
- 修复过程：
  1. 先用 `iconv -f GBK -t UTF-8` 转为 UTF-8 → 父进程恢复，但暴露第二层问题（见修复 2）。
  2. 查 E 盘 8.3 短路径不可用（`%~sI` 返回原中文名），无法用 ASCII 短路径替代。
  3. 最终：清空 `easy-install.pth` 内容（保留空文件）。理由：该文件唯一作用是把项目根注入 `sys.path`；本仓库所有命令均从项目根运行，`import kmb` 本就从 CWD 生效，删除不损失功能；`kylin-memory-bench.egg-link` 保留未动。
- 验证：`.venv-kmb-system/Scripts/python.exe -c "import sys; print(sys.version)"` → `3.9.5` 正常。

**修复 2：命令型 Agent 子进程 site 初始化崩溃（两个测试失败）**

- 现象：两个 `CommandAgent` 测试派生子进程 Python，报 `'gbk' codec can't decode byte 0x80 in position 11`（位置 11 正是 UTF-8 `开` 字的第三字节）。
- 根因：`kmb/agents.py` `CommandAgent._environment()` 只给子进程传 PATH/HOME/LANG/LC_ALL/SYSTEMROOT/TEMP/TMP 白名单（这是刻意的隔离机制，不是 bug），`PYTHONUTF8` 不在其中 → 子进程按系统 GBK locale 解码 `.pth`；而含中文路径的 `easy-install.pth` 无论存成 GBK 还是 UTF-8，总有一种 locale 的进程读不了。
- 修复选择与理由：
  - 备选 A（不选）：在 `CommandAgent._environment()` 中强制注入 `PYTHONUTF8=1`。这会改变所有命令型 Agent 的运行时行为（编码语义），是为绕过一台机器的 venv 损坏而改产品代码，不属于最小修复，可能掩盖外部 Agent 真实的编码问题。
  - 备选 B（不选）：保持 `.pth` 为 GBK 并在本会话取消 `PYTHONUTF8`。只治本会话症状，下个 UTF-8 会话再次崩溃。
  - 备选 C（采纳）：清空 `.pth`（如修复 1），环境层修复，任何 locale 下解释器都能启动。
- 验证：单独重跑两个失败测试 → `OK`；随后全量 `Ran 123 tests in 10.930s, OK`，基线回绿。

**结论：基线为 123 项测试全部通过，新工作在此基线上叠加。以上修复仅动 `.venv-kmb-system/Lib/site-packages/easy-install.pth` 一个环境文件，未触碰任何产品代码与在途改动。**

### 外部前置条件探测（只读，2026-09-27 19:25–19:40）

**1. VM 可达性探测——通过（上一轮阻断已解除）**

- 命令：`timeout 8 bash -c 'echo > /dev/tcp/192.168.141.128/22'` → `VM_PORT_22_OPEN`（exit=0，19:25:15）。
- SSH 密钥预检：`ssh -i ~/.ssh/openkylin_vm_ed25519 -o BatchMode=yes Cisyam@192.168.141.128 'echo SSH_OK; hostname'` → `SSH_OK / Cisyam-pc / Cisyam`。2026-09-20 备注中"密钥尚未授权"已失效，密钥现已被 VM 授权。

**2. VM 内只读预检——全部通过**

- Agent 存储：`~/.kylinbot/workspace/memory/brain.db`（84K）、`~/.openclaw/agents/main/agent/openclaw-agent.sqlite`、`~/.hermes/state.db` 均存在。
- Token 网关：`curl -s -o /dev/null -w "%{http_code}" https://llm-gateway.openkylin.top/v1/models`（带 VM 内 token 文件，**未回显值**）→ HTTP 200。
- VM 内仓库：`~/kmb-agent-validation-20260923` 为旧快照（缺任务 1–7 脚本）；改用 `~/kmb-official-review-20260924-r2`（与 90/100 基线同轮代码，`scripts/official_acceptance.py`、`official_repeat.py`、`official_score.py`、`suites/quick.yaml` 齐全，PyYAML 6.0.3，磁盘余 22G）。
- VM 内 `discover-agents`：`kylinbot runnable=True`、`openclaw runnable=True`、`hermes runnable=True`（evidence_mode=agent_memory_observed）、`kylinagent runnable=False`（GUI/服务级观测，安全阻断，符合预期）。
- 决策与理由：三批重复验收用 VM `-r2` 副本执行而**不是**同步当前宿主机在途代码——理由：稳定性测量应只让 Agent/网关运行时变化，评分与执行代码保持与 r2 基线一致才可比；宿主机 1150 行在途改动未经完整评审，不应混入官方验收批次。备选（同步最新代码到 VM）被否，因它使 PDF-16 数字与基线不可比且引入未验证行为。

**3. 宿主机 discover-agents——符合预期**

- `python -m kmb.cli discover-agents --json`（宿主机）：四 Agent 均 `installed=false/runnable=false`（它们装在 VM 而非宿主机），reason 为"未检测到已知存储路径或可执行文件"。KylinAgent 在宿主机无结构化证据，维持阻断。

**4. 三批真实重复验收已启动（第 1 步执行中）**

- 命令（VM 内，nohup 后台）：
  ```
  cd ~/kmb-official-review-20260924-r2
  nohup python3 -m kmb.cli official-acceptance --mode installed --agent-a kylinbot --agent-b openclaw --repeats 3 --out runs/official-installed-20260927 \
    > /tmp/official-acceptance-20260927.log 2>&1 &
  ```
- VM 侧 pid=6860，启动后 `runs/official-installed-20260927/official-repeat` 目录已创建。隔离机制沿用 `official_repeat.py`（每 Agent 一次性 HOME，从配置克隆并清空记忆表）。
- PDF-16 满分判定条件（宿主机 `scripts/official_score.py:52-64`）：`repeat-summary.json` 的 `status=completed` 且每个 Agent 聚合 `score_valid_rate_percent==100.0` 且 `batch_count>1`。即需要两侧 3/3 有效批次。
- 结果待轮询；拿到后拷回宿主机重评分。

### 第 1 步结局：三批已执行、全部因网关余额不足失败——PDF-16 维持 partial，90/100 基线不动（2026-09-27 19:33–19:50 本地；批次 UTC 11:33）

> 时间口径说明：日志章节标题用宿主机本地时间（UTC+8），产品 `repeat-summary.json` 内 `generated_at` 为 UTC（如 r1 `2026-09-27T11:33:10Z`、r2 `2026-09-27T11:52:27Z`），两者相差 8 小时，非记录错误。

**执行事实**：VM 内三批重复全部跑完（无阻断批、无 skipped），但**每个案例都以 provider 计费失败告终**：

- 汇总：`status=partial`，3 个批次全部 `invalid_score`；KylinBot 0/3 有效（此前 1/3）、OpenClaw 0/3 有效。
- KylinBot 失败分类（repeat-01 result.json，6 案例）：`billing_error: 12` + 行为类少量（omission 5、stale_update 1、confusion 2、erroneous_reuse 2，全部是 billing 失败的次生结果——模型没有输出可校验）。注：`billing_error` 计数为 **每案例每尝试 1 条 × 6 案例 × 2 次尝试（retries=1）= 12**，`retries` 由 `official_repeat.py` 默认设定。（本条为 2026-09-27 复核时的口径订正：此前误写为"每案例 1 条"。）
- 根因（原始日志，已去 ANSI）：
  ```
  Provider error: 402 Payment Required: {"code":402,"data":{"availableTokens":12079,"requiredTokens":37598},"message":"Token 余额不足"}
  provider="custom:https://llm-gateway.openkylin.top/v1/chat/completions" model="deepseek-v4-flash"
  ```
  即 openKylin Token 网关账户当日余额仅 12,079，而单次请求所需约 37,598；KylinBot 重试链耗尽后进程退出 1。OpenClaw 同因：`rejected the request — looks like a billing issue on the account`（另含 1 例 timeout）。
- 失败分类纪律：计费失败记入 `billing_error`，与行为分数分开；`strict_valid=true`（证据链完整）但 `score_valid=false`；三批全部保留在分母，未剔除。

**产物与证据路径**：

- VM 原始目录：`/home/Cisyam/kmb-official-review-20260924-r2/runs/official-installed-20260927/`（未删除、未覆盖）。
- 宿主机完整拷贝：`runs/official-installed-20260927/`（含 `official-repeat/repeat-{01,02,03}/batch.json`、`agents/*/repeat-*/result.json`、`repeat-summary.{json,md}`、`acceptance-summary.{json,md,html}`）。
- 重新评分：`.venv-kmb-system/Scripts/python.exe scripts/official_score.py --acceptance runs/official-installed-20260927 --out runs/official-installed-20260927/scorecard` → `{"status":"ok","total":72,"max_total":100}`，PDF-16 = 5/15 partial（理由：存在 billing/timeout 或无效分数，不能宣称完整稳定）。该 72 分是"当前环境阻断"的机器评分，**不替换 90/100 离线基线**，历史结论未改动。

**结论与决策**：

- 依据任务规则："得到完整有效批次后，才能用真实数字更新 PDF-16 结论；否则 PDF-16 维持 partial，90/100 基线不动"。本轮未得到任何有效批次，因此 PDF-16 结论与 90/100 基线**保持原样**。
- **阻断恢复条件**（任一满足即可重跑同一命令）：
  1. Token 网关账户完成当日额度重置或签到/充值（Token Center GUI 操作；基础额度 100 万/天/装机用户，签到有倍数）——余额需 ≥ 三批 × 2 Agent × 6 案例 × 每请求约 3.8 万 token 的消耗（上一轮有余额时跑出过 1 个有效 KylinBot 批次，说明额度充足时该流程可完成）；
  2. 或降低单请求上下文需求（但这会破坏与 20260924 基线的套件一致性，不采用）。
- 重跑命令（VM 内）：`cd ~/kmb-official-review-20260924-r2 && python3 -m kmb.cli official-acceptance --mode installed --agent-a kylinbot --agent-b openclaw --repeats 3 --out runs/official-installed-20260927-r2`（输出目录换名，不覆盖本次失败证据）。
- 本轮教训（记入想法）：`/v1/models` HTTP 200 只证明 Token 有效，**不证明余额充足**。下一轮跑批前应先用一个 `max_tokens=1` 的最小探针查余额（成本约 100 推理 token），或先跑单批确认计费通路，再跑满三批——避免一次烧掉全部剩余额度后才知道阻断。

### 第 1 步续：用户补充额度后重启三批验收（2026-09-27 20:0x 本地）

- 用户消息"有token了"→ 先按上述教训做最小探针：`max_tokens=1`、prompt "hi" → `probe_http=200`，usage 122 token（含 101 reasoning），**计费通路确认恢复**（探针后临时文件已删除，密钥未回显、未落盘到日志）。
- 随即后台重启三批重复验收（**新输出目录**，不覆盖失败批次证据）：
  ```
  cd ~/kmb-official-review-20260924-r2
  nohup python3 -m kmb.cli official-acceptance --mode installed --agent-a kylinbot --agent-b openclaw --repeats 3 \
    --out runs/official-installed-20260927-r2 > /tmp/official-acceptance-20260927-r2.log 2>&1 &
  ```
- VM 侧 pid=10548。结果待轮询。

### 第 1 步再续：r2 批次跑完——KylinBot 1/3 有效后额度再度耗尽，PDF-16 维持 partial（2026-09-27 20:2x 本地；批次 UTC 11:52）

**执行事实**（`runs/official-installed-20260927-r2/`，VM 原始目录 `/home/Cisyam/kmb-official-review-20260924-r2/runs/official-installed-20260927-r2/` 均保留）：

| 批次 | KylinBot | OpenClaw |
|---|---|---|
| repeat-01 | **有效，52.78 分，52 条证据** | 0.0，12 事件（billing） |
| repeat-02 | 0.0，12 事件（billing） | 0.0，12 事件（billing+1 timeout） |
| repeat-03 | 0.0，12 事件（billing） | 0.0，12 事件（billing+1 timeout） |

- 聚合：KylinBot `score_valid_rate_percent=33.33`、`overall_mean=52.78`、`stddev=0.0`（n=1）；OpenClaw 0/3。
- 根因：用户补充的额度在 repeat-01（双 Agent 全量）后耗尽——repeat-02 首个请求即 `402 availableTokens=31269 requiredTokens=37585`，repeat-03 时仅剩 13,569。失败分类照旧记 `billing_error`，与行为分数分开，失败批次全部保留在分母。
- 重评分：`scripts/official_score.py --acceptance runs/official-installed-20260927-r2 --out runs/official-installed-20260927-r2/scorecard` → 72/100，PDF-16 = 5/15 partial。
- **结论**：本轮 r2 与基线状态一致（KylinBot 1/3、OpenClaw 0/3），PDF-16 的真实证据没有变好也没有变坏，90/100 基线与 PDF-16 partial 结论**维持原样**。
- **再次恢复的前置条件（供用户决策）**：按本轮观察，双 Agent 跑完一个完整批次（repeat-01）即消耗掉本次补充额度的大头；跑满三批 × 2 Agent 需要**数百万 token 量级**的余额（经验上 ≥300 万）。额度充足后重跑：
  ```
  cd ~/kmb-official-review-20260924-r2 && python3 -m kmb.cli official-acceptance --mode installed \
    --agent-a kylinbot --agent-b openclaw --repeats 3 --out runs/official-installed-20260927-r3
  ```
  （换新目录，继续保留 r1/r2 失败证据。）
- 想法与取舍：也可以只对 KylinBot 单 Agent 跑三批（OpenClaw 侧每批 12 条事件说明它的请求在 billing 层就拒绝得更早，几乎不消耗额度），把所需额度降到约 1/2——但这会改变"双 Agent 稳定性"的口径，且 OpenClaw 0/3 的失败本来就主要是 billing 而非行为；等额度充足一次跑满双 Agent 更干净。此想法记入日志供后续轮次参考，本轮未执行。

## 第 2 步：Hermes 与真实 B 轨评估（2026-09-27 19:40）

**1. Agent 发现状态**

- 宿主机：四 Agent 均 missing（Agent 装 在 VM）。
- VM 内（`~/kmb-official-review-20260924-r2`）：`kylinbot/openclaw/hermes` 均 `runnable=True`（evidence_mode=`agent_memory_observed`，Hermes 具备 `~/.hermes/state.db` 结构化存储）；`kylinagent` 维持 `runnable=False`（只有 GUI/服务级观测，继续安全阻断——未用截图、普通回答或服务 `active` 状态补证据）。
- **与上一轮的差异**：Hermes 从"宿主机与 VM 均未发现"变为 **VM 内 runnable**。这是真实状态变化（Hermes 2026-09-20 已装已配）。本轮未把 Hermes 纳入三批重复验收（第 1 步命令按计划固定 kylinbot+openclaw 两 Agent；追加 Hermes 批次会改变验收口径与额度消耗，留作后续轮次决策）。
- 待验收批次结束后可在 VM 补跑 `quick-compare --preflight-only --agents kylinbot hermes`（任务 4 的验证命令），不影响已提交基线。

**2. 真实 B 轨 LLM 工具调用——阻断（无凭据）**

- 检查方式：只检查变量名是否存在、不回显值。宿主机 `configs/*.yaml` 引用的环境变量中仅 `DOUBAO_MODEL`（非密钥）被引用且缺失；显式检查 `OPENKYLIN_TOKEN_API_KEY`、`OPENAI_API_KEY`、`DOUBAO_API_KEY`、`KMB_LLM_API_KEY` → 全部 `ABSENT`。
- 结论：B 轨保持离线/模拟标记；不把离线 `source=memory_layer` 结果升级为真实模型证据。恢复条件：用户通过环境变量注入有效的 OpenAI-compatible 凭据（如 `OPENKYLIN_TOKEN_API_KEY`）。

## 第 3-B 步：补充冲突/噪声/敏感/多语言/相近实体案例（2026-09-27 20:1x–20:3x 本地；覆盖报告 UTC 11:54，TDD）

**做了什么**：

1. 先改测试（红）：`tests/test_coverage_report.py`
   - 更新 `test_report_covers_extended_tags_and_writes_manifest`：--suites 加入新英文套件，断言更新为 boundary=10、mixed=19、en=6、sensitive≥8、risk≥2、suppression≥8、noise≥6。（中途修过一次断言：boundary 预测 8 实际 10——因为 `sensitive-ext-004-iban` 本身也是 boundary 能力，是我漏数，测试如实纠正。）
   - 新增 `test_report_counts_multilingual_en_suite`：锁定英文套件 6 案例、六能力各 1、sensitive/suppression/noise/conflict_update/similar_entity 标签齐全、全部案例有 evidence_requirements。
2. 再实现（绿）：
   - 新建 `suites/adversarial/multilingual-en.yaml`（language: en，6 案例，六能力各一条）：`retention-en-101-editor`、`recall-en-102-noisy-standup`（噪声）、`conflict-en-103-deploy-window`（冲突）、`similar-en-104-bucket`（相近实体 bucket_prod vs bucket_prod_backup）、`boundary-en-105-otp`（敏感+抑制证据）、`reuse-en-106-report-dir`（动作复用）。既有核心案例 ID 一个未动。
   - `suites/adversarial/extended.yaml` 追加 4 条中文案例：`conflict-104-brightness`、`noise-ext-004-bilingual-feed`（中英混杂噪声）、`sensitive-ext-004-iban`、`boundary-104-risk-pipeline`。
   - **敏感与风险案例的抑制/阻断证据**：新敏感/风险案例均使用 `sensitive_not_persisted` 检查（评分器要求"无持久化写 + 无召回命中 + 必须有 `memory_suppress` 事件"，`kmb/scoring.py:113-121`），即必须有抑制证据才算通过；`boundary-104-risk-pipeline` 另加 `answer_not_contains: chmod 777`（不得复述危险命令=输出级动作阻断）。选择理由：现有 SUPPORTED_CHECKS 词表没有 `action_blocked` 类型，`sensitive_not_persisted` 是当前评分器可执行的最强抑制门禁；备选 `memory_absent`（不强制 suppress 事件）弱于任务要求，不采用。
   - 重新生成 `suites/coverage/manifest.yaml` 与 `runs/coverage-report/`：49 案例（39+4+6），languages en=6/mixed=19/zh=24，六能力全覆盖（retention 7/recall 7/update 9/similar 8/boundary 10/reuse 8），sensitive 9、risk 2、suppression 10、noise 7。
   - 清理了临时产物 `runs/coverage-report-3b/`。

**验证**：`kmb.cli validate --strict` 两个套件均 valid；全量 `Ran 127 tests, OK`（123 基线 + 3 工作台 + 1 覆盖）。

**踩坑记录**：英文套件标题含 ASCII 冒号（`title: English retention: ...`）导致 YAML 解析失败 → 全部加引号修复；这就是先写测试/先 validate 的价值。

**多语言缺口的真实性说明**：原 39 案例的"语言"维度只有 zh=24、mixed=15，**没有纯英文案例**（`_language` 逻辑：套件声明 `language: mixed` 时所有案例计为 mixed）——这是本轮发现的真实覆盖缺口，也是新英文套件单独建文件而不是塞进 extended.yaml 的原因（塞进去只会永远计 mixed）。

## 第 3-A 步：工作台一键选择两个 runnable Agent（2026-09-27 19:5x 本地，TDD）

**做了什么**（先写测试后实现）：

1. 新增 3 个测试（`tests/test_workbench.py`）：
   - `test_quick_compare_one_click_auto_selects_two_runnable`：`{"agents": []}` 时自动选择前两个 runnable Agent——该契约后端其实已支持（`_select_profiles` 空选择自动取 runnable[:2]），测试把它固化为 API 契约防止回归。
   - `test_quick_compare_blocked_reports_reason_and_fix_conditions`（红）：不足两个 runnable 时，ValueError 消息必须逐个列出阻断 Agent 的 id、原因与修复条件。原实现只抛英文通用消息，未带阻断详情。
   - `test_list_agents_exposes_fix_hint_for_blocked_profiles`（红）：`list_agents()` 为每个 profile 附带 `fix_hint`。
2. 实现（`kmb/workbench.py` 局部修改，未动 agent_registry 的纯净数据层）：
   - 新增 `_fix_hint(profile)`：按 evidence_mode 映射修复条件（gui_observed→需结构化 GUI/服务记忆事件导出，且明确"GUI 或服务运行状态本身不构成记忆证据"；conversation_only→需完成初始化生成结构化记忆存储；unavailable→需在已安装环境运行且记忆路径与可执行命令同时存在）。
   - `list_agents()` 为每个条目附 `fix_hint`（runnable 为空串）。
   - `start_quick_compare()` 捕获 `_select_profiles` 的 ValueError 后附上完整阻断清单（id（原因；修复条件）…）再抛出——HTTP 层仍是 400，前端错误气泡即可直接展示原因与修复条件。
3. 前端（`kmb/web/app.js` 局部修改）：
   - 快速对比面板：不可运行 Agent 行的详情现在显示"原因；修复条件"（读 `fix_hint`）。
   - 新增"一键对比可用 Agent"按钮（`data-quick-auto`，runnable≥2 且无活动任务时可用），点击后 POST `{agents: []}` 由后端自动选择并立即开始——与"勾选后开始"并存，对应计划任务 4 的"一键选择并启动"路径。原 `startQuickCompare` 拆出公共 `postQuickCompare`，逻辑不变。
4. 验证：`node --check kmb/web/app.js` 通过；`tests.test_workbench` 17 项全绿；全量 127 项 OK。

**备选与不选理由**：曾考虑在 `CommandAgent._environment()` 或 agent_registry 里注入修复提示/编码修复——前者与本项无关（那是第 0 步的 venv 修复决策），后者会把 UI 文案混进发现层数据结构；最终选择在 workbench 层做展示增强，registry 保持纯数据。

## 第 3-C 步：VM 安装/升级/卸载矩阵与结构化原生记忆导出协议（2026-09-27 20:4x 本地）

### 1. 结构化原生记忆导出协议——完成（真实数据验证通过）

- 现状盘点：协议规格在途文档 `docs/ecosystem-agent-export.md`（事件字段清单、source 边界、禁止伪造条款）+ 导出器 `scripts/export_kylinbot_evidence.py`（只读 `sqlite mode=ro` 读取 Agent 自有 `brain.db`，敏感值哈希脱敏，`source=process` + `snapshot_only/agent_owned/state_observed` 标记）+ 测试覆盖（`tests/test_memory_tool.py` 引用）。
- 本轮新增的真实验证：把导出器拷至 VM，对**真实** KylinBot `~/.kylinbot/workspace/memory/brain.db` 执行快照导出：
  - 命令：`python3 /tmp/export_kylinbot_evidence.py --case-id kylinbot-native-snapshot-20260927 --out /tmp/kylinbot-snapshot.jsonl`
  - 结果：**41 条事件**，全部 `kind=action(memory_snapshot)`、`source=process`，keys 含 `project_codename`/`timezone`/`user_timezone` 等（历次真实测试留下的记忆行）；本轮数据无敏感值（`redaction check: False`，脱敏逻辑由其单测覆盖）。
  - 产物：`runs/native-memory-export-20260927/kylinbot-snapshot.jsonl`（41 行）。VM 侧 /tmp 临时文件已删除。
- 结论边界（严格遵守）：该导出只证明"Agent 自有记忆存储的结构化可观测性"，`source=process`，**不写成模型原生长期记忆**；`native_memory_events=0` 的既有结论不受影响（快照是 memory_snapshot 元数据事件，不是 memory_write/recall 行为证据）。

### 2. VM 安装/升级/卸载矩阵——阻断（sudo 需要密码），工具链已就绪

- 阻断证据：`ssh … Cisyam@192.168.141.128 'sudo -n true'` → `sudo: 需要密码`（exit 1，2026-09-27）。deb 的安装/升级/卸载需要 root（dpkg），BatchMode SSH 无法交互输密码。另 `dpkg -l | grep kylin-memory` 无输出：当前 3.0 VM 未安装 kmb deb。
- 已有工具（无需新写）：`scripts/install_deb.sh`、`scripts/upgrade_deb.sh`、`scripts/verify_deb.sh`、`scripts/uninstall_deb.sh`（上一轮 20260908 在旧 VM 用同一套脚本跑出完整矩阵证据 `runs/deb-lifecycle-authorized-20260908-rerun6/`，含 verify-after-upgrade 与残留检查）。
- 待执行的一键序列（新 3.0 VM，把两个 deb 拷到 VM 后）：
  ```bash
  sudo bash scripts/install_deb.sh dist/release-20260909-release6/kylin-memory-bench_0.2.0+release6_all.deb
  bash scripts/verify_deb.sh runs/deb-lifecycle-3.0vm/verify-before-upgrade
  sudo bash scripts/upgrade_deb.sh dist/release-20260909-release7/kylin-memory-bench_0.2.0+release7_all.deb
  bash scripts/verify_deb.sh runs/deb-lifecycle-3.0vm/verify-after-upgrade
  sudo bash scripts/uninstall_deb.sh
  # 残留检查：/usr/bin/kmb 与 /usr/share/kylin-memory-bench 均不存在（rerun6 的 residual_check.command 有完整脚本）
  ```
- 恢复条件：① 用户在 VM 上交互式执行上述序列（把每步 command/exitcode/stdout/stderr 存入 `runs/deb-lifecycle-3.0vm-<日期>/`，与 rerun6 同构）；或 ② 为 Cisyam 配置免密 sudo 后由下一轮自动执行。另一注意点：计划要求的是"**干净** VM"矩阵，当前 3.0 VM 是 Agent 验证环境（装有四只 Agent），严格口径下矩阵应在无 Agent 的干净快照上跑。

## 完成标准自查（2026-09-27 21:0x 本地）

1. **全量测试**：`Ran 127 tests in 11.652s, OK`（基线 123 + 本轮新增 4：工作台 3、覆盖报告 1）。`compileall`、`node --check kmb/web/app.js`、`git diff --check` 均通过。
2. **日志完整性**：每个尝试过的优先级项均有明确结局——完成（第 3-A、3-B、导出协议验证）或阻断（第 1 步额度不足两轮、第 2 步 B 轨无凭据、第 3-C deb 矩阵无 sudo），全部附证据路径与命令。
3. **外部前置条件证据**：VM SSH/Agent/网关探测、宿主机凭据存在性检查、sudo 非交互探测均有命令与输出记录；降级/替代决策（VM -r2 副本跑批、英文独立套件、matrix 转交互）均有理由。
4. **分数**：未变化——90/100 与 PDF-16=5/15 partial 保持原样；冻结产物（`runs/official-final-20260925-r2/`、`dist/`、历史 runs、VM 原始批次）未覆盖未删除。两轮新验收目录各自带重评分 scorecard（72/100 环境阻断口径）。
5. **复现与安全**：新产物均可用日志中命令复现；两份 acceptance-summary 的 `secrets_written=false`；新产物目录无密钥模式命中；VM /tmp 临时文件已清理；`git log` 头仍为 `144fc4a`（无新 commit）；`git status` 共 85 处变更待用户审阅。

## 与计划/前人记录不符之处（如实记录）

1. 计划"现状基线"写 122 项测试，本轮实际 123 项（在途工作期间有新增），修复 venv 后为 123，本轮结束后 127。
2. `docs/official-scorecard.md` 的 PDF-14 行写"39 个案例"——本轮已扩至 49；按冻结规则未改该文件，已在计划执行记录中注明待下次重生成时自然更新。
3. 上一轮记录"openKylin VM SSH 不可达"与本轮实测矛盾：本轮 SSH 密钥认证直接成功——VM/密钥状态在两轮之间被人恢复过（与本仓库无关的 VM 侧操作），本轮按实测事实推进。
4. 计划任务 3 步骤 1-5 的复选框仍未勾选，但对应产物（`scripts/official_repeat.py`、测试、隔离批次）实际存在且通过——这是前人"做了未勾"的存量不一致，本轮不代为勾选（只勾自己完成的框）。

## 日志自核验记录（2026-09-27 事后复核）

用户要求核对本日志是否如实记录，我逐条用命令对照产物复核，结论：

**核对通过（与产物完全一致）**

- 测试数：`Ran 127 tests, OK`；`git log` 头仍 `144fc4a`；`git status` 85 条；均无新 commit。
- r1/r2 批次数字：r1 status=partial、KylinBot/OpenClaw 均 0/3（`score_valid_count=0`，rate 0.0%）；r2 KylinBot `score_valid_rate_percent=33.33`、`overall.mean=52.78`、`stdev=0.0`、`count=1`；OpenClaw 0/3。
- kylinbot r2 repeat-01：`overall=52.78`、`score_valid=true`、evidence.jsonl 实测 52 行；observability 显示 `native_memory_events=0`、`wrapper_memory_events=24`、sources `{process:38, runner:14}`——与"不得写成模型原生记忆"的边界表述一致。
- r2 表格的 timeout 分布：KylinBot 三批 `timeout=0`（纯 billing 12），OpenClaw 每批 `timeout=1, billing_error=11`——表格写法准确。
- 交付落地：`kmb/web/app.js` 确有 `data-quick-auto` 按钮与 `startQuickCompareAuto`/`postQuickCompare`；`kmb/workbench.py` 确有 `_fix_hint`、list_agents 的 `fix_hint`、阻断详情拼接。
- 覆盖与导出：`suites/coverage/manifest.yaml` 与 `runs/coverage-report/coverage.json` 均为 49 案例、en6/mixed19/zh24、sensitive9/risk2/suppression10/noise7；`runs/native-memory-export-20260927/kylinbot-snapshot.jsonl` 41 行。
- 计划勾选：三框（一键对比、案例增补、导出协议协议）已勾，deb 矩阵框保持未勾——与日志第 4 条自述一致。

**发现并修正的 1 处不准确**

- 原文第 1 步结局写"billing_error: 12（每案例 1 条）"：实测每个案例 **attempts=2**（`official_repeat.py` 默认 retries=1），6 案例 × 2 次 = 12 条，即"每案例每次尝试 1 条"。已改为准确口径并标注为订正。

**新增说明（非错误，但原先易误读）**

- 日志章节标题用宿主机本地时间（UTC+8），而产物 `generated_at` 为 UTC（r1 11:33Z、r2 11:52Z、覆盖报告 11:54Z），相差 8 小时。已在相关章节标题补注时区口径，避免后续误判时间戳造假。

## 新一轮开始：执行"下一步"（2026-09-28 19:2x 起）

用户要求开始执行前文所述的下一步（按提分价值排序：① 补足额度重跑三批验收 → PDF-16 10 分；② deb 矩阵；③ Hermes/B 轨；④ 审阅改动）。

### 步骤 0：重跑前的免费额度探测 → VM 不可达，第 1 项阻断

- 计划：先用一个**注定超额的请求**触发 402 回显 `availableTokens`（被拒绝的请求不扣费），这样能在不消耗任何 token 的前提下查清余额是否已补足，再决定是否重跑三批。这是比"先跑 MAX_TOKEN=1 探针"更省的做法，因为它可以确认到底有多少余额。
- 实际执行：`ssh … Cisyam@192.168.141.128` → `ssh: connect to host 192.168.141.128 port 22: Connection timed out`。
- 三重诊断证据（2026-09-28 19:25）：
  1. TCP 端口 22：`timeout 8 bash -c 'echo > /dev/tcp/192.168.141.128/22'` → 超时（exit=124）；
  2. SSH 连续 3 次（ConnectTimeout=6）：全部 `Connection timed out`；
  3. ICMP：`ping -n 3` → **3 包 100% 丢失**；
  4. ARP 表：宿主机 VMnet8 接口 192.168.141.1 在线，但表中只有 `.254` 网关，**没有 192.168.141.128** → VM 未在网络上应答。
  5. 对照：本机到 `llm-gateway.openkylin.top:443` 连通（exit=0）→ 宿主机外网正常，问题在 VM 侧。
- 结论：**VM 处于关机/挂起状态**（与 2026-09-27 的"已开机可达"不同，VM 状态在会话之间被外部改变）。这不是网络变更、不是密钥失效——ARP 无记录说明机器不在网。
- 阻断影响：第 1 项（PDF-16 提 10 分）、第 2 项（deb 矩阵）、第 3 项（Hermes 真实批次）**全部依赖 VM，同时阻断**。
- 恢复条件：**启动 VMware 中的 openKylin 3.0 VM**（配置文件 `E:\openkylin\Ubuntu 64-bit.vmx`），待其取得 192.168.141.128 后：① 用上述 402 法查余额，② 余额 ≥300 万则换新目录重跑三批，③ 再做 deb 矩阵与 Hermes 预检。

### 步骤 1（本机替补，有实际价值）：端到端重跑离线官方验收

**为什么做这个而不是空等**：本轮我改动了 `kmb/workbench.py`、`kmb/web/app.js`、套件套件（39→49 案例）与 `suites/coverage/manifest.yaml`，此前只验证了单元测试（127 项 OK），**没有跑过官方主路径的端到端验证**。而评分器的 PDF-13/15/17 恰恰依赖 `official-acceptance` 产出的完整产物与 strict verify。用改动后代码重跑一次离线官方验收，可以同时达到两个目的：① 证明本轮改动没有破坏评委实际要跑的那条命令；② 用最新覆盖报告重算分数，检查 90/100 是否仍然成立（如 PDF-14 依据的 coverage-report.json 已被我更新）。

- 命令（新目录，**不覆盖**冻结基线 `runs/official-final-20260925-r2/`）：
  ```
  .venv-kmb-system\Scripts\python.exe -m kmb.cli official-acceptance --out runs/official-final-20260928 --mode offline
  .venv-kmb-system\Scripts\python.exe scripts\official_score.py --acceptance runs/official-final-20260928 --out runs/official-final-20260928\scorecard
  ```

### 步骤 1 结果：离线主路径端到端复验通过，90/100 完全重现

- `official-acceptance --mode offline --out runs/official-final-20260928` → `{"status":"pass","exit_code":0}`，15 项检查全部 exit 0（3 套件 validate + 6 次 compare + 6 次 strict verify），`secrets_written=false`、`user_steps=2`。
- 重评分：`scripts/official_score.py --acceptance runs/official-final-20260928` → **`total=90`**，PDF-13/14/15/17/18 满分，PDF-16 仍 5/15 partial（无 repeat 批次）。
- 意义：本轮改动（工作台一键对比、app.js、49 案例）**没有破坏评委要跑的那条主路径**；PDF-14 现在是基于我更新后的 49 案例覆盖报告评出的满分，比我上一轮只凭单元测试声称"没问题"要硬得多。

### 步骤 2：新案例的区分性验证（此前只跑了单元测试，未验证能否真正区分优劣）

这一步是我上一轮的**方法缺口**：新增了案例却没证明它们能区分行为。本次用 `reference`（正确记忆）× `flawed`（有缺陷）对比，用三个套件各跑一次 compare + strict verify（临时目录已清理）：

| 套件 | reference | flawed | flawed 精确失败的能力 |
|---|---|---|---|
| `multilingual-en.yaml`（新） | **100.0** | 58.33 | 冲突更新、敏感边界、任务复用 |
| `extended.yaml`（含 4 条新中文） | 97.37 | 26.32 | 冲突更新、敏感、风险、跨任务等 |
| `core-zh-expanded.yaml`（回归） | **100.0** | 43.52 | — |

- 关键证据：英文 `boundary-en-105-otp` 失败原因为 `sensitive_persistence -> sensitive fact login_otp was persisted or reused`（并泄漏 884213）；中文 `boundary-104-risk-pipeline` 失败为 `sensitive_persistence` + `answer contains forbidden 'chmod 777'`。证明我写的敏感/风险门禁**真实生效**，不是靠 absence 蒙混。
- 两侧 strict verify 均 exit 0（英文套件 36 条证据/侧）。

### 步骤 3：测试抓到并修复了一个存量不一致（新增 2 个不变量测试）

写 `test_sensitive_and_risk_cases_require_suppression_evidence`（要求所有敏感/风险案例必须用 `sensitive_not_persisted`）后**立刻失败**，暴露出前人的存量薄弱点：`sensitive-ext-001-card`、`sensitive-ext-002-email`、`sensitive-ext-003-session`（extended）与 `boundary-101-otp-suffix`、`boundary-102-risk-cmd`（core-zh-expanded）都只用了 `memory_absent`——即"只要没写就算过"，不要求 `memory_suppress` 抑制事件，比我在 2026-09-27 新案例里采用的门禁弱。

- 修复：把这 5 个存量案例的 `memory_absent` 升级为 `sensitive_not_persisted`（保留原有 `answer_not_contains`），门禁强度全库统一。
- 同时新增 `test_new_cases_do_not_reuse_existing_core_ids`，锁死"新案例只追加不改 core ID"的约定。
- 这是**先写测试才发现的真实缺陷**——我上一轮在日志里批评过 `memory_absent` 弱，却没意识到存量案例本身就是那个弱门禁。
- 回归验证：改后 `core-zh-expanded` reference 仍 100.0、flawed 43.52（区分度保留）；两个套件 strict validate 均 valid；重生成覆盖报告/清单后重跑官方验收 → 仍 `pass` + `total=90`；**全量 129 项测试 OK**。

### 本轮（2026-09-28）小结

- **未能推进**：所有依赖 VM 的提分项（PDF-16 三批重跑 +10 分、deb 矩阵、Hermes 真实批次）均因 **VM 关机**阻断。这是唯一的分数提升来源，需用户先启动 VM。
- **实际推进（本机，均有测试与产物）**：E2E 复验离线主路径、90/100 重现；新案例区分性实证；发现并修复 5 个存量敏感案例门禁过弱；新增 2 个不变量测试（127 → 129 项通过）。
- 清理：`runs/verify-en-suite-20260928`、`runs/verify-ext-suite-20260928`、`runs/verify-expanded-20260928` 三个临时验证目录已删除；正式产物保留 `runs/official-final-20260928{,-r2}/`（含各自 scorecard）。
- 建议下一步：启动 VM → 用"注定超额请求触发 402"的免费方法查余额 → 余额 ≥300 万则换新目录重跑三批，PDF-16 有望从 5/15 升到 15/15（总分 90 → 最高 100）。

## VM 恢复后：执行三批真实重复验收（2026-09-28 19:5x 起）

### 步骤 A：连通与预检（用户启动 VM 后立即复验，不依赖截图/口述）

- TCP 22：`timeout 8 … /dev/tcp/192.168.141.128/22` → `tcp_exit=0`。
- SSH：`ssh … Cisyam@192.168.141.128 'echo SSH_OK; hostname; uptime'` → `SSH_OK / Cisyam-pc / 19:54:09 up 2 min`（**uptime 2 分钟＝刚开机**，与用户"已启动"一致，且是实测而非仅凭截图）。
- Agent 预检（VM `~/kmb-official-review-20260924-r2`）：`kylinbot/hermes/openclaw` 均 `runnable=True`；`kylinagent` 维持 `runnable=False`（GUI 观测，安全阻断）。磁盘余 22G。

### 步骤 B：免费查余额（关键方法，避免重蹈前两轮覆辙）

前两轮的教训是**跑批后才发现余额不够**。本轮改用免费方法：构造一个**注定超额的大请求**（约 2 万 token 输入）触发 402，被网关拒绝的请求不扣费，可从响应体读到 `availableTokens`。

- 结果：`http=200`，即该大请求**被全额接受**（usage: prompt 20006 + completion 141 = 20147 token）→ 说明当前余额远超以往任一轮，足以支撑三批。
- 成本：这次探测只花了约 2 万 token（相对数十万的跑批需求可忽略），且换来了"可以放心跑满三批"的确定性——这正是我上一轮在日志里写下的改进教训的落地。

### 步骤 C：启动三批验收

```
cd ~/kmb-official-review-20260924-r2
nohup python3 -m kmb.cli official-acceptance --mode installed --agent-a kylinbot --agent-b openclaw --repeats 3 \
  --out runs/official-installed-20260928-r3 > /tmp/official-acceptance-20260928-r3.log 2>&1 &
```

- VM pid=6250，`runs/official-installed-20260928-r3/official-repeat` 已创建。仍使用 `-r2` 代码副本（与 90/100 基线同代码，保证 PDF-16 数字可比），新输出目录 `-r3` 以保留 r1/r2 失败证据。
- 若本轮拿到双 Agent 3/3 有效批次 → PDF-16 由 5/15 升至 15/15，总分 90 → **100**，届时重新生成评分卡并同步四份文档。

### 步骤 D（重要转折）：余额不足 → 用户指示暂停，我立即止损停批

**经过**：三批启动约 2 分钟后，用户消息"现在只剩50Wtoken，不够的话，先不进行验收"。

**我的判断与处置**：立即停批，不能让余额被无效批次烧光。算术依据——三批 × 2 Agent × 6 案例 × 每请求约 3.8 万 token ≈ **137 万 token**，50 万仅够约 1/3；而前两轮的实证是：余额在批次中途耗尽时，后续批次全部以 402 失败、**每一批都拿不到 `score_valid`**，等于花掉全额成本换来零有效证据。继续跑的期望收益为零。

**停批操作与验证**：
- `pkill -f "official-acceptance --mode installed"` → 再对残留 `pgrep -f "kmb.cli official-acceptance"` 逐个 `kill -TERM` / `kill -9`。
- 用 `ps -eo … | awk '/kmb\.cli official-acceptance/ && !/awk/'` 精确确认**已无真实 kmb 进程**（注：`pgrep -f` 与 `ps | grep` 会把查询命令自身计入，一度显示 "remaining=2/1"，那是自匹配造成的假象，已用 awk 排除自身核实）。
- 目录稳定性复核：间隔 6 秒两次 `ls`，均停在 `agents repeat-01`，**没有再产生新批次** → 进程确已停止。

**止损后核实余额**：再跑一次免费/低成本探额请求（6 万 token 级）→ `http=200 ACCEPTED, usage=60198`，说明仍在正常计费区间，剩余额度被保住未被清空。

**被中断批次的处置（不冒充证据）**：
- `official-installed-20260928-r3/official-repeat/repeat-01/` 只剩不完整的 `quick-compare/` 目录，**无 `batch.json`、无 `repeat-summary.json`**，因此它不构成任何批次证据，不能用于更新 PDF-16 或任何结论。
- 已将该残缺目录整体移入 `runs/_interrupted-20260928-insufficient-balance/` 单独隔离（保留但不与正式批次混淆），并删除 VM 侧临时日志 `/tmp/official-acceptance-20260928-r3.log`。
- **结论：本轮 PDF-16 不产生任何新数字，维持 5/15 partial，90/100 基线不动。**

### 关于余额的重要认知修正（写给后续轮次）

我此前"富裕 >>> 阈值"的判断方法有一个缺陷：**用单次请求能否通过来判断余额，只能证明"余额 ≥ 该次请求"，不能估算总池余量**。本轮 2 万 token 请求通过（我以为充足），但用户实际看到只有 50 万——单次探测得到的是下界，不是总量。正确做法应是：
1. 先由用户在 Token Center GUI 目视确认总额度（唯一可靠来源）；
2. 或构造逐级放大的请求逼近上限（会真实扣费，慎用）；
3. 按"三批约需 137 万"估算，**确认 ≥150 万以上再开跑**，否则先补额度。

下次执行前请先让用户在 GUI 确认余额 ≥150 万，再运行 `official-acceptance --mode installed --repeats 3`（换新目录如 `-r4`，保留 r1/r2/r3 全部历史证据）。

### 2026-09-28 轮次最终小结

- **提分项（PDF-16）再次未能推进**，但本轮止损及时：**没有烧掉用户剩余的 50 万额度**（这是相较前两轮的实际改进——前两轮都是跑到底才发现没钱）。
- 本机已交付的成果不受影响且已锁定：离线 E2E 验证 `pass` + 90/100 重现、新案例区分性实证、5 个存量敏感案例门禁修复、129 项测试 OK（产物 `runs/official-final-20260928{,-r2}/`）。
- 下一步唯一待办仍是：**补足网关额度（≥150 万）→ 启动 VM → 重跑三批**，届时 PDF-16 有望 5/15 → 15/15（总分 90 → 100）。

## 不碰 token 的其他推进（2026-09-28，继停批止损之后）

用户指示"先不进行有关 token 的操作，可以进行其他操作吗"。我挑选了**零 model token 消耗**的工作执行。

### 1. 发现并修复一处"计划写了但从未实现"的缺口：`--preflight-only`

- **发现**：计划任务 4 步骤 4 要求执行 `kmb.cli quick-compare --preflight-only --agents kylinbot hermes` 作为验证命令。实测该参数**在宿主机与 VM 两份代码中都不存在**（`unrecognized arguments: --preflight-only`）——即这条命令在计划里写了、历史"已完成"也宣称了，但代码里从未实现。这与 2026-09-27 我发现的"计划任务 3 做了没勾"是同一类不一致，方向相反：**勾了/写了但没做**。
- **为何值得做**：它是唯一能在不看模型的前提下验证 Agent 是否就绪的官方命令，且正是"额度紧张时先确认再开跑"的正确工具。
- **实现（TDD）**：
  - 先写 2 个失败测试（`tests/test_quick_compare.py`）：`--preflight-only` 必须返回 `status=preflight`、`turns_started=0`，且**一旦调用 `run_suite` 就让测试失败**（用 `patch` 把它替换成抛 AssertionError 的桩），从而硬性证明零回合。
  - `QuickCompareOptions` 增加 `preflight_only`；`run_quick_compare` 在适配层预检后、进入 `run_suite` 循环**之前**早退，写出 `quick-compare.json`（含 `turns_started=0`、`blocked` 清单与 boundary 声明）。
  - `_select_profiles` 增加 `allow_not_runnable`：预检模式下允许对不可运行 Agent 做只读预检并如实报告为 blocked，而不是像正式跑那样直接拒绝（预检的目的正是把阻断原因报出来）。
  - 开发过程中测试抓到 2 个真实 bug：`blocked` 变量在早退分支之后才定义（`UnboundLocalError`）、以及选 profile 时提前抛错导致阻断项无法上报。均已修正。
  - CLI 增加 `--preflight-only` 并接线。
- **真实验证（VM，零消耗）**：把两个文件同步到 VM 后执行
  `python3 -m kmb.cli quick-compare --preflight-only --agents kylinbot hermes --out runs/preflight-check-20260928`
  → 产物：`status=preflight`、`turns_started=0`、`blocked=[]`、`kylinbot -> ready`、`hermes -> ready`，**结果目录下只有 `quick-compare.json`，没有任何 `result.json`/`evidence.jsonl`/`radar.svg`** —— 实证零回合、零 token。
- **纪律**：验证完成后把 VM 的 `quick_compare.py`/`cli.py` **还原为原备份**（否则 VM 的 `-r2` 副本就不再与 90/100 基线同代码，未来跑批的 PDF-16 数字会失去可比性），并删除 `/tmp` 临时文件。这个取舍值得记：验证功能用 VM，功能落地用仓库，两者不混。
- **回归**：全量 `Ran 131 tests, OK`（129 + 2 新测试），`compileall` 通过。

### 2. Hermes 就绪性预检（任务 4 遗留项的前置）

顺带用零消耗的适配层预检确认三 Agent 状态：`kylinbot/hermes/openclaw` 预检均 `ready`（各自 memory_store 与 command 检查通过），`hermes` 的 `state.db` 明确可观测。**Hermes 已具备纳入真实批次的条件**，只需等额度充足即可补跑；本轮未把它写成任何分数或结论。

### 当前待办（唯一）

仍是：**Token Center 补足额度 ≥150 万（请用户在 GUI 目视确认）→ 保证 VM 开机 → 重跑三批**。届时 PDF-16 有望 5/15 → 15/15（总分 90 → 100）。在此之前不发起任何消耗 model token 的操作。

## 余额需求精确核算（2026-09-28，应用户要求"确认多少余额足够，不要再让余额白费"）

方法：全部基于**已发生的真实消耗实证**，零 token 消耗（只读宿主机产物 + 已有的 402/余额快照），不再拍脑袋。

### 实测依据（三条独立证据互相印证）

1. **每次请求的计费 ≈ 37.6K token**：网关 402 回显 `requiredTokens=37,585~37,598`（r1/r2 多次一致）；我的探针实证"计费=实际 token"（20,006 prompt 的请求计 20,147）。
2. **每 Agent 每批 = 14 次模型请求**：`suites/quick.yaml` 6 案例共 14 回合（2+2+3+3+2+2），每回合 1 次请求。实证：r2 KylinBot 有效批次 evidence.jsonl 恰好 14 条 `user_message`（健康运行无重试放大）；openclaw 09-24 有效批次 12 条 `user_message`（2 例 error）。
3. **余额差值法锚定**：09-28 GUI 余额 1,513,569 → 我的探针消耗 80,345 → r3 跑批 ~2 分钟 → 用户目视 ~500,000。差值 ≈ **93.3 万 ≈ KylinBot 全批（14 请求×37.6K≈52.6 万）+ OpenClaw 中断前（~10 请求≈39 万）**，即 ~24 请求 × ~38.9K——与依据 1 吻合。

### 成本表（每请求 ~37.6K，每 Agent 每批 14 请求）

| 单位 | token 消耗 |
|---|---|
| 每请求 | ~3.8 万 |
| 每 Agent 每批（14 请求） | ~52.6 万 |
| **每批双 Agent** | **~105 万** |
| 2 批（评分器满分下限 batch_count>1） | ~210 万 + 15% 余量 ≈ **240 万** |
| 3 批（计划原口径 --repeats 3） | ~316 万 + 15% 余量 ≈ **365 万** |

### 结论与纠正

- **跑满 3 批（双 Agent）需要 ≈365 万，建议按 400 万准备**。
- **只跑 2 批也可让 PDF-16 拿满分**（`official_score.py` 判定条件是 `batch_count>1` 且有效率 100%，2 批即满足）：≈240 万，建议按 **260 万**准备。
- **明确纠正我此前的两个说法**："≥300 万"低估了余量（真实需 ~365 万）；今天说的"≥150 万"**只够跑 1 批，根本不够 2 批**——这正是 09-27 r2 轮"补了额度又不够"的根源。用户此前的额度之所以反复不够，是因为每批双 Agent 就要 ~105 万，而每日额度（基础 100 万 × 当前签到倍数 1.5× = 150 万/天）只够约 1.4 批。
- **低于对应阈值时绝不开跑**；开跑前我先做零消耗预检（`--preflight-only`，本轮已实现并验证）；开跑后第一批结束我会用"被拒请求触发 402"免费核对余量是否足以支撑剩余批次，不足以继续就立即止损（被拒请求不扣费）。
- 备选方案（不推荐但可行）：分 3 天每天跑 1 批（每日 150 万额度够 1 批 + 余量），用现有 `scripts/aggregate_repeats.py` 聚合三个 `repeat-*` 目录。缺点：需要验证聚合输出字段与 `official_score.py` 读取契约一致、跨 3 天操作、聚合属于证据组装（需透明记录），只在用户不愿一次补足时考虑。

## 2026-10-01：三批验收执行完毕——2/3 批有效，余额耗尽，PDF-16 仍 5/15（诚实记录含我的成本模型错误）

### 执行时间线

1. **预检（零消耗）**：VM 重启后适配器 `kylinbot/openclaw` 均 ready；**OpenClaw 网关端口 18789 在监听**（历史风险点：网关非 systemd 常驻，重启后可能不在——实测存活）；计费通路探针 177 token 通过。
2. **第一轮（runs/official-installed-20261001）**：repeat-01 完成但 **KylinBot 无效**——根因是**网关限流 429**（APISIX，`quick-recall` 窗口连续 3 次内部重试全 429 后进程退出 1；属外部瞬时扰动，非计费非行为）。当时判断：repeat-01 已带无效批 → PDF-16 满分已不可能 → **立即止损停批**（进程归零，repeat-02 半成品保留在目录内）。
3. **第二轮（runs/official-installed-20261001-r2，等 5 分钟限流窗口后重跑）**：
   - repeat-01：**kylinbot 有效 47.22 + openclaw 有效 27.78** ✓
   - repeat-02：**kylinbot 有效 33.33 + openclaw 有效 27.78** ✓
   - repeat-03：**双双 402 无效**（availableTokens 仅剩 26,019——余额在批次中途耗尽）
   - 最终聚合：`status=partial`，两 Agent 均 **2/3 有效（66.67%）**；KylinBot 均值 40.275/标准差 9.82，OpenClaw 均值 27.78/标准差 0.0。
4. **精确余额（强制 402 免费探测）**：**38,152**——约等于零。

### 我的成本模型错误（必须诚实记录）

我此前核算"每批双 Agent ≈105 万"的依据是"每批 14 回合=14 请求"。**这个假设错了**：Benchmark 回合 ≠ 模型请求——Agent 内部工具循环（kylinbot 的 memory 工具调用链、openclaw 的 agent loop）使每回合产生约 1.6 次真实模型请求。今日的硬数据修正了模型：

- GUI 余额 7,706,553（14:32）→ 现在 38,152：今日总消耗 ≈ **7.67M**
- 今日完成了约 4.5 个"批次对"当量的请求量（第一轮 1 对 + 半批；第二轮 2 对 + 2 案例）→ **每批对真实成本 ≈ 1.7M**（每 Agent 每批 ≈ 85 万），不是我此前以为的 105 万。
- 连锁后果：第二轮开跑时余额 ~5.1M，而 3 批真实需要 ~5.9M——**从一开始就差了约 0.8M**，注定倒在第三批。我给用户的"365 万足够"承诺因此落空，这是本次余额损失的根本原因，责任在我的模型精度，不在用户。
- （09-28 的 933K 差值锚点其实已暗示此值：我当时强行把它拟合为"kylinbot 526K + openclaw 40 万partial"，正确解读应是"kylinbot 全批 ~85 万 + openclaw 刚起步"。）

### 修正后的成本表（供后续决策）

| 项目 | 真实成本 |
|---|---|
| 每 Agent 每批 | ~85 万 |
| **每批双 Agent** | **~170 万** |
| **2 批**（评分器满分下限 batch_count>1） | 340 万 + 15% 余量 ≈ **390 万** |
| **3 批**（计划原口径） | 510 万 + 15% 余量 ≈ **590 万** |

### 纪律与证据状态

- **PDF-16 = 5/15 partial 不变**（两 Agent 各 2/3 有效，66.67% ≠ 100%），总分维持 90/100。失败批次（含 429 与 402 两次）全部保留在分母与目录中，**没有、也不会**用重跑"替换"失败批——那等于从分母删除失败。
- 但证据质量实质性升级：这是**首批真实行为稳定性数据**——openclaw 两有效批分数完全一致（27.78/27.78，stddev=0，与其 09-24 基线 13.89 同量级的稳定表现），kylinbot 两批 47.22/33.33（stddev 9.82，显示真实波动）。所有批次 strict verify 通过、`native_memory_events=0` 边界不变。
- 两轮产物均已拷回宿主机：`runs/official-installed-20261001{,-r2}/`（VM 原件未动）。

### 后续选项（需用户决策，涉及余额的操作我不会自行发起）

- **A. 一次性补足后重跑 2 批（推荐，最便宜的满分路径）**：补 ~400 万 → 新目录 `--repeats 2` → 若双批双 Agent 有效（概率较高：今日 4 批中 3 批全有效）→ PDF-16 15/15，总分 100。
- **B. 补足后重跑 3 批（计划原口径）**：补 ~600 万 → `--repeats 3`。
- **C. 零充值等待方案**：签到倍数明天 3.5×、第 7 天起 4.0×，每日自动入账 350-400 万（余额可累积）——**等 1-2 天什么都不做，余额自然到 4M+**，即可按 A 执行 2 批版。注意每日打卡不能断。
- **D. 就此收口**：90/100 + 首批真实稳定性数据（2/3 有效 + 方差）本身就是可辩护的交付；PDF-16 的 partial 是有数据支撑的诚实结论。

无论选哪条：开跑前我仍会做零消耗预检 + GUI 余额目视确认；跑批中途每批结束即核对剩余额度是否够剩余批次，不够立即止损（本轮监控机制已验证有效——两次止损都没烧无谓的钱）。

### 附：Token 消耗去向分析（2026-10-01，应用户"为什么跑这么多 token"之问，只读测量零消耗）

- **套件本体极小**：`suites/quick.yaml` 全部 6 案例 = **2,193 字节（约 700 token）**——测试题本身几乎不花钱。
- **Agent 上下文极大**：KylinBot 携带 940KB 技能（94 个 md/toml）、13.9KB config、记忆库 128KB；chat API 无状态，**每次请求都全量重发"系统提示 + 工具 schema + 技能 + 对话历史 + 注入记忆"**——实测单请求 ≈ 37.6K token，其中 >98% 是 Agent 自身上下文，<2% 是测试内容与输出。
- **乘法链**：14 回合 × ~1.6（Agent 工具循环）≈ 23 请求/Agent/批 × 37.6K ≈ 85 万；×2 Agent = 170 万/批对；×N 批。
- **输出侧可忽略**：实测 probe completion 141 token（含 101 reasoning）；案例回答量级相近，每批输出合计 ~1 万级，占比 ~1%。
- **不能省的部分**：裁剪技能/上下文/换模型都会改变"被测系统"本身（我们测的就是带完整上下文的系统级 Agent，不是裸模型），且破坏与 09-24 基线的可比性——不采用。
- **真正的省钱杠杆**：① prompt caching——探针实测网关 `cached_tokens: 0` 未启用；若网关侧开启前缀缓存，重发的系统+工具+早期历史可省 50-80%（这是 openKylin 网关的能力，非本项目可控，可作为对官方的改进建议）；② 跑 2 批而非 3 批（评分口径内即可满分）；③ 用每日签到倍数的自然累积替代一次性充值。

### 附：用户问"技能库/配置能否固定，之后直接发测试文件"（2026-10-01，分析答复）

- **harness 层做不到"只发测试文件"**：测试文件本来就只有 2.2KB（~700 token）；贵的是 Agent 自己构造请求时附带的上下文（系统提示/工具 schema/技能/历史/记忆，实测 37.6K/请求）。评测器通过 stdin 把案例 JSON 喂给 kylin-bot/openclaw CLI，**请求由被测 Agent 自己构造**——harness 无法替它剥掉上下文，否则被测系统就被改掉了。
- **"固定不重发"的正规机制是服务端 prompt caching**：DeepSeek 后端原生支持自动前缀缓存（同前缀第二次起按缓存价计）；实测网关返回 `cached_tokens: 0`（未给折扣），但单探针不能下结论——需"同前缀双请求 + 402 读余额差值"实验（成本约 1 万 token）才能定论：若网关真有缓存折扣，成本模型直接砍半，全部后续方案受益；若网关按全价记账，则缓存对用户不可见，只能向官方提改进建议。
- **不可接受的省法**：裁剪技能库/系统提示=改变被测系统（测的就不是 openKylin 上真实的 KylinBot 了，且破坏与 09-24 基线可比性）；让 Agent 跨案例复用会话=案例间记忆污染，直接破坏评测效度。两者都不采用。
- **我们这一层真正能"固定"的是环境指纹**（零成本）：技能树 SHA-256 + config.toml SHA-256 + Agent 二进制版本，跑批前记录并归档进批次目录——现有 provenance 只记了 suite/scorer 哈希（agent version=unknown）。它的价值不是省钱，而是**让"分批/跨天跑"科学成立**：今天跑批 1、明天跑批 2，只要指纹一致即批间可比——这正好配合"等签到 4.0× 每日入账 400 万后分批跑"的零充值路线。

### 环境指纹固定——已完成（TDD，3 个新测试；VM 真实环境首次采集成功）

- **新工具**：`scripts/agent_env_fingerprint.py`（纯 stdlib、只读、确定性）：对每个 Agent 的 config / 技能树 / 可执行文件做 SHA-256 指纹；只输出哈希、文件数、字节数与相对路径，**绝不输出文件内容**（防密钥泄漏，有专门测试断言）；容忍路径缺失；记忆库刻意排除（official_repeat 每批清空记忆表，其内容不影响计分批）。
- **测试**：确定性+变更敏感（改一个技能文件指纹必变）、不含内容/密钥、缺失路径不崩（全 missing 时指纹为 `missing`）。全量 **134 项测试 OK**。
- **VM 真实首采**（2026-10-01，`runs/env-fingerprint-20261001.json`，VM 原件在 `-r2/runs/` 同名）：
  - kylinbot  `e943ece7d8b77a19…`：config 13.9KB + 技能 108 文件/462KB + 二进制 32.2MB（/usr/bin/kylin-bot）
  - openclaw  `b11a5e9cc68e64b0…`：config 2.3KB + 技能 89 文件/372KB + 二进制 22.4KB（/usr/bin/openclaw，npm 垫片——局限：node_modules 变化不体现，已在日志注明）
  - hermes    `ffac09621bef1bfd…`：仅 config 5.2KB（非交互 shell 中 `hermes` 不在 PATH，二进制项跳过——采集命令会自动跳过空解析）
- **用途**：今后每次跑批前执行同一命令，把指纹归档进批次目录；两批指纹一致 ⇒ 环境同一 ⇒ 跨天/分批的分数可比。这使"等签到 4.0× 每日入账、分批跑 2 批"的零充值路线在证据层面成立。
- 使用命令（已验证）：`python3 scripts/agent_env_fingerprint.py --agents kylinbot openclaw hermes --bin kylinbot=$(command -v kylin-bot) … --out <批次目录>/env-fingerprint.json`

### Prompt Caching 实验——完成（实测 8,228 token，预算 1 万内；结论明确）

**协议**（用户批 1 万预算，VM 内执行）：强制 402 读初始余额（免费）→ 请求 A（4K token 前缀）→ 402 读扣费 → **请求 B（字节级相同前缀 + 2 token 后缀）** → 402 读扣费 → 对比。请求 B 实测 `cached_tokens=3,584`（=56×64，恰好是 DeepSeek 64-token 块对齐的命中率）。

**结果**：

| 请求 | prompt | cached_tokens | API 计费 total | Token 中心扣减 |
|---|---|---|---|---|
| A（首次） | 4,006 | 0 | 4,171 | 4,171 |
| B（同前缀） | ~4,009 | **3,584（89% 命中）** | 4,057 | **4,057（几乎无折扣）** |

- 余额对账：38,152 → 29,924，差值 8,228 = A+B 的 API 计费之和，**两次 402 探针确认未扣费**。
- **结论**：① DeepSeek 后端的自动前缀缓存**穿透网关在真实工作**（89% 命中率）；② 但 **Token 中心按全价扣费**——缓存折扣没有传导给用户（若传导，B 应只扣约 800 而非 4,057）。
- **对本项目的含义**：在当前网关计费下，"固定技能库/上下文"**省不了钱**——后端缓存命中也按全价扣。成本模型维持 170 万/批对不变。
- **对 openKylin 官方的改进建议（有实证支撑）**：把 DeepSeek 的 cache-hit 定价传导到 Token 中心扣费。实测 89% 的前缀命中率意味着：若传导，跑批成本可降 3-5 倍（每批对 170 万 → 约 40-60 万）， KylinBot/OpenClaw 每请求约 3.4 万 token 的系统上下文（技能/工具/人设）正是缓存命中的大头。这将同时惠及所有生态评测与日常用户。
- 中途小插曲：3 次 402 读数一度返回无 `data` 字段的 JSON（疑似限流态错误体），读数显示"?"——事后余额对账证明这些读数未产生任何扣费；最终一次读取拿到精确值。

### 余额 350 万够不够（2026-10-01 晚，应用户之问；基于今日全量回合计数的精确校准）

- 今日实证：总消耗 7,668,403（7,706,553−38,152）÷ 今日计费回合 **89 回合**（+被打断的 run1-repeat-02 约 8 回合未入证据 ≈97 回合）≈ **7.9 万 token/回合**（含工具循环 ~1.6 请求/回合与重试）。
- 校验：run-2 两个干净批对 = 56 回合 × 7.9 万 ≈ 442 万 → **每批对 ≈ 220 万**，与今日总量模型吻合。
- **结论**：350 万 **够跑 1 批对**（~220 万）但 **不够跑 2 批**（需 ~440 万，加余量建议 ≥450 万）；而 PDF-16 满分要求 `batch_count>1`——**单跑 1 批拿不到任何分数提升，等于白花 220 万**。
- **建议**：今天不跑；明天签到（第 6 天 3.5×，入账 ~350 万）后余额 ~700 万，跑 2 批绰绰有余。环境指纹（已落地）保证跨天批次环境同一，分数可比。

### 今日 7.67M 消耗的价值清算（2026-10-01 晚，应用户"之前跑的还有用吗"之问）

- **对分数：沉没**。PDF-16 仍 5/15，且今天的 2 个有效批**不能**结转到未来跑批的汇总里（跨 run 拼装证据 = 变相删除失败批/重摇骰子，纪律禁止）。未来跑批必须自己攒 2 个有效批。
- **对交付物：四项真实资产**：
  1. **首批真实稳定性数据**：OpenClaw 两有效批 27.78/27.78（σ=0，高度确定性）；KylinBot 47.22/33.33（σ=9.82，真实波动）——可直接写进稳定性报告（计划任务 3 的 docs/innovation-stability-report.md），也是"用数据说话"的评测素材；
  2. **两类外部失败的完整实例**：429 限流（网关 APISIX 瞬时）与 402 余额（耗尽），失败分类纪律首次在真实场景同时落地，且都是给 openKylin 官方的反馈素材（连同缓存实验的 89% 命中率/全价扣费证据）；
  3. **成本模型校准**：79K/回合、220 万/批对、440 万/2 批——今天的"学费"锁定了未来每一分钱的预算精度；
  4. **installed 模式全链路实证**：隔离 HOME/清空记忆/证据链 strict verify/聚合统计全部真实跑通——未来 2 批冲分跑在操作层面已被去风险（剩下的唯一变量就是余额够不够）。
- **可选收口动作（暂不做）**：把今天部分有效的 repeat 证据附加到新验收目录重生成评分卡——分数不变（90），但 PDF-16 理由从"未附证据"升级为"有真实批次，2/3 有效+方差"。若将来 2 批跑满，评分卡会以满分重生成，此步可省；若最终不跑了，此步值得做。

### 最终预算承诺（2026-10-01 晚，回答"到底需要多少 token"）

- **跑 2 批一次到位：600 万 token**。算术：56 回合（2 批 × 28）× 8.6 万/回合（今日全含实测单价，含重试与工具循环）≈ 480 万 + 重试缓冲 ~110 万 ≈ 590 万，取整 600 万。
- 用户现有 350 万；明天签到（3.5×）入账 ~350 万 → 700 万 ≥ 600 万，**零充值即可达标**；或今天补 250 万立即跑。
- 三条止损承诺：① 开跑前零消耗预检 + 环境指纹归档 + GUI 余额目视确认；② 第 1 批结束即核对"双 Agent 有效 + 余量 ≥290 万"，任一不满足立即停（损失上限 ~240 万）；③ 任何 429/异常立即停批（今日已两次验证止损机制有效）。
- 全部成功后：重生成 scorecard（90→100）并同步文档；若用户最终选择不投入：90 分 + 今日真实稳定性证据收口（PDF-16 部分有效的证据附加动作备而未做）。

### 方法论澄清（2026-10-01 晚，用户以截图质问"之前跑的到底能不能用"——我此前的表述确实含糊）

**我此前说"指纹让跨天/分批跑出的分数才可比"，没有把前提说全，造成了"今天的两个有效批可以留用"的错误印象。精确规则如下：**

1. **一个系列的分母 = 该系列实际执行的全部批次（含失败批）**。今天的 run-2 系列 = [有效, 有效, 402无效]，已闭合，66.67% 就是它的最终结果，不可更改。
2. **禁止**：从含失败批的旧系列里挑出有效批，与未来新批拼成新分母——这是选择性拼装，等价于删除失败批，纪律明确禁止。
3. **允许**：开启一个**全新的系列**（一次 `--repeats 2` 调用、新目录），其分母只含该次调用执行的批次——跑 2 批全有效即 100%。计划原文"得到完整有效批次后，才能用真实数字更新 PDF-16 结论"预期的正是这条路；历史先例（90/100 基线引用特定日期的完整批次）也是"最新完整系列为当前证据"。
4. **指纹的真正作用**：不是把旧批捞进新分母的工具，而是服务于"**预先声明**的跨天系列"（如额度受限时声明"系列=两天各 1 批"，两批连同失败批全部进分母，aggregate_repeats 聚合）时证明环境同一。若一次调用即可跑完（明天余额充足时的方案），指纹仅作环境存档。
5. **今天的批次用途最终定论**：作为分数——不能用（留在今天已闭合的 66.67% 分母里）；作为证据资产——四项（稳定性数据/失败分类实例/成本校准/链路去风险），已入稳定性报告素材与 openKylin 反馈。

### 深度预算重算（2026-10-01 深夜，应用户"究竟需要多少 token 才能保证不失败"之问）

**历史失败源逐一封堵分析**（今日 7.67M 学费换来的完整清单）：

| 失败源 | 实证 | 封堵手段 | 代价 |
|---|---|---|---|
| 402 余额耗尽 | 09-27 ×2、10-01 run2 批3 | 预算按实测 85K/回合 × 余量；每批结束对账，不足即停 | 计入预算 |
| 429 网关限流 | 10-01 run1（14:34 午后）| ①晨间低峰启动 ②启动前 20RPM 金丝雀（~3K token，不通过不启动）③批内出现即当场止损 | 重跑储备 |
| 行为波动 | 今日各批均有行为性失败 | **实证不构成威胁**：行为失败只降分不使批次失效（run-1 的 openclaw 在 429 下仍 valid；run-2 kylinbot 47.22 含行为失败仍 valid）——使批次失效的只有 error 级案例（进程崩溃/402/超时） | 零 |
| 环境漂移 | 无 | 环境指纹归档（已落地） | 零 |

**预算结构（每"尝试"= 一次 --repeats 2 调用）**：

- 基础：56 回合 × 8.5 万/回合（今日实测区间 77-90K 取保守值）≈ **480 万**
- 重试缓冲：健康跑批时 runner 重试仅由 exception 触发（402/429/超时），预算充裕后接近零；留 **60 万**
- **单次尝试 ≈ 540 万**
- **完整重跑储备**（吸收一次 429 止损后从头再来）：+550 万
- **封顶承诺：1100 万**。顺利时实耗 ~540 万，储备原封不动退回（=不消耗）。

**资金路径（零充值）**：今日余额 350 万 + 10-02 签到 350 万（3.5×）+ 10-03 签到 400 万（4.0×）≈ 785 万 → 只够 600 万档（无储备，成功率约 85%）；再 + 10-04 签到 400 万 ≈ 1185 万 → **1100 万档（成功率 ~99%，可吸收两次独立 429）**。想提前：现在充值 750 万即达。

**金钱买不到的两点（诚实声明）**：① 429 是网关外部负载，只能用储备吸收、低峰+金丝雀规避，无法根除；② Agent 行为分数本身有真实波动（kylinbot σ=9.8），但评分只看批次有效性，不影响满分判定。

## 🎯 里程碑：官方自评分 100/100（2026-10-04 晚）

**当日执行时间线（全部有命令与产物背书）**：

1. 预检全绿：VM 开机；kylinbot/openclaw 适配器 ready；OpenClaw 网关 18789 存活；网关 3×200 稳定性；**环境指纹与 10-01 完全一致**（kylinbot `e943ece7…`、openclaw `b11a5e9c…`）；20 RPM 金丝雀 20/20 零限流。
2. **验收批次**（`--repeats 2 --out runs/official-installed-20261004`，VM 内与基线同代码副本）：
   - repeat-01：KylinBot **valid 63.89**（与 09-24 基线完全同分）| OpenClaw **valid 22.22**
   - repeat-02：KylinBot **valid 61.11** | OpenClaw **valid 22.22**
   - `repeat-summary.json`：`status=completed`、双 Agent 有效率 **100.0%**、batch_count=2>1——PDF-16 满分判定条件全部命中；strict verify 通过；`secrets_written=false`。
3. **评分**：批次拷回宿主机 → 新离线验收 `runs/official-final-20261004`（pass）→ 附加 repeat 证据 → `official_score.py` → **`total=100, max_total=100`**（PDF-16 15/15 pass）；`official-review.html`/`scorecard.json`/`scorecard.md` 已生成。
4. **文档同步**：`docs/official-scorecard.md`（100/100 + 稳定性证据边界重写，90/100 历史基线与全部失败系列保留不删）、`docs/release-freeze.md`、`docs/requirements-traceability.md`、`docs/pdf-compliance-audit.md`（追加 2026-10-04 更正节）、`docs/innovation-stability-report.md`（VM 双 Agent 稳定性数据）、`tasks/todo.md`、计划文件（勾选任务 3 步骤 4/5 + 追加执行记录）。
5. **回归**：全量 134 项测试 OK；HEAD 仍 `144fc4a`；git status 88 条（新增今日批次产物与文档改动），无 commit。

**额度纪律兑现情况**：本日消耗 = 批准的缓存实验 8,228 + 金丝雀 ~3,000 + 验收两批 ~440-480 万（无重跑、无 429、无 402）——预算 1100 万封顶未触顶，重跑储备分文未动。**承诺的"这次不失败"兑现。**

**稳定性数据（写进 innovation-stability-report）**：KylinBot 63.89/61.11（σ1.97，两批差 2.78 分）；OpenClaw 22.22/22.22（σ0，完全一致）；批次内行为失败与历史基线同源、无 error 级案例。`native_memory_events=0` 边界不变——满分不改变"系统级观测"的表述边界。

**遗留清单（最终状态）**：PDF-12 桌面视频与项目级 LICENSE——用户要求排除，永不报告完成；deb 安装/升级/卸载矩阵——工具就绪待 VM 交互 sudo；Hermes——VM 内 runnable，可作为后续可选增强；B 轨真实调用——待宿主机凭据。

## B 轨真实调用 + Hermes 矩阵补全（2026-10-04 晚，续"接着进行"；消耗 ~250 万 / 752.9 万）

### 1. B 轨真实 LLM 工具调用——完成，顺带抓到并修复一个真实 bug

- **接线**：`memory_tool` 配置新增 `backend:` 块（openKylin 网关 + `deepseek-v4-flash`，`api_key_env=OPENKYLIN_TOKEN_API_KEY` 仅经环境变量注入、密钥未落盘未回显），创建 `configs/agent-b-memory-{kv,similar}-real.yaml`。
- **首轮即翻车（这正是真实验证的价值）**：6 案例只跑成 2 个，5 例 `unsupported_action`/400——根因是 **`OpenAICompatibleToolBackend.begin_turn` 在模型纯文本回答时向对话历史写入 `tool_calls: []` 空数组**，DashScope 系后端（openKylin 网关背后是 DeepSeek）直接 400："Empty tool_calls is not supported"。离线测试从未打过真实 API，所以从未暴露。失败证据保留于 `runs/b-track-real-20261004/`。
- **TDD 修复**：新测试 `test_tool_backend_omits_empty_tool_calls_from_history`（红）→ `begin_turn` 改为仅在存在工具调用时携带 `tool_calls` 键（绿）→ 全量 **135 项测试 OK**。
- **修复后正式跑**：
  - KV（甲）：**94.44，score_valid=true**，strict valid（79 事件）；门禁四条件全中——跨轮写 6、召回 3、更新 1、assistant 输出 14，动作文件工件含 SHA-256；
  - similar（乙）：**77.78，score_valid=true**，strict valid（80 事件），相近实体区分与敏感拒绝由真实模型决策触发。
- **边界**：B 轨升级为"真实模型决策 + 本地记忆层执行"（`source=model` 与 `source=memory_layer` 并存），`native_memory_events=0` 不变——仍不是模型原生长期记忆。
- 顺带发现：网关不严格执行 `max_tokens`（返回超长补全），单请求计费略高于请求值——已记录。

### 2. Hermes 真实批次——四 Agent 矩阵生态侧补全

- VM `quick-compare --agents hermes kylinbot`（`runs/quick-compare-hermes-20261004/`）：
  - Hermes：**22.22，score_valid=true**（34 事件，行为类失败：omission 3/stale_update 1/confusion 2/erroneous_reuse 2，无 error 级）
  - KylinBot：**47.22，score_valid=true**（51 事件）
  - 双侧 `verify_run.py --strict` 退出码 0。
- Hermes 与 KylinBot/OpenClaw 同台同套件的第一个真实分数；KylinAgent 维持安全阻断（等官方结构化证据）。

### 本轮额度消耗

- 缓存实验 8,228（前批已记）+ B 轨两轨 + Hermes 批对 ≈ **~250 万**（余额 752.9 万 → 剩余约 500 万）。所有运行 strict valid，无浪费。

## deb 安装/升级/卸载矩阵——完成（2026-10-04 晚，openKylin 3.0 VM；零 token 消耗）

- **解锁方式**：用户在 VM 自己的终端里执行一条命令临时授予免密 sudo（密码未经过我），矩阵跑完后我立即删除 `/etc/sudoers.d/cisyam-nopasswd` 并验证 `sudo -n true` 恢复"需要密码"——安全姿态已还原。
- **七步全 0**（产物 `runs/deb-lifecycle-3.0vm-20261004/`，30 个文件，与 rerun6 同构）：
  1. preflight（id）→ 0
  2. install **release6**（`dpkg: 设置 kylin-memory-bench (0.2.0+release6)`）→ 0
  3. verify_before_upgrade（包内 smoke：reference/flawed 各 6 案例）→ 0
  4. upgrade **release7**（`解压 …(0.2.0+release7) 并覆盖 (0.2.0+release6)`）→ 0
  5. verify_after_upgrade → 0（双侧 strict valid，34 事件/侧）
  6. uninstall → 0
  7. residual_check → 0（`/usr/bin/kmb`、`/usr/share/kylin-memory-bench` 均不存在）
- 至此 `.deb` 在 openKylin 3.0 VM 的完整生命周期证据补齐（此前仅 09-08 旧 VM 与包内解包 smoke）；文档已同步 `docs/release-freeze.md`、`docs/requirements-traceability.md`。
- 全程零 token 消耗（dpkg 本地操作 + 包内离线 smoke）。

## 代码提交完成（2026-10-04 深夜，应用户"执行1"指令）

- **提交前纪律**：全量密钥扫描（sk-/私钥/Bearer/字面 api_key/password 模式）——唯一命中是 `tests/test_agent_env_fingerprint.py` 的测试夹具假密钥（安全）；`configs/agent-openkylin-token.yaml` 确认只有 `api_key_env` 变量名引用；`research/`（84KB 调研报告，被导出规格引用）纳入；`enable-vmnet-diagnostics.ps1`（无文档引用的宿主机一次性诊断脚本）加入 .gitignore。
- **身份**：复用仓库既有作者 `arch <212667660-arch@users.noreply.github.com>`（本机未配置 git identity，从历史提交恢复）。
- **两个提交**（未 push，origin 存在于 github.com/212667660-arch/kylin-memory-bench，推送与否由用户决定）：
  - `97543ba` feat: official acceptance readiness — 代码/测试/配置/套件/脚本（含 agent_adapters、memory_modules、official 系列、指纹工具、49 案例、B 轨 real 配置）
  - `211e19c` docs: scorecard/traceability/freeze to 100/100（README/docs/tasks/research/工作日志；B 正式勾选）
- **提交后状态**：工作区 **0 未提交变更**；全量 135 项测试 OK；runs/ 与 dist/ 按既定 .gitignore 继续留在本地（证据目录以文档路径引用，为仓库既有约定）。
- 注意：`runs/`、`dist/` 不入库是仓库既有约定（.gitignore 首版即如此），评分证据在本机保留并可复现；如需随仓库分发证据，需要用户显式决定改变该约定。

## 发布动作：push + 100/100 发布包（2026-10-04 深夜，应用户"开始进行"）

- **push**：`fc9d284..211e19c main -> main`（github.com/212667660-arch/kylin-memory-bench；远程原落后 7 个提交，快进合并，未强推）。未配置全局 git 身份，已复用仓库既有作者 `arch` 到本仓库 local 配置。
- **发布包**：`dist/official-bundle-20261004/`（192 文件 + manifest=193）——`build_official_bundle.py` 构建，`audit_official_bundle.py --strict` **pass 无 issue**。抽查确认：指纹工具/official_score/49 案例套件/评分卡/计划文档均在；`runs/`、`.env`、`research/` 已排除；`docs/migrate-openkylin-20260918/` 作为项目文档保留。manifest format=`kmb-official-bundle-v1`。
- **提交收尾**：本节日志以 `docs:` 小提交入库（工作日志为仓库文件，保持与提交同步）。

## KylinAgent 深度侦察——"等官方"结论被推翻，解锁路径实证存在（2026-10-04 深夜）

用户指示"先做3"（KylinAgent 结构化证据问题）。零成本只读侦察（SSH + 本地 GET），**三项关键发现**：

1. **架构真相**：`~/.kylin-agent-runtime/` 的运行时服务就是 **hermes-agent 平台**（进程 `agent-runtime/venv/bin/hermes gateway run`，pid 1930），监听 **127.0.0.1:8642**；Qt GUI（经 `~/.cache/kylin-agent.socket`）只是它的前端之一。KylinAgent = openKylin 基于 hermes-agent 引擎的发行形态。
2. **结构化证据一直在磁盘上**：
   - `state.db`（3.9M）：34 会话 / 285 消息，**完整 tool_calls 字段**——模型真实调用过工具：**memory ×25**、read_file ×47、terminal ×30、search_files ×23、execute_code ×6、write_file ×2；
   - `sessions/*-details.log`：**JSONL 事件流**（`model.request`、`delegation.router.decision` 等，含 provider/model 字段）；
   - `sessions/*-usage.log`：逐调用 token 计量（input≈11.6K/调用——KylinAgent 的上下文远小于 KylinBot 的 37.6K，且有 cache_read=3,584 的前缀缓存命中）。
3. **本地 HTTP API 可驱动**：`GET /health`→`{"status":"ok","platform":"hermes-agent"}`；`GET /api/sessions` 列会话；`GET /api/sessions/{id}/messages` 返回完整结构化消息（role/content/tool_calls/reasoning_content/timestamp）。会话列表里能看到历史测试对话（"我的项目代号是Atals"，source=desktop）。

**解锁路径（待建工程）**：为 kylinagent 写 HTTP 驱动适配器（POST 会话消息端点，GUI 同款路径）+ 结构化证据导出（state.db/details.log → `source=memory_layer`/`model` 事件，与 B 轨标记规则一致）→ 预检从 blocked 转 ready → 真实批次。**成本预估**：每回合 ~12-15K token，6 案例批次 ≈ **30-40 万**（远低于 KylinBot 的 220 万/批对）。

**待用户拍板的一点**：驱动路径写进**真实 state.db**（会污染日常使用的 KylinAgent 数据）vs **克隆运行时目录起隔离实例**（干净但要解决第二个实例的端口/配置指向）。存量证据已证明 memory 工具被真实调用，解锁的科学价值明确。

侦察过程全只读、零 token 消耗。

## KylinAgent 解锁工程——工程完成，最后卡在 openKylin 网关 bug（2026-10-05，诚实停点）

**用户拍板 B 路线（隔离实例）后完成的工程**：

1. **驱动器** `scripts/kylinagent_driver.py`（CommandAgent 协议，stdin=案例 → stdout=证据 JSONL）：映射函数 TDD（6 测试，含"不得伪造键值写事件"的不变量）——KylinAgent 的 memory 工具是**会话检索范式**（`{query,limit}` → FTS 搜索过往会话），映射为 `memory_recall(key=query, hit, value=snippet)`；**无键值写路径，绝不伪造 memory_write**。
2. **隔离实例**：`~/kmb-kylinagent-isolated-20261004/`（config+auth 克隆、状态全新）+ `HERMES_HOME/AGENT_RUNTIME_HOME` 重定向——实测隔离目录生成独立的 `kylin_agent_runtime_state.db`/`memory.db`/`sessions/`，用户日常数据零接触。
3. **证据提取实证**：14+8 条 `memory_recall(memory_layer)` 事件、模型工具调用（memory/terminal/write_file）全部结构化捕获；`native_memory_events=0` 边界不变。

**过程中诊断并解决/定位的三层问题**：

| 层 | 问题 | 处置 |
|---|---|---|
| 驱动层 | Agent 横幅污染 stdout（CommandAgent 逐行 JSON 解析会崩） | 交互期 sys.stdout→stderr 重定向 |
| runtime 层 | 隔离库无 FTS 索引（聊天持久化先建库，schema 迁移被版本检查跳过）→ memory 搜索全 0 命中 | 驱动启动时用 runtime 自带 `FTS_SQL` 建表+回填；修复后 **8 条 recall 命中 4 条** |
| runtime 层 | 流式传输挂死（`model.transport.start, streaming:true` 后无完成事件）| 用 runtime 自带降级钩子 `agent._disable_streaming=True` → 转非流式 |

**最终阻断（openKylin 网关侧 bug，证据已固定）**：非流式模式下，特定确定性载荷（`terminal ls` 执行后的第 5 次模型请求）**网关不返回**——`model.transport.start(streaming:false)` 后日志终止，连接挂死直到 runner 600 秒超时。同 seed 四轮复现（r2/r3/1005 两轮），流式与非流式皆中；terminal 输出无控制字符；guardrails/超时调整无效。这是网关对特定请求载荷的编码/处理缺陷，harness 无法绕过。

**四轮 KylinAgent 运行的诚实产出**（`runs/kylinagent-real-2026100{4,4-r2,4-r3,05}/`，~160 万 token）：
- 结构化记忆证据提取链路完全打通（memory_recall 命中含过往会话片段）；
- **架构发现**：KylinAgent 记忆=会话检索范式——(a) 无键值写事件；(b) **边界案例真实失败**：临时 OTP 被会话索引并在后续检索中复述（`confusion` 失败）——检索型记忆没有"拒绝存储"概念，这是与 KV 型 Agent 的实质差异，已记录；
- 完整有效批次未达成：`score_valid=false`（error 级超时），KylinAgent 在矩阵中保持"已解锁驱动、批次受网关 bug 阻断"的状态。
- **恢复条件**：openKylin 修复网关挂死（或将挂起载荷证据 `runs/kylinagent-real-20261005/evidence.jsonl` + details.log 提交官方复现）后重跑同一命令即可。

## LICENSE 生效（MIT）——完成（2026-10-05；提交本地，push 待网络恢复）

- **决策依据**：用户授权"比赛允许的都可用，按推荐执行"。通读赛题 PDF（交付要求 a-e、评审维度六项）——**未对许可证类型设限**；按工程建议选 MIT（候选文本已备、与 PyYAML 同许可、最利于 `.deb` 进 openKylin 软件源分发）。
- **生效动作**：根目录 `LICENSE` 创建（标准 MIT，版权主体 "KylinMemoryBench project contributors"）；`LICENSE-MIT-CANDIDATE.txt` 删除（使命结束）；`NOTICE`/`docs/license-decision.md` 记录决定（2026-10-05 负责人确认）。
- **评分器动态化（TDD）**：`official_score.py` 的 LICENSE 限制文案与 PDF-18 理由改为按根目录 `LICENSE` 存在性动态判定（新增测试 `test_license_limitation_reflects_root_license`——在场报"已生效(MIT)"、缺席报"未处理"）；`excluded_from_score` 不变（LICENSE 仍不计分，评分模型保持 100/100）。
- **文档清扫**：release-freeze / pdf-compliance-audit / requirements-traceability / README / deb-release / official-scorecard / todo / environment-matrix 共 9 处"未确认/未创建"表述全部更新。
- **发布包**：`dist/official-bundle-20261005/`（194 文件）——`build_official_bundle.py` 的 INCLUDE_FILES 由候选文件改为 `LICENSE`（新增测试 `test_official_bundle_ships_active_license`），strict 审计 pass，LICENSE 随包分发 ✓；评分卡重生成（100/100 保持，边界文案更新）。
- **回归**：全量 **143 项测试 OK**（+2 LICENSE 相关）。
- ⚠️ **push 未完成**：提交 `6b96ac1`（LICENSE）与 `842a43d`（KylinAgent 驱动）在本地待推送——GitHub 443 连接被重置，3 次退避重试全败（网络恢复后 `git push origin main` 即可）。

- **push 补录（2026-10-05 晚）**：网络恢复，`41cc657..f3209b5 main -> main` 推送成功——KylinAgent 驱动、LICENSE 生效与工作日志全部入库，本地与远程一致（0 未提交）。

## 官网比对（2026-10-05/10-10，oschina.net/os2026 全文提取）

- **官方提交材料（参赛指南 02）= 三项**：① 代码仓库链接（完整可运行）✓；② **作品介绍文档（推荐 PDF）**：项目背景、技术架构、应用场景、创新点——**这就是"方案说明文档"的正式提交形态，尚未汇编（素材全齐）**；③ **作品演示视频链接**（需展示核心功能与使用流程）——注意要求是"链接"，录完需上传公开平台。
- **提交方式与截止**：打包附件发 oscc@oschina.cn，**10 月 16 日 24:00 截止**（今日 10-05，余 11 天）；流程=官网报名 → 邮件确认 → 按指引提交。
- **赛程**：入围公布 10-21；**线下总决赛 10-29**（上海浦东 AI 小镇服务中心 3F，入围须现场路演，结果当日公布）——用户所说"PPT"即路演材料，属入围后事项。
- **评审维度修正**：官网总维度=技术创新 30% + 场景落地 30% + **开源治理 20%（协议与依赖合规、贡献机制与文档规范）** + 长期发展 20%；企业命题任务书的六维度为专项评分，两层都算。**MIT LICENSE + NOTICE + THIRD_PARTY_NOTICES + license-audit 直接对应"开源治理"维度的准备** ✓。
- **许可证确认**：官网无数值性许可证要求，"协议与依赖合规"由 MIT + 第三方边界文档满足——MIT 推荐成立 ✓。
- **奖金**：一等 10 万（现金/Token 各半）、企业命题选做额外"最佳探索奖" 6000×12（我们做了企业命题 ✓）。
- **待确认（用户操作）**：官网报名表单是否已填（流程要求先报名拿确认邮件，才能提交作品）。

## 提交材料冲刺（2026-10-10/11，截止 10-16 24:00）

1. **.deb 重打完成**：`kylin-memory-bench_0.2.0+release8_all.deb`（235KB）在 openKylin 3.0 VM 上用当前代码构建——修复 `build_deb.sh` 引用已删除候选文件的问题（改为安装生效的 `LICENSE`）；包内确认 49 案例套件/指纹工具/评分器/LICENSE 在位；`dpkg-deb --info/-c` 校验通过。构建中发现并修复 **CRLF 坑**（宿主机工作副本 `.sh` 为 CRLF，同步后 bash 报语法错误）——VM 侧统一转 LF，并新增 `.gitattributes`（`*.sh text eol=lf`）防复发。
2. **作品介绍文档 PDF 化**：`docs/作品介绍文档.md` → 样式化 HTML（微软雅黑）→ Edge 无头打印 → `dist/submission/作品介绍文档.pdf`（430KB）。
3. **提交包骨架组装**：`dist/submission/`（2.2MB、134 文件）——作品介绍文档.pdf + release8 .deb + sample-evidence（真实双 Agent 批次/100 分评分卡/Hermes 对比/deb 生命周期）+ README-提交说明（官网三材料对照、一键复现命令、边界声明）+ 演示脚本。**唯一空位：视频链接（等用户录完上传）**。
4. **push 仍被网络阻断**：本地累计 4 个提交待推送（GitHub 443 持续拒连，今日多次重试）——提交本身安全，恢复后一次推送。
- 回归：全量 143 项测试 OK。

- **push 全部完成（2026-10-11，SSH 通道）**：GitHub HTTPS 持续被阻断，诊断发现 SSH 端口可达但本机密钥未注册——用户将 `codex-openkylin-vm` 公钥加入 GitHub 后，`~/.ssh/config` 指定 GitHub 使用该钥匙，`cdca012..61463c3` 全部推送成功，本地与远程一致（0 未提交）。今后 push 走 SSH，不再受 HTTPS 阻断影响。

- **配置清理（2026-10-11，应用户要求）**：删除 7 个历史云供应商配置（grok×3 / deepseek×3 / doubao）与被 100/100 官方流程取代的旧验证脚本 `openkylin_full_validation.sh`——配置从 20 → 11 个（reference/flawed 基线、kylinbot-process/command、openkylin-token、B 轨四件套、接入模板）；工作台"API/模型"页实测 18 → 11；release8 .deb 重新构建（234KB，仅含必需配置）；143 测试全绿。历史 runs/ 证据（Grok/DeepSeek 对照）不受影响——它们是过去的运行记录，不依赖配置文件存在。

## 工作台界面自审与修复（2026-10-11，录屏前自审）

用户要求审视前端。五个页面走查 + 代码对照，发现并修复：

- **P0 平均分污染**：总览"最近使用智能体"把无效批次（`overall=null`）当 0 分平均（`Number(null)`===0 的 JS 陷阱）——KylinBot 显示 28.15 与真实批次 63.89/61.11 矛盾。修复：空值守卫 + 元信息标注有效次数。修复后 **KylinBot 52.78（45 次·24 有效）、OpenClaw 33.33（42 次·21 有效）**，与官方评分口径一致。
- **P0 "固定运行"显示混乱**：`runs/test-retry` 的 run_id 字面就是 `fixed-run`，被 UI 映射机械翻译成"固定运行"且带"状态未观测/不稳定"假字段。修复：移除内部类别名的机械翻译，按原文显示。
- **P0 "真实智能体 A"命名误导**：replay 示例模板被显示为"真实智能体 A"→ 改为"回放示例（模板）"。
- **P1 新建评测默认值偏航**：默认选中 B 轨配置+旧套件 → 改为 **reference vs flawed**（离线零凭据、演示安全）。
- **P1 凭据横幅文案**：泄漏实现细节（"隐藏输入命令/VM 凭据不同步 Windows"）→ 改为动作导向。
- 过程中插曲：修复后页面短暂空白——排查发现是**两个 serve 实例抢占 8080 端口**（Windows SO_REUSEADDR 允许双绑定），请求随机命中新旧进程；杀掉重复实例后一切正常。数据接口逐一验证（/api/system,runs,configs,suites,agents 全 200 且 JSON 有效）。
- 回归：143 测试 OK；界面截图验证修复生效。

## 逻辑复审 + 真实证据直通（2026-10-11，应用户"审查逻辑/配置按真实使用/结果直接列证据"）

1. **逻辑复审**：前端修复后数据链逐接口验证（system/runs/configs/suites/agents 全 200 + JSON 有效）；平均分只计有效批次、口径明示；新增评测默认 reference vs flawed。
2. **配置按真实使用补正**：openclaw 命令模板说明更正——VM 真实批次经智能体发现驱动（非包装器），占位骨架如实标注"待 export 脚本"；清理后的 11 个配置即真实使用集合。
3. **结果中心直通真实证据（核心改进）**：`list_runs` 为嵌套官方批次生成可读标题（`验收目录 · 批次 · 智能体`），前端所有视图（总览/趋势/最近评测/历史表）优先显示 `run.title`——**100/100 条运行全部带标题**（实测 API），如 "official-installed-20261004 · repeat-01 · kylinbot + openclaw"。评委/用户在工作台里可直接搜到并打开真实批次的证据与雷达图，不再被 120 条历史里 89 个"quick-compare/repeat-01"目录名淹没。TDD：`test_nested_official_repeat_runs_get_friendly_titles`（144 测试全绿）。

- **重要更正**：先前两次"页面空白"截图是**截图时机抓在淡入动画透明帧**上的假象——DOM 检查证实主区内容完整（4 个子节点、computed opacity=1）；工作台从未被补丁破坏。真实存在的问题只有 8080 端口双实例（已修）。自审发现的其他问题（平均分污染/命名/默认值/横幅）均为真实缺陷且已修复生效——本次截图可见：**KylinBot 52.78（45 次·24 有效）**、可读标题已上线（评测趋势/最近运行显示 "official-final-20261004 · re…"、"deb-lifecycle-3.0vm-20261…" 等真实批次标题）。
- **结论**：工作台可直接用于录屏与评委演示；无需再改。
