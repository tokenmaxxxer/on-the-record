"""Issue #2874: reconcile()/`_auto_respawn_check()` judged a completed
session "crashed" and queued a respawn in the same tick poll-report
(`diagnose_health()`) correctly called it COMPLETED.

Root cause: `session_end_verdict()` only ever checked the claude
subprocess's own pid. That pid dies at `proc.wait()` inside
`_spawn_one()`'s `for line in proc.stdout:` loop tail -- normal exit --
*before* the wrapper finishes push/gate/classify/ledger_write and appends
the `session-end` event (spawn.py, `_spawn_one()`). A poll tick landing in
that narrow window sees a dead child pid and no `session-end` yet, and
`session_end_verdict()` returned `crashed` for a session that had already
succeeded and opened its PR -- the exact shape issue #224's hunt already
fixed for `_watch --follow` (events.py) via `wrapper_pid` (the roster
entry's own driving process, alive through the whole tail), but that fix
was never threaded into `session_end_verdict()` itself, so reconcile(),
`_auto_respawn_check()`, and `diagnose_health()` kept disagreeing.

This reproduces the race directly (a `session-start` event with no
`session-end`, and a dead recorded pid) against the real entry points --
`board.session_end_verdict()`, `spawn.reconcile()` fed by
`spawn._build_expected`/`_build_observed()`, `lifecycle._auto_respawn_check()`
(via `spawn._auto_respawn_check`), and `watchdog.diagnose_health()` -- never
a stub of any of them. Each test also has a genuine-crash counterpart
(wrapper_pid absent/dead too) to prove respawn keeps firing for real
crashes, per the issue's "must not" constraint.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import board  # noqa: E402
import lifecycle  # noqa: E402
import spawn  # noqa: E402
import watchdog  # noqa: E402

board._sp = spawn
watchdog._sp = spawn
lifecycle._sp = spawn

DEAD_PID = 999999999  # never a real pid (test_unrecovered_commit_count.py convention)


def _git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a],
                           capture_output=True, text=True, check=True)


class CrashVerdictRaceTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        self.remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        self.work = self.tmp / "on-the-record-issue-2874-demo"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.work)], check=True)
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        (self.work / "a.txt").write_text("1")
        _git(self.work, "add", "a.txt")
        _git(self.work, "commit", "-q", "-m", "c1")
        self.branch = "issue-2874/demo"
        _git(self.work, "branch", "-m", self.branch)
        _git(self.work, "push", "-q", "-u", "origin", self.branch)
        self.events_path = spawn._events_path(str(self.work))
        self.events_path.write_text(
            '{"ts": 1, "type": "session-start", "detail": {"pid": %d}}\n' % DEAD_PID)

    def _entry(self, wrapper_pid=None):
        e = {"pid": DEAD_PID, "work": str(self.work), "before_head":
             _git(self.work, "rev-parse", "HEAD").stdout.strip(),
             "log": None, "issue": 2874, "skill": "demo", "expects_pr": False}
        if wrapper_pid is not None:
            e["wrapper_pid"] = wrapper_pid
        return e

    # --- session_end_verdict() itself -----------------------------------

    def test_verdict_in_flight_when_wrapper_still_alive(self):
        verdict = board.session_end_verdict(str(self.work), None, wrapper_pid=os.getpid())
        self.assertEqual(verdict, "in-progress")

    def test_verdict_still_crashed_when_wrapper_also_dead(self):
        verdict = board.session_end_verdict(str(self.work), None, wrapper_pid=DEAD_PID)
        self.assertEqual(verdict, "crashed")

    def test_verdict_unchanged_when_wrapper_pid_omitted(self):
        # existing callers that never learned about wrapper_pid keep today's
        # behavior byte-identical (pure-addition guarantee).
        verdict = board.session_end_verdict(str(self.work), None)
        self.assertEqual(verdict, "crashed")

    # --- reconcile(), fed by the real _build_expected/_build_observed ---

    def test_reconcile_no_divergence_for_in_flight_completion(self):
        entry = self._entry(wrapper_pid=os.getpid())
        divergences = spawn.reconcile(spawn._build_expected(entry),
                                       spawn._build_observed(self.tmp, entry))
        self.assertEqual(divergences, [])

    def test_reconcile_still_flags_genuine_crash(self):
        entry = self._entry(wrapper_pid=DEAD_PID)
        divergences = spawn.reconcile(spawn._build_expected(entry),
                                       spawn._build_observed(self.tmp, entry))
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0]["kind"], "session-crashed")
        self.assertEqual(divergences[0]["next_action"], "respawn")

    # --- _auto_respawn_check(): the action that actually queues a respawn

    def test_auto_respawn_check_does_not_respawn_in_flight_completion(self):
        entry = self._entry(wrapper_pid=os.getpid())
        with mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap:
            spawn._auto_respawn_check("issue-2874/demo", entry, {})
        respawn_or_cap.assert_not_called()

    def test_auto_respawn_check_still_respawns_genuine_crash(self):
        # Issue #2969: a single "crashed" verdict snapshot no longer
        # triggers a respawn by itself -- it takes
        # RESPAWN_CONSECUTIVE_CONFIRMATIONS consecutive ticks agreeing
        # (same shared state dict, as roster_watchdog() would pass tick
        # to tick) before _respawn_or_cap() is ever called.
        entry = self._entry(wrapper_pid=DEAD_PID)
        state = {}
        with mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap:
            for _ in range(spawn.RESPAWN_CONSECUTIVE_CONFIRMATIONS - 1):
                spawn._auto_respawn_check("issue-2874/demo", entry, state)
            respawn_or_cap.assert_not_called()
            spawn._auto_respawn_check("issue-2874/demo", entry, state)
        respawn_or_cap.assert_called_once()

    # --- diagnose_health() (poll-report): stays correct in general, not
    #     only when a PR already happens to exist (the pre-#2874 fallback)

    def test_diagnose_health_completion_without_a_pr_via_wrapper_pid(self):
        entry = self._entry(wrapper_pid=os.getpid())
        health = watchdog.diagnose_health(self.branch, entry, root=self.tmp,
                                           pr_index={}, commit_count=0)
        self.assertIsNone(health["state"])

    def test_diagnose_health_still_dead_errored_for_genuine_crash(self):
        entry = self._entry(wrapper_pid=DEAD_PID)
        health = watchdog.diagnose_health(self.branch, entry, root=self.tmp,
                                           pr_index={}, commit_count=0)
        self.assertEqual(health["state"], "DEAD-ERRORED")


if __name__ == "__main__":
    unittest.main()
