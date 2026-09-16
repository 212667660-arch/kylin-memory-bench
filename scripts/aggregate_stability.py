#!/usr/bin/env python3
"""Combine repeated-run summaries for two real backends."""

import argparse
import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path

DIMENSIONS = ["retention", "memory_recall", "dynamic_update", "similar_distinction", "boundary", "task_reuse"]


def _read_summary(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = ("agent", "batch_count", "valid_batch_count", "overall", "dimensions", "runs", "observability")
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError("summary missing fields: %s" % ", ".join(missing))
    if int(payload["batch_count"]) != len(payload["runs"]):
        raise ValueError("summary batch_count does not match runs: %s" % path)
    return payload


def _finite(value):
    return value is not None and math.isfinite(float(value))


def _suite_for_summary(summary):
    """Keep comparison reports tied to the suite that produced each summary."""
    explicit = summary.get("suite")
    if explicit:
        return str(explicit)
    root = str(summary.get("runs_root", "")).replace("\\", "/").lower()
    if "innovation" in root or "lifecycle" in root:
        return "suites/lifecycle/innovation.yaml"
    return "suites/core-zh.yaml"


def build_comparison(grok_path: str, deepseek_path: str) -> dict:
    paths = {"grok": Path(grok_path), "deepseek": Path(deepseek_path)}
    source = {key: _read_summary(path) for key, path in paths.items()}
    agents = []
    for label, summary in source.items():
        agents.append({
            "label": label,
            "agent": summary["agent"],
            "batch_count": int(summary["batch_count"]),
            "valid_batch_count": int(summary["valid_batch_count"]),
            "execution_success_rate": summary.get("execution_success_rate"),
            "execution_failure_rate": summary.get("execution_failure_rate"),
            "behavioral_case_pass_rate": summary.get("behavioral_case_pass_rate"),
            "overall": summary["overall"],
            "dimensions": summary["dimensions"],
            "latency_ms": summary.get("latency_ms", {}),
            "failure_counts": summary.get("failure_counts", {}),
            "innovation_metrics": summary.get("innovation_metrics", {}),
            "metamorphic": summary.get("metamorphic", {}),
            "lifecycle": summary.get("lifecycle", {}),
            "actions": summary.get("actions", {}),
            "evidence_chain": summary.get("evidence_chain", {}),
            "security_red_team_failure_counts": summary.get("security_red_team_failure_counts", {}),
            "consistency": summary.get("consistency", {}),
            "observability": summary.get("observability", {}),
            "source_summary": str(paths[label]),
            "runs": summary.get("runs", []),
        })
    grok, deepseek = agents
    difference = None
    if _finite(grok["overall"].get("mean")) and _finite(deepseek["overall"].get("mean")):
        difference = round(float(grok["overall"]["mean"]) - float(deepseek["overall"]["mean"]), 4)
    modes = sorted(set((source["grok"].get("observability") or {}).get("mode", [])) | set((source["deepseek"].get("observability") or {}).get("mode", [])))
    wrapper = "system_level_wrapper_assisted" in modes
    suites = {_suite_for_summary(summary) for summary in source.values()}
    suite = next(iter(suites)) if len(suites) == 1 else "mixed"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite": suite,
        "mode": "system_level_wrapper_assisted" if wrapper else "system_level_no_memory_baseline",
        "disclaimer": ("Statistics describe repeated system-level behavior of each model backend plus the same external memory/action wrapper; they do not prove native model memory."
                       if wrapper else "Statistics describe real model backends with the external memory controller disabled; they do not prove native model memory."),
        "agents": agents,
        "comparison": {
            "overall_mean_difference_grok_minus_deepseek": difference,
            "same_case_suite": len(suites) == 1,
            "same_seed": True,
            "same_timeout_and_retries": True,
            "cross_agent_stability_claim": "descriptive_only",
        },
    }


def _svg(payload: dict) -> str:
    size, center, radius = 520, 260, 175
    count = len(DIMENSIONS)

    def point(index, value):
        import math as m
        angle = -m.pi / 2 + index * 2 * m.pi / count
        distance = radius * max(0.0, min(100.0, float(value or 0))) / 100
        return center + m.cos(angle) * distance, center + m.sin(angle) * distance

    import math as m
    axes, labels = [], []
    for index, key in enumerate(DIMENSIONS):
        angle = -m.pi / 2 + index * 2 * m.pi / count
        x, y = center + m.cos(angle) * radius, center + m.sin(angle) * radius
        axes.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#9ca3af"/>' % (center, center, x, y))
        labels.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="12">%s</text>' % (center + m.cos(angle) * (radius + 28), center + m.sin(angle) * (radius + 28), html.escape(key)))
    polygons = []
    colors = {"grok": "#2563eb", "deepseek": "#dc2626"}
    for agent in payload["agents"]:
        values = [agent["dimensions"].get(key, {}).get("mean", 0) for key in DIMENSIONS]
        polygon = " ".join("%.1f,%.1f" % point(index, value) for index, value in enumerate(values))
        color = colors.get(agent["label"], "#4b5563")
        polygons.append('<polygon points="%s" fill="%s" fill-opacity=".18" stroke="%s" stroke-width="2"/>' % (polygon, color, color))
    return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="white"/><text x="24" y="26" font-size="14">Grok mean (blue) / DeepSeek mean (red)</text>%s%s%s</svg>' % (size, size, size, size, "".join(axes), "".join(labels), "".join(polygons))


def _markdown(payload: dict) -> str:
    lines = ["# 双 Agent 稳定性汇总", "", "> %s" % payload["disclaimer"], "", "- 套件：`%s`" % payload["suite"], "- 比较约束：同一套件、seed、超时、重试和评分器；跨 Agent 稳定性仅作描述性统计。", "", "| Agent | 批次 | 执行成功率 | Overall 均值 | 标准差 | 最小 | 最大 | 一致性 |", "|---|---:|---:|---:|---:|---:|---:|---|"]
    for agent in payload["agents"]:
        item = agent["overall"]
        lines.append("| %s | %d | %s%% | %s | %s | %s | %s | %s |" % (agent["agent"], agent["batch_count"], agent.get("execution_success_rate"), item.get("mean"), item.get("stdev"), item.get("min"), item.get("max"), str(agent["consistency"].get("overall_all_equal", False)).lower()))
    lines.extend(["", "## 六维均值", "", "| Agent | %s |" % " | ".join(DIMENSIONS), "|---|" + "|".join("---:" for _ in DIMENSIONS) + "|"])
    for agent in payload["agents"]:
        lines.append("| %s | %s |" % (agent["agent"], " | ".join(str(agent["dimensions"].get(key, {}).get("mean")) for key in DIMENSIONS)))
    lines.extend(["", "## 创新层统计", "", "| Agent | 变形组通过率 | 生命周期状态转换正确率 | 实际动作成功率 | 证据链完整批次率 | 安全失败类型 |", "|---|---:|---:|---:|---:|---|"])
    for agent in payload["agents"]:
        innovation = agent.get("innovation_metrics", {})
        lines.append("| %s | %s%% | %s%% | %s%% | %s%% | %s |" % (
            agent["agent"],
            (agent.get("metamorphic") or {}).get("pass_rate"),
            (agent.get("lifecycle") or {}).get("state_transition_correctness"),
            (agent.get("actions") or {}).get("success_rate"),
            (agent.get("evidence_chain") or {}).get("complete_rate"),
            html.escape(json.dumps(agent.get("security_red_team_failure_counts", {}), ensure_ascii=False)),
        ))
    lines.extend(["", "## 证据路径", ""])
    for agent in payload["agents"]:
        lines.append("- `%s`：`%s`；原生记忆事件合计 `%s`。" % (agent["agent"], agent["source_summary"], agent["observability"].get("native_memory_events", 0)))
    return "\n".join(lines) + "\n"


def _html(payload: dict) -> str:
    rows, details = [], []
    for agent in payload["agents"]:
        item = agent["overall"]
        rows.append("<tr><th>%s</th><td>%s</td><td>%s%%</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (html.escape(agent["agent"]), agent["batch_count"], agent.get("execution_success_rate"), item.get("mean"), item.get("stdev"), item.get("min"), item.get("max")))
        failures = "".join("<li>%s: %s</li>" % (html.escape(str(key)), value) for key, value in sorted(agent.get("failure_counts", {}).items()))
        details.append("<details><summary>%s</summary><p>Summary: %s</p><p>Native memory events: %s</p><p>Metamorphic pass: %s%%; lifecycle state correctness: %s%%; action success: %s%%; evidence-chain complete batches: %s%%.</p><ul>%s</ul></details>" % (html.escape(agent["agent"]), html.escape(agent["source_summary"]), agent["observability"].get("native_memory_events", 0), (agent.get("metamorphic") or {}).get("pass_rate"), (agent.get("lifecycle") or {}).get("state_transition_correctness"), (agent.get("actions") or {}).get("success_rate"), (agent.get("evidence_chain") or {}).get("complete_rate"), failures))
    return "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\"><title>Dual-agent stability</title><style>body{font-family:system-ui,sans-serif;margin:2rem}table{border-collapse:collapse}th,td{border:1px solid #ccd;padding:.4rem .6rem}details{margin:.5rem 0;padding:.5rem;background:#f5f7fa}</style><h1>Dual-agent stability</h1><p>%s</p><img src=\"stability-radar.svg\" alt=\"mean dimension radar\" width=\"520\"><table><tr><th>Agent</th><th>Batches</th><th>Execution success</th><th>Mean</th><th>Stddev</th><th>Min</th><th>Max</th></tr>%s</table>%s</html>" % (html.escape(payload["disclaimer"]), "".join(rows), "".join(details))


def write_outputs(payload: dict, output_path: str) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(_markdown(payload), encoding="utf-8")
    output.with_suffix(".html").write_text(_html(payload), encoding="utf-8")
    output.with_name("stability-radar.svg").write_text(_svg(payload), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate two repeated-run summaries")
    parser.add_argument("--grok-summary", required=True)
    parser.add_argument("--deepseek-summary", required=True)
    parser.add_argument("--out", required=True, help="JSON output path")
    args = parser.parse_args(argv)
    payload = build_comparison(args.grok_summary, args.deepseek_summary)
    write_outputs(payload, args.out)
    print(json.dumps({"status": "ok", "out": args.out, "agents": [item["agent"] for item in payload["agents"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
