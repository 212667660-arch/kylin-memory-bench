"""Read default native Agent API metadata without exporting or decrypting secrets.

Only known files beneath the selected HOME are inspected. No native command,
credential helper, external secret reference, or network request is executed.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from urllib.parse import quote, urlsplit, urlunsplit

import yaml

try:
    import tomllib
except ImportError:  # Python 3.9/3.10
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

MAX_CONFIG_BYTES = 256 * 1024
INSPECTION_REVISION = 2
ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
ENV_REFERENCE = re.compile(r"^(?:\$\{([A-Za-z_][A-Za-z0-9_]*)\}|env:([A-Za-z_][A-Za-z0-9_]*))$")
PLACEHOLDER = re.compile(r"(?i)redacted|your[-_ ]?(?:api[-_ ]?)?key|replace[-_ ]?me|changeme|^\*+$")
SECRET_TEXT = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|(?:AKIA|ASIA)[A-Z0-9]{16})\b")
PROVIDER_ENV = {
    "deepseek": "DEEPSEEK_API_KEY", "openai": "OPENAI_API_KEY", "openai-api": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
    "grok": "XAI_API_KEY", "xai": "XAI_API_KEY", "groq": "GROQ_API_KEY",
    "google": "GEMINI_API_KEY", "gemini": "GEMINI_API_KEY",
}


class ConfigInspectionError(Exception):
    pass


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


class ConfigReader:
    def __init__(self, home: Path, environment: Mapping[str, str]):
        self.home = home.expanduser().resolve()
        self.environment = environment
        self.private_values: set[str] = set()
        self.env_files: Dict[str, str] = {}
        self.last_config: Optional[str] = None

    def safe_path(self, relative: str) -> Path:
        path = self.home / relative
        try:
            path.resolve().relative_to(self.home)
            current = path
            while current != self.home:
                if current.is_symlink():
                    raise ConfigInspectionError("linked_path")
                current = current.parent
            return path
        except ConfigInspectionError:
            raise
        except (OSError, ValueError):
            raise ConfigInspectionError("unreadable") from None

    def has_file(self, relative: str) -> bool:
        try:
            return self.safe_path(relative).is_file()
        except OSError:
            raise ConfigInspectionError("unreadable") from None

    def text(self, relative: str) -> Optional[str]:
        try:
            path = self.safe_path(relative)
            if not path.exists():
                return None
            if not path.is_file():
                raise ConfigInspectionError("not_regular_file")
            with path.open("rb") as handle:
                content = handle.read(MAX_CONFIG_BYTES + 1)
            if len(content) > MAX_CONFIG_BYTES:
                raise ConfigInspectionError("too_large")
            return content.decode("utf-8-sig")
        except ConfigInspectionError:
            raise
        except (OSError, ValueError, UnicodeError):
            raise ConfigInspectionError("unreadable") from None

    def config(self, relative: str) -> Optional[Dict[str, Any]]:
        self.last_config = relative
        text = self.text(relative)
        if text is None:
            return None
        try:
            if relative.endswith(".toml"):
                if tomllib is None:
                    raise ConfigInspectionError("toml_unavailable")
                value = tomllib.loads(text)
            elif relative.endswith(".json"):
                value = json.loads(text)
            else:
                value = yaml.safe_load(text)
            if not isinstance(value, dict):
                raise ConfigInspectionError("invalid_config")
            return value
        except ConfigInspectionError:
            raise
        except (ValueError, TypeError, RecursionError, yaml.YAMLError):
            # Parser messages can contain the original input, including a key.
            raise ConfigInspectionError("invalid_config") from None

    def remember(self, value: Any) -> None:
        if isinstance(value, str) and value.strip():
            self.private_values.add(value.strip())
            normalized = "".join(char for char in value.strip() if char.isprintable())
            if normalized:
                self.private_values.add(normalized)

    def env_value(self, name: str, relative: str) -> tuple[Optional[str], str]:
        if not ENV_NAME.fullmatch(name):
            return None, "invalid_reference"
        if name in self.environment:
            value = self.environment[name]
            self.remember(value)
            return value, "process_environment"
        if relative not in self.env_files:
            self.env_files[relative] = self.text(relative) or ""
        for line in self.env_files[relative].splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[7:].lstrip()
            key, separator, value = line.partition("=")
            if separator and key.strip() == name:
                value = value.strip()
                if value.startswith(("\"", "'")):
                    quoted = re.match(r'''^("(?:\\.|[^"\\])*"|'[^']*')\s*(?:#.*)?$''', value)
                    if not quoted:
                        raise ConfigInspectionError("invalid_config")
                    quoted_value = quoted.group(1)
                    try:
                        value = json.loads(quoted_value) if quoted_value.startswith('"') else quoted_value[1:-1]
                    except ValueError:
                        raise ConfigInspectionError("invalid_config") from None
                else:
                    value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
                self.remember(value)
                return value, "agent_env_file"
        return None, "environment_reference"

    def credential(self, value: Any, env_file: str) -> tuple[str, str]:
        if isinstance(value, dict):
            if value.get("source") == "env":
                name = str(value.get("id") or "")
            elif value.get("source") in {"file", "exec", "store"}:
                return "external", "external_reference"
            else:
                return "unknown", "invalid_reference"
        elif isinstance(value, str):
            value = value.strip()
            if value.lower().startswith(("secretref-", "__openclaw_")):
                return "external", "external_reference"
            reference = ENV_REFERENCE.fullmatch(value)
            if reference:
                name = next(item for item in reference.groups() if item)
            else:
                self.remember(value)
                if not value or PLACEHOLDER.search(value):
                    return "missing", "agent_configuration"
                if value.lower().startswith("enc:") or value.lower().startswith("enc("):
                    return "present", "encrypted_agent_configuration"
                return "present", "agent_configuration"
        else:
            return "missing", "agent_configuration"
        resolved, source = self.env_value(name, env_file)
        if resolved and not PLACEHOLDER.search(resolved) and not ENV_REFERENCE.fullmatch(resolved.strip()):
            return "present", source
        return "reference_missing", source

    def public_text(self, value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None
        text = "".join(char for char in value.strip() if char.isprintable())
        for secret in sorted(self.private_values, key=len, reverse=True):
            for candidate in (secret, quote(secret, safe="")):
                text = text.replace(candidate, "[REDACTED]")
        return SECRET_TEXT.sub("[REDACTED]", text)[:512] or None

    def public_url(self, value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None
        try:
            url = urlsplit(value)
            if url.scheme not in {"http", "https"} or not url.hostname:
                return None
            self.remember(url.username)
            self.remember(url.password)
            host = "[%s]" % url.hostname if ":" in url.hostname else url.hostname
            if url.port is not None:
                host += ":%d" % url.port
            # Query/fragment and URL user information never reach the browser.
            return self.public_text(urlunsplit((url.scheme, host, url.path, "", "")))
        except ValueError:
            return None


def _kylinbot(reader: ConfigReader, result: Dict[str, Any]) -> None:
    for relative in (".kylinbot/config.toml", ".kylinbot/config.json", ".kylinbot/config.yaml", ".kylinbot/config.yml"):
        config = reader.config(relative)
        if config is not None:
            break
    else:
        return
    result.update(config_found=True, config_source="~/" + relative)
    providers = _mapping(config.get("providers"))
    provider = providers.get("fallback") or config.get("provider")
    models = _mapping(providers.get("models"))
    active = _mapping(models.get(provider)) if isinstance(provider, str) else {}
    if not active:
        result.update(status="unknown", reason="发现配置，但未识别默认模型路由")
        return
    result.update(provider=provider, model=active.get("model"), base_url=active.get("base_url"))
    result["credential_status"], result["credential_source"] = reader.credential(active.get("api_key"), ".kylinbot/.env")
    reliability = _mapping(config.get("reliability"))
    if reliability.get("model_routes") or reliability.get("fallback_providers"):
        result["reason"] = "检测的是默认路由；额外路由与回退由智能体决定"


def _openclaw(reader: ConfigReader, result: Dict[str, Any]) -> None:
    config = reader.config(".openclaw/openclaw.json")
    if config is None:
        return
    result.update(config_found=True, config_source="~/.openclaw/openclaw.json")
    agents = _mapping(config.get("agents"))
    defaults = _mapping(agents.get("defaults"))
    selected = defaults.get("model")
    for item in agents.get("list", []) if isinstance(agents.get("list", []), list) else []:
        if isinstance(item, dict) and item.get("id") == "main" and item.get("model"):
            selected = item["model"]
            break
    reference = selected.get("primary") if isinstance(selected, dict) else selected
    if not isinstance(reference, str) or "/" not in reference:
        result.update(status="unknown", reason="发现配置，但默认模型不是可识别的 provider/model 路由")
        return
    provider, model = reference.split("/", 1)
    active = dict(_mapping(_mapping(_mapping(config.get("models")).get("providers")).get(provider)))
    model_store = reader.config(".openclaw/agents/main/agent/models.json")
    if model_store:
        override = _mapping(_mapping(model_store.get("providers")).get(provider))
        original_key = active.get("apiKey")
        cached_key = override.get("apiKey")
        reader.remember(original_key)
        reader.remember(cached_key)
        active.update(override)
        original_reference = isinstance(original_key, dict) or (isinstance(original_key, str) and ENV_REFERENCE.fullmatch(original_key.strip()))
        cached_marker = isinstance(cached_key, str) and cached_key.lower().startswith(("secretref-", "__openclaw_"))
        if original_reference or (cached_marker and original_key is not None):
            # Generated cache markers must not hide the source's explicit reference.
            active["apiKey"] = original_key
    result.update(provider=provider, model=model, base_url=active.get("baseUrl"))
    state, source = reader.credential(active.get("apiKey"), ".openclaw/.env")
    if state == "missing":
        auth = reader.config(".openclaw/agents/main/agent/auth-profiles.json")
        entries = _mapping(_mapping(auth).get("profiles"))
        for entry in entries.values():
            if not isinstance(entry, dict) or entry.get("provider") != provider:
                continue
            candidate = entry.get("key") or entry.get("access") or entry.get("accessToken") or entry.get("token") or entry.get("keyRef") or entry.get("tokenRef")
            candidate_state, _ = reader.credential(candidate, ".openclaw/.env")
            if candidate_state == "present":
                state, source = "present", "agent_auth_store"
                break
            if candidate_state == "external":
                state, source = "external", "agent_auth_store"
                break
    if state == "missing" and reader.has_file(".openclaw/agents/main/agent/openclaw-agent.sqlite"):
        state, source = "unknown", "agent_database_not_inspected"
        result.update(status="unknown", reason="原生数据库可能保存凭据，未读取其内容；请以智能体实际配置为准")
    if state == "missing" and provider in PROVIDER_ENV:
        state, source = reader.credential("${%s}" % PROVIDER_ENV[provider], ".openclaw/.env")
    result["credential_status"], result["credential_source"] = state, source


def _hermes(reader: ConfigReader, result: Dict[str, Any], directory: str) -> None:
    relative = directory + "/config.yaml"
    config = reader.config(relative)
    if config is None:
        return
    result.update(config_found=True, config_source="~/" + relative)
    model_config = _mapping(config.get("model"))
    provider = model_config.get("provider") or config.get("provider")
    model = model_config.get("default") or model_config.get("name") or (config.get("model") if isinstance(config.get("model"), str) else None)
    result.update(provider=provider, model=model, base_url=model_config.get("base_url") or config.get("base_url"))
    credential = model_config.get("api_key") or config.get("api_key")
    env_name = model_config.get("key_env") or model_config.get("api_key_env") or config.get("key_env") or config.get("api_key_env") or PROVIDER_ENV.get(provider.lower() if isinstance(provider, str) else "")
    if credential is None and isinstance(env_name, str) and ENV_NAME.fullmatch(env_name):
        credential = "${%s}" % env_name
    if model_config.get("key_cmd") or config.get("key_cmd"):
        reader.remember(credential)
        result.update(credential_status="external", credential_source="external_reference")
    else:
        result["credential_status"], result["credential_source"] = reader.credential(credential, directory + "/.env")
        if credential is None and isinstance(provider, str) and provider not in PROVIDER_ENV and provider != "ollama":
            result.update(status="unknown", reason="原生认证或自定义凭据未解析，不能据此认定凭据缺失")
    if not isinstance(provider, str) or not provider or provider == "auto":
        result.update(status="unknown", reason="智能体自动选择服务商，未启动原生命令解析路由")


def inspect_native_api(agent_id: str, home: Path, environment: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    """Inspect the default API for one supported Agent; returned fields are public."""
    result: Dict[str, Any] = {
        "inspection_revision": INSPECTION_REVISION,
        "status": "not_configured", "config_found": False, "config_source": None,
        "provider": None, "model": None, "base_url": None,
        "credential_status": "missing", "credential_source": None,
        "connection_checked": False, "reason": "未发现该目录中的原生 API 配置",
    }
    reader = ConfigReader(Path(home), os.environ if environment is None else environment)
    try:
        if agent_id == "kylinbot":
            _kylinbot(reader, result)
        elif agent_id == "openclaw":
            _openclaw(reader, result)
        elif agent_id in {"hermes", "kylinagent"}:
            _hermes(reader, result, ".hermes" if agent_id == "hermes" else ".kylin-agent-runtime")
        else:
            result.update(status="unsupported", reason="未实现该智能体的配置状态读取")
    except ConfigInspectionError as exc:
        reasons = {
            "invalid_config": "配置格式无法安全解析（JSON 扩展语法也可能不受支持）",
            "toml_unavailable": "当前 Python 缺少 TOML 解析支持，请安装 tomli 或使用 Python 3.11 以上",
            "too_large": "配置文件超过只读检测大小限制",
            "linked_path": "配置为符号链接，未读取链接目标",
        }
        result.update(status="unknown", config_found=True, credential_status="unknown", reason=reasons.get(str(exc), "配置无法安全读取"))
        if not result["config_source"] and reader.last_config:
            result["config_source"] = "~/" + reader.last_config
    if result["config_found"] and result["status"] == "not_configured":
        if result["provider"] == "ollama" and result["credential_status"] == "missing":
            result.update(status="local", credential_status="not_required", reason="默认使用本地 Ollama；服务可用性尚未验证")
        elif not isinstance(result["model"], str) or not result["model"].strip():
            result.update(status="unknown", reason="发现配置，但默认模型信息不完整")
        elif result["credential_status"] == "unknown":
            result.update(status="unknown", reason="凭据引用格式未识别，不能据此认定凭据缺失")
        elif result["credential_status"] == "present":
            result.update(status="configured", reason=result["reason"] if result["reason"].startswith("检测的是") else "发现配置与凭据，未验证鉴权、连接或额度")
        elif result["credential_status"] == "external":
            result.update(status="managed", reason="凭据由原生外部引用提供；未执行或解析引用目标")
        else:
            result.update(status="missing_credentials", reason="发现 API 配置，但当前环境缺少可识别凭据")
    result["base_url"] = reader.public_url(result["base_url"])
    for name in ("provider", "model", "reason"):
        result[name] = reader.public_text(result[name])
    return result
