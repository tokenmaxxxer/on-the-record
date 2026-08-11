"""Tests for gh-write-allow-gate.sh (issue #856).

Mirrors test_spawn_allow_gate.py's structure and env-injection technique,
adapted to the gh issue/pr write verbs (create/comment/close) instead of
spawn.py invocations.

  python3 on-the-record/hooks/test_gh_write_allow_gate.py
"""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "on-the-record" / "hooks" / "gh-write-allow-gate.sh"

# A minimal stand-in deny gate, in the exact JSON/exit-code shape a real
# PreToolUse deny hook (e.g. contract-guard.sh, pr-preflight.sh) uses: it
# denies any `gh issue close`/`gh pr close` on principle, independent of
# what any allow-gate on the same Bash call decides. It exists only to
# prove gh-write-allow-gate.sh's own composition claim — this gate never
# emits "deny" itself, so a real deny gate's exit-code-2 stands on its own
# regardless of order — without coupling the test to another gate's
# unrelated internal preconditions.
_STUB_DENY_GATE = '''#!/usr/bin/env bash
set -uo pipefail
payload="$(cat)"
STUB_PAYLOAD="$payload" python3 -c "
import json, os, sys
e = json.loads(os.environ.get('STUB_PAYLOAD', ''))
cmd = (e.get('tool_input') or {}).get('command', '')
if 'gh issue close' in cmd or 'gh pr close' in cmd:
    sys.stderr.write('stub-deny-gate: closing issues/PRs is denied on principle\\n')
    sys.exit(2)
sys.exit(0)
"
'''


def _run(command: str, extra_env: dict | None = None,
          cwd: Path | None = None) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(cwd) if cwd else os.getcwd(),
        "session_id": "test-session",
    })
    env = dict(os.environ)
    env.pop("CLAUDE_ROLE", None)
    env.pop("OTR_ROLE_BIND_STATE_DIR", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(["bash", str(SCRIPT)], input=payload,
                           capture_output=True, text=True, env=env)


def _decision(stdout: str) -> str | None:
    stdout = stdout.strip()
    if not stdout:
        return None
    data = json.loads(stdout)
    return data["hookSpecificOutput"]["permissionDecision"]


def t_orchestrator_issue_create_gets_allow(tmp_path: Path):
    r = _run('gh issue create --title "t" --body "b"')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) == "allow", repr(r.stdout)


def t_orchestrator_issue_comment_gets_allow(tmp_path: Path):
    r = _run('gh issue comment 12 --body "b"')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) == "allow", repr(r.stdout)


def t_orchestrator_pr_comment_gets_allow(tmp_path: Path):
    r = _run('gh pr comment 12 --body "b"')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) == "allow", repr(r.stdout)


def t_orchestrator_issue_close_gets_allow(tmp_path: Path):
    r = _run('gh issue close 12')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) == "allow", repr(r.stdout)


def t_orchestrator_pr_close_gets_allow(tmp_path: Path):
    r = _run('gh pr close 12')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) == "allow", repr(r.stdout)


def t_cd_prefixed_invocation_gets_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(f'cd {target} && gh issue comment 12 --body "b"')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) == "allow", repr(r.stdout)


def t_role_session_never_gets_allow(tmp_path: Path):
    r = _run('gh issue create --title "t" --body "b"',
             extra_env={"CLAUDE_ROLE": "implementation"})
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) is None, repr(r.stdout)


def t_sensitive_literal_in_body_does_not_falsely_allow_or_block(tmp_path: Path):
    # The decision is keyed on command shape only, never on the --body
    # text — a body carrying gate-design vocabulary must still allow
    # (not falsely block), and must not need any special-casing to do so
    # (not falsely "extra" allow either — same shape, same outcome).
    sensitive = ('gh issue comment 12 --body '
                 '"merge-allow-gate default-on permissionDecision '
                 'landing_readiness deny gh pr merge"')
    r = _run(sensitive)
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) == "allow", repr(r.stdout)


def t_unquoted_chained_command_after_verb_is_unreached(tmp_path: Path):
    r = _run('gh issue create --title "t" && rm -rf /tmp/x')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) is None, repr(r.stdout)


def t_chain_prepended_with_semicolon_is_not_allowed(tmp_path: Path):
    r = _run('evil ; gh issue create --title "t"')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) is None, repr(r.stdout)


def t_chain_appended_with_pipe_is_not_allowed(tmp_path: Path):
    r = _run('gh pr comment 12 --body "b" | evil')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) is None, repr(r.stdout)


def t_double_quoted_command_substitution_is_unreached(tmp_path: Path):
    r = _run('gh issue comment 12 --body "$(touch /tmp/PWNED_MARKER)"')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) is None, repr(r.stdout)


def t_backtick_command_substitution_is_unreached(tmp_path: Path):
    r = _run('gh issue comment 12 --body "`touch /tmp/PWNED_MARKER`"')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) is None, repr(r.stdout)


def t_single_quoted_shell_operator_in_body_does_not_trip_chain_check(tmp_path: Path):
    r = _run("gh issue comment 12 --body 'build A && B; also C | D'")
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) == "allow", repr(r.stdout)


def t_non_gh_command_is_untouched(tmp_path: Path):
    r = _run('git status')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) is None, repr(r.stdout)


def t_gh_pr_merge_is_not_this_gates_verb(tmp_path: Path):
    # merge is a distinct, more consequential verb owned by
    # merge-allow-gate.sh; this gate must not also match it.
    r = _run('gh pr merge 12')
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) is None, repr(r.stdout)


def t_kill_switch_suppresses_allow(tmp_path: Path):
    r = _run('gh issue create --title "t"', extra_env={"ORCHESTRATE_OFF": "1"})
    assert r.returncode == 0, r.stderr
    assert _decision(r.stdout) is None, repr(r.stdout)


def t_deny_gate_still_wins_when_both_fire(tmp_path: Path):
    # Safe-composition check (same proven precedence as #816): this gate
    # only ever emits "allow" or no JSON — it never emits "deny" itself —
    # so a separately-firing deny gate on the identical Bash call still
    # returns its own exit-code-2 verdict, independent of what this gate
    # decided moments earlier in the same PreToolUse chain.
    command = 'gh issue close 12'

    allow_r = _run(command)
    assert _decision(allow_r.stdout) == "allow", repr(allow_r.stdout)

    stub_path = tmp_path / "stub-deny-gate.sh"
    stub_path.write_text(_STUB_DENY_GATE)
    stub_path.chmod(0o755)

    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": os.getcwd(),
        "session_id": "test-session",
    })
    deny_r = subprocess.run(["bash", str(stub_path)], input=payload,
                             capture_output=True, text=True)
    assert deny_r.returncode == 2, (deny_r.returncode, deny_r.stdout, deny_r.stderr)


if __name__ == "__main__":
    import tempfile
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        with tempfile.TemporaryDirectory() as td:
            t(Path(td))
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
