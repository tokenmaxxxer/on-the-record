"""The alive marker was written once and never again (issue #3278).

`directive.sh`'s dead-monitor check compares that marker's age against a
600s grace. Measured on 2026-09-03: the marker was 10,901 seconds old --
three hours -- while the heartbeat was running and had ticked about
ninety times. A check that reads stale for a LIVE monitor cannot fire for
a dead one either, which is why three heartbeat deaths in one session
were each learned from the harness, never from this repository's own
detection.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "poll-heartbeat.sh"
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "gates"))

import monitor_ownership  # noqa: E402


class TheMarkerIsRefreshedEveryTickTest(unittest.TestCase):
    def _run(self, cwd, ticks, sleep_s="1"):
        env = dict(os.environ,
                   POLL_HEARTBEAT_SLEEP_SECONDS=sleep_s,
                   POLL_HEARTBEAT_MAX_TICKS=str(ticks))
        return subprocess.run(["bash", str(SCRIPT)], cwd=cwd, env=env,
                              capture_output=True, text=True, timeout=180)

    def test_the_marker_is_younger_than_the_run_that_wrote_it(self):
        cwd = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", cwd], check=True)
        d = monitor_ownership.alive_dir_for(cwd)
        self._run(cwd, ticks=3)
        marker = d / "alive"
        self.assertTrue(marker.is_file(), "no marker written at all")
        # Three ticks at one second each: a marker written only at startup
        # would be at least as old as the run, and this is the assertion
        # that failed for three days in production.
        self.assertLess(time.time() - marker.stat().st_mtime, 2.5)

    def test_the_owner_marker_is_refreshed_too(self):
        cwd = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", cwd], check=True)
        d = monitor_ownership.alive_dir_for(cwd)
        self._run(cwd, ticks=3)
        owners = list(d.glob("owner-*"))
        self.assertTrue(owners, "no owner marker written")
        self.assertLess(time.time() - owners[0].stat().st_mtime, 2.5)

    def test_the_refresh_lives_inside_the_tick_loop(self):
        # Structural: the startup write alone is what rotted. If someone
        # moves this back above `while true`, the runtime test above can
        # still pass on a fast enough run -- this one cannot.
        src = SCRIPT.read_text(encoding="utf-8")
        loop_at = src.index("while true; do")
        self.assertIn('touch "${_alive_dir}/alive"', src[loop_at:],
                      "the marker refresh must be inside the tick loop")


if __name__ == "__main__":
    unittest.main()
