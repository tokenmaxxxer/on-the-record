"""Issue #2979 acceptance:
  - check: board_sweep_non_subject_aggregated
  - check: board_sweep_subject_mapping_loss_reported
  - check: spawn_coverage_reports_change

Test derivation (test-derivation skill). Both board-sweep checks share one
underlying decision table over `watchdog._classify_narrowing_prs`:

  C1: branch matches `issue-<n>/<skill>` shape (board-subject-shaped)?
  C2: (only meaningful when C1=Y) is that issue currently a board subject?

  | C1  | C2  | outcome                                              |
  |-----|-----|-------------------------------------------------------|
  | N   | n/a | non-subject -> aggregate count only, never individual |
  | Y   | Y   | normal mapping -> folded into changed_numbers, silent |
  | Y   | N   | subject mapping loss -> individual line + remediation |

3 feasible columns, all exercised below (100% decision-table coverage).
The C1=N branch is additionally split into two equivalence-partition
members of "branch never shaped" (a real but wrongly-shaped branch, and no
branch at all / PR deleted) since both must fold into the same bucket.

The one-shot repeat-suppression dimension for the C1=Y/C2=N outcome is a
2-state model (not-yet-reported -> reported) exercised with all-transitions
coverage: first-observe (state change, individual line) and
second-observe-unchanged (self-transition, suppressed to a count).

spawn_coverage_reports_change routes to a second decision table over
`watchdog._watchdog_note_spawn_coverage_delta`:

  D1: issue was in the previous tick's uncovered set?
  D2: issue is in the current tick's uncovered set?

  | D1  | D2  | outcome                                    |
  |-----|-----|---------------------------------------------|
  | N   | Y   | newly uncovered -> reported                |
  | Y   | Y   | standing uncovered -> not reported (again) |
  | Y   | N   | became covered -> dropped, not reported     |

All 3 meaningful columns exercised (D1=N/D2=N is a no-op, not a signal).
Empty-state acceptance note ("an unchanged set reports no new entries;
passes") is the D1=Y/D2=Y case.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "gates"))

import spawn  # noqa: E402
import watchdog  # noqa: E402
import state_paths  # noqa: E402

watchdog._sp = spawn


class BoardSweepNonSubjectAggregatedTest(unittest.TestCase):
    """check: board_sweep_non_subject_aggregated"""

    def test_board_sweep_non_subject_aggregated_never_shaped_branch(self):
        # C1=N: branch is a real branch but never issue-<n>/<skill> shaped.
        (changed, non_subject, loss_new, loss_repeat) = watchdog._classify_narrowing_prs(
            Path("/nonexistent"), {7}, {7: "fix/verify-plugins-actually-loaded"}, {})
        self.assertEqual(changed, set())
        self.assertEqual(non_subject, 1)
        self.assertEqual(loss_new, [])
        self.assertEqual(loss_repeat, 0)

    def test_board_sweep_non_subject_aggregated_deleted_branch_none(self):
        # C1=N, equivalence-partition member 2: no branch at all (PR
        # missing from pr_index -- number_to_branch.get returns None).
        (changed, non_subject, loss_new, loss_repeat) = watchdog._classify_narrowing_prs(
            Path("/nonexistent"), {1985}, {}, {})
        self.assertEqual(changed, set())
        self.assertEqual(non_subject, 1)
        self.assertEqual(loss_new, [])

    def test_board_sweep_non_subject_aggregated_multiple_prs_fold_into_count(self):
        pr_numbers = {1, 7, 26, 1985}
        branches = {1: "fix/verify-plugins-actually-loaded",
                    7: "plan/state-gate-into-core",
                    26: "docs/readme-refresh",
                    1985: None}
        (changed, non_subject, loss_new, loss_repeat) = watchdog._classify_narrowing_prs(
            Path("/nonexistent"), pr_numbers, branches, {})
        self.assertEqual(changed, set())
        self.assertEqual(non_subject, 4)
        self.assertEqual(loss_new, [])

    def test_board_sweep_non_subject_aggregated_empty_state_reports_nothing(self):
        (changed, non_subject, loss_new, loss_repeat) = watchdog._classify_narrowing_prs(
            Path("/nonexistent"), set(), {}, {})
        self.assertEqual(non_subject, 0)
        self.assertEqual(loss_new, [])
        self.assertEqual(loss_repeat, 0)
        # non_subject_count == 0 is exactly the signal the caller in
        # _board_wide_sweep gates its print on ("if non_subject_count:
        # print(...)") -- a caller-side aggregate-count line, never a
        # per-item line, so nothing prints for an empty non-subject set.


class BoardSweepSubjectMappingLossReportedTest(unittest.TestCase):
    """check: board_sweep_subject_mapping_loss_reported"""

    def setUp(self):
        import tempfile
        self._orig_state_root = state_paths.STATE_ROOT
        state_paths.STATE_ROOT = Path(tempfile.mkdtemp())

    def tearDown(self):
        state_paths.STATE_ROOT = self._orig_state_root

    def test_board_sweep_subject_mapping_loss_reported_shaped_branch_not_on_board(self):
        # C1=Y (branch matches issue-<n>/<skill>), C2=N (issue-2379 is not
        # a current board subject) -> mapping loss, individual + remediation.
        # issue #3047: cause classification needs `pr_index` too -- a lone
        # OPEN entry for this subject (no merged/closed sibling) is the
        # no-record-yet class, not corrupted-merge-base.
        pr_index = {"issue-2379/observability-signal-golden-abc123":
                    {"number": 42, "state": "OPEN", "body": ""}}
        (changed, non_subject, loss_new, loss_repeat) = watchdog._classify_narrowing_prs(
            Path("/nonexistent"), {42}, {42: "issue-2379/observability-signal-golden-abc123"}, {},
            pr_index)
        self.assertEqual(changed, set())
        self.assertEqual(non_subject, 0)
        self.assertEqual(loss_new, [(42, 2379, "issue-2379/observability-signal-golden-abc123",
                                      watchdog._MAPPING_LOSS_NO_RECORD_YET)])

    def test_board_sweep_subject_mapping_loss_reported_not_flagged_when_on_board(self):
        # C1=Y, C2=Y -> normal mapping, folded silently into changed_numbers.
        board_now = {"issue-2379": {"observability-signal-golden": {}}}
        (changed, non_subject, loss_new, loss_repeat) = watchdog._classify_narrowing_prs(
            Path("/nonexistent"), {42}, {42: "issue-2379/observability-signal-golden-abc123"},
            board_now)
        self.assertEqual(changed, {2379})
        self.assertEqual(non_subject, 0)
        self.assertEqual(loss_new, [])

    def test_board_sweep_subject_mapping_loss_reported_suppressed_on_repeat(self):
        root = Path("/nonexistent")
        branch_map = {42: "issue-2379/observability-signal-golden-abc123"}
        pr_index = {"issue-2379/observability-signal-golden-abc123":
                    {"number": 42, "state": "OPEN", "body": ""}}
        first = watchdog._classify_narrowing_prs(root, {42}, branch_map, {}, pr_index)
        second = watchdog._classify_narrowing_prs(root, {42}, branch_map, {}, pr_index)
        self.assertEqual(first[2], [(42, 2379, branch_map[42],
                                      watchdog._MAPPING_LOSS_NO_RECORD_YET)])
        self.assertEqual(second[2], [])
        self.assertEqual(second[3], 1)

    def test_board_sweep_subject_mapping_loss_reported_resurfaces_for_new_pr(self):
        root = Path("/nonexistent")
        pr_index = {"issue-2379/observability-signal-golden-abc123":
                    {"number": 42, "state": "OPEN", "body": ""},
                    "issue-2379/observability-signal-golden-def456":
                    {"number": 99, "state": "OPEN", "body": ""}}
        watchdog._classify_narrowing_prs(
            root, {42}, {42: "issue-2379/observability-signal-golden-abc123"}, {}, pr_index)
        # A different, never-before-seen PR number for the same subject
        # is new information (issue #2196's one-shot marker keys on PR
        # number, not subject) and must still surface once.
        third = watchdog._classify_narrowing_prs(
            root, {99}, {99: "issue-2379/observability-signal-golden-def456"}, {}, pr_index)
        self.assertEqual(third[2], [(99, 2379, "issue-2379/observability-signal-golden-def456",
                                      watchdog._MAPPING_LOSS_NO_RECORD_YET)])


class SpawnCoverageReportsChangeTest(unittest.TestCase):
    """check: spawn_coverage_reports_change"""

    def setUp(self):
        import tempfile
        self._orig_state_root = state_paths.STATE_ROOT
        state_paths.STATE_ROOT = Path(tempfile.mkdtemp())

    def tearDown(self):
        state_paths.STATE_ROOT = self._orig_state_root

    def test_spawn_coverage_reports_change_new_entry_surfaces(self):
        # D1=N, D2=Y
        root = Path("/nonexistent")
        newly = watchdog._watchdog_note_spawn_coverage_delta(root, [100])
        self.assertEqual(newly, [100])

    def test_spawn_coverage_reports_change_unchanged_set_reports_nothing(self):
        # D1=Y, D2=Y -- empty-state acceptance note.
        root = Path("/nonexistent")
        watchdog._watchdog_note_spawn_coverage_delta(root, [100])
        newly = watchdog._watchdog_note_spawn_coverage_delta(root, [100])
        self.assertEqual(newly, [])

    def test_spawn_coverage_reports_change_standing_entries_not_repeated(self):
        root = Path("/nonexistent")
        watchdog._watchdog_note_spawn_coverage_delta(root, [100, 200])
        newly = watchdog._watchdog_note_spawn_coverage_delta(root, [100, 200, 300])
        self.assertEqual(newly, [300])

    def test_spawn_coverage_reports_change_flap_reappears_reported_again(self):
        # D1=Y, D2=N (tick 2: covered, dropped) then D1=N, D2=Y (tick 3:
        # uncovered again) -- flapping resurfaces as new, not sticky-once.
        root = Path("/nonexistent")
        tick1 = watchdog._watchdog_note_spawn_coverage_delta(root, [100])
        tick2 = watchdog._watchdog_note_spawn_coverage_delta(root, [])
        tick3 = watchdog._watchdog_note_spawn_coverage_delta(root, [100])
        self.assertEqual(tick1, [100])
        self.assertEqual(tick2, [])
        self.assertEqual(tick3, [100])


if __name__ == "__main__":
    unittest.main()
