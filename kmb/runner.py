import json
import hashlib
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from .agents import AgentAdapter
from .agent_adapters.base import ERROR_CATEGORIES, classify_error
from .models import BenchmarkCase, EvidenceEvent, ScoreResult, summarize_evidence
from .scoring import score_case, score_metamorphic_groups, validate_answer_check

SUPPORTED_CAPABILITIES = {
    "retention", "memory_recall", "dynamic_update", "similar_distinction", "boundary", "task_reuse",
}
SUPPORTED_CHECKS = {
    "answer_contains", "answer_not_contains", "memory_recall", "memory_absent", "memory_value",
    "memory_expired", "scope_isolation", "sensitive_not_persisted", "memory_version",
    "action_path", "action_tool", "artifact_exists", "artifact_contains", "action_exit_code",
    "restart_boundary", "evidence_chain", "state_sequence",
}


def load_suite(path: str) -> List[BenchmarkCase]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if isinstance(raw, list):
        cases = raw
    elif isinstance(raw, dict):
        cases = raw.get("cases", [])
    else:
        raise ValueError("suite must be a mapping with cases or a case list")
    return [BenchmarkCase.from_dict(item) for item in cases]


def validate_cases(cases: Iterable[BenchmarkCase], require_all_capabilities: bool = False) -> None:
    cases = list(cases)
    seen = set()
    for case in cases:
        if case.id in seen:
            raise ValueError("duplicate case id: %s" % case.id)
        seen.add(case.id)
        if case.capability not in SUPPORTED_CAPABILITIES:
            raise ValueError("unsupported capability '%s' in case %s" % (case.capability, case.id))
        for check in case.checks:
            check_type = str(check.get("type", ""))
            if check_type not in SUPPORTED_CHECKS:
                raise ValueError("unsupported check type '%s' in case %s" % (check_type, case.id))
            validate_answer_check(check, len(case.turns))
        for fact in case.facts:
            if not fact.get("fact_id") or not fact.get("key"):
                raise ValueError("fact metadata requires fact_id and key in case %s" % case.id)
            if int(fact.get("version", 1)) < 1:
                raise ValueError("fact metadata version must be positive in case %s" % case.id)
        if case.metamorphic:
            if not case.metamorphic.get("group_id"):
                raise ValueError("metamorphic case requires group_id: %s" % case.id)
            if case.metamorphic.get("role") not in (None, "baseline", "variant"):
                raise ValueError("metamorphic role must be baseline or variant: %s" % case.id)
        if not isinstance(case.action_assertions, list):
            raise ValueError("action_assertions must be a list in case %s" % case.id)
    if require_all_capabilities:
        missing = sorted(SUPPORTED_CAPABILITIES - {case.capability for case in cases})
        if missing:
            raise ValueError("suite missing capabilities: " + ", ".join(missing))


def run_suite(
    agent: AgentAdapter,
    cases: Iterable[BenchmarkCase],
    out_dir: str,
    timeout_seconds: float = 30.0,
    retries: int = 0,
    run_id: str = None,
    seed: int = None,
) -> Dict[str, Any]:
    cases = list(cases)
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    all_scores: List[ScoreResult] = []
    failure_counts = Counter()
    failure_categories = Counter()
    case_events: Dict[str, List[EvidenceEvent]] = {}
    resolved_run_id = run_id or uuid.uuid4().hex[:12]
    evidence_path = destination / "evidence.jsonl"
    with evidence_path.open("w", encoding="utf-8") as evidence_file:
        for case in cases:
            events: List[EvidenceEvent] = []
            attempt_events: List[EvidenceEvent] = []
            error = None
            attempts = 0
            for attempt in range(max(0, retries) + 1):
                attempts = attempt + 1
                started = time.monotonic()
                try:
                    events = agent.run(case)
                    if time.monotonic() - started > timeout_seconds:
                        raise TimeoutError("agent exceeded %.2fs" % timeout_seconds)
                    error = None
                    break
                except Exception as exc:
                    error = "%s: %s" % (type(exc).__name__, exc)
                    error_name = classify_error(exc)
                    failure_counts[error_name] += 1
                    error_data = {
                        "message": error,
                        "attempt": attempts,
                        "category": error_name,
                        "exception_type": type(exc).__name__,
                    }
                    for field_name in ("returncode", "stdout_tail", "stderr_tail"):
                        value = getattr(exc, field_name, None)
                        if value not in (None, ""):
                            error_data[field_name] = value
                    error_event = EvidenceEvent("error", error_data, 0, source="runner")
                    attempt_events.append(error_event)
                    events = [error_event]
            # Keep every failed attempt for audit, while scoring the final attempt only.
            evidence_events = attempt_events + ([] if attempt_events and attempt_events[-1] is events[0] else events)
            correlation_id = "%s:%s" % (resolved_run_id, case.id)
            previous_event_id = ""
            for index, event in enumerate(evidence_events, 1):
                if not event.event_id:
                    event.event_id = "%s:%03d:%s" % (correlation_id, index, uuid.uuid4().hex[:8])
                if not event.correlation_id:
                    event.correlation_id = correlation_id
                if not event.parent_event_id and previous_event_id:
                    event.parent_event_id = previous_event_id
                if not event.fact_id:
                    event.fact_id = str(event.data.get("fact_id") or "")
                if event.fact_version is None and event.data.get("fact_version") is not None:
                    event.fact_version = int(event.data.get("fact_version"))
                if not event.scope:
                    event.scope = str(event.data.get("scope") or "")
                if not event.artifact_path:
                    event.artifact_path = str(event.data.get("artifact_path") or event.data.get("actual_path") or "")
                if not event.artifact_sha256:
                    event.artifact_sha256 = str(event.data.get("artifact_sha256") or "")
                if event.artifact_path and not event.artifact_sha256:
                    artifact = Path(event.artifact_path)
                    if artifact.is_file():
                        event.artifact_sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
                event.data.setdefault("event_id", event.event_id)
                event.data.setdefault("correlation_id", event.correlation_id)
                if event.parent_event_id:
                    event.data.setdefault("parent_event_id", event.parent_event_id)
                if event.fact_id:
                    event.data.setdefault("fact_id", event.fact_id)
                if event.fact_version is not None:
                    event.data.setdefault("fact_version", event.fact_version)
                if event.scope:
                    event.data.setdefault("scope", event.scope)
                if event.artifact_path:
                    event.data.setdefault("artifact_path", event.artifact_path)
                if event.artifact_sha256:
                    event.data.setdefault("artifact_sha256", event.artifact_sha256)
                event.data.setdefault("trust_level", event.trust_level)
                previous_event_id = event.event_id
            for event in evidence_events:
                evidence_file.write(json.dumps({"run_id": resolved_run_id, "agent": agent.name, "case_id": case.id, **event.to_dict()}, ensure_ascii=False) + "\n")
            case_events[case.id] = list(events)
            score = score_case(case, events)
            score.observability = summarize_evidence(evidence_events)
            if error:
                error_category = str((evidence_events[-1].data if evidence_events else {}).get("category") or "runtime_error")
                score.status, score.score = "error", 0.0
                score.failures.append({"type": error_category, "category": error_category, "reason": error, "check": {}, "evidence_refs": [{"kind": "error", "step": 0, "source": "runner", "evidence_class": "runtime_error", "category": error_category}]})
            for failure in score.failures:
                failure_type = failure.get("type", "invalid_behavior")
                # Runtime categories were counted once per failed attempt in
                # the exception path above. Only behavioral failure types are
                # added here.
                if failure_type not in ERROR_CATEGORIES:
                    failure_counts[failure_type] += 1
                failure_categories[str(failure.get("category") or "behavior_failure")] += 1
            score.attempts = attempts
            all_scores.append(score)
    by_capability: Dict[str, List[float]] = {}
    for result in all_scores:
        by_capability.setdefault(result.capability, []).append(result.score)
    dimensions = {key: round(sum(values) / len(values) * 100, 2) for key, values in by_capability.items()}
    metamorphic_groups = score_metamorphic_groups(cases, all_scores, case_events)
    evidence_chain = {
        "schema_version": 2,
        "events": sum(len(events) for events in case_events.values()),
        "linked_events": sum(1 for events in case_events.values() for event in events if event.event_id and event.correlation_id),
        "parent_linked_events": sum(1 for events in case_events.values() for event in events if event.parent_event_id),
        "artifact_events": sum(1 for events in case_events.values() for event in events if event.artifact_sha256),
    }
    evidence_chain["link_coverage"] = round(evidence_chain["linked_events"] / evidence_chain["events"], 4) if evidence_chain["events"] else 0.0
    error_cases = sum(1 for item in all_scores if item.status == "error")
    summary = {
        "run_id": resolved_run_id, "started_at": datetime.now(timezone.utc).isoformat(),
        "agent": agent.name, "cases": len(all_scores), "seed": seed, "retries": retries,
        "agent_metadata": agent.describe() if hasattr(agent, "describe") else {"adapter": type(agent).__name__, "agent": agent.name},
        "score_valid": error_cases == 0,
        "score_status": "valid" if error_cases == 0 else "invalid_runtime",
        "completed_cases": len(all_scores) - error_cases,
        "error_cases": error_cases,
        "observability": {"mode": "memory_state_unobservable", "disclaimer": "Per-case observability is authoritative; native memory is not inferred from text."},
        "dimensions": dimensions, "failure_counts": dict(failure_counts), "failure_categories": dict(failure_categories),
        "overall": round(sum(item.score for item in all_scores) / len(all_scores) * 100, 2) if all_scores else 0.0,
        "results": [item.to_dict() for item in all_scores], "evidence": str(evidence_path),
        "evidence_schema_version": 2, "evidence_chain": evidence_chain, "metamorphic_groups": metamorphic_groups,
    }
    # Aggregate observability from the per-case summaries without re-reading raw JSONL.
    case_observability = [item.observability for item in all_scores]
    modes = {item.get("mode") for item in case_observability}
    summary_mode = "mixed" if len(modes) > 1 else (case_observability[0].get("mode") if case_observability else "memory_state_unobservable")
    summary_disclaimer = (
        case_observability[0].get("disclaimer", "") if len(modes) == 1 and case_observability
        else "See per-case observability; wrapper-assisted scores are system-level and do not prove native model memory."
    )
    summary["observability"] = {
        "mode": summary_mode,
        "disclaimer": summary_disclaimer,
        "native_memory_events": sum(int(item.get("native_memory_events", 0)) for item in case_observability),
        "wrapper_memory_events": sum(int(item.get("wrapper_memory_events", 0)) for item in case_observability),
        "memory_disabled_events": sum(int(item.get("memory_disabled_events", 0)) for item in case_observability),
        "provider_memory_events_unverified": sum(int(item.get("provider_memory_events_unverified", 0)) for item in case_observability),
        "model_claims_unverified": sum(int(item.get("model_claims_unverified", 0)) for item in case_observability),
        "unobservable_internal_state": any(bool(item.get("unobservable_internal_state", True)) for item in case_observability),
        "sources": {key: sum(int(item.get("sources", {}).get(key, 0)) for item in case_observability) for key in {key for item in case_observability for key in item.get("sources", {})}},
        "classes": {key: sum(int(item.get("classes", {}).get(key, 0)) for item in case_observability) for key in {key for item in case_observability for key in item.get("classes", {})}},
    }
    (destination / "result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
