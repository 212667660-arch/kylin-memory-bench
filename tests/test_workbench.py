import json
import os
import tempfile
import time
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from kmb.agent_registry import AgentProfile
from kmb.agents import build_agent_from_config
from kmb.workbench import WorkbenchHandler, WorkbenchState, load_credentials_file


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=str(Path.cwd()))
        self.root = Path(self.temp.name)
        (self.root / "configs").mkdir()
        (self.root / "suites").mkdir()
        (self.root / "runs" / "sample" / "reference").mkdir(parents=True)
        (self.root / "configs" / "reference.yaml").write_text(
            "name: reference\ntype: deterministic\ndescription: local\n", encoding="utf-8"
        )
        (self.root / "configs" / "bad.yaml").write_text(
            "name: api\ntype: http\nbase_url: https://example.test/v1\nmodel: demo\napi_key_env: KMB_TEST_SECRET\n", encoding="utf-8"
        )
        (self.root / "suites" / "core.yaml").write_text(
            "cases:\n  - id: c1\n    capability: retention\n    title: one\n    turns: []\n    checks: []\n", encoding="utf-8"
        )
        result = {
            "run_id": "sample-run", "started_at": "2026-09-09T00:00:00+00:00",
            "agent": "reference", "cases": 1, "seed": 42, "retries": 1,
            "overall": 100.0, "dimensions": {"retention": 100.0},
            "observability": {"mode": "simulated_baseline", "disclaimer": "synthetic", "native_memory_events": 0},
            "failure_counts": {}, "evidence_chain": {"events": 1, "link_coverage": 1.0},
            "results": [{"case_id": "c1", "capability": "retention", "score": 1.0, "status": "pass", "checks": [], "failures": []}],
            "evidence": "runs/sample/reference/evidence.jsonl",
        }
        (self.root / "runs" / "sample" / "reference" / "result.json").write_text(json.dumps(result), encoding="utf-8")
        (self.root / "runs" / "sample" / "reference" / "evidence.jsonl").write_text(
            json.dumps({"run_id": "sample-run", "agent": "reference", "case_id": "c1", "kind": "assistant_message", "data": {"text": "ok"}, "step": 1, "source": "model"}) + "\n", encoding="utf-8"
        )
        self.state = WorkbenchState(str(self.root))

    def tearDown(self):
        self.state.close()
        self.temp.cleanup()

    def test_lists_only_non_secret_config_metadata(self):
        os.environ["KMB_TEST_SECRET"] = "do-not-return-this-value"
        try:
            configs = self.state.list_configs()
        finally:
            os.environ.pop("KMB_TEST_SECRET", None)
        self.assertEqual({item["name"] for item in configs}, {"reference", "api"})
        serialized = json.dumps(configs)
        self.assertNotIn("do-not-return-this-value", serialized)
        self.assertNotIn("Authorization", serialized)
        self.assertIn("configured", serialized)

    def test_agent_discovery_endpoint_returns_safe_profiles(self):
        with patch("kmb.workbench.discover_agents", return_value=[]):
            self.assertEqual(self.state.list_agents(), [])
        server = ThreadingHTTPServer(("127.0.0.1", 0), WorkbenchHandler)
        server.workbench_state = self.state
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:%d" % server.server_address[1]
        try:
            with patch.object(self.state, "list_agents", return_value=[{"id": "kylinbot", "installed": True, "runnable": True}]):
                with urlopen(base + "/api/agents", timeout=3) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["agents"][0]["id"], "kylinbot")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_quick_compare_accepts_two_runnable_installed_agents_only(self):
        profiles = [
            AgentProfile("kylinbot", "小K KylinBot", True, True, "kylinbot", evidence_mode="agent_memory_observed"),
            AgentProfile("hermes", "Hermes", True, True, "hermes", evidence_mode="agent_memory_observed"),
            AgentProfile("kylinagent", "KylinAgent", True, False, "kylinagent", evidence_mode="gui_observed", reason="需要 GUI 控制器"),
        ]
        with patch("kmb.workbench.discover_agents", return_value=profiles), patch.object(self.state.executor, "submit", return_value=None):
            job = self.state.start_quick_compare({"agents": ["kylinbot", "hermes"]})
        self.assertEqual(job["kind"], "quick_compare")
        self.assertEqual(job["agents"], ["kylinbot", "hermes"])
        self.assertEqual(job["params"]["suite"], "suites/quick.yaml")
        with patch("kmb.workbench.discover_agents", return_value=profiles):
            with self.assertRaisesRegex(ValueError, "not automatically runnable"):
                self.state.start_quick_compare({"agents": ["kylinbot", "kylinagent"]})

    def test_quick_compare_one_click_auto_selects_two_runnable(self):
        profiles = [
            AgentProfile("kylinbot", "小K KylinBot", True, True, "kylinbot", evidence_mode="agent_memory_observed"),
            AgentProfile("kylinagent", "KylinAgent", True, False, "kylinagent", evidence_mode="gui_observed", reason="已安装，但当前只有 GUI/服务级观测"),
            AgentProfile("hermes", "Hermes", True, True, "hermes", evidence_mode="agent_memory_observed"),
        ]
        with patch("kmb.workbench.discover_agents", return_value=profiles), patch.object(self.state.executor, "submit", return_value=None):
            job = self.state.start_quick_compare({"agents": []})
        self.assertEqual(job["kind"], "quick_compare")
        self.assertEqual(job["agents"], ["kylinbot", "hermes"])

    def test_quick_compare_blocked_reports_reason_and_fix_conditions(self):
        profiles = [
            AgentProfile("kylinbot", "小K KylinBot", True, True, "kylinbot", evidence_mode="agent_memory_observed"),
            AgentProfile("kylinagent", "KylinAgent", True, False, "kylinagent", evidence_mode="gui_observed", reason="已安装，但当前只有 GUI/服务级观测，不能自动生成结构化记忆证据"),
            AgentProfile("openclaw", "OpenClaw", False, False, "openclaw", evidence_mode="unavailable", reason="未检测到已知存储路径或可执行文件"),
        ]
        with patch("kmb.workbench.discover_agents", return_value=profiles):
            with self.assertRaises(ValueError) as ctx:
                self.state.start_quick_compare({"agents": []})
        message = str(ctx.exception)
        self.assertIn("kylinagent", message)
        self.assertIn("GUI/服务级观测", message)
        self.assertIn("openclaw", message)
        self.assertIn("修复条件", message)

    def test_list_agents_exposes_fix_hint_for_blocked_profiles(self):
        profiles = [
            AgentProfile("kylinbot", "小K KylinBot", True, True, "kylinbot", evidence_mode="agent_memory_observed"),
            AgentProfile("kylinagent", "KylinAgent", True, False, "kylinagent", evidence_mode="gui_observed", reason="已安装，但当前只有 GUI/服务级观测"),
            AgentProfile("hermes", "Hermes", False, False, "hermes", evidence_mode="unavailable", reason="未检测到已知存储路径或可执行文件"),
        ]
        with patch("kmb.workbench.discover_agents", return_value=profiles):
            agents = {item["id"]: item for item in self.state.list_agents()}
        self.assertEqual(agents["kylinbot"]["fix_hint"], "")
        self.assertIn("结构化", agents["kylinagent"]["fix_hint"])
        self.assertIn("修复条件", agents["hermes"]["fix_hint"])

    def test_quick_compare_http_endpoint_passes_agent_ids_without_secrets(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), WorkbenchHandler)
        server.workbench_state = self.state
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:%d" % server.server_address[1]
        payload = {"agents": ["kylinbot", "hermes"], "api_key": "must-not-leak"}
        safe_job = {"id": "quick-test", "kind": "quick_compare", "status": "queued", "agents": payload["agents"]}
        try:
            with patch.object(self.state, "start_quick_compare", return_value=safe_job) as start:
                request = Request(base + "/api/quick-compare", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
                with urlopen(request, timeout=3) as response:
                    self.assertEqual(response.status, 202)
                    result = json.loads(response.read().decode("utf-8"))
            start.assert_called_once_with(payload)
            self.assertEqual(result["id"], "quick-test")
            self.assertNotIn("must-not-leak", json.dumps(result))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_cloud_config_metadata_identifies_provider_and_mode(self):
        (self.root / "configs" / "agent-grok.yaml").write_text(
            "name: grok-api\ntype: http\nbase_url: https://api.wapq.cn/v1\nmodel: grok-4.6\napi_key_env: GROK_API_KEY\n",
            encoding="utf-8",
        )
        (self.root / "configs" / "agent-deepseek-memory.yaml").write_text(
            "name: deepseek-memory-controller\ntype: memory_controller\nbase_url: https://api.deepseek.com\nmodel: deepseek-v4-flash\napi_key_env: DEEPSEEK_API_KEY\n",
            encoding="utf-8",
        )
        configs = {item["name"]: item for item in self.state.list_configs()}
        self.assertEqual(configs["grok-api"]["provider"], "Grok")
        self.assertEqual(configs["grok-api"]["profile_mode"], "标准 API")
        self.assertEqual(configs["deepseek-memory-controller"]["provider"], "DeepSeek")
        self.assertEqual(configs["deepseek-memory-controller"]["profile_mode"], "记忆开启")

    def test_create_api_profile_writes_pool_entry_without_agent_files(self):
        result = self.state.create_api_profile({
            "profile_id": "openrouter",
            "provider": "OpenRouter",
            "name": "OpenRouter · GPT-4.1 mini",
            "base_url": "https://openrouter.ai/api/v1",
            "endpoint": "/chat/completions",
            "model": "openai/gpt-4.1-mini",
            "api_key_env": "OPENROUTER_API_KEY",
            "timeout_seconds": "75",
            "temperature": "0.2",
            "description": "shared gateway",
        })
        self.assertEqual(result["status"], "created")
        entry = {item["id"]: item for item in self.state.list_api_profiles()}["openrouter"]
        self.assertEqual(entry["model"], "openai/gpt-4.1-mini")
        self.assertEqual(entry["credential"], "not_detected")
        # 不再生成任何智能体文件——API 档案是全局资源池
        agent_files = [p.name for p in (self.root / "configs").glob("agent-openrouter*")]
        self.assertEqual(agent_files, [])
        # 池文件只保存变量名，不保存密钥值
        blob = (self.root / "configs" / "api-profiles.yaml").read_text(encoding="utf-8")
        self.assertNotIn("must-not-leak", blob)

    def test_create_api_profile_rejects_secret_payload_and_duplicate(self):
        with self.assertRaises(ValueError):
            self.state.create_api_profile({
                "profile_id": "unsafe",
                "name": "Unsafe",
                "base_url": "https://example.test/v1",
                "model": "demo",
                "api_key_env": "UNSAFE_API_KEY",
                "api_key": "must-not-be-accepted",
            })
        self.state.create_api_profile({
            "profile_id": "duplicate",
            "name": "Duplicate",
            "base_url": "https://example.test/v1",
            "model": "demo",
            "api_key_env": "DUPLICATE_API_KEY",
        })
        with self.assertRaises(FileExistsError):
            self.state.create_api_profile({
                "profile_id": "duplicate",
                "name": "Duplicate again",
                "base_url": "https://example.test/v1",
                "model": "demo",
                "api_key_env": "DUPLICATE_API_KEY",
            })

    def test_update_api_profile_changes_resolved_model_without_touching_agent_files(self):
        self.state.create_api_profile({
            "profile_id": "pooled",
            "name": "Pooled gateway",
            "base_url": "https://example.test/v1",
            "model": "model-a",
            "api_key_env": "POOLED_API_KEY",
        })
        agent_path = self.root / "configs" / "agent-memory.yaml"
        original_yaml = (
            "name: memory-track\ntype: memory_tool\nmemory_impl: kv\n"
            "api_profile: pooled\naction_root: actions\n"
        )
        agent_path.write_text(original_yaml, encoding="utf-8")
        before = build_agent_from_config(str(agent_path))
        self.assertEqual(before.backend.backend.model, "model-a")
        self.state.update_api_profile("pooled", {
            "profile_id": "pooled",
            "name": "Pooled gateway",
            "base_url": "https://example.test/v1",
            "model": "model-b",
            "api_key_env": "POOLED_API_KEY",
        })
        after = build_agent_from_config(str(agent_path))
        self.assertEqual(after.backend.backend.model, "model-b")
        # 智能体文件未被回写
        self.assertEqual(agent_path.read_text(encoding="utf-8"), original_yaml)

    def test_list_configs_classifies_tracks(self):
        (self.root / "configs" / "api-profiles.yaml").write_text(
            "version: 1\nprofiles:\n  - id: pooled\n    base_url: https://example.test/v1\n    model: model-a\n    api_key_env: POOLED_API_KEY\n",
            encoding="utf-8",
        )
        (self.root / "configs" / "agent-memory.yaml").write_text(
            "name: memory-track\ntype: memory_tool\nmemory_impl: kv\napi_profile: pooled\n",
            encoding="utf-8",
        )
        (self.root / "configs" / "agent-kylinbot-command.yaml").write_text(
            "name: kylinbot-command\ntype: command\ncommand: [\"echo\", \"hi\"]\n",
            encoding="utf-8",
        )
        tracks = {item["name"]: item["track"] for item in self.state.list_configs()}
        self.assertEqual(tracks["reference"], "control")
        self.assertEqual(tracks["memory-track"], "B")
        self.assertEqual(tracks["kylinbot-command"], "A")

    def test_start_run_records_track_and_materializes_api_override(self):
        self.state.create_api_profile({
            "profile_id": "pooled",
            "name": "Pooled gateway",
            "base_url": "https://example.test/v1",
            "model": "model-a",
            "api_key_env": "POOLED_API_KEY",
        })
        agent_yaml = (
            "name: memory-track\ntype: memory_tool\nmemory_impl: kv\n"
            "api_profile: pooled\naction_root: actions\n"
        )
        (self.root / "configs" / "agent-memory.yaml").write_text(agent_yaml, encoding="utf-8")
        (self.root / "configs" / "agent-memory2.yaml").write_text(
            agent_yaml.replace("memory-track", "memory-track-2"), encoding="utf-8")
        payload = {
            "primary_agent": "configs/agent-memory.yaml",
            "comparison_agent": "configs/agent-memory2.yaml",
            "suite": "suites/core.yaml",
            "track": "B",
            "api_profiles": {"configs/agent-memory.yaml": "pooled"},
        }
        job = self.state.start_run(payload)
        self.assertEqual(job["track"], "B")
        output = self.root / job["output"]
        meta = json.loads((output / "workbench-meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["track"], "B")
        self.assertEqual(meta["api_profiles"]["configs/agent-memory.yaml"]["profile_id"], "pooled")
        runtime = output / ".runtime"
        self.assertTrue(any(p.name.startswith("agent-memory-") for p in runtime.glob("*.yaml")))
        # 智能体默认引用未被回写
        self.assertEqual((self.root / "configs" / "agent-memory.yaml").read_text(encoding="utf-8"), agent_yaml)
        # 停止后台评测并等待线程收尾，避免异步写入与临时目录清理竞态
        self.state.stop_job(job["id"])
        for _ in range(50):
            snapshot = self.state.jobs.get(job["id"], {})
            if snapshot.get("status") in {"stopped", "failed", "completed"}:
                break
            time.sleep(0.2)

    def test_credentials_file_loads_workspace_referenced_custom_env(self):
        path = self.root / "credentials.env"
        path.write_text("CUSTOM_PROVIDER_API_KEY=synthetic-custom-secret\n", encoding="utf-8")
        os.chmod(path, 0o600)
        (self.root / "configs" / "custom.yaml").write_text(
            "name: custom\ntype: http\nbase_url: https://example.test/v1\nmodel: demo\napi_key_env: CUSTOM_PROVIDER_API_KEY\n",
            encoding="utf-8",
        )
        previous_file = os.environ.get("KMB_CREDENTIALS_FILE")
        previous = os.environ.pop("CUSTOM_PROVIDER_API_KEY", None)
        os.environ["KMB_CREDENTIALS_FILE"] = str(path)
        try:
            with patch("kmb.workbench._credential_file_status", return_value={"status": "secure", "path": "configured credential file", "mode": "0600", "loaded_names": []}):
                result = load_credentials_file(self.root)
            self.assertEqual(result["loaded_names"], ["CUSTOM_PROVIDER_API_KEY"])
            self.assertEqual(os.environ["CUSTOM_PROVIDER_API_KEY"], "synthetic-custom-secret")
            self.assertNotIn("synthetic-custom-secret", json.dumps(result))
        finally:
            os.environ.pop("CUSTOM_PROVIDER_API_KEY", None)
            if previous is not None:
                os.environ["CUSTOM_PROVIDER_API_KEY"] = previous
            if previous_file is None:
                os.environ.pop("KMB_CREDENTIALS_FILE", None)
            else:
                os.environ["KMB_CREDENTIALS_FILE"] = previous_file

    def test_secure_credentials_file_loads_allowlisted_names_without_returning_values(self):
        path = self.root / "credentials.env"
        path.write_text(
            "GROK_API_KEY=synthetic-grok-secret\nDEEPSEEK_MODEL=deepseek-v4-flash\nIGNORED=value\n",
            encoding="utf-8",
        )
        previous = {name: os.environ.pop(name, None) for name in ("GROK_API_KEY", "DEEPSEEK_MODEL")}
        previous_file = os.environ.get("KMB_CREDENTIALS_FILE")
        os.environ["KMB_CREDENTIALS_FILE"] = str(path)
        try:
            with patch("kmb.workbench._credential_file_status", return_value={"status": "secure", "path": "configured credential file", "mode": "0600", "loaded_names": []}):
                result = load_credentials_file()
            self.assertEqual(result["status"], "secure")
            self.assertEqual(result["loaded_names"], ["DEEPSEEK_MODEL", "GROK_API_KEY"])
            self.assertNotIn("synthetic-grok-secret", json.dumps(result))
            self.assertEqual(os.environ["DEEPSEEK_MODEL"], "deepseek-v4-flash")
        finally:
            for name in ("GROK_API_KEY", "DEEPSEEK_MODEL"):
                os.environ.pop(name, None)
                if previous[name] is not None:
                    os.environ[name] = previous[name]
            if previous_file is None:
                os.environ.pop("KMB_CREDENTIALS_FILE", None)
            else:
                os.environ["KMB_CREDENTIALS_FILE"] = previous_file

    def test_result_listing_and_detail_use_workspace_relative_paths(self):
        entries = self.state.list_runs()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["path"], "runs/sample/reference")
        detail = self.state.get_run("runs/sample/reference")
        self.assertEqual(detail["kind"], "single")
        self.assertEqual(detail["result"]["run_id"], "sample-run")
        self.assertEqual(detail["result"]["_workbench"]["evidence_path"], "runs/sample/reference/evidence.jsonl")

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            self.state.artifact("runs/../configs/reference.yaml")
        with self.assertRaises(ValueError):
            self.state.config_path("../secrets.yaml")

    def test_deterministic_health_does_not_require_credentials(self):
        result = self.state.health("configs/reference.yaml")
        self.assertEqual(result["status"], "healthy")
        self.assertNotIn("secret", json.dumps(result).lower())

    def test_stop_job_sets_cancel_event_without_marking_completed(self):
        job_id = "wb-stop-test"
        self.state.jobs[job_id] = {
            "id": job_id, "status": "queued", "output": "runs/workbench/wb-stop-test",
            "progress": {"completed": 0, "total": 2, "phase": "排队中"}, "error": None,
        }
        self.state.cancel_events[job_id] = threading.Event()
        result = self.state.stop_job(job_id)
        self.assertEqual(result["status"], "stopping")
        self.assertTrue(self.state.cancel_events[job_id].is_set())
        self.assertNotEqual(result["status"], "completed")

    def test_http_endpoints_return_real_data_and_reject_unknown_paths(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), WorkbenchHandler)
        server.workbench_state = self.state
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:%d" % server.server_address[1]
        try:
            with urlopen(base + "/api/runs", timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["runs"][0]["path"], "runs/sample/reference")
            request = Request(base + "/api/health", data=json.dumps({"config": "configs/reference.yaml"}).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=3) as response:
                self.assertEqual(json.loads(response.read().decode("utf-8"))["status"], "healthy")
            with self.assertRaises(HTTPError) as error:
                urlopen(base + "/api/artifact?path=" + "../outside.txt", timeout=3)
                self.assertEqual(error.exception.code, 400)
            profile_request = Request(
                base + "/api/profiles",
                data=json.dumps({
                    "profile_id": "api-test",
                    "name": "API Test",
                    "provider": "TestGW",
                    "base_url": "https://example.test/v1",
                    "endpoint": "/chat/completions",
                    "model": "demo",
                    "api_key_env": "API_TEST_KEY",
                    "timeout_seconds": "60",
                    "temperature": "0",
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urlopen(profile_request, timeout=3) as response:
                self.assertEqual(response.status, 201)
                created = json.loads(response.read().decode("utf-8"))
            self.assertEqual(created["status"], "created")
            self.assertNotIn("secret", json.dumps(created).lower())
            with urlopen(base + "/api/profiles", timeout=3) as response:
                profiles = json.loads(response.read().decode("utf-8"))["profiles"]
            self.assertIn("api-test", [item["id"] for item in profiles])
            # 旧端点已移除：POST /api/configs 返回 404
            with self.assertRaises(HTTPError) as removed:
                urlopen(Request(base + "/api/configs", data=b"{}", headers={"Content-Type": "application/json"}, method="POST"), timeout=3)
            self.assertEqual(removed.exception.code, 404)
            secret_request = Request(
                base + "/api/profiles",
                data=json.dumps({
                    "profile_id": "api-secret",
                    "name": "API Secret",
                    "base_url": "https://example.test/v1",
                    "model": "demo",
                    "api_key_env": "API_SECRET_KEY",
                    "api_key": "should-not-pass",
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with self.assertRaises(HTTPError) as secret_error:
                urlopen(secret_request, timeout=3)
            self.assertEqual(secret_error.exception.code, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


    def test_nested_official_repeat_runs_get_friendly_titles(self):
        """官方批次嵌套目录（验收目录/official-repeat/...）在结果列表中应显示可读标题。"""
        base = self.root / "runs" / "official-installed-20261004" / "official-repeat"
        agent_dir = base / "agents" / "kylinbot" / "repeat-01"
        agent_dir.mkdir(parents=True)
        (agent_dir / "result.json").write_text(json.dumps({
            "run_id": "quick-c5dddf589c00-kylinbot", "agent": "kylinbot",
            "overall": 63.89, "score_valid": True, "cases": 6,
            "results": [], "started_at": "2026-10-04T08:00:00Z",
        }), encoding="utf-8")
        compare_dir = base / "repeat-01" / "quick-compare"
        compare_dir.mkdir(parents=True)
        (compare_dir / "comparison.json").write_text(json.dumps({
            "agents": [
                {"agent": "kylinbot", "overall": 63.89, "score_valid": True, "started_at": "2026-10-04T08:00:00Z"},
                {"agent": "openclaw", "overall": 22.22, "score_valid": True, "started_at": "2026-10-04T08:05:00Z"},
            ],
        }), encoding="utf-8")
        entries = {entry["path"]: entry for entry in self.state.list_runs(limit=500)}
        single = entries.get("runs/official-installed-20261004/official-repeat/agents/kylinbot/repeat-01")
        self.assertIsNotNone(single)
        self.assertEqual(single["title"], "official-installed-20261004 · repeat-01 · kylinbot")
        compare = entries.get("runs/official-installed-20261004/official-repeat/repeat-01/quick-compare")
        self.assertIsNotNone(compare)
        self.assertEqual(compare["title"], "official-installed-20261004 · repeat-01 · kylinbot + openclaw")

if __name__ == "__main__":
    unittest.main()
