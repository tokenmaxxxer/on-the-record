"""Issue #2941: reconcile() and the absorbed-branch recut both read
"not yet appeared" as "gone".

Site 1 (reconcile): `_build_observed()` fed the individual, `--head`-
filtered `gh pr list` lookup (`_pr_open_or_merged_for_branch()`) into
`reconcile()`. That lookup and the poll-report path's board-index lookup
(`_pr_state_from_index()`, fed by `_board_pr_index()`) are two different
data sources reachable at two different moments -- the exact split issue
#2874's own after-proposal hunt used to construct a reconcile/poll-report
disagreement (adversarial-review-5200fcf2.md item 8), and the shape the
issue's 43 `[reconcile-poll-disagreement]` firings and four confirmed
individual PRs (#2930, #2934, #2937, #2919) matched. The fix threads the
same shared `pr_index` poll-report already trusts into `_build_observed()`
so both paths read one source instead of two.

Site 2 (absorbed-branch recut): `_recut_absorbed_branch()`'s `local_zero`
branch ("0 commits ahead of base") read as "absorbed into base" with no
distinction from "just created, nothing committed yet" -- the exact shape
that deleted the local branch of two live, working sessions
(issue-2920/adversarial-review-2a32a671, issue-2925/independent-
verification-1) after a watchdog-observed-crashed misfire respawned them.
The fix reads the local ref's own reflog creation time and treats a ref
younger than `SPAWN_ATTEMPT_GRACE_SEC` (300s, roster.py -- an existing,
already-justified constant, not a new guess) as "not yet", never
recutting it; a ref older than that grace window still recuts exactly as
before -- issue #732's guarantee (an absorbed branch must not block a
workspace from reopening a PR) is unaffected for genuinely old branches.

Both cases below are constructed live against the real functions (real
git repos, real reflogs, real `_build_observed`/`reconcile`) -- no stub of
either function under test, per the issue's own evidentiary bar
(adversarial-review-5200fcf2.md item 8's convention).
"""
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402
import watchdog  # noqa: E402

watchdog._sp = spawn


def _git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a],
                           capture_output=True, text=True, check=True)


class RecutNotYetVsGoneTest(unittest.TestCase):
    """Site 2: construct a freshly-started branch and a genuinely absorbed
    branch against the real `_recut_absorbed_branch()`, show they now
    produce different outcomes."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        self.remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        self.work = self.tmp / "work"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.work)], check=True)
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        (self.work / "a.txt").write_text("1")
        _git(self.work, "add", "a.txt")
        _git(self.work, "commit", "-q", "-m", "c1")
        _git(self.work, "branch", "-m", "main")
        _git(self.work, "push", "-q", "-u", "origin", "main")
        self.branch = "issue-2941/demo"

    def _advance_base(self):
        # Push a second commit to origin/main from a second clone, so
        # `_base()` (origin/HEAD) has moved past where `self.branch` sits
        # -- a recut is now observable as a SHA change, not a no-op that
        # happens to land on the same commit.
        other = self.tmp / "other-clone"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(other)], check=True)
        _git(other, "config", "user.email", "t@example.com")
        _git(other, "config", "user.name", "t")
        _git(other, "checkout", "main")
        (other / "b.txt").write_text("2")
        _git(other, "add", "b.txt")
        _git(other, "commit", "-q", "-m", "c2-advances-base")
        _git(other, "push", "-q", "origin", "main")
        _git(self.work, "fetch", "-q", "origin")

    def test_freshly_started_branch_is_not_recut(self):
        # Case A: a session was just spawned onto `self.branch` -- 0
        # commits ahead of base, same shape a genuinely absorbed branch
        # has. Meanwhile base moved on (another PR merged to main) while
        # this session was still in its first moments, exactly like the
        # issue's two respawned sessions. Only the ref's own age tells
        # this apart from Case B below.
        _git(self.work, "checkout", "-b", self.branch)
        before = _git(self.work, "rev-parse", self.branch).stdout.strip()
        self._advance_base()
        result = spawn._recut_absorbed_branch(str(self.work), self.branch)
        self.assertEqual(result.returncode, 0)
        after = _git(self.work, "rev-parse", self.branch).stdout.strip()
        self.assertEqual(before, after,
                          "a branch created moments ago must not be recut, "
                          "even though base has since moved past it")

    def test_genuinely_absorbed_branch_is_still_recut(self):
        # Case B: the identical 0-ahead-of-base shape, but the branch is
        # old -- fake its age past the grace window the same way a branch
        # that has genuinely sat absorbed for a while would read.
        _git(self.work, "checkout", "-b", self.branch)
        old_sha = _git(self.work, "rev-parse", self.branch).stdout.strip()
        self._advance_base()
        base_tip = _git(self.work, "rev-parse", "origin/main").stdout.strip()
        future = time.time() + spawn.SPAWN_ATTEMPT_GRACE_SEC + 60
        with mock.patch.object(spawn, "time") as mock_time:
            mock_time.time.return_value = future
            result = spawn._recut_absorbed_branch(str(self.work), self.branch)
        self.assertEqual(result.returncode, 0)
        new_sha = _git(self.work, "rev-parse", self.branch).stdout.strip()
        self.assertNotEqual(old_sha, new_sha,
                             "a genuinely old, absorbed branch must still be recut")
        self.assertEqual(new_sha, base_tip)

    def test_construction_actually_differs(self):
        # The two cases above must not silently converge -- prove the
        # "not yet" branch is reachable at all by checking the guard
        # itself reports a young age for a fresh branch and an old one
        # for a branch whose creation is pushed into the past via the
        # same time-mock the genuinely-absorbed case uses.
        _git(self.work, "checkout", "-b", self.branch)
        fresh_age = spawn._branch_created_age_sec(str(self.work), self.branch)
        self.assertIsNotNone(fresh_age)
        self.assertLess(fresh_age, spawn.SPAWN_ATTEMPT_GRACE_SEC)
        old_age = spawn._branch_created_age_sec(
            str(self.work), self.branch,
            now=time.time() + spawn.SPAWN_ATTEMPT_GRACE_SEC + 60)
        self.assertGreaterEqual(old_age, spawn.SPAWN_ATTEMPT_GRACE_SEC)


class ReconcilePrIndexConsistencyTest(unittest.TestCase):
    """Site 1: `_build_observed()` must read the same PR-existence signal
    poll-report's `diagnose_health()` already trusts, instead of a second,
    independently-lagging `gh pr list --head` call."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        self.remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        self.work = self.tmp / "work"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.work)], check=True)
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        (self.work / "a.txt").write_text("1")
        _git(self.work, "add", "a.txt")
        _git(self.work, "commit", "-q", "-m", "c1")
        _git(self.work, "branch", "-m", "issue-2941/demo")
        _git(self.work, "push", "-q", "-u", "origin", "issue-2941/demo")
        self.entry = {"pid": 999999999, "work": str(self.work),
                      "before_head": _git(self.work, "rev-parse", "HEAD").stdout.strip(),
                      "log": None, "issue": 2941, "skill": "demo", "expects_pr": True}

    def test_without_index_uses_the_laggy_live_call(self):
        # Today's behavior, unchanged when no shared index is supplied
        # (CLI call sites that never race a poll-report on the same tick).
        with mock.patch.object(spawn, "_pr_open_or_merged_for_branch",
                                return_value=None) as mocked:
            observed = spawn._build_observed(self.tmp, self.entry)
        mocked.assert_called_once()
        self.assertIsNone(observed["pr_number"])

    def test_with_index_reads_the_same_source_as_poll_report(self):
        # Simulate exactly the reported failure moment: GitHub's
        # `--head`-filtered search index has not caught up yet (the live
        # call would return None), but the PR already exists and the
        # board-derived bulk index (poll-report's own source) already has
        # it. With the shared index wired through, reconcile now agrees.
        pr_index = {"issue-2941/demo": {"number": 2942, "state": "OPEN"}}
        with mock.patch.object(spawn, "_pr_open_or_merged_for_branch",
                                return_value=None) as mocked:
            observed = spawn._build_observed(self.tmp, self.entry, pr_index=pr_index)
        mocked.assert_not_called()
        self.assertEqual(observed["pr_number"], 2942)

    def test_no_more_pr_expected_missing_when_index_already_has_it(self):
        pr_index = {"issue-2941/demo": {"number": 2942, "state": "OPEN"}}
        with mock.patch.object(spawn, "_pr_open_or_merged_for_branch",
                                return_value=None):
            observed = spawn._build_observed(self.tmp, self.entry, pr_index=pr_index)
        divergences = spawn.reconcile(spawn._build_expected(self.entry), observed)
        self.assertEqual(divergences, [],
                          "the two sources agree now -- no pr-expected-missing")

    def test_still_flags_a_real_missing_pr(self):
        # must-not: this must not silently resolve every disagreement --
        # a branch genuinely missing from both sources must still fire.
        pr_index = {}
        with mock.patch.object(spawn, "_pr_open_or_merged_for_branch",
                                return_value=None) as mocked:
            observed = spawn._build_observed(self.tmp, self.entry, pr_index=pr_index)
        mocked.assert_not_called()
        divergences = spawn.reconcile(spawn._build_expected(self.entry), observed)
        kinds = [d["kind"] for d in divergences]
        self.assertIn("pr-expected-missing", kinds)


if __name__ == "__main__":
    unittest.main()
