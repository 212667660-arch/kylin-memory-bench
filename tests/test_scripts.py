import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScriptTests(unittest.TestCase):
    def test_env_probe_reports_local_python_and_cli(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "env_probe.py"), "--json"],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["checks"]["python"]["ok"])
        self.assertTrue(payload["checks"]["cli_import"]["ok"])

    def test_verify_run_checks_result_and_evidence_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "result.json").write_text(json.dumps({
                "agent": "a", "cases": 1, "results": [{"case_id": "c", "status": "pass"}],
            }), encoding="utf-8")
            (path / "evidence.jsonl").write_text(json.dumps({"case_id": "c", "kind": "assistant_message", "data": {}, "step": 1}) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "verify_run.py"), str(path)],
                cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("valid", result.stdout)

    def test_verify_run_rejects_unknown_event_kind(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "result.json").write_text(json.dumps({
                "agent": "a", "cases": 1, "results": [{"case_id": "c", "status": "pass"}],
            }), encoding="utf-8")
            (path / "evidence.jsonl").write_text(json.dumps({"case_id": "c", "kind": "unknown", "data": {}, "step": 1}) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "verify_run.py"), str(path)],
                cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("unsupported evidence event kind", result.stderr)

    def test_verify_run_accepts_explicit_provenance_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "result.json").write_text(json.dumps({
                "agent": "wrapper", "cases": 1, "results": [{"case_id": "c", "status": "pass"}],
            }), encoding="utf-8")
            event = {
                "case_id": "c", "kind": "memory_write", "data": {"key": "x", "source": "wrapper", "evidence_class": "wrapper_operation"},
                "step": 1, "source": "wrapper", "evidence_class": "wrapper_operation",
            }
            (path / "evidence.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "verify_run.py"), str(path)],
                cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_reference_license_audit_script_is_read_only_and_structured(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_reference_licenses.py")],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["repositories"]), 7)
        self.assertIn("needs_manual_review", payload["repositories"][0])

    def test_enrich_run_provenance_writes_new_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            output = Path(directory) / "output"
            source.mkdir()
            (source / "result.json").write_text(json.dumps({
                "agent": "wrapper", "cases": 1, "dimensions": {
                    "retention": 100, "memory_recall": 0, "dynamic_update": 0,
                    "similar_distinction": 0, "boundary": 0, "task_reuse": 0,
                }, "overall": 100, "results": [{"case_id": "c", "status": "pass", "score": 1,
                    "checks": [{"passed": True, "reason": "observed", "evidence_refs": [{"kind": "memory_write", "step": 1}]}]}],
            }), encoding="utf-8")
            (source / "evidence.jsonl").write_text(json.dumps({
                "case_id": "c", "kind": "memory_write", "data": {"key": "x", "source": "wrapper"},
                "step": 1, "source": "wrapper",
            }) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "enrich_run_provenance.py"), str(source), "--out", str(output)],
                cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            enriched = json.loads((output / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(enriched["observability"]["mode"], "system_level_wrapper_assisted")
            self.assertEqual(enriched["results"][0]["checks"][0]["evidence_refs"][0]["source"], "wrapper")

    def test_rescore_run_preserves_source_and_rejects_blocked_action(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            output = Path(directory) / "output"
            suite = Path(directory) / "suite.yaml"
            source.mkdir()
            suite.write_text(
                "cases:\n- id: c\n  capability: task_reuse\n  title: action\n  turns: []\n  checks:\n  - type: action_tool\n    value: write_file\n",
                encoding="utf-8",
            )
            (source / "result.json").write_text(json.dumps({
                "agent": "no-memory", "cases": 1, "results": [{"case_id": "c", "attempts": 1}],
            }), encoding="utf-8")
            (source / "evidence.jsonl").write_text(
                json.dumps({"case_id": "c", "kind": "action", "data": {"tool": "write_file", "blocked": True}, "step": 1, "source": "runner"})
                + "\n" + json.dumps({"case_id": "c", "kind": "error", "data": {"message": "TimeoutError: timeout"}, "step": 0, "source": "runner"}) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "rescore_run.py"), str(source), "--suite", str(suite), "--out", str(output)],
                cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rescored = json.loads((output / "result.json").read_text(encoding="utf-8"))
            self.assertFalse(rescored["results"][0]["checks"][0]["passed"])
            self.assertEqual(rescored["attempt_error_counts"], {"timeout": 1})
            self.assertTrue((source / "evidence.jsonl").exists())

    def test_aggregate_repeats_reports_statistics_without_mutating_runs(self):
        from scripts.aggregate_repeats import aggregate_repeats

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repeats"
            root.mkdir()
            dimensions = {
                "retention": 50, "memory_recall": 0, "dynamic_update": 25,
                "similar_distinction": 50, "boundary": 100, "task_reuse": 0,
            }
            for index, overall in enumerate((37.5, 62.5), 1):
                run = root / ("repeat-%02d" % index)
                run.mkdir()
                (run / "result.json").write_text(json.dumps({
                    "run_id": "repeat-%02d" % index, "agent": "grok-no-memory-baseline",
                    "cases": 1, "overall": overall, "dimensions": dimensions,
                    "failure_counts": {"omission": index},
                    "results": [{"case_id": "c", "status": "pass"}],
                    "observability": {"mode": "no_memory_baseline", "native_memory_events": 0},
                }), encoding="utf-8")
                (run / "evidence.jsonl").write_text(json.dumps({
                    "case_id": "c", "kind": "model_response",
                    "data": {"elapsed_ms": 1000 * index}, "step": 1,
                }) + "\n", encoding="utf-8")
            output = root / "summary.json"
            payload = aggregate_repeats(root, output)
            self.assertEqual(payload["batch_count"], 2)
            self.assertEqual(payload["overall"]["mean"], 50.0)
            self.assertEqual(payload["overall"]["min"], 37.5)
            self.assertEqual(payload["overall"]["max"], 62.5)
            self.assertEqual(payload["latency_ms"]["mean"], 1500.0)
            self.assertFalse(payload["consistency"]["overall_all_equal"])
            self.assertIn("innovation_metrics", payload)
            self.assertIn("metamorphic", payload)
            self.assertIn("lifecycle", payload)
            self.assertIn("actions", payload)
            self.assertIn("evidence_chain", payload)
            self.assertTrue(output.exists())
            self.assertTrue(output.with_suffix(".md").exists())

    def test_aggregate_stability_writes_all_report_formats(self):
        from scripts.aggregate_stability import build_comparison, write_outputs

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dimensions = {key: {"mean": 50, "stdev": 0, "min": 50, "max": 50} for key in (
                "retention", "memory_recall", "dynamic_update", "similar_distinction", "boundary", "task_reuse"
            )}
            summaries = []
            for name in ("grok", "deepseek"):
                summary = root / (name + ".json")
                summary.write_text(json.dumps({
                    "agent": name + "-no-memory-baseline", "batch_count": 1,
                    "valid_batch_count": 1, "execution_success_rate": 100.0,
                    "overall": {"count": 1, "mean": 50, "stdev": 0, "min": 50, "max": 50},
                    "dimensions": dimensions, "runs": [{"run_id": name + "-01"}],
                    "runs_root": "runs/innovation-no-memory/%s" % name,
                    "observability": {"native_memory_events": 0},
                }), encoding="utf-8")
                summaries.append(summary)
            payload = build_comparison(str(summaries[0]), str(summaries[1]))
            self.assertEqual(payload["suite"], "suites/lifecycle/innovation.yaml")
            self.assertTrue(payload["comparison"]["same_case_suite"])
            output = root / "stability" / "comparison.json"
            write_outputs(payload, str(output))
            self.assertEqual(payload["comparison"]["overall_mean_difference_grok_minus_deepseek"], 0.0)
            self.assertTrue(output.exists())
            self.assertTrue(output.with_suffix(".md").exists())
            self.assertTrue(output.with_suffix(".html").exists())
            self.assertTrue((output.parent / "stability-radar.svg").exists())

    def test_uninstall_cleanup_is_scoped_and_covers_kare_views(self):
        source = (ROOT / "scripts" / "uninstall_deb.sh").read_text(encoding="utf-8")
        self.assertIn("/opt/kare-applications/shadow/upper/usr/share/kylin-memory-bench", source)
        self.assertIn("nsenter -t \"$kare_pid\" -m", source)
        self.assertIn("cleanup_generated_bytecode\n  if [ \"$(id -u)\"", source)
        self.assertIn("cleanup_generated_bytecode\nfi\nelse", source)
        self.assertIn("refusing to clean outside package payload", source)
        self.assertNotIn("rm -rf -- /usr/share", source)
