"""Tests for role-test-claim-guard.sh (issue #457 Group C porting)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "role-test-claim-guard.sh"


def _run(message, role="implementation"):
    payload = json.dumps({"last_assistant_message": message})
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    if role:
        env["CLAUDE_ROLE"] = role
    else:
        env.pop("CLAUDE_ROLE", None)
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def t_orchestrator_session_skipped(tmp_path):
    r = _run("all tests pass\n```\nSKIPPED test_x.py:1: reason\n```", role=None)
    assert r.returncode == 0
    assert r.stdout == ""


def t_no_test_output_is_fine():
    r = _run("Implemented the feature and wrote docs.")
    assert r.returncode == 0


def t_skip_conflated_with_clean_pass_flagged():
    msg = ("모두 통과했습니다.\n```\n"
           "SKIPPED test_x.py:10: dependency missing\n"
           "3 passed\n```")
    r = _run(msg)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "issue #334" in out["hookSpecificOutput"]["additionalContext"]


def t_skip_acknowledged_is_not_flagged():
    msg = ("2 passed, 1 skipped (dependency missing).\n```\n"
           "SKIPPED test_x.py:10: dependency missing\n"
           "2 passed\n```")
    r = _run(msg)
    assert r.returncode == 0
    assert r.stdout == ""


def t_hand_typed_count_mismatch_flagged():
    msg = "5개가 통과했습니다.\n```\n3 passed\n```"
    r = _run(msg)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "issue #435" in out["hookSpecificOutput"]["additionalContext"]


def t_hand_typed_count_match_passes():
    msg = "3개가 통과했습니다.\n```\n3 passed\n```"
    r = _run(msg)
    assert r.returncode == 0
    assert r.stdout == ""


def t_malformed_payload_is_allowed():
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env["CLAUDE_ROLE"] = "implementation"
    r = subprocess.run(["bash", str(GUARD)], input="not json",
                        capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 0


# --- unset-spoof regression (issue #706) ---

SESSION_ID = "sess-706-rtcg"


def _run_with_bind(message, bind_state_dir, bind_role, live_role=None,
                    session_id=SESSION_ID):
    payload = json.dumps({"last_assistant_message": message, "session_id": session_id})
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    if live_role:
        env["CLAUDE_ROLE"] = live_role
    else:
        env.pop("CLAUDE_ROLE", None)
    if bind_role is not None:
        bind_state_dir.mkdir(parents=True, exist_ok=True)
        (bind_state_dir / f"{session_id}.json").write_text(json.dumps({"role": bind_role}))
    env["OTR_ROLE_BIND_STATE_DIR"] = str(bind_state_dir)
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def t_unset_spoof_with_bound_role_still_checked(tmp_path):
    # session bound to "implementation" at SessionStart, then unsets
    # CLAUDE_ROLE before this Stop -- the hook must still resolve the
    # bound role and apply the role-only test-claim check, not silently
    # skip into the "not a role session" branch.
    msg = "5개가 통과했습니다.\n```\n3 passed\n```"
    r = _run_with_bind(msg, tmp_path / "bind", "implementation", live_role=None)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "issue #435" in out["hookSpecificOutput"]["additionalContext"]


def t_no_snapshot_falls_back_to_live_env(tmp_path):
    msg = "5개가 통과했습니다.\n```\n3 passed\n```"
    r = _run_with_bind(msg, tmp_path / "bind", None, live_role="implementation")
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "issue #435" in out["hookSpecificOutput"]["additionalContext"]
