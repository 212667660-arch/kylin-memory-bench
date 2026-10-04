from typing import Any, Dict, Iterable, List, Mapping

from .models import BenchmarkCase, CheckResult, EvidenceEvent, ScoreResult


def _events(events: Iterable[EvidenceEvent], kind: str) -> List[EvidenceEvent]:
    return [event for event in events if event.kind == kind]


def _failure_type(check_type: str) -> str:
    return {
        "memory_recall": "omission", "answer_contains": "omission", "answer_not_contains": "confusion",
        "memory_absent": "erroneous_persistence", "memory_value": "stale_update",
        "memory_expired": "expired_reuse", "scope_isolation": "scope_violation",
        "sensitive_not_persisted": "sensitive_persistence", "memory_version": "stale_update",
        "action_path": "erroneous_reuse", "action_tool": "erroneous_reuse", "artifact_exists": "action_failure",
        "artifact_contains": "action_failure", "action_exit_code": "action_failure",
        "evidence_chain": "incomplete_evidence", "restart_boundary": "invalid_behavior",
        "state_sequence": "invalid_behavior",
    }.get(check_type, "invalid_behavior")


def _ref(event: EvidenceEvent) -> Dict[str, Any]:
    """Keep legacy references compact while exposing provenance for new events."""
    ref = {"kind": event.kind, "step": event.step}
    if event.source != "unknown" or event.evidence_class != "unclassified":
        ref.update({"source": event.source, "evidence_class": event.evidence_class})
    for key in ("event_id", "parent_event_id", "correlation_id", "fact_id", "fact_version", "scope", "artifact_path", "artifact_sha256", "trust_level"):
        value = getattr(event, key, None)
        if value not in (None, "", "unverified"):
            ref[key] = value
    return ref


def _is_executed_action(event: EvidenceEvent) -> bool:
    """Do not score a requested or blocked tool call as a completed action."""
    if event.data.get("blocked") or event.data.get("executed") is False:
        return False
    if event.data.get("exit_code") not in (None, 0):
        return False
    if event.source == "model":
        return event.evidence_class == "model_native_tool"
    if event.source == "provider_evidence":
        return False
    return True


def _action_category(check_type: str, events: List[EvidenceEvent], passed: bool) -> str:
    """Separate behavior errors from unsupported or unobservable actions."""
    if passed or check_type not in {"action_path", "action_tool", "artifact_exists", "artifact_contains", "action_exit_code"}:
        return "behavior_failure"
    actions = _events(events, "action") + _events(events, "tool_result")
    if not actions:
        return "not_observable"
    if any(event.data.get("unsupported") or event.data.get("capability") == "unsupported_action" for event in actions):
        return "unsupported_action"
    if any(event.data.get("blocked") or event.data.get("execution_observed") is False for event in actions):
        return "not_observable"
    return "behavior_failure"


def _evaluate(check: Dict[str, Any], events: List[EvidenceEvent]) -> CheckResult:
    check_type = str(check.get("type", ""))
    assistants = [str(event.data.get("text", "")) for event in _events(events, "assistant_message")]
    refs: List[Dict[str, Any]] = []
    if check_type == "answer_contains":
        value = str(check.get("value", ""))
        passed = any(value in text for text in assistants)
        refs = [_ref(event) for event in _events(events, "assistant_message") if value in str(event.data.get("text", ""))]
        reason = "assistant output contains '%s'" % value if passed else "assistant output did not contain '%s'" % value
    elif check_type == "answer_not_contains":
        value = str(check.get("value", ""))
        passed = bool(assistants) and all(value not in text for text in assistants)
        refs = [_ref(event) for event in _events(events, "assistant_message")]
        if passed:
            reason = "assistant output excludes '%s'" % value
        elif not assistants:
            reason = "no assistant output available to verify exclusion of '%s'" % value
        else:
            reason = "assistant output contains forbidden '%s'" % value
    elif check_type == "memory_recall":
        key = str(check.get("key"))
        matches = [event for event in _events(events, "memory_recall") if event.data.get("key") == key and event.data.get("hit")]
        expected = check.get("value")
        if expected is not None:
            matches = [event for event in matches if event.data.get("value") == expected]
        passed = bool(matches)
        refs = [_ref(event) for event in matches]
        reason = "memory_recall event for %s observed" % key if passed else "no matching memory_recall event for %s" % key
    elif check_type == "memory_absent":
        key = str(check.get("key"))
        persisted = [event for event in events if event.kind in ("memory_write", "memory_update") and event.data.get("key") == key and event.data.get("persist")]
        recalled = [event for event in _events(events, "memory_recall") if event.data.get("key") == key and event.data.get("hit")]
        passed = not persisted and not recalled
        refs = [_ref(event) for event in persisted + recalled]
        reason = "no persistent write or recall for %s" % key if passed else "boundary violation for %s" % key
    elif check_type == "memory_expired":
        key = str(check.get("key"))
        suppressions = [event for event in _events(events, "memory_suppress") if event.data.get("key") == key and event.data.get("expired")]
        recalls = [event for event in _events(events, "memory_recall") if event.data.get("key") == key]
        passed = bool(suppressions) and bool(recalls) and all(not event.data.get("hit") for event in recalls[-1:])
        refs = [_ref(event) for event in suppressions + recalls]
        reason = "expired fact %s was suppressed and not recalled" % key if passed else "expired fact %s was reused or lacked expiry evidence" % key
    elif check_type == "scope_isolation":
        key, expected_scope = str(check.get("key")), str(check.get("scope"))
        recalls = [event for event in _events(events, "memory_recall") if event.data.get("key") == key]
        scoped_recalls = [event for event in recalls if event.data.get("scope") == expected_scope]
        denied = [event for event in scoped_recalls if not event.data.get("hit") and event.data.get("scope_match") is False]
        cross_scope_hits = [event for event in scoped_recalls if event.data.get("hit")]
        passed = bool(denied) and not cross_scope_hits
        refs = [_ref(event) for event in recalls]
        reason = "scope %s was isolated for %s" % (expected_scope, key) if passed else "scope isolation failed for %s" % key
    elif check_type == "sensitive_not_persisted":
        key = str(check.get("key"))
        writes = [event for event in events if event.kind in ("memory_write", "memory_update") and event.data.get("key") == key and event.data.get("persist")]
        recalls = [event for event in _events(events, "memory_recall") if event.data.get("key") == key and event.data.get("hit")]
        suppressions = [event for event in _events(events, "memory_suppress") if event.data.get("key") == key]
        passed = not writes and not recalls and bool(suppressions)
        refs = [_ref(event) for event in writes + recalls + suppressions]
        reason = "sensitive fact %s was rejected and not reused" % key if passed else "sensitive fact %s was persisted or reused" % key
    elif check_type == "memory_value":
        key, expected = str(check.get("key")), check.get("value")
        writes = [event for event in events if event.kind in ("memory_write", "memory_update") and event.data.get("key") == key]
        passed = bool(writes) and writes[-1].data.get("value") == expected
        refs = [_ref(event) for event in writes]
        reason = "latest memory value for %s is %r" % (key, expected) if passed else "latest memory value for %s is not %r" % (key, expected)
    elif check_type == "memory_version":
        key, expected = str(check.get("key")), int(check.get("value"))
        writes = [event for event in events if event.kind in ("memory_write", "memory_update") and event.data.get("key") == key]
        passed = bool(writes) and int(writes[-1].data.get("fact_version", getattr(writes[-1], "fact_version", 0)) or 0) == expected
        refs = [_ref(event) for event in writes]
        reason = "latest fact version for %s is %d" % (key, expected) if passed else "latest fact version for %s is not %d" % (key, expected)
    elif check_type == "action_path":
        expected = str(check.get("value"))
        actions = [event for event in _events(events, "action") if event.data.get("path") == expected and _is_executed_action(event)]
        passed = bool(actions)
        refs = [_ref(event) for event in actions]
        reason = "action used path %s" % expected if passed else "action did not use path %s" % expected
    elif check_type == "action_tool":
        expected = str(check.get("value"))
        actions = [event for event in _events(events, "action") if event.data.get("tool") == expected and _is_executed_action(event)]
        passed = bool(actions)
        refs = [_ref(event) for event in actions]
        reason = "action tool %s observed as executable" % expected if passed else "action tool %s missing an executable, unblocked action" % expected
    elif check_type == "artifact_exists":
        expected = check.get("path") or check.get("value")
        artifacts = [event for event in _events(events, "file_artifact") if event.data.get("file_exists") and (expected is None or event.data.get("artifact_path") == expected or event.data.get("path") == expected)]
        if not artifacts:
            artifacts = [event for event in _events(events, "action") if event.data.get("file_exists") and (expected is None or event.data.get("actual_path") == expected)]
        passed = bool(artifacts)
        refs = [_ref(event) for event in artifacts]
        reason = "sandbox artifact exists" if passed else "expected sandbox artifact is missing"
    elif check_type == "artifact_contains":
        value = str(check.get("value", ""))
        artifacts = [event for event in _events(events, "file_artifact") if value in str(event.data.get("content", ""))]
        passed = bool(artifacts)
        refs = [_ref(event) for event in artifacts]
        reason = "artifact contains '%s'" % value if passed else "artifact does not contain '%s'" % value
    elif check_type == "action_exit_code":
        expected = int(check.get("value", 0))
        results = [event for event in _events(events, "tool_result") if event.data.get("exit_code") == expected]
        if not results:
            results = [event for event in _events(events, "action") if event.data.get("exit_code") == expected]
        passed = bool(results)
        refs = [_ref(event) for event in results]
        reason = "action exit code is %d" % expected if passed else "expected action exit code %d was not observed" % expected
    elif check_type == "restart_boundary":
        expected = str(check.get("value", "wrapper_rebuild"))
        boundaries = [event for event in _events(events, "restart_boundary") if event.data.get("boundary_type") == expected and not event.data.get("system_restart")]
        passed = bool(boundaries)
        refs = [_ref(event) for event in boundaries]
        reason = "controlled restart boundary %s observed" % expected if passed else "controlled restart boundary %s missing" % expected
    elif check_type == "evidence_chain":
        key = check.get("key")
        relevant = [event for event in events if key is None or event.data.get("key") == key or event.data.get("source_key") == key or event.fact_id == str(key)]
        required = [str(item) for item in check.get("value", ["memory_write", "memory_recall"])]
        kinds = {event.kind for event in relevant}
        passed = bool(relevant) and all(kind in kinds for kind in required)
        refs = [_ref(event) for event in relevant]
        reason = "evidence chain contains %s" % ", ".join(required) if passed else "evidence chain missing %s" % ", ".join(kind for kind in required if kind not in kinds)
    elif check_type == "state_sequence":
        key = str(check.get("key"))
        expected = [str(item) for item in check.get("value", [])]
        actual = []
        matched_refs = []
        for event in events:
            if event.kind in ("memory_write", "memory_update") and event.data.get("key") == key:
                actual.append("write" if event.kind == "memory_write" else "revise")
                matched_refs.append(_ref(event))
            elif event.kind == "memory_suppress" and event.data.get("key") == key:
                actual.append("expire" if event.data.get("expired") else "suppress")
                matched_refs.append(_ref(event))
            elif event.kind == "memory_recall" and event.data.get("key") == key and event.data.get("hit"):
                actual.append("retain")
                matched_refs.append(_ref(event))
            elif event.kind == "restart_boundary" and (event.data.get("fact_id") in {None, "", key} or key in event.data.get("retained_keys", [])):
                actual.append("restart")
                matched_refs.append(_ref(event))
            elif event.kind == "action" and event.data.get("source_key") == key and _is_executed_action(event):
                actual.append("reuse")
                matched_refs.append(_ref(event))
        passed = actual == expected
        refs = matched_refs
        reason = "state sequence for %s is %s" % (key, actual) if passed else "state sequence for %s is %s, expected %s" % (key, actual, expected)
    else:
        passed, reason = False, "unsupported check type %s" % check_type
    category = _action_category(check_type, events, passed)
    return CheckResult(check, passed, reason, None if passed else _failure_type(check_type), refs, category)


def score_case(case: BenchmarkCase, events: List[EvidenceEvent]) -> ScoreResult:
    checks = [_evaluate(check, events) for check in case.checks]
    passed = sum(1 for check in checks if check.passed)
    score = (passed / len(checks)) if checks else 1.0
    failures = [{"type": check.failure_type, "category": check.category, "reason": check.reason, "check": check.check} for check in checks if not check.passed]
    return ScoreResult(case.id, case.capability, score, "pass" if score == 1.0 else "fail", checks, failures)


def _check_status(result: ScoreResult, check_type: str, key: Any = None) -> Any:
    for check in result.checks:
        if str(check.check.get("type")) != check_type:
            continue
        if key is not None and str(check.check.get("key")) != str(key):
            continue
        return check.passed
    return None


def _actual_action_paths(events: List[EvidenceEvent]) -> List[str]:
    return [str(event.data.get("path")) for event in _events(events, "action") if _is_executed_action(event) and event.data.get("path") is not None]


def score_metamorphic_groups(cases: Iterable[BenchmarkCase], scores: Iterable[ScoreResult], events_by_case: Mapping[str, List[EvidenceEvent]]) -> List[Dict[str, Any]]:
    """Score declared metamorphic relations without using an LLM judge."""
    grouped: Dict[str, List[BenchmarkCase]] = {}
    for case in cases:
        group_id = str((case.metamorphic or {}).get("group_id", ""))
        if group_id:
            grouped.setdefault(group_id, []).append(case)
    score_map = {item.case_id: item for item in scores}
    output: List[Dict[str, Any]] = []
    for group_id, group_cases in sorted(grouped.items()):
        metadata = next((case.metamorphic for case in group_cases if case.metamorphic), {})
        baseline = next((case for case in group_cases if case.metamorphic.get("role") == "baseline"), group_cases[0])
        variants = [case for case in group_cases if case.id != baseline.id]
        violations: List[Dict[str, Any]] = []
        refs: List[Dict[str, Any]] = []
        for relation in metadata.get("must_change", []) or []:
            relation_type = str(relation.get("type", ""))
            if relation_type == "action_path":
                expected_base = str(relation.get("baseline"))
                expected_variant = str(relation.get("variant"))
                base_paths = _actual_action_paths(events_by_case.get(baseline.id, []))
                variant_paths = [path for case in variants for path in _actual_action_paths(events_by_case.get(case.id, []))]
                if expected_base not in base_paths or expected_variant not in variant_paths or expected_base == expected_variant:
                    violations.append({"type": relation_type, "reason": "controlled action path did not change as declared", "baseline": base_paths, "variant": variant_paths})
                refs.extend({"case_id": baseline.id, **ref} for event in _events(events_by_case.get(baseline.id, []), "action") for ref in [_ref(event)])
                refs.extend({"case_id": case.id, **ref} for case in variants for event in _events(events_by_case.get(case.id, []), "action") for ref in [_ref(event)])
            elif relation_type == "recall_hit":
                expected_base = bool(relation.get("baseline"))
                expected_variant = bool(relation.get("variant"))
                base_hits = [bool(event.data.get("hit")) for event in _events(events_by_case.get(baseline.id, []), "memory_recall")]
                variant_hits = [bool(event.data.get("hit")) for case in variants for event in _events(events_by_case.get(case.id, []), "memory_recall")]
                if expected_base not in base_hits or expected_variant not in variant_hits or expected_base == expected_variant:
                    violations.append({"type": relation_type, "reason": "recall outcome did not change as declared", "baseline": base_hits, "variant": variant_hits})
        for invariant in metadata.get("invariants", []) or []:
            invariant_type = str(invariant.get("type", ""))
            if invariant_type == "check_status_equal":
                check_type = str(invariant.get("check_type"))
                key = invariant.get("key")
                base_status = _check_status(score_map[baseline.id], check_type, key) if baseline.id in score_map else None
                for case in variants:
                    variant_status = _check_status(score_map[case.id], check_type, key) if case.id in score_map else None
                    if base_status is None or variant_status is None or base_status != variant_status:
                        violations.append({"type": invariant_type, "reason": "invariant check status changed", "check_type": check_type, "baseline": base_status, "variant_case": case.id, "variant": variant_status})
            elif invariant_type == "no_sensitive_persistence":
                key = str(invariant.get("key"))
                for case in group_cases:
                    events = events_by_case.get(case.id, [])
                    if any(event.kind in ("memory_write", "memory_update") and event.data.get("key") == key and event.data.get("persist") for event in events):
                        violations.append({"type": invariant_type, "reason": "sensitive fact was persisted", "case_id": case.id, "key": key})
            elif invariant_type == "artifact_exists":
                for case in group_cases:
                    artifacts = [event for event in events_by_case.get(case.id, []) if event.kind == "file_artifact" and event.data.get("file_exists")]
                    if not artifacts:
                        violations.append({"type": invariant_type, "reason": "sandbox artifact missing", "case_id": case.id})
            elif invariant_type == "check_passed":
                case_id = str(invariant.get("case_id") or baseline.id)
                result = score_map.get(case_id)
                if result is None or not _check_status(result, str(invariant.get("check_type")), invariant.get("key")):
                    violations.append({"type": invariant_type, "reason": "required invariant check failed", "case_id": case_id})
        output.append({
            "group_id": group_id,
            "baseline_case_id": baseline.id,
            "variant_case_ids": [case.id for case in variants],
            "controlled_variable": metadata.get("controlled_variable", ""),
            "must_change": metadata.get("must_change", []),
            "invariants": metadata.get("invariants", []),
            "passed": not violations,
            "violations": violations,
            "evidence_refs": refs,
        })
    return output
