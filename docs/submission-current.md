# KylinMemoryBench 当前提交材料

日期：2026-10-15。唯一提交版：软件 0.2.5；实际系统仍为 openKylin 3.0。报名已确认；邮件未发送。

## 正式入口

- 代码：https://github.com/212667660-arch/kylin-memory-bench
- 全部材料：https://github.com/212667660-arch/kylin-memory-bench/releases/tag/v0.2.5
- 完整 ZIP（含视频）：https://github.com/212667660-arch/kylin-memory-bench/releases/download/v0.2.5/KylinMemoryBench-submission-0.2.5-20261015.zip
- 作品介绍 PDF：https://github.com/212667660-arch/kylin-memory-bench/releases/download/v0.2.5/project-introduction-0.2.5.pdf
- 视频：https://github.com/212667660-arch/kylin-memory-bench/releases/download/v0.2.5/KylinMemoryBench-demo-20261014.mp4

官网 https://www.oschina.net/os2026/ 要求完整可运行代码的仓库链接、作品介绍（推荐 PDF）与展示核心功能/使用流程的视频链接，按报名确认邮件指引于北京时间 2026-10-16 24:00 前发送至 oscc@oschina.cn。确认邮件若要求项目编号或特定格式，以其指引为准。本轮不填造身份、不发送邮件；上传附件不等于正式提交成功。

## 完整 ZIP 与独立附件

| 材料 | 用途 |
| --- | --- |
| project-introduction-0.2.5.pdf / .docx | 作品介绍与可编辑副本 |
| submission-guide-20261015.pdf / SUBMISSION-README.md | 唯一入口、发送步骤、版本和视频限制 |
| kylin-memory-bench-0.2.5-source.zip | Git 提交锁定的公开源码 |
| kylin_memory_bench-0.2.5-py3-none-any.whl | Python 3.9+ 包，含网页和案例数据 |
| kylin-memory-bench_0.2.5_all.deb | openKylin/Debian 安装包 |
| example-data-and-results-0.2.5.zip | 六例数据、离线结果/证据及历史真实结果摘要 |
| KylinMemoryBench-demo-20261014.mp4 | 原始成片；完整 ZIP 内含视频，亦可独立下载 |
| verification-summary-0.2.5.json | 本轮验证范围、历史来源与未验证项 |
| delivery-manifest-0.2.5.json / CONTENTS-SHA256.txt | ZIP 内来源与校验值 |
| SHA256SUMS-0.2.5.txt | 含完整 ZIP 在内的独立附件校验，不含其自身 |
| submission-email-draft.txt | 未发送草稿，身份占位须由负责人填写 |

## 发送步骤

1. 查看报名确认邮件，补齐已报名团队名、负责人、邮箱和项目编号，不要把占位符原样发出。
2. 使用最新草稿中的仓库、材料和视频链接。建议邮件附介绍 PDF、说明 PDF 和校验清单，避免把大视频直接塞进邮件。
3. 在未登录状态确认下载可用。本地打包上传使用包含视频的完整 ZIP；完整 ZIP 与独立视频无需重复下载。
4. 在截止前由负责人发送，保存已发送记录和回执。材料准备与 GitHub 发布均不能代替此步骤。

## 版本和视频限制

0.2.5 统一包含原生 API 状态读取与快速对比测试准备修复。旧提交材料清理后以本页为当前入口；历史软件标签和技术记录保留当时事实。

视频原 SHA-256：a0fefdbf85575cbd7f4d1a41e2157a667ba6b514c278a4810ab5ef1f333d1b13。片中 19:32 启动任务与 12:40 展示结果不同批次；22.22 / 36.11 属于后者，不能归属新任务。视频用于功能和历史样例展示，不能作为新批次连续成功证明，也未完整展示后来新增的 API 状态分区。提交者应阅读此限制，必要时补录同一批次的结果段。

本轮没有编辑视频、分数、历史事件、原生密钥或原 openKylin 3.0，没有新增真实模型调用。API 凭据存在不代表鉴权或额度可用。离线样例与历史真实摘要分开标识，不混合评分。

## 隐私与复现

不分发 .env、credentials.env、私钥、密码、私有 HOME、会话摘录、个人原始日志或开发缓存；只发布公开源码与核对后的材料，明确假字符串保留。视频与旧成片逐字节一致，既有敏感内容审阅基于抽样画面和自动转写，不扩大为逐帧无遗漏保证。

按 README 的 Python 3.9+ 步骤安装源码或 wheel。CLI 与网页均使用后端所在主机的环境；Windows 未安装原生智能体时显示未安装是正常的，真实生态评测请在已安装它们的后端执行。工作台 API 档案不替换原生配置。
