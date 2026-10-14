import os
import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from kmb.agent_registry import discover_agents, profile_to_dict


class AgentRegistryTests(unittest.TestCase):
    def _home(self):
        tmp = tempfile.TemporaryDirectory()
        home = Path(tmp.name)
        (home / ".kylinbot/workspace/memory").mkdir(parents=True)
        (home / ".kylinbot/workspace/memory/brain.db").touch()
        (home / ".hermes").mkdir()
        (home / ".hermes/state.db").touch()
        (home / ".openclaw/agents/main/agent").mkdir(parents=True)
        (home / ".openclaw/agents/main/agent/openclaw-agent.sqlite").touch()
        (home / ".openclaw/workspace").mkdir(parents=True)
        (home / ".openclaw/workspace/USER.md").write_text("secret should not be read", encoding="utf-8")
        (home / ".kylin-agent-runtime").mkdir()
        (home / ".kylin-agent-runtime/state.db").touch()
        (home / ".kylin-agent-runtime/memory.db").touch()
        return tmp, home

    def test_discovery_reports_four_installed_agents_without_reading_contents(self):
        tmp, home = self._home()
        try:
            with patch.dict(os.environ, {"KMB_AGENT_HOME": str(home)}, clear=False):
                profiles = discover_agents()
            by_id = {profile.id: profile for profile in profiles}
            self.assertEqual(set(by_id), {"kylinbot", "hermes", "openclaw", "kylinagent"})
            self.assertTrue(all(profile.installed for profile in profiles))
            self.assertEqual(by_id["kylinbot"].evidence_mode, "agent_memory_observed")
            self.assertEqual(by_id["hermes"].evidence_mode, "agent_memory_observed")
            self.assertEqual(by_id["openclaw"].evidence_mode, "agent_memory_observed")
            self.assertEqual(by_id["kylinagent"].evidence_mode, "gui_observed")
            self.assertFalse(by_id["kylinagent"].runnable)
            self.assertIn("不能自动", by_id["kylinagent"].reason)
        finally:
            tmp.cleanup()

    def test_absent_agents_are_safe_and_explainable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"KMB_AGENT_HOME": tmp}, clear=False):
                profiles = discover_agents(path_lookup=lambda _: None)
            self.assertEqual(len(profiles), 4)
            self.assertTrue(all(not profile.installed for profile in profiles))
            self.assertTrue(all(profile.reason for profile in profiles))

    def test_kylinbot_toml_only_installation_is_detected_without_reading_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".kylinbot").mkdir()
            path = home / ".kylinbot/config.toml"
            path.write_text("native-private-config-not-to-read", encoding="utf-8")
            with patch.object(Path, "read_text", side_effect=AssertionError("Installation detection reads only metadata")):
                profile = discover_agents(home=home, path_lookup=lambda _: None)[0]
            self.assertTrue(profile.installed)
            self.assertFalse(profile.runnable)
            self.assertIn("configuration_file", profile.detection_sources)

    def test_serialization_exposes_metadata_only(self):
        tmp, home = self._home()
        try:
            with patch.dict(os.environ, {"KMB_AGENT_HOME": str(home)}, clear=False):
                profile = discover_agents()[0]
            payload = profile_to_dict(profile)
            self.assertEqual(payload["id"], profile.id)
            self.assertNotIn("secret should not be read", str(payload))
            self.assertNotIn("content", payload)
            self.assertIsInstance(payload["memory_paths"], list)
        finally:
            tmp.cleanup()

    def test_cli_discover_agents_accepts_json_flag(self):
        from kmb.cli import main

        with patch("kmb.agent_registry.discover_agents", return_value=[]), patch("sys.stdout", new_callable=StringIO) as stdout:
            self.assertEqual(main(["discover-agents", "--json"]), 0)
        self.assertEqual(json.loads(stdout.getvalue()), {"agents": []})


if __name__ == "__main__":
    unittest.main()
