"""issue #3061: a heartbeat wake that advances nothing (this tick's delta
against the previous tick is empty) is counted as idle-wake, distinct from
a wake that acted (delta non-empty) — both persisted in the same tick-state
file poll_heartbeat_delta.py already writes.

Test derivation (test-derivation skill): equivalence partitioning over one
input axis (this tick's delta: empty vs non-empty) crossed with prior
persisted state (none vs some idle-wake vs some acted), plus the two
must-not checks from the issue body: idle-wake must never itself produce a
non-zero exit code or any "failure"/error framing (a quiet tick is not a
defect), and the periodic liveness beacon (which prints even though
nothing changed) must still count as idle-wake, not acted — `emitted_now`
is not the signal, `to_emit` is (see poll_heartbeat_delta.py's own comment
at the wake_outcomes assembly site).

Run: python3 -m pytest on-the-record/monitors/test_wake_outcomes.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

MONITORS_DIR = Path(__file__).resolve().parent
DELTA_SCRIPT = MONITORS_DIR / "poll_heartbeat_delta.py"


def _run_tick(state_path: Path, text: str, now: int | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["POLL_HEARTBEAT_TEXT"] = text
    return subprocess.run(
        [sys.executable, str(DELTA_SCRIPT), str(state_path), str(now or int(time.time()))],
        capture_output=True, text=True, env=env, timeout=15,
    )


def _run_report(state_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(DELTA_SCRIPT), "--report", str(state_path)],
        capture_output=True, text=True, timeout=15,
    )


class WakeOutcomeCountingTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_path = Path(self._tmp.name) / "state.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_report_with_no_prior_ticks_reads_as_zero_not_omitted(self):
        r = _run_report(self.state_path)
        self.assertEqual(r.returncode, 0)
        self.assertIn("idle-wake=0", r.stdout)
        self.assertIn("acted=0", r.stdout)

    def test_first_tick_with_content_counts_as_acted(self):
        _run_tick(self.state_path, "[poll-report] foo: HEALTHY-CONFIRMED — ok")
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["wake_outcomes"], {"idle_wake": 0, "acted": 1})

    def test_repeat_tick_with_no_change_counts_as_idle_wake(self):
        text = "[poll-report] foo: HEALTHY-CONFIRMED — ok"
        _run_tick(self.state_path, text)
        _run_tick(self.state_path, text)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["wake_outcomes"], {"idle_wake": 1, "acted": 1})

    def test_empty_roster_tick_is_idle_wake_not_omitted(self):
        # A wake with nothing at all to report (empty POLL_HEARTBEAT_TEXT)
        # is exactly the "spawned sessions legitimately mid-flight, nothing
        # to advance" case the issue's must-not clause protects — it must
        # still be counted (not silently dropped), as idle-wake.
        _run_tick(self.state_path, "")
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["wake_outcomes"], {"idle_wake": 1, "acted": 0})

    def test_changed_content_after_idle_ticks_flips_back_to_acted(self):
        text_a = "[poll-report] foo: HEALTHY-CONFIRMED — ok"
        text_b = "[poll-report] foo: STALLED — no progress"
        _run_tick(self.state_path, text_a)
        _run_tick(self.state_path, text_a)  # idle
        _run_tick(self.state_path, text_b)  # acted (changed)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["wake_outcomes"], {"idle_wake": 1, "acted": 2})

    def test_idle_wake_never_produces_a_nonzero_exit_code(self):
        # must-not: a quiet heartbeat is not a defect — it must never look
        # like a failure to a caller checking the process exit code.
        text = "[poll-report] foo: HEALTHY-CONFIRMED — ok"
        _run_tick(self.state_path, text)
        r = _run_tick(self.state_path, text)  # idle-wake tick
        self.assertEqual(r.returncode, 0)
        r2 = _run_report(self.state_path)
        self.assertEqual(r2.returncode, 0)

    def test_periodic_beacon_tick_still_counts_as_idle_wake_not_acted(self):
        # The 1800s liveness beacon prints even when nothing changed
        # (emitted_now True) -- the wake-outcome signal must be `to_emit`
        # (real content changed), not `emitted_now`, or every beacon tick
        # would be miscounted as "acted" despite advancing nothing.
        text = "[returned-pr] issue #22: PR #101 age=1h\n"
        now0 = int(time.time())
        _run_tick(self.state_path, text, now=now0)  # first_tick -> acted
        r = _run_tick(self.state_path, text, now=now0 + 1900)  # unchanged, past 1800s bound
        self.assertIn("returned-pr-pending", r.stdout)  # beacon did print
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["wake_outcomes"], {"idle_wake": 1, "acted": 1})


if __name__ == "__main__":
    unittest.main()
