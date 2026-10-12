import json
import hashlib
import os
import re
import shlex
import subprocess
import sys
import time
from copy import deepcopy
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

from .models import BenchmarkCase, EvidenceEvent, validate_event_dict


class AgentAdapter(ABC):
    name = "agent"

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": type(self).__name__, "agent": self.name,
            "memory_observability": "unknown",
            "native_memory_capability": "not_claimed",
        }

    def preflight(self) -> Dict[str, Any]:
        """Return a read-only readiness report before any benchmark turns run."""
        return {"status": "ready", "checks": [], "agent": self.name}

    @abstractmethod
    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        raise NotImplementedError


class MemoryAgent(AgentAdapter):
    """Deterministic local agent used as a reference and adapter contract example."""

    name = "reference"

    def __init__(self, flawed: bool = False):
        self.flawed = flawed
        self.name = "flawed" if flawed else "reference"

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": type(self).__name__, "agent": self.name,
            "memory_observability": "simulated_baseline",
            "native_memory_capability": "not_applicable",
        }

    @staticmethod
    def _event(kind: str, data: Dict[str, Any], step: int) -> EvidenceEvent:
        return EvidenceEvent(kind, data, step, source="simulated")

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        memory: Dict[str, Any] = {}
        events: List[EvidenceEvent] = []
        for step, turn in enumerate(case.turns, 1):
            user = str(turn.get("user", ""))
            events.append(self._event("user_message", {"text": user}, step))
            mem = turn.get("memory")
            if mem is None and user.lower().startswith("remember ") and "=" in user:
                key, value = user[9:].split("=", 1)
                mem = {"op": "write", "key": key.strip(), "value": value.strip(), "persist": True}
            if mem:
                op = str(mem.get("op", "write"))
                key, value = str(mem.get("key")), mem.get("value")
                persist = bool(mem.get("persist", True))
                if op in ("write", "update") and persist:
                    if self.flawed and op == "update":
                        # Record the attempted revision while retaining the stale stored value.
                        stale = memory.get(key)
                        events.append(self._event("memory_update", {"key": key, "value": stale, "requested_value": value, "old_value": stale, "persist": True}, step))
                    elif self.flawed and not persist:
                        memory[key] = value
                        events.append(self._event("memory_write", {"key": key, "value": value, "persist": True}, step))
                    else:
                        old = memory.get(key)
                        memory[key] = value
                        kind = "memory_update" if op == "update" and old is not None else "memory_write"
                        events.append(self._event(kind, {"key": key, "value": value, "old_value": old, "persist": True}, step))
                else:
                    if self.flawed and not persist:
                        memory[key] = value
                        events.append(self._event("memory_write", {"key": key, "value": value, "persist": True}, step))
                    else:
                        events.append(self._event("memory_suppress", {"key": key, "value": value, "persist": False}, step))
            query = turn.get("query")
            if query:
                key = str(query.get("key"))
                value = memory.get(key)
                if self.flawed and case.capability == "similar_distinction":
                    # Deliberate cross-entity confusion: return the first remembered value.
                    value = next(iter(memory.values()), None)
                events.append(self._event("memory_recall", {"key": key, "value": value, "hit": value is not None}, step))
                text = "I don't know."
                if value is not None:
                    text = str(value)
                events.append(self._event("assistant_message", {"text": text}, step))
            action = turn.get("action")
            if action:
                tool = str(action.get("tool", "action"))
                path = action.get("path")
                source_key = action.get("path_from_memory")
                if source_key:
                    path = memory.get(str(source_key))
                    if self.flawed:
                        path = None
                events.append(self._event("action", {"tool": tool, "path": path, "source_key": source_key}, step))
                events.append(self._event("assistant_message", {"text": "action completed" if path else "action failed"}, step))
        return events


class ReferenceAgent(MemoryAgent):
    def __init__(self):
        super().__init__(flawed=False)


class FlawedAgent(MemoryAgent):
    def __init__(self):
        super().__init__(flawed=True)


def build_agent(name: str) -> AgentAdapter:
    normalized = name.lower()
    if normalized in ("reference", "ref", "baseline"):
        return ReferenceAgent()
    if normalized in ("flawed", "naive", "baseline-flawed"):
        return FlawedAgent()
    raise ValueError("unknown agent '%s' (use reference or flawed)" % name)


class ReplayAgent(AgentAdapter):
    """Adapter for external agents that export normalized JSONL evidence."""

    def __init__(self, name: str, evidence_path: str):
        self.name = name
        self.evidence_path = evidence_path

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        events: List[EvidenceEvent] = []
        path = Path(self.evidence_path)
        if not path.exists():
            raise FileNotFoundError(str(path))
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            raw = json.loads(line)
            if raw.get("case_id") != case.id:
                continue
            validate_event_dict(raw)
            events.append(EvidenceEvent(
                kind=str(raw["kind"]), data=dict(raw.get("data", {})),
                step=int(raw.get("step", line_number)), timestamp=str(raw.get("timestamp") or EvidenceEvent("x", {}, 0).timestamp),
                source=str(raw.get("source") or raw.get("data", {}).get("source") or "unknown"),
                evidence_class=str(raw.get("evidence_class") or raw.get("data", {}).get("evidence_class") or ""),
            ))
        return events


class CommandAgent(AgentAdapter):
    """Run an external agent command using stdin case JSON and stdout JSONL evidence."""

    def __init__(self, name: str, command: Any, timeout_seconds: float = 30.0, env_allowlist: List[str] = None, cwd: str = None):
        self.name = name
        if isinstance(command, str):
            command = shlex.split(command)
        if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
            raise ValueError("command must be a non-empty string or argument list")
        self.command = list(command)
        if self.command[0] in ("python", "python3"):
            self.command[0] = sys.executable
        self.timeout_seconds = float(timeout_seconds)
        self.env_allowlist = list(env_allowlist or [])
        self.cwd = cwd

    def _environment(self) -> Dict[str, str]:
        inherited = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL", "SYSTEMROOT", "TEMP", "TMP") if key in os.environ}
        for key in self.env_allowlist:
            if key in os.environ:
                inherited[key] = os.environ[key]
        inherited["PYTHONIOENCODING"] = "utf-8"
        return inherited

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        completed = subprocess.run(
            self.command,
            input=json.dumps(asdict(case), ensure_ascii=False),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=self.timeout_seconds,
            cwd=self.cwd,
            env=self._environment(),
            check=False,
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or "external command failed"
            raise RuntimeError("command exited %d: %s" % (completed.returncode, message))
        events: List[EvidenceEvent] = []
        for line_number, line in enumerate(completed.stdout.splitlines(), 1):
            if not line.strip():
                continue
            raw = json.loads(line)
            if raw.get("case_id") != case.id:
                continue
            try:
                validate_event_dict(raw)
            except ValueError as exc:
                raise ValueError("invalid evidence event on stdout line %d: %s" % (line_number, exc))
            events.append(EvidenceEvent(
                kind=str(raw["kind"]), data=dict(raw.get("data", {})),
                step=int(raw.get("step", line_number)), timestamp=str(raw.get("timestamp") or EvidenceEvent("x", {}, 0).timestamp),
                source=str(raw.get("source") or raw.get("data", {}).get("source") or "unknown"),
                evidence_class=str(raw.get("evidence_class") or raw.get("data", {}).get("evidence_class") or ""),
            ))
        return events


_ENV_REFERENCE = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def _resolve_config_value(value: Any, field: str) -> Any:
    """Resolve an exact ${ENV_VAR} reference without ever persisting its value."""
    if not isinstance(value, str):
        return value
    match = _ENV_REFERENCE.match(value.strip())
    if not match:
        return value
    env_name = match.group(1)
    resolved = os.environ.get(env_name)
    if not resolved:
        raise RuntimeError("required environment variable %s is not set for %s" % (env_name, field))
    return resolved


def _content_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") in (None, "text", "output_text"):
                text = item.get("text")
                if text is not None:
                    parts.append(str(text))
        return "".join(parts)
    return str(content)


class OpenAICompatibleAgent(AgentAdapter):
    """Call an OpenAI-compatible chat API and collect only observable evidence.

    This adapter deliberately does not invent memory events. Providers or a real
    agent wrapper may return a ``kmb_evidence`` array, and function/tool calls are
    mapped when they are present in the API response. Plain text responses alone
    therefore cannot pass memory-state checks, which keeps the benchmark honest.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        model: str,
        api_key_env: str,
        endpoint: str = "/chat/completions",
        timeout_seconds: float = 60.0,
        system_prompt: str = "",
        request_options: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        evidence_field: str = "kmb_evidence",
    ):
        self.name = str(name)
        self.base_url = str(_resolve_config_value(base_url, "base_url")).rstrip("/")
        self.model = str(_resolve_config_value(model, "model"))
        self.api_key_env = str(api_key_env)
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", self.api_key_env):
            raise ValueError("api_key_env must be a valid environment variable name")
        self.endpoint = str(_resolve_config_value(endpoint, "endpoint"))
        self.timeout_seconds = float(timeout_seconds)
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.system_prompt = str(system_prompt or "")
        self.request_options = dict(request_options or {})
        self.headers = dict(headers or {})
        self.evidence_field = str(evidence_field or "kmb_evidence")

    def _url(self) -> str:
        if self.endpoint.startswith("http://") or self.endpoint.startswith("https://"):
            return self.endpoint
        return "%s/%s" % (self.base_url, self.endpoint.lstrip("/"))

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": type(self).__name__, "agent": self.name, "backend": "openai_compatible_http",
            "model": self.model, "endpoint": self._url(), "api_key_env": self.api_key_env,
            "evidence_field": self.evidence_field,
            "memory_observability": "provider_export_or_native_tools_only",
            "native_memory_capability": "unverified_without_native_events",
        }

    def _api_key(self) -> str:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise RuntimeError("required environment variable %s is not set" % self.api_key_env)
        return key

    def _request(self, messages: List[Dict[str, Any]], extra_options: Dict[str, Any] = None) -> Dict[str, Any]:
        key = self._api_key()
        payload = dict(self.request_options)
        payload.update(extra_options or {})
        payload["model"] = self.model
        payload["messages"] = messages
        request_headers = {"Content-Type": "application/json", "Authorization": "Bearer " + key}
        for header_name, header_value in self.headers.items():
            request_headers[str(header_name)] = str(_resolve_config_value(header_value, "header %s" % header_name))
        request = Request(
            self._url(),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=request_headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:500]
            body = body.replace(key, "[REDACTED]")
            raise RuntimeError("HTTP %d from agent API: %s" % (exc.code, body))
        except URLError as exc:
            raise RuntimeError("agent API connection failed: %s" % exc.reason)
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("agent API returned non-JSON response: %s" % exc)
        if not isinstance(result, dict):
            raise ValueError("agent API response must be a JSON object")
        if result.get("error"):
            error = result.get("error")
            if isinstance(error, dict):
                error = error.get("message") or error
            raise RuntimeError("agent API returned an error: %s" % str(error).replace(key, "[REDACTED]"))
        return result

    def _message(self, response: Dict[str, Any]) -> Dict[str, Any]:
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("agent API response has no choices")
        choice = choices[0]
        if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
            raise ValueError("agent API response choice has no message")
        return choice["message"]

    def _evidence_events(self, case: BenchmarkCase, response: Dict[str, Any], message: Dict[str, Any], step: int) -> List[EvidenceEvent]:
        candidates = []
        for container in (response, message):
            if isinstance(container, dict) and isinstance(container.get(self.evidence_field), list):
                candidates.extend(container[self.evidence_field])
        events = []
        for raw in candidates:
            if not isinstance(raw, dict):
                raise ValueError("%s entries must be objects" % self.evidence_field)
            raw_case_id = raw.get("case_id")
            if raw_case_id is not None and str(raw_case_id) != case.id:
                continue
            validate_event_dict(raw)
            data = dict(raw.get("data", {}))
            if raw.get("source") or data.get("source"):
                data["declared_source"] = raw.get("source") or data.get("source")
            if raw.get("evidence_class") or data.get("evidence_class"):
                data["declared_evidence_class"] = raw.get("evidence_class") or data.get("evidence_class")
            events.append(EvidenceEvent(
                kind=str(raw["kind"]),
                data=data,
                step=int(raw.get("step", step)),
                timestamp=str(raw.get("timestamp") or EvidenceEvent("x", {}, 0).timestamp),
                source="provider_evidence",
            ))
        return events

    def _tool_events(self, message: Dict[str, Any], step: int) -> List[EvidenceEvent]:
        tool_calls = message.get("tool_calls") or []
        if not isinstance(tool_calls, list):
            return []
        events = []
        memory_kinds = {"memory_write", "memory_update", "memory_suppress", "memory_recall"}
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            function = call.get("function") or {}
            if not isinstance(function, dict):
                continue
            tool_name = str(function.get("name") or "tool")
            arguments = function.get("arguments", {})
            parsed_arguments = arguments
            if isinstance(arguments, str):
                try:
                    parsed_arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    parsed_arguments = {"raw_arguments": arguments}
            data = {"tool": tool_name, "arguments": parsed_arguments}
            if isinstance(parsed_arguments, dict):
                data.update(parsed_arguments)
            kind = tool_name if tool_name in memory_kinds else "action"
            if kind == "action":
                data.setdefault("tool", tool_name)
            events.append(EvidenceEvent(kind, data, step))
        return events

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        messages: List[Dict[str, Any]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        events: List[EvidenceEvent] = []
        for step, turn in enumerate(case.turns, 1):
            user_text = str(turn.get("user", ""))
            messages.append({"role": "user", "content": user_text})
            events.append(EvidenceEvent("user_message", {"text": user_text}, step, source="runner"))
            response = self._request(messages)
            message = self._message(response)
            content = _content_text(message.get("content"))
            if content:
                events.append(EvidenceEvent("assistant_message", {"text": content, "backend": self.name, "model": self.model}, step, source="model"))
            for tool_event in self._tool_events(message, step):
                tool_data = dict(tool_event.data)
                tool_data.update({"source": "model", "tool_call_observed": True})
                events.append(EvidenceEvent(tool_event.kind, tool_data, tool_event.step, source="model"))
            events.extend(self._evidence_events(case, response, message, step))
            messages.append({"role": "assistant", "content": content})
        return events


# Short alias used by configuration-oriented callers.
HttpAgent = OpenAICompatibleAgent


class MemoryControllerAgent(AgentAdapter):
    """Transparent external memory/action controller around a real model API.

    The benchmark case declares the state transition to exercise; this controller
    executes it in a local, auditable store and supplies only the relevant context
    to the model. Every wrapper event is marked ``source=wrapper`` while model
    responses and native tool calls are marked ``source=model``. This measures the
    assembled agent workflow and must not be reported as native model memory.
    """

    def __init__(self, name: str, backend: OpenAICompatibleAgent, action_root: str = "runs/controller-actions"):
        self.name = str(name)
        self.backend = backend
        root = Path(action_root)
        if not root.is_absolute():
            root = Path.cwd() / root
        self.action_root = root

    @staticmethod
    def _event(kind: str, data: Dict[str, Any], step: int) -> EvidenceEvent:
        enriched = dict(data)
        enriched.setdefault("source", "wrapper")
        return EvidenceEvent(kind, enriched, step)

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": type(self).__name__, "agent": self.name,
            "controller": "external_memory_and_action_controller", "controller_source": "wrapper",
            "model_backend": self.backend.describe(), "action_root": str(self.action_root),
            "memory_observability": "wrapper_operations_and_model_observations",
            "native_memory_capability": "not_claimed",
            "capability_statement": "system_level_wrapper_assisted_evaluation",
            "lifecycle_metadata": ["persistence", "sensitivity", "scope", "version", "expires_at", "provenance"],
            "restart_boundary": "wrapper_rebuild_only",
            "action_execution": "sandbox_file_and_tool_result_observed",
        }

    @staticmethod
    def _record_value(record: Dict[str, Any]) -> Any:
        return record.get("value") if isinstance(record, dict) else record

    @staticmethod
    def _safe_value(record: Dict[str, Any]) -> Any:
        if isinstance(record, dict) and str(record.get("sensitivity", "normal")) not in ("normal", "public", "none"):
            return "[REDACTED_SYNTHETIC_SECRET]"
        return MemoryControllerAgent._record_value(record)

    @staticmethod
    def _redact_text(text: str, directive: Dict[str, Any]) -> str:
        sensitivity = str(directive.get("sensitivity", "normal"))
        value = directive.get("value")
        if value is not None and sensitivity not in ("normal", "public", "none"):
            return str(text).replace(str(value), "[REDACTED_SYNTHETIC_SECRET]")
        return str(text)

    def _fact_template(self, case: BenchmarkCase, directive: Dict[str, Any], step: int, old: Dict[str, Any] = None) -> Dict[str, Any]:
        key = str(directive.get("key", ""))
        known = next((fact for fact in case.facts if fact.get("key") == key), {})
        previous_version = int((old or {}).get("version", known.get("version", 0)) or 0)
        requested_version = directive.get("version")
        operation = str(directive.get("op", "write")).lower()
        version = int(requested_version) if requested_version is not None else (previous_version + 1 if operation in ("update", "revise") and previous_version else max(1, previous_version))
        persistence = str(directive.get("persistence", known.get("persistence", "persistent" if directive.get("persist", True) else "ephemeral")))
        sensitivity = str(directive.get("sensitivity", known.get("sensitivity", "normal")))
        scope = str(directive.get("scope", known.get("scope", "default")))
        ttl_steps = directive.get("ttl_steps", known.get("ttl_steps"))
        expires_at = directive.get("expires_at", known.get("expires_at"))
        if ttl_steps is not None:
            ttl_steps = int(ttl_steps)
            expires_at = step + ttl_steps
        return {
            "fact_id": str(directive.get("fact_id", known.get("fact_id", "%s:%s" % (case.id, key)))),
            "key": key, "value": directive.get("value"), "persistence": persistence,
            "sensitivity": sensitivity, "scope": scope, "version": version,
            "expires_at": expires_at, "ttl_steps": ttl_steps,
            "provenance": directive.get("provenance", known.get("provenance", {"source": "scenario", "case_id": case.id, "step": step})),
        }

    @staticmethod
    def _metadata(record: Dict[str, Any]) -> Dict[str, Any]:
        if not record:
            return {}
        result = {key: record.get(key) for key in ("fact_id", "persistence", "sensitivity", "scope", "expires_at", "provenance") if record.get(key) is not None}
        if record.get("version") is not None:
            result["fact_version"] = int(record["version"])
        return result

    def _apply_memory(self, case: BenchmarkCase, memory: Dict[str, Any], directive: Dict[str, Any], step: int) -> EvidenceEvent:
        op = str(directive.get("op", "write")).lower()
        key = str(directive.get("key", ""))
        value = directive.get("value")
        persist = bool(directive.get("persist", True))
        if not key:
            raise ValueError("memory directive requires key")
        old = memory.get(key)
        if not persist or op in ("suppress", "forget"):
            memory.pop(key, None)
            record = self._fact_template(case, directive, step, old)
            return self._event("memory_suppress", {
                "key": key, "value": None if record["sensitivity"] not in ("normal", "public", "none") else value,
                "persist": False, "controller": "scenario_directive",
                "reason": "sensitive_rejection" if record["sensitivity"] not in ("normal", "public", "none") else "explicit_suppress",
                "fact_id": record["fact_id"], "fact_version": record["version"], "scope": record["scope"],
                "persistence": record["persistence"], "sensitivity": record["sensitivity"], "provenance": record["provenance"],
            }, step)
        record = self._fact_template(case, directive, step, old)
        memory[key] = record
        kind = "memory_update" if op in ("update", "revise") and old is not None else "memory_write"
        payload = {"key": key, "value": self._safe_value(record), "old_value": self._safe_value(old) if old else None,
                   "persist": True, "controller": "scenario_directive", "state_transition": "revise" if kind == "memory_update" else "write"}
        payload.update(self._metadata(record))
        payload["fact_version"] = record["version"]
        return self._event(kind, payload, step)

    def _expire_memory(self, memory: Dict[str, Any], step: int) -> List[EvidenceEvent]:
        events = []
        for key, record in list(memory.items()):
            expires_at = record.get("expires_at") if isinstance(record, dict) else None
            try:
                expired = expires_at is not None and int(expires_at) <= step
            except (TypeError, ValueError):
                expired = False
            if expired:
                memory.pop(key, None)
                payload = {"key": key, "value": None, "persist": False, "expired": True, "reason": "ttl_expired", "state_transition": "expire"}
                payload.update(self._metadata(record))
                events.append(self._event("memory_suppress", payload, step))
        return events

    def _restart_boundary(self, memory: Dict[str, Any], step: int) -> EvidenceEvent:
        retained = {key: deepcopy(record) for key, record in memory.items() if isinstance(record, dict) and record.get("persistence") in ("persistent", "session")}
        memory.clear()
        memory.update(retained)
        return self._event("restart_boundary", {
            "boundary_type": "wrapper_rebuild", "system_restart": False,
            "retained_fact_ids": [record.get("fact_id") for record in retained.values()],
            "retained_keys": sorted(retained), "state_transition": "restart",
            "reason": "controlled agent/controller reconstruction; not an OS restart",
        }, step)

    def _action(self, case: BenchmarkCase, action: Dict[str, Any], memory: Dict[str, Any], step: int) -> EvidenceEvent:
        tool = str(action.get("tool", "action"))
        source_key = action.get("path_from_memory")
        requested_path = action.get("path")
        record = None
        if source_key:
            record = memory.get(str(source_key))
            requested_path = self._record_value(record) if record else None
        requested_scope = str(action.get("scope", ""))
        if record and requested_scope and record.get("scope") != requested_scope:
            requested_path = None
        agent_component = re.sub(r"[^A-Za-z0-9_.-]+", "_", self.name).strip("._") or "agent"
        case_root = self.action_root / agent_component / case.id
        case_root.mkdir(parents=True, exist_ok=True)
        actual_path = case_root / "action-result.txt"
        executed = bool(requested_path is not None and (not requested_scope or not record or record.get("scope") == requested_scope))
        exit_code = 0 if executed else 1
        content = "KylinMemoryBench controller action\ncase=%s\ntool=%s\nrequested_path=%s\n" % (case.id, tool, requested_path)
        if executed:
            actual_path.write_text(content, encoding="utf-8")
        artifact_sha256 = hashlib.sha256(actual_path.read_bytes()).hexdigest() if actual_path.exists() else ""
        metadata = self._metadata(record or {})
        payload = {
            "tool": tool,
            "path": requested_path,
            "source_key": source_key,
            "actual_path": str(actual_path),
            "file_exists": actual_path.exists(),
            "artifact_path": str(actual_path), "artifact_sha256": artifact_sha256,
            "exit_code": exit_code, "executed": executed, "blocked": not executed,
            "blocked_reason": "missing_memory_or_scope" if not executed else None,
            "execution_observed": executed, "execution_scope": "sandbox",
            "executed_by": "wrapper",
            "trust_level": "verified" if executed else "observed", "scope": record.get("scope", requested_scope) if record else requested_scope,
        }
        payload.update(metadata)
        return self._event("action", payload, step)

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        memory: Dict[str, Any] = {}
        messages: List[Dict[str, Any]] = [{
            "role": "system",
            "content": (
                "You are the model backend inside a transparent KylinMemoryBench controller. "
                "The controller, not you, executes memory and file actions. Use the supplied "
                "controller context when answering. Do not claim native memory storage or tool execution."
            ),
        }]
        events: List[EvidenceEvent] = []
        for step, turn in enumerate(case.turns, 1):
            user_text = str(turn.get("user", ""))
            directive = turn.get("memory")
            model_user_text = self._redact_text(user_text, dict(directive) if isinstance(directive, dict) else {})
            events.extend(self._expire_memory(memory, step))
            boundary = turn.get("restart_boundary") or (isinstance(turn.get("control"), dict) and turn.get("control", {}).get("op") == "restart-boundary")
            if boundary:
                events.append(self._restart_boundary(memory, step))
            events.append(self._event("user_message", {"text": model_user_text, "backend": self.backend.model}, step))
            if directive:
                events.append(self._apply_memory(case, memory, dict(directive), step))
            query = turn.get("query")
            recalled = None
            recalled_record = None
            if query:
                key = str(query.get("key", ""))
                query_scope = str(query.get("scope", ""))
                recalled_record = memory.get(key)
                scope_match = bool(recalled_record and (not query_scope or recalled_record.get("scope") == query_scope))
                recalled = self._record_value(recalled_record) if scope_match else None
                recall_payload = {
                    "key": key, "value": self._safe_value(recalled_record) if scope_match and recalled_record else None,
                    "hit": recalled is not None, "scope": query_scope or (recalled_record or {}).get("scope", ""),
                    "scope_match": scope_match, "controller": "scenario_directive",
                    "blocked_reason": "scope_mismatch" if recalled_record and not scope_match else None,
                }
                recall_payload.update(self._metadata(recalled_record or {}))
                recall_payload["scope"] = query_scope or (recalled_record or {}).get("scope", "")
                events.append(self._event("memory_recall", recall_payload, step))
            action = turn.get("action")
            if action:
                action_event = self._action(case, dict(action), memory, step)
                events.append(action_event)
                events.append(self._event("tool_result", {
                    "tool": action_event.data.get("tool"), "exit_code": action_event.data.get("exit_code"),
                    "executed": action_event.data.get("executed"), "blocked": action_event.data.get("blocked"),
                    "artifact_path": action_event.data.get("artifact_path"), "artifact_sha256": action_event.data.get("artifact_sha256"),
                    "stdout": "sandbox action completed" if action_event.data.get("executed") else "sandbox action blocked",
                    "stderr": "" if action_event.data.get("executed") else str(action_event.data.get("blocked_reason")),
                    "source_key": action_event.data.get("source_key"), "scope": action_event.data.get("scope", ""),
                    "fact_id": action_event.data.get("fact_id"), "fact_version": action_event.data.get("fact_version"),
                    "trust_level": action_event.data.get("trust_level", "observed"),
                }, step))
                if action_event.data.get("file_exists"):
                    events.append(self._event("file_artifact", {
                        "artifact_path": action_event.data.get("artifact_path"), "path": action_event.data.get("artifact_path"),
                        "file_exists": True,
                        "content": "KylinMemoryBench controller action\ncase=%s\ntool=%s\nrequested_path=%s\n" % (case.id, action_event.data.get("tool"), action_event.data.get("path")),
                        "artifact_sha256": action_event.data.get("artifact_sha256"), "source_key": action_event.data.get("source_key"),
                        "fact_id": action_event.data.get("fact_id"), "fact_version": action_event.data.get("fact_version"),
                        "scope": action_event.data.get("scope", ""), "trust_level": "verified",
                    }, step))
            context_parts = [
                "[KMB controller context]",
                "Memory is externally managed and observable only through this context.",
            ]
            if query:
                context_parts.append("Recall %s = %s" % (query.get("key"), self._safe_value(recalled_record) if recalled is not None else "<absent>"))
            if action:
                path_key = action.get("path_from_memory")
                action_record = memory.get(str(path_key)) if path_key else None
                context_parts.append("Action %s requested path %s" % (action.get("tool", "action"), self._record_value(action_record) if action_record else action.get("path")))
            prompt = model_user_text + "\n\n" + "\n".join(context_parts)
            messages.append({"role": "user", "content": prompt})
            request_started = time.monotonic()
            events.append(self._event("model_request", {
                "backend": self.backend.name, "model": self.backend.model, "endpoint": self.backend._url(),
                "message_count": len(messages), "messages": list(messages), "source": "model",
            }, step))
            response = self.backend._request(messages)
            elapsed_ms = round((time.monotonic() - request_started) * 1000, 1)
            message = self.backend._message(response)
            content = _content_text(message.get("content"))
            if content:
                events.append(EvidenceEvent("assistant_message", {
                    "text": content, "source": "model", "backend": self.backend.name, "model": self.backend.model,
                }, step))
            for native_event in self.backend._tool_events(message, step):
                native_data = dict(native_event.data)
                native_data.update({"source": "model", "backend": self.backend.name, "model": self.backend.model, "tool_call_observed": True})
                events.append(EvidenceEvent(native_event.kind, native_data, native_event.step))
            for external_event in self.backend._evidence_events(case, response, message, step):
                external_data = dict(external_event.data)
                external_data.setdefault("source", "provider_evidence")
                external_data.setdefault("backend", self.backend.name)
                external_data.setdefault("model", self.backend.model)
                events.append(EvidenceEvent(external_event.kind, external_data, external_event.step, external_event.timestamp))
            events.append(self._event("model_response", {
                "backend": self.backend.name, "model": self.backend.model,
                "response_id": response.get("id"), "finish_reason": (response.get("choices") or [{}])[0].get("finish_reason"),
                "elapsed_ms": elapsed_ms, "response_keys": sorted(response.keys()), "source": "model",
            }, step))
            messages.append({"role": "assistant", "content": content})
        return events


class NoMemoryAgent(AgentAdapter):
    """Run a real model with the external memory/action controller disabled.

    This is a comparison baseline, not a skipped evaluation: every case still
    calls the model and emits explicit miss/suppression/block events for the
    memory operations declared by the suite. No persistent dictionary or file
    action is created by this adapter.
    """

    def __init__(self, name: str, backend: OpenAICompatibleAgent):
        self.name = str(name)
        self.backend = backend

    @staticmethod
    def _baseline_event(kind: str, data: Dict[str, Any], step: int) -> EvidenceEvent:
        enriched = dict(data)
        enriched.update({"memory_mode": "no_memory_baseline", "source": "runner"})
        return EvidenceEvent(kind, enriched, step, source="runner", evidence_class="no_memory_baseline")

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": type(self).__name__, "agent": self.name,
            "controller": "disabled", "memory_mode": "disabled",
            "model_backend": self.backend.describe(),
            "memory_observability": "disabled_external_memory_and_model_observations",
            "native_memory_capability": "unverified_without_native_events",
            "capability_statement": "system_level_no_memory_baseline",
        }

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        messages: List[Dict[str, Any]] = [{
            "role": "system",
            "content": (
                "You are the model backend in a KylinMemoryBench no-memory baseline. "
                "External memory storage, recall, suppression and file actions are disabled. "
                "Answer only from the current user message and do not claim that memory was stored "
                "or that an action was executed."
            ),
        }]
        events: List[EvidenceEvent] = []
        for step, turn in enumerate(case.turns, 1):
            user_text = str(turn.get("user", ""))
            events.append(EvidenceEvent("user_message", {"text": user_text}, step, source="runner"))

            directive = turn.get("memory")
            if directive:
                directive = dict(directive)
                requested_op = str(directive.get("op", "write")).lower()
                key = str(directive.get("key", ""))
                events.append(self._baseline_event("memory_suppress", {
                    "key": key,
                    "value": directive.get("value"),
                    "persist": False,
                    "requested_op": requested_op,
                    "disabled": True,
                    "blocked_reason": "external_memory_disabled",
                    "controller": "disabled",
                }, step))

            query = turn.get("query")
            if query:
                key = str(query.get("key", ""))
                events.append(self._baseline_event("memory_recall", {
                    "key": key,
                    "value": None,
                    "hit": False,
                    "disabled": True,
                    "blocked_reason": "external_memory_disabled",
                    "controller": "disabled",
                }, step))

            action = turn.get("action")
            if action:
                action = dict(action)
                source_key = action.get("path_from_memory")
                events.append(self._baseline_event("action", {
                    "tool": str(action.get("tool", "action")),
                    "path": None if source_key else action.get("path"),
                    "source_key": source_key,
                    "executed": False,
                    "blocked": True,
                    "blocked_reason": "memory_disabled" if source_key else "no_memory_baseline_actions_disabled",
                    "executed_by": "none",
                }, step))

            messages.append({"role": "user", "content": user_text})
            request_started = time.monotonic()
            events.append(EvidenceEvent("model_request", {
                "backend": self.backend.name, "model": self.backend.model, "endpoint": self.backend._url(),
                "message_count": len(messages), "messages": list(messages), "memory_mode": "no_memory_baseline",
            }, step, source="model"))
            response = self.backend._request(messages)
            elapsed_ms = round((time.monotonic() - request_started) * 1000, 1)
            message = self.backend._message(response)
            content = _content_text(message.get("content"))
            if content:
                events.append(EvidenceEvent("assistant_message", {
                    "text": content, "backend": self.backend.name, "model": self.backend.model,
                }, step, source="model"))
            for native_event in self.backend._tool_events(message, step):
                native_data = dict(native_event.data)
                native_data.update({"source": "model", "backend": self.backend.name, "model": self.backend.model, "tool_call_observed": True, "executed": False})
                events.append(EvidenceEvent(native_event.kind, native_data, native_event.step, source="model"))
            for external_event in self.backend._evidence_events(case, response, message, step):
                external_data = dict(external_event.data)
                external_data.setdefault("source", "provider_evidence")
                external_data.setdefault("backend", self.backend.name)
                external_data.setdefault("model", self.backend.model)
                external_data.setdefault("memory_mode", "no_memory_baseline")
                events.append(EvidenceEvent(external_event.kind, external_data, external_event.step, external_event.timestamp, source="provider_evidence"))
            events.append(EvidenceEvent("model_response", {
                "backend": self.backend.name, "model": self.backend.model,
                "response_id": response.get("id"), "finish_reason": (response.get("choices") or [{}])[0].get("finish_reason"),
                "elapsed_ms": elapsed_ms, "response_keys": sorted(response.keys()), "memory_mode": "no_memory_baseline",
            }, step, source="model"))
            messages.append({"role": "assistant", "content": content})
        return events


# Descriptive alias for callers that prefer the configuration terminology.
MemoryDisabledAgent = NoMemoryAgent


class DecisionTextBackend:
    """B-track tool-policy backend that decides from *user text*, not suite YAML ops.

    Stands in for an LLM tool-calling loop. Real HTTP tool-calling backends can
    replace this later; both B sides must share the same backend type.
    """

    def plan(self, user: str, memory: Any, step: int) -> List[Dict[str, Any]]:
        text = str(user or "")
        calls: List[Dict[str, Any]] = []
        # Explicit update (multi-word values)
        m = re.search(
            r"([A-Za-z0-9_.-]+)\s*(?:changed\s+to|changed|is\s+now|→|->)\s+(.+?)\s*$",
            text, re.I | re.M,
        )
        m2 = re.search(r"([A-Za-z0-9_.-]+)\s*(?:改成|改为|现在是)\s*(.+?)\s*$", text)
        if m or m2:
            mm = m or m2
            value = mm.group(2).strip().strip("。.,，")
            calls.append({"tool": "update", "key": mm.group(1), "value": value, "context": text})
            return calls
        # Remember k=v
        m = re.search(r"remember\s+([A-Za-z0-9_.-]+)\s*=\s*([^\n]+)", text, re.I)
        m2 = re.search(r"记住\s*([A-Za-z0-9_.-]+)\s*[=＝]\s*([^\n]+)", text)
        if not m and not m2:
            m3 = re.search(r"记住([A-Za-z0-9_.-]+)是([^\s，。]+)", text)
            if m3:
                m = m3
        if m or m2:
            mm = m or m2
            value = mm.group(2).strip().strip("。.,，")
            calls.append({"tool": "save", "key": mm.group(1).strip(), "value": value, "persist": True, "context": text})
            return calls
        # Ephemeral/sensitive mention -> agent still *attempts* save; memory layer may refuse
        m = re.search(
            r"(?:my\s+)?(?:one[-\s]?time\s+)?(?:code|otp|password|token|session\s*key)\s*(?:is|为|=|：)\s*([A-Za-z0-9_\-]+)",
            text, re.I,
        )
        m2 = re.search(r"(验证码|密码|口令|token|密钥)\s*(?:是|为|=|：)\s*([A-Za-z0-9_\-]+)", text)
        if m or m2:
            mm = m or m2
            key = "otp" if re.search(r"code|otp|验证码", text, re.I) else "secret_temp"
            calls.append({"tool": "save", "key": key, "value": mm.group(1) if m else mm.group(2), "persist": True, "context": text})
            return calls
        # Recall
        if re.search(r"(what\s+is|which|recall|use\s+my|where|do\s+you\s+remember)", text, re.I) or re.search(r"(是什么|哪个|回忆|调用|使用|在哪|记得)", text):
            key_m = re.search(r"(?:what\s+is|which|recall|use)\s+(?:my\s+)?([A-Za-z0-9_.-]+)", text, re.I)
            key_m2 = re.search(r"([A-Za-z0-9_.-]+)\s*(?:是什么|在哪|在哪里)", text)
            key_m3 = re.search(r"(?:where\s+is\s+the\s+|do\s+you\s+remember\s+my\s+)([A-Za-z0-9_.-]+)", text, re.I)
            key = ""
            if key_m:
                key = key_m.group(1)
            elif key_m3:
                key = key_m3.group(1)
            elif key_m2:
                key = key_m2.group(1)
            elif re.search(r"one[-\s]?time|code|otp|验证码", text, re.I):
                key = "otp"
            elif re.search(r"venue|会议室", text, re.I):
                key = "venue"
            elif re.search(r"project", text, re.I):
                key = "project"
            key = key.strip()
            if key:
                calls.append({"tool": "recall", "key": key, "context": text})
                return calls
        # Task action
        if re.search(r"(create|export|write|archive|put|report|file)", text, re.I) or re.search(r"(创建|导出|写入|归档|报表|报告|放到)", text):
            key_m = re.search(r"(?:under|using|in|to)\s+(?:the\s+)?(?:remembered\s+)?([A-Za-z0-9_.-]+)", text, re.I)
            key_m2 = re.search(r"(?:在|用|放到)\s*([A-Za-z0-9_.-]+)", text)
            source_key = (key_m.group(1) if key_m else (key_m2.group(1) if key_m2 else "")).strip() or None
            if not source_key:
                for candidate in ("output_dir", "workspace", "cache", "export", "artifacts", "logs"):
                    hit, _ = memory.recall(candidate) if hasattr(memory, "recall") else (False, None)
                    if hit:
                        source_key = candidate
                        break
            calls.append({"tool": "write_file", "source_key": source_key, "context": text})
        return calls


class OpenAICompatibleToolBackend:
    """Standard OpenAI-compatible tool-calling loop for the B track.

    The model chooses a tool from the declared schema; the local memory layer
    executes it and returns a tool result for the model's final response.
    """

    TOOLS = [
        {"type": "function", "function": {"name": "save_memory", "description": "Persist a non-sensitive fact", "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "value": {}, "persist": {"type": "boolean"}}, "required": ["key", "value"]}}},
        {"type": "function", "function": {"name": "update_memory", "description": "Update an existing fact", "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "value": {}}, "required": ["key", "value"]}}},
        {"type": "function", "function": {"name": "recall_memory", "description": "Recall a fact by key", "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}}},
        {"type": "function", "function": {"name": "write_file", "description": "Write a report using a remembered path", "parameters": {"type": "object", "properties": {"source_key": {"type": "string"}}, "required": ["source_key"]}}},
    ]

    def __init__(self, backend: OpenAICompatibleAgent):
        self.backend = backend
        self.messages: List[Dict[str, Any]] = []

    def _model_event(self, kind: str, data: Dict[str, Any], step: int) -> EvidenceEvent:
        data = dict(data)
        data.update({"backend": self.backend.name, "model": self.backend.model})
        return EvidenceEvent(kind, data, step, source="model")

    @staticmethod
    def _canonical_call(call: Dict[str, Any]) -> Dict[str, Any]:
        function = call.get("function") or {}
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"raw_arguments": arguments}
        arguments = arguments if isinstance(arguments, dict) else {}
        mapping = {"save_memory": "save", "update_memory": "update", "recall_memory": "recall", "write_file": "write_file"}
        return {"tool": mapping.get(str(function.get("name") or ""), str(function.get("name") or "action")), "call_id": call.get("id", ""), **arguments}

    def begin_turn(self, user: str, step: int) -> Dict[str, Any]:
        self.messages.append({"role": "user", "content": user})
        response = self.backend._request(deepcopy(self.messages), extra_options={"tools": self.TOOLS, "tool_choice": "auto"})
        message = self.backend._message(response)
        # DashScope-style backends reject assistant messages whose tool_calls
        # list is present but empty — only include the key when tools were called.
        assistant = {"role": "assistant", "content": message.get("content")}
        if message.get("tool_calls"):
            assistant["tool_calls"] = list(message["tool_calls"])
        self.messages.append(assistant)
        calls = [self._canonical_call(call) for call in (message.get("tool_calls") or []) if isinstance(call, dict)]
        events = [self._model_event("model_request", {"tool_schema_count": len(self.TOOLS), "message_count": len(self.messages) - 1}, step)]
        events.extend(self._model_event("memory_%s" % call["tool"] if call["tool"] in {"write", "update", "recall"} else "action", {"tool": call["tool"], "arguments": {key: value for key, value in call.items() if key not in {"tool", "call_id"}}, "tool_call_observed": True, "execution_observed": False}, step) for call in calls)
        return {"calls": calls, "events": events, "response": response, "content": message.get("content") or ""}

    def end_turn(self, tool_results: List[Dict[str, Any]], step: int) -> List[EvidenceEvent]:
        for result in tool_results:
            self.messages.append({"role": "tool", "tool_call_id": result.get("call_id", ""), "name": result.get("tool", "tool"), "content": json.dumps(result, ensure_ascii=False)})
        response = self.backend._request(deepcopy(self.messages), extra_options={"tools": self.TOOLS, "tool_choice": "none"})
        message = self.backend._message(response)
        content = _content_text(message.get("content"))
        self.messages.append({"role": "assistant", "content": content})
        return [self._model_event("assistant_message", {"text": content, "tool_call_followup": True}, step), self._model_event("model_response", {"response_id": response.get("id"), "finish_reason": (response.get("choices") or [{}])[0].get("finish_reason")}, step)]


class MemoryToolAgent(AgentAdapter):
    """B-track agent: shared dialogue backend + pluggable memory implementation.

    Tool decisions come from the backend policy (user language), not from
    case.turns[].memory. Memory modules only execute save/update/recall.
    Events from the store use source=memory_layer (system memory implementation).
    """

    def __init__(self, name: str, memory_impl: str = "kv", backend: Any = None, action_root: str = "runs/memory-tool-actions"):
        from .memory_modules import build_memory_impl

        self.name = name
        self.memory_kind = str(memory_impl)
        self.memory = build_memory_impl(memory_impl)
        self.backend = backend or DecisionTextBackend()
        self.action_root = Path(action_root)
        if not self.action_root.is_absolute():
            self.action_root = Path.cwd() / self.action_root
        self.action_root.mkdir(parents=True, exist_ok=True)

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": type(self).__name__,
            "agent": self.name,
            "memory_observability": "b_track_memory_layer",
            "memory_impl": self.memory_kind,
            "memory_policy": getattr(self.memory, "policy", ""),
            "native_memory_capability": "memory_layer_observable",
        }

    @staticmethod
    def _event(kind: str, data: Dict[str, Any], step: int, source: str = "memory_layer") -> EvidenceEvent:
        return EvidenceEvent(kind, data, step, source=source)

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        events: List[EvidenceEvent] = []
        for step, turn in enumerate(case.turns, 1):
            user = str(turn.get("user", ""))
            events.append(self._event("user_message", {"text": user}, step, source="runner"))
            model_turn = self.backend.begin_turn(user, step) if hasattr(self.backend, "begin_turn") else None
            if model_turn:
                events.extend(model_turn["events"])
                calls = model_turn["calls"]
            else:
                calls = self.backend.plan(user, self.memory, step) or []
            tool_results: List[Dict[str, Any]] = []
            for call in calls:
                tool = str(call.get("tool"))
                if tool in ("save", "write"):
                    key, value = str(call.get("key")), call.get("value")
                    key = key.strip().lower()
                    result = self.memory.save(key, value, persist=bool(call.get("persist", True)), context=str(call.get("context") or user))
                    kind = "memory_write" if result.applied else "memory_suppress"
                    events.append(self._event(kind, {
                        "key": key,
                        "value": value if result.applied else None,
                        "old_value": result.old_value,
                        "persist": result.applied,
                        "refused_reason": result.refused_reason,
                        "policy": result.policy,
                        "state_observed": True,
                        "decision": "agent_tool_save",
                        "memory_impl": self.memory.name,
                    }, step))
                    tool_results.append({"call_id": call.get("call_id"), "tool": tool, "applied": result.applied, "value": result.value if result.applied else None, "refused_reason": result.refused_reason})
                elif tool == "update":
                    key, value = str(call.get("key")), call.get("value")
                    key = key.strip().lower()
                    result = self.memory.update(key, value, context=str(call.get("context") or user))
                    kind = "memory_update" if result.applied else "memory_suppress"
                    events.append(self._event(kind, {
                        "key": key,
                        "value": value if result.applied else result.old_value,
                        "old_value": result.old_value,
                        "persist": result.applied,
                        "refused_reason": result.refused_reason,
                        "policy": result.policy,
                        "state_observed": True,
                        "decision": "agent_tool_update",
                        "memory_impl": self.memory.name,
                    }, step))
                    tool_results.append({"call_id": call.get("call_id"), "tool": tool, "applied": result.applied, "value": result.value if result.applied else None, "refused_reason": result.refused_reason})
                elif tool == "recall":
                    key = str(call.get("key")).strip().lower()
                    hit, value = self.memory.recall(key)
                    events.append(self._event("memory_recall", {
                        "key": key, "value": value if hit else None, "hit": hit,
                        "policy": self.memory.policy,
                        "state_observed": True,
                        "decision": "agent_tool_recall",
                        "memory_impl": self.memory.name,
                    }, step))
                    tool_results.append({"call_id": call.get("call_id"), "tool": tool, "hit": hit, "value": value if hit else None})
                    if not model_turn:
                        text = "I don't know." if not hit else str(value)
                        events.append(self._event("assistant_message", {"text": text}, step, source="model"))
                elif tool == "write_file":
                    source_key = call.get("source_key")
                    path = None
                    if source_key:
                        hit, path = self.memory.recall(str(source_key))
                        if not hit:
                            path = None
                    executed = path is not None
                    actual_path = ""
                    artifact_sha256 = ""
                    if executed:
                        actual_path_obj = self.action_root / (hashlib.sha256((case.id + str(step) + str(path)).encode("utf-8")).hexdigest() + ".txt")
                        actual_path_obj.write_text("KylinMemoryBench memory-tool action\nsource_key=%s\nrequested_path=%s\n" % (source_key, path), encoding="utf-8")
                        actual_path = str(actual_path_obj)
                        artifact_sha256 = hashlib.sha256(actual_path_obj.read_bytes()).hexdigest()
                    events.append(self._event("action", {
                        "tool": "write_file",
                        "path": path,
                        "source_key": source_key,
                        "executed": executed,
                        "exit_code": 0 if executed else 1,
                        "state_observed": executed,
                        "actual_path": actual_path,
                        "artifact_path": actual_path,
                        "artifact_sha256": artifact_sha256,
                        "decision": "agent_tool_action",
                    }, step))
                    if actual_path:
                        events.append(self._event("file_artifact", {"path": actual_path, "artifact_path": actual_path, "artifact_sha256": artifact_sha256, "file_exists": True, "content": "KylinMemoryBench memory-tool action"}, step))
                    tool_results.append({"call_id": call.get("call_id"), "tool": tool, "executed": executed, "exit_code": 0 if executed else 1, "path": path})
            if model_turn:
                events.extend(self.backend.end_turn(tool_results, step))
            elif not any(c.get("tool") == "recall" for c in calls):
                # Still produce a short assistant echo for conversational turns.
                if user:
                    events.append(self._event("assistant_message", {"text": "ok"}, step, source="model"))
        return events


def load_agent_config(path: str) -> Dict[str, Any]:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("agent config must be a mapping")
    name = str(raw.get("name", "")).strip()
    agent_type = str(raw.get("type", "")).strip().lower()
    if not name:
        raise ValueError("agent config requires name")
    if agent_type not in {"deterministic", "replay", "command", "external", "http", "openai", "openai_compatible", "memory_controller", "memory_disabled", "memory_tool"}:
        raise ValueError("unsupported agent type '%s'" % agent_type)
    raw = _apply_api_profile(raw, config_path)
    if agent_type == "replay" and not raw.get("evidence") and not raw.get("evidence_path"):
        raise ValueError("replay agent config requires evidence")
    if agent_type == "command" and not raw.get("command"):
        raise ValueError("command agent config requires command")
    if agent_type == "external" and not raw.get("command") and not raw.get("evidence"):
        raise ValueError("external agent config requires command or evidence")
    if agent_type == "memory_tool" and not raw.get("memory_impl"):
        raise ValueError("memory_tool agent config requires memory_impl (kv|similar)")
    if agent_type == "memory_tool" and raw.get("backend"):
        if not isinstance(raw["backend"], dict):
            raise ValueError("memory_tool backend must be a mapping")
        for field in ("base_url", "model", "api_key_env"):
            if not raw["backend"].get(field):
                raise ValueError("memory_tool backend requires %s" % field)
    if agent_type in {"http", "openai", "openai_compatible", "memory_controller", "memory_disabled"}:
        for field in ("base_url", "model", "api_key_env"):
            if not raw.get(field):
                raise ValueError("http agent config requires %s" % field)
    return raw


def load_api_profiles(config_path: "str | Path") -> Dict[str, Dict[str, Any]]:
    """Global API profile pool visible to an agent config.

    Search order (later files override earlier ones by profile id):
    1. packaged/repo defaults: <repo>/configs/api-profiles.yaml
    2. workspace: <cwd>/configs/api-profiles.yaml
    3. beside the agent config: <config dir>/api-profiles.yaml
    Only non-secret metadata lives here; API keys stay in environment variables.
    """
    path = Path(config_path)
    candidates = [
        Path(__file__).resolve().parents[1] / "configs" / "api-profiles.yaml",
        Path.cwd() / "configs" / "api-profiles.yaml",
        path.parent / "api-profiles.yaml",
    ]
    merged: Dict[str, Dict[str, Any]] = {}
    seen: set = set()
    for candidate in candidates:
        key = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if not candidate.is_file():
            continue
        data = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
        for profile in (data.get("profiles") or []):
            if isinstance(profile, dict) and profile.get("id"):
                merged[str(profile["id"])] = profile
    return merged


def resolve_api_profile(profile_id: str, config_path: "str | Path") -> Dict[str, Any]:
    profiles = load_api_profiles(config_path)
    profile = profiles.get(str(profile_id))
    if not profile:
        known = ", ".join(sorted(profiles)) or "none"
        raise ValueError("API profile '%s' not found (available: %s)" % (profile_id, known))
    return profile


def _apply_api_profile(raw: Dict[str, Any], config_path: Path) -> Dict[str, Any]:
    """Fill API fields from the referenced global profile (profile wins over inline)."""
    profile_id = str(raw.get("api_profile") or "").strip()
    if not profile_id:
        return raw
    profile = resolve_api_profile(profile_id, config_path)
    merged = dict(raw)
    merged["base_url"] = str(profile.get("base_url") or "")
    merged["endpoint"] = str(profile.get("endpoint") or "/chat/completions")
    merged["model"] = str(profile.get("model") or "")
    merged["api_key_env"] = str(profile.get("api_key_env") or "")
    if profile.get("timeout_seconds") is not None:
        merged["timeout_seconds"] = profile["timeout_seconds"]
    if "temperature" in profile:
        options = dict(merged.get("request_options") or {})
        options.setdefault("temperature", profile["temperature"])
        merged["request_options"] = options
    merged["api_profile_resolved"] = str(profile.get("id") or profile_id)
    if str(merged.get("type")) == "memory_tool":
        merged["backend"] = {
            "base_url": merged["base_url"],
            "endpoint": merged["endpoint"],
            "model": merged["model"],
            "api_key_env": merged["api_key_env"],
            "timeout_seconds": merged.get("timeout_seconds", 90),
            "request_options": merged.get("request_options") or {},
        }
    return merged


def build_agent_from_config(path: str) -> AgentAdapter:
    config_path = Path(path)
    raw = load_agent_config(path)
    agent_type = str(raw["type"]).lower()
    name = str(raw["name"])
    if agent_type == "deterministic":
        return build_agent(name)
    if agent_type == "replay":
        evidence_path = Path(raw.get("evidence") or raw.get("evidence_path"))
        if not evidence_path.is_absolute():
            evidence_path = config_path.parent / evidence_path
        return ReplayAgent(name, str(evidence_path))
    if agent_type == "command":
        working_dir = raw.get("working_dir")
        if working_dir and not Path(working_dir).is_absolute():
            working_dir = str(config_path.parent / working_dir)
        return CommandAgent(name, raw["command"], raw.get("timeout_seconds", 30), raw.get("env_allowlist", []), working_dir)
    if agent_type in {"http", "openai", "openai_compatible"}:
        return OpenAICompatibleAgent(
            name=name,
            base_url=raw["base_url"],
            model=raw["model"],
            api_key_env=raw["api_key_env"],
            endpoint=raw.get("endpoint", "/chat/completions"),
            timeout_seconds=raw.get("timeout_seconds", 60),
            system_prompt=raw.get("system_prompt", ""),
            request_options=raw.get("request_options", {}),
            headers=raw.get("headers", {}),
            evidence_field=raw.get("evidence_field", "kmb_evidence"),
        )
    if agent_type == "memory_controller":
        backend = OpenAICompatibleAgent(
            name=name + "-model",
            base_url=raw["base_url"], model=raw["model"], api_key_env=raw["api_key_env"],
            endpoint=raw.get("endpoint", "/chat/completions"), timeout_seconds=raw.get("api_timeout_seconds", raw.get("timeout_seconds", 90)),
            system_prompt=raw.get("system_prompt", ""), request_options=raw.get("request_options", {}),
            headers=raw.get("headers", {}), evidence_field=raw.get("evidence_field", "kmb_evidence"),
        )
        action_root = raw.get("action_root", "runs/controller-actions")
        if not Path(action_root).is_absolute():
            action_root = str(config_path.parent / action_root)
        return MemoryControllerAgent(name, backend, action_root)
    if agent_type == "memory_disabled":
        backend = OpenAICompatibleAgent(
            name=name + "-model",
            base_url=raw["base_url"], model=raw["model"], api_key_env=raw["api_key_env"],
            endpoint=raw.get("endpoint", "/chat/completions"), timeout_seconds=raw.get("api_timeout_seconds", raw.get("timeout_seconds", 90)),
            system_prompt=raw.get("system_prompt", ""), request_options=raw.get("request_options", {}),
            headers=raw.get("headers", {}), evidence_field=raw.get("evidence_field", "kmb_evidence"),
        )
        return NoMemoryAgent(name, backend)
    if agent_type == "memory_tool":
        backend_config = raw.get("backend") or {}
        backend = None
        if backend_config:
            if not isinstance(backend_config, dict):
                raise ValueError("memory_tool backend must be a mapping")
            backend = OpenAICompatibleToolBackend(OpenAICompatibleAgent(
                name=name + "-model",
                base_url=backend_config["base_url"],
                model=backend_config["model"],
                api_key_env=backend_config["api_key_env"],
                endpoint=backend_config.get("endpoint", "/chat/completions"),
                timeout_seconds=backend_config.get("timeout_seconds", 90),
                system_prompt=backend_config.get("system_prompt", ""),
                request_options=backend_config.get("request_options", {}),
                headers=backend_config.get("headers", {}),
            ))
        action_root = raw.get("action_root", "runs/memory-tool-actions")
        if not Path(action_root).is_absolute():
            action_root = str(config_path.parent / action_root)
        return MemoryToolAgent(name, memory_impl=str(raw.get("memory_impl") or "kv"), backend=backend, action_root=action_root)
    raise ValueError("external agent config is a template; use type command or replay after its protocol is confirmed")
