import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kmb.native_api import MAX_CONFIG_BYTES, inspect_native_api


class NativeApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.secret = "synthetic-private-sentinel-987654"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, value):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")
        return path

    def claw(self, credential=None, provider="deepseek"):
        config = {
            "agents": {"defaults": {"model": {"primary": provider + "/model-demo"}}},
            "models": {"providers": {provider: {"baseUrl": "https://api.example.test/v1", "apiKey": credential}}},
        }
        self.write(".openclaw/openclaw.json", config)
        return config

    def inspect(self, agent="openclaw", environment=None):
        value = inspect_native_api(agent, self.home, {} if environment is None else environment)
        self.assertFalse(value["connection_checked"])
        self.assertNotIn(self.secret, json.dumps(value))
        return value

    def test_kylinbot_reads_actual_provider_models_toml_without_decrypting(self):
        self.write(".kylinbot/config.toml", '[providers]\nfallback="deepseek"\n[providers.models.deepseek]\nmodel="model-demo"\nbase_url="https://api.example.test/v1"\napi_key="enc:v1:synthetic-private-sentinel-987654"\n')
        result = self.inspect("kylinbot")
        self.assertEqual(result["status"], "configured")
        self.assertEqual(result["provider"], "deepseek")
        self.assertEqual(result["credential_source"], "encrypted_agent_configuration")

    def test_openclaw_env_reference_uses_native_env_file(self):
        self.claw("${DEEPSEEK_API_KEY}")
        self.write(".openclaw/.env", 'DEEPSEEK_API_KEY="' + self.secret + '"\n')
        result = self.inspect()
        self.assertEqual(result["status"], "configured")
        self.assertEqual(result["credential_source"], "agent_env_file")

    def test_process_environment_takes_precedence_over_native_env_file(self):
        self.claw("${DEEPSEEK_API_KEY}")
        self.write(".openclaw/.env", "DEEPSEEK_API_KEY=" + self.secret)
        result = self.inspect(environment={"DEEPSEEK_API_KEY": ""})
        self.assertEqual(result["status"], "missing_credentials")
        self.assertEqual(result["credential_source"], "process_environment")

    def test_native_env_comments_do_not_change_the_key_or_allow_metadata_leaks(self):
        config = self.claw("${DEEPSEEK_API_KEY}")
        config["agents"]["defaults"]["model"]["primary"] = "deepseek/" + self.secret
        self.write(".openclaw/openclaw.json", config)
        self.write(".openclaw/.env", 'DEEPSEEK_API_KEY="' + self.secret + '" # private comment\n')
        result = self.inspect()
        self.assertEqual(result["status"], "configured")
        self.assertEqual(result["model"], "[REDACTED]")

    def test_long_secret_is_redacted_before_display_length_limit(self):
        secret = "synthetic-long-private-" + "x" * 700
        config = self.claw(secret)
        config["agents"]["defaults"]["model"]["primary"] = "deepseek/" + secret
        self.write(".openclaw/openclaw.json", config)
        result = self.inspect()
        self.assertEqual(result["model"], "[REDACTED]")
        self.assertNotIn("synthetic-long-private-", json.dumps(result))

    def test_missing_reference_is_not_reported_as_configured(self):
        self.claw("${DEEPSEEK_API_KEY}")
        result = self.inspect()
        self.assertEqual(result["status"], "missing_credentials")
        self.assertEqual(result["credential_status"], "reference_missing")

    def test_openclaw_main_model_and_model_store_override_are_observed(self):
        config = self.claw()
        config["agents"]["list"] = [{"id": "main", "model": {"primary": "other/selected-model"}}]
        self.write(".openclaw/openclaw.json", config)
        self.write(".openclaw/agents/main/agent/models.json", {"providers": {"other": {"baseUrl": "https://selected.example.test/v1", "apiKey": self.secret}}})
        result = self.inspect()
        self.assertEqual(result["model"], "selected-model")
        self.assertEqual(result["base_url"], "https://selected.example.test/v1")
        self.assertEqual(result["status"], "configured")

    def test_auth_store_checks_only_matching_provider(self):
        self.claw()
        self.write(".openclaw/agents/main/agent/auth-profiles.json", {"profiles": {"unrelated": {"provider": "other", "key": self.secret}}})
        self.assertEqual(self.inspect()["status"], "missing_credentials")
        self.write(".openclaw/agents/main/agent/auth-profiles.json", {"profiles": {"deepseek:default": {"provider": "deepseek", "type": "api_key", "key": self.secret}}})
        self.assertEqual(self.inspect()["credential_source"], "agent_auth_store")

    def test_missing_explicit_reference_does_not_fall_back_to_another_auth_profile(self):
        self.claw({"source": "env", "provider": "default", "id": "DEEPSEEK_API_KEY"})
        self.write(".openclaw/agents/main/agent/auth-profiles.json", {"profiles": {"deepseek:default": {"provider": "deepseek", "key": self.secret}}})
        self.assertEqual(self.inspect()["status"], "missing_credentials")

    def test_cached_secret_marker_does_not_make_missing_reference_configured(self):
        self.claw("${DEEPSEEK_API_KEY}")
        self.write(".openclaw/agents/main/agent/models.json", {"providers": {"deepseek": {"apiKey": "secretref-env:DEEPSEEK_API_KEY"}}})
        self.assertEqual(self.inspect()["status"], "missing_credentials")
        self.write(".openclaw/.env", "DEEPSEEK_API_KEY=" + self.secret)
        self.assertEqual(self.inspect()["status"], "configured")

    def test_native_database_is_not_read_or_assumed_to_have_no_credentials(self):
        self.claw()
        self.write(".openclaw/agents/main/agent/openclaw-agent.sqlite", self.secret)
        result = self.inspect()
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["credential_source"], "agent_database_not_inspected")

    def test_url_credentials_and_query_are_removed_and_duplicate_secret_is_redacted(self):
        config = self.claw(self.secret)
        config["agents"]["defaults"]["model"]["primary"] = "deepseek/" + self.secret
        config["models"]["providers"]["deepseek"]["baseUrl"] = "https://private-user:private-password@api.example.test/v1?key=" + self.secret + "#private-fragment"
        self.write(".openclaw/openclaw.json", config)
        result = self.inspect()
        serialized = json.dumps(result)
        for private in ("private-user", "private-password", "private-fragment", "?key="):
            self.assertNotIn(private, serialized)
        self.assertEqual(result["base_url"], "https://api.example.test/v1")
        self.assertEqual(result["model"], "[REDACTED]")

    def test_external_reference_is_not_followed_or_executed(self):
        self.claw({"source": "exec", "id": "must-not-execute"})
        with patch("subprocess.run", side_effect=AssertionError("No command is allowed")), patch("urllib.request.urlopen", side_effect=AssertionError("No network is allowed")):
            result = self.inspect()
        self.assertEqual(result["status"], "managed")
        self.assertEqual(result["credential_status"], "external")

    def test_unknown_reference_format_is_not_reported_as_missing_or_configured(self):
        self.claw({"unexpected_source": "unrecognized"})
        self.assertEqual(self.inspect()["status"], "unknown")

    def test_hermes_provider_and_env_are_detected(self):
        self.write(".hermes/config.yaml", "model:\n  provider: openrouter\n  default: vendor/model-demo\n  base_url: https://api.example.test/v1\n")
        self.write(".hermes/.env", "OPENROUTER_API_KEY=" + self.secret)
        result = self.inspect("hermes")
        self.assertEqual(result["status"], "configured")
        self.assertEqual(result["model"], "vendor/model-demo")

    def test_hermes_custom_key_env_is_resolved_without_changing_the_environment(self):
        self.write(".hermes/config.yaml", "model:\n  provider: custom\n  default: model-demo\n  base_url: https://api.example.test/v1\n  key_env: CUSTOM_API_KEY\n")
        self.write(".hermes/.env", "CUSTOM_API_KEY=" + self.secret)
        environment = {}
        result = self.inspect("hermes", environment)
        self.assertEqual(result["status"], "configured")
        self.assertEqual(environment, {})

    def test_hermes_key_command_is_not_executed_or_replaced_with_static_key(self):
        self.write(".hermes/config.yaml", "model:\n  provider: custom\n  default: model-demo\n  key_cmd: must-not-execute\n  api_key: " + self.secret + "\n")
        with patch("subprocess.run", side_effect=AssertionError("No helper is allowed")):
            result = self.inspect("hermes")
        self.assertEqual(result["status"], "managed")

    def test_auto_provider_stays_unknown_even_if_an_env_key_exists(self):
        self.write(".hermes/config.yaml", "model:\n  provider: auto\n  default: vendor/model-demo\n")
        result = self.inspect("hermes", {"OPENROUTER_API_KEY": self.secret})
        self.assertEqual(result["status"], "unknown")

    def test_invalid_and_oversized_config_do_not_leak_parser_input(self):
        self.write(".openclaw/openclaw.json", '{"apiKey":"' + self.secret)
        result = self.inspect()
        self.assertEqual(result["status"], "unknown")
        self.assertTrue(result["config_found"])
        self.write(".openclaw/openclaw.json", " " * (MAX_CONFIG_BYTES + 1))
        self.assertEqual(self.inspect()["status"], "unknown")

    def test_placeholder_is_not_a_real_credential(self):
        self.claw("[REDACTED]")
        self.assertEqual(self.inspect()["status"], "missing_credentials")

    def test_ollama_is_local_without_claiming_a_running_service(self):
        self.claw(provider="ollama")
        result = self.inspect()
        self.assertEqual(result["status"], "local")
        self.assertEqual(result["credential_status"], "not_required")

    def test_missing_config_does_not_probe_environment_for_unselected_providers(self):
        result = self.inspect(environment={"DEEPSEEK_API_KEY": self.secret})
        self.assertEqual(result["status"], "not_configured")
        self.assertFalse(result["config_found"])

    def test_symlinked_config_is_not_read(self):
        target = self.write("private.json", {"apiKey": self.secret})
        link = self.home / ".openclaw/openclaw.json"
        link.parent.mkdir(parents=True)
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("OS does not permit creating symlinks")
        self.assertEqual(self.inspect()["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
