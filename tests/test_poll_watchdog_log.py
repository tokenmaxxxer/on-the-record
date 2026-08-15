#!/usr/bin/env python3
"""issue #1466: poll-watchdog.log gets an ISO-8601 tick-header line per
appended tick and single-generation size-based rotation (`.1`), both
non-fatal to on-the-record/monitors/poll-heartbeat.sh's tick loop.
Monitor-channel stdout must stay byte-identical.

  python3 -m pytest tests/test_poll_watchdog_log.py
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POLL_HEARTBEAT = REPO_ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh"

FAKE_SPAWN_PY = """#!/usr/bin/env python3
import os, sys
if sys.argv[1:2] == ["poll-due"]:
    sys.exit(0 if os.environ.get("FAKE_POLL_DUE") == "1" else 1)
if sys.argv[1:2] == ["watchdog"]:
    report = os.environ.get("FAKE_WATCHDOG_REPORT", "")
    if report:
        print(report)
    sys.exit(0)
sys.exit(0)
"""

TICK_HEADER_RE = re.compile(r"^\[tick\] \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4}$")

REPORT = "[poll-report] roster: empty\n[poll-report] quiet, nothing in flight"


def _make_checkout(tmp: Path) -> Path:
    checkout = tmp / "checkout"
    checkout.mkdir()
    (checkout / "spawn.py").write_text(FAKE_SPAWN_PY, encoding="utf-8")
    return checkout


def _run_heartbeat(checkout: Path, home: Path, env_extra: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env["HOME"] = str(home)
    env["POLL_HEARTBEAT_MAX_TICKS"] = "1"
    env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
    env.pop("CLAUDE_ROLE", None)
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True,
        env=env, timeout=15, cwd=str(REPO_ROOT),
    )


def _log_path(home: Path) -> Path:
    return home / ".claude" / "tokenmaxxxer" / "poll-watchdog.log"


def test_tick_header_timestamp():
    # empty state: first-ever append to a missing log file creates it
    # with a header.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        log = _log_path(home)
        assert not log.exists()
        r = _run_heartbeat(checkout, home, {"FAKE_POLL_DUE": "1", "FAKE_WATCHDOG_REPORT": REPORT})
        assert r.returncode == 0, r.stderr
        assert log.exists()
        lines = log.read_text(encoding="utf-8").splitlines()
        assert lines, "log should not be empty after a due tick"
        assert TICK_HEADER_RE.match(lines[0]), f"first line is not a parseable tick header: {lines[0]!r}"
        assert REPORT in "\n".join(lines[1:])


def test_rotation_at_threshold():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        log = _log_path(home)
        log.parent.mkdir(parents=True)
        log.write_text("x" * 2000, encoding="utf-8")
        r = _run_heartbeat(checkout, home, {
            "FAKE_POLL_DUE": "1", "FAKE_WATCHDOG_REPORT": REPORT,
            "POLL_WATCHDOG_LOG_MAX_BYTES": "1000",
        })
        assert r.returncode == 0, r.stderr
        rotated = Path(str(log) + ".1")
        assert rotated.exists(), "log grown past threshold should rotate to .1"
        assert rotated.read_text(encoding="utf-8") == "x" * 2000
        live = log.read_text(encoding="utf-8")
        assert "x" * 2000 not in live, "live file should be truncated (a fresh file) after rotation"
        assert TICK_HEADER_RE.match(live.splitlines()[0])


def test_rotation_failure_nonfatal():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        log_dir = _log_path(home).parent
        log_dir.mkdir(parents=True)
        _log_path(home).write_text("x" * 2000, encoding="utf-8")
        os.chmod(log_dir, 0o555)
        try:
            r = _run_heartbeat(checkout, home, {
                "FAKE_POLL_DUE": "1", "FAKE_WATCHDOG_REPORT": REPORT,
                "POLL_WATCHDOG_LOG_MAX_BYTES": "1000",
            })
        finally:
            os.chmod(log_dir, 0o755)
        assert r.returncode == 0, f"a read-only log directory must not raise out of the append path: {r.stderr}"
        assert REPORT in r.stdout


def test_monitor_stdout_unchanged():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        r = _run_heartbeat(checkout, home, {"FAKE_POLL_DUE": "1", "FAKE_WATCHDOG_REPORT": REPORT})
        assert r.returncode == 0, r.stderr
        assert r.stdout == REPORT + "\n", (
            "Monitor stdout must stay byte-identical with the log-side change: "
            f"{r.stdout!r}"
        )
