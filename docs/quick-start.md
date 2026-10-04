# 快速对比

KylinMemoryBench 不会下载或安装 Agent。它只发现当前 openKylin 用户已经安装的 Agent，并读取其可观测运行/记忆证据。

官方评审的最短无凭据路径是：

```bash
python3 -m kmb.cli official-acceptance --out runs/official-acceptance
```

这会生成离线验收摘要和严格校验的比较产物，不会代表真实 Agent 模型能力。openKylin 上对比本机已安装 Agent 时，见下方工作台路径或 `docs/official-acceptance.md` 的 `installed` 模式。

## 用户操作

1. 在已安装四个 Agent 的 openKylin 环境启动工作台：

   ```bash
   python3 -m kmb.cli serve --host 127.0.0.1 --port 8765 --root /path/to/kylin-memory-bench
   ```

2. 打开 `http://127.0.0.1:8765/`，总览页会自动发现 KylinBot、Hermes、OpenClaw、KylinAgent。
3. 勾选两个“可自动运行”的 Agent，点击“开始快速对比”。Seed、重试、超时和六维套件已经固定，不需要编辑 YAML 或手填参数。
4. 任务完成后，页面自动进入结果中心；结果包含每个 Agent 的六维分数、失败原因、证据链和观测边界。

## 命令行等价路径

```bash
python3 -m kmb.cli discover-agents --json
python3 -m kmb.cli quick-compare --agents kylinbot hermes
```

默认参数为 Seed `42`、重试 `1`、单案例超时 `180` 秒，固定套件为 `suites/quick.yaml`。运行器不会自动安装或下载 Agent。

## 观测边界

- KylinBot、Hermes、OpenClaw 只有在发现真实存储和可用 CLI 后才允许自动对比。
- 点击开始后会先执行只读预检（可执行入口、记忆存储和结构化证据能力）；预检未通过时不会启动 Agent 回合，并会在 `quick-compare.json` 保留阻断原因。
- 结果会把 `behavior_failure`、`runtime_error`、`credential_error`、`billing_error`、`timeout`、`missing_input`、`not_observable` 和 `unsupported_action` 分开记录；动作没有真实执行证据时不会计作成功。
- KylinAgent 当前标记为“已安装但不可自动驱动”，因为 GUI/服务状态不能替代结构化记忆证据；它不会被伪造为自动评分对象。
- 分数描述的是 Agent 后端与其外部记忆/动作控制器的系统级行为，不证明模型原生记忆能力。
- 凭据不通过网页提交，也不会写入 YAML、日志或结果 JSON。
