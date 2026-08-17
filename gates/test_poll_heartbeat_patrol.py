#!/usr/bin/env python3
"""issue #1598 (patrol wiring E2): coverage for the patrol_promote
wiring added to on-the-record/monitors/poll-heartbeat.sh
(docs/issue-1598/proposals/patrol-heartbeat-wiring.md). Drives the real
poll-heartbeat.sh (same harness pattern as
gates/test_poll_heartbeat_delta.py / on-the-record/monitors/test_poll_heartbeat.py)
against a fake spawn.py (supplying ROLES) and a fake
gates/patrol_promote.py stub, asserting:
  (a) patrol_promote is invoked only on every Nth tick (its own counter,
      POLL_HEARTBEAT_PATROL_EVERY_N), not every tick;
  (b) the kill-switch file (.on-the-record/patrol-disabled) suppresses
      invocation and produces its own trace line;
  (c) a role with no board data still results in zero patrol side
      effects (zero promotions counted, wiring makes exactly one call
      per role and does nothing further).

  python3 gates/test_poll_heartbeat_patrol.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POLL_HEARTBEAT = REPO_ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh"

FAKE_SPAWN_PY = """#!/usr/bin/env python3
import os, sys
ROLES = ("test-role",)
if __name__ == "__main__":
    if sys.argv[1:2] == ["poll-due"]:
        sys.exit(0 if os.environ.get("FAKE_POLL_DUE") == "1" else 1)
    if sys.argv[1:2] == ["watchdog"]:
        sys.exit(0)
    sys.exit(0)
"""

FAKE_PATROL_PROMOTE_PY = """#!/usr/bin/env python3
import json, os, sys

marker = os.environ["FAKE_PATROL_MARKER"]
with open(marker, "a", encoding="utf-8") as f:
    f.write(sys.argv[-1] + "\\n")

promotions = int(os.environ.get("FAKE_PATROL_PROMOTIONS", "0"))
summary = {"dry_run": False, "api_calls": 1,
           "promotions": [{"fingerprint": "x", "issue": 1}] * promotions,
           "deferred": []}
print(json.dumps(summary, indent=2))
"""


def _make_checkout(tmp: Path) -> Path:
    checkout = tmp / "checkout"
    checkout.mkdir()
    (checkout / "spawn.py").write_text(FAKE_SPAWN_PY, encoding="utf-8")
    gates = checkout / "gates"
    gates.mkdir()
    (gates / "patrol_promote.py").write_text(FAKE_PATROL_PROMOTE_PY, encoding="utf-8")
    return checkout


def _run(checkout: Path, home: Path, marker: Path, extra_env: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env["FAKE_SPAWN_MARKER"] = str(checkout / "spawn_marker.log")
    env["FAKE_PATROL_MARKER"] = str(marker)
    env["FAKE_POLL_DUE"] = "0"
    env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
    env["HOME"] = str(home)
    env.pop("CLAUDE_ROLE", None)
    env.update(extra_env)
    return subprocess.run(
        ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True, text=True, env=env, timeout=15,
    )


def t_patrol_invoked_only_on_nth_tick():
    """(a) with POLL_HEARTBEAT_PATROL_EVERY_N=3, a run bounded at tick 2
    must not invoke patrol_promote (patrol_tick is in-process-only, like
    the existing `tick` counter, so each run starts fresh at 0); a run
    reaching tick 3 must invoke it exactly once (one call per configured
    role), on tick 3 only."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        marker = tmp / "patrol_marker.log"

        r1 = _run(checkout, home, marker, {
            "POLL_HEARTBEAT_MAX_TICKS": "2",
            "POLL_HEARTBEAT_PATROL_EVERY_N": "3",
        })
        assert r1.returncode == 0, r1.stderr
        assert not marker.exists(), f"patrol must not fire before tick 3: {marker.read_text() if marker.exists() else ''}"
        assert "[patrol-poll]" not in r1.stdout, r1.stdout

        marker2 = tmp / "patrol_marker_2.log"
        r2 = _run(checkout, home, marker2, {
            "POLL_HEARTBEAT_MAX_TICKS": "3",
            "POLL_HEARTBEAT_PATROL_EVERY_N": "3",
        })
        assert r2.returncode == 0, r2.stderr
        assert marker2.exists(), "patrol must fire once patrol_tick reaches the Nth tick"
        calls = marker2.read_text().strip().splitlines()
        assert calls == ["test-role"], calls
        assert "[patrol-poll] checked" not in r2.stdout, r2.stdout


def t_kill_switch_suppresses_and_traces():
    """(b) .on-the-record/patrol-disabled short-circuits the patrol
    invocation entirely and emits its own trace line, even on a
    patrol-due tick."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        (checkout / ".on-the-record").mkdir()
        (checkout / ".on-the-record" / "patrol-disabled").write_text("", encoding="utf-8")
        home = tmp / "home"
        home.mkdir()
        marker = tmp / "patrol_marker.log"

        r = _run(checkout, home, marker, {
            "POLL_HEARTBEAT_MAX_TICKS": "1",
            "POLL_HEARTBEAT_PATROL_EVERY_N": "1",
        })
        assert r.returncode == 0, r.stderr
        assert not marker.exists(), "kill-switch must prevent any patrol_promote invocation"
        assert "[patrol-poll] disabled, skipped" in r.stdout, r.stdout


def t_no_board_role_zero_side_effects():
    """(c) a role with no board issue (fake patrol_promote returns zero
    promotions) results in zero counted promotions and exactly one call
    per role -- no extra invocation, no extra state."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        home = tmp / "home"
        home.mkdir()
        marker = tmp / "patrol_marker.log"

        r = _run(checkout, home, marker, {
            "POLL_HEARTBEAT_MAX_TICKS": "1",
            "POLL_HEARTBEAT_PATROL_EVERY_N": "1",
            "FAKE_PATROL_PROMOTIONS": "0",
        })
        assert r.returncode == 0, r.stderr
        assert marker.read_text().strip().splitlines() == ["test-role"], marker.read_text()
        assert "[patrol-poll] checked" not in r.stdout, r.stdout
        assert "promotion(s)" not in r.stdout, r.stdout


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
