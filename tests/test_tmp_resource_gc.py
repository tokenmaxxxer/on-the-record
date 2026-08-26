#!/usr/bin/env python3
"""issue-2468 — GC sweep for orphaned check_runner.py PR worktrees and
consult.py/spawn.py settings.json temp files.

Both resource classes are cleaned up on normal exit (existing try/finally),
but SIGKILL/a hard crash before that point cannot be caught by Python at
all — the resource is then permanently orphaned in system /tmp. The fix
records the owning pid at creation time (`spawn._record_tmp_resource`) and
sweeps (`spawn.tmp_resource_sweep`) by the same pid-liveness pattern
already proven for spawn-attempt pruning (`_pid_is_alive`, issue #2413).

  python3 -m pytest tests/test_tmp_resource_gc.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
import check_runner as cr  # noqa: E402


def _dead_pid():
    """A pid guaranteed not to be alive: fork, exit immediately, reap.
    Same helper as tests/test_watch_hardening.py's SpawnAttemptPruneLiveness
    — deterministic and fast, standing in for a SIGKILL/crash victim."""
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0)
    return pid


class TmpResourceSweepLiveness(unittest.TestCase):
    """Both directions live, per issue #2468 acceptance: a dead-owner
    resource is removed, a live-owner resource never is."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.ledger = Path(self._td.name) / "tmp-resources.jsonl"
        patch = mock.patch.object(spawn, "TMP_RESOURCE_LEDGER_PATH", self.ledger)
        patch.start()
        self.addCleanup(patch.stop)

    def _write(self, records):
        with self.ledger.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec) + "\n")

    def test_orphaned_worktree_dir_with_dead_pid_is_removed(self):
        """Simulates the check_runner.py kill-9-mid-worktree-creation
        fixture: a worktree-shaped directory on disk whose creating
        process is confirmed dead (present on disk, owning pid dead —
        the exact orphan state a `kill -9` between `mkdtemp()` and the
        matching `remove_worktree()` leaves behind)."""
        dead_pid = _dead_pid()
        orphan = Path(self._td.name) / "check-runner-pr-orphan"
        orphan.mkdir()
        (orphan / "marker").write_text("x")
        self.assertTrue(orphan.exists())  # orphan confirmed present
        self.assertFalse(spawn._pid_is_alive(dead_pid))  # owning pid confirmed dead
        self._write([{"path": str(orphan), "pid": dead_pid, "kind": "worktree",
                      "ts": time.time()}])

        removed = spawn.tmp_resource_sweep()

        self.assertEqual(removed, 1)
        self.assertFalse(orphan.exists())

    def test_live_owned_worktree_dir_is_never_removed(self):
        """The other direction, same fixture shape: an equivalent resource
        whose owning pid is still alive (this test process's own pid)
        must survive the sweep untouched."""
        live = Path(self._td.name) / "check-runner-pr-live"
        live.mkdir()
        self._write([{"path": str(live), "pid": os.getpid(), "kind": "worktree",
                      "ts": time.time()}])

        removed = spawn.tmp_resource_sweep()

        self.assertEqual(removed, 0)
        self.assertTrue(live.exists())

    def test_orphaned_settings_json_with_dead_pid_is_removed(self):
        """Same demonstration for the consult.py/spawn.py settings.json
        class — a plain file, not a directory."""
        dead_pid = _dead_pid()
        orphan = Path(self._td.name) / "settings-orphan.json"
        orphan.write_text("{}")
        self._write([{"path": str(orphan), "pid": dead_pid, "kind": "settings",
                      "ts": time.time()}])

        removed = spawn.tmp_resource_sweep()

        self.assertEqual(removed, 1)
        self.assertFalse(orphan.exists())

    def test_live_owned_settings_json_is_never_removed(self):
        live = Path(self._td.name) / "settings-live.json"
        live.write_text("{}")
        self._write([{"path": str(live), "pid": os.getpid(), "kind": "settings",
                      "ts": time.time()}])

        removed = spawn.tmp_resource_sweep()

        self.assertEqual(removed, 0)
        self.assertTrue(live.exists())

    def test_already_cleaned_resource_self_prunes_without_counting_as_removed(self):
        """A resource that already went through the normal-exit cleanup
        path (ledger entry present, but the path itself is gone) must not
        be double-counted as a sweep removal — and the stale ledger line
        must not accumulate forever."""
        gone = Path(self._td.name) / "already-gone.json"
        self._write([{"path": str(gone), "pid": os.getpid(), "kind": "settings",
                      "ts": time.time()}])

        removed = spawn.tmp_resource_sweep()

        self.assertEqual(removed, 0)
        self.assertEqual(self.ledger.read_text(), "")

    def test_record_tmp_resource_appends_a_line_the_sweep_can_consume(self):
        """End-to-end wiring: `_record_tmp_resource` (guarded off under
        pytest by default, same as `_record_spawn_attempt`) with that
        guard explicitly lifted actually produces a ledger line the sweep
        can act on."""
        dead_pid = _dead_pid()
        orphan = Path(self._td.name) / "wired.json"
        orphan.write_text("{}")
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PYTEST_CURRENT_TEST", None)
            spawn._record_tmp_resource(orphan, dead_pid, "settings")
        self.assertEqual(spawn.tmp_resource_sweep(), 1)
        self.assertFalse(orphan.exists())


@pytest.fixture()
def fixture_pr_branch(tmp_path):
    """A local git repo/branch standing in for a PR branch checkout —
    same fixture shape as gates/test_check_runner.py's."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "existing.txt").write_text("hello world\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "pr-branch"], cwd=repo, check=True)
    return repo


def test_worktree_for_ref_records_owning_pid_before_git_worktree_add(fixture_pr_branch):
    """issue #2468: the ledger entry must exist as early as possible —
    right after `mkdtemp()`, before `git worktree add` even runs — so a
    kill -9 during the (slower) worktree-add step still leaves a record
    behind. Verified by making the recording call itself raise: if
    `worktree_for_ref` recorded the resource before calling out to git,
    the directory it made is still on disk (and still orphaned) even
    though the function never returns normally."""
    calls = []

    def _spy(path, pid, kind):
        calls.append((Path(path), pid, kind))
        raise RuntimeError("simulated crash right after recording")

    with mock.patch.object(spawn, "_record_tmp_resource", _spy):
        with pytest.raises(RuntimeError):
            cr.worktree_for_ref(fixture_pr_branch, "pr-branch")

    assert len(calls) == 1
    path, pid, kind = calls[0]
    assert kind == "worktree"
    assert pid == os.getpid()
    assert path.exists()  # orphaned exactly as a real kill -9 here would leave it
    assert path.name.startswith("check-runner-pr-")
    import shutil
    shutil.rmtree(path, ignore_errors=True)


def test_worktree_for_ref_success_path_is_gc_sweepable_end_to_end(tmp_path, fixture_pr_branch):
    """Full pipeline for a genuinely orphaned (dead-owner) worktree: create
    it for real via `worktree_for_ref`, confirm it is on disk and its
    recorded owner is this pid, then simulate that owner having crashed
    (dead pid) and confirm the sweep removes exactly it — never touching
    a live-owned sibling."""
    ledger = tmp_path / "tmp-resources.jsonl"
    with mock.patch.object(spawn, "TMP_RESOURCE_LEDGER_PATH", ledger), \
            mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("PYTEST_CURRENT_TEST", None)
        worktree, err = cr.worktree_for_ref(fixture_pr_branch, "pr-branch")
        assert err is None
        assert worktree.exists()

        # dead-owner rewrite: simulate the creating process having crashed
        dead_pid = _dead_pid()
        lines = ledger.read_text().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["pid"] == os.getpid()
        entry["pid"] = dead_pid
        ledger.write_text(json.dumps(entry) + "\n")

        # a live-owned sibling must survive the same sweep pass
        live_sibling = tmp_path / "check-runner-pr-live-sibling"
        live_sibling.mkdir()
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"path": str(live_sibling), "pid": os.getpid(),
                                  "kind": "worktree", "ts": time.time()}) + "\n")

        removed = spawn.tmp_resource_sweep(ledger_path=ledger)

        assert removed == 1
        assert not worktree.exists()
        assert live_sibling.exists()
