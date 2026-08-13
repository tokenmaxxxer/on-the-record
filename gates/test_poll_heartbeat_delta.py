#!/usr/bin/env python3
"""issue #1117: delta-suppression coverage for
on-the-record/monitors/poll-heartbeat.sh — a due tick whose captured
watchdog report text is byte-identical to the previous EMITTED tick must
not printf/echo it again (Monitor-surfaced stdout only; the
poll-watchdog.log append is untouched). Hash is persisted in a plain
sibling file next to the poll TTL stamp (runs/poll_heartbeat_last_hash),
per docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md.

Reuses the fake-spawn.py / POLL_HEARTBEAT_MAX_TICKS /
POLL_HEARTBEAT_SLEEP_SECONDS harness pattern from
on-the-record/monitors/test_poll_heartbeat.py, run once per tick (this
suite invokes the script multiple times against the SAME checkout to
carry hash state across "ticks", since POLL_HEARTBEAT_MAX_TICKS=1 keeps
each invocation to one tick).

  python3 gates/test_poll_heartbeat_delta.py
"""
from __future__ import annotations
import os
import subprocess
import sys
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

REPORT_A = "[poll-report] roster: empty\n[poll-report] quiet, nothing in flight"
REPORT_B = "[poll-report] roster: 1 entry\nissue-999/implementation: STALLED (watcher-dead)"


def _make_checkout(tmp: Path) -> Path:
    checkout = tmp / "checkout"
    checkout.mkdir()
    (checkout / "spawn.py").write_text(FAKE_SPAWN_PY, encoding="utf-8")
    return checkout


def _run_tick(checkout: Path, home: Path, report: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env["FAKE_SPAWN_MARKER"] = str(checkout / "marker.log")
    env["POLL_HEARTBEAT_MAX_TICKS"] = "1"
    env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
    env["FAKE_POLL_DUE"] = "1"
    env["FAKE_WATCHDOG_REPORT"] = report
    env["HOME"] = str(home)
    env.pop("CLAUDE_ROLE", None)
    return subprocess.run(
        ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True, env=env, timeout=15,
    )


def t_identical_second_tick_suppressed():
    """Acceptance (a): two consecutive identical due ticks -> second
    tick's stdout carries no report text."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        r1 = _run_tick(checkout, home, REPORT_A)
        assert r1.returncode == 0, r1.stderr
        assert REPORT_A in r1.stdout, r1.stdout

        r2 = _run_tick(checkout, home, REPORT_A)
        assert r2.returncode == 0, r2.stderr
        assert REPORT_A not in r2.stdout, r2.stdout
        assert r2.stdout.strip() == "", r2.stdout


def t_changed_tick_emits():
    """Acceptance (b): a due tick with different report text from any
    prior state -> emits."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        r1 = _run_tick(checkout, home, REPORT_A)
        assert r1.returncode == 0, r1.stderr
        assert REPORT_A in r1.stdout, r1.stdout

        r2 = _run_tick(checkout, home, REPORT_B)
        assert r2.returncode == 0, r2.stderr
        assert REPORT_B in r2.stdout, r2.stdout


def t_change_after_suppression_emits():
    """Acceptance (c): identical tick (suppressed) followed by a changed
    tick -> the changed one still emits."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        r1 = _run_tick(checkout, home, REPORT_A)
        assert REPORT_A in r1.stdout, r1.stdout

        r2 = _run_tick(checkout, home, REPORT_A)
        assert REPORT_A not in r2.stdout, r2.stdout

        r3 = _run_tick(checkout, home, REPORT_B)
        assert r3.returncode == 0, r3.stderr
        assert REPORT_B in r3.stdout, r3.stdout


def t_fresh_state_first_tick_always_emits():
    """Empty state: first-ever tick (no stored hash) must emit."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        assert not (checkout / "runs" / "poll_heartbeat_last_hash").exists()

        r1 = _run_tick(checkout, home, REPORT_A)
        assert r1.returncode == 0, r1.stderr
        assert REPORT_A in r1.stdout, r1.stdout
        assert (checkout / "runs" / "poll_heartbeat_last_hash").exists()


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("t_")]


def main() -> int:
    failures = []
    for fn in TESTS:
        try:
            fn()
            print(f"ok  {fn.__name__}")
        except AssertionError as e:
            failures.append(fn.__name__)
            print(f"FAIL {fn.__name__}: {e}")
    if failures:
        print(f"\n{len(failures)}/{len(TESTS)} failed: {failures}")
        return 1
    print(f"\n{len(TESTS)}/{len(TESTS)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
