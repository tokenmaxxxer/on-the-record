#!/usr/bin/env python3
"""issue-1476 Acceptance — spawn-on-pr respawn gate parks a verification
role whose only blocker is an unchanged awaiting-human-APPROVE state,
keyed off a structured signal (never prose matching).

  python3 -m pytest tests/test_spawn_on_pr_park.py
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn_on_pr  # noqa: E402


@pytest.fixture()
def fixture_repo(tmp_path):
    """A local git repo standing in for the board root + a PR-having branch
    with no board record for either PR-triggered role — the state
    issue-1163/conformance-review was stuck in for 17 ticks."""
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


def _mock_common(monkeypatch, pr_number=42):
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: pr_number if branch == "issue-9001/implementation" else None)
    registered, spawned = [], []
    monkeypatch.setattr(spawn_on_pr.spawn, "roster_register",
                         lambda key, entry: registered.append((key, entry)))
    monkeypatch.setattr(spawn_on_pr.spawn, "_spawn_one",
                         lambda *a, **k: spawned.append((a, k)))
    return registered, spawned


def _seed_parked(root, subject, role, pr_number, blocked=True):
    state = {f"{subject}/{role}": {"blocked": blocked, "pr_number": pr_number, "parked": False}}
    path = root / spawn_on_pr.PARK_STATE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state))


def test_approval_blocked_respawn_parked(fixture_repo, monkeypatch):
    """Mocked approval-blocked state, unchanged since prior tick -> gate
    skips the spawn for the parked pair."""
    _seed_parked(fixture_repo, "issue-9001", "conformance-review", pr_number=42)
    registered, spawned = _mock_common(monkeypatch, pr_number=42)
    monkeypatch.setattr(spawn_on_pr, "is_approval_blocked", lambda root, issue, role: True)

    pairs = spawn_on_pr.spawn_missing_for_pr(
        fixture_repo, str(fixture_repo), dry_run=False, issue_states={9001: "OPEN"})

    assert ("issue-9001", "conformance-review") not in pairs
    assert ("issue-9001", "execution-observation") in pairs
    assert all(key != "issue-9001/conformance-review" for key, _ in registered)
    assert len(spawned) == 1


def test_no_18th_spawn_on_replay(fixture_repo, monkeypatch):
    """Regression replay of the issue-1163 sequence: tick after tick with
    the same blocker (still no APPROVE comment, no new commit) -> no
    further spawn once parked, however many ticks run."""
    _mock_common(monkeypatch, pr_number=1474)
    monkeypatch.setattr(spawn_on_pr, "is_approval_blocked", lambda root, issue, role: True)

    # Tick 1: first sighting, no prior park record -> spawns once (as the
    # real 1st-17th re-check sessions did).
    pairs1 = spawn_on_pr.spawn_missing_for_pr(
        fixture_repo, str(fixture_repo), dry_run=False, issue_states={9001: "OPEN"})
    assert ("issue-9001", "conformance-review") in pairs1

    # Ticks 2-5: same PR (no new commit), still blocked -> parked every time.
    for _ in range(4):
        _, spawned = _mock_common(monkeypatch, pr_number=1474)
        pairs = spawn_on_pr.spawn_missing_for_pr(
            fixture_repo, str(fixture_repo), dry_run=False, issue_states={9001: "OPEN"})
        assert ("issue-9001", "conformance-review") not in pairs
        assert spawned == []


def test_unpark_on_approve_comment(fixture_repo, monkeypatch):
    """A synthetic APPROVE comment (role no longer blocked) -> respawn
    resumes even though the PR head is unchanged."""
    _seed_parked(fixture_repo, "issue-9001", "conformance-review", pr_number=42)
    registered, spawned = _mock_common(monkeypatch, pr_number=42)
    monkeypatch.setattr(spawn_on_pr, "is_approval_blocked", lambda root, issue, role: False)

    pairs = spawn_on_pr.spawn_missing_for_pr(
        fixture_repo, str(fixture_repo), dry_run=False, issue_states={9001: "OPEN"})

    assert ("issue-9001", "conformance-review") in pairs
    assert any(key == "issue-9001/conformance-review" for key, _ in registered)


def test_parked_entry_still_reported(fixture_repo, monkeypatch):
    """A parked entry stays visible via parked_report() as waiting-for-human
    (watch-coverage inviolable — park suppresses the spawn, not the
    observation)."""
    _seed_parked(fixture_repo, "issue-9001", "conformance-review", pr_number=42)
    registered, spawned = _mock_common(monkeypatch, pr_number=42)
    monkeypatch.setattr(spawn_on_pr, "is_approval_blocked", lambda root, issue, role: True)

    spawn_on_pr.spawn_missing_for_pr(
        fixture_repo, str(fixture_repo), dry_run=False, issue_states={9001: "OPEN"})

    assert ("issue-9001", "conformance-review") in spawn_on_pr.parked_report(fixture_repo)


def test_empty_state_spawns_normally(fixture_repo, monkeypatch):
    """No prior park record at all (empty roster/no-blocker state) -> spawns
    normally, no gh approval lookup needed."""
    called = []
    monkeypatch.setattr(spawn_on_pr, "is_approval_blocked",
                         lambda root, issue, role: called.append(1) or True)
    registered, spawned = _mock_common(monkeypatch, pr_number=1)

    pairs = spawn_on_pr.spawn_missing_for_pr(
        fixture_repo, str(fixture_repo), dry_run=False, issue_states={9001: "OPEN"})

    assert set(pairs) == {("issue-9001", "execution-observation"),
                           ("issue-9001", "conformance-review")}
    assert called == []
    assert spawn_on_pr.parked_report(fixture_repo) == []


def test_should_park_pure():
    assert spawn_on_pr.should_park(None, 42, True) is False
    assert spawn_on_pr.should_park({"blocked": True, "pr_number": 42}, 42, True) is True
    assert spawn_on_pr.should_park({"blocked": True, "pr_number": 41}, 42, True) is False
    assert spawn_on_pr.should_park({"blocked": True, "pr_number": 42}, 42, False) is False
    assert spawn_on_pr.should_park({"blocked": False, "pr_number": 42}, 42, True) is False


def test_unpark_explicit(fixture_repo):
    _seed_parked(fixture_repo, "issue-9001", "conformance-review", pr_number=42)
    assert spawn_on_pr.unpark(fixture_repo, "issue-9001", "conformance-review") is True
    assert spawn_on_pr.load_park_state(fixture_repo) == {}
    assert spawn_on_pr.unpark(fixture_repo, "issue-9001", "conformance-review") is False
