# 贡献指南

提交前请运行：

```bash
python -m unittest discover -s tests -v
python -m compileall -q kmb tests
python -m kmb.cli validate --suite suites/core-zh.yaml
```

新增案例必须声明六类能力之一，提供可解释 checks，并确保运行证据写入 JSONL。新增 Agent 应实现 `AgentAdapter`，或导出 [`docs/evidence-protocol.md`](docs/evidence-protocol.md) 规定的 JSONL。

许可证和仓库托管策略目前仍待项目负责人确认，确认前请不要在文件头添加未批准的许可证声明。
`LICENSE-MIT-CANDIDATE.txt` 是非生效候选文本；提交前还应检查 `NOTICE` 和 `THIRD_PARTY_NOTICES.md`，不得把候选文本当作最终授权。
