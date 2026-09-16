#!/usr/bin/env python3
"""Run safe, auditable openKylin system-boundary checks.

Only the evaluator process, a user network namespace, and a private test
directory are touched. OS reboot and cross-user checks are recorded as
not-executed unless an external controller and dedicated test identities are
available.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kmb.models import EvidenceEvent, validate_event_dict  # noqa: E402


SAFE_SCENARIOS = ("process-restart", "system-reboot", "user-switch", "offline", "permissions")


def _uid() -> int:
    getter = getattr(os, "geteuid", None)
    return int(getter()) if getter is not None else -1


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def _run(command: List[str], timeout: float = 10.0) -> Dict[str, Any]:
    started = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        error = ""
    except Exception as exc:  # pragma: no cover - platform-specific process failures
        return {"command": command, "exit_code": None, "stdout": "", "stderr": str(exc), "elapsed_ms": round((time.monotonic() - started) * 1000, 1), "error": type(exc).__name__}
    return {
        "command": command,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
        "error": error,
    }


class ScenarioRecorder:
    def __init__(self, output: Path, run_id: str):
        self.output = output
        self.run_id = run_id
        self.events: List[Dict[str, Any]] = []
        self.counter = 0

    def event(self, scenario: str, kind: str, data: Dict[str, Any], step: int = 1, *, source: str = "runner", trust: str = "verified") -> Dict[str, Any]:
        self.counter += 1
        correlation = "%s:%s" % (self.run_id, scenario)
        payload = dict(data)
        payload.setdefault("scenario", scenario)
        payload.setdefault("source", source)
        payload.setdefault("executor", "system-scenario-executor")
        payload.setdefault("trust_level", trust)
        event = EvidenceEvent(
            kind,
            payload,
            step,
            source=source,
            correlation_id=correlation,
            event_id="%s:%04d" % (correlation, self.counter),
            trust_level=trust,
            fact_id=str(payload.get("fact_id", "")),
            fact_version=payload.get("fact_version"),
            scope=str(payload.get("scope", "")),
            artifact_path=str(payload.get("artifact_path", "")),
            artifact_sha256=str(payload.get("artifact_sha256", "")),
        )
        raw = {"run_id": self.run_id, "case_id": scenario, **event.to_dict()}
        validate_event_dict(raw)
        self.events.append(raw)
        return raw

    def write(self) -> None:
        path = self.output / "evidence.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in self.events), encoding="utf-8")


def _fact(scenario: str, key: str, value: str, scope: str, version: int = 1, persistence: str = "persistent", sensitivity: str = "normal") -> Dict[str, Any]:
    return {
        "fact_id": "%s:%s" % (scenario, key),
        "key": key,
        "value": value,
        "persistence": persistence,
        "sensitivity": sensitivity,
        "scope": scope,
        "version": version,
        "expires_at": None,
        "ttl_steps": None,
        "provenance": {"source": "synthetic-system-scenario", "scenario": scenario},
    }


def _artifact(recorder: ScenarioRecorder, scenario: str, path: Path, fact: Dict[str, Any], step: int, content: str) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    digest = _sha256(path)
    recorder.event(scenario, "action", {
        "tool": "write_file",
        "path": fact["value"],
        "requested_path": fact["value"],
        "actual_path": str(path),
        "artifact_path": str(path),
        "artifact_sha256": digest,
        "file_exists": True,
        "exit_code": 0,
        "executed": True,
        "execution_observed": True,
        "execution_scope": "private-test-directory",
        "fact_id": fact["fact_id"],
        "fact_version": fact["version"],
        "scope": fact["scope"],
        "persistence": fact["persistence"],
        "sensitivity": fact["sensitivity"],
        "provenance": fact["provenance"],
    }, step)
    recorder.event(scenario, "tool_result", {
        "tool": "write_file", "exit_code": 0, "executed": True,
        "artifact_path": str(path), "artifact_sha256": digest,
        "fact_id": fact["fact_id"], "fact_version": fact["version"], "scope": fact["scope"],
    }, step)
    recorder.event(scenario, "file_artifact", {
        "artifact_path": str(path), "artifact_sha256": digest, "file_exists": True,
        "content_sha256": digest, "fact_id": fact["fact_id"], "fact_version": fact["version"], "scope": fact["scope"],
    }, step)
    return {"path": str(path), "sha256": digest, "exit_code": 0}


def run_process_restart(recorder: ScenarioRecorder, output: Path) -> Dict[str, Any]:
    scenario = "process-restart"
    state_path = output / "artifacts" / scenario / "state.json"
    marker_path = output / "artifacts" / scenario / "process-markers.jsonl"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    fact = _fact(scenario, "workspace", "/data/process-restart-v2", "project-process", version=2)
    state_path.write_text(json.dumps({"fact": fact}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pre = _run([sys.executable, str(Path(__file__).resolve()), "--worker", "process", "--phase", "pre", "--state", str(state_path), "--marker", str(marker_path)])
    post = _run([sys.executable, str(Path(__file__).resolve()), "--worker", "process", "--phase", "post", "--state", str(state_path), "--marker", str(marker_path)])
    markers = []
    if marker_path.exists():
        markers = [json.loads(line) for line in marker_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    pids = [item.get("pid") for item in markers]
    passed = pre.get("exit_code") == 0 and post.get("exit_code") == 0 and len(pids) == 2 and pids[0] != pids[1]
    recorder.event(scenario, "memory_write", {**fact, "state_transition": "write"}, 1)
    recorder.event(scenario, "restart_boundary", {
        "boundary_type": "agent_process_restart", "system_restart": False,
        "process_pid_before": pids[0] if pids else None, "process_pid_after": pids[1] if len(pids) > 1 else None,
        "same_state_file": state_path.exists(), "state_transition": "restart",
        "fact_id": fact["fact_id"], "fact_version": fact["version"], "scope": fact["scope"],
        "persistence": fact["persistence"], "sensitivity": fact["sensitivity"], "provenance": fact["provenance"],
    }, 2)
    recorder.event(scenario, "memory_recall", {**fact, "hit": passed, "state_transition": "recall"}, 3)
    artifact = _artifact(recorder, scenario, output / "artifacts" / scenario / "action-result.txt", fact, 4, "process restart action\nworkspace=%s\n" % fact["value"])
    return {
        "scenario": scenario, "status": "pass" if passed else "fail", "score": 1.0 if passed else 0.0,
        "failure_type": None if passed else "action_or_executor_failure",
        "reason": "two distinct evaluator PIDs resumed the same persistent fact" if passed else "process restart worker did not resume as expected",
        "worker": {"pre": pre, "post": post, "pids": pids}, "artifact": artifact,
        "limitations": ["controlled evaluator process restart; not an OS reboot", "no model API request was made"],
    }


def process_worker(phase: str, state: Path, marker: Path) -> int:
    payload = json.loads(state.read_text(encoding="utf-8"))
    marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"phase": phase, "pid": os.getpid(), "fact_version": payload["fact"]["version"], "timestamp": time.time()}) + "\n")
    return 0


def run_offline(recorder: ScenarioRecorder, output: Path) -> Dict[str, Any]:
    scenario = "offline"
    fact = _fact(scenario, "workspace", "/data/offline-v2", "project-offline", version=2)
    code = (
        "import socket,sys; s=socket.socket(); s.settimeout(2); "
        "\ntry: s.connect(('1.1.1.1',443)); print('network_blocked=false'); sys.exit(7) "
        "\nexcept Exception as exc: print('network_blocked=true error='+type(exc).__name__); sys.exit(0)"
    )
    unshare = shutil.which("unshare")
    probe = _run([unshare or "unshare", "--user", "--mount", "--net", "--fork", sys.executable, "-c", code], timeout=8) if unshare else {"exit_code": None, "stdout": "", "stderr": "unshare unavailable", "command": []}
    blocked = probe.get("exit_code") == 0 and "network_blocked=true" in probe.get("stdout", "")
    recorder.event(scenario, "memory_write", {**fact, "state_transition": "write"}, 1)
    recorder.event(scenario, "capability_probe", {
        "probe": "user_network_namespace", "network_blocked": blocked,
        "command": probe.get("command"), "exit_code": probe.get("exit_code"),
        "stdout": probe.get("stdout", "")[-1000:], "stderr": probe.get("stderr", "")[-1000:],
        "fact_id": fact["fact_id"], "fact_version": fact["version"], "scope": fact["scope"],
    }, 2, trust="observed" if blocked else "unverified")
    if blocked:
        recorder.event(scenario, "memory_recall", {**fact, "hit": True, "state_transition": "recall", "recovered_after_boundary": True}, 3)
    artifact = _artifact(recorder, scenario, output / "artifacts" / scenario / "action-result.txt", fact, 4, "offline recovery action\nworkspace=%s\n" % fact["value"]) if blocked else None
    return {
        "scenario": scenario, "status": "pass" if blocked and artifact else "not_executed" if probe.get("exit_code") is None else "fail",
        "score": 1.0 if blocked and artifact else None,
        "failure_type": None if blocked and artifact else "environment_capability_insufficient" if probe.get("exit_code") is None else "offline_probe_failed",
        "reason": "user network namespace blocked external connect; no API response was fabricated" if blocked else "network namespace did not prove blocking",
        "probe": probe, "artifact": artifact,
        "limitations": ["only a process network namespace was isolated", "no cloud model request was attempted while offline"],
    }


def run_permissions(recorder: ScenarioRecorder, output: Path) -> Dict[str, Any]:
    scenario = "permissions"
    if os.name != "posix":
        return {"scenario": scenario, "status": "not_executed", "score": None, "failure_type": "environment_capability_insufficient", "reason": "POSIX owner permission semantics are unavailable on this host", "limitations": ["run in the openKylin POSIX environment"]}
    if _uid() == 0:
        return {"scenario": scenario, "status": "not_executed", "score": None, "failure_type": "environment_capability_insufficient", "reason": "root would bypass the intended owner permission denial", "limitations": ["run as a dedicated unprivileged test user"]}
    root = output / "artifacts" / scenario
    root.mkdir(parents=True, exist_ok=True)
    restricted = root / "restricted.txt"
    restricted.write_text("synthetic permission fact\n", encoding="utf-8")
    fact = _fact(scenario, "workspace", "/data/permissions-v2", "project-permissions", version=2)
    os.chmod(restricted, 0)
    denied = False
    denied_error = ""
    try:
        restricted.read_text(encoding="utf-8")
    except PermissionError as exc:
        denied, denied_error = True, type(exc).__name__
    finally:
        os.chmod(restricted, 0o600)
    restored = restricted.read_text(encoding="utf-8") == "synthetic permission fact\n"
    recorder.event(scenario, "memory_write", {**fact, "state_transition": "write"}, 1)
    recorder.event(scenario, "action", {
        "tool": "read_file", "path": str(restricted), "exit_code": 1 if denied else 0,
        "executed": False if denied else True, "blocked": denied, "blocked_reason": "permission_denied" if denied else None,
        "permission_mode": "000", "fact_id": fact["fact_id"], "fact_version": fact["version"], "scope": fact["scope"],
    }, 2, trust="verified" if denied else "observed")
    recorder.event(scenario, "tool_result", {"tool": "read_file", "exit_code": 1 if denied else 0, "stderr": denied_error, "permission_restored": restored, "fact_id": fact["fact_id"], "fact_version": fact["version"], "scope": fact["scope"]}, 2)
    if restored:
        recorder.event(scenario, "memory_recall", {**fact, "hit": True, "state_transition": "recall", "recovered_after_boundary": True}, 3)
    passed = denied and restored
    return {
        "scenario": scenario, "status": "pass" if passed else "fail", "score": 1.0 if passed else 0.0,
        "failure_type": None if passed else "permission_executor_failure", "reason": "private test file denied then readable after permission restore" if passed else "permission transition was not observed",
        "permission_file": str(restricted), "denied": denied, "restored": restored,
        "limitations": ["only the dedicated test file was chmod'ed", "no system or project file was modified"],
    }


def run_not_executed(recorder: ScenarioRecorder, scenario: str, reason: str, required: List[str], recovery: List[str]) -> Dict[str, Any]:
    plan = {"scenario": scenario, "status": "not_executed", "reason": reason, "required_capabilities": required, "recovery_steps": recovery}
    recorder.event(scenario, "capability_probe", {"available": False, "reason": reason, "required_capabilities": required}, 1, trust="observed")
    return {**plan, "score": None, "failure_type": "environment_capability_insufficient", "limitations": ["not executed; no ordinary CLI result is substituted"]}


def run_all(output: Path, run_id: str, selected: List[str]) -> Dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    recorder = ScenarioRecorder(output, run_id)
    results = []
    if "process-restart" in selected:
        results.append(run_process_restart(recorder, output))
    if "system-reboot" in selected:
        results.append(run_not_executed(recorder, "system-reboot", "no authenticated root or external post-reboot control channel", ["root_or_authenticated_sudo", "post_reboot_control_channel", "boot_marker_recovery"], ["write pre-reboot marker", "reboot only from VM console/controller", "verify post-boot marker and SSH reconnect", "run recovery action", "archive boot ID and logs"]))
    if "user-switch" in selected:
        results.append(run_not_executed(recorder, "user-switch", "only one interactive user exists and no authorized user-creation/switch path is available", ["dedicated_test_users", "authenticated_switch_executor", "separate_home_or_scope"], ["create two disposable users", "write scoped synthetic fact as user A", "switch to user B", "verify recall miss and return to user A", "delete only disposable users"]))
    if "offline" in selected:
        results.append(run_offline(recorder, output))
    if "permissions" in selected:
        results.append(run_permissions(recorder, output))
    recorder.write()
    summary = {
        "run_id": run_id,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "system": {"platform": platform.platform(), "python": platform.python_version(), "uid": _uid()},
        "executor": "controlled_system_scenario_executor",
        "scenarios": results,
        "scoreable_scenarios": sum(1 for item in results if item.get("score") is not None),
        "passed_scenarios": sum(1 for item in results if item.get("status") == "pass"),
        "not_executed_scenarios": sum(1 for item in results if item.get("status") == "not_executed"),
        "native_memory_events": 0,
        "model_requests": 0,
        "boundary_statement": "These checks observe a controlled evaluator, user namespace, and private test directory. They do not prove model-native memory or unexecuted OS boundaries.",
    }
    (output / "system-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# openKylin 系统级场景记录", "", "本记录只包含受控执行器、用户网络 namespace 和专用测试目录的实际证据；未执行场景不以普通 CLI 结果替代。", ""]
    for item in results:
        lines.append("- `%s`: **%s**；%s" % (item["scenario"], item["status"], item.get("reason", "")))
    lines.extend(["", "- 原生记忆事件：`0`；模型请求：`0`。本批次不是模型 API 结果，不能证明模型原生长期记忆能力。", ""])
    (output / "system-summary.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run safe openKylin system-boundary checks")
    parser.add_argument("--out", required=False)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--scenario", action="append", choices=SAFE_SCENARIOS)
    parser.add_argument("--worker", choices=["process"])
    parser.add_argument("--phase")
    parser.add_argument("--state")
    parser.add_argument("--marker")
    args = parser.parse_args(argv)
    if args.worker == "process":
        if not args.phase or not args.state or not args.marker:
            return 2
        return process_worker(args.phase, Path(args.state), Path(args.marker))
    if not args.out:
        parser.error("--out is required unless --worker is used")
    run_id = args.run_id or "system-scenarios-%s" % uuid.uuid4().hex[:12]
    selected = args.scenario or list(SAFE_SCENARIOS)
    summary = run_all(Path(args.out), run_id, selected)
    print(json.dumps({"status": "ok", "run_id": run_id, "out": args.out, "passed": summary["passed_scenarios"], "not_executed": summary["not_executed_scenarios"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
