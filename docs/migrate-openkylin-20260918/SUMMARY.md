# openKylin 迁移 + 无 API 验收摘要（2026-09-18）

## 通道
- VMware: E:\VMware\vmware.exe / vmrun
- VM: D:\openKylin-VM\openKylin.vmx（openKylin 2.0 SP2，已运行）
- SSH: Cisyam@192.168.182.129:2222，密钥 %USERPROFILE%\.ssh\openkylin_vm_ed25519（无私钥内容入库）

## 远端路径
- REMOTE_ROOT=/data/usershare/kylin-memory-bench-20260918
- 数据盘：/dev/sda4 → /data（约 21G 可用）；/data 根目录 555，用户写入点为 /data/usershare
- 未覆盖 /home/Cisyam/kmb-openkylin-validation-20260906

## 同步
- 宿主打包 kmb-src-20260918.tar.gz
- SHA256: 926AF68E7BA50A8918530D593A60D39FDBD2F36A63A890B60932B53C11399E23（宿主/客机一致）
- 排除：runs/、.venv*、__pycache__、credentials.env、密钥文件

## 安装
- bash scripts/install_local.sh python3 → 退出码 0
- .kmb-venv 位于 REMOTE_ROOT 下；Python 3.12.2；PyYAML 6.0.1
- import kmb 成功，路径在项目 venv site-packages

## 无 API 验收（实测退出码）
| 项 | 退出码 | 结果 |
|----|--------|------|
| uname / os-release | 0 | openKylin 2.0 SP2 (nile) |
| env_probe --require-openkylin | 0 | status=ok；checks.openkylin.ok=true |
| unittest discover | **1** | 71 项中 **1 FAIL**（见下） |
| validate --strict core-zh | 0 | 6 cases valid |

### unittest 失败（如实记录）
- `tests.test_system_scenarios.test_safe_executor_records_real_and_unexecuted_boundaries`
- 断言：posix 上 expects recalls>=3，实测 **2**
- 平台/KARE 场景执行器在该 VM 环境下边界事件数不足；**非静默忽略**

## 边界
- 本轮为「迁入 + 无 API 验收」
- **不是**真实 Grok/DeepSeek API 对比
- **不是** A/B 原生记忆主结论
- wrapper/register/no-memory 能力未删除

## 日志
本目录复制自远端 migrate-logs/
