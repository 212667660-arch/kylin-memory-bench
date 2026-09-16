# openKylin 验证失败排查说明（2026-09-02）

## 已确认的失败阶段

1. Windows 主机不是 openKylin，`scripts/env_probe.py --require-openkylin --json` 返回退出码 2，`checks.openkylin.ok=false`。
2. Hyper-V 功能查询返回“请求的操作需要提升”；CPU WMI 标志 `VirtualizationFirmwareEnabled=false`、`SecondLevelAddressTranslationExtensions=false`、`VMMonitorModeExtensions=false`。
3. 未发现 VirtualBox、VMware Workstation/`vmrun`、libvirt；只有 QEMU 11.1.0。QEMU 的 WHPX 空机可启动但提示主机不支持 CPUID 特性，尚未证明可完成桌面安装。
4. 当前仅有已停止的 `docker-desktop` WSL 发行版，Docker daemon 不可用；即使可用也只能作为依赖预检，不能替代完整 openKylin 实机/虚拟机。

## 已尝试命令

```text
Get-CimInstance Win32_Processor | Select Name,VirtualizationFirmwareEnabled,SecondLevelAddressTranslationExtensions,VMMonitorModeExtensions
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
qemu-system-x86_64.exe -accel whpx -machine q35 -m 512 -smp 1 -nodefaults -nographic -monitor stdio -serial none -S -no-reboot
wsl --status; wsl -l -v
docker version
```

## 最小外部条件

- BIOS/UEFI 开启 Intel VT-x/SLAT，或提供已安装且可交互登录的 openKylin x86_64 虚拟机/远程主机；
- 可访问官方镜像并拥有至少 40 GiB 专用虚拟磁盘空间；
- 真实运行双 Agent 所需的 `GROK_API_KEY`、`DEEPSEEK_API_KEY` 及赛事允许的网络/脱敏策略；
- 若使用 Hyper-V，需要管理员权限创建和启动虚拟机。

在满足条件后，运行 `scripts/openkylin_qemu_prepare.ps1`（若使用 QEMU）或把项目复制到 openKylin，再执行 `scripts/openkylin_full_validation.sh`。任何“完成”结论必须以环境内 `/etc/os-release` 和探针 JSON 为依据。
