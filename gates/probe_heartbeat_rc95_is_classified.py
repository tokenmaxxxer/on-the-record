#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3120, layer 1.

Exists so the classification requirement can be stated as a plain
`check:` line (`python3 gates/probe_heartbeat_rc95_is_classified.py`)
instead of a shell one-liner, mirroring gates/probe_drift_repo_leak.py's
convention.

`on-the-record/monitors/poll-heartbeat.sh` runs `spawn.py watchdog
--auto-respawn` on every due tick. `spawn.py` returns
`WATCHDOG_STALE_CODE_SENTINEL = 95` (spawn.py:677) when
`watchdog_freshness_check` (watchdog.py:1867) finds the checkout HEAD has
moved since this invocation started -- a `git pull`, a `claude plugin
marketplace update`, or an ordinary merge landing while the tick runs.
Before this issue's fix, poll-heartbeat.sh's own crash classification
(`rc >= 128 || rc == 97`) does not match 95, so the tick's stdout carries
no line distinguishing "stale code, restart required" from either the
`[watchdog-crash]` label (a genuine crash) or plain silence (nothing
happened) -- the exact "unattributable" gap issue #3120 reports.

This probe drives the real `on-the-record/monitors/poll-heartbeat.sh`
(unmodified, no monkeypatching of the script itself) through a single due
tick with a fake `spawn.py` whose `watchdog` role deterministically exits
95, and checks the tick's captured stdout for a label that is:
  - present at all (not silence), and
  - distinct from `[watchdog-crash]` (not misreported as a crash), and
  - distinct from a fabricated `[watchdog-timeout]`/`[watchdog-oops]`-style
    placeholder no real code would ever emit (guards against a probe that
    only checks "some bracket tag exists").

Run as `python3 gates/probe_heartbeat_rc95_is_classified.py` from the repo
root, no arguments, no network. Prints `ok` and exits 0 on success; prints
a message to stderr and exits non-zero otherwise.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLL_HEARTBEAT = ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh"

FAKE_SPAWN_PY = """#!/usr/bin/env python3
import os, sys
if sys.argv[1:2] == ["poll-due"]:
    sys.exit(0)
if sys.argv[1:2] == ["watchdog"]:
    marker = os.environ["FAKE_SPAWN_MARKER"]
    with open(marker, "a", encoding="utf-8") as f:
        f.write("watchdog-ran\\n")
    # mirrors watchdog_freshness_check's real stdout shape (watchdog.py:1895)
    print("[watchdog] \\ucf54\\ub4dc-\\uc2e0\\uc120\\ub3c4: \\uccb4\\ud06c\\uc544\\uc6c3 HEAD \\uac00 \\ubc14\\ub018\\ub2e4 "
          "(\\uc2dc\\uc791=aaaaaaaaaaaa \\ud604\\uc7ac=bbbbbbbbbbbb) \\u2014 \\uc7ac\\uae30\\ub3d9 \\ud544\\uc694")
    sys.exit(95)
sys.exit(0)
"""


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = tmp / "checkout"
        checkout.mkdir()
        (checkout / "spawn.py").write_text(FAKE_SPAWN_PY, encoding="utf-8")
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()

        env = dict(os.environ)
        env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
        env["FAKE_SPAWN_MARKER"] = str(marker)
        env["POLL_HEARTBEAT_MAX_TICKS"] = "1"
        env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
        env["FAKE_POLL_DUE"] = "1"
        env["HOME"] = str(home)
        env["ORCHESTRATE_OFF"] = ""
        env["OTR_MONITOR_OFF"] = ""
        env.pop("CLAUDE_SKILL", None)

        r = subprocess.run(
            ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True,
            text=True, env=env, timeout=15, cwd=str(tmp),
        )

        if r.returncode != 0:
            _fail(f"poll-heartbeat.sh exited {r.returncode} on a due tick "
                  f"with a stale-code watchdog rc; expected a clean tick "
                  f"(rc=95 is neither a crash nor a reason to fail the "
                  f"loop itself). stdout={r.stdout!r} stderr={r.stderr!r}")

        if not marker.exists() or "watchdog-ran" not in marker.read_text():
            _fail("watchdog was never invoked on the due tick -- probe "
                  "setup bug, not the defect under test.")

        stdout = r.stdout
        if "재기동 필요" not in stdout:
            _fail("the fake watchdog's own stale-code message did not "
                  f"reach stdout at all: {stdout!r}")

        if "[watchdog-crash]" in stdout:
            _fail(f"rc=95 (stale code) was misclassified as a crash: {stdout!r}")

        if "[watchdog-stale-code]" not in stdout:
            _fail(
                "rc=95 (WATCHDOG_STALE_CODE_SENTINEL) produced no distinct "
                "'[watchdog-stale-code]'-style label in the tick's stdout -- "
                "it is unattributable: tellable apart from neither a crash "
                f"nor silence. Full stdout: {stdout!r}"
            )

        if "rc=95" not in stdout:
            _fail(f"the classification line does not name the actual rc "
                  f"(95), so an operator cannot tell which sentinel fired: "
                  f"{stdout!r}")

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
