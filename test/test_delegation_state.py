"""issue #3061: standing delegation as machine-visible state, and the
after-the-fact audit for a turn that asked for authority a recorded
delegation already covered.

Test derivation (test-derivation skill), by requirement:

- delegation_state.py's grant/read/revoke/expiry cycle is a
  state-transition problem (NONE -> IN_FORCE -> {REVOKED, EXPIRED}) --
  DelegationStateTransitionsTest, unchanged shape from before this
  round's manifest repair, plus one new transition case for the
  manifest field itself.
- is_covered()'s matching rule is a 3-condition AND decision (tool
  matches AND resource glob matches AND repo glob matches) -- tested
  MC/DC-style in ManifestLookupConditionsTest, one baseline-true case
  per condition flipped to show it independently controls the
  covered/not-covered outcome.
- parse_allow_spec()'s TOOL:RESOURCE[:REPO] grammar is an equivalence
  partition problem (well-formed 2-part / well-formed 3-part / missing
  tool / missing resource / empty spec) -- AllowSpecParsingTest.
- audit()'s flagging rule is a 5-condition AND decision (no tool_use in
  the ask event AND text non-empty AND delegation in force AND
  timestamp >= since AND a later tool_use exists whose action
  is_covered()) -- AuditFlaggingConditionsTest, MC/DC-style again.
- The regression requirement -- four real turns four independent
  verification rounds (PR #3097, #3102, #3107, #3122) each found
  wrongly flagged as redundant by the old lexical classifier must now
  correctly NOT be flagged -- is RegressionFailureCasesTest: each case
  is the real quoted text as the ask, plus a next action the case's own
  manifest does not cover.
- The must-not's positive half -- this is not "always say no" -- is
  covered by the one true-positive case in AuditFlaggingConditionsTest
  (a covered action following a stop IS flagged).
- The escalate-by-default requirement (three actions outside any
  manifest) is DefaultEscalationTest, calling is_covered() directly
  rather than through audit() -- this is the live-facing property a
  future pre-ask hook would call, not just the retrospective audit.

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


def _assistant_text_event(ts: datetime, text: str) -> dict:
    return {"type": "assistant", "timestamp": ts.isoformat(),
            "message": {"content": [{"type": "text", "text": text}]}}


def _assistant_tool_use_event(ts: datetime, tool: str, resource_field: str,
                               resource_value: str, text: str | None = None) -> dict:
    content = []
    if text is not None:
        content.append({"type": "text", "text": text})
    content.append({"type": "tool_use", "id": "t1", "name": tool,
                     "input": {resource_field: resource_value}})
    return {"type": "assistant", "timestamp": ts.isoformat(),
            "message": {"content": content}}


class DelegationStateTransitionsTest(unittest.TestCase):
    """R1: NONE -> IN_FORCE -> {REVOKED, EXPIRED}, plus the invalid-
    transition guards (revoke from NONE, self-grant from a skill-bound
    session, empty-scope grant), plus the manifest field's own
    default/round-trip."""

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

    def test_grant_with_no_manifest_argument_stores_an_empty_manifest_not_a_permissive_one(self):
        # issue #3061 seam change: omitting --allow / manifest= must not
        # silently grant coverage of everything -- it grants coverage of
        # nothing, and describe() must say so plainly.
        now = datetime.now(timezone.utc)
        record = ds.grant(self.repo, "쭉 해", "jiwon", now=now, skill_env="")
        self.assertEqual(record["manifest"], [])
        self.assertIn("manifest: 0 action(s)", ds.describe(self.repo, now=now))
        self.assertFalse(ds.is_covered({"tool": "Bash", "resource": "git status"},
                                        record["manifest"]))

    def test_grant_with_explicit_manifest_round_trips_through_load_state(self):
        now = datetime.now(timezone.utc)
        manifest = [{"tool": "Bash", "resource": "git *", "repo": "*"}]
        ds.grant(self.repo, "scope", "jiwon", now=now, skill_env="", manifest=manifest)
        self.assertEqual(ds.load_state(self.repo)["manifest"], manifest)

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

    def test_legacy_record_with_no_manifest_key_reads_as_empty_not_a_crash(self):
        # silent-failure-audit finding: a record written before this
        # module's manifest field existed has no "manifest" key at all.
        # audit()/is_covered() must default that to "covers nothing",
        # never raise and never treat it as "covers everything".
        now = datetime.now(timezone.utc)
        ds.grant(self.repo, "scope", "jiwon", now=now, skill_env="")
        path = Path(self.repo) / ds.STATE_REL_PATH
        record = json.loads(path.read_text())
        del record["manifest"]
        path.write_text(json.dumps(record))
        loaded = ds.load_state(self.repo)
        self.assertNotIn("manifest", loaded)
        self.assertFalse(ds.is_covered({"tool": "Bash", "resource": "git status"},
                                        loaded.get("manifest")))


class AllowSpecParsingTest(unittest.TestCase):
    """R2 authoring surface: parse_allow_spec()'s TOOL:RESOURCE[:REPO]
    grammar, by equivalence partition (well-formed 2-part, well-formed
    3-part, missing tool, missing resource, empty spec, resource itself
    containing a colon)."""

    def test_two_part_spec_defaults_repo_to_wildcard(self):
        self.assertEqual(ds.parse_allow_spec("Bash:git *"),
                          {"tool": "Bash", "resource": "git *", "repo": "*"})

    def test_three_part_spec_captures_explicit_repo(self):
        self.assertEqual(
            ds.parse_allow_spec("Bash:gh pr *:on-the-record"),
            {"tool": "Bash", "resource": "gh pr *", "repo": "on-the-record"})

    def test_missing_colon_raises(self):
        with self.assertRaises(ValueError):
            ds.parse_allow_spec("Bash git status")

    def test_empty_tool_raises(self):
        with self.assertRaises(ValueError):
            ds.parse_allow_spec(":git *")

    def test_empty_resource_raises(self):
        with self.assertRaises(ValueError):
            ds.parse_allow_spec("Bash:")

    def test_empty_spec_raises(self):
        with self.assertRaises(ValueError):
            ds.parse_allow_spec("")


class ManifestLookupConditionsTest(unittest.TestCase):
    """R2 core: is_covered()'s AND decision (tool matches AND resource
    glob matches AND repo glob matches), MC/DC-style -- one
    baseline-true case, then one condition flipped false at a time."""

    def setUp(self):
        self.manifest = [{"tool": "Bash", "resource": "git *", "repo": "on-the-record"}]

    def test_baseline_all_conditions_true_is_covered(self):
        self.assertTrue(ds.is_covered(
            {"tool": "Bash", "resource": "git status"}, self.manifest,
            repo="on-the-record"))

    def test_tool_mismatch_is_not_covered(self):
        self.assertFalse(ds.is_covered(
            {"tool": "Edit", "resource": "git status"}, self.manifest,
            repo="on-the-record"))

    def test_resource_glob_mismatch_is_not_covered(self):
        self.assertFalse(ds.is_covered(
            {"tool": "Bash", "resource": "rm -rf /"}, self.manifest,
            repo="on-the-record"))

    def test_repo_glob_mismatch_is_not_covered(self):
        self.assertFalse(ds.is_covered(
            {"tool": "Bash", "resource": "git status"}, self.manifest,
            repo="some-other-repo"))

    def test_empty_manifest_covers_nothing(self):
        self.assertFalse(ds.is_covered(
            {"tool": "Bash", "resource": "git status"}, [], repo="on-the-record"))

    def test_none_manifest_covers_nothing_not_a_crash(self):
        self.assertFalse(ds.is_covered(
            {"tool": "Bash", "resource": "git status"}, None, repo="on-the-record"))

    def test_wildcard_repo_entry_matches_any_repo(self):
        manifest = [{"tool": "Bash", "resource": "git *", "repo": "*"}]
        self.assertTrue(ds.is_covered(
            {"tool": "Bash", "resource": "git log"}, manifest, repo="anything"))

    def test_repo_none_skips_the_repo_check(self):
        # audit() always passes a repo; a direct caller that doesn't
        # know/care about repo scoping (e.g. a quick manual check) can
        # omit it, and the entry's repo glob is simply not consulted.
        self.assertTrue(ds.is_covered(
            {"tool": "Bash", "resource": "git status"}, self.manifest, repo=None))


class DefaultEscalationTest(unittest.TestCase):
    """R2 must-not, structural half: an action deliberately outside
    every manifest entry defaults to escalation (not covered) -- called
    directly against is_covered(), the same primitive a live pre-ask
    check would use, not routed through audit()'s transcript scan."""

    def setUp(self):
        # A realistic, non-trivial manifest -- ordinary git/gh read
        # operations -- so "not covered" here means "not enumerated",
        # not "manifest happens to be empty".
        self.manifest = [
            {"tool": "Bash", "resource": "git status", "repo": "*"},
            {"tool": "Bash", "resource": "git log*", "repo": "*"},
            {"tool": "Bash", "resource": "gh pr view*", "repo": "*"},
        ]

    def test_destructive_shell_command_outside_manifest_escalates(self):
        self.assertFalse(ds.is_covered(
            {"tool": "Bash", "resource": "rm -rf /var/lib/postgres"},
            self.manifest, repo="on-the-record"))

    def test_force_push_outside_manifest_escalates(self):
        self.assertFalse(ds.is_covered(
            {"tool": "Bash", "resource": "git push --force origin main"},
            self.manifest, repo="on-the-record"))

    def test_privileged_pr_merge_outside_manifest_escalates(self):
        self.assertFalse(ds.is_covered(
            {"tool": "Bash", "resource": "gh pr merge --admin 123"},
            self.manifest, repo="on-the-record"))


class RegressionFailureCasesTest(unittest.TestCase):
    """The four real historical misclassifications, one per independent
    verification round that found the old lexical classifier flagging a
    genuine escalation as redundant. Each is expressed as the real
    quoted ask text, plus the real irreversible action that ask was
    actually about, against a manifest that (realistically) does not
    cover it -- and audit() must NOT flag any of them."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = str(Path(self._tmp.name) / "myrepo")
        Path(self.repo).mkdir()
        self.work_dir = Path(self._tmp.name) / "work"
        self.work_dir.mkdir()
        self.log = self.work_dir / "myrepo.session.1.1.log"
        self.now = datetime.now(timezone.utc)
        self.granted_at = self.now - timedelta(hours=1)
        # A manifest covering only ordinary, reversible git/gh reads --
        # none of the four cases' actual actions (a DROP TABLE, a
        # customer-data delete, a prod deploy, a secret rotation) match
        # it, which is the point: these are genuinely uncovered actions.
        self.manifest = [
            {"tool": "Bash", "resource": "git *", "repo": "*"},
            {"tool": "Bash", "resource": "gh pr *", "repo": "*"},
        ]
        ds.grant(self.repo, "다 판단해서 처분해서 해", "jiwon", now=self.granted_at,
                  skill_env="", manifest=self.manifest)
        self.since = (self.now - timedelta(days=1)).strftime("%Y-%m-%d")

    def tearDown(self):
        self._tmp.cleanup()

    def _audit_count(self, ask_text: str, next_command: str) -> int:
        events = [
            _assistant_text_event(self.now, ask_text),
            _assistant_tool_use_event(
                self.now + timedelta(seconds=5), "Bash", "command", next_command),
        ]
        _write_log(self.log, events)
        result = ds.audit(self.repo, self.since, work_dir=self.work_dir, now=self.now)
        return result["count"]

    def test_pr3097_dropping_the_legacy_table_is_not_flagged(self):
        # PR #3097 (first independent verification of PR #3087): five
        # genuine escalations misflagged by the first lexical cut; this
        # is the one quoted verbatim in that record's Criterion 2.
        count = self._audit_count(
            "Should I proceed with dropping the legacy table? This is "
            "irreversible and I want to confirm the call is still yours "
            "to make, not mine.",
            "psql prod -c 'DROP TABLE legacy_table;'")
        self.assertEqual(count, 0)

    def test_pr3102_deleting_the_customer_table_is_not_flagged(self):
        # PR #3102 (second independent verification): the narrowed
        # classifier's own bare-stem generalization flagged this one --
        # quoted verbatim from that record's finding.
        count = self._audit_count(
            "프로덕션 DB의 고객 테이블을 지금 삭제하는 작업을 진행할까요? "
            "되돌릴 수 없는 작업이라 운영자 판단이 필요합니다.",
            "psql prod -c 'DELETE FROM customers;'")
        self.assertEqual(count, 0)

    def test_pr3107_the_irreversible_prod_deploy_is_not_flagged(self):
        # PR #3107 (third independent verification): the trailing-
        # punctuation-fixed classifier still flagged this one -- quoted
        # verbatim from that record's finding.
        count = self._audit_count(
            "이 작업은 되돌릴 수 없습니다. 프로덕션 배포를 진행할까요?",
            "./deploy-prod.sh")
        self.assertEqual(count, 0)

    def test_pr3122_the_prod_secret_rotation_is_not_flagged(self):
        # PR #3122 (fourth independent verification, of the repair
        # round): 3 of 6 genuine escalations built to share a retained
        # idiom were misflagged -- quoted verbatim from that record's
        # reproduction (the "이대로 갈까요?" idiom case).
        count = self._audit_count(
            "이대로 갈까요? 이 변경은 프로덕션 시크릿을 회전시키므로 "
            "기존 세션이 모두 끊깁니다.",
            "rotate-prod-secrets.sh --all")
        self.assertEqual(count, 0)


class AuditFlaggingConditionsTest(unittest.TestCase):
    """audit()'s flagging decision, MC/DC-style: one baseline-true case
    (a covered action DOES get flagged -- the must-not's positive half,
    proving this isn't just "always say no"), then one condition
    flipped false at a time."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = str(Path(self._tmp.name) / "myrepo")
        Path(self.repo).mkdir()
        self.work_dir = Path(self._tmp.name) / "work"
        self.work_dir.mkdir()
        self.log = self.work_dir / "myrepo.session.1.1.log"
        self.now = datetime.now(timezone.utc)
        self.granted_at = self.now - timedelta(hours=1)
        self.manifest = [{"tool": "Bash", "resource": "git *", "repo": "*"}]
        ds.grant(self.repo, "다 판단해서 처분해서 해", "jiwon", now=self.granted_at,
                  skill_env="", manifest=self.manifest)
        self.since = (self.now - timedelta(days=1)).strftime("%Y-%m-%d")

    def tearDown(self):
        self._tmp.cleanup()

    def _audit_count(self, events: list[dict]) -> int:
        _write_log(self.log, events)
        result = ds.audit(self.repo, self.since, work_dir=self.work_dir, now=self.now)
        return result["count"]

    def _baseline_events(self):
        return [
            _assistant_text_event(self.now, "계속 진행할까요?"),
            _assistant_tool_use_event(
                self.now + timedelta(seconds=5), "Bash", "command", "git status"),
        ]

    def test_baseline_stop_then_covered_action_is_flagged(self):
        # The must-not's positive half: a stop that was genuinely
        # avoidable -- the next action was already in the manifest --
        # IS flagged. This is not a design that always says "genuine".
        self.assertEqual(self._audit_count(self._baseline_events()), 1)

    def test_tool_use_in_the_same_event_as_the_ask_is_not_a_stop_not_flagged(self):
        events = [
            _assistant_tool_use_event(
                self.now, "Bash", "command", "git status", text="계속 진행할까요?"),
        ]
        self.assertEqual(self._audit_count(events), 0)

    def test_empty_text_ask_event_is_not_flagged(self):
        events = [
            _assistant_text_event(self.now, ""),
            _assistant_tool_use_event(
                self.now + timedelta(seconds=5), "Bash", "command", "git status"),
        ]
        self.assertEqual(self._audit_count(events), 0)

    def test_delegation_not_in_force_is_not_flagged(self):
        ds.revoke(self.repo, "jiwon", now=self.now - timedelta(minutes=30))
        self.assertEqual(self._audit_count(self._baseline_events()), 0)

    def test_timestamp_before_since_cutoff_is_not_flagged(self):
        before_since = self.now - timedelta(days=2)
        events = [
            _assistant_text_event(before_since, "계속 진행할까요?"),
            _assistant_tool_use_event(
                before_since + timedelta(seconds=5), "Bash", "command", "git status"),
        ]
        self.assertEqual(self._audit_count(events), 0)

    def test_timestamp_before_grant_is_not_flagged(self):
        before_grant = self.granted_at - timedelta(minutes=1)
        events = [
            _assistant_text_event(before_grant, "계속 진행할까요?"),
            _assistant_tool_use_event(
                before_grant + timedelta(seconds=5), "Bash", "command", "git status"),
        ]
        self.assertEqual(self._audit_count(events), 0)

    def test_next_action_not_covered_by_manifest_is_not_flagged(self):
        events = [
            _assistant_text_event(self.now, "계속 진행할까요?"),
            _assistant_tool_use_event(
                self.now + timedelta(seconds=5), "Bash", "command", "rm -rf /"),
        ]
        self.assertEqual(self._audit_count(events), 0)

    def test_no_later_tool_use_event_at_all_is_not_flagged(self):
        # The log ends right at the ask -- there is nothing to check the
        # stop against, so this cannot be established as avoidable.
        events = [_assistant_text_event(self.now, "계속 진행할까요?")]
        self.assertEqual(self._audit_count(events), 0)

    def test_the_words_of_the_ask_no_longer_matter_at_all(self):
        # Central property of the redesign: text content plays no part
        # in the decision anymore. A completely different sentence,
        # paired with the same covered next action, is flagged exactly
        # like the baseline -- and a question using none of the old
        # classifier's retired idioms still flags when its next action
        # is covered.
        events = [
            _assistant_text_event(self.now, "Want me to keep going with this?"),
            _assistant_tool_use_event(
                self.now + timedelta(seconds=5), "Bash", "command", "git log --oneline"),
        ]
        self.assertEqual(self._audit_count(events), 1)

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

    def test_format_audit_flagged_entry_names_the_covering_action(self):
        self._audit_count(self._baseline_events())
        result = ds.audit(self.repo, self.since, work_dir=self.work_dir, now=self.now)
        text = ds.format_audit(result)
        self.assertIn("Bash", text)
        self.assertIn("git status", text)


if __name__ == "__main__":
    unittest.main()
