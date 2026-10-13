# KylinMemoryBench 完成度与可用性复核（2026-10-13）

## 当前 0.2.2 修复结论

视频深审的两个 P1 问题已修复，新增 18 项回归、全量 176 项测试与三项跨平台 CI 均通过。现有 openKylin 3.0 的项目包已从 0.2.1 升级至 0.2.2，安装后 CLI 与工作台验证通过。新的真实双 Agent 六案例结果和首次网关失败均保留，详见 [修复验证报告](answer-evidence-fix-20261013.md)。

当前发行材料为 `dist/submission-0.2.2-20261013/`，旧发布原样保留。视频和正式作品提交仍未完成；用户已确认报名，邮件草稿未发送。当前代码可运行和规则回归通过不等于官方评审通过。

## 以下为 0.2.1 阶段的历史审计

下文当时的“最新”“最终”和分数均属于 0.2.1 阶段，已由上方 0.2.2 结论补充修正；尤其旧 CLI 解析受影响的分数不得作为当前版本结果。


## 追加复核：视频录制前深度审阅

本日随后的视频前深审复现了两个 P1 问题：回答检查跨回合导致误通过或误扣分，CLI 答复解析可能误取工具元数据。正式录制前应先修正并生成新的真实样例，详见 [复现证据与建议](video-review-20261013.md)。下文“非视频工程交付已完成”是先前安装、打包及既有测试覆盖范围下的结论；当前应区分工程可运行与语义评分可靠性，不能据旧结论宣称没有待修问题。旧包、证据和分数保留为当时记录。

## 结论

核心评测工具已经实现，并能在 Windows 和 openKylin 3.0 运行。本轮发现的发行包与验收缺陷已修复并同步 GitHub main。追加收口发布补丁版本 **0.2.1**，修复英文 Windows 的中文子进程编码问题；Windows/openKylin 各 158 项测试、三项 GitHub CI，以及隔离环境与主系统管理员环境的 release9→0.2.1 九步 dpkg 生命周期矩阵全部通过。最终 0.2.1 已重新安装，普通用户 CLI 和工作台对照评测也通过。**非视频工程交付已完成，赛事整体仍未完成**：视频按用户要求后置；仓库经审查按用户授权公开，未登录代码访问已通过；用户确认报名已完成，正式作品提交仍需参赛身份、确认邮件指引和视频链接。

当前 `dist/submission/` 是 10 月 11 日旧材料，不应直接提交。更新后的最终非视频材料位于 `dist/submission-public-20261013/`；其 README 和 manifest 标明当前状态、包版本、样例证据及 SHA-256。此前 `dist/submission-nonvideo-20261013/`、审计候选和原始失败记录保留，最终二进制沿用已验证的同一份 0.2.1 文件。

## 官网与 PDF 的对应

核对来源：用户提供的 3 页 PDF `ai_open_kylin_open_kylin_benchmark_XaCQyZepC8.pdf`、[比赛官网](https://www.oschina.net/os2026/)。PDF 的命令/示例只作为需求材料，未作为操作授权。

官网当前报名和作品提交截止：**2026-10-16 24:00（北京时间）**；入围名单 10 月 21 日，总决赛 10 月 29 日。官网公开数据的赛程记录最后更新时间为 2026-09-23，已于本轮实时读取，故不沿用 8 月公告中的 10 月 11 日/10 月 24 日旧日期。

| 官网要求 | 当前证据与状态 |
|---|---|
| 完整可运行的代码仓库链接 | `https://github.com/212667660-arch/kylin-memory-bench`；修复已上传 GitHub。用户授权审查后公开，实测 `isPrivate=false`；不携带登录凭据的 GitHub API 和 main/README 请求均 HTTP 200 |
| 作品介绍文档，推荐 PDF | 已有旧 PDF；本轮修正文稿与 PDF，包含背景、架构、场景、创新及维护规划 |
| 展示核心功能和流程的演示视频链接 | 未完成；旧提交说明仍是空白占位 |
| 报名确认后按邮件指引提交材料 | 用户已确认报名完成；尚未读取确认邮件指引，材料提交草稿已准备但未发送，未取得作品提交成功回执 |

官网四维评审为技术创新 30%、场景落地 30%、开源治理 20%、长期发展 20%；PDF 企业命题另列六维权重 15%/25%/25%/15%/10%/10%。项目的 `official_score.py` 是按 PDF 制作的工程自评工具，**100/100 不代表组委会评分，也不能免除必交视频**。

官网直接正文在本次浏览器中部分未加载；本轮通过搜索获取官网参赛指南，并读取页面脚本实际使用的公开赛程/评审数据验证。只读取公开资料，没有提交表单或发送邮件。原始网页、公开数据与赛题正文留存于 `runs/audit-20261013/`。

| PDF 交付 | 当前判断 | 实现/证据 |
|---|---|---|
| a. 完整评测方案 | 已具备 | `docs/solution.md`、`docs/evidence-protocol.md`、`docs/dataset-provenance.md` |
| 数据结构、案例和可解释自动评分 | 已具备，本轮修复一条错误期望 | `suites/`、`kmb/models.py`、`kmb/scoring.py`；主覆盖报告 49 案例、六类能力；扩展对抗套件已升为 version 2 |
| b. 示例任务、运行证据和结果 | 已具备 | 本轮离线验收、历史真实双 Agent 样例、JSON/JSONL/HTML/Markdown/SVG |
| c. 可复现脚本、配置、README、代码 | 修复后通过，并已上传 GitHub | Windows 与 openKylin 测试、干净 wheel 安装、源码包测试 |
| d. CLI/GUI，一键运行、批量对比 | 已具备，旧 `.deb` 缺陷已修复 | CLI、工作台实际点击验证、release9 解包后完整离线验收 |
| `.deb` 软件包（建议格式） | 最终 0.2.1 运行与真实 dpkg 生命周期均通过 | openKylin 3.0 隔离命名空间及主系统 sudo 管理员环境：release9 安装→验证→0.2.1 升级→完整验收→卸载→残留检查，九步均全 0；随后重新安装供普通用户使用 |
| e. openKylin 桌面、至少两款真实智能体、多维雷达图完整录屏 | **未完成** | 当前媒体文件为 0；`docs/demo-script.md` 只是录制脚本 |

## 已修复的可复现问题

| 问题 | 修复前实测 | 本轮修复 |
|---|---|---|
| pip 安装缺少运行时模块和数据 | 从项目外启动 wheel 的 CLI：`ModuleNotFoundError: No module named 'scripts'` | 随 wheel 安装 `scripts` 包及 configs/suites/脚本数据；统一定位源码、Debian 和 pip 的运行资源 |
| `.deb` 漏装离线进程演示脚本 | release8 中 kylinbot-process 六案例全部 `invalid_runtime`、`error_cases=6` | 包内加入 `scripts/openkylin_ecosystem_agent.py`；release9 相同路径六案例有效、100 分 |
| 验收把结构合法的失败证据判为通过 | release8 `official-acceptance` 显示 pass/0，但一侧分数无效 | strict verify 后继续检查 `score_valid is True`；缺脚本、超时等无效结果不能通过验收 |
| 空重复批次可获稳定性满分 | `all([])` 导致空 aggregates 通过 | 满分要求两款 Agent，且每侧多于一批、有效率 100% |
| 更新路径后复用被误扣分 | `cross-task-002-export-new` 正确生成 write/revise/reuse，却期望 write/reuse；参考侧对抗套件 97.37 | 修正期望序列为 write/revise/reuse；正确行为 100，旧路径仍扣分；升版并重新生成覆盖 manifest |
| 源码发行包中的测试失败 | 漏掉测试依赖的生态调研报告；`/tmp` 指向 `/var/tmp` 时路径断言失败 | 附贡献指南和指定公开报告；路径断言先 resolve；源码包在 VM 回归通过 |
| 交付说明过时/夸大完成状态 | MIT 已生效仍写待确认；文稿暗示视频已存在 | 统一 README、贡献指南与当前状态说明；明确自评分、历史证据和待交付视频 |
| 工作台信息不一致 | 已选套件仍显示未选择，coverage manifest 被当作无效套件；未安装 KylinAgent 却显示“已安装” | 套件摘要跟随表单；覆盖清单不进入可运行套件选择；发现状态说明一致 |
| 英文 Windows 中文子进程失败 | GitHub Windows Python 3.9 使用 cp1252；中文输出报 UnicodeEncodeError | Agent UTF-8 JSONL/文本协议显式设置子进程 PYTHONIOENCODING=utf-8；新增强制 cp1252 的回归测试，版本升至 0.2.1 |

回归测试在修复前确实重现验收误通过和案例误扣分，修复后通过。保留的日志包括 `regression-before.log`、`regression-after.log`、`suite-regression-before.log`、`suite-regression-after.log`。

## 验证范围和结果

| 检查 | 本轮结果 | 可核验证据 |
|---|---|---|
| Windows 全量单元测试 | 最新 158 项通过 | `runs/nonvideo-closeout-20261013/unittest-encoding-fixed.log` |
| openKylin 3.0 源码包测试 | 最新 158 项全部通过 | `runs/nonvideo-closeout-20261013/vm/unittest-021.log` |
| CLI 离线验收 | pass/0；四组对比、八份有效结果 | `runs/audit-20261013/acceptance-final/` |
| 干净 wheel 安装，在源码目录之外执行 | 0.2.1 在 Windows Python 3.9、Ubuntu Python 3.12 的 CI 中全部通过 | 最终候选包 `verification/` |
| Debian release9 包内离线验收 | pass/0；core 进程侧 `score_valid=true`、100 分、零运行错误 | VM 本轮包内验收记录 |
| Debian 包内最小 smoke | 2 项通过 | VM 包内 `tests/smoke_test.py` |
| 案例覆盖报告 | 49 个主案例，六类能力完整 | `runs/audit-20261013/coverage-final-v2/`、`suites/coverage/manifest.yaml` |
| 浏览器工作台 | 创建对照评测→运行完成→结果中心→六维指标与雷达图，控制台无 error | `runs/workbench/wb-20261013-010027-eed853ab/`（reference 100、flawed 41.67） |
| 当前真实双 Agent | 两批全部完成，四份分数均有效、strict 校验全 0 | `runs/audit-20261013/vm/installed/` |
| release9 生命周期 | 九步全部退出码 0，主系统包数据库哈希未变，主系统仍无 kmb | `runs/nonvideo-closeout-20261013/vm/lifecycle-r4/lifecycle-summary.json` |
| 自动发行回归 | Windows Python 3.9、Ubuntu Python 3.12 干净 wheel 验收，以及 Ubuntu 安装/升级/卸载矩阵 | `.github/workflows/verify.yml`；GitHub Actions 运行记录附最终 manifest |
| 最终 0.2.1 隔离生命周期 | release9→0.2.1 九步全 0，主机状态哈希未变 | `runs/nonvideo-closeout-20261013/vm/final-evidence/lifecycle-r4/lifecycle-summary.json` |
| 主系统管理员生命周期 | release9→0.2.1 九步全 0，真实 sudo/root 与系统 dpkg；卸载后无命令、payload、文档残留 | `runs/nonvideo-closeout-20261013/host-admin-evidence/host-admin-lifecycle/lifecycle-summary.json`；交付包 `sample-evidence/host-admin-lifecycle/` |
| 最终安装包的普通用户使用 | 0.2.1 已重新安装；从源码外执行 CLI 离线验收 pass；工作台 HTTP、配置/套件、创建评测、结果及两侧雷达图检查全通过 | 交付包 `verification/installed-user-summary.json`；普通用户工作区 `~/KylinMemoryBench`，启动说明见 `docs/deb-release.md` |

0.2.1 代码 CI：[运行 38303384340](https://github.com/212667660-arch/kylin-memory-bench/actions/runs/38303384340)，main 收口 CI：[运行 38304015260](https://github.com/212667660-arch/kylin-memory-bench/actions/runs/38304015260)，三项 job 均 success。首轮发现 Windows 编码错误的失败记录同样保留，未跳过失败测试。随后仅更新文档与证据状态，运行时代码和已测试二进制不变。

SSH 本轮已连通，VM 为 openKylin 3.0（huanghe）、Python 3.12.2、PyYAML 6.0.3。远程使用独立 `/tmp/kmb-audit-20261013/`，真实复测使用脚本创建的每 Agent 临时 HOME 与空记忆库。没有重装或卸载日常 Agent。

本轮真实六类快速套件结果：KylinBot 两批 **22.22、30.56**，均值 **26.39**、样本标准差 **5.8973**；OpenClaw **22.22、22.22**，均值 **22.22**、标准差 **0**。各侧有效分数率均为 **100%**，事件数分别为 KylinBot 50/50、OpenClaw 34/35；`native_memory_events=0`。当前 Agent 环境指纹为 KylinBot `fc5ac5eb62b9120f…`、OpenClaw `27e95041a45c9084…`，与旧文档中的 10 月 4 日指纹不同，不把两个日期直接合并为同一实验。低分是被测 Agent 的案例行为结果，不能等同于 Benchmark 程序失败；但 KylinBot 的批次波动也不能被“有效率 100%”掩盖。

真实复测使用本轮独立代码快照 `source-fixed`；其 `suites/quick.yaml`、`kmb/runner.py`、`kmb/scoring.py` 与最终包保持相同文件哈希。随后修改的扩展对抗用例与界面不影响这两批快速套件的评分；没有把最终包中未运行的扩展套件说成真实 Agent 全矩阵验证。

复现时需要区分环境：Windows 可以运行 CLI、工作台和离线演示；当前主机没有 openKylin 生态 Agent，快速发现应明确阻断。真实 Agent 对比应在安装了 Agent 的 openKylin 环境执行，并具备有效网关凭据/网络/额度。

## 完成提交还需要的工作

1. 在 openKylin 桌面录制至少两款真实 Agent 的评测与多维雷达图，建议 3–5 分钟；视频脚本不是视频证据。
2. 上传视频到评委可访问的位置，并在提交说明中填入真实链接。
3. 填写参赛身份与报名确认信息，待视频链接齐备后按邮件指引完成正式提交并保存回执。用户已确认报名，公开代码访问已解决；邮件草稿为 `docs/submission-email-draft.md`，未发送。

## 可继续改进

- **发行包回归已落地**：CI 从源码目录外安装 wheel 和验证 `.deb`，避免源码可用掩盖漏包。工作流只授予 contents:read 权限，固定 Action 提交，关闭 checkout 凭据持久化。
- **真实稳定性**：两批有效只是可运行的证据，不能证明长期稳定。应在冻结模型、网关、Agent 版本和套件后跑更多批次，保留失败分母并比较均值/标准差。
- **覆盖深度**：主覆盖报告 49 条以声明式人工案例为主，后续增加实体/噪声/语言变体和更多跨会话/长间隔测试。包装层重建不能称为真实 OS 重启。
- **评分可信度**：工程自评分仍以文件、检查和产物作为代理指标，无法自动评价创新价值、实际应用效果和社区治理；应展示真实证据与限制。
- **系统生命周期已补齐**：相同 0.2.1 二进制同时通过 openKylin 隔离系统目录和主系统 sudo 管理员的真实 dpkg 矩阵。当前验证沿用已有 VM 和依赖，不冒称全新 VM；若后续进入发行版软件源，再增加标准镜像和目标架构认证。
- **KylinAgent**：当前结构化自动评测仍阻断；PDF 只要求至少两款，因此它不阻断已有双 Agent 方案。不要把发现到服务当成适配已完成。

## 使用命令

先在源码包根目录安装依赖或执行 `python3 -m pip install .`。离线复核：

```bash
python3 -m unittest discover -s tests -v
python3 -m kmb.cli official-acceptance --out runs/my-acceptance --mode offline
python3 -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .
```

真实对比应使用隔离重复入口，避免污染日常记忆：

```bash
python3 -m kmb.cli official-acceptance --mode installed \
  --agent-a kylinbot --agent-b openclaw --repeats 2 \
  --out runs/my-installed-acceptance
```

所有分数结合观测边界解释：offline/reference/flawed/stand-in 是模拟或演示；真实进程/Agent 存储证据测系统级行为。`native_memory_events=0` 时不宣称模型原生长期记忆能力。

## 仓库与权限核查

公开前复查全部可达历史的 362 个 Git blob、提交/标签正文及四次 CI 完整日志，覆盖 API/GitHub/AWS token、私钥、Bearer、带凭据 URL 和直接赋值密钥模式。六个直接赋值候选经上下文核实为两处中文配置占位和四个历史版本的故意拒绝密钥输入测试；未发现待处理密钥。只记录对象、路径、类型和摘要，不记录密钥值。这是有限模式审查，不能保证排除所有敏感资料。根据用户“审查通过后公开现有仓库”的明确授权，将现有仓库设置为 PUBLIC；未登录仓库 API 和 main/README 均 HTTP 200。审查与访问证据见最终包 `verification/repository-public-review.json` 和 `verification/public-access-check.json`。

隔离生命周期使用 Bubblewrap 用户命名空间将当前用户映射为容器内 root，系统根只读；包数据库、命令目录和新包文件写入独立目录。用户随后授权管理员验证，本轮通过 sudo 在主系统额外执行完整矩阵，预检确认本包原先未安装；九步全部通过后，再安装已验证的最终版本并完成普通用户检查。两类证据分别归档，不再把主系统状态表述为全程未修改。所有安装/升级/卸载均由实际 dpkg 执行，没有使用 `--force-depends` 或伪造包状态；密码只用于 sudo 交互，不写入项目、日志或交付材料。

0.2.1 的编码修复在 Linux 中不改变记忆评分规则或案例；10 月 13 日真实双 Agent 证据仍作为同一 quick 套件/评分器下的系统行为样例，未冒称在新版本上重新消耗 Token 完成全矩阵。
