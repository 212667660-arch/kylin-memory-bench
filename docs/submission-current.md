# KylinMemoryBench 当前提交材料

日期：2026-10-15。唯一提交版：软件 0.2.5；实际系统仍为 openKylin 3.0。按负责人提供的组委会反馈，项目材料已收到，现补充视频网站在线观看链接；本工具未代发补交邮件。

## 正式入口

- 代码：https://github.com/212667660-arch/kylin-memory-bench
- 全部材料：https://github.com/212667660-arch/kylin-memory-bench/releases/tag/v0.2.5
- 完整 ZIP（含视频）：https://github.com/212667660-arch/kylin-memory-bench/releases/download/v0.2.5/KylinMemoryBench-submission-0.2.5-20261015.zip
- 作品介绍 PDF：https://github.com/212667660-arch/kylin-memory-bench/releases/download/v0.2.5/project-introduction-0.2.5.pdf
- 演示视频在线观看（正式补交使用）：https://www.bilibili.com/video/BV133J16wEsF/
- 原视频归档下载：https://github.com/212667660-arch/kylin-memory-bench/releases/download/v0.2.5/KylinMemoryBench-demo-20261014.mp4

负责人已自行上传至哔哩哔哩。本轮独立未登录浏览器检查：作品页 HTTP 200、标题为 KylinMemoryBench介绍视频、视频时长约 4 分 51 秒，播放器实际播放并持续推进，无媒体错误。正式回复组委会使用上面的 B站作品页链接。

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
| VIDEO-ONLINE.md / submission-video-reply.txt（发布页补充附件） | B站正式观看入口与当前补交邮件草稿；原 ZIP 保留冻结版本 |

## 发送步骤

1. 在组委会要求补充在线观看链接的原邮件中点“回复”，保留原主题与参赛身份。
2. 使用更新后的 `docs/submission-email-draft.md` 或本机补交草稿，提供 B站作品页链接；不要把后台投稿页、带时间参数的分享链接或下载直链当作补交的观看地址。
3. 发送前用未登录/无痕浏览器打开 B站作品页，检查能播放且没有仅自己可见的限制。
4. 在截止前由负责人回复，保存已发送记录和回执；补交邮件由负责人发送。

v0.2.5 原完整 ZIP、介绍 PDF、源码和安装包保留原冻结快照与哈希。其材料中原 MP4 链接为归档下载；当前观看入口和补交邮件以本页及发布页置顶 B站链接为准。

## 版本和视频限制

0.2.5 统一包含原生 API 状态读取与快速对比测试准备修复。旧提交材料清理后以本页为当前入口；历史软件标签和技术记录保留当时事实。

视频原 SHA-256：a0fefdbf85575cbd7f4d1a41e2157a667ba6b514c278a4810ab5ef1f333d1b13。片中 19:32 启动任务与 12:40 展示结果不同批次；22.22 / 36.11 属于后者，不能归属新任务。视频用于功能和历史样例展示，不能作为新批次连续成功证明，也未完整展示后来新增的 API 状态分区。提交者应阅读此限制，必要时补录同一批次的结果段。

本轮没有编辑视频、分数、历史事件、原生密钥或原 openKylin 3.0，没有新增真实模型调用。API 凭据存在不代表鉴权或额度可用。离线样例与历史真实摘要分开标识，不混合评分。

## 隐私与复现

不分发 .env、credentials.env、私钥、密码、私有 HOME、会话摘录、个人原始日志或开发缓存；只发布公开源码与核对后的材料，明确假字符串保留。视频与旧成片逐字节一致，既有敏感内容审阅基于抽样画面和自动转写，不扩大为逐帧无遗漏保证。

按 README 的 Python 3.9+ 步骤安装源码或 wheel。CLI 与网页均使用后端所在主机的环境；Windows 未安装原生智能体时显示未安装是正常的，真实生态评测请在已安装它们的后端执行。工作台 API 档案不替换原生配置。
