import json
import tempfile
import unittest
from pathlib import Path

from scripts.agent_env_fingerprint import fingerprint_agent_home


class AgentEnvFingerprintTests(unittest.TestCase):
    def _make_home(self, root: Path, secret: str = "") -> None:
        skills = root / ".kylinbot" / "workspace" / "skills" / "demo"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text("demo skill body\n", encoding="utf-8")
        (skills / "manifest.toml").write_text("name = 'demo'\n", encoding="utf-8")
        config = root / ".kylinbot" / "config.toml"
        config.write_text("model = 'deepseek-v4-flash'\n" + secret, encoding="utf-8")

    def test_fingerprint_is_deterministic_and_change_sensitive(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self._make_home(home)
            first = fingerprint_agent_home("kylinbot", home)
            second = fingerprint_agent_home("kylinbot", home)
            self.assertEqual(first, second)
            self.assertNotEqual(first["fingerprint_sha256"], "")
            skills = home / ".kylinbot" / "workspace" / "skills" / "demo" / "SKILL.md"
            skills.write_text("changed body\n", encoding="utf-8")
            third = fingerprint_agent_home("kylinbot", home)
            self.assertNotEqual(third["fingerprint_sha256"], first["fingerprint_sha256"])

    def test_fingerprint_never_contains_file_contents_or_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self._make_home(home, secret="api_key = 'super-secret-value-123'\n")
            payload = json.dumps(fingerprint_agent_home("kylinbot", home))
            self.assertNotIn("super-secret-value-123", payload)
            self.assertNotIn("demo skill body", payload)

    def test_fingerprint_tolerates_missing_paths_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "nonexistent"
            report = fingerprint_agent_home("kylinbot", home)
            self.assertEqual(report["agent"], "kylinbot")
            self.assertTrue(all(item["sha256"] == "" for item in report["items"]))
            self.assertEqual(report["fingerprint_sha256"], "missing")


if __name__ == "__main__":
    unittest.main()
