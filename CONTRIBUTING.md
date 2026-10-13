# 贡献指南

可通过 [Issues](https://github.com/212667660-arch/kylin-memory-bench/issues) 反馈安装、评测或工作台问题。请使用问题模板记录版本、环境、复现步骤及实际结果，日志先移除凭据和个人信息。功能建议可直接开 Issue 说明使用场景。

提交改动时从 `main` 创建分支，并通过 Pull Request 说明问题、行为变化和实际验证结果。案例、评分与 Agent 适配器的改动应同时说明证据来源，不能将包装层事件作为模型原生记忆证据。

提交前请运行：

```bash
python -m unittest discover -s tests -v
python -m compileall -q kmb tests
python -m kmb.cli validate --suite suites/core-zh.yaml
```

新增案例必须声明六类能力之一，提供可解释 checks，并确保运行证据写入 JSONL。新增 Agent 应实现 `AgentAdapter`，或导出 [`docs/evidence-protocol.md`](docs/evidence-protocol.md) 规定的 JSONL。

本项目采用根目录 `LICENSE` 的 MIT 许可证。贡献应遵循同一许可，并保留第三方版权声明；提交前请检查 `NOTICE` 和 `THIRD_PARTY_NOTICES.md`。许可证决定见 `docs/license-decision.md`。
