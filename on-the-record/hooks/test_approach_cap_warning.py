"""Tests for approach-cap-warning.sh (issue #2262's approach-cap warning)."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "approach-cap-warning.sh"


def _run(mode, payload, state_dir, *, cap=None, warn_turns=None,
         role="implementation", orchestrate_off=""):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = orchestrate_off
    env["OTR_APPROACH_CAP_STATE_DIR"] = str(state_dir)
    # no session-role-bind snapshot in these tests -- live-env fallback.
    env["OTR_ROLE_BIND_STATE_DIR"] = str(state_dir / "no-such-role-bind-dir")
    if role:
        env["CLAUDE_ROLE"] = role
    else:
        env.pop("CLAUDE_ROLE", None)
    if cap is not None:
        env["MUSTER_SESSION_MAX_TURNS_RESOLVED"] = str(cap)
    else:
        env.pop("MUSTER_SESSION_MAX_TURNS_RESOLVED", None)
    if warn_turns is not None:
        env["MUSTER_APPROACH_WARNING_TURNS"] = str(warn_turns)
    else:
        env.pop("MUSTER_APPROACH_WARNING_TURNS", None)
    args = ["bash", str(HOOK)]
    if mode is not None:
        args.append(mode)
    return subprocess.run(
        args, input=json.dumps(payload), capture_output=True, text=True,
        env=env, timeout=20,
    )


def _bump(state_dir, session_id, cap, n, warn_turns=20, role="implementation"):
    """Fire `post` n times for one session — the counter this hook keys
    its warning-window check off of."""
    for _ in range(n):
        r = _run("post", {"session_id": session_id}, state_dir, cap=cap,
                  warn_turns=warn_turns, role=role)
        assert r.returncode == 0
    return session_id


def t_invalid_mode_is_a_distinct_wiring_error():
    # hooks.json only ever calls this with "pre"/"post" -- an unrecognized
    # $1 is a real registration bug, not a fail-open environment gap, so
    # it gets its own exit code instead of masquerading as a normal no-op.
    with tempfile.TemporaryDirectory() as td:
        state_dir = Path(td)
        r = _run("bogus", {"session_id": "s1"}, state_dir, cap=30)
        assert r.returncode == 1


def t_no_cap_env_is_noop_on_pre_and_post():
    # #2262 acceptance "empty state": no MUSTER_SESSION_MAX_TURNS_RESOLVED
    # (uncapped/unresolved spawn) -> both modes are silent no-ops.
    with tempfile.TemporaryDirectory() as td:
        state_dir = Path(td)
        session_id = "s-nocap"
        r_post = _run("post", {"session_id": session_id}, state_dir, cap=None)
        assert r_post.returncode == 0
        assert r_post.stdout == ""
        r_pre = _run("pre", {"session_id": session_id}, state_dir, cap=None)
        assert r_pre.returncode == 0
        assert r_pre.stdout == ""


def t_pre_silent_far_from_the_cap():
    # #2262 acceptance "empty state": a session nowhere near its budget
    # sees no warning and no behavior change.
    with tempfile.TemporaryDirectory() as td:
        state_dir = Path(td)
        session_id = _bump(state_dir, "s-far", cap=200, n=5, warn_turns=20)
        r = _run("pre", {"session_id": session_id}, state_dir, cap=200,
                  warn_turns=20)
        assert r.returncode == 0
        assert r.stdout == ""


def t_pre_injects_convergence_warning_inside_the_window():
    # remaining = cap(30) - count(15) = 15, inside (0, warn_turns(20)] ->
    # the additionalContext nudge fires.
    with tempfile.TemporaryDirectory() as td:
        state_dir = Path(td)
        session_id = _bump(state_dir, "s-window", cap=30, n=15, warn_turns=20)
        r = _run("pre", {"session_id": session_id}, state_dir, cap=30,
                  warn_turns=20)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "converge" in ctx.lower()
        assert "15" in ctx and "30" in ctx


def t_pre_silent_once_past_the_cap_into_the_wrap_up_allowance():
    # remaining <= 0 (the session is already spending the wrap-up
    # allowance pipeline.py adds on top of the resolved cap) -- this hook
    # never blocks a tool call, so it stays silent rather than nag past
    # the point convergence should already be underway.
    with tempfile.TemporaryDirectory() as td:
        state_dir = Path(td)
        session_id = _bump(state_dir, "s-past", cap=30, n=31, warn_turns=20)
        r = _run("pre", {"session_id": session_id}, state_dir, cap=30,
                  warn_turns=20)
        assert r.returncode == 0
        assert r.stdout == ""


def t_pre_silent_without_a_bound_role():
    # No role bound (orchestrator session) -- pipeline.py never sets
    # MUSTER_SESSION_MAX_TURNS_RESOLVED for the orchestrator in the first
    # place, but this is a second, independent guard against warning a
    # session this feature isn't scoped to.
    with tempfile.TemporaryDirectory() as td:
        state_dir = Path(td)
        session_id = "s-norole"
        for _ in range(15):
            r = _run("post", {"session_id": session_id}, state_dir, cap=30,
                      warn_turns=20, role=None)
            assert r.returncode == 0
        r = _run("pre", {"session_id": session_id}, state_dir, cap=30,
                  warn_turns=20, role=None)
        assert r.returncode == 0
        assert r.stdout == ""
