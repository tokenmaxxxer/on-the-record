"""issue #2742: a spawn that never started (operator declined it at the
approval prompt, or the orchestrator's own Bash-tool call timed out mid-
bootstrap) used to be reported by the watchdog as a probable crash — "no
outcome recorded ... process likely died before it could report why" —
and left its cloned workspace, `.spawn-claim`, and `.task.txt` behind
(83-88MB observed live). Nothing died in either case; the caller went
away.

The general case is "the caller went away", not "the operator declined" —
a decline is one instance of it, an orchestrator tool-call timeout is
another, and both arrive at the spawn.py process as the same real signal
(SIGTERM/SIGINT). A genuine crash (SIGKILL/OOM) is not catchable by
Python at all, so it must and does keep producing the old generic line —
that divergence is exactly what tells the two cases apart, per the
issue's must-not (no timeout heuristic; the signal itself is the only
distinguishing evidence).

  python3 -m pytest test/test_bootstrap_signal_guard.py
"""
from __future__ import annotations
import json
import os
import signal
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import spawn
import roster


def _wait_for(path: Path, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise AssertionError(f"{path} never appeared — child never reached armed state")


class BootstrapSignalGuardCaughtSignalTest(unittest.TestCase):
    """Real signal delivered to a real forked process — the same
    real-process convention as tests/test_tmp_resource_gc.py's
    `_dead_pid()`, since a mocked call can't stand in for "the OS actually
    interrupted this process mid-syscall"."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.attempts_path = Path(self._td.name) / "spawn-attempts.jsonl"
        p = mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.attempts_path)
        p.start()
        self.addCleanup(p.stop)

    def _fork_armed_child(self, work: Path, attempt_id: str, ready: Path) -> int:
        pid = os.fork()
        if pid == 0:
            try:
                armed = spawn._arm_bootstrap_signal_guard(attempt_id)
                armed[0]["cwd"] = str(work)
                ready.write_text("1")
                time.sleep(30)  # a real signal arrives long before this elapses
            except BaseException:
                os._exit(1)
            os._exit(0)
        return pid

    def test_sigterm_mid_bootstrap_reports_caller_departed_and_cleans_up(self):
        work = Path(self._td.name) / "ws"
        work.mkdir()
        (work / "marker").write_text("cloned")
        claim = spawn._spawn_claim_path(str(work))
        claim.write_text("{}")
        task_file = Path(str(work) + ".task.txt")
        task_file.write_text("do the thing")
        ready = Path(self._td.name) / "ready-term"

        pid = self._fork_armed_child(work, "2742:role:1:1", ready)
        _wait_for(ready)
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)

        self.assertFalse(work.exists())
        self.assertFalse(claim.exists())
        self.assertFalse(task_file.exists())
        events = [json.loads(l) for l in
                  self.attempts_path.read_text(encoding="utf-8").splitlines()]
        outcomes = [e for e in events if e.get("event") == "spawn_attempt_outcome"]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["outcome"], "halted")
        self.assertIn("SIGTERM", outcomes[0]["detail"])
        self.assertIn("not a crash", outcomes[0]["detail"])
        self.assertNotIn("likely died", outcomes[0]["detail"])

    def test_sigint_mid_bootstrap_also_reports_caller_departed(self):
        work = Path(self._td.name) / "ws-int"
        work.mkdir()
        ready = Path(self._td.name) / "ready-int"

        pid = self._fork_armed_child(work, "2742:role:2:2", ready)
        _wait_for(ready)
        os.kill(pid, signal.SIGINT)
        os.waitpid(pid, 0)

        self.assertFalse(work.exists())
        events = [json.loads(l) for l in
                  self.attempts_path.read_text(encoding="utf-8").splitlines()]
        outcomes = [e for e in events if e.get("event") == "spawn_attempt_outcome"]
        self.assertEqual(len(outcomes), 1)
        self.assertIn("SIGINT", outcomes[0]["detail"])

    def test_sigkill_mid_bootstrap_records_nothing_and_leaves_workspace(self):
        """The uncatchable case: no Python code runs at all, so nothing is
        recorded and nothing is cleaned up. This is the case that must
        keep producing the old generic line — it is a real, if rare, way
        for a spawn to actually die, and coverage of it must not narrow."""
        work = Path(self._td.name) / "ws-kill"
        work.mkdir()
        (work / "marker").write_text("cloned")
        ready = Path(self._td.name) / "ready-kill"

        pid = self._fork_armed_child(work, "2742:role:3:3", ready)
        _wait_for(ready)
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)

        self.assertTrue(work.exists())  # nothing could run to remove it
        if self.attempts_path.exists():
            events = [json.loads(l) for l in
                      self.attempts_path.read_text(encoding="utf-8").splitlines()]
            self.assertFalse(any(e.get("event") == "spawn_attempt_outcome"
                                  for e in events))

    def test_disarmed_after_session_log_survives_sigterm_untouched(self):
        """Once bootstrap succeeds (`_record_spawn_outcome(..., "session-
        log", ...)` already written) the guard must be off — a signal
        arriving after that point is the existing dead-entry watchdog's
        job, not this one's, and must never delete a workspace a real
        session may now be using."""
        work = Path(self._td.name) / "ws-live"
        work.mkdir()
        (work / "marker").write_text("session running")
        ready = Path(self._td.name) / "ready-live"
        attempt_id = "2742:role:4:4"

        def _child():
            armed = spawn._arm_bootstrap_signal_guard(attempt_id)
            armed[0]["cwd"] = str(work)
            spawn._record_spawn_outcome(attempt_id, "session-log", "/dev/null")
            spawn._disarm_bootstrap_signal_guard(armed)
            ready.write_text("1")
            time.sleep(30)

        pid = os.fork()
        if pid == 0:
            try:
                _child()
            except BaseException:
                os._exit(1)
            os._exit(0)
        _wait_for(ready)
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)

        self.assertTrue(work.exists())  # default SIGTERM: process ends, workspace untouched
        events = [json.loads(l) for l in
                  self.attempts_path.read_text(encoding="utf-8").splitlines()]
        outcomes = [e for e in events if e.get("event") == "spawn_attempt_outcome"]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["outcome"], "session-log")


class SpawnAttemptSweepReportsCallerDepartedDistinctlyTest(unittest.TestCase):
    """End-to-end through the watchdog sweep (issue #2742 acceptance bullet
    2): the SIGTERM-recorded outcome and a genuinely-dead (no outcome)
    attempt must produce different `[spawn-attempt]` lines."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.attempts_path = Path(self._td.name) / "spawn-attempts.jsonl"
        patches = [
            mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.attempts_path),
            mock.patch.object(spawn, "ledger_write", lambda ev: None),
            mock.patch.object(spawn, "ledger_check_and_stamp", lambda *a, **k: True),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_declined_and_genuinely_dead_produce_different_lines(self):
        now = time.time()
        with self.attempts_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"event": "spawn_attempt", "attempt_id": "a1",
                                  "issue": 2741, "skill": "declined-role",
                                  "pid": 111, "cwd": "/tmp/does-not-matter-a",
                                  "ts": now - 5}) + "\n")
            fh.write(json.dumps({"event": "spawn_attempt_outcome",
                                  "attempt_id": "a1", "outcome": "halted",
                                  "detail": "caller departed before bootstrap "
                                            "finished (received SIGTERM) — "
                                            "this is not a crash, no session "
                                            "ever started",
                                  "ts": now - 4}) + "\n")
            fh.write(json.dumps({"event": "spawn_attempt", "attempt_id": "a2",
                                  "issue": 2741, "skill": "killed-role",
                                  "pid": 222, "cwd": "/tmp/does-not-matter-b",
                                  "ts": now - (roster.SPAWN_ATTEMPT_GRACE_SEC + 30)}) + "\n")

        with mock.patch("builtins.print") as mocked_print:
            count = roster.spawn_attempt_sweep(d_all={}, now=now)

        self.assertEqual(count, 2)
        lines = [str(c.args[0]) for c in mocked_print.call_args_list]
        declined_line = next(l for l in lines if "declined-role" in l)
        killed_line = next(l for l in lines if "killed-role" in l)
        self.assertIn("SIGTERM", declined_line)
        self.assertIn("not a crash", declined_line)
        self.assertNotIn("likely died", declined_line)
        self.assertIn("likely died", killed_line)
        self.assertNotIn("SIGTERM", killed_line)
        self.assertNotEqual(declined_line, killed_line)


if __name__ == "__main__":
    unittest.main()
