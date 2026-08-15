#!/usr/bin/env python3
"""이슈 #1507 — repo_scope.py 의 freshness 확장 테스트.

`check_absence_freshness()`가 절대-부재 주장에 "verified against
origin/main at <sha>, fetched <timestamp>" 문구를 요구하는지, 부재 주장이
없는 텍스트는 게이트하지 않는지를 검증한다."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from repo_scope import Violation, check_absence_freshness


class AbsenceFreshnessGate(unittest.TestCase):
    def test_missing_phrase_is_rejected_with_named_clause(self):
        text = ("The record-tiering hooks does not exist anywhere in the "
                "working tree.")
        violations = check_absence_freshness(text)
        self.assertEqual(len(violations), 1)
        self.assertIn("freshness", violations[0].reason)
        self.assertIn("fetched <timestamp>", violations[0].reason)

    def test_current_sha_and_timestamp_phrase_passes(self):
        text = ("The record-tiering hooks does not exist anywhere in the "
                "working tree, verified against origin/main at "
                "a1b2c3d4e5f6, fetched 2026-08-15T00:00:00Z.")
        self.assertEqual(check_absence_freshness(text), [])

    def test_old_style_as_of_sha_alone_is_not_enough(self):
        # #415 의 일반 스코프 어구만으로는 freshness 요건을 만족하지 못한다
        # — sha 는 있어도 fetch 시각이 없다.
        text = ("The record-tiering hooks does not exist anywhere in the "
                "working tree, as of a1b2c3d4e5f6.")
        violations = check_absence_freshness(text)
        self.assertEqual(len(violations), 1)

    def test_no_absence_claim_is_not_gated(self):
        text = "The record-tiering hooks exist and are wired into main."
        self.assertEqual(check_absence_freshness(text), [])

    def test_file_scoped_absence_claim_is_skipped(self):
        text = "`gates/foo.py:12` does not exist in this checkout."
        self.assertEqual(check_absence_freshness(text), [])

    def test_violation_equality(self):
        v1 = Violation("s", "r")
        v2 = Violation("s", "r")
        self.assertEqual(v1, v2)


if __name__ == "__main__":
    unittest.main()
