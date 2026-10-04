#!/usr/bin/env python3
"""Aggregate repeated benchmark runs without changing their evidence.

The report separates execution failures from behavioral failures.  It only
reads result.json/evidence.jsonl files and never loads credentials.
"""

import argparse
import json
import math
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_run import verify_run

DIMENSIONS = ["retention", "memory_recall", "dynamic_update", "similar_distinction", "boundary", "task_reuse"]
LIFECYCLE_CHECK_TYPES = {"state_sequence"}
SECURITY_FAILURE_TERMS = ("sensitive", "scope", "persist", "token", "leak", "reuse", "boundary")


def _stats(values):
    numbers = [float(value) for value in values]
    if not numbers:
        return {"count": 0, "mean": None, "stdev": None, "min": None, "max": None}
    return {
        "count": len(numbers),
        "mean": round(statistics.mean(numbers), 4),
        "stdev": round(statistics.stdev(numbers), 4) if len(numbers) > 1 else 0.0,
        "min": round(min(numbers), 4),
        "max": round(max(numbers), 4),
    }


def _latency(evidence_path):
    values = []
    with evidence_path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            raw = json.loads(line)
            if raw.get("kind") != "model_response":
                continue
            elapsed = raw.get("data", {}).get("elapsed_ms")
            if isinstance(elapsed, (int, float)) and math.isfinite(float(elapsed)):
                values.append(float(elapsed))
    return values


def _innovation_metrics(result, evidence_rows):
    """Extract deterministic innovation metrics from already scored evidence."""
    groups = result.get("metamorphic_groups") or []
    group_passed = sum(1 for group in groups if group.get("passed") is True)
    state_checks = []
    for row in result.get("results") or []:
        for check in row.get("checks") or []:
            if (check.get("check") or {}).get("type") in LIFECYCLE_CHECK_TYPES:
                state_checks.append(bool(check.get("passed")))
    actions = [row for row in evidence_rows if row.get("kind") == "action"]
    successful_actions = sum(1 for row in actions if row.get("data", {}).get("executed") is True and row.get("data", {}).get("exit_code") == 0)
    chain = result.get("evidence_chain") or {}
    failure_counts = result.get("failure_counts") or {}
    security_failures = {
        str(key): int(value) for key, value in failure_counts.items()
        if any(term in str(key).lower() for term in SECURITY_FAILURE_TERMS)
    }
    return {
        "metamorphic_group_count": len(groups),
        "metamorphic_group_passed": group_passed,
        "metamorphic_group_pass_rate": round(group_passed / len(groups) * 100, 4) if groups else None,
        "lifecycle_state_sequence_checks": len(state_checks),
        "lifecycle_state_sequence_passed": sum(state_checks),
        "lifecycle_state_transition_correctness": round(sum(state_checks) / len(state_checks) * 100, 4) if state_checks else None,
        "action_count": len(actions),
        "action_success_count": successful_actions,
        "action_success_rate": round(successful_actions / len(actions) * 100, 4) if actions else None,
        "evidence_chain_link_coverage": chain.get("link_coverage"),
        "evidence_chain_complete": bool(chain.get("link_coverage") == 1.0),
        "artifact_events": int(chain.get("artifact_events", 0) or 0),
        "security_red_team_failure_counts": security_failures,
    }


def _failure_class(category):
    value = str(category or "runtime_error").lower()
    if any(term in value for term in ("billing", "quota", "balance", "payment", "402")):
        return "billing"
    if any(term in value for term in ("credential", "auth", "unauthorized", "forbidden", "401", "403")):
        return "credential"
    if any(term in value for term in ("provider", "http_4", "http_5", "api_error")):
        return "provider"
    if "timeout" in value or "timed_out" in value:
        return "timeout"
    if any(term in value for term in ("behavior", "boundary", "recall", "mismatch", "incorrect", "missing_memory")):
        return "behavior"
    return "runtime"
def aggregate_repeats(runs_root, output_path=None, pattern="repeat-*"):
    root = Path(runs_root)
    if not root.exists():
        raise ValueError("runs root does not exist: %s" % root)
    directories = sorted(path for path in root.glob(pattern) if path.is_dir())
    if not directories:
        raise ValueError("no run directories matched %s under %s" % (pattern, root))

    records = []
    failures = Counter()
    overall_values = []
    dimension_values = {key: [] for key in DIMENSIONS}
    latency_values = []
    metric_values = {
        "metamorphic_group_pass_rate": [],
        "lifecycle_state_transition_correctness": [],
        "action_success_rate": [],
        "evidence_chain_link_coverage": [],
    }
    security_failures = Counter()
    failure_types = Counter()
    source_counts = Counter()
    metamorphic_group_count = metamorphic_group_passed = 0
    lifecycle_check_count = lifecycle_check_passed = 0
    action_count = action_success_count = 0
    artifact_event_count = 0
    execution_error_runs = 0
    strict_invalid_runs = 0
    score_valid_runs = 0
    case_count = 0
    passing_cases = 0

    for directory in directories:
        result_path = directory / "result.json"
        evidence_path = directory / "evidence.jsonl"
        if not result_path.exists() or not evidence_path.exists():
            strict_invalid_runs += 1
            records.append({"directory": str(directory), "verification_status": "invalid", "verification_error": "missing result.json or evidence.jsonl", "score_valid": False, "overall": None, "failure_counts": {}})
            continue
        try:
            verification = verify_run(str(directory), strict=True)
        except Exception as exc:
            strict_invalid_runs += 1
            records.append({"directory": str(directory), "verification_status": "invalid", "verification_error": str(exc), "score_valid": False, "overall": None, "failure_counts": {}})
            continue
        result = json.loads(result_path.read_text(encoding="utf-8"))
        evidence_rows = [json.loads(line) for line in evidence_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        run_failures = {str(key): int(value) for key, value in (result.get("failure_counts") or {}).items()}
        failures.update(run_failures)
        errors = [row for row in evidence_rows if row.get("kind") == "error"]
        for error in errors:
            category = str((error.get("data") or {}).get("category") or (error.get("data") or {}).get("failure_type") or "runtime_error")
            failure_types[_failure_class(category)] += 1
        if errors:
            execution_error_runs += 1
        rows = result.get("results") or []
        runtime_cases = {str(row.get("case_id")) for row in errors}
        for case in rows:
            if case.get("status") != "pass" and str(case.get("case_id")) not in runtime_cases:
                failure_types["behavior"] += 1
        declared_score_valid = result.get("score_valid")
        if declared_score_valid is None:
            # Preserve compatibility with historical summaries that predate
            # the explicit field, while still rejecting runtime-invalid runs.
            score_valid = not errors and result.get("score_status") not in {"invalid", "invalid_runtime"}
        else:
            score_valid = declared_score_valid is True
        if score_valid:
            score_valid_runs += 1
            case_count += len(rows)
            passing_cases += sum(1 for row in rows if row.get("status") == "pass")
        overall = float(result.get("overall", 0.0)) if score_valid else None
        if score_valid:
            overall_values.append(overall)
        dimensions = result.get("dimensions") or {}
        if score_valid:
            for key in DIMENSIONS:
                if key in dimensions:
                    dimension_values[key].append(float(dimensions[key]))
        latencies = _latency(evidence_path)
        latency_values.extend(latencies)
        innovation = _innovation_metrics(result, evidence_rows)
        for key in metric_values:
            value = innovation.get(key)
            if value is not None:
                metric_values[key].append(float(value))
        metamorphic_group_count += innovation["metamorphic_group_count"]
        metamorphic_group_passed += innovation["metamorphic_group_passed"]
        lifecycle_check_count += innovation["lifecycle_state_sequence_checks"]
        lifecycle_check_passed += innovation["lifecycle_state_sequence_passed"]
        action_count += innovation["action_count"]
        action_success_count += innovation["action_success_count"]
        artifact_event_count += innovation["artifact_events"]
        security_failures.update(innovation["security_red_team_failure_counts"])
        sources = (result.get("observability") or {}).get("sources") or {}
        for row in evidence_rows:
            source = row.get("source") or (row.get("data") or {}).get("source")
            if source:
                sources[source] = int(sources.get(source, 0)) + 1
        for source in ("process", "wrapper", "model", "simulated"):
            if int(sources.get(source, 0)) > 0:
                source_counts[source] += 1
        records.append({
            "directory": str(directory),
            "verification_status": "valid",
            "run_id": result.get("run_id"),
            "agent": result.get("agent"),
            "overall": overall,
            "score_valid": score_valid,
            "dimensions": {key: dimensions.get(key) for key in DIMENSIONS},
            "cases": int(result.get("cases", len(rows))),
            "evidence_events": verification["evidence_events"],
            "model_responses": len(latencies),
            "latency_ms": _stats(latencies),
            "failure_counts": run_failures,
            "execution_error_events": len(errors),
            "mode": (result.get("observability") or {}).get("mode"),
            "native_memory_events": int((result.get("observability") or {}).get("native_memory_events", 0)),
            "innovation_metrics": innovation,
        })

    dimension_stats = {key: _stats(values) for key, values in dimension_values.items()}
    consistency = {
        "overall_all_equal": bool(overall_values) and len(set(overall_values)) <= 1,
        "dimensions_all_equal": bool(overall_values) and all(len(set(values)) <= 1 for values in dimension_values.values() if values),
        "identical_result_count": sum(1 for value in overall_values if value == overall_values[0]) if overall_values else 0,
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs_root": str(root),
        "pattern": pattern,
        "agent": records[0].get("agent") if records else None,
        "batch_count": len(records),
        "valid_batch_count": sum(1 for record in records if record.get("verification_status") == "valid"),
        "strict_invalid_count": strict_invalid_runs,
        "score_valid_count": score_valid_runs,
        "score_valid_rate": round(score_valid_runs / len(directories), 4) if directories else 0.0,
        "execution_success_count": sum(1 for record in records if record.get("verification_status") == "valid" and not record.get("execution_error_events")),
        "execution_failure_count": len(directories) - sum(1 for record in records if record.get("verification_status") == "valid" and not record.get("execution_error_events")),
        "execution_success_rate": round(sum(1 for record in records if record.get("verification_status") == "valid" and not record.get("execution_error_events")) / len(directories) * 100, 2) if directories else 0.0,
        "execution_failure_rate": round((len(directories) - sum(1 for record in records if record.get("verification_status") == "valid" and not record.get("execution_error_events"))) / len(directories) * 100, 2) if directories else 0.0,
        "success_rate": round(sum(1 for record in records if record.get("verification_status") == "valid" and not record.get("execution_error_events")) / len(directories), 4) if directories else 0.0,
        "score_valid_rate_percent": round(score_valid_runs / len(directories) * 100, 2) if directories else 0.0,
        "behavioral_case_count": case_count,
        "behavioral_pass_count": passing_cases,
        "behavioral_case_pass_rate": round(passing_cases / case_count * 100, 2) if case_count else 0.0,
        "overall": _stats(overall_values),
        "dimensions": dimension_stats,
        "latency_ms": _stats(latency_values),
        "innovation_metrics": {key: _stats(values) for key, values in metric_values.items()},
        "metamorphic": {
            "group_count": metamorphic_group_count,
            "passed_count": metamorphic_group_passed,
            "pass_rate": round(metamorphic_group_passed / metamorphic_group_count * 100, 4) if metamorphic_group_count else None,
        },
        "lifecycle": {
            "state_sequence_check_count": lifecycle_check_count,
            "state_sequence_passed_count": lifecycle_check_passed,
            "state_transition_correctness": round(lifecycle_check_passed / lifecycle_check_count * 100, 4) if lifecycle_check_count else None,
        },
        "actions": {
            "count": action_count,
            "success_count": action_success_count,
            "success_rate": round(action_success_count / action_count * 100, 4) if action_count else None,
        },
        "evidence_chain": {
            "complete_run_count": sum(1 for value in metric_values["evidence_chain_link_coverage"] if value == 1.0),
            "run_count": len(records),
            "complete_rate": round(sum(1 for value in metric_values["evidence_chain_link_coverage"] if value == 1.0) / len(records) * 100, 4) if records else 0.0,
            "artifact_events": artifact_event_count,
        },
        "security_red_team_failure_counts": dict(sorted(security_failures.items())),
        "failure_counts": dict(sorted(failures.items())),
        "failure_types": {key: failure_types.get(key, 0) for key in ("provider", "billing", "credential", "timeout", "runtime", "behavior")},
        "source": max(source_counts, key=source_counts.get) if source_counts else "simulated",
        "source_counts": dict(sorted(source_counts.items())),
        "consistency": consistency,
        "observability": {
            "mode": sorted(set(record.get("mode") for record in records)),
            "native_memory_events": sum(record["native_memory_events"] for record in records),
            "disclaimer": _disclaimer(sorted(set(record.get("mode") for record in records))),
        },
        "runs": records,
    }
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _write_markdown(payload, output.with_suffix(".md"))
    return payload


def aggregate_repeat_runs(runs_root, output_path=None, pattern="repeat-*"):
    """Stable public API used by the official acceptance report."""
    return aggregate_repeats(runs_root, output_path=output_path, pattern=pattern)


def _disclaimer(modes):
    modes = set(modes)
    if "system_level_wrapper_assisted" in modes:
        return "Statistics describe repeated system-level behavior of the model backend plus the external memory/action wrapper; they do not prove native model memory."
    if "no_memory_baseline" in modes or "system_level_no_memory_baseline" in modes:
        return "Statistics describe repeated system-level no-memory baseline runs; they do not prove native model memory."
    return "Statistics describe observed benchmark runs; native model memory is not established without native state events."


def _write_markdown(payload, path):
    lines = [
        "# 重复运行稳定性汇总", "", 
        "> %s" % payload["observability"]["disclaimer"], "",
        "- 批次：%d" % payload["batch_count"],
        "- 严格结构有效批次：%d/%d" % (payload["valid_batch_count"], payload["batch_count"]),
        "- 执行成功率：%.2f%%" % payload["execution_success_rate"],
        "- 有效分数率：%.2f%%" % payload["score_valid_rate_percent"],
        "- 行为案例通过率：%.2f%%" % payload["behavioral_case_pass_rate"],
        "- Overall 均值/标准差/最小/最大：%(mean)s / %(stdev)s / %(min)s / %(max)s" % payload["overall"],
        "- 模型响应延迟均值/标准差/最小/最大(ms)：%(mean)s / %(stdev)s / %(min)s / %(max)s" % payload["latency_ms"],
        "", "## 六维统计", "", "| 能力 | 均值 | 标准差 | 最小 | 最大 |", "|---|---:|---:|---:|---:|",
    ]
    for key in DIMENSIONS:
        item = payload["dimensions"][key]
        lines.append("| %s | %s | %s | %s | %s |" % (key, item["mean"], item["stdev"], item["min"], item["max"]))
    lines.extend(["", "## 创新层统计", "", "| 指标 | 均值 | 标准差 | 最小 | 最大 |", "|---|---:|---:|---:|---:|"])
    for key, item in payload.get("innovation_metrics", {}).items():
        lines.append("| %s | %s | %s | %s | %s |" % (key, item["mean"], item["stdev"], item["min"], item["max"]))
    lines.extend(["", "- 变形组通过率：%s%%（%s/%s）" % (payload["metamorphic"]["pass_rate"], payload["metamorphic"]["passed_count"], payload["metamorphic"]["group_count"]), "- 生命周期状态转换正确率：%s%%（%s/%s）" % (payload["lifecycle"]["state_transition_correctness"], payload["lifecycle"]["state_sequence_passed_count"], payload["lifecycle"]["state_sequence_check_count"]), "- 实际动作成功率：%s%%（%s/%s）" % (payload["actions"]["success_rate"], payload["actions"]["success_count"], payload["actions"]["count"]), "- 证据链完整批次率：%s%%" % payload["evidence_chain"]["complete_rate"], "- 安全红队失败类型：%s" % json.dumps(payload["security_red_team_failure_counts"], ensure_ascii=False)])
    lines.extend(["", "## 失败类型合计", ""])
    for key, value in sorted(payload["failure_counts"].items()):
        lines.append("- %s: %d" % (key, value))
    lines.extend(["", "## 批次", "", "| Run ID | Overall | 证据事件 | 模型响应 | 延迟均值(ms) |", "|---|---:|---:|---:|---:|"])
    for record in payload["runs"]:
        if record.get("verification_status") != "valid":
            lines.append("| `%s` | strict verify 失败 | 0 | 0 | - |" % record.get("directory"))
        else:
            overall = "%.2f" % record["overall"] if record.get("score_valid") else "不可评分"
            lines.append("| `%s` | %s | %d | %d | %s |" % (record.get("run_id"), overall, record["evidence_events"], record["model_responses"], record["latency_ms"]["mean"]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Aggregate repeated KylinMemoryBench runs")
    parser.add_argument("runs_root", help="directory containing repeat-* run directories")
    parser.add_argument("--out", required=True, help="JSON output path; Markdown is written beside it")
    parser.add_argument("--pattern", default="repeat-*")
    args = parser.parse_args(argv)
    try:
        payload = aggregate_repeats(args.runs_root, args.out, args.pattern)
    except Exception as exc:
        print("aggregate failed: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps({"status": "ok", "batch_count": payload["batch_count"], "out": args.out}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
