"""issue #2924: `_watcher_looks_real()`/`_session_looks_real()`
(roster.py) and `watchdog_lock_acquire()` (watchdog.py) verify pid
*identity* via `/proc` -- on a platform without `/proc` (macOS) they
degrade to a bare liveness check, reopening the pid-reuse hole
#2749/PR #2823 closed. That degradation was already handled (nothing
crashes) but was visible only in a docstring. This asserts it is now
visible at runtime: once per process for the roster.py identity checks
(not per call -- `_watcher_looks_real` is called every patrol tick, and
per-tick noise is exactly what the issue's must-nots forbid), and inline
in the returned message for `watchdog_lock_acquire`'s refusal (the only
place that message is ever surfaced -- its caller `print()`s it as-is).

Run: python3 -m pytest test/test_proc_identity_degradation_visibility.py -q
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import roster as roster_mod
import spawn
import watchdog

roster_mod._sp = spawn
watchdog._sp = spawn


def _capture(fn, *a, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a, **kw)
    return rc, buf.getvalue()


class ProcIdentityNoteTest(unittest.TestCase):
    def setUp(self):
        self._orig_available = roster_mod._PROC_AVAILABLE
        self._orig_noted = roster_mod._proc_identity_degradation_noted
        roster_mod._proc_identity_degradation_noted = False

    def tearDown(self):
        roster_mod._PROC_AVAILABLE = self._orig_available
        roster_mod._proc_identity_degradation_noted = self._orig_noted

    def test_note_prints_exactly_once_per_process(self):
        _, out = _capture(lambda: (
            roster_mod._note_proc_identity_degraded("site-a"),
            roster_mod._note_proc_identity_degraded("site-b"),
        ))
        self.assertEqual(out.count("[proc-identity]"), 1, out)
        self.assertIn("site-a", out)
        self.assertNotIn("site-b", out)

    def test_watcher_looks_real_notes_when_proc_unavailable(self):
        roster_mod._PROC_AVAILABLE = False
        with unittest.mock.patch.object(spawn, "_alive", return_value=True), \
             unittest.mock.patch.object(Path, "exists", return_value=False):
            _, out = _capture(roster_mod._watcher_looks_real, 99999, 123)
        self.assertIn("[proc-identity] _watcher_looks_real", out)

    def test_session_looks_real_notes_when_proc_unavailable(self):
        roster_mod._PROC_AVAILABLE = False
        with unittest.mock.patch.object(spawn, "_alive", return_value=True), \
             unittest.mock.patch.object(Path, "exists", return_value=False):
            _, out = _capture(roster_mod._session_looks_real, 99999, "/some/work")
        self.assertIn("[proc-identity] _session_looks_real", out)

    def test_watcher_looks_real_silent_when_proc_available(self):
        # This test host is Linux -- /proc is real, and this process's own
        # pid has a real cmdline entry, so identity resolves normally with
        # no degrade note (must-not: don't weaken/change the Linux path).
        with unittest.mock.patch.object(spawn, "_alive", return_value=True):
            _, out = _capture(roster_mod._watcher_looks_real, os.getpid(), None)
        self.assertNotIn("[proc-identity]", out)


class WatchdogLockDegradedNoteTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.lock_path = Path(self._tmp.name) / "watchdog.lock"

    def tearDown(self):
        self._tmp.cleanup()

    def test_refusal_message_flags_unverifiable_identity_when_start_time_is_none(self):
        # issue #2924: on a platform without /proc, _proc_start_time()
        # always returns None -- the lock file below is exactly what a
        # macOS host writes at acquire time.
        self.lock_path.write_text(json.dumps({"pid": 424242, "start_time": None}))
        with unittest.mock.patch.object(spawn, "_alive", return_value=True), \
             unittest.mock.patch.object(spawn, "_proc_start_time", return_value=None):
            ok, msg = watchdog.watchdog_lock_acquire(lock_path=self.lock_path,
                                                       pid=999999)
        self.assertFalse(ok)
        self.assertIn("신원 확인 불가", msg)

    def test_refusal_message_unchanged_when_start_time_is_real(self):
        # Linux path: a genuine start_time match carries no degraded note.
        self.lock_path.write_text(json.dumps({"pid": 424242, "start_time": "12345"}))
        with unittest.mock.patch.object(spawn, "_alive", return_value=True), \
             unittest.mock.patch.object(spawn, "_proc_start_time", return_value="12345"):
            ok, msg = watchdog.watchdog_lock_acquire(lock_path=self.lock_path,
                                                       pid=999999)
        self.assertFalse(ok)
        self.assertNotIn("신원 확인 불가", msg)


if __name__ == "__main__":
    unittest.main()
