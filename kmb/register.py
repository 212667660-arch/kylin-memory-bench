"""Register OpenAI-compatible models as benchmark-ready agent packs.

Shared by ``python -m kmb.cli register-agent`` and
``scripts/register_openai_agent.py`` so field conventions cannot drift.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

DEFAULT_ENDPOINT = "/chat/completions"
API_KEY_ENV_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,62}$")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if not value:
        raise ValueError("name must contain letters or digits")
    return value[:48]


def resolve_api_key_env(agent_id: str, api_key_env: str = "") -> str:
    resolved = (api_key_env or (agent_id.replace("-", "_").upper() + "_API_KEY")).strip()
    if not API_KEY_ENV_PATTERN.fullmatch(resolved):
        raise ValueError("api_key_env must be UPPER_SNAKE_CASE (e.g. PROVIDER_API_KEY): %s" % resolved)
    return resolved


def build_pack_configs(
    agent_id: str,
    display_name: str,
    base_url: str,
    model: str,
    api_key_env: str,
    endpoint: str = DEFAULT_ENDPOINT,
    temperature: float = 0.0,
    timeout: int = 180,
    provider: str = "",
    description: str = "",
) -> Dict[str, Dict[str, Any]]:
    endpoint = endpoint.strip()
    if not endpoint.startswith("/") or endpoint.startswith("//"):
        raise ValueError("endpoint must start with /")
    base_url = base_url.strip().rstrip("/")
    if not base_url:
        raise ValueError("base_url is required")
    model = model.strip()
    if not model:
        raise ValueError("model is required")
    display_name = (display_name or agent_id).strip()
    temperature_value = int(temperature) if float(temperature).is_integer() else float(temperature)
    timeout_value = int(timeout) if float(timeout).is_integer() else float(timeout)
    base: Dict[str, Any] = {
        "base_url": base_url,
        "endpoint": endpoint,
        "model": model,
        "api_key_env": api_key_env,
        "request_options": {"temperature": temperature_value},
    }
    if provider:
        base["provider"] = provider
    http: Dict[str, Any] = {
        "name": agent_id,
        "type": "http",
        **base,
        "timeout_seconds": timeout_value,
        "description": description or (
            "OpenAI-compatible HTTP agent (%s / %s). Only model text is observable; "
            "prefer the memory_controller pack for long-term-memory scoring."
            % (display_name, model)
        ),
    }
    memory: Dict[str, Any] = {
        "name": agent_id + "-memory",
        "type": "memory_controller",
        **base,
        "api_timeout_seconds": timeout_value,
        "action_root": "../runs/controller-actions",
        "description": (
            "Transparent memory/action controller over %s (%s). "
            "Memory/file events are source=wrapper (system-level); "
            "model replies are source=model. Does not claim native model memory."
            % (display_name, model)
        ),
    }
    no_memory: Dict[str, Any] = {
        "name": agent_id + "-no-memory",
        "type": "memory_disabled",
        **base,
        "api_timeout_seconds": timeout_value,
        "description": (
            "Same backend as %s with external memory/actions disabled "
            "(no_memory_baseline). Contrast for controller on/off."
            % agent_id
        ),
    }
    return {"http": http, "memory_controller": memory, "memory_disabled": no_memory}


def _pack_paths(configs_root: Path, agent_id: str) -> Dict[str, Path]:
    return {
        "http": configs_root / ("agent-%s.yaml" % agent_id),
        "memory_controller": configs_root / ("agent-%s-memory.yaml" % agent_id),
        "memory_disabled": configs_root / ("agent-%s-no-memory.yaml" % agent_id),
    }


def write_agent_pack(
    configs_root: Path,
    agent_id: str,
    display_name: str,
    base_url: str,
    model: str,
    api_key_env: str = "",
    endpoint: str = DEFAULT_ENDPOINT,
    temperature: float = 0.0,
    timeout: int = 180,
    provider: str = "",
    description: str = "",
) -> List[Path]:
    """Write the three-config pack. Rejects if any target already exists."""
    agent_id = slugify(agent_id)
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", agent_id):
        raise ValueError("invalid agent id: %s" % agent_id)
    env_name = resolve_api_key_env(agent_id, api_key_env)
    pack = build_pack_configs(
        agent_id=agent_id,
        display_name=display_name,
        base_url=base_url,
        model=model,
        api_key_env=env_name,
        endpoint=endpoint,
        temperature=temperature,
        timeout=timeout,
        provider=provider,
        description=description,
    )
    paths = _pack_paths(configs_root, agent_id)
    for path in paths.values():
        if path.exists() or path.is_symlink():
            raise FileExistsError("agent config already exists: %s" % path.name)
    configs_root.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    try:
        for key in ("http", "memory_controller", "memory_disabled"):
            path = paths[key]
            text = yaml.safe_dump(pack[key], allow_unicode=True, sort_keys=False, default_flow_style=False)
            path.write_text(text, encoding="utf-8")
            written.append(path)
    except Exception:
        for path in written:
            try:
                path.unlink()
            except OSError:
                pass
        raise
    return [paths["http"], paths["memory_controller"], paths["memory_disabled"]]


def next_steps_text(agent_id: str, api_key_env: str) -> str:
    return "\n".join([
        "Next steps (key never stored in YAML):",
        "  export %s='...'   # or $env:%s = '...' on PowerShell" % (api_key_env, api_key_env),
        "  python3 -m kmb.cli run --agent configs/agent-%s-memory.yaml --suite suites/core-zh.yaml --out runs/%s-smoke --seed 42 --retries 0 --timeout 180" % (agent_id, agent_id),
        "  # compare two wrapped agents:",
        "  python3 -m kmb.cli compare --agents configs/agent-%s-memory.yaml configs/agent-<other>-memory.yaml --suite suites/core-zh.yaml --out runs/%s-vs-other --seed 42 --retries 1 --timeout 180" % (agent_id, agent_id),
        "  # optional on/off contrast (controller vs no-memory):",
        "  python3 -m kmb.cli compare --agents configs/agent-%s-memory.yaml configs/agent-%s-no-memory.yaml --suite suites/core-zh.yaml --out runs/%s-wrapper-vs-off --seed 42 --retries 1 --timeout 180" % (agent_id, agent_id, agent_id),
    ])


def register_from_args(
    *,
    name: str,
    base_url: str,
    model: str,
    api_key_env: str = "",
    endpoint: str = DEFAULT_ENDPOINT,
    temperature: float = 0.0,
    timeout: int = 180,
    agent_id: str = "",
    configs_root: Optional[Path] = None,
    provider: str = "",
    description: str = "",
    print_fn=None,
) -> List[Path]:
    emit = print_fn or print
    root = Path(configs_root) if configs_root else Path("configs")
    resolved_id = slugify(agent_id or name)
    env_name = resolve_api_key_env(resolved_id, api_key_env)
    paths = write_agent_pack(
        configs_root=root,
        agent_id=resolved_id,
        display_name=name,
        base_url=base_url,
        model=model,
        api_key_env=env_name,
        endpoint=endpoint,
        temperature=temperature,
        timeout=timeout,
        provider=provider,
        description=description,
    )
    for path in paths:
        try:
            emit("wrote %s" % path.relative_to(Path.cwd()))
        except ValueError:
            emit("wrote %s" % path)
    emit("")
    emit(next_steps_text(resolved_id, env_name))
    return paths
