# openKylin Token Center 接入说明

> 调研依据：`research/openkylin-agent-ecosystem/REPORT.md`（2026-09-18）  
> 配置模板：`configs/agent-openkylin-token.yaml`  
> **本轮未在 VM 实测 Token Center**；模板仅为接入准备。

## 官方要点（2026-09-09 openkylin.top）

| 项 | 内容 |
|----|------|
| 预装 | openKylin **3.0**「Token 中心」客户端 |
| 协议 | **完全兼容 OpenAI** |
| Base URL | `https://llm-gateway.openkylin.top/v1` |
| Chat 接口 | `https://llm-gateway.openkylin.top/v1/chat/completions` |
| Key 申领 | 客户端「Token 申请和管理」→ 审批 → 领取；**完整 Key 仅显示一次** |
| 额度 | 免费额度靠**每日签到**入账，调用扣减、可累积；**每日数值 / RPM 官方未公开**，本文不编造额度表 |
| 模型名（官方新闻示例） | `deepseek-v4-flash`、`deepseek-v4-pro`、`qwen3.8-max`、`qwen3.7-max`、`qwen3.7-plus`；**以客户端列表为准** |
| 链路 | `Agent → OpenAI-compatible → Token Center → qwen/deepseek 等`（官方叙事） |

## 环境变量（密钥不进仓库）

```bash
# bash
export OPENKYLIN_TOKEN_API_KEY='仅在申领后写入本机环境'
```

```powershell
# PowerShell
$env:OPENKYLIN_TOKEN_API_KEY = "仅在申领后写入本机环境"
```

也可写入 `~/.config/kmb/credentials.env`（权限 `600`），仅含变量名=值，**不要**提交到 Git。

## 配置模板

`configs/agent-openkylin-token.yaml` 关键字段：

- `type: http`
- `base_url: https://llm-gateway.openkylin.top/v1`
- `endpoint: /chat/completions`
- `api_key_env: OPENKYLIN_TOKEN_API_KEY`
- `model` 默认 `deepseek-v4-flash`（可按客户端列表改）

**表述边界**：无 `kmb_evidence` 时 HTTP 轨仅文本可观测，记忆维可能 miss；**不能**单独作为长期记忆验收。包装轨见 `memory_controller`，仍属系统级 C 轨对照。

## 运行示例（有 Key 后）

```bash
python -m kmb.cli run \
  --agent configs/agent-openkylin-token.yaml \
  --suite suites/core-zh.yaml \
  --out runs/openkylin-token-smoke \
  --seed 42 --retries 1 --timeout 180
```

与包装层对比（系统级，非原生记忆）：

```bash
# 可基于本模板复制为 type: memory_controller 后 compare
python -m kmb.cli compare \
  --agents configs/agent-openkylin-token.yaml configs/agent-reference.yaml \
  --suite suites/core-zh.yaml \
  --out runs/openkylin-token-vs-ref \
  --seed 42 --retries 1 --timeout 180
```

自动生成三件套亦可：

```bash
python -m kmb.cli register-agent \
  --name openkylin-token \
  --base-url https://llm-gateway.openkylin.top/v1 \
  --model deepseek-v4-flash \
  --api-key-env OPENKYLIN_TOKEN_API_KEY
```

## 支持级别（勿写错）

| 对象 | 级别 |
|------|------|
| Token 中心 | **官方明确**（3.0 预装 + OpenAI 兼容） |
| 经 Token 调用的 qwen/deepseek | 网关背后的模型后端，非 openKylin 自研记忆 |
| 本仓库 http 模板 | 接入准备；**非**「VM 实测通过」 |

更多生态分级见 `research/openkylin-agent-ecosystem/REPORT.md` 与 `docs/ecosystem-agent-export.md`。
