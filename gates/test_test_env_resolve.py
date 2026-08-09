from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_env_resolve import EX_TEMPFAIL, SKIP_MESSAGE, main, resolve_core


def _make_core(tmp_path, name="core"):
    root = tmp_path / name
    (root / "hooks" / "lib").mkdir(parents=True)
    (root / "hooks" / "lib" / "gate-lib.sh").write_text("# gate-lib\n")
    return str(root)


def test_env_var_hit(tmp_path):
    core = _make_core(tmp_path)
    result = resolve_core(env={"CLAUDE_PLUGIN_ROOT_CORE": core}, candidates=[])
    assert result.skip is False
    assert result.path == core


def test_env_unset_sibling_candidate_hit(tmp_path):
    core = _make_core(tmp_path)
    result = resolve_core(env={}, candidates=["/nonexistent", core])
    assert result.skip is False
    assert result.path == core


def test_env_unset_no_candidate_skips(tmp_path):
    result = resolve_core(env={}, candidates=[str(tmp_path / "missing")])
    assert result.skip is True
    assert result.path is None
    assert result.message == SKIP_MESSAGE


def test_env_var_missing_gate_lib_falls_through_to_candidates(tmp_path):
    bad_root = tmp_path / "bad-core"
    bad_root.mkdir()
    core = _make_core(tmp_path, name="good-core")
    result = resolve_core(env={"CLAUDE_PLUGIN_ROOT_CORE": str(bad_root)}, candidates=[core])
    assert result.skip is False
    assert result.path == core


def test_main_skip_exit_code(tmp_path, capsys):
    env_backup = os.environ.pop("CLAUDE_PLUGIN_ROOT_CORE", None)
    try:
        rc = main([str(tmp_path / "missing")])
    finally:
        if env_backup is not None:
            os.environ["CLAUDE_PLUGIN_ROOT_CORE"] = env_backup
    assert rc == EX_TEMPFAIL
    assert SKIP_MESSAGE in capsys.readouterr().err


def test_empty_stub_gate_lib_does_not_resolve(tmp_path):
    root = tmp_path / "stale-core"
    (root / "hooks" / "lib").mkdir(parents=True)
    (root / "hooks" / "lib" / "gate-lib.sh").write_text("")  # zero-byte stub
    result = resolve_core(env={"CLAUDE_PLUGIN_ROOT_CORE": str(root)}, candidates=[])
    assert result.skip is True
    assert result.path is None


def test_main_resolved_exit_code(tmp_path):
    core = _make_core(tmp_path)
    rc = main([core])
    assert rc == 0
