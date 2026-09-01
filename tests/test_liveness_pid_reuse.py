"""Issue #2969, acceptance check 2: liveness must pair `pid` with process
start time rather than trusting `_alive()` (raw `os.kill(pid, 0)`) alone --
a crashed session's pid can be reused by an unrelated process, which
`_alive()` cannot tell apart from the original session still running
(the same shape as issue #2749/#2924's identity-check gap, now closed for
`diagnose_health()`'s own liveness gate via `watchdog._paired_liveness()`).

Test derivation (test-derivation skill, EP route): `_paired_liveness(pid,
recorded_start_time)` partitions into 5 equivalence classes --
  1. dead pid -> "dead" (regardless of recorded_start_time)
  2. alive pid, recorded_start_time matches current -> "alive" (confirmed)
  3. alive pid, recorded_start_time present but MISMATCHES current
     (pid reuse) -> "dead" (confirmed reused, not confirmed alive)
  4. alive pid, recorded_start_time is None (older/legacy entry) ->
     "unconfirmed" (pairing cannot be established)
  5. alive pid, recorded_start_time present but the current process's own
     start time cannot be read (/proc unavailable, issue #2924's macOS
     gap) -> "unconfirmed"
All 5 partitions and their boundary (start_time equal vs one-char
different) are exercised below; 5/5 = 100% EP coverage of this function's
documented contract."""
import os
import sys
import unittest
from unittest import mock

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402
import watchdog  # noqa: E402

watchdog._sp = spawn

DEAD_PID = 999999999


class LivenessPidReuseTest(unittest.TestCase):
    def test_liveness_pid_reuse_dead_pid_is_dead_regardless_of_start_time(self):
        self.assertEqual(watchdog._paired_liveness(DEAD_PID, "12345"), "dead")
        self.assertEqual(watchdog._paired_liveness(DEAD_PID, None), "dead")

    def test_liveness_pid_reuse_alive_with_matching_start_time_is_alive(self):
        my_pid = os.getpid()
        real_start = watchdog._proc_start_time(my_pid)
        self.assertEqual(watchdog._paired_liveness(my_pid, real_start), "alive")

    def test_liveness_pid_reuse_alive_with_mismatched_start_time_is_dead(self):
        # This is the actual pid-reuse scenario: the pid the roster recorded
        # started at some earlier time; the pid now belongs to a process
        # (still this test's own pid, for reproducibility) whose recorded
        # start time no longer matches -- must NOT read as "alive".
        my_pid = os.getpid()
        real_start = watchdog._proc_start_time(my_pid)
        bogus_start = (real_start + "0") if real_start else "0"
        self.assertEqual(watchdog._paired_liveness(my_pid, bogus_start), "dead")

    def test_liveness_pid_reuse_alive_with_no_recorded_start_time_is_unconfirmed(self):
        # A pre-#2969 roster entry never recorded start_time -- pairing
        # cannot be established, so this must not be reported "alive".
        my_pid = os.getpid()
        self.assertEqual(watchdog._paired_liveness(my_pid, None), "unconfirmed")

    def test_liveness_pid_reuse_proc_unavailable_degrades_to_unconfirmed(self):
        # Issue #2924's platform gap (macOS has no /proc): even with a
        # recorded start_time on file, if _proc_start_time() cannot read
        # the current process's start time, the pairing cannot be
        # established either -- demote to unconfirmed, never guess alive.
        my_pid = os.getpid()
        with mock.patch.object(watchdog, "_proc_start_time", return_value=None):
            self.assertEqual(
                watchdog._paired_liveness(my_pid, "some-recorded-value"),
                "unconfirmed")

    def test_liveness_pid_reuse_diagnose_health_reports_third_state_not_healthy_or_dead(self):
        # Integration: diagnose_health() must not resolve an unconfirmed
        # pairing by guessing in either direction (the issue's must-not) --
        # it reaches a dedicated third state, not HEALTHY and not any DEAD-*.
        entry = {"pid": os.getpid(), "issue": 9002, "skill": "demo"}
        health = watchdog.diagnose_health("issue-9002/demo", entry, anomalies=[])
        self.assertEqual(health["state"], "LIVENESS-UNCONFIRMED")
        self.assertEqual(health["next_action"], "resume-watch")


if __name__ == "__main__":
    unittest.main()
