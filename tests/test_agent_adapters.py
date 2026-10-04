import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kmb.agent_adapters.base import AgentCommandError
from kmb.agent_adapters.hermes import HermesAdapter
from kmb.agent_adapters.kylinagent import KylinAgentAdapter
from kmb.agent_adapters.openclaw import OpenClawAdapter
from kmb.models import BenchmarkCase


def _case():
    return BenchmarkCase.from_dict({
        "id": "adapter-gate",
        "capability": "retention",
        "title": "adapter gate",
        "turns": [
            {"user": "Please remember that my benchmark alias is Atlas."},
            {"user": "What is my benchmark alias?", "query": {"key": "benchmark_alias"}},
        ],
        "checks": [],
    })


class AgentAdapterTests(unittest.TestCase):
    def test_hermes_reads_only_memory_marked_message_deltas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.db"
            connection = sqlite3.connect(state)
            connection.execute("create table messages (id text primary key, content text, created_at text)")
            connection.commit()
            connection.close()
            fake = root / "fake_hermes.py"
            fake.write_text(
                """import os, sqlite3, sys
message = sys.argv[-1]
con = sqlite3.connect(os.environ['HERMES_STATE'])
if 'remember' in message.lower():
    con.execute(\"insert into messages values ('memory-1', 'memory_write benchmark_alias=Atlas', '1')\")
else:
    con.execute(\"insert into messages values ('chat-1', 'ordinary chat benchmark_alias Atlas', '2')\")
con.commit(); con.close(); print('{\\\"text\\\":\\\"Atlas\\\"}')
""",
                encoding="utf-8",
            )
            env = {"HERMES_COMMAND": '"%s" "%s"' % (sys.executable, fake.as_posix()), "HERMES_STATE": str(state)}
            with patch.dict(os.environ, env, clear=False):
                events = HermesAdapter(state_path=state).run(_case())
            self.assertTrue(any(event.kind == "memory_write" and event.data["key"] == "benchmark_alias" for event in events))
            self.assertTrue(any(event.kind == "memory_recall" and event.data["hit"] is True for event in events))
            self.assertTrue(any(event.kind == "assistant_message" and "Atlas" in event.data["text"] for event in events))
            self.assertFalse(any(event.kind == "memory_write" and event.data.get("value") == "ordinary chat benchmark_alias Atlas" for event in events))

    def test_hermes_detects_provider_error_even_when_cli_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.db"
            connection = sqlite3.connect(state)
            connection.execute("create table messages (id text primary key, content text, created_at text)")
            connection.commit()
            connection.close()
            with patch(
                "kmb.agent_adapters.hermes.invoke_command",
                return_value="API call failed after 3 retries: HTTP 402: Token balance insufficient",
            ):
                with self.assertRaises(AgentCommandError) as raised:
                    HermesAdapter(state_path=state).run(_case())
            self.assertEqual(raised.exception.category, "billing_error")

    def test_openclaw_file_delta_and_recall_are_observed(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            workspace = home / ".openclaw/workspace"
            workspace.mkdir(parents=True)
            user_file = workspace / "USER.md"
            user_file.write_text("# User\n", encoding="utf-8")
            adapter = OpenClawAdapter(home=home)
            calls = []

            def fake_invoke(command, timeout, env=None):
                calls.append((command, env))
                del timeout
                with user_file.open("a", encoding="utf-8") as handle:
                    handle.write("- benchmark alias: Atlas\n")
                return '{"text":"Your benchmark alias is Atlas."}'

            with patch.dict(os.environ, {"KMB_OPENCLAW_LOCAL": "1"}, clear=False), patch(
                "kmb.agent_adapters.openclaw.invoke_command", side_effect=fake_invoke
            ):
                events = adapter.run(_case())
            self.assertTrue(any(event.kind == "memory_write" and event.data["key"] == "benchmark_alias" for event in events))
            self.assertTrue(any(event.kind == "memory_recall" and event.data["hit"] is True for event in events))
            commands = [command for command, _env in calls]
            session_keys = [command[command.index("--session-key") + 1] for command in commands]
            self.assertEqual(len(set(session_keys)), 1)
            self.assertIn("adapter-gate", session_keys[0])
            self.assertTrue(all("--local" in command for command in commands))
            self.assertTrue(all(env["HOME"] == str(home) for _command, env in calls))

    def test_kylinagent_refuses_to_fabricate_gui_memory_events(self):
        adapter = KylinAgentAdapter(home=Path(tempfile.gettempdir()))
        with self.assertRaisesRegex(RuntimeError, "GUI evidence"):
            adapter.run(_case())
        self.assertEqual(adapter.describe()["evidence_mode"], "gui_observed")


if __name__ == "__main__":
    unittest.main()
