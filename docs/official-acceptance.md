# 官方验收入口

KylinMemoryBench 提供一个无云凭据的单命令验收。评委在项目根目录运行：

```bash
python3 -m kmb.cli official-acceptance --out runs/official-acceptance
```

Windows PowerShell 可用当前 Python 环境替换 `python3`：

```powershell
python -m kmb.cli official-acceptance --out runs/official-acceptance
```

命令执行中文核心、扩展、对抗和错误行为对照，逐份运行 `verify_run.py --strict`，生成对比报告、雷达图、命令记录、文件 SHA-256 清单和验收摘要。完成后打开：

```text
runs/official-acceptance/acceptance-summary.html
```

## 模式

- `offline`（默认）：不需要网络、API Key、VM 或额外 Agent 下载；使用 deterministic reference、flawed 对照和 process 协议 stand-in 验证工具、评分和证据链。它不是官方真实 Agent 能力分数。
- `installed`：在 openKylin 上发现当前用户已安装的 Agent，只对两个通过只读预检的 Agent 执行真实快速对比；不会安装 Agent、读取密钥值或把密钥写入结果。若不足两个可运行 Agent，摘要状态为 `blocked`，并说明阻断原因。

真实 Agent 模式：

```bash
python3 -m kmb.cli official-acceptance \
  --mode installed \
  --agent-a kylinbot \
  --agent-b openclaw \
  --out runs/official-real-compare
```

入口不接受网页提交密钥、不要求编辑 YAML。运行器固定使用快速六类套件和项目默认 seed/retry/timeout。自定义运行参数仍可通过高级 CLI 使用，但不属于官方最短路径。

## 结果与退出码

| 产物 | 内容 |
|---|---|
| `acceptance-summary.html` | 人工快速查看状态和各项检查 |
| `acceptance-summary.json` / `.md` | 机器可读及文本摘要 |
| `commands.json` | 实际执行命令、退出码和输出尾部 |
| `artifacts.json` | 产物路径、字节数和 SHA-256 |
| `<suite>/comparison.html` | 双侧详细结果、六维分数、失败和证据引用 |
| `<suite>/<agent>/result.json` 与 `evidence.jsonl` | 单侧评分与原始结构化证据 |

| 退出码 | 含义 |
|---:|---|
| `0` | 验收链路通过，所有纳入检查的比较和 strict verify 均成功 |
| `2` | 环境、Agent 可用性或凭据条件阻断；摘要保留原因 |
| `3` | 评测结果无效或秘密扫描发现泄漏风险 |
| `4` | 参数或工具自身错误 |

所有 Agent 分数必须结合观测边界解释。`simulated` 仅验证工具链；`process`/`wrapper` 证明系统级行为；`native_memory_events=0` 时不作模型原生记忆结论。视频（PDF-12）和项目级许可证不由该命令判定。
