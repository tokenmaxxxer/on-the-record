"""issue #3061: standing delegation as machine-visible state, and the
after-the-fact audit for a turn that asked for authority a recorded
delegation already covered.

Test derivation (test-derivation skill): delegation_state.py's grant/read/
revoke/expiry cycle is a state-transition problem (NONE -> IN_FORCE ->
{REVOKED, EXPIRED}); audit()'s flagging rule is a 6-condition AND decision
(no tool_use AND matches a redundant-ask phrasing AND no fork marker AND
delegation in force AND timestamp >= since AND timestamp >= granted_at) —
tested MC/DC-style, one baseline-true case per condition flipped to show it
independently controls the flagged/not-flagged outcome. The fork-marker
case is the must-not case from the issue body (a genuine escalation must
never be flagged as redundant) and gets its own adversarial case where the
redundant-ask phrase and the fork marker are BOTH present in one turn.

Run: python3 -m pytest test/test_delegation_state.py -q
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
import delegation_state as ds  # noqa: E402


def _write_log(path: Path, events: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def _assistant_event(ts: datetime, text: str | None = None,
                      tool_use: bool = False) -> dict:
    content = []
    if tool_use:
        content.append({"type": "tool_use", "name": "Bash", "input": {}})
    if text is not None:
        content.append({"type": "text", "text": text})
    return {"type": "assistant", "timestamp": ts.isoformat(),
            "message": {"content": content}}


class DelegationStateTransitionsTest(unittest.TestCase):
    """R1: NONE -> IN_FORCE -> {REVOKED, EXPIRED}, plus the invalid-
    transition guards (revoke from NONE, self-grant from a skill-bound
    session, empty-scope grant)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_none_state_reports_cleanly_not_error(self):
        self.assertIsNone(ds.load_state(self.repo))
        self.assertEqual(ds.describe(self.repo), "no standing delegation recorded")
        self.assertFalse(ds.in_force(None))

    def test_grant_transitions_to_in_force(self):
        now = datetime.now(timezone.utc)
        record = ds.grant(self.repo, "다 판단해서 처분해서 해", "jiwon", now=now, skill_env="")
        self.assertTrue(ds.in_force(record, now=now))
        self.assertIn("IN FORCE", ds.describe(self.repo, now=now))

    def test_revoke_transitions_in_force_to_revoked(self):
        now = datetime.now(timezone.utc)
        ds.grant(self.repo, "scope", "jiwon", now=now, skill_env="")
        revoked = ds.revoke(self.repo, "jiwon", now=now + timedelta(minutes=1))
        self.assertFalse(ds.in_force(revoked, now=now + timedelta(minutes=2)))
        self.assertIn("NOT in force", ds.describe(self.repo, now=now + timedelta(minutes=2)))
        self.assertIn("revoked_at", ds.describe(self.repo, now=now + timedelta(minutes=2)))

    def test_expiry_transitions_in_force_to_expired_without_explicit_revoke(self):
        now = datetime.now(timezone.utc)
        ds.grant(self.repo, "scope", "jiwon", hours=1, now=now, skill_env="")
        later = now + timedelta(hours=2)
        record = ds.load_state(self.repo)
        self.assertFalse(ds.in_force(record, now=later))
        self.assertIn("expired at", ds.describe(self.repo, now=later))

    def test_revoke_from_none_state_is_a_clean_noop_not_an_error(self):
        self.assertIsNone(ds.revoke(self.repo, "jiwon"))

    def test_skill_bound_session_cannot_grant_its_own_delegation(self):
        with self.assertRaises(ds.SkillBoundGrantError):
            ds.grant(self.repo, "scope", "jiwon", skill_env="implementation")
        self.assertIsNone(ds.load_state(self.repo))

    def test_empty_scope_is_refused(self):
        with self.assertRaises(ValueError):
            ds.grant(self.repo, "   ", "jiwon", skill_env="")

    def test_second_grant_replaces_the_first_state_not_a_log(self):
        now = datetime.now(timezone.utc)
        ds.grant(self.repo, "first scope", "a", now=now, skill_env="")
        ds.grant(self.repo, "second scope", "b", now=now, skill_env="")
        self.assertEqual(ds.load_state(self.repo)["scope"], "second scope")

    def test_malformed_expires_at_is_fail_closed_not_never_expires(self):
        # silent-failure-audit finding: a parse failure on a present
        # expires_at must not default to "no expiry" (indefinite
        # authority) -- it must default to not-in-force.
        now = datetime.now(timezone.utc)
        ds.grant(self.repo, "scope", "jiwon", now=now, skill_env="")
        path = Path(self.repo) / ds.STATE_REL_PATH
        record = json.loads(path.read_text())
        record["expires_at"] = "not-a-real-timestamp"
        path.write_text(json.dumps(record))
        self.assertFalse(ds.in_force(ds.load_state(self.repo), now=now))

    def test_corrupt_state_file_reports_unreadable_not_plain_none(self):
        # silent-failure-audit finding: a corrupt file must read
        # differently from "nothing was ever granted".
        path = Path(self.repo) / ds.STATE_REL_PATH
        path.parent.mkdir(parents=True)
        path.write_text("{not valid json")
        self.assertIsNone(ds.load_state(self.repo))
        self.assertIn("unreadable/corrupt", ds.describe(self.repo))


class DelegationAuditFlaggingTest(unittest.TestCase):
    """R2: audit()'s flagging decision, MC/DC-style — one baseline-true
    case, then one case per condition flipped to False."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = str(Path(self._tmp.name) / "myrepo")
        Path(self.repo).mkdir()
        self.work_dir = Path(self._tmp.name) / "work"
        self.work_dir.mkdir()
        self.log = self.work_dir / "myrepo.session.1.1.log"
        self.now = datetime.now(timezone.utc)
        self.granted_at = self.now - timedelta(hours=1)
        ds.grant(self.repo, "다 판단해서 처분해서 해", "jiwon",
                  now=self.granted_at, skill_env="")
        self.since = (self.now - timedelta(days=1)).strftime("%Y-%m-%d")

    def tearDown(self):
        self._tmp.cleanup()

    def _audit_count(self, events: list[dict]) -> int:
        _write_log(self.log, events)
        result = ds.audit(self.repo, self.since, work_dir=self.work_dir, now=self.now)
        return result["count"]

    def test_baseline_all_conditions_true_is_flagged(self):
        ev = _assistant_event(self.now, text="이대로 갈까요?")
        self.assertEqual(self._audit_count([ev]), 1)

    def test_tool_use_present_is_not_flagged(self):
        ev = _assistant_event(self.now, text="진행할까요?", tool_use=True)
        self.assertEqual(self._audit_count([ev]), 0)

    def test_text_not_matching_redundant_ask_pattern_is_not_flagged(self):
        ev = _assistant_event(self.now, text="다음 파일을 확인하겠습니다.")
        self.assertEqual(self._audit_count([ev]), 0)

    def test_fork_marker_present_is_not_flagged_must_not_suppress_escalation(self):
        # issue #3061 must-not: a genuine fork the operator must decide is
        # exactly what should still surface — even when its phrasing also
        # matches a redundant-ask pattern (adversarial combined case).
        ev = _assistant_event(
            self.now,
            text="이대로 갈까요? 옵션 1과 옵션 2 중 어느 쪽으로 갈지 결정이 필요합니다.")
        self.assertEqual(self._audit_count([ev]), 0)

    def test_delegation_not_in_force_is_not_flagged(self):
        ds.revoke(self.repo, "jiwon", now=self.now - timedelta(minutes=30))
        ev = _assistant_event(self.now, text="이대로 갈까요?")
        self.assertEqual(self._audit_count([ev]), 0)

    def test_timestamp_before_since_cutoff_is_not_flagged(self):
        before_since = self.now - timedelta(days=2)
        ev = _assistant_event(before_since, text="이대로 갈까요?")
        self.assertEqual(self._audit_count([ev]), 0)

    def test_timestamp_before_grant_is_not_flagged(self):
        before_grant = self.granted_at - timedelta(minutes=1)
        ev = _assistant_event(before_grant, text="이대로 갈까요?")
        self.assertEqual(self._audit_count([ev]), 0)

    def test_english_phrasing_also_matches(self):
        ev = _assistant_event(self.now, text="Should I proceed with the next step?")
        self.assertEqual(self._audit_count([ev]), 1)

    def test_empty_state_no_delegation_ever_granted_reports_zero(self):
        other_repo = str(Path(tempfile.mkdtemp()) / "otherrepo")
        Path(other_repo).mkdir(parents=True)
        result = ds.audit(other_repo, self.since, work_dir=self.work_dir, now=self.now)
        self.assertEqual(result["count"], 0)

    def test_empty_state_no_session_logs_reports_zero(self):
        empty_work_dir = Path(tempfile.mkdtemp())
        result = ds.audit(self.repo, self.since, work_dir=empty_work_dir, now=self.now)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["scanned_logs"], 0)

    def test_format_audit_empty_state_reads_as_zero_not_blank(self):
        result = ds.audit(self.repo, self.since, work_dir=Path(tempfile.mkdtemp()), now=self.now)
        self.assertIn("0 turn(s)", ds.format_audit(result))


if __name__ == "__main__":
    unittest.main()
