#!/usr/bin/env python3
"""issue #1554 req 2 — cross-workspace board-sweep dedup: two watchdog loops
started from different checkouts (simulated here as two `pid`s over the same
target repo) contend for one lock keyed by the target repo's identity, not by
either checkout's own state root, so exactly one of them runs the board-wide
sweep. Hermetic — pure local filesystem/pid state, no gh calls.

  python3 -m pytest tests/test_board_sweep_cross_workspace_lock.py
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn  # noqa: E402


def test_second_workspace_defers(tmp_path, monkeypatch):
    """Two watchdog loops (both calling the acquire function with the same
    `pid` == this process — a live process) over the same target repo:
    the first acquires, the second is refused."""
    monkeypatch.setenv("MUSTER_WORK_DIR", str(tmp_path / "work"))
    target_repo = tmp_path / "target-repo"
    target_repo.mkdir()

    my_pid = os.getpid()
    got1, _msg1 = spawn.cross_workspace_board_sweep_lock_acquire(target_repo, pid=my_pid)
    got2, msg2 = spawn.cross_workspace_board_sweep_lock_acquire(target_repo, pid=my_pid)

    assert got1 is True
    assert got2 is False
    assert "실행 중" in msg2


def test_same_repo_different_checkout_shares_one_lock_path(tmp_path, monkeypatch):
    """The lock path itself does not depend on which checkout's `ROOT`/
    `STATE_ROOT` is executing — only on the swept repo's identity and the
    shared workspace base. Simulate 'different checkout' by pointing at two
    distinct repo directories that resolve to the same repo identity
    (same basename, no git remote) and asserting they collide on one path."""
    monkeypatch.setenv("MUSTER_WORK_DIR", str(tmp_path / "work"))
    repo_a = tmp_path / "checkout-a" / "same-repo-name"
    repo_b = tmp_path / "checkout-b" / "same-repo-name"
    repo_a.mkdir(parents=True)
    repo_b.mkdir(parents=True)

    path_a = spawn._cross_workspace_board_sweep_lock_path(repo_a)
    path_b = spawn._cross_workspace_board_sweep_lock_path(repo_b)
    assert path_a == path_b


def test_different_repos_get_independent_locks(tmp_path, monkeypatch):
    """Different target repos never contend for the same lock file — a
    sweeper for repo A must not be blocked by a sweeper for repo B."""
    monkeypatch.setenv("MUSTER_WORK_DIR", str(tmp_path / "work"))
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    repo_a.mkdir()
    repo_b.mkdir()

    my_pid = os.getpid()
    got_a, _ = spawn.cross_workspace_board_sweep_lock_acquire(repo_a, pid=my_pid)
    got_b, _ = spawn.cross_workspace_board_sweep_lock_acquire(repo_b, pid=my_pid)
    assert got_a is True
    assert got_b is True


def test_crashed_holder_lock_is_reclaimed(tmp_path, monkeypatch):
    """A lock left by a pid that is no longer alive is reclaimed, not
    treated as a live holder forever (mirrors `watchdog_lock_acquire`'s
    existing crash-recovery contract, reused here)."""
    monkeypatch.setenv("MUSTER_WORK_DIR", str(tmp_path / "work"))
    target_repo = tmp_path / "target-repo"
    target_repo.mkdir()

    with mock.patch.object(spawn, "_alive", return_value=False):
        got1, _ = spawn.cross_workspace_board_sweep_lock_acquire(target_repo, pid=999999)
    assert got1 is True

    got2, _ = spawn.cross_workspace_board_sweep_lock_acquire(target_repo, pid=os.getpid())
    assert got2 is True
