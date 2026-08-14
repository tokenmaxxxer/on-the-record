#!/usr/bin/env python3
"""issue #287 S1/S7: `gh` 호출 실패가 "위반 없음"으로 둔갑하면 안 된다.

  python3 -m pytest gates/test_closure_sweep.py
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
import closure_sweep


class IssueViewFailure(unittest.TestCase):
    def test_gh_failure_yields_ok_false(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=1, stdout="")
            state, ok = closure_sweep._issue_view(Path("."), 1)
        self.assertFalse(ok)
        self.assertIsNone(state)

    def test_gh_success_yields_ok_true(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="OPEN\n")
            state, ok = closure_sweep._issue_view(Path("."), 1)
        self.assertTrue(ok)
        self.assertEqual(state, "OPEN")


class PrViewFailure(unittest.TestCase):
    def test_gh_failure_yields_ok_false(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=1, stdout="")
            view, ok = closure_sweep._pr_view_state_body(Path("."), 1)
        self.assertFalse(ok)
        self.assertIsNone(view)

    def test_unparseable_json_yields_ok_false(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="not-json")
            view, ok = closure_sweep._pr_view_state_body(Path("."), 1)
        self.assertFalse(ok)
        self.assertIsNone(view)


class FindViolationsSkips(unittest.TestCase):
    """gh 실패로 확인 못한 subject 는 skips 에 남는다 — violations 가 0건
    이어도 "checked, clean" 이 아니다.

    issue #1320: 스윕 경로는 O(1) gh 호출만 쓴다 — 벌크 인덱스가 실패/잘림
    이어도 더 이상 `_issue_view`/`_pr_view_state_body` 개별 조회로
    되돌아가지 않고, 곧장 skip 이 된다."""

    def setUp(self):
        self.orig_issue_state_index_all = closure_sweep.issue_state_index_all
        self.orig_pr_index_all = closure_sweep._pr_index_all
        self.addCleanup(setattr, closure_sweep, "issue_state_index_all",
                         self.orig_issue_state_index_all)
        self.addCleanup(setattr, closure_sweep, "_pr_index_all", self.orig_pr_index_all)

    def test_issue_list_failure_is_a_skip_not_a_silent_pass(self):
        closure_sweep.issue_state_index_all = lambda root: (None, False)
        closure_sweep._pr_index_all = lambda root: ({}, True)
        subjects = {"issue-135": {"implementation": {}}}
        violations, skips = closure_sweep.find_violations(Path("."), subjects=subjects)
        self.assertEqual(violations, [])
        self.assertEqual(len(skips), 1)
        self.assertEqual(skips[0]["subject"], "issue-135")
        self.assertEqual(skips[0]["reason"], "gh-issue-list-failed")

    def test_pr_list_truncation_is_a_skip_with_no_per_item_fallback(self):
        closure_sweep.issue_state_index_all = lambda root: ({135: "OPEN"}, True)
        closure_sweep._pr_index_all = lambda root: (None, True)
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            subjects = {"issue-135": {"implementation": {}}}
            violations, skips = closure_sweep.find_violations(Path("."), subjects=subjects)
        run.assert_not_called()
        self.assertEqual(violations, [])
        self.assertEqual(len(skips), 1)
        self.assertEqual(skips[0]["reason"], "gh-pr-list-truncated")

    def test_no_gh_issue_or_pr_view_invoked_in_sweep_path(self):
        """issue #1320 acceptance (b): any `gh issue view`/`gh pr view`
        call from the sweep path is a failure — assert directly on the
        subprocess.run argv the sweep issues."""
        closure_sweep.issue_state_index_all = lambda root: (None, False)
        closure_sweep._pr_index_all = lambda root: (None, False)
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            subjects = {f"issue-{n}": {"implementation": {}} for n in range(1, 51)}
            closure_sweep.find_violations(Path("."), subjects=subjects)
        run.assert_not_called()

    def test_sweep_gh_call_count_is_constant_in_board_size(self):
        """issue #1320 acceptance (a): constant gh invocations for N in
        {5, 50}."""
        def run_stub(cmd, cwd=None, capture_output=None, text=None):
            if cmd[:2] == ["gh", "issue"]:
                return mock.Mock(returncode=0, stdout=json.dumps(
                    [{"number": n, "state": "OPEN"} for n in range(1, 51)]))
            if cmd[:2] == ["gh", "pr"]:
                return mock.Mock(returncode=0, stdout=json.dumps([]))
            raise AssertionError(f"unexpected gh call in sweep path: {cmd}")

        for n in (5, 50):
            subjects = {f"issue-{i}": {"implementation": {}} for i in range(1, n + 1)}
            with mock.patch.object(closure_sweep.subprocess, "run", side_effect=run_stub) as run:
                closure_sweep.find_violations(Path("."), subjects=subjects)
            self.assertEqual(run.call_count, 2)


class RateLimitGuard(unittest.TestCase):
    """issue #1320 requirement 3/acceptance (c): pre-sweep GraphQL
    rate-limit guard."""

    def test_remaining_parsed_from_rate_limit_api(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout=json.dumps(
                {"resources": {"graphql": {"remaining": 42}}}))
            remaining, ok = closure_sweep.rate_limit_remaining(Path("."))
        self.assertTrue(ok)
        self.assertEqual(remaining, 42)

    def test_gh_failure_yields_ok_false(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=1, stdout="")
            remaining, ok = closure_sweep.rate_limit_remaining(Path("."))
        self.assertFalse(ok)
        self.assertIsNone(remaining)

    def test_main_short_circuits_below_threshold(self):
        orig_rate_limit_remaining = closure_sweep.rate_limit_remaining
        closure_sweep.rate_limit_remaining = lambda root: (137, True)
        self.addCleanup(setattr, closure_sweep, "rate_limit_remaining", orig_rate_limit_remaining)
        orig_find_violations = closure_sweep.find_violations
        called = []
        closure_sweep.find_violations = lambda *a, **k: called.append(1)
        self.addCleanup(setattr, closure_sweep, "find_violations", orig_find_violations)

        argv = sys.argv
        sys.argv = ["closure_sweep.py"]
        self.addCleanup(setattr, sys, "argv", argv)

        buf = []
        with mock.patch("builtins.print", side_effect=lambda *a, **k: buf.append(" ".join(str(x) for x in a))):
            rc = closure_sweep.main()
        self.assertEqual(rc, 2)
        self.assertEqual(called, [])
        self.assertEqual(buf, ["[watchdog] board-sweep: 미집계 (rate-limit, remaining=137)"])

    def test_main_proceeds_when_above_threshold(self):
        orig_rate_limit_remaining = closure_sweep.rate_limit_remaining
        closure_sweep.rate_limit_remaining = lambda root: (5000, True)
        self.addCleanup(setattr, closure_sweep, "rate_limit_remaining", orig_rate_limit_remaining)
        orig_issue_state_index_all = closure_sweep.issue_state_index_all
        closure_sweep.issue_state_index_all = lambda root: ({}, True)
        self.addCleanup(setattr, closure_sweep, "issue_state_index_all",
                         orig_issue_state_index_all)
        orig_find_violations = closure_sweep.find_violations
        closure_sweep.find_violations = lambda root, subjects=None, issue_states=None: ([], [])
        self.addCleanup(setattr, closure_sweep, "find_violations", orig_find_violations)

        argv = sys.argv
        sys.argv = ["closure_sweep.py"]
        self.addCleanup(setattr, sys, "argv", argv)

        with mock.patch("builtins.print"):
            rc = closure_sweep.main()
        self.assertEqual(rc, 0)


class MainExitCode(unittest.TestCase):
    """issue #287 S1: gh 를 강제로 실패시키면 exit 0("위반 없음")도 exit
    1("위반 발견")도 아니라 exit 2("확인 불가")여야 한다."""

    def test_exit_code_is_2_and_prints_could_not_check(self):
        orig_find_violations = closure_sweep.find_violations
        closure_sweep.find_violations = lambda root, subjects=None, issue_states=None: (
            [], [{"subject": "issue-135", "reason": "gh-issue-view-failed"}])
        self.addCleanup(setattr, closure_sweep, "find_violations", orig_find_violations)

        orig_issue_state_index_all = closure_sweep.issue_state_index_all
        closure_sweep.issue_state_index_all = lambda root: (None, False)
        self.addCleanup(setattr, closure_sweep, "issue_state_index_all",
                         orig_issue_state_index_all)

        argv = sys.argv
        sys.argv = ["closure_sweep.py"]
        self.addCleanup(setattr, sys, "argv", argv)

        buf = []
        orig_print = __builtins__["print"] if isinstance(__builtins__, dict) else __builtins__.print
        with mock.patch("builtins.print", side_effect=lambda *a, **k: buf.append(" ".join(str(x) for x in a))):
            rc = closure_sweep.main()
        self.assertEqual(rc, 2)
        joined = "\n".join(buf)
        self.assertIn("확인 불가", joined)
        self.assertNotIn("위반 없음", joined)


class AccumulationTrend(unittest.TestCase):
    """issue #512 requirement 4: watchdog-tick advisory trend measurement."""

    def _repo(self, files):
        d = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        for path, content in files.items():
            f = d / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(content)
        subprocess.run(["git", "add", "-A"], cwd=d, check=True)
        subprocess.run(["git", "-c", "user.email=t@t.com", "-c", "user.name=t",
                        "commit", "-q", "-m", "init"], cwd=d, check=True)
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return d

    def test_empty_state_produces_valid_no_data_artifact(self):
        d = self._repo({"README.md": "hello\n"})
        trend = closure_sweep.accumulation_trend(d)
        self.assertFalse(trend["has_prior"])
        self.assertEqual(trend["current"], {"shape1_sites": 0, "shape5_files": 0})
        self.assertNotIn("delta", trend)
        report = closure_sweep.format_accumulation_trend(trend)
        self.assertIn("no prior tick data", report)

    def test_second_tick_reports_delta_against_first(self):
        d = self._repo({"README.md": "hello\n"})
        closure_sweep.accumulation_trend(d)
        (d / "roles").mkdir()
        (d / "roles" / "x.json").write_text("{}\n")
        subprocess.run(["git", "-C", str(d), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(d), "-c", "user.email=t@t.com",
                        "-c", "user.name=t", "commit", "-q", "-m", "add"], check=True)
        trend = closure_sweep.accumulation_trend(d)
        self.assertTrue(trend["has_prior"])
        self.assertEqual(trend["delta"]["shape5_files"], 1)
        report = closure_sweep.format_accumulation_trend(trend)
        self.assertIn("shape5_files=1", report)


if __name__ == "__main__":
    unittest.main()
