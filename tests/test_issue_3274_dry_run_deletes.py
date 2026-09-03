"""`spawn.py clean --dry-run` really deleted, and left no trace of what.

The flag was parsed and never read on this path: `spawn.py`'s `clean`
dispatch called `roster_clean(wb, issue, repo)`, which had no `dry_run`
parameter at all, while the `sweep-orphans` dispatch two lines below passed
`a.dry_run` correctly. So the flag worked where it was wired and was silently
inert where it was not.

This cost a workspace. The orchestrator ran `clean --dry-run` twice to
compare a PR branch against `main`, believing both read-only; the first run
reported `정리 끝 — 지움 1` and that deletion was real. Which workspace it
was could not be recovered: the deletion printed one line to stdout and wrote
no durable record.

A flag whose whole purpose is "show me what would happen without doing it" is
what an operator reaches for when unsure. Making it destructive inverts the
safety property exactly when it is trusted most.

  python3 -m pytest tests/test_issue_3274_dry_run_deletes.py -q
"""
from __future__ import annotations

import io
import contextlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import lifecycle  # noqa: E402
import spawn  # noqa: E402

lifecycle._sp = spawn


def _git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True,
                          text=True, check=True)


class _ReclaimableWorkspace(unittest.TestCase):
    """A workspace the classifier will happily reclaim: pushed, clean tree."""

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.addCleanup(self._t.cleanup)
        self.wb = self.tmp / "work"
        self.wb.mkdir()
        remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
        self.work = self.wb / "on-the-record-issue-9301-demo"
        subprocess.run(["git", "clone", "-q", str(remote), str(self.work)], check=True)
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        (self.work / "a.txt").write_text("1")
        _git(self.work, "add", "a.txt")
        _git(self.work, "commit", "-q", "-m", "c1")
        _git(self.work, "push", "-q", "-u", "origin", "HEAD:main")

    def _clean(self, **kw):
        buf = io.StringIO()
        with mock.patch.object(spawn, "_live_workspaces_union", return_value=({}, [])), \
             mock.patch.object(spawn, "ledger_write") as ledger, \
             contextlib.redirect_stdout(buf):
            lifecycle.roster_clean(self.wb, None, None, **kw)
        return buf.getvalue(), ledger


class DryRunDeletesNothingTest(_ReclaimableWorkspace):

    def test_the_workspace_survives_a_dry_run(self):
        out, _ = self._clean(dry_run=True)
        self.assertIn("지움 1", out, out)          # it would have reclaimed it
        self.assertTrue(self.work.is_dir(), "dry-run deleted the workspace")

    def test_the_output_says_it_was_a_dry_run(self):
        out, _ = self._clean(dry_run=True)
        self.assertIn("[dry-run]", out)

    def test_the_counts_match_a_real_run_so_the_numbers_are_comparable(self):
        dry, _ = self._clean(dry_run=True)
        dry_summary = re.search(r"정리 끝 — 지움 (\d+), 남김 (\d+)", dry).groups()
        real, _ = self._clean()
        real_summary = re.search(r"정리 끝 — 지움 (\d+), 남김 (\d+)", real).groups()
        self.assertEqual(dry_summary, real_summary)

    def test_without_the_flag_it_still_deletes(self):
        """The fix must not be 'disable clean'."""
        out, _ = self._clean()
        self.assertIn("지움 1", out)
        self.assertFalse(self.work.exists(), "clean stopped deleting")

    def test_dry_run_does_not_prune_worktrees_either(self):
        with mock.patch.object(lifecycle, "_prune_worktrees") as prune, \
             mock.patch.object(spawn, "_live_workspaces_union", return_value=({}, [])), \
             contextlib.redirect_stdout(io.StringIO()):
            lifecycle.roster_clean(self.wb, None, self.tmp, dry_run=True)
        prune.assert_not_called()


class DeletionLeavesATraceTest(_ReclaimableWorkspace):
    """stdout vanishes when the caller does not capture it -- which is exactly
    how the lost workspace became unidentifiable."""

    def test_a_real_deletion_is_recorded_by_name(self):
        _, ledger = self._clean()
        events = [c.args[0] for c in ledger.call_args_list
                  if c.args and c.args[0].get("event") == "workspace_reclaimed"]
        self.assertEqual(len(events), 1, events)
        self.assertEqual(events[0]["workspace"], "on-the-record-issue-9301-demo")

    def test_a_dry_run_records_nothing(self):
        _, ledger = self._clean(dry_run=True)
        events = [c.args[0] for c in ledger.call_args_list
                  if c.args and c.args[0].get("event") == "workspace_reclaimed"]
        self.assertEqual(events, [])


class TheFlagReachesTheDispatchTest(unittest.TestCase):
    """The wiring itself, not just the function: `clean` must pass the flag."""

    def test_clean_dispatch_passes_dry_run(self):
        src = (ROOT / "spawn.py").read_text(encoding="utf-8")
        m = re.search(r'if a\.role == "clean":\n((?:        .*\n|\n)+)', src)
        self.assertIsNotNone(m, "clean dispatch not found")
        self.assertIn("a.dry_run", m.group(1))

    def test_no_boolean_flag_is_parsed_but_never_read(self):
        """The class, not the instance. `--dry-run` was inert on one path
        while working on another; enumerate rather than trust."""
        src = (ROOT / "spawn.py").read_text(encoding="utf-8")
        flags = re.findall(r'ap\.add_argument\("(--[a-z-]+)", action="store_true"', src)
        self.assertGreater(len(flags), 10, "flag scan found suspiciously few flags")
        unread = []
        for flag in flags:
            dest = flag[2:].replace("-", "_")
            body = re.sub(r'ap\.add_argument\("%s".*?\)\n' % re.escape(flag),
                          "", src, flags=re.S)
            if f"a.{dest}" not in body:
                unread.append(flag)
        self.assertEqual(unread, [], f"parsed but never read: {unread}")


if __name__ == "__main__":
    unittest.main()
