#!/usr/bin/env python3
"""issue #1497: poll-heartbeat liveness stamp, quiet ticks, and the
turn-driven staleness re-arm directive.

  python3 -m pytest tests/test_monitor_liveness.py
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POLL_HEARTBEAT = REPO_ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh"
DIRECTIVE = REPO_ROOT / "on-the-record" / "hooks" / "directive.sh"
STOP_POLL_REARM = REPO_ROOT / "on-the-record" / "hooks" / "stop-poll-rearm.sh"

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

ROSTER_REPORT = "[poll-report] roster: alpha/beta:1234 healthy"


def _make_checkout(tmp: Path) -> Path:
    checkout = tmp / "checkout"
    checkout.mkdir()
    (checkout / "spawn.py").write_text(FAKE_SPAWN_PY, encoding="utf-8")
    return checkout


def _run_heartbeat(checkout: Path, home: Path, env_extra: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env["HOME"] = str(home)
    env["POLL_HEARTBEAT_MAX_TICKS"] = env_extra.pop("POLL_HEARTBEAT_MAX_TICKS", "1")
    env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
    env.pop("CLAUDE_ROLE", None)
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True,
        env=env, timeout=15, cwd=str(checkout),
    )


def _alive_stamp(checkout: Path) -> Path:
    return checkout / "runs" / "poll_heartbeat_alive.json"


def test_quiet_tick_emits_nothing():
    # A due tick whose watchdog report has no new signal vs the previous
    # tick's recorded state must produce empty stdout, yet still write the
    # liveness stamp (req 1 pinned + req 2's unconditional stamp write).
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()

        r1 = _run_heartbeat(checkout, home, {"FAKE_POLL_DUE": "1", "FAKE_WATCHDOG_REPORT": ROSTER_REPORT})
        assert r1.returncode == 0, r1.stderr
        assert r1.stdout == ROSTER_REPORT + "\n"
        stamp1 = json.loads(_alive_stamp(checkout).read_text(encoding="utf-8"))
        assert isinstance(stamp1["last_tick"], (int, float))

        time.sleep(1.1)
        r2 = _run_heartbeat(checkout, home, {"FAKE_POLL_DUE": "1", "FAKE_WATCHDOG_REPORT": ROSTER_REPORT})
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout == "", f"unchanged report on a repeat tick must be silent: {r2.stdout!r}"
        stamp2 = json.loads(_alive_stamp(checkout).read_text(encoding="utf-8"))
        assert stamp2["last_tick"] > stamp1["last_tick"], "stamp must advance on every tick, quiet or not"


def test_delta_tick_emits_only_delta():
    # A tick with one new/changed signal line vs the previous tick's state
    # emits only that delta, not the full roster dump, while still
    # stamping liveness.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()

        first_report = "[poll-report] roster: alpha/beta:1234 healthy\n[poll-report] roster: gamma/delta:5678 healthy"
        r1 = _run_heartbeat(checkout, home, {"FAKE_POLL_DUE": "1", "FAKE_WATCHDOG_REPORT": first_report})
        assert r1.returncode == 0, r1.stderr
        assert r1.stdout == first_report + "\n"

        time.sleep(1.1)
        second_report = "[poll-report] roster: alpha/beta:1234 healthy\n[poll-report] roster: gamma/delta:5678 stalled"
        r2 = _run_heartbeat(checkout, home, {"FAKE_POLL_DUE": "1", "FAKE_WATCHDOG_REPORT": second_report})
        assert r2.returncode == 0, r2.stderr
        assert r2.stdout == "[poll-report] roster: gamma/delta:5678 stalled\n", (
            f"only the changed line should be emitted, not the full report: {r2.stdout!r}"
        )
        stamp = json.loads(_alive_stamp(checkout).read_text(encoding="utf-8"))
        assert isinstance(stamp["last_tick"], (int, float))


def _run_hook(script: Path, checkout: Path, workdir: Path, env_extra: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env.pop("CLAUDE_ROLE", None)
    env.pop("ORCHESTRATE_OFF", None)
    env.update(env_extra)
    payload = json.dumps({"session_id": "test-session"})
    return subprocess.run(
        ["bash", str(script)], input=payload, capture_output=True, text=True,
        env=env, timeout=15, cwd=str(workdir),
    )


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)


def test_stale_stamp_directive():
    # A stamp older than 3x the interval (threshold overridden here for a
    # fast test) makes the hook emit the re-arm directive line exactly
    # once per staleness episode -- a second call while still stale, with
    # the same stamp, must not repeat it.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        _git_init(checkout)
        (checkout / "docs" / "specs").mkdir(parents=True)
        (checkout / "docs" / "specs" / "approvers.md").write_text("x", encoding="utf-8")
        runs = checkout / "runs"
        runs.mkdir()
        stale_time = time.time() - 1000
        (runs / "poll_heartbeat_alive.json").write_text(
            json.dumps({"last_tick": stale_time}), encoding="utf-8",
        )

        for script in (DIRECTIVE, STOP_POLL_REARM):
            state_path = runs / "poll_heartbeat_staleness_state.json"
            if state_path.exists():
                state_path.unlink()
            r1 = _run_hook(script, checkout, checkout, {"MONITOR_LIVENESS_STALE_SECONDS": "5"})
            assert "poll-heartbeat monitor dead since" in r1.stdout, (
                f"{script.name}: expected re-arm directive, got: {r1.stdout!r} / {r1.stderr!r}"
            )
            # issue #2182: distinct tag (not the routine [orchestrate] prefix
            # shared with the always-present per-turn directive block) and an
            # explicit persistent:true mandate, so a literal re-arm cannot
            # silently die again after the Monitor tool's 5-minute default.
            assert "[orchestrate][MONITOR-DEAD]" in r1.stdout
            assert "persistent: true" in r1.stdout
            assert str(checkout) in r1.stdout, "re-arm command must name the checkout path"

            r2 = _run_hook(script, checkout, checkout, {"MONITOR_LIVENESS_STALE_SECONDS": "5"})
            assert "poll-heartbeat monitor dead since" not in r2.stdout, (
                f"{script.name}: directive must not repeat within the same staleness episode: {r2.stdout!r}"
            )


def test_fresh_stamp_silent():
    # A fresh stamp (within threshold) means both hooks emit nothing about
    # the monitor's liveness.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        _git_init(checkout)
        (checkout / "docs" / "specs").mkdir(parents=True)
        (checkout / "docs" / "specs" / "approvers.md").write_text("x", encoding="utf-8")
        runs = checkout / "runs"
        runs.mkdir()
        (runs / "poll_heartbeat_alive.json").write_text(
            json.dumps({"last_tick": time.time()}), encoding="utf-8",
        )

        for script in (DIRECTIVE, STOP_POLL_REARM):
            r = _run_hook(script, checkout, checkout, {"MONITOR_LIVENESS_STALE_SECONDS": "180"})
            assert "poll-heartbeat monitor dead" not in r.stdout, (
                f"{script.name}: fresh stamp must stay silent: {r.stdout!r}"
            )


def test_monitor_dead_standing_invariant_always_present():
    # issue #2182: the standing re-arm rule lives in directive.sh's
    # byte-stable per-turn ALWAYS-ON INVARIANTS block, so it is present
    # on every turn (not only the turn a staleness episode is detected)
    # -- it is what makes the [MONITOR-DEAD] tag actionable rather than
    # a one-off line the orchestrator has to already know the meaning of.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        _git_init(checkout)
        (checkout / "docs" / "specs").mkdir(parents=True)
        (checkout / "docs" / "specs" / "approvers.md").write_text("x", encoding="utf-8")
        runs = checkout / "runs"
        runs.mkdir()
        (runs / "poll_heartbeat_alive.json").write_text(
            json.dumps({"last_tick": time.time()}), encoding="utf-8",
        )

        r = _run_hook(DIRECTIVE, checkout, checkout, {"MONITOR_LIVENESS_STALE_SECONDS": "180"})
        assert "poll-heartbeat monitor dead" not in r.stdout, "fresh stamp must stay silent on the notice itself"
        assert "[orchestrate][MONITOR-DEAD]" in r.stdout, (
            f"standing invariant bullet naming the tag must always be present: {r.stdout!r}"
        )
        assert "persistent: true" in r.stdout


def test_missing_stamp_treated_as_stale():
    # empty state: no stamp file at all (monitor never started this
    # session) is stale from the first hook check.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        _git_init(checkout)
        (checkout / "docs" / "specs").mkdir(parents=True)
        (checkout / "docs" / "specs" / "approvers.md").write_text("x", encoding="utf-8")
        assert not _alive_stamp(checkout).exists()

        r = _run_hook(DIRECTIVE, checkout, checkout, {"MONITOR_LIVENESS_STALE_SECONDS": "180"})
        assert "poll-heartbeat monitor dead since" in r.stdout, (
            f"missing stamp must be treated as stale from the first check: {r.stdout!r} / {r.stderr!r}"
        )
