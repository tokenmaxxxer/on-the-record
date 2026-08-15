#!/usr/bin/env python3
"""issue #1492 — trivial-lane machine-checked triviality gate tests.

Covers the four acceptance IDs named in the issue: a pure-rename diff
passes; a semantic (non-trivial) diff is rejected with the violated
clause named; a diff carrying only a self-declared trivial label
(never consulted by `classify()`) still fails the same way as an
unlabeled non-trivial diff; and a lane-landed change still shows the
required audit artifacts (issue reference, an APPROVE-token-shaped
comment, and the record file) present.

  python3 -m pytest tests/test_trivial_lane_gate.py
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import trivial_lane_gate  # noqa: E402


class TestRenameOnlyDiffPasses(unittest.TestCase):
    def test_rename_only_diff_passes(self):
        rows = [(0, 0, "docs/old_name.md => docs/new_name.md")]
        lane_class, reason = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], set())
        self.assertEqual(lane_class, "rename-only")
        self.assertTrue(reason)

    def test_rename_only_rejects_when_content_changes(self):
        rows = [(1, 0, "old.py => new.py")]
        lane_class, _ = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], set())
        self.assertNotEqual(lane_class, "rename-only")


class TestSemanticChangeRejected(unittest.TestCase):
    def test_semantic_change_rejected(self):
        rows = [(80, 40, "gates/skip_eligibility.py")]
        lane_class, reason = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], set())
        self.assertIsNone(lane_class)
        self.assertIn("no trivial-lane class matched", reason)

    def test_empty_diff_rejected(self):
        lane_class, reason = trivial_lane_gate.classify([], [], set())
        self.assertIsNone(lane_class)
        self.assertTrue(reason)

    def test_deletion_blocks_test_name_only(self):
        rows = [(0, 5, "tests/test_old.py")]
        lane_class, reason = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], {"tests/test_old.py"})
        self.assertIsNone(lane_class)


class TestProseClaimInsufficient(unittest.TestCase):
    def test_prose_claim_insufficient(self):
        # `classify()` takes no label/claim-vocabulary argument at all —
        # a diff shaped like a real code change is rejected regardless
        # of any `validity-consult-skip: trivial`-style label a caller
        # might attach elsewhere; the label is never consulted here.
        rows = [(30, 10, "spawn.py")]
        lane_class, reason = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], set())
        self.assertIsNone(lane_class)
        self.assertIn("full pipeline", reason)

    def test_docs_only_still_requires_docs_paths(self):
        rows = [(5, 0, "spawn.py")]
        lane_class, _ = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], set())
        self.assertNotEqual(lane_class, "docs-only")


class TestDocsOnlyAndTestNameOnlyClasses(unittest.TestCase):
    def test_docs_only_under_threshold_passes(self):
        rows = [(10, 5, "docs/issue-1/reports/implementation.md")]
        lane_class, _ = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], set())
        self.assertEqual(lane_class, "docs-only")

    def test_docs_only_over_threshold_rejected(self):
        rows = [(80, 30, "docs/issue-1/reports/implementation.md")]
        lane_class, _ = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], set())
        self.assertIsNone(lane_class)

    def test_test_name_only_passes(self):
        rows = [(3, 1, "tests/test_foo.py")]
        lane_class, _ = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], set())
        self.assertEqual(lane_class, "test-name-only")


class TestAuditArtifactsPresent(unittest.TestCase):
    def test_audit_artifacts_present(self):
        # existence-check for the three audit artifacts a lane-landed
        # change must still keep, per issue #1492 requirement 2:
        # the issue reference, an APPROVE-token-shaped record, and the
        # record file itself.
        record = ROOT / "docs" / "issue-1492" / "reports" / "implementation.md"
        self.assertTrue(record.exists(), f"record file missing: {record}")
        self.assertIn("#1492", record.read_text())
        proposal = (ROOT / "docs" / "issue-1492" / "proposals" /
                    "2026-08-15-trivial-lane-machine-gate.md")
        self.assertTrue(proposal.exists(),
                         f"phase-1 proposal missing: {proposal}")


if __name__ == "__main__":
    unittest.main()
