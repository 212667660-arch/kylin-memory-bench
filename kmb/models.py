from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

SUPPORTED_EVENT_KINDS = {
    "user_message", "assistant_message", "memory_write", "memory_update",
    "memory_suppress", "memory_recall", "action", "tool_result", "file_artifact",
    "model_request", "model_response", "restart_boundary", "capability_probe", "error",
}

SUPPORTED_EVIDENCE_SOURCES = {
    "unknown", "runner", "model", "wrapper", "provider_evidence", "simulated",
}
SUPPORTED_EVIDENCE_CLASSES = {
    "unclassified", "runner_observation", "model_observation", "model_claim_unverified",
    "model_memory_request_unverified", "model_tool_request_unverified",
    "model_native_memory", "model_native_tool", "provider_claim_unverified",
    "wrapper_observation", "wrapper_operation", "simulated_baseline", "no_memory_baseline", "runtime_error",
}
SUPPORTED_TRUST_LEVELS = {"unverified", "observed", "verified", "derived"}
MEMORY_EVENT_KINDS = {"memory_write", "memory_update", "memory_suppress", "memory_recall"}


def classify_evidence(kind: str, source: str, data: Optional[Dict[str, Any]] = None) -> str:
    """Classify provenance without treating model text as verified memory state."""
    data = data or {}
    source = str(source or "unknown")
    if kind == "error":
        return "runtime_error"
    if source == "runner" and data.get("memory_mode") == "no_memory_baseline":
        return "no_memory_baseline"
    if source == "wrapper":
        return "wrapper_operation" if kind in MEMORY_EVENT_KINDS or kind in {"action", "tool_result", "file_artifact"} else "wrapper_observation"
    if source == "model":
        if kind in MEMORY_EVENT_KINDS and data.get("native") and data.get("state_observed"):
            return "model_native_memory"
        if kind in MEMORY_EVENT_KINDS:
            return "model_memory_request_unverified"
        if kind in {"action", "tool_result"} and data.get("native") and data.get("execution_observed"):
            return "model_native_tool"
        if kind in {"action", "tool_result"}:
            return "model_tool_request_unverified"
        if kind == "assistant_message":
            return "model_claim_unverified"
        return "model_observation"
    if source == "provider_evidence":
        return "provider_claim_unverified"
    if source == "simulated":
        return "simulated_baseline"
    if source == "runner":
        return "runner_observation"
    if kind == "assistant_message":
        return "model_claim_unverified"
    return "unclassified"


def validate_event_dict(raw: Dict[str, Any]) -> None:
    if not isinstance(raw, dict):
        raise ValueError("evidence event must be an object")
    kind = raw.get("kind")
    if kind not in SUPPORTED_EVENT_KINDS:
        raise ValueError("unsupported evidence event kind: %s" % kind)
    if not isinstance(raw.get("data", {}), dict):
        raise ValueError("evidence event data must be an object")
    data = raw.get("data", {})
    source = raw.get("source", data.get("source", "unknown"))
    evidence_class = raw.get("evidence_class", data.get("evidence_class"))
    if not isinstance(source, str) or not source:
        raise ValueError("evidence event source must be a non-empty string")
    if source not in SUPPORTED_EVIDENCE_SOURCES:
        raise ValueError("unsupported evidence event source: %s" % source)
    if evidence_class is not None and evidence_class not in SUPPORTED_EVIDENCE_CLASSES:
        raise ValueError("unsupported evidence class: %s" % evidence_class)
    if "source" in raw and data.get("source") not in (None, source):
        raise ValueError("evidence event source differs between top-level and data")
    if "evidence_class" in raw and data.get("evidence_class") not in (None, evidence_class):
        raise ValueError("evidence class differs between top-level and data")
    if evidence_class == "model_native_memory" and not (source == "model" and data.get("state_observed")):
        raise ValueError("model_native_memory requires source=model and state_observed=true")
    if evidence_class == "model_native_tool" and not (source == "model" and data.get("execution_observed")):
        raise ValueError("model_native_tool requires source=model and execution_observed=true")
    event_id = raw.get("event_id")
    if event_id is not None and (not isinstance(event_id, str) or not event_id.strip()):
        raise ValueError("evidence event event_id must be a non-empty string when provided")
    for field_name in ("parent_event_id", "correlation_id", "fact_id", "scope", "artifact_path"):
        value = raw.get(field_name)
        if value is not None and not isinstance(value, str):
            raise ValueError("evidence event %s must be a string when provided" % field_name)
    fact_version = raw.get("fact_version")
    if fact_version is not None:
        try:
            if int(fact_version) < 1:
                raise ValueError("fact_version must be positive")
        except (TypeError, ValueError):
            raise ValueError("evidence event fact_version must be a positive integer")
    artifact_sha256 = raw.get("artifact_sha256")
    if artifact_sha256 is not None and artifact_sha256 != "":
        if not isinstance(artifact_sha256, str) or len(artifact_sha256) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in artifact_sha256):
            raise ValueError("evidence event artifact_sha256 must be a SHA256 hex digest")
    trust_level = raw.get("trust_level", data.get("trust_level", "unverified"))
    if trust_level not in SUPPORTED_TRUST_LEVELS:
        raise ValueError("unsupported evidence trust level: %s" % trust_level)
    try:
        int(raw.get("step", 0))
    except (TypeError, ValueError):
        raise ValueError("evidence event step must be an integer")


@dataclass
class EvidenceEvent:
    kind: str
    data: Dict[str, Any]
    step: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = ""
    evidence_class: str = ""
    event_id: str = ""
    parent_event_id: str = ""
    correlation_id: str = ""
    fact_id: str = ""
    fact_version: Optional[int] = None
    scope: str = ""
    artifact_path: str = ""
    artifact_sha256: str = ""
    trust_level: str = ""

    def __post_init__(self) -> None:
        payload = dict(self.data or {})
        resolved_source = str(self.source or payload.get("source") or "unknown")
        resolved_class = str(self.evidence_class or payload.get("evidence_class") or classify_evidence(self.kind, resolved_source, payload))
        if resolved_source not in SUPPORTED_EVIDENCE_SOURCES:
            raise ValueError("unsupported evidence event source: %s" % resolved_source)
        if resolved_class not in SUPPORTED_EVIDENCE_CLASSES:
            raise ValueError("unsupported evidence class: %s" % resolved_class)
        if resolved_class == "model_native_memory" and not (resolved_source == "model" and payload.get("state_observed")):
            raise ValueError("model_native_memory requires source=model and state_observed=true")
        if resolved_class == "model_native_tool" and not (resolved_source == "model" and payload.get("execution_observed")):
            raise ValueError("model_native_tool requires source=model and execution_observed=true")
        payload["source"] = resolved_source
        payload["evidence_class"] = resolved_class
        self.event_id = str(self.event_id or payload.get("event_id") or "")
        self.parent_event_id = str(self.parent_event_id or payload.get("parent_event_id") or "")
        self.correlation_id = str(self.correlation_id or payload.get("correlation_id") or "")
        self.fact_id = str(self.fact_id or payload.get("fact_id") or "")
        raw_version = self.fact_version if self.fact_version is not None else payload.get("fact_version")
        self.fact_version = int(raw_version) if raw_version not in (None, "") else None
        self.scope = str(self.scope or payload.get("scope") or "")
        self.artifact_path = str(self.artifact_path or payload.get("artifact_path") or "")
        self.artifact_sha256 = str(self.artifact_sha256 or payload.get("artifact_sha256") or "")
        self.trust_level = str(self.trust_level or payload.get("trust_level") or "unverified")
        if self.trust_level not in SUPPORTED_TRUST_LEVELS:
            raise ValueError("unsupported evidence trust level: %s" % self.trust_level)
        for field_name, value in (
            ("event_id", self.event_id), ("parent_event_id", self.parent_event_id),
            ("correlation_id", self.correlation_id), ("fact_id", self.fact_id),
            ("scope", self.scope), ("artifact_path", self.artifact_path),
        ):
            if value:
                payload.setdefault(field_name, value)
        if self.fact_version is not None:
            payload.setdefault("fact_version", self.fact_version)
        if self.artifact_sha256:
            payload.setdefault("artifact_sha256", self.artifact_sha256)
        payload.setdefault("trust_level", self.trust_level)
        self.data = payload
        self.source = resolved_source
        self.evidence_class = resolved_class

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "kind": self.kind, "data": self.data, "step": self.step,
            "timestamp": self.timestamp, "source": self.source,
            "evidence_class": self.evidence_class,
        }
        for key in ("event_id", "parent_event_id", "correlation_id", "fact_id", "fact_version", "scope", "artifact_path", "artifact_sha256"):
            value = getattr(self, key)
            if value not in ("", None):
                result[key] = value
        result["trust_level"] = self.trust_level
        return result


@dataclass
class BenchmarkCase:
    id: str
    capability: str
    title: str
    turns: List[Dict[str, Any]]
    checks: List[Dict[str, Any]]
    description: str = ""
    facts: List[Dict[str, Any]] = field(default_factory=list)
    lifecycle: Dict[str, Any] = field(default_factory=dict)
    metamorphic: Dict[str, Any] = field(default_factory=dict)
    action_assertions: List[Dict[str, Any]] = field(default_factory=list)

    @staticmethod
    def _normalise_fact(case_id: str, raw: Dict[str, Any], fallback_turn: int = 1) -> Dict[str, Any]:
        if not isinstance(raw, dict):
            raise ValueError("fact metadata must be an object")
        key = str(raw.get("key", "")).strip()
        if not key:
            raise ValueError("fact metadata requires key")
        persistence = str(raw.get("persistence", "persistent" if raw.get("persist", True) else "ephemeral"))
        if persistence not in {"persistent", "ephemeral", "session", "derived"}:
            raise ValueError("unsupported fact persistence: %s" % persistence)
        sensitivity = str(raw.get("sensitivity", "normal"))
        scope = str(raw.get("scope", "default"))
        version = int(raw.get("version", 1))
        if version < 1:
            raise ValueError("fact version must be positive")
        fact = {
            "fact_id": str(raw.get("fact_id", "%s:%s" % (case_id, key))),
            "key": key,
            "value": raw.get("value"),
            "persistence": persistence,
            "sensitivity": sensitivity,
            "scope": scope,
            "version": version,
            "expires_at": raw.get("expires_at"),
            "ttl_steps": raw.get("ttl_steps"),
            "provenance": raw.get("provenance", {"source": "scenario", "turn": fallback_turn}),
        }
        if fact["ttl_steps"] is not None:
            fact["ttl_steps"] = int(fact["ttl_steps"])
            if fact["ttl_steps"] < 1:
                raise ValueError("fact ttl_steps must be positive")
        return fact

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "BenchmarkCase":
        required = ("id", "capability", "title", "turns", "checks")
        missing = [key for key in required if key not in raw]
        if missing:
            raise ValueError("case missing fields: " + ", ".join(missing))
        if not isinstance(raw["turns"], list) or not isinstance(raw["checks"], list):
            raise ValueError("turns and checks must be lists")
        facts_by_key: Dict[str, Dict[str, Any]] = {}
        for index, item in enumerate(raw.get("facts", []) or [], 1):
            fact = cls._normalise_fact(str(raw["id"]), item, index)
            facts_by_key[fact["key"]] = fact
        for index, turn in enumerate(raw["turns"], 1):
            directive = turn.get("memory") if isinstance(turn, dict) else None
            if isinstance(directive, dict) and directive.get("key"):
                key = str(directive["key"])
                if key not in facts_by_key:
                    facts_by_key[key] = cls._normalise_fact(
                        str(raw["id"]),
                        dict(directive, value=directive.get("value"), version=directive.get("version", 1),
                             persistence=directive.get("persistence", "persistent" if directive.get("persist", True) else "ephemeral")),
                        index,
                    )
        lifecycle = dict(raw.get("lifecycle") or {})
        if "phases" in lifecycle and not isinstance(lifecycle["phases"], list):
            raise ValueError("lifecycle phases must be a list")
        metamorphic = dict(raw.get("metamorphic") or {})
        if metamorphic and not metamorphic.get("group_id"):
            raise ValueError("metamorphic metadata requires group_id")
        action_assertions = raw.get("action_assertions", []) or []
        if not isinstance(action_assertions, list):
            raise ValueError("action_assertions must be a list")
        return cls(
            id=str(raw["id"]), capability=str(raw["capability"]), title=str(raw["title"]),
            turns=raw["turns"], checks=raw["checks"], description=str(raw.get("description", "")),
            facts=list(facts_by_key.values()), lifecycle=lifecycle, metamorphic=metamorphic,
            action_assertions=action_assertions,
        )


@dataclass
class CheckResult:
    check: Dict[str, Any]
    passed: bool
    reason: str
    failure_type: Optional[str] = None
    evidence_refs: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "check": self.check,
            "passed": self.passed,
            "reason": self.reason,
            "evidence_refs": self.evidence_refs,
        }
        if self.failure_type:
            result["failure_type"] = self.failure_type
        return result


@dataclass
class ScoreResult:
    case_id: str
    capability: str
    score: float
    status: str
    checks: List[CheckResult]
    failures: List[Dict[str, Any]]
    attempts: int = 1
    observability: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id, "capability": self.capability, "score": self.score,
            "status": self.status, "checks": [item.to_dict() for item in self.checks],
            "failures": self.failures, "attempts": self.attempts,
            "observability": self.observability,
        }


def summarize_evidence(events: Iterable[EvidenceEvent]) -> Dict[str, Any]:
    """Summarize what was observable and state what remains unknowable."""
    events = list(events)
    source_counts = Counter(event.source for event in events)
    class_counts = Counter(event.evidence_class for event in events)
    native_memory = class_counts.get("model_native_memory", 0)
    wrapper_memory = sum(
        1 for event in events
        if event.evidence_class == "wrapper_operation" and event.kind in MEMORY_EVENT_KINDS
    )
    provider_memory = sum(
        1 for event in events
        if event.evidence_class == "provider_claim_unverified" and event.kind in MEMORY_EVENT_KINDS
    )
    model_claims = class_counts.get("model_claim_unverified", 0)
    simulated_events = class_counts.get("simulated_baseline", 0)
    no_memory_events = class_counts.get("no_memory_baseline", 0)
    if simulated_events:
        mode = "simulated_baseline"
        disclaimer = "This is a deterministic demonstration baseline, not a real participating agent or native model memory measurement."
    elif no_memory_events:
        mode = "no_memory_baseline"
        disclaimer = "Score measures the real model backend with external memory disabled; it is a comparison baseline, not proof of native model memory."
    elif native_memory:
        mode = "native_memory_events_observed"
        disclaimer = "Observed native memory events are limited to the exported tool/event evidence; hidden internal state is still not proven."
    elif wrapper_memory:
        mode = "system_level_wrapper_assisted"
        disclaimer = "Score measures the model backend plus an external memory/action controller, not native model memory."
    elif provider_memory:
        mode = "provider_evidence_unverified"
        disclaimer = "Provider-exported memory events are recorded but their internal persistence is not independently verified."
    else:
        mode = "memory_state_unobservable"
        disclaimer = "No verified native or wrapper memory operation was observed; assistant text is an unverified claim only."
    return {
        "mode": mode,
        "disclaimer": disclaimer,
        "native_memory_events": native_memory,
        "wrapper_memory_events": wrapper_memory,
        "provider_memory_events_unverified": provider_memory,
        "model_claims_unverified": model_claims,
        "memory_disabled_events": no_memory_events,
        "unobservable_internal_state": native_memory == 0 and not simulated_events,
        "sources": dict(source_counts),
        "classes": dict(class_counts),
    }
