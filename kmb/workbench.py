"""Small, local-only web workbench for KylinMemoryBench.

The workbench is intentionally a thin adapter over the existing CLI data model.
It never accepts an API key from a browser and only reads or writes paths inside
the project workspace.  The browser is therefore a view and a controlled job
launcher, not a second benchmark implementation.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import mimetypes
import os
import platform
import re
import stat
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

import yaml

from . import __version__
from .agent_registry import discover_agents, host_home, profiles_to_dicts
from .agents import build_agent_from_config, load_agent_config, resolve_api_profile
from .report import radar_svg, write_compare, write_html_report, write_markdown
from .runner import load_suite, run_suite, validate_cases


CAPABILITY_LABELS = {
    "retention": "长期保持",
    "memory_recall": "记忆调用",
    "dynamic_update": "动态更新",
    "similar_distinction": "相近区分",
    "boundary": "边界识别",
    "task_reuse": "任务复用",
}

SAFE_ARTIFACT_SUFFIXES = {
    ".json", ".jsonl", ".md", ".html", ".svg", ".log", ".txt", ".yaml", ".yml",
}
SENSITIVE_ENV_NAMES = re.compile(r"(API[_-]?KEY|TOKEN|SECRET|PASSWORD|PASSWD|AUTH)", re.I)
ENV_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,62}$")
PROFILE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
BEARER_PATTERN = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+")
CREDENTIAL_NAMES = {
    "GROK_API_KEY", "DEEPSEEK_API_KEY",
    "GROK_BASE_URL", "GROK_MODEL",
    "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _evaluation_parameters(payload: Dict[str, Any]) -> Dict[str, Any]:
    seed = payload.get("seed", 42)
    seed = None if seed in (None, "") else int(seed)
    retries = int(payload.get("retries", 1))
    timeout = float(payload.get("timeout", 180))
    scorer_version = str(payload.get("scorer_version", "deterministic-v2"))
    if retries < 0 or retries > 5:
        raise ValueError("重试次数必须在 0 到 5 之间")
    if not math.isfinite(timeout) or timeout < 1 or timeout > 900:
        raise ValueError("超时时间必须在 1 到 900 秒之间")
    if not re.fullmatch(r"[A-Za-z0-9._+:-]{1,64}", scorer_version):
        raise ValueError("评分器版本格式无效")
    return {"seed": seed, "retries": retries, "timeout": timeout, "scorer_version": scorer_version}


def _fix_hint(profile: Any) -> str:
    """Return the action a user must take before this Agent becomes runnable."""
    evidence_mode = str(getattr(profile, "evidence_mode", "") or "")
    if getattr(profile, "runnable", False):
        return ""
    if evidence_mode == "gui_observed" or (getattr(profile, "id", "") == "kylinagent" and getattr(profile, "installed", False)):
        return "修复条件：提供结构化 GUI/服务记忆事件导出；GUI 或服务运行状态本身不构成记忆证据"
    if evidence_mode == "conversation_only":
        return "修复条件：完成该 Agent 初始化以生成结构化记忆存储"
    return "修复条件：在已安装该 Agent 的环境中运行，并确保记忆存储路径与可执行命令同时存在"


def _is_credential_name(name: str) -> bool:
    return bool(ENV_NAME_PATTERN.fullmatch(name)) and bool(re.search(r"(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|PASSWD|AUTH|KEY)$", name, re.I))


def _credentials_path() -> Path:
    configured = os.environ.get("KMB_CREDENTIALS_FILE")
    return Path(configured).expanduser() if configured else Path.home() / ".config" / "kmb" / "credentials.env"


def _credential_file_status() -> Dict[str, Any]:
    """Return safe credential-file metadata without reading or exposing values."""
    path = _credentials_path()
    display_path = "~/.config/kmb/credentials.env" if not os.environ.get("KMB_CREDENTIALS_FILE") else "configured credential file"
    if not path.is_file():
        return {"status": "absent", "path": display_path, "loaded_names": []}
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError as exc:
        return {"status": "unreadable", "path": display_path, "loaded_names": [], "error": type(exc).__name__}
    if os.name == "posix" and mode & 0o077:
        # POSIX: enforce the 0600 rule. Windows/NTFS uses ACLs instead of these
        # bits (stat always reports broad modes), so the strict check would
        # reject every file and make credentials unusable on Windows hosts.
        return {"status": "insecure", "path": display_path, "mode": format(mode, "04o"), "loaded_names": []}
    return {"status": "secure", "path": display_path, "mode": format(mode, "04o"), "loaded_names": []}


def _configured_credential_names(root: Optional[Path] = None) -> set[str]:
    """Return fixed credentials plus API key names referenced by workspace configs."""
    names = set(CREDENTIAL_NAMES)
    config_root = (root or Path.cwd()) / "configs"
    if not config_root.is_dir():
        return names
    for path in config_root.rglob("*.y*ml"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, ValueError, yaml.YAMLError):
            continue
        if not isinstance(raw, dict):
            continue
        env_name = str(raw.get("api_key_env", "")).strip()
        if _is_credential_name(env_name):
            names.add(env_name)
        if path.name == "api-profiles.yaml":
            # 全局 API 档案池：收集 profiles[].api_key_env（单一事实来源）
            for profile in (raw.get("profiles") or []):
                if isinstance(profile, dict):
                    pool_env = str(profile.get("api_key_env", "")).strip()
                    if _is_credential_name(pool_env):
                        names.add(pool_env)
    return names


def load_credentials_file(root: Optional[Path] = None) -> Dict[str, Any]:
    """Load fixed and workspace-referenced provider variables from credentials.env.

    Existing process variables take precedence. Values are never returned or logged.
    """
    status = _credential_file_status()
    if status.get("status") != "secure":
        return status
    path = _credentials_path()
    loaded = []
    allowed_names = _configured_credential_names(Path(root).resolve() if root else None)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {"status": "unreadable", "path": status.get("path"), "loaded_names": [], "error": type(exc).__name__}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name not in allowed_names:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if not value or name in os.environ:
            continue
        os.environ[name] = value
        loaded.append(name)
    return {"status": "secure", "path": status.get("path"), "mode": status.get("mode"), "loaded_names": sorted(loaded)}


def _provider_for_config(config: Dict[str, Any]) -> str:
    explicit = str(config.get("provider", "")).strip()
    if explicit:
        return explicit
    haystack = " ".join(str(config.get(key, "")) for key in ("name", "base_url", "model", "description")).lower()
    if "deepseek" in haystack:
        return "DeepSeek"
    if "grok" in haystack or "wapq.cn" in haystack or "x.ai" in haystack:
        return "Grok"
    return "其他"


def _profile_mode(config: Dict[str, Any]) -> str:
    agent_type = str(config.get("type", "")).lower()
    return {
        "memory_controller": "记忆开启",
        "memory_disabled": "无记忆基线",
        "http": "标准 API",
        "openai": "标准 API",
        "openai_compatible": "标准 API",
        "deterministic": "本地基线",
        "replay": "证据回放",
        "command": "命令适配器",
    }.get(agent_type, agent_type or "未分类")


def _redact_text(value: Any) -> Any:
    """Redact credentials from errors and arbitrary provider payloads."""
    if isinstance(value, str):
        text = BEARER_PATTERN.sub(r"\1[REDACTED]", value)
        for name, secret in os.environ.items():
            if SENSITIVE_ENV_NAMES.search(name) and secret and len(secret) >= 6:
                text = text.replace(secret, "[REDACTED]")
        return text
    if isinstance(value, list):
        return [_redact_text(item) for item in value]
    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            if SENSITIVE_ENV_NAMES.search(str(key)):
                output[str(key)] = "[REDACTED]"
            else:
                output[str(key)] = _redact_text(item)
        return output
    return value


def _safe_component(value: str, fallback: str = "item") -> str:
    component = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._")
    return component[:96] or fallback


def _relative(path: Path, root: Path) -> Optional[str]:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _resolve_workspace_path(root: Path, raw: Any, allowed: Iterable[Path]) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("path is required")
    candidate = Path(raw).expanduser()
    if ".." in candidate.parts:
        raise ValueError("path traversal is not allowed")
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if not any(_under(candidate, base) for base in allowed):
        raise ValueError("path is outside the workbench allowlist")
    return candidate


def _safe_endpoint(base_url: Any, endpoint: Any) -> str:
    base = str(base_url or "").rstrip("/")
    suffix = str(endpoint or "/chat/completions")
    if suffix.startswith("http://") or suffix.startswith("https://"):
        parsed = urlparse(suffix)
        return "%s://%s%s" % (parsed.scheme, parsed.netloc, parsed.path or "/")
    parsed = urlparse(base + "/" + suffix.lstrip("/"))
    if parsed.scheme and parsed.netloc:
        return "%s://%s%s" % (parsed.scheme, parsed.netloc, parsed.path or "/")
    return base + "/" + suffix.lstrip("/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path, max_bytes: int = 12 * 1024 * 1024) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    if path.stat().st_size > max_bytes:
        raise ValueError("result file is too large to load in the workbench")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("result JSON must be an object")
    return raw


def _result_status(result: Dict[str, Any]) -> str:
    statuses = {str(item.get("status", "")) for item in result.get("results", []) if isinstance(item, dict)}
    if str(result.get("status", "")) in {"error", "failed"} or "error" in statuses:
        return "failed"
    if statuses and statuses - {"pass"}:
        return "partial"
    if result.get("overall") is not None:
        return "completed"
    return "unknown"


def _mode_for_result(result: Dict[str, Any]) -> str:
    observability = result.get("observability") or {}
    mode = str(observability.get("mode") or "memory_state_unobservable")
    if mode == "simulated_baseline":
        return "simulated"
    if mode == "no_memory_baseline":
        return "no_memory"
    if mode == "system_level_wrapper_assisted":
        return "wrapper_assisted"
    return mode


def _evidence_path(result: Dict[str, Any], result_path: Path, root: Path) -> Optional[Path]:
    value = result.get("evidence")
    if isinstance(value, str) and value:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = candidate.resolve()
        if _under(candidate, root / "runs") and candidate.is_file():
            return candidate
    fallback = result_path.parent / "evidence.jsonl"
    return fallback if fallback.is_file() else None


def _evidence_metrics(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.is_file():
        return {"events": 0, "model_responses": 0, "latency_ms": {"count": 0}}
    count = 0
    model_responses = 0
    latencies: List[float] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                count += 1
                raw = json.loads(line)
                if raw.get("kind") == "model_response":
                    model_responses += 1
                    value = (raw.get("data") or {}).get("elapsed_ms")
                    if isinstance(value, (int, float)):
                        latencies.append(float(value))
    except (OSError, ValueError, json.JSONDecodeError):
        return {"events": count, "model_responses": model_responses, "latency_ms": {"count": len(latencies)}}
    latency = {"count": len(latencies)}
    if latencies:
        latency.update({
            "mean": round(sum(latencies) / len(latencies), 1),
            "min": round(min(latencies), 1),
            "max": round(max(latencies), 1),
        })
    return {"events": count, "model_responses": model_responses, "latency_ms": latency}


def _track_for_config(config: Dict[str, Any]) -> str:
    """UI classification only: A=ecosystem agents, B=memory-layer agents, control=offline baselines.

    Track labels never change evidence semantics.
    """
    agent_type = str(config.get("type", ""))
    if agent_type == "memory_tool":
        return "B"
    if agent_type in {"deterministic", "replay", "memory_disabled", "http"}:
        return "control"
    return "A"


def _friendly_run_title(relative: str, agents: List[str], kind: str) -> str:
    """Readable title for nested runs: <acceptance dir> · <batch/step> · <agents>.
    Keeps the flagship real-batch evidence discoverable in the workbench instead
    of burying it under generic directory names (quick-compare / repeat-01).
    """
    parts = [part for part in str(relative).replace("\\", "/").split("/") if part]
    if not parts or parts[0] != "runs" or len(parts) < 2:
        return ""
    noise = {"official-repeat", "quick-compare", "agents", "result.json", "smoke-compare"}
    noise.update(str(a).strip().lower() for a in agents if a)
    head = parts[1]
    tail = [seg for seg in parts[2:] if seg.lower() not in noise]
    agent_label = " + ".join(a for a in agents if a)
    pieces = [head]
    if tail:
        pieces.append(" / ".join(tail[:2]))
    if agent_label:
        pieces.append(agent_label)
    return " · ".join(pieces)


class WorkbenchState:
    def __init__(self, root: Optional[str] = None):
        self.root = Path(root or Path.cwd()).resolve()
        self.config_root = self.root / "configs"
        self.suite_root = self.root / "suites"
        self.runs_root = self.root / "runs"
        self.web_root = Path(__file__).resolve().parent / "web"
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="kmb-workbench")
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.cancel_events: Dict[str, threading.Event] = {}
        self.lock = threading.RLock()

    def close(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)

    def config_path(self, raw: Any) -> Path:
        return _resolve_workspace_path(self.root, raw, (self.config_root,))

    def list_agents(self) -> List[Dict[str, Any]]:
        """Discover host installation and evaluation readiness independently.

        This reads path metadata and existing result summaries only. It does not
        read credentials, start Agents, or probe a model provider.
        """
        profiles = discover_agents(self.root)
        host = {profile.id: profile for profile in discover_agents(self.root, home=host_home())}
        payload = profiles_to_dicts(profiles)
        runs = self.list_runs()
        configured_home = os.environ.get("KMB_AGENT_HOME")
        isolated = bool(configured_home and Path(configured_home).expanduser().resolve() != host_home().resolve())
        detected_at = _utc_now()
        for profile, item in zip(profiles, payload):
            installed_on_host = bool(host.get(profile.id) and host[profile.id].installed)
            item["host_installed"] = installed_on_host
            item["host_detection_sources"] = list(host[profile.id].detection_sources) if installed_on_host else []
            item["host_executable_path"] = host[profile.id].executable_path
            item["discovery_host"] = platform.node()
            item["detected_at"] = detected_at
            item["installed"] = profile.installed or installed_on_host
            item["workspace_ready"] = profile.runnable
            item["execution_scope"] = "isolated" if isolated else "user"
            item["credential"] = "agent_managed" if item["installed"] else "not_detected"
            item["credential_source"] = "agent_configuration"
            item["connection_checked"] = False
            item["readiness"] = "ready" if profile.runnable else ("manual" if item["installed"] and profile.id == "kylinagent" else "blocked")
            item["fix_hint"] = _fix_hint(profile)
            if installed_on_host and not profile.runnable and profile.id != "kylinagent":
                item["reason"] = "本机已安装，但当前评测目录尚未准备该智能体的记忆存储或运行入口"
                item["fix_hint"] = "为当前评测目录准备独立配置和记忆副本，然后刷新；本机安装无需重复执行"
            recent = next((run for run in runs if run.get("kind") == "single" and run.get("agent") == profile.id), None)
            item["last_run"] = None
            if recent:
                categories = recent.get("failure_categories") or {}
                error = next((category for category in ("billing_error", "credential_error", "timeout", "runtime_error", "missing_input", "not_observable") if categories.get(category)), None) if recent.get("score_valid") is False else None
                item["last_run"] = {
                    "id": recent.get("id"), "path": recent.get("path"),
                    "status": recent.get("status"), "score_valid": recent.get("score_valid"),
                    "overall": recent.get("overall"), "runtime_error": error,
                }
        return payload

    def _validate_api_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a non-secret API profile payload (shared by create/update)."""
        if not isinstance(payload, dict):
            raise ValueError("配置请求必须是对象")
        forbidden = {
            key for key in payload
            if key.lower() in {"api_key", "secret", "token", "password", "authorization", "headers"}
            or (key.lower() != "api_key_env" and SENSITIVE_ENV_NAMES.search(key))
        }
        if forbidden:
            raise ValueError("不得通过网页提交 API Key、密钥或请求头；请只提交 api_key_env")
        profile_id = str(payload.get("profile_id") or payload.get("name") or "").strip()
        profile_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", profile_id).strip(".-")
        if not PROFILE_ID_PATTERN.fullmatch(profile_id):
            raise ValueError("配置标识只能包含字母、数字、点、下划线和连字符")
        name = str(payload.get("name") or "").strip()
        if not name or len(name) > 120:
            raise ValueError("配置名称不能为空且最多 120 个字符")
        provider = str(payload.get("provider") or "").strip()
        if len(provider) > 120 or "\n" in provider or "\r" in provider:
            raise ValueError("提供商名称最多 120 个字符且不能包含换行")
        base_url = str(payload.get("base_url") or "").strip().rstrip("/")
        parsed_base = urlparse(base_url)
        if parsed_base.scheme not in {"http", "https"} or not parsed_base.netloc:
            raise ValueError("base_url 必须是 http 或 https 地址")
        if parsed_base.username or parsed_base.password or parsed_base.fragment:
            raise ValueError("base_url 不得包含用户名、密码或 fragment")
        endpoint = str(payload.get("endpoint") or "/chat/completions").strip()
        if not endpoint.startswith("/") or endpoint.startswith("//") or "\n" in endpoint or "\r" in endpoint:
            raise ValueError("endpoint 必须是以 / 开头的相对路径")
        if len(endpoint) > 200:
            raise ValueError("endpoint 过长")
        model = str(payload.get("model") or "").strip()
        if not model or len(model) > 160 or "\n" in model or "\r" in model:
            raise ValueError("模型 ID 不能为空且不能包含换行")
        api_key_env = str(payload.get("api_key_env") or "").strip()
        if not _is_credential_name(api_key_env):
            raise ValueError("api_key_env 必须是类似 PROVIDER_API_KEY 的安全环境变量名")
        try:
            timeout_seconds = float(payload.get("timeout_seconds", 60))
        except (TypeError, ValueError):
            raise ValueError("timeout_seconds 必须是数字")
        if timeout_seconds <= 0 or timeout_seconds > 900:
            raise ValueError("timeout_seconds 必须在 1 到 900 秒之间")
        try:
            temperature = float(payload.get("temperature", 0))
        except (TypeError, ValueError):
            raise ValueError("temperature 必须是数字")
        if temperature < 0 or temperature > 2:
            raise ValueError("temperature 必须在 0 到 2 之间")
        description = str(payload.get("description") or "").strip()
        if len(description) > 500:
            raise ValueError("description 最多 500 个字符")
        timeout_value = int(timeout_seconds) if float(timeout_seconds).is_integer() else timeout_seconds
        temperature_value = int(temperature) if float(temperature).is_integer() else temperature
        return {
            "profile_id": profile_id, "name": name, "provider": provider,
            "base_url": base_url, "endpoint": endpoint, "model": model,
            "api_key_env": api_key_env, "timeout_seconds": timeout_value,
            "temperature": temperature_value, "description": description,
        }

    def _api_profiles_path(self) -> Path:
        return self.config_root / "api-profiles.yaml"

    def _read_api_profiles(self) -> List[Dict[str, Any]]:
        path = self._api_profiles_path()
        if not path.is_file():
            return []
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return [item for item in (data.get("profiles") or []) if isinstance(item, dict) and item.get("id")]

    def _write_api_profiles(self, profiles: List[Dict[str, Any]]) -> None:
        self.config_root.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "profiles": profiles}
        serialized = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
        fd, temporary = tempfile.mkstemp(prefix=".api-profiles-", suffix=".yaml.tmp", dir=str(self.config_root))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._api_profiles_path())
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

    def list_api_profiles(self) -> List[Dict[str, Any]]:
        output = []
        for profile in self._read_api_profiles():
            env_name = str(profile.get("api_key_env", ""))
            output.append({
                "id": str(profile.get("id")),
                "name": str(profile.get("display_name") or profile.get("id")),
                "provider": str(profile.get("provider") or ""),
                "base_url": str(profile.get("base_url") or ""),
                "endpoint": str(profile.get("endpoint") or "/chat/completions"),
                "model": str(profile.get("model") or ""),
                "api_key_env": env_name,
                "timeout_seconds": profile.get("timeout_seconds"),
                "temperature": profile.get("temperature"),
                "description": str(profile.get("description") or ""),
                "credential": "configured" if env_name and os.environ.get(env_name) else "not_detected",
            })
        return output

    def create_api_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create one global API profile; never creates or rewrites agent files."""
        fields = self._validate_api_payload(payload)
        profiles = self._read_api_profiles()
        if any(item["id"] == fields["profile_id"] for item in profiles):
            raise FileExistsError("API 档案已存在：%s" % fields["profile_id"])
        profiles.append({
            "id": fields["profile_id"],
            "provider": fields["provider"],
            "display_name": fields["name"],
            "base_url": fields["base_url"],
            "endpoint": fields["endpoint"],
            "model": fields["model"],
            "api_key_env": fields["api_key_env"],
            "timeout_seconds": fields["timeout_seconds"],
            "temperature": fields["temperature"],
            "description": fields["description"],
        })
        self._write_api_profiles(profiles)
        return {"status": "created", "id": fields["profile_id"], "profile_count": len(profiles)}

    def update_api_profile(self, profile_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        fields = self._validate_api_payload(payload)
        profiles = self._read_api_profiles()
        target = None
        for item in profiles:
            if item["id"] == profile_id:
                target = item
                break
        if target is None:
            raise FileNotFoundError("API 档案不存在：%s" % profile_id)
        target.update({
            "provider": fields["provider"], "display_name": fields["name"],
            "base_url": fields["base_url"], "endpoint": fields["endpoint"],
            "model": fields["model"], "api_key_env": fields["api_key_env"],
            "timeout_seconds": fields["timeout_seconds"], "temperature": fields["temperature"],
            "description": fields["description"],
        })
        self._write_api_profiles(profiles)
        return {"status": "updated", "id": profile_id}

    def suite_path(self, raw: Any) -> Path:
        return _resolve_workspace_path(self.root, raw, (self.suite_root,))

    def artifact_path(self, raw: Any) -> Path:
        return _resolve_workspace_path(self.root, raw, (self.runs_root, self.config_root, self.suite_root, self.root / "docs"))

    def list_configs(self) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []
        load_credentials_file(self.root)
        if not self.config_root.is_dir():
            return output
        for path in sorted(self.config_root.rglob("*.y*ml")):
            if not path.is_file() or path.is_symlink():
                continue
            if path.name == "api-profiles.yaml":
                continue  # 全局 API 档案池不是智能体配置
            relative = _relative(path, self.root)
            try:
                config = load_agent_config(str(path))
                agent_type = str(config.get("type", ""))
                model = str(config.get("model", ""))
                env_name = str(config.get("api_key_env", ""))
                backend = config.get("backend") if isinstance(config.get("backend"), dict) else {}
                if backend.get("api_key_env"):
                    env_name = str(backend["api_key_env"])
                requires_api = agent_type in {"http", "openai", "openai_compatible", "memory_controller", "memory_disabled"} or (agent_type == "memory_tool" and bool(backend))
                configured = bool(env_name and os.environ.get(env_name))
                if requires_api or (env_name and agent_type in {"command", "external"}):
                    credential = "configured" if configured else "not_detected"
                    credential_source = "workbench_environment"
                elif agent_type == "command" or (agent_type == "external" and config.get("command")):
                    credential = "agent_managed"
                    credential_source = "agent_configuration"
                else:
                    credential = "not_required"
                    credential_source = "none"
                output.append({
                    "path": relative,
                    "name": str(config.get("name", path.stem)),
                    "type": agent_type,
                    "provider": _provider_for_config(config),
                    "profile_mode": _profile_mode(config),
                    "model": model if not model.startswith("${") else "待运行时解析",
                    "endpoint": _safe_endpoint(config.get("base_url"), config.get("endpoint")) if config.get("base_url") else "本地适配器",
                    "version": str(config.get("version", "")),
                    "description": str(config.get("description", "")),
                    "credential": credential,
                    "credential_source": credential_source,
                    "requires_api": requires_api,
                    "api_profile": str(config.get("api_profile", "")) or None,
                    "track": _track_for_config(config),
                    "source": "workspace config",
                })
            except Exception as exc:
                output.append({"path": relative, "name": path.stem, "type": "invalid", "status": "error", "error": _redact_text(str(exc))})
        return output

    def list_suites(self) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []
        if not self.suite_root.is_dir():
            return output
        for path in sorted(self.suite_root.rglob("*.y*ml")):
            if not path.is_file() or path.is_symlink():
                continue
            if path.relative_to(self.suite_root).parts[0] == "coverage":
                continue
            relative = _relative(path, self.root)
            try:
                cases = load_suite(str(path))
                validate_cases(cases)
                output.append({
                    "path": relative,
                    "name": path.stem,
                    "cases": len(cases),
                    "capabilities": sorted({case.capability for case in cases}),
                    "capability_labels": [CAPABILITY_LABELS.get(case.capability, case.capability) for case in cases],
                    "sha256": _sha256(path),
                    "status": "valid",
                })
            except Exception as exc:
                output.append({"path": relative, "name": path.stem, "status": "invalid", "error": _redact_text(str(exc))})
        return output

    def _single_entry(self, result_path: Path) -> Optional[Dict[str, Any]]:
        try:
            result = _read_json(result_path)
        except Exception:
            return None
        relative = _relative(result_path.parent, self.root)
        if not relative:
            return None
        evidence = _evidence_path(result, result_path, self.root)
        metadata = result.get("agent_metadata") or {}
        return {
            "id": str(result.get("run_id") or result_path.parent.name),
            "run_id": str(result.get("run_id") or result_path.parent.name),
            "path": relative,
            "result_path": _relative(result_path, self.root),
            "evidence_path": _relative(evidence, self.root) if evidence else None,
            "kind": "single",
            "status": _result_status(result),
            "started_at": result.get("started_at"),
            "agents": [str(result.get("agent", ""))],
            "agent": str(result.get("agent", "")),
            "overall": result.get("overall") if result.get("score_valid", True) is not False else None,
            "score_valid": result.get("score_valid", True),
            "score_status": result.get("score_status", "valid"),
            "dimensions": result.get("dimensions") or {},
            "cases": result.get("cases", len(result.get("results", []))),
            "mode": _mode_for_result(result),
            "observability": result.get("observability") or {},
            "preflight": result.get("preflight") or {},
            "failure_counts": result.get("failure_counts") or {},
            "failure_categories": result.get("failure_categories") or {},
            "evidence_chain": result.get("evidence_chain") or {},
            "agent_metadata": {
                "adapter": metadata.get("adapter"),
                "model": ((metadata.get("model_backend") or {}).get("model") if isinstance(metadata, dict) else None) or metadata.get("model"),
            },
            "metrics": _evidence_metrics(evidence),
        }

    def list_runs(self, limit: int = 100) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        if not self.runs_root.is_dir():
            return entries
        comparison_paths = [path for path in self.runs_root.rglob("comparison.json") if path.is_file() and not path.is_symlink()]
        comparison_dirs = {path.parent.resolve() for path in comparison_paths}
        for path in comparison_paths:
            try:
                comparison = _read_json(path)
            except Exception:
                continue
            agents = comparison.get("agents") if isinstance(comparison.get("agents"), list) else []
            relative = _relative(path.parent, self.root)
            if not relative:
                continue
            statuses = []
            modes = []
            overalls = []
            score_validities = []
            for item in agents:
                if isinstance(item, dict):
                    valid = item.get("score_valid", True) is not False
                    score_validities.append(valid)
                    overalls.append(item.get("overall") if valid else None)
                    modes.append(_mode_for_result(item))
            entry_agents = [str(item.get("agent", "")) for item in agents if isinstance(item, dict)]
            entries.append({
                "id": path.parent.name,
                "run_id": path.parent.name,
                "path": relative,
                "title": _friendly_run_title(relative, entry_agents, "comparison"),
                "result_path": _relative(path, self.root),
                "kind": "comparison",
                "status": "failed" if score_validities and not all(score_validities) else "completed" if agents else "unknown",
                "started_at": max((item.get("started_at") for item in agents if isinstance(item, dict) and item.get("started_at")), default=None),
                "agents": entry_agents,
                "overall": overalls,
                "mode": "mixed" if len(set(modes)) > 1 else (modes[0] if modes else "unknown"),
                "comparison": True,
                "_mtime": path.stat().st_mtime,
            })
        for path in self.runs_root.rglob("result.json"):
            if not path.is_file() or path.is_symlink() or path.parent.resolve() in comparison_dirs:
                continue
            entry = self._single_entry(path)
            if entry:
                entry["_mtime"] = path.stat().st_mtime
                title = _friendly_run_title(_relative(path.parent, self.root), [str(entry.get("agent", ""))], "single")
                if title:
                    entry["title"] = title
                entries.append(entry)
        for entry in entries:
            parts = [seg for seg in str(entry.get("path", "")).replace("\\", "/").split("/") if seg]
            if len(parts) >= 3 and parts[0] == "runs" and parts[1] == "workbench":
                meta_path = self.runs_root / "workbench" / parts[2] / "workbench-meta.json"
                if meta_path.is_file():
                    try:
                        entry["track"] = _read_json(meta_path).get("track")
                    except Exception:
                        pass
        entries.sort(key=lambda item: (float(item.get("_mtime", 0)), str(item.get("path"))), reverse=True)
        for entry in entries:
            entry.pop("_mtime", None)
        return entries[: max(1, min(int(limit), 500))]

    def _load_summary(self, result_path: Path) -> Dict[str, Any]:
        result = _read_json(result_path)
        evidence = _evidence_path(result, result_path, self.root)
        result["_workbench"] = {
            "result_path": _relative(result_path, self.root),
            "evidence_path": _relative(evidence, self.root) if evidence else None,
            "report_paths": {
                suffix: _relative(result_path.parent / suffix, self.root)
                for suffix in ("result.md", "result.html", "radar.svg", "evidence.jsonl")
                if (result_path.parent / suffix).is_file()
            },
            "metrics": _evidence_metrics(evidence),
        }
        return _redact_text(result)

    def get_run(self, raw_path: str) -> Dict[str, Any]:
        requested = self._resolve_run_dir(raw_path)
        comparison_path = requested / "comparison.json" if requested.is_dir() else requested
        if comparison_path.name == "comparison.json" and comparison_path.is_file():
            comparison = _redact_text(_read_json(comparison_path))
            children = []
            for item in comparison.get("agents", []) if isinstance(comparison.get("agents"), list) else []:
                agent_name = str(item.get("agent", "")) if isinstance(item, dict) else ""
                candidate = requested / _safe_component(agent_name) / "result.json"
                if candidate.is_file():
                    children.append(self._load_summary(candidate))
            return {"kind": "comparison", "path": _relative(requested, self.root), "comparison": comparison, "agents": children}
        if requested.name != "result.json":
            requested = requested / "result.json"
        return {"kind": "single", "path": _relative(requested.parent, self.root), "result": self._load_summary(requested)}

    def _resolve_run_dir(self, raw_path: str) -> Path:
        path = _resolve_workspace_path(self.root, raw_path, (self.runs_root,))
        if path.is_dir():
            return path
        if path.name in {"result.json", "comparison.json"}:
            return path
        raise FileNotFoundError(str(path))

    def evidence(self, raw_path: str, case_id: Optional[str] = None, agent: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
        path = self.artifact_path(raw_path)
        if path.name == "result.json":
            result = _read_json(path)
            evidence_path = _evidence_path(result, path, self.root)
            if not evidence_path:
                return []
            path = evidence_path
        if path.suffix.lower() != ".jsonl" or not path.is_file():
            raise ValueError("evidence path is not a JSONL file")
        output = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                raw = json.loads(line)
                if case_id and str(raw.get("case_id")) != str(case_id):
                    continue
                if agent and str(raw.get("agent")) != str(agent):
                    continue
                output.append(_redact_text(raw))
                if len(output) >= max(1, min(int(limit), 2000)):
                    break
        return output

    def artifact(self, raw_path: str) -> Tuple[Path, str]:
        path = self.artifact_path(raw_path)
        if path.suffix.lower() not in SAFE_ARTIFACT_SUFFIXES:
            raise ValueError("artifact type is not viewable")
        if not path.is_file():
            raise FileNotFoundError(str(path))
        if path.stat().st_size > 12 * 1024 * 1024:
            raise ValueError("artifact is too large to display")
        content_type = mimetypes.guess_type(path.name)[0] or "text/plain"
        return path, content_type

    def system_info(self) -> Dict[str, Any]:
        load_credentials_file(self.root)
        openkylin = {"detected": False, "distribution": None, "version": None}
        os_release = Path("/etc/os-release")
        if os_release.is_file():
            values = {}
            for line in os_release.read_text(encoding="utf-8", errors="replace").splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    values[key] = value.strip().strip('"')
            ident = (values.get("ID") or "").lower()
            openkylin = {"detected": ident in {"openkylin", "openkylin-desktop"}, "distribution": values.get("PRETTY_NAME") or ident, "version": values.get("VERSION_ID")}
        try:
            cli_version = importlib.metadata.version("kylin-memory-bench")
        except importlib.metadata.PackageNotFoundError:
            cli_version = __version__
        try:
            import yaml as yaml_module
            yaml_version = getattr(yaml_module, "__version__", "unknown")
        except Exception:
            yaml_version = "unavailable"
        credentials = _credential_file_status()
        api_profiles = self.list_api_profiles()
        credentials["scope"] = "workbench_api"
        credentials["configured_profiles"] = sum(profile["credential"] == "configured" for profile in api_profiles)
        credentials["api_ready"] = credentials["configured_profiles"] > 0
        return {
            "openkylin": openkylin,
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
            "agent_discovery": {"scope": "backend_host", "hostname": platform.node(), "automatic": True, "checks": ["executable", "memory_store", "configuration_file_metadata"], "starts_agents": False},
            "python": platform.python_version(),
            "python_executable": str(Path(os.sys.executable).resolve()),
            "pyyaml": yaml_version,
            "cli_version": cli_version,
            "workspace": _relative(self.root, self.root) or ".",
            "results_directory": _relative(self.runs_root, self.root) or "runs",
            "config_directory": _relative(self.config_root, self.root) or "configs",
            "suite_directory": _relative(self.suite_root, self.root) or "suites",
            "credentials": credentials,
            "system_scenarios": {
                "agent_process_restart": {"status": "controlled_boundary_only", "note": "CLI 可重建包装层；不等同于系统重启"},
                "system_restart": {"status": "requires_openkylin_controller", "note": "需受控 VM 控制器"},
                "user_switch": {"status": "requires_dedicated_users", "note": "需专用测试账户"},
                "offline": {"status": "requires_network_namespace", "note": "只允许测试命名空间"},
                "permission_change": {"status": "sandbox_only", "note": "只允许专用测试目录"},
            },
        }

    def health(self, raw_config: str) -> Dict[str, Any]:
        path = self.config_path(raw_config)
        config = load_agent_config(str(path))
        name = str(config.get("name", path.stem))
        model = str(config.get("model", ""))
        endpoint = _safe_endpoint(config.get("base_url"), config.get("endpoint")) if config.get("base_url") else "本地适配器"
        started = time.monotonic()
        try:
            agent = build_agent_from_config(str(path))
            if str(config.get("type", "")).lower() in {"http", "openai", "openai_compatible", "memory_controller", "memory_disabled"}:
                backend = getattr(agent, "backend", agent)
                response = backend._request([{"role": "user", "content": "Reply with exactly: ok"}])
                backend._message(response)
            elapsed = round((time.monotonic() - started) * 1000, 1)
            return {"status": "healthy", "http_status": 200, "latency_ms": elapsed, "name": name, "model": model, "endpoint": endpoint, "checked_at": _utc_now()}
        except Exception as exc:
            elapsed = round((time.monotonic() - started) * 1000, 1)
            return {"status": "error", "http_status": None, "latency_ms": elapsed, "name": name, "model": model, "endpoint": endpoint, "error": _redact_text(str(exc)), "checked_at": _utc_now()}

    def start_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        source = payload.get("source", "configuration")
        if source == "installed":
            if payload.get("api_profiles"):
                raise ValueError("已安装智能体使用自身配置，不接受工作台 API 档案覆盖")
            return self.start_quick_compare(dict(payload, agents=[payload.get("primary_agent"), payload.get("comparison_agent")]))
        if source != "configuration":
            raise ValueError("source 必须是 installed 或 configuration")
        primary = self.config_path(payload.get("primary_agent"))
        comparison = self.config_path(payload.get("comparison_agent"))
        suite = self.suite_path(payload.get("suite"))
        primary_config = load_agent_config(str(primary))
        comparison_config = load_agent_config(str(comparison))
        if str(primary_config.get("name")) == str(comparison_config.get("name")):
            raise ValueError("主 Agent 与对比 Agent 必须不同")
        cases = load_suite(str(suite))
        validate_cases(cases, require_all_capabilities=False)
        parameters = _evaluation_parameters(dict(payload, seed=payload.get("seed")))
        seed, retries, timeout, scorer_version = (parameters[key] for key in ("seed", "retries", "timeout", "scorer_version"))
        track = str(payload.get("track") or "control")
        if track not in {"A", "B", "control"}:
            raise ValueError("track 必须是 A（生态智能体）/ B（记忆层）/ control（对照基线）")
        api_profiles = payload.get("api_profiles") or {}
        if not isinstance(api_profiles, dict):
            raise ValueError("api_profiles 必须是 {配置路径: API 档案 id} 映射")
        available = {item["id"] for item in self.list_api_profiles()}
        for key, profile_id in api_profiles.items():
            if profile_id not in available:
                raise ValueError("API 档案不存在：%s" % profile_id)
        job_id = "wb-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
        output = self.runs_root / "workbench" / job_id
        output.mkdir(parents=True, exist_ok=False)
        runtime_specs = {}
        for key, profile_id in api_profiles.items():
            source = self.config_path(key)
            materialized = self._materialize_api_override(source, profile_id, output)
            runtime_specs[_relative(source, self.root)] = {
                "profile_id": profile_id,
                "path": _relative(materialized, self.root),
            }
        job = {
            "id": job_id, "status": "queued", "created_at": _utc_now(), "updated_at": _utc_now(),
            "track": track,
            "progress": {"completed": 0, "total": 2, "phase": "排队中", "current_agent": None},
            "params": {"seed": seed, "retries": retries, "timeout": timeout, "scorer_version": scorer_version, "suite": _relative(suite, self.root), "suite_sha256": _sha256(suite)},
            "agents": [_relative(primary, self.root), _relative(comparison, self.root)],
            "api_profiles": runtime_specs,
            "output": _relative(output, self.root), "error": None,
        }
        (output / "workbench-meta.json").write_text(json.dumps({
            "track": track, "api_profiles": runtime_specs, "created_at": _utc_now(),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        with self.lock:
            self.jobs[job_id] = job
            self.cancel_events[job_id] = threading.Event()
        self._write_job(job)
        self.executor.submit(self._run_job, job_id, [primary, comparison], cases, output, seed, retries, timeout, scorer_version, runtime_specs)
        return self._public_job(job)

    def _materialize_api_override(self, source: Path, profile_id: str, output_dir: Path) -> Path:
        """Materialize a per-run agent config whose API is pinned to the chosen profile.

        The runtime snapshot records exactly what this evaluation used; the agent's
        own YAML (default API reference) is never rewritten.
        """
        raw = load_agent_config(str(source))
        profile = resolve_api_profile(profile_id, source)
        raw["base_url"] = str(profile.get("base_url") or "")
        raw["endpoint"] = str(profile.get("endpoint") or "/chat/completions")
        raw["model"] = str(profile.get("model") or "")
        raw["api_key_env"] = str(profile.get("api_key_env") or "")
        if profile.get("timeout_seconds") is not None:
            raw["timeout_seconds"] = profile["timeout_seconds"]
        if "temperature" in profile:
            options = dict(raw.get("request_options") or {})
            options.setdefault("temperature", profile["temperature"])
            raw["request_options"] = options
        raw.pop("api_profile", None)  # 快照固化本次评测实际使用的 API，不随池后续变化
        runtime_dir = output_dir / ".runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        target = runtime_dir / (Path(source).stem + "-" + str(profile_id) + ".yaml")
        target.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return target

    def start_quick_compare(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        from .quick_compare import QuickCompareOptions, QUICK_SUITE, _select_profiles

        raw_agents = payload.get("agents") or payload.get("agent_ids") or []
        if not isinstance(raw_agents, list):
            raise ValueError("agents 必须是 Agent id 数组")
        parameters = _evaluation_parameters(payload)
        if parameters["scorer_version"] != "deterministic-v2":
            raise ValueError("已安装智能体当前使用 deterministic-v2 评分器")
        suite = self.suite_path(payload.get("suite") or QUICK_SUITE)
        cases = load_suite(str(suite))
        suite_relative = _relative(suite, self.root)
        validate_cases(cases, require_all_capabilities=(suite_relative == QUICK_SUITE))
        profiles = discover_agents(self.root)
        try:
            selected = _select_profiles(
                QuickCompareOptions(agent_ids=[str(item) for item in raw_agents] or None),
                profiles,
            )
        except ValueError as exc:
            blockers = [profile for profile in profiles if not profile.runnable]
            detail = "；".join(
                "%s（%s；%s）" % (profile.id, profile.reason or "不可自动运行", _fix_hint(profile))
                for profile in blockers
            )
            raise ValueError("%s。阻断详情：%s" % (exc, detail or "未发现任何已安装 Agent")) from None
        job_id = "quick-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
        output = self.runs_root / "workbench" / job_id
        output.mkdir(parents=True, exist_ok=False)
        job = {
            "id": job_id, "kind": "quick_compare", "status": "queued", "created_at": _utc_now(), "updated_at": _utc_now(),
            "progress": {"completed": 0, "total": 2, "phase": "排队中", "current_agent": None},
            "params": dict(parameters, suite=suite_relative, suite_sha256=_sha256(suite)),
            "track": "A", "source": "installed",
            "agents": [profile.id for profile in selected],
            "output": _relative(output, self.root), "error": None,
        }
        (output / "workbench-meta.json").write_text(json.dumps({"track": "A", "source": "installed", "created_at": job["created_at"], "parameters": job["params"]}, ensure_ascii=False, indent=2), encoding="utf-8")
        with self.lock:
            self.jobs[job_id] = job
            self.cancel_events[job_id] = threading.Event()
        self._write_job(job)
        self.executor.submit(self._run_quick_job, job_id, [profile.id for profile in selected], output, job["params"])
        return self._public_job(job)

    def _write_job(self, job: Dict[str, Any]) -> None:
        output = self.root / str(job.get("output", ""))
        output.mkdir(parents=True, exist_ok=True)
        safe = _redact_text(job)
        (output / "workbench-job.json").write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")

    def _public_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        return _redact_text(dict(job))

    def _update_job(self, job_id: str, **updates: Any) -> None:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            job.update(updates)
            job["updated_at"] = _utc_now()
            snapshot = self._public_job(job)
        self._write_job(snapshot)

    def _run_job(self, job_id: str, config_paths: List[Path], cases: List[Any], output: Path, seed: Optional[int], retries: int, timeout: float, scorer_version: str, runtime_specs: Optional[Dict[str, Dict[str, str]]] = None) -> None:
        runtime_specs = runtime_specs or {}
        summaries = []
        cancel_event = self.cancel_events.get(job_id)
        try:
            self._update_job(job_id, status="running", progress={"completed": 0, "total": len(config_paths), "phase": "运行中", "current_agent": None})
            for index, config_path in enumerate(config_paths):
                if cancel_event and cancel_event.is_set():
                    self._update_job(job_id, status="stopped", progress=self.jobs.get(job_id, {}).get("progress", {}), error="用户请求停止评测")
                    return
                config = load_agent_config(str(config_path))
                agent_name = str(config.get("name", config_path.stem))
                agent_dir = output / _safe_component(agent_name)
                self._update_job(job_id, progress={"completed": index, "total": len(config_paths), "phase": "运行 %s" % agent_name, "current_agent": agent_name})
                spec = runtime_specs.get(_relative(config_path, self.root)) or {}
                build_path = (self.root / spec["path"]) if spec.get("path") else config_path
                agent = build_agent_from_config(str(build_path))
                summary = run_suite(agent, cases, str(agent_dir), timeout_seconds=timeout, retries=retries, run_id=job_id + "-" + _safe_component(agent_name), seed=seed)
                if cancel_event and cancel_event.is_set():
                    self._update_job(job_id, status="stopped", progress=self.jobs.get(job_id, {}).get("progress", {}), error="用户请求停止评测")
                    return
                summary["workbench"] = {
                    "scorer_version": scorer_version, "config": _relative(config_path, self.root),
                    "suite": self.jobs.get(job_id, {}).get("params", {}).get("suite"),
                    "track": self.jobs.get(job_id, {}).get("track"),
                    "api_profile": (spec or {}).get("profile_id"),
                }
                write_markdown(summary, str(agent_dir / "result.md"))
                (agent_dir / "radar.svg").write_text(radar_svg(summary.get("dimensions", {}), score_valid=summary.get("score_valid", True)), encoding="utf-8")
                write_html_report([summary], str(agent_dir / "result.html"))
                (agent_dir / "result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
                summaries.append(summary)
                self._update_job(job_id, progress={"completed": index + 1, "total": len(config_paths), "phase": "已完成 %s" % agent_name, "current_agent": agent_name})
            comparison = write_compare(summaries, str(output))
            metadata = {
                "job_id": job_id, "created_at": _utc_now(), "scorer_version": scorer_version,
                "suite": self.jobs.get(job_id, {}).get("params", {}).get("suite"),
                "agents": [_relative(path, self.root) for path in config_paths], "result_directory": _relative(output, self.root),
                "disclaimer": "结果评估模型后端 + 统一包装层的系统级长期记忆行为；原生记忆状态不可由普通 API 响应证明。",
            }
            (output / "workbench-run.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            self._update_job(job_id, status="completed", progress={"completed": len(config_paths), "total": len(config_paths), "phase": "已完成", "current_agent": None}, result_path=_relative(output, self.root), comparison=comparison)
        except Exception as exc:
            message = _redact_text("%s: %s" % (type(exc).__name__, exc))
            (output / "workbench-error.log").write_text(str(message) + "\n", encoding="utf-8")
            self._update_job(job_id, status="error", progress=self.jobs.get(job_id, {}).get("progress", {}), error=message, result_path=_relative(output, self.root))

    def _run_quick_job(self, job_id: str, agent_ids: List[str], output: Path, parameters: Optional[Dict[str, Any]] = None) -> None:
        from .quick_compare import QuickCompareOptions, run_quick_compare

        try:
            self._update_job(job_id, status="running", progress={"completed": 0, "total": 2, "phase": "准备快速对比", "current_agent": None})
            parameters = parameters or {}
            result = run_quick_compare(
                QuickCompareOptions(agent_ids=agent_ids, out_dir=str(output), suite=parameters.get("suite", "suites/quick.yaml"), seed=parameters.get("seed", 42), retries=parameters.get("retries", 1), timeout=parameters.get("timeout", 180)),
                root=self.root,
            )
            self._update_job(
                job_id,
                status="completed",
                progress={"completed": 2, "total": 2, "phase": "已完成", "current_agent": None},
                result_path=_relative(output, self.root),
                comparison=result.get("comparison"),
            )
        except Exception as exc:
            message = _redact_text("%s: %s" % (type(exc).__name__, exc))
            (output / "workbench-error.log").write_text(str(message) + "\n", encoding="utf-8")
            self._update_job(job_id, status="error", progress=self.jobs.get(job_id, {}).get("progress", {}), error=message, result_path=_relative(output, self.root))

    def stop_job(self, job_id: str) -> Dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                path = self.runs_root / "workbench" / _safe_component(job_id) / "workbench-job.json"
                if path.is_file():
                    return _redact_text(_read_json(path))
                raise FileNotFoundError(job_id)
            if job.get("status") in {"completed", "error", "failed", "stopped"}:
                return self._public_job(job)
            event = self.cancel_events.get(job_id)
            if event:
                event.set()
            job["status"] = "stopping"
            job["error"] = "停止请求已接收"
            job["updated_at"] = _utc_now()
            snapshot = self._public_job(job)
        self._write_job(snapshot)
        return snapshot

    def get_job(self, job_id: str) -> Dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
        if job:
            return self._public_job(job)
        path = self.runs_root / "workbench" / _safe_component(job_id) / "workbench-job.json"
        if path.is_file():
            return _redact_text(_read_json(path))
        raise FileNotFoundError(job_id)


class WorkbenchHandler(BaseHTTPRequestHandler):
    server_version = "KMBWorkbench/1.0"

    @property
    def state(self) -> WorkbenchState:
        return self.server.workbench_state  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:
        # Keep request logs concise and never include request bodies or headers.
        return

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(_redact_text(payload), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str) -> None:
        self._send_json({"error": _redact_text(message)}, status)

    def _body_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0 or length > 128 * 1024:
            raise ValueError("request body is empty or too large")
        raw = self.rfile.read(length)
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)
        try:
            if path == "/api/profiles":
                self._send_json({"profiles": self.state.list_api_profiles()})
            elif path == "/api/configs":
                self._send_json({"configs": self.state.list_configs()})
            elif path == "/api/agents":
                self._send_json({"agents": self.state.list_agents()})
            elif path == "/api/suites":
                self._send_json({"suites": self.state.list_suites()})
            elif path == "/api/runs":
                requested = query.get("path", [None])[0]
                if requested:
                    self._send_json(self.state.get_run(requested))
                else:
                    self._send_json({"runs": self.state.list_runs(int(query.get("limit", [100])[0]))})
            elif path.startswith("/api/runs/"):
                requested = path[len("/api/runs/"):]
                self._send_json(self.state.get_run(requested))
            elif path == "/api/evidence":
                events = self.state.evidence(query.get("path", [""])[0], query.get("case", [None])[0], query.get("agent", [None])[0], int(query.get("limit", [500])[0]))
                self._send_json({"events": events})
            elif path == "/api/artifact":
                artifact, content_type = self.state.artifact(query.get("path", [""])[0])
                body = artifact.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") or content_type.endswith("svg+xml") else ""))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif path == "/api/system":
                self._send_json(self.state.system_info())
            elif path == "/api/jobs/" or path == "/api/jobs":
                self._error(400, "job id is required")
            elif path.startswith("/api/jobs/"):
                self._send_json(self.state.get_job(path[len("/api/jobs/"):]))
            else:
                self._static(path)
        except FileExistsError as exc:
            self._error(409, str(exc))
        except FileNotFoundError as exc:
            self._error(404, "not found: %s" % exc)
        except (ValueError, KeyError, TypeError) as exc:
            self._error(400, str(exc))
        except Exception as exc:
            self._error(500, str(exc))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self._body_json()
            if parsed.path == "/api/profiles":
                self._send_json(self.state.create_api_profile(payload), HTTPStatus.CREATED)
            elif parsed.path.startswith("/api/profiles/") and parsed.path.endswith("/update"):
                profile_id = parsed.path[len("/api/profiles/"):-len("/update")].strip("/")
                self._send_json(self.state.update_api_profile(profile_id, payload))
            elif parsed.path == "/api/health":
                self._send_json(self.state.health(str(payload.get("config", ""))))
            elif parsed.path == "/api/runs":
                self._send_json(self.state.start_run(payload), HTTPStatus.ACCEPTED)
            elif parsed.path == "/api/quick-compare":
                self._send_json(self.state.start_quick_compare(payload), HTTPStatus.ACCEPTED)
            elif parsed.path.startswith("/api/jobs/") and parsed.path.endswith("/stop"):
                job_id = parsed.path[len("/api/jobs/"):-len("/stop")].strip("/")
                if not job_id:
                    self._error(400, "job id is required")
                else:
                    self._send_json(self.state.stop_job(job_id))
            else:
                self._error(404, "unknown POST endpoint")
        except FileExistsError as exc:
            self._error(409, str(exc))
        except FileNotFoundError as exc:
            self._error(404, "not found: %s" % exc)
        except (ValueError, KeyError, TypeError) as exc:
            self._error(400, str(exc))
        except Exception as exc:
            self._error(500, str(exc))

    def _static(self, path: str) -> None:
        relative = "index.html" if path in {"/", ""} else path.lstrip("/")
        candidate = (self.state.web_root / relative).resolve()
        if not _under(candidate, self.state.web_root) or not candidate.is_file():
            self._error(404, "static file not found")
            return
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") or candidate.suffix in {".js", ".css", ".html"} else ""))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(root: Optional[str] = None, host: str = "127.0.0.1", port: int = 8765) -> None:
    state = WorkbenchState(root)
    load_credentials_file(state.root)
    server = ThreadingHTTPServer((host, int(port)), WorkbenchHandler)
    server.workbench_state = state  # type: ignore[attr-defined]
    print("KylinMemoryBench workbench listening on http://%s:%d" % (host, int(port)), flush=True)
    try:
        server.serve_forever()
    finally:
        state.close()
        server.server_close()
