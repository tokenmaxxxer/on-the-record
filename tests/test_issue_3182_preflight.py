"""Issue #3182 round 2: drives `scripts/preflight/consumer_preconditions.py`
as a real subprocess (not an import) so the acceptance check exercises the
exact command an operator runs, exit code included.

Test derivation (test-derivation skill): the acceptance criteria are a
contract on a CLI's output shape plus two safety properties, so each gets
its own case rather than one combined assertion:

  - equivalence partition on the JSON shape: `--json` emits a
    `preconditions` list of at least five entries, and every entry has all
    four required fields (`name`, `satisfied`, `remedy`, `source`) -- a
    dropped field on any one entry is a partition boundary the script must
    not cross silently.
  - boundary value on `source`: each citation must resolve to a real file
    in this repo (not a stale path from a rename) with a line number
    attached (not just a bare filename) -- the traceability claim the
    preflight makes to the reader.
  - boundary on exit code: only 0 or 1 are contractual per the script's
    own docstring; anything else (a traceback exit, e.g.) is a defect.
  - decision-table case for the one precondition the script cannot
    actually observe without a mutating action (`remote_push_access`,
    per the script's own comment): it must be reported unsatisfied, never
    guessed satisfied -- the "never asserts what it did not check"
    invariant, negative case.
  - idempotence/read-only property, run twice rather than asserted in
    prose: `git status --porcelain` must be byte-identical before, between,
    and after two consecutive runs in both flag forms.

  python3 -m pytest tests/test_issue_3182_preflight.py -q
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "preflight" / "consumer_preconditions.py"

REQUIRED_FIELDS = ("name", "satisfied", "remedy", "source")

# "spawn.py:2668,4639 (...)" / "board.py:246-256 (...)" / "path/to/x.sh:341 (...)"
SOURCE_RE = re.compile(r"^(?P<file>\S+?):(?P<lines>[0-9]+(?:[,-][0-9]+)*)(?:\s|$)")


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=30,
    )


def _git_status_porcelain() -> str:
    return subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=30,
    ).stdout


class PreflightJsonShapeTest(unittest.TestCase):
    def setUp(self):
        self.result = _run("--json")
        self.assertIn(
            self.result.returncode,
            (0, 1),
            f"exit code must be 0 or 1, got {self.result.returncode}: "
            f"stderr={self.result.stderr!r}",
        )
        self.data = json.loads(self.result.stdout)

    def test_at_least_five_preconditions(self):
        preconditions = self.data["preconditions"]
        self.assertGreaterEqual(len(preconditions), 5)

    def test_every_entry_has_required_fields(self):
        for entry in self.data["preconditions"]:
            for field in REQUIRED_FIELDS:
                self.assertIn(
                    field, entry, f"entry {entry.get('name', entry)!r} missing {field!r}"
                )

    def test_every_source_cites_a_real_file_with_a_line_number(self):
        for entry in self.data["preconditions"]:
            source = entry["source"]
            m = SOURCE_RE.match(source)
            self.assertIsNotNone(
                m, f"{entry['name']}: source {source!r} has no <file>:<line> prefix"
            )
            cited_path = ROOT / m.group("file")
            self.assertTrue(
                cited_path.is_file(),
                f"{entry['name']}: source cites {m.group('file')!r}, "
                f"which does not exist under {ROOT}",
            )

    def test_exit_code_is_zero_or_one_only(self):
        self.assertIn(self.result.returncode, (0, 1))

    def test_exit_code_tracks_actual_satisfaction_state(self):
        # PR #3195 finding: membership in {0,1} alone passes against a
        # mutant that ignores every verdict and always returns the same
        # code. Recompute the expected code from the parsed JSON's own
        # satisfied flags and require the process's real exit code to
        # match it -- remote_push_access is always unsatisfied by design
        # (see test_unobservable_precondition_reported_unsatisfied), so
        # this is 1 on every real run today, but the assertion is derived
        # from the data, not hardcoded, so it stays correct if that ever
        # changes.
        preconditions = self.data["preconditions"]
        expected = 0 if all(e["satisfied"] for e in preconditions) else 1
        self.assertEqual(
            self.result.returncode, expected,
            f"exit code {self.result.returncode} does not match the satisfaction "
            f"state in the parsed JSON (expected {expected})",
        )

    def test_unobservable_precondition_reported_unsatisfied(self):
        # remote_push_access requires a mutating `git push` to check for
        # real; the script's own contract says it must never guess this
        # one satisfied.
        by_name = {e["name"]: e for e in self.data["preconditions"]}
        self.assertIn("remote_push_access", by_name)
        self.assertFalse(
            by_name["remote_push_access"]["satisfied"],
            "remote_push_access must be reported unsatisfied: it cannot be "
            "observed without a mutating git push",
        )


class PreflightReadOnlyTest(unittest.TestCase):
    def test_working_tree_unchanged_across_two_runs_json(self):
        before = _git_status_porcelain()
        _run("--json")
        after_first = _git_status_porcelain()
        _run("--json")
        after_second = _git_status_porcelain()
        self.assertEqual(before, after_first)
        self.assertEqual(before, after_second)

    def test_working_tree_unchanged_across_two_runs_human(self):
        before = _git_status_porcelain()
        _run()
        after_first = _git_status_porcelain()
        _run()
        after_second = _git_status_porcelain()
        self.assertEqual(before, after_first)
        self.assertEqual(before, after_second)


if __name__ == "__main__":
    unittest.main()
