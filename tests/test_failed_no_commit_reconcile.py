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

  python3 -m pytest tests/test_failed_no_commit_reconcile.py -q
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import board  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
