# Debian 技术验收包

该目录的 `.deb` 流程用于 openKylin 的可复现技术验收。包名为
`kylin-memory-bench`，架构为 `all`，依赖 `python3 (>= 3.9)` 与
`python3-yaml`。安装内容包括 CLI、`kmb/` 源码、默认 Agent 配置、核心和
对抗套件、协议/运行文档、重复运行汇总脚本、系统场景执行器、最小结构校验脚本以及 `tests/smoke_test.py` 最小离线测试集。

## 构建

在 openKylin 或另一台 Debian 系构建机运行：

```bash
bash scripts/build_deb.sh dist
dpkg-deb --info dist/kylin-memory-bench_0.2.0_all.deb
dpkg-deb --contents dist/kylin-memory-bench_0.2.0_all.deb
```

如需模拟升级，使用一个有效的 Debian 版本号构建新包：

```bash
KMB_DEB_VERSION=0.2.0+test1 bash scripts/build_deb.sh dist
```

### 当前发布候选（2026-09-08）

在 openKylin 2.0 SP2 VM 使用 `KMB_DEB_VERSION=0.2.0+release1 bash scripts/build_deb.sh dist/release-20260908` 构建并审计通过。产物为 `dist/release-20260908/kylin-memory-bench_0.2.0+release1_all.deb`，SHA-256 为 `E5C0991E7641B6A92A4A71AF667F5E7592D3D1FC67F6305B900A349D8D1E8BAC`。构建日志、`dpkg-deb --info`、完整清单和禁止内容审计见 `runs/openkylin-validation-20260908/release-build/`，均为退出码 `0`。该批次只做包构建和内容审计，不替代已归档的第六批系统生命周期。

在同一 openKylin 2.0 SP2 VM 将生命周期、变形和沙箱行动证据创新层纳入 `release2` 发布候选：`KMB_DEB_VERSION=0.2.0+release2 bash scripts/build_deb.sh dist/release-20260908-release2`，构建、内容审计、创新套件严格校验和包内 smoke 均为退出码 `0`。产物为 `dist/release-20260908-release2/kylin-memory-bench_0.2.0+release2_all.deb`；最终 SHA-256 以 `runs/openkylin-validation-20260908/release-manifest-final/release-manifest-release2.json` 为准，详细日志见 `runs/openkylin-validation-20260908/release-build-innovation-final/`。本批次不替代第六批系统生命周期。

当前 release4 技术候选（2026-09-09）在同一 openKylin VM 重新纳入系统场景执行器和最新统计/文档：`KMB_DEB_VERSION=0.2.0+release4 bash scripts/build_deb.sh dist/release-20260909-release4`。构建、禁止内容、核心/创新套件校验和包内 smoke 均为退出码 `0`；包哈希和审计路径以 `runs/openkylin-validation-20260909/release-manifest-release4/release-manifest-release4.json` 为准。该批次只做包构建和内容审计，不替代第六批系统生命周期。

release5 技术候选（2026-09-09）纳入 no-memory 聚合器字段修复和 release4 文档状态修正，作为历史中间产物保留：`KMB_DEB_VERSION=0.2.0+release5 bash scripts/build_deb.sh dist/release-20260909-release5`。构建、禁止内容、核心/创新套件校验和包内 smoke 均为退出码 `0`；产物为 `dist/release-20260909-release5/kylin-memory-bench_0.2.0+release5_all.deb`，SHA-256 和审计路径见 `runs/openkylin-validation-20260909/release-manifest-release5/release-manifest-release5.json`。该批次只做包构建和内容审计，不替代第六批系统生命周期。

当前 release7 技术候选（2026-09-09）纳入 release6 之后的发布文档状态统一和最终非视频复核引用：`KMB_DEB_VERSION=0.2.0+release7 bash scripts/build_deb.sh dist/release-20260909-release7`。构建、禁止内容、五套件校验和包内 smoke 均为退出码 `0`；产物为 `dist/release-20260909-release7/kylin-memory-bench_0.2.0+release7_all.deb`，SHA-256 和审计路径以 `runs/openkylin-validation-20260909/release-manifest-release7/release-manifest-release7.json` 为准。该批次只做包构建和内容审计，不替代第六批系统生命周期。

## 安装、验证、升级与卸载

```bash
bash scripts/install_deb.sh dist/kylin-memory-bench_0.2.0_all.deb
kmb validate --strict --suite /usr/share/kylin-memory-bench/suites/core-zh.yaml
bash scripts/verify_deb.sh /tmp/kmb-deb-smoke

# 新版本使用同一安装入口，dpkg 会执行升级。
bash scripts/upgrade_deb.sh dist/kylin-memory-bench_0.2.0+test1_all.deb
bash scripts/uninstall_deb.sh
```

openKylin KARE 会将应用 payload 和 dpkg 状态放入 shadow overlay。生命周期脚本会检查 `/opt/kare-applications/shadow/upper` 中的状态；KARE 的“安装成功/卸载成功”日志不能替代版本、CLI、升级和残留检查。验证脚本禁写 Python 字节码，卸载时仅清理本包目录内由验证生成的 `__pycache__`/`.pyc` 文件。第六批真实生命周期证据见 `runs/deb-lifecycle-authorized-20260908-rerun6/`，九个步骤均为退出码 `0`。

`verify_deb.sh` 先运行包内最小 smoke 测试，再使用内置确定性 reference/flawed 来验证安装包的 CLI、套件、
JSONL、评分和报告产物，不得把它当作正式双真实 Agent 结果。正式评测使用
`configs/agent-grok-memory.yaml`、`configs/agent-deepseek-memory.yaml` 及用户进程环境中的密钥。

如评分规则升级，包内 `scripts/rescore_run.py` 可从既有 `evidence.jsonl` 生成新的结果目录，
不会覆盖原始运行证据或原始分数。

若当前终端没有 sudo，允许使用 `dpkg-deb -x` 和 `KMB_HOME=<解包路径>` 做用户态
payload smoke，以确认包内启动器、CLI 和套件可运行；这不能替代 `dpkg -i` 的系统安装验收。

## 排除与许可证边界

构建脚本显式排除 `runs/`、虚拟环境、pip 缓存、研究缓存、`.env`、
`credentials.env` 和字节码文件；不要向包内写入 API Key、密码、私有数据、模型权重或
未经授权的第三方材料。

当前项目尚未选定项目级 LICENSE；`LICENSE-MIT-CANDIDATE.txt` 只是非生效候选文本。故 `.deb` 可作为内部技术验收和赛事现场复现材料构建、
安装和验证，但不得在没有项目负责人完成 LICENSE 选择、版权声明和第三方审计前宣称可对外
再分发。候选方案见 `docs/license-decision.md`，详见 `NOTICE` 与 `docs/license-audit.md`。
