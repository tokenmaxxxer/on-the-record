"""Tests for retry-loop-bound.sh (issue #507).

Fixture shape reconstructs the issue-474 identical-retry log cited by
#505's mining (docs/issue-505/reports/implementation.md:26-27,47-70) --
25 identical board-gate.sh R4 refusals of a `docs/issue-416/...` write
from an `issue-474/implementation` session -- using board-gate.sh:512's
exact message template (`docs/issue-507/reports/implementation/survey.md`
confirms the template text by direct read; no raw .log file is available
in this checkout to replay).

Red baseline (pre-hook, undocumented before this change): nothing bounds
the loop -- the hook did not exist, so a `pre` payload after any number
of identical `post` denials produced no output and no abort; the 25th
(or 52nd) identical retry proceeded exactly like the 1st. Green (this
file): the K-th identical denial's next attempt carries
`additionalContext`, the 2K-th is denied outright.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "retry-loop-bound.sh"

SESSION = "sess-issue474"
TOOL = "Write"
TARGET = "docs/issue-416/reports/implementation.md"

DENY_REASON = (
    "writing docs/issue-416/ requires branch issue-474/implementation "
    "(current: issue-474/implementation). Every role writes its own "
    "board only from its own issue branch -- never a direct write from "
    "another branch. (contract v3 s10)"
)
DENY_TOOL_RESPONSE = (
    "PreToolUse:Write hook error: [board-gate.sh: refused — " + DENY_REASON + "]"
)


def _run(payload, state_dir, k=5):
    env = dict(os.environ)
    env["OTR_RETRY_BOUND_STATE_DIR"] = str(state_dir)
    env["OTR_RETRY_BOUND_K"] = str(k)
    env.pop("CLAUDE_ROLE", None)
    env["ORCHESTRATE_OFF"] = ""
    mode = payload.pop("_mode")
    return subprocess.run(
        ["bash", str(HOOK), mode],
        input=json.dumps(payload), capture_output=True, text=True, env=env,
        timeout=20,
    )


def _post(state_dir, target=TARGET, k=5, tool_name=TOOL, input_key="file_path"):
    return _run(
        {
            "_mode": "post",
            "session_id": SESSION,
            "tool_name": tool_name,
            "tool_input": {input_key: target},
            "tool_response": DENY_TOOL_RESPONSE,
        },
        state_dir, k,
    )


def _pre(state_dir, target=TARGET, k=5, tool_name=TOOL, input_key="file_path"):
    return _run(
        {
            "_mode": "pre",
            "session_id": SESSION,
            "tool_name": tool_name,
            "tool_input": {input_key: target},
        },
        state_dir, k,
    )


def t_zero_denials_pre_is_silent():
    with tempfile.TemporaryDirectory() as td:
        r = _pre(td)
        assert r.returncode == 0
        assert r.stdout == ""


def t_below_k_denials_pre_is_silent():
    with tempfile.TemporaryDirectory() as td:
        for _ in range(4):
            assert _post(td, k=5).returncode == 0
        r = _pre(td, k=5)
        assert r.returncode == 0
        assert r.stdout == ""


def t_kth_denial_triggers_corrective_context():
    with tempfile.TemporaryDirectory() as td:
        for _ in range(5):
            assert _post(td, k=5).returncode == 0
        r = _pre(td, k=5)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "denied 5 times" in ctx
        assert "requires branch issue-474/implementation" in ctx


def t_25_identical_denials_issue_474_shape_aborts_at_2k():
    """Reproduces #505's issue-474 citation: 25 identical R4 refusals."""
    with tempfile.TemporaryDirectory() as td:
        k = 5
        nudged = False
        for i in range(1, 26):
            assert _post(td, k=k).returncode == 0
            r = _pre(td, k=k)
            if i >= 2 * k:
                assert r.returncode == 2, "expected abort by denial #%d" % i
                assert "aborted" in r.stderr
                assert str(i if i == 2 * k else 2 * k) in r.stderr or (
                    "denied" in r.stderr
                )
            elif i >= k:
                assert r.returncode == 0
                nudged = True
        assert nudged


def t_non_identical_denials_never_trip_threshold():
    with tempfile.TemporaryDirectory() as td:
        for n in range(10):
            assert _post(td, target="docs/issue-%d/x.md" % n, k=5).returncode == 0
            r = _pre(td, target="docs/issue-%d/x.md" % n, k=5)
            assert r.returncode == 0
            assert r.stdout == ""


def t_2k_denial_is_terminal_deny():
    with tempfile.TemporaryDirectory() as td:
        k = 3
        for _ in range(2 * k):
            assert _post(td, k=k).returncode == 0
        r = _pre(td, k=k)
        assert r.returncode == 2
        assert TARGET in r.stderr


# --- Bash fatigue-allow scope regression (issue #846) ---

BASH_CMD = 'cd $(touch /tmp/pwned_poc_846)&&python3 spawn.py implementation "task" --issue 834'


def t_bash_kth_denial_no_longer_carries_permission_decision():
    """issue #846 / PR #843 3-step repro: an unrelated, state-dependent gate
    denies an identical Bash command 5 times, then this hook's own K-tier
    nudge must not independently supply permissionDecision: allow for a
    Bash call -- merge-allow-gate.sh/spawn-allow-gate.sh may be withholding
    their own allow for that exact command shape, and this hook's allow
    would be the only permission signal left once the unrelated gate stops
    firing. additionalContext (the corrective nudge) must still appear.
    """
    with tempfile.TemporaryDirectory() as td:
        for _ in range(5):
            assert _post(
                td, target=BASH_CMD, k=5, tool_name="Bash", input_key="command"
            ).returncode == 0
        r = _pre(td, target=BASH_CMD, k=5, tool_name="Bash", input_key="command")
        assert r.returncode == 0
        out = json.loads(r.stdout)
        hso = out["hookSpecificOutput"]
        assert "permissionDecision" not in hso
        assert "permissionDecisionReason" not in hso
        assert "denied 5 times" in hso["additionalContext"]


def t_write_kth_denial_still_carries_permission_decision():
    """Non-Bash tool_name keeps #507's shipped allow-with-context behavior
    unchanged -- the scope-out is Bash-only, not global."""
    with tempfile.TemporaryDirectory() as td:
        for _ in range(5):
            assert _post(td, k=5).returncode == 0
        r = _pre(td, k=5)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"


# --- unset-spoof regression (issue #706) ---

def _post_with_bind(state_dir, bind_state_dir, bind_role, k=5):
    env = dict(os.environ)
    env["OTR_RETRY_BOUND_STATE_DIR"] = str(state_dir)
    env["OTR_RETRY_BOUND_K"] = str(k)
    env.pop("CLAUDE_ROLE", None)
    env["ORCHESTRATE_OFF"] = ""
    if bind_role is not None:
        bind_state_dir.mkdir(parents=True, exist_ok=True)
        (bind_state_dir / f"{SESSION}.json").write_text(json.dumps({"role": bind_role}))
    env["OTR_ROLE_BIND_STATE_DIR"] = str(bind_state_dir)
    return subprocess.run(
        ["bash", str(HOOK), "post"],
        input=json.dumps({
            "session_id": SESSION, "tool_name": TOOL,
            "tool_input": {"file_path": TARGET},
            "tool_response": DENY_TOOL_RESPONSE,
        }),
        capture_output=True, text=True, env=env, timeout=20,
    )


def t_unset_spoof_with_bound_role_never_counts(tmp_path):
    # session bound to "implementation" at SessionStart, then unsets
    # CLAUDE_ROLE before every retried tool call -- the hook must still
    # resolve the bound role and skip counting (role sessions are outside
    # this bound), not silently start applying the orchestrator-only bound.
    state_dir = tmp_path / "state"
    bind_dir = tmp_path / "bind"
    for _ in range(10):
        r = _post_with_bind(state_dir, bind_dir, "implementation", k=5)
        assert r.returncode == 0
    r = _pre(state_dir, k=5)
    assert r.returncode == 0
    assert r.stdout == ""


def t_orchestrate_off_is_silent():
    with tempfile.TemporaryDirectory() as td:
        for _ in range(6):
            env_post = dict(os.environ)
            env_post["OTR_RETRY_BOUND_STATE_DIR"] = str(td)
            env_post["OTR_RETRY_BOUND_K"] = "5"
            env_post["ORCHESTRATE_OFF"] = "1"
            env_post.pop("CLAUDE_ROLE", None)
            subprocess.run(
                ["bash", str(HOOK), "post"],
                input=json.dumps({
                    "session_id": SESSION, "tool_name": TOOL,
                    "tool_input": {"file_path": TARGET},
                    "tool_response": DENY_TOOL_RESPONSE,
                }),
                capture_output=True, text=True, env=env_post, timeout=20,
            )
        env_pre = dict(os.environ)
        env_pre["OTR_RETRY_BOUND_STATE_DIR"] = str(td)
        env_pre["OTR_RETRY_BOUND_K"] = "5"
        env_pre["ORCHESTRATE_OFF"] = "1"
        env_pre.pop("CLAUDE_ROLE", None)
        r = subprocess.run(
            ["bash", str(HOOK), "pre"],
            input=json.dumps({
                "session_id": SESSION, "tool_name": TOOL,
                "tool_input": {"file_path": TARGET},
            }),
            capture_output=True, text=True, env=env_pre, timeout=20,
        )
        assert r.returncode == 0
        assert r.stdout == ""
