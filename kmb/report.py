import json
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List

DIMENSIONS = ["retention", "memory_recall", "dynamic_update", "similar_distinction", "boundary", "task_reuse"]


def radar_svg(dimensions: Dict[str, float], size: int = 420, score_valid: bool = True) -> str:
    import math
    center, radius = size / 2, size * 0.36
    n = len(DIMENSIONS)
    def point(index: int, value: float) -> str:
        angle = -math.pi / 2 + index * 2 * math.pi / n
        distance = radius * max(0.0, min(100.0, value)) / 100
        return "%.1f,%.1f" % (center + math.cos(angle) * distance, center + math.sin(angle) * distance)
    axes = []
    for index, key in enumerate(DIMENSIONS):
        angle = -math.pi / 2 + index * 2 * math.pi / n
        end = "%.1f,%.1f" % (center + math.cos(angle) * radius, center + math.sin(angle) * radius)
        axes.append('<line x1="%.1f" y1="%.1f" x2="%s" y2="%s" stroke="#9ca3af" />' % (center, center, end.split(",")[0], end.split(",")[1]))
    polygon = " ".join(point(i, float(dimensions.get(key, 0))) for i, key in enumerate(DIMENSIONS))
    labels = []
    for i, key in enumerate(DIMENSIONS):
        angle = -math.pi / 2 + i * 2 * math.pi / n
        x, y = center + math.cos(angle) * (radius + 24), center + math.sin(angle) * (radius + 24)
        labels.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="12">%s</text>' % (x, y, key))
    data_layer = (
        '<polygon points="%s" fill="#2563eb" fill-opacity=".25" stroke="#1d4ed8" stroke-width="2"/>' % polygon
        if score_valid else
        '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="16" fill="#991b1b">运行错误，分数无效</text>' % (center, center)
    )
    return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="white"/><g>%s</g>%s%s</svg>' % (size, size, size, size, "".join(axes), data_layer, "".join(labels))


def write_markdown(summary: Dict[str, Any], path: str) -> None:
    observability = summary.get("observability", {})
    preflight = summary.get("preflight", {})
    score_valid = summary.get("score_valid", True) is not False
    overall = "**%.2f/100**" % summary["overall"] if score_valid else "**不可评分（运行错误）**"
    lines = ["# KylinMemoryBench 评测结果", "", "- Agent: `%s`" % summary["agent"], "- Cases: %d" % summary["cases"], "- Overall: %s" % overall, "- Score status: `%s`" % summary.get("score_status", "valid" if score_valid else "invalid_runtime"), "", "## 能力边界", "", "- 观测模式: `%s`" % observability.get("mode", "memory_state_unobservable"), "- 结论限制: %s" % observability.get("disclaimer", "未提供可观测性声明"), "- 运行前预检: `%s`" % preflight.get("status", "未记录"), "- 模型原生记忆事件: %d" % int(observability.get("native_memory_events", 0)), "- 包装层记忆事件: %d" % int(observability.get("wrapper_memory_events", 0)), "- 无记忆基线事件: %d" % int(observability.get("memory_disabled_events", 0)), "- 未证实模型自述: %d" % int(observability.get("model_claims_unverified", 0)), "", "## 六维指标", "", "| 能力 | 得分 |", "|---|---:|"]
    for key in DIMENSIONS:
        value = "%.2f" % summary["dimensions"].get(key, 0.0) if score_valid else "不可评分"
        lines.append("| %s | %s |" % (key, value))
    categories = summary.get("failure_categories", {})
    lines.extend(["", "## 失败分类", "", "- " + ("；".join("%s: %s" % (key, value) for key, value in sorted(categories.items())) if categories else "无失败分类")])
    chain = summary.get("evidence_chain", {})
    lines.extend(["", "## 证据链", "", "- Schema: `%s`；事件数: %s；父事件关联数: %s；工件哈希事件数: %s；关联覆盖率: %s" % (
        summary.get("evidence_schema_version", 1), chain.get("events", 0), chain.get("parent_linked_events", 0), chain.get("artifact_events", 0), chain.get("link_coverage", 0.0)
    )])
    groups = summary.get("metamorphic_groups", [])
    if groups:
        lines.extend(["", "## 变形组", "", "| 组 | 基准 | 变体 | 结果 | 违反不变量 |", "|---|---|---|---|---|"])
        for group in groups:
            lines.append("| %s | %s | %s | %s | %s |" % (
                group.get("group_id", ""), group.get("baseline_case_id", ""), ", ".join(group.get("variant_case_ids", [])),
                "PASS" if group.get("passed") else "FAIL", json.dumps(group.get("violations", []), ensure_ascii=False),
            ))
    lines.extend(["", "## 用例明细", ""])
    for result in summary["results"]:
        lines.append("### `%s` (%s): %.2f" % (result["case_id"], result["status"], result["score"] * 100))
        case_observability = result.get("observability", {})
        lines.append("- 观测模式: `%s`；%s" % (case_observability.get("mode", "memory_state_unobservable"), case_observability.get("disclaimer", "")))
        for check in result["checks"]:
            lines.append("- %s [%s]: %s (evidence=%s)" % ("PASS" if check["passed"] else "FAIL", check.get("category", "behavior_failure"), check["reason"], json.dumps(check.get("evidence_refs", []), ensure_ascii=False)))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_compare(summaries: Iterable[Dict[str, Any]], out_dir: str) -> Dict[str, Any]:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    items = list(summaries)
    comparison = {"agents": [{
        "agent": item["agent"], "overall": item["overall"], "dimensions": item["dimensions"],
        "score_valid": item.get("score_valid", True), "score_status": item.get("score_status", "valid"),
        "completed_cases": item.get("completed_cases", item.get("cases", 0)), "error_cases": item.get("error_cases", 0),
        "agent_metadata": item.get("agent_metadata", {}), "observability": item.get("observability", {}), "preflight": item.get("preflight", {}), "failure_categories": item.get("failure_categories", {}),
        "evidence_chain": item.get("evidence_chain", {}), "metamorphic_groups": item.get("metamorphic_groups", []),
    } for item in items]}
    (destination / "comparison.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Agent 对比", "", "> 包装层分数表示模型后端与外部控制器组成的系统级行为，不证明模型原生长期记忆。", "", "| Agent | Overall | " + " | ".join(DIMENSIONS) + " | 观测模式 |", "|---|---:|" + "---:|" * len(DIMENSIONS) + "---|"]
    for item in items:
        valid = item.get("score_valid", True) is not False
        overall = "%.2f" % item["overall"] if valid else "不可评分"
        dimensions = " | ".join("%.2f" % item["dimensions"].get(key, 0) if valid else "不可评分" for key in DIMENSIONS)
        lines.append("| %s | %s | %s | %s |" % (item["agent"], overall, dimensions, item.get("observability", {}).get("mode", "memory_state_unobservable")))
    groups_by_agent = []
    for item in items:
        groups = item.get("metamorphic_groups", [])
        if groups:
            groups_by_agent.append("- `%s`: %s" % (item["agent"], "; ".join("%s=%s" % (group.get("group_id", ""), "PASS" if group.get("passed") else "FAIL") for group in groups)))
    if groups_by_agent:
        lines.extend(["", "## 变形组汇总", ""] + groups_by_agent)
    (destination / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    # One radar per agent keeps evidence tied to its source run.
    for item in items:
        (destination / (item["agent"] + "-radar.svg")).write_text(radar_svg(item["dimensions"], score_valid=item.get("score_valid", True) is not False), encoding="utf-8")
    write_html_report(items, str(destination / "comparison.html"))
    return comparison


def write_html_report(summaries: Iterable[Dict[str, Any]], path: str) -> None:
    """Write an offline report with evidence details for audit and demos."""
    items = list(summaries)
    rows = []
    for item in items:
        valid = item.get("score_valid", True) is not False
        dimensions = "".join("<td>%s</td>" % ("%.2f" % float(item.get("dimensions", {}).get(key, 0)) if valid else "不可评分") for key in DIMENSIONS)
        overall = "%.2f" % float(item.get("overall", 0)) if valid else "不可评分"
        rows.append("<tr><th>%s</th><td>%s</td>%s</tr>" % (escape(str(item.get("agent", ""))), overall, dimensions))
    details = []
    for item in items:
        agent_name = str(item.get("agent", ""))
        report_dir = Path(path).parent
        preferred_radar = report_dir / (agent_name + "-radar.svg")
        radar_name = preferred_radar.name if preferred_radar.exists() else ("radar.svg" if (report_dir / "radar.svg").exists() else "")
        radar_html = "<img src=\"%s\" alt=\"%s radar\" width=\"360\">" % (escape(radar_name), escape(agent_name)) if radar_name else ""
        observability = item.get("observability", {})
        preflight = item.get("preflight", {})
        details.append("<h2>%s</h2>%s" % (escape(agent_name), radar_html))
        details.append("<p><strong>评分状态：</strong>%s；运行错误案例=%d。运行错误时不比较能力分数。</p>" % (
            "有效" if item.get("score_valid", True) is not False else "不可评分",
            int(item.get("error_cases", 0)),
        ))
        details.append("<p><strong>能力边界：</strong>%s；%s<br>运行前预检=%s<br>原生记忆事件=%d，包装层记忆事件=%d，无记忆基线事件=%d，未证实模型自述=%d</p>" % (
            escape(str(observability.get("mode", "memory_state_unobservable"))),
            escape(str(observability.get("disclaimer", ""))),
            escape(str(preflight.get("status", "未记录"))),
            int(observability.get("native_memory_events", 0)),
            int(observability.get("wrapper_memory_events", 0)),
            int(observability.get("memory_disabled_events", 0)),
            int(observability.get("model_claims_unverified", 0)),
        ))
        chain = item.get("evidence_chain", {})
        details.append("<p><strong>证据链：</strong>schema=%s，事件=%s，父事件关联=%s，工件哈希=%s，关联覆盖率=%s</p>" % (
            escape(str(item.get("evidence_schema_version", 1))), int(chain.get("events", 0)), int(chain.get("parent_linked_events", 0)), int(chain.get("artifact_events", 0)), escape(str(chain.get("link_coverage", 0.0)))
        ))
        groups = item.get("metamorphic_groups", [])
        if groups:
            details.append("<h3>变形组</h3><ul>%s</ul>" % "".join(
                "<li>%s: %s；违反=%s</li>" % (escape(str(group.get("group_id", ""))), "PASS" if group.get("passed") else "FAIL", escape(json.dumps(group.get("violations", []), ensure_ascii=False)))
                for group in groups
            ))
        failure_counts = item.get("failure_counts", {})
        details.append("<h3>失败统计</h3><ul>%s</ul>" % "".join("<li>%s: %s</li>" % (escape(str(key)), int(value)) for key, value in sorted(failure_counts.items())))
        categories = item.get("failure_categories", {})
        details.append("<h3>失败分类</h3><ul>%s</ul>" % "".join("<li>%s: %s</li>" % (escape(str(key)), int(value)) for key, value in sorted(categories.items())))
        for result in item.get("results", []):
            details.append("<details><summary>%s: %s (%.2f)</summary>" % (escape(str(result.get("case_id", ""))), escape(str(result.get("status", ""))), float(result.get("score", 0)) * 100))
            details.append("<ul>")
            details.append("<li><strong>观测模式：</strong>%s；%s</li>" % (escape(str(result.get("observability", {}).get("mode", "memory_state_unobservable"))), escape(str(result.get("observability", {}).get("disclaimer", "")))))
            for check in result.get("checks", []):
                refs = escape(json.dumps(check.get("evidence_refs", []), ensure_ascii=False))
                details.append("<li>%s: %s <code>evidence=%s</code></li>" % ("PASS" if check.get("passed") else "FAIL", escape(str(check.get("reason", ""))), refs))
            for failure in result.get("failures", []):
                details.append("<li><strong>%s</strong> [%s]: %s</li>" % (escape(str(failure.get("type", "failure"))), escape(str(failure.get("category", "behavior_failure"))), escape(str(failure.get("reason", "")))))
            details.append("</ul></details>")
    html = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>KylinMemoryBench 对比报告</title>
<style>body{font-family:system-ui,sans-serif;margin:2rem;color:#17202a}table{border-collapse:collapse}th,td{border:1px solid #ccd;padding:.4rem .6rem;text-align:right}th:first-child,td:first-child{text-align:left}details{margin:.4rem 0;padding:.4rem;background:#f5f7fa}code{font-size:.8em}</style>
<h1>KylinMemoryBench 对比报告</h1><table><thead><tr><th>Agent</th><th>Overall</th>%s</tr></thead><tbody>%s</tbody></table>%s</html>""" % ("".join("<th>%s</th>" % escape(key) for key in DIMENSIONS), "".join(rows), "".join(details))
    Path(path).write_text(html, encoding="utf-8")
