# 忆衡发布冻结清单

状态：**本机开发与 P1 提分项已完成（扩展套件、openKylin 进程适配器 Agent、无凭据双 Agent 对比 demo、文档口径统一）；openKylin 实机迁移验收与桌面视频、项目级 LICENSE 仍后置。**

说明：下文所列 openKylin VM / `.deb` 证据为历史归档，**不作为本阶段「实机已验证」宣称**；迁移后需在目标机重跑验收命令。

## 固定版本

- 项目版本：`kylin-memory-bench 0.2.0`
- Python 要求：`>=3.9`
- 运行依赖：`PyYAML>=6.0`
- 当前 openKylin 验证环境：2.0 SP2、x86_64、Python 3.12.2、PyYAML 6.0.1
- 默认真实后端：Grok `grok-4.6`、DeepSeek `deepseek-v4-flash`
- 统一运行参数：seed `42`、retries `1`、timeout `180s`

## 套件和代码指纹

以下 SHA-256 以本次 release7 manifest 为准；任何变更后必须重新生成：

| 内容 | SHA-256 |
|---|---|
| `suites/core-zh.yaml` | `b2f698e997d73ad17c89c8372c4a9dd780655af990b4fbd5ba0e48df4101f7f2` |
| `suites/core-zh-expanded.yaml` | （本机新增，冻结时用 sha256sum 写入） |
| `suites/adversarial/extended.yaml` | （本机新增，冻结时用 sha256sum 写入） |
| `scripts/openkylin_ecosystem_agent.py` | （本机新增 process 适配器） |
| `suites/core-en.yaml` | `0011a45df20b25a6f9875cd5068b19732a1a2009f988191d568291561604bf5a` |
| `suites/adversarial/core.yaml` | `1bcdcfe6c66396295ff61b8e2875e81e0ab20b109b2f9456b01f77c2e20e9304` |
| `suites/adversarial/core-en.yaml` | `0441bb6b55f04fb6de08542a5ff2b100803dcfb0a12c31733a9f54401cc1e166` |
| `kmb/agents.py` | `3f3be079bff4bafdad4f6fbfc5ce3084a5bc0f2d4aaad29c120a3c84b6de4e76` |
| `kmb/models.py` | `c8ba23838ef55e0d61ba7ee73cc726aecc975cd2b286c2864583942ea3e2283f` |
| `kmb/runner.py` | `514df2c2f4f4ce6ba2319a35d22ca46156689737e1717c59aa1c9d444fab2c97` |
| `kmb/scoring.py` | `0a2c0ba9e192476a6c0b2bc3126a48fe0050ab9db2105ab440e0d0c626a6b224` |
| `kmb/report.py` | `b08a1aa84d4563d91ab2450d436cd566a20141907df4f8568ff8f5f792d63bc4` |
| `suites/lifecycle/innovation.yaml` | `c3543730c40fde5995cdf87012695754f66dff82698feb50c9c1d6e14bae1b0a` |
| `scripts/aggregate_stability.py` | `cc4ac8519c7160843d78004f561089f8bbece98503c3f0c2d26433b584dca05d` |
| `scripts/aggregate_repeats.py` | `2be22990b4062125e0f39d018682248406a4c05be44f089086f2a8de43f1b364` |
| `scripts/system_scenarios.py` | `956dfc758327ba71f606e01634c7a65b5aade13cb0bc6c6fd06c6e84f22132ab` |
| `scripts/build_deb.sh` | `d9c5d99525525662bbd6a2838f507c0b6e0c401f6e9b3ee60aebaee49babf408` |

> 代码指纹用于人工识别；正式发布前用 `Get-FileHash` 或 `sha256sum` 重新核对完整值。若文件变更，本清单必须同步更新。

## 权威真实运行证据

- 中文核心/对抗：`runs/openkylin-validation-20260906/final-compare/`、`runs/openkylin-validation-20260908/adversarial-expanded-compare/`
- 英文核心：`runs/openkylin-validation-20260908/core-en-compare-rerun2/`
- 英文对抗：`runs/openkylin-validation-20260908/adversarial-en-compare-rerun2/`
- Grok core no-memory 5 批：`runs/openkylin-validation-20260906/grok-no-memory-repeats/`
- DeepSeek core no-memory 5 批：`runs/openkylin-validation-20260908/deepseek-no-memory-repeats/`
- Grok innovation no-memory 5 批：`runs/openkylin-validation-20260909/innovation-no-memory/grok-no-memory/`
- DeepSeek innovation no-memory 5 批：`runs/openkylin-validation-20260909/innovation-no-memory/deepseek-no-memory/`
- 双 Agent 稳定性：`runs/openkylin-validation-20260908/stability/`
- 创新套件多批稳定性：`runs/openkylin-validation-20260908/innovation-stability/`；补充报告：`docs/innovation-stability-report.md`
- 系统级场景：`runs/openkylin-validation-20260908/system-scenarios-20260908/`
- 创新层 Grok：`runs/openkylin-validation-20260908/innovation-grok-wrapper/`
- 创新层 DeepSeek：`runs/openkylin-validation-20260908/innovation-deepseek-wrapper/`
- 创新层双 Agent 对比：`runs/openkylin-validation-20260908/innovation-dual-compare/`
- `.deb` 第六批：`runs/deb-lifecycle-authorized-20260908-rerun6/`
- 发布候选包：`dist/release-20260909-release7/kylin-memory-bench_0.2.0+release7_all.deb`；最终 SHA-256 以 `runs/openkylin-validation-20260909/release-manifest-release7/release-manifest-release7.json` 为准；构建/内容审计记录见 `runs/openkylin-validation-20260909/release7-build/` 和 `runs/openkylin-validation-20260909/release7-audit/`
- 最终非视频检查：`runs/final-nonvideo-20260909-b143/`（逐项退出码见 `batch-summary.json`）
- 最终复现清单：`docs/final-reproduction-checklist.md`
- 机器可读发布 manifest：`runs/openkylin-validation-20260909/release-manifest-release7/release-manifest-release7.json`

每个真实 Agent 结果必须同时检查 `result.json`、`evidence.jsonl` 和 `verify_run.py --strict` 输出。`source=wrapper` 只证明外部控制器执行；当前真实轨道 `native_memory_events=0`，不得称为模型原生长期记忆。

## 最终非视频命令

评审无凭据闭环（新增，不改动既有指纹文件）：

```bash
bash scripts/run_offline_demo.sh runs/offline-demo
# 或逐步：validate suites/core-zh-expanded.yaml + reference/flawed compare
# 说明：docs/judge-reproduction-card.md
```

既有验收命令：

```bash
python -m unittest discover -s tests -v
python -m compileall -q kmb scripts tests
python -m kmb.cli validate --strict --suite suites/core-zh.yaml
python -m kmb.cli validate --strict --suite suites/adversarial/core.yaml
python -m kmb.cli validate --strict --suite suites/core-en.yaml
python -m kmb.cli validate --strict --suite suites/adversarial/core-en.yaml
python -m kmb.cli validate --strict --suite suites/lifecycle/innovation.yaml
python scripts/verify_run.py runs/openkylin-validation-20260908/innovation-grok-wrapper --strict
python scripts/verify_run.py runs/openkylin-validation-20260908/innovation-deepseek-wrapper --strict
python scripts/aggregate_stability.py \
  --grok-summary runs/openkylin-validation-20260906/grok-no-memory-repeats/summary.json \
  --deepseek-summary runs/openkylin-validation-20260908/deepseek-no-memory-repeats/summary.json \
  --out runs/openkylin-validation-20260908/stability/dual-agent-stability.json
```

release7 已在目标 VM 执行 `dpkg-deb --contents`、禁止内容、核心/创新套件和包内 smoke 审计；审计日志见 `runs/openkylin-validation-20260909/release7-audit/`。结果目录敏感令牌扫描和最终非视频复核见 `runs/final-nonvideo-20260909-b179-release6/`。

## 未完成与暂缓

- 根目录生效 `LICENSE`：待项目负责人/法务确认；`LICENSE-MIT-CANDIDATE.txt` 不授予权利。
- 3-5 分钟 openKylin 桌面双 Agent 视频：按项目安排最后录制，当前没有媒体文件。
- release7 manifest 已生成并纳入 `scripts/system_scenarios.py`、统计脚本、文档和测试的当前 SHA-256；旧 release2-release6 包/manifest 仅保留为历史记录。
- innovation memory-enabled 统计已完成两 Agent 各 5 个目录，但 Grok 含 1 个真实 runtime-error 批次（执行成功率 80%），不能写成 5/5 成功；innovation no-memory 对照已完成两 Agent 各 5 批，Grok 执行成功率 60%、DeepSeek 100%，失败样本均保留。no-memory 双 Agent 汇总见 `runs/openkylin-validation-20260909/innovation-no-memory/dual-agent-innovation-no-memory.json`。
- 历史运行报告中的旧状态文字：历史文件保留不可覆盖；当前结论以本清单和上下文批次 108-112 为准。

## 当前状态边界

- `0.2.0+release7` 发布候选已包含当前创新代码、系统场景执行器、套件、统计修复和文档并通过 VM 包内容审计；`.deb` 对外再分发仍受项目级许可证未确认限制。
- Grok/DeepSeek 真实轨道均未导出原生记忆状态；所有 wrapper/no-memory 结果均为系统级行为或基线描述。
- 英文/扩展/创新套件已有真实运行；创新 memory-enabled 与 no-memory 两 Agent 均已归档各 5 批统计，Grok 两条轨道均保留真实失败样本。
- 桌面视频严格暂缓，只有在许可证、文档和最终验收确认后录制。
- 系统级 OS 重启和跨用户切换仍需具备恢复通道的 VM 控制器/认证 root 与专用用户。
