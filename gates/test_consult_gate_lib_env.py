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
import subprocess
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
    monkeypatch.setattr(spawn, "resolve_role_source", lambda role, repo_root: {"skill_dirs": [], "skills": [], "skill_sha": None})
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
    monkeypatch.setattr(spawn, "resolve_role_source", lambda role, repo_root: {"skill_dirs": [], "skills": [], "skill_sha": None})
    monkeypatch.setattr(spawn, "role_settings",
                         lambda role, cwd, inject_self_hosted_hooks=False: {})

    cmd, env, settings_path = spawn._consult_cmd_and_env("qa", {}, str(tmp_path))
    try:
        assert "CLAUDE_PLUGIN_ROOT_CORE" not in env
    finally:
        os.unlink(settings_path)


def test_exclude_core_plugins_omits_named_plugin_dirs_from_argv(tmp_path, monkeypatch):
    """issue #2201: `exclude_core_plugins` (reused by `_skill_judge_consult`
    as `_JUDGE_EXCLUDED_CORE_PLUGINS`, issue #1587) must drop only the named
    plugins' `--plugin-dir` flags — every other caller's default (empty set)
    stays byte-identical (covered by the two tests above)."""
    core_dir = _make_fixture_core(tmp_path)
    freelunch_dir = tmp_path / "freelunch"
    freelunch_dir.mkdir()
    monkeypatch.setattr(spawn, "core_plugin_dirs", lambda: [core_dir, freelunch_dir])
    monkeypatch.setattr(spawn, "resolve_role_source", lambda role, repo_root: {"skill_dirs": [], "skills": [], "skill_sha": None})
    monkeypatch.setattr(spawn, "role_settings",
                         lambda role, cwd, inject_self_hosted_hooks=False: {})

    cmd, env, settings_path = spawn._consult_cmd_and_env(
        "qa", {}, str(tmp_path), exclude_core_plugins=frozenset({"freelunch"}))
    try:
        assert str(core_dir) in cmd
        assert str(freelunch_dir) not in cmd
        # CLAUDE_PLUGIN_ROOT_CORE 는 core 가 여전히 붙어 있으니 그대로 남는다.
        assert env.get("CLAUDE_PLUGIN_ROOT_CORE") == str(core_dir)
    finally:
        os.unlink(settings_path)


def test_skill_judge_consult_passes_judge_excluded_core_plugins(tmp_path, monkeypatch):
    """issue #2201: cross_family's skill_judge consult reuses the exact
    `_JUDGE_EXCLUDED_CORE_PLUGINS` set issue #1587 already validated for the
    read-only `judge` machinery (freelunch/scout/warrant) — this pins the
    wiring so a future edit can't silently drop the kwarg."""
    seen = {}

    def spy_consult_cmd_and_env(role, spec, cwd, model, **kwargs):
        seen["exclude_core_plugins"] = kwargs.get("exclude_core_plugins")
        return (["cat"], {}, None)

    session_json = ('{"result": "{\\"picked\\": [], \\"rejected\\": [], '
                    '\\"reasons\\": {}}"}')
    monkeypatch.setattr(spawn, "_consult_cmd_and_env", spy_consult_cmd_and_env)
    monkeypatch.setattr(spawn.subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(
                            a, 0, stdout=session_json, stderr=""))
    spawn._skill_judge_consult("some task", "implementation", [], 2201, str(tmp_path))
    assert seen["exclude_core_plugins"] == spawn._JUDGE_EXCLUDED_CORE_PLUGINS
