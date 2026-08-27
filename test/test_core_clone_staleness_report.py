"""Tests for issue #2616: the managed `tokenmaxxxer-core` rulebook clone
never reports when it's behind its origin — a session bootstrap should
surface that.

`spawn.core_clone_staleness_line(d)` wraps `checkout_staleness()` (issue
#2506, reused as-is -- fetch + compare, never mutates the working tree) and
turns it into a one-line bootstrap message. Empty string means either "not a
git clone with an origin" (undetermined) or "current" -- both are silent by
design; only a confirmed-stale checkout gets a line.

Run: python3 -m pytest test/test_core_clone_staleness_report.py -q
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import spawn  # noqa: E402


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(cwd), *args],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r


class CoreCloneStalenessReportTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.bare = base / "origin.git"
        self.a = base / "checkout-a"  # the clone under test
        self.b = base / "checkout-b"  # advances origin
        _git(base, "init", "-q", "--initial-branch=main", str(self.bare), "--bare")
        for clone in (self.a, self.b):
            subprocess.run(["git", "clone", "-q", str(self.bare), str(clone)],
                           capture_output=True, text=True, check=True)
            _git(clone, "config", "user.email", "a@b.c")
            _git(clone, "config", "user.name", "test")
        (self.a / "README.md").write_text("hello\n")
        _git(self.a, "add", "README.md")
        _git(self.a, "commit", "-q", "-m", "init")
        subprocess.run(["git", "-C", str(self.a), "push", "-q", "origin", "main"],
                       capture_output=True, text=True, check=True)
        # A clone made from an empty bare repo (as `b` was, above) never
        # gets `origin/HEAD` set automatically -- only a clone of a
        # non-empty repo does. Both checkouts need it for the ancestry
        # comparison `checkout_staleness()` relies on.
        _git(self.a, "remote", "set-head", "origin", "-a")
        _git(self.b, "pull", "-q", "origin", "main")
        _git(self.b, "remote", "set-head", "origin", "-a")

    def _advance_origin_from_b(self):
        (self.b / "NEWS.md").write_text("gate landed\n")
        _git(self.b, "add", "NEWS.md")
        _git(self.b, "commit", "-q", "-m", "advance")
        subprocess.run(["git", "-C", str(self.b), "push", "-q", "origin", "main"],
                       capture_output=True, text=True, check=True)

    def test_fresh_checkout_reports_nothing(self):
        line = spawn.core_clone_staleness_line(self.a)
        self.assertEqual(line, "")

    def test_deliberately_stale_checkout_is_reported_with_path_and_count(self):
        self._advance_origin_from_b()
        # checkout-a never fetched/pulled the new commit -- deliberately stale.
        line = spawn.core_clone_staleness_line(self.a)
        self.assertNotEqual(line, "")
        self.assertIn(str(self.a), line)
        self.assertIn("1개", line)

    def test_non_git_dir_is_undetermined_not_current(self):
        empty = Path(self._tmp.name) / "not-a-clone"
        empty.mkdir()
        line = spawn.core_clone_staleness_line(empty)
        self.assertEqual(line, "")

    def test_git_repo_with_no_origin_is_undetermined_not_current(self):
        solo = Path(self._tmp.name) / "solo"
        subprocess.run(["git", "init", "-q", "--initial-branch=main", str(solo)],
                       capture_output=True, text=True, check=True)
        _git(solo, "config", "user.email", "a@b.c")
        _git(solo, "config", "user.name", "test")
        (solo / "f.txt").write_text("x\n")
        _git(solo, "add", "f.txt")
        _git(solo, "commit", "-q", "-m", "init")
        line = spawn.core_clone_staleness_line(solo)
        self.assertEqual(line, "")


if __name__ == "__main__":
    unittest.main()
