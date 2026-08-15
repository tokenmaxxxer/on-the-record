#!/usr/bin/env python3
"""issue #1510: poll-heartbeat cadence and its derived staleness tolerance
are one decision, not two — this test parses both defaults straight from
the shipped shell files so a future cadence edit that forgets to scale the
tolerance fails loudly instead of silently false-alarming "monitor dead"."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLL_HEARTBEAT_SH = ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh"
DIRECTIVE_SH = ROOT / "on-the-record" / "hooks" / "directive.sh"


def _parse_default(path: Path, var_name: str) -> int:
    text = path.read_text()
    m = re.search(rf'\${{{re.escape(var_name)}:-(\d+)}}', text)
    if not m:
        raise AssertionError(f"{var_name} default not found in {path}")
    return int(m.group(1))


class TestHeartbeatCadenceDefaults(unittest.TestCase):
    def test_defaults_scaled_together(self):
        heartbeat_default = _parse_default(POLL_HEARTBEAT_SH, "POLL_HEARTBEAT_SLEEP_SECONDS")
        stale_default = _parse_default(DIRECTIVE_SH, "MONITOR_LIVENESS_STALE_SECONDS")
        self.assertEqual(heartbeat_default, 120)
        self.assertGreaterEqual(stale_default, 3 * heartbeat_default)


if __name__ == "__main__":
    unittest.main()
