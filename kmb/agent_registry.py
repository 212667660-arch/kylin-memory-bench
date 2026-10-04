"""Safe discovery metadata for Agents already installed on the host.

Discovery intentionally checks only well-known paths and executable names. It
does not open databases, start an Agent, read conversation contents, or load
credentials. Runtime adapters are responsible for producing evidence.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional


EvidenceMode = str
PathLookup = Callable[[str], Optional[str]]


@dataclass
class AgentProfile:
    id: str
    display_name: str
    installed: bool
    runnable: bool
    adapter: str
    version: Optional[str] = None
    evidence_mode: EvidenceMode = "unavailable"
    memory_paths: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    config_path: Optional[str] = None
    reason: str = ""


CAPABILITIES = [
    "retention",
    "memory_recall",
    "dynamic_update",
    "similar_distinction",
    "boundary",
    "task_reuse",
]


def _home() -> Path:
    configured = os.environ.get("KMB_AGENT_HOME")
    return Path(configured).expanduser() if configured else Path.home()


def _display_path(path: Path, home: Path) -> str:
    try:
        return "~/" + path.resolve().relative_to(home.resolve()).as_posix()
    except ValueError:
        return str(path)


def _profile(
    *,
    agent_id: str,
    display_name: str,
    adapter: str,
    home: Path,
    paths: List[Path],
    command_names: List[str],
    path_lookup: PathLookup,
    evidence_mode: EvidenceMode,
    capabilities: Optional[List[str]] = None,
    command_label: str = "可执行文件",
) -> AgentProfile:
    existing_paths = [path for path in paths if path.is_file() or path.is_socket()]
    command = next((name for name in command_names if path_lookup(name)), None)
    installed = bool(existing_paths or command)
    runnable = bool(command and existing_paths)
    observed_mode = evidence_mode if existing_paths else ("conversation_only" if command else "unavailable")
    if existing_paths:
        reason = "检测到已安装存储路径"
    elif command:
        reason = "%s %s 可用，但尚未发现记忆存储路径" % (command_label, command)
    else:
        reason = "未检测到已知存储路径或可执行文件"
    return AgentProfile(
        id=agent_id,
        display_name=display_name,
        installed=installed,
        runnable=runnable,
        adapter=adapter,
        evidence_mode=observed_mode,
        memory_paths=[_display_path(path, home) for path in paths],
        capabilities=list(capabilities or (CAPABILITIES if observed_mode == "agent_memory_observed" else [])),
        reason=reason,
    )


def discover_agents(root: Optional[Path] = None, path_lookup: Optional[PathLookup] = None) -> List[AgentProfile]:
    """Return safe metadata for the four supported openKylin Agents.

    ``root`` is accepted for callers that already resolve a workspace; host
    Agent data always comes from the current user's home directory. Tests use
    ``KMB_AGENT_HOME`` to point discovery at an isolated fixture tree.
    """
    del root  # reserved for future workspace profile lookup
    home = _home()
    lookup = path_lookup or shutil.which

    kylinbot = _profile(
        agent_id="kylinbot",
        display_name="小K KylinBot",
        adapter="kylinbot",
        home=home,
        paths=[
            home / ".kylinbot/workspace/memory/brain.db",
            home / ".kylinbot/workspace/sessions/sessions.db",
        ],
        command_names=["kylin-bot"],
        path_lookup=lookup,
        evidence_mode="agent_memory_observed",
    )
    hermes = _profile(
        agent_id="hermes",
        display_name="Hermes",
        adapter="hermes",
        home=home,
        paths=[home / ".hermes/state.db"],
        command_names=[
            "hermes",
            "hermes-agent",
            str(home / ".kylin-agent-runtime/agent-runtime/venv/bin/hermes"),
        ],
        path_lookup=lookup,
        evidence_mode="agent_memory_observed",
    )
    openclaw_paths = [
        home / ".openclaw/agents/main/agent/openclaw-agent.sqlite",
        home / ".openclaw/workspace/USER.md",
        home / ".openclaw/workspace/MEMORY.md",
    ]
    openclaw = _profile(
        agent_id="openclaw",
        display_name="OpenClaw",
        adapter="openclaw",
        home=home,
        paths=openclaw_paths,
        command_names=["openclaw"],
        path_lookup=lookup,
        evidence_mode="agent_memory_observed",
    )
    kylinagent = _profile(
        agent_id="kylinagent",
        display_name="KylinAgent",
        adapter="kylinagent",
        home=home,
        paths=[
            home / ".kylin-agent-runtime/state.db",
            home / ".kylin-agent-runtime/memory.db",
            home / ".cache/kylin-agent.socket",
        ],
        command_names=["kylin-agent", "kylin-agent-runtime"],
        path_lookup=lookup,
        evidence_mode="gui_observed",
        capabilities=["retention", "memory_recall"],
    )
    # The runtime is installed, but the current adapter has no structured
    # memory API and must not claim that a GUI/service process is runnable.
    kylinagent.runnable = False
    kylinagent.reason = "已安装，但当前只有 GUI/服务级观测，不能自动生成结构化记忆证据"
    return [kylinbot, hermes, openclaw, kylinagent]


def profile_to_dict(profile: AgentProfile) -> Dict[str, object]:
    """Serialize discovery metadata without reading any Agent content."""
    payload = asdict(profile)
    payload["memory_paths"] = list(profile.memory_paths)
    payload["capabilities"] = list(profile.capabilities)
    return payload


def profiles_to_dicts(profiles: List[AgentProfile]) -> List[Dict[str, object]]:
    return [profile_to_dict(profile) for profile in profiles]
