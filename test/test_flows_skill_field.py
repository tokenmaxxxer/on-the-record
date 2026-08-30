"""issue #1824: `gates/flows.py._pr_approved` dual-read coverage — the #1818
structured approval record (`.git/gh-read-cache/issue-<n>-approvals.json`)
is preferred, with fallback to the pre-existing needle/PR-review scan.
Mirrors #1821's `test_approval_gate_role_field.py` shape (per
docs/issue-1824/proposals/rsb-dual-read.md, "What will be done" item 2).
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "gates"))

import spawn  # noqa: E402
import flows  # noqa: E402


class PrApprovedRoleFieldTest(unittest.TestCase):
    # `conftest.py`'s session-wide `_isolated_gh_read_cache_approvals`
    # autouse fixture already scopes `spawn._approval_record_path` to a
    # per-test tmp dir so this test never touches the real
    # `.git/gh-read-cache` — `self.root` only needs to be *some* root the
    # patched path function accepts; the fixture ignores it.
    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.root = tmp_path

    def _write_record(self, issue_n: int, record: dict) -> None:
        path = spawn._approval_record_path(self.root, issue_n)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record), encoding="utf-8")

    def test_record_hit_short_circuits_with_no_comment_or_review(self):
        self._write_record(1792, {"implementation": {"actor": "approver1",
                                                       "timestamp": "2026-08-21T00:00:00+00:00"}})
        approved = flows._pr_approved(
            {"reviews": []}, [], {"approver1"}, "issue-1792", "implementation",
            self.root,
        )
        self.assertTrue(approved)

    def test_fallback_to_needle_when_record_absent(self):
        comments = [{"body": "APPROVE issue-1792/implementation", "login": "approver1"}]
        approved = flows._pr_approved(
            {"reviews": []}, comments, {"approver1"}, "issue-1792", "implementation",
            self.root,
        )
        self.assertTrue(approved)

    def test_no_carrier_legacy_case_byte_identical(self):
        comments = [{"body": "APPROVE issue-1792/implementation", "login": "approver1"}]
        pr = {"reviews": []}
        approved_default_root = flows._pr_approved(
            pr, comments, {"approver1"}, "issue-1792", "implementation",
        )
        approved_empty_root = flows._pr_approved(
            pr, comments, {"approver1"}, "issue-1792", "implementation", self.root,
        )
        self.assertEqual(approved_default_root, approved_empty_root)
        self.assertTrue(approved_empty_root)

        not_approved = flows._pr_approved(
            {"reviews": []}, [], {"approver1"}, "issue-1792", "implementation",
            self.root,
        )
        self.assertFalse(not_approved)


if __name__ == "__main__":
    unittest.main()
