#!/usr/bin/env python3
"""issue-801 phase 2: poll-rearm.sh + stop-poll-rearm.sh — the turn-driven
best-effort self-poll widening (docs/issue-801/proposals/technical-
feasibility.md, candidate 4). Exercises the SAME poll_rearm_arm_if_due()
that directive.sh (UserPromptSubmit) and stop-poll-rearm.sh (Stop) both
call, using a fake spawn.py so no real watchdog/roster machinery runs.

  python3 on-the-record/hooks/test_poll_rearm.py
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
POLL_REARM = HOOKS_DIR / "poll-rearm.sh"
DIRECTIVE = HOOKS_DIR / "directive.sh"
STOP_POLL_REARM = HOOKS_DIR / "stop-poll-rearm.sh"

FAKE_SPAWN_PY = """#!/usr/bin/env python3
import os, sys, time
marker = os.environ["FAKE_SPAWN_MARKER"]
if sys.argv[1:2] == ["poll-due"]:
    sys.exit(0 if os.environ.get("FAKE_POLL_DUE") == "1" else 1)
if sys.argv[1:2] == ["watchdog"]:
    with open(marker, "a", encoding="utf-8") as f:
        f.write("watchdog-ran\\n")
    sys.exit(0)
sys.exit(0)
"""


def _make_checkout(tmp: Path) -> Path:
    checkout = tmp / "checkout"
    checkout.mkdir()
    (checkout / "spawn.py").write_text(FAKE_SPAWN_PY, encoding="utf-8")
    return checkout


def _run_hook(script: Path, checkout: Path, marker: Path, env_extra: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env["FAKE_SPAWN_MARKER"] = str(marker)
    env.pop("CLAUDE_ROLE", None)
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(script)], input="", capture_output=True, text=True, env=env, timeout=15,
    )


def _wait_for_marker(marker: Path, timeout_s: float = 5.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if marker.exists() and marker.read_text().strip():
            return True
        time.sleep(0.1)
    return False


def t_stop_poll_rearm_spawns_watchdog_when_due():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_hook(STOP_POLL_REARM, checkout, marker,
                      {"FAKE_POLL_DUE": "1", "HOME": str(home)})
        assert r.returncode == 0, f"stop-poll-rearm.sh should exit 0: {r.stderr}"
        assert _wait_for_marker(marker), "watchdog was not spawned when poll-due reported due"


def t_stop_poll_rearm_skips_watchdog_when_not_due():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_hook(STOP_POLL_REARM, checkout, marker,
                      {"FAKE_POLL_DUE": "0", "HOME": str(home)})
        assert r.returncode == 0
        # Give any errant background spawn a moment, then assert it never landed.
        time.sleep(0.5)
        assert not (marker.exists() and marker.read_text().strip()), \
            "watchdog must not spawn when poll-due reports not-due"


def t_stop_poll_rearm_noop_inside_role_session():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_hook(STOP_POLL_REARM, checkout, marker,
                      {"FAKE_POLL_DUE": "1", "HOME": str(home), "CLAUDE_ROLE": "implementation"})
        assert r.returncode == 0
        time.sleep(0.5)
        assert not (marker.exists() and marker.read_text().strip()), \
            "a spawned role session must never arm the watchdog itself"


def t_stop_poll_rearm_respects_kill_switch():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_hook(STOP_POLL_REARM, checkout, marker,
                      {"FAKE_POLL_DUE": "1", "HOME": str(home), "ORCHESTRATE_OFF": "1"})
        assert r.returncode == 0
        time.sleep(0.5)
        assert not (marker.exists() and marker.read_text().strip()), \
            "ORCHESTRATE_OFF=1 must suppress the Stop-side re-arm too"


def t_directive_sh_still_spawns_watchdog_on_userpromptsubmit():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _make_checkout(tmp)
        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        r = _run_hook(DIRECTIVE, checkout, marker, {"FAKE_POLL_DUE": "1", "HOME": str(home)})
        assert r.returncode == 0, f"directive.sh should exit 0: {r.stderr}"
        assert _wait_for_marker(marker), \
            "directive.sh's turn-start arm regressed after factoring into poll-rearm.sh"


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
