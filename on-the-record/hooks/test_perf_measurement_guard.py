"""Tests for perf-measurement-guard.sh (issue #1130, row 28)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "perf-measurement-guard.sh"


def _run(command, cwd):
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command, "cwd": str(cwd)},
        "cwd": str(cwd),
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def _init_repo_with_staged_hotpath(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    hot = tmp_path / "src" / "hot"
    hot.mkdir(parents=True)
    (hot / "loop.py").write_text("def run(): pass\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    return tmp_path


def t_non_commit_command_is_ignored(tmp_path):
    repo = _init_repo_with_staged_hotpath(tmp_path)
    r = _run("git status", repo)
    assert r.returncode == 0


def t_seeded_violation_hotpath_commit_with_no_perf_trailer_is_denied(tmp_path):
    repo = _init_repo_with_staged_hotpath(tmp_path)
    r = _run('git commit -m "speed up the loop"', repo)
    assert r.returncode == 2
    assert "perf:" in r.stderr


def t_hotpath_commit_with_perf_trailer_passes(tmp_path):
    repo = _init_repo_with_staged_hotpath(tmp_path)
    r = _run('git commit -m "speed up the loop\n\nperf: p99 420ms -> 180ms"', repo)
    assert r.returncode == 0


def t_non_hotpath_commit_passes(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("docs\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    r = _run('git commit -m "update docs"', tmp_path)
    assert r.returncode == 0


def t_orchestrate_off_disables_guard(tmp_path):
    repo = _init_repo_with_staged_hotpath(tmp_path)
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": 'git commit -m "speed up"', "cwd": str(repo)},
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = "1"
    r = subprocess.run(["bash", str(GUARD)], input=payload, capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 0
