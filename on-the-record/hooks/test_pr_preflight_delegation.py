"""End-to-end tests for pr-preflight.sh's delegation-citation phase
detection (issue #707) — the phase2 branch added alongside the exact-match
`APPROVE issue-<n>/<role>` check. Runs the real shipped script via
subprocess with a fake `gh` shim, same harness shape as
test_approval_gate.py.

Run: python3 -m pytest on-the-record/hooks/test_pr_preflight_delegation.py -q
"""
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "pr-preflight.sh"

ISSUE = 707
ROLE = "implementation"
BRANCH = f"issue-{ISSUE}/{ROLE}"
SCOPE = BRANCH

FAKE_GH = """#!/usr/bin/env python3
import json, os, sys

comments = json.loads(os.environ.get("FAKE_GH_COMMENTS", "[]"))
argv = sys.argv[1:]
if argv[:2] == ["issue", "view"] and "comments" in argv:
    print(json.dumps(comments))
elif argv[:2] == ["issue", "view"] and "body" in argv:
    print(json.dumps(""))
else:
    sys.exit(1)
"""


def _write_fake_gh(bin_dir: Path):
    p = bin_dir / "gh"
    p.write_text(FAKE_GH)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)


def _init_repo(root: Path, branch: str):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    (root / "README.md").write_text("x")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=root, check=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "target"
    r.mkdir()
    _init_repo(r, BRANCH)
    specs = r / "docs" / "specs"
    specs.mkdir(parents=True)
    (specs / "approvers.md").write_text("- octocat\n")
    return r


@pytest.fixture
def bin_dir(tmp_path):
    b = tmp_path / "bin"
    b.mkdir()
    _write_fake_gh(b)
    return b


def _run(repo, bin_dir, body, comments):
    cmd = f'gh pr create --body "{body}"'
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_GH_COMMENTS"] = json.dumps(comments)
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(
        ["bash", str(GUARD)], input=payload, capture_output=True, text=True,
        cwd=repo, env=env, timeout=30,
    )


def _delegate(scope, until, revoked_at=None):
    out = [{"body": f"DELEGATE {scope} UNTIL {until}", "author": {"login": "octocat"},
            "createdAt": "2026-01-01T00:00:00Z"}]
    if revoked_at:
        out.append({"body": f"REVOKE {scope}", "author": {"login": "octocat"},
                     "createdAt": revoked_at})
    return out


def test_valid_delegation_citation_treated_as_phase2(repo, bin_dir):
    # phase2 with no plan -> requires 'Closes #<issue>'; a plain '#<issue>'
    # ref must be REFUSED once the citation flips detection to phase2.
    comments = _delegate(SCOPE, "2099-01-01") + [
        {"body": f"APPROVE {BRANCH} VIA DELEGATION {SCOPE}", "author": {"login": "octocat"},
         "createdAt": "2026-01-02T00:00:00Z"},
    ]
    r = _run(repo, bin_dir, f"see #{ISSUE}", comments)
    assert r.returncode == 2, r.stderr
    assert "Closes" in r.stderr


def test_revoked_delegation_citation_stays_phase1(repo, bin_dir):
    comments = _delegate(SCOPE, "2099-01-01", revoked_at="2026-01-03T00:00:00Z") + [
        {"body": f"APPROVE {BRANCH} VIA DELEGATION {SCOPE}", "author": {"login": "octocat"},
         "createdAt": "2026-01-04T00:00:00Z"},
    ]
    r = _run(repo, bin_dir, f"see #{ISSUE}", comments)
    assert r.returncode == 0, r.stderr


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
