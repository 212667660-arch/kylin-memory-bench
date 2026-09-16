# openKylin 环境建设与验证记录（2026-09-02）

## 状态

真实 openKylin 实机/虚拟机验证未完成。本记录只包含本机探针、官方介质获取尝试、QEMU 准备结果和可复现脚本；Windows、WSL、Docker 或普通容器结果不作为 openKylin 验证结论。

## 主机与能力

- 主机探针：`runs/openkylin-validation-20260902/host-probe.json`
- 主机：Windows 11 Home China，AMD64，Intel Core i7-14650HX，24 逻辑处理器，约 31.73 GiB RAM。
- 磁盘：E 盘约 85.30 GiB 可用；专用工作目录位于 `runs/openkylin-validation-20260902`。
- 网络：WLAN 可用，官方站点和南京大学镜像可访问。
- 虚拟化：QEMU 11.1.0 已安装，`tcg` 与 `whpx` 后端可启动空机；固件虚拟化标志探针为 false，Hyper-V 状态查询需要提升权限。
- WSL：只发现已停止的 `docker-desktop`，无可用于验证的 openKylin 发行版；Docker daemon 未运行。

## 官方介质

- 官方入口：`https://www.openkylin.top/downloads/download-smp.php?id=116`
- 实际重定向/下载源：`https://mirror.nju.edu.cn/openkylin-cdimage/2.0-SP2/openKylin-Desktop-V2.0-SP2-20260813-x86_64.iso`
- 版本/架构：openKylin 2.0 SP2（2026-08-13），x86_64。
- Content-Length：8,930,932,736 字节（约 8.31 GiB）。
- 文件元数据及 SHA256/MD5：下载完成后写入同目录的 `.metadata.json`；官方 MD5 页面为 `https://www.openkylin.top/md5.html`。
- 实际 SHA256：`d146f8ac6c76fbfaa3ae6554010dcaed868ba4323c8c6eb83c9ff3a3984e6bf7`。
- 实际 MD5：`04ca4c0ef61694e4afe67ac40e6978ec`，与官方 x86 通用值一致；官方页面未发布 detached GPG 签名。

## QEMU 隔离目录

`openkylin_qemu_prepare.ps1` 只创建专用 qcow2 文件和启动脚本，不接触物理磁盘、分区或引导配置。启动脚本默认使用 `-accel whpx`、4 GiB RAM、4 vCPU、用户态 NAT 和无 GUI 串口日志；若 WHPX 报错，可人工改为 `-accel tcg`，但性能与可交互性不足以替代正式验收。

已执行 `openkylin_qemu_boot.ps1 -Accel whpx -Seconds 30`：QEMU 进程运行满 30 秒后按约定以退出码 124 停止，stderr 记录 WHPX CPUID/中断能力警告，串口为空（桌面 ISO 未配置串口控制台）。未获得 openKylin 登录或 SSH 证据。

启动脚本曾先后暴露 Windows 非 ASCII 路径和字符设备参数问题，分别记录在 `boot-whpx.stderr.log`、`boot-tcg.stderr.log`；脚本已改用 ASCII junction 和 `file:` 字符设备语法，最终 WHPX 运行记录为上段所述。

## 正式验证入口

在已启动并可登录的 openKylin 环境中执行：

```bash
bash scripts/openkylin_full_validation.sh runs/openkylin-validation/real-run
```

该脚本逐步保存 `/etc/os-release`、`uname -a`、Python/pip、安装、探针、validate、compare、verify、卸载的 stdout/stderr 和退出码。只有探针确认 `openkylin.ok=true` 且全部流程有可导出结果时，才可宣称完成。

当前 Windows 预检执行结果见 `runs/openkylin-validation-20260902/windows-full-validation/exit-codes.tsv`：`os-release=1`、`uname=0`、`python-version=49`、`pip-version=49`、`install=49`、`env-probe=127`，后续 CLI 步骤因 Windows bash 环境缺少 `python3` 均为 127；`uninstall=0`。这些结果不构成 openKylin 验证。

## 客观阻塞

当前无法在无提升权限且无可交互安装通道的 Windows 会话中完成桌面 ISO 的系统安装、SSH/控制台登录、项目安装及双 Agent API 运行。最小外部条件是：可访问的已安装 openKylin x86_64 实机/虚拟机（或允许启用 BIOS 虚拟化/Hyper-V 的主机），以及正式运行所需 API 凭据和网络策略。
