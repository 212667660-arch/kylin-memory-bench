# openKylin 环境矩阵（2026-09-02）

| 环境 | 架构 | 介质/工具 | 可启动 | 可登录 | CLI 验收 | 结论 |
|---|---|---|---|---|---|---|
| 当前主机 Windows 11 | AMD64 | QEMU 11.1.0；官方 x86_64 ISO 已校验 | QEMU 空机/ISO 进程可运行 30 秒 | 否 | 否 | 仅主机预检 |
| WSL `docker-desktop`（已停止） | AMD64 | WSL2/Docker | 否 | 否 | 否 | 不适用，禁止替代 openKylin |
| openKylin 2.0 SP2 x86_64 | x86_64 | NJU 官方镜像 ISO | 待实测 | 待实测 | 待实测 | 未完成 |

ISO SHA256：`d146f8ac6c76fbfaa3ae6554010dcaed868ba4323c8c6eb83c9ff3a3984e6bf7`；MD5：`04ca4c0ef61694e4afe67ac40e6978ec`（官方页面一致）。

验收命令和标准以 `docs/openkylin-validation-runbook.md` 与 `scripts/openkylin_full_validation.sh` 为准。所有待实测字段必须在真实 openKylin 环境内填写，不能用其他系统结果替代。
