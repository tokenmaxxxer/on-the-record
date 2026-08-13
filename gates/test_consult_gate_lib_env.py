#!/usr/bin/env python3
"""issue #1141 — consult_cmd()'s env must carry CLAUDE_PLUGIN_ROOT_CORE.

Hermetic: no live `claude` process, no network clone. Calls
`_consult_cmd_and_env()` (spawn.py) directly against a tmp_path fixture
core carrying `hooks/lib/gate-lib.sh`, monkeypatching `core_plugin_dirs()`
and `plugin_dirs()` so the real injection code path runs without a real
rulebook checkout. Reuses `resolve_core()` (gates/test_env_resolve.py) to
pin the same acceptance shape `spawn_cmd()` already meets (issue #182).

  python3 -m pytest gates/test_consult_gate_lib_env.py -v
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_env_resolve import resolve_core  # noqa: E402

import spawn  # noqa: E402


def _make_fixture_core(tmp_path):
    root = tmp_path / "core"
    (root / "hooks" / "lib").mkdir(parents=True)
    (root / "hooks" / "lib" / "gate-lib.sh").write_text("# gate-lib\n")
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text('{"name": "core"}')
    return root


def test_consult_env_injects_core_plugin_root(tmp_path, monkeypatch):
    core_dir = _make_fixture_core(tmp_path)
    monkeypatch.setattr(spawn, "core_plugin_dirs", lambda: [core_dir])
    monkeypatch.setattr(spawn, "plugin_dirs", lambda role, spec: [])
    monkeypatch.setattr(spawn, "role_settings",
                         lambda role, cwd, inject_self_hosted_hooks=False: {})

    cmd, env, settings_path = spawn._consult_cmd_and_env("qa", {}, str(tmp_path))
    try:
        assert env.get("CLAUDE_PLUGIN_ROOT_CORE") == str(core_dir)
        result = resolve_core(env=env, candidates=[])
        assert result.skip is False
        assert result.path == str(core_dir)
        assert os.path.isfile(os.path.join(result.path, "hooks", "lib", "gate-lib.sh"))
    finally:
        os.unlink(settings_path)


def test_consult_env_missing_core_entry_omits_var(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT_CORE", raising=False)
    monkeypatch.setattr(spawn, "core_plugin_dirs", lambda: [])
    monkeypatch.setattr(spawn, "plugin_dirs", lambda role, spec: [])
    monkeypatch.setattr(spawn, "role_settings",
                         lambda role, cwd, inject_self_hosted_hooks=False: {})

    cmd, env, settings_path = spawn._consult_cmd_and_env("qa", {}, str(tmp_path))
    try:
        assert "CLAUDE_PLUGIN_ROOT_CORE" not in env
    finally:
        os.unlink(settings_path)
