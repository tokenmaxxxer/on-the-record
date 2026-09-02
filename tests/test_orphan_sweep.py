"""issue-3118 — `spawn.py sweep-orphans [--dry-run]`.

Verification sessions create `/tmp` git worktrees directly via bash
(`git worktree add /tmp/pr3085-verify`), never through `session_temp_root()`
— so `git worktree prune` and `auto_sweep()` cannot see them once the
checkout that registered them (the verification session's own throwaway
workspace) is itself gone. This module covers the three orphan classes
`sweep_orphans()` scans (`/tmp` worktrees, `_workspace_base()` workspaces
whose branch never merged, and orphaned session-log sidecars), each gated
on process-state liveness before age.

  python3 -m pytest tests/test_orphan_sweep.py -q
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn


def _dead_pid():
    """A pid guaranteed not to be alive (fork, exit, reap) -- same helper
    tests/test_tmp_resource_gc.py uses."""
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0)
    return pid


def _make_worktree(tmp_path, name, owner_repo=None, admin_exists=True):
    """A `/tmp/<name>` directory shaped like `git worktree add`'s output:
    a `.git` FILE pointing at `<owner_repo>/.git/worktrees/<name>`.
    `admin_exists=False` simulates the owner checkout having already been
    deleted (its `.git/worktrees/<name>` admin dir goes with it)."""
    owner_repo = owner_repo if owner_repo is not None else tmp_path / "owner-repo"
    entry = tmp_path / name
    entry.mkdir()
    admin_dir = owner_repo / ".git" / "worktrees" / name
    if admin_exists:
        admin_dir.mkdir(parents=True)
    (entry / ".git").write_text(f"gitdir: {admin_dir}\n")
    return entry, owner_repo, admin_dir


# ---------------------------------------------------------------------------
# _worktree_admin_dir
# ---------------------------------------------------------------------------

def test_worktree_admin_dir_reads_gitdir_pointer(tmp_path):
    admin = tmp_path / "owner" / ".git" / "worktrees" / "wt"
    admin.mkdir(parents=True)
    git_file = tmp_path / "wt" / ".git"
    git_file.parent.mkdir()
    git_file.write_text(f"gitdir: {admin}\n")
    assert spawn._worktree_admin_dir(git_file) == admin


def test_worktree_admin_dir_none_for_plain_clone_directory(tmp_path):
    git_dir = tmp_path / "clone" / ".git"
    git_dir.mkdir(parents=True)
    assert spawn._worktree_admin_dir(git_dir) is None


def test_worktree_admin_dir_none_for_missing_git_entry(tmp_path):
    assert spawn._worktree_admin_dir(tmp_path / "nope" / ".git") is None


# ---------------------------------------------------------------------------
# _scan_orphan_worktrees — category 1 (the 190-of-193 `/tmp` worktrees)
# ---------------------------------------------------------------------------

def test_orphan_worktree_with_dead_owner_is_flagged(tmp_path):
    entry, owner_repo, _admin = _make_worktree(tmp_path, "pr123-verify")
    now = time.time() + 100_000  # far enough past the min-age floor
    results = spawn._scan_orphan_worktrees(
        [tmp_path], live={}, unreadable=[], now=now, min_age_seconds=60)
    assert [r["path"] for r in results] == [entry]
    assert "no live pid" in results[0]["reason"]


def test_live_owner_worktree_survives_regardless_of_age(tmp_path):
    entry, owner_repo, _admin = _make_worktree(tmp_path, "pr123-verify")
    live = {owner_repo.resolve(): {"pid": os.getpid()}}
    now = time.time() + 10_000_000  # a session running far past any age floor
    results = spawn._scan_orphan_worktrees(
        [tmp_path], live=live, unreadable=[], now=now, min_age_seconds=60)
    assert results == []


def test_worktree_with_owner_checkout_already_gone_is_flagged(tmp_path):
    entry, _owner_repo, admin = _make_worktree(
        tmp_path, "pr123-verify", admin_exists=False)
    assert not admin.exists()
    now = time.time() + 100_000
    results = spawn._scan_orphan_worktrees(
        [tmp_path], live={}, unreadable=[], now=now, min_age_seconds=60)
    assert [r["path"] for r in results] == [entry]
    assert "admin dir missing" in results[0]["reason"]


def test_worktree_younger_than_floor_never_flagged_by_age_alone(tmp_path):
    """must-not (issue #3118): a dead-owner worktree that is nonetheless
    too fresh (inside the create-time-race floor) must not be swept --
    liveness alone flags it, but the floor still gates it."""
    _make_worktree(tmp_path, "pr123-verify")
    results = spawn._scan_orphan_worktrees(
        [tmp_path], live={}, unreadable=[], now=time.time(),
        min_age_seconds=3600)
    assert results == []


def test_worktree_scan_conservative_when_neighbor_roster_unreadable(tmp_path):
    """Same "unknown must not mean empty" caution `_workspace_clean_state()`
    applies elsewhere: an unreadable sibling roster means liveness can't be
    proven either way, so the candidate is left alone this pass."""
    _make_worktree(tmp_path, "pr123-verify")
    now = time.time() + 100_000
    results = spawn._scan_orphan_worktrees(
        [tmp_path], live={}, unreadable=["sibling roster unreadable"],
        now=now, min_age_seconds=60)
    assert results == []


def test_plain_clone_directory_is_out_of_scope_not_guessed_at(tmp_path):
    """A `.git` DIRECTORY (a full `git clone`, not `git worktree add`) has
    no owner pointer to resolve -- left alone rather than treated as
    always-orphaned (which would make the "no live pid" signal vacuous)."""
    clone = tmp_path / "main-baseline"
    clone.mkdir()
    (clone / ".git").mkdir()
    now = time.time() + 100_000
    results = spawn._scan_orphan_worktrees(
        [tmp_path], live={}, unreadable=[], now=now, min_age_seconds=60)
    assert results == []


def test_orchestrator_scratch_namespace_is_never_touched_or_recursed_into(tmp_path):
    """must-not (issue #3118): a bulk `rm` under `/tmp/claude-1000` was
    blocked by the classifier during the 2026-08-26 inode incident, and
    that directory holds this session's own scratch. The scan only
    resolves a `.git` pointer FILE directly at a temp-root entry's own
    top level (`entry / ".git"`) -- a scratch namespace with no such
    pointer is never flagged, and its contents are never even walked
    (no recursion below one level), so a worktree accidentally nested
    two levels deep inside it still cannot make the namespace itself a
    candidate."""
    claude_scratch = tmp_path / "claude-1000"
    claude_scratch.mkdir()
    nested = claude_scratch / "some-session" / "scratch-file.json"
    nested.parent.mkdir(parents=True)
    nested.write_text("{}")
    now = time.time() + 100_000
    results = spawn._scan_orphan_worktrees(
        [tmp_path], live={}, unreadable=[], now=now, min_age_seconds=60)
    assert results == []
    assert nested.exists()  # never even walked, let alone removed


def test_no_platform_gate_disables_the_sweep_on_darwin(tmp_path):
    """must-not (issue #3118): degrading to a no-op on macOS reproduces
    the exact defect this board keeps meeting -- machinery that reports
    fine while doing nothing. There must be no `sys.platform` branch
    anywhere in the sweep path; pin it by actually flipping platform and
    confirming a real orphan still gets removed."""
    wb = tmp_path / "work"
    wb.mkdir()
    tmp_root = tmp_path / "tmp-root"
    tmp_root.mkdir()
    entry, _owner_repo, _admin = _make_worktree(tmp_root, "orphan-wt")
    now = time.time() + 100_000
    with mock.patch("sys.platform", "darwin"):
        report = spawn.sweep_orphans(
            wb, temp_roots=[tmp_root], now=now, min_age_seconds=60,
            dry_run=False)
    assert report["tmp_worktrees"][0]["removed"] is True
    assert not entry.exists()


def test_missing_temp_root_is_skipped_not_an_error(tmp_path):
    missing = tmp_path / "does-not-exist"
    results = spawn._scan_orphan_worktrees(
        [missing], live={}, unreadable=[], now=time.time(),
        min_age_seconds=60)
    assert results == []


# ---------------------------------------------------------------------------
# _scan_orphan_workspaces — category 3 (branch never merged)
# ---------------------------------------------------------------------------

@pytest.fixture()
def git_workspace(tmp_path):
    """A minimal local repo/branch standing in for a session workspace --
    same fixture shape as tests/test_tmp_resource_gc.py's fixture_pr_branch.
    `_scan_orphan_workspaces()` only needs `git rev-parse --abbrev-ref HEAD`
    to resolve for real; every safety judgement it delegates
    (`_workspace_clean_state()`, the PR lookups) is mocked per test so this
    module never re-verifies logic already owned by other test files."""
    w = tmp_path / "issue-100-implementation-abcd"
    w.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=w, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"],
                    cwd=w, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=w, check=True)
    (w / "f.txt").write_text("x\n")
    subprocess.run(["git", "add", "."], cwd=w, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=w, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "issue-100/implementation"],
                    cwd=w, check=True)
    return w


def test_workspace_not_flagged_when_clean_state_says_live(git_workspace):
    with mock.patch.object(spawn, "_workspace_clean_state",
                            return_value=("live", "session running")):
        results = spawn._scan_orphan_workspaces(
            git_workspace.parent, live={}, unreadable=[],
            now=time.time() + 100_000, min_age_seconds=60)
    assert results == []


def test_workspace_not_flagged_when_clean_state_says_dirty(git_workspace):
    with mock.patch.object(spawn, "_workspace_clean_state",
                            return_value=("dirty", "unpushed commits")):
        results = spawn._scan_orphan_workspaces(
            git_workspace.parent, live={}, unreadable=[],
            now=time.time() + 100_000, min_age_seconds=60)
    assert results == []


def test_workspace_not_flagged_when_open_pr_exists(git_workspace):
    with mock.patch.object(spawn, "_workspace_clean_state",
                            return_value=(None, "")), \
         mock.patch.object(spawn, "_pr_list_call_ok", return_value=True), \
         mock.patch.object(spawn, "_pr_open_or_merged_for_branch",
                            return_value=42):
        results = spawn._scan_orphan_workspaces(
            git_workspace.parent, live={}, unreadable=[],
            now=time.time() + 100_000, min_age_seconds=60)
    assert results == []


def test_workspace_flagged_when_safe_dead_and_no_pr(git_workspace):
    with mock.patch.object(spawn, "_workspace_clean_state",
                            return_value=(None, "")), \
         mock.patch.object(spawn, "_pr_list_call_ok", return_value=True), \
         mock.patch.object(spawn, "_pr_open_or_merged_for_branch",
                            return_value=None):
        results = spawn._scan_orphan_workspaces(
            git_workspace.parent, live={}, unreadable=[],
            now=time.time() + 100_000, min_age_seconds=60)
    assert [r["path"] for r in results] == [git_workspace]
    assert "no open PR" in results[0]["reason"]


def test_workspace_not_flagged_when_gh_call_fails(git_workspace):
    """An unreachable/erroring `gh` call must read as "unknown", never as
    "no PR" -- an API hiccup must not become grounds for deletion."""
    with mock.patch.object(spawn, "_workspace_clean_state",
                            return_value=(None, "")), \
         mock.patch.object(spawn, "_pr_list_call_ok", return_value=False):
        results = spawn._scan_orphan_workspaces(
            git_workspace.parent, live={}, unreadable=[],
            now=time.time() + 100_000, min_age_seconds=60)
    assert results == []


def test_workspace_younger_than_floor_never_flagged_by_age_alone(git_workspace):
    with mock.patch.object(spawn, "_workspace_clean_state",
                            return_value=(None, "")), \
         mock.patch.object(spawn, "_pr_list_call_ok", return_value=True), \
         mock.patch.object(spawn, "_pr_open_or_merged_for_branch",
                            return_value=None):
        results = spawn._scan_orphan_workspaces(
            git_workspace.parent, live={}, unreadable=[],
            now=time.time(), min_age_seconds=3600)
    assert results == []


# ---------------------------------------------------------------------------
# sweep_orphans() orchestration + dry-run / real removal
# ---------------------------------------------------------------------------

def test_sweep_orphans_dry_run_lists_but_does_not_delete(tmp_path):
    wb = tmp_path / "work"
    wb.mkdir()
    tmp_root = tmp_path / "tmp-root"
    tmp_root.mkdir()
    entry, _owner_repo, _admin = _make_worktree(tmp_root, "orphan-wt")
    now = time.time() + 100_000
    report = spawn.sweep_orphans(
        wb, temp_roots=[tmp_root], now=now,
        min_age_seconds=60, dry_run=True)
    assert report["dry_run"] is True
    assert [r["path"] for r in report["tmp_worktrees"]] == [entry]
    assert entry.exists()  # dry-run: nothing removed


def test_sweep_orphans_real_run_removes_orphan_tmp_worktree(tmp_path):
    wb = tmp_path / "work"
    wb.mkdir()
    tmp_root = tmp_path / "tmp-root"
    tmp_root.mkdir()
    entry, _owner_repo, _admin = _make_worktree(tmp_root, "orphan-wt")
    now = time.time() + 100_000
    report = spawn.sweep_orphans(
        wb, temp_roots=[tmp_root], now=now, min_age_seconds=60,
        dry_run=False)
    assert report["tmp_worktrees"][0]["removed"] is True
    assert not entry.exists()


def test_sweep_orphans_real_run_spares_live_worktree(tmp_path):
    wb = tmp_path / "work"
    wb.mkdir()
    tmp_root = tmp_path / "tmp-root"
    tmp_root.mkdir()
    entry, owner_repo, _admin = _make_worktree(tmp_root, "live-wt")
    with mock.patch.object(spawn, "_live_workspaces_union",
                            return_value=({owner_repo.resolve(): {"pid": os.getpid()}}, [])):
        report = spawn.sweep_orphans(
            wb, temp_roots=[tmp_root], now=time.time() + 10_000_000,
            min_age_seconds=60, dry_run=False)
    assert report["tmp_worktrees"] == []
    assert entry.exists()


def test_sweep_orphans_nothing_orphaned_removes_nothing(tmp_path):
    """Symmetric negative (issue #3118 acceptance): an empty environment
    reports zero candidates in every category, not just tmp-worktrees."""
    wb = tmp_path / "work"
    wb.mkdir()
    tmp_root = tmp_path / "tmp-root"
    tmp_root.mkdir()
    report = spawn.sweep_orphans(
        wb, temp_roots=[tmp_root], now=time.time(), min_age_seconds=3600,
        dry_run=True)
    assert report["tmp_worktrees"] == []
    assert report["workspaces"] == []
    assert report["sidecars"] == []


def test_sweep_orphans_cli_reports_zero_candidates_explicitly(tmp_path, capsys):
    wb = tmp_path / "work"
    wb.mkdir()
    with mock.patch.object(spawn, "_sweep_temp_roots",
                            return_value=[tmp_path / "empty-tmp-root"]):
        spawn.sweep_orphans_cli(wb, dry_run=True)
    out = capsys.readouterr().out
    assert "지울 후보 없음" in out


def test_sweep_orphans_cli_lists_each_candidate_with_a_reason(tmp_path, capsys):
    wb = tmp_path / "work"
    wb.mkdir()
    tmp_root = tmp_path / "tmp-root"
    tmp_root.mkdir()
    entry, _owner_repo, _admin = _make_worktree(tmp_root, "orphan-wt")
    now = time.time() + 100_000
    with mock.patch.object(spawn, "_sweep_temp_roots", return_value=[tmp_root]), \
         mock.patch("time.time", return_value=now):
        spawn.sweep_orphans_cli(wb, dry_run=True)
    out = capsys.readouterr().out
    assert str(entry) in out
    assert "no live pid" in out
    assert "age" in out  # acceptance wording: lists what+why (age, no live pid, no open PR)
    assert entry.exists()  # dry-run through the CLI still deletes nothing


# ---------------------------------------------------------------------------
# orphaned session-log sidecars share _orphaned_sidecar_groups() with
# _prune_orphaned_sidecars() -- this only pins that sweep_orphans() wires
# it in, not the grouping/eligibility logic itself (already covered by
# tests/test_cross_checkout_prune_liveness.py).
# ---------------------------------------------------------------------------

def test_sweep_orphans_reports_orphaned_session_log_sidecar(tmp_path):
    wb = tmp_path / "work"
    wb.mkdir()
    log = wb / "issue-1-implementation-abcd.session.20260101T000000.999999.log"
    log.write_text("stream\n")
    now = time.time() + 100_000
    report = spawn.sweep_orphans(
        wb, temp_roots=[tmp_path / "no-tmp-root"], now=now,
        min_age_seconds=60, dry_run=True)
    assert [s["name"] for s in report["sidecars"]] == [
        "issue-1-implementation-abcd"]
    assert log.exists()  # dry-run


def test_sweep_orphans_cli_surfaces_a_failed_deletion_not_silently(tmp_path, capsys):
    """silent-failure-audit finding (issue #3118): a real removal that
    raises OSError must not print the same success-shaped line a real
    removal would -- and the CLI must not exit 0 while something it
    claimed to sweep is still on disk."""
    wb = tmp_path / "work"
    wb.mkdir()
    tmp_root = tmp_path / "tmp-root"
    tmp_root.mkdir()
    entry, _owner_repo, _admin = _make_worktree(tmp_root, "orphan-wt")
    now = time.time() + 100_000
    with mock.patch.object(spawn, "_sweep_temp_roots", return_value=[tmp_root]), \
         mock.patch.object(spawn, "_force_rmtree",
                            side_effect=OSError("permission denied")), \
         mock.patch("time.time", return_value=now):
        rc = spawn.sweep_orphans_cli(wb, dry_run=False)
    out = capsys.readouterr().out
    assert "삭제 실패" in out
    assert "permission denied" in out
    assert rc != 0
    assert entry.exists()  # the failed deletion really did leave it in place


def test_sweep_orphans_real_run_removes_orphaned_session_log_sidecar(tmp_path):
    wb = tmp_path / "work"
    wb.mkdir()
    log = wb / "issue-1-implementation-abcd.session.20260101T000000.999999.log"
    log.write_text("stream\n")
    now = time.time() + 100_000
    report = spawn.sweep_orphans(
        wb, temp_roots=[tmp_path / "no-tmp-root"], now=now,
        min_age_seconds=60, dry_run=False)
    assert report["sidecars"][0]["removed"] is True
    assert not log.exists()
