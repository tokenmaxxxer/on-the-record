#!/usr/bin/env python3
"""Issue #2137 — verify-at-landing: executed acceptance evidence replaces
default test authoring (operator decision 2026-08-24).

Fixture landing proof: a mocked landing in a throwaway git repo produces a
real `git diff` whose only verification content is the implementation
record's per-check EXECUTED evidence (command + actual output). Asserts:

1. the produced record carries executed per-check evidence for every
   `- check:` in the issue (an `acceptance: <command> — result: ...`
   citation plus recorded output),
2. the landing diff contains NO new test files,
3. `gates/requirement_met.py` grades the landing as unblocked on that
   evidence-in-record alone (the #2137 compatibility path).

Conventions follow tests/test_checkpoint_mode.py's local-git-fixture style:
no network, no real spawn.
"""
from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
import requirement_met as rm  # noqa: E402

_ISSUE_BODY = """## Acceptance
- check: `python3 scripts/clamp.py --selftest` exits 0.
  provenance: executed-live
- check: `python3 scripts/clamp.py 35 30` prints 30.
  provenance: executed-live
"""

_CHECK_COMMANDS = [
    "python3 scripts/clamp.py --selftest",
    "python3 scripts/clamp.py 35 30",
]


def _run(cwd: Path, *args: str) -> str:
    r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                       check=True)
    return r.stdout


def _git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run(path, "git", "init", "-q")
    _run(path, "git", "config", "user.email", "t@example.com")
    _run(path, "git", "config", "user.name", "t")
    (path / "scripts").mkdir()
    (path / "scripts" / "clamp.py").write_text(
        "import sys\nprint(min(int(sys.argv[1]), int(sys.argv[2])))\n")
    _run(path, "git", "add", "-A")
    _run(path, "git", "commit", "-q", "-m", "base")


def _land_fixture(repo: Path) -> str:
    """Simulate the landing: code change + implementation record whose
    Verification section is per-check command+output evidence. Returns the
    landing diff (base..HEAD)."""
    base = _run(repo, "git", "rev-parse", "HEAD").strip()
    # the code deliverable
    (repo / "scripts" / "clamp.py").write_text(
        "import sys\n"
        "if sys.argv[1] == '--selftest':\n"
        "    assert min(35, 30) == 30\n"
        "    raise SystemExit(0)\n"
        "print(min(int(sys.argv[1]), int(sys.argv[2])))\n")
    # the record: per-check executed evidence, no test files authored
    record = repo / "docs" / "issue-9" / "reports" / "implementation.md"
    record.parent.mkdir(parents=True)
    record.write_text(
        "# issue-9 implementation record\n\n"
        "## Verification\n"
        "- acceptance: python3 scripts/clamp.py --selftest — result: PASS\n"
        "  output: (exit 0)\n"
        "- acceptance: python3 scripts/clamp.py 35 30 — result: PASS\n"
        "  output: 30\n")
    _run(repo, "git", "add", "-A")
    _run(repo, "git", "commit", "-q", "-m", "issue-9: landing")
    return _run(repo, "git", "diff", f"{base}..HEAD")


class VerifyAtLandingFixture(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import tempfile
        cls._tmp = tempfile.TemporaryDirectory()
        cls.repo = Path(cls._tmp.name) / "target"
        _git_repo(cls.repo)
        cls.diff = _land_fixture(cls.repo)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_record_carries_executed_per_check_evidence(self):
        record = (self.repo / "docs" / "issue-9" / "reports" /
                  "implementation.md").read_text()
        self.assertIn("## Verification", record)
        for cmd in _CHECK_COMMANDS:
            m = re.search(
                r"acceptance: %s — result: PASS\n\s+output: " % re.escape(cmd),
                record)
            self.assertIsNotNone(
                m, f"no executed command+output evidence for {cmd!r}")

    def test_landing_diff_contains_no_new_test_files(self):
        new_files = re.findall(r"^diff --git a/\S+ b/(\S+)$", self.diff,
                               re.MULTILINE)
        self.assertTrue(new_files)
        test_like = [f for f in new_files
                     if re.search(r"(^|/)tests?(/|$)|(^|/)test_[^/]*$|_test\.[^/]*$",
                                  f)]
        self.assertEqual(test_like, [],
                         f"landing diff added test files: {test_like}")

    def test_requirement_met_grades_unblocked_on_evidence_in_record(self):
        verdicts = {
            "`python3 scripts/clamp.py --selftest` exits 0.": rm.YES,
            "`python3 scripts/clamp.py 35 30` prints 30.": rm.YES,
        }
        result = rm.grade(_ISSUE_BODY, self.diff, verdicts)
        self.assertFalse(result["blocked"], result["blocking_reasons"])
        for c in result["criteria"]:
            self.assertTrue(c["artifact_in_diff"], c)
            self.assertFalse(c["command_identity_mismatch"], c)

    def test_recorded_evidence_is_actually_reexecutable(self):
        """cut-7 style re-verification: replay the recorded acceptance
        statements against the current build."""
        for cmd in _CHECK_COMMANDS:
            r = subprocess.run(cmd.split(), cwd=str(self.repo),
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, (cmd, r.stderr))


if __name__ == "__main__":
    unittest.main()
