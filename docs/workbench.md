# 本地评测工作台

## 0.2.4 自动发现与新建评测（2026-10-14）

“新建评测”默认进入“已安装智能体 · 自动发现”，主智能体和对比智能体直接选择小K KylinBot、OpenClaw 等后端注册表条目。已安装但当前评测目录未准备的 Hermes、需手动观测的 KylinAgent 仍显示实际状态，未就绪时不能启动。两侧使用同一套件、Seed、重试和超时；后端经 `POST /api/runs` 的 `source=installed` 传入既有真实适配器和 runner。可选快速或其他有效套件，不会忽略所选参数，也不会改写智能体自身模型和凭据。

安装检查发生在工作台服务所在系统、当前 OS 用户的目录中：PATH 之外还检查 `.local/bin`、npm/pnpm、Bun、Hermes 运行时及系统常用可执行文件目录；配置文件只检查存在性，不读取内容。返回可执行文件路径、检测来源、宿主机名和时间；进入总览、智能体、新建评测页及页面可见时每 30 秒重新发现，用户也可点“重新检测”。检查不会启动 Agent、执行模型连接请求或扫描整块磁盘。

**检测范围是后端所在主机。** Windows 浏览器通过 SSH 隧道访问 VM 服务时，检查的是 openKylin VM；不能据此声称 Windows 宿主系统的安装已检测。当前默认支持四款已实现适配器的智能体，不宣称识别所有第三方应用。配置或命令存在、评测目录就绪也不代表云端认证与余额已验证；最近额度不足继续按真实历史结果显示。

“高级配置 · 记忆层 / 对照”保留原 YAML 流程。`b-memory-kv-real` 是键值记忆层的云模型方案，`b-memory-similar-real` 是相近信息检索记忆层的云模型方案；不带 `real` 的对应配置是本地规则方案。这些是评测配置，不是本机安装的智能体。云模型配置需要工作台 API 档案，离线规则配置无需云凭据。

按负责人要求，本轮仅做静态审阅、语法、构建部署和页面/安装元数据核对，没有运行测试套件或真实 Agent 回合。0.2.4 未发布正式标签，0.2.2 历史测试和分数不能视为当前版本回归结果。

## 0.2.3 智能体页修复（2026-10-13）

“智能体”页的“本机智能体”来自后端 `GET /api/agents` 对真实可执行文件和存储路径的发现，优先显示小K KylinBot、OpenClaw、Hermes 和 KylinAgent。勾选两款就绪参与者后，“开始快速对比”通过 `POST /api/quick-compare` 进入现有真实 CLI 适配器和 runner；没有用 YAML 模板冒充系统安装。

后端分别报告本机安装与当前评测目录就绪。使用独立记忆副本时，Hermes 在本机已安装但副本未准备，会显示“当前目录未就绪”；KylinAgent 当前适配器仍需要手动观测。详情只显示路径元数据、凭据来源、最近运行和评测范围，不读取或返回密钥。

页面将 YAML 自定义方案、离线基线和回放归入“评测方案与示例”。本地记忆方案/回放显示“无需云凭据”，命令适配器显示“智能体自行管理”，HTTP 实调用按真正使用的 API 环境变量判断。底栏的“工作台 API 未配置凭据”只适用于工作台 API 档案，不代表独立智能体缺凭据。

最近运行的额度不足、鉴权或超时来自已有结果 JSON，单独呈现；“命令/存储就绪”不等于当前云端余额或连接已验证。补充 Token 后可以重新执行，但当前负责人要求先修改，本轮不运行测试套件或模型请求。0.2.3 正式标签尚未发布，旧 0.2.2 验证结果保留为历史基线。

KylinMemoryBench 工作台是 CLI 之上的本地浏览器界面。它读取 `runs/`、`configs/`、`suites/` 中的真实文件，并通过受控后端调用现有 `kmb` runner；没有第二套评分逻辑，也不会把模型文本推断成记忆状态。

## 启动

在 openKylin 或其他已安装项目依赖的环境中执行：

```bash
python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .
```

然后在本机浏览器打开 `http://127.0.0.1:8765/`。`--host` 默认只绑定回环地址；需要远程访问时应由用户自行配置受控 SSH 隧道，不要直接暴露到公共网卡。

## 快速对比

总览页会调用 `GET /api/agents` 发现当前主机已安装的 KylinBot、Hermes、OpenClaw 和 KylinAgent。用户只需选择两个标记为“可自动运行”的 Agent，点击“开始快速对比”；后端使用固定 `suites/quick.yaml`、Seed `42`、重试 `1`、单案例超时 `180` 秒，并在完成后自动打开结果中心。工作台不会下载或安装 Agent。

KylinAgent 即使检测到运行时和数据库，也会显示为“已安装但不可自动驱动”，因为当前适配器只能确认 GUI/服务级状态，不能伪造结构化记忆事件。需要自定义套件或参数时进入“新建评测”的已安装智能体模式；需要 YAML 记忆层或对照配置时选择高级配置。详细用户步骤见 [`docs/quick-start.md`](quick-start.md)。

`serve` 启动时会尝试读取 `~/.config/kmb/credentials.env`。只有文件权限为 `600` 时才加载，并且只读取固定的 `GROK_*`、`DEEPSEEK_*` 字段及工作区配置档案中声明的安全环境变量名；已有进程环境变量优先。文件不存在或权限不安全时，页面会显示“未检测到凭据”，云端连接检查不会成功。Windows 本机服务不会自动获得 openKylin VM 的凭据，需在 VM 内启动工作台，或通过受控 SSH 隧道访问 VM 服务。

## 界面与数据来源

- **新建评测**：默认选择两个实际发现的智能体、套件、seed、重试和超时；高级配置模式另保留 YAML 档案。两个 Agent 共用同一组参数；修改后界面显示“比较参数已变化”。运行由后端异步触发，结果写入 `runs/workbench/<job-id>/`。
- **结果中心**：显示运行 ID、套件哈希、六个固定维度（长期保持、记忆调用、动态更新、相近区分、边界识别、任务复用）、稳定性摘要和失败入口。条形图是精确比较，雷达图只作概览。
- **失败案例**：从结果 JSON 的失败项定位到同一案例的 `evidence.jsonl`，在侧栏展示事实/版本、状态操作、来源、动作、工件、退出码和规则理由。证据不存在时显示未观测，而不是通过。
- **历史运行**：只读浏览工作区内的单 Agent 和双 Agent 结果，并标记包装层、无记忆基线、模拟基线或失败运行。
- **API 配置**：页面默认将 Grok、DeepSeek 作为正式云端提供商展示；每个提供商下的“标准 API”“记忆开启”“无记忆基线”是运行模式，不是额外模型版本。通过“新增 API 配置档案”可以接入其他 OpenAI-compatible Chat Completions 服务。表单只提交配置标识、名称、Base URL、接口路径、模型 ID、超时和 `api_key_env`，后端以白名单字段原子写入 **三件套**（与 CLI `scripts/register_openai_agent.py` 对齐），禁止覆盖已有档案和提交 `api_key`/Authorization/headers。新增档案会进入“其他 API、本地基线与接入模板”区域，并可直接发起连接检查。
- **系统设置**：显示 Python、PyYAML、CLI、目录和系统级场景能力矩阵。普通包装层重建不会显示为真实系统重启。

## 新增 API 配置

工作台只接受 OpenAI-compatible 的 JSON Chat Completions 接口。网页表单只保存非敏感元数据，API Key 必须在同一运行环境中通过安全凭据文件或进程环境变量提供。新增档案会出现在“其他 API、本地基线与接入模板”区域。

**提交后自动生成三件套**（与 `python -m kmb.cli register-agent` / `scripts/register_openai_agent.py` 共用 `kmb/register.py` 字段约定；任一目标文件已存在则整体拒绝）：

| 文件 | type | 接入层级 |
|------|------|----------|
| `configs/agent-<id>.yaml` | `http` | **仅连通**（只观测模型文本） |
| `configs/agent-<id>-memory.yaml` | `memory_controller` | **具备可观测证据**（`source=wrapper`，系统级包装轨） |
| `configs/agent-<id>-no-memory.yaml` | `memory_disabled` | 同一后端无记忆对照（`no_memory_baseline`） |

表述边界：包装轨可支撑长期记忆评测的系统级结论；**不得**写成「模型原生长期记忆」。http 轨仅用于连通与对照，不能单独作为长期记忆验收。

**R0**：工作台自动生成的三件套属于 **C 轨（对照/接入）**，不得作为赛题「不同智能体原生/可观测记忆」主结论。A/B 主结论路径、证据门禁与状态标签见 [`docs/native-memory-compare.md`](docs/native-memory-compare.md)。功能（自动包装、register-agent）**保留**，仅叙事降级。

配置示例（http 轨；memory / no-memory 由后端一并写出）：

```yaml
name: openrouter
type: http
base_url: https://openrouter.ai/api/v1
endpoint: /chat/completions
model: openai/gpt-4.1-mini
api_key_env: OPENROUTER_API_KEY
timeout_seconds: 60
request_options:
  temperature: 0
```

推荐在「新建评测」中选用 `<id>-memory` 与另一款 memory 配置做对比。

凭据文件示例（输入时不回显密钥）：

```bash
umask 077
mkdir -p ~/.config/kmb
chmod 700 ~/.config/kmb
read -rsp "OPENROUTER_API_KEY: " KMB_NEW_KEY; printf '\n'
tmp="$(mktemp ~/.config/kmb/credentials.XXXXXX)"
grep -v '^OPENROUTER_API_KEY=' ~/.config/kmb/credentials.env 2>/dev/null > "$tmp" || true
printf 'OPENROUTER_API_KEY=%s\n' "$KMB_NEW_KEY" >> "$tmp"
chmod 600 "$tmp" && mv "$tmp" ~/.config/kmb/credentials.env
unset KMB_NEW_KEY
```

服务启动或刷新配置时，会读取固定的 Grok/DeepSeek 变量，以及工作区配置档案中声明的安全环境变量名。已有进程环境变量优先。凭据文件必须是 `600`，不安全权限会被拒绝。非 OpenAI-compatible 服务不能只靠此表单接入，应使用经过验证的 `type: command` 或外部适配器并遵守 JSONL `EvidenceEvent` 协议。

## 安全边界

后端只允许读取 `configs/`、`suites/`、`docs/` 和 `runs/`，运行输出固定在 `runs/workbench/`。请求拒绝 `..` 路径、非白名单后缀和超大工件。健康检查和运行只从已有配置的 `api_key_env` 读取进程环境变量；服务启动/刷新时会先从权限为 `600` 的安全凭据文件加载允许变量，错误和响应经过脱敏处理。

结果中的 `source=model` 表示模型请求/响应或未证实自述，`source=wrapper` 表示外部包装层操作，`source=simulated` 表示离线基线，`source=runner` 表示运行器观察。当前 Grok/DeepSeek 没有原生记忆状态事件，所有包装层分数只能表述为“模型后端 + 统一包装层”的系统级长期记忆行为。

## 复现

界面启动的作业仍等价于现有命令：

```bash
python -m kmb.cli compare --agents <agent-a.yaml> <agent-b.yaml> \
  --suite <suite.yaml> --out runs/workbench/<job-id> \
  --seed <seed> --retries <retries> --timeout <seconds>
```

实际作业的配置、套件哈希、评分器版本和结果目录保存在 `workbench-run.json` 与 `workbench-job.json`；密钥永不写入这些文件。
