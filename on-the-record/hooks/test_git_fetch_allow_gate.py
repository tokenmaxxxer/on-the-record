"""Tests for git-fetch-allow-gate.sh (issue #894 finding #1 fix).

Mirrors test_merge_allow_gate.py / test_spawn_allow_gate.py's structure and
env-injection technique, adapted to `git fetch` invocations.

  python3 on-the-record/hooks/test_git_fetch_allow_gate.py
"""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "on-the-record" / "hooks" / "git-fetch-allow-gate.sh"


def _run(target: Path, command: str,
          extra_env: dict | None = None) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(target),
        "session_id": "test-session",
    })
    env = dict(os.environ)
    env.pop("CLAUDE_ROLE", None)
    env.pop("OTR_ROLE_BIND_STATE_DIR", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(["bash", str(SCRIPT)], cwd=target, input=payload,
                           capture_output=True, text=True, env=env)


def _allow_decision(stdout: str) -> str | None:
    stdout = stdout.strip()
    if not stdout:
        return None
    data = json.loads(stdout)
    return data["hookSpecificOutput"]["permissionDecision"]


def t_orchestrator_git_fetch_gets_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, "git fetch")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) == "allow", repr(r.stdout)


def t_git_fetch_with_remote_and_refspec_gets_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, "git fetch origin main")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) == "allow", repr(r.stdout)


def t_cd_prefixed_git_fetch_gets_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, f"cd {target} && git fetch origin")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) == "allow", repr(r.stdout)


def t_role_session_never_gets_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, "git fetch", extra_env={"CLAUDE_ROLE": "implementation"})
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_non_fetch_git_command_is_untouched(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, "git push --force")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_unquoted_chained_command_after_fetch_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, "git fetch && rm -rf /tmp/x")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_chain_prepended_with_semicolon_is_not_allowed(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, "evil ; git fetch")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_chain_appended_with_pipe_is_not_allowed(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, "git fetch | evil")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_double_quoted_command_substitution_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, 'git fetch "$(touch /tmp/PWNED_MARKER)"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_backtick_command_substitution_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, 'git fetch "`touch /tmp/PWNED_MARKER`"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_command_substitution_hidden_in_cd_prefix_dir_slot_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, 'cd $(touch${IFS}/tmp/PWNED_MARKER) && git fetch')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_kill_switch_suppresses_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    r = _run(target, "git fetch", extra_env={"ORCHESTRATE_OFF": "1"})
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


if __name__ == "__main__":
    import tempfile
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        with tempfile.TemporaryDirectory() as td:
            t(Path(td))
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
