"""Issue #3047 acceptance:
  - check: `python3 -m pytest tests/test_watchdog_cause_classification.py -q`
  - check: `python3 gates/probe_cause_misattribution.py`

The defect: `_classify_narrowing_prs` named exactly one cause
(corrupted-merge-base, #2379) for a board-mapping absence that has at
least three possible causes, and attached a `recut-corrupted` force-push
remediation sentence to that one guess regardless of which cause actually
held. A brand-new issue with an open PR and no merged record yet produced
the identical alarm+repair as a genuinely corrupted merge-base.

Test derivation (test-derivation skill). This routes to decision-table
testing: `watchdog._classify_mapping_loss_cause(pr_index, issue_n)`
inspects every sibling branch under `issue-<issue_n>/` already present in
`pr_index` (the existing `gh pr list`-equivalent bulk index, `state=all`
-- no extra `gh` call) and decides among three outcomes from two boolean
conditions, checked in priority order:

  C1: does any sibling branch have state MERGED?
  C2: (only decisive when C1=N) does any sibling branch have state CLOSED
      (i.e. closed without merging)?

  | C1  | C2  | outcome                                                |
  |-----|-----|---------------------------------------------------------|
  | Y   | Y   | corrupted-merge-base (a merged record existed; C1 wins) |
  | Y   | N   | corrupted-merge-base                                    |
  | N   | Y   | unclassified (closed-without-merge is ambiguous)        |
  | N   | N   | no-record-yet (only OPEN siblings, or none at all)      |

4 feasible columns (C1 checked unconditionally, so all 2x2 combinations
are reachable), all exercised below -- 100% decision-table coverage. The
C1=N/C2=N row is additionally split into two equivalence-partition members
("only OPEN siblings" and "no siblings at all, self excluded") since both
must fold into the same no-record-yet bucket.

A second dimension -- text-level guarantee on `_format_mapping_loss_line`
-- is exercised by GWT: the `recut-corrupted` remediation sentence must
appear in exactly one of the three causes' output text, never the other
two (the issue's second acceptance check, restated as a unit assertion
per cause rather than only at the probe's live-classifier level)."""
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


class ClassifyMappingLossCauseDecisionTableTest(unittest.TestCase):
    """Decision table over `_classify_mapping_loss_cause`. check:
    `python3 -m pytest tests/test_watchdog_cause_classification.py -q`"""

    def test_c1_y_c2_y_merged_and_closed_sibling_is_corrupted(self):
        # C1=Y, C2=Y: a merged sibling exists AND a closed-non-merged
        # sibling also exists -- MERGED still wins (checked first).
        pr_index = {
            "issue-42/skillA-abc": {"number": 1, "state": "MERGED", "body": ""},
            "issue-42/skillB-def": {"number": 2, "state": "CLOSED", "body": ""},
            "issue-42/skillC-ghi": {"number": 3, "state": "OPEN", "body": ""},
        }
        self.assertEqual(
            watchdog._classify_mapping_loss_cause(pr_index, 42),
            watchdog._MAPPING_LOSS_CORRUPTED)

    def test_c1_y_c2_n_merged_only_is_corrupted(self):
        # C1=Y, C2=N: a merged sibling exists, no closed-non-merged one.
        pr_index = {
            "issue-42/skillA-abc": {"number": 1, "state": "MERGED", "body": ""},
            "issue-42/skillB-def": {"number": 2, "state": "OPEN", "body": ""},
        }
        self.assertEqual(
            watchdog._classify_mapping_loss_cause(pr_index, 42),
            watchdog._MAPPING_LOSS_CORRUPTED)

    def test_c1_n_c2_y_closed_without_merge_is_unclassified(self):
        # C1=N, C2=Y: no merged sibling, but one was closed without
        # merging -- could be normal supersession or an abandoned
        # corrupted attempt; the index alone can't tell, so unclassified.
        pr_index = {
            "issue-42/skillA-abc": {"number": 1, "state": "CLOSED", "body": ""},
            "issue-42/skillB-def": {"number": 2, "state": "OPEN", "body": ""},
        }
        self.assertEqual(
            watchdog._classify_mapping_loss_cause(pr_index, 42),
            watchdog._MAPPING_LOSS_UNCLASSIFIED)

    def test_c1_n_c2_n_only_open_siblings_is_no_record_yet(self):
        # C1=N, C2=N, equivalence-partition member 1: siblings exist but
        # are all OPEN -- consistent with "first record not merged yet".
        pr_index = {
            "issue-42/skillA-abc": {"number": 1, "state": "OPEN", "body": ""},
            "issue-42/skillB-def": {"number": 2, "state": "OPEN", "body": ""},
        }
        self.assertEqual(
            watchdog._classify_mapping_loss_cause(pr_index, 42),
            watchdog._MAPPING_LOSS_NO_RECORD_YET)

    def test_c1_n_c2_n_no_siblings_at_all_is_no_record_yet(self):
        # C1=N, C2=N, equivalence-partition member 2: this is the only PR
        # this subject has ever had (a brand-new issue's first session) --
        # the strongest possible no-record-yet signal.
        pr_index = {
            "issue-99/skillA-abc": {"number": 501, "state": "OPEN", "body": ""},
        }
        self.assertEqual(
            watchdog._classify_mapping_loss_cause(pr_index, 99),
            watchdog._MAPPING_LOSS_NO_RECORD_YET)

    def test_empty_pr_index_is_no_record_yet_not_a_crash(self):
        self.assertEqual(
            watchdog._classify_mapping_loss_cause({}, 42),
            watchdog._MAPPING_LOSS_NO_RECORD_YET)

    def test_other_issue_numbers_do_not_leak_across_prefix_match(self):
        # issue-4/... must not be matched as a sibling of issue-42 --
        # startswith on a bare prefix without the trailing "/" would
        # wrongly fold issue-420 into issue-42's evidence.
        pr_index = {
            "issue-420/skillA-abc": {"number": 1, "state": "MERGED", "body": ""},
            "issue-4/skillB-def": {"number": 2, "state": "MERGED", "body": ""},
        }
        self.assertEqual(
            watchdog._classify_mapping_loss_cause(pr_index, 42),
            watchdog._MAPPING_LOSS_NO_RECORD_YET)


class FormatMappingLossLineRemediationTextTest(unittest.TestCase):
    """GWT: the `recut-corrupted` remediation sentence is attached to the
    cause it actually diagnoses, and to no other. check: `the new-issue
    case's output contains no recut-corrupted instruction`."""

    def test_corrupted_cause_carries_recut_corrupted_instruction(self):
        # Given a mapping-loss item classified as corrupted-merge-base,
        # when the line is formatted, then it names `recut-corrupted`.
        line = watchdog._format_mapping_loss_line(
            42, 2379, "issue-2379/observability-signal-golden-abc123",
            watchdog._MAPPING_LOSS_CORRUPTED)
        self.assertIn("recut-corrupted", line)

    def test_no_record_yet_cause_carries_no_recut_corrupted_instruction(self):
        # Given a mapping-loss item classified as no-record-yet (new
        # issue, first record not merged), when the line is formatted,
        # then it does NOT name `recut-corrupted`.
        line = watchdog._format_mapping_loss_line(
            43, 3042, "issue-3042/implementation-audit-0d4eb553",
            watchdog._MAPPING_LOSS_NO_RECORD_YET)
        self.assertNotIn("recut-corrupted", line)

    def test_unclassified_cause_carries_no_recut_corrupted_instruction(self):
        # Given a mapping-loss item that could not be classified, when
        # the line is formatted, then it does NOT name `recut-corrupted`
        # either -- an unset cause never inherits a repair instruction.
        line = watchdog._format_mapping_loss_line(
            44, 5000, "issue-5000/some-skill-abc123",
            watchdog._MAPPING_LOSS_UNCLASSIFIED)
        self.assertNotIn("recut-corrupted", line)
        self.assertIn("unclassified", line)

    def test_three_causes_produce_three_distinct_output_strings(self):
        # check: run the classifier against distinct subjects and show
        # the outputs differ -- restated here at the pure-formatter level
        # for all three causes, not just the two named in the issue.
        args = (42, 2379, "issue-2379/some-skill-abc123")
        lines = {cause: watchdog._format_mapping_loss_line(*args, cause)
                 for cause in (watchdog._MAPPING_LOSS_CORRUPTED,
                               watchdog._MAPPING_LOSS_NO_RECORD_YET,
                               watchdog._MAPPING_LOSS_UNCLASSIFIED)}
        self.assertEqual(len(set(lines.values())), 3)


class ClassifyNarrowingPrsRoutesCauseIntoTupleTest(unittest.TestCase):
    """`_classify_narrowing_prs` threads the classified cause through to
    its `mapping_loss_new` tuples end-to-end (not just the pure helper in
    isolation) -- the shape the board-sweep print loop actually consumes."""

    def setUp(self):
        import tempfile
        self._orig_state_root = state_paths.STATE_ROOT
        state_paths.STATE_ROOT = Path(tempfile.mkdtemp())

    def tearDown(self):
        state_paths.STATE_ROOT = self._orig_state_root

    def test_new_issue_subject_routes_to_no_record_yet_cause(self):
        pr_index = {"issue-3042/implementation-audit-0d4eb553":
                    {"number": 43, "state": "OPEN", "body": ""}}
        (_changed, _non_subject, loss_new, _repeat) = watchdog._classify_narrowing_prs(
            Path("/nonexistent"), {43},
            {43: "issue-3042/implementation-audit-0d4eb553"}, {}, pr_index)
        self.assertEqual(len(loss_new), 1)
        prn, issue_n, branch, cause = loss_new[0]
        self.assertEqual((prn, issue_n), (43, 3042))
        self.assertEqual(cause, watchdog._MAPPING_LOSS_NO_RECORD_YET)

    def test_corrupted_subject_routes_to_corrupted_cause(self):
        pr_index = {
            "issue-2379/observability-signal-golden-abc123":
                {"number": 41, "state": "MERGED", "body": ""},
            "issue-2379/observability-signal-golden-def456":
                {"number": 42, "state": "OPEN", "body": ""},
        }
        (_changed, _non_subject, loss_new, _repeat) = watchdog._classify_narrowing_prs(
            Path("/nonexistent"), {42},
            {42: "issue-2379/observability-signal-golden-def456"}, {}, pr_index)
        self.assertEqual(len(loss_new), 1)
        prn, issue_n, branch, cause = loss_new[0]
        self.assertEqual((prn, issue_n), (42, 2379))
        self.assertEqual(cause, watchdog._MAPPING_LOSS_CORRUPTED)

    def test_missing_pr_index_argument_routes_to_unclassified_not_a_guess(self):
        # silent-failure-audit finding (issue #3047): a caller that has no
        # pr_index at all (none of production's -- the parameter is
        # optional only for defensive callers) is a genuinely different,
        # weaker epistemic state than "fetched pr_index and it says
        # nothing about this subject" -- collapsing "could not check" into
        # the confident no-record-yet guess would reproduce this issue's
        # own defect at the width of one optional parameter. Must not
        # crash, and must not silently default into either named cause.
        (_changed, _non_subject, loss_new, _repeat) = watchdog._classify_narrowing_prs(
            Path("/nonexistent"), {42}, {42: "issue-2379/some-skill-abc123"}, {})
        self.assertEqual(loss_new[0][3], watchdog._MAPPING_LOSS_UNCLASSIFIED)


if __name__ == "__main__":
    unittest.main()
