# 贡献指南

提交前请运行：

```bash
python -m unittest discover -s tests -v
python -m compileall -q kmb tests
python -m kmb.cli validate --suite suites/core-zh.yaml
```

新增案例必须声明六类能力之一，提供可解释 checks，并确保运行证据写入 JSONL。新增 Agent 应实现 `AgentAdapter`，或导出 [`docs/evidence-protocol.md`](docs/evidence-protocol.md) 规定的 JSONL。

本项目采用根目录 `LICENSE` 的 MIT 许可证。贡献应遵循同一许可，并保留第三方版权声明；提交前请检查 `NOTICE` 和 `THIRD_PARTY_NOTICES.md`。许可证决定见 `docs/license-decision.md`。
