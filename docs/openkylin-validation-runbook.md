# openKylin 实机/虚拟机验证执行清单

当前目标和实机是 **openKylin 3.0（huanghe）**，原操作系统版本保持不动。本轮 2026-10-13 的实际证据见 [完成度审计](completion-audit-20261013.md) 和 [当前环境说明](current-environment.md)。

> 历史实际记录：2026-09-08 曾在 openKylin 2.0 SP2 x86_64 VM 完成源码安装、环境门禁、真实 Grok/DeepSeek 双 Agent 核心/对抗运行、证据/评分/报告和 `.deb` 第六批完整生命周期。下文对应旧环境的版本、命令和结果保留为历史；不能把一次 VM 记录外推到所有 openKylin 版本。

## 生命周期扩展执行边界

新增 `suites/lifecycle/innovation.yaml` 可在 VM 中按与核心套件相同的 Agent、seed、超时和重试参数运行。它会验证事实元数据、TTL、作用域隔离、敏感 token 拒绝、变形组和沙箱动作工件。报告应以 `evidence_schema_version=2` 的 JSONL、父事件关联、文件 SHA256 和退出码为依据；`source=wrapper` 仍只支持“模型后端 + 外部包装层”的系统级结论。

案例中的 `restart-boundary` 只重建包装层/控制器状态，并在事件中标记 `system_restart=false`。真实系统重启、用户切换、离线切换和系统权限变更必须通过 root/VM 控制器接口执行；没有该接口时应保留为“需受控 openKylin 环境执行”，不可用普通 CLI 结果替代。

## 系统级场景受控执行器

`scripts/system_scenarios.py` 只使用项目 `runs/` 下的专用目录和合成事实，实际可执行的边界为：评测器进程重启、用户网络 namespace 离线探针、专用测试文件权限拒绝/恢复。执行：

```bash
python3 scripts/system_scenarios.py \
  --out runs/openkylin-validation-20260909/system-scenarios-20260909-v2 \
  --run-id system-scenarios-20260909-v2
```

输出 `system-summary.json`、`system-summary.md`、`evidence.jsonl`、`artifacts/` 和实际退出码。事件中的 `agent_process_restart` 不是 OS 重启；离线探针只证明测试进程 namespace 阻断外连，不生成或伪造模型响应。若没有已认证 root/VM 控制器和至少两个专用用户，`system-reboot`、`user-switch` 只生成 `not_executed` 计划与恢复步骤，不得以普通 CLI 结果替代。

## 当前探测结论

截至 2026-09-02，宿主机历史预检结果：

- 系统：Windows 10，AMD64；Python 3.9.5；PyYAML 6.0.3。
- 工作区：E 盘剩余约 85.31 GB；项目虚拟环境为 `E:\上海开源软件应用创新大赛\.venv-kmb-system`。
- 可见能力：WSL 命令存在但仅有停止的 `docker-desktop`；Docker daemon 未运行；未发现 QEMU、VirtualBox、VMware、Podman；未发现 openKylin ISO/虚拟磁盘/容器介质。
- `scripts/env_probe.py --require-openkylin --json` 退出码 2，原因是当前没有 `/etc/os-release` 且系统不是 openKylin。
- 历史结论：Windows 结果仅作为本地预检，不能写成 openKylin 兼容性结论。后续实际 VM 验证见本文件表格和 `runs/openkylin-validation-20260906/final-event-report.md`。

## 实机/虚拟机记录

| 项目 | 实际值 |
|---|---|
| openKylin 版本 / 镜像哈希 | openKylin 2.0 SP2 (nile)；镜像哈希未记录 |
| 介质 | 虚拟机 |
| 架构 | x86_64 |
| Kernel | 6.6.0-25-generic #0ok2-KYLINOS |
| Python / pip | Python 3.12.2 / pip 26.2.1 |
| 网络/代理 | VM 内 ens160=192.168.182.129/24；未记录密钥 |
| 磁盘可用空间 | 约 20.62 GB |
| 图形界面 | CLI 已验证；桌面录屏未完成 |

## 必须执行的命令

```bash
uname -a
cat /etc/os-release
python3 --version
python3 -m pip --version
bash scripts/install_local.sh python3
export KMB_PYTHON="$PWD/.kmb-venv/bin/python"
"$KMB_PYTHON" scripts/env_probe.py --require-openkylin --json | tee runs/openkylin-validation/env-probe.json
# Set GROK_API_KEY and DEEPSEEK_API_KEY only in the process environment, never in YAML or logs.
KMB_PYTHON="$KMB_PYTHON" bash scripts/run_acceptance.sh \
  configs/agent-grok.yaml configs/agent-deepseek.yaml suites/core-zh.yaml \
  runs/openkylin-validation/real-compare
bash scripts/uninstall_local.sh
```

## 验收标准

- 探针 `status=ok` 且 `openkylin.ok=true`。
- 安装、validate、compare、verify、卸载均记录退出码为 0；失败时记录原始日志和客观原因。
- 双 Agent 使用同一套件、seed、超时、重试和评分版本；不存在 `reference/flawed` 冒充真实 Agent。
- 结果包含 `evidence.jsonl`、`result.json`、`comparison.json`、Markdown/HTML/SVG 报告。
- 报告中的包装层运行必须写为“模型后端 + 外部控制器的系统级行为”，不能写成模型原生记忆。
- 保存安装日志、完整 CLI 输出、环境 JSON 和结果文件哈希；卸载后确认虚拟环境/安装文件按方案清理。

在 openKylin KARE 环境中，`dpkg` 可能由 `/usr/bin/dpkg_wrapper` 转发到 shadow overlay，root 生命周期 shell 与 SSH 会话的 `/usr` 视图可能不同。生命周期脚本会优先检查 `/opt/kare-applications/shadow/upper`（包括其 `var/lib/dpkg/status` 和 payload），再检查普通系统路径；KARE 返回“成功”仍必须经过 CLI、升级、卸载和残留检查，不能单独作为完整生命周期通过证据。

## 当前阻塞

- 3-5 分钟 openKylin 桌面演示视频尚未录制，按项目安排在所有非视频收尾工作完成后执行。
- 项目级 LICENSE 和云 API 的赛事使用、额度、网络、数据脱敏政策仍需项目负责人确认。
- `.deb` 第六批已通过当前 VM/KARE 版本的系统级生命周期；跨镜像、跨版本和干净机器复核仍不应由该批次推断。

## 已归档的系统包生命周期

第六批实际命令和逐步退出码保存在 `runs/deb-lifecycle-authorized-20260908-rerun6/`；
`preflight/install/version/verify/build_upgrade/upgrade/verify_after_upgrade/uninstall/residual_check`
均为 `0`，清单校验为 `manifest_verify=ok`。以下命令仍用于后续目标镜像复核，不应与已完成批次混淆。

在具备 sudo/root 的 openKylin VM 终端执行以下命令，并将完整 stdout/stderr、退出码和
`dpkg-query` 结果保存到 `runs/openkylin-validation-20260906/deb-release/`：

```bash
bash scripts/install_deb.sh dist/kylin-memory-bench_0.2.0_all.deb
bash scripts/verify_deb.sh /tmp/kmb-deb-smoke
KMB_DEB_VERSION=0.2.0+test1 bash scripts/build_deb.sh dist
bash scripts/upgrade_deb.sh dist/kylin-memory-bench_0.2.0+test1_all.deb
bash scripts/uninstall_deb.sh
```

也可以使用带日志的生命周期记录脚本：

```bash
bash scripts/record_deb_lifecycle.sh \
  runs/openkylin-validation-20260906/deb-release/system-lifecycle \
  dist/kylin-memory-bench_0.2.0_all.deb \
  dist/kylin-memory-bench_0.2.0+test1_all.deb
```

录制桌面演示时，在 openKylin 桌面终端运行：

```bash
bash scripts/record_desktop_demo.sh runs/openkylin-validation-20260906/desktop-demo 300
```

该录屏脚本要求有效 `DISPLAY` 和 `ffmpeg`。若通过 SSH 执行且没有图形会话变量，脚本会以退出码 2 停止；这不是视频录制成功证据。
