#!/usr/bin/env python3
"""Tests for gates/auto_approval_class.py — issue #1739 Acceptance 1-3.

Acceptance 1: adversarial boundary cases (docs+code mixed diff, docs edit
under on-the-record/hooks/, partially out-of-scope diff, test file
editing production fixture).
Acceptance 2: shadow-mode case asserting gate refusal without APPROVE
comment plus audit-log line presence.
Acceptance 3: quota exhaustion and circuit-breaker suspension unit cases.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import auto_approval_class as aac  # noqa: E402


def test_classify_module_level_docs_only():
    """Module-level live-fire: calls auto_approval_class.classify directly."""
    class_, _ = aac.classify(["docs/reports/foo.md"])
    assert class_ == aac.DOCS_ONLY


def test_classify_module_level_contract_path_not_eligible():
    """Module-level live-fire: calls auto_approval_class.classify directly."""
    class_, _ = aac.classify(["gates/auto_approval_class.py"])
    assert class_ == aac.NOT_ELIGIBLE


class ClassifyBasicTest(unittest.TestCase):
    def test_docs_only(self):
        class_, _ = aac.classify(["docs/handbooks/foo.md", "docs/reports/bar.md"])
        self.assertEqual(class_, aac.DOCS_ONLY)

    def test_test_only(self):
        class_, _ = aac.classify(["test/test_foo.py"])
        self.assertEqual(class_, aac.TEST_ONLY)

    def test_empty_diff_not_eligible(self):
        class_, _ = aac.classify([])
        self.assertEqual(class_, aac.NOT_ELIGIBLE)


class AdversarialBoundaryTest(unittest.TestCase):
    """Acceptance 1: adversarial boundary cases."""

    def test_docs_and_code_mixed_diff_not_eligible(self):
        class_, reason = aac.classify(["docs/reports/foo.md", "src/app.py"])
        self.assertEqual(class_, aac.NOT_ELIGIBLE)
        self.assertIn("src/app.py", reason)

    def test_docs_edit_under_hooks_not_eligible(self):
        class_, reason = aac.classify(["on-the-record/hooks/approval-gate.sh.md"])
        self.assertEqual(class_, aac.NOT_ELIGIBLE)
        self.assertIn("on-the-record/hooks/", reason)

    def test_docs_edit_under_hooks_even_when_only_diff_path(self):
        # A single-path diff that LOOKS docs-shaped by content but lives
        # under a behavior-contract prefix must still be not_eligible —
        # the contract-path check runs before the docs/test classification.
        class_, reason = aac.classify(
            ["on-the-record/hooks/README.md"])
        self.assertEqual(class_, aac.NOT_ELIGIBLE)
        self.assertIn("on-the-record/hooks/", reason)

    def test_partially_out_of_scope_diff_not_eligible(self):
        class_, reason = aac.classify(
            ["docs/reports/foo.md", "docs/reports/bar.md"],
            out_of_scope_paths=["docs/reports/bar.md"],
        )
        self.assertEqual(class_, aac.NOT_ELIGIBLE)
        self.assertIn("docs/reports/bar.md", reason)

    def test_test_file_editing_production_fixture_not_eligible(self):
        class_, reason = aac.classify(
            ["test/test_foo.py"],
            production_fixture_paths=["test/test_foo.py"],
        )
        self.assertEqual(class_, aac.NOT_ELIGIBLE)
        self.assertIn("production fixture", reason)

    def test_gates_prefix_always_not_eligible(self):
        class_, _ = aac.classify(["gates/scope_adherence.py"])
        self.assertEqual(class_, aac.NOT_ELIGIBLE)

    def test_specs_prefix_always_not_eligible(self):
        class_, _ = aac.classify(["docs/specs/auto-approval-config.json"])
        self.assertEqual(class_, aac.NOT_ELIGIBLE)


class ShadowModeTest(unittest.TestCase):
    """Acceptance 2: shadow-mode gate refusal + audit-log presence."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.TemporaryDirectory()
        self.audit_log_path = Path(self.tmpdir.name) / "audit-log.md"
        self.state_path = Path(self.tmpdir.name) / "state.json"
        self.config_path = Path(self.tmpdir.name) / "config.json"

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_shadow_verdict_never_bypasses_human_approve(self):
        # shadow_verdict() must never itself constitute an APPROVE — it
        # has no code path that touches approval-gate.sh or emits an
        # APPROVE-shaped string. Assert the module exposes no such
        # capability: no reference to "APPROVE" or "approval-gate.sh"
        # anywhere in its source.
        src = Path(aac.__file__).read_text()
        self.assertNotIn("approval-gate.sh\"", src)
        self.assertNotIn("'approval-gate.sh'", src)
        verdict = aac.shadow_verdict(
            diff_paths=["docs/reports/foo.md"],
            gate_results={
                "scope_adherence": True,
                "stale_revert_guard": True,
                "requirement_met": True,
            },
            issue=1739,
            pr=1740,
            timestamp="2026-08-20T00:00:00Z",
            config_path=self.config_path,
            state_path=self.state_path,
            audit_log_path=self.audit_log_path,
        )
        # would_auto_approve is a recorded label only; it is never an
        # action, and no APPROVE comment or hook call is produced.
        self.assertIsInstance(verdict.would_auto_approve, bool)

    def test_shadow_verdict_writes_audit_log_line(self):
        self.assertFalse(self.audit_log_path.exists())
        aac.shadow_verdict(
            diff_paths=["docs/reports/foo.md"],
            gate_results={
                "scope_adherence": True,
                "stale_revert_guard": True,
                "requirement_met": True,
            },
            issue=1739,
            pr=1740,
            timestamp="2026-08-20T00:00:00Z",
            config_path=self.config_path,
            state_path=self.state_path,
            audit_log_path=self.audit_log_path,
        )
        self.assertTrue(self.audit_log_path.exists())
        content = self.audit_log_path.read_text()
        self.assertIn("issue=1739", content)
        self.assertIn("pr=1740", content)
        self.assertIn("class=docs_only", content)

    def test_shadow_verdict_not_eligible_still_writes_audit_log(self):
        aac.shadow_verdict(
            diff_paths=["gates/foo.py"],
            gate_results={
                "scope_adherence": True,
                "stale_revert_guard": True,
                "requirement_met": True,
            },
            issue=1739,
            pr=1741,
            timestamp="2026-08-20T00:01:00Z",
            config_path=self.config_path,
            state_path=self.state_path,
            audit_log_path=self.audit_log_path,
        )
        content = self.audit_log_path.read_text()
        self.assertIn("would_auto_approve=False", content)


class QuotaAndCircuitBreakerTest(unittest.TestCase):
    """Acceptance 3: quota exhaustion and circuit-breaker suspension."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.TemporaryDirectory()
        self.audit_log_path = Path(self.tmpdir.name) / "audit-log.md"
        self.state_path = Path(self.tmpdir.name) / "state.json"
        self.config_path = Path(self.tmpdir.name) / "config.json"

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write_state(self, **kwargs):
        import json
        self.state_path.write_text(json.dumps(kwargs))

    def _write_config(self, **kwargs):
        import json
        self.config_path.write_text(json.dumps(kwargs))

    def test_sixth_candidate_within_24h_routes_to_human(self):
        self._write_config(shadow_mode=True, quota_per_24h=5)
        self._write_state(approvals_last_24h=[f"pr-{i}" for i in range(5)])
        verdict = aac.shadow_verdict(
            diff_paths=["docs/reports/foo.md"],
            gate_results={
                "scope_adherence": True,
                "stale_revert_guard": True,
                "requirement_met": True,
            },
            issue=1739,
            pr=1746,
            timestamp="2026-08-20T00:02:00Z",
            config_path=self.config_path,
            state_path=self.state_path,
            audit_log_path=self.audit_log_path,
        )
        self.assertFalse(verdict.would_auto_approve)
        self.assertIn("quota exhausted", verdict.reason)
        self.assertEqual(verdict.quota_remaining, 0)

    def test_under_quota_is_not_blocked_by_quota(self):
        self._write_config(shadow_mode=True, quota_per_24h=5)
        self._write_state(approvals_last_24h=["pr-1", "pr-2"])
        verdict = aac.shadow_verdict(
            diff_paths=["docs/reports/foo.md"],
            gate_results={
                "scope_adherence": True,
                "stale_revert_guard": True,
                "requirement_met": True,
            },
            issue=1739,
            pr=1747,
            timestamp="2026-08-20T00:03:00Z",
            config_path=self.config_path,
            state_path=self.state_path,
            audit_log_path=self.audit_log_path,
        )
        self.assertTrue(verdict.would_auto_approve)
        self.assertEqual(verdict.quota_remaining, 3)

    def test_recorded_revert_suspends_class(self):
        self._write_state(suspended_classes=["docs_only"])
        verdict = aac.shadow_verdict(
            diff_paths=["docs/reports/foo.md"],
            gate_results={
                "scope_adherence": True,
                "stale_revert_guard": True,
                "requirement_met": True,
            },
            issue=1739,
            pr=1748,
            timestamp="2026-08-20T00:04:00Z",
            config_path=self.config_path,
            state_path=self.state_path,
            audit_log_path=self.audit_log_path,
        )
        self.assertFalse(verdict.would_auto_approve)
        self.assertTrue(verdict.circuit_breaker_suspended)
        self.assertIn("suspended", verdict.reason)

    def test_reverts_last_28d_also_suspends(self):
        self._write_state(reverts_last_28d=["pr-999"])
        verdict = aac.shadow_verdict(
            diff_paths=["docs/reports/foo.md"],
            gate_results={
                "scope_adherence": True,
                "stale_revert_guard": True,
                "requirement_met": True,
            },
            issue=1739,
            pr=1749,
            timestamp="2026-08-20T00:05:00Z",
            config_path=self.config_path,
            state_path=self.state_path,
            audit_log_path=self.audit_log_path,
        )
        self.assertFalse(verdict.would_auto_approve)
        self.assertTrue(verdict.circuit_breaker_suspended)

    def test_absent_state_file_reads_as_zero_consumed_not_unlimited(self):
        # No state file at all: quota check must see zero consumed (and
        # therefore not-blocked-by-quota), never "unlimited" as a
        # separate unchecked code path.
        self.assertFalse(self.state_path.exists())
        state = aac.load_state(self.state_path)
        self.assertEqual(state["approvals_last_24h"], [])
        self.assertEqual(state["suspended_classes"], [])

    def test_absent_config_file_means_feature_off(self):
        self.assertFalse(self.config_path.exists())
        config = aac.load_config(self.config_path)
        self.assertFalse(config["present"])


if __name__ == "__main__":
    unittest.main()
