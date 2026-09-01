"""Issue #2978 acceptance: two watchdog checks were reporting a correct,
ordinary state as a violation.

  1. `spawn_on_pr.missing_verification()` printed a "deliverable branch
     not found in pr_index" line for a subject whose deliverable PR has
     never been opened yet -- the normal state of a freshly filed issue,
     not a mapping failure.
  2. `closure_sweep.find_violations()` flagged a record-only PR
     (independent-verification, conformance-review, ...) landing before
     or after the subject's real delivery PR as a closure violation --
     the ordinary landing order this system prescribes.

Both fixes are structural (issue #2978's own must-not: no issue age, time
window, or hardcoded issue-number cutoff):

  - spawn-on-pr: `subject_deliverable_record()` already tells apart "this
    subject's own deliverable record has landed to main" (its PR
    necessarily existed and merged at some point) from "no deliverable
    record landed yet" (only a verification-slot record put this subject
    on the board) -- reused as the no-PR-yet vs genuinely-missing
    discriminator.
  - closure-sweep: reuses issue #2974's own structural record-only test
    (`check_runner.touches_implementation_paths()` on the PR's diff) to
    tell a record-only PR apart from an actual delivery PR, instead of a
    branch name or issue age.

Test derivation (test-derivation skill, decision-table route): each
check is a 2x2 of (deliverable/delivery record already landed or not) x
(branch/PR found in the index or not) -- only the "not landed, not
found" and "landed-elsewhere-but-not-a-delivery, found" cells are new
empty states; the other cells are the pre-existing, already-tested
"genuine" behavior this issue must not silence.

  python3 -m pytest tests/test_watchdog_normal_state_not_violation_2978.py -q
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import spawn_on_pr  # noqa: E402
import closure_sweep  # noqa: E402


class SpawnOnPrNoPrYetIsNotReported(unittest.TestCase):
    """Acceptance 1: an issue with no PR yet is not reported as a
    branch-mapping failure."""

    def test_spawn_on_pr_no_pr_yet_prints_nothing_and_never_one_shot_marks(self):
        # This subject reached the board only because an independent
        # verification record already landed for it (`verifies_subject:
        # true`) -- its OWN deliverable has never had a PR opened, let
        # alone landed. `subject_deliverable_record()` therefore resolves
        # to (None, {}): no unique non-verifying record.
        subject = "issue-97001"
        board = {subject: {"independent-verification-1":
                            {"verifies_subject": "true", "author": "bob"}}}
        with mock.patch.object(spawn_on_pr.spawn, "board", lambda root: board), \
             mock.patch.object(
                 spawn_on_pr.spawn, "_watchdog_note_unmappable_subject_branch",
                 return_value=True) as marker:
            with mock.patch("builtins.print") as fake_print:
                out = spawn_on_pr.missing_verification(
                    Path("/tmp/does-not-matter"),
                    issue_states={97001: "OPEN"}, pr_index={})

        self.assertEqual(out, {})
        fake_print.assert_not_called()
        marker.assert_not_called()


class SpawnOnPrGenuinelyMissingBranchIsStillReported(unittest.TestCase):
    """Acceptance 2: a branch genuinely absent from `pr_index` after a PR
    exists for it is still reported."""

    def test_spawn_on_pr_genuinely_missing_branch_still_prints(self):
        # This subject's OWN deliverable record has already landed
        # (`implementation`, not self-declared as a verifying record) --
        # its PR necessarily existed and merged at some point, so its
        # absence from `pr_index` now is a genuine anomaly (e.g. #2379's
        # corrupted merge-base case), not "no PR yet".
        subject = "issue-97002"
        board = {subject: {"implementation": {"author": "alice"}}}
        with mock.patch.object(spawn_on_pr.spawn, "board", lambda root: board), \
             mock.patch.object(
                 spawn_on_pr.spawn, "_watchdog_note_unmappable_subject_branch",
                 return_value=True):
            with mock.patch("builtins.print") as fake_print:
                out = spawn_on_pr.missing_verification(
                    Path("/tmp/does-not-matter"),
                    issue_states={97002: "OPEN"}, pr_index={})

        self.assertEqual(out, {})
        printed = "\n".join(str(c.args[0]) for c in fake_print.call_args_list)
        self.assertIn(
            f"[spawn-on-pr] {subject}: deliverable 브랜치를 pr_index 에서 찾지 못했다",
            printed)


class ClosureSweepRecordAfterMergeIsNotAViolation(unittest.TestCase):
    """Acceptance 3: a record PR still open on an issue that GitHub
    auto-closed at implementation merge is not reported as a closure
    violation."""

    def test_closure_sweep_record_after_merge_produces_no_violation(self):
        subject = "issue-2827"
        skill = "independent-verification-1"
        pr_number = 2851
        subjects = {subject: {skill: {}}}
        issue_states = {2827: "CLOSED"}  # closed by the earlier implementation merge
        pr_index = {
            f"{subject}/{skill}": {
                "number": pr_number, "state": "OPEN",
                "body": "Verifies #2827 (independent verification round 1)",
            },
        }

        with mock.patch.object(closure_sweep.check_runner, "pr_diff_paths",
                                return_value=["docs/issue-2827/reports/"
                                              "independent-verification-1.md"]):
            violations, skips = closure_sweep.find_violations(
                Path("/tmp/does-not-matter"), subjects=subjects,
                issue_states=issue_states, pr_index=pr_index)

        self.assertEqual(violations, [])
        self.assertEqual(skips, [])


class ClosureSweepGenuineViolationIsStillReported(unittest.TestCase):
    """Acceptance 4: an issue genuinely left open with delivery merged
    and no record PR pending is still reported."""

    def test_closure_sweep_genuine_violation_still_reported(self):
        subject = "issue-3001"
        skill = "implementation"
        pr_number = 3050
        subjects = {subject: {skill: {}}}
        issue_states = {3001: "OPEN"}  # genuinely stuck open, not auto-closed
        pr_index = {
            f"{subject}/{skill}": {
                "number": pr_number, "state": "MERGED",
                "body": "Closes #3001",
            },
        }

        with mock.patch.object(closure_sweep.check_runner, "pr_diff_paths",
                                return_value=["gates/some_module.py",
                                              "docs/issue-3001/reports/"
                                              "implementation.md"]):
            violations, skips = closure_sweep.find_violations(
                Path("/tmp/does-not-matter"), subjects=subjects,
                issue_states=issue_states, pr_index=pr_index)

        self.assertEqual(violations, [{
            "issue": 3001, "pr": pr_number, "skill": skill,
            "kind": closure_sweep.MERGED_DELIVERY_ISSUE_OPEN,
        }])
        self.assertEqual(skips, [])


if __name__ == "__main__":
    unittest.main()
