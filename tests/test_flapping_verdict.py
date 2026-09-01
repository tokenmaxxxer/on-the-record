"""Issue #2969, acceptance check 3: the field report itself was a verdict
reversal (STALLED-FLAT-PROGRESS, then minutes later HEALTHY) that passed
as two independent, unremarkable reports. A verdict that reverses within a
short window must be reported as a signal in its own right (FLAPPING)
instead.

Test derivation (test-derivation skill, state-transition route):
`watchdog._record_verdict_and_check_flapping(key, verdict_state, now,
state)` is a 3-observation ring buffer per key. States exercised:
  - <3 observations recorded yet -> never flags (stable/insufficient history)
  - A -> B -> A within FLAPPING_WINDOW_SEC -> flags True (the reversal)
  - A -> B -> A but OUTSIDE the window -> does not flag (too far apart to
    call it flapping, per the "short window" qualifier)
  - A -> A -> A (no reversal at all, stable) -> never flags
  - A -> B -> C (three distinct states, no reversal back to A) -> never
    flags
Empty-state acceptance note ("a stable verdict history emits no flapping
signal; passes") is covered by the A -> A -> A and <3-observation cases."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402
import watchdog  # noqa: E402

watchdog._sp = spawn


class FlappingVerdictTest(unittest.TestCase):
    def test_flapping_verdict_insufficient_history_never_flags(self):
        state = {}
        self.assertFalse(
            watchdog._record_verdict_and_check_flapping("k", "A", 1000, state))
        self.assertFalse(
            watchdog._record_verdict_and_check_flapping("k", "B", 1010, state))

    def test_flapping_verdict_reversal_within_window_flags(self):
        state = {}
        watchdog._record_verdict_and_check_flapping("k", "HEALTHY-CONFIRMED", 1000, state)
        watchdog._record_verdict_and_check_flapping("k", "STALLED-FLAT-PROGRESS", 1010, state)
        flagged = watchdog._record_verdict_and_check_flapping(
            "k", "HEALTHY-CONFIRMED", 1010 + watchdog.FLAPPING_WINDOW_SEC - 1, state)
        self.assertTrue(flagged)

    def test_flapping_verdict_reversal_outside_window_does_not_flag(self):
        # The window is measured from when the verdict LEFT the first
        # state (t2) to when it returned to it (t3) -- not from the first
        # observation ever made of that state.
        state = {}
        watchdog._record_verdict_and_check_flapping("k", "HEALTHY-CONFIRMED", 1000, state)
        watchdog._record_verdict_and_check_flapping("k", "STALLED-FLAT-PROGRESS", 1010, state)
        flagged = watchdog._record_verdict_and_check_flapping(
            "k", "HEALTHY-CONFIRMED", 1010 + watchdog.FLAPPING_WINDOW_SEC + 1, state)
        self.assertFalse(flagged)

    def test_flapping_verdict_stable_repeated_verdict_never_flags(self):
        state = {}
        watchdog._record_verdict_and_check_flapping("k", "HEALTHY-CONFIRMED", 1000, state)
        watchdog._record_verdict_and_check_flapping("k", "HEALTHY-CONFIRMED", 1010, state)
        flagged = watchdog._record_verdict_and_check_flapping(
            "k", "HEALTHY-CONFIRMED", 1020, state)
        self.assertFalse(flagged)

    def test_flapping_verdict_three_distinct_states_no_reversal_does_not_flag(self):
        state = {}
        watchdog._record_verdict_and_check_flapping("k", "A", 1000, state)
        watchdog._record_verdict_and_check_flapping("k", "B", 1010, state)
        flagged = watchdog._record_verdict_and_check_flapping("k", "C", 1020, state)
        self.assertFalse(flagged)

    def test_flapping_verdict_keys_are_independent(self):
        state = {}
        watchdog._record_verdict_and_check_flapping("k1", "A", 1000, state)
        watchdog._record_verdict_and_check_flapping("k1", "B", 1010, state)
        # A different key's first two observations must not borrow k1's
        # history and must not spuriously flag.
        flagged = watchdog._record_verdict_and_check_flapping("k2", "A", 1020, state)
        self.assertFalse(flagged)

    def test_flapping_verdict_surfaces_on_diagnose_health_result(self):
        # Integration: diagnose_health() attaches the flag to its own
        # returned dict when a shared state store crosses ticks, so
        # roster_watchdog() can print a dedicated [flapping] signal.
        state = {}
        entry_healthy = {"pid": __import__("os").getpid(), "issue": 9003,
                         "skill": "demo",
                         "start_time": watchdog._proc_start_time(__import__("os").getpid())}
        watchdog.diagnose_health("issue-9003/demo", entry_healthy, anomalies=[], state=state)
        watchdog.diagnose_health("issue-9003/demo", entry_healthy,
                                 anomalies=["log-silence: 999분째 로그 무응답 (x)"],
                                 state=state, now=1000)
        third = watchdog.diagnose_health("issue-9003/demo", entry_healthy, anomalies=[],
                                         state=state, now=1000 + watchdog.FLAPPING_WINDOW_SEC - 1)
        self.assertTrue(third.get("flapping"))


if __name__ == "__main__":
    unittest.main()
