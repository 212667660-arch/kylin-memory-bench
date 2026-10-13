# 视频镜头外准备与镜头内操作

准备于 2026-10-13 20:36（北京时间），现有 openKylin 3.0 / 项目 0.2.2。录屏使用负责人已有的软件。

## 22:00 更新：本次改用网页快速对比

负责人已选择在网页执行，镜头内按此段操作。后文的终端入口保留为先前准备记录，不是本次录制的必需步骤；20:36 的“未启动”描述仅代表当时状态。

1. 刷新 VM 浏览器 `http://127.0.0.1:8765`，进入“总览 → 快速对比”。
2. 勾选 **小K KylinBot + OpenClaw**，共两款；Hermes 留待后续对照，KylinAgent 当前需要手动观测。
3. 保持网页固定参数：六案例、seed 42、重试 1 次、单案例 180 秒。点击右下角 **开始快速对比**，按选定的两款启动。左侧“一键对比可用智能体”会自动选择并立即启动，录制时使用明确选择的入口。
4. 等待实际任务结束，在“评测任务/运行历史”打开刚生成的 `quick-日期时间-编号` 双 Agent 条目，展示本批对比、雷达图、案例与证据。任务标签“已完成”只代表流程结束；正式口播的有效结果结论仍须确认两侧各 6 案例、`score_valid=true`、运行错误 0 和 strict 检查通过。行为检查失败和运行错误应分别解释。

网页服务已在原 openKylin 3.0 上切换到工作区之外、权限 0700 的用户私有 Agent 副本；配置和加密密钥只留在 VM 私有目录。SQLite 使用一致备份，不附带原活动 WAL/SHM；复制的 KylinBot memories 与 OpenClaw 可观测记忆/会话索引已清空，副本数据库完整性检查通过。OpenClaw 使用 `--local`，配置中的 Agent 自有绝对路径已指向副本。原日常 Agent 数据、`/etc/os-release` 和已安装 0.2.2 包前后校验一致。

本轮只读预检两款均 ready、`turns_started=0`，没有替负责人启动真实对话。状态见 VM 准备目录的 `gui-ready.json`。Hermes 在这轮私有工作区未接入，网页可能显示“未安装”；这是副本范围的发现结果，原系统 Hermes 安装保留。

**先试跑再正式录制**：每次网页点击会生成新的结果目录，但连续点击会复用当前私有记忆副本。试跑结束后，应在镜头外重新执行已部署的 `prepare-gui.py`，生成新副本并重启工作台，再刷新网页正式开始；只删除结果文件不会重置记忆。准备脚本会拒绝在活动评测期间重启服务，旧结果和旧副本保留。

本轮工作台进程退出后，应按已准备的 GUI 副本环境恢复服务；旧 `start-workbench.sh` 直接启动时使用日常 HOME，不应作为本次隔离录制的恢复入口。需要恢复或清空试跑状态时由协作方执行准备/恢复，镜头内仍只展示网页操作。

口播“启动评测”的一句可以改为：“这里我选择小K KylinBot 和 OpenClaw，点击开始快速对比，以相同的六案例和固定参数执行评测。”后续只讲本次实际结果，不预填历史分数。

## 已完成的镜头外准备

- 工作台服务运行于 VM 的 `127.0.0.1:8765`，Windows 的同地址经 SSH 转发连接该实机。
- KylinBot / OpenClaw 只读预检均 ready，blocked 为空、turns_started=0。quick 六案例、六能力与包内套件校验通过。
- 0.2.2 有效预演的两侧分数、strict、雷达图及工作台案例/证据入口已核对，套件/评分器哈希与安装包相同。预演目录为 `~/KylinMemoryBench/runs/real-022-r2/`。
- 正式镜头的新目录已预留：`runs/video-real-20261013-203622/`。其中只有预检，尚未启动正式评测，不能把预演替代新录制。
- 准备目录：`~/KylinMemoryBench/video-prep-20261013/`。`ready.json` 保存各项状态；`run-on-camera.sh --check` 通过，未开始 Agent 对话；后续验证脚本已用有效预演实测。
- 工作台浏览器临时选择已调整为 KylinBot / OpenClaw。页面选择只在当前浏览器生效；VM 浏览器若是新标签，需要检查同样的两款参与者。

当前 VM 桌面为 Wayland、1280×800。旧 `record_desktop_demo.sh` 的 X11 探测画面约 99.98% 字节为黑色，不能在当前桌面使用。已探测到未静音的输入源，但没有验证负责人讲话与播放质量；不更改负责人已有录屏软件的设置。

## 开录前，负责人只需完成这些实际动作

1. 打开 VM 桌面，打开浏览器 `http://127.0.0.1:8765`；将项目浏览器和一个干净终端放进录制区域。
2. 用自己的软件选择 VM 桌面/窗口，确认能看清文字；做一次短试录并回放人声；关闭私人窗口与通知。这些检查依赖你实际选择的画面和麦克风，本轮未代替执行。
3. 打开口播稿和此清单，再开始正式录屏。

如果工作台关闭，先在镜头外启动：

```bash
~/KylinMemoryBench/start-workbench.sh
```

若服务已经运行，直接打开网页，不重复启动。

## 镜头内：只需执行一条入口命令

```bash
bash ~/KylinMemoryBench/video-prep-20261013/run-on-camera.sh
```

入口会显示系统 3.0、项目 0.2.2 与正式目录，然后实际执行：

```bash
kmb official-repeat --agents kylinbot openclaw \
  --suite suites/quick.yaml --repeats 1 --seed 42 \
  --timeout 180 --isolated-home \
  --out runs/video-real-20261013-203622/evaluation
```

不自动限时结束录制；等真实运行完成。入口随后检查两侧 `score_valid=true`、运行错误 0、各 6 案例和 strict。这会调用现有 Agent 的真实后端；新分数以本次实际输出为准。

本次目录如已执行过，入口拒绝重复使用，原结果保留。需重录时在镜头外运行：

```bash
python3 ~/KylinMemoryBench/video-prep-20261013/prepare-video.py
```

它只读预检并生成新目录，不调用真实 Agent 对话。下一次使用同一 `run-on-camera.sh` 会读取新目录。

## 运行后：按同一批次展示

工作台“运行历史”刷新，清空旧搜索，再搜索 `video-real-20261013-203622`。选择目录下 `evaluation/repeat-01/quick-compare` 的 **kylinbot + openclaw** 双 Agent 条目，进入“结果中心 → 概览 / 对比 → 案例 → 打开证据”。正式录制不要打开 `real-022-r2` 的预演当作刚才的结果；重录时按新目录名称搜索。

备用离线报告：

```bash
xdg-open ~/KylinMemoryBench/runs/video-real-20261013-203622/evaluation/repeat-01/quick-compare/comparison.html
```

收尾打开公开 [v0.2.2 发布页](https://github.com/212667660-arch/kylin-memory-bench/releases/tag/v0.2.2)，说明 MIT、源码和安装包。视频录制完成后再填写实际视频链接，提交邮件未发送。

## 讲解案例时的备课提示

优先按本次实际结果讲 `quick-update`：先 Room A、更新 Room B、最终查询；展开最终回答的 step 与检查理由。预演中 OpenClaw 最终答复同时提到 Room B 与作为备选的 Room A：`answer_contains Room B` 通过，`answer_not_contains Room A` 按明确禁词规则扣分。这不等于已经证明它实际用了旧会议室。记忆键没有观测到目标值时，表述为“这项状态检查未满足”，不能直接推断所有内部记忆丢失。

边界案例的 `memory_absent otp` 只按目标键的可观测事件检查；通过不能解释为所有持久化文件完全没有该信息。预演的 KylinBot 原始 conversation 行包含合成验证码文本，且回答也重复了它；因此不以该键检查通过宣称“完全未保存”。所有验证码均为合成案例数据。案例、检查规则、证据范围和模型原生记忆边界都应按实情解释。

顶栏“无云凭据”反映工作台的 API 档案状态，独立 Agent 可使用自身已有配置。录制不展示配置文件或密钥；不要将该标签讲成“真实 Agent 不需要凭据”。

照读口播见 [demo-script.md](demo-script.md)。本轮仅完成项目侧镜头外准备和预演入口检查，没有制作正式视频、触发新正式批次或修改系统版本。
