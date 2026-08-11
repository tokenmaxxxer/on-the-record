#!/usr/bin/env python3
"""issue #659 Axis 1 — batch_eligible_groups: write-set non-overlap grouping.

  python3 gates/test_batch_eligible_groups.py
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import risk_report  # noqa: E402


class BatchEligibleGroups(unittest.TestCase):
    def test_no_prs_is_empty(self):
        self.assertEqual(risk_report.batch_eligible_groups([], ROOT), [])

    def test_singleton_pr_is_trivial_singleton_group(self):
        prs = [{"path": "docs/issue-1/proposals/a.md", "files": ["a.py"]}]
        groups = risk_report.batch_eligible_groups(prs, ROOT)
        self.assertEqual(groups, [["docs/issue-1/proposals/a.md"]])

    def test_non_overlapping_prs_are_separate_groups(self):
        prs = [
            {"path": "pr-a", "files": ["a.py"]},
            {"path": "pr-b", "files": ["b.py"]},
        ]
        groups = risk_report.batch_eligible_groups(prs, ROOT)
        self.assertEqual(len(groups), 2)
        self.assertIn(["pr-a"], groups)
        self.assertIn(["pr-b"], groups)

    def test_overlapping_prs_grouped_together(self):
        prs = [
            {"path": "pr-a", "files": ["shared.py"]},
            {"path": "pr-b", "files": ["shared.py"]},
            {"path": "pr-c", "files": ["other.py"]},
        ]
        groups = risk_report.batch_eligible_groups(prs, ROOT)
        self.assertEqual(len(groups), 2)
        overlap_group = next(g for g in groups if "pr-a" in g)
        self.assertEqual(set(overlap_group), {"pr-a", "pr-b"})
        self.assertIn(["pr-c"], groups)

    def test_transitive_overlap_joins_one_group(self):
        prs = [
            {"path": "pr-a", "files": ["x.py"]},
            {"path": "pr-b", "files": ["x.py", "y.py"]},
            {"path": "pr-c", "files": ["y.py"]},
        ]
        groups = risk_report.batch_eligible_groups(prs, ROOT)
        self.assertEqual(len(groups), 1)
        self.assertEqual(set(groups[0]), {"pr-a", "pr-b", "pr-c"})

    def test_glob_write_scope_overlap_detected(self):
        prs = [
            {"path": "pr-a", "files": ["docs/**"]},
            {"path": "pr-b", "files": ["docs/issue-1/x.md"]},
        ]
        groups = risk_report.batch_eligible_groups(prs, ROOT)
        self.assertEqual(len(groups), 1)


if __name__ == "__main__":
    unittest.main()
