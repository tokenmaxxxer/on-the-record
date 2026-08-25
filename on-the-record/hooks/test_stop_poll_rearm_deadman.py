"""issue #2140 (#2101 mechanism 4): the Stop poll hook is the EXTERNAL
caller of `spawn.py deadman-check` — the watch layer's own death must be
observable from outside it. Unit-tests the hook script end-to-end with a
synthetic STATE_ROOT: a stale coverage-OK marker makes the hook's output
carry the DEAD advisory; a fresh (or absent) marker stays quiet. The
invocation is advisory-only (hook always exits 0) and is recorded in the
fires-log.

  python3 -m pytest on-the-record/hooks/test_stop_poll_rearm_deadman.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / "on-the-record" / "hooks" / "stop-poll-rearm.sh"

DEAD_NEEDLE = "WATCH LAYER ITSELF IS DEAD"
FIRES_NEEDLE = "Stop stop-poll-rearm.sh deadman-check"


def _run_hook(tmp_path: Path, state_root: Path) -> subprocess.CompletedProcess:
    cwd = tmp_path / "cwd"
    cwd.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(REPO_ROOT)
    env["MUSTER_STATE_ROOT"] = str(state_root)
    env["HOME"] = str(tmp_path / "home")
    env.pop("CLAUDE_ROLE", None)
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(
        ["bash", str(HOOK)], input="", capture_output=True, text=True,
        env=env, timeout=60, cwd=str(cwd),
    )


def _write_marker(state_root: Path, age_seconds: float) -> None:
    state_root.mkdir(parents=True, exist_ok=True)
    marker = state_root / "watch-coverage-ok"
    ts = time.time() - age_seconds
    marker.write_text(json.dumps({"ts": ts}))
    os.utime(marker, (ts, ts))


def test_stale_marker_surfaces_dead_advisory_and_fires_log(tmp_path):
    state_root = tmp_path / "state"
    # default threshold: 120s x 5 intervals = 600s; go well past it.
    _write_marker(state_root, age_seconds=3600)
    r = _run_hook(tmp_path, state_root)
    assert r.returncode == 0, r.stderr
    assert DEAD_NEEDLE in r.stdout
    fires = (tmp_path / "cwd" / ".orchestrate-hook-fires" / "unknown.log").read_text()
    assert FIRES_NEEDLE in fires


def test_fresh_marker_stays_quiet_but_still_recorded(tmp_path):
    state_root = tmp_path / "state"
    _write_marker(state_root, age_seconds=1)
    r = _run_hook(tmp_path, state_root)
    assert r.returncode == 0, r.stderr
    assert DEAD_NEEDLE not in r.stdout
    fires = (tmp_path / "cwd" / ".orchestrate-hook-fires" / "unknown.log").read_text()
    assert FIRES_NEEDLE in fires


def test_no_marker_ever_is_no_baseline_no_advisory(tmp_path):
    state_root = tmp_path / "state"
    state_root.mkdir(parents=True, exist_ok=True)
    r = _run_hook(tmp_path, state_root)
    assert r.returncode == 0, r.stderr
    assert DEAD_NEEDLE not in r.stdout
