# Zcode-agent对比方案

> 生成：2026-09-20（ZCode 协助全过程） · 环境：openKylin 3.0 Desktop（VMware 虚拟机）
> 内容：openKylin 生态 Agent 调研 → 实机安装配置 → 记忆行为实测 → 证据地图 → 坑与解法
> 口径：安装、文件盘点和烟测来自 2026-09-20 实机；服务状态复核于 2026-09-21。2026-09-22 已在同一 openKylin 3.0 VM 完成 KylinBot 真实 CLI 门禁；历史“待确认/未完成”表述仅适用于门禁前快照。

---

## 0. 摘要（今天下午完成了什么）

1. **生态调研**：盘点 openKylin 生态支持的智能体及获取方式（官方原生 / 商店 GUI / 独立开源 / 框架四类）；
2. **环境确认**：核实实机为 openKylin 3.0 Desktop（`E:\openkylin\Ubuntu 64-bit.vmx`）；
3. **模型后端打通**：Token 中心网关实测可用（OpenAI 兼容），确认 8 个可用模型；
4. **四只 Agent 安装配置完成**：KylinBot（预装）、kylin-agent 0.9.5（apt）、OpenClaw 2026.9.5（npm）、Hermes（install.sh）；
5. **公共配置复核**：四只均配置过 Token 网关和 `deepseek-v4-flash`；Hermes 的无效 `reasoning_effort: none` 已于 2026-09-21 修正为 `low`，其余专有参数仍需按各 Agent 能力解释；
6. **记忆行为实测**：同一句「记住我的项目代号是 Atalas」对比四只的记忆机制（三种主动写入 + 一种只查不写）；
7. **证据地图**：通过 SSH 实机盘点四只 Agent 的会话/记忆存储位置与可脚本化驱动接口；
8. **修复与加固**：OpenClaw 网关装成 systemd 服务（自启）、上下文修正、权限收紧；Hermes 当前实际运行在 Kylin-Agent runtime 内，不存在独立 `hermes-gateway.service`。

**当前状态**：OpenClaw 与 Kylin-Agent runtime 已复核为 `enabled + active`；Hermes 进程由后者托管；Hermes reasoning 已修正为 `low`；KylinBot/OpenClaw/KylinAgent 的用户记忆或状态文件权限已收紧为 `600`。KylinBot 当前仓库适配器已切换为真实 `kylin-bot agent` CLI 驱动；2026-09-24 在独立 HOME/空白记忆库中完成 KylinBot 与 OpenClaw 六案例快速对比，得分 `63.89` 与 `13.89`。结果属于 Agent 自有存储可观测的系统级证据，不是模型原生记忆证明。

### 2026-09-22 当前复核（替代门禁前快照口径）

- VM：openKylin 3.0 (huanghe)，`<vm-user>@<vm-address>:22`；`kylin-bot` 可执行，用户级 `openclaw-gateway.service` 与 `kylin-agent-runtime-gateway.service` 均为 `active`。
- 配置：`configs/agent-kylinbot-command.yaml` + `suites/native/kylinbot-gate.yaml`；驱动器逐轮调用 `kylin-bot agent --message`，复用临时 session state，并以前后 `brain.db` 差异生成事件。
- 结果：`runs/kylinbot-gate-20260922/result.json`，`overall=100.0`；证据含 `source=process` 的 `memory_write`（`benchmark_alias`）、精确 `memory_recall`（命中 Atlas）和两轮 assistant 输出。
- 口径：`observability.mode=system_level_wrapper_assisted`，`wrapper_memory_events=4`，`native_memory_events=0`；可宣称 KylinBot Agent 记忆行为门禁通过，不可宣称模型原生长期记忆。
- 清理：门禁后仅删除本轮新增的 `benchmark_alias` 与两条关联 `user_msg_*`，既有烟测数据未触碰。

---

## 1. 背景与目标

- 赛题要求（长期记忆 Benchmark 设计）：评测 **至少两款不同智能体** 在 openKylin 操作系统上的记忆能力，需在 openKylin 环境内完成运行与演示；
- 本次任务链：**盘点生态有哪些 Agent → 确认获取渠道 → 实机安装 → 统一配置 → 验证记忆行为 → 找到证据导出位置**；
- 被测对象选择原则：① 官方点名/生态真实存在；② 能在 openKylin 上实际运行；③ 记忆行为可观测（有可导出的证据）；④ 可对比（共用同一模型后端）。

---

## 2. 生态盘点（调研结论）

### 2.1 获取渠道分类

> 核心结论：**所有 Agent 的获取与运行都在 openKylin 虚拟机内完成**；Windows 宿主机只用于下载 ISO、抓取资料、调用网关 API 做连通性测试（不算评测）。

| 类别 | 对象 | 获取方式 | 备注 |
|---|---|---|---|
| **系统级原生** | KylinBot | openKylin 3.0 **系统预装**（桌面「小K」入口） | 赛题点名 |
| | kylin-agent | 软件商店搜"系统智能体" 或 `sudo apt install kylin-agent` | AgentOS SIG 维护 |
| | Token 中心 | 3.0 预装客户端 →「Token申请和管理」领 Key | 全局模型后端 |
| | AgentOS | 官网「下载 → 生态版本 → AgentOS」镜像 | 智能体向生态镜像 |
| **商店 GUI** | WorkBuddy（腾讯） | 软件商店（2.0+ 一键安装） | 闭源，证据链弱 |
| | 商汤小浣熊 Raccoon Work | 软件商店搜"商汤小浣熊" | 闭源 |
| | AutoClaw（智谱） | 软件商店（2026-09-14 上架，50+ Skills） | 闭源；apt 源里也有 `autoclaw` 包 |
| | Goose（Block） | 软件商店 / `curl … block/goose … download_cli.sh` | CLI 开源 |
| **独立开源** | OpenClaw | `curl -fsSL https://openclaw.ai/install.sh \| bash` 或 npm | MIT，官方声明 3.0 可运行 |
| | Hermes Agent（Nous Research） | `curl -fsSL https://hermes-agent.nousresearch.com/install.sh \| bash` | 主打持久记忆，与赛题最贴 |
| | Astron Agent（讯飞） | Docker Compose 本地部署 | Hack-Astron 赛题要求 2.0+ 本机部署 |
| **框架级** | LangChain / LangGraph / AgentScope / Qwen-Agent / CrewAI / AutoGen | pip / uv 安装 | 仅 Linux 可运行，**无 openKylin 官方适配声明**，不能写成官方支持 |
| **技能生态** | openkylin-skills | `git clone https://gitee.com/openkylin/openkylin-skills.git` | 官方 org + 社区维护；6 分类 40 技能 |

### 2.2 被测对象选定（本次）

**KylinBot（小K）+ kylin-agent + OpenClaw + Hermes** 四只 —— 覆盖"官方原生 / 系统智能体 / 独立开源 / 记忆专长"四种形态，全部满足可在 openKylin 运行且记忆行为可观测（KylinAgent 除外，见第 6 节）。

---

## 3. 实机环境

### 3.1 虚拟机

| 项 | 值 |
|---|---|
| 虚拟机 | `E:\openkylin\Ubuntu 64-bit.vmx`（VMware；displayName 仅兼容标签） |
| 系统 | **openKylin 3.0** Desktop（ISO `openKylin-Desktop-V3.0-20260905-x86_64.iso`） |
| IP / SSH | `<vm-address>:22`，用户 `<vm-user>`（SSH 密钥登录已配置，可远程运维） |
| 内存 | 6GB |

> 历史环境说明：旧 2.0 SP2 虚拟机（`D:\openKylin-VM`）已删除；D 盘 3.0 AgentOS 安装尝试（2026-09-18）已废弃；当前实机为 E 盘 3.0 Desktop。

### 3.2 Token 中心网关

| 项 | 值 |
|---|---|
| Base URL | `https://llm-gateway.openkylin.top/v1`（**完全兼容 OpenAI 协议**，`/v1/models` 可用） |
| 可用模型（8 个） | `deepseek-v4-flash`、`deepseek-v4-pro`、`deepseek-chat`、`deepseek`、`qwen3.8-max`、`qwen3.7-max`、`qwen3.7-plus`、`qwen-plus` |
| API Key | Token 中心客户端领取（**完整 Key 仅显示一次**）；VM 内存 `~/.openkylin-token`（权限 600），环境变量 `OPENKYLIN_TOKEN_API_KEY` |
| 额度 | 基础 **100 万 token/天/装机用户**；连续签到倍数：第 2 天 ×1.5、第 7 天封顶 **×4.0** |
| `reasoning_effort` 白名单 | **仅 `low` / `medium` / `high` / `xhigh` / `max`**；`minimal` 与"关闭推理"→ HTTP 400 |
| 上下文 | 官方文档推荐 32768（**非硬上限**，见 5.1 实测）；四 Agent 统一声明 **64000** |

**官方接入文档**：《openKylin免费Token接入指南》—— `docs.openkylin.top` → 1入门与参与 / 1_5基础设施平台指南 / AI模型配置指南 / 子文档 / 06（含 openKylin AI 助手、OpenClaw、DeepSeek Harness、Codex、Claude Code 五种接法）。

---

## 4. 安装与配置实录

### 4.1 KylinBot / 小K（官方预装）

- **获取**：无需安装，系统预装；桌面「小K」图标即入口，另有「对话 / 通道 / 技能 / 任务 / 模型」五个 tab；
- **模型配置**（文件级确认）`~/.kylinbot/config.toml`：
  ```toml
  [providers.models."custom:https://llm-gateway.openkylin.top/v1/chat/completions"]
  model = "deepseek-v4-flash"
  ```
  ✅ 已验证走 Token 网关；
- **技能**：`~/.kylinbot/workspace/skills/`（openkylin-skills 全套 40 个 UKUI 桌面技能）；
- **数据目录**：`~/.kylinbot/workspace/`（`sessions/`、`memory/`、`devices.db`、`cron/`、`state/`、`skills/`）。

### 4.2 kylin-agent / KylinAgent（apt 包）

- **安装**：`sudo apt update && sudo apt install -y kylin-agent`（0.9.5；会拉 llvm/clang 工具链，包偏重）；
- **驱动限制**：**纯 GUI 单实例 Qt 应用，无 CLI**（`--help` / `--version` 会拉起 GUI 而非输出帮助）；
- **架构**：GUI 前端 + **Kylin-Agent-Runtime 本地服务**（systemd 用户服务 `kylin-agent-runtime-gateway.service`，socket `~/.cache/kylin-agent.socket`）；
- **设置页**：通用 / CUA 智能体 / 模型 / 技能 / 个性 / **记忆 / 日志** / 用量；
- **模型配置**：GUI「设置 → 模型 → 添加模型」（提供商选自定义，Base URL 填完整网关地址，模型 `deepseek-v4-flash`，上下文长度手动填 64000）；
- **上下文压缩**（runtime `config.yaml` 内置）：达模型上下文 **50%** 触发，保留最近 N 轮（默认 20 条消息），中间轮次由廉价模型摘要；
- **同源疑点**：runtime `config.yaml` 头部自述 *"Hermes Agent CLI Configuration"*，目录结构（`auth.json` / `channel_directory.json` / `cron/` / `bin/` / `audio_cache/` / `cache/` / `config.yaml.bak-last-good`）与 `~/.hermes` 高度相似 → **疑似同源或衍生（待进一步验证，报告表述需谨慎）**。

### 4.3 OpenClaw（npm 安装）

**安装（踩坑后走通的完整路径）**：

```bash
# ① NodeSource 检测不认 openKylin（ID=openkylin）→ 手动加源
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
sudo apt update && sudo apt install -y nodejs        # → v24.21.0

# ② npm 11+ 默认拦截 install scripts → 显式放行
sudo npm install -g openclaw@latest \
  --allow-scripts=openclaw,@google/genai,koffi,tree-sitter-bash,protobufjs \
  --registry=https://registry.npmmirror.com          # → 2026.9.5
```

**模型配置** `~/.openclaw/openclaw.json`：

```json
"models": { "providers": { "custom-llm-gateway-openkylin-top": {
  "baseUrl": "https://llm-gateway.openkylin.top/v1",
  "api": "openai-completions",
  "models": [{ "id": "deepseek-v4-flash", "contextWindow": 64000,
               "maxTokens": 4096, "reasoning": false, "input": ["text"] }]
}}}
```
密钥在 `~/.openclaw/.env`；**注意**：向导初始写入的 `contextWindow` 是 **128000**，需手动改为 64000（见坑 #8）。

**网关服务**：systemd 用户服务 `openclaw-gateway.service`（127.0.0.1:18789，已 enable 开机自启）；
**驱动接口**：`openclaw agent -m "消息" --json`（可脚本化）、`openclaw audit`（审计轨迹）；
**技能**：`~/.openclaw/skills/`（与 KylinBot 同一套 openkylin-skills，便于同任务对比）。

### 4.4 Hermes Agent（Nous Research）

**安装**：

```bash
# GitHub 直连仅 57 KiB/s（282MB 仓库要 30+ 分钟）→ 用镜像预先克隆
git clone --depth 1 --branch main \
  https://gh-proxy.com/https://github.com/NousResearch/hermes-agent.git ~/.hermes/hermes-agent
# 重跑官方安装脚本：检测到已有仓库 → 跳过克隆，只做 fetch + 构建
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

**配置**（`~/.hermes/config.yaml`，setup 向导逐项选择）：

| 向导项 | 选择 |
|---|---|
| 数据迁移（检测到 ~/.openclaw） | **Skipping migration**（保持干净基线） |
| 安装模式 | Full setup |
| Provider | Custom OpenAI-compatible（display name：`openkylin-token`） |
| Base URL / 模型 | `https://llm-gateway.openkylin.top/v1` / `deepseek-v4-flash` |
| API mode | `chat_completions` |
| 上下文 | 64000（向导里先填 32768 会被拒，见坑 #7） |
| Reasoning effort | **`low`**（Disable 会 400，见坑 #6） |
| 终端后端 | Local |
| 消息平台 | 全不选 |
| 工具（浏览器/CUA/图像生成/TTS/视觉/搜索） | 全 Skip |

**实机复核**：`~/.hermes/config.yaml` 曾为 `reasoning_effort: none`，相关日志记录过 400；已于 2026-09-21 改为白名单值 `low`（保留权限 600 的本地备份）。声明上下文必须 **≥64000**，否则拒绝启动模型连接；
**命令**：`hermes`（对话）、`hermes config edit`、`hermes doctor`、`hermes gateway install`（消息+cron 网关，暂未装）、`hermes update`。

### 4.5 统一配置决定（四只对齐）

| 配置项 | 统一值 | 依据 |
|---|---|---|
| 模型后端 | Token 网关 `https://llm-gateway.openkylin.top/v1` | 赛题要求 openKylin 生态内统一模型 |
| 模型 | `deepseek-v4-flash` | 8 个可用中成本/速度最优；推理默认开启 |
| 声明上下文 | **64000** | Hermes 硬性下限；距实测通过点（67,990）留约 4K 余量；案例级上下文（~10K）不触发压缩 |
| reasoning | Hermes=`low`；其余不发参数或使用各自默认 | 白名单校验；成本可控 |
| 专有设置 | 全部保持默认（如 KylinAgent「优先级：中」「位置：上海」） | 公平性：只统一公共配置，不动各 Agent 私有旋钮 |

---

## 5. 关键实测与数据

### 5.1 网关上下文上限实测（2026-09-20）

| 探针 | 输入规模 | 结果 | 计费 token |
|---|---|---|---|
| 第一次 | 72,000 汉字 | **HTTP 200 接受** | 36,004 |
| 第二次 | 135,972 汉字 | **HTTP 200 接受** | 67,990 |

**结论**：官方文档的 32768 是**推荐配置值、非硬性上限**；网关实际接受远超它的输入。探针共消耗约 10.4 万 token 签到额度。

### 5.2 reasoning_effort 三档对比（同一简单题，temperature=0）

| 档位 | reasoning_tokens | completion_tokens |
|---|---|---|
| 不发参数（其余三只的实际行为） | 98 | 100 |
| `low`（Hermes 设置） | 104 | 106 |
| `medium` | 105 | 107 |

**结论**：三档差异 <10%（噪声级），参数影响弱；Hermes 的 `low` 与其余三只的默认行为**等效，无不对称**。成本事实：推理默认开启，简单问题也烧 ~100 推理 token。

### 5.3 额度与成本

| 项 | 数值 |
|---|---|
| 基础额度 | 100 万 token/天；签到倍数最高 ×4.0（第 7 天） |
| 2026-09-20 余额 | 1,304,181（含探针消耗） |
| 实测单会话 | KylinAgent 6 条消息 = 上下文 13.6K / **总消耗 40.5K token**（每轮全量重发系统提示+工具+历史） |
| 推算 | 单案例（~12 轮）约 5-12 万；6 案例套件/Agent 约 30-90 万 → 1× 倍数下每天约 1.5-2 个 Agent 套件 |
| 优化杠杆 | ① 每日签到（倍数最大）；② `reasoning_effort=low`；③ 分天运行 / 高倍数日跑全套件 |
| 单轮耗时 | OpenClaw 实测约 41 秒/轮（时间预算需计入） |

---

## 6. 记忆行为实测对比（2026-09-20）

**方法**：向四只 Agent 发送同一句「记住我的项目代号是 Atalas」。

| Agent | 反应 | 是否落盘 | 证据位置 |
|---|---|---|---|
| **KylinBot / 小K** | 工具调用「已记录 ✓ …已存入我的长期记忆」 | ✅ | `brain.db.memories`：`(key='project_codename', content='用户的系统项目代号是 Atals', category='core')` |
| **Hermes** | `preparing memory... / memory +user: "User's project codename: Atalas"`，回复"记下了" | ✅ | `state.db.messages`（grep 命中 3 处） |
| **OpenClaw** | 回复"已记录：**项目代号 Atlas** ✓" | ✅ | `workspace/USER.md`：`<!-- observed: 2026-09-20 \| status: active -->` + `- 项目代号：Atlas，…` |
| **KylinAgent** | "没有找到关于…的过往对话记录"（**只查不写**） | ❌ | 画像 0 字段；全部 `.db` 无该字符串 |

**结论**：三只为**主动抽取型**（识别持久事实即写入并确认）；KylinAgent 为**检索型**（查历史但不主动沉淀画像）。该行为差异本身即 benchmark 的有效区分维度。

> 注：烟测写入的记忆（Atalas / Atlas）在正式跑套件前需决定处理策略：清空（干净基线）或标记为预热数据。

---

## 7. 证据地图（完整）

### 7.1 汇总

| Agent | 会话/对话存储 | 记忆存储 | 驱动接口 | 可读性 |
|---|---|---|---|---|
| KylinBot | `~/.kylinbot/workspace/sessions/sessions.db` | `~/.kylinbot/workspace/memory/brain.db` | GUI（`gateway.sock` 待探） | ⭐⭐⭐ |
| Hermes | `~/.hermes/state.db` → `sessions`/`messages` | 同库 `messages`（memory 工具事件） | TUI + 网关 :8642 | ⭐⭐⭐ |
| OpenClaw | `openclaw-agent.sqlite` → `transcript_events` 等 | **`workspace/USER.md` / `MEMORY.md`** + SQLite 索引 | **`openclaw agent --json`** + `audit` | ⭐⭐⭐ |
| KylinAgent | `~/.kylin-agent-runtime/state.db`、`response_store.db` | `memory.db` + GUI 画像（加密） | **仅 GUI** | ⭐ |

### 7.2 存储结构明细

**KylinBot**：`brain.db` 表 = `memories` + `memories_fts`（全文索引）+ `embedding_cache`；`memories` 的 DDL：
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY, key TEXT NOT NULL UNIQUE, content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'core',   -- core | conversation
    embedding BLOB, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    session_id TEXT, namespace TEXT DEFAULT 'default', ...
)
```

**Hermes**：`state.db` 表 = `sessions`、`messages`（+`messages_fts` 及 trigram 变体）、`system_prompts`、`session_model_usage`、`conversation_generations`、`compression_locks`、`session_turn_leases`、`async_delegations`、`delivery_obligations`、`gateway_routing` 等；`shared-state.db` 为协作房间（非记忆）；数据目录含 `logs/`（agent.log、errors.log、curator/）、`cron/`、`skills/`。

**OpenClaw**：每 Agent 库 `~/.openclaw/agents/main/agent/openclaw-agent.sqlite` 相关表——
- 会话/对话：`session_nodes`、`session_windows`、`conversations`、`conversation_deliveries`、`transcript_events`、`session_transcript_archives`、`trajectory_runtime_events`
- 记忆/索引：`memory_index_meta`、`memory_index_sources`、`memory_index_chunks`、`memory_index_chunk_recall_metadata`、`memory_index_chunk_provenance`、`memory_entry_origins`、`memory_embedding_cache`、`standing_intents`（+FTS）
- 审计/运行：`audit_events`、`diagnostic_events`、`task_runs`、`subagent_runs`、`cron_jobs`
- 用户：`user_preferences`、`user_profiles`、`user_profile_identities`

工作区记忆文件（实际落点）：`~/.openclaw/workspace/USER.md`（用户画像，4000 字符预算/每会话加载）+ `MEMORY.md`（持久非画像事实）；条目格式 `<!-- observed: YYYY-MM-DD | status: active/superseded -->`，变更时旧条目标 superseded 原地重写（天然对应 write/update 事件）。

**KylinAgent**：`state.db` / `memory.db` 表 = `sessions`、`messages`、`task_runs`、`task_subruns`、`task_checkpoints`；`response_store.db` = `responses`、`conversations`；`kanban.db` = `tasks`、`task_links`、`task_comments`、`task_events` 等；GUI 画像加密。

### 7.3 事件映射（KMB 协议）

| Agent | → `memory_write` | → `memory_update` | → `memory_recall` |
|---|---|---|---|
| KylinBot | `brain.db.memories` 新增行 | 同 key 行 `updated_at` 变化 | `memories_fts` 命中 |
| Hermes | `messages` 中 memory 工具事件 | 工具事件序列 | memory 工具查询事件 |
| OpenClaw | `USER.md`/`MEMORY.md` 新条目 | 旧条目 `superseded` + 新 active | `memory_index_chunk_recall_metadata` |
| KylinAgent | （当前无自动写入） | — | 对话记录中的检索行为 |

### 7.4 可脚本化驱动命令

```bash
# OpenClaw（当前最完整）：带 JSON 结果与 runId
openclaw agent -m "<消息>" --json          # 中文建议用 --message-file <path>
openclaw audit --after "<ISO时间>" --agent main
# KylinBot / Hermes / KylinAgent 的驱动接口见第 4 节对应档案
```

---

## 8. 已知坑与解法清单（实战记录）

| # | 现象 | 根因 | 解法 |
|---|---|---|---|
| 1 | OpenClaw install.sh 报 "only supported on Debian-based systems" | NodeSource 检测不认 openKylin（`ID=openkylin` 且无 `ID_LIKE=debian`） | 手动添加 NodeSource `node_24.x` 源 |
| 2 | npm 装完 openclaw 缺功能 | npm 11+ 默认拦截 install scripts | `--allow-scripts=openclaw,@google/genai,koffi,tree-sitter-bash,protobufjs` |
| 3 | openkylin-skills 只装 10 个且大量报错 | Gitee API 匿名配额耗尽（HTTP 000）；脚本分类失败静默跳过、失败仍计成功 | **弃用 install.sh**：`git clone --depth 1` 后 `cp -r skills/. <目标>/` |
| 4 | Hermes 克隆 GitHub 仅 57 KiB/s | 大仓库单包被节流 | 镜像 `https://gh-proxy.com/https://github.com/...`（实测 87 秒/282MB） |
| 5 | `openclaw gateway install` 被拒（unsafe-permissions） | `~/.config/systemd/user` 上级目录组/其他可写（openKylin 家目录默认 775） | `chmod go-w ~ ~/.config`；`chmod 700 ~/.config/systemd/user` |
| 6 | Hermes 报 `reasoning_effort must be one of…` | Hermes 的 "Disable reasoning" 发送的取值不在网关白名单 | 改 `low`；白名单为 `low/medium/high/xhigh/max` |
| 7 | Hermes 拒绝启动模型连接（32,768 < 64,000） | Hermes 硬性要求声明上下文 ≥64000 | 声明值改 **64000**（0.5 压缩阈值在 32K 触发，恰低于网关实测上限） |
| 8 | OpenClaw `contextTokens: 128000`（改了没生效） | 向导初始写入 128000，`sed 32768→64000` 无匹配 | Python 精确改 `models[].contextWindow`，重启网关后用 `openclaw agent --json` 验证 |
| 9 | 宿主机 curl 发中文 JSON 报 400 | Windows Git Bash 对 `-d` 内联中文的编码破坏 | 用 `--data-binary @文件` |
| 10 | curl 报 `CRYPT_E_REVOCATION_OFFLINE` | Windows schannel 吊销检查离线 | `curl --ssl-no-revoke` |
| 11 | autoclaw 与 OpenClaw 混淆 | apt 源的 `autoclaw`（智谱，描述含 "powered by OpenClaw Gateway"）不是 OpenClaw 本体 | OpenClaw 本体走 npm；autoclaw 是另一产品 |
| 12 | OpenClaw 网关重启后掉线、消息丢失 | 网关未装成常驻服务（onboarding 提示 Gateway service disabled） | `openclaw gateway install` + `start`（systemd 用户服务，已自启） |
| 13 | 密钥多次暴露于聊天/截图/桌面文件 | 明文 Key 放在桌面 `key.txt`、聊天记录 | 移入 `~/.openkylin-token`（600）；**评测后应立即在 Token 中心轮换 Key** |

---

## 9. 未决事项与下一步

### 未决事项

1. **KylinBot 扩展门禁**：最小 CLI 门禁已通过；若进入正式多维套件，仍需按同一驱动器补充更多能力案例并保留逐轮证据；
2. **KylinAgent 证据方案**：不自动写画像 → 是否走 Runtime 服务 API，或仅以"对话记录"作其证据等级；
3. **记忆清理策略**：Atalas/Atlas 已写入三只 Agent，正式运行前需明确清空/预热规则；
4. **KylinAgent 同源疑点**：与 Hermes 的相似性需进一步验证（影响报告表述）；
5. **Key 轮换**：Token Key 已在聊天/截图多处暴露，评测完成后应重新申领并作废；
6. **运行排期**：按额度与签到倍数安排正式套件运行（建议高倍数日跑全套件）。

### 下一步（工程清单）

1. **扩展真实会话证据**（KylinBot/OpenClaw 六案例快速对比已完成，配置为 `configs/agent-kylinbot-command.yaml`）：
   - 当前驱动器已在 guest 内记录“发送 → 写入 → 回忆”的时序；正式多维套件仍需按同一口径扩展案例；
   - OpenClaw：`openclaw agent --json` 驱动 + 解析 `USER.md` / `MEMORY.md`；适配器按案例使用独立 `--session-key`，隔离验收可显式使用临时 HOME；
   - Hermes：读 `state.db.messages`；
   - KylinAgent：走 GUI/服务 API（最后处理）。
2. **入口门禁**：跑最小案例验证"被测量方自有记忆事件 > 0"（KMB 协议门禁）；
3. **正式套件**：如需完整四只 Agent × 核心/对抗矩阵，补跑 Hermes；KylinAgent 需先完成结构化 GUI/服务证据方案。桌面录屏仍是赛题交付要求 e，按项目安排最后录制。

---

## 附录 A：本次涉及的关键路径速查

```
# 模型与网关
https://llm-gateway.openkylin.top/v1          # Gateway Base URL
~/.openkylin-token                            # Key 存放（600）

# KylinBot
~/.kylinbot/config.toml                       # 模型配置
~/.kylinbot/workspace/memory/brain.db         # 记忆库（memories 表）
~/.kylinbot/workspace/sessions/sessions.db    # 会话
~/.kylinbot/workspace/skills/                 # 40 个技能

# KylinAgent
~/.kylin-agent-runtime/state.db / memory.db / response_store.db / kanban.db
~/.kylin-agent-runtime/config.yaml            # runtime 配置（含压缩阈值）
~/.cache/kylin-agent.socket                   # 服务 socket

# OpenClaw
~/.openclaw/openclaw.json                     # 模型/网关配置
~/.openclaw/.env                              # 密钥
~/.openclaw/workspace/USER.md / MEMORY.md     # 记忆文件
~/.openclaw/agents/main/agent/openclaw-agent.sqlite   # 会话/索引库
~/.openclaw/skills/                           # 技能

# Hermes
~/.hermes/config.yaml                         # 模型/上下文/reasoning 配置
~/.hermes/.env                                # 密钥
~/.hermes/state.db                            # 会话/记忆（messages）
~/.hermes/logs/                               # agent.log 等
~/.hermes/hermes-agent/                       # 代码（镜像克隆）

# 技能仓库
https://gitee.com/openkylin/openkylin-skills  # git clone 获取（勿用 install.sh）
```
