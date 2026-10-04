# 创新套件稳定性与系统级场景补充报告

**批次**：2026-09-09，openKylin 2.0 SP2 (nile) VM，x86_64，Python 3.12.2  
**套件**：`suites/lifecycle/innovation.yaml`，SHA-256 `c3543730c40fde5995cdf87012695754f66dff82698feb50c9c1d6e14bae1b0a`  
**统一参数**：seed `42`、retries `1`、每案例 timeout `180s`；模型调用从 VM `~/.config/kmb/credentials.env` 加载，凭据值未写入结果。

## 观测边界

下表描述的是每个模型后端与相同外部忆衡记忆/行动包装层组合后的系统级行为。两条真实轨道均 `native_memory_events=0`，因此不能据此证明模型原生长期记忆能力。`source=wrapper` 表示包装层实际操作，`source=model` 表示 API 请求/响应或未证实模型自述。

## 多批统计

| Agent | 批次 | 执行成功率 | 行为案例通过率 | Overall 均值 | 样本标准差 | 最小 | 最大 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Grok `grok-4.6` | 5 | 80% | 88% | 92.446 | 11.9272 | 71.11 | 97.78 |
| DeepSeek `deepseek-v4-flash` | 5 | 100% | 93.33% | 97.78 | 0 | 97.78 | 97.78 |

Grok 第 2 批保留了 8 个真实 `runtime_error` 事件，未从分母剔除；因此 Grok 只有 4 个执行无错误的批次，不能宣称“五批全部成功”或绝对稳定。DeepSeek 五批均严格校验通过，但 API 响应延迟仍有波动。跨 Agent 均值差异 `Grok - DeepSeek = -5.334`，仅作描述性比较，不作因果结论。

### 能力和证据指标

| Agent | 变形组通过率 | 生命周期状态转换正确率 | 实际动作成功率 | 证据链完整批次率 | 安全相关失败类型 |
|---|---:|---:|---:|---:|---|
| Grok | 96% (24/25) | 100% (10/10) | 100% (13/13) | 100% (5/5) | `erroneous_reuse=2` |
| DeepSeek | 100% (25/25) | 100% (10/10) | 100% (15/15) | 100% (5/5) | 无 |

六维均值见机器可读汇总；Grok：`retention=80`、`memory_recall=80`、`dynamic_update=66.67`、`similar_distinction=100`、`boundary=100`、`task_reuse=86.666`；DeepSeek：`100/100/66.67/100/100/100`。

### No-memory 对照

在同一套件、seed、超时和重试参数下，外部忆衡控制器关闭后分别完成 Grok 与 DeepSeek 各 5 个独立批次。该轨道仍是真实模型 API 加关闭的外部包装层，不是模型原生记忆状态观测。

| Agent | 批次 | 执行成功率 | 行为案例通过率 | Overall 均值 | 样本标准差 | 最小 | 最大 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Grok `grok-4.6` | 5 | 60% | 18.67% | 22.444 | 3.3691 | 16.67 | 25.56 |
| DeepSeek `deepseek-v4-flash` | 5 | 100% | 20% | 22.664 | 1.4892 | 20.0 | 23.33 |

Grok 的 repeat-01 为真实连接拒绝、repeat-03 含真实超时；失败批次保留在统计分母中。no-memory 双 Agent 汇总见 `runs/openkylin-validation-20260909/innovation-no-memory/dual-agent-innovation-no-memory.json`、`.md`、`.html` 和 `stability-radar.svg`，均值差异 `Grok - DeepSeek = -0.22` 仅作描述性比较。

## 系统级场景

执行器：`scripts/system_scenarios.py`，只使用项目 `runs/` 专用目录、合成事实和用户网络 namespace。

| 场景 | 状态 | 证据 |
|---|---|---|
| Agent 进程重启 | `pass` | 两个不同 PID `188410/188411` 读取同一持久事实并完成沙箱动作 |
| 测试进程网络 namespace 离线 | `pass` | `unshare --user --mount --net --fork` 外连探针退出 `0`，输出 `network_blocked=true`；未伪造 API 响应 |
| 专用文件权限变化 | `pass` | 仅测试文件 chmod `000` 后拒绝读取，恢复 `0600` 后成功 |
| 操作系统重启 | `not_executed` | 无认证 root 和重启后外部控制通道 |
| 用户切换/跨用户 | `not_executed` | 仅一个活动用户且无授权创建/切换专用用户通道 |

场景证据目录：`runs/openkylin-validation-20260909/system-scenarios-20260909-v2/`，包含 `system-summary.json`、`system-summary.md`、`evidence.jsonl`、`artifacts/` 和 CLI 退出码。该执行器结果不包含模型请求，不能证明模型原生记忆。

## 机器可读产物

- Grok memory-enabled：`runs/openkylin-validation-20260908/innovation-stability/grok-memory/summary.json`、`.md`
- DeepSeek memory-enabled：`runs/openkylin-validation-20260908/innovation-stability/deepseek-memory/summary.json`、`.md`
- memory-enabled 双 Agent：`runs/openkylin-validation-20260908/innovation-stability/dual-agent-innovation-stability.json`、`.md`、`.html`、`stability-radar.svg`
- no-memory 双 Agent：`runs/openkylin-validation-20260909/innovation-no-memory/dual-agent-innovation-no-memory.json`、`.md`、`.html`、`stability-radar.svg`
- memory-enabled 与 no-memory 的 20 个 repeat 目录均包含 `result.json`、`evidence.jsonl`、`result.md`、`result.html`、`radar.svg`、CLI/verify 日志和退出码；strict verify 退出码均为 `0`。

## 限制

本批次没有执行 OS 重启和真实跨用户切换；这些场景需要具备恢复通道的 VM 控制器/已认证 root 与专用测试用户。innovation no-memory 对照已完成两 Agent 各 5 批，但 Grok 含连接拒绝/超时失败，不能宣称五批全部成功或绝对稳定。所有结果均未将包装层行为称作模型原生长期记忆；当前发布候选为 release7，manifest 以 `runs/openkylin-validation-20260909/release-manifest-release7/release-manifest-release7.json` 为准。


## 2026-10-04 增补：openKylin 生态 Agent 真实重复批次稳定性

openKylin 3.0 VM 上的生态双 Agent（KylinBot/OpenClaw，均为系统级外部记忆/动作控制器观测，`native_memory_events=0`）完成 `--repeats 2` 重复批次（独立 HOME、清空记忆表、固定 seed 42 与套件 `suites/quick.yaml`）：

- KylinBot：63.89 / 61.11（均值 62.50，标准差 1.97）——两批差异 2.78 分，波动小
- OpenClaw：22.22 / 22.22（标准差 0.00）——完全一致
- 两批双 Agent `score_valid=true`，strict verify 退出码 0；失败类型（omission/confusion/erroneous_reuse 等）与历史基线同源，无 error 级案例
- 环境指纹（技能树/配置/二进制 SHA-256，`runs/env-fingerprint-20261001.json`）与跑批日采集一致，排除环境漂移
- 证据：`runs/official-installed-20261004/`（VM 原始目录 `/home/Cisyam/kmb-official-review-20260924-r2/runs/official-installed-20261004/`）

边界：本数据描述"模型后端 + Agent 外部记忆/动作控制器"的系统级稳定性；不构成模型原生长期记忆证据。执行波动史（429/402 系列）见 `runs/official-installed-20261001{,-r2}/`。
