# KylinMemoryBench 视频分镜与口播稿

版本：2026-10-13。主场景：现有 openKylin 3.0 桌面。建议讲解与操作约 4 分 50 秒，真实 Agent 的网络等待另计。

**使用前提：先修正 [深度审阅](video-review-20261013.md) 中两个 P1 评分/解析问题，并以修正后新批次录制。** 本稿不预填总分；不是已完成的视频。旧 10 月 5 日稿已备份到本轮 runs，旧视频操作和“官方满分”说法不再沿用。

## 你应该录哪些功能

必录六件事：**openKylin 3.0 环境；KylinBot 与 OpenClaw 两款真实 Agent；六类案例与同一评测参数；一次隔离评测从启动到完成；双 Agent 六维雷达图；至少一个案例的检查理由与证据。**

收尾再展示 GitHub、MIT 和 `.deb`。无需把 API 配置填写、每个菜单、四款 Agent、安装卸载全过程都录一遍。API 接入和离线模拟对照属于补充功能，不能代替真实双 Agent 的主流程。

## 分镜顺序

| 参考时段 | 画面与操作 | 必须让评委看见 |
|---|---|---|
| 0:00–0:20 | openKylin 桌面与项目工作台，口播项目用途 | 项目解决什么问题 |
| 0:20–0:45 | 终端系统/包版本；工作台“智能体”页 | 系统 3.0；项目版本为实际安装值；两款真实参与者 |
| 0:45–1:15 | “新建评测”选 quick 套件查看摘要；说明六类与会议室更新例 | 测试内容具体，共享参数一致 |
| 1:15–2:00，加实际等待 | 在终端启动六案例隔离评测，等待完成 | 真实运行、同一运行目录、两款 Agent 和完整六案例 |
| 2:00–2:55 | 工作台“运行历史”选本次 comparison，“查看”进入“结果中心” | 两侧名称、六维表、雷达图、有效性与真实分数 |
| 2:55–4:00 | “案例”选 quick-update 或本次其他案例，再看“证据/记忆轨迹” | 输入、预期、实际答复、规则理由、step/source/引用 |
| 4:00–4:25 | 本次目录与 strict 校验，简述隔离、参数和观测边界 | 报告可复核，系统行为与模型原生记忆分开 |
| 4:25–4:50 | GitHub 发布页，显示源码、PDF、deb/wheel、CI、MIT | 可部署和开源复现入口 |

时间是镜头编排建议，不是对网关运行时间的保证。保留连续完整原片；真实评测超过 5 分钟时，优先保留完整流程。可另附标注“等待段倍速”的展示版，原始片仍留存。

## 录制前准备（镜头外）

在 VM 桌面中操作，保持原 openKylin 3.0 系统；不用 sudo，不升级或降级操作系统。先修正评分/解析问题并安装修正后的项目版本，确认一批真实六案例预演有效。

终端 A 启动已准备的工作台：

```bash
~/KylinMemoryBench/start-workbench.sh
```

浏览器打开 `http://127.0.0.1:8765`。终端 B：

```bash
cd ~/KylinMemoryBench
VIDEO_RUN="runs/video-real-$(date +%Y%m%d-%H%M%S)"
printf '%s\n' "$VIDEO_RUN"
kmb quick-compare --agents kylinbot openclaw \
  --preflight-only --out "$VIDEO_RUN/preflight"
```

检查真实预检状态，不只看命令退出码：

```bash
python3 - "$VIDEO_RUN/preflight/quick-compare.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
for item in r['preflight']:
    print(item['agent'], item['status'])
print('blocked=', r['blocked'], 'turns=', r['turns_started'])
assert r['turns_started'] == 0
assert not r['blocked'], '处理预检阻断后再录制'
PY
```

预检 ready 只确认命令与存储；正式评测会调用真实 Agent 后端并消耗相应额度。不要沿用旧稿的“40–60 秒必完成”或“重录成本低”。录制前关闭通知和账户/Token 页面，只展示本批合成案例。

录屏选整个 VM 桌面，文字清晰，建议 1920×1080；用已安装的录屏工具确认能录麦克风。仓库 ffmpeg 脚本只录屏幕，可录后配旁白，但不要误以为它自动录音或保证完整时长。

## 镜头中实际命令

环境展示：

```bash
grep -E 'PRETTY_NAME|VERSION_ID' /etc/os-release
dpkg-query -W kylin-memory-bench
```

“新建评测”页选择 `suites/quick.yaml` 只查看六类摘要，不在日常 HOME 点击“开始快速对比”。返回终端 B，启动已实现的隔离入口：

```bash
kmb official-repeat --agents kylinbot openclaw \
  --suite suites/quick.yaml --repeats 1 --seed 42 \
  --timeout 180 --isolated-home \
  --out "$VIDEO_RUN/evaluation"
```

看到 `status=completed` 后，检查两侧有效性和运行错误：

```bash
python3 - "$VIDEO_RUN/evaluation" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
for agent in ('kylinbot', 'openclaw'):
    p = root / 'repeat-01/quick-compare' / agent / 'result.json'
    r = json.loads(p.read_text())
    print(agent, 'score=', r['overall'],
          'valid=', r['score_valid'], 'errors=', r['error_cases'])
    assert r['score_valid'] is True and r['error_cases'] == 0
PY
```

浏览器刷新工作台，“运行历史”中找到本次目录下 `evaluation/repeat-01/quick-compare` 的双 Agent comparison，点击“查看”。用目录和时间定位，避免误点之前的 reference/flawed 对照或重复汇总中的单 Agent 记录。

如果界面定位不顺，可从同一批次打开离线比较报告：

```bash
xdg-open "$VIDEO_RUN/evaluation/repeat-01/quick-compare/comparison.html"
```

`.deb` 包已安装严格校验入口，可直接执行：

```bash
python3 /usr/share/kylin-memory-bench/scripts/verify_run.py \
  "$VIDEO_RUN/evaluation/agents/kylinbot/repeat-01" --strict
python3 /usr/share/kylin-memory-bench/scripts/verify_run.py \
  "$VIDEO_RUN/evaluation/agents/openclaw/repeat-01" --strict
```

`comparison.html`、两侧 `radar.svg`、`result.json`、`evidence.jsonl` 和 `repeat-summary.json` 来自同一批次。单批演示不宣称稳定性统计；需要额外重复时在新目录用 `--repeats 2`，全部批次包括失败都应保留。

## 完整口播稿（照读）

### 1. 项目用途

大家好，我展示的项目是 KylinMemoryBench，一套运行在 openKylin 上的智能体长期记忆自动化评测工具。它帮助开发者判断：智能体是否能记住应该保留的信息、更新旧信息、拒绝不该保存的信息，并把记忆用于实际任务。我们将运行证据组织起来，自动给出可解释的指标。

### 2. 真实环境和参与者

这里是原有的 openKylin 3.0 桌面，终端显示当前系统和项目软件版本。项目软件版本与操作系统版本是两回事。这次参与评测的是已经安装的 KylinBot 和 OpenClaw。工具可以发现它们的命令入口与存储，预检通过后再启动真实评测。

### 3. 案例和公平性

这次选用 quick 套件，六个案例分别覆盖长期保持、记忆调用、动态更新、相近区分、边界识别和任务复用。例如，先告诉智能体会议室是 Room A，再改成 Room B，最后查询时，应该使用新信息。两款 Agent 使用同一套件、随机种子和运行参数。这里展示的是六案例流程，不代表两款 Agent 已完整跑过项目全部案例。

### 4. 启动真实隔离评测

现在通过一条命令启动评测。工具为每款 Agent 准备临时 HOME 和独立记忆状态副本，合成案例不会写入日常记忆。本次调用真实 Agent 后端，运行完成后会自动生成评分、比较报告和雷达图。网络等待时间由实际环境决定。

### 5. 多维结果

评测完成后，我在运行历史中打开刚才这一批结果。这里显示两款 Agent 的实际总分，以及六个能力维度的对比和雷达图。总分用来概览，具体维度帮助定位差异。有效低分是值得分析的结果；运行错误则需要先处理，不能混作正常能力分数。

### 6. 解释一项检查

接下来打开一个具体案例。这里能对应看到输入、目标检查、实际答复和评分理由，再沿引用查看不同步骤的证据。对于会议室更新，既要检查最新状态是否为 Room B，也要检查最终查询是否使用新值。通过同样需要证据；没有观测到的内部状态不会自动当作已经验证。

### 7. 可复核与边界

本次运行保留了案例结果、原始事件、报告和运行参数，可以做严格结构校验，也能在工作台回溯。但结构完整不等于所有语义规则都天然正确。这里评测的是 Agent 和记忆、动作机制的系统级行为；没有明确的原生记忆事件时，不宣称模型原生长期记忆。单批短任务也不能证明数天或长期稳定性。

### 8. 开源交付和价值

最后，项目提供 CLI、浏览器工作台、openKylin Debian 安装包及完整可复现材料。代码采用 MIT 许可证，GitHub 发布页提供源码、使用说明和验证记录。希望这套工具帮助 openKylin 社区用具体案例和可核查证据，持续发现并改进智能体的记忆问题。谢谢大家。

## 案例讲解的两个分支

如果本批有失败案例，选择一个有清晰规则和证据的失败，补一句：“这一项没有满足检查，原因和对应事件都能展开查看。”不要把未观测到的动作解释为确定发生了错误动作。

如果全部通过，选择一个通过案例，补一句：“这一项通过，是因为状态、答复或动作证据满足了对应检查。”需要补充扣分演示时，可另开 reference/flawed 离线对照，画面明确标注模拟基线；不能替代前面的两款真实 Agent。

## 可省略或作为备用镜头的功能

- 一键离线工程验收：`kmb official-acceptance --mode offline --out <新目录>`，用于证明工具链可复现，不是“官方评审通过”。
- 多批次聚合：在新目录运行 `official-repeat --repeats 2`，展示均值、标准差和有效分数率；不宣称两批代表长期稳定。
- API 档案注册：只说明可扩展接入，不录入密钥，也不把两个提供商自动说成两款生态 Agent。

## 录完后的检查

确认能看清系统 3.0、两款真实 Agent、启动和完成、六维雷达、至少一个案例及证据；声音清楚、没有凭据和私人通知；保持同一批次的目录与参数。保留原始连续片，上传后用未登录窗口确认视频可播放。当前稿子不把“视频已完成”或“正式材料已发送”写成事实。
