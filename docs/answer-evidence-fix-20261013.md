# 回答评分与 CLI 证据修复验证（0.2.2）

2026-10-13。已修复视频深审复现的两个 P1 问题，现有 openKylin 3.0 上已升级项目软件到 0.2.2。操作系统版本保持原状。

## 修复内容

- 普通 `answer_contains` / `answer_not_contains` 默认只检查案例最后一个声明回合，前面的确认语不能替代最终答复，也不会因初次正确确认旧值而误扣更新分。boundary 禁词检查保留全程，显式 `answer_scope: last/all` 或正整数 `step` 可指定范围；非法或互相冲突的范围在运行前拒绝。
- CLI 先完整解析 JSON，再从已识别的 assistant 字段提取文本；支持带前缀的格式化 JSON、JSONL 与按顺序分块的正文，排除工具、日志、模型元数据。成功 stdout 不再以 8192 字符截断后才解析，错误诊断仍有长度上限。OpenClaw 无可观测回答时标为运行错误，不能拿工具名补位。
- `.deb` 版本提取移除 CRLF 的尾部 CR 字符；CI 覆盖 CRLF 默认版本构建。

## 实际验证

| 验证 | 结果与证据 |
|---|---|
| 修复前语义回归 | 18 项测试复现失败（含子测试共 22 项失败）；`runs/fix-answer-evidence-20261013/regression-before.log` |
| 修复后回归 | 新增 18 项通过；Windows/openKylin 全量均 176 项通过 |
| 跨平台 CI | Windows Python 3.9、Ubuntu Python 3.12 单测与干净 wheel 安装，以及 Debian 安装/升级/卸载 job 全通过；[代码 CI](https://github.com/212667660-arch/kylin-memory-bench/actions/runs/38379838449) |
| 安装后使用 | 原 openKylin 3.0 软件包 0.2.1→0.2.2 升级成功；普通用户包内 smoke、strict 对照及完整离线验收通过；工作台 HTTP/创建评测/结果/雷达/真实案例证据读取通过 |
| 真实第一批 | OpenClaw 六案例有效，30.56；KylinBot quick-update 网关连接失败，整侧无效。原始记录保留在 `vm/real-022/`，不纳入正常能力均值 |
| 真实第二批 | 新隔离 HOME、quick 六案例、seed 42、repeats 1、timeout 180；KylinBot 22.22、OpenClaw 30.56，两侧 `score_valid=true`、运行错误 0、strict 通过；`vm/real-022-r2/` |
| 实际解析样例 | OpenClaw quick-update 的三轮确认/最终答复已为正文；没有 `edit` 或整段 JSON 元数据冒充回答。工作台可读取同一批证据 |

本轮证据在 `runs/fix-answer-evidence-20261013/`，发行材料中保留 `verification/` 与 `sample-evidence/`。结果 manifest 的 scorer SHA-256 为 `6c2407c8d9dc6dcb5aebf5b91cc4a9466b1c2f43137c6daa6430277f7c99c705`，quick 套件 SHA-256 为 `b470c0025403be97f303a3112735f5f6d8020a5f28f2ed1ab1aafd2443674fd7`；不同版本评分不可直接合并。

## 解释与限制

有效低分可用于讲解实际案例。最终答复若仍包含案例禁止词，仍按明确规则扣分；修复不会通过改答案或放松案例制造高分。本次两款 Agent 只跑了六案例快速套件，没有宣称完整跑过主覆盖清单全部 49 案例。单批有效结果不证明长期稳定性，第一批网关失败也保留。

两侧 `native_memory_events=0`，结果反映 Agent 和记忆/动作机制的系统级行为；没有证据的模型原生记忆与动作不会视为已验证。strict 验证结构与链条完整性，语义正确性另由规则回归和正文核对支持；仍不等同于赛事官方评审。

视频由负责人录制；[分镜和照读稿](demo-script.md) 已按 0.2.2 更新。报名已确认，正式提交邮件草稿尚未发送，团队身份、确认邮件指引和实际视频链接仍需补齐。
