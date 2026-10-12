import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from kmb.agents import MemoryControllerAgent, NoMemoryAgent, OpenAICompatibleAgent, ReferenceAgent, FlawedAgent, ReplayAgent, CommandAgent, load_agent_config
from kmb.models import BenchmarkCase, EvidenceEvent


class AgentTests(unittest.TestCase):
    def test_command_agent_utf8_protocol_does_not_follow_host_encoding(self):
        import os
        import sys
        from unittest.mock import patch

        case = BenchmarkCase.from_dict({"id": "unicode", "capability": "retention", "title": "中文", "turns": [], "checks": []})
        program = "import json; print(json.dumps({'case_id':'unicode','kind':'assistant_message','data':{'text':'你好'},'step':1},ensure_ascii=False))"
        with patch.dict(os.environ, {"PYTHONIOENCODING": "cp1252"}):
            events = CommandAgent("unicode", [sys.executable, "-c", program], env_allowlist=["PYTHONIOENCODING"]).run(case)
        self.assertEqual(events[0].data["text"], "你好")

    def test_reference_agent_emits_memory_and_action_evidence(self):
        case = BenchmarkCase.from_dict({
            "id": "reuse",
            "capability": "task_reuse",
            "title": "reuse",
            "turns": [
                {"user": "Remember output_dir=/tmp/demo"},
                {"user": "create report", "action": {"tool": "write_file", "path_from_memory": "output_dir"}},
            ],
            "checks": [],
        })
        events = ReferenceAgent().run(case)
        self.assertTrue(any(e.kind == "memory_write" for e in events))
        self.assertTrue(any(e.kind == "action" and e.data.get("path") == "/tmp/demo" for e in events))

    def test_flawed_agent_is_deterministically_different(self):
        case = BenchmarkCase.from_dict({
            "id": "recall",
            "capability": "memory_recall",
            "title": "recall",
            "turns": [{"user": "Remember project=Atlas"}, {"user": "What is project?"}],
            "checks": [],
        })
        first = FlawedAgent().run(case)
        second = FlawedAgent().run(case)
        self.assertEqual(
            [(e.kind, e.data, e.step) for e in first],
            [(e.kind, e.data, e.step) for e in second],
        )

    def test_replay_agent_loads_external_jsonl_evidence(self):
        import json
        import tempfile
        from pathlib import Path

        case = BenchmarkCase.from_dict({
            "id": "replay-1", "capability": "memory_recall", "title": "replay",
            "turns": [], "checks": [],
        })
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            path.write_text(json.dumps({
                "case_id": "replay-1", "kind": "memory_recall",
                "data": {"key": "x", "value": "y", "hit": True}, "step": 1,
            }) + "\n", encoding="utf-8")
            events = ReplayAgent("external", str(path)).run(case)
        self.assertEqual(events[0].kind, "memory_recall")
        self.assertEqual(events[0].data["value"], "y")

    def test_command_agent_reads_jsonl_from_external_process(self):
        import sys

        case = BenchmarkCase.from_dict({
            "id": "command-1", "capability": "memory_recall", "title": "command",
            "turns": [], "checks": [],
        })
        command = [sys.executable, "-c", "import json; print(json.dumps({'case_id':'command-1','kind':'assistant_message','data':{'text':'ok'},'step':1}))"]
        events = CommandAgent("external-command", command).run(case)
        self.assertEqual(events[0].kind, "assistant_message")
        self.assertEqual(events[0].data["text"], "ok")

    def test_command_agent_uses_current_runtime_for_generic_python_command(self):
        import sys

        command = ["python", "-c", "import json; print(json.dumps({'case_id':'command-1','kind':'assistant_message','data':{'text':'ok'},'step':1}))"]
        agent = CommandAgent("external-command", command)
        self.assertEqual(agent.command[0], sys.executable)

        case = BenchmarkCase.from_dict({
            "id": "command-1", "capability": "memory_recall", "title": "command",
            "turns": [], "checks": [],
        })
        events = agent.run(case)
        self.assertEqual(events[0].data["text"], "ok")

    def test_agent_config_requires_command_for_command_type(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.yaml"
            path.write_text("name: external\ntype: command\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_agent_config(str(path))

    def test_http_agent_maps_chat_tools_and_normalized_evidence(self):
        received = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received["authorization"] = self.headers.get("Authorization")
                received["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                payload = {
                    "choices": [{"message": {
                        "content": "Atlas",
                        "tool_calls": [{"function": {"name": "memory_recall", "arguments": {"key": "project", "value": "Atlas", "hit": True}}}],
                        "kmb_evidence": [{"case_id": "http-1", "kind": "memory_recall", "data": {"key": "project", "value": "Atlas", "hit": True}, "step": 1}],
                    }}]
                }
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            import os
            os.environ["KMB_TEST_API_KEY"] = "test-secret"
            agent = OpenAICompatibleAgent(
                "http", "http://127.0.0.1:%d" % server.server_port, "test-model", "KMB_TEST_API_KEY",
            )
            case = BenchmarkCase.from_dict({
                "id": "http-1", "capability": "memory_recall", "title": "http",
                "turns": [{"user": "What is project?"}], "checks": [],
            })
            events = agent.run(case)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            os.environ.pop("KMB_TEST_API_KEY", None)
        self.assertEqual(received["authorization"], "Bearer test-secret")
        self.assertEqual(received["body"]["model"], "test-model")
        self.assertTrue(any(event.kind == "assistant_message" and event.data["text"] == "Atlas" for event in events))
        self.assertTrue(any(event.kind == "memory_recall" and event.data["value"] == "Atlas" for event in events))

    def test_http_config_requires_api_fields(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.yaml"
            path.write_text("name: external\ntype: http\nbase_url: http://localhost\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_agent_config(str(path))

    def test_memory_controller_marks_wrapper_and_model_sources_and_sandboxes_action(self):
        import tempfile
        from pathlib import Path

        class FakeBackend:
            name = "fake-model"
            model = "fake-v1"

            def _url(self):
                return "http://mock.local/chat/completions"

            def _request(self, messages):
                return {"id": "mock-response", "choices": [{"message": {"content": "Room B"}, "finish_reason": "stop"}]}

            def _message(self, response):
                return response["choices"][0]["message"]

            def _tool_events(self, message, step):
                return []

            def _evidence_events(self, case, response, message, step):
                return []

        case = BenchmarkCase.from_dict({
            "id": "controller-1", "capability": "task_reuse", "title": "controller",
            "turns": [
                {"user": "Remember output_dir=/tmp/demo", "memory": {"op": "write", "key": "output_dir", "value": "/tmp/demo", "persist": True}},
                {"user": "Where?", "query": {"key": "output_dir"}},
                {"user": "Create report", "action": {"tool": "write_file", "path_from_memory": "output_dir"}},
            ],
            "checks": [],
        })
        with tempfile.TemporaryDirectory(dir=str(Path.cwd())) as directory:
            events = MemoryControllerAgent("controller", FakeBackend(), directory).run(case)
            wrapper_events = [event for event in events if event.data.get("source") == "wrapper"]
            model_events = [event for event in events if event.data.get("source") == "model"]
            action = next(event for event in events if event.kind == "action")
            self.assertTrue(any(event.kind == "memory_write" for event in wrapper_events))
            self.assertTrue(any(event.kind == "memory_recall" for event in wrapper_events))
            self.assertTrue(any(event.kind == "assistant_message" for event in model_events))
            self.assertEqual(action.data["path"], "/tmp/demo")
            self.assertTrue(Path(action.data["actual_path"]).exists())

    def test_memory_controller_config_is_accepted(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.yaml"
            path.write_text(
                "name: controller\ntype: memory_controller\nbase_url: http://localhost\nmodel: fake\napi_key_env: TEST_KEY\n",
                encoding="utf-8",
            )
            self.assertEqual(load_agent_config(str(path))["type"], "memory_controller")

    def test_no_memory_agent_runs_model_and_records_disabled_operations(self):
        class FakeBackend:
            name = "fake-model"
            model = "fake-v1"

            def describe(self):
                return {"adapter": "FakeBackend", "model": self.model}

            def _url(self):
                return "http://mock.local/chat/completions"

            def _request(self, messages):
                return {"id": "mock-response", "choices": [{"message": {"content": "I cannot access memory."}, "finish_reason": "stop"}]}

            def _message(self, response):
                return response["choices"][0]["message"]

            def _tool_events(self, message, step):
                return []

            def _evidence_events(self, case, response, message, step):
                return []

        case = BenchmarkCase.from_dict({
            "id": "no-memory-1", "capability": "task_reuse", "title": "no memory",
            "turns": [
                {"user": "Remember output_dir=/tmp/demo", "memory": {"op": "write", "key": "output_dir", "value": "/tmp/demo", "persist": True}},
                {"user": "Where?", "query": {"key": "output_dir"}},
                {"user": "Create report", "action": {"tool": "write_file", "path_from_memory": "output_dir"}},
            ],
            "checks": [],
        })
        events = NoMemoryAgent("no-memory", FakeBackend()).run(case)
        baseline = [event for event in events if event.evidence_class == "no_memory_baseline"]
        self.assertTrue(any(event.kind == "memory_suppress" and event.data.get("disabled") for event in baseline))
        self.assertTrue(any(event.kind == "memory_recall" and not event.data.get("hit") for event in baseline))
        action = next(event for event in baseline if event.kind == "action")
        self.assertFalse(action.data["executed"])
        self.assertIsNone(action.data["path"])
        self.assertEqual(len([event for event in events if event.kind == "model_request"]), 3)
        self.assertFalse(any(event.kind in ("memory_write", "memory_update") for event in baseline))

    def test_no_memory_config_is_accepted(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.yaml"
            path.write_text(
                "name: no-memory\ntype: memory_disabled\nbase_url: http://localhost\nmodel: fake\napi_key_env: TEST_KEY\n",
                encoding="utf-8",
            )
            self.assertEqual(load_agent_config(str(path))["type"], "memory_disabled")

    def test_evidence_provenance_is_explicit(self):
        case = BenchmarkCase.from_dict({
            "id": "provenance", "capability": "memory_recall", "title": "provenance",
            "turns": [{"user": "Remember project=Atlas"}], "checks": [],
        })
        event = ReferenceAgent().run(case)[1]
        self.assertEqual(event.source, "simulated")
        self.assertEqual(event.evidence_class, "simulated_baseline")
        self.assertEqual(event.to_dict()["source"], "simulated")
        self.assertEqual(event.to_dict()["evidence_class"], "simulated_baseline")

    def test_native_memory_requires_observed_state(self):
        with self.assertRaises(ValueError):
            EvidenceEvent("memory_write", {"key": "x", "value": "y"}, 1, source="model", evidence_class="model_native_memory")
        observed = EvidenceEvent(
            "memory_write", {"key": "x", "value": "y", "state_observed": True}, 1,
            source="model", evidence_class="model_native_memory",
        )
        self.assertEqual(observed.evidence_class, "model_native_memory")


if __name__ == "__main__":
    unittest.main()
