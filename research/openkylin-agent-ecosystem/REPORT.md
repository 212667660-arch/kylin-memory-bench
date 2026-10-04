# openKylin 智能体生态核实（截至 2026-09）与 KylinMemoryBench 可测性

> Generated 2026-09-18 · depth: standard · findings: F1–F4 · workspace: research/openkylin-agent-ecosystem/
> 证据规则：优先 openkylin.top / openkylin Gitee / 各项目官方 GitHub/文档；「pip 能装 ≠ openKylin 官方支持」。

## Executive summary

- openKylin **3.0**（2026-09-07 官方发布）定位「智能体开放底座」，**官方明确** KylinBot 为原生智能体，并称 KylinBot、WorkBuddy、OpenClaw、Raccoon Work 等可在 3.0 上完整运行，智能体经 **MCP** 直调桌面能力 [1][2]。
- **Token 中心**预装于 3.0：官方声明 **完全兼容 OpenAI 协议**，Base URL 为 `https://llm-gateway.openkylin.top/v1/chat/completions`；Key 在客户端「Token申请和管理」审批后领取（完整 Key 仅显示一次）；免费额度靠**每日签到**入账并调用扣减、可累积；2026-09-09 上新 qwen3.8-max / qwen3.7-max / qwen3.7-plus / deepseek-v4-pro / deepseek-v4-flash [3][4][5]。
- 软件商店侧官方新闻确认：WorkBuddy（腾讯，**2.0+ 商店一键装**）[6]；商汤小浣熊 Raccoon Work **0day 适配**（商店搜「商汤小浣熊」）[7]；智谱 **AutoClaw** 2026-09-14 上架（50+ Skills）[8]。
- **AgentOS** 为官方生态镜像通道（官网下载-生态版本-AgentOS），2026-09-07 推送 3.0 更新，覆盖系统智能体、CUA、统一模型推理、Agent Runtime 等 [9]；**AgentOS SIG** 维护 kylin-agent / agent-runtime / **agent-memory** / **agent-benchmark** / **agent-evaluation** 等包 [10]。
- **openkylin-skills** 在官方 Gitee org：`https://gitee.com/openkylin/openkylin-skills`，`install.sh --agent openclaw|kylin-bot|claw`，KylinBot 路径 `~/.kylinbot/workspace/skills/`，OpenClaw 为 `~/.openclaw/skills/`；README 声称 MulanPSL-2.0，维护者个人、属**官方命名空间下的社区维护**；仓内**未写 MCP 协议文档** [11][12]。
- **OpenClaw** 本体是独立开源项目（GitHub `openclaw/openclaw`，MIT，Foundation 501(c)(3)，无付费层），Linux 安装 `curl -fsSL https://openclaw.ai/install.sh | bash`；Skills 是 SKILL.md，MCP 是独立 `mcp.servers` 配置层 [13][14][15]——openKylin 3.0 官方新闻将其列为可运行智能体，属**官方声明生态可运行**，不是「OpenClaw 由 openKylin 官方开发」。
- **Astron Agent**（科大讯飞，Apache-2.0）有 Memory/MCP/RPA 模块与 Docker Compose 本地安装；openKylin **Hack-Astron 赛题要求在 2.0+ 本地部署** Astron + Skillhub，技能提交至 openkylin-skills——属**官方赛事级生态适配要求**，不是系统预装 [16][17][18]。
- 六大框架（LangChain/LangGraph/AgentScope/Qwen-Agent/AutoGen/CrewAI）均为纯 Python，**Linux 可 pip/uv 安装**；在已检索官方源中**未发现 openKylin 对其「官方适配」声明** → 标注 **仅 Linux 可运行**，License 与 Memory 能力见总表 [19][20][21][22][23][24]。
- **KylinMemoryBench 当前可测**：离线 reference/flawed、`kylinbot-process` stand-in、OpenAI-compatible `type:http`（含 Token Center 有 Key 后）、`memory_controller`/`memory_disabled` 包装轨、`command`/`replay`。**不可在无导出证据时测「原生记忆」**；GUI 商店应用若无 API/日志导出，只能作生态叙述，不能直接进评分主结论。
- **Benchmark 优先部署（客观维度见正文）**：① openKylin 上可脚本化的 **kylin-agent / KylinBot（command 导出）** ② **OpenClaw（CLI + 可选 memory/MCP）** ③ **Token Center 作统一模型后端**（http）④ **LangGraph / AgentScope 2.0 / CrewAI 之一做双记忆机制对照**。WorkBuddy/Raccoon 等 GUI 产品证据链最弱，不宜作记忆主被测对象。

---

## 支持级别定义（强制）

| 级别 | 含义 |
|------|------|
| **官方明确支持/适配** | openkylin.top 官方新闻、openkylin 官方 Gitee org/SIG、官方商店公告明确写出版本/安装/能力 |
| **社区生态支持** | 官方 org 下社区维护，或独立开源项目被官方点名「可运行」，但非系统产品组件 |
| **仅 Linux/Python 可运行** | 任何现代 Linux 装得上；**没有** openKylin 官方适配声明 |

---

## 一、openKylin 官方/生态 Agent

### 1. KylinBot — 官方明确支持（3.0 原生智能体）

| 项 | 核实结果 |
|----|----------|
| 官方定位 | openKylin 3.0「KylinBot 原生智能体」，公测重点验证对象 [1][25] |
| 是否预装 | 官方新闻将其列为 3.0 原生/系统智能体；**未在检索中抓到包名级「deb 预装清单」**[single source 级：发布文案] [1][25] |
| 支持版本 | 官方叙事绑定 **openKylin 3.0**（2026-09）[1]；2.0 上独立安装方式未在本轮官方源核实 |
| 启动/调用 | 公测新闻：任务结果可推送企业微信/飞书/钉钉 [25]；技能默认路径 `~/.kylinbot/workspace/skills/`（openkylin-skills 文档）[11] |
| MCP / Skill | 3.0 官方称智能体经 MCP 调桌面能力 [2]；Skill 接 openkylin-skills（`--agent kylin-bot`）[11] |
| API / 模型 | Token 中心新闻点名 KylinBot 可接入 OpenAI 兼容网关 [4] |
| 免费 | 系统/Agent 安装细节定价页未找到；模型侧走 Token 签到额度 [3] |
| 地址 | 官网新闻 [1][25]；独立 Gitee 仓 `gitee.com/openkylin/kylinbot` 本轮 **403**，未能读 README |

### 2. OpenClaw — 官方新闻「3.0 可完整运行」+ 社区开源本体

| 项 | 核实结果 |
|----|----------|
| openKylin 官方 | 3.0 新闻列名可运行 + Token 可用 [2][4]；**本体非 openKylin 官方项目** |
| 安装（官方 OpenClaw） | Linux: `curl -fsSL https://openclaw.ai/install.sh \| bash`；npm 需 Node 24.16+ 或 26.1+ [14] |
| 启动/调用 | CLI + 对话；Skills：`openclaw skills install` / `$skill` / `openclaw skills load` [14][12] |
| MCP | 独立配置 `mcp.servers`（stdio/SSE/Streamable HTTP）[15] |
| openkylin-skills | `--agent openclaw` → `~/.openclaw/skills/` [11] |
| Token Center | 官方点名 OpenClaw 可用 Token 中心 [3][4] |
| 本地模型 | OpenClaw 文档层需单独核实（本轮 findings 未展开 Ollama 章节）[open question] |
| 费用 | 软件本身免费、无 paid tier；**模型 API 可能产生费用**（Token 签到或第三方 Key）[13][3] |
| 地址 | https://github.com/openclaw/openclaw [13] |

### 3. WorkBuddy — 官方商店适配

| 项 | 核实结果 |
|----|----------|
| 类型 | 腾讯「全场景 AI 智能体工作台」[6] |
| 商店 | **已上架 openKylin 软件商店**（2026-09-07 新闻）[6] |
| 版本 | **openKylin 2.0 及以上**，商店搜索 WorkBuddy 一键安装 [6] |
| 模型 | 新闻称接入混元、DeepSeek、GLM、Kimi 等 [6] |
| API/MCP/Skill | 本轮**未**在官方新闻中找到 WorkBuddy 独立 API/MCP 开放文档 |
| 免费/限制 | 定价与免费额度页未在本轮官方源取得 [open question] |
| 地址 | https://www.openkylin.top/news/4115-cn.html [6] |

### 4. Raccoon Work / 商汤小浣熊 — 官方商店适配

| 项 | 核实结果 |
|----|----------|
| 适配 | 2026-08-26 Linux 桌面端 openKylin 适配，0day 首发 [7] |
| 安装 | 软件商店搜索「商汤小浣熊」[7] |
| 免费/会员 | 官方新闻未给会员/积分细则；商汤产品常见额度机制**本轮未证实** [open question] |
| API/MCP/Skill | 未在 openKylin 官方新闻找到开放 API/MCP 说明 |
| 地址 | https://www.openkylin.top/news/4096-cn.html [7] |

### 5. AutoClaw（补充，商店生态）

- 智谱 AI 工作助手，2026-09-14 上架商店；两步安装；50+ Skills、Goal 模式、集群多 Agent [8]。
- 地址：https://www.openkylin.top/news/4135-cn.html [8]

### 6. openKylin AgentOS — 官方生态发行/SIG

| 项 | 核实结果 |
|----|----------|
| 是什么 | 官网「下载 → 生态版本 → AgentOS」通道；非与 Desktop 二选一的营销口径下，定位为**智能体向生态镜像/运行时栈** [9] |
| 与 Desktop | 3.0 Desktop 强调 Agent 叙事；AgentOS 更新强调系统智能体、**CUA**、**统一模型推理**、**Agent Runtime**、语音与人机协同 [9] |
| 版本/日期 | 2026-09-07 推送 openKylin 3.0 AgentOS 新一轮更新 [9] |
| 安装 | 官网生态版本下载（ISO/镜像细节页本轮未逐项抓取）[9] |
| 组件 | AgentOS SIG：统一模型推理、Agent Runtime/Harness、**记忆、规划、技能、工具**；包含 kylin-agent、system-agent、computer-use-agent、agent-runtime、**agent-memory**、agent-skills、uni-model-infer、**agent-evaluation / agent-benchmark** [10] |
| 费用 | 开源生态镜像通道；模型 Token 另计 [3][9] |
| 地址 | 新闻 [9]；SIG https://gitee.com/openkylin/community/tree/master/sig/AgentOS [10] |

### 7. openkylin-skills — 官方 org + 社区维护

| 项 | 核实结果 |
|----|----------|
| 地址 | **Gitee**：https://gitee.com/openkylin/openkylin-skills（GitHub 搜索无同名官方仓）[12] |
| 支持 Agent | install.sh：OpenClaw / Kylin Bot / Claw [11] |
| 主要 Skill | UKUI 设备与桌面（亮度/音量/WiFi/蓝牙/电源、主题壁纸任务栏、会话、截图录屏、通知、应用等约 16 项）+ linux-generic/community/devops/ai/domain（如 `linux-blaze-fan`、`cangjie-skill`、`ai-memocap`）[12] |
| 安装 | `curl -fsSL https://gitee.com/openkylin/openkylin-skills/raw/master/install.sh \| bash -s -- --agent openclaw`（或 `kylin-bot` / `claw`）[11] |
| 调用 | 自然语言或 `openclaw skills load <skill>` [12] |
| 与 MCP | **仓内 README/install 未写 MCP**；与 3.0「智能体经 MCP 调桌面」是不同层：技能多为 SKILL.md/脚本，MCP 在 Agent/系统侧 [11][2] vs [15] |
| License | README 称 MulanPSL-2.0；Gitee 可能无独立 LICENSE 文件 [12] [single source] |
| 级别 | **官方命名空间 + 社区维护者**（kiber234324）[12] |

### 8. Astron Agent — 讯飞开源 + openKylin 官方赛事级适配要求

| 项 | 核实结果 |
|----|----------|
| 类型 | 企业级 Agentic Workflow：编排、模型管理、**MCP**、**RPA**、协作 [16] |
| openKylin | Hack-Astron 要求 **openKylin 2.0+ 本地部署** Astron Agent 开源版 + Skillhub，用原生 RPA；不接受仅 SaaS 云端作品 [17] |
| 安装 | `git clone https://github.com/iflytek/astron-agent.git` → `cd docker/astronAgent` → `cp .env.example .env` → `docker compose -f docker-compose-with-auth.yaml up -d`；前端 localhost，Casdoor 默认 admin/123（**上线须改密**）[18] |
| 硬件 | Agent：CPU≥2 / RAM≥4GiB / Disk≥50GB；RagFlow 可选更高 [18] |
| Memory | 文档：Memory DB Service（长期/短期记忆、会话持久化）[18] |
| Skillhub | https://github.com/iflytek/skillhub（Apache-2.0），技能可被 Astron 加载 [18] |
| 技能提交 | openkylin-skills（Hack-Astron）[17][12] |
| License | Apache-2.0 [16] |
| 地址 | https://github.com/iflytek/astron-agent [16] |

---

## 二、主流 Agent 开发框架（openKylin 未官方点名适配）

结论先说：下列框架 **均为「仅 Linux/Python 可运行」**；openkylin.top 与已读官方页**未**列其为 openKylin 官方适配框架 [24]。

| 框架 | GitHub | Docs | License | 安装（官方） | Py | OpenAI API | MCP | Memory/长期记忆 | 多 Agent | 本地模型 | 适合 KMB |
|------|--------|------|---------|--------------|----|------------|-----|-----------------|----------|----------|----------|
| LangChain | langchain-ai/langchain | docs.langchain.com | MIT | `uv add langchain` / `pip install langchain` | ≥3.10 | 是（extras） | extras `mcp` | 靠 LangGraph 生态 | 弱于 LangGraph | Ollama extras | 中（骨架） |
| LangGraph | langchain-ai/langgraph | docs.langchain.com/oss/…/langgraph/memory | MIT | `pip install -U langgraph` | ≥3.10 | 是 | 生态集成 | **短期+长期 store** [20][21] | 是 | Ollama 等 | **高** |
| AgentScope 2.0 | agentscope-ai/agentscope | docs.agentscope.io | Apache-2.0 | `uv pip install agentscope` | **≥3.11** | 是 | Toolkit + MCP Registry | Agentic / ReMe / Mem0 [22] | Agent Team | Ollama 等 | **高** |
| Qwen-Agent | QwenLM/Qwen-Agent | GitHub README | Apache-2.0 | `pip install -U "qwen-agent[gui,rag,code_interpreter,mcp]"` | GUI≥3.10 | OpenAI-compatible | **支持**（含 server-memory 示例） | RAG/记忆偏薄 | 有限 | vLLM/Ollama | 中（MCP+本地 Qwen） |
| AutoGen | microsoft/autogen | GitHub | MIT（代码） | `pip install -U "autogen-agentchat" "autogen-ext[openai]"` | ≥3.10 | 是 | McpWorkbench | 有会话记忆，**维护模式** | 是 | 可配 | 中低（继任 MS Agent Framework） |
| CrewAI | crewAIInc/crewAI | docs.crewai.com | MIT | Linux: `uv tool install crewai` | ≥3.10,<3.14 | 默认 OpenAI | MCP/A2A | **统一 Memory API** [23] | Crews/Flows | Ollama/LM Studio | **高** |

安装示例（框架官方 README，openKylin 上需自备 Python 版本）：

~~~bash
# LangGraph
pip install -U langgraph

# AgentScope 2.0（需 Python 3.11+）
uv pip install agentscope

# Qwen-Agent（含 MCP extra）
pip install -U "qwen-agent[gui,rag,code_interpreter,mcp]"

# CrewAI（官方 Linux）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install crewai
~~~

---

## 三、openKylin Token Center（重点）

| 项 | 结论 | 来源 |
|----|------|------|
| 是否 OpenAI-compatible | **是**（官方原文「完全兼容 OpenAI 接口协议」） | [4] |
| API Base / Chat | `https://llm-gateway.openkylin.top/v1/chat/completions` | [4] |
| 申请 Key | openKylin **3.0 预装** Token 中心客户端 →「Token申请和管理」→ 审批 →「领取 API Key」；**完整 Key 仅领取时显示一次** | [3][4] |
| 模型（2026-09-09） | qwen3.8-max、qwen3.7-max、qwen3.7-plus、deepseek-v4-pro、deepseek-v4-flash | [4] |
| 免费额度 | **每日签到**自动入账、调用扣减、可累积；3.0 宣传「万亿 Token」与邀请加成 | [3][4] |
| 数值额度 / RPM | **官方公开页未给出**每日具体数值与限流表 [open question] | [4] |
| 可接入 Agent | 官方点名：KylinBot、WorkBuddy、OpenClaw、DeepSeek Harness、Codex、Claude Code 等 | [4] |
| 形成链路 | `Agent/框架 → OpenAI-compatible → Token Center 网关 → qwen* / deepseek*` **官方叙事成立**；实测需自备 Key | [4] |

### Python（OpenAI SDK）示例 [基于官方 OpenAI 兼容声明][4]

~~~python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["OPENKYLIN_TOKEN_API_KEY"],  # 领取后仅进程环境变量
    base_url="https://llm-gateway.openkylin.top/v1",
)
resp = client.chat.completions.create(
    model="deepseek-v4-flash",  # 或 qwen3.8-max 等，以 Token 中心列表为准
    messages=[{"role": "user", "content": "用一句话介绍 openKylin"}],
    temperature=0,
)
print(resp.choices[0].message.content)
~~~

### curl 示例

~~~bash
export OPENKYLIN_TOKEN_API_KEY='从 Token 中心领取的 Key'
curl -sS "https://llm-gateway.openkylin.top/v1/chat/completions" \
  -H "Authorization: Bearer ${OPENKYLIN_TOKEN_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-v4-flash",
    "messages": [{"role":"user","content":"ping"}],
    "temperature": 0
  }'
~~~

**与忆衡/KMB 对接**：与现有 `configs/agent-grok.yaml` 同类——新建 `type: http`，`base_url: https://llm-gateway.openkylin.top/v1`，`endpoint: /chat/completions`，`api_key_env: OPENKYLIN_TOKEN_API_KEY`，`model` 填 Token 中心模型名。无 `kmb_evidence` 时仅文本轨，记忆维会 miss。

---

## 四、MCP / Skill 体系

| 层级 | 核实 |
|------|------|
| 系统/3.0 | 官方：智能体通过 **MCP 协议直接调用桌面能力**，无需模拟点击 [2] |
| 技能仓 | openkylin-skills：SKILL/脚本类技能 + install.sh 多 Agent 路径 [11][12] |
| OpenClaw | MCP 与 Skills **分离**：`mcp.servers` vs SKILL.md [15][13] |
| openkylin-skills↔MCP | 技能仓**未**文档化 MCP Server 包；不能写成「openkylin-skills = MCP 官方服务器注册表」[11] |
| 其它 Agent | 3.0/Token 新闻称 WorkBuddy/OpenClaw 等可跑在 3.0 并用 Token；是否绑定同一套 MCP Server **需实机/发行说明** [2][4] |
| AgentScope/Qwen-Agent | 框架侧有 MCP 能力；能否调 openKylin 桌面 MCP **取决于系统是否暴露 MCP Server 端点**——官方 MCP Server 安装包/启动命令**本轮未在 openkylin 官方页抓到** [open question] |

**真实可执行示例（技能，非 MCP）** [11][12]：

~~~bash
# 在 openKylin 上为 OpenClaw 安装 openkylin-skills
curl -fsSL https://gitee.com/openkylin/openkylin-skills/raw/master/install.sh \
  | bash -s -- --agent openclaw --category ukui

# 会话内或 CLI 触发（OpenClaw）
openclaw skills load <skill-name>
~~~

**Astron 本地（赛事路径）** [17][18]：

~~~bash
git clone https://github.com/iflytek/astron-agent.git
cd astron-agent/docker/astronAgent
cp .env.example .env
# 修改 .env 中密钥与端口后
docker compose -f docker-compose-with-auth.yaml up -d
~~~

---

## 五、总表（字段压缩，空=本轮官方源未证实）

| 项目 | 类型 | openKylin 级别 | 版本 | 安装 | 官方地址 | 开源 | License | 免费安装 | 免费使用 | 额度/限制 | OpenAI API | MCP | Skill | Memory | 长期记忆 | 多Agent | 本地模型 | 适合 KMB |
|------|------|----------------|------|------|----------|------|---------|----------|----------|-----------|------------|-----|-------|--------|----------|---------|----------|----------|
| KylinBot | 系统级 Agent | **官方** | 3.0 原生 | 系统/3.0 生态 | openkylin.top 新闻；独立仓 403 | 未证实开源仓 | — | 系统侧 | — | Token 签到 | 经 Token 中心 [4] | 官方称桌面 MCP [2] | openkylin-skills [11] | 待实机 | 待实机 | 待实机 | 系统模型服务 [9] | **高（command）** |
| OpenClaw | 开源 Agent | **官方声明可运行** + 社区本体 | — | `install.sh` / npm [14] | github.com/openclaw/openclaw | 是 | MIT [13] | 是 | 是（无 paid tier）[13] | 模型另计 | 可接 Token [4] | `mcp.servers` [15] | SKILL.md + openkylin-skills | 文档有记忆能力（未展开） | 视配置 | 有限 | 待核实 | **高** |
| WorkBuddy | AI 工作台 | **官方商店** | 2.0+ [6] | 商店搜索安装 [6] | news/4115 | 闭源产品 | — | 商店可装 | 未知 | 未知 | 多模型接入 [6] | 未证实 | 未证实 | 未知 | 未知 | 未知 | 未知 | **低（GUI）** |
| Raccoon Work | AI 办公 | **官方商店适配** | 2026-08-26 适配 [7] | 商店「商汤小浣熊」[7] | news/4096 | 闭源 | — | 商店可装 | 未知 | 未知会员/积分 | 未证实 | 未证实 | 未证实 | 未知 | 未知 | 未知 | 未知 | **低** |
| AutoClaw | AI 工作助手 | **官方商店** | 2026-09-14 [8] | 商店搜索 [8] | news/4135 | — | — | 商店可装 | 未知 | 未知 | 未知 | 未知 | 50+ Skills [8] | 未知 | 未知 | 集群并行 [8] | 未知 | **低–中** |
| AgentOS | 生态镜像/Runtime | **官方** | 3.0 更新 2026-09-07 [9] | 官网生态下载 [9] | news/4122 + SIG | SIG 组件开源向 | 各包 | 生态镜像 | — | Token 另计 | 统一推理 [9] | 系统叙事 [2] | agent-skills [10] | agent-memory [10] | SIG 目标 | Runtime/Harness | uni-model-infer [10] | **高（跑在 3.0）** |
| openkylin-skills | Skill 生态 | **官方 org + 社区维护** | install.sh 1.0.0 [11] | curl install.sh [11] | gitee.com/openkylin/openkylin-skills | 是（Gitee） | MulanPSL-2.0（README）[12] | 是 | 是 | — | — | 仓内未写 MCP [11] | 本体 | — | — | — | — | 间接（行为） |
| Astron Agent | 编排平台 | **官方赛事要求本地部署** [17] | 开源版 | Docker Compose [18] | github.com/iflytek/astron-agent | 是 | Apache-2.0 [16] | 是 | 是（本地） | 自托管 | 模型管理 [16] | 是 [16] | Skillhub [18] | **Memory DB** [18] | 工作流级 | 可配模型 | **中–高** |
| LangChain | 框架 | **仅 Linux** | 1.x | pip/uv [19] | github.com/langchain-ai/langchain | 是 | MIT | 是 | 是 | — | 是 | extras | — | 依赖 LangGraph | 中 | 是 | Ollama | 中 |
| LangGraph | 框架 | **仅 Linux** | 1.2.x | pip [20] | github.com/langchain-ai/langgraph | 是 | MIT | 是 | 是 | — | 是 | 生态 | — | store 长期记忆 [21] | **是** | **是** | 是 | **高** |
| AgentScope 2.0 | 框架 | **仅 Linux** | 2.0.8 (2026-09-08) | pip/uv, Py≥3.11 [22] | github.com/agentscope-ai/agentscope | 是 | Apache-2.0 | 是 | 是 | — | 是 | Toolkit | — | Agentic/ReMe/Mem0 [22] | **是** | Team | Ollama | **高** |
| Qwen-Agent | 框架 | **仅 Linux** | 0.0.34 | pip extras mcp | github.com/QwenLM/Qwen-Agent | 是 | Apache-2.0 | 是 | 是 | DashScope 或自备 | OpenAI-compatible | **是** | MCP memory 示例 | RAG 向 | 有限 | vLLM/Ollama | 中 |
| AutoGen | 框架 | **仅 Linux** | 维护模式 | pip agentchat [24] | github.com/microsoft/autogen | 是 | MIT | 是 | 是 | — | 是 | McpWorkbench | — | 会话级 | **是** | 可 | 中低 |
| CrewAI | 框架 | **仅 Linux** | — | `uv tool install crewai` [23] | github.com/crewAIInc/crewAI | 是 | MIT | 是 | 是 | OpenAI/自备 | 默认 OpenAI | MCP/A2A | — | **统一 Memory** [23] | **是** | Ollama | **高** |

---

## 六、KylinMemoryBench：哪些「当前项目可以测试」

### 6.1 已具备适配器（仓库事实）

| type | 用途 | 证据 |
|------|------|------|
| `deterministic` reference/flawed | 离线校验评分器 | README / offline demo |
| `command` | stdin 案例 JSON → stdout `kmb_evidence` JSONL | `kmb/agents.py` CommandAgent；`agent-kylinbot-process.yaml` |
| `http` / openai_compatible | OpenAI 兼容 Chat；无证据则记忆 miss | `docs/evidence-protocol.md` |
| `memory_controller` | 包装层系统级记忆（**非原生**） | 协议 + 既有 Grok/DeepSeek 运行 |
| `memory_disabled` | 同后端无记忆对照 | 配置三件套 |
| `replay` | 外部导出 JSONL 重放评分 | `agent-replay-example.yaml` |

### 6.2 可测性矩阵（按对象）

| 对象 | 当前能否进 KMB | 接入方式 | 记忆结论边界 |
|------|----------------|----------|--------------|
| reference / flawed | **已可测** | 内置 | 模拟基线，非真实 Agent |
| kylinbot-process stand-in | **已可测**（离线 demo） | `type: command` | `source=process`，stand-in ≠ 原生 KylinBot |
| Grok / DeepSeek API | **已可测**（有 Key） | `type: http` + wrapper/no-memory | 包装轨系统级；`native_memory_events=0` |
| Token Center（qwen/deepseek） | **有 Key 即可测** | 新建 `type: http` + gateway | 同 HTTP 文本轨；无 kmb_evidence 则记忆维 miss |
| **真实 KylinBot** | **需实机 + 证据导出包装** | 把 `command` 指到包装：调 KylinBot → 导出 JSONL | 决策须来自 Bot 自身，包装不代写 op |
| **OpenClaw** | **较可测**（CLI） | `command` 包装读会话/Skill/文件日志 → kmb_evidence；或 MCP memory 工具日志 | 需导出 write/recall/suppress，否则仅行为轨 |
| WorkBuddy / Raccoon / AutoClaw | **默认不可作记忆主测** | GUI；无官方 API/证据协议则无法自动评分 | 不宜写入主结论 |
| Astron Agent（本地） | **中等** | Memory DB/工作流日志 → `replay`/`command` | 可谈「平台记忆行为」，非模型原生 |
| LangGraph / AgentScope / CrewAI 自建双记忆 | **可测（B 轨）** | 自写 Agent 暴露 save/recall 工具并输出 kmb_evidence | 适合机制对比；框架本身≠赛题「智能体产品」 |
| Qwen-Agent + MCP memory | **可测** | command 包装 + MCP server-memory 日志导出 | 同上 |
| AutoGen | 可测但非优先 | 维护模式 | 对长期记忆评测优先级低 |

### 6.3 一句话

**当前项目「现在就能跑」的是：离线基线 + kylinbot-process + 任意 OpenAI-compatible HTTP（含未来的 Token Center）+ 包装轨 + replay。**  
**要测「智能体长期记忆」主结论，缺的是：openKylin 实机上两款能导出真实记忆事件的被测对象（优先 KylinBot/kylin-agent 与 OpenClaw），而不是再包一层让分数好看。**

---

## 七、若目标是「openKylin 多 Agent 长期记忆 Benchmark」：优先部署建议

维度定义：安装难度 · 开放程度 · API · MCP · Memory · 长期运行 · 自动化测试 · 可复现 · 免费程度（1–5，5 最好；**相对排序，非绝对分**）。

| 优先级 | 对象 | 安装 | 开放 | API | MCP | Memory | 长期运行 | 自动化 | 可复现 | 免费 | 理由 |
|--------|------|------|------|-----|-----|--------|----------|--------|--------|------|------|
| **P0** | openKylin 3.0 + Token Center + KMB CLI | 3（装 3.0/VM） | 4（OpenAI 网关） | 5 | — | — | 4 | 5 | 5 | 4（签到额度） | 统一模型后端，已有 `http` 适配器可直接配 |
| **P0** | KylinBot / kylin-agent（command 包装） | 3（需 3.0/导出） | 3（官方智能体，仓不完全透明） | 3（经 Token） | 4（官方 MCP 叙事） | 4（系统/技能） | 4 | 4（CLI/包装） | 3（需锁定版本） | 4 | **最对题**：赛题点名生态 Agent |
| **P1** | OpenClaw | 4（install.sh） | 5（MIT、公开 GitHub） | 4（自选模型/Token） | 5（mcp.servers） | 3–4（会话/文件/MCP memory） | 4 | 4（CLI） | 4 | 5（本体免费） | 与 KylinBot 互比叙事强；证据导出需工程包装 |
| **P1** | LangGraph **或** AgentScope 2.0 **或** CrewAI（B 轨双记忆） | 4（pip，注意 Py 版本） | 5 | 5 | 4–5 | **5** | 4 | 5（纯代码） | **5** | 5 | **区分度与机制解释**最强；结论写「记忆机制」不写「模型记忆」 |
| **P2** | Astron Agent + Skillhub 本地 | 2（Docker/磁盘） | 5（Apache-2.0） | 4 | 5 | 5（Memory DB） | 3（自托管） | 3–4 | 3（组件多） | 5 | Hack-Astron 生态加分；偏工作流平台 |
| **P3** | WorkBuddy / Raccoon / AutoClaw | 5（商店） | 1–2（闭源 GUI） | 1–2 | 1–2 | 不可观测 | 3 | **1** | 2 | 未知 | 适合演示/生态，**不适合**自动记忆评分主结论 |
| **P3** | Qwen-Agent | 4 | 5 | 5 | 5 | 3 | 4 | 4 | 4 | 5 | MCP+本地 Qwen 好；长期记忆弱于 LangGraph 系 |
| **不优先** | AutoGen | 4 | 5 | 5 | 4 | 3 | 2（维护模式） | 4 | 4 | 5 | 新项目应评估 Microsoft Agent Framework |

**建议落地顺序（客观，不绑定单一“最好”）：**

1. **环境 P0**：openKylin 3.0（或 AgentOS 镜像）VM + Token Center Key → KMB `type: http` 打通 qwen/deepseek 文本轨（证明统一模型通路）。  
2. **被测 P0**：在 VM 安装/启用 **KylinBot（或 kylin-agent）**，只写 **evidence exporter**（`type: command`），跑最小 `native_memory_events>0` 门禁。  
3. **被测 P1**：安装 **OpenClaw**，第二套 exporter；两 Agent 同 `core-zh`（及决策留给 Agent 的案例）对比 → 赛题主叙事。  
4. **机制 P1**：同一 Token/本地模型 + **两套真实记忆实现**（例如 AgentScope Mem0 vs 精确 KV，或 LangGraph store vs CrewAI Memory）→ 解释分差，防止 wrapper 送分。  
5. **生态 P2/P3**：Astron/Skills/商店 GUI 作演示与生态章节，**不进主雷达**，除非导出可核验证据。

**为什么不是只选一个框架/产品：**  
- 赛题要求「至少两款智能体」且在 **openKylin 桌面环境**演示 [官方赛题新闻 4094] → 需要 **系统/生态 Agent 对**，不能只跑两个 pip 框架。  
- 评分科学需要 **记忆机制可归因** → 需要 B 轨框架/双记忆，避免 Grok-wrapper vs DeepSeek-wrapper 同分被解读成「记忆一样强」。  
- 自动化与可复现 → OpenClaw/KylinBot 必须能 **非交互脚本化 + 导出 kmb_evidence**；GUI 商店应用在这三项上客观最弱。

---

## Open questions

1. KylinBot **独立源码仓、是否预装包名、CLI/API 文档**（Gitee kylinbot 403）。  
2. Token Center **每日签到具体额度、RPM/TPM、`/v1/models` 是否存在**（官方未给数值）。  
3. openKylin 3.0 **系统 MCP Server 的安装包名与启动方式**（仅有「经 MCP 调桌面」叙事，未见 Server 发行说明）。  
4. WorkBuddy / Raccoon / AutoClaw 的 **免费限制、会员/积分、是否有 API/MCP 开放**。  
5. AgentOS 中 **agent-memory / agent-benchmark** 是否已发布可运行包及与 KMB 的接口（SIG 列表存在，产物需 Gitee 细读）。  
6. OpenClaw 在 openKylin 上的 **本地模型路径与默认记忆落盘位置**（便于 exporter）。  
7. 历史 VM 仍为 **2.0 SP2**；官方 Agent 叙事绑 **3.0**——评测环境是否升级需负责人决策。

---

## Sources

[1] openKylin 3.0 版本正式发布 — https://www.openkylin.top/news/4098-cn.html (published 2026-09-07, accessed 2026-09-18)  
[2] 同上（MCP 桌面能力与多智能体可运行声明）— https://www.openkylin.top/news/4098-cn.html  
[3] 同上（Token 中心预装与每日签到）— https://www.openkylin.top/news/4098-cn.html  
[4] Token 中心模型上新与 OpenAI 兼容接入 — https://www.openkylin.top/news/4131-cn.html (published 2026-09-09, accessed 2026-09-18)  
[5] 同 [4] 模型列表与 Key 领取说明  
[6] WorkBuddy 上架 openKylin 软件商店 — https://www.openkylin.top/news/4115-cn.html (published 2026-09-07, accessed 2026-09-18)  
[7] 商汤小浣熊 Raccoon Work openKylin 适配 — https://www.openkylin.top/news/4096-cn.html (published 2026-09-07, accessed 2026-09-18)  
[8] AutoClaw 上架 openKylin 软件商店 — https://www.openkylin.top/news/4135-cn.html (published 2026-09-14, accessed 2026-09-18)  
[9] openKylin 3.0 AgentOS 更新 — https://www.openkylin.top/news/4122-cn.html (published 2026-09-08, accessed 2026-09-18)  
[10] AgentOS SIG 维护范围 — https://gitee.com/openkylin/community/tree/master/sig/AgentOS (accessed 2026-09-18)  
[11] openkylin-skills install 与路径 — https://gitee.com/openkylin/openkylin-skills (accessed 2026-09-18)  
[12] openkylin-skills README（技能清单/维护者/License 声称）— https://gitee.com/openkylin/openkylin-skills/raw/master/README.md (accessed 2026-09-18)  
[13] OpenClaw GitHub — https://github.com/openclaw/openclaw (accessed 2026-09-18)  
[14] OpenClaw 安装说明（README）— https://github.com/openclaw/openclaw (accessed 2026-09-18)  
[15] OpenClaw MCP 文档 — https://docs.openclaw.ai/tools/mcp (accessed 2026-09-18)  
[16] Astron Agent GitHub — https://github.com/iflytek/astron-agent (accessed 2026-09-18)  
[17] Hack-Astron x openKylin — https://www.openkylin.top/news/4123-cn.html (published 2026-09-08, accessed 2026-09-18)  
[18] Astron 安装/模块文档 — https://iflytek.github.io/astron-agent/zh/guide/quick-start 与 .../PROJECT_MODULES (accessed 2026-09-18)  
[19] LangChain GitHub/PyPI — https://github.com/langchain-ai/langchain (accessed 2026-09-18)  
[20] LangGraph GitHub — https://github.com/langchain-ai/langgraph (accessed 2026-09-18)  
[21] LangGraph Memory 文档 — https://docs.langchain.com/oss/python/langgraph/memory (accessed 2026-09-18)  
[22] AgentScope GitHub + long-term memory 文档 — https://github.com/agentscope-ai/agentscope · https://docs.agentscope.io/latest/en/building-blocks/long-term-memory (accessed 2026-09-18)  
[23] CrewAI GitHub + Memory 文档 — https://github.com/crewAIInc/crewAI · https://docs.crewai.com/en/concepts/memory (accessed 2026-09-18)  
[24] AutoGen GitHub（maintenance mode）— https://github.com/microsoft/autogen (accessed 2026-09-18)  
[25] openKylin 3.0 公测/ KylinBot 验证相关 — https://www.openkylin.top/news/4129-cn.html (published 2026-09-09, accessed 2026-09-18)  
[26] 赛题：长期记忆 Benchmark 设计 — https://www.openkylin.top/news/4094-cn.html (published 2026-09-07, accessed 2026-09-18)  

**研究限制**：子代理反馈部分会话 WebSearch 不可用，官方站点与 Gitee/GitHub 直抓为主；negative（「未官方适配」）结论基于已抓取官方页，不能外推到未检索的私有文档。
