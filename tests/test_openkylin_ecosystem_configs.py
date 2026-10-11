# -*- coding: utf-8 -*-
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs"


class TokenCenterAndEcosystemConfigTests(unittest.TestCase):
    def test_openkylin_token_http_template(self):
        """文本轨智能体只保留 api_profile 引用；API 设置在全局档案池中。"""
        path = CONFIGS / "agent-openkylin-token.yaml"
        self.assertTrue(path.is_file())
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(raw.get("type"), "http")
        self.assertEqual(raw.get("api_profile"), "openkylin-token")
        self.assertNotIn("base_url", raw)
        self.assertNotIn("api_key_env", raw)
        pool = yaml.safe_load((CONFIGS / "api-profiles.yaml").read_text(encoding="utf-8"))
        profiles = {p["id"]: p for p in pool.get("profiles", [])}
        profile = profiles["openkylin-token"]
        self.assertEqual(profile.get("base_url"), "https://llm-gateway.openkylin.top/v1")
        self.assertEqual(profile.get("endpoint"), "/chat/completions")
        self.assertEqual(profile.get("api_key_env"), "OPENKYLIN_TOKEN_API_KEY")
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("sk-", text)
        self.assertNotIn("api_key:", text.lower().replace("api_key_env", "").replace("api_profile", ""))

    def test_ecosystem_command_examples_parse_without_secrets(self):
        for name in ("agent-kylinbot-command.yaml.example", "agent-openclaw-command.yaml.example"):
            path = CONFIGS / name
            self.assertTrue(path.is_file(), name)
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(raw.get("type"), "command", name)
            self.assertTrue(raw.get("command"), name)
            self.assertIsInstance(raw.get("env_allowlist"), list, name)
            text = path.read_text(encoding="utf-8")
            self.assertFalse(re.search(r"sk-[A-Za-z0-9]{16,}", text), name)
            # api_key style assignments should not hold values
            for line in text.splitlines():
                if re.match(r"^\s*(api_key|password|token)\s*:", line, re.I):
                    self.fail("secret-like key in %s: %s" % (name, line))

    def test_kylinbot_snapshot_profile_uses_guest_python3(self):
        path = CONFIGS / "agent-kylinbot-command.yaml"
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(raw.get("type"), "command")
        self.assertEqual((raw.get("command") or [None])[0], "python3")
        self.assertIn("cli-driver", str(raw.get("version", "")).lower())
        self.assertIn("brain.db", str(raw.get("description", "")).lower())

    def test_docs_exist(self):
        for rel in (
            "docs/openkylin-token-center.md",
            "docs/ecosystem-agent-export.md",
            "research/openkylin-agent-ecosystem/REPORT.md",
        ):
            self.assertTrue((ROOT / rel).is_file(), rel)


if __name__ == "__main__":
    unittest.main()
