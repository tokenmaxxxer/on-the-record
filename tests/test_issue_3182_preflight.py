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

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "preflight" / "consumer_preconditions.py"

REQUIRED_FIELDS = ("name", "satisfied", "remedy", "source")

# "spawn.py:2668,4639 (...)" / "board.py:246-256 (...)" / "path/to/x.sh:341 (...)"
# Issue #3297: the `source` prose names a file, not a file:line. Line
# numbers here drifted silently -- nothing verified them, unlike
# `line_anchors`, which are now ordinals checked against the real file.
# A citation that can rot without anyone noticing is worse than one that
# points at the file and makes the reader look.
SOURCE_RE = re.compile(r"^(?P<file>[\w./-]+\.(?:py|sh))(?:\s|$)")

# Imported directly (not just driven as a subprocess) so the disk-headroom
# observation-failure tests below can monkeypatch os.statvfs.
_spec = importlib.util.spec_from_file_location("consumer_preconditions_direct", SCRIPT)
_cp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cp)


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

    def test_every_source_cites_a_real_file(self):
        for entry in self.data["preconditions"]:
            source = entry["source"]
            m = SOURCE_RE.match(source)
            self.assertIsNotNone(
                m, f"{entry['name']}: source {source!r} does not start with a "
                "file path"
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


class WorkspaceDiskHeadroomObservationFailureTest(unittest.TestCase):
    """Round 4: PR #3184's round-3 verification (PR #3203) reproduced a
    defect by monkeypatching os.statvfs() to raise -- the inode half of
    check_workspace_disk_headroom() never ran, yet the precondition still
    reported satisfied=True. That inverts the script's own contract
    (module docstring: an unobservable precondition is reported
    unsatisfied, never guessed satisfied). Both directions are asserted so
    a fix that over-corrects to always-unsatisfied is caught too."""

    def test_statvfs_failure_reports_unsatisfied_naming_what_failed(self):
        # shutil.disk_usage() is itself implemented on top of os.statvfs()
        # on POSIX, so disk_usage must be faked to succeed independently --
        # otherwise patching os.statvfs alone trips disk_usage's own
        # except-OSError branch first and never reaches the inode check
        # this test targets.
        fake_usage = mock.Mock(free=10 * 1024 * 1024 * 1024)
        with mock.patch.object(_cp.shutil, "disk_usage", return_value=fake_usage), \
             mock.patch.object(_cp.os, "statvfs", side_effect=OSError("boom")):
            ok, detail = _cp.check_workspace_disk_headroom()
        self.assertFalse(
            ok, f"os.statvfs() raising must report unsatisfied, got detail={detail!r}"
        )
        self.assertIn("inode", detail, f"detail must name what could not be observed: {detail!r}")

    def test_disk_usage_failure_still_reports_unsatisfied(self):
        # Locks in the sibling exception path (shutil.disk_usage raising)
        # that was already correct before this fix, so a future edit can't
        # silently regress it while touching the statvfs branch.
        with mock.patch.object(_cp.shutil, "disk_usage", side_effect=OSError("boom")):
            ok, detail = _cp.check_workspace_disk_headroom()
        self.assertFalse(ok, f"shutil.disk_usage() raising must report unsatisfied, got {detail!r}")

    def test_statvfs_success_with_ample_headroom_reports_satisfied(self):
        fake_usage = mock.Mock(free=10 * 1024 * 1024 * 1024)
        fake_statvfs = mock.Mock(f_favail=1_000_000)
        with mock.patch.object(_cp.shutil, "disk_usage", return_value=fake_usage), \
             mock.patch.object(_cp.os, "statvfs", return_value=fake_statvfs):
            ok, detail = _cp.check_workspace_disk_headroom()
        self.assertTrue(ok, f"ample, observable headroom must report satisfied, got {detail!r}")

    def test_statvfs_zero_free_inodes_reports_unsatisfied(self):
        # Round 5 (PR #3208 finding): f_favail == 0 is an observed value --
        # the worst possible one, a completely full filesystem -- not a
        # missing one. `if free_inodes and free_inodes < min_inodes` treated
        # 0 as falsy and skipped the comparison, so the exact condition this
        # check exists to catch was the one case it reported satisfied.
        fake_usage = mock.Mock(free=10 * 1024 * 1024 * 1024)
        fake_statvfs = mock.Mock(f_favail=0)
        with mock.patch.object(_cp.shutil, "disk_usage", return_value=fake_usage), \
             mock.patch.object(_cp.os, "statvfs", return_value=fake_statvfs):
            ok, detail = _cp.check_workspace_disk_headroom()
        self.assertFalse(ok, f"0 free inodes must report unsatisfied, got detail={detail!r}")
        self.assertIn("0 free inodes", detail, f"detail must name the observed count: {detail!r}")


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
