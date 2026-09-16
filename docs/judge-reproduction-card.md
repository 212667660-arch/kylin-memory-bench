# 评委复现卡（非视频 / 无云凭据）

一页纸：如何在 **约 5 分钟内** 离线验证 KylinMemoryBench 核心链路。

## 1. 环境

- Python ≥ 3.9，依赖：`PyYAML≥6`
- 无需 API Key、无需网络、无需 openKylin 桌面
- 工作区根目录执行

```bash
python -m unittest discover -s tests -q
python -m kmb.cli validate --strict --suite suites/core-zh.yaml
```

## 2. 一键离线对比（推荐）

```bash
bash scripts/run_offline_demo.sh runs/offline-demo
```

产物：

| 路径 | 含义 |
|------|------|
| `runs/offline-demo/core-compare/comparison.html` | 双 Agent 对比 + 六维雷达 |
| `runs/offline-demo/core-compare/comparison.json` | 机器可读对比 |
| `runs/offline-demo/expanded-compare/` | 扩展 18 案例结果 |
| `*/evidence.jsonl` | 每案例证据事件 |
| `*/result.json` | 逐检查项评分与失败类型 |

## 3. 手动等价命令

```bash
python -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-flawed.yaml \
  --suite suites/core-zh.yaml \
  --out runs/offline-demo/core-compare \
  --seed 42 --retries 0 --timeout 30

python scripts/verify_run.py runs/offline-demo/core-compare/reference --strict
python scripts/verify_run.py runs/offline-demo/core-compare/flawed --strict
```

## 4. 六类能力覆盖

核心套件 6 类各 1 条；扩展套件 `suites/core-zh-expanded.yaml` 每类再 +3 条（共 18）：

- 长期保持 / 记忆调用 / 动态更新 / 相近区分 / 边界识别 / 任务复用

```bash
python -m kmb.cli list-cases --suite suites/core-zh-expanded.yaml
```

## 5. 真实 Agent（可选，需云凭据）

openKylin / Linux 上设置环境变量后：

```bash
export GROK_API_KEY=...
export DEEPSEEK_API_KEY=...
python -m kmb.cli compare \
  --agents configs/agent-grok-memory.yaml configs/agent-deepseek-memory.yaml \
  --suite suites/core-zh.yaml \
  --out runs/real-compare --seed 42 --retries 1 --timeout 180
```

见 `docs/demo-script.md` 与 `docs/final-reproduction-checklist.md`。

## 6. 结论表述边界（必读）

| 证据来源 | 可写 | 不可写 |
|----------|------|--------|
| `source=simulated`（reference/flawed） | 评测流水线可运行、可区分正确/错误记忆行为 | 真实模型能力 |
| `source=model` | API 请求/响应、可观察文本 | 模型内部记忆状态 |
| `source=wrapper` | 外部记忆控制器执行的系统级行为 | 模型原生长期记忆 |

真实 Grok/DeepSeek 轨道当前 `native_memory_events=0`，报告须分层表述。

## 7. 更多材料

- 方案：`docs/solution.md`
- 证据协议：`docs/evidence-protocol.md`
- 发布冻结：`docs/release-freeze.md`
- openKylin 演示脚本：`docs/demo-script.md`（视频待录）
- 本地 GUI：`python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .`
