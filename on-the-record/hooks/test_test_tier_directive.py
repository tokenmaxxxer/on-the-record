"""Live-fire tests for test-tier-directive.sh (issue #1518)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
DIRECTIVE = HOOKS_DIR / "test-tier-directive.sh"
HOOKS_JSON = HOOKS_DIR / "hooks.json"


def _run_directive(orchestrate_off=""):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = orchestrate_off
    return subprocess.run(
        ["bash", str(DIRECTIVE)],
        input="", capture_output=True, text=True, env=env, timeout=20,
    )


def t_directive_states_test_tier_contract_policy():
    r = _run_directive()
    assert r.returncode == 0
    out = r.stdout
    assert "<test-tier-directive" in out
    assert ".on-the-record/test-tiers.json" in out
    assert "budget_seconds" in out
    assert "trigger_change_classes" in out
    assert "never" in out.lower() and "silent" in out.lower()


def t_directive_is_silent_when_orchestrate_off():
    r = _run_directive(orchestrate_off="1")
    assert r.returncode == 0
    assert r.stdout == ""


def t_directive_registered_in_hooks_json():
    payload = json.loads(HOOKS_JSON.read_text())
    user_prompt_hooks = payload["hooks"]["UserPromptSubmit"]
    commands = [
        h["command"]
        for group in user_prompt_hooks
        for h in group["hooks"]
    ]
    assert any("test-tier-directive.sh" in c for c in commands)
