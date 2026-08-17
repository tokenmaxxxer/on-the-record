"""Tests for stop-gate.sh (issue #411's approval-shape structural check)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "stop-gate.sh"


def _run(message, role=None, orchestrate_off="", stop_hook_active=False):
    payload = json.dumps({
        "last_assistant_message": message,
        "stop_hook_active": stop_hook_active,
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = orchestrate_off
    if role:
        env["CLAUDE_ROLE"] = role
    else:
        env.pop("CLAUDE_ROLE", None)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


APPROVAL_MISSING_RISK = "Requesting approve for #411 — this will change stop-gate.sh."
APPROVAL_COMPLIANT = (
    "Requesting approve for #411 — this will change stop-gate.sh. "
    "Risk: a false positive could misfire on an unusual reply."
)


def t_missing_clause_is_flagged():
    r = _run(APPROVAL_MISSING_RISK)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "risk/tradeoff statement" in out["hookSpecificOutput"]["additionalContext"]


def t_all_clauses_present_is_silent():
    r = _run(APPROVAL_COMPLIANT)
    assert r.returncode == 0
    assert r.stdout == ""


def t_non_approval_reply_is_silent():
    r = _run("Here is a status update on the current task, nothing to approve.")
    assert r.returncode == 0
    assert r.stdout == ""


def t_role_session_is_noop():
    r = _run(APPROVAL_MISSING_RISK, role="qa")
    assert r.returncode == 0
    assert r.stdout == ""


def t_orchestrate_off_is_noop():
    r = _run(APPROVAL_MISSING_RISK, orchestrate_off="1")
    assert r.returncode == 0
    assert r.stdout == ""


def t_malformed_payload_fails_closed():
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env.pop("CLAUDE_ROLE", None)
    r = subprocess.run(["bash", str(HOOK)], input="not json",
                        capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 2


def t_stop_hook_active_emits_nothing_for_missing_clause():
    # issue #1725: a stop_hook_active turn must emit nothing at all, even
    # for a scenario that otherwise flags a missing clause.
    r = _run(APPROVAL_MISSING_RISK, stop_hook_active=True)
    assert r.returncode == 0
    assert r.stdout == ""
