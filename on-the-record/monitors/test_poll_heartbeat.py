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
import re
import shutil
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
    env.pop("CLAUDE_SKILL", None)
    # issue #1724: normalize unconditionally, mirroring
    # POLL_HEARTBEAT_SLEEP_SECONDS/POLL_HEARTBEAT_MAX_TICKS above and the
    # CLAUDE_SKILL pop -- otherwise an ambient OTR_MONITOR_OFF=1 in the
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
    env.pop("CLAUDE_SKILL", None)
    return subprocess.run(
        ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True, env=env, timeout=15,
    )


# issue #1722: a roles-configured patrol fixture. role_data()/poll-due/
# watchdog dispatch is guarded under __main__ so a plain `import spawn` for
# role_data() alone (poll-heartbeat.sh's role-list read, issue #2560:
# reads `spawn.role_data()` since `spawn.ROLES` was retired) doesn't also
# run the CLI branches or force an exit.
FAKE_SPAWN_PY_WITH_SKILLS = """#!/usr/bin/env python3
import os, sys
def role_data():
    return {"role-a": {}, "role-b": {}}
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
    (checkout / "spawn.py").write_text(FAKE_SPAWN_PY_WITH_SKILLS, encoding="utf-8")
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
    env.pop("CLAUDE_SKILL", None)
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
    suite has no `role_data()` function (issue #2560: poll-heartbeat.sh
    reads `spawn.role_data()`, `spawn.ROLES` having been retired), so the
    patrol block's role-list import fails and yields zero roles --
    exercising the "own counter fires, but no roles configured" path
    without a live patrol_promote.py call, while still proving the
    due-branch report is unaffected and the loop still stops at
    MAX_TICKS."""
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
        env.pop("CLAUDE_SKILL", None)
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


def t_unkeyed_line_insertion_suppresses_unchanged_lines_below():
    """issue #1734 Acceptance check 1: inserting one new unkeyed line at the
    top of the unkeyed-line block must not re-emit the unchanged lines
    below it -- content-derived keys travel with each line, not its
    position, so only the genuinely new line appears on tick 2."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        line_a = "[spawn-on-pr] issue-1701: subject PR merged, closing"
        line_b = "watch: nothing pending, board quiet"
        report_tick1 = f"{line_a}\n{line_b}"
        r1 = _run_tick(checkout, home, report_tick1)
        assert r1.returncode == 0, r1.stderr
        assert line_a in r1.stdout, r1.stdout
        assert line_b in r1.stdout, r1.stdout

        line_new = "[spawn-on-pr] issue-1705: a different subject PR just merged"
        report_tick2 = f"{line_new}\n{line_a}\n{line_b}"
        r2 = _run_tick(checkout, home, report_tick2)
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout.strip() == line_new, r2.stdout


def _healthy_report(idx: int, workspace: str = "손댄 파일 없음") -> str:
    """issue #2906: mirrors watchdog.py's real `[poll-report] <key>:
    HEALTHY — <key>: 최근 로그 성장, RUNNING — <workspace>; <activity>`
    shape (diagnose_health(), workspace/activity_summary joined with
    "; "). `<activity>` embeds the entry's last-tool-activity timestamp
    (`_last_tool_activity_summary()`) -- the part that legitimately
    changes on every tick an entry is actively worked, even though
    nothing anomalous is happening. `<workspace>` (dirty-file summary)
    is left constant by default so tests isolate the activity-only
    drift; callers that want to pin the opposite (a real workspace
    change) pass a different `workspace` value."""
    return (
        f"[poll-report] issue-500/implementation: HEALTHY — "
        f"issue-500/implementation: 최근 로그 성장, RUNNING — "
        f"{workspace}; 마지막 도구 호출: Read file{idx}.py (10:{idx:02d}:00 UTC)\n"
        f"[watchdog] issue-500/implementation: 정상\n"
        f"이상 신호 없음"
    )


def t_healthy_poll_report_with_drifting_detail_suppresses_after_first_tick():
    """issue #2906: a live roster entry that stays HEALTHY across ticks
    must stop reaching the Monitor channel after its first sighting, even
    though `[poll-report]`'s detail (last-tool-activity, dirty-file list)
    keeps changing tick to tick as the session keeps working -- the
    plain full-line compare this pins against (pre-#2906) never saw two
    identical HEALTHY lines and woke the orchestrator on every due tick
    for the lifetime of every actively-worked session."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()

        r1 = _run_tick(checkout, home, _healthy_report(0))
        assert r1.returncode == 0, r1.stderr
        assert "[poll-report] issue-500/implementation: HEALTHY" in r1.stdout, r1.stdout

        for i in range(1, 6):
            r = _run_tick(checkout, home, _healthy_report(i))
            assert r.returncode == 0, r.stderr
            assert r.stdout.strip() == "", (
                f"tick {i}: HEALTHY entry with only its detail changed "
                f"must not re-notify: {r.stdout!r}"
            )


def t_healthy_to_stalled_transition_still_notifies():
    """issue #2906 must-not: suppressing repeat HEALTHY confirmations must
    never suppress a real anomaly. A HEALTHY entry that goes STALLED is a
    state change, not a detail drift -- it must reach the Monitor channel
    exactly like before this issue."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()

        r1 = _run_tick(checkout, home, _healthy_report(0))
        assert r1.returncode == 0, r1.stderr

        r2 = _run_tick(checkout, home, _healthy_report(1))
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout.strip() == "", r2.stdout

        stalled_report = (
            "[poll-report] issue-500/implementation: STALLED — "
            "issue-500/implementation: idle > 20분, RUNNING"
        )
        r3 = _run_tick(checkout, home, stalled_report)
        assert r3.returncode == 0, r3.stderr
        assert "STALLED" in r3.stdout, r3.stdout

        # recovering back to HEALTHY is itself worth one notification —
        # only the *repeat* confirmations that follow stay suppressed.
        r4 = _run_tick(checkout, home, _healthy_report(2))
        assert r4.returncode == 0, r4.stderr
        assert "HEALTHY" in r4.stdout, r4.stdout

        r5 = _run_tick(checkout, home, _healthy_report(3))
        assert r5.returncode == 0, r5.stderr
        assert r5.stdout.strip() == "", r5.stdout


def t_healthy_workspace_change_still_notifies_despite_activity_drift():
    """issue #2906 must-not, guards against over-broad suppression: a
    HEALTHY entry whose workspace summary actually changes (a new file
    touched, a record started) must still notify even though the
    activity-drift suppression above is active -- this is the exact
    shape test/test_workspace_progress_tracking.py's
    test_new_file_touched_reemits_the_changed_line pins at the watchdog
    layer; this test pins the same distinction at the delta-diff layer
    this issue's fix touches."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()

        r1 = _run_tick(checkout, home, _healthy_report(0, workspace="손댄 파일 없음"))
        assert r1.returncode == 0, r1.stderr

        # activity-only drift (same workspace) stays suppressed
        r2 = _run_tick(checkout, home, _healthy_report(1, workspace="손댄 파일 없음"))
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout.strip() == "", r2.stdout

        # a newly-dirtied file is a real workspace change -- must notify
        r3 = _run_tick(
            checkout, home,
            _healthy_report(2, workspace="손댄 파일 1건: spawn.py, 기록 아직 없음"),
        )
        assert r3.returncode == 0, r3.stderr
        assert "spawn.py" in r3.stdout, r3.stdout


def t_unkeyed_line_content_change_still_emits():
    """issue #1734 Acceptance check 2: an unkeyed line whose own content
    changes between ticks is still emitted -- content-derived keying must
    not over-suppress a genuine change."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        report_tick1 = "[spawn-on-pr] issue-1701: subject PR merged, closing"
        r1 = _run_tick(checkout, home, report_tick1)
        assert r1.returncode == 0, r1.stderr
        assert report_tick1 in r1.stdout, r1.stdout

        report_tick2 = "[spawn-on-pr] issue-1701: subject PR merged, closing — retry succeeded"
        r2 = _run_tick(checkout, home, report_tick2)
        assert r2.returncode == 0, r2.stderr
        assert report_tick2 in r2.stdout, r2.stdout


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
    """issue #1732 Acceptance check 2, updated by issue #2180: an
    unchanged report carrying a returned-pr entry, ticked past the 1800s
    last_emit_epoch bound, no longer re-prints the full [returned-pr]
    line verbatim (that repeat-forever shape is exactly what #2180
    reports as noise) -- it now emits a single collapsed
    [returned-pr-pending] count+label line, and still no 'monitoring
    active' line."""
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
        assert r2.stdout.strip() == "[returned-pr-pending] 1 PR(s) still awaiting review: #22", r2.stdout
        assert "monitoring active" not in r2.stdout, r2.stdout


def t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line():
    """issue #2180 acceptance check 1: a newly-returned PR produces a
    distinct, unmistakable [new-returned-pr] signal on the tick it first
    appears -- a different bracket tag from the routine [returned-pr]
    line (and from any other heartbeat body line), placed ahead of the
    rest of that tick's output so it doesn't blend into routine noise.
    The original [returned-pr] line is still present too, unchanged, for
    any existing consumer of that exact tag."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        report = (
            "[watchdog] some-repo: board-sweep: no-change\n"
            "[returned-pr] issue #40 (phase2): age=0.1h — https://example/40"
        )
        r = _run_tick(checkout, home, report)
        assert r.returncode == 0, r.stderr
        lines = r.stdout.splitlines()
        assert lines, r.stdout
        assert lines[0] == "[new-returned-pr] issue #40 (phase2): age=0.1h — https://example/40", r.stdout
        assert "[returned-pr] issue #40 (phase2): age=0.1h — https://example/40" in r.stdout, r.stdout


def t_returned_pr_new_marker_does_not_repeat_on_later_tick():
    """issue #2180 acceptance check 2 (regression, two-tick sequence): an
    already-surfaced PR does not re-emit the same full [returned-pr] line
    -- nor its one-shot [new-returned-pr] marker -- on a later tick where
    nothing but its age= token changed."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        report_tick1 = "[returned-pr] issue #22 (phase1): age=1.0h — https://example/22"
        r1 = _run_tick(checkout, home, report_tick1)
        assert r1.returncode == 0, r1.stderr
        assert "[new-returned-pr] issue #22" in r1.stdout, r1.stdout
        assert "[returned-pr] issue #22" in r1.stdout, r1.stdout

        report_tick2 = "[returned-pr] issue #22 (phase1): age=1.5h — https://example/22"
        r2 = _run_tick(checkout, home, report_tick2)
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout.strip() == "", r2.stdout


def t_returned_pr_phase_transition_does_not_refire_new_marker():
    """issue #2180 warrant-hunt regression: the diff key
    (`returned-pr:issue #N (phaseX)`) bakes in the phase label, so a
    phase1->phase2 transition on the SAME still-open PR used to be
    treated as a brand-new sighting and re-fire [new-returned-pr]. The
    plain [returned-pr] line still legitimately re-emits (the phase text
    really did change), but the one-shot marker must not repeat for a
    PR whose issue number was already surfaced."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        report_phase1 = "[returned-pr] issue #999 (phase1): age=1.0h — https://example/999"
        r1 = _run_tick(checkout, home, report_phase1)
        assert r1.returncode == 0, r1.stderr
        assert "[new-returned-pr] issue #999" in r1.stdout, r1.stdout

        report_phase2 = "[returned-pr] issue #999 (phase2): age=1.2h — https://example/999"
        r2 = _run_tick(checkout, home, report_phase2)
        assert r2.returncode == 0, r2.stderr
        assert "[returned-pr] issue #999 (phase2)" in r2.stdout, r2.stdout
        assert "[new-returned-pr]" not in r2.stdout, r2.stdout


def t_returned_pr_first_ever_tick_treats_every_open_pr_as_new():
    """issue #2180 empty-state clause: a first-ever tick with no prior
    surfaced-marker file (no runs/poll_heartbeat_last_state.json yet)
    treats every currently-open returned-pr entry as new -- each gets its
    own [new-returned-pr] marker exactly once, then is suppressed on the
    very next tick even though nothing changed."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        assert not (checkout / "runs" / "poll_heartbeat_last_state.json").exists()

        report = (
            "[returned-pr] issue #22 (phase1): age=1.0h — https://example/22\n"
            "[returned-pr] issue #40 (phase2): age=0.1h — https://example/40"
        )
        r1 = _run_tick(checkout, home, report)
        assert r1.returncode == 0, r1.stderr
        assert "[new-returned-pr] issue #22" in r1.stdout, r1.stdout
        assert "[new-returned-pr] issue #40" in r1.stdout, r1.stdout

        r2 = _run_tick(checkout, home, report)
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout.strip() == "", r2.stdout


def t_patrol_quiet_tick_with_skills_emits_no_summary_line():
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


def t_patrol_crashed_skill_tick_still_prints_summary_line():
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


def t_patrol_tick_skips_when_checkout_vanishes_mid_sleep():
    """issue #2163 regression: CHECKOUT is resolved once at Monitor
    startup; this test runs the script as a background subprocess and
    deletes the checkout dir while it sleeps between ticks, simulating a
    marketplace reclone's stale-dir cleanup mid-session. Before the fix,
    a tick landing in that window spawned one gates/patrol_promote.py
    subprocess per configured role, each dying rc=2 ("can't open file",
    errno 2) --
    a crash-line burst sized to the role count. After the fix, the tick
    detects the missing checkout up front and prints exactly one skip
    line, spawning no per-role subprocess at all (proven via the marker
    file staying absent, mirroring the kill-switch test above)."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = tmp / "checkout"
        checkout.mkdir()
        (checkout / "spawn.py").write_text(FAKE_SPAWN_PY_WITH_SKILLS, encoding="utf-8")
        gates_dir = checkout / "gates"
        gates_dir.mkdir()
        (gates_dir / "patrol_promote.py").write_text(FAKE_PATROL_PROMOTE_PY, encoding="utf-8")
        home = tmp / "home"
        home.mkdir()
        patrol_marker = tmp / "patrol_marker.log"
        env = dict(os.environ)
        env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
        env["FAKE_SPAWN_MARKER"] = str(checkout / "marker.log")
        env["POLL_HEARTBEAT_MAX_TICKS"] = "1"
        env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "1"
        env["POLL_HEARTBEAT_PATROL_EVERY_N"] = "1"
        env["FAKE_POLL_DUE"] = "0"
        env["FAKE_PATROL_MARKER"] = str(patrol_marker)
        env["HOME"] = str(home)
        env.pop("CLAUDE_SKILL", None)
        proc = subprocess.Popen(
            ["bash", str(POLL_HEARTBEAT)], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=env,
        )
        try:
            # Startup (CHECKOUT resolution, the ROLES read, GC) happens
            # before the loop's first `sleep 1` -- this window lets that
            # settle before the reclone simulation removes the dir.
            time.sleep(0.3)
            shutil.rmtree(checkout)
            out, err = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise
        assert proc.returncode == 0, f"poll-heartbeat.sh should exit 0: {err}"
        assert "[poll-heartbeat] checkout unavailable" in out, out
        assert "crashed" not in out, out
        assert "[patrol-poll]" not in out, out
        assert not patrol_marker.exists(), \
            "no per-role patrol_promote.py subprocess should run when checkout is missing"


# issue #2266: bash 3.2-compatibility regression smoke. #1719 documented
# that a `python3 - <<'PY' ... PY` heredoc nested inside a `$( )` command
# substitution makes bash 3.2 miscount quote nesting while scanning for
# the $( )'s own closing paren -- and #2181's comment edits flipped the
# heredoc body's total apostrophe count from even to odd, reviving the
# exact failure #1719 had worked around. The fix (extracting the Python
# to on-the-record/monitors/poll_heartbeat_delta.py) removes the shape
# entirely rather than re-balancing the count, so this pins the shape's
# absence structurally instead of pinning a specific apostrophe count.
#
# warrant-hunt finding (docs/issue-2266/reports/implementation/2026-08-25-
# hunt-poll-heartbeat-bash32-heredoc-fix.md): a same-line-only regex
# (`\$\(.*<<DELIM$`) misses a `$( )` and its heredoc opener split across a
# `\`-continued or otherwise multi-line command substitution -- confirmed
# against a real bash 3.2 container that this shape reproduces the
# identical parse failure while the naive regex stays silent. Replaced
# with a depth-tracking scan: count unmatched `$(` opens across the whole
# file (heredoc bodies excluded from counting, since their content isn't
# what the bash 3.2 parser miscounts) and flag any heredoc opener seen
# while that count is still positive, regardless of line span.
_HEREDOC_OPEN_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def _find_command_substitution_wrapped_heredocs(text: str) -> list[tuple[int, str]]:
    lines = text.split("\n")
    open_depth = 0
    in_heredoc = False
    heredoc_delim = None
    heredoc_strip_tabs = False
    findings = []
    for lineno, line in enumerate(lines, 1):
        if in_heredoc:
            probe = line.lstrip("\t") if heredoc_strip_tabs else line
            if probe == heredoc_delim:
                in_heredoc = False
            continue
        if line.lstrip().startswith("#"):
            continue
        j = 0
        while j < len(line):
            if line[j:j + 2] == "$(":
                open_depth += 1
                j += 2
                continue
            if line[j] == ")" and open_depth > 0:
                open_depth -= 1
                j += 1
                continue
            j += 1
        m = _HEREDOC_OPEN_RE.search(line)
        if m:
            if open_depth > 0:
                findings.append((lineno, line.strip()))
            heredoc_delim = m.group(2)
            heredoc_strip_tabs = "<<-" in line
            in_heredoc = True
    return findings


def t_no_command_substitution_wrapped_heredoc_in_script():
    """issue #2266 acceptance check: poll-heartbeat.sh opens no heredoc
    while a `$( ... )` command substitution from the same or an earlier
    line is still unclosed -- the structural shape #1719/#2181 hit,
    checked directly rather than by counting apostrophes in a heredoc
    body that no longer exists."""
    text = POLL_HEARTBEAT.read_text(encoding="utf-8")
    hits = _find_command_substitution_wrapped_heredocs(text)
    assert not hits, f"command-substitution-wrapped heredoc(s) found: {hits}"


def t_command_substitution_wrapped_heredoc_detector_catches_multiline_shape():
    """issue #2266 warrant-hunt finding, detector self-check: the earlier
    same-line-only regex passed silently on a `$( )` and its heredoc
    opener split across a `\\`-continued line (confirmed against a real
    bash 3.2 container to be the identical parse failure). Pins that the
    depth-tracking detector above still flags that shape, using a
    synthetic sample -- never the real poll-heartbeat.sh -- so this test
    cannot pass merely because the file happens to be clean."""
    sample = (
        "out=\"$(printf 'hi' | \\\n"
        "python3 - <<'PY'\n"
        "print('hi')\n"
        "PY\n"
        ")\"\n"
    )
    hits = _find_command_substitution_wrapped_heredocs(sample)
    assert hits, "detector must flag a multi-line command-substitution-wrapped heredoc"


def t_poll_heartbeat_bash_syntax_is_clean():
    """issue #2266 acceptance check: `bash -n` parses poll-heartbeat.sh
    cleanly under whatever bash the test host ships -- the minimal proxy
    for a bash 3.2 binary when one isn't reachable in CI (the structural
    check above is the primary regression pin; this catches any other
    parse-time break)."""
    r = subprocess.run(["bash", "-n", str(POLL_HEARTBEAT)], capture_output=True, text=True)
    assert r.returncode == 0, f"bash -n failed: {r.stderr}"


# issue #2919: poll-heartbeat.sh died with exit 1 on macOS (bash 3.2, no
# flock) -- two independent regressions, pinned below. Reproduction
# against a real bash 3.2.57 container (this issue's investigation)
# confirmed bash 3.2 treats even a *declared, genuinely-empty* array as
# unbound under `set -u` when expanded bare (`ARR=(); "${ARR[@]}"` still
# raises) -- not just an unset-variable case -- so the fix is the
# `${NAME[@]+"${NAME[@]}"}` guard, not merely ensuring the array is
# declared.
_GUARDED_ARRAY_RE = re.compile(
    r'\$\{([A-Za-z_][A-Za-z0-9_]*)\[([@*])\]\+"\$\{\1\[\2\]\}"\}'
)
_ARRAY_EXPANSION_RE = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\[[@*]\]\}')


def _find_unguarded_array_expansions(text: str) -> list[tuple[int, str]]:
    """Masks every occurrence of the bash-3.2-safe
    `${NAME[@]+"${NAME[@]}"}` idiom first, then flags any `${NAME[@]}` /
    `${NAME[*]}` expansion left over -- bounded by scanning the whole
    file for every `[@]`/`[*]` occurrence, so a new array introduced
    later and left unguarded is caught the same way this one was found."""
    masked = _GUARDED_ARRAY_RE.sub("", text)
    findings = []
    for lineno, line in enumerate(masked.split("\n"), 1):
        if _ARRAY_EXPANSION_RE.search(line):
            findings.append((lineno, line.strip()))
    return findings


def t_no_unguarded_array_expansion_in_script_issue_2919():
    """issue #2919 acceptance check 3: enumerate every `${...[@]}` (or
    `[*]`) expansion in poll-heartbeat.sh and require each to use the
    bash-3.2-safe guarded idiom -- precedent controller #521/#523, where a
    fix that patched only the one firing unguarded expansion left others
    in the same file to fail later on the same platform. Search bound:
    the whole file, via regex over every `[@]`/`[*]` occurrence -- not
    just the line the reporter's traceback named."""
    text = POLL_HEARTBEAT.read_text(encoding="utf-8")
    hits = _find_unguarded_array_expansions(text)
    assert not hits, f"unguarded array expansion(s) found (bash-3.2-unsafe): {hits}"


def t_unguarded_array_detector_catches_a_bare_expansion_issue_2919():
    """Detector self-check, mirroring t_command_substitution_wrapped_heredoc_detector_catches_multiline_shape:
    a synthetic bare `${ARR[@]}` (never the real poll-heartbeat.sh) must
    be flagged, so the check above cannot pass merely because the file
    happens to be clean."""
    sample = 'for x in "${ARR[@]}"; do\n  echo "$x"\ndone\n'
    hits = _find_unguarded_array_expansions(sample)
    assert hits, "detector must flag a bare, unguarded array expansion"


FAKE_SPAWN_PY_NO_ROLE_DATA = """#!/usr/bin/env python3
import os, sys
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

FAKE_SPAWN_PY_EMPTY_SKILLS = """#!/usr/bin/env python3
import os, sys
def role_data():
    return {}
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


def _run_skills_query_tick(checkout_spawn_py: str, tmp: Path) -> subprocess.CompletedProcess:
    checkout = tmp / "checkout"
    checkout.mkdir()
    (checkout / "spawn.py").write_text(checkout_spawn_py, encoding="utf-8")
    marker = tmp / "marker.log"
    home = tmp / "home"
    home.mkdir()
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env["FAKE_SPAWN_MARKER"] = str(marker)
    env["POLL_HEARTBEAT_MAX_TICKS"] = "1"
    env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
    env["POLL_HEARTBEAT_PATROL_EVERY_N"] = "1"
    env["FAKE_POLL_DUE"] = "0"
    env["HOME"] = str(home)
    env.pop("CLAUDE_SKILL", None)
    return subprocess.run(
        ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True, env=env, timeout=15,
    )


def t_patrol_skills_query_failure_is_visible_issue_2919():
    """issue #2919 acceptance check 3 (must-not clause): a patrol-skills
    query that FAILS -- `import spawn` succeeds but `spawn.role_data()`
    raises AttributeError (confirmed live: this is the actual shape of
    the real repo's spawn.py right now, which has no role_data() either
    -- see this issue's Open findings) -- must print a visible
    per-patrol-tick line. It must not read as an indistinguishable quiet
    zero-roles tick, the must-not this issue names explicitly."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = _run_skills_query_tick(FAKE_SPAWN_PY_NO_ROLE_DATA, Path(d))
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert "[patrol-poll] skills query failed at startup" in r.stdout, r.stdout


def t_patrol_skills_genuinely_empty_roster_stays_quiet_issue_2919():
    """issue #2919 acceptance check 3 counterpart: a role_data() that
    SUCCEEDS but legitimately returns zero skills must stay quiet -- no
    query-failed line -- proving the two conditions (failed query vs.
    genuinely-empty roster) are actually distinguishable and not just the
    failure case made loud."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = _run_skills_query_tick(FAKE_SPAWN_PY_EMPTY_SKILLS, Path(d))
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0: {r.stderr}"
        assert "skills query failed" not in r.stdout, r.stdout
        assert "[patrol-poll]" not in r.stdout, r.stdout


def t_alive_stamp_write_survives_missing_flock_issue_2919():
    """issue #2919 acceptance check 2: on a host with no `flock` reachable
    on PATH (the reported macOS condition -- flock ships with util-linux,
    absent by default on macOS), the tick must still complete cleanly and
    the alive-stamp write must not silently drop serialisation. PATH is
    rebuilt from symlinks to only the binaries the script needs, minus
    flock, so `command -v flock` genuinely fails the way it does on the
    reporter's host -- not merely un-exercised."""
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        bindir = tmp / "bin"
        bindir.mkdir()
        needed = ["bash", "python3", "git", "mkdir", "touch", "mv", "rm", "rmdir",
                  "wc", "date", "sleep", "dirname", "cat", "printf", "sh", "env",
                  "basename", "chmod"]
        for name in needed:
            src = shutil.which(name)
            if src:
                (bindir / name).symlink_to(src)
        assert not (bindir / "flock").exists(), \
            "test setup bug: flock leaked into the restricted PATH"
        env = dict(os.environ)
        env["PATH"] = str(bindir)
        env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
        env["FAKE_SPAWN_MARKER"] = str(marker)
        env["POLL_HEARTBEAT_MAX_TICKS"] = "1"
        env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
        env["FAKE_POLL_DUE"] = "1"
        env["FAKE_WATCHDOG_REPORT"] = EMPTY_ROSTER_REPORT
        env["HOME"] = str(home)
        env.pop("CLAUDE_SKILL", None)
        r = subprocess.run(
            [str(bindir / "bash"), str(POLL_HEARTBEAT)], input="", capture_output=True, text=True,
            env=env, timeout=15,
        )
        assert r.returncode == 0, f"poll-heartbeat.sh should exit 0 even without flock: {r.stderr}"
        assert "flock" not in r.stderr, r.stderr
        stamp = checkout / "runs" / "poll_heartbeat_alive.json"
        assert stamp.exists(), "alive stamp must still be written when flock is absent"
        assert '"last_tick"' in stamp.read_text(), stamp.read_text()


# issue #2919 follow-up (adversarial review of PR #2923's mkdir-mutex fix,
# docs/issue-2919/reports/adversarial-review-a4f05242.md "Open findings"
# point 1): the 20-failed-retries-then-force-break threshold could evict a
# live, merely-slow holder's lock -- confirmed live under real bash 3.2
# with `flock` absent (docker bash:3.2, restricted PATH) during this
# fix's own verification. These tests exercise the fixed mutex by
# dynamically EXTRACTING the real `_alive_stamp_lock_owner_status` and
# `_alive_stamp_write` function bodies out of the actual script text (not
# a hand-maintained copy) so they can never silently drift from the
# implementation under review, then splice in test-only ENTER/hold/EXIT
# instrumentation at a uniquely-anchored point -- mirroring the
# adversarial review's own harness shape (its points 9/10: "extracted the
# mkdir-mutex acquire/release code verbatim ... into a standalone harness
# with a widened critical section", "the widening changes only the
# payload timing, not the mutex code under test"). The mutex logic itself
# (noclobber-write/case/kill -0/rm) is portable POSIX shell, not
# bash-3.2-specific -- host bash is sufficient for these; the bash-3.2
# array/flock-detection concerns are already covered separately above.
# The bash-3.2/no-`flock` concurrency claims specifically (mutual
# exclusion holding under the real reported platform, not just under
# host bash) are covered by the docker bash:3.2 container tests below.
def _extract_bash_function(text: str, name: str) -> str:
    marker = f"{name}() {{"
    start = text.index(marker)
    depth = 0
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise AssertionError(f"unterminated function {name!r} while extracting from script")


def _splice_test_instrumentation(alive_stamp_write_text: str) -> str:
    """Inserts ENTER/optional-self-kill/hold/EXIT logging immediately
    after the acquire loop's closing `done` (the point the fixed code has
    already atomically created the lockfile with its own pid inside it --
    issue #2919 follow-up: creation and identity-publication are now one
    command, so there is no longer a separate pid-write line to anchor on)
    and before the real stamp write + release -- test-only instrumentation,
    anchored on a substring unique to that exact point so a future edit to
    this line fails the test loudly (via the uniqueness assert) rather than
    silently splicing into the wrong place."""
    anchor = '\n    done\n'
    count = alive_stamp_write_text.count(anchor)
    assert count == 1, f"expected exactly one acquire-loop close anchor, found {count}"
    idx = alive_stamp_write_text.index(anchor) + len(anchor)
    instrumentation = """
    printf '%s ENTER %s pid=%s\\n' "$(date +%s.%N 2>/dev/null || date +%s)" "${MUTEX_TEST_WORKER_ID}" "$$" >>"${MUTEX_TEST_LOGFILE}"
    if [ "${MUTEX_TEST_KILL_SELF:-0}" = "1" ]; then
      sleep "${MUTEX_TEST_HOLD_SECONDS:-0}"
      printf '%s SELFKILL %s pid=%s\\n' "$(date +%s.%N 2>/dev/null || date +%s)" "${MUTEX_TEST_WORKER_ID}" "$$" >>"${MUTEX_TEST_LOGFILE}"
      kill -9 $$
    fi
    sleep "${MUTEX_TEST_HOLD_SECONDS:-0}"
    printf '%s EXIT %s pid=%s\\n' "$(date +%s.%N 2>/dev/null || date +%s)" "${MUTEX_TEST_WORKER_ID}" "$$" >>"${MUTEX_TEST_LOGFILE}"
"""
    return alive_stamp_write_text[:idx] + instrumentation + alive_stamp_write_text[idx:]


def _write_mutex_harness(tmp: Path) -> Path:
    script_text = POLL_HEARTBEAT.read_text(encoding="utf-8")
    owner_status_fn = _extract_bash_function(script_text, "_alive_stamp_lock_owner_status")
    alive_stamp_write_fn = _splice_test_instrumentation(
        _extract_bash_function(script_text, "_alive_stamp_write")
    )
    harness = tmp / "mutex_harness.sh"
    harness.write_text(
        "#!/usr/bin/env bash\n"
        "set -uo pipefail\n"
        f"{owner_status_fn}\n"
        f"{alive_stamp_write_fn}\n"
        "_poll_watchdog_log_append() {\n"
        "  printf '%s [log:%s] %s\\n' \"$(date +%s.%N 2>/dev/null || date +%s)\" "
        "\"${MUTEX_TEST_WORKER_ID}\" \"$1\" >>\"${MUTEX_TEST_LOGFILE}\"\n"
        "}\n"
        "_alive_stamp_has_flock=0\n"
        "CHECKOUT=\"$(dirname \"$1\")\"\n"
        "_alive_stamp_path=\"$1\"\n"
        "_alive_stamp_write\n",
        encoding="utf-8",
    )
    return harness


def _run_mutex_worker(harness: Path, stamp_path: Path, logfile: Path, worker_id: str,
                       hold_seconds: str, kill_self: str) -> subprocess.Popen:
    env = dict(os.environ)
    env["MUTEX_TEST_WORKER_ID"] = worker_id
    env["MUTEX_TEST_LOGFILE"] = str(logfile)
    env["MUTEX_TEST_HOLD_SECONDS"] = hold_seconds
    env["MUTEX_TEST_KILL_SELF"] = kill_self
    return subprocess.Popen(
        ["bash", str(harness), str(stamp_path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
    )


def _parse_mutex_log(logfile: Path) -> dict:
    events = {}
    if not logfile.exists():
        return events
    for line in logfile.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        ts, kind, worker = parts[0], parts[1], parts[2]
        if kind in ("ENTER", "EXIT", "SELFKILL"):
            events.setdefault(worker, {})[kind] = float(ts)
    return events


def t_alive_stamp_lock_owner_status_establishes_liveness_issue_2919():
    """issue #2919 follow-up: direct unit test of the sprouted seam
    (_alive_stamp_lock_owner_status), independent of the full
    acquire/release sequence -- refactoring-legacy-seam-selection rule 1
    (Sprout Method: a single, clearly-localized behavioral change gets
    its own separately-testable function). Pins all three verdicts:
    a lockfile with no readable content yet ("forming"), one naming a
    genuinely live process ("alive"), and one naming a confirmed-reaped
    process ("dead") -- liveness is ESTABLISHED via a real PID check,
    never inferred."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        script_text = POLL_HEARTBEAT.read_text(encoding="utf-8")
        owner_status_fn = _extract_bash_function(script_text, "_alive_stamp_lock_owner_status")
        driver = tmp / "owner_status_driver.sh"
        driver.write_text(f"#!/usr/bin/env bash\nset -uo pipefail\n{owner_status_fn}\n_alive_stamp_lock_owner_status \"$1\"\n",
                           encoding="utf-8")

        lockfile = tmp / "stamp.lockfile"
        lockfile.write_text("", encoding="utf-8")
        r = subprocess.run(["bash", str(driver), str(lockfile)], capture_output=True, text=True, timeout=5)
        assert r.stdout == "forming", f"empty lockfile must read as forming: {r.stdout!r}"

        live_proc = subprocess.Popen(["sleep", "5"])
        try:
            lockfile.write_text(str(live_proc.pid), encoding="utf-8")
            r = subprocess.run(["bash", str(driver), str(lockfile)], capture_output=True, text=True, timeout=5)
            assert r.stdout == "alive", f"a genuinely running owner pid must read as alive: {r.stdout!r}"
        finally:
            live_proc.kill()
            live_proc.wait()

        dead_proc = subprocess.Popen(["true"])
        dead_pid = dead_proc.pid
        dead_proc.wait()
        import time as _time
        deadline = _time.time() + 5
        while _time.time() < deadline:
            try:
                os.kill(dead_pid, 0)
                _time.sleep(0.05)
            except OSError:
                break
        lockfile.write_text(str(dead_pid), encoding="utf-8")
        r = subprocess.run(["bash", str(driver), str(lockfile)], capture_output=True, text=True, timeout=5)
        assert r.stdout == "dead", f"a confirmed-reaped owner pid must read as dead: {r.stdout!r}"


def t_alive_stamp_mutex_never_evicts_slow_live_holder_issue_2919():
    """issue #2919 follow-up regression pin for the adversarial review's
    highest-severity Open finding: a live holder that merely runs long
    (here, past the OLD 20-failed-retry/20s break threshold this fix
    replaces) must never have its lock broken and re-entered by a
    contending worker. Worker A holds the critical section 22s (alive the
    whole time); worker B starts 0.3s later and must not ENTER until
    strictly after A's EXIT -- proving at most one holder at any instant,
    live under the same mutex code the adversarial review attacked."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        harness = _write_mutex_harness(tmp)
        stamp = tmp / "stamp"
        logfile = tmp / "log"
        proc_a = _run_mutex_worker(harness, stamp, logfile, "A", "22", "0")
        time.sleep(0.3)
        proc_b = _run_mutex_worker(harness, stamp, logfile, "B", "0.2", "0")
        out_a, err_a = proc_a.communicate(timeout=40)
        out_b, err_b = proc_b.communicate(timeout=40)
        assert proc_a.returncode == 0, f"worker A must exit 0: {err_a}"
        assert proc_b.returncode == 0, f"worker B must exit 0: {err_b}"

        events = _parse_mutex_log(logfile)
        assert "A" in events and "ENTER" in events["A"] and "EXIT" in events["A"], events
        assert "B" in events and "ENTER" in events["B"] and "EXIT" in events["B"], events
        assert events["B"]["ENTER"] >= events["A"]["EXIT"], (
            f"worker B entered before worker A (still alive) released the lock -- "
            f"mutual exclusion violated: {events}"
        )


def t_alive_stamp_mutex_recovers_crashed_holder_issue_2919():
    """issue #2919 follow-up: the companion property this fix must
    preserve -- a genuinely crashed holder (SIGKILL'd mid-critical-section
    without releasing the lockfile) must not deadlock the tick forever.
    Worker A enters, holds 1s, then SIGKILLs itself without cleanup;
    worker B, contending 0.3s after A started, must detect A's pid as
    dead and complete (ENTER+EXIT) within a bounded time -- proving
    recovery, not just eviction-avoidance.

    A is reaped promptly by a background thread the moment it exits, the
    same way a real crashed writer's own parent process reaps it -- `kill
    -0` reports a zombie (unreaped exited process) as still existing, so
    an unreaped A would make this test's own harness artificially slow to
    detect death, which is a property of the test's process supervision,
    not of the fixed liveness check itself. This is exactly the gap
    adversarial-review-95d4569a point 2 named: who reaps a crashed
    poll-heartbeat.sh in real deployment, and how promptly, is a Claude
    Code plugin Monitor platform capability this repo cannot establish
    (docs/specs/platform-capabilities.md) -- this test's prompt reaping is
    a test-harness convenience, not a production guarantee. The
    deployment-independent recovery path for a holder whose reap never
    happens is exercised separately below, by
    t_alive_stamp_mutex_max_age_recovers_unreaped_holder_issue_2919, which
    never reaps its holder at all."""
    import tempfile
    import threading
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        harness = _write_mutex_harness(tmp)
        stamp = tmp / "stamp"
        logfile = tmp / "log"
        proc_a = _run_mutex_worker(harness, stamp, logfile, "A", "1", "1")
        threading.Thread(target=proc_a.wait, daemon=True).start()
        time.sleep(0.3)
        proc_b = _run_mutex_worker(harness, stamp, logfile, "B", "0.1", "0")
        out_b, err_b = proc_b.communicate(timeout=15)
        assert proc_b.returncode == 0, f"worker B must recover and exit 0: {err_b}"
        proc_a.wait(timeout=5)

        events = _parse_mutex_log(logfile)
        assert "A" in events and "SELFKILL" in events["A"], events
        assert "B" in events and "ENTER" in events["B"] and "EXIT" in events["B"], (
            f"worker B must recover the crashed holder's lock and complete: {events}"
        )
        assert not (stamp.with_name(stamp.name + ".lockfile")).exists(), \
            "no lockfile should remain after the crashed holder was reclaimed and B released cleanly"


def t_alive_stamp_mutex_max_age_recovers_unreaped_holder_issue_2919():
    """issue #2919 follow-up (adversarial-review-95d4569a point 2, "the
    zombie/reap-uncertainty gap"): proves the recovery path that does NOT
    depend on pid liveness at all. Worker A self-kills but is deliberately
    left UNREAPED for the whole test (no background wait(), unlike the
    sibling crash-recovery test above) -- os.kill(pid, 0) on an unreaped
    exited child keeps succeeding exactly like a real zombie would, so
    `_alive_stamp_lock_owner_status` would report "alive" for it
    indefinitely and a waiter relying solely on that check would block
    forever. POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE is overridden to 2s so the
    test does not need to wait out the 60s production default; worker B
    must still recover and complete well within a bounded time, and the
    watchdog log must name this specific reclaim as the max-age safety
    valve (not a normal `dead` reclaim), since collapsing the two into one
    log message would misrepresent an assumption override as an
    established fact -- the same silent-failure-audit distinction this
    fix's `dead`-branch log message already draws."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        harness = _write_mutex_harness(tmp)
        stamp = tmp / "stamp"
        logfile = tmp / "log"
        env = dict(os.environ)
        env["POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE"] = "2"
        env["MUTEX_TEST_WORKER_ID"] = "A"
        env["MUTEX_TEST_LOGFILE"] = str(logfile)
        env["MUTEX_TEST_HOLD_SECONDS"] = "0.2"
        env["MUTEX_TEST_KILL_SELF"] = "1"
        proc_a = subprocess.Popen(
            ["bash", str(harness), str(stamp)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
        )
        try:
            # Deliberately never poll()/wait() proc_a until the final
            # cleanup below -- either call reaps it via waitpid(), which
            # would silently turn this into the sibling prompt-reaping
            # test instead of the unreaped-zombie case this test exists
            # to cover. Wait on the log line instead of the process.
            deadline = time.time() + 5
            while time.time() < deadline and "SELFKILL A" not in (
                logfile.read_text(encoding="utf-8") if logfile.exists() else ""
            ):
                time.sleep(0.05)
            assert "SELFKILL A" in logfile.read_text(encoding="utf-8"), \
                "worker A must have self-killed before worker B starts contending"
            env_b = dict(os.environ)
            env_b["POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE"] = "2"
            env_b["MUTEX_TEST_WORKER_ID"] = "B"
            env_b["MUTEX_TEST_LOGFILE"] = str(logfile)
            env_b["MUTEX_TEST_HOLD_SECONDS"] = "0.1"
            env_b["MUTEX_TEST_KILL_SELF"] = "0"
            proc_b = subprocess.Popen(
                ["bash", str(harness), str(stamp)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env_b,
            )
            out_b, err_b = proc_b.communicate(timeout=15)
            assert proc_b.returncode == 0, f"worker B must recover via the max-age valve and exit 0: {err_b}"
        finally:
            proc_a.kill()
            proc_a.wait()

        events = _parse_mutex_log(logfile)
        assert "A" in events and "SELFKILL" in events["A"], events
        assert "B" in events and "ENTER" in events["B"] and "EXIT" in events["B"], (
            f"worker B must recover the unreaped holder's lock via the max-age valve and complete: {events}"
        )
        log_text = logfile.read_text(encoding="utf-8")
        assert "force-reclaimed independent of liveness check" in log_text, (
            f"the max-age reclaim must be logged distinctly from a normal dead-owner reclaim: {log_text}"
        )


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
