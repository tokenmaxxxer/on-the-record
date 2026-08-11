"""Tests for session-role-bind.sh (issue #698).

Invokes the real shipped script via subprocess against fixture SessionStart
payloads, checking the resulting state file under a scratch
OTR_ROLE_BIND_STATE_DIR.

Run: python3 -m pytest on-the-record/hooks/test_session_role_bind.py -q
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "session-role-bind.sh"

SESSION_ID = "sess-abc123"


def _run(state_dir: Path, payload: dict, role: str | None):
    env = dict(os.environ)
    env["OTR_ROLE_BIND_STATE_DIR"] = str(state_dir)
    env.pop("ORCHESTRATE_OFF", None)
    if role is None:
        env.pop("CLAUDE_ROLE", None)
    else:
        env["CLAUDE_ROLE"] = role
    r = subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
    return r


def _snapshot(state_dir: Path, session_id: str = SESSION_ID):
    p = state_dir / f"{session_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def test_role_set_and_session_id_present_writes_snapshot(tmp_path):
    state_dir = tmp_path / "state"
    _run(state_dir, {"session_id": SESSION_ID}, role="implementation")
    assert _snapshot(state_dir) == {"role": "implementation"}


def test_role_unset_noops(tmp_path):
    state_dir = tmp_path / "state"
    _run(state_dir, {"session_id": SESSION_ID}, role=None)
    assert _snapshot(state_dir) is None


def test_session_id_missing_noops(tmp_path):
    state_dir = tmp_path / "state"
    _run(state_dir, {}, role="implementation")
    assert _snapshot(state_dir) is None


def test_replay_does_not_overwrite_existing_snapshot(tmp_path):
    state_dir = tmp_path / "state"
    _run(state_dir, {"session_id": SESSION_ID}, role="implementation")
    assert _snapshot(state_dir) == {"role": "implementation"}

    # A second SessionStart within the same session_id, now claiming a
    # different role, must not rebind — first observation wins.
    _run(state_dir, {"session_id": SESSION_ID}, role="hunt")
    assert _snapshot(state_dir) == {"role": "implementation"}
