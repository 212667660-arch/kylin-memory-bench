"""B-track memory modules: real stores used by MemoryToolAgent.

Decision to write/read must come from the agent tool layer (model policy),
not from suite YAML. These modules only execute persist/recall operations
and report whether a write was applied or refused.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

SENSITIVE_KEY = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|otp|one[_-]?time|session[_-]?key|"
    r"ssn|card|credit|auth|credential|private[_-]?key)",
    re.I,
)
SENSITIVE_VALUE = re.compile(
    r"(^|\b)(sk-[A-Za-z0-9]{8,}|pw[_-]?[A-Za-z0-9]{4,}|otp[_-]?[A-Za-z0-9]{3,}|"
    r"token[_-][A-Za-z0-9]{4,}|one[- ]?time|一次性|验证码|密码|口令)",
    re.I,
)
EPHEMERAL_HINT = re.compile(r"(session only|this session|only for now|temporary|temp|临时|仅本次|用完即弃|discard)", re.I)


def looks_persist_refusal(key: str, value: Any, context: str = "") -> Optional[str]:
    blob = "%s %s %s" % (key, value, context)
    if SENSITIVE_KEY.search(str(key)) or SENSITIVE_VALUE.search(str(value)) or SENSITIVE_KEY.search(blob):
        return "sensitive"
    if EPHEMERAL_HINT.search(blob) or SENSITIVE_VALUE.search(blob):
        return "ephemeral_or_sensitive"
    return None


@dataclass
class MemoryWriteResult:
    applied: bool
    key: str
    value: Any
    old_value: Any = None
    refused_reason: str = ""
    policy: str = ""


@dataclass
class ExactKVMemory:
    """Memory 甲: exact key-value; policy writes whenever the agent asks."""

    name: str = "exact-kv"
    policy: str = "write_eager"
    store: Dict[str, Any] = field(default_factory=dict)

    def save(self, key: str, value: Any, persist: bool = True, context: str = "") -> MemoryWriteResult:
        if not persist:
            return MemoryWriteResult(False, key, value, refused_reason="persist=false", policy=self.policy)
        old = self.store.get(key)
        self.store[key] = value
        return MemoryWriteResult(True, key, value, old_value=old, policy=self.policy)

    def update(self, key: str, value: Any, context: str = "") -> MemoryWriteResult:
        old = self.store.get(key)
        self.store[key] = value
        return MemoryWriteResult(True, key, value, old_value=old, policy=self.policy)

    def recall(self, key: str) -> Tuple[bool, Any]:
        if key in self.store:
            return True, self.store[key]
        return False, None

    def delete(self, key: str) -> bool:
        return self.store.pop(key, None) is not None or key in self.store


@dataclass
class SimilarityMemory:
    """Memory 乙: approximate retrieval + refuse sensitive/ephemeral writes."""

    name: str = "similarity-guarded"
    policy: str = "similar_retrieve_refuse_boundary"
    store: Dict[str, Any] = field(default_factory=dict)

    def _similar_keys(self, query: str, limit: int = 5) -> List[str]:
        q = str(query).lower()
        tokens = {t for t in re.split(r"[^a-z0-9]+", q) if t}
        scored: List[Tuple[int, str]] = []
        for key in self.store:
            k = key.lower()
            kt = {t for t in re.split(r"[^a-z0-9]+", k) if t}
            score = len(tokens & kt)
            compact_q = q.replace("_", "")
            compact_k = k.replace("_", "")
            if compact_q in compact_k or compact_k in compact_q:
                score += 2
            if score:
                scored.append((score, key))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [key for _, key in scored[:limit]]

    def save(self, key: str, value: Any, persist: bool = True, context: str = "") -> MemoryWriteResult:
        reason = looks_persist_refusal(key, value, context)
        if reason or not persist:
            return MemoryWriteResult(
                False, key, value,
                refused_reason=reason or "persist=false",
                policy=self.policy,
            )
        old = self.store.get(key)
        self.store[key] = value
        return MemoryWriteResult(True, key, value, old_value=old, policy=self.policy)

    def update(self, key: str, value: Any, context: str = "") -> MemoryWriteResult:
        reason = looks_persist_refusal(key, value)
        if reason:
            return MemoryWriteResult(False, key, value, refused_reason=reason, policy=self.policy)
        old = self.store.get(key)
        self.store[key] = value
        return MemoryWriteResult(True, key, value, old_value=old, policy=self.policy)

    def recall(self, key: str) -> Tuple[bool, Any]:
        if key in self.store:
            return True, self.store[key]
        hits = self._similar_keys(key, limit=3)
        if hits:
            return True, self.store[hits[0]]
        return False, None

    def delete(self, key: str) -> bool:
        existed = key in self.store
        self.store.pop(key, None)
        return existed


def build_memory_impl(kind: str):
    normalized = str(kind or "kv").strip().lower()
    if normalized in {"kv", "exact", "exact_kv", "memory_kv"}:
        return ExactKVMemory()
    if normalized in {"similar", "similarity", "memory_similar", "similarity_guarded"}:
        return SimilarityMemory()
    raise ValueError("unknown memory_impl '%s' (use kv or similar)" % kind)
