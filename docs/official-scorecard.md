# 官方视角评分卡

此工具是项目按 PDF 六维权重制作的工程自评，不能替代组委会评分或推断所有交付已完成。官网另列技术创新/场景落地/开源治理/长期发展四维权重 30%/30%/20%/20%。2026-10-13 发现旧验收会接受运行失败但结构有效的证据，已增加 `score_valid` 门禁；旧评分保留作历史记录，当前结论见 `docs/completion-audit-20261013.md`。

本评分卡记录当前非视频收口结果。评分只使用已生成的验收产物、命令记录和严格校验结果，不把文档中的自述当作证据。

## 当前结果

- 当前得分：**90/100**
- 评分产物：`runs/official-final-20260925-r2/scorecard-final/`
- 验收命令：

  ```powershell
  .\\.venv-kmb-system\\Scripts\\python.exe -m kmb.cli official-acceptance --out runs/official-final-20260925-r2 --mode offline
  .\\.venv-kmb-system\\Scripts\\python.exe scripts/official_score.py --acceptance runs/official-final-20260925-r2 --out runs/official-final-20260925-r2/scorecard-final
  ```

- 评分器退出码：`0`
- 本轮评分、重复批次和发布包相关回归测试均通过。

## 分项得分

| 项目 | 权重 | 得分 | 状态 | 官方依据 |
|---|---:|---:|---|---|
| PDF-13 通用性 | 15 | 15 | pass | 统一 CLI、Agent 发现/预检、`EvidenceEvent` 严格校验 |
| PDF-14 数据设计 | 25 | 25 | pass | 49 个案例（含英文多语言套件）、六类能力、语言/风险标签和套件哈希 |
| PDF-15 自动评分 | 25 | 25 | pass | 结构化结果、失败分类、证据引用和 strict verify |
| PDF-16 稳定性 | 15 | 15 | pass | openKylin 3.0 VM 真实双 Agent 重复批次：两批双 Agent 全部 `score_valid=true`（有效率 100%，batch_count=2>1），含均值/标准差与失败类型 |
| PDF-17 指标完整性 | 10 | 10 | pass | JSON、Markdown、HTML 和对比雷达产物齐全 |
| PDF-18 工程落地 | 10 | 10 | pass | 脱敏发布包、审计、CLI 和 Debian 打包入口齐全 |

评分明细以 `scorecard.json` 为准，人工查看可打开 `scorecard.md` 或 `official-review.html`。

## 稳定性证据边界

**当前证据（2026-10-04，满分依据）**：`runs/official-installed-20261004/official-repeat/`（VM 原始目录 `<user-home>/kmb-official-review-20260924-r2/runs/official-installed-20261004/`）。`status=completed`；KylinBot 2/2 批有效（63.89/61.11，均值 62.50、标准差 1.97）、OpenClaw 2/2 批有效（22.22/22.22，标准差 0.00）；环境指纹与 2026-10-01 采集一致（kylinbot `e943ece7…`、openclaw `b11a5e9c…`），证明跨日批次环境同一。批次失败分类纪律不变：error 级失败（若有）保留在分母。

**历史证据（保留）**：早期真实 VM 重复批次 `runs/official-repeat-vm-20260924-fixed/`（KylinBot 1/3、OpenClaw 0/3 有效，billing/timeout 保留在分母）、`runs/official-installed-20260927{,-r2}/`（网关 402 余额不足）与 `runs/official-installed-20261001{,-r2}/`（429 限流与余额耗尽各一次，run-2 两批有效但批 3 402）——这些系列记录了真实的执行波动与失败分类，均不参与当前满分判定。

早期 VM 重复批次原始目录为：

```text
<user-home>/kmb-agent-validation-20260923/runs/official-repeat-20260924-fixed/
```

该批次保留了 3 个重复批次、billing/timeout 失败和有效性统计：KylinBot 为 1/3 有效分数，OpenClaw 为 0/3 有效分数。失败批次不能从分母中删除，因此 PDF-16 暂定部分得分。OpenClaw 的 SQLite 隔离外键问题已修复，当前失败应按真实 billing/timeout 解释，而不是归因于隔离代码错误。

## 观测边界

- `source=simulated` 只验证工具链和评分逻辑。
- `source=process`、`source=wrapper` 只证明系统级 Agent/外部记忆或动作控制器行为。
- 当前真实 KylinBot/OpenClaw 批次的 `native_memory_events=0`，不能据此宣称模型原生长期记忆。
- B 轨离线记忆工具调用必须标记为离线/模拟；它不能替代真实 LLM 工具调用证据。

## 明确排除项

- `PDF-12` 桌面视频：按用户要求未处理。
- 根目录项目级 `LICENSE`：已于 2026-10-05 生效（MIT，负责人确认）；评分模型不变，仍不计入权重。

因此，90/100 是当前非视频、排除 LICENSE 后的保守工程自评分，不是赛事最终总分承诺。

## 2026-09-25 安装模式复核

本机按三次重复命令执行了安装模式验收：

```powershell
.\\.venv-kmb-system\\Scripts\\python.exe -m kmb.cli discover-agents --json
.\\.venv-kmb-system\\Scripts\\python.exe -m kmb.cli official-acceptance --mode installed --agent-a kylinbot --agent-b openclaw --repeats 3 --out runs/official-installed-final-20260925
.\\.venv-kmb-system\\Scripts\\python.exe scripts/official_score.py --acceptance runs/official-installed-final-20260925 --out runs/official-installed-final-20260925/scorecard
```

结果目录为 `runs/official-installed-final-20260925/`：KylinBot/OpenClaw 在当前 Windows 主机均未发现已安装存储，三批均保留为 `blocked`，原因是缺少 `.kylinbot`；没有生成 Agent 分数。该批次的机器评分为 72/100，仅表示当前环境阻断，不替换上面的无凭据离线基线。openKylin VM SSH 端口当前不可达，因此未声称完成真实 VM 三批稳定性。
