"""A session can stop its own heartbeat, and only its own.

Before this, every session's poll-heartbeat had a byte-identical command
line and shared one workspace-keyed alive marker. Nothing told one session's
heartbeat apart from a neighbour's, and both consequences landed on
2026-09-03:

- I ran `pkill -f "tokenmaxxxer/work"` during runaway containment and killed
  sessions in a repository I was not orchestrating.
- A sibling session ran `pkill -f "monitors/poll-heartbeat.sh"` to tidy what
  it reasonably read as duplicate heartbeats, killed mine, and removed the
  shared `runs/watchdog.lock`. It reported the mistake itself.

Neither session did anything unreasonable. Neither could name its own.

The refusal is the load-bearing half. `stop_owned()` signals only when the
token names a live process that still matches it; an unknown token, a stale
marker, or a reused pid is refused with a reason. Falling back to a pattern
is exactly the behaviour being removed, so "refuses" is tested as carefully
as "stops".

  python3 -m pytest tests/test_issue_3293_monitor_ownership.py -q
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))

import monitor_ownership as mo  # noqa: E402

DEAD_PID = 999999999  # never a real pid on this machine


class _MarkerFixture(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.addCleanup(self._t.cleanup)
        self.cwd = self.tmp / "workspace"
        self.cwd.mkdir()
        self.alive = mo.alive_dir_for(self.cwd)
        self.alive.mkdir(parents=True, exist_ok=True)
        self.addCleanup(self._purge)

    def _purge(self):
        for p in self.alive.glob("owner-*"):
            try:
                p.unlink()
            except OSError:
                pass

    def _write_marker(self, token: str, pid: int):
        (self.alive / f"owner-{token}").write_text(str(pid), encoding="utf-8")

    def _self_token(self) -> str:
        pid = os.getpid()
        start = mo._proc_start_tick(pid) or "nostat"
        return f"{pid}.{start}"


class StopsOnlyTheNamedOneTest(_MarkerFixture):

    def test_a_live_owned_heartbeat_is_signalled(self):
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        self.addCleanup(proc.kill)
        start = mo._proc_start_tick(proc.pid) or "nostat"
        token = f"{proc.pid}.{start}"
        self._write_marker(token, proc.pid)

        res = mo.stop_owned(token, self.cwd)

        self.assertTrue(res["stopped"], res.get("reason"))
        self.assertEqual(res["pid"], proc.pid)
        proc.wait(timeout=10)

    def test_a_second_heartbeat_survives_the_first_being_stopped(self):
        """The whole point: one goes, the neighbour keeps ticking."""
        procs = [subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
                 for _ in range(2)]
        for p in procs:
            self.addCleanup(p.kill)
        tokens = []
        for p in procs:
            start = mo._proc_start_tick(p.pid) or "nostat"
            tok = f"{p.pid}.{start}"
            tokens.append(tok)
            self._write_marker(tok, p.pid)

        res = mo.stop_owned(tokens[0], self.cwd)

        self.assertTrue(res["stopped"], res.get("reason"))
        procs[0].wait(timeout=10)
        self.assertIsNone(procs[1].poll(), "the neighbour was killed too")

    def test_the_stopped_marker_is_removed_and_the_other_kept(self):
        procs = [subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
                 for _ in range(2)]
        for p in procs:
            self.addCleanup(p.kill)
        tokens = []
        for p in procs:
            tok = f"{p.pid}.{mo._proc_start_tick(p.pid) or 'nostat'}"
            tokens.append(tok)
            self._write_marker(tok, p.pid)

        mo.stop_owned(tokens[0], self.cwd)

        self.assertFalse((self.alive / f"owner-{tokens[0]}").exists())
        self.assertTrue((self.alive / f"owner-{tokens[1]}").exists())


class RefusesRatherThanGuessingTest(_MarkerFixture):
    """Each of these used to be a `pkill`."""

    def test_an_unknown_token_is_refused(self):
        res = mo.stop_owned("12345.678", self.cwd)
        self.assertFalse(res["stopped"])
        self.assertIn("no heartbeat marker", res["reason"])

    def test_a_stale_marker_is_refused(self):
        self._write_marker(f"{DEAD_PID}.111", DEAD_PID)
        res = mo.stop_owned(f"{DEAD_PID}.111", self.cwd)
        self.assertFalse(res["stopped"])
        self.assertIn("not running", res["reason"])

    def test_a_reused_pid_is_refused(self):
        """The pid is alive but is no longer the process the token names."""
        me = os.getpid()
        real_start = mo._proc_start_tick(me)
        if real_start is None:
            self.skipTest("no /proc on this platform")
        self._write_marker(f"{me}.0000000", me)
        res = mo.stop_owned(f"{me}.0000000", self.cwd)
        self.assertFalse(res["stopped"])
        self.assertIn("reused", res["reason"])

    def test_a_malformed_token_is_refused(self):
        self._write_marker("not-a-token", 1)
        res = mo.stop_owned("not-a-token", self.cwd)
        self.assertFalse(res["stopped"])

    def test_an_unreadable_start_time_refuses_rather_than_signalling_on_pid(self):
        """Without start-time confirmation the pid alone is not enough --
        signalling on it is how a reused pid gets killed."""
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        self.addCleanup(proc.kill)
        token = f"{proc.pid}.12345"
        self._write_marker(token, proc.pid)
        with mock.patch.object(mo, "_proc_start_tick", return_value=None):
            res = mo.stop_owned(token, self.cwd)
        self.assertFalse(res["stopped"])
        self.assertIsNone(proc.poll(), "refused but signalled anyway")

    def test_a_nostat_token_is_accepted_but_says_the_guarantee_is_weaker(self):
        """macOS has no /proc, so the pid alone is all there is. Accepted,
        with the weakness stated rather than hidden."""
        ok, reason = mo.owner_matches(f"{os.getpid()}.nostat", os.getpid())
        self.assertTrue(ok)
        self.assertIn("pid reuse", reason)


class TheHeartbeatPublishesItsOwnerTest(unittest.TestCase):

    def test_the_script_exports_and_announces_an_owner_token(self):
        src = (ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh").read_text(
            encoding="utf-8")
        self.assertIn("export OTR_MONITOR_OWNER", src)
        self.assertIn("monitor-stop --owner", src)

    def test_the_script_writes_an_owner_scoped_marker(self):
        src = (ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh").read_text(
            encoding="utf-8")
        self.assertIn('owner-${OTR_MONITOR_OWNER}', src)

    def test_the_shared_alive_marker_is_still_written(self):
        """directive.sh's degradation check reads it; this change is additive."""
        src = (ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh").read_text(
            encoding="utf-8")
        self.assertIn('touch "${_alive_dir}/alive"', src)

    def test_the_cli_refuses_monitor_stop_without_an_owner(self):
        r = subprocess.run([sys.executable, str(ROOT / "spawn.py"),
                            "monitor-stop", "-C", str(ROOT)],
                           capture_output=True, text=True, timeout=120)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--owner", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
