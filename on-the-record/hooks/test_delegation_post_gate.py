"""Tests for delegation-post-gate.sh (issue #707).

Invokes the real shipped script via subprocess against fixture stdin
payloads shaped like the PreToolUse(Bash) hook contract. Covers the
self-approval invariant: a role-bound session (matching or not matching
the citation's own issue/role) is refused when it tries to POST a
"VIA DELEGATION" APPROVE citation itself, regardless of whether the cited
delegation record would otherwise validate — only an orchestrator session
(no CLAUDE_ROLE bound) may post one.

Run: python3 -m pytest on-the-record/hooks/test_delegation_post_gate.py -q
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "delegation-post-gate.sh"

CITATION = "APPROVE issue-707/implementation VIA DELEGATION issue-707/implementation"
CMD = f'gh issue comment 707 --body "{CITATION}"'


def _run(cmd, role=None, session_id=None, bound_role=None, state_dir=None):
    payload = {"tool_name": "Bash", "tool_input": {"command": cmd}}
    if session_id:
        payload["session_id"] = session_id
    env = dict(os.environ)
    if role is None:
        env.pop("CLAUDE_ROLE", None)
    else:
        env["CLAUDE_ROLE"] = role
    env.pop("ORCHESTRATE_OFF", None)
    if state_dir is not None:
        env["OTR_ROLE_BIND_STATE_DIR"] = str(state_dir)
        if bound_role is not None:
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / f"{session_id}.json").write_text(json.dumps({"role": bound_role}))
    return subprocess.run(
        ["bash", str(GUARD)], input=json.dumps(payload), capture_output=True,
        text=True, env=env, timeout=30,
    )


def test_orchestrator_session_allowed(tmp_path):
    r = _run(CMD, role=None)
    assert r.returncode == 0, r.stderr


def test_role_bound_session_refused_matching_role(tmp_path):
    r = _run(CMD, role="implementation")
    assert r.returncode == 2, r.stderr
    assert "self_approval_violation_count" in r.stderr


def test_role_bound_session_refused_unrelated_role(tmp_path):
    # the after-proposal hunt's finding: an unrelated role must also be
    # refused, not only a role matching the citation's own branch.
    r = _run(CMD, role="qa")
    assert r.returncode == 2, r.stderr


def test_bound_snapshot_wins_over_live_env_spoof(tmp_path):
    state_dir = tmp_path / "state"
    r = _run(CMD, role="", session_id="sess-1", bound_role="implementation", state_dir=state_dir)
    assert r.returncode == 2, r.stderr


def test_non_citation_comment_allowed(tmp_path):
    r = _run('gh issue comment 707 --body "looks good"', role="implementation")
    assert r.returncode == 0, r.stderr


def test_non_gh_command_allowed(tmp_path):
    r = _run("echo hello", role="implementation")
    assert r.returncode == 0, r.stderr


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
