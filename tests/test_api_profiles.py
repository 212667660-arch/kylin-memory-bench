import json
import re
import tempfile
import unittest
from pathlib import Path

from kmb.agents import build_agent_from_config, load_api_profiles, resolve_api_profile

PROFILE_YAML = """version: 1
profiles:
  - id: test-gateway
    provider: TestGW
    display_name: 测试网关
    base_url: https://gateway.example.com/v1
    endpoint: /chat/completions
    model: test-model-1
    api_key_env: TESTGW_API_KEY
    timeout_seconds: 90
    temperature: 0
"""

HTTP_AGENT_YAML = """name: text-track
type: http
api_profile: test-gateway
"""

MEMORY_AGENT_YAML = """name: memory-track
type: memory_tool
memory_impl: kv
api_profile: test-gateway
action_root: actions
"""


class ApiProfilePoolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.configs = self.tmp / "configs"
        self.configs.mkdir(parents=True)
        (self.configs / "api-profiles.yaml").write_text(PROFILE_YAML, encoding="utf-8")

    def _agent(self, text: str, name: str = "agent-t.yaml", subdir: str = "configs") -> Path:
        directory = self.tmp / subdir if subdir else self.tmp
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_http_agent_resolves_base_url_and_model_from_pool(self):
        path = self._agent(HTTP_AGENT_YAML)
        agent = build_agent_from_config(str(path))
        self.assertEqual(agent.base_url, "https://gateway.example.com/v1")
        self.assertEqual(agent.model, "test-model-1")
        self.assertEqual(agent.api_key_env, "TESTGW_API_KEY")

    def test_memory_tool_agent_gets_backend_from_pool(self):
        path = self._agent(MEMORY_AGENT_YAML, "agent-m.yaml")
        agent = build_agent_from_config(str(path))
        self.assertIsNotNone(agent.backend)
        self.assertEqual(agent.backend.backend.base_url, "https://gateway.example.com/v1")
        self.assertEqual(agent.backend.backend.model, "test-model-1")

    def test_missing_profile_raises_with_available_ids(self):
        path = self._agent(HTTP_AGENT_YAML.replace("test-gateway", "nope"), "agent-x.yaml")
        with self.assertRaisesRegex(ValueError, "nope.*test-gateway"):
            build_agent_from_config(str(path))

    def test_adjacent_pool_wins_over_upstream_pool(self):
        """与智能体同目录的池优先于上游（仓库级）池——同 id 就近覆盖。"""
        agent_dir = self.tmp / "agent-dir"
        agent_dir.mkdir(parents=True)
        # 上游池（不在 agent 旁边）：model A
        (self.tmp / "configs").mkdir(exist_ok=True)
        (self.tmp / "configs" / "api-profiles.yaml").write_text(PROFILE_YAML, encoding="utf-8")
        # 就近池：同 id test-gateway，但 model B
        (agent_dir / "api-profiles.yaml").write_text(
            PROFILE_YAML.replace("test-model-1", "nearest-model-b"), encoding="utf-8")
        (agent_dir / "agent.yaml").write_text(
            HTTP_AGENT_YAML.replace("test-gateway", "test-gateway"), encoding="utf-8")
        # 上游 id 不可见时使用就近池；此处的候选链里没有仓库文件（路径不在仓库下）
        profiles = load_api_profiles(agent_dir / "agent.yaml")
        self.assertEqual(profiles["test-gateway"]["model"], "nearest-model-b")
        agent = build_agent_from_config(str(agent_dir / "agent.yaml"))
        self.assertEqual(agent.model, "nearest-model-b")

    def test_resolve_api_profile_direct(self):
        path = self._agent(HTTP_AGENT_YAML)
        profile = resolve_api_profile("test-gateway", path)
        self.assertEqual(profile["model"], "test-model-1")
        # 只允许变量名引用，不允许任何形如密钥的值
        self.assertTrue(re.fullmatch(r"[A-Z][A-Z0-9_]{1,62}", profile["api_key_env"]))
        self.assertFalse(re.search(r"sk-[A-Za-z0-9]{8,}", json.dumps(profile)))

    def test_pool_file_has_no_secret_values(self):
        path = self._agent(HTTP_AGENT_YAML)
        blob = (self.configs / "api-profiles.yaml").read_text(encoding="utf-8")
        self.assertFalse(re.search(r"sk-[A-Za-z0-9_-]{8,}", blob))
        self.assertNotIn("authorization", blob.lower())


if __name__ == "__main__":
    unittest.main()
