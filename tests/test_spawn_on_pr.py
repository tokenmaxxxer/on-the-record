#!/usr/bin/env python3
"""issue-1323 req 3 — `spawn_on_pr` 단위테스트. 로컬 fixture 보드/로스터
만 쓴다, 네트워크 없음, 실제 세션 스폰 없음(dry_run).

  python3 -m pytest tests/test_spawn_on_pr.py
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn_on_pr  # noqa: E402


def test_applicable_roles_both_missing():
    assert spawn_on_pr.applicable_roles({}) == [
        "execution-observation", "conformance-review"]


def test_applicable_roles_one_missing():
    board = {"execution-observation": {"loop_state": "landed"}}
    assert spawn_on_pr.applicable_roles(board) == ["conformance-review"]


def test_applicable_roles_none_missing():
    board = {
        "execution-observation": {"loop_state": "landed"},
        "conformance-review": {"loop_state": "landed"},
    }
    assert spawn_on_pr.applicable_roles(board) == []


@pytest.fixture()
def fixture_repo(tmp_path, monkeypatch):
    """A local git repo standing in for the board root + a PR-having branch."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    docs = repo / "docs" / "issue-9001" / "reports"
    docs.mkdir(parents=True)
    (docs / "implementation.md").write_text(
        "---\nloop_state: landed\n---\nbody\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def test_spawn_missing_for_pr_dry_run_returns_pairs_no_side_effects(fixture_repo, monkeypatch):
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)

    registered = []
    spawned = []
    monkeypatch.setattr(spawn_on_pr.spawn, "roster_register",
                         lambda key, entry: registered.append((key, entry)))
    monkeypatch.setattr(spawn_on_pr.spawn, "_spawn_one",
                         lambda *a, **k: spawned.append((a, k)))

    pairs = spawn_on_pr.spawn_missing_for_pr(
        fixture_repo, str(fixture_repo), dry_run=True, issue_states={9001: "OPEN"})

    assert pairs == [
        ("issue-9001", "execution-observation"),
        ("issue-9001", "conformance-review"),
    ]
    assert registered == []
    assert spawned == []


def test_spawn_missing_for_pr_live_registers_and_spawns(fixture_repo, monkeypatch):
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)

    registered = []
    spawned = []
    monkeypatch.setattr(spawn_on_pr.spawn, "roster_register",
                         lambda key, entry: registered.append((key, entry)))
    monkeypatch.setattr(spawn_on_pr.spawn, "_spawn_one",
                         lambda *a, **k: spawned.append((a, k)))

    pairs = spawn_on_pr.spawn_missing_for_pr(
        fixture_repo, str(fixture_repo), dry_run=False, issue_states={9001: "OPEN"})

    assert pairs == [
        ("issue-9001", "execution-observation"),
        ("issue-9001", "conformance-review"),
    ]
    assert [key for key, _ in registered] == [
        "issue-9001/execution-observation", "issue-9001/conformance-review"]
    assert len(spawned) == 2


def test_missing_verification_skips_subjects_without_pr(fixture_repo, monkeypatch):
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: None)

    assert spawn_on_pr.missing_verification(fixture_repo, issue_states={9001: "OPEN"}) == {}


def test_missing_verification_skips_closed_issue(fixture_repo, monkeypatch):
    """issue #1360 acceptance (a): closed-issue subject with a merged PR and
    no verification record yields zero spawn pairs."""
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)

    assert spawn_on_pr.missing_verification(fixture_repo, issue_states={9001: "CLOSED"}) == {}


def test_missing_verification_open_issue_still_yields_pairs(fixture_repo, monkeypatch):
    """issue #1360 acceptance (b)."""
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)

    assert spawn_on_pr.missing_verification(fixture_repo, issue_states={9001: "OPEN"}) == {
        "issue-9001": ["execution-observation", "conformance-review"],
    }


def test_missing_verification_unknown_issue_state_excluded(fixture_repo, monkeypatch):
    """No issue_states available (gh failure) -> fail-closed, no spawn."""
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)

    assert spawn_on_pr.missing_verification(fixture_repo, issue_states=None) == {}


def test_spawn_missing_for_pr_caps_per_tick_and_defers_rest(fixture_repo, monkeypatch, capsys):
    """issue #1360 acceptance (c): more eligible pairs than the cap ->
    exactly `spawn_cap` pairs spawn, and one deferral line is printed."""
    docs2 = fixture_repo / "docs" / "issue-9002" / "reports"
    docs2.mkdir(parents=True)
    (docs2 / "implementation.md").write_text("---\nloop_state: landed\n---\nbody\n")
    subprocess.run(["git", "add", "."], cwd=fixture_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "second subject"], cwd=fixture_repo, check=True)

    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: 42 if branch.startswith("issue-900") else None)

    registered = []
    spawned = []
    monkeypatch.setattr(spawn_on_pr.spawn, "roster_register",
                         lambda key, entry: registered.append((key, entry)))
    monkeypatch.setattr(spawn_on_pr.spawn, "_spawn_one",
                         lambda *a, **k: spawned.append((a, k)))

    pairs = spawn_on_pr.spawn_missing_for_pr(
        fixture_repo, str(fixture_repo), dry_run=False,
        issue_states={9001: "OPEN", 9002: "OPEN"}, spawn_cap=3)

    assert len(pairs) == 3
    assert len(spawned) == 3
    out = capsys.readouterr().out
    deferral_lines = [line for line in out.splitlines() if "미룸" in line]
    assert len(deferral_lines) == 1
    assert "1건" in deferral_lines[0]


def test_backfill_closed_dry_run_lists_without_spawning(fixture_repo, monkeypatch):
    """issue #1360 acceptance (d): opt-in backfill lists closed-issue pairs
    in dry-run without spawning."""
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)
    monkeypatch.setattr(
        spawn_on_pr.closure_sweep, "issue_state_index_all",
        lambda root: ({9001: "CLOSED"}, True))

    registered = []
    spawned = []
    monkeypatch.setattr(spawn_on_pr.spawn, "roster_register",
                         lambda key, entry: registered.append((key, entry)))
    monkeypatch.setattr(spawn_on_pr.spawn, "_spawn_one",
                         lambda *a, **k: spawned.append((a, k)))

    pairs = spawn_on_pr.backfill_closed(fixture_repo, str(fixture_repo))

    assert pairs == [
        ("issue-9001", "execution-observation"),
        ("issue-9001", "conformance-review"),
    ]
    assert registered == []
    assert spawned == []


def _make_branch_with_diff(repo, branch, files):
    """Create `branch` off current HEAD, write/commit `files` ({path: text}),
    return to the branch that was checked out before (main)."""
    subprocess.run(["git", "checkout", "-b", branch], cwd=repo, check=True,
                    capture_output=True)
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        subprocess.run(["git", "add", rel], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "diff"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "master", "-q"], cwd=repo, check=True,
                    capture_output=True)


def test_missing_verification_skips_execution_observation_for_population_s(
        fixture_repo, monkeypatch):
    """issue #745 Item 3 — a small, safe, claim-free diff is population S:
    `execution-observation` is dropped from the missing-roles list, but
    `conformance-review` (unconditioned) still shows up."""
    _make_branch_with_diff(
        fixture_repo, "issue-9001/implementation",
        {"src/feature.py": "x = 1\n"})
    monkeypatch.setattr(spawn_on_pr.skip_eligibility.gates, "BASE", "master")
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)

    out = spawn_on_pr.missing_verification(
        fixture_repo, issue_states={9001: "OPEN"}, pr_index=None)

    assert out["issue-9001"] == ["conformance-review"]


def test_missing_verification_keeps_execution_observation_for_population_r(
        fixture_repo, monkeypatch):
    """A diff touching a hard-to-revert path (`gates/*.py`) is population R:
    `execution-observation` stays in the missing-roles list."""
    _make_branch_with_diff(
        fixture_repo, "issue-9001/implementation",
        {"gates/some_gate.py": "x = 1\n"})
    monkeypatch.setattr(spawn_on_pr.skip_eligibility.gates, "BASE", "master")
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)

    out = spawn_on_pr.missing_verification(
        fixture_repo, issue_states={9001: "OPEN"}, pr_index=None)

    assert out["issue-9001"] == ["execution-observation", "conformance-review"]
