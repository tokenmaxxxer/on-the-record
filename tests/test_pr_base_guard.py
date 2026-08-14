#!/usr/bin/env python3
"""Tests for `on-the-record/hooks/pr-base-guard.sh` (issue #1461).

Drives the real hook end-to-end (subprocess, stub `gh`) — same shape as
`on-the-record/hooks/test_pr_preflight.py` — since the hook embeds its
checker as inline Python inside a bash heredoc and isn't importable.

Run: python3 -m pytest tests/test_pr_base_guard.py -v
"""
import json
import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "on-the-record" / "hooks" / "pr-base-guard.sh"

FAKE_GH = """#!/usr/bin/env python3
import json, os, sys

fixtures = json.load(open(os.environ["GH_FIXTURES"]))
argv = sys.argv[1:]

if argv[:2] == ["repo", "view"]:
    default_branch = fixtures.get("default_branch")
    if default_branch is None:
        sys.exit(1)
    print(default_branch)
elif argv[:2] == ["issue", "view"]:
    print(fixtures.get("issue_body", ""))
else:
    sys.exit(1)
"""


def _write_fake_gh(bin_dir):
    p = bin_dir / "gh"
    p.write_text(FAKE_GH)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _repo_dir(tmp_path, branch):
    d = tmp_path / "repo"
    d.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=d, check=True)
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com",
         "commit", "-q", "--allow-empty", "-m", "init"],
        cwd=d, check=True,
    )
    return d


def _run_hook(cmd, repo_dir, fixtures, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    _write_fake_gh(bin_dir)
    fixtures_path = tmp_path / "fixtures.json"
    fixtures_path.write_text(json.dumps(fixtures))

    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["GH_FIXTURES"] = str(fixtures_path)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload, capture_output=True, text=True,
        env=env, cwd=str(repo_dir), timeout=20,
    )


def test_rejects_nonmain_base(tmp_path):
    """A `gh pr create --base issue-X/role` from a role workspace, whose
    issue body names no alternate base, is refused — the exact issue #1461
    incident shape (issue-1202/execution-observation -> --base
    issue-247/conformance-review)."""
    repo_dir = _repo_dir(tmp_path, "issue-1202/execution-observation")
    fixtures = {
        "default_branch": "main",
        "issue_body": "some issue body with no base directive",
    }
    cmd = (
        "gh pr create --base issue-247/conformance-review "
        "--head issue-1202/execution-observation --title t --body b"
    )
    r = _run_hook(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 2, r.stderr
    assert "main" in r.stderr


def test_allows_default_base(tmp_path):
    """`--base main` (the repo's resolved default branch) passes through."""
    repo_dir = _repo_dir(tmp_path, "issue-1202/execution-observation")
    fixtures = {"default_branch": "main"}
    cmd = "gh pr create --base main --head issue-1202/execution-observation --title t --body b"
    r = _run_hook(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 0, r.stderr


def test_allows_no_base_flag(tmp_path):
    """No --base at all is out of scope — `gh` itself defaults to the repo
    default branch, nothing for this hook to check."""
    repo_dir = _repo_dir(tmp_path, "issue-1202/execution-observation")
    fixtures = {"default_branch": "main"}
    cmd = "gh pr create --title t --body b"
    r = _run_hook(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 0, r.stderr


def test_fail_closed_on_unknown_default(tmp_path):
    """When the default branch cannot be resolved (`gh repo view` fails),
    the gate refuses rather than passing a non-default --base through."""
    repo_dir = _repo_dir(tmp_path, "issue-1202/execution-observation")
    fixtures = {}  # no "default_branch" key -> fake gh exits 1
    cmd = (
        "gh pr create --base issue-247/conformance-review "
        "--head issue-1202/execution-observation --title t --body b"
    )
    r = _run_hook(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 2, r.stderr
    assert "fail-closed" in r.stderr or "확인할 수 없다" in r.stderr


def test_allows_alternate_base_named_in_issue_body(tmp_path):
    """A non-default --base is allowed when the issue body explicitly names
    it as the intended base (requirement 2's escape hatch)."""
    repo_dir = _repo_dir(tmp_path, "issue-1202/execution-observation")
    fixtures = {
        "default_branch": "main",
        "issue_body": "This delivery's PR base should be `release/2026-08`.",
    }
    cmd = "gh pr create --base release/2026-08 --title t --body b"
    r = _run_hook(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 0, r.stderr


def test_rejects_rest_pulls_create_nonmain_base(tmp_path):
    """The same guard applies to a REST `gh api .../pulls` create with a
    non-default `base` field, not just `gh pr create`."""
    repo_dir = _repo_dir(tmp_path, "issue-1202/execution-observation")
    fixtures = {"default_branch": "main"}
    cmd = (
        "gh api repos/o/r/pulls -f title=t -f head=issue-1202/execution-observation "
        "-f base=issue-247/conformance-review"
    )
    r = _run_hook(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 2, r.stderr


def test_ignores_non_role_workspace_branch(tmp_path):
    """A branch that doesn't match issue-<n>/<role> is out of this gate's
    scope (fail-open, not this gate's job)."""
    repo_dir = _repo_dir(tmp_path, "main")
    fixtures = {"default_branch": "main"}
    cmd = "gh pr create --base issue-247/conformance-review --title t --body b"
    r = _run_hook(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 0, r.stderr
