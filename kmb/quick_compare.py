"""One-command orchestration for comparing already-installed Agents."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_registry import AgentProfile, discover_agents, profile_to_dict
from .agent_adapters.hermes import HermesAdapter
from .agent_adapters.kylinagent import KylinAgentAdapter
from .agent_adapters.kylinbot import KylinBotAdapter
from .agent_adapters.openclaw import OpenClawAdapter
from .report import radar_svg, write_compare, write_html_report, write_markdown
from .runner import load_suite, run_suite, validate_cases


QUICK_SUITE = "suites/quick.yaml"
DEFAULT_SEED = 42
DEFAULT_RETRIES = 1
DEFAULT_TIMEOUT = 180.0


@dataclass
class QuickCompareOptions:
    agent_ids: Optional[List[str]] = None
    out_dir: str = ""
    seed: int = DEFAULT_SEED
    retries: int = DEFAULT_RETRIES
    timeout: float = DEFAULT_TIMEOUT
    agent_homes: Optional[Dict[str, str]] = None
    suite: str = QUICK_SUITE
    preflight_only: bool = False


def _home(root: Path) -> Path:
    import os
    return Path(os.environ.get("KMB_AGENT_HOME") or Path.home()).expanduser()


def adapter_for_profile(profile: AgentProfile, timeout: float, home: Optional[Path] = None):
    home = Path(home).expanduser() if home else _home(Path.cwd())
    if profile.id == "kylinbot":
        return KylinBotAdapter(home / ".kylinbot/workspace/memory/brain.db", timeout=timeout, home=home)
    if profile.id == "hermes":
        return HermesAdapter(home / ".hermes/state.db", timeout=timeout, home=home)
    if profile.id == "openclaw":
        return OpenClawAdapter(home=home, timeout=timeout)
    if profile.id == "kylinagent":
        return KylinAgentAdapter(home=home)
    raise ValueError("unsupported discovered Agent: %s" % profile.id)


def _select_profiles(options: QuickCompareOptions, profiles: List[AgentProfile], allow_not_runnable: bool = False) -> List[AgentProfile]:
    by_id = {profile.id: profile for profile in profiles}
    selected_ids = list(options.agent_ids or [profile.id for profile in profiles if profile.runnable][:2])
    if len(selected_ids) != 2:
        raise ValueError("quick compare requires exactly two runnable Agents; use --agents A B")
    if len(set(selected_ids)) != 2:
        raise ValueError("quick compare requires two distinct Agents")
    selected: List[AgentProfile] = []
    for agent_id in selected_ids:
        profile = by_id.get(agent_id)
        if profile is None:
            raise ValueError("unknown Agent '%s'; run discover-agents to inspect availability" % agent_id)
        if not profile.installed:
            raise ValueError("Agent '%s' is not installed: %s" % (profile.display_name, profile.reason))
        if not profile.runnable and not allow_not_runnable:
            raise ValueError("Agent '%s' is installed but not automatically runnable: %s" % (profile.display_name, profile.reason))
        selected.append(profile)
    return selected


def run_quick_compare(options: QuickCompareOptions, root: Optional[Path] = None) -> Dict[str, Any]:
    workspace = Path(root or Path.cwd()).resolve()
    profiles = discover_agents(workspace)
    selected = _select_profiles(options, profiles, allow_not_runnable=bool(options.preflight_only))
    suite_path = Path(options.suite)
    if not suite_path.is_absolute():
        suite_path = workspace / suite_path
    cases = load_suite(str(suite_path))
    validate_cases(cases, require_all_capabilities=True)
    output = Path(options.out_dir) if options.out_dir else workspace / "runs" / ("quick-compare-" + uuid.uuid4().hex[:12])
    if not output.is_absolute():
        output = workspace / output
    output.mkdir(parents=True, exist_ok=True)
    run_id = "quick-" + uuid.uuid4().hex[:12]
    summaries: List[Dict[str, Any]] = []
    preflight: List[Dict[str, Any]] = []
    adapters = []
    for profile in selected:
        home = Path(options.agent_homes[profile.id]).expanduser() if options.agent_homes and profile.id in options.agent_homes else None
        adapter = adapter_for_profile(profile, options.timeout, home=home)
        report = adapter.preflight() if hasattr(adapter, "preflight") else {"agent": profile.id, "status": "ready", "checks": []}
        report = dict(report)
        report.setdefault("agent", profile.id)
        preflight.append(report)
        adapters.append((profile, adapter, report))
    blocked = [item for item in preflight if item.get("status") != "ready"]
    # Read-only preflight mode: report adapter readiness without starting a
    # single Agent turn, so operator checks never consume model Tokens. Even a
    # blocked preflight is reported rather than raised here.
    if options.preflight_only:
        payload = {
            "run_id": run_id,
            "suite": str(options.suite),
            "agents": [profile_to_dict(profile) for profile in selected],
            "parameters": {"seed": options.seed, "retries": options.retries, "timeout": options.timeout},
            "preflight": preflight,
            "status": "preflight",
            "turns_started": 0,
            "blocked": [item["agent"] for item in blocked],
            "result_directory": str(output),
            "boundary": "read-only preflight; no Agent turns were started and no model Tokens were consumed",
        }
        (output / "quick-compare.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    if blocked:
        details = "; ".join("%s: %s" % (item.get("agent", "agent"), item.get("reason", "preflight blocked")) for item in blocked)
        (output / "quick-compare.json").write_text(json.dumps({
            "run_id": run_id,
            "suite": QUICK_SUITE,
            "agents": [profile_to_dict(profile) for profile in selected],
            "parameters": {"seed": options.seed, "retries": options.retries, "timeout": options.timeout},
            "preflight": preflight,
            "status": "blocked",
            "result_directory": str(output),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        raise RuntimeError("quick compare preflight failed; no Agent turns were started: %s" % details)
    for profile, adapter, _report in adapters:
        agent_dir = output / profile.id
        summary = run_suite(
            adapter,
            cases,
            str(agent_dir),
            timeout_seconds=options.timeout,
            retries=options.retries,
            run_id=run_id + "-" + profile.id,
            seed=options.seed,
        )
        summary["discovery"] = profile_to_dict(profile)
        summary["preflight"] = _report
        write_markdown(summary, str(agent_dir / "result.md"))
        (agent_dir / "radar.svg").write_text(radar_svg(summary["dimensions"], score_valid=summary.get("score_valid", True)), encoding="utf-8")
        write_html_report([summary], str(agent_dir / "result.html"))
        (agent_dir / "result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        summaries.append(summary)
    comparison = write_compare(summaries, str(output))
    metadata = {
        "run_id": run_id,
        "status": "completed",
        "suite": suite_path.relative_to(workspace).as_posix() if suite_path.is_relative_to(workspace) else str(suite_path),
        "agents": [profile_to_dict(profile) for profile in selected],
        "parameters": {"seed": options.seed, "retries": options.retries, "timeout": options.timeout},
        "preflight": preflight,
        "result_directory": str(output),
        "comparison": comparison,
    }
    (output / "quick-compare.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata
