#!/usr/bin/env python3
"""issue #1791 — auto-approval shadow wiring at the approval-observation
call site (`gates/ci.py:_autodetect_issue_phase` -> `_shadow_wire_approval_observation`).

Acceptance 1: a simulated approval event drives `_autodetect_issue_phase`
to observe phase2 and produces exactly one appended sample in both the
audit log and the state file; `on-the-record/hooks/approval-gate.sh` is
byte-identical (diff assertion against the repo's working copy).

Acceptance 2: an exception inside the shadow call site (gate composition
or `shadow_verdict()` itself) is caught, logged as a degraded sample, and
never propagates into `_autodetect_issue_phase()`'s/`check()`'s own
return value.

No network, no real `gh` calls — everything the shadow call touches is
monkeypatched at the module level, the same convention
`gates/test_closes_gate_ci.py` and `gates/test_auto_approval_class.py`
already use.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gates"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ci
import spawn
import auto_approval_class as aac
import scope_adherence
import merge_gate
import requirement_met

REPO_ROOT = Path(__file__).resolve().parent.parent


def _install_approval(monkeypatch_targets, issue: int, approver: str = "jjongkwann"):
    """Simulate one qualifying `APPROVE issue-<n>/<role>` issue comment."""
    orig_approvers, orig_comments, orig_reviews = (
        spawn._approvers, spawn._issue_comments, ci._pr_reviews)
    spawn._approvers = lambda repo: {approver}
    spawn._issue_comments = (
        lambda repo, n: ([{"login": approver, "body": f"APPROVE issue-{issue}/implementation"}], True)
        if n == issue else ([], True))
    ci._pr_reviews = lambda repo, pr: []
    monkeypatch_targets.append((orig_approvers, orig_comments, orig_reviews))
    return orig_approvers, orig_comments, orig_reviews


class ShadowWiringTestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmpdir.name)
        (self.repo / "docs" / "specs").mkdir(parents=True)
        (self.repo / "docs" / "specs" / "auto-approval-config.json").write_text(
            json.dumps({"shadow_mode": True, "quota_per_24h": 5}))
        self._restore = []
        self._restore.append(("spawn._approvers", spawn._approvers))
        self._restore.append(("spawn._issue_comments", spawn._issue_comments))
        self._restore.append(("ci._pr_reviews", ci._pr_reviews))
        self._restore.append(("ci._pr_head_ref", ci._pr_head_ref))
        self._restore.append(("ci._shadow_diff_paths", ci._shadow_diff_paths))
        ci._pr_head_ref = lambda repo, pr: "issue-1791/implementation"
        self._restore.append(("scope_adherence.check", scope_adherence.check))
        self._restore.append(("merge_gate.stale_revert_reasons", merge_gate.stale_revert_reasons))
        self._restore.append(("requirement_met.check", requirement_met.check))

    def tearDown(self):
        self.tmpdir.cleanup()
        for target, value in self._restore:
            mod_name, attr = target.split(".")
            mod = {"spawn": spawn, "ci": ci, "scope_adherence": scope_adherence,
                   "merge_gate": merge_gate, "requirement_met": requirement_met}[mod_name]
            setattr(mod, attr, value)

    def _approve(self, issue: int):
        approver = "jjongkwann"
        spawn._approvers = lambda repo: {approver}
        spawn._issue_comments = (
            lambda repo, n: ([{"login": approver, "body": f"APPROVE issue-{issue}/implementation"}], True)
            if n == issue else ([], True))
        ci._pr_reviews = lambda repo, pr: []

    def _no_approval(self):
        spawn._approvers = lambda repo: {"jjongkwann"}
        spawn._issue_comments = lambda repo, n: ([], True)
        ci._pr_reviews = lambda repo, pr: []

    def _stub_clean_gates(self, diff_paths=None):
        ci._shadow_diff_paths = lambda repo, pr: list(diff_paths or ["docs/reports/foo.md"])
        scope_adherence.check = lambda repo, issue, pr: (scope_adherence.PASS, None)
        merge_gate.stale_revert_reasons = lambda repo, pr: []
        requirement_met.check = lambda repo, issue, pr: {"blocked": False, "advisory": [], "blocking_reasons": []}

    def _state(self):
        state_path = self.repo / aac.DEFAULT_STATE_PATH
        if not state_path.exists():
            return {}
        return json.loads(state_path.read_text())

    def _audit_log_text(self):
        audit_log_path = self.repo / aac.DEFAULT_AUDIT_LOG_PATH
        if not audit_log_path.exists():
            return ""
        return audit_log_path.read_text()


class SimulatedApprovalAppendsSampleTest(ShadowWiringTestBase):
    """Acceptance 1: simulated approval event -> sample appended; diff
    assertion on approval-gate.sh."""

    def test_phase2_observation_appends_one_sample_to_audit_log_and_state(self):
        self._approve(issue=1791)
        self._stub_clean_gates()

        result = ci._autodetect_issue_phase(self.repo, pr=42, issue=1791, phase=None)

        self.assertEqual(result, (1791, "phase2"))

        audit_text = self._audit_log_text()
        self.assertIn("issue=1791", audit_text)
        self.assertIn("pr=42", audit_text)
        self.assertEqual(audit_text.count("issue=1791 | pr=42"), 1)

        state = self._state()
        self.assertIn([1791, 42], state.get("shadow_wired_pairs", []))

    def test_repeated_observation_of_same_pr_appends_exactly_one_sample(self):
        # "first observes phase2" — a second CI tick over the same
        # already-approved (issue, pr) must not append a second sample.
        self._approve(issue=1791)
        self._stub_clean_gates()

        ci._autodetect_issue_phase(self.repo, pr=42, issue=1791, phase=None)
        ci._autodetect_issue_phase(self.repo, pr=42, issue=1791, phase=None)

        audit_text = self._audit_log_text()
        self.assertEqual(audit_text.count("issue=1791 | pr=42"), 1)

    def test_empty_state_no_approval_appends_no_sample_state_file_unchanged(self):
        self._no_approval()
        self._stub_clean_gates()

        result = ci._autodetect_issue_phase(self.repo, pr=42, issue=1791, phase=None)

        self.assertEqual(result, (1791, "phase1"))
        self.assertFalse((self.repo / aac.DEFAULT_AUDIT_LOG_PATH).exists())
        self.assertFalse((self.repo / aac.DEFAULT_STATE_PATH).exists())

    def test_approval_gate_sh_is_byte_identical(self):
        """diff assertion: this PR's approval-gate.sh (working tree) must
        be byte-identical to origin/main's copy."""
        hook_path = "on-the-record/hooks/approval-gate.sh"
        r = subprocess.run(["git", "diff", "--exit-code", "origin/main", "HEAD", "--", hook_path],
                            cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0,
                          f"{hook_path} changed against origin/main:\n{r.stdout}\n{r.stderr}")


class FaultInjectionTest(ShadowWiringTestBase):
    """Acceptance 2: a raised exception inside the shadow call site
    leaves the watch/poll path functioning and logs a degraded sample."""

    def test_exception_in_gate_composition_is_caught_and_logged_as_degraded(self):
        self._approve(issue=1791)

        def _boom(repo, pr):
            raise RuntimeError("simulated gate-composition failure")

        ci._shadow_diff_paths = _boom
        scope_adherence.check = lambda repo, issue, pr: (scope_adherence.PASS, None)
        merge_gate.stale_revert_reasons = lambda repo, pr: []
        requirement_met.check = lambda repo, issue, pr: {"blocked": False, "advisory": [], "blocking_reasons": []}

        result = ci._autodetect_issue_phase(self.repo, pr=42, issue=1791, phase=None)

        # check()'s own control flow is unaffected: phase is still phase2.
        self.assertEqual(result, (1791, "phase2"))

        audit_text = self._audit_log_text()
        self.assertIn("class=degraded", audit_text)
        self.assertIn("issue=1791", audit_text)
        self.assertIn("pr=42", audit_text)
        self.assertIn("simulated gate-composition failure", audit_text)

    def test_exception_in_shadow_verdict_itself_is_caught_and_logged_as_degraded(self):
        self._approve(issue=1791)
        self._stub_clean_gates()

        orig_shadow_verdict = aac.shadow_verdict
        try:
            aac.shadow_verdict = lambda *a, **kw: (_ for _ in ()).throw(
                RuntimeError("simulated shadow_verdict failure"))

            result = ci._autodetect_issue_phase(self.repo, pr=42, issue=1791, phase=None)

            self.assertEqual(result, (1791, "phase2"))
            audit_text = self._audit_log_text()
            self.assertIn("class=degraded", audit_text)
            self.assertIn("simulated shadow_verdict failure", audit_text)
        finally:
            aac.shadow_verdict = orig_shadow_verdict

    def test_state_file_read_corruption_does_not_break_check(self):
        # Corrupt state file (unparseable JSON) — the shadow call must
        # still fail closed to "not yet recorded" and never raise into
        # the caller.
        self._approve(issue=1791)
        self._stub_clean_gates()
        state_path = self.repo / aac.DEFAULT_STATE_PATH
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text("{not json")

        result = ci._autodetect_issue_phase(self.repo, pr=42, issue=1791, phase=None)

        self.assertEqual(result, (1791, "phase2"))


if __name__ == "__main__":
    unittest.main()
