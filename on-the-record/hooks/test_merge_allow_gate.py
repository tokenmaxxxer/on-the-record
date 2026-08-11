"""Tests for merge-allow-gate.sh (issue #810).

The real `gates/landing_readiness.py` already has its own unit coverage
(gates/test_landing_readiness.py) for the READY predicate itself. This file
tests merge-allow-gate.sh's own logic: role gating, command-shape
resolution, and that it calls out to (rather than reimplements) the READY
predicate — via a synthetic `TOKENMAXXXER_CHECKOUT` whose `gates/
landing_readiness.py` is a stub that echoes back canned classification
lines, so the hook's own branching is exercised in isolation.

  python3 on-the-record/hooks/test_merge_allow_gate.py
"""
from __future__ import annotations
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "on-the-record" / "hooks" / "merge-allow-gate.sh"

STUB_LANDING_READINESS = """#!/usr/bin/env python3
import os, sys
print(os.environ.get("FAKE_LANDING_OUTPUT", ""))
sys.exit(0)
"""


def _make_checkout(tmp_path: Path) -> Path:
    checkout = tmp_path / "checkout"
    (checkout / "gates").mkdir(parents=True)
    (checkout / "spawn.py").write_text("# stub\n")
    lr = checkout / "gates" / "landing_readiness.py"
    lr.write_text(STUB_LANDING_READINESS)
    lr.chmod(lr.stat().st_mode | stat.S_IEXEC)
    return checkout


def _run(target: Path, checkout: Path, command: str, *, ready_output: str = "",
          extra_env: dict | None = None) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(target),
        "session_id": "test-session",
    })
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env["FAKE_LANDING_OUTPUT"] = ready_output
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


def t_orchestrator_ready_pr_gets_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, "gh pr merge 42 --squash",
             ready_output="PR #42: READY")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) == "allow", repr(r.stdout)


def t_role_session_never_gets_allow_even_if_ready(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, "gh pr merge 42 --squash",
             ready_output="PR #42: READY",
             extra_env={"CLAUDE_ROLE": "implementation"})
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_blocked_pr_gets_no_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, "gh pr merge 42 --squash",
             ready_output="PR #42: BLOCKED_ON_PR (checks: fail)")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_ready_line_for_a_different_pr_number_does_not_match(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, "gh pr merge 42 --squash",
             ready_output="PR #99: READY")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_bare_merge_with_no_explicit_pr_number_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, "gh pr merge --squash", ready_output="PR #42: READY")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_non_merge_command_is_untouched(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, "gh pr list", ready_output="PR #42: READY")
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_kill_switch_suppresses_allow(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, "gh pr merge 42 --squash",
             ready_output="PR #42: READY",
             extra_env={"ORCHESTRATE_OFF": "1"})
    assert r.returncode == 0, r.stderr
    assert _allow_decision(r.stdout) is None, repr(r.stdout)


def t_no_gh_repo_flag_with_no_local_checkout_is_unreached(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    checkout = _make_checkout(tmp_path)
    r = _run(target, checkout, "gh pr merge 42 -R owner/repo",
             ready_output="PR #42: READY")
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
