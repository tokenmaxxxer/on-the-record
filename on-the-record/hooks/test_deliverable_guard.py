"""Tests for deliverable-guard.sh (issue #287, session-role-bind port issue #706).

Invokes the real shipped script via subprocess against fixture stdin
payloads in a disposable directory that looks like a board repo (has
docs/specs/approvers.md).
"""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "deliverable-guard.sh"

SESSION_ID = "sess-706-dg"


def _board_repo(tmp_path):
    r = tmp_path / "target"
    (r / "docs" / "specs").mkdir(parents=True)
    (r / "docs" / "specs" / "approvers.md").write_text("- octocat\n")
    (r / ".git").mkdir()  # root-detection only requires a .git dir present
    return r


def _plain_target_repo(tmp_path):
    # issue #787 H1: an ordinary target repo with NO board files at all —
    # no docs/specs/approvers.md, no src/test(s)/docs segment convention,
    # a flat top-level package layout like the #776 fixture's.
    r = tmp_path / "target"
    r.mkdir(parents=True)
    (r / ".git").mkdir()
    return r


def _run(repo, file_path, role_env, session_id=None, state_dir=None,
          tool_name="Write", include_cwd=True):
    payload = {
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path, "content": "x"},
    }
    if include_cwd:
        payload["cwd"] = str(repo)
    if session_id is not None:
        payload["session_id"] = session_id
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    if role_env is None:
        env.pop("CLAUDE_ROLE", None)
    else:
        env["CLAUDE_ROLE"] = role_env
    if state_dir is not None:
        env["OTR_ROLE_BIND_STATE_DIR"] = str(state_dir)
    return subprocess.run(
        ["bash", str(GUARD)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
        timeout=30,
    )


def test_orchestrator_session_writing_deliverable_denied(tmp_path):
    repo = _board_repo(tmp_path)
    r = _run(repo, "docs/issue-1/reports/foo.md", role_env=None)
    assert r.returncode == 2, r.stderr


def test_role_session_writing_own_deliverable_allowed(tmp_path):
    repo = _board_repo(tmp_path)
    r = _run(repo, "docs/issue-1/reports/foo.md", role_env="implementation")
    assert r.returncode == 0, r.stderr


def test_non_deliverable_path_allowed(tmp_path):
    repo = _board_repo(tmp_path)
    r = _run(repo, "scratch/notes.txt", role_env=None)
    assert r.returncode == 0, r.stderr


# --- spoof regression (issue #706): bound snapshot wins over live env ------

def test_unset_spoof_with_bound_role_stays_allowed(tmp_path):
    # session bound to "implementation" at SessionStart, then the session
    # unsets CLAUDE_ROLE before this Write — the hook must still resolve
    # the bound role and treat this as the role's own deliverable write
    # (allow), not silently flip into the orchestrator-only deny branch.
    repo = _board_repo(tmp_path)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / f"{SESSION_ID}.json").write_text(
        json.dumps({"role": "implementation"})
    )
    r = _run(
        repo, "docs/issue-1/reports/foo.md", role_env=None,
        session_id=SESSION_ID, state_dir=state_dir,
    )
    assert r.returncode == 0, r.stderr


def test_no_snapshot_falls_back_to_live_env(tmp_path):
    repo = _board_repo(tmp_path)
    state_dir = tmp_path / "state"
    r = _run(
        repo, "docs/issue-1/reports/foo.md", role_env="implementation",
        session_id=SESSION_ID, state_dir=state_dir,
    )
    assert r.returncode == 0, r.stderr


# --- issue #787 H1: widened tree detection + relaxed approvers.md precondition ---

def test_flat_package_layout_denied(tmp_path):
    # the #776 baseline's exact shape: a top-level package file with no
    # src/test(s)/docs segment at all, in a plain (non-board) target repo.
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "fixture_target/__init__.py", role_env=None)
    assert r.returncode == 2, r.stderr


def test_flat_top_level_test_file_denied(tmp_path):
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "test_fixture_target.py", role_env=None)
    assert r.returncode == 2, r.stderr


def test_plain_target_repo_without_approvers_md_still_guarded(tmp_path):
    # the approvers.md-presence precondition is dropped: a repo that never
    # carried on-the-record's own board files is still guarded once it is
    # a git repo reachable from cwd.
    repo = _plain_target_repo(tmp_path)
    assert not (repo / "docs" / "specs" / "approvers.md").exists()
    r = _run(repo, "src/module.py", role_env=None)
    assert r.returncode == 2, r.stderr


def test_role_session_writes_flat_package_layout_allowed(tmp_path):
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "fixture_target/__init__.py", role_env="implementation")
    assert r.returncode == 0, r.stderr


def test_approvers_md_write_still_allowed(tmp_path):
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "docs/specs/approvers.md", role_env=None)
    assert r.returncode == 0, r.stderr


# --- issue #1111: product-capture-stopgate.sh exemption ---------------

def test_product_capture_priorities_write_allowed(tmp_path):
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "docs/reports/product/priorities.md", role_env=None)
    assert r.returncode == 0, r.stderr


def test_product_capture_issue_scoped_write_allowed(tmp_path):
    repo = _plain_target_repo(tmp_path)
    r = _run(
        repo, "docs/issue-123/reports/product/priorities.md", role_env=None,
    )
    assert r.returncode == 0, r.stderr


def test_product_capture_unrelated_file_denied(tmp_path):
    # exemption stays scoped to the stopgate's four categories — not a
    # general docs/reports/product/* bypass, nor a general docs/reports/*
    # bypass.
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "docs/reports/product/other.md", role_env=None)
    assert r.returncode == 2, r.stderr


def test_scratch_path_allowed(tmp_path):
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "scratch/notes.txt", role_env=None)
    assert r.returncode == 0, r.stderr


def test_tmp_path_allowed(tmp_path):
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "tmp/scratchpad.txt", role_env=None)
    assert r.returncode == 0, r.stderr


def test_relative_cwd_denied_fail_closed(tmp_path):
    # warrant hunt (docs/issue-787/reports/implementation/
    # 2026-08-11-hunt-h1-deliverable-guard.md): a relative cwd (e.g. ".")
    # must not silently resolve against the hook process's own unrelated
    # cwd instead of the session's actual one — fail closed, same as a
    # missing cwd.
    repo = _plain_target_repo(tmp_path)
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "src/evil.py", "content": "x"},
        "cwd": ".",
    }
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env.pop("CLAUDE_ROLE", None)
    r = subprocess.run(
        ["bash", str(GUARD)], input=json.dumps(payload),
        capture_output=True, text=True, cwd=repo, env=env, timeout=30,
    )
    assert r.returncode == 2, r.stderr


def test_missing_cwd_denied_fail_closed(tmp_path):
    # issue #787 H1 residual risk (hunt-after-proposal.md stance 0): a
    # missing/empty cwd must no longer silently fall back to the hook
    # process's own os.getcwd() and ALLOW — it must fail closed.
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "src/module.py", role_env=None, include_cwd=False)
    assert r.returncode == 2, r.stderr


# --- empty state: a non-requirement (chat/question) turn issues no denying
# tool call at all — the gate only ever examines Write/Edit/MultiEdit/
# NotebookEdit, by construction, so a non-deliverable-shaped tool call (the
# closest a non-write turn gets to exercising this hook) must never deny.

def test_non_write_tool_call_never_denied(tmp_path):
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "src/module.py", role_env=None, tool_name="Read")
    assert r.returncode == 0, r.stderr


def test_bash_tool_call_never_denied(tmp_path):
    repo = _plain_target_repo(tmp_path)
    r = _run(repo, "src/module.py", role_env=None, tool_name="Bash")
    assert r.returncode == 0, r.stderr


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
