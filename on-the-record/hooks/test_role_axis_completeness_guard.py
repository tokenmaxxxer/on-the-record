"""Tests for role-axis-completeness-guard.sh (issue #650, hunt #628
finding). Drives the CALLER (the hook process, via a real git repo
fixture), not gates/role_spec_shape.py's CLI directly — the issue's own
acceptance criterion, aimed at preventing a repeat where only the
entrypoint is proven to work in isolation.
"""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "role-axis-completeness-guard.sh"

_AXES = ("alignment", "maintenance_complexity", "external_burden",
         "attack_potential", "performance")


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "roles").mkdir()
    return repo


def _write_role(repo, name, axes):
    (repo / "roles" / f"{name}.json").write_text(
        json.dumps({"judgment_axes": axes}), encoding="utf-8")


def _stage_all(repo):
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)


def _run(repo, command="git commit -m test"):
    payload = json.dumps({
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": command},
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
        cwd=repo,
    )


def _complete_ownership_roles():
    # one role per axis, complete ownership, valid shape.
    return {f"role-{i}": [axis] for i, axis in enumerate(_AXES)}


def t_valid_axis_ownership_allows_commit(tmp_path):
    repo = _init_repo(tmp_path)
    for name, axes in _complete_ownership_roles().items():
        _write_role(repo, name, axes)
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""


def t_zero_owner_axis_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    roles = _complete_ownership_roles()
    dropped = [n for n, axes in roles.items() if axes == ["performance"]][0]
    del roles[dropped]
    for name, axes in roles.items():
        _write_role(repo, name, axes)
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "performance" in r.stderr
    assert "owned by zero roles" in r.stderr


def t_double_owner_axis_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    roles = _complete_ownership_roles()
    for name, axes in roles.items():
        _write_role(repo, name, axes)
    _write_role(repo, "role-extra", ["alignment"])
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "alignment" in r.stderr
    assert "owned by more than one role" in r.stderr


def t_invalid_axis_name_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    for name, axes in _complete_ownership_roles().items():
        _write_role(repo, name, axes)
    _write_role(repo, "role-bad", ["not-a-real-axis"])
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "not-a-real-axis" in r.stderr


def t_no_staged_roles_json_is_fine(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0
    assert r.stdout == ""


def t_non_commit_command_is_skipped(tmp_path):
    repo = _init_repo(tmp_path)
    roles = _complete_ownership_roles()
    del roles[[n for n, axes in roles.items() if axes == ["performance"]][0]]
    for name, axes in roles.items():
        _write_role(repo, name, axes)
    _stage_all(repo)
    r = _run(repo, command="git status")
    assert r.returncode == 0


def t_orchestrate_off_bypasses(tmp_path):
    repo = _init_repo(tmp_path)
    roles = _complete_ownership_roles()
    del roles[[n for n, axes in roles.items() if axes == ["performance"]][0]]
    for name, axes in roles.items():
        _write_role(repo, name, axes)
    _stage_all(repo)
    payload = json.dumps({
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git commit -m test"},
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = "1"
    r = subprocess.run(["bash", str(GUARD)], input=payload,
                        capture_output=True, text=True, env=env, timeout=20, cwd=repo)
    assert r.returncode == 0
