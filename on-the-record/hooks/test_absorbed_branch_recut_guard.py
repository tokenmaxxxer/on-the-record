"""Tests for absorbed-branch-recut-guard.sh (issue #784).

Invokes the hook script directly against a fixture repo left in the
merged/absorbed state #732 already validated at spawn time, and asserts
it performs the recut (via `spawn.py recut-if-absorbed`) before exiting 0
(allow) — mirroring test_contract_guard.py's direct-subprocess shape.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
GUARD = HOOKS_DIR / "absorbed-branch-recut-guard.sh"


def _git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a],
                          capture_output=True, text=True)


def _init_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "t@t.t")
    _git(path, "config", "user.name", "t")


def _make_absorbed_workspace(tmp_path):
    """base 에 완전히 흡수된(0-ahead) 로컬 브랜치를 만든다 — 세션이 살아
    있는 동안 phase-1 PR 이 merge+delete-branch 된 상태와 동치."""
    origin = tmp_path / "origin"
    work = tmp_path / "work"
    _init_repo(origin)
    (origin / "a.txt").write_text("base")
    _git(origin, "add", "a.txt")
    _git(origin, "commit", "-q", "-m", "base commit")
    base_branch = _git(origin, "symbolic-ref", "--short", "HEAD").stdout.strip()

    r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    _git(work, "config", "user.email", "t@t.t")
    _git(work, "config", "user.name", "t")

    br = "issue-999913/implementation"
    _git(work, "checkout", "-q", "-b", br, base_branch)
    base_commit = _git(work, "rev-parse", base_branch).stdout.strip()
    return work, br, base_commit, base_branch


def _run_guard(work, payload):
    env = dict(os.environ)
    # This repo's own spawn.py sits one directory up from its
    # on-the-record/ plugin dir — the self-hosted layout the hook resolves
    # `${CLAUDE_PLUGIN_ROOT}/../spawn.py` against.
    env["CLAUDE_PLUGIN_ROOT"] = str(REPO_ROOT / "on-the-record")
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(
        ["bash", str(GUARD)], cwd=work, input=json.dumps(payload),
        capture_output=True, text=True, env=env,
    )


def test_recuts_absorbed_branch_before_allowing_git_commit(tmp_path):
    work, br, base_commit, _base_branch = _make_absorbed_workspace(tmp_path)
    (work / "scratch.txt").write_text("uncommitted, untracked")

    r = _run_guard(work, {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -q -m 'phase 2 commit'"},
    })

    assert r.returncode == 0, r.stderr
    after = _git(work, "rev-parse", br).stdout.strip()
    assert after == base_commit, "흡수된 브랜치가 재컷돼야 한다"
    assert (work / "scratch.txt").read_text() == "uncommitted, untracked", \
        "untracked 작업이 재컷 뒤에도 남아있어야 한다"


def test_recuts_absorbed_branch_for_cd_prefixed_commit(tmp_path):
    # before-landing hunt (stance 2): an anchored startswith missed a
    # `cd <dir> && git commit ...` compound command entirely — this must
    # still resolve the `cd` target and recut it.
    work, br, base_commit, _base_branch = _make_absorbed_workspace(tmp_path)
    (work / "scratch.txt").write_text("uncommitted, untracked")

    r = _run_guard(work, {
        "tool_name": "Bash",
        "tool_input": {"command": f"cd {work} && git commit -q -m 'phase 2 commit'"},
    })

    assert r.returncode == 0, r.stderr
    after = _git(work, "rev-parse", br).stdout.strip()
    assert after == base_commit, "cd 로 감싼 git commit 도 재컷을 트리거해야 한다"


def test_recuts_absorbed_branch_before_allowing_gh_pr_create(tmp_path):
    work, br, base_commit, _base_branch = _make_absorbed_workspace(tmp_path)

    r = _run_guard(work, {
        "tool_name": "Bash",
        "tool_input": {"command": "gh pr create --fill"},
    })

    assert r.returncode == 0, r.stderr
    after = _git(work, "rev-parse", br).stdout.strip()
    assert after == base_commit


def test_ignores_unrelated_command(tmp_path):
    work, br, _base_commit, _base_branch = _make_absorbed_workspace(tmp_path)
    before = _git(work, "rev-parse", br).stdout.strip()

    r = _run_guard(work, {
        "tool_name": "Bash",
        "tool_input": {"command": "ls -la"},
    })

    assert r.returncode == 0, r.stderr
    after = _git(work, "rev-parse", br).stdout.strip()
    assert after == before, "무관한 커맨드는 브랜치를 건드리면 안 된다"


def test_orchestrate_off_bypasses_guard(tmp_path):
    work, br, _base_commit, _base_branch = _make_absorbed_workspace(tmp_path)
    before = _git(work, "rev-parse", br).stdout.strip()

    env = dict(os.environ)
    env["CLAUDE_PLUGIN_ROOT"] = str(REPO_ROOT / "on-the-record")
    env["ORCHESTRATE_OFF"] = "1"
    r = subprocess.run(
        ["bash", str(GUARD)], cwd=work,
        input=json.dumps({"tool_name": "Bash",
                          "tool_input": {"command": "git commit -m x"}}),
        capture_output=True, text=True, env=env,
    )

    assert r.returncode == 0, r.stderr
    after = _git(work, "rev-parse", br).stdout.strip()
    assert after == before
