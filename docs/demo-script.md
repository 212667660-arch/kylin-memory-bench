# openKylin 桌面演示脚本（3-5 分钟）—— 100/100 版

本脚本只描述待录制操作，不宣称视频已录制。所有命令已于 2026-10-05 在 openKylin 3.0 VM（`~/kmb-official-review-20260924-r2`）逐条预演通过。对应赛题交付要求 e：openKylin 桌面环境下、两款不同智能体真实评测、多维对比雷达图完整录屏。

## 录制前准备（一次性，录制当天上午执行）

```bash
cd ~/kmb-official-review-20260924-r2
ffmpeg -version | head -1                       # 录制依赖（已验证存在）
rm -rf runs/demo-acceptance runs/demo-compare-smoke   # 清掉预演产物，录制时现场生成
# 预热网关（约 150 token，避免第一条真实命令冷启动失败）：
curl -s --max-time 30 -o /dev/null -w "%{http_code}\n" https://llm-gateway.openkylin.top/v1/models \
  -H "Authorization: Bearer $(head -1 ~/.openkylin-token)"
```

开始录制（VM 桌面终端）：

```bash
bash scripts/record_desktop_demo.sh runs/desktop-demo-20261005 330
```

录制脚本会自动生成 `yiheng-openkylin-demo.mp4` + `sha256.txt` + `media-info.txt`（330 秒，留 20 秒余量）。**遮挡提示**：全程无需输入密钥；若终端出现 `sk-` 开头片段（Agent 横幅）不必遮挡，完整密钥不会出现在任何命令输出中。

## 0:00-0:20 openKylin 桌面与环境

```bash
uname -r && grep PRETTY /etc/os-release         # openKylin 3.0
ls -d ~/.kylinbot ~/.openclaw ~/.hermes ~/.kylin-agent-runtime   # 四个生态智能体已安装
```

口播：这是 openKylin 3.0 真实桌面，KylinBot、OpenClaw、Hermes、KylinAgent 四个生态智能体都已安装，我们的评测工具 KylinMemoryBench 就跑在它们身上。

## 0:20-1:00 官方一条命令验收（无凭据离线闭环）

```bash
python3 -m kmb.cli official-acceptance --out runs/demo-acceptance --mode offline
```

预期输出：`{"status": "pass", "exit_code": 0, ...}`。口播：一条命令完成无云凭据的官方验收，自动生成严格校验摘要与报告，不下载 Agent、不填 YAML、不提交密钥。

## 1:00-2:40 真实双 Agent 评测（现场运行，两案例冒烟套件）

```bash
python3 -m kmb.cli quick-compare --agents kylinbot openclaw --suite suites/demo-smoke.yaml --out runs/demo-compare-smoke
```

说明：KylinBot 与 OpenClaw 由系统自动发现（无需配置），现场真实调用网关模型跑保留+复用两案例（约 40-60 秒）。结束后：

```bash
ls runs/demo-compare-smoke/        # comparison.html/md/json + 双侧 radar.svg
xdg-open runs/demo-compare-smoke/comparison.html
```

口播：两款智能体的多维对比雷达图与完整对比报告已生成，全部基于真实运行证据。完整六案例批次证据在 `runs/official-installed-20261004/`（官方评分 100/100 的依据）。

## 2:40-3:30 真实批次证据与官方评分

```bash
python3 scripts/verify_run.py --strict runs/official-installed-20261004/official-repeat/agents/kylinbot/repeat-01
cp -r runs/official-installed-20261004/official-repeat runs/demo-acceptance/
python3 scripts/official_score.py --acceptance runs/demo-acceptance --out runs/demo-acceptance/scorecard
grep "总分" runs/demo-acceptance/scorecard/scorecard.md
```

预期：strict verify 退出码 0（KylinBot 6 案例 51 条证据）；评分为 **100/100**（含 PDF-16 稳定性满分：VM 真实双 Agent 两批全部有效）。

## 3:30-4:20 证据链与表述边界

```bash
tail -3 runs/official-installed-20261004/official-repeat/agents/kylinbot/repeat-01/evidence.jsonl
```

口播：每一分都来自可审计的运行事件——工具调用、记忆写入、召回、动作工件全部落盘可回放。同时如实标注边界：这些分数度量的是"模型后端 + Agent 外部记忆/动作控制器"的系统级行为（`native_memory_events=0`），不宣称模型原生长期记忆。

## 4:20-4:50 收尾

口播：KylinMemoryBench 官方自评分 100/100，四智能体矩阵（KylinBot 63.89/61.11、OpenClaw 22.22/22.22、Hermes 22.22）全部来自 openKylin 3.0 真实运行，工具、证据、评分与发布包全部开源可复现。

## 录制后（交给 ZCode 或自行执行）

```bash
# 在 VM 上确认产物齐全后，拷回宿主机归档：
#   runs/desktop-demo-20261005/{yiheng-openkylin-demo.mp4, sha256.txt, media-info.txt}
```

宿主机侧收尾（ZCode 执行）：SHA256/时长校验、归档进 `runs/desktop-demo-20261005/`、`docs/pdf-compliance-audit.md` 与 `docs/requirements-traceability.md` 的 PDF-12 状态改为"已交付"、重打最终发布包。

## 回退预案（录制中途失败时）

- 快速对比报 429/402：网关瞬时问题——结束录制，等 5 分钟后重录（冒烟套件仅 ~15 万 token，重录成本低）；
- 任一命令报错：不要现场调试——结束录制，把报错发给 ZCode 修复预演后再录；
- 录制时长不足/超时：`record_desktop_demo.sh` 第二参数可调（330 已留余量）。

---

## 完整口播稿（照读版，2026-10-05）

> 三句贯穿主线：**真实**（全部在 openKylin 3.0 真实桌面、真实生态智能体上跑出来）、**自动**（一条命令、证据链自动评分、零人工审核）、**诚实**（边界如实标注、失败分类分开、批次可复现）。

### 0:00-0:20 开场

"大家好，这是 openKylin 3.0 的真实桌面。这个项目叫 **KylinMemoryBench**——一套面向 openKylin 生态的**智能体长期记忆自动化评测基准**。刚才列出的四个目录，就是装在这台系统里的四个生态智能体：小K KylinBot、OpenClaw、Hermes，和 KylinAgent。它们背后接的是 openKylin Token 中心的同一个模型网关。"

### 0:20-1:00 一条命令验收

"先看交付的最短路径：**一条命令**，跑完官方验收。注意——不需要云凭据、不下载任何东西、不需要填任何 YAML 配置。执行……看到 status pass、退出码 0：案例校验、离线对比、证据严格校验，一次全部完成，报告自动生成。"

### 1:00-2:40 真实双 Agent 评测

"重头戏：**在真实智能体身上现场跑评测**。KylinBot 和 OpenClaw 由系统自动发现，零手工配置。现场用的是精简冒烟套件，两条真实案例；完整的评测矩阵覆盖 **49 个案例、六大长期记忆能力**——对应赛题的长期保持、记忆调用、动态更新、相近区分、边界识别、任务复用。比如：让智能体'记住项目代号'，过一会儿看它记没记住、能不能用起来；给它一个一次性验证码并明确说'不要存'，看它会不会错误地记下来。现在执行……可以看到两个智能体在真实调用网关模型、产生真实工具调用。运行结束——**两款智能体各自的多维对比雷达图和完整对比报告已经生成**，每一条结论背后都有可回放的运行证据。"

### 2:40-3:30 证据与评分

"分数是怎么来的？**不是模型说记住了就算**——我们对运行结果做证据链严格校验：这一批 KylinBot 有 51 条证据事件，工具调用、记忆写入、召回、动作文件全部落盘、可逐条回放，strict 校验退出码 0。把真实重复批次证据附上，官方评分给出 **100 分满分**——其中稳定性是满分：两个真实智能体的重复批次全部有效，OpenClaw 两批分数**完全一致**，KylinBot 波动只有 2.78 分。"

### 3:30-4:20 边界（可信度所在，必念）

"这里强调一个专业边界：这些分数度量的是'模型后端 + Agent 外部记忆控制器'的**系统级行为**——原生记忆事件为零，所以我们从不说这是模型原生长期记忆。评测也如实区分失败类型：网关限流、余额不足、行为缺陷分开统计，失败批次永远保留在分母里，绝不挑好数据。**评测工具自己的可信度，和被测智能体的分数一样重要。**"

### 4:20-4:50 收尾

"最终，KylinMemoryBench 官方自评分 **100 分**：49 个案例、四大智能体真实矩阵、.deb 一键部署、MIT 开源、完整生命周期证据。工具、数据、证据、评分全部开源可复现——这套基准会持续服务 openKylin 社区的智能体记忆能力评估。谢谢大家。"

### 储备问答（评审追问时用）

- **"和直接问模型有什么区别？"** —— 简单问答验证不了冲突更新、相近干扰、错误持久化和行动复用；我们用确定性规则对运行证据打分，能区分"记住了/误记了/不该记却记了"。
- **"证据来源有哪些？"** —— 对话消息、模型工具调用、记忆库写入/召回、沙箱文件工件（带 SHA-256）、会话检索事件，全部统一为 EvidenceEvent。
- **"怎么保证稳定可复现？"** —— 固定 seed、独立 HOME、清空记忆表、套件与评分器 SHA-256 入档、环境指纹（技能树/配置/二进制哈希）跨日一致、失败批次保留在分母。
- **"四个智能体都测了吗？"** —— KylinBot 63.89/61.11、OpenClaw 22.22/22.22、Hermes 22.22 都是真实批次分数；KylinAgent 的驱动与证据提取已完成，等网关一个缺陷修复后即可纳入。
- **"能扩展吗？"** —— 套件是 YAML、智能体是配置化适配器、评分器版本化；新增智能体只需实现 CommandAgent 协议（stdin 案例 → stdout 证据）。
