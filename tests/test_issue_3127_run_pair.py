"""Issue #3127 repair round, defect 3 (found by PR #3145's second
independent verification): scrub_skill_slugs() and evaluate_pair_blind()
existed (or, before this repair, did not exist at all) but were never
called by anything the harness's real execution path reaches -- "defined
and never invoked" is exactly the shape defect 3 names.

This file tests run_pair() -- the orchestration entry point that ties
execute_arm() (dispatch+watch), gate_pair_on_h1() (defect 2's H1 gate),
and evaluate_pair_blind() (defect 3's scorer) into one call, proving the
scorer is actually reachable from the harness's real per-pair flow, not
just callable in isolation from a test.

Repair round 2 (independent verification on PR #3131, PR #3158): every
test below this docstring mocks `arm_workspace_dir()` itself, which means
they pass whether or not `arm_workspace_dir()`'s own body is reachable --
and it was not: it referenced the undefined name `_spawn_mod`, so a real
call raised `NameError` before the H1 gate or blind scorer was ever
reached. `RunPairRealReachabilityTest` below calls `run_pair()` without
mocking `arm_workspace_dir()` -- only the spawn.py dispatch boundary
(`subprocess.run` calls whose command is literally `python3 spawn.py
...`) is stubbed, so `arm_workspace_dir()`'s real body, including its
call into `spawn.py`'s own `_workspace_target_path()`, actually executes
against a real (if throwaway) git repo.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "issue-3127"))
import run_consumer_pair as rcp  # noqa: E402


def _watched_result(arm_name: str, issue: int) -> dict:
    return {"arm": arm_name, "issue": issue, "status": "watched-to-completion",
            "wall_clock_to_pr_open_s": 12.3, "dispatch_returncode": 0,
            "watch_returncode": 0, "watch_stderr": None}


class RunPairTest(unittest.TestCase):
    def setUp(self):
        args = _fake_args()
        self.plan = rcp.build_plan(args)
        self.pair = self.plan.pairs[0]

    def tearDown(self):
        import shutil
        shutil.rmtree(self.plan.arms[1].skill_repo_env_override,
                       ignore_errors=True)

    def test_h1_pass_reaches_and_calls_the_blind_scorer(self):
        """The core defect-3 claim: evaluate_pair_blind() is reachable
        from run_pair(), the harness's real per-pair flow -- not orphaned."""
        scorer_calls = []

        def fake_evaluator_fn(prompt: str) -> str:
            scorer_calls.append(prompt)
            return '{"document_1_score": 8, "document_2_score": 6, ' \
                   '"verdict": "document_1", "reasoning": "x"}'

        with mock.patch.object(rcp, "execute_arm") as m_exec, \
             mock.patch.object(rcp, "arm_workspace_dir") as m_ws:
            m_exec.side_effect = lambda plan, pair, arm, issue, confirm: \
                _watched_result(arm.name, issue)
            m_ws.side_effect = lambda plan, issue: Path(f"/tmp/does-not-"
                                                          f"matter-{issue}")

            def fetcher(plan, issue):
                return f"deliverable text for issue {issue}, no slug"

            with mock.patch.object(rcp, "collect_directive_bytes") as m_bytes:
                m_bytes.side_effect = lambda ws: 500 if "101" in str(ws) else 50
                result = rcp.run_pair(
                    self.plan, self.pair, on_issue=101, off_issue=102,
                    confirm_real_spawn=True,
                    known_slugs=[self.plan.skill_name],
                    deliverable_fetcher=fetcher,
                    evaluator_fn=fake_evaluator_fn)

        self.assertFalse(result["excluded_from_h2"])
        self.assertIsNotNone(result["h2"])
        self.assertEqual(len(scorer_calls), 1)  # scorer was actually invoked
        # Genuinely blind: arm labels never in the prompt handed to the
        # evaluator.
        self.assertNotIn("skills-on", scorer_calls[0])
        self.assertNotIn("skills-off", scorer_calls[0])

    def test_h1_failure_excludes_pair_and_scorer_is_never_called(self):
        scorer_calls = []

        def fake_evaluator_fn(prompt: str) -> str:
            scorer_calls.append(prompt)
            return "{}"

        with mock.patch.object(rcp, "execute_arm") as m_exec, \
             mock.patch.object(rcp, "arm_workspace_dir") as m_ws, \
             mock.patch.object(rcp, "collect_directive_bytes") as m_bytes:
            m_exec.side_effect = lambda plan, pair, arm, issue, confirm: \
                _watched_result(arm.name, issue)
            m_ws.side_effect = lambda plan, issue: Path(f"/tmp/ws-{issue}")
            m_bytes.return_value = 500  # identical for both arms -> H1 fails

            result = rcp.run_pair(
                self.plan, self.pair, on_issue=201, off_issue=202,
                confirm_real_spawn=True,
                known_slugs=[self.plan.skill_name],
                deliverable_fetcher=lambda plan, issue: "text",
                evaluator_fn=fake_evaluator_fn)

        self.assertTrue(result["excluded_from_h2"])
        self.assertIsNone(result["h2"])
        self.assertEqual(scorer_calls, [])

    def test_missing_deliverable_leaves_h2_none_with_reason_not_h1_reason(self):
        with mock.patch.object(rcp, "execute_arm") as m_exec, \
             mock.patch.object(rcp, "arm_workspace_dir") as m_ws, \
             mock.patch.object(rcp, "collect_directive_bytes") as m_bytes:
            m_exec.side_effect = lambda plan, pair, arm, issue, confirm: \
                _watched_result(arm.name, issue)
            m_ws.side_effect = lambda plan, issue: Path(f"/tmp/ws-{issue}")
            m_bytes.side_effect = lambda ws: 500 if "301" in str(ws) else 50

            result = rcp.run_pair(
                self.plan, self.pair, on_issue=301, off_issue=302,
                confirm_real_spawn=True,
                known_slugs=[self.plan.skill_name],
                deliverable_fetcher=lambda plan, issue: None,
                evaluator_fn=lambda prompt: "{}")

        self.assertFalse(result["excluded_from_h2"])
        self.assertIsNone(result["h2"])
        self.assertIn("deliverable fetch failed", result["h2_unavailable_reason"])


class RunPairRealReachabilityTest(unittest.TestCase):
    """Round 2's must-not: do not mock `arm_workspace_dir()`. Only the
    spawn.py dispatch boundary is stubbed (at the `subprocess.run` process
    level, and only for commands that are literally `python3 spawn.py
    ...`) -- `arm_workspace_dir()` itself, and the `git remote get-url
    origin` call inside spawn.py's own `_workspace_target_path()` that it
    reaches, run for real."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="issue-3127-reachability-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.work_dir = self.tmp / "work"
        self.work_dir.mkdir()
        self.sandbox = self.tmp / "sandbox"
        self.sandbox.mkdir()
        subprocess.run(["git", "init"], cwd=self.sandbox, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin",
                         "https://github.com/acme/sandbox.git"],
                        cwd=self.sandbox, capture_output=True)

        env_patch = mock.patch.dict(os.environ, {"MUSTER_WORK_DIR": str(self.work_dir)})
        env_patch.start()
        self.addCleanup(env_patch.stop)

        args = _fake_args(repo=str(self.sandbox))
        self.plan = rcp.build_plan(args)
        self.addCleanup(shutil.rmtree, self.plan.arms[1].skill_repo_env_override,
                         ignore_errors=True)
        self.pair = self.plan.pairs[0]

    def _make_workspace(self, issue: int, directive_byte_count: int) -> Path:
        # Must match spawn.py's own _workspace_target_path() naming
        # exactly (<repo_name>-issue-<n>-<skill>) -- this test does not
        # re-derive that convention, it relies on arm_workspace_dir()'s
        # real call into spawn.py to compute it, and only pre-populates
        # the directory that call will resolve to.
        ws = self.work_dir / f"sandbox-issue-{issue}-{self.plan.skill_name}"
        directive_dir = ws / ".on-the-record" / "directive"
        directive_dir.mkdir(parents=True)
        (directive_dir / "a.md").write_text("x" * directive_byte_count, encoding="utf-8")
        return ws

    def _stubbed_subprocess_run(self, real_run):
        def _fake(cmd, *args, **kwargs):
            if list(cmd[:2]) == ["python3", "spawn.py"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            return real_run(cmd, *args, **kwargs)
        return _fake

    def test_run_pair_real_flow_reaches_h1_gate_and_blind_scorer(self):
        on_issue, off_issue = 401, 402
        self._make_workspace(on_issue, 500)
        self._make_workspace(off_issue, 50)

        scorer_calls = []

        def fake_evaluator_fn(prompt: str) -> str:
            scorer_calls.append(prompt)
            return ('{"document_1_score": 8, "document_2_score": 6, '
                    '"verdict": "document_1", "reasoning": "x"}')

        real_run = subprocess.run
        with mock.patch.object(rcp.subprocess, "run",
                                side_effect=self._stubbed_subprocess_run(real_run)):
            result = rcp.run_pair(
                self.plan, self.pair, on_issue=on_issue, off_issue=off_issue,
                confirm_real_spawn=True, known_slugs=[self.plan.skill_name],
                deliverable_fetcher=lambda plan, issue: f"deliverable {issue}, no slug",
                evaluator_fn=fake_evaluator_fn)

        self.assertFalse(result["excluded_from_h2"])
        self.assertTrue(result["h1_manipulation_ok"])
        self.assertIsNotNone(result["h2"])
        # The must-prove claim: the blind scorer was actually invoked from
        # run_pair()'s real, unmocked arm_workspace_dir() flow -- not just
        # callable in isolation.
        self.assertEqual(len(scorer_calls), 1)

    def test_run_pair_real_flow_h1_failure_still_excludes_and_skips_scorer(self):
        on_issue, off_issue = 501, 502
        self._make_workspace(on_issue, 500)
        self._make_workspace(off_issue, 500)  # identical bytes -> H1 fails

        scorer_calls = []

        def fake_evaluator_fn(prompt: str) -> str:
            scorer_calls.append(prompt)
            return "{}"

        real_run = subprocess.run
        with mock.patch.object(rcp.subprocess, "run",
                                side_effect=self._stubbed_subprocess_run(real_run)):
            result = rcp.run_pair(
                self.plan, self.pair, on_issue=on_issue, off_issue=off_issue,
                confirm_real_spawn=True, known_slugs=[self.plan.skill_name],
                deliverable_fetcher=lambda plan, issue: f"deliverable {issue}",
                evaluator_fn=fake_evaluator_fn)

        self.assertTrue(result["excluded_from_h2"])
        self.assertIsNone(result["h2"])
        self.assertEqual(scorer_calls, [])


def _fake_args(**overrides):
    import argparse
    ns = argparse.Namespace(
        repo="/tmp/sandbox", pinned_sha=None,
        skill="product-discovery-hypothesis-preregistration", model="sonnet",
        pairs="01-study-groups", skill_repo_on="$MUSTER_SKILL_REGISTRY_ROOT",
        skill_repo_off=None, watch_timeout=1800)
    for k, v in overrides.items():
        setattr(ns, k, v)
    return ns


if __name__ == "__main__":
    unittest.main()
