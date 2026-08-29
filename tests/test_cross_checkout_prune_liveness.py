"""Issue #2492: `_live_workspaces()` (backing `ROSTER` liveness for two
prune paths) was checkout-scoped -- it only ever consulted the calling
checkout's own `runs/active.json`. On a host with many checkouts sharing
one `~/.tokenmaxxxer/work` (`MUSTER_STATE_ROOT` unset -- the one override
that would unify them), each checkout resolves its own
ROOT/STATE_ROOT/ROSTER independently. A prune running from checkout A
could treat a session as dead purely because checkout B's roster --
which actually knows the session is live -- was invisible to A.

Fix: `lifecycle._live_workspaces_union()` widens `_live_workspaces()`
with sibling checkouts' rosters -- immediate children of the shared work
dir (`_workspace_base()`) that resolve as checkout roots (contain their
own `spawn.py`), bounded to one level, malformed/unreadable siblings
degrading to zero live sessions rather than raising. Both prune call
sites (`_prune_orphaned_sidecars()`, issue #2443, and `auto_sweep()`'s
workspace-directory prune, issue #2383/#2411) now consult the union.

Each prune path gets the same three-part story:
  - pre-fix repro: with the union temporarily swapped back to the old
    checkout-local lookup, the real prune function actually deletes a
    file/directory whose session is live only in checkout B's roster;
  - fix: with the union wired in (default), that file/directory survives;
  - regression: an entry live in NEITHER checkout's roster is still
    pruned by both paths -- the fix isn't a permanent no-op.

  python3 -m pytest tests/test_cross_checkout_prune_liveness.py -v
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


def _dead_pid() -> int:
    """A pid guaranteed not to be alive: fork, exit immediately, reap.
    Same pattern as tests/test_tmp_resource_gc.py's `_dead_pid()`."""
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0)
    return pid


def _git(args: list[str], cwd: Path) -> None:
    r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True,
                        text=True)
    assert r.returncode == 0, f"git {args} in {cwd} failed: {r.stderr}"


def _make_pushed_git_workspace(path: Path) -> None:
    """A workspace dir that `_workspace_clean_state()` finds safe-to-
    delete on its own merits (no uncommitted changes, no commits the
    remote doesn't have) -- so the ONLY thing standing between it and
    deletion in these tests is the liveness check under test."""
    path.mkdir(parents=True)
    _git(["init", "-q"], path)
    _git(["config", "user.email", "test@example.com"], path)
    _git(["config", "user.name", "Test"], path)
    (path / "f.txt").write_text("x")
    _git(["add", "f.txt"], path)
    _git(["commit", "-q", "-m", "init"], path)
    remote = path.parent / (path.name + "-remote.git")
    _git(["init", "-q", "--bare", str(remote)], path.parent)
    _git(["remote", "add", "origin", str(remote)], path)
    _git(["push", "-q", "-u", "origin", "HEAD"], path)


class _TwoCheckoutFixture(unittest.TestCase):
    """Shared setup: `shared/` (the parent work dir, `_workspace_base()`)
    containing `checkout-a/` and `checkout-b/`, each with its own
    `spawn.py` marker + `runs/active.json` roster -- the same layout the
    real per-checkout ROOT/STATE_ROOT/ROSTER convention produces. Tests
    run "from checkout A": `spawn.ROOT`/`spawn.ROSTER` point at A. A live
    session is registered in B's roster only, never A's."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.shared = Path(self._td.name) / "work"
        self.checkout_a = self.shared / "checkout-a"
        self.checkout_b = self.shared / "checkout-b"
        for c in (self.checkout_a, self.checkout_b):
            c.mkdir(parents=True)
            (c / "spawn.py").write_text("# fixture checkout marker\n")
            (c / "runs").mkdir()
            (c / "runs" / "active.json").write_text("{}")

        patches = [
            mock.patch.object(spawn, "ROOT", self.checkout_a),
            mock.patch.object(spawn, "ROSTER",
                               self.checkout_a / "runs" / "active.json"),
            mock.patch.object(spawn, "_workspace_base", lambda: self.shared),
            # The merge-trigger (#2447) shells out to `gh` -- irrelevant to
            # this fix and out of scope; keep it a permanent no-op so the
            # age/size + liveness path is the only thing under test.
            mock.patch.object(spawn, "_workspace_merge_trigger_status",
                               lambda w: (False, "pr-check-failed")),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def _set_b_roster(self, entries: dict) -> None:
        (self.checkout_b / "runs" / "active.json").write_text(
            json.dumps(entries))


class SidecarPruneCrossCheckoutTest(_TwoCheckoutFixture):
    """Issue #2443 sidecar-prune path, cross-checkout liveness (#2492)."""

    def _write_sidecar_set(self, name: str, mtime: float) -> list[Path]:
        files = [
            self.shared / f"{name}.events.jsonl",
            self.shared / f"{name}.events.offset",
            self.shared / f"{name}.watcher.log",
            self.shared / f"{name}.task.txt",
            self.shared / f"{name}.session.20260101T000000.123.log",
        ]
        for f in files:
            f.write_text("x")
            os.utime(f, (mtime, mtime))
        return files

    def test_pre_fix_local_lookup_misses_live_sibling_session(self):
        """The old checkout-local lookup, called directly from checkout
        A's context, wrongly reports checkout B's live session as dead."""
        work_dir = self.shared / "proj-issue-1-implementation"
        self._set_b_roster({
            "issue-1/implementation": {
                "pid": os.getpid(), "work": str(work_dir),
                "issue": 1, "skill": "implementation",
            }
        })
        old_local_live = spawn._live_workspaces()
        self.assertNotIn(work_dir.resolve(), old_local_live,
                          "pre-fix local-only lookup should NOT see "
                          "checkout B's live session -- that's the bug")

    def test_pre_fix_prune_deletes_sidecars_of_sibling_live_session(self):
        """Concrete repro: with the union swapped back to the old
        checkout-local lookup, the real sidecar-prune function deletes
        files tied to a session that's live only in checkout B."""
        name = "proj-issue-2-implementation"
        work_dir = self.shared / name
        self._set_b_roster({
            "issue-2/implementation": {
                "pid": os.getpid(), "work": str(work_dir),
                "issue": 2, "skill": "implementation",
            }
        })
        now = 2_000_000_000.0
        files = self._write_sidecar_set(name, now - 30 * 86400)
        with mock.patch.object(spawn, "_live_workspaces_union",
                                lambda: (spawn._live_workspaces(), [])):
            outcome = spawn._prune_orphaned_sidecars(
                self.shared, max_age_days=14, now=now)
        self.assertEqual(outcome["removed"], len(files),
                          "pre-fix: sidecars of a live-in-B session get "
                          "wrongly pruned")
        for f in files:
            self.assertFalse(f.exists())

    def test_fix_prune_keeps_sidecars_of_sibling_live_session(self):
        """The sidecar prune, run from checkout A with the fix wired in,
        must NOT remove files paired with checkout B's live session."""
        name = "proj-issue-3-implementation"
        work_dir = self.shared / name
        self._set_b_roster({
            "issue-3/implementation": {
                "pid": os.getpid(), "work": str(work_dir),
                "issue": 3, "skill": "implementation",
            }
        })
        now = 2_000_000_000.0
        files = self._write_sidecar_set(name, now - 30 * 86400)
        outcome = spawn._prune_orphaned_sidecars(
            self.shared, max_age_days=14, now=now)
        self.assertEqual(outcome["removed"], 0)
        self.assertEqual(outcome["kept"], 1)
        for f in files:
            self.assertTrue(f.exists(), f"{f} wrongly removed")

    def test_dead_sibling_roster_entry_does_not_block_prune(self):
        """A stale entry in B's roster (dead pid) must not block prune --
        the union only carries over pid-alive entries, same contract as
        the local `_live_workspaces()`."""
        name = "proj-issue-4-implementation"
        work_dir = self.shared / name
        self._set_b_roster({
            "issue-4/implementation": {
                "pid": _dead_pid(), "work": str(work_dir),
                "issue": 4, "skill": "implementation",
            }
        })
        now = 2_000_000_000.0
        files = self._write_sidecar_set(name, now - 30 * 86400)
        outcome = spawn._prune_orphaned_sidecars(
            self.shared, max_age_days=14, now=now)
        self.assertEqual(outcome["removed"], len(files))
        for f in files:
            self.assertFalse(f.exists())

    def test_regression_dead_everywhere_still_pruned(self):
        """An entry live in NEITHER checkout's roster is still pruned --
        the fix must not make sidecar-prune a permanent no-op."""
        name = "proj-issue-9-implementation"
        now = 2_000_000_000.0
        files = self._write_sidecar_set(name, now - 30 * 86400)
        # both rosters stay {} -- nothing live anywhere
        outcome = spawn._prune_orphaned_sidecars(
            self.shared, max_age_days=14, now=now)
        self.assertEqual(outcome["removed"], len(files))
        for f in files:
            self.assertFalse(f.exists())


class WorkspaceDirPruneCrossCheckoutTest(_TwoCheckoutFixture):
    """Issue #2383/#2411 `auto_sweep()` workspace-directory prune path,
    cross-checkout liveness (#2492)."""

    def test_pre_fix_prune_deletes_dir_of_sibling_live_session(self):
        """Concrete repro: with the union swapped back to the old
        checkout-local lookup, `auto_sweep()` deletes a workspace
        directory whose session is live only in checkout B's roster."""
        work_dir = self.shared / "proj-issue-5-implementation"
        _make_pushed_git_workspace(work_dir)
        now = 2_000_000_000.0
        os.utime(work_dir, (now - 30 * 86400, now - 30 * 86400))
        self._set_b_roster({
            "issue-5/implementation": {
                "pid": os.getpid(), "work": str(work_dir),
                "issue": 5, "skill": "implementation",
            }
        })
        with mock.patch.object(spawn, "_live_workspaces_union",
                                lambda: (spawn._live_workspaces(), [])):
            outcome = spawn.auto_sweep(self.shared, max_age_days=14,
                                        max_bytes=10 ** 12, now=now)
        self.assertEqual(outcome["removed"], 1,
                          "pre-fix: a dir live only in B's roster gets "
                          "wrongly swept")
        self.assertFalse(work_dir.exists())

    def test_fix_prune_keeps_dir_of_sibling_live_session(self):
        """`auto_sweep()`, run from checkout A with the fix wired in,
        must NOT remove a workspace directory whose session is live only
        in checkout B's roster."""
        work_dir = self.shared / "proj-issue-6-implementation"
        _make_pushed_git_workspace(work_dir)
        now = 2_000_000_000.0
        os.utime(work_dir, (now - 30 * 86400, now - 30 * 86400))
        self._set_b_roster({
            "issue-6/implementation": {
                "pid": os.getpid(), "work": str(work_dir),
                "issue": 6, "skill": "implementation",
            }
        })
        outcome = spawn.auto_sweep(self.shared, max_age_days=14,
                                    max_bytes=10 ** 12, now=now)
        self.assertEqual(outcome["removed"], 0)
        self.assertTrue(work_dir.is_dir())

    def test_dead_sibling_roster_entry_does_not_block_prune(self):
        """A stale entry in B's roster (dead pid) must not block prune."""
        work_dir = self.shared / "proj-issue-8-implementation"
        _make_pushed_git_workspace(work_dir)
        now = 2_000_000_000.0
        os.utime(work_dir, (now - 30 * 86400, now - 30 * 86400))
        self._set_b_roster({
            "issue-8/implementation": {
                "pid": _dead_pid(), "work": str(work_dir),
                "issue": 8, "skill": "implementation",
            }
        })
        outcome = spawn.auto_sweep(self.shared, max_age_days=14,
                                    max_bytes=10 ** 12, now=now)
        self.assertEqual(outcome["removed"], 1)
        self.assertFalse(work_dir.exists())

    def test_regression_dead_everywhere_still_swept(self):
        """A workspace dir live in NEITHER checkout's roster is still
        swept -- the fix must not neuter the prune."""
        work_dir = self.shared / "proj-issue-7-implementation"
        _make_pushed_git_workspace(work_dir)
        now = 2_000_000_000.0
        os.utime(work_dir, (now - 30 * 86400, now - 30 * 86400))
        # both rosters stay {} -- nothing live anywhere
        outcome = spawn.auto_sweep(self.shared, max_age_days=14,
                                    max_bytes=10 ** 12, now=now)
        self.assertEqual(outcome["removed"], 1)
        self.assertFalse(work_dir.exists())


class SiblingDiscoveryBoundaryTest(_TwoCheckoutFixture):
    """Requirement 4/design-note guarantees: discovery is bounded to
    immediate children that resolve as checkout roots, and a malformed
    sibling roster does not crash or block the prune."""

    def test_sibling_checkout_roots_skips_non_checkout_dirs(self):
        not_a_checkout = self.shared / "just-a-workspace"
        not_a_checkout.mkdir()
        roots = spawn._sibling_checkout_roots(self.shared)
        self.assertNotIn(not_a_checkout, roots)
        self.assertIn(self.checkout_a, roots)
        self.assertIn(self.checkout_b, roots)

    def test_malformed_sibling_roster_does_not_crash_and_keeps_workspace(self):
        """Issue #2603: a corrupt (as opposed to absent) sibling roster used
        to degrade to "zero live sessions", which made this workspace look
        provably dead and get swept -- exactly the defect this issue fixes.
        It must now survive as unknown-liveness, not get deleted, and the
        sweep must still finish rather than raising."""
        (self.checkout_b / "runs" / "active.json").write_text(
            "{not valid json")
        work_dir = self.shared / "proj-issue-10-implementation"
        _make_pushed_git_workspace(work_dir)
        now = 2_000_000_000.0
        os.utime(work_dir, (now - 30 * 86400, now - 30 * 86400))
        # must not raise despite B's roster being corrupt
        outcome = spawn.auto_sweep(self.shared, max_age_days=14,
                                    max_bytes=10 ** 12, now=now)
        self.assertEqual(outcome["removed"], 0)
        self.assertTrue(work_dir.is_dir())


class UnreadableSiblingRosterPruneTest(_TwoCheckoutFixture):
    """Issue #2603: `_sibling_live_sessions()` used to fold "roster file
    exists but can't be read/parsed" into the same `{}` result as "roster
    file absent", so both prune paths read a broken sibling as "sibling has
    no live sessions" -- silently making that sibling's live workspaces
    prunable. A corrupt sibling roster must now read as unknown, and unknown
    liveness must keep a workspace, not delete it -- while genuinely dead
    entries elsewhere (no ambiguity involved) are still pruned in the same
    run, and the run still completes and names the sibling it could not
    read."""

    def _corrupt_b_roster(self) -> None:
        (self.checkout_b / "runs" / "active.json").write_text(
            "{not: valid json, at all")

    def test_workspace_survives_both_prune_paths_when_sibling_roster_corrupt(self):
        name = "proj-issue-20-implementation"
        work_dir = self.shared / name
        _make_pushed_git_workspace(work_dir)
        now = 2_000_000_000.0
        os.utime(work_dir, (now - 30 * 86400, now - 30 * 86400))
        files = self._write_sidecar_files(name, now - 30 * 86400)
        self._corrupt_b_roster()

        sweep_outcome = spawn.auto_sweep(self.shared, max_age_days=14,
                                          max_bytes=10 ** 12, now=now)
        self.assertEqual(sweep_outcome["removed"], 0)
        self.assertTrue(work_dir.is_dir(),
                         "workspace under an unreadable sibling roster must "
                         "survive the workspace-dir prune path")

        sidecar_outcome = spawn._prune_orphaned_sidecars(
            self.shared, max_age_days=14, now=now)
        self.assertEqual(sidecar_outcome["removed"], 0)
        for f in files:
            self.assertTrue(f.exists(),
                             "sidecars of a workspace under an unreadable "
                             "sibling roster must survive the sidecar-prune "
                             "path too")

    def test_prune_completes_prunes_dead_elsewhere_and_names_unreadable_sibling(self):
        name = "proj-issue-21-implementation"
        work_dir = self.shared / name
        _make_pushed_git_workspace(work_dir)
        now = 2_000_000_000.0
        os.utime(work_dir, (now - 30 * 86400, now - 30 * 86400))
        self._corrupt_b_roster()

        # Genuinely dead elsewhere: an orphaned sidecar set whose paired
        # workspace directory is already gone -- its deadness doesn't
        # depend on any roster (sibling or local), so B's corruption must
        # not block it.
        dead_files = self._write_sidecar_files(
            "proj-issue-22-implementation", now - 30 * 86400)

        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            sweep_outcome = spawn.auto_sweep(
                self.shared, max_age_days=14, max_bytes=10 ** 12, now=now)
        sweep_stderr = buf.getvalue()

        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            sidecar_outcome = spawn._prune_orphaned_sidecars(
                self.shared, max_age_days=14, now=now)
        sidecar_stderr = buf.getvalue()

        # completes (no exception) and keeps the ambiguous workspace
        self.assertEqual(sweep_outcome["removed"], 0)
        self.assertTrue(work_dir.is_dir())
        # genuinely dead entry elsewhere is still pruned in the same run
        self.assertEqual(sidecar_outcome["removed"], len(dead_files))
        for f in dead_files:
            self.assertFalse(f.exists())
        # names the sibling it could not read
        b_root = str(self.checkout_b.resolve())
        self.assertTrue(
            any(b_root in line for line in sweep_stderr.splitlines()),
            f"expected auto_sweep to name {b_root} as unreadable, got: "
            f"{sweep_stderr!r}")
        self.assertTrue(
            any(b_root in line for line in sidecar_stderr.splitlines()),
            f"expected sidecar-prune to name {b_root} as unreadable, got: "
            f"{sidecar_stderr!r}")

    def test_missing_sibling_roster_file_stays_prunable(self):
        """A sibling that has never spawned (no runs/active.json at all) is
        a legitimate empty state, not "unknown" -- must not regress to
        unprunable."""
        (self.checkout_b / "runs" / "active.json").unlink()
        name = "proj-issue-23-implementation"
        work_dir = self.shared / name
        _make_pushed_git_workspace(work_dir)
        now = 2_000_000_000.0
        os.utime(work_dir, (now - 30 * 86400, now - 30 * 86400))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            outcome = spawn.auto_sweep(self.shared, max_age_days=14,
                                        max_bytes=10 ** 12, now=now)
        self.assertEqual(outcome["removed"], 1)
        self.assertFalse(work_dir.exists())
        self.assertNotIn("확인 불가", buf.getvalue())

    def _write_sidecar_files(self, name: str, mtime: float) -> list[Path]:
        files = [
            self.shared / f"{name}.events.jsonl",
            self.shared / f"{name}.events.offset",
            self.shared / f"{name}.watcher.log",
            self.shared / f"{name}.task.txt",
            self.shared / f"{name}.session.20260101T000000.123.log",
        ]
        for f in files:
            f.write_text("x")
            os.utime(f, (mtime, mtime))
        return files


if __name__ == "__main__":
    unittest.main()
