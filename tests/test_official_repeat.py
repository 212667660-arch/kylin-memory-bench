import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.aggregate_repeats import aggregate_repeat_runs
from scripts.official_repeat import prepare_agent_home


class OfficialRepeatTests(unittest.TestCase):
    def test_agent_home_snapshot_is_cleaned_without_changing_source_db(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source-home"
            isolated = root / "isolated-home"
            db = source / ".kylinbot/workspace/memory/brain.db"
            db.parent.mkdir(parents=True)
            connection = sqlite3.connect(str(db))
            connection.execute("CREATE TABLE memories (id TEXT, key TEXT, content TEXT, category TEXT, created_at TEXT, updated_at TEXT)")
            connection.execute("INSERT INTO memories VALUES ('1','private','source-only','core','1','1')")
            connection.commit()
            connection.close()
            config = source / ".kylinbot/config.yaml"
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text("model: configured\n", encoding="utf-8")

            prepare_agent_home("kylinbot", source, isolated)

            connection = sqlite3.connect(str(isolated / ".kylinbot/workspace/memory/brain.db"))
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM memories").fetchone()[0], 0)
            connection.close()
            connection = sqlite3.connect(str(db))
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM memories").fetchone()[0], 1)
            connection.close()
            self.assertTrue((isolated / ".kylinbot/config.yaml").is_file())

    def test_openclaw_snapshot_clears_transcript_dependents_without_orphaned_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source-home"
            isolated = root / "isolated-home"
            database = source / ".openclaw/agents/main/agent/openclaw-agent.sqlite"
            database.parent.mkdir(parents=True)
            connection = sqlite3.connect(str(database))
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("CREATE TABLE transcript_events (session_id TEXT, seq INTEGER, PRIMARY KEY(session_id, seq))")
            connection.execute("CREATE TABLE session_transcript_active_events (session_id TEXT, event_seq INTEGER, FOREIGN KEY(session_id, event_seq) REFERENCES transcript_events(session_id, seq) ON DELETE CASCADE)")
            connection.execute("INSERT INTO transcript_events VALUES ('s', 1)")
            connection.execute("INSERT INTO session_transcript_active_events VALUES ('s', 1)")
            connection.commit()
            connection.close()

            prepare_agent_home("openclaw", source, isolated)

            connection = sqlite3.connect(str(isolated / ".openclaw/agents/main/agent/openclaw-agent.sqlite"))
            try:
                connection.execute("PRAGMA foreign_keys=ON")
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM transcript_events").fetchone()[0], 0)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM session_transcript_active_events").fetchone()[0], 0)
            finally:
                connection.close()
            connection = sqlite3.connect(str(database))
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM transcript_events").fetchone()[0], 1)
            connection.close()

    def test_summary_separates_execution_success_from_valid_score_statistics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dimensions = {key: 50 for key in ("retention", "memory_recall", "dynamic_update", "similar_distinction", "boundary", "task_reuse")}
            for index, valid in enumerate((True, True, False), 1):
                run = root / ("repeat-%02d" % index)
                run.mkdir()
                result = {
                    "run_id": "repeat-%02d" % index,
                    "agent": "kylinbot",
                    "cases": 1,
                    "overall": 50 if valid else 0,
                    "dimensions": dimensions,
                    "score_valid": valid,
                    "score_status": "valid" if valid else "invalid_runtime",
                    "failure_counts": {},
                    "results": [{"case_id": "c", "status": "pass" if valid else "error"}],
                    "observability": {"mode": "system_level_wrapper_assisted", "native_memory_events": 0, "sources": {"process": 2, "runner": 1}},
                }
                (run / "result.json").write_text(json.dumps(result), encoding="utf-8")
                event = {"case_id": "c", "kind": "assistant_message", "data": {"text": "ok"}, "step": 1, "source": "process"}
                rows = [event]
                if not valid:
                    rows.append({"case_id": "c", "kind": "error", "data": {"category": "timeout", "message": "timeout"}, "step": 0, "source": "runner"})
                (run / "evidence.jsonl").write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            summary = aggregate_repeat_runs(root)
            self.assertEqual(summary["batch_count"], 3)
            self.assertAlmostEqual(summary["success_rate"], 2 / 3, places=4)
            self.assertAlmostEqual(summary["score_valid_rate"], 2 / 3, places=4)
            self.assertEqual(summary["overall"]["count"], 2)
            self.assertEqual(summary["overall"]["mean"], 50.0)
            self.assertEqual(summary["source"], "process")
            self.assertEqual(summary["failure_types"]["timeout"], 1)
            self.assertEqual(set(summary["failure_types"]), {"provider", "billing", "credential", "timeout", "runtime", "behavior"})

    def test_failure_categories_are_normalized_without_treating_behavior_as_runtime(self):
        from scripts.aggregate_repeats import _failure_class

        self.assertEqual(_failure_class("billing_error"), "billing")
        self.assertEqual(_failure_class("credential_error"), "credential")
        self.assertEqual(_failure_class("provider_http_503"), "provider")
        self.assertEqual(_failure_class("timeout"), "timeout")
        self.assertEqual(_failure_class("runtime_error"), "runtime")
        self.assertEqual(_failure_class("boundary_mismatch"), "behavior")


if __name__ == "__main__":
    unittest.main()
