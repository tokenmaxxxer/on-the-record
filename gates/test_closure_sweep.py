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
import state_paths


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
        {5, 50}. issue #1554: `issue_state_index_all` probes the repo slug
        once (`gh repo view`, cached process-wide by `spawn._repo_slug`) and
        uses it for an ETag-conditional issue list; issue #1702:
        `_pr_index_all` now shares that same cached slug for its own
        `gh api .../pulls` pagination instead of calling `gh pr list`
        directly — both index builders resolve the slug once per process,
        so a single-page issue list + single-page pr list still costs
        exactly 3 calls total (repo view, issues page, pulls page); the
        slug cache is cleared each iteration so both N=5 and N=50 see the
        same probe."""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import spawn

        def run_stub(cmd, cwd=None, capture_output=None, text=None):
            if cmd[:3] == ["gh", "repo", "view"]:
                return mock.Mock(returncode=0, stdout="owner/repo\n", stderr="")
            if cmd[:3] == ["gh", "api", "repos/owner/repo/issues"]:
                headers = "\n".join(["HTTP/2.0 200", ""])
                body = json.dumps(
                    [{"number": n, "state": "OPEN"} for n in range(1, 51)])
                return mock.Mock(returncode=0, stdout=f"{headers}\n{body}")
            if cmd[:3] == ["gh", "api", "repos/owner/repo/pulls"]:
                return mock.Mock(returncode=0, stdout=json.dumps([]))
            raise AssertionError(f"unexpected gh call in sweep path: {cmd}")

        for n in (5, 50):
            spawn._repo_slug_cache_clear()
            subjects = {f"issue-{i}": {"implementation": {}} for i in range(1, n + 1)}
            with mock.patch.object(closure_sweep.subprocess, "run", side_effect=run_stub) as run:
                closure_sweep.find_violations(Path("."), subjects=subjects)
            self.assertEqual(run.call_count, 3)


class OutOfIndexSubjectIsNotAGhFailureSkip(unittest.TestCase):
    """issue #1613: a subject whose issue number is not present in a
    *successfully*-fetched issue-state index (e.g. it belongs to another
    repo) must not be reported as a `gh 실패` skip — only an actual `gh`
    call failure earns that reason.

    issue #1643: it also must not be silently `continue`d forever — it is
    classified ONCE as out-of-scope with a distinct reason (not a
    per-tick skip, not silence), and a subsequent tick does not repeat
    it. Each test uses its own tmpdir as `root` since the one-time
    classification is now tracked in local state under `root/runs/`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_subject_missing_from_successful_index_is_not_a_gh_failure_skip(self):
        subjects = {"issue-9999": {"implementation": {}}}
        violations, skips = closure_sweep.find_violations(
            self.root, subjects=subjects, issue_states={135: "OPEN"})
        self.assertEqual(skips, [])
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["kind"], closure_sweep.OUT_OF_INDEX_SUBJECT)
        self.assertEqual(violations[0]["subject"], "issue-9999")
        self.assertEqual(violations[0]["issue"], 9999)

    def test_subsequent_tick_does_not_repeat_the_classification(self):
        subjects = {"issue-9999": {"implementation": {}}}
        first, _ = closure_sweep.find_violations(
            self.root, subjects=subjects, issue_states={135: "OPEN"})
        second, skips = closure_sweep.find_violations(
            self.root, subjects=subjects, issue_states={135: "OPEN"})
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(skips, [])

    def test_mixed_board_only_flags_the_unresolved_ones(self):
        subjects = {"issue-135": {"implementation": {}},
                    "issue-9999": {"implementation": {}}}
        orig_pr_index_all = closure_sweep._pr_index_all
        closure_sweep._pr_index_all = lambda root: ({}, True)
        try:
            violations, skips = closure_sweep.find_violations(
                self.root, subjects=subjects, issue_states={135: "OPEN"})
        finally:
            closure_sweep._pr_index_all = orig_pr_index_all
        self.assertEqual([s["subject"] for s in skips], [])
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["subject"], "issue-9999")
        self.assertEqual(violations[0]["kind"], closure_sweep.OUT_OF_INDEX_SUBJECT)

    def test_all_in_index_board_is_byte_identical_to_no_out_of_scope_entries(self):
        """acceptance empty-state: boards with all subjects in-index keep
        today's behavior — no out-of-scope entries, no state file
        written."""
        subjects = {"issue-135": {"implementation": {}}}
        orig_pr_index_all = closure_sweep._pr_index_all
        closure_sweep._pr_index_all = lambda root: ({}, True)
        try:
            violations, skips = closure_sweep.find_violations(
                self.root, subjects=subjects, issue_states={135: "OPEN"})
        finally:
            closure_sweep._pr_index_all = orig_pr_index_all
        self.assertEqual(violations, [])
        self.assertEqual(skips, [])
        # issue #2240: this state is orchestrator-scoped now, not
        # `self.root`-scoped — assert against the real accessor.
        self.assertFalse(state_paths.orchestrator_state_path(
            closure_sweep.OUT_OF_INDEX_SEEN_STATE_FILENAME).exists())


class PrIndexAllPagination(unittest.TestCase):
    """issue #1702: `_pr_index_all` must page through `gh api .../pulls`
    instead of a single `--limit`-bounded `gh pr list` call, so a repo with
    more PRs than the old 1000-item limit still returns a complete index."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.addCleanup(closure_sweep.spawn._repo_slug_cache_clear)

    def _pr(self, n, merged=False):
        return {"number": n, "head": {"ref": f"branch-{n}"},
                "state": "closed" if merged else "open",
                "merged_at": "2026-01-01T00:00:00Z" if merged else None,
                "body": f"body-{n}"}

    def test_pagination_fixture_returns_complete_index_over_1000_prs(self):
        """mocked >1000-PR listing across multiple pages: asserts multiple
        page calls happened and the full entry count came back."""
        total = 1250
        prs = [self._pr(n) for n in range(1, total + 1)]
        pages = [prs[i:i + 100] for i in range(0, len(prs), 100)]

        def run_stub(cmd, cwd=None, capture_output=None, text=None):
            if cmd[:3] == ["gh", "repo", "view"]:
                return mock.Mock(returncode=0, stdout="owner/repo\n")
            if cmd[:3] == ["gh", "api", "repos/owner/repo/pulls"]:
                page_arg = [a for a in cmd if a.startswith("page=")][0]
                page = int(page_arg.split("=")[1])
                data = pages[page - 1] if 1 <= page <= len(pages) else []
                return mock.Mock(returncode=0, stdout=json.dumps(data))
            raise AssertionError(f"unexpected call: {cmd}")

        with mock.patch.object(closure_sweep.subprocess, "run", side_effect=run_stub) as run:
            index, ok = closure_sweep._pr_index_all(self.root)

        self.assertTrue(ok)
        self.assertIsNotNone(index)
        self.assertEqual(len(index), total)
        page_calls = [c for c in run.call_args_list
                      if c.args[0][:3] == ["gh", "api", "repos/owner/repo/pulls"]]
        self.assertEqual(len(page_calls), len(pages))
        self.assertGreater(len(page_calls), 1)

    def test_repos_under_1000_prs_still_make_one_page_call(self):
        def run_stub(cmd, cwd=None, capture_output=None, text=None):
            if cmd[:3] == ["gh", "repo", "view"]:
                return mock.Mock(returncode=0, stdout="owner/repo\n")
            if cmd[:3] == ["gh", "api", "repos/owner/repo/pulls"]:
                return mock.Mock(returncode=0, stdout=json.dumps(
                    [self._pr(n) for n in range(1, 6)]))
            raise AssertionError(f"unexpected call: {cmd}")

        with mock.patch.object(closure_sweep.subprocess, "run", side_effect=run_stub) as run:
            index, ok = closure_sweep._pr_index_all(self.root)

        self.assertTrue(ok)
        self.assertEqual(len(index), 5)
        page_calls = [c for c in run.call_args_list
                      if c.args[0][:3] == ["gh", "api", "repos/owner/repo/pulls"]]
        self.assertEqual(len(page_calls), 1)

    def test_merged_state_reconstructed_from_merged_at(self):
        def run_stub(cmd, cwd=None, capture_output=None, text=None):
            if cmd[:3] == ["gh", "repo", "view"]:
                return mock.Mock(returncode=0, stdout="owner/repo\n")
            if cmd[:3] == ["gh", "api", "repos/owner/repo/pulls"]:
                return mock.Mock(returncode=0, stdout=json.dumps(
                    [self._pr(1, merged=True), self._pr(2, merged=False)]))
            raise AssertionError(f"unexpected call: {cmd}")

        with mock.patch.object(closure_sweep.subprocess, "run", side_effect=run_stub):
            index, ok = closure_sweep._pr_index_all(self.root)

        self.assertTrue(ok)
        self.assertEqual(index["branch-1"]["state"], "MERGED")
        self.assertEqual(index["branch-2"]["state"], "OPEN")

    def test_exact_saturation_of_safety_ceiling_still_returns_none_true(self):
        """exact-saturation-of-final-safety-ceiling still returns
        (None, True) — same truncation-safe contract as the old
        `--limit`-hit case, just at the new, much higher ceiling."""
        ceiling = closure_sweep._PR_INDEX_SAFETY_CEILING
        per_page = closure_sweep._PR_INDEX_PER_PAGE
        full_pages, remainder = divmod(ceiling, per_page)

        def run_stub(cmd, cwd=None, capture_output=None, text=None):
            if cmd[:3] == ["gh", "repo", "view"]:
                return mock.Mock(returncode=0, stdout="owner/repo\n")
            if cmd[:3] == ["gh", "api", "repos/owner/repo/pulls"]:
                page_arg = [a for a in cmd if a.startswith("page=")][0]
                page = int(page_arg.split("=")[1])
                if page <= full_pages:
                    data = [self._pr(page * per_page + i) for i in range(per_page)]
                elif page == full_pages + 1 and remainder:
                    data = [self._pr(ceiling + i) for i in range(remainder)]
                else:
                    data = [self._pr(ceiling + per_page + i) for i in range(per_page)]
                return mock.Mock(returncode=0, stdout=json.dumps(data))
            raise AssertionError(f"unexpected call: {cmd}")

        with mock.patch.object(closure_sweep.subprocess, "run", side_effect=run_stub):
            index, ok = closure_sweep._pr_index_all(self.root)

        self.assertIsNone(index)
        self.assertTrue(ok)

    def test_gh_call_failure_yields_ok_false(self):
        def run_stub(cmd, cwd=None, capture_output=None, text=None):
            if cmd[:3] == ["gh", "repo", "view"]:
                return mock.Mock(returncode=0, stdout="owner/repo\n")
            return mock.Mock(returncode=1, stdout="")

        with mock.patch.object(closure_sweep.subprocess, "run", side_effect=run_stub):
            index, ok = closure_sweep._pr_index_all(self.root)

        self.assertIsNone(index)
        self.assertFalse(ok)

    def test_unresolvable_slug_yields_ok_false(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="")
            index, ok = closure_sweep._pr_index_all(self.root)
        self.assertIsNone(index)
        self.assertFalse(ok)


class ConditionalIssueListUsesExplicitGetMethod(unittest.TestCase):
    """issue #1613 root cause: `gh api ... -f k=v` defaults to POST unless
    `--method GET` is explicit (gh's own documented behavior) — that
    silent POST is what turned every `issue_state_index_all` call into a
    422 failure, which cascaded into every subject on the board being
    reported as a permanent `gh-issue-list-failed` skip, not just
    cross-repo ones. This pins the fix: the conditional list call always
    states its method explicitly."""

    def test_cmd_carries_explicit_method_get(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=1, stdout="", stderr="")
            closure_sweep._conditional_issue_list(
                Path("."), "owner/repo", Path("/tmp/nonexistent-cache.json"))
        cmd = run.call_args.args[0]
        self.assertIn("--method", cmd)
        self.assertEqual(cmd[cmd.index("--method") + 1], "GET")


class OneTickOneSweep(unittest.TestCase):
    """issue #1320 requirement 2/acceptance (d): one tick triggers
    exactly one board-wide sweep — guards spawn.py's watchdog wiring
    against re-invoking closure_sweep/spawn_coverage 2-4x per tick."""

    def test_roster_watchdog_triggers_board_wide_sweep_exactly_once(self):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import spawn
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "docs" / "specs" / "approvers.md").write_text("someone\n")
            (root / "runs").mkdir()
            with mock.patch.object(spawn, "ROSTER", root / "runs" / "roster.json"), \
                 mock.patch.object(spawn, "_board_wide_sweep", return_value=0) as m:
                spawn.roster_watchdog(root=root)
            self.assertEqual(m.call_count, 1)


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
