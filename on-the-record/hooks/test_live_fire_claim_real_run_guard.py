"""Tests for live-fire-claim-real-run-guard.sh (issue #914 step 2,
mechanism c). Drives the CALLER (the hook process, via a real git repo
fixture), not the guard's derivation logic directly -- same convention
test_gate_registration_guard.py/test_live_fire_test_guard.py/
test_acceptance_command_real_run_guard.py use. This IS the guard's own
required live-fire test (issue #918/mechanism b): it pipes crafted
PreToolUse/Bash payloads into the script by name and asserts >= 2
distinct exit-code outcomes (allow vs. deny).
"""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "live-fire-claim-real-run-guard.sh"

PASSING_HOOK_TEST = '''"""fixture live-fire test that passes."""
def test_ok():
    assert True
'''

FAILING_HOOK_TEST = '''"""fixture live-fire test that fails."""
def test_ok():
    assert False
'''


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "on-the-record" / "hooks").mkdir(parents=True)
    (repo / "gates").mkdir()
    (repo / "docs" / "reports").mkdir(parents=True)
    return repo


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
        input=payload, capture_output=True, text=True, env=env, timeout=60,
        cwd=repo,
    )


def t_no_live_fire_citation_allows_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "docs" / "reports" / "note.md").write_text(
        "plain note, no outcome claim\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr


def t_missing_cited_test_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (repo / "docs" / "reports" / "impl.md").write_text(
        "done: live-fire: on-the-record/hooks/new-guard.sh — result: allow\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "does not exist" in r.stderr


def t_passing_live_fire_test_allows_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (repo / "on-the-record" / "hooks" / "test_new_guard.py").write_text(
        PASSING_HOOK_TEST, encoding="utf-8")
    (repo / "docs" / "reports" / "impl.md").write_text(
        "done: live-fire: on-the-record/hooks/new-guard.sh — result: allow\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr


def t_failing_live_fire_test_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (repo / "on-the-record" / "hooks" / "test_new_guard.py").write_text(
        FAILING_HOOK_TEST, encoding="utf-8")
    (repo / "docs" / "reports" / "impl.md").write_text(
        "done: live-fire: on-the-record/hooks/new-guard.sh — result: allow\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "just exited" in r.stderr


def t_live_fire_recheck_n_a_trailer_exempts_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (repo / "docs" / "reports" / "impl.md").write_text(
        "done: live-fire: on-the-record/hooks/new-guard.sh — result: allow\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo, command=(
        "git commit -m 'msg\n\n"
        "Live-fire-recheck-N/A: no pytest runner available for this check'"
    ))
    assert r.returncode == 0, r.stderr


def t_non_commit_command_no_ops(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "docs" / "reports" / "impl.md").write_text(
        "done: live-fire: on-the-record/hooks/new-guard.sh — result: allow\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo, command="git status")
    assert r.returncode == 0, r.stderr
