"""Tests for api-version-guard.sh (issue #1130, row 2)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "api-version-guard.sh"

OLD_SPEC = json.dumps({
    "openapi": "3.0.0",
    "info": {"title": "x", "version": "1.0.0"},
    "paths": {
        "/widgets": {"get": {"responses": {"200": {}}}},
    },
})

NEW_SPEC_REMOVED_PATH = json.dumps({
    "openapi": "3.0.0",
    "info": {"title": "x", "version": "1.0.0"},
    "paths": {},
})

NEW_SPEC_BUMPED = json.dumps({
    "openapi": "3.0.0",
    "info": {"title": "x", "version": "2.0.0"},
    "paths": {},
})


def _run(tool_input, tool_name="Write", cwd=None):
    payload = json.dumps({
        "tool_name": tool_name,
        "tool_input": tool_input,
        "cwd": str(cwd) if cwd else os.getcwd(),
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def t_non_contract_path_is_ignored(tmp_path):
    r = _run({"file_path": str(tmp_path / "foo.json"), "content": "{}"})
    assert r.returncode == 0


def t_seeded_violation_removed_path_no_version_bump_is_denied(tmp_path):
    f = tmp_path / "openapi.json"
    f.write_text(OLD_SPEC)
    r = _run({"file_path": str(f), "content": NEW_SPEC_REMOVED_PATH})
    assert r.returncode == 2
    assert "widgets" in r.stderr


def t_removed_path_with_version_bump_passes(tmp_path):
    f = tmp_path / "openapi.json"
    f.write_text(OLD_SPEC)
    r = _run({"file_path": str(f), "content": NEW_SPEC_BUMPED})
    assert r.returncode == 0


def t_new_file_with_no_prior_version_is_unreached(tmp_path):
    f = tmp_path / "openapi.json"
    r = _run({"file_path": str(f), "content": OLD_SPEC})
    assert r.returncode == 0


def t_orchestrate_off_disables_guard(tmp_path):
    f = tmp_path / "openapi.json"
    f.write_text(OLD_SPEC)
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": str(f), "content": NEW_SPEC_REMOVED_PATH},
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = "1"
    r = subprocess.run(["bash", str(GUARD)], input=payload, capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 0
