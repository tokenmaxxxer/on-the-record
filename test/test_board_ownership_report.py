"""issue #2719: `ownership_report()` used to exempt `spikes/` and
`postmortems/` only when `role` literally equalled `technical-feasibility`
/ `release-engineering` -- a 2-name closed-set membership test, the
retired role-catalog dispatch shape reproduced under skill identity
(issue #2626 finding A). Replaced with a path-only signal
(`ALT_RECORD_SUBDIRS`) that does not read `role` for this branch at all.
These cases pin the two behaviors that must stay unchanged (a role's own
`<role>.md` record, and an unrelated path is still flagged) and the one
behavior that is a deliberate, disclosed widening (any role writing to
`spikes/`/`postmortems/` is now exempted, not just the two that
historically did -- `git log --all --diff-filter=A -- 'docs/issue-*/
reports/spikes/*' 'docs/issue-*/reports/postmortems/*'` finds zero
commits in this repo's history, so no real write is reclassified)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import board  # noqa: E402


class OwnershipReportAltRecordSubdirsTest(unittest.TestCase):
    def test_own_named_record_unflagged(self):
        delta = ["docs/issue-9/reports/coding.md"]
        self.assertEqual(board.ownership_report(".", "coding", delta), [])

    def test_technical_feasibility_own_spikes_unflagged_unchanged(self):
        delta = ["docs/issue-9/reports/spikes/foo.md"]
        self.assertEqual(
            board.ownership_report(".", "technical-feasibility", delta), [])

    def test_release_engineering_own_postmortems_unflagged_unchanged(self):
        delta = ["docs/issue-9/reports/postmortems/foo.md"]
        self.assertEqual(
            board.ownership_report(".", "release-engineering", delta), [])

    def test_other_role_writing_alt_subdir_now_unflagged_disclosed_widening(self):
        delta = ["docs/issue-9/reports/spikes/foo.md"]
        self.assertEqual(board.ownership_report(".", "coding", delta), [])

    def test_unrelated_path_still_flagged(self):
        delta = ["docs/issue-9/reports/other-role.md"]
        report = board.ownership_report(".", "coding", delta)
        self.assertTrue(report)
        self.assertIn("docs/issue-9/reports/other-role.md", report[-1])

    def test_no_delta_no_report(self):
        self.assertEqual(board.ownership_report(".", "coding", []), [])

    def test_consult_log_unflagged_regardless_of_role(self):
        # Issue #3230: `consult-log/` writes can now land inside the
        # board_snapshot before/after delta window (the cross-family
        # judge that writes it moved to a detached subprocess launched
        # after Popen), so the timing guarantee that used to make this a
        # non-issue no longer holds -- it needs the same path-only
        # exemption `spikes/`/`postmortems/` already get.
        delta = ["docs/issue-9/reports/consult-log/2026-09-03.md"]
        self.assertEqual(board.ownership_report(".", "implementation", delta), [])


if __name__ == "__main__":
    unittest.main()
