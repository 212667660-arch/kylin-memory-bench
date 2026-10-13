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
    executable_path: Optional[str] = None
    detected_paths: List[str] = field(default_factory=list)
    detection_sources: List[str] = field(default_factory=list)


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


def host_home() -> Path:
    """Return this OS user's home independently of evaluation HOME overrides."""
    if os.name != "nt":
        import pwd
        return Path(pwd.getpwuid(os.getuid()).pw_dir)
    return Path(os.environ.get("USERPROFILE") or Path.home())


def _display_path(path: Path, home: Path) -> str:
    try:
        return "~/" + path.resolve().relative_to(home.resolve()).as_posix()
    except ValueError:
        return str(path)


def resolve_agent_executable(name: str, home: Optional[Path] = None) -> Optional[str]:
    """Find an executable without running it or recursively scanning the host.

    Service PATHs can omit per-user npm/pip installations. Use the same bounded
    search for discovery and execution, including the real user's HOME when an
    evaluation uses an isolated memory directory.
    """
    found = shutil.which(name)
    if found or Path(name).is_absolute() or Path(name).name != name:
        return found
    homes = list(dict.fromkeys([Path(home).expanduser() if home else _home(), host_home()]))
    directories = []
    for base in homes:
        directories.extend([
            base / ".local/bin", base / "bin", base / ".npm-global/bin",
            base / ".npm/bin", base / ".local/share/pnpm",
            base / ".bun/bin", base / ".hermes/venv/bin",
            base / ".kylin-agent-runtime/agent-runtime/venv/bin",
        ])
        if os.name == "nt":
            directories.append(base / "AppData/Roaming/npm")
    if os.name != "nt":
        directories.extend([Path("/usr/local/bin"), Path("/usr/bin"), Path("/bin"), Path("/snap/bin")])
    return shutil.which(name, path=os.pathsep.join(str(path) for path in directories))


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
    installation_paths: Optional[List[Path]] = None,
    required_memory_path: Optional[Path] = None,
) -> AgentProfile:
    existing_paths = [path for path in paths if path.is_file() or path.is_socket()]
    existing_installation = [path for path in (installation_paths or []) if path.is_file()]
    executable = next((found for name in command_names if (found := path_lookup(name))), None)
    installed = bool(existing_paths or existing_installation or executable)
    memory_ready = required_memory_path.is_file() if required_memory_path else bool(existing_paths)
    runnable = bool(executable and memory_ready)
    observed_mode = evidence_mode if memory_ready else ("conversation_only" if executable else "unavailable")
    if existing_paths:
        reason = "检测到已安装存储路径"
    elif executable:
        reason = "%s可用，但尚未发现记忆存储路径" % command_label
    elif existing_installation:
        reason = "检测到智能体配置文件，但未发现可执行文件或记忆存储"
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
        executable_path=str(executable) if executable else None,
        detected_paths=[_display_path(path, home) for path in existing_paths + existing_installation],
        detection_sources=(["executable"] if executable else []) + (["memory_store"] if existing_paths else []) + (["configuration_file"] if existing_installation else []),
    )


def discover_agents(root: Optional[Path] = None, path_lookup: Optional[PathLookup] = None, home: Optional[Path] = None) -> List[AgentProfile]:
    """Return safe metadata for the four supported openKylin Agents.

    ``root`` is accepted for callers that already resolve a workspace; host
    Agent data always comes from the current user's home directory. Tests use
    ``KMB_AGENT_HOME`` to point discovery at an isolated fixture tree. An explicit
    ``home`` lets the workbench inspect host installation separately from the
    selected evaluation HOME without changing the process environment.
    """
    del root  # reserved for future workspace profile lookup
    home = Path(home).expanduser() if home is not None else _home()
    lookup = path_lookup or (lambda name: resolve_agent_executable(name, home))

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
        installation_paths=[home / ".kylinbot/config.json", home / ".kylinbot/config.yaml"],
        required_memory_path=home / ".kylinbot/workspace/memory/brain.db",
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
        installation_paths=[home / ".hermes/config.yaml"],
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
        installation_paths=[home / ".openclaw/openclaw.json"],
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
    if kylinagent.installed:
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
