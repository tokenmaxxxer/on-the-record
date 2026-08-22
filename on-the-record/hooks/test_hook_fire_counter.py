"""issue #2028: the #2016 survey left "how often does Stop/
UserPromptSubmit actually fire per session" an unmeasured open finding.
directive.sh (UserPromptSubmit) and stop-gate.sh (Stop) each now append
one line to a per-workspace counter file on every firing, written before
any kill-switch/role short-circuit so the count reflects every real trip,
not just the ones that go on to do work.

  python3 -m pytest on-the-record/hooks/test_hook_fire_counter.py
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
DIRECTIVE = HOOKS_DIR / "directive.sh"
STOP_GATE = HOOKS_DIR / "stop-gate.sh"
COUNTER_NAME = ".orchestrate-hook-fires.log"


def _run(hook, payload, workspace, env_extra=None):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = "1"  # fast, deterministic exit right after the counter write
    env.pop("CLAUDE_ROLE", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(hook)], input=payload, capture_output=True, text=True,
        env=env, cwd=str(workspace), timeout=20,
    )


def t_directive_sh_appends_one_line_per_firing_even_when_gate_is_off():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        payload = json.dumps({"session_id": "s1", "cwd": str(ws)})
        r1 = _run(DIRECTIVE, payload, ws)
        assert r1.returncode == 0
        counter = ws / COUNTER_NAME
        lines1 = counter.read_text().splitlines()
        assert len(lines1) == 1
        assert "UserPromptSubmit directive.sh" in lines1[0]

        r2 = _run(DIRECTIVE, payload, ws)
        assert r2.returncode == 0
        lines2 = counter.read_text().splitlines()
        assert len(lines2) == 2


def t_stop_gate_sh_appends_one_line_per_firing_even_when_gate_is_off():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        payload = json.dumps({"last_assistant_message": "hi", "stop_hook_active": False})
        r1 = _run(STOP_GATE, payload, ws)
        assert r1.returncode == 0
        counter = ws / COUNTER_NAME
        lines1 = counter.read_text().splitlines()
        assert len(lines1) == 1
        assert "Stop stop-gate.sh" in lines1[0]

        r2 = _run(STOP_GATE, payload, ws)
        assert r2.returncode == 0
        lines2 = counter.read_text().splitlines()
        assert len(lines2) == 2


def t_directive_and_stop_gate_share_the_same_counter_file_in_a_workspace():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        _run(DIRECTIVE, json.dumps({"session_id": "s1", "cwd": str(ws)}), ws)
        _run(STOP_GATE, json.dumps({"last_assistant_message": "hi", "stop_hook_active": False}), ws)
        counter = ws / COUNTER_NAME
        lines = counter.read_text().splitlines()
        assert len(lines) == 2
        assert any("directive.sh" in l for l in lines)
        assert any("stop-gate.sh" in l for l in lines)
