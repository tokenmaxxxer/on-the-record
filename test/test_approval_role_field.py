"""Structured approval record field-read/dual-write/fallback tests (issue #1818).

Mirrors issue #1803's field-present-vs-key-split equivalence method: the
record is a write-through cache of `_approved_roles_on_issue`'s own comment
scan, so "record path" and "comment-scan path" must agree by construction.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "gates"))

import spawn  # noqa: E402
import ci  # noqa: E402


class ApprovalRecordFieldTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self._orig_approvers = spawn._approvers
        self._orig_comments = spawn._issue_comments
        spawn._approvers = lambda repo: {"approver1"}

    def tearDown(self):
        spawn._approvers = self._orig_approvers
        spawn._issue_comments = self._orig_comments
        self._tmp.cleanup()

    def _record_path(self, issue: int) -> Path:
        return spawn._approval_record_path(self.repo, issue)

    def test_dual_write_shape(self):
        # a fresh scan that finds an approval writes a record with the
        # approving login and a timestamp, keyed by role.
        spawn._issue_comments = lambda repo, issue: (
            [{"login": "approver1", "body": "APPROVE issue-9001/implementation"}], True)
        roles = ci._approved_roles_on_issue(self.repo, 9001)
        self.assertEqual(roles, {"implementation"})

        record_path = self._record_path(9001)
        self.assertTrue(record_path.exists())
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertIn("implementation", record)
        self.assertEqual(record["implementation"]["actor"], "approver1")
        self.assertTrue(record["implementation"]["timestamp"])

    def test_field_read_preferred_when_present(self):
        # record already covers a role; comment scan returns nothing for
        # it (simulating an unreachable/rate-limited gh call) — the
        # record answer still surfaces the role.
        record_path = self._record_path(9002)
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps(
            {"implementation": {"actor": "approver1", "timestamp": "2026-01-01T00:00:00+00:00"}}),
            encoding="utf-8")
        spawn._issue_comments = lambda repo, issue: ([], True)
        roles = ci._approved_roles_on_issue(self.repo, 9002)
        self.assertEqual(roles, {"implementation"})

    def test_fallback_covers_role_record_does_not_have(self):
        # record covers one role; comment scan finds a second, newer
        # approval for a different role — fallback (still-run scan)
        # picks it up and the record is extended to cover it too.
        record_path = self._record_path(9003)
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps(
            {"implementation": {"actor": "approver1", "timestamp": "2026-01-01T00:00:00+00:00"}}),
            encoding="utf-8")
        spawn._issue_comments = lambda repo, issue: (
            [{"login": "approver1", "body": "APPROVE issue-9003/review"}], True)
        roles = ci._approved_roles_on_issue(self.repo, 9003)
        self.assertEqual(roles, {"implementation", "review"})
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertIn("review", record)
        self.assertIn("implementation", record)

    def test_legacy_token_only_issue_resolves_identically_to_today(self):
        # no record file at all (fresh workspace / pre-#1818 issue) —
        # the comment-scan-only path must resolve exactly as it did
        # before this change.
        spawn._issue_comments = lambda repo, issue: (
            [{"login": "approver1", "body": "APPROVE issue-9004/implementation"},
             {"login": "not-an-approver", "body": "APPROVE issue-9004/review"},
             {"login": "approver1", "body": "APPROVE issue-9004/"},  # empty suffix, ignored
             {"login": "approver1", "body": "not an approval"}],
            True)
        self.assertFalse(self._record_path(9004).exists())
        roles = ci._approved_roles_on_issue(self.repo, 9004)
        self.assertEqual(roles, {"implementation"})

    def test_record_absent_and_comments_unreachable_fails_closed(self):
        spawn._issue_comments = lambda repo, issue: ([], False)
        roles = ci._approved_roles_on_issue(self.repo, 9005)
        self.assertEqual(roles, set())

    def test_corrupt_record_file_falls_back_to_scan(self):
        record_path = self._record_path(9006)
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text("not json", encoding="utf-8")
        spawn._issue_comments = lambda repo, issue: (
            [{"login": "approver1", "body": "APPROVE issue-9006/implementation"}], True)
        roles = ci._approved_roles_on_issue(self.repo, 9006)
        self.assertEqual(roles, {"implementation"})


if __name__ == "__main__":
    unittest.main()
