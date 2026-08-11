"""Tests for deliverable-guard.sh (issue #287, session-role-bind port issue #706).

Invokes the real shipped script via subprocess against fixture stdin
payloads in a disposable directory that looks like a board repo (has
docs/specs/approvers.md).
"""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "deliverable-guard.sh"

SESSION_ID = "sess-706-dg"


def _board_repo(tmp_path):
    r = tmp_path / "target"
    (r / "docs" / "specs").mkdir(parents=True)
    (r / "docs" / "specs" / "approvers.md").write_text("- octocat\n")
    (r / ".git").mkdir()  # root-detection only requires a .git dir present
    return r


def _run(repo, file_path, role_env, session_id=None, state_dir=None):
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "x"},
        "cwd": str(repo),
    }
    if session_id is not None:
        payload["session_id"] = session_id
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    if role_env is None:
        env.pop("CLAUDE_ROLE", None)
    else:
        env["CLAUDE_ROLE"] = role_env
    if state_dir is not None:
        env["OTR_ROLE_BIND_STATE_DIR"] = str(state_dir)
    return subprocess.run(
        ["bash", str(GUARD)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
        timeout=30,
    )


def test_orchestrator_session_writing_deliverable_denied(tmp_path):
    repo = _board_repo(tmp_path)
    r = _run(repo, "docs/issue-1/reports/foo.md", role_env=None)
    assert r.returncode == 2, r.stderr


def test_role_session_writing_own_deliverable_allowed(tmp_path):
    repo = _board_repo(tmp_path)
    r = _run(repo, "docs/issue-1/reports/foo.md", role_env="implementation")
    assert r.returncode == 0, r.stderr


def test_non_deliverable_path_allowed(tmp_path):
    repo = _board_repo(tmp_path)
    r = _run(repo, "scratch/notes.txt", role_env=None)
    assert r.returncode == 0, r.stderr


# --- spoof regression (issue #706): bound snapshot wins over live env ------

def test_unset_spoof_with_bound_role_stays_allowed(tmp_path):
    # session bound to "implementation" at SessionStart, then the session
    # unsets CLAUDE_ROLE before this Write — the hook must still resolve
    # the bound role and treat this as the role's own deliverable write
    # (allow), not silently flip into the orchestrator-only deny branch.
    repo = _board_repo(tmp_path)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / f"{SESSION_ID}.json").write_text(
        json.dumps({"role": "implementation"})
    )
    r = _run(
        repo, "docs/issue-1/reports/foo.md", role_env=None,
        session_id=SESSION_ID, state_dir=state_dir,
    )
    assert r.returncode == 0, r.stderr


def test_no_snapshot_falls_back_to_live_env(tmp_path):
    repo = _board_repo(tmp_path)
    state_dir = tmp_path / "state"
    r = _run(
        repo, "docs/issue-1/reports/foo.md", role_env="implementation",
        session_id=SESSION_ID, state_dir=state_dir,
    )
    assert r.returncode == 0, r.stderr


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
