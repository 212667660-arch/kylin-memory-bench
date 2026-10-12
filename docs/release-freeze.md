# 忆衡发布冻结清单

当前版本的工程复核见 `docs/completion-audit-20261013.md`。本文件中的 release7、旧 SHA-256 和旧自评分为历史冻结记录；2026-10-13 已发现并修复 pip 安装、Debian 离线验收和扩展案例期望序列问题，应使用本轮 release9 及其新 manifest。MIT 已生效，桌面视频仍待完成。

历史状态：PDF a-d 已有 openKylin 验证记录；当前须同时参考上述工程复核。桌面视频（e）待完成，项目级 MIT 许可证已生效。

说明：下文较早 release7 路径为历史归档；最新 openKylin 3.0 VM 复核记录在本轮工作区外的 `/tmp/kmb-verification`，结论摘要见 `docs/requirements-traceability.md`。

## 固定版本

- 项目版本：`kylin-memory-bench 0.2.0`
- Python 要求：`>=3.9`
- 运行依赖：`PyYAML>=6.0`
- 当前 openKylin 验证环境：3.0 (huanghe)、x86_64、Python 3.12.2、PyYAML 6.0.3
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
| `scripts/build_deb.sh` | `9cfadf4536a40f43ca2b907de2464e4fb8ae8b60f741873e77e9dfe3cad43120` |
| `scripts/official_score.py` | `9fca0ea169a8142208f0335c5bb4fb1a4606843224c1b2ca86f45f54d2978f96` |

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
- `.deb` 最新生命周期（2026-10-04，openKylin 3.0 VM）：`runs/deb-lifecycle-3.0vm-20261004/`——preflight/install(release6)/verify_before/upgrade(release7)/verify_after/uninstall/residual_check 七步全部退出码 0，升级路径 release6→release7 经 dpkg 确认，卸载后 `/usr/bin/kmb` 与 `/usr/share/kylin-memory-bench` 残留检查通过；此前第六批 `runs/deb-lifecycle-authorized-20260908-rerun6/` 保留
- 发布候选包：`dist/release-20260909-release7/kylin-memory-bench_0.2.0+release7_all.deb`；最终 SHA-256 以 `runs/openkylin-validation-20260909/release-manifest-release7/release-manifest-release7.json` 为准；构建/内容审计记录见 `runs/openkylin-validation-20260909/release7-build/` 和 `runs/openkylin-validation-20260909/release7-audit/`
- 最终非视频检查：`runs/final-nonvideo-20260909-b143/`（逐项退出码见 `batch-summary.json`）
- **最新真实双 Agent 批次（2026-09-24）**：VM `/home/Cisyam/kmb-agent-validation-20260923/runs/quick-compare-isolated-20260924/`；KylinBot `63.89`、OpenClaw `13.89`，六案例双侧 `score_valid=true`；`verify_run.py --strict` 分别校验 51/34 条证据并退出 0。该批次使用独立 HOME/空白记忆库，属于系统级外部记忆/动作控制器观测，`native_memory_events=0`。
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
- 2026-09-23 之前的 402 `billing_error` 结果属于旧 Token 快照；2026-09-24 新 Token 的 `/v1/models` 返回 200，最新双 Agent 批次未出现 billing/runtime 错误。

## 当前状态边界

- `0.2.0+release7` 发布候选已包含当前创新代码、系统场景执行器、套件、统计修复和文档并通过 VM 包内容审计；`.deb` 对外再分发限制已随项目级 LICENSE（MIT，2026-10-05）生效解除；第三方边界见 THIRD_PARTY_NOTICES.md。
- Grok/DeepSeek 真实轨道均未导出原生记忆状态；所有 wrapper/no-memory 结果均为系统级行为或基线描述。
- **R0**：包装/HTTP/三件套历史 runs **保留**为 C 轨对照证据；赛题「不同智能体长期记忆」主结论路径为 A+B 且须通过证据门禁（见 `docs/native-memory-compare.md`）。**不得**将 wrapper 互比写成主结论或原生记忆对比。
- 英文/扩展/创新套件已有真实运行；创新 memory-enabled 与 no-memory 两 Agent 均已归档各 5 批统计，Grok 两条轨道均保留真实失败样本。
- 桌面视频严格暂缓，只有在许可证、文档和最终验收确认后录制。
- 系统级 OS 重启和跨用户切换仍需具备恢复通道的 VM 控制器/认证 root 与专用用户。

## 最新非视频冻结附录（2026-09-25）

以下内容覆盖本文件中较早的“当前”措辞；历史运行记录保持不变。

- 官方离线验收：`runs/official-final-20260925-r2/`，退出码 `0`。
- 官方评分：`runs/official-final-20261004/scorecard/`，当前得分 **100/100**（2026-10-04；90/100 历史基线保留于 `runs/official-final-20260925-r2/scorecard-final/`）。
- 评分排除：`PDF-12` 桌面视频（仍未处理）。根目录 `LICENSE` 已于 2026-10-05 生效（MIT，仍不计入评分权重）。
- 评分明细文档：`docs/official-scorecard.md`；机器可读来源为 `scorecard.json`。
- 评分回归：`tests.test_official_score`、`tests.test_official_repeat` 共 6 项通过；完整测试仍以本轮全量命令输出为准。
- 真实 VM 重复批次（当前）：`runs/official-installed-20261004/`（2026-10-04，openKylin 3.0 VM，--repeats 2）：两批双 Agent 全部 `score_valid=true`（KylinBot 63.89/61.11，OpenClaw 22.22/22.22），环境指纹与 10-01 一致；PDF-16 据此计满分。历史批次（09-24 的 1/3 与 0/3、09-27 的 402、10-01 的 429/402 系列）全部保留并记录于 `docs/official-scorecard.md`。
- 真实轨道的 `native_memory_events=0`，发布材料只能使用“系统级 Agent/外部记忆控制器观测”表述。
- `.deb` 构建脚本现已把运行时脚本依赖和 `scripts/official_score.py` 安装到包内 `usr/share/kylin-memory-bench/scripts/`；最终包已在 openKylin VM 完成完整生命周期矩阵（见上），包内 smoke（reference/flawed 各 6 案例 34 事件）strict valid。
- 2026-09-25 Windows 安装模式复核保存在 `runs/official-installed-final-20260925/`：KylinBot/OpenClaw 均未发现本机 Agent 存储，三批均按 `blocked` 保留，未生成伪造分数；该环境的机器评分为 72/100，不替换离线基线。（其时 SSH 不可达；09-27 起恢复，10-04 已完成真实批次。）

正式冻结前的最短复核命令：

```powershell
.\\.venv-kmb-system\\Scripts\\python.exe -m kmb.cli official-acceptance --out runs/official-final-20260925-r2 --mode offline
.\\.venv-kmb-system\\Scripts\\python.exe scripts/official_score.py --acceptance runs/official-final-20260925-r2 --out runs/official-final-20260925-r2/scorecard-final
```
