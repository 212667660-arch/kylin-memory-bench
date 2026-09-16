# 忆衡最终复现清单（非视频）

状态：2026-09-09 非视频收尾版本。项目级 `LICENSE`、云 API 展示授权和桌面视频仍需负责人确认/录制。

## 固定输入

- 目标系统：openKylin 2.0 SP2 (nile)，x86_64；本清单的系统证据只覆盖已记录 VM/KARE 版本。
- Python：3.12.2；虚拟环境：项目目录 `.kmb-venv`；PyYAML：6.0.1。
- 真实后端：Grok `grok-4.6` (`https://api.wapq.cn/v1`)；DeepSeek `deepseek-v4-flash` (`https://api.deepseek.com`)。
- 凭据：从 `~/.config/kmb/credentials.env` 以权限 `600` 加载，禁止写入 YAML、日志、报告或本清单。
- 统一参数：seed `42`、retries `1`、每案例 timeout `180` 秒；评分只读取 `EvidenceEvent`。
- 项目版本：`kylin-memory-bench 0.2.0`；发布候选包：`0.2.0+release7`（已包含生命周期/变形/行动证据创新层、系统场景执行器、no-memory 统计修复和最终发布文档）。

## 命令顺序

```bash
cd /home/Cisyam/kmb-openkylin-validation-20260906
test "$(stat -c '%a' ~/.config/kmb/credentials.env)" = 600
. .kmb-venv/bin/activate
python scripts/env_probe.py --require-openkylin --json
python -m kmb.cli validate --strict --suite suites/core-zh.yaml
python -m kmb.cli validate --strict --suite suites/adversarial/core.yaml
python -m kmb.cli validate --strict --suite suites/core-en.yaml
python -m kmb.cli validate --strict --suite suites/adversarial/core-en.yaml
python -m kmb.cli validate --strict --suite suites/lifecycle/innovation.yaml
python -m kmb.cli compare \
  --agents configs/agent-grok-memory.yaml configs/agent-deepseek-memory.yaml \
  --suite suites/core-zh.yaml \
  --out runs/final-wrapper-<date> \
  --run-id final-wrapper-<date> --seed 42 --retries 1 --timeout 180
python scripts/verify_run.py runs/final-wrapper-<date>/grok-memory-controller --strict
python scripts/verify_run.py runs/final-wrapper-<date>/deepseek-memory-controller --strict
python scripts/verify_run.py runs/openkylin-validation-20260908/innovation-grok-wrapper --strict
python scripts/verify_run.py runs/openkylin-validation-20260908/innovation-deepseek-wrapper --strict
```

真实对抗/英文套件运行使用相同参数和配置，分别保存独立运行目录；失败批次保留原始日志，不得覆盖成功或失败证据。创新套件 memory-enabled 多批统计见 `runs/openkylin-validation-20260908/innovation-stability/`，no-memory 五批对照见 `runs/openkylin-validation-20260909/innovation-no-memory/`，均使用 `scripts/aggregate_repeats.py` 和 `scripts/aggregate_stability.py` 生成 JSON/Markdown/HTML/SVG。统计描述“模型后端 + 外部包装层”的系统级行为，不证明模型原生记忆。

系统级边界检查可运行：

```bash
python scripts/system_scenarios.py \
  --out runs/openkylin-validation-20260908/system-scenarios-20260908 \
  --run-id system-scenarios-20260908
```

该命令只触碰项目专用目录和用户 network namespace；当前 VM 实际通过了进程重启、namespace 离线和专用文件权限场景，OS 重启与跨用户场景因能力不足记录为 `not_executed`。详见 `docs/innovation-stability-report.md`。

## 结果验收

每个真实 Agent 目录必须包含 `result.json`、`evidence.jsonl`、`result.md`、`result.html`、`radar.svg`，并通过 `scripts/verify_run.py --strict`。对比目录必须包含 `comparison.json`、`comparison.md`、`comparison.html` 和两份雷达图。

事件解释必须分层：`source=model` 是 API 请求/响应或未证实模型自述，`source=wrapper` 是外部控制器实际执行，`native_memory_events=0` 时不得写成模型原生长期记忆。`reference/flawed` 仅用于离线机制 smoke。

## 固定证据

- 中文核心/对抗：`runs/openkylin-validation-20260906/final-compare/`、`runs/openkylin-validation-20260908/adversarial-expanded-compare/`
- 英文核心/对抗：`runs/openkylin-validation-20260908/core-en-compare-rerun2/`、`adversarial-en-compare-rerun2/`
- 稳定性：`runs/openkylin-validation-20260908/stability/`
- 创新层 Grok：`runs/openkylin-validation-20260908/innovation-grok-wrapper/`
- 创新层 DeepSeek：`runs/openkylin-validation-20260908/innovation-deepseek-wrapper/`
- 创新层双 Agent 对比：`runs/openkylin-validation-20260908/innovation-dual-compare/`
- `.deb` 第六批：`runs/deb-lifecycle-authorized-20260908-rerun6/`
- 发布候选：`dist/release-20260909-release7/kylin-memory-bench_0.2.0+release7_all.deb`
- 最终非视频检查：`runs/final-nonvideo-20260909-b179-release6/`

发布候选 SHA-256：以 `runs/openkylin-validation-20260909/release-manifest-release7/release-manifest-release7.json` 中的 `candidate_package.sha256` 为准。

## 不在本清单内

本清单不包含 API Key、密码、模型权重或私有数据；不替代项目级许可证、云服务条款确认、跨版本兼容性测试或最后的 3-5 分钟桌面视频录制。
