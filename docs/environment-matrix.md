# 环境验证矩阵

当前实机为 **openKylin 3.0（huanghe）**，原系统版本保持不动；见 [当前环境说明](current-environment.md) 和 [2026-10-13 审计](completion-audit-20261013.md)。本文件下文保留 2026-09-02 Windows 预检及 2026-09-08 openKylin 2.0 SP2 历史记录，不能将它们当作当前系统状态。

## 历史本地预检记录（2026-09-02）

本轮实际预检主机为 Windows 10（AMD64），Python 3.9.5，PyYAML 6.0.3。CLI 导入和核心套件严格校验均通过；`/etc/os-release`、`dpkg-deb` 不可用，故本记录不构成 openKylin 验证。

| 项目 | 待填写值 |
|---|---|
| openKylin 版本 | 待确认；当前主机不是 openKylin |
| 架构 | 待确认（x86_64 / ARM64）；当前 Windows 为 AMD64 |
| 介质 | 待确认（实体机 / 虚拟机 / 官方镜像） |
| Kernel | 待实机记录；当前 Windows 结果不替代 |
| Python | 待实机记录；当前本地 3.9.5 |
| PyYAML | 待实机记录；当前本地 6.0.3 |
| 安装命令 | `python -m pip install .` 或离线安装方案 |
| CLI 验证 | `python -m kmb.cli compare ...` |
| 卸载验证 | 待实机记录 |

验证时应保存 `uname -a`、`cat /etc/os-release`、Python/pip 版本、安装日志、完整 CLI 输出和 `runs/` 目录校验值。

本地预检命令：

```bash
python3 scripts/env_probe.py --json
python3 scripts/env_probe.py --require-openkylin --json
```

第二条命令只有在实际 openKylin 主机上才应作为通过条件。当前 Windows 环境只能执行第一条，并且不能替代 openKylin 验证。

本轮实际结果：`python scripts/env_probe.py --json` 返回 `status: ok`；`python scripts/env_probe.py --require-openkylin --json` 返回退出码 2，原因是当前系统为 Windows 且没有 `/etc/os-release`。该失败是预期的环境门禁，不是 CLI 运行失败。

本轮进一步探测：工作区所在 E 盘剩余约 85.31 GB；WSL 仅发现已停止的 `docker-desktop` 发行版；Docker CLI 存在但 daemon 未运行；QEMU、VirtualBox、VMware、Podman 均未发现；Hyper-V PowerShell cmdlet 不可用。未发现 openKylin 实机、虚拟机、官方镜像或可运行容器，因此本轮不执行虚拟机安装，也不把 Windows 结果替代为 openKylin 结果。项目虚拟环境已使用 `E:\上海开源软件应用创新大赛\.venv-kmb-system`，PyYAML 6.0.3 位于该虚拟环境自己的 `site-packages`；pip 临时目录和缓存固定在 E 盘 `.tmp-pip`/`.pip-cache`。Windows 可复现安装脚本为 `scripts/install_local.ps1`，Linux/openKylin 脚本为 `scripts/install_local.sh`。正式验收脚本 `scripts/run_acceptance.sh` 会强制 `--require-openkylin`，并拒绝 `deterministic` 演示 Agent。

## 历史 VM 验证附录（2026-09-08）

| 项目 | 实际值 | 证据 |
|---|---|---|
| 系统 | openKylin 2.0 SP2 (nile) | `runs/openkylin-validation-20260906/environment/ssh-environment.stdout.log` |
| 架构 / 内核 | x86_64 / `6.6.0-25-generic #0ok2-KYLINOS` | 同上 |
| Python / pip / setuptools | 3.12.2 / 26.2.1 / 84.0.0 | `runs/openkylin-validation-20260906/environment/` |
| PyYAML | 6.0.1 | `runs/openkylin-validation-20260906/environment/probe-validate.stdout.log` |
| CLI 与套件门禁 | `env_probe --require-openkylin`、四套件 strict validate 均为 0 | `runs/openkylin-validation-20260906/environment/`、批次 112 |
| 系统包生命周期 | 第六批九步骤均为 0，含卸载/残留检查 | `runs/deb-lifecycle-authorized-20260908-rerun6/` |
| 真实 Agent | Grok 4.6、DeepSeek v4 flash；原生记忆事件 0 | `runs/openkylin-validation-20260906/final-event-report.md`、`runs/openkylin-validation-20260908/` |

该附录只覆盖已记录的单个 VM/KARE 版本；不能外推到其他镜像或版本。桌面视频仍未录制（脚本/工具就绪）；项目级许可证为 MIT（2026-10-05 已生效）。
