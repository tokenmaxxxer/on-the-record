"""issue #2028: the #2016 survey left "how often does Stop/
UserPromptSubmit actually fire per session" an unmeasured open finding.
directive.sh (UserPromptSubmit) and stop-gate.sh (Stop) each now append
one line to a per-workspace counter shard on every firing, written before
any kill-switch/role short-circuit so the count reflects every real trip,
not just the ones that go on to do work.

issue #2348: the counter is now sharded per session (hook_fires.py's
_hook_fires_shard_id() -- sha256(session_id)[:24]) instead of one shared
append-only .orchestrate-hook-fires.log, the same conflict-elimination
shape issue #2333 shipped for consult-log.md.

  python3 -m pytest on-the-record/hooks/test_hook_fire_counter.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
DIRECTIVE = HOOKS_DIR / "directive.sh"
STOP_GATE = HOOKS_DIR / "stop-gate.sh"
SHARD_DIRNAME = ".orchestrate-hook-fires"

ROOT = HOOKS_DIR.parent.parent
sys.path.insert(0, str(ROOT))
from hook_fires import _hook_fires_shard_id  # noqa: E402


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


def _shard_path(workspace, session_id):
    return workspace / SHARD_DIRNAME / f"{_hook_fires_shard_id(session_id)}.log"


def t_directive_sh_appends_one_line_per_firing_even_when_gate_is_off():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        payload = json.dumps({"session_id": "s1", "cwd": str(ws)})
        r1 = _run(DIRECTIVE, payload, ws)
        assert r1.returncode == 0
        shard = _shard_path(ws, "s1")
        lines1 = shard.read_text().splitlines()
        assert len(lines1) == 1
        assert "UserPromptSubmit directive.sh" in lines1[0]

        r2 = _run(DIRECTIVE, payload, ws)
        assert r2.returncode == 0
        lines2 = shard.read_text().splitlines()
        assert len(lines2) == 2


def t_stop_gate_sh_appends_one_line_per_firing_even_when_gate_is_off():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        payload = json.dumps({
            "session_id": "s1", "last_assistant_message": "hi", "stop_hook_active": False,
        })
        r1 = _run(STOP_GATE, payload, ws)
        assert r1.returncode == 0
        shard = _shard_path(ws, "s1")
        lines1 = shard.read_text().splitlines()
        assert len(lines1) == 1
        assert "Stop stop-gate.sh" in lines1[0]

        r2 = _run(STOP_GATE, payload, ws)
        assert r2.returncode == 0
        lines2 = shard.read_text().splitlines()
        assert len(lines2) == 2


def t_directive_and_stop_gate_share_the_same_shard_file_for_one_session():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        _run(DIRECTIVE, json.dumps({"session_id": "s1", "cwd": str(ws)}), ws)
        _run(STOP_GATE, json.dumps({"session_id": "s1", "last_assistant_message": "hi",
                                     "stop_hook_active": False}), ws)
        shard = _shard_path(ws, "s1")
        lines = shard.read_text().splitlines()
        assert len(lines) == 2
        assert any("directive.sh" in l for l in lines)
        assert any("stop-gate.sh" in l for l in lines)


def t_two_sessions_never_write_the_same_shard():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        _run(DIRECTIVE, json.dumps({"session_id": "session-a", "cwd": str(ws)}), ws)
        _run(DIRECTIVE, json.dumps({"session_id": "session-b", "cwd": str(ws)}), ws)
        shard_a = _shard_path(ws, "session-a")
        shard_b = _shard_path(ws, "session-b")
        assert shard_a != shard_b
        assert shard_a.is_file()
        assert shard_b.is_file()
        assert len(shard_a.read_text().splitlines()) == 1
        assert len(shard_b.read_text().splitlines()) == 1


def t_missing_session_id_falls_back_to_unknown_shard_without_dropping_the_line():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        r = _run(DIRECTIVE, json.dumps({"cwd": str(ws)}), ws)
        assert r.returncode == 0
        shard = ws / SHARD_DIRNAME / "unknown.log"
        assert shard.is_file()
        assert "UserPromptSubmit directive.sh" in shard.read_text()
