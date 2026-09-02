"""Issue #3050, acceptance check 3: a session that had in fact pushed was
classified `failed-no-commit`, and an orchestrator that trusts that
classification respawned onto the same, already-corrected unit (issue
timeline: 10:28 corrects+pushes, PR head moves; 10:38 a second session is
spawned onto the same unit; the harness's own `[flapping]` watchdog only
named the contradiction ten minutes later, after the respawn had already
fired).

`board.fail_closed_downgrade()`'s pre-fix `progressed` branch trusted only
the local before/after HEAD diff (`new_commit`) to decide `failed-no-commit`
-- `push_succeeded` (a real remote check: `ensure_pushed()` diffs the
branch against `origin/<branch>` before deciding whether to push at all)
was already threaded through as a parameter but never consulted in that
branch. Must-not clause (issue #3050): the fix may not make the classifier
trust the session's own success claim (issue #2667's recorded failure
mode) -- `push_succeeded` is not a claim, it is `ensure_pushed()`'s
observed remote outcome, structurally the same kind of signal
`_unrecovered_commit_count()`/`_remote_branch_head()` (issue #2795) already
use to reconcile against `origin/<branch>` elsewhere in this module.

Test derivation (test-derivation skill, decision-table route): the branch
under test in `fail_closed_downgrade()` when `outcome == "progressed"` and
`issue is not None` and `blocked` is empty is a decision over four
conditions (new_commit, uncommitted, already_delivered, push_succeeded).
Feasible columns actually reachable through that branch (blocked/outcome
already dispatched away above it) are enumerated below; `reconcile_disagreement()`
is exercised as an equivalence partition over the same input shape (the
one case it must flag True, its immediate neighbors that must stay False).

Repair round (PR #3086 held, PR #3108's confirmed-and-reproduced finding):
every decision-table case above hand-supplies `push_succeeded` as a
literal `True`/`False`, so the property was never exercised by the code
that actually computes it -- `spawn.py`'s `push_succeeded = push_result is
not None and push_result["status"] not in (...)` derivation from
`ensure_pushed()`'s real result. `ensure_pushed()`'s `"nothing-to-push"`
status (session made zero commits, its role branch never existed locally)
was missing from that exclusion tuple, so a session that pushed nothing
was classified as having pushed successfully -- must-not B's forbidden
shape (the classifier trusting a self-report instead of the remote
check), reproduced independently against real code in PR #3108's record.
`PushSucceededDerivationLiveTest` below closes that gap: it calls the real
`spawn.ensure_pushed()` against scratch git repos (never a hand-typed
`push_result` dict) and the real `spawn._push_succeeded()` derivation,
feeding only what those real calls returned into `fail_closed_downgrade()`.

  python3 -m pytest tests/test_failed_no_commit_reconcile.py -q
"""
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import board  # noqa: E402
import spawn  # noqa: E402


class FailClosedDowngradeReconcileTest(unittest.TestCase):
    """Decision table over (new_commit, uncommitted, already_delivered,
    push_succeeded), outcome='progressed', issue=1, blocked=[]."""

    def test_new_commit_true_regression_unchanged(self):
        # Baseline: local diff already agrees -- untouched by this fix.
        self.assertEqual(
            board.fail_closed_downgrade("progressed", 1, [], True, [], False, True),
            "progressed")

    def test_local_diff_missed_it_but_remote_confirms_pushed(self):
        # The story case: session committed+pushed, local before/after HEAD
        # diff came back false anyway. Must NOT be failed-no-commit.
        result = board.fail_closed_downgrade("progressed", 1, [], False, [], False, True)
        self.assertNotEqual(result, "failed-no-commit")
        self.assertEqual(result, "progressed")

    def test_genuine_failure_no_commit_no_push_stays_failed(self):
        # Both signals agree on failure -- the fix must not paper over a
        # real failed-no-commit.
        self.assertEqual(
            board.fail_closed_downgrade("progressed", 1, [], False, [], False, False),
            "failed-no-commit")

    def test_uncommitted_work_fails_regardless_of_push_succeeded(self):
        # Dirty tree is never safe -- "already delivered" doesn't mean
        # this session's own new, uncommitted changes are safe either
        # (documented invariant this fix must not weaken).
        self.assertEqual(
            board.fail_closed_downgrade("progressed", 1, [], False, ["M x"], False, True),
            "failed-no-commit")

    def test_new_commit_and_uncommitted_stays_dirty_tree_regardless_of_push(self):
        self.assertEqual(
            board.fail_closed_downgrade("progressed", 1, [], True, ["M x"], False, True),
            "progressed-dirty-tree")
        self.assertEqual(
            board.fail_closed_downgrade("progressed", 1, [], True, ["M x"], False, False),
            "progressed-dirty-tree")

    def test_already_delivered_unaffected_by_push_succeeded_false(self):
        # Pre-existing branch (issue #129), unrelated to this fix -- pin
        # to catch accidental interaction with the new push_succeeded check.
        self.assertEqual(
            board.fail_closed_downgrade("progressed", 1, [], False, [], True, False),
            "progressed")

    def test_blocked_short_circuits_before_reconciliation(self):
        self.assertEqual(
            board.fail_closed_downgrade("progressed", 1, ["a"], False, [], False, True),
            "progressed")

    def test_non_progressed_outcome_passthrough_unaffected(self):
        self.assertEqual(
            board.fail_closed_downgrade("crashed", 1, [], False, [], False, True),
            "crashed")

    def test_silent_failure_branch_unaffected_regression_pin(self):
        # Different branch of the function entirely (issue #484) -- pinned
        # so this fix is verifiably scoped to the progressed/failed-no-commit
        # branch only.
        self.assertEqual(
            board.fail_closed_downgrade("silent-failure", 1, [], True, [], False, True),
            "progressed")


class ReconcileDisagreementTest(unittest.TestCase):
    """`reconcile_disagreement()` names exactly the case where remote
    reconciliation is what kept the outcome from downgrading -- the signal
    `[reconcile-poll-disagreement]` needs at decision time, not ten minutes
    later from the watchdog."""

    def test_flags_the_story_case(self):
        self.assertTrue(
            board.reconcile_disagreement("progressed", 1, [], False, [], False, True))

    def test_does_not_flag_when_local_diff_already_agrees(self):
        self.assertFalse(
            board.reconcile_disagreement("progressed", 1, [], True, [], False, True))

    def test_does_not_flag_when_push_also_failed(self):
        self.assertFalse(
            board.reconcile_disagreement("progressed", 1, [], False, [], False, False))

    def test_does_not_flag_with_uncommitted_work(self):
        self.assertFalse(
            board.reconcile_disagreement("progressed", 1, [], False, ["M x"], False, True))

    def test_does_not_flag_when_already_delivered(self):
        self.assertFalse(
            board.reconcile_disagreement("progressed", 1, [], False, [], True, True))

    def test_does_not_flag_when_blocked(self):
        self.assertFalse(
            board.reconcile_disagreement("progressed", 1, ["a"], False, [], False, True))

    def test_does_not_flag_non_progressed_outcome(self):
        self.assertFalse(
            board.reconcile_disagreement("silent-failure", 1, [], False, [], False, True))

    def test_does_not_flag_without_issue(self):
        self.assertFalse(
            board.reconcile_disagreement("progressed", None, [], False, [], False, True))


class PushSucceededDerivationLiveTest(unittest.TestCase):
    """Reaches `push_succeeded` through `spawn.py`'s real code, not around
    it: a real bare-origin + clone, a real `spawn.ensure_pushed()` call,
    the real `spawn._push_succeeded()` derivation, and only then
    `board.fail_closed_downgrade()`. No test in this class hand-supplies
    `push_succeeded` as a literal boolean."""

    FAKE_GH = """#!/usr/bin/env python3
import sys
argv = sys.argv[1:]
if argv[:3] == ["pr", "list", "--head"]:
    print("0")
elif argv[:2] == ["pr", "create"]:
    print("https://github.com/example/repo/pull/1")
else:
    sys.exit(1)
"""

    def _write_fake_gh(self, bin_dir: Path):
        p = bin_dir / "gh"
        p.write_text(self.FAKE_GH)
        p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def _bare_and_clone(self, tmp: Path):
        origin = tmp / "origin.git"
        work = tmp / "work"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True)
        subprocess.run(["git", "-C", str(work), "config", "user.email", "t@example.com"], check=True)
        subprocess.run(["git", "-C", str(work), "config", "user.name", "t"], check=True)
        return origin, work

    def test_zero_commits_role_branch_never_created_reconciles_to_failed_no_commit(self):
        # The story case, reconstructed live: a session that committed and
        # pushed nothing at all -- its role branch `issue-<n>/<skill>` was
        # never created locally, so `ensure_pushed()`'s own
        # `git rev-parse --verify -q <role-branch>` fails before any
        # network call. This must reconcile the same way local and remote
        # signals agreeing on failure already do -- not the story case
        # from the issue (which pushed something real).
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            _, work = self._bare_and_clone(tmp)
            # No commit, no checkout of issue-30501/coding -- work sits on
            # whatever empty default branch `git clone` left it on.

            push_result = spawn.ensure_pushed(str(work), 30501, "coding")
            self.assertEqual(push_result["status"], "nothing-to-push", push_result)

            push_succeeded = spawn._push_succeeded(push_result)
            self.assertFalse(push_succeeded, push_result)

            outcome = board.fail_closed_downgrade(
                "progressed", 30501, [], False, [], False, push_succeeded)
            self.assertEqual(outcome, "failed-no-commit")

    def test_genuine_push_and_pr_open_reconciles_to_progressed(self):
        # Regression pin, same real path: a session that actually
        # committed+pushed must still reconcile to `progressed` -- the fix
        # narrows what counts as success, it must not narrow it to nothing.
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            bin_dir = tmp / "bin"
            bin_dir.mkdir()
            self._write_fake_gh(bin_dir)
            _, work = self._bare_and_clone(tmp)
            subprocess.run(["git", "-C", str(work), "checkout", "-q", "-b",
                            "issue-30502/coding"], check=True)
            (work / "f.txt").write_text("x")
            subprocess.run(["git", "-C", str(work), "add", "f.txt"], check=True)
            subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "work"], check=True)

            orig_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}:{orig_path}"
            try:
                push_result = spawn.ensure_pushed(str(work), 30502, "coding")
            finally:
                os.environ["PATH"] = orig_path

            self.assertEqual(push_result["status"], "pr-opened", push_result)

            push_succeeded = spawn._push_succeeded(push_result)
            self.assertTrue(push_succeeded, push_result)

            outcome = board.fail_closed_downgrade(
                "progressed", 30502, [], False, [], False, push_succeeded)
            self.assertEqual(outcome, "progressed")


if __name__ == "__main__":
    unittest.main()
