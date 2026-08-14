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

    pairs = spawn_on_pr.spawn_missing_for_pr(fixture_repo, str(fixture_repo), dry_run=True)

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

    pairs = spawn_on_pr.spawn_missing_for_pr(fixture_repo, str(fixture_repo), dry_run=False)

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

    assert spawn_on_pr.missing_verification(fixture_repo) == {}
