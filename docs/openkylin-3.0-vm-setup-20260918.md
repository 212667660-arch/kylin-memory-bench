# openKylin 3.0 AgentOS VM 安装记录（2026-09-18）

> 口径：**power-on 已成功，安装向导进行中**（需人工完成 GUI 安装）。  
> **未**迁移项目、**未**跑 Benchmark / Token / KylinBot。

## 重启前阻塞（已解除）

- Hyper-V / VirtualMachinePlatform / HypervisorPlatform：管理员关闭后 **Disabled**；`HypervisorPresent=False`；`Virtualization-based security: Not enabled`
- ISO：`D:\ISOs\openKylin-Desktop-V3.0-AgentOS-20260905-x86_64.iso`，大小 **7435438080**，CD001 正常
- 首次启动失败原因还包括：
  1. vmx 路径错误（`D:\\\\` 四反斜杠）
  2. `guestOS = other6x-64` **不受支持**
  3. `virtualHW.version = 19` + 过高配置导致 `vmware-vmx` **0xc0000005** 崩溃

## 当前可用配置（已简化并成功启动）

| 项 | 值 |
|----|-----|
| VM | `D:\openKylin-VM-3.0-AgentOS\openKylin-3.0-AgentOS.vmx` |
| 硬件 | **virtualHW 18**，**2 vCPU / 4GB**，BIOS |
| guestOS | `ubuntu-64`（兼容标签；系统实际为 openKylin ISO） |
| 系统盘 | `openKylin-3.0-system.vmdk`（80GB sparse，已重建） |
| 数据盘 | `openKylin-3.0-data.vmdk`（60GB sparse，当前 vmx 中 `scsi0:1.present=FALSE`，安装系统后再挂） |
| ISO | 光驱已连接上述 3.0 AgentOS ISO |
| 启动结果 | **`vmrun list` = 1**，日志显示 BIOS、scsi 容量 `167772160` 扇区（80G）、屏幕 720x400 |
| 界面 | VMware Player / Workstation 窗口已打开 |

安装完成后可选：改回 4 vCPU / 8GB、启用数据盘、挂载 `/data`。

## 人工安装步骤（当前）

在 VMware 窗口中完成 openKylin 3.0 安装向导：

1. 系统装入 **80GB** SCSI 盘  
2. 创建用户与密码（**不要**把密码写进项目仓库）  
3. 可选安装 openssh-server  
4. 安装完成后：**关机 → 断开 ISO**（设置里取消连接，或改 vmx `cdrom0.startConnected=FALSE`）→ **从磁盘启动**  
5. 客户机内验收：`cat /etc/os-release`、`uname -a`、`df -h`、`lsblk`

## 口径（强制）

- 当前：**VM 已能从 ISO 启动**；**安装完成前**不得写「openKylin 3.0 已安装」或「长期记忆评测已验收」
- 宿主机项目仓库未迁入本轮
- 旧 2.0 `D:\openKylin-VM` 已删除，不恢复、不冒充


## 已就绪

| 项 | 值 |
|----|-----|
| ISO | `D:\ISOs\openKylin-Desktop-V3.0-AgentOS-20260905-x86_64.iso` |
| ISO 大小 | **7435438080**（与预期一致） |
| ISO 头 | ISO9660 `CD001` 已核验 |
| VM 目录 | `D:\openKylin-VM-3.0-AgentOS\` |
| 配置 | `openKylin-3.0-AgentOS.vmx` |
| 硬件 | 4 vCPU / 8GB；系统盘 80GB sparse；数据盘 60GB sparse |
| 工具 | `E:\VMware\vmrun.exe`、`vmware.exe`、`vmplayer.exe` |

## 本轮已修复的配置问题

1. **vmx 路径错误**：原文件中 `D:\\\\...` 四反斜杠，导致磁盘/ISO 路径无效。已改为：
   - `scsi0:0.fileName = "D:\openKylin-VM-3.0-AgentOS\openKylin-3.0-system.vmdk"`
   - `scsi0:1.fileName = "D:\openKylin-VM-3.0-AgentOS\openKylin-3.0-data.vmdk"`
   - `cdrom0.fileName = "D:\ISOs\openKylin-Desktop-V3.0-AgentOS-20260905-x86_64.iso"`
2. `deviceType` 由 `disk` 改为 `scsi-hardDisk`。
3. **固件**：`efi` → `bios`（尝试规避启动问题）。
4. 清理陈旧 `.lck` / `.vmem`；备份 `openKylin-3.0-AgentOS.vmx.bak-paths`。

## 启动阻塞（如实）

`vmware.log` 关键行：

```text
IOPL_Init: Hyper-V detected by CPUID
Powering on guestOS 'other6xlinux-64' ...
MsgHint: msg.loader.mitigations.wsAndFusion
VMAutomationProcessMessage: Postpone the command. VM not running
```

- `Get-Process`：`vmware-vmx` 进程存在  
- `vmrun -T ws list`：**Total running VMs: 0**（未完成 power-on）  
- `HypervisorPresent = True`（宿主启用了 Hyper-V / 虚拟化监控）  
- 曾出现 `vmware-vmx.dmp` 与早期 `0xc0000005` 崩溃（路径修复前）

**结论**：当前无法在本机完成 openKylin 3.0 **交互安装**，因 VMware 未能在 Hyper-V 存在时正常启动客户机。

## 人工解除阻塞（需管理员 + 重启）

以管理员 PowerShell：

```powershell
# 查看
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform

# 关闭 Hyper-V 相关功能（会要求重启）
Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
Disable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart
# 重启后
Restart-Computer
```

说明：

- **WSL2 / Docker Desktop** 常依赖 Hyper-V 或 Virtual Machine Platform；关闭后可能受影响。  
- 重启后再次：

```powershell
& "E:\VMware\vmrun.exe" -T ws list
& "E:\VMware\vmrun.exe" -T ws start "D:\openKylin-VM-3.0-AgentOS\openKylin-3.0-AgentOS.vmx" gui
```

并请在 VMware 窗口中处理可能出现的 **side channel mitigations** 提示。

## 安装向导要点（待 VM 能启动后）

1. 系统装入 **80GB** SCSI 盘。  
2. **60GB** 盘尽量单独挂载 `/data`；若安装器不支持，验收时写明「无独立数据盘」。  
3. 用户密码 / SSH **不得**写入 `E:\上海开源软件应用创新大赛`。  
4. 安装后 **断开 ISO**（`cdrom0.startConnected=FALSE`），从磁盘重启。  
5. 客户机验收：`whoami` / `uname -a` / `cat /etc/os-release` / `df -h` / `lsblk`。

## 口径（强制）

- 当前状态：**VM 配置已校正，安装未完成**。  
- **不得**写成「openKylin 3.0 已安装」或「长期记忆评测已在 3.0 验收」。  
- 宿主机仓库 `E:\上海开源软件应用创新大赛` **未**在本轮修改评测逻辑；仅追加本说明。

## 旧环境

- `D:\openKylin-VM`（2.0）已按任务说明删除，**不恢复、不冒充 3.0**。
