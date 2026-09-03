"""Issue #3273: dead lock files piled up and looked like a jammed system.

3,945 of them, the oldest from 2026-08-15, every one held by a dead pid.
They blocked nothing -- acquire already reclaims a dead lock -- but reading
that directory is what made me call the watchdog "really broken" and
retract it a minute later. The state that looks alarming and the state
that is alarming were indistinguishable at a glance.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402
import watchdog  # noqa: E402

watchdog._sp = spawn
OLD = time.time() - watchdog.DEAD_LOCK_MIN_AGE_SEC - 60


class OnlyProvablyDeadLocksAreRemovedTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())

    def _write(self, name, payload, mtime=OLD):
        p = self.d / name
        p.write_text(payload if isinstance(payload, str) else json.dumps(payload),
                     encoding="utf-8")
        os.utime(p, (mtime, mtime))
        return p

    def test_a_dead_holders_lock_is_removed(self):
        p = self._write("a.lock", {"pid": 999999, "start_time": "1"})
        r = watchdog.sweep_dead_locks(self.d)
        self.assertEqual(r["removed"], 1)
        self.assertFalse(p.exists())

    def test_a_live_holders_lock_survives(self):
        me = os.getpid()
        p = self._write("b.lock",
                        {"pid": me, "start_time": spawn._proc_start_time(me)})
        r = watchdog.sweep_dead_locks(self.d)
        self.assertEqual(r["removed"], 0)
        self.assertEqual(r["live"], 1)
        self.assertTrue(p.exists(), "removing a live lock lets two watchdogs "
                                    "sweep one board at once")

    def test_a_reused_pid_with_a_different_start_time_is_dead(self):
        me = os.getpid()
        p = self._write("c.lock", {"pid": me, "start_time": "definitely-not"})
        watchdog.sweep_dead_locks(self.d)
        self.assertFalse(p.exists())

    def test_an_unreadable_lock_is_counted_not_deleted(self):
        p = self._write("d.lock", "{not json")
        r = watchdog.sweep_dead_locks(self.d)
        self.assertEqual(r["unreadable"], 1)
        self.assertTrue(p.exists(), "uncertainty must never delete")

    def test_a_just_written_lock_is_not_touched(self):
        p = self._write("e.lock", {"pid": 999999, "start_time": "1"},
                        mtime=time.time())
        r = watchdog.sweep_dead_locks(self.d)
        self.assertEqual(r["too_young"], 1)
        self.assertTrue(p.exists(), "a holder may still be starting up")

    def test_the_budget_bounds_one_tick(self):
        for i in range(20):
            self._write(f"f{i}.lock", {"pid": 999999, "start_time": "1"})
        r = watchdog.sweep_dead_locks(self.d, budget=5)
        self.assertEqual(r["examined"], 5)
        self.assertEqual(len(list(self.d.glob("*.lock"))), 15)

    def test_a_missing_directory_is_not_an_error(self):
        r = watchdog.sweep_dead_locks(self.d / "nope")
        self.assertEqual(r["removed"], 0)


if __name__ == "__main__":
    unittest.main()
