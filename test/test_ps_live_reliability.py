"""issue #2203: `spawn.py ps` must never render a live session invisible.

Two recorded incidents: `ps` printed the plain "no sessions running" line
while a session was demonstrably alive (pid up, session log growing), and
that empty read was read as authoritative and triggered destructive
"recovery" of healthy work (force-push+merge a running branch; `git
stash` of a running session's uncommitted edits) — both times.

This spawns a real subprocess to stand in for a live session, wires it
into the roster and the spawn-claim registry (the two independent
liveness surfaces `ps`/spawn-refusal each read), then drives `roster_ps()`
through: (a) a roster read failure shaped like an interrupted write
(what a reinstall/reload racing `_roster_save()` used to produce before
this fix made saves atomic), and (b) the roster simply missing the entry
while the claim still shows it alive — the exact shape of the freshest
live reproduction in the issue thread (2026-08-25, pids 2600425). Both
must fail loud (never the bare empty line), and a genuinely empty state
must still read as empty (regression guard, acceptance criterion 2)."""
import contextlib
import io
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

import pytest

import board
import roster as roster_mod
import spawn

board._sp = spawn
roster_mod._sp = spawn


def _capture(fn, *a, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a, **kw)
    return rc, buf.getvalue()


class LivePsReliabilityTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.orig_roster = spawn.ROSTER
        self.orig_workspace_base = spawn._workspace_base
        self.orig_ws_index_load = spawn._workspace_index_load
        spawn.ROSTER = self.base / "active.json"
        spawn._workspace_base = lambda: self.base
        spawn._workspace_index_load = lambda: {}
        self.proc = subprocess.Popen(["sleep", "60"])

    def tearDown(self):
        self.proc.kill()
        self.proc.wait()
        spawn.ROSTER = self.orig_roster
        spawn._workspace_base = self.orig_workspace_base
        spawn._workspace_index_load = self.orig_ws_index_load
        self._tmp.cleanup()

    def _register(self, work):
        entry = {
            "pid": self.proc.pid, "skill": "implementation", "issue": 2203,
            "ts": int(time.time()), "work": str(work),
            "log": str(work) + ".log", "expects_pr": True,
            "session_id": None,
        }
        spawn.roster_register(spawn.lease_key(2203, "implementation"), entry)

    def _claim(self, work):
        rejection = spawn._acquire_spawn_claim(str(work), 2203, "implementation")
        self.assertIsNone(rejection)

    @pytest.mark.slow
    def test_live_session_survives_roster_write_corruption(self):
        work = self.base / "on-the-record-issue-2203-implementation"
        work.mkdir()
        self._register(work)
        self._claim(work)

        rc, out = _capture(board.roster_ps)
        self.assertEqual(rc, 0)
        self.assertIn("RUNNING", out)
        self.assertNotIn("역할 세션 없음", out)

        # Reinstall-shaped failure mode: a reader observes the roster file
        # mid interrupted-write, i.e. truncated/invalid JSON -- what
        # `_roster_save()`'s old plain `write_text()` could leave behind
        # for any unlocked concurrent reader (`ps` never took the write
        # lock). `_roster_load()` swallowed this into `{}`, identical to
        # a genuinely empty roster.
        spawn.ROSTER.write_text('{"issue-2203/implementati')

        rc, out = _capture(board.roster_ps)
        self.assertNotIn("돌고 있는 역할 세션 없음", out)
        self.assertIn("확인 불가", out)
        self.assertIn(str(work.resolve()), out)
        self.assertEqual(rc, 2)

    @pytest.mark.slow
    def test_live_session_missing_from_roster_but_claim_alive(self):
        # The freshest live reproduction in the issue thread: the roster
        # parses fine and simply has no entry for the session, while the
        # spawn-claim (the surface the spawn-refusal path trusts) still
        # shows it alive. `_roster_load()`/`_roster_load_checked()` can't
        # catch this -- the JSON is valid, just short an entry -- so `ps`
        # needs the independent claim cross-check.
        work = self.base / "on-the-record-issue-2203-execution-observation"
        work.mkdir()
        self._claim(work)
        spawn.ROSTER.write_text("{}")

        rc, out = _capture(board.roster_ps)
        self.assertNotIn("돌고 있는 역할 세션 없음", out)
        self.assertIn("claim-only", out)
        self.assertIn(str(work.resolve()), out)
        self.assertEqual(rc, 0)

    def test_corrupt_claim_file_surfaces_as_warning_not_silent_skip(self):
        # silent-failure-audit finding on the first draft: an unreadable
        # claim file was silently `continue`d past, which recreates the
        # exact ambiguity this issue is about, just on the claim side of
        # the reconciliation instead of the roster side.
        claim_path = self.base / "some-orphaned-workspace.spawn-claim"
        claim_path.write_text("{not valid json")

        rc, out = _capture(board.roster_ps)
        self.assertNotIn("돌고 있는 역할 세션 없음", out)
        self.assertIn("경고", out)
        self.assertIn(str(claim_path), out)
        self.assertEqual(rc, 2)

    def test_genuinely_no_sessions_still_reports_empty(self):
        # Regression guard (acceptance criterion 2): no roster file, no
        # claim files -- this empty read must stay legitimate.
        rc, out = _capture(board.roster_ps)
        self.assertIn("돌고 있는 역할 세션 없음", out)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
