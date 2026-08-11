"""Tests for gate-registration-guard.sh (issue #759). Drives the CALLER
(the hook process, via a real git repo fixture), not
gates/test_boundary.py's/gates/test_generated_paths.py's derivation
logic directly — same convention test_role_axis_completeness_guard.py
uses.
"""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "gate-registration-guard.sh"

BOUNDARY_HEADER = "| mechanism | verdict | reason |\n|---|---|---|\n"
PATHS_HEADER = "| mechanism | classification | verdict |\n|---|---|---|\n"


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "gates").mkdir()
    (repo / "on-the-record" / "hooks").mkdir(parents=True)
    (repo / "docs" / "specs").mkdir(parents=True)
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER, encoding="utf-8")
    (repo / "docs" / "specs" / "generated-paths.md").write_text(
        PATHS_HEADER, encoding="utf-8")
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
        input=payload, capture_output=True, text=True, env=env, timeout=20,
        cwd=repo,
    )


def t_new_gate_module_with_no_boundary_row_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "new_gate.py").write_text("# new gate\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "new_gate.py" in r.stderr
    assert "enforcement-boundary.md" in r.stderr


def t_new_gate_module_with_boundary_row_in_same_commit_passes(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "new_gate.py").write_text("# new gate\n", encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new_gate.py` | repo-local | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""


def t_new_hook_script_needs_both_spec_rows(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new-guard.sh` | contract | test fixture |\n",
        encoding="utf-8")
    # generated-paths.md still has no row for it -> still denied
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "new-guard.sh" in r.stderr
    assert "generated-paths.md" in r.stderr


def t_new_hook_script_with_both_rows_in_same_commit_passes(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new-guard.sh` | contract | test fixture |\n",
        encoding="utf-8")
    (repo / "docs" / "specs" / "generated-paths.md").write_text(
        PATHS_HEADER + "| `new-guard.sh` | n/a | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""


def t_new_hook_script_with_wrong_classification_denies_commit(tmp_path):
    """issue #839 regression: a newly-staged hook script with no write call
    in its own text but a generated-paths.md row recorded out-of-tree (this
    incident's exact shape -- `stop-poll-rearm.sh` in `d4a8228`) must be
    denied at commit time, not just a missing row."""
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new-guard.sh` | contract | test fixture |\n",
        encoding="utf-8")
    (repo / "docs" / "specs" / "generated-paths.md").write_text(
        PATHS_HEADER + "| `new-guard.sh` | out-of-tree | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "new-guard.sh" in r.stderr
    assert "classification mismatch" in r.stderr


def t_no_registration_target_change_passes_untouched(tmp_path):
    """issue #759 acceptance's stated empty-state green case: a change
    touching no new mechanism file passes untouched."""
    repo = _init_repo(tmp_path)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0
    assert r.stdout == ""


def t_editing_an_already_registered_gate_module_is_untouched(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "existing_gate.py").write_text("v1\n", encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `existing_gate.py` | repo-local | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=repo, check=True)

    (repo / "gates" / "existing_gate.py").write_text("v2\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""


def t_test_and_init_gate_files_are_excluded(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "test_new_gate.py").write_text("# test\n", encoding="utf-8")
    (repo / "gates" / "__init__.py").write_text("", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""


def t_rename_of_unrelated_tracked_file_into_new_gate_path_denies_commit(tmp_path):
    """Before-landing hunt, stance 0: renaming an existing, unrelated
    tracked file into a gates/*.py path reports git status "R100", not
    "A" — without this case, the rename alone would pass, and the
    follow-up edit would show as a plain "M" this guard intentionally
    leaves untouched, letting a genuinely unregistered module land
    through two ordinary commits with the guard never denying either."""
    repo = _init_repo(tmp_path)
    (repo / "gates" / "dead_stub.py").write_text("def helper():\n    return 1\n",
                                                   encoding="utf-8")
    _stage_all(repo)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=repo, check=True)

    subprocess.run(["git", "mv", "gates/dead_stub.py", "gates/new_gate.py"],
                    cwd=repo, check=True)
    r = subprocess.run(["git", "diff", "--cached", "--name-status"],
                        cwd=repo, capture_output=True, text=True, check=True)
    assert r.stdout.startswith("R"), r.stdout

    r = _run(repo, command="git commit -m step1")
    assert r.returncode == 2, r.stdout
    assert "new_gate.py" in r.stderr
    assert "enforcement-boundary.md" in r.stderr


def t_rename_into_new_gate_path_with_row_in_same_commit_passes(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "dead_stub.py").write_text("def helper():\n    return 1\n",
                                                   encoding="utf-8")
    _stage_all(repo)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=repo, check=True)

    subprocess.run(["git", "mv", "gates/dead_stub.py", "gates/new_gate.py"],
                    cwd=repo, check=True)
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new_gate.py` | repo-local | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo, command="git commit -m step1")
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""


def t_non_commit_command_is_skipped(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "new_gate.py").write_text("# new gate\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo, command="git status")
    assert r.returncode == 0


def t_git_dash_c_commit_is_still_detected(tmp_path):
    """issue #876 (porting #866's spec-index-preflight.sh fix): a global
    option between `git` and `commit` (`git -c k=v commit ...`) used to
    defeat this hook's plain `\\bgit\\s+commit\\b` substring trigger,
    silently letting an unregistered gate module land uninspected."""
    repo = _init_repo(tmp_path)
    (repo / "gates" / "new_gate.py").write_text("# new gate\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo, command='git -c user.name=Bot -c user.email=bot@example.com commit -m msg')
    assert r.returncode == 2, r.stdout
    assert "new_gate.py" in r.stderr
    assert "enforcement-boundary.md" in r.stderr


def t_commit_tree_is_not_a_commit_trigger(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "new_gate.py").write_text("# new gate\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo, command="git commit-tree deadbeef")
    assert r.returncode == 0, r.stderr


def t_orchestrate_off_bypasses(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "new_gate.py").write_text("# new gate\n", encoding="utf-8")
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


def t_script_is_executable():
    """After-proposal hunt finding (stance 4): hooks.json invokes every
    hook by its raw path with no interpreter prefix, so a missing
    execute bit fails silently (exit 126) at real invocation time even
    though every sibling test drives its script via
    `subprocess.run(["bash", str(script)])`, which is blind to the
    file's own execute permission (issue #459's own merge commit hit
    and fixed this exact gap once via a before-landing hunt, not
    pytest). This assertion closes that gap mechanically this time.
    """
    assert os.access(GUARD, os.X_OK), f"{GUARD} is missing its execute bit"
