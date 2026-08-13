#!/usr/bin/env python3
"""issue #835 phase 2 / issue #922 phase 2: monitors/poll-heartbeat.sh —
the plugin-Monitor default-on ~60s poll heartbeat
(docs/issue-835/proposals/technical-feasibility.md, candidate 1;
docs/issue-922/proposals/poll-heartbeat-capture-hop.md for the due
branch's foreground capture-hop). Exercises the SAME
`python3 spawn.py poll-due` atomic TTL gate that
on-the-record/hooks/directive.sh (UserPromptSubmit) and
on-the-record/hooks/stop-poll-rearm.sh (Stop) already call via
poll_rearm_arm_if_due(), using a fake spawn.py so no real
watchdog/roster machinery runs. The loop is bounded via
POLL_HEARTBEAT_MAX_TICKS and sped up via POLL_HEARTBEAT_SLEEP_SECONDS so
the test does not wait on a real 60s cadence.

  python3 on-the-record/monitors/test_poll_heartbeat.py
"""
from __future__ import annotations
import os
import subprocess
import sys
import time
from pathlib import Path

MONITORS_DIR = Path(__file__).resolve().parent
POLL_HEARTBEAT = MONITORS_DIR / "poll-heartbeat.sh"

FAKE_SPAWN_PY = """#!/usr/bin/env python3
import os, sys
marker = os.environ["FAKE_SPAWN_MARKER"]
if sys.argv[1:2] == ["poll-due"]:
    sys.exit(0 if os.environ.get("FAKE_POLL_DUE") == "1" else 1)
if sys.argv[1:2] == ["watchdog"]:
    with open(marker, "a", encoding="utf-8") as f:
        f.write("watchdog-ran\\n")
    report = os.environ.get("FAKE_WATCHDOG_REPORT", "")
    if report:
        print(report)
    sys.exit(0)
sys.exit(0)
"""

# issue #922: mirrors roster_watchdog()'s empty-state pair verbatim
# (docs/issue-922/reports/product-discovery/survey.md).
EMPTY_ROSTER_REPORT = "[poll-report] roster: empty\n[poll-report] quiet, nothing in flight"

# issue #922: mirrors roster_watchdog()'s STALLED/watcher-dead surfacing
# plus a [resume] auto-respawn confirmation line for a crashed entry.
DEAD_POLLER_REPORT = (
    "[poll-report] roster: 1 entry\n"
    "issue-999/implementation: STALLED (watcher-dead)\n"
    "[resume] issue-999/implementation: respawned watcher"
)


def _wait_for_marker(marker: Path, timeout_s: float = 5.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if marker.exists() and marker.read_text().strip():
            return True
        time.sleep(0.1)
    return False


def _make_checkout(tmp: Path) -> Path:
    checkout = tmp / "checkout"
    checkout.mkdir()
    (checkout / "spawn.py").write_text(FAKE_SPAWN_PY, encoding="utf-8")
    return checkout


def _run_heartbeat(checkout: Path, marker: Path, env_extra: dict, cwd: Path = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env["FAKE_SPAWN_MARKER"] = str(marker)
    env["POLL_HEARTBEAT_MAX_TICKS"] = "1"
    env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
    env.pop("CLAUDE_ROLE", None)
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True, env=env, timeout=15,
        cwd=str(cwd) if cwd is not None else None,
    )


def t_heartbeat_arms_watchdog_when_due(tmp_path_factory=None):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_heartbeat(checkout, marker,
                            {"FAKE_POLL_DUE": "1", "HOME": str(home),
                             "FAKE_WATCHDOG_REPORT": EMPTY_ROSTER_REPORT})
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert EMPTY_ROSTER_REPORT in r.stdout, r.stdout
        assert _wait_for_marker(marker), "watchdog was not run on a due tick"


def t_heartbeat_skips_watchdog_when_not_due():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_heartbeat(checkout, marker, {"FAKE_POLL_DUE": "0", "HOME": str(home)})
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        # issue #1220: delta-only emission — a non-due tick is now fully
        # silent (no "skipped (within TTL)" line) instead of a constant
        # per-minute echo.
        assert r.stdout.strip() == "", r.stdout
        assert not (marker.exists() and marker.read_text().strip()), \
            "watchdog must not spawn when poll-due reports not-due"


def t_heartbeat_respects_kill_switch():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_heartbeat(checkout, marker,
                            {"FAKE_POLL_DUE": "1", "HOME": str(home), "ORCHESTRATE_OFF": "1"})
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0 even when disabled: {r.stderr}"
        assert not (marker.exists() and marker.read_text().strip()), \
            "ORCHESTRATE_OFF=1 must suppress the Monitor heartbeat loop too"


def t_heartbeat_surfaces_empty_roster_report():
    """issue #922 acceptance case 1: empty roster, clean board-wide sweep
    -> captured stdout carries the two existing empty-state lines
    verbatim, not the old bare "poll tick: due, watchdog armed" line."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_heartbeat(checkout, marker,
                            {"FAKE_POLL_DUE": "1", "HOME": str(home),
                             "FAKE_WATCHDOG_REPORT": EMPTY_ROSTER_REPORT})
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert EMPTY_ROSTER_REPORT in r.stdout, r.stdout
        assert "poll tick: due, watchdog armed" not in r.stdout, r.stdout
        log = (home / ".claude" / "tokenmaxxxer" / "poll-watchdog.log").read_text()
        assert EMPTY_ROSTER_REPORT in log, log


def t_heartbeat_surfaces_induced_dead_poller():
    """issue #922 acceptance case 2: induced dead-poller/stalled-watch
    fixture -> captured stdout carries the STALLED/watcher-dead/
    [poll-report] line and the [resume] auto-respawn confirmation."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_heartbeat(checkout, marker,
                            {"FAKE_POLL_DUE": "1", "HOME": str(home),
                             "FAKE_WATCHDOG_REPORT": DEAD_POLLER_REPORT})
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert "STALLED (watcher-dead)" in r.stdout, r.stdout
        assert "[poll-report]" in r.stdout, r.stdout
        assert "[resume]" in r.stdout, r.stdout


def t_heartbeat_skips_attachment_on_non_board_repo():
    """issue #1245: a target repo with no docs/specs/approvers.md must
    never get the Monitor attached at all -- no alive marker, no state
    file, no watchdog log, even on a due tick."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        target_repo = tmp / "foreign_repo"
        target_repo.mkdir()
        r = _run_heartbeat(checkout, marker,
                            {"FAKE_POLL_DUE": "1", "HOME": str(home),
                             "FAKE_WATCHDOG_REPORT": EMPTY_ROSTER_REPORT},
                            cwd=target_repo)
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert not (target_repo / ".orchestrate-monitor-alive").exists(), \
            "non-board target repo must not get an alive marker"
        assert not (checkout / "runs" / "poll_heartbeat_last_state.json").exists(), \
            "non-board target repo must not get a poll_heartbeat_last_state.json"
        assert not (home / ".claude" / "tokenmaxxxer" / "poll-watchdog.log").exists(), \
            "non-board target repo must not get a poll-watchdog.log"
        assert not (marker.exists() and marker.read_text().strip()), \
            "non-board target repo must not run the watchdog"


def t_heartbeat_attaches_on_board_repo():
    """issue #1245 counterpart: a target repo carrying
    docs/specs/approvers.md keeps today's due-tick behavior byte-for-byte
    -- alive marker created, watchdog invoked, captured report in stdout."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        target_repo = tmp / "board_repo"
        (target_repo / "docs" / "specs").mkdir(parents=True)
        (target_repo / "docs" / "specs" / "approvers.md").write_text("- someone\n", encoding="utf-8")
        r = _run_heartbeat(checkout, marker,
                            {"FAKE_POLL_DUE": "1", "HOME": str(home),
                             "FAKE_WATCHDOG_REPORT": EMPTY_ROSTER_REPORT},
                            cwd=target_repo)
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert EMPTY_ROSTER_REPORT in r.stdout, r.stdout
        assert (target_repo / ".orchestrate-monitor-alive" / "alive").exists(), \
            "board target repo must get an alive marker"
        assert _wait_for_marker(marker), "watchdog was not run on a due tick for a board repo"


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
