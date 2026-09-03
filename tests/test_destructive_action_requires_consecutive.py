"""Issue #2969, acceptance check 4: destructive action (respawn) must not
be triggered by a single verdict snapshot. The issue is explicit this is
not hypothetical -- two live sessions were killed in error on an earlier
occasion by trusting a single verdict. `lifecycle._auto_respawn_check()`
(reached via `spawn._auto_respawn_check`) now requires
`RESPAWN_CONSECUTIVE_CONFIRMATIONS` consecutive "crashed" verdicts, sharing
the same `respawn_state.json`-backed dict a real watchdog tick would pass
tick to tick, before it ever calls `_record_dead_session()`.

Test derivation (test-derivation skill, BVA route on the confirmation
counter): the boundary is the counter crossing
RESPAWN_CONSECUTIVE_CONFIRMATIONS.
  - N-1 consecutive "crashed" calls -> _record_dead_session NOT called (below
    boundary)
  - N consecutive "crashed" calls -> _record_dead_session called exactly once
    (at boundary)
  - a non-"crashed" verdict between two "crashed" calls resets the streak
    -- N-1 crashed, 1 non-crashed, N-1 crashed again must still not reach
    the boundary
  - "stalled" and "in-progress" verdicts never count towards the streak at
    all (existing observe-only contract, unaffected by this change)"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402

DEAD_PID = 999999999


def _git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a],
                           capture_output=True, text=True, check=True)


class DestructiveActionRequiresConsecutiveTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
        self.work = self.tmp / "on-the-record-issue-9004-demo"
        subprocess.run(["git", "clone", "-q", str(remote), str(self.work)], check=True)
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        (self.work / "a.txt").write_text("1")
        _git(self.work, "add", "a.txt")
        _git(self.work, "commit", "-q", "-m", "c1")
        self.branch = "issue-9004/demo"
        _git(self.work, "branch", "-m", self.branch)
        _git(self.work, "push", "-q", "-u", "origin", self.branch)
        self.events_path = spawn._events_path(str(self.work))
        # No session-end and a dead recorded pid -> session_end_verdict()
        # resolves to "crashed" every time this entry is checked (same
        # fixture shape as test_reconcile_crash_verdict_race.py).
        self.events_path.write_text(
            '{"ts": 1, "type": "session-start", "detail": {"pid": %d}}\n' % DEAD_PID)

    def _entry(self, wrapper_pid=DEAD_PID):
        return {"pid": DEAD_PID, "work": str(self.work),
                "before_head": _git(self.work, "rev-parse", "HEAD").stdout.strip(),
                "log": None, "issue": 9004, "skill": "demo",
                "expects_pr": False, "wrapper_pid": wrapper_pid}

    def test_destructive_action_requires_consecutive_below_threshold_never_respawns(self):
        entry = self._entry()
        state = {}
        with mock.patch.object(spawn, "_record_dead_session") as respawn_or_cap:
            for _ in range(spawn.RESPAWN_CONSECUTIVE_CONFIRMATIONS - 1):
                spawn._auto_respawn_check("issue-9004/demo", entry, state)
        respawn_or_cap.assert_not_called()

    def test_destructive_action_requires_consecutive_at_threshold_respawns_once(self):
        entry = self._entry()
        state = {}
        with mock.patch.object(spawn, "_record_dead_session") as respawn_or_cap:
            for _ in range(spawn.RESPAWN_CONSECUTIVE_CONFIRMATIONS):
                spawn._auto_respawn_check("issue-9004/demo", entry, state)
        respawn_or_cap.assert_called_once()

    def test_destructive_action_requires_consecutive_streak_persists_across_calls_via_state(self):
        # Same contract as above, but proves the counter genuinely lives in
        # the passed-in `state` dict (what roster_watchdog() reloads from
        # respawn_state.json each tick) rather than some in-call-only
        # bookkeeping -- a fresh dict each call would never reach threshold.
        entry = self._entry()
        state = {}
        with mock.patch.object(spawn, "_record_dead_session") as respawn_or_cap:
            spawn._auto_respawn_check("issue-9004/demo", entry, state)
            respawn_or_cap.assert_not_called()
            self.assertGreaterEqual(state["issue-9004/demo"]["crash_confirms"], 1)
            for _ in range(spawn.RESPAWN_CONSECUTIVE_CONFIRMATIONS - 1):
                spawn._auto_respawn_check("issue-9004/demo", entry, state)
        respawn_or_cap.assert_called_once()

    def test_destructive_action_requires_consecutive_non_crash_verdict_resets_streak(self):
        # An in-flight completion (wrapper still alive) reads as
        # "in-progress", not "crashed" -- it must zero the streak, so a
        # crash run interrupted by one good tick has to start over.
        entry = self._entry()
        in_flight_entry = self._entry(wrapper_pid=os.getpid())
        state = {}
        with mock.patch.object(spawn, "_record_dead_session") as respawn_or_cap:
            for _ in range(spawn.RESPAWN_CONSECUTIVE_CONFIRMATIONS - 1):
                spawn._auto_respawn_check("issue-9004/demo", entry, state)
            spawn._auto_respawn_check("issue-9004/demo", in_flight_entry, state)
            self.assertEqual(state["issue-9004/demo"]["crash_confirms"], 0)
            for _ in range(spawn.RESPAWN_CONSECUTIVE_CONFIRMATIONS - 1):
                spawn._auto_respawn_check("issue-9004/demo", entry, state)
            respawn_or_cap.assert_not_called()
            spawn._auto_respawn_check("issue-9004/demo", entry, state)
        respawn_or_cap.assert_called_once()


if __name__ == "__main__":
    unittest.main()
