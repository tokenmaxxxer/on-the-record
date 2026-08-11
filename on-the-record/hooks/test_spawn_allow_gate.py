"""Tests for spawn-allow-gate.sh (issue #810 SCOPE EXTENSION 2).

Mirrors test_merge_allow_gate.py's structure and env-injection technique,
adapted to spawn.py invocations instead of `gh pr merge`.

  python3 on-the-record/hooks/test_spawn_allow_gate.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "on-the-record" / "hooks" / "spawn-allow-gate.sh"


def _make_checkout(tmp_path: Path) -> Path:
    checkout = tmp_path / "checkout"
    checkout.mkdir(parents=True)
    (checkout / "spawn.py").write_text("# stub\n")
    return checkout


def _run(target: Path, checkout: Path, command: str,
          extra_env: dict | None = None) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(target),
        "session_id": "test-session",
    })
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
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


def t_orchestrator_spawn_invocation_gets_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, 'python3 spawn.py review "PR 12 를 리뷰해라"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) == "allow", repr(r.stdout)


def t_sensitive_literal_in_task_text_does_not_block_allow(tmp_path: Path):
    # This is the exact live-observed failure mode (SCOPE EXTENSION 2): the
    # classifier blocked on argument TEXT containing forge-verb/allow-design
    # vocabulary. The allow decision must not key on that text at all.
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout,
             'python3 spawn.py implementation "merge-allow-gate default-on '
             'permissionDecision gh pr merge landing_readiness"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) == "allow", repr(r.stdout)


def t_cd_prefixed_spawn_invocation_gets_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout,
             f'cd {checkout} && python3 spawn.py watch --issue 810')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) == "allow", repr(r.stdout)


def t_consult_invocation_gets_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, 'python3 spawn.py consult review "질문"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) == "allow", repr(r.stdout)


def t_role_session_never_gets_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, 'python3 spawn.py review "task"',
             extra_env={"CLAUDE_ROLE": "implementation"})
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_unquoted_chained_command_after_spawn_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, 'python3 spawn.py review "task" && rm -rf /tmp/x')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_single_quoted_shell_operator_in_task_text_does_not_trip_chain_check(tmp_path: Path):
    # Only single quotes fully neutralize &&/;/| — this is the case that is
    # actually safe to allow through unexamined.
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout,
             "python3 spawn.py review 'build A && B; also C | D'")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) == "allow", repr(r.stdout)


def t_double_quoted_command_substitution_is_unreached(tmp_path: Path):
    # Regression for the warrant-hunt finding: $(...) still executes inside
    # double quotes, so it must never be waved through as "just quoted text".
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout,
             'python3 spawn.py review "$(touch /tmp/PWNED_MARKER)"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_backtick_command_substitution_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout,
             'python3 spawn.py review "`touch /tmp/PWNED_MARKER`"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_spawn_py_outside_checkout_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    other = tmp_path / "elsewhere" / "spawn.py"
    other.parent.mkdir()
    other.write_text("# not the real checkout\n")
    r = _run(target, checkout, f'python3 {other} review "task"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_non_spawn_command_is_untouched(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, 'gh pr list')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_kill_switch_suppresses_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, 'python3 spawn.py review "task"',
             extra_env={"ORCHESTRATE_OFF": "1"})
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


# --- issue #834: strict command-shape validation — a command-substitution
# payload hidden in the `cd`-prefix directory slot (this issue's exact
# reproduction), either chain direction, `;`, `|`, and a backslash-escaped-
# quote payload must never get `allow`, mirroring issue #824's own
# regression set (docs/issue-824/reports/implementation/
# hunt-strict-merge-allow-validation.md) for this file's now-identical-in-
# shape check.


def t_cd_prefix_dollar_paren_substitution_in_dir_slot_is_unreached(tmp_path: Path):
    # This issue's exact reproduction: the old regex stripped the `cd DIR &&`
    # prefix before ever searching for operators, so a substitution with no
    # internal whitespace hidden in DIR vanished from what got checked.
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout,
             'cd $(touch /tmp/PWNED_MARKER) && python3 spawn.py review "task"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_cd_prefix_backtick_substitution_in_dir_slot_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout,
             'cd `touch /tmp/PWNED_MARKER` && python3 spawn.py review "task"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_chain_prepended_with_semicolon_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, 'evil ; python3 spawn.py review "task"')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_chain_appended_with_semicolon_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, 'python3 spawn.py review "task" ; evil')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_chain_appended_with_pipe_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, 'python3 spawn.py review "task" | evil')
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_backslash_escaped_quote_payload_is_unreached(tmp_path: Path):
    # docs/issue-824/reports/implementation/hunt-strict-merge-allow-validation.md:
    # a naive `re.sub(r"'[^']*'", "", rest)` quote-stripper desyncs from
    # bash's real quote state on this exact payload shape and misses the
    # live, unquoted `;` it hides — shlex(posix=True) must not repeat that.
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, "python3 spawn.py review 42 \\';evil;'X'")
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
