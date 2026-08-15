#!/usr/bin/env python3
"""issue #745 Item 3 — three-axis skip-eligibility classification.

Covers: each axis's trip condition, the population S vs R decision
(ALL three low-risk -> S), and that any single axis tripping forces R.

  python3 gates/test_skip_eligibility.py
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import skip_eligibility  # noqa: E402


class NonDocsLinesChanged(unittest.TestCase):
    def test_docs_only_rows_do_not_count(self):
        rows = [(10, 5, "docs/issue-1/reports/implementation.md"),
                (20, 0, "docs/proposals/x.md")]
        self.assertEqual(skip_eligibility.non_docs_lines_changed(rows), 0)

    def test_non_docs_rows_summed(self):
        rows = [(10, 5, "spawn.py"), (1, 1, "docs/x.md")]
        self.assertEqual(skip_eligibility.non_docs_lines_changed(rows), 15)


class HardToRevertHit(unittest.TestCase):
    def test_gates_python_path_hits(self):
        rows = [(1, 0, "gates/spawn_on_pr.py")]
        self.assertEqual(
            skip_eligibility.hard_to_revert_hit(rows, set()),
            "gates/spawn_on_pr.py")

    def test_hooks_shell_and_hooks_json_hit(self):
        for path in ["on-the-record/hooks/pr-preflight.sh",
                     "on-the-record/hooks/hooks.json"]:
            self.assertEqual(
                skip_eligibility.hard_to_revert_hit([(1, 0, path)], set()), path)

    def test_role_spec_json_hits(self):
        rows = [(1, 0, "roles/execution-observation.json")]
        self.assertEqual(
            skip_eligibility.hard_to_revert_hit(rows, set()),
            "roles/execution-observation.json")

    def test_migrations_path_hits(self):
        rows = [(1, 0, "migrations/0001_init.sql")]
        self.assertEqual(
            skip_eligibility.hard_to_revert_hit(rows, set()),
            "migrations/0001_init.sql")

    def test_any_deletion_hits_regardless_of_path(self):
        self.assertEqual(
            skip_eligibility.hard_to_revert_hit([], {"src/harmless.py"}),
            "src/harmless.py")

    def test_low_risk_paths_no_hit(self):
        rows = [(10, 3, "src/feature.py"), (2, 0, "docs/handbooks/x.md")]
        self.assertIsNone(skip_eligibility.hard_to_revert_hit(rows, set()))


class ClaimVocabularyHit(unittest.TestCase):
    def test_claim_word_matches(self):
        self.assertEqual(
            skip_eligibility.claim_vocabulary_hit("tests passed cleanly"),
            "tests passed")

    def test_no_claim_word_no_match(self):
        self.assertIsNone(skip_eligibility.claim_vocabulary_hit("built the feature"))

    def test_empty_text_no_match(self):
        self.assertIsNone(skip_eligibility.claim_vocabulary_hit(""))


class ClassifyRowsPopulation(unittest.TestCase):
    def test_all_low_risk_is_skip_eligible_population_s(self):
        rows = [(10, 2, "src/feature.py")]
        result = skip_eligibility.classify_rows(rows, set(), "built the feature")
        self.assertTrue(result["skip_eligible"])
        self.assertEqual(result["population"], "S")
        self.assertFalse(result["size_axis_trip"])
        self.assertFalse(result["reversibility_axis_trip"])
        self.assertFalse(result["claim_axis_trip"])

    def test_size_axis_alone_forces_population_r(self):
        rows = [(30, 25, "src/feature.py")]
        result = skip_eligibility.classify_rows(rows, set(), "no claim words here")
        self.assertFalse(result["skip_eligible"])
        self.assertEqual(result["population"], "R")
        self.assertTrue(result["size_axis_trip"])

    def test_size_exactly_at_threshold_trips(self):
        rows = [(30, 20, "src/feature.py")]
        result = skip_eligibility.classify_rows(rows, set(), "")
        self.assertEqual(
            result["non_docs_lines_changed"], skip_eligibility.NON_DOCS_LINE_THRESHOLD)
        self.assertTrue(result["size_axis_trip"])
        self.assertEqual(result["population"], "R")

    def test_reversibility_axis_alone_forces_population_r(self):
        rows = [(1, 0, "gates/gates.py")]
        result = skip_eligibility.classify_rows(rows, set(), "")
        self.assertFalse(result["skip_eligible"])
        self.assertEqual(result["population"], "R")
        self.assertTrue(result["reversibility_axis_trip"])

    def test_claim_axis_alone_forces_population_r(self):
        rows = [(1, 0, "src/feature.py")]
        result = skip_eligibility.classify_rows(rows, set(), "I verified this works")
        self.assertFalse(result["skip_eligible"])
        self.assertEqual(result["population"], "R")
        self.assertTrue(result["claim_axis_trip"])

    def test_docs_only_large_diff_stays_population_s(self):
        rows = [(500, 200, "docs/issue-1/reports/implementation.md")]
        result = skip_eligibility.classify_rows(rows, set(), "no claim words")
        self.assertTrue(result["skip_eligible"])
        self.assertEqual(result["population"], "S")


if __name__ == "__main__":
    unittest.main()


def test_classify_for_subject_live_fire_population_s(tmp_path):
    """Top-level live-fire: real git branches, real subprocess calls inside
    `skip_eligibility.classify_for_subject`, asserting the S outcome."""
    import subprocess as sp
    repo = tmp_path / "repo"
    repo.mkdir()
    sp.run(["git", "init", "-q"], cwd=repo, check=True)
    sp.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    sp.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "a.txt").write_text("base\n")
    sp.run(["git", "add", "."], cwd=repo, check=True)
    sp.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    default = sp.run(["git", "-C", str(repo), "branch", "--show-current"],
                      capture_output=True, text=True).stdout.strip()
    sp.run(["git", "checkout", "-b", "issue-9999/implementation"], cwd=repo, check=True,
           capture_output=True)
    (repo / "src.py").write_text("x = 1\n")
    sp.run(["git", "add", "."], cwd=repo, check=True)
    sp.run(["git", "commit", "-q", "-m", "small safe change"], cwd=repo, check=True)

    result = skip_eligibility.classify_for_subject(
        repo, "issue-9999", base=default)
    assert result["population"] == "S"
    assert result["skip_eligible"] is True


def test_classify_for_subject_live_fire_population_r(tmp_path):
    """Same live-fire harness, hard-to-revert path -> population R."""
    import subprocess as sp
    repo = tmp_path / "repo"
    repo.mkdir()
    sp.run(["git", "init", "-q"], cwd=repo, check=True)
    sp.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    sp.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "a.txt").write_text("base\n")
    sp.run(["git", "add", "."], cwd=repo, check=True)
    sp.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    default = sp.run(["git", "-C", str(repo), "branch", "--show-current"],
                      capture_output=True, text=True).stdout.strip()
    sp.run(["git", "checkout", "-b", "issue-9999/implementation"], cwd=repo, check=True,
           capture_output=True)
    (repo / "gates" / "some_gate.py").parent.mkdir(parents=True, exist_ok=True)
    (repo / "gates" / "some_gate.py").write_text("x = 1\n")
    sp.run(["git", "add", "."], cwd=repo, check=True)
    sp.run(["git", "commit", "-q", "-m", "risky change"], cwd=repo, check=True)

    result = skip_eligibility.classify_for_subject(
        repo, "issue-9999", base=default)
    assert result["population"] == "R"
    assert result["skip_eligible"] is False
