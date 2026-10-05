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
