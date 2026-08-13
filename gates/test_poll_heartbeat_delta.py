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
    """Empty state: first-ever tick (no stored state file) must emit the
    full initial state once (issue #1220 Acceptance)."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        assert not (checkout / "runs" / "poll_heartbeat_last_state.json").exists()

        r1 = _run_tick(checkout, home, REPORT_A)
        assert r1.returncode == 0, r1.stderr
        assert REPORT_A in r1.stdout, r1.stdout
        assert (checkout / "runs" / "poll_heartbeat_last_state.json").exists()


def t_only_changed_line_emitted_not_full_report():
    """issue #1220 proposal item (a): two due ticks where only one
    session's line changed emit ONLY that session's changed line, not
    the full report text of the unchanged sessions."""
    report_1 = "[poll-report] roster: 2 entries\nissue-1/implementation: healthy\nissue-2/implementation: healthy"
    report_2 = "[poll-report] roster: 2 entries\nissue-1/implementation: healthy\nissue-2/implementation: STALLED (watcher-dead)"
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        r1 = _run_tick(checkout, home, report_1)
        assert report_1 in r1.stdout, r1.stdout

        r2 = _run_tick(checkout, home, report_2)
        assert r2.returncode == 0, r2.stderr
        assert "issue-2/implementation: STALLED (watcher-dead)" in r2.stdout, r2.stdout
        assert "issue-1/implementation: healthy" not in r2.stdout, r2.stdout
        assert "[poll-report] roster: 2 entries" not in r2.stdout, r2.stdout


def t_dead_session_line_always_emits_even_unchanged():
    """issue #1220 proposal item (b) / issue req #2 regression guard: a
    dead/STALLED-labeled line must emit every tick even when byte-identical
    to the previous tick."""
    report = "[poll-report] roster: 1 entry\nissue-999/implementation: STALLED (watcher-dead)"
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        r1 = _run_tick(checkout, home, report)
        assert "STALLED (watcher-dead)" in r1.stdout, r1.stdout

        r2 = _run_tick(checkout, home, report)
        assert r2.returncode == 0, r2.stderr
        assert "STALLED (watcher-dead)" in r2.stdout, r2.stdout

        r3 = _run_tick(checkout, home, report)
        assert "STALLED (watcher-dead)" in r3.stdout, r3.stdout


def t_non_due_tick_produces_no_output():
    """issue #1220 proposal item (c): a non-due (within-TTL) tick must
    produce empty stdout — no "skipped (within TTL)" line."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        env = dict(os.environ)
        env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
        env["FAKE_SPAWN_MARKER"] = str(checkout / "marker.log")
        env["POLL_HEARTBEAT_MAX_TICKS"] = "1"
        env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
        env["FAKE_POLL_DUE"] = "0"
        env["HOME"] = str(home)
        env.pop("CLAUDE_ROLE", None)
        r = subprocess.run(
            ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True, env=env, timeout=15,
        )
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == "", r.stdout


def t_watchdog_anomaly_bullets_survive_round_trip():
    """issue #1220 warrant-hunt regression guard: a `[watchdog] {key}: N건`
    header followed by multiple `  - {a}` anomaly bullet lines must
    round-trip through the diff intact across two identical ticks — all
    bullets present on tick 1, none dropped, and none re-emitted (since
    unchanged) on tick 2."""
    report = (
        "[watchdog] issue-100/role-a: anomaly 2\n"
        "  - anomaly one: disk full\n"
        "  - anomaly two: stale lock\n"
        "[watchdog] issue-200/role-b: ok"
    )
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        r1 = _run_tick(checkout, home, report)
        assert r1.returncode == 0, r1.stderr
        assert "anomaly one: disk full" in r1.stdout, r1.stdout
        assert "anomaly two: stale lock" in r1.stdout, r1.stdout

        r2 = _run_tick(checkout, home, report)
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout.strip() == "", r2.stdout


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
