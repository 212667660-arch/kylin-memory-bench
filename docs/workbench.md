# 本地评测工作台

KylinMemoryBench 工作台是 CLI 之上的本地浏览器界面。它读取 `runs/`、`configs/`、`suites/` 中的真实文件，并通过受控后端调用现有 `kmb` runner；没有第二套评分逻辑，也不会把模型文本推断成记忆状态。

## 启动

在 openKylin 或其他已安装项目依赖的环境中执行：

```bash
python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .
```

然后在本机浏览器打开 `http://127.0.0.1:8765/`。`--host` 默认只绑定回环地址；需要远程访问时应由用户自行配置受控 SSH 隧道，不要直接暴露到公共网卡。

`serve` 启动时会尝试读取 `~/.config/kmb/credentials.env`。只有文件权限为 `600` 时才加载，并且只读取固定的 `GROK_*`、`DEEPSEEK_*` 字段及工作区配置档案中声明的安全环境变量名；已有进程环境变量优先。文件不存在或权限不安全时，页面会显示“未检测到凭据”，云端连接检查不会成功。Windows 本机服务不会自动获得 openKylin VM 的凭据，需在 VM 内启动工作台，或通过受控 SSH 隧道访问 VM 服务。

## 界面与数据来源

- **新建评测**：选择两个配置档案、套件、seed、重试、超时和评分器版本。两个 Agent 共用同一组参数；修改后界面显示“比较参数已变化”。运行由后端异步触发，结果写入 `runs/workbench/<job-id>/`。
- **结果中心**：显示运行 ID、套件哈希、六个固定维度（长期保持、记忆调用、动态更新、相近区分、边界识别、任务复用）、稳定性摘要和失败入口。条形图是精确比较，雷达图只作概览。
- **失败案例**：从结果 JSON 的失败项定位到同一案例的 `evidence.jsonl`，在侧栏展示事实/版本、状态操作、来源、动作、工件、退出码和规则理由。证据不存在时显示未观测，而不是通过。
- **历史运行**：只读浏览工作区内的单 Agent 和双 Agent 结果，并标记包装层、无记忆基线、模拟基线或失败运行。
- **API 配置**：页面默认将 Grok、DeepSeek 作为正式云端提供商展示；每个提供商下的“标准 API”“记忆开启”“无记忆基线”是运行模式，不是额外模型版本。通过“新增 API 配置档案”可以接入其他 OpenAI-compatible Chat Completions 服务。表单只提交配置标识、名称、Base URL、接口路径、模型 ID、超时和 `api_key_env`，后端以白名单字段原子写入 `configs/agent-*.yaml`，禁止覆盖已有档案和提交 `api_key`/Authorization/headers。新增档案会进入“其他 API、本地基线与接入模板”区域，并可直接发起连接检查。
- **系统设置**：显示 Python、PyYAML、CLI、目录和系统级场景能力矩阵。普通包装层重建不会显示为真实系统重启。

## 新增 API 配置

工作台只接受 OpenAI-compatible 的 JSON Chat Completions 接口。网页表单只保存非敏感元数据，API Key 必须在同一运行环境中通过安全凭据文件或进程环境变量提供。新增档案会出现在“其他 API、本地基线与接入模板”区域。

配置示例：

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
