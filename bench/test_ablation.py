"""Tests for bench/ablation.py (issue #2130).

Covers the three load-bearing invariants:
  1. key-exclusion — key/ material never present in a prepared run workspace;
  2. scoresheet schema — blank verdicts, all four metric families, JSON+md twin;
  3. stream-json parsing — cost/turns pulled from the terminal result event,
     honest None when absent.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ablation  # noqa: E402


class KeyExclusionTest(unittest.TestCase):
    def test_every_task_workspace_excludes_key_material(self):
        for task_id in ablation.list_tasks():
            task = ablation.load_task(task_id)
            with tempfile.TemporaryDirectory() as td:
                ws = ablation.prepare_workspace(task, Path(td) / "ws")
                names = {p.name for p in ws.rglob("*")}
                self.assertNotIn("key", names, task_id)
                self.assertNotIn("answers", names, task_id)
                self.assertNotIn("key.json", names, task_id)
                self.assertNotIn("key.md", names, task_id)

    def test_assert_no_key_material_raises_on_leak(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            (ws / "key").mkdir(parents=True)
            with self.assertRaises(RuntimeError):
                ablation.assert_no_key_material(ws)

    def test_every_task_has_key_and_metadata(self):
        tasks = ablation.list_tasks()
        self.assertGreaterEqual(len(tasks), 6)
        classes = set()
        for task_id in tasks:
            task = ablation.load_task(task_id)
            key = ablation.load_key(task_id)
            self.assertTrue(task["requirement"])
            self.assertTrue((ablation.ROOT / task["fixture"]).is_dir())
            self.assertGreaterEqual(len(key["acceptance"]), 3)
            self.assertTrue(key["adjudication"])
            classes.add(task["class"])
        self.assertLessEqual(
            {"bugfix", "feature", "derivation", "underspecified"}, classes)


class StreamJsonParsingTest(unittest.TestCase):
    def test_parses_terminal_result_event(self):
        log = "\n".join([
            json.dumps({"type": "system", "subtype": "init"}),
            json.dumps({"type": "assistant", "message": {}}),
            "not json at all",
            json.dumps({"type": "result", "total_cost_usd": 0.42,
                        "num_turns": 7, "duration_ms": 12345,
                        "result": "done", "is_error": False}),
        ])
        p = ablation.parse_stream_json(log)
        self.assertTrue(p["found"])
        self.assertEqual(p["cost_usd"], 0.42)
        self.assertEqual(p["num_turns"], 7)
        self.assertEqual(p["duration_ms"], 12345)
        self.assertEqual(p["result_text"], "done")
        self.assertFalse(p["is_error"])

    def test_missing_result_event_is_honest_none(self):
        p = ablation.parse_stream_json(
            json.dumps({"type": "assistant"}) + "\n")
        self.assertFalse(p["found"])
        self.assertIsNone(p["cost_usd"])
        self.assertIsNone(p["num_turns"])


class ScoresheetSchemaTest(unittest.TestCase):
    def _fake_run(self):
        return {"arm": "B", "rep": 1, "exit": 0, "model": "sonnet",
                "max_turns_budget": 200, "wall_clock_sec": 12.3,
                "cost_usd": 0.1, "turns": 5, "cli_duration_ms": 1000,
                "result_found": True, "is_error": False,
                "workspace": "/tmp/x", "stream_log": "b-1.stream.jsonl",
                "files_touched": ["foo.py"],
                "final_output": "I fixed foo.py and ran the tests; all pass."}

    def test_scoresheet_has_blank_verdicts_and_all_metric_families(self):
        task = ablation.load_task("t01-version-bugfix")
        with tempfile.TemporaryDirectory() as td:
            j, m = ablation.emit_scoresheet(task, self._fake_run(), Path(td))
            sheet = json.loads(j.read_text())
            # metric families: requirement-met, wall-clock/cost/turns,
            # fabrication check
            self.assertIn("requirement_met", sheet)
            for row in sheet["requirement_met"]:
                self.assertIsNone(row["verdict"])   # BLANK by protocol
            for metric in ("wall_clock_sec", "cost_usd", "turns"):
                self.assertIn(metric, sheet["metrics"])
            self.assertIn("fabrication_check", sheet)
            for claim in sheet["fabrication_check"]:
                self.assertIsNone(claim["artifact_exists"])
                self.assertIsNone(claim["runnable"])
            # no aggregation anywhere
            text = j.read_text() + m.read_text()
            for banned in ("pass_rate", "score_total", "aggregate"):
                self.assertNotIn(banned, text)
            # markdown twin exists and carries the same acceptance rows
            md = m.read_text()
            for row in sheet["requirement_met"]:
                self.assertIn(row["id"], md)

    def test_fabrication_check_extracts_artifact_claims(self):
        claims = ablation.extract_claims(
            "I added test_foo.py and ran pytest; everything passes. "
            "The fix lives in fixture_target/__init__.py.")
        self.assertTrue(claims)
        joined = " ".join(c["claim"] for c in claims)
        self.assertIn("test_foo.py", joined)

    def test_arm_a_plan_names_spawn_and_budget(self):
        task = ablation.load_task("t01-version-bugfix")
        plan = ablation.arm_a_plan(task, "sonnet", 200)
        self.assertIn("spawn.py implementation", plan)
        self.assertIn("--max-turns 200", plan)
        self.assertIn("--model sonnet", plan)


if __name__ == "__main__":
    unittest.main()
