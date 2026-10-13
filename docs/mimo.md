# 修改台账（mimo.md）

> 路径固定：`docs/mimo.md`。面向本仓库所有 AI / 协作会话。

## 2026-10-14 重新编写网页演示演讲稿（完成）

- 意图：依据当前 0.2.4 自动发现及负责人直接在网页执行的要求，生成可照念口播与对应点击流程。
- 范围：新增 `docs/demo-script-20261014.md`；`dist/speech-web-20261014/` 的运行前口播、有效结果后口播、异常备用口播和操作说明；README 当前稿件入口、`tasks/todo.md` 与本台账；同步 VM 新稿目录及 GitHub 文档。
- 边界：主流程采用总览勾选小K/OpenClaw并开始快速对比；新建评测只作替代入口说明，不重复启动。只写稿，不配置凭据、不补充 Token、不发起评测、不录制视频、不改原 openKylin 3.0、项目安装包、冻结标签与既有证据。旧稿清理记录保留，新稿使用独立日期路径。
- 验收：口播与实际页面标签、quick 六案例和 42/1/180 参数一致；结果段以本批有效结果为前提，额度不足提供异常分支；不预填分数、不声称自动 strict、完整矩阵或模型原生长期记忆已验证。检查正文一致、中文编码和链接，完成同步后登记实际交付。
- 实际交付：主口播 10 段、859 个汉字，运行前 4 段，结果有效后 6 段；提供独立异常备用段。`docs/demo-script-20261014.md` 含逐段点击与等待、结果有效性条件、新建评测替代流程以及录制前额度/副本说明。`dist/speech-web-20261014/` 生成 3 份照读 TXT、1 份操作版 MD 与 SHA-256 manifest，UTF-8 回读及正文提取一致。
- 内容核对：采用总览“开始快速对比”，也可由新建评测以同一套件/参数替代；结果中心使用实际“概览/案例/证据/日志”标签与 quick-update。没有预填现场分数、假设规则全通过或宣称自动执行 strict。正式录制画面须体现 openKylin 桌面，模型调用等待另计；当前额度不足时只使用异常分支，不能念有效结果段。
- 同步与边界：新稿单独同步至 VM `~/KylinMemoryBench/speech-web-20261014/` 及用户工作区文档，GitHub 同步当前稿件入口。旧稿清理区、历史材料和原安装包保留；没有启动评测/测试、补充 Token、重置记忆、录制视频或发送提交材料。

## 2026-10-14 新建评测与宿主环境自动发现统一（代码与部署完成，未运行测试）

- 意图：解决新建评测仍只展示内部 YAML 配置的问题；默认选择工作台服务所在系统已安装的智能体，并真实支持自定义套件与共同参数。
- 范围：`kmb/agent_registry.py` 的有界安装/可执行文件发现与元数据；`kmb/agent_adapters/base.py`、`hermes.py`、`kylinbot.py` 的一致命令解析；`kmb/workbench.py` 和 `kmb/quick_compare.py` 的真实已安装智能体任务参数；`kmb/web/app.js` 及必要样式的默认入口、选择、草稿与刷新；版本、README、CHANGELOG、工作台/当前环境文档与本台账；`runs/host-agent-discovery-20261014/` 的静态记录和 VM 部署。
- 边界：自动检测仅针对后端所在机器和用户，浏览器在 Windows 不代表检测 Windows 宿主系统；不扫描整个磁盘、不读取或返回密钥、不自动安装 Agent、不修改日常记忆、不创建替代模拟智能体。保留高级 A/B/对照配置与冻结 0.2.2 材料，原 openKylin 3.0 不变。
- 验收：后端真实发现与新建评测共享同一注册表，已安装但不可驱动/隔离目录未就绪明确显示并阻断启动；用户选定的 suite/seed/retries/timeout 传入现有原生适配器/runner，而不是退回固定快速套件。按负责人要求不执行测试、连接探针或模型调用，仅静态审阅/语法、构建安装和只读页面/元数据核对。
- 实际修改：发现使用 PATH 与固定常见用户/系统目录，OS 用户 HOME 独立于隔离 HOME；安装来源、命令路径、检测时间/主机由后端返回。新建评测以已安装智能体为默认入口；高级记忆层配置保留且增加中文名称与用途。旧草稿不再把新入口带回内部 YAML；本轮保存的草稿包含来源、轨道和实际两侧标识。
- 执行边界：原生任务收到真实 Agent id，后端重新检查可执行性并校验共享 suite/seed/retries/timeout，转入原生适配器和现有 runner。实际评分器固定 deterministic-v2；主机安装与评测目录就绪分开判断，未就绪不能启动。页面进入和可见时每 30 秒仅查询安装元数据，输入/下拉操作时避免重绘打断。
- 部署结果：0.2.4 已构建安装，工作台 PID 28508 返回版本 0.2.4，检测主机 Cisyam-pc。小K/OpenClaw installed=true、runnable=true；Hermes 已安装但隔离目录未准备；KylinAgent 需手动观测。保留原 KMB_AGENT_HOME 与 openKylin 3.0，系统版本文件 SHA-256 前后相同。
- 静态与页面：全部 tracked Python 源仅语法解析，JavaScript `node --check` 与差异空白检查通过；七项安装后的源文件与本机 SHA-256 一致。页面已显示小K/OpenClaw、六案例 quick、42/1/180 参数及两侧最近额度不足。证据为 `runs/host-agent-discovery-20261014/new-evaluation.png`、`deployment-status.json`、`static-checks.json`；deb SHA-256 为 85d9088cdef617958401f73cfde74ec5b7b0caf0a60f8d4662cfa3dc1a692927。没有点击开始、运行测试或新的模型回合；本轮不宣称评测回归通过、不发布正式标签。
- 交付：同步工作区文档到 VM 并提交 GitHub；旧 0.2.2 标签、发行附件、历史结果与清理记录保留。

## 2026-10-13 清理旧演讲稿与录制材料（清理完成）

- 意图：按负责人要求清理旧演讲稿、分镜、录制操作说明及其独立交付包，避免继续误用。
- 范围：移出 `docs/demo-script.md`、`docs/video-preparation-20261013.md`；`dist/speech-gui-20261013/`、`dist/speech-latest-20261013/`、`dist/video-ready-20261013/` 及同名 ZIP、`dist/video-script-20261013/`；`runs/speech-gui-20261013/`、`runs/speech-refresh-20261013/` 及视频审阅目录中的两份旧稿；VM `video-prep-20261013/` 和用户工作区中对应的旧稿/分镜/录制入口。更新 README、当前作品介绍、评审复现卡、任务状态、修复报告与审计中的失效入口说明，以及本台账。
- 补充范围：`runs/video-prep-20261013/` 中旧录制、设备调查、排版脚本与排版检查图，以及 `vm-prep/` 的旧录制入口/环境说明副本；准备状态、预检证据与原界面截图保留。
- 边界：材料移入工作区外的可恢复清理区；保留代码、安装包、冻结发行/提交快照、真实运行和审阅证据、历史台账。保留 VM 当前隔离 HOME、`prepare-gui.py`、状态引用和工作台服务。遵守 Token 用完且不需要测试的要求，不运行测试或 Agent 回合，不改 openKylin 3.0。
- 验收：逐项检查活动路径已移出、文档当前入口无失效稿件链接、保留文件和工作台进程仍在；只做文件/进程元数据核对与文档差异检查，记录实际清理数量并同步 GitHub。
- 实际清理：Windows 共移出 22 项路径、65 个文件；VM 共移出 19 个文件，两份 docs 源稿原本已不在 VM 工作区。全部已存在的目标路径复核后均无残留；恢复清单位于 `C:/Users/123/.codex/trash/kmb-recording-20261013-233650/cleanup-manifest.json` 和 VM `/home/Cisyam/.local/share/kmb-cleanup/recording-20261013-233748/cleanup-manifest.json`。
- 保留与核对：VM `prepare-gui.py`、`gui-private-home.txt`、`gui-ready.json` 和当前私有 HOME 均保留，工作台仍为 PID 22733；本机 GUI 准备脚本和评分复现探针仍在。文档活动链接不再指向已清理稿件；历史审计、台账、冻结提交包与发行包中的文档快照原样保留。未运行测试、Agent 调用或系统升级。
- 文档交付：README、评审卡、作品介绍、任务状态与修复报告改为视频暂缓且旧稿已清理；技术审阅和审计追加历史引用说明。同步 VM 用户工作区与 GitHub 当前分支，冻结标签和发行附件不变。

## 2026-10-13 已安装智能体入口与真实后端状态修复（代码与部署完成，按要求未运行测试）

- 意图：修复智能体页只列 YAML 方案而遗漏已安装小K/OpenClaw的问题，连接真实发现、选择和快速对比后端；修正凭据误报、隔离目录下的安装误报及最近运行状态。
- 范围：`kmb/agent_registry.py`、`kmb/workbench.py`、`kmb/web/app.js`/`styles.css`、项目版本文件；`docs/workbench.md`、`docs/current-environment.md`、README/变更说明与本台账；`runs/installed-agent-registry-20261013/` 的静态检查、构建/部署记录与界面截图；VM 中项目代码/软件包与工作台服务，不修改 Agent 日常数据。
- 用户最新约束：VM 确实已安装 Agent；目前 Token 用完，先修改，不需要测试。本轮不运行测试套件、连接探针、真实 Agent 回合或充值动作，只做静态审阅、语法检查和部署后的页面/安全元数据核对。
- 边界：保留原 openKylin 3.0 与既有安装、记忆和历史失败结果；不导入或输出密钥、不将额度不足讲成缺凭据或低分；保留冻结 0.2.2 标签/包，当前修复使用新的项目版本，不发布未经测试的新正式标签。
- 验收口径：后端返回真实已安装条目和当前工作区 readiness；页面选择调用既有真实快速对比端点；本地/回放方案无需云凭据，命令方案由自身管理，HTTP 实调用缺凭据单独显示；历史额度不足保留并明确展示。完成后记录静态检查和实际部署结果，不宣称真实评测或测试通过。
- 实际结果：已构建并安装项目包 0.2.3，工作台 PID 22733 加载新后端。VM GET /api/agents 返回四款 installed=true：小K/OpenClaw 当前独立目录 runnable=true；Hermes 本机已安装、独立目录未准备；KylinAgent 需结构化 GUI/服务事件导出。最近两侧实际失败均显示 billing_error，不显示为缺凭据或正常低分。
- 页面与接口：智能体页优先呈现真实本机条目，勾选/开始沿用 POST /api/quick-compare；提供原生详情和最近运行入口，11 项 YAML 方案收纳到可展开的评测方案与示例。只读 API 已核对本地记忆/回放 not_required、命令 agent_managed、HTTP 真调用 not_detected；底栏明确工作台 API 的凭据范围。
- 检查与交付：Python/JavaScript 语法及 git diff --check 通过；安装后的五项后端/前端源文件 SHA-256 与本机修改一致。界面截图 `runs/installed-agent-registry-20261013/native-agent-page.png`、部署状态及当前 deb 保留；当前 deb SHA-256 为 424aecd8bd0acf7e1cbdf4f3b1192a095ac822f21e987e8df005416af00d6f41。未运行 unittest、连接检查或新 Agent 回合，未发布 0.2.3 正式标签。
- 原系统与数据：/etc/os-release 前后校验一致，仍为 openKylin 3.0。部署未向日常 Agent 配置/记忆发起写入；全目录指纹因后台 daemon_state.json 刷新而未完全一致，时间戳检查只发现该动态状态文件变化，不把全目录字节完全不变作为已验证结论。

## 2026-10-13 按网页执行流程重新生成演讲稿（完成）

- 意图：按负责人最新要求，将照读稿完整改为网页选择 KylinBot + OpenClaw、开始快速对比和回溯本次结果的录制流程。
- 范围：`docs/demo-script.md`、`docs/video-preparation-20261013.md` 的稿件指引、本台账；`runs/speech-gui-20261013/` 中的旧稿备份、排版脚本与检查；`dist/speech-gui-20261013/` 的纯口播 TXT/MD/PDF、操作版 MD/PDF 与 manifest；同步 VM 准备目录和 GitHub 文档。
- 边界：只生成/同步稿件，不点击真实评测、不重置正在使用的副本、不配置新的云凭据、不修改 openKylin 3.0、冻结 0.2.2 软件包和旧交付材料。正文不预填总分，不把“预检 ready”解释为云端鉴权通过，不宣称 GUI 自动执行 strict 验证。
- 验收：全部镜头动作与当前网页标签一致；工作台 API 档案与独立 Agent 配置说明准确；等待和有效结果条件明确，提供错误时的备用口播；两份 PDF 提取文本与稿件一致并完成页面渲染检查，旧稿保留。
- 实际结果：新版正文 9 段、974 汉字，约 4-5 分钟讲解，真实运行等待另计。第 5 段点“开始快速对比”后停顿；第 6-9 段以本批各 6 案例、有效分数、错误 0 与镜头外 strict 检查为条件。结果完成后的自动跳转、历史回看和 quick-update 最终回合证据步骤已对照源码；正文没有终端启动命令、预填总分或自动 strict 声称。
- 交付：`dist/speech-gui-20261013/` 中直接照读 TXT/MD/PDF（PDF 1 页）、完整操作稿 MD/PDF（PDF 3 页）、准备说明和 SHA-256 manifest；PDF 完整正文提取匹配，两份均渲染检查通过。旧正文备份保留于 `runs/speech-gui-20261013/demo-script-before.md`，原交付目录不覆盖。
- 凭据口径：工作台 credentials.env 缺失和 Token 环境变量未加载已核对；独立 Agent 从自身配置执行，预检 ready 不等于云端鉴权成功。稿件说明统一凭据标签的局限并提供异常备用口播。本轮仅同步稿件与说明，不改云凭据、评测运行状态、操作系统或发布软件包。

## 2026-10-13 改用网页快速对比的镜头外准备（完成）

- 意图：按负责人改用网页选择执行的要求，为 KylinBot + OpenClaw 准备独立记忆副本，提供准确的选择建议。
- 范围：本台账、`docs/video-preparation-20261013.md` 的网页入口说明；`runs/gui-video-prep-20261013/` 中的准备脚本与脱敏状态；VM 普通用户私有目录中的两款 Agent 副本，以及工作台进程环境、准备目录状态和入口说明。
- 边界：保持原 openKylin 3.0、冻结 0.2.2 软件包与发布材料；不改日常 Agent 配置/记忆，不启动真实 Agent 对话，不替负责人点击开始评测。SQLite 采用一致备份，不复制活动 WAL/SHM 到快照；凭据副本只存于 VM 工作区之外的用户私有目录。
- 验收：确认没有终端评测或工作台活动任务；副本数据库完整、复制的记忆已清空；两款只读预检 ready、turns_started=0；工作台继承隔离目录并可访问，原系统/包与日常数据前后校验一致；逐次试跑产生新结果目录，但新一轮正式录制前仍需刷新记忆副本。
- 实际结果：22:00（北京时间）准备成功；旧终端评测已停止、工作台无活动任务。私有 HOME 权限 0700；复制数据库 integrity_check 全通过、KylinBot memories=0，OpenClaw 已清空可观测状态并迁移 14 处副本配置路径。两款 preflight ready、turns_started=0；服务 PID 17361 的 KMB_AGENT_HOME 与 KMB_OPENCLAW_LOCAL=1 已核实，网页两款可选、开始按钮可用、状态空闲。日常 Agent 文件/数据库逻辑内容、系统版本文件和 0.2.2 已安装包前后校验一致。
- 记录：`runs/gui-video-prep-20261013/prepare-gui.py`、脱敏 `gui-ready.json` 及 `gui-ready.png`；VM 准备目录的同名脚本/状态与私有路径引用。准备脚本只复制/预检/重启工作台，不运行 Agent 回合；空 SQLite 的校验改为只读逻辑快照。私有凭据副本未放入仓库或发布材料，原系统 Hermes 仍保留、本轮独立副本不接入它。
- 文档：在 `docs/video-preparation-20261013.md` 追加网页操作、实际结果验收和试跑后刷新记忆说明，保留历史终端方案；旧包/旧录制稿/冻结材料未覆盖。尚未点击真实评测、录制视频或发送提交邮件。

## 2026-10-13 按最新准备流程重写演讲稿（完成）

- 意图：生成可直接照念、与镜头内单命令和当前案例解释对应的正式录制稿。
- 范围：重写 `docs/demo-script.md`；本台账；`runs/speech-refresh-20261013/` 中旧稿备份/编辑与排版检查；`dist/speech-latest-20261013/` 的纯口播 TXT/PDF、操作版 MD/PDF 与 manifest；同步 VM 准备目录及 GitHub 文档。
- 边界：稿件更新不启动正式评测、不制作视频、不预填现场分数，不改变原 openKylin 3.0、0.2.2 软件包、日常 Agent 数据或既有冻结材料。录屏使用负责人已有软件。
- 验收：镜头外/内清晰分开，正文不用临时数字或替换占位；完成后的口播只在实际有效运行完成后念；案例说明与禁词/目标键/观测边界一致；两份 PDF 文本与页面渲染检查通过。
- 实际结果：正文 8 段、900 汉字，独立 TXT/MD 和直接照读 PDF 1 页；操作与演讲稿 PDF 3 页。正文没有预填总分或占位；第 4 段后的等待与第 5 段起的 completed / valid / errors / strict 条件明确。全文 PDF 提取与正文一致，页面渲染检查通过，稿件与 manifest 位于 `dist/speech-latest-20261013/`。
- 同步：镜头内仅保留已部署 `run-on-camera.sh` 主入口，结果按终端本次目录定位，界面动作名称改为实际“打开”；旧稿备份和旧交付包保留。VM 准备目录新增最新稿件，仓库同步文档；不重新消耗 Agent 对话额度、不改系统或冻结软件包。

## 2026-10-13 视频镜头外准备（项目侧完成，正式视频由负责人录制）

- 意图：按负责人要求完成录制前可自动执行的准备，留下明确的镜头内操作入口。
- 范围：`docs/demo-script.md`、新增 `docs/video-preparation-20261013.md`、本台账；`runs/video-prep-20261013/`、`dist/video-ready-20261013/` 的准备脚本、状态与稿件；VM 普通用户工作区中的预检、录制目录和快捷入口，以及工作台浏览器临时选择。
- 边界：保持原 openKylin 3.0 与冻结 0.2.2 二进制，不改日常 Agent 记忆；不提前运行镜头内正式评测，不制作正式视频，不发送材料。设备读写测试只做短时空输出探测，不保存桌面/声音内容。
- 验收：两款 Agent 只读预检 ready、blocked 为空、turns_started=0；既有 0.2.2 有效预演 strict 通过并可在工作台回溯；桌面/音频源和编码工具可用；入口脚本语法与只读检查通过；录制说明明确剩余的人声、隐私画面与实际视频操作。
- 实际结果：20:36（北京时间）全部项目侧准备检查通过；新目录 `runs/video-real-20261013-203622/` 仅有预检，正式对话未开始。工作台两款参与者选择、六维预演、案例与证据入口已在浏览器逐项核对；旧搜索将清空以免误选预演。入口 `--check` 及后续 verifier 对既有预演实测通过，不消耗新的真实对话额度。
- 录屏调整：实机是 Wayland，旧 X11 捕获的单帧统计约 99.98% 黑色；只保存像素统计、不保存画面或声音。负责人说明有其他录屏软件，已停止替代工具调查与配置。麦克风源存在、未静音，人声回放和负责人录制画面仍须亲自检查。
- 材料与限制：生成镜头外清单、准备状态和镜头内单命令入口，当前系统 3.0 与冻结 0.2.2 不变。备课说明精确区分禁词规则、目标键检查、原始 conversation 持久化与不可观测模型状态；没有把旧预演冒充新现场结果。正式视频与作品提交未完成。
- 交付核对：20 项准备检查全通过；脚本语法、正常预演校验及无效批次拒绝检查通过。准备 PDF 2 页、分镜/口播 PDF 4 页均渲染检查通过；`dist/video-ready-20261013/` 提供稿件、已部署脚本、状态与界面截图，ZIP SHA-256 为 `6c64091c7047380ea8092a098273b353026d641ea13ec6e8d3ec7e63aeae1e55`。VM 准备目录同步稿件，浏览器预演筛选已清空，正式新目录仍未启动；本轮仅同步文档，不改发布标签或二进制。

## 2026-10-13 回答评分与 CLI 解析修复（完成，v0.2.2 已发布）

- 意图：修复视频深审复现的两个 P1 问题，补充语义回归，并交付修正后的可复现版本。
- 范围：`kmb/scoring.py`、`kmb/runner.py`、`kmb/agent_adapters/base.py`/`openclaw.py`、对应测试；版本与 CI、证据协议/审计/README/视频稿/发布说明；本台账及本轮 runs/dist 证据。
- 方法：普通回答检查默认末回合；boundary 的禁止回答检查保留全程，显式 `answer_scope` 或 `step` 可限定检查范围。JSON 只提取已识别的 assistant 文本，成功输出完整解析，元数据不能充作答复。
- 补充范围：`scripts/build_deb.sh` 的 CRLF 版本元数据兼容，以及 CI 默认版本构建回归；实机打包复现尾部 CR 字符导致合法 0.2.2 被误拒绝。
- 边界：只修项目软件，保持原 openKylin 3.0；历史证据和旧包不覆盖；真实复测使用临时 HOME 和空白记忆副本，不改日常 Agent 状态。
- 验收：先重现失败测试，再修复并跑全量单测、源码/安装包离线验收和新的真实双 Agent 批次；同步 GitHub、更新录制材料与版本/哈希。

- 实际结果：新增 18 项回归从失败到通过；Windows/openKylin 各 176 项通过；三项代码 CI success。项目包在原 openKylin 3.0 中完成 0.2.1→0.2.2 升级，安装后离线验收与工作台通过。第一批 KylinBot 网关错误使该侧无效并保留，第二批六案例两侧有效、错误 0、strict 通过（KylinBot 22.22、OpenClaw 30.56）。未覆盖完整 49 条真实矩阵，不宣称原生记忆或长期稳定。
- 文档：同步 README、当前环境、修复报告、历史审阅/完成度审计、作品介绍、录制稿、发布冻结和未发送邮件草稿；新材料位于 `dist/submission-0.2.2-20261013/`，旧包与证据保留。GitHub main 已同步，v0.2.2 冻结于 1c4aadf；main CI 三项全通过。最终 deb 安装后 18 项回归、离线验收与工作台全部通过；最终 wheel 在源码外安装验收通过。496 文件交付 manifest、源码审计和材料凭据扫描通过，四份 PDF 渲染检查通过（1/6/4/4 页）。新发布含 9 项附件，匿名下载全部成功并逐项匹配 SHA-256；旧 v0.2.1 标签/二进制保留。非视频 ZIP SHA-256 为 a5e2f32189f1feda1a6ac1e25ec1b6d25e81dac1a73dfd939a9e5603b863b8a0。

## 2026-10-13 视频方案深度复核（审阅与稿件完成，两个 P1 待修）

- 意图：依据当前 0.2.1 代码、openKylin 3.0 实机与命题 PDF，给出可照着操作和朗读的录制稿。
- 范围：`docs/demo-script.md`、`docs/video-review-20261013.md`、`docs/completion-audit-20261013.md` 的追加复核说明、README 的录制前提示、本台账，以及 `dist/video-script-20261013/` 中的 PDF/口播文本；旧稿和探针证据保存在本轮 `runs/` 中。
- 边界：保持原操作系统版本；不修改评分器、案例、Agent 适配器或已发布二进制；本轮只读预检不启动真实 Agent 对话、不消耗模型 Token，不录制或伪造视频。
- 验收：逐项核对 PDF 交付 e、六类 quick 案例、实际 UI 标签、隔离入口及报告路径；核实两款 Agent 预检阻断列表，检查文档命令参数、PDF 排版和 GitHub 同步。
- 实际结果：只读预检两款 Agent 均 ready、blocked 为空、turns_started=0；工作台成功载入历史双 Agent comparison，读取 quick-update 的 7 条事件。语义探针复现更新误扣分（2/3）、最终回答错误却通过（1.0）及 CLI 正确答复被解析为 edit，证据见 `runs/video-script-review-20261013/review-probes.json`。
- 稿件：分镜与实际操作、约 828 汉字照读口播、失败/通过案例分支和录后清单已完成；PDF 4 页、审阅 PDF 3 页，页面渲染检查通过。
- 当前边界：两个 P1 未作代码修复，本次未跑新的付费真实评分；README 与先前完成度审计已追加修正项，旧材料和原始分数保留。正式录制应先修复并使用新的真实批次。

## 协作原则（强制）

1. **本文件职责**  
   项目修改台账：登记「已经修改的」与「将要修改的」；写清改了哪里；供其他 AI 核对。

2. **改完必更新（强制）**  
   任何 AI / 协作会话，**只要对本仓库有任何写入修改**（代码、文档、配置、脚本、测试），**在向用户交付/结束前必须更新本文件**。  
   - 将本次「计划中」更新为实际状态，并写清**改动点路径**。  
   - 若只计划未执行，只维护「计划中」。  
   - **禁止**交付时台账仍停留在改动前状态。  
   - 无仓库写入的任务可标注「本次不适用」，但不得删除既有条目。

3. **先登记再动手**  
   动手前写「计划中」（意图、路径、边界、验收）；紧急修复可在同一交付内补登记，不得省略。

4. **只改已登记范围**  
   未写明的模块默认未授权，不得擅自扩大。

5. **需求与实现分离**  
   「意图」= 目标；「改动点」= 文件/函数/选择器级落点。

6. **可核对**  
   验收写命令、现象或截图路径；禁止只写「更好了」。

7. **不替代其他文档**  
   本台账 ≠ `CHANGELOG.md` ≠ `docs/release-freeze.md` ≠ `tasks/todo.md`。

8. **历史只增不删**  
   作废用状态标记，不覆盖原文。

9. **表述边界强制**  
   登记 Agent / 配置 / 评测相关改动时必须按「表述边界」分类，禁止夸大（见下节）。

---

## 表述边界（强制）

### 两层能力

**A. 只为了「能调用 API」——通常够用：**

- `base_url`（如 `https://api.deepseek.com`）
- API Key（**只放环境变量，不进仓库**）
- `model`（如 `grok-4.6` / `deepseek-flash`）
- 接口路径（一般 `/chat/completions`）

可跑通 HTTP 适配器，得到对比和雷达图。

**B. 为了「按文档评长期记忆」——只有 key + base_url 不够：**

PDF/文档要求基于**真实运行证据**自动评分，并覆盖六类记忆能力。纯 API 只能看到回答文本：

- 看不到是否真的 **写入 / 更新 / 调用 / 抑制** 记忆
- 当前真实 HTTP 轨道 `native_memory_events=0`
- **普通文本不能推断成记忆写入或读取**

还需要至少一种**可观测证据**：

| 方式 | 说明 |
|------|------|
| 包装层 / memory controller | 外部记忆状态机 + 沙箱动作，事件标 `source=wrapper` |
| 进程 Agent | 子进程按协议吐 JSONL（如 `kylinbot-process`） |
| Agent 原生导出 | 对方给出记忆/工具轨迹，映射为统一 `EvidenceEvent` |

### 结论表

| 目标 | 只给 key + base_url？ |
|------|------------------------|
| 连通、跑通 CLI、出雷达图 | 可以 |
| 符合「长期记忆自动化评测」验收 | **不行**，还差记忆证据 |

文档里的「导入不同智能体配置」= **配置接入 + 证据协议**；Key/Base URL 只是配置接入的第一步。

### 登记规则

- 凡登记涉及 Agent / API / 评测接入的条目，必须标明属于：**仅连通** 还是 **具备可观测记忆证据**（并写 source 类型）。
- 禁止：仅有 key + base_url 时写成「已验收长期记忆评测」或「已证明模型原生长期记忆」。
- 雷达图 / CLI 跑通不能替代证据验收表述。

---

## 状态与模板

状态：`计划中` | `进行中` | `已完成` | `作废` | `回滚`

```markdown
### [YYYY-MM-DD] 简短标题
- **状态**: 计划中 | 进行中 | 已完成 | 作废 | 回滚
- **意图**: 一句话
- **改动点**:
  - `路径/文件` — 改了什么
- **接入层级**（若涉及 Agent/API/评测）: 仅连通 | 具备可观测证据（source=…） | 不适用
- **保留/禁止**: 可选
- **验收**: 如何确认
- **本次是否已同步本台账**: 是 | 否 | 不适用（有仓库写入时交付前必须为「是」）
```

---

## 台账条目（只增不删）

### [2026-09-16] 建立修改台账 docs/mimo.md
- **状态**: 已完成
- **意图**: 固定协作登记入口，强制改完必更新与表述边界
- **改动点**:
  - `docs/mimo.md` — 新建/更新本文件（原则、表述边界、模板、历史）
- **接入层级**: 不适用
- **保留/禁止**: 不改业务代码；不建 `AGENTS.md`；不改 CHANGELOG / release-freeze / todo
- **验收**: 本文件存在且含文首强制原则与表述边界专节
- **本次是否已同步本台账**: 是

### [2026-09-16] 本会话既往写入（回溯登记）
- **状态**: 已完成
- **意图**: 将本会话已落盘的仓库修改登记入台账；后续交付仍须先写「计划中」再动手
- **改动点**:
  - `kmb/web/styles.css` — UI Token/布局/边界/下拉；Codex++ 对齐深色工作台
  - `kmb/web/index.html` — 侧栏分组、Topbar（标题+副标题+状态芯片）
  - `kmb/web/app.js` — 页面 chrome、自定义 select（fixed 浮层）、Provider 列表等
  - `kmb/models.py` — 证据来源增加 `process`（系统级分类）
  - `suites/core-zh-expanded.yaml` — 新建，六类扩展 18 案例
  - `suites/adversarial/extended.yaml` — 新建，冲突/相近/噪声/敏感/跨任务各 3 条
  - `scripts/openkylin_ecosystem_agent.py` — 新建，进程适配器
  - `configs/agent-kylinbot-process.yaml` — 新建，command 配置
  - `scripts/run_offline_demo.sh` — 新建/更新，无凭据双 Agent 对比 demo
  - `scripts/register_openai_agent.py` — 新建，按 key 环境变量 + base_url + model 生成包装配置（脚本已写；CLI 子命令是否接线：待核实）
  - `docs/judge-reproduction-card.md` — 新建/更新评委复现卡
  - `tasks/todo.md` / `README.md` / `docs/release-freeze.md` — 口径对齐（本机 P1；实机后置）
- **接入层级**:
  - `kylinbot-process`：具备可观测证据（source=process，系统级，非模型原生记忆）
  - reference/flawed：离线基线（source=simulated）
- **保留/禁止**: 密钥不入库；不夸大「已验收长期记忆」
- **验收**: 曾通过 unittest 59、`run_offline_demo` 退出码 0 等（以当时交付说明为准）
- **本次是否已同步本台账**: 是

### [2026-09-16] 真实 API 连通与核心套件对比（运行记录）
- **状态**: 已完成
- **意图**: 使用环境变量密钥做本机真实双 Agent 对比
- **改动点**:
  - 运行目录 `runs/real-api-20260916/` — Grok `grok-4.6` vs DeepSeek（`deepseek-v4-flash`→映射 `deepseek-flash`），seed 42
  - 密钥仅进程环境变量，未写入仓库
- **接入层级**: 仅连通（HTTP 文本可观测；`native_memory_events=0`，非长期记忆验收）
- **验收**: `verify_run --strict` 两侧通过；`comparison.html`/雷达存在；结果内无密钥
- **本次是否已同步本台账**: 是

### [2026-09-16] 工作台新增 API 配置自动生成三件套
- **状态**: 已完成
- **意图**: 提交 profile 后写出 http / memory_controller / memory_disabled 三份 YAML，与 `scripts/register_openai_agent.py` 对齐
- **改动点**:
  - `kmb/workbench.py` — `create_config`：三路径预检、原子写三份、失败回滚；响应含 `configs`/`generated`/`note`
  - `kmb/web/app.js` — 成功提示列出三件套与「http 仅连通；memory/no-memory 包装轨」边界
  - `tests/test_workbench.py` — 断言三文件与 type、generated 类型集合
  - `docs/workbench.md` — 三件套表与接入层级
  - `docs/mimo.md` — 本条
- **接入层级**: http=仅连通；memory_controller/no-memory=具备可观测证据（source=wrapper）
- **保留/禁止**: 不写密钥；不覆盖已有文件
- **验收**: `python -m unittest discover -s tests` 59 OK；HTTP POST `/api/configs` 返回 201 且三份 YAML type 正确；重复 POST 409；烟测文件已删
- **本次是否已同步本台账**: 是

### [2026-09-16] Grok-memory × DeepSeek-memory 包装轨真实对比（core-zh）
- **状态**: 已完成
- **意图**: 真实双 API + 包装层跑核心六类套件并归档
- **改动点**:
  - 运行目录 `runs/real-api-wrapper-20260916/results/` — comparison、两侧 result/evidence/雷达
  - 旁路 `runs/real-api-wrapper-20260916/compare.stdout.log`、`cli.exitcode`（0）
- **接入层级**: 具备可观测证据（source=wrapper；native_memory_events=0；mode=system_level_wrapper_assisted）
- **保留/禁止**: 不得写成「模型原生长期记忆已验证」；密钥仅环境变量
- **验收**: compare 退出码 0；两侧 strict 通过（各 72 事件）；wrapper_memory_events=13；总分均 86.11；归档无明文密钥
- **本次是否已同步本台账**: 是

### [2026-09-16] CLI register-agent 接线（与脚本共用实现）
- **状态**: 已完成
- **意图**: `python -m kmb.cli register-agent` 生成三件套，避免与脚本两套逻辑
- **改动点**:
  - `kmb/register.py` — 新建公共实现
  - `kmb/cli.py` — 新增 register-agent
  - `scripts/register_openai_agent.py` — 调用 kmb.register
  - `tests/test_register_agent.py` — 5 项用例
  - `README.md` / `docs/workbench.md`
- **接入层级**: 不适用（注册工具）
- **验收**: `--help` 可用；全量 unittest 64 OK
- **本次是否已同步本台账**: 是

### [2026-09-16] A+B 原生/可观测记忆对比设计 + R0 口径降级
- **状态**: 已完成
- **意图**: 文档化 A/B/C 轨、门禁、选型、导出规格、防送分、B 轨机制、runbook、并排模板；包装叙事降为 C 轨
- **改动点**:
  - `docs/native-memory-compare.md` — 新建完整设计与门禁；§11 当前 A=`candidate-pending`，正式主结论未开放
  - `README.md` — R0：包装/三件套为 C 轨，主结论走 A+B 门禁
  - `docs/workbench.md` / `docs/judge-reproduction-card.md` — R0 与标准句
  - `tasks/todo.md` — A+B 门禁任务与 R0 说明
  - `docs/release-freeze.md` — wrapper runs 保留为 C 轨，非主结论
  - `docs/mimo.md` — 本条
- **接入层级**: C 轨 wrapper 保留；A/B 门禁前不写 ready
- **保留/禁止**: 未删 wrapper/register/no-memory/configs/历史 runs；未伪造 A 轨 Agent 或 native_memory_events>0
- **验收**: 设计文档完整；相关配置文件仍在；`unittest discover` 退出码 0
- **本次是否已同步本台账**: 是

### [2026-09-16] B 轨实现：两套记忆模块 + 工具决策 + 证据导出
- **状态**: 已完成
- **意图**: 落地 B 轨骨架；决策归工具层；甲/乙策略可区分
- **改动点**:
  - `kmb/memory_modules.py` — ExactKVMemory / SimilarityMemory
  - `kmb/agents.py` — MemoryToolAgent、DecisionTextBackend、type `memory_tool`
  - `kmb/models.py` — source `memory_layer`
  - `configs/agent-b-memory-kv.yaml`、`configs/agent-b-memory-similar.yaml`
  - `suites/native/decision-core.yaml` — 人话套件
  - `tests/test_memory_tool.py` — 模块/Agent/配置/套件用例
  - `docs/native-memory-compare.md` §11 — B 骨架状态
- **接入层级**: B 骨架（memory_layer 可观测）；非 A/B 正式主结论 ready
- **保留/禁止**: wrapper 未删；未按 suite YAML 预写记忆库
- **验收**: unittest 通过；compare 冒烟 KV 91.67 vs Similar 100.0（边界维可区分）；`memory_layer` 事件存在
- **本次是否已同步本台账**: 是

### [2026-09-18] 迁入 openKylin VM + 无 API 验收
- **状态**: 已完成（含 1 项 unittest 平台失败，已如实记录）
- **意图**: Windows 仓库同步到 VM 数据盘新目录，install_local + 探针/单测/validate（无云 API）
- **改动点**:
  - 远端 `REMOTE_ROOT=/data/usershare/kylin-memory-bench-20260918`（`/dev/sda4` → `/data`，非系统盘）
  - 打包 `kmb-src-20260918.tar.gz`，SHA256 `926AF68E7BA50A8918530D593A60D39FDBD2F36A63A890B60932B53C11399E23`
  - 排除 `runs/`、`.venv*`、`__pycache__`、密钥
  - 宿主归档 `docs/migrate-openkylin-20260918/`（含 SUMMARY.md 与日志）
  - `tasks/todo.md` — 迁入无 API 验收说明
  - `docs/mimo.md` — 本条
- **接入层级**: 不适用（迁移验收）；非真实 API / 非 A/B 主结论
- **SSH（脱敏）**: `Cisyam@192.168.182.129:2222`，密钥 `~/.ssh/openkylin_vm_ed25519`
- **验收退出码**:
  - env_probe --require-openkylin：**0**，`checks.openkylin.ok=true`（openKylin 2.0 SP2）
  - install_local.sh：**0**，`.kmb-venv` 在项目内，import kmb 成功
  - validate --strict core-zh：**0**
  - unittest：**1**（71 项，1 失败：`test_safe_executor_records_real_and_unexecuted_boundaries`，posix 期望 recalls>=3 实测 2，平台/KARE 场景）
- **保留/禁止**: 未覆盖历史 validation 目录；未迁 runs/；未调用云 API；未删 wrapper
- **本次是否已同步本台账**: 是

### [2026-09-18] Token Center 配置模板 + 生态 Agent 导出规格
- **状态**: 已完成
- **意图**: openKylin Token Center http 模板；KylinBot/OpenClaw command 导出字段与门禁口径
- **改动点**:
  - `configs/agent-openkylin-token.yaml` — http 模板，无密钥，`OPENKYLIN_TOKEN_API_KEY`
  - `configs/agent-kylinbot-command.yaml.example` / `agent-openclaw-command.yaml.example` — exporter 占位
  - `docs/openkylin-token-center.md` — URL/模型/申领/额度未公开/run 示例/调研链接
  - `docs/ecosystem-agent-export.md` — 级别对照、command 职责、字段清单、门禁、skills/MCP 口径
  - `docs/evidence-protocol.md` / `README.md` — 交叉引用
  - `tests/test_openkylin_ecosystem_configs.py`
  - `docs/mimo.md` — 本条
- **接入层级**: Token http=仅连通设计；command 包装=exporter-pending（stand-in 未删）
- **调研**: `research/openkylin-agent-ecosystem/REPORT.md`
- **保留/禁止**: 未实测 Token Center/KylinBot；未删 wrapper/stand-in；无密钥入库；未编造额度
- **验收**: 相关 unittest 通过；discover 退出码 0
- **本次是否已同步本台账**: 是

### [2026-09-18] openKylin 3.0 AgentOS VM 安装与安装级验收
- **状态**: 作废/阻塞（安装未完成）
- **意图**: 核对 ISO/VM → 启动 → 安装 → 客户机验收（不迁项目）
- **改动点**:
  - `D:\openKylin-VM-3.0-AgentOS\openKylin-3.0-AgentOS.vmx` — 修正错误路径（`D:\\\\`→`D:\`）、`scsi-hardDisk`、固件 `efi`→`bios`；备份 `.bak-paths`
  - `docs/openkylin-3.0-vm-setup-20260918.md` — 阻塞与解除步骤
  - `docs/mimo.md` — 本条
- **ISO**: 大小 7435438080，CD001 已核验
- **硬件配置**: 4 vCPU / 8GB / 系统盘 80GB sparse / 数据盘 60GB sparse（未安装、未挂载验收）
- **验收结果**: ISO/VMX 文件就绪；**power-on 失败**（日志 `IOPL_Init: Hyper-V detected by CPUID`；`vmrun list` 仍为 0）
- **SSH**: 无（系统未装成）
- **保留/禁止**: 未迁项目；未把 2.0 冒充 3.0；无密码/私钥入库
- **口径**: **仅**配置校正；**不得**称 3.0 安装完成或评测已验收
- **后续**: 管理员关闭 Hyper-V/VirtualMachinePlatform 并重启后，再执行 `vmrun start ... gui` 与安装向导
- **本次是否已同步本台账**: 是

### [2026-09-18] openKylin 3.0 AgentOS VM 安装与安装级验收（续）
- **状态**: 进行中（power-on 成功；GUI 安装待人工完成）
- **意图**: 解除 Hyper-V/vmx 阻塞并启动 3.0 安装环境
- **改动点**:
  - 关闭 VirtualMachinePlatform / HypervisorPlatform（用户管理员操作 + 重启）
  - `openKylin-3.0-AgentOS.vmx` — 路径修复、重建 vmdk、**virtualHW 18**、2 vCPU/4GB、`guestOS=ubuntu-64`、单系统盘启动
  - `docs/openkylin-3.0-vm-setup-20260918.md` — 状态更新
- **验收**: `vmrun list`=1；日志显示 BIOS + 80G SCSI + 720x400；**尚未**进入已安装系统
- **口径**: 仅「安装环境已启动」；未迁项目、未跑评测
- **本次是否已同步本台账**: 是

### [2026-09-18] 删除本机 openKylin 3.0 下载与虚拟机
- **状态**: 已完成
- **意图**: 清除本任务下载/创建的 3.0 安装介质与 VM 配置
- **改动点**:
  - 删除 `D:\openKylin-VM-3.0-AgentOS\`（vmx、vmdk、install.iso 副本、日志等）
  - 删除 `D:\ISOs\openKylin-Desktop-V3.0-AgentOS-20260905-x86_64.iso`
- **保留/禁止**: 未删除宿主项目仓库；未改业务代码；历史 2.0 目录此前已不存在
- **验收**: 删除后 `Test-Path` VM 目录为 False；`E:\上海开源软件应用创新大赛\README.md` 仍存在
- **口径**: 3.0 安装验收未完成；本次仅为介质/VM 清理，不计入「已验证」
- **本次是否已同步本台账**: 是

---

## 计划中

### [2026-09-23] 真实 Agent 快速对比隔离与赛题非视频验收
- **状态**: 已完成（非视频交付；视频与许可证仍后置）
- **意图**: 在不污染用户日常记忆的临时 Agent HOME 中，用重新可用的 Token 复测 KylinBot/OpenClaw 六维快速对比，并按 PDF 交付项校正完成口径。
- **改动点**:
  - `kmb/agent_adapters/openclaw.py` — 为每个案例生成独立会话键；支持显式本地隔离模式并将子进程 HOME 指向适配器 HOME
  - `tests/test_agent_adapters.py` — 验证会话隔离、临时 HOME 与本地模式
  - `docs/requirements-traceability.md`、`docs/release-freeze.md`、`tasks/todo.md`、`docs/Zcode-agent对比方案.md`、`docs/mimo.md` — 按新鲜验证与真实 Agent 结果更新状态
- **接入层级**: KylinBot/OpenClaw 真实系统级 Agent 行为，可观测记忆事件；不声称模型原生记忆
- **保留/禁止**: 使用空白临时记忆库与副本配置；不修改原 Agent 记忆/配置；Token 不回显、不入库
- **验收**: 全量 104+ unittest、隔离 VM 六案例双 Agent quick-compare、各结果 `verify_run.py --strict`；证据路径写入追踪清单
- **结果**: VM `/home/Cisyam/kmb-agent-validation-20260923/runs/quick-compare-isolated-20260924/`；KylinBot `63.89`、OpenClaw `13.89`；两侧 `score_valid=true`，strict 退出码 0（51/34 条证据）；新 Token `/v1/models` 返回 200，未再出现 402
- **边界**: 结果为系统级外部记忆/动作控制器行为，`native_memory_events=0`；Hermes 本轮未重跑，KylinAgent 仍不可自动驱动；视频与 LICENSE 仍后置
- **本次是否已同步本台账**: 是

### [2026-09-18] 测试修复 + A 轨门禁口径 + KylinBot 导出器（历史快照，已由 2026-09-22 门禁条目替代）
- **状态**: 已完成（门禁实验已跑；案例得分与 strict 限制如实记录）
- **意图**: 修 test_memory_tool；A 门禁改为 Agent 自有可观测记忆事件；实现 KylinBot 导出器
- **改动点**:
  - `docs/native-memory-compare.md` — §2 门禁口径修正 + §2b 门禁计数 + §11 实验状态
  - `tests/test_memory_tool.py` — 重写（KV/相似/B 骨架/门禁计数）
  - `scripts/export_kylinbot_evidence.py` — brain.db → kmb_evidence JSONL
  - `scripts/kylinbot_command_wrapper.py` — CommandAgent 协议包装
  - `configs/agent-kylinbot-command.yaml` — command 指向导出器（保留 stand-in 配置）
  - `suites/native/kylinbot-gate.yaml` — 单案例门禁套件
  - `kmb/agents.py` — CommandAgent subprocess `errors=replace`（Windows UTF-8）
  - `docs/mimo.md` — 本条
- **门禁口径**: A 轨 = Agent 自有记忆事件（`source=process/memory_layer/wrapper` 的 memory_*）；**不要求** `native_memory_events>0`；原生轨单独记录
- **A 轨实验**:
  - VM openKylin 3.0 `192.168.141.128:22`；`brain.db` 真实拷贝 `_migrate_stage/kylinbot-brain.db`
  - 历史实现曾把全库行计为 **agent_owned_memory_events=3**；2026-09-21 复核后已撤销该口径，当前 case 只保留精确键的 snapshot recall
  - `native_memory_events=0`
  - overall 0.0：DB 键 `project_codename/Atals` vs 案例 `project=Atlas`（烟测数据，如实 omission）
  - `verify --strict` 失败：单案例套件仅 retention（非导出器伪造）
- **当时标签**: `A: snapshot-only / gate-pending`；`B: skeleton-only`；`C: wrapper-only`
- **git**: 已 `git add` 关键文件；**未 commit**（待负责人授权）
- **保留/禁止**: stand-in/wrapper 未删；无密钥入库；未宣称四 Agent 正式评测完成
- **验收**: 2026-09-21 `unittest discover` **78 tests OK**；VM `python3` + 真实 `brain.db` 快照烟测通过，正式会话门禁未通过
- **本次是否已同步本台账**: 是



---

### [2026-09-19] 补录本轮台账并清理 review 烟测产物
- **状态**: 已完成
- **意图**: 修复本次审阅发现的台账缺失：将 2026-09-19 会话写入同步到 docs/mimo.md，并清理 review 过程产生的临时配置。
- **改动点**:
  - docs/mimo.md — 补录本轮条目并更新为已交付
  - configs/agent-openrouter*.yaml — 删除 review 烟测产物
- **接入层级**: 不适用
- **保留/禁止**: 不删除既有台账历史；不触碰其他业务文件
- **验收**: git status --short 中不再出现 gent-openrouter*.yaml；docs/mimo.md 含本轮登记
- **本次是否已同步本台账**: 是







### [2026-09-22] KylinBot 真实 CLI 门禁通过与证据归档
- **状态**: 已完成（A 轨最小门禁通过）
- **意图**: 在已启动的 openKylin 3.0 VM 中核对真实会话驱动，区分快照/stand-in 与当前 Agent 自有记忆事件。
- **改动点**:
  - `scripts/kylinbot_command_agent.py` — 逐轮调用 `kylin-bot agent --message`，复用临时 session state，读取 `brain.db` 前后差异并输出真实事件
  - `configs/agent-kylinbot-command.yaml` — 从只读快照 exporter 切换为真实 CLI 驱动
  - `suites/native/kylinbot-gate.yaml` — 自然语言 remember/recall 门禁
  - `README.md`、`docs/Zcode-agent对比方案.md`、`docs/native-memory-compare.md`、`docs/ecosystem-agent-export.md` — 更新当前门禁口径
- **VM**: openKylin 3.0 (huanghe)，`Cisyam@192.168.141.128:22`；`kylin-bot` 可执行；用户级 OpenClaw 与 Kylin-Agent runtime 服务 `active`。
- **结果**: `runs/kylinbot-gate-20260922/result.json`，`overall=100.0`；`evidence.jsonl` 含 `source=process` 的 `memory_write`、精确 `memory_recall` 命中 Atlas 和两轮 assistant 输出。
- **观测口径**: `system_level_wrapper_assisted`，`wrapper_memory_events=4`，`native_memory_events=0`；可标记 `A: ready(agent-memory-observable)`，不可宣称模型原生记忆。
- **清理**: 仅删除本轮新增 `benchmark_alias` 与两条关联 `user_msg_*`；既有烟测数据保留。
- **回归**: `.venv-kmb-system\Scripts\python.exe -m unittest discover -s tests -v`，**83 tests OK**；`verify_run.py runs/kylinbot-gate-20260922` 退出码 0。该单案例门禁的 `--strict` 按设计因缺少其余五个维度退出码 2。
- **本次是否已同步本台账**: 是

### [2026-09-22] 四 Agent 快速对比代码整改与 openKylin 3.0 验收
- **状态**: 已完成（代码、本地回归、VM 快速对比）
- **意图**: 将用户流程收敛为“发现已有 Agent → 选择两个 → 一次点击”，保留证据边界，不自动下载 Agent。
- **代码**: 新增 `kmb/agent_registry.py`、四个原生 Agent 适配器、`kmb/quick_compare.py`、`suites/quick.yaml`；工作台新增 `GET /api/agents`、`POST /api/quick-compare` 和总览页快速对比面板。
- **本地回归**: `.venv-kmb-system\\Scripts\\python.exe -m unittest discover -s tests -v`，**94 tests OK**；`node --check kmb/web/app.js` 通过；快速套件严格校验通过。
- **VM**: openKylin 3.0 (huanghe)，`Cisyam@192.168.141.128:22`；KylinBot、Hermes、OpenClaw 自动适配可用；KylinAgent 已安装但因 GUI/服务级证据限制标记为不可自动驱动。
- **VM 结果**: `~/kmb-quick-compare-20260922/runs/openkylin-validation-20260922/quick-compare/kylinbot-hermes/` 与 `kylinbot-openclaw/`；两组均生成六案例双 Agent结果、`comparison.*`、`quick-compare.json`，四份 `result/evidence` 通过 `scripts/verify_run.py --strict`。
- **观测结论**: KylinBot + Hermes 总分分别 `63.89`、`22.22`；KylinBot + OpenClaw 分别 `41.67`、`27.78`。失败项保留为真实 omission/stale_update/confusion/runtime_error/erroneous_reuse，不把网关账单拒绝或模型文本自述计为通过。
- **安全**: 未复制 Agent 数据库、密钥或原始凭据到仓库；VM 结果目录位于 `runs/`（gitignored），只记录脱敏路径和摘要。
- **本次是否已同步本台账**: 是


