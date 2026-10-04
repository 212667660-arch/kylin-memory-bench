import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kmb.agent_registry import AgentProfile
from kmb.agents import ReferenceAgent
from kmb.quick_compare import QuickCompareOptions, _select_profiles, run_quick_compare


def _profile(agent_id, runnable=True):
    return AgentProfile(
        id=agent_id,
        display_name=agent_id.title(),
        installed=True,
        runnable=runnable,
        adapter=agent_id,
        evidence_mode="agent_memory_observed",
        memory_paths=["~/.%s/state.db" % agent_id],
        capabilities=["retention", "memory_recall", "dynamic_update", "similar_distinction", "boundary", "task_reuse"],
        reason="fixture",
    )


class QuickCompareTests(unittest.TestCase):
    def test_preflight_only_reports_readiness_without_running_any_turns(self):
        """任务 4 步骤 4 要求的 --preflight-only：只读预检，不得发起模型回合。"""
        profiles = [_profile("kylinbot"), _profile("hermes")]
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            with patch("kmb.quick_compare.discover_agents", return_value=profiles), \
                 patch("kmb.quick_compare.run_suite", side_effect=AssertionError("preflight-only 不得执行任何 Agent 回合")):
                result = run_quick_compare(
                    QuickCompareOptions(agent_ids=["kylinbot", "hermes"], preflight_only=True, out_dir=str(out)),
                    root=Path.cwd(),
                )
            self.assertEqual(result["status"], "preflight")
            self.assertEqual(result["turns_started"], 0)
            self.assertEqual({item["agent"] for item in result["preflight"]}, {"kylinbot", "hermes"})
            self.assertTrue((out / "quick-compare.json").is_file())

    def test_preflight_only_reports_blocked_agents_and_still_runs_no_turns(self):
        class BlockedAdapter:
            def preflight(self):
                return {"agent": "kylinagent", "status": "blocked", "reason": "gui_observed only"}

        profiles = [_profile("kylinbot"), _profile("kylinagent", runnable=False)]
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            with patch("kmb.quick_compare.discover_agents", return_value=profiles), \
                 patch("kmb.quick_compare.adapter_for_profile", side_effect=[ReferenceAgent(), BlockedAdapter()]), \
                 patch("kmb.quick_compare.run_suite", side_effect=AssertionError("blocked 预检也不得执行 Agent 回合")):
                result = run_quick_compare(
                    QuickCompareOptions(agent_ids=["kylinbot", "kylinagent"], preflight_only=True, out_dir=str(out)),
                    root=Path.cwd(),
                )
            self.assertEqual(result["turns_started"], 0)
            self.assertIn("kylinagent", [item["agent"] for item in result["preflight"]])

    def test_selection_requires_two_distinct_runnable_agents(self):
        profiles = [_profile("kylinbot"), _profile("hermes"), _profile("kylinagent", runnable=False)]
        self.assertEqual([profile.id for profile in _select_profiles(QuickCompareOptions(), profiles)], ["kylinbot", "hermes"])
        with self.assertRaisesRegex(ValueError, "distinct"):
            _select_profiles(QuickCompareOptions(agent_ids=["kylinbot", "kylinbot"]), profiles)
        with self.assertRaisesRegex(ValueError, "not automatically runnable"):
            _select_profiles(QuickCompareOptions(agent_ids=["kylinbot", "kylinagent"]), profiles)

    def test_quick_compare_uses_requested_suite_and_fixed_parameters(self):
        profiles = [_profile("kylinbot"), _profile("hermes")]

        def fake_adapter(profile, timeout, home=None):
            del timeout, home
            adapter = ReferenceAgent()
            adapter.name = profile.id
            return adapter

        with tempfile.TemporaryDirectory() as tmp:
            root = Path.cwd()
            with patch("kmb.quick_compare.discover_agents", return_value=profiles), patch("kmb.quick_compare.adapter_for_profile", side_effect=fake_adapter):
                result = run_quick_compare(QuickCompareOptions(out_dir=str(Path(tmp) / "runs/quick"), suite="suites/core-zh.yaml"), root=root)
            self.assertEqual(result["parameters"], {"seed": 42, "retries": 1, "timeout": 180.0})
            self.assertEqual(result["suite"], "suites/core-zh.yaml")
            self.assertEqual([item["id"] for item in result["agents"]], ["kylinbot", "hermes"])
            self.assertTrue((Path(tmp) / "runs/quick/comparison.json").is_file())
            self.assertTrue((Path(tmp) / "runs/quick/quick-compare.json").is_file())

    def test_quick_compare_routes_distinct_isolated_homes_per_agent(self):
        profiles = [_profile("kylinbot"), _profile("openclaw")]
        observed = {}

        def fake_adapter(profile, timeout, home=None):
            del timeout
            observed[profile.id] = str(home)
            adapter = ReferenceAgent()
            adapter.name = profile.id
            return adapter

        with tempfile.TemporaryDirectory() as tmp:
            homes = {"kylinbot": str(Path(tmp) / "isolated/kylinbot"), "openclaw": str(Path(tmp) / "isolated/openclaw")}
            with patch("kmb.quick_compare.discover_agents", return_value=profiles), patch("kmb.quick_compare.adapter_for_profile", side_effect=fake_adapter):
                run_quick_compare(QuickCompareOptions(out_dir=str(Path(tmp) / "runs/quick"), agent_homes=homes), root=Path.cwd())
        self.assertEqual(observed, homes)


if __name__ == "__main__":
    unittest.main()
