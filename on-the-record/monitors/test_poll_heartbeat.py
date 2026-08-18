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
import tempfile
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


def _run_heartbeat(checkout: Path, marker: Path, env_extra: dict, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env["FAKE_SPAWN_MARKER"] = str(marker)
    env["POLL_HEARTBEAT_MAX_TICKS"] = "1"
    env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
    env.pop("CLAUDE_ROLE", None)
    # issue #1724: normalize unconditionally, mirroring
    # POLL_HEARTBEAT_SLEEP_SECONDS/POLL_HEARTBEAT_MAX_TICKS above and the
    # CLAUDE_ROLE pop -- otherwise an ambient OTR_MONITOR_OFF=1 in the
    # invoking shell (the very thing this proposal tells operators to set
    # via .claude/settings.local.json) would silently mask a regression in
    # any test that claims OTR_MONITOR_OFF is unset.
    env["OTR_MONITOR_OFF"] = env_extra.get("OTR_MONITOR_OFF", "")
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True, env=env, timeout=15,
        cwd=str(cwd) if cwd else None,
    )


def _run_tick(checkout: Path, home: Path, report: str) -> subprocess.CompletedProcess:
    """issue #1719: two-ticks-against-the-same-checkout harness, mirroring
    gates/test_poll_heartbeat_delta.py's _run_tick, for the returned-pr/
    board-sweep delta cases below."""
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


# issue #1722: a roles-configured patrol fixture. ROLES/poll-due/watchdog
# dispatch is guarded under __main__ so a plain `import spawn` for ROLES
# alone (poll-heartbeat.sh's role-list read) doesn't also run the CLI
# branches or force an exit.
FAKE_SPAWN_PY_WITH_ROLES = """#!/usr/bin/env python3
import os, sys
ROLES = ["role-a", "role-b"]
if __name__ == "__main__":
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

# issue #1722: a fake gates/patrol_promote.py whose behavior (quiet /
# promote / crash) is selected via FAKE_PATROL_BEHAVIOR, mirroring
# _run_tick's FAKE_WATCHDOG_REPORT env-var-selected-fixture pattern. Each
# invocation appends its role arg to FAKE_PATROL_MARKER (when set) so a
# test can prove patrol_promote.py actually ran per configured role.
FAKE_PATROL_PROMOTE_PY = """#!/usr/bin/env python3
import json, os, sys
role = sys.argv[-1]
marker = os.environ.get("FAKE_PATROL_MARKER")
if marker:
    with open(marker, "a", encoding="utf-8") as f:
        f.write(role + "\\n")
behavior = os.environ.get("FAKE_PATROL_BEHAVIOR", "quiet")
if behavior == "crash":
    sys.stderr.write("boom\\n")
    sys.exit(1)
if behavior == "promote":
    print(json.dumps({"promotions": [{"role": role}]}))
    sys.exit(0)
print(json.dumps({"promotions": []}))
sys.exit(0)
"""


def _run_patrol_tick(checkout: Path, home: Path, *, patrol_behavior: str | None = None,
                      patrol_marker: Path | None = None, patrol_disabled: bool = False) -> subprocess.CompletedProcess:
    """issue #1722: drives the patrol block in isolation from the due
    branch (FAKE_POLL_DUE=0) via a roles-configured fake spawn.py and a
    fake gates/patrol_promote.py whose behavior is env-var-selected."""
    (checkout / "spawn.py").write_text(FAKE_SPAWN_PY_WITH_ROLES, encoding="utf-8")
    gates_dir = checkout / "gates"
    gates_dir.mkdir(exist_ok=True)
    (gates_dir / "patrol_promote.py").write_text(FAKE_PATROL_PROMOTE_PY, encoding="utf-8")
    if patrol_disabled:
        otr = checkout / ".on-the-record"
        otr.mkdir(exist_ok=True)
        (otr / "patrol-disabled").write_text("", encoding="utf-8")
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env["FAKE_SPAWN_MARKER"] = str(checkout / "marker.log")
    env["POLL_HEARTBEAT_MAX_TICKS"] = "1"
    env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
    env["POLL_HEARTBEAT_PATROL_EVERY_N"] = "1"
    env["FAKE_POLL_DUE"] = "0"
    env["HOME"] = str(home)
    if patrol_behavior is not None:
        env["FAKE_PATROL_BEHAVIOR"] = patrol_behavior
    if patrol_marker is not None:
        env["FAKE_PATROL_MARKER"] = str(patrol_marker)
    env.pop("CLAUDE_ROLE", None)
    return subprocess.run(
        ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True, env=env, timeout=15,
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


def t_heartbeat_respects_monitor_only_kill_switch():
    """issue #1724 acceptance check 1: OTR_MONITOR_OFF=1 exits 0 before the
    first sleep, writes nothing to stdout, and touches no runs/ state
    file, mirroring t_heartbeat_respects_kill_switch (ORCHESTRATE_OFF)
    above."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_heartbeat(checkout, marker,
                            {"FAKE_POLL_DUE": "1", "HOME": str(home), "OTR_MONITOR_OFF": "1"})
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0 even when disabled: {r.stderr}"
        assert r.stdout == "", r.stdout
        assert not (marker.exists() and marker.read_text().strip()), \
            "OTR_MONITOR_OFF=1 must suppress the Monitor heartbeat loop"
        assert not (checkout / "runs").exists(), \
            "OTR_MONITOR_OFF=1 must touch no runs/ state file"


def t_heartbeat_orchestrate_off_alone_still_stops_monitor():
    """issue #1724 empty-state clause: ORCHESTRATE_OFF=1 alone, with
    OTR_MONITOR_OFF normalized to unset by _run_heartbeat, still stops the
    monitor exactly as it does today -- pins that the new switch is
    additive, not a replacement for the existing one."""
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
        assert r.stdout == "", r.stdout
        assert not (marker.exists() and marker.read_text().strip()), \
            "ORCHESTRATE_OFF=1 alone must still suppress the Monitor heartbeat loop"


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


def _alive_marker_path(home: Path, arm_root: Path) -> Path:
    """Mirrors poll-heartbeat.sh's inline python: sha256(pwd -P)[:24],
    joined under ~/.claude/tokenmaxxxer/monitor-alive/ (issue #1280
    relocation, docs/issue-1280/reports/implementation.md "What was
    done" -- marker moved from `<repo>/.orchestrate-monitor-alive/alive`
    to `~/.claude/tokenmaxxxer/monitor-alive/<sha256(pwd -P)[:24]>/alive`)."""
    import hashlib
    root = str(arm_root.resolve())
    h = hashlib.sha256(root.encode("utf-8", "surrogatepass")).hexdigest()[:24]
    return home / ".claude" / "tokenmaxxxer" / "monitor-alive" / h / "alive"


def t_heartbeat_refuses_to_arm_on_non_git_root():
    """issue #1292 (docs/issue-1292/reports/implementation.md "Summary of
    work"): the #1275 hard `exit 1` non-git refusal is demoted to the
    same sweep-exclusion/dormancy path #1245/#1280 built for the
    non-board case -- a non-git arm-root no longer refuses to arm. The
    tick loop always runs, the relocated alive marker is written
    unconditionally, and the watchdog still runs on a due tick; no
    `[monitor-arm-refused]` error and no exit-1 remain on this path."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        non_git_root = tmp / "not-a-repo"
        non_git_root.mkdir()
        r = _run_heartbeat(checkout, marker,
                            {"FAKE_POLL_DUE": "1", "HOME": str(home),
                             "FAKE_WATCHDOG_REPORT": EMPTY_ROSTER_REPORT},
                            cwd=non_git_root)
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert "[monitor-arm-refused]" not in r.stderr, r.stderr
        assert EMPTY_ROSTER_REPORT in r.stdout, r.stdout
        assert _alive_marker_path(home, non_git_root).exists(), \
            "non-git arm-root must still get the relocated alive marker"
        assert _wait_for_marker(marker), \
            "watchdog must still run on a due tick when the arm-root is not a git repo"


def t_heartbeat_skips_attachment_on_non_board_repo():
    """issue #1280 (docs/issue-1280/reports/implementation.md "What was
    done"): the #1245 non-board `exit 0` gate is demoted to an
    `is_board` flag that only scopes `spawn.py`'s `_board_wide_sweep_all`
    arm-root inclusion -- it no longer skips Monitor attachment at the
    poll-heartbeat.sh level. A non-board git repo now attaches
    identically to a board repo: relocated alive marker written, tick
    loop runs, watchdog invoked on a due tick."""
    import subprocess as _subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        target_repo = tmp / "foreign_repo"
        target_repo.mkdir()
        _subprocess.run(["git", "init", "-q"], cwd=str(target_repo), check=True)
        r = _run_heartbeat(checkout, marker,
                            {"FAKE_POLL_DUE": "1", "HOME": str(home),
                             "FAKE_WATCHDOG_REPORT": EMPTY_ROSTER_REPORT},
                            cwd=target_repo)
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert EMPTY_ROSTER_REPORT in r.stdout, r.stdout
        assert _alive_marker_path(home, target_repo).exists(), \
            "non-board target repo must still get the relocated alive marker"
        assert not (target_repo / ".orchestrate-monitor-alive").exists(), \
            "the old repo-local marker path must never be recreated"
        assert _wait_for_marker(marker), \
            "non-board target repo must still run the watchdog on a due tick"


def t_heartbeat_attaches_on_board_repo():
    """issue #1245 (docs/issue-1245/reports/implementation.md "What was
    done") + #1280's relocation: a target repo carrying
    docs/specs/approvers.md keeps due-tick attachment -- alive marker
    created (now at the relocated ~/.claude/tokenmaxxxer/monitor-alive/
    path, not the old repo-local one), watchdog invoked, captured report
    in stdout."""
    import subprocess as _subprocess
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
        _subprocess.run(["git", "init", "-q"], cwd=str(target_repo), check=True)
        r = _run_heartbeat(checkout, marker,
                            {"FAKE_POLL_DUE": "1", "HOME": str(home),
                             "FAKE_WATCHDOG_REPORT": EMPTY_ROSTER_REPORT},
                            cwd=target_repo)
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert EMPTY_ROSTER_REPORT in r.stdout, r.stdout
        assert _alive_marker_path(home, target_repo).exists(), \
            "board target repo must get the relocated alive marker"
        assert not (target_repo / ".orchestrate-monitor-alive").exists(), \
            "the old repo-local marker path must never be recreated"
        assert _wait_for_marker(marker), "watchdog was not run on a due tick for a board repo"


def t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior():
    """issue #1598 (patrol wiring E2) regression pin: adding the
    independent `patrol_tick` counter and patrol invocation must not
    change the existing `tick`/`POLL_HEARTBEAT_MAX_TICKS` bounding or the
    watchdog/rearm due-branch output. The fake spawn.py stub used by this
    suite has no `ROLES` constant, so the patrol block's role-list import
    fails and yields zero roles -- exercising the "own counter fires, but
    no roles configured" path without a live patrol_promote.py call, while
    still proving the due-branch report is unaffected and the loop still
    stops at MAX_TICKS."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        env = dict(os.environ)
        env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
        env["FAKE_SPAWN_MARKER"] = str(marker)
        env["POLL_HEARTBEAT_MAX_TICKS"] = "5"
        env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
        env["FAKE_POLL_DUE"] = "1"
        env["FAKE_WATCHDOG_REPORT"] = EMPTY_ROSTER_REPORT
        env["HOME"] = str(home)
        env.pop("CLAUDE_ROLE", None)
        r = subprocess.run(
            ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True, env=env, timeout=15,
        )
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert EMPTY_ROSTER_REPORT in r.stdout, r.stdout
        assert _wait_for_marker(marker), "watchdog was not run on a due tick"
        # issue #1722: the summary line only prints when there's a
        # promotion or a crash — a quiet tick (zero roles here) prints
        # nothing patrol-related.
        assert "[patrol-poll] checked" not in r.stdout, r.stdout


def t_returned_pr_unchanged_set_produces_no_output_on_due_tick():
    """issue #1719 Acceptance check 1: an unchanged (issue, pr) returned-pr
    set across two ticks -- same issue/phase/url, only age= advancing --
    produces no Monitor output on the second due tick."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        report_tick1 = "[returned-pr] issue #22 (phase1): age=1.0h — https://example/22"
        r1 = _run_tick(checkout, home, report_tick1)
        assert r1.returncode == 0, r1.stderr
        assert "[returned-pr] issue #22" in r1.stdout, r1.stdout

        report_tick2 = "[returned-pr] issue #22 (phase1): age=1.5h — https://example/22"
        r2 = _run_tick(checkout, home, report_tick2)
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout.strip() == "", r2.stdout


def t_returned_pr_new_item_emits_on_due_tick():
    """issue #1719 Acceptance check 1: a returned-pr set that gains a new
    (issue, pr) item between two ticks emits the new item's line on the
    due tick where it appears."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        report_tick1 = "[returned-pr] issue #22 (phase1): age=1.0h — https://example/22"
        r1 = _run_tick(checkout, home, report_tick1)
        assert r1.returncode == 0, r1.stderr
        assert "[returned-pr] issue #22" in r1.stdout, r1.stdout

        report_tick2 = (
            "[returned-pr] issue #22 (phase1): age=1.5h — https://example/22\n"
            "[returned-pr] issue #40 (phase2): age=0.1h — https://example/40"
        )
        r2 = _run_tick(checkout, home, report_tick2)
        assert r2.returncode == 0, r2.stderr
        assert "[returned-pr] issue #40" in r2.stdout, r2.stdout
        assert "[returned-pr] issue #22" not in r2.stdout, r2.stdout


def t_board_sweep_lock_skip_treated_as_no_change():
    """issue #1719 Acceptance check 2: a board-sweep lock-contention skip
    line on tick 2, following a real sweep-result line on tick 1, is not
    emitted -- and a tick 3 identical to tick 1's real result is also not
    emitted, proving the previous sweep state was kept, not flapped."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        real_result = "[watchdog] board-sweep: no-change (delta empty) — cursor kept"
        lock_skip = "[watchdog] board-sweep: repo-a 건너뜀 (다른 워크스페이스가 스윕 중) — held by pid 123"

        r1 = _run_tick(checkout, home, real_result)
        assert r1.returncode == 0, r1.stderr
        assert real_result in r1.stdout, r1.stdout

        r2 = _run_tick(checkout, home, lock_skip)
        assert r2.returncode == 0, r2.stderr
        assert "건너뜀" not in r2.stdout, r2.stdout
        assert r2.stdout.strip() == "", r2.stdout

        r3 = _run_tick(checkout, home, real_result)
        assert r3.returncode == 0, r3.stderr
        assert r3.stdout.strip() == "", r3.stdout


def _force_last_emit_epoch(checkout: Path, epoch: int) -> None:
    """issue #1732: the 1800s bound can't be crossed by real wall-clock
    waiting in a test -- rewrite runs/poll_heartbeat_last_state.json's
    last_emit_epoch directly, the same on-disk state file poll-heartbeat.sh
    itself reads/writes (mirrors _run_tick's use of that state file)."""
    import json
    state_path = checkout / "runs" / "poll_heartbeat_last_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["last_emit_epoch"] = epoch
    state_path.write_text(json.dumps(state), encoding="utf-8")


def t_heartbeat_bound_with_no_returned_pr_emits_nothing():
    """issue #1732 Acceptance check 1: an unchanged report with no
    returned-pr entries, ticked past the 1800s last_emit_epoch bound,
    writes nothing to stdout and leaves last_emit_epoch untouched (no
    'monitoring active' line)."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        report = EMPTY_ROSTER_REPORT
        r1 = _run_tick(checkout, home, report)
        assert r1.returncode == 0, r1.stderr
        assert EMPTY_ROSTER_REPORT in r1.stdout, r1.stdout

        _force_last_emit_epoch(checkout, 0)
        r2 = _run_tick(checkout, home, report)
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout == "", r2.stdout
        assert "monitoring active" not in r2.stdout, r2.stdout

        import json
        state_path = checkout / "runs" / "poll_heartbeat_last_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["last_emit_epoch"] == 0, \
            f"last_emit_epoch must stay untouched on an empty bound tick: {state}"


def t_heartbeat_bound_with_returned_pr_emits_only_those_lines():
    """issue #1732 Acceptance check 2: an unchanged report carrying a
    returned-pr entry, ticked past the 1800s last_emit_epoch bound, emits
    exactly that returned-pr line and no 'monitoring active' line."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        report = "[returned-pr] issue #22 (phase1): age=1.0h — https://example/22"
        r1 = _run_tick(checkout, home, report)
        assert r1.returncode == 0, r1.stderr
        assert "[returned-pr] issue #22" in r1.stdout, r1.stdout

        _force_last_emit_epoch(checkout, 0)
        r2 = _run_tick(checkout, home, report)
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout.strip() == "[returned-pr] issue #22 (phase1): age=1.0h — https://example/22", r2.stdout
        assert "monitoring active" not in r2.stdout, r2.stdout


def t_patrol_quiet_tick_with_roles_emits_no_summary_line():
    """issue #1722 Acceptance check 1: a patrol-due tick with roles
    configured, zero promotions, and no crash writes nothing
    patrol-related to Monitor stdout — the patrol still runs
    (patrol_promote.py invoked once per configured role, proven via the
    marker file)."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = tmp / "checkout"
        checkout.mkdir()
        home = tmp / "home"
        home.mkdir()
        patrol_marker = tmp / "patrol_marker.log"
        r = _run_patrol_tick(checkout, home, patrol_marker=patrol_marker)
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert "[patrol-poll]" not in r.stdout, r.stdout
        invoked = patrol_marker.read_text().splitlines() if patrol_marker.exists() else []
        assert invoked == ["role-a", "role-b"], \
            f"patrol_promote.py must still run once per configured role: {invoked}"


def t_patrol_promotion_tick_still_prints_summary_line():
    """issue #1722 Acceptance check 2: a patrol-due tick with a promotion
    keeps printing its existing [patrol-poll] lines unchanged."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = tmp / "checkout"
        checkout.mkdir()
        home = tmp / "home"
        home.mkdir()
        r = _run_patrol_tick(checkout, home, patrol_behavior="promote")
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert "[patrol-poll] role-a: 1 promotion(s)" in r.stdout, r.stdout
        assert "[patrol-poll] role-b: 1 promotion(s)" in r.stdout, r.stdout
        assert "[patrol-poll] checked 2 role(s), 2 promotion(s)" in r.stdout, r.stdout


def t_patrol_crashed_role_tick_still_prints_summary_line():
    """issue #1722 Acceptance check 2: a patrol-due tick with a crashed
    role keeps printing both the per-role crash line and the summary
    line unchanged."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = tmp / "checkout"
        checkout.mkdir()
        home = tmp / "home"
        home.mkdir()
        r = _run_patrol_tick(checkout, home, patrol_behavior="crash")
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert "[patrol-poll] role-a: crashed (rc=1)" in r.stdout, r.stdout
        assert "[patrol-poll] role-b: crashed (rc=1)" in r.stdout, r.stdout
        assert "[patrol-poll] checked 2 role(s), 0 promotion(s)" in r.stdout, r.stdout


def t_patrol_kill_switch_still_prints_disabled_line_only():
    """issue #1722 Acceptance check 2: the kill-switch
    (.on-the-record/patrol-disabled) keeps printing only its existing
    disabled-skip line, unchanged, with no summary line — even when
    roles are configured."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = tmp / "checkout"
        checkout.mkdir()
        home = tmp / "home"
        home.mkdir()
        patrol_marker = tmp / "patrol_marker.log"
        r = _run_patrol_tick(checkout, home, patrol_marker=patrol_marker, patrol_disabled=True)
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert "[patrol-poll] disabled, skipped" in r.stdout, r.stdout
        assert "[patrol-poll] checked" not in r.stdout, r.stdout
        assert not patrol_marker.exists(), \
            "the kill-switch must short-circuit before patrol_promote.py runs"


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
