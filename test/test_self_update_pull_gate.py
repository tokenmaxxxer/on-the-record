"""issue #2749: `spawn.py self-update` is the deliberate replacement for
`self-update.sh`'s old unconditional `git pull --ff-only`. It must refuse
to advance the working tree (no `git pull`, no `.pull-check` "ok") while
any session is live or the roster can't be trusted -- and must actually
advance it, recording `pull=ok`, when nothing is live to observe the
swap. Same "zero sessions running at pull time" discipline issue #2670
ran by hand (docs/issue-2670/reports/... final comment), now a checkable
command instead of an unwritten habit.

Run: python3 -m pytest test/test_self_update_pull_gate.py -q
"""
from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

import roster as roster_mod
import spawn

roster_mod._sp = spawn


def _capture(fn, *a, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a, **kw)
    return rc, buf.getvalue()


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args],
                           capture_output=True, text=True, check=True)


class SelfUpdatePullGateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)

        # bare "origin" plus a working checkout tracking it -- mirrors the
        # shared marketplace checkout self-update.sh/self-update pull
        # advance together.
        origin = base / "origin.git"
        origin.mkdir()
        _git(origin, "init", "--bare", "-q")
        src = base / "seed"
        src.mkdir()
        _git(src, "init", "-q")
        _git(src, "config", "user.email", "t@example.com")
        _git(src, "config", "user.name", "t")
        (src / "spawn.py").write_text("# seed\n")
        _git(src, "add", "spawn.py")
        _git(src, "commit", "-q", "-m", "seed")
        _git(src, "branch", "-M", "main")
        _git(src, "remote", "add", "origin", str(origin))
        _git(src, "push", "-q", "-u", "origin", "main")

        self.checkout = base / "checkout"
        _git(base, "clone", "-q", str(origin), str(self.checkout))
        _git(self.checkout, "checkout", "-q", "-B", "main", "origin/main")
        _git(self.checkout, "branch", "-q", "--set-upstream-to=origin/main", "main")

        self.origin = origin
        self.src = src

        self.orig_root = spawn.ROOT
        self.orig_roster = spawn.ROSTER
        self.orig_workspace_base = spawn._workspace_base
        spawn.ROOT = self.checkout
        spawn.ROSTER = base / "active.json"
        spawn._workspace_base = lambda: base

    def tearDown(self):
        spawn.ROOT = self.orig_root
        spawn.ROSTER = self.orig_roster
        spawn._workspace_base = self.orig_workspace_base
        self._tmp.cleanup()

    def _head(self) -> str:
        return _git(self.checkout, "rev-parse", "HEAD").stdout.strip()

    def test_zero_live_sessions_pulls_and_records_ok(self):
        # origin advances past the checkout's current HEAD
        (self.src / "new.txt").write_text("x\n")
        _git(self.src, "add", "new.txt")
        _git(self.src, "commit", "-q", "-m", "advance")
        _git(self.src, "push", "-q", "origin", "main")
        before = self._head()

        rc, out = _capture(spawn.self_update_pull_cli)

        self.assertEqual(rc, 0, out)
        self.assertNotEqual(self._head(), before)
        self.assertEqual((self.checkout / ".pull-check").read_text().strip(), "pull=ok")

    def test_live_roster_session_refuses_without_pulling(self):
        (self.src / "new.txt").write_text("x\n")
        _git(self.src, "add", "new.txt")
        _git(self.src, "commit", "-q", "-m", "advance")
        _git(self.src, "push", "-q", "origin", "main")
        before = self._head()

        proc = subprocess.Popen(["sleep", "30"])
        try:
            spawn.roster_register(
                spawn.lease_key(2749, "implementation"),
                {"pid": proc.pid, "skill": "implementation", "issue": 2749,
                 "ts": int(time.time()), "work": str(self.checkout),
                 "log": str(self.checkout) + ".log", "expects_pr": True,
                 "session_id": None},
            )

            rc, out = _capture(spawn.self_update_pull_cli)

            self.assertEqual(rc, 1, out)
            self.assertEqual(self._head(), before,
                              "working tree must not advance while a session is live")
            marker = (self.checkout / ".pull-check").read_text().strip()
            self.assertTrue(marker.startswith("pull=refused:"), marker)
            self.assertIn("live-sessions", marker)
        finally:
            proc.kill()
            proc.wait()

    def test_unreadable_roster_refuses_without_pulling(self):
        (self.src / "new.txt").write_text("x\n")
        _git(self.src, "add", "new.txt")
        _git(self.src, "commit", "-q", "-m", "advance")
        _git(self.src, "push", "-q", "origin", "main")
        before = self._head()

        spawn.ROSTER.parent.mkdir(parents=True, exist_ok=True)
        spawn.ROSTER.write_text("{not valid json")

        rc, out = _capture(spawn.self_update_pull_cli)

        self.assertEqual(rc, 2, out)
        self.assertEqual(self._head(), before)
        marker = (self.checkout / ".pull-check").read_text().strip()
        self.assertTrue(marker.startswith("pull=refused:roster-unreadable:"), marker)

    def test_already_current_pulls_cleanly(self):
        before = self._head()

        rc, out = _capture(spawn.self_update_pull_cli)

        self.assertEqual(rc, 0, out)
        self.assertEqual(self._head(), before)
        self.assertEqual((self.checkout / ".pull-check").read_text().strip(), "pull=ok")


if __name__ == "__main__":
    unittest.main()
