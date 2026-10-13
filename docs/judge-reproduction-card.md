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

演示 Agent：

| Agent | 说明 |
|-------|------|
| `reference` | 离线确定性基线（`simulated`） |
| `kylinbot-process` | **openKylin 生态进程适配器**（子进程 CommandAgent，`source=process`） |
| `flawed` | 错误记忆对照（仅 contrast 目录） |

产物：

| 路径 | 含义 |
|------|------|
| `runs/offline-demo/core-compare/comparison.html` | 双 Agent 对比 + 六维雷达 |
| `runs/offline-demo/core-compare/reference-radar.svg` | 侧 A 雷达 |
| `runs/offline-demo/core-compare/kylinbot-process-radar.svg` | 侧 B 雷达 |
| `runs/offline-demo/expanded-compare/` | 扩展 18 案例 |
| `runs/offline-demo/adversarial-compare/` | 冲突/相近/噪声/敏感/跨任务 15 案例 |
| `runs/offline-demo/flawed-contrast/` | 参考 vs 缺陷对照 |

脚本在双侧均通过 `verify_run --strict` 且雷达文件存在后才成功退出。

## 3. 手动等价命令

```bash
python -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-kylinbot-process.yaml \
  --suite suites/core-zh.yaml \
  --out runs/offline-demo/core-compare \
  --seed 42 --retries 0 --timeout 30

python scripts/verify_run.py runs/offline-demo/core-compare/reference --strict
python scripts/verify_run.py runs/offline-demo/core-compare/kylinbot-process --strict
```

## 4. 套件覆盖

| 套件 | 规模 | 侧重 |
|------|------|------|
| `suites/core-zh.yaml` | 6 | 六类最小闭环 |
| `suites/core-zh-expanded.yaml` | 18 | 每类 +3 |
| `suites/adversarial/core.yaml` | 12 | 基础对抗 |
| `suites/adversarial/extended.yaml` | 15 | 冲突×3、相近实体×3、噪声×3、敏感×3、跨任务×3 |

```bash
python -m kmb.cli list-cases --suite suites/adversarial/extended.yaml
```

## 5. openKylin 进程适配器

```bash
# 协议：stdin 案例 JSON → stdout 证据 JSONL
python -m kmb.cli run \
  --agent configs/agent-kylinbot-process.yaml \
  --suite suites/core-zh.yaml \
  --out runs/kylinbot-demo --seed 42 --retries 0 --timeout 30
```

实机迁移：将 YAML 中 `command` 指向原生 KylinBot/kylin-agent 包装脚本即可，证据协议不变。

## 6. 真实 Agent（可选，需云凭据）

```bash
export GROK_API_KEY=...
export DEEPSEEK_API_KEY=...
python -m kmb.cli compare \
  --agents configs/agent-grok-memory.yaml configs/agent-deepseek-memory.yaml \
  --suite suites/core-zh.yaml \
  --out runs/real-compare --seed 42 --retries 1 --timeout 180
```

## 7. 结论表述边界（必读）

| 证据来源 | 可写 | 不可写 |
|----------|------|--------|
| `simulated` | 流水线可运行、可区分正确/错误行为 | 真实模型能力 |
| `process` / `wrapper` | 系统级进程/控制器行为 | 模型原生长期记忆 |
| `model`（native_memory_events=0） | API 文本与请求 | 原生记忆能力 |

**R0 / 门禁**：wrapper、HTTP、三件套、offline demo 属 **C 轨对照**（`C: wrapper-only` 等），**不是**赛题主结论。不同智能体长期记忆差异须在 **A/B 轨**讨论，且正式结论需被测方自有记忆事件（例如 `source=process` 的 Agent 存储事件、`source=memory_layer`，或另有 `native_memory_events>0`）通过门禁。详见 [`docs/native-memory-compare.md`](docs/native-memory-compare.md)。评审标准句：包装轨同分是因为测同一包装层。

## 8. 更多材料

- 方案：`docs/solution.md`
- 证据协议：`docs/evidence-protocol.md`
- 任务状态：`tasks/todo.md`
- 发布边界：`docs/release-freeze.md`
- 当前工作台操作：`docs/workbench.md`（旧视频稿已清理，视频待录）
- 本地 GUI：`python -m kmb.cli serve --host 127.0.0.1 --port 8765 --root .`
