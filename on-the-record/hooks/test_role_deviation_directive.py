"""Live-fire tests for role-deviation-directive.sh (issue #983)."""
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
DIRECTIVE = HOOKS_DIR / "role-deviation-directive.sh"


def _run_directive(claude_role="implementation", orchestrate_off=""):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = orchestrate_off
    if claude_role is None:
        env.pop("CLAUDE_ROLE", None)
    else:
        env["CLAUDE_ROLE"] = claude_role
    return subprocess.run(
        ["bash", str(DIRECTIVE)],
        input="", capture_output=True, text=True, env=env, timeout=20,
    )


def t_directive_states_role_variant_deviation_loop():
    r = _run_directive(claude_role="implementation")
    assert r.returncode == 0
    out = r.stdout
    assert "<role-deviation-directive>" in out
    assert "RECOGNIZE" in out
    assert "SCOPE-EXCEEDED" in out


def t_directive_is_silent_without_claude_role():
    r = _run_directive(claude_role=None)
    assert r.returncode == 0
    assert r.stdout == ""


def t_directive_fails_open_when_orchestrate_off_set():
    r = _run_directive(claude_role="implementation", orchestrate_off="1")
    assert r.returncode == 0
    assert r.stdout == ""
