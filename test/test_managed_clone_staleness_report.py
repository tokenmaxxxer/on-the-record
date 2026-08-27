"""Tests for issue #2616: the core rulebook clone (and the skill-repository
managed clone, which shares the exact same TTL-pull code path) must report
when it is behind origin instead of silently reading as current.

`pipeline._report_managed_clone_staleness(d, label)` is the reporting layer
added for this issue. It reuses `spawn.checkout_staleness()` (issue #2506)
rather than re-deriving staleness detection — this file tests the report
formatting and the wiring into `core_root()` / `_skill_repo_managed_root()`,
not staleness detection itself (that is covered by test_checkout_staleness.py).

Run: python3 -m pytest test/test_managed_clone_staleness_report.py -q
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import spawn  # noqa: E402
import pipeline  # noqa: E402
import skills  # noqa: E402


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(cwd), *args],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r


class ReportFormattingTest(unittest.TestCase):
    """Mocked `checkout_staleness()` results — pure formatting/empty-state."""

    def test_current_clone_prints_nothing(self):
        fresh = {"checked": True, "stale": False, "behind": 0,
                  "fetch_ok": True, "detail": ""}
        with mock.patch.object(spawn, "checkout_staleness", return_value=fresh):
            buf = StringIO()
            with mock.patch("sys.stderr", buf):
                pipeline._report_managed_clone_staleness(Path("/fake/core"), "core")
        self.assertEqual(buf.getvalue(), "")

    def test_stale_clone_names_path_and_behind_count_and_fix_command(self):
        stale = {"checked": True, "stale": True, "behind": 3,
                  "fetch_ok": True, "detail": "3개 커밋 뒤처졌다"}
        with mock.patch.object(spawn, "checkout_staleness", return_value=stale):
            buf = StringIO()
            with mock.patch("sys.stderr", buf):
                pipeline._report_managed_clone_staleness(Path("/fake/core"), "core")
        out = buf.getvalue()
        self.assertIn("/fake/core", out)
        self.assertIn("3", out)
        self.assertIn("git -C /fake/core pull --ff-only", out)

    def test_undetermined_is_distinguished_from_current(self):
        undetermined = {"checked": False, "stale": False, "behind": 0,
                        "fetch_ok": False, "detail": "origin/HEAD 를 resolve 할 수 없다"}
        with mock.patch.object(spawn, "checkout_staleness", return_value=undetermined):
            buf = StringIO()
            with mock.patch("sys.stderr", buf):
                pipeline._report_managed_clone_staleness(Path("/fake/core"), "core")
        out = buf.getvalue()
        self.assertIn("/fake/core", out)
        self.assertIn("판정할 수 없다", out)
        self.assertNotIn("뒤처졌다", out)


class ReportAgainstRealCloneTest(unittest.TestCase):
    """Executable-live check (acceptance bullet 1 & 2): a deliberately stale
    real clone produces the reported line; a non-git-clone path reports
    undetermined, never current."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.bare = base / "origin.git"
        self.a = base / "checkout-a"
        self.b = base / "checkout-b"
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
        _git(self.a, "remote", "set-head", "origin", "-a")
        _git(self.b, "pull", "-q", "origin", "main")
        _git(self.b, "remote", "set-head", "origin", "-a")

    def test_deliberately_one_commit_behind_clone_reports_the_line(self):
        (self.b / "NEWS.md").write_text("gate landed\n")
        _git(self.b, "add", "NEWS.md")
        _git(self.b, "commit", "-q", "-m", "advance")
        subprocess.run(["git", "-C", str(self.b), "push", "-q", "origin", "main"],
                       capture_output=True, text=True, check=True)
        # checkout-a never fetched/pulled -- deliberately one commit behind,
        # and its own cached origin/main ref is stale too, exactly like the
        # measured incident in issue #2616.
        buf = StringIO()
        with mock.patch("sys.stderr", buf):
            pipeline._report_managed_clone_staleness(self.a, "core")
        out = buf.getvalue()
        self.assertIn(str(self.a), out)
        self.assertIn("1", out)
        self.assertIn(f"git -C {self.a} pull --ff-only", out)

    def test_current_clone_is_silent(self):
        buf = StringIO()
        with mock.patch("sys.stderr", buf):
            pipeline._report_managed_clone_staleness(self.a, "core")
        self.assertEqual(buf.getvalue(), "")

    def test_path_that_is_not_a_git_clone_reports_undetermined_not_current(self):
        not_a_clone = Path(self._tmp.name) / "plain-directory"
        not_a_clone.mkdir()
        buf = StringIO()
        with mock.patch("sys.stderr", buf):
            pipeline._report_managed_clone_staleness(not_a_clone, "core")
        out = buf.getvalue()
        self.assertIn(str(not_a_clone), out)
        self.assertIn("판정할 수 없다", out)
        self.assertNotIn("현재", out)


class WiringTest(unittest.TestCase):
    """core_root() and _skill_repo_managed_root() both reach the report on
    their existing-valid-clone path -- the two managed clones that share the
    TTL-pull code path (issue #2616's non-goal carve-out check)."""

    def test_core_root_reports_staleness_on_existing_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "runs" / "rulebooks" / "tokenmaxxxer-core"
            (d / "core" / ".claude-plugin").mkdir(parents=True)
            (d / "core" / ".claude-plugin" / "plugin.json").write_text("{}")
            with mock.patch.object(spawn, "_core_candidates", return_value=[]), \
                 mock.patch.object(spawn, "ROOT", Path(tmp)), \
                 mock.patch.object(spawn, "_locked_rulebook_dir",
                                    return_value=mock.MagicMock(__enter__=lambda s: None,
                                                                 __exit__=lambda *a: None)), \
                 mock.patch.object(spawn, "_migrate_legacy_ttl_marker"), \
                 mock.patch.object(spawn, "_pull_is_fresh", return_value=True), \
                 mock.patch.object(spawn, "_report_managed_clone_staleness") as report:
                result = pipeline.core_root()
        self.assertEqual(result, d)
        report.assert_called_once_with(d, "core")

    def test_skill_repo_managed_root_reports_staleness_on_existing_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "runs" / "rulebooks" / "skill-repository"
            (d / "skills" / "example-skill").mkdir(parents=True)
            with mock.patch.object(spawn, "ROOT", Path(tmp)), \
                 mock.patch.object(spawn, "_locked_rulebook_dir",
                                    return_value=mock.MagicMock(__enter__=lambda s: None,
                                                                 __exit__=lambda *a: None)), \
                 mock.patch.object(spawn, "_pull_is_fresh", return_value=True), \
                 mock.patch.object(spawn, "_report_managed_clone_staleness") as report:
                result = skills._skill_repo_managed_root()
        self.assertEqual(result, d / "skills")
        report.assert_called_once_with(d, "skill-repo")


if __name__ == "__main__":
    unittest.main()
