"""Issue #2969, acceptance check 1: `watchdog.py:519`'s old residual
`HEALTHY` branch printed "최근 로그 성장, RUNNING" (I confirmed growth) for
every session that tripped no anomaly check above it -- including sessions
where nothing was actually observed growing. This asserted an active
observation the code never made.

Test derivation (test-derivation skill, state-transition route): the
residual branch is a 2-state machine keyed off "did the session's log
grow since the last observation this key was seen at":
  - state CONFIRMED: this tick's log size > last-recorded size for this key
  - state UNCONFIRMED: log absent, state-store absent (single-shot call),
    size unchanged, or no prior observation to compare against (first tick)
Transitions exercised below: first-tick (no prior) -> UNCONFIRMED,
UNCONFIRMED -> CONFIRMED (growth arrives), CONFIRMED -> UNCONFIRMED
(growth stops), and the empty-state acceptance note (no live session ->
no verdict at all, unaffected by this split).

`diagnose_health()` reaches this branch only past every anomaly check, so
each test entry is built to fall through: alive (paired via `start_time`),
no deadlock signature (no `work`), and `anomalies=[]` explicitly."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402
import watchdog  # noqa: E402

watchdog._sp = spawn


def _entry(log_path):
    return {"pid": os.getpid(), "log": str(log_path), "issue": 9001,
            "skill": "demo", "start_time": watchdog._proc_start_time(os.getpid())}


class HealthVerdictConfirmedVsUnconfirmedTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.log_path = Path(self._tmpdir.name) / "session.log"
        self.log_path.write_text("line one\n")
        self.addCleanup(self._tmpdir.cleanup)

    def test_health_verdict_confirmed_vs_unconfirmed_first_observation_is_unconfirmed(self):
        # Given a key with no prior recorded log size (first tick),
        # When diagnose_health() reaches the residual branch,
        # Then it reports UNCONFIRMED -- there is nothing to compare
        # growth against yet, so growth must not be claimed.
        state = {}
        health = watchdog.diagnose_health("issue-9001/demo", _entry(self.log_path),
                                          anomalies=[], state=state)
        self.assertEqual(health["state"], "HEALTHY-UNCONFIRMED")
        self.assertNotIn("성장 확인", health["detail"])

    def test_health_verdict_confirmed_vs_unconfirmed_growth_between_ticks_confirms(self):
        # Given a first tick already observed (state primed),
        # When the log genuinely grows before the next tick,
        # Then the verdict flips to CONFIRMED and the detail says so.
        state = {}
        watchdog.diagnose_health("issue-9001/demo", _entry(self.log_path),
                                 anomalies=[], state=state)
        with self.log_path.open("a") as f:
            f.write("a whole lot more transcript content just got appended\n")
        health = watchdog.diagnose_health("issue-9001/demo", _entry(self.log_path),
                                          anomalies=[], state=state)
        self.assertEqual(health["state"], "HEALTHY-CONFIRMED")
        self.assertIn("성장 확인", health["detail"])

    def test_health_verdict_confirmed_vs_unconfirmed_no_growth_stays_unconfirmed(self):
        # Given a first tick already observed,
        # When the next tick's log is byte-identical (no growth),
        # Then the verdict stays UNCONFIRMED -- "no anomaly" is not
        # "confirmed progress".
        state = {}
        watchdog.diagnose_health("issue-9001/demo", _entry(self.log_path),
                                 anomalies=[], state=state)
        health = watchdog.diagnose_health("issue-9001/demo", _entry(self.log_path),
                                          anomalies=[], state=state)
        self.assertEqual(health["state"], "HEALTHY-UNCONFIRMED")

    def test_health_verdict_confirmed_vs_unconfirmed_missing_log_never_confirms(self):
        # Given an entry with no log path at all (e.g. adhoc/legacy entry),
        # When diagnose_health() reaches the residual branch,
        # Then it can never assert confirmed growth -- there is no source
        # to observe growth from.
        entry = {"pid": os.getpid(), "issue": 9001, "skill": "demo",
                 "start_time": watchdog._proc_start_time(os.getpid())}
        state = {}
        health = watchdog.diagnose_health("issue-9001/demo", entry,
                                          anomalies=[], state=state)
        self.assertEqual(health["state"], "HEALTHY-UNCONFIRMED")

    def test_health_verdict_confirmed_vs_unconfirmed_reverts_when_growth_stops(self):
        # Given a tick that already confirmed growth,
        # When the following tick shows no further growth,
        # Then the verdict demotes back to UNCONFIRMED -- each tick's
        # detail reflects only what was actually observed that tick.
        state = {}
        watchdog.diagnose_health("issue-9001/demo", _entry(self.log_path),
                                 anomalies=[], state=state)
        with self.log_path.open("a") as f:
            f.write("more content\n")
        confirmed = watchdog.diagnose_health("issue-9001/demo", _entry(self.log_path),
                                             anomalies=[], state=state)
        self.assertEqual(confirmed["state"], "HEALTHY-CONFIRMED")
        stalled_growth = watchdog.diagnose_health("issue-9001/demo", _entry(self.log_path),
                                                  anomalies=[], state=state)
        self.assertEqual(stalled_growth["state"], "HEALTHY-UNCONFIRMED")

    def test_health_verdict_confirmed_vs_unconfirmed_empty_state_no_live_session(self):
        # Empty-state acceptance note: no live session means no verdict is
        # produced at all -- a dead pid short-circuits before this branch
        # and this split never applies to it.
        entry = {"pid": 999999999, "issue": 9001, "skill": "demo"}
        health = watchdog.diagnose_health("issue-9001/demo", entry, anomalies=[])
        self.assertNotIn(health["state"], ("HEALTHY-CONFIRMED", "HEALTHY-UNCONFIRMED"))


if __name__ == "__main__":
    unittest.main()
