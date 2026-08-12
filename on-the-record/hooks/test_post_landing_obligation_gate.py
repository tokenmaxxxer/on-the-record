"""Tests for post-landing-obligation-gate.sh (issue #1098). Drives the
hook script itself (subprocess, real git repo fixture), same convention
test_role_axis_completeness_guard.py already uses.

Issue/role resolution reads the merged PR's own `headRefName` via
`gh pr view` (warrant-hunter before-landing finding: `gh pr merge` is an
orchestrator-only action per merge-allow-gate.sh's own invariant, and the
orchestrator merges from the base/main checkout, never from the PR's
`issue-<n>/<role>` branch — so the caller's own current branch is never
the right read). Tests stub `gh` on PATH rather than hitting the network.
"""
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "post-landing-obligation-gate.sh"
REPO_ROOT = HOOKS_DIR.parent.parent


def _init_repo(tmp_path, branch="main"):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "README.md").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    if branch != "main":
        subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=repo, check=True)
    return repo


def _stub_gh(tmp_path, head_ref, sha="deadbeefcafe"):
    """Writes a fake `gh` on a PATH-prepended bin dir that answers
    `pr view <n> --json headRefName,mergeCommit` with a fixed head ref —
    the merged PR's branch, independent of the caller's own branch."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    if head_ref is None:
        body = "exit 1\n"
    else:
        payload = json.dumps({"headRefName": head_ref,
                               "mergeCommit": {"oid": sha}})
        body = f"cat <<'EOF'\n{payload}\nEOF\n"
    gh.write_text(f"#!/usr/bin/env bash\n{body}")
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
    return bindir


def _run(repo, command, tool_response="Merged pull request #1101",
         bindir=None):
    payload = json.dumps({
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": command},
        "tool_response": tool_response,
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env["TOKENMAXXXER_CHECKOUT"] = str(REPO_ROOT)
    if bindir is not None:
        env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=30,
        cwd=repo,
    )


def _obligation_path(repo, issue, role, pr):
    return repo / ".landing-obligations" / f"{issue}-{role}-{pr}.json"


def t_successful_merge_opens_obligation_for_pr_head_branch(tmp_path):
    repo = _init_repo(tmp_path)  # orchestrator: merges from main
    bindir = _stub_gh(tmp_path, "issue-1098/implementation")
    r = _run(repo, "gh pr merge 1101 --squash", bindir=bindir)
    assert r.returncode == 0, r.stderr
    path = _obligation_path(repo, 1098, "implementation", 1101)
    assert path.exists(), r.stderr
    data = json.loads(path.read_text())
    assert data["status"] == "open"
    assert data["pr"] == 1101
    assert data["issue"] == 1098
    assert data["role"] == "implementation"
    assert data["sha"] == "deadbeefcafe"


def t_non_merge_bash_command_is_noop(tmp_path):
    repo = _init_repo(tmp_path)
    bindir = _stub_gh(tmp_path, "issue-1098/implementation")
    r = _run(repo, "git status", tool_response="clean", bindir=bindir)
    assert r.returncode == 0, r.stderr
    assert not (repo / ".landing-obligations").exists()


def t_failed_merge_response_is_noop(tmp_path):
    repo = _init_repo(tmp_path)
    bindir = _stub_gh(tmp_path, "issue-1098/implementation")
    r = _run(repo, "gh pr merge 1101 --squash",
             tool_response="failed to merge pull request: mergeable state",
             bindir=bindir)
    assert r.returncode == 0, r.stderr
    assert not _obligation_path(repo, 1098, "implementation", 1101).exists()


def t_chained_command_bypass_is_noop(tmp_path):
    """issue #824's bypass class — a chained payload after the merge call
    must never open an obligation for the merge, mirroring
    merge-allow-gate.sh's own strict shape check."""
    repo = _init_repo(tmp_path)
    bindir = _stub_gh(tmp_path, "issue-1098/implementation")
    r = _run(repo, "gh pr merge 1101 --squash && rm -rf /tmp/whatever",
             bindir=bindir)
    assert r.returncode == 0, r.stderr
    assert not _obligation_path(repo, 1098, "implementation", 1101).exists()


def t_pr_head_not_an_issue_role_branch_is_noop(tmp_path):
    repo = _init_repo(tmp_path)
    bindir = _stub_gh(tmp_path, "some-feature-branch")
    r = _run(repo, "gh pr merge 1101 --squash", bindir=bindir)
    assert r.returncode == 0, r.stderr
    assert not (repo / ".landing-obligations").exists()


def t_implicit_current_pr_is_noop(tmp_path):
    repo = _init_repo(tmp_path)
    bindir = _stub_gh(tmp_path, "issue-1098/implementation")
    r = _run(repo, "gh pr merge --squash", bindir=bindir)
    assert r.returncode == 0, r.stderr
    assert not (repo / ".landing-obligations").exists()


def t_merge_from_orchestrator_base_branch_still_resolves_via_pr_view(tmp_path):
    """Regression for the warrant-hunter before-landing finding: the
    orchestrator's own current branch is `main` (merge-allow-gate.sh's
    documented invariant — role sessions never call `gh pr merge`), yet
    the obligation must still open because resolution reads the PR's own
    head ref, not the caller's branch."""
    repo = _init_repo(tmp_path)
    caller_branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=repo,
        capture_output=True, text=True).stdout.strip()
    assert not caller_branch.startswith("issue-")
    bindir = _stub_gh(tmp_path, "issue-1098/implementation")
    r = _run(repo, "gh pr merge 1101 --squash", bindir=bindir)
    assert r.returncode == 0, r.stderr
    assert _obligation_path(repo, 1098, "implementation", 1101).exists()
