"""Tests for approval-gate.sh (issue #608 step 2).

Invokes the real shipped script via subprocess against fixture stdin
payloads, with a fake `gh` shim on PATH, in a disposable git repo checked
out on a branch named issue-<n>/<role> (the shape approval-gate.sh parses).
This closes the coverage hole step 1's fixture measurement confirmed: no
deployed hook checked phase-2 approval state for a role session's own
Write/Edit/MultiEdit.

Run: python3 -m pytest on-the-record/hooks/test_approval_gate.py -q
"""
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "approval-gate.sh"

ISSUE = 608
ROLE = "implementation"
BRANCH = f"issue-{ISSUE}/{ROLE}"

FAKE_GH = """#!/usr/bin/env python3
import json, os, sys

comments = json.loads(os.environ.get("FAKE_GH_COMMENTS", "[]"))
argv = sys.argv[1:]
if argv[:2] == ["issue", "view"] and "comments" in argv:
    print(json.dumps(comments))
else:
    sys.exit(1)
"""


def _write_fake_gh(bin_dir: Path):
    p = bin_dir / "gh"
    p.write_text(FAKE_GH)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _init_repo(root: Path, branch: str):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    (root / "README.md").write_text("x")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=root, check=True)


def _run(repo: Path, bin_dir: Path, file_path: str, comments, approvers_present):
    if approvers_present:
        specs = repo / "docs" / "specs"
        specs.mkdir(parents=True, exist_ok=True)
        (specs / "approvers.md").write_text("- octocat\n")
    else:
        p = repo / "docs" / "specs" / "approvers.md"
        if p.exists():
            p.unlink()

    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "x"},
        "cwd": str(repo),
    })
    env = dict(os.environ)
    env["CLAUDE_ROLE"] = ROLE
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_GH_COMMENTS"] = json.dumps(comments)
    env.pop("ORCHESTRATE_OFF", None)
    r = subprocess.run(
        ["bash", str(GUARD)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
        timeout=30,
    )
    return r


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "target"
    r.mkdir()
    _init_repo(r, BRANCH)
    return r


@pytest.fixture
def bin_dir(tmp_path):
    b = tmp_path / "bin"
    b.mkdir()
    _write_fake_gh(b)
    return b


APPROVED_COMMENTS = [{"body": f"APPROVE {BRANCH}", "author": {"login": "octocat"}}]
UNAPPROVED_COMMENTS = [{"body": "looks good", "author": {"login": "octocat"}}]

RECORD_PATH = f"docs/issue-{ISSUE}/reports/{ROLE}.md"
SRC_PATH = "src/thing.py"
TEST_PATH = "test/test_thing.py"
PROPOSAL_PATH = f"docs/issue-{ISSUE}/proposals/implementation.md"
SURVEY_PATH = f"docs/issue-{ISSUE}/reports/implementation/survey.md"


# --- matrix: {approvers present, absent} x {approved, unapproved} x {record, src} --

@pytest.mark.parametrize("target", [RECORD_PATH, SRC_PATH, TEST_PATH])
def test_approvers_absent_denies_refuse_and_instruct(repo, bin_dir, target):
    r = _run(repo, bin_dir, target, UNAPPROVED_COMMENTS, approvers_present=False)
    assert r.returncode == 2, r.stderr
    assert "approvers.md" in r.stderr
    assert "expected:" in r.stderr


@pytest.mark.parametrize("target", [RECORD_PATH, SRC_PATH, TEST_PATH])
def test_approvers_present_unapproved_denies(repo, bin_dir, target):
    r = _run(repo, bin_dir, target, UNAPPROVED_COMMENTS, approvers_present=True)
    assert r.returncode == 2, r.stderr
    assert "APPROVE" in r.stderr


@pytest.mark.parametrize("target", [RECORD_PATH, SRC_PATH, TEST_PATH])
def test_approvers_present_approved_allows(repo, bin_dir, target):
    r = _run(repo, bin_dir, target, APPROVED_COMMENTS, approvers_present=True)
    assert r.returncode == 0, r.stderr


def test_approvers_absent_approved_still_denies(repo, bin_dir):
    # approvers.md presence is checked before the APPROVE comment lookup —
    # absence must never be bypassed by an otherwise-matching comment.
    r = _run(repo, bin_dir, RECORD_PATH, APPROVED_COMMENTS, approvers_present=False)
    assert r.returncode == 2, r.stderr
    assert "approvers.md" in r.stderr


# --- phase-1-legal control row: always allowed regardless of approval state --

@pytest.mark.parametrize("approvers_present", [True, False])
@pytest.mark.parametrize("comments", [APPROVED_COMMENTS, UNAPPROVED_COMMENTS])
def test_phase1_legal_paths_always_allowed(repo, bin_dir, approvers_present, comments):
    for target in (PROPOSAL_PATH, SURVEY_PATH):
        r = _run(repo, bin_dir, target, comments, approvers_present=approvers_present)
        assert r.returncode == 0, (target, r.stderr)


# --- orchestrator session (no CLAUDE_ROLE): not this hook's job --------------

def test_orchestrator_session_skipped(repo, bin_dir):
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": RECORD_PATH, "content": "x"},
        "cwd": str(repo),
    })
    env = dict(os.environ)
    env.pop("CLAUDE_ROLE", None)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_GH_COMMENTS"] = json.dumps(UNAPPROVED_COMMENTS)
    r = subprocess.run(
        ["bash", str(GUARD)], input=payload, capture_output=True, text=True,
        cwd=repo, env=env, timeout=30,
    )
    assert r.returncode == 0, r.stderr


# --- gh lookup failure fails open --------------------------------------------

def test_gh_lookup_failure_fails_open(repo, tmp_path):
    empty_bin = tmp_path / "empty_bin"
    empty_bin.mkdir()
    specs = repo / "docs" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "approvers.md").write_text("- octocat\n")
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": RECORD_PATH, "content": "x"},
        "cwd": str(repo),
    })
    env = dict(os.environ)
    env["CLAUDE_ROLE"] = ROLE
    # python3/git present (needed for the branch-parse subprocess call and
    # the interpreter itself), gh deliberately absent from every entry.
    env["PATH"] = f"{empty_bin}{os.pathsep}/usr/bin{os.pathsep}/bin"
    bash_path = subprocess.run(["which", "bash"], capture_output=True, text=True).stdout.strip()
    r = subprocess.run(
        [bash_path, str(GUARD)], input=payload, capture_output=True, text=True,
        cwd=repo, env=env, timeout=30,
    )
    assert r.returncode == 0, r.stderr


# --- spoof regression (issue #698): bound snapshot wins over live env ------

SESSION_ID = "sess-spoof-1"


def _run_with_session(repo, bin_dir, state_dir, file_path, comments,
                       approvers_present, live_role, bound_role):
    if approvers_present:
        specs = repo / "docs" / "specs"
        specs.mkdir(parents=True, exist_ok=True)
        (specs / "approvers.md").write_text("- octocat\n")
    else:
        p = repo / "docs" / "specs" / "approvers.md"
        if p.exists():
            p.unlink()

    if bound_role is not None:
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / f"{SESSION_ID}.json").write_text(
            json.dumps({"role": bound_role})
        )

    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "x"},
        "cwd": str(repo),
        "session_id": SESSION_ID,
    })
    env = dict(os.environ)
    env["CLAUDE_ROLE"] = live_role
    env["OTR_ROLE_BIND_STATE_DIR"] = str(state_dir)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_GH_COMMENTS"] = json.dumps(comments)
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
        timeout=30,
    )


def test_spoofed_live_env_ignored_when_bound_role_matches_branch_and_approved(
    repo, bin_dir, tmp_path
):
    # session bound to ROLE ("implementation") at SessionStart, then the
    # session re-exports CLAUDE_ROLE to a different role ("hunt") before a
    # Write — the gate must still use the bound role, which matches the
    # branch and is approved, so this is allowed.
    r = _run_with_session(
        repo, bin_dir, tmp_path / "state", RECORD_PATH, APPROVED_COMMENTS,
        approvers_present=True, live_role="hunt", bound_role=ROLE,
    )
    assert r.returncode == 0, r.stderr


def test_spoofed_live_env_still_denied_without_matching_approval(
    repo, bin_dir, tmp_path
):
    # Same spoof attempt, but no APPROVE comment exists for the bound role
    # ("implementation"). If the gate trusted the live "hunt" value instead,
    # role != branch_role would make it exit 0 (not this hook's target) —
    # the spoof's actual goal. The bound snapshot must prevent that.
    r = _run_with_session(
        repo, bin_dir, tmp_path / "state", RECORD_PATH, UNAPPROVED_COMMENTS,
        approvers_present=True, live_role="hunt", bound_role=ROLE,
    )
    assert r.returncode == 2, r.stderr
    assert f"APPROVE issue-{ISSUE}/{ROLE}" in r.stderr


def test_no_snapshot_falls_back_to_live_env(repo, bin_dir, tmp_path):
    # session-role-bind.sh hasn't fired (or its state dir was cleared) —
    # no snapshot file exists, so the gate falls back to the live env var,
    # preserving pre-#698 behavior.
    r = _run_with_session(
        repo, bin_dir, tmp_path / "state", RECORD_PATH, APPROVED_COMMENTS,
        approvers_present=True, live_role=ROLE, bound_role=None,
    )
    assert r.returncode == 0, r.stderr


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
