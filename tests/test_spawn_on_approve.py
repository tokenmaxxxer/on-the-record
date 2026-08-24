#!/usr/bin/env python3
"""issue #2173 — `spawn_on_approve` unit tests. Local fixture repo only,
no network, no real session spawn (mocked/dry_run).

  python3 -m pytest tests/test_spawn_on_approve.py
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn_on_approve  # noqa: E402


@pytest.fixture(autouse=True)
def _no_bulk_pr_index_by_default(monkeypatch):
    """issue #2173 before-landing hunt fix: `ready_for_phase2`/
    `spawn_phase2` now bulk-fetch `closure_sweep._pr_index_all()` once
    when the caller passes no `pr_index`, to avoid an uncounted `gh pr
    list` call per candidate branch. Default this to a failed fetch
    (`(None, False)`, no network) so the module falls through to the
    per-branch `spawn._pr_open_or_merged_for_branch` fallback tests
    already mock — the real bulk fetch is exercised only by the tests
    that explicitly monkeypatch it below."""
    monkeypatch.setattr(spawn_on_approve.closure_sweep, "_pr_index_all",
                         lambda root: (None, False))


def _git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True)


@pytest.fixture()
def fixture_repo(tmp_path):
    """A local git repo with an `issue-9001/implementation` phase-1 branch
    (proposal-only — no landed record) standing in for the board root."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "a.txt").write_text("base")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "branch", "issue-9001/implementation")
    return repo


def test_candidate_branches_finds_local_branch(fixture_repo):
    assert spawn_on_approve._candidate_branches(fixture_repo) == {
        ("issue-9001", "implementation")}


def test_candidate_branches_empty_repo(tmp_path):
    repo = tmp_path / "empty"
    repo.mkdir()
    _git(repo, "init", "-q")
    assert spawn_on_approve._candidate_branches(repo) == set()


def test_ready_for_phase2_approved_with_open_pr_is_returned(fixture_repo, monkeypatch):
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: 42)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})

    out = spawn_on_approve.ready_for_phase2(fixture_repo, issue_states={9001: "OPEN"})
    assert out == {"issue-9001": ["implementation"]}


def test_ready_for_phase2_skips_when_not_approved(fixture_repo, monkeypatch):
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: set())
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: 42)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})

    assert spawn_on_approve.ready_for_phase2(fixture_repo, issue_states={9001: "OPEN"}) == {}


def test_ready_for_phase2_skips_when_record_already_landed(fixture_repo, monkeypatch):
    # board() already carries an "implementation" record -> phase-2 is done,
    # this is the exact opposite condition of "phase-1 only".
    monkeypatch.setattr(spawn_on_approve.spawn, "board",
                         lambda root: {"issue-9001": {"implementation": {"loop_state": "landed"}}})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: 42)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})

    assert spawn_on_approve.ready_for_phase2(fixture_repo, issue_states={9001: "OPEN"}) == {}


def test_ready_for_phase2_skips_without_open_pr(fixture_repo, monkeypatch):
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: None)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})

    assert spawn_on_approve.ready_for_phase2(fixture_repo, issue_states={9001: "OPEN"}) == {}


def test_ready_for_phase2_skips_unknown_issue_state(fixture_repo, monkeypatch):
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: 42)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})

    assert spawn_on_approve.ready_for_phase2(fixture_repo, issue_states=None) == {}


def test_ready_for_phase2_skips_active_session(fixture_repo, monkeypatch):
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: 42)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load",
                         lambda: {"issue-9001/implementation": {"pid": 123456}})
    monkeypatch.setattr(spawn_on_approve.spawn, "_alive", lambda pid: True)

    assert spawn_on_approve.ready_for_phase2(fixture_repo, issue_states={9001: "OPEN"}) == {}


def test_ready_for_phase2_skips_already_attempted(fixture_repo, monkeypatch):
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: 42)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})
    spawn_on_approve._save_attempted(
        fixture_repo, {"issue-9001/implementation": {"pr_number": 42}})

    assert spawn_on_approve.ready_for_phase2(fixture_repo, issue_states={9001: "OPEN"}) == {}


def test_ready_for_phase2_narrows_to_given_subjects(fixture_repo, monkeypatch):
    _git(fixture_repo, "branch", "issue-9002/implementation")
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: 42)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})

    out = spawn_on_approve.ready_for_phase2(
        fixture_repo, subjects={"issue-9002"}, issue_states={9001: "OPEN", 9002: "OPEN"})
    assert out == {"issue-9002": ["implementation"]}


def test_ready_for_phase2_no_pr_index_arg_uses_one_bulk_fetch_not_per_branch(
        fixture_repo, monkeypatch):
    """issue #2173 before-landing hunt: calling `ready_for_phase2` with no
    `pr_index` (its default) must fetch the bulk index exactly once and
    use it for every candidate branch — not fall back to one
    `spawn._pr_open_or_merged_for_branch` (real `gh pr list`) call per
    branch, which was the actual finding (5 branches -> 5 uncounted `gh`
    calls)."""
    for n in range(9002, 9006):
        _git(fixture_repo, "branch", f"issue-{n}/implementation")
    bulk_calls = []

    def _bulk(root):
        bulk_calls.append(root)
        return ({f"issue-{n}/implementation": {"number": n, "state": "OPEN"}
                  for n in range(9001, 9006)}, True)

    monkeypatch.setattr(spawn_on_approve.closure_sweep, "_pr_index_all", _bulk)
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    per_branch_calls = []
    monkeypatch.setattr(
        spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: per_branch_calls.append(branch) or 99)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})

    out = spawn_on_approve.ready_for_phase2(
        fixture_repo, issue_states={n: "OPEN" for n in range(9001, 9006)})

    assert len(out) == 5
    assert len(bulk_calls) == 1  # exactly one bulk fetch, not one per branch
    assert per_branch_calls == []  # the per-branch gh fallback never fires


def test_spawn_phase2_no_pr_index_arg_shares_one_bulk_fetch(fixture_repo, monkeypatch):
    """Same guard as above, through the `spawn_phase2` entry point (the
    one `watchdog._board_wide_sweep` actually calls) — including its own
    second `_pr_number_for_branch` call when recording `attempted[...]`."""
    bulk_calls = []

    def _bulk(root):
        bulk_calls.append(root)
        return ({"issue-9001/implementation": {"number": 9001, "state": "OPEN"}}, True)

    monkeypatch.setattr(spawn_on_approve.closure_sweep, "_pr_index_all", _bulk)
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: (_ for _ in ()).throw(
                             AssertionError("per-branch gh fallback must not fire")))
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})
    monkeypatch.setattr(spawn_on_approve.spawn, "roster_register", lambda key, entry: None)
    monkeypatch.setattr(spawn_on_approve.spawn, "_spawn_one", lambda *a, **k: None)

    pairs = spawn_on_approve.spawn_phase2(
        fixture_repo, str(fixture_repo), dry_run=False, issue_states={9001: "OPEN"})

    assert pairs == [("issue-9001", "implementation")]
    assert len(bulk_calls) == 1
    assert spawn_on_approve.load_attempted(fixture_repo) == {
        "issue-9001/implementation": {"pr_number": 9001}}


def test_spawn_phase2_dry_run_no_side_effects(fixture_repo, monkeypatch):
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: 42)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})
    registered, spawned = [], []
    monkeypatch.setattr(spawn_on_approve.spawn, "roster_register",
                         lambda key, entry: registered.append((key, entry)))
    monkeypatch.setattr(spawn_on_approve.spawn, "_spawn_one",
                         lambda *a, **k: spawned.append((a, k)))

    pairs = spawn_on_approve.spawn_phase2(fixture_repo, str(fixture_repo),
                                          dry_run=True, issue_states={9001: "OPEN"})

    assert pairs == [("issue-9001", "implementation")]
    assert registered == [] and spawned == []
    assert spawn_on_approve.load_attempted(fixture_repo) == {}  # dry-run never marks attempted


def test_spawn_phase2_live_registers_spawns_and_marks_attempted(fixture_repo, monkeypatch):
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: 42)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})
    registered, spawned = [], []
    monkeypatch.setattr(spawn_on_approve.spawn, "roster_register",
                         lambda key, entry: registered.append((key, entry)))
    monkeypatch.setattr(spawn_on_approve.spawn, "_spawn_one",
                         lambda *a, **k: spawned.append((a, k)))

    pairs = spawn_on_approve.spawn_phase2(fixture_repo, str(fixture_repo),
                                          dry_run=False, issue_states={9001: "OPEN"})

    assert pairs == [("issue-9001", "implementation")]
    assert [key for key, _ in registered] == ["issue-9001/implementation"]
    assert len(spawned) == 1
    assert spawn_on_approve.load_attempted(fixture_repo) == {
        "issue-9001/implementation": {"pr_number": 42}}

    # second sweep: same conditions, but now already-attempted -> no re-spawn
    pairs2 = spawn_on_approve.spawn_phase2(fixture_repo, str(fixture_repo),
                                           dry_run=False, issue_states={9001: "OPEN"})
    assert pairs2 == []
    assert len(spawned) == 1  # unchanged


def test_spawn_phase2_caps_per_tick_and_defers_rest(fixture_repo, monkeypatch, capsys):
    _git(fixture_repo, "branch", "issue-9002/implementation")
    monkeypatch.setattr(spawn_on_approve.spawn, "board", lambda root: {})
    monkeypatch.setattr(spawn_on_approve._ci, "_approved_roles_on_issue",
                         lambda root, issue: {"implementation"})
    monkeypatch.setattr(spawn_on_approve.spawn, "_pr_open_or_merged_for_branch",
                         lambda root, branch: 42)
    monkeypatch.setattr(spawn_on_approve.spawn, "_roster_load", lambda: {})
    monkeypatch.setattr(spawn_on_approve.spawn, "roster_register", lambda key, entry: None)
    spawned = []
    monkeypatch.setattr(spawn_on_approve.spawn, "_spawn_one",
                         lambda *a, **k: spawned.append((a, k)))

    pairs = spawn_on_approve.spawn_phase2(
        fixture_repo, str(fixture_repo), dry_run=False,
        issue_states={9001: "OPEN", 9002: "OPEN"}, spawn_cap=1)

    assert len(pairs) == 1
    assert len(spawned) == 1
    assert "cap=1" in capsys.readouterr().out
