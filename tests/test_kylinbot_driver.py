# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.kylinbot_command_agent import (
    diff_memory_rows,
    parse_agent_output,
    run_case,
)


class KylinBotDriverTests(unittest.TestCase):
    def test_script_can_start_when_executed_by_path(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "kylinbot_command_agent.py"
        completed = subprocess.run(
            [sys.executable, str(script)],
            input="",
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("empty case on stdin", completed.stderr)

    def test_parse_agent_output_discards_runtime_logs(self):
        raw = (
            "2026-09-22T00:00:00Z INFO startup\n"
            "2026-09-22T00:00:01Z WARN noisy skill\n"
            "已记住，你的 benchmark 别名为 Atlas。\n"
        )
        self.assertEqual(parse_agent_output(raw), "已记住，你的 benchmark 别名为 Atlas。")

    def test_diff_memory_rows_only_reports_current_turn_changes(self):
        before = {
            "old": {"id": "old", "key": "old", "content": "same", "category": "core", "created_at": "1", "updated_at": "1"}
        }
        after = {
            **before,
            "new": {"id": "new", "key": "project", "content": "Atlas", "category": "core", "created_at": "2", "updated_at": "2"},
            "old": {"id": "old", "key": "old", "content": "changed", "category": "core", "created_at": "1", "updated_at": "3"},
        }
        events = diff_memory_rows(before, after)
        self.assertEqual([item["kind"] for item in events], ["memory_write", "memory_update"])
        self.assertEqual(events[0]["data"]["key"], "project")
        self.assertEqual(events[1]["data"]["old_value"], "same")

    def test_run_case_reuses_session_and_emits_answer_and_memory_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "brain.db"
            session_dir = root / "sessions"
            fake = root / "fake-kylin-bot.py"
            fake.write_text(
                """import os, sqlite3, sys
args = sys.argv[1:]
message = args[args.index('--message') + 1]
session = args[args.index('--session-state-file') + 1]
os.makedirs(os.path.dirname(session), exist_ok=True)
if not os.path.exists(session): open(session, 'w').write('{}')
conn = sqlite3.connect(os.environ['KYLINBOT_BRAIN_DB'])
conn.execute('create table if not exists memories (id text primary key, key text unique, content text, category text, created_at text, updated_at text)')
if 'Remember project=Atlas' in message:
    conn.execute("insert or replace into memories values ('1','project','Atlas','core','1','1')")
    conn.commit(); print('已记住。')
else:
    print('Atlas')
conn.close()
""",
                encoding="utf-8",
            )
            import sqlite3
            conn = sqlite3.connect(db)
            conn.execute("create table memories (id text primary key, key text unique, content text, category text, created_at text, updated_at text)")
            conn.commit()
            conn.close()
            case = {"id": "driver-1", "turns": [
                {"user": "Remember project=Atlas"},
                {"user": "What is project?", "query": {"key": "project"}},
            ]}
            events = run_case(
                case,
                # openKylin ships ``python3`` without a ``python`` alias;
                # use the interpreter running this test unless overridden.
                command=[os.environ.get("PYTHON", sys.executable), str(fake)],
                db_path=db,
                session_root=session_dir,
            )
            self.assertTrue(any(e["kind"] == "memory_write" and e["data"]["key"] == "project" for e in events))
            self.assertTrue(any(e["kind"] == "memory_recall" and e["data"]["key"] == "project" and e["data"]["hit"] for e in events))
            self.assertTrue(any(e["kind"] == "assistant_message" and e["data"]["text"] == "Atlas" for e in events))
            self.assertTrue((session_dir).exists())

    def test_run_case_uses_isolated_home_and_config_dir_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "agent-home"
            db = root / "brain.db"
            import sqlite3
            conn = sqlite3.connect(db)
            conn.execute("create table memories (id text primary key, key text unique, content text, category text, created_at text, updated_at text)")
            conn.commit()
            conn.close()
            calls = []

            class FakeProcess:
                returncode = 0

                def __init__(self, command, **kwargs):
                    calls.append((command, kwargs["env"]))

                def communicate(self, timeout=None):
                    return "ok", ""

            with patch.dict(os.environ, {}, clear=True), patch(
                "scripts.kylinbot_command_agent.subprocess.Popen", FakeProcess
            ):
                run_case(
                    {"id": "isolated", "turns": [{"user": "ping"}]},
                    command=["kylin-bot"],
                    db_path=db,
                    home=home,
                )

            self.assertIn("--config-dir", calls[0][0])
            config_index = calls[0][0].index("--config-dir")
            self.assertEqual(calls[0][0][config_index + 1], str(home / ".kylinbot"))
            self.assertEqual(calls[0][1]["HOME"], str(home))


if __name__ == "__main__":
    unittest.main()
