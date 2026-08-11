"""Tests for acceptance-command-real-run-guard.sh (issue #914 step 2,
mechanism a). Drives the CALLER (the hook process, via a real git repo
fixture), not the guard's derivation logic directly -- same convention
test_gate_registration_guard.py/test_live_fire_test_guard.py use. This
IS the guard's own required live-fire test (issue #918/mechanism b):
it pipes crafted PreToolUse/Bash payloads into the script by name and
asserts >= 2 distinct exit-code outcomes (allow vs. deny).
"""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "acceptance-command-real-run-guard.sh"

REGISTRY_HEADER = "| target | command | confirmed |\n|---|---|---|\n"


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "docs" / "specs").mkdir(parents=True)
    (repo / "docs" / "reports").mkdir(parents=True)
    return repo


def _write_registry(repo, *rows):
    body = REGISTRY_HEADER + "".join(rows)
    (repo / "docs" / "specs" / "acceptance-commands.md").write_text(
        body, encoding="utf-8")


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
        input=payload, capture_output=True, text=True, env=env, timeout=30,
        cwd=repo,
    )


def t_no_acceptance_citation_allows_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "docs" / "reports" / "note.md").write_text(
        "plain note, no outcome claim\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr


def t_unregistered_command_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "docs" / "reports" / "impl.md").write_text(
        "done: acceptance: echo hi — result: PASS\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "no row in docs/specs/acceptance-commands.md" in r.stderr


def t_registered_command_that_actually_passes_and_claims_pass_allows_commit(tmp_path):
    repo = _init_repo(tmp_path)
    _write_registry(repo, "| self | `python3 -c \"import sys; sys.exit(0)\"` | 2026-08-12 |\n")
    (repo / "docs" / "reports" / "impl.md").write_text(
        'done: acceptance: python3 -c "import sys; sys.exit(0)" — result: PASS\n',
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr


def t_registered_command_that_actually_fails_but_claims_pass_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    _write_registry(repo, "| self | `python3 -c \"import sys; sys.exit(1)\"` | 2026-08-12 |\n")
    (repo / "docs" / "reports" / "impl.md").write_text(
        'done: acceptance: python3 -c "import sys; sys.exit(1)" — result: PASS\n',
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "a real re-run against the current target just exited 1" in r.stderr


def t_registered_command_that_actually_fails_and_claims_fail_allows_commit(tmp_path):
    repo = _init_repo(tmp_path)
    _write_registry(repo, "| self | `python3 -c \"import sys; sys.exit(1)\"` | 2026-08-12 |\n")
    (repo / "docs" / "reports" / "impl.md").write_text(
        'done: acceptance: python3 -c "import sys; sys.exit(1)" — result: FAIL\n',
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr


def t_unmeasured_result_never_re_run_and_always_allowed(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "docs" / "reports" / "impl.md").write_text(
        "UNMEASURED-with-reason: acceptance: nonexistent-command-xyz — "
        "result: UNMEASURED\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr


def t_acceptance_recheck_n_a_trailer_exempts_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "docs" / "reports" / "impl.md").write_text(
        "done: acceptance: echo hi — result: PASS\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo, command=(
        "git commit -m 'msg\n\n"
        "Acceptance-recheck-N/A: no CI runner available for this check'"
    ))
    assert r.returncode == 0, r.stderr


def t_non_commit_command_no_ops(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "docs" / "reports" / "impl.md").write_text(
        "done: acceptance: echo hi — result: PASS\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo, command="git status")
    assert r.returncode == 0, r.stderr
