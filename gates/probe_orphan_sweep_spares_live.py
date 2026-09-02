#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3118.

Measured after one day of heavy parallel-session use: 193 `/tmp` git
worktree directories, of which `git worktree list` (run from any repo
still on disk) knows about only 3. The other 190 were created directly by
verification-session bash (`git worktree add /tmp/pr3085-verify`), never
through `session_temp_root()` -- so neither `git worktree prune` nor
`auto_sweep()` can see them once the checkout that registered them (the
verification session's own throwaway workspace) is itself gone.

This probe must FAIL against current `main`: `spawn.sweep_orphans` does
not exist there at all, so importing it raises `AttributeError` -- there
is no mechanism a first `--dry-run` could inspect before anything is
deleted. Against this branch, it builds a real live session's worktree +
session-log pair alongside a real orphaned pair, runs the sweep for
real, and asserts:

  1. the live pair survives (an owning session that has been "running"
     for 40+ minutes must never be swept on age alone -- liveness is
     process state, checked via `_live_workspaces_union()`, never a
     hardcoded age threshold);
  2. the orphaned pair is gone;
  3. the symmetric negative -- a sweep of an environment with nothing
     orphaned removes nothing and says so explicitly, not silently.

Run as `python3 gates/probe_orphan_sweep_spares_live.py` from the repo
root, no arguments. Prints one line per assertion and `ok` on success;
prints `FAIL` lines and exits non-zero on any mismatch.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

failures: list[str] = []


def _fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL: {msg}")


def _dead_pid() -> int:
    """A pid guaranteed not to be alive: fork, exit immediately, reap --
    stands in for a verification session that crashed/was killed rather
    than exiting normally (the exact case the issue's must-not calls
    out: the cleaner must run regardless of how the session ended)."""
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0)
    return pid


def _make_worktree_pair(tmp_root: Path, name: str, owner_repo: Path) -> Path:
    """A `/tmp/<name>` directory shaped exactly like `git worktree add`'s
    output: a `.git` FILE pointing at `<owner_repo>/.git/worktrees/<name>`."""
    entry = tmp_root / name
    entry.mkdir()
    admin_dir = owner_repo / ".git" / "worktrees" / name
    admin_dir.mkdir(parents=True)
    (entry / ".git").write_text(f"gitdir: {admin_dir}\n")
    return entry


def main() -> int:
    try:
        import spawn
    except Exception as exc:  # noqa: BLE001 - this IS the current-main failure mode
        _fail(f"spawn module import raised {exc!r} before sweep-orphans could "
              f"even be reached -- expected on main (no sweep_orphans exists yet)")
        sys.exit(1)

    if not hasattr(spawn, "sweep_orphans"):
        _fail("spawn.sweep_orphans does not exist -- this is exactly the gap "
              "issue #3118 reports: no mechanism a --dry-run could inspect")
        sys.exit(1)

    scratch = Path(tempfile.mkdtemp(prefix="probe-orphan-sweep-"))
    try:
        wb = scratch / "work"
        wb.mkdir()
        tmp_root = scratch / "tmp-root"
        tmp_root.mkdir()

        # --- live session's worktree + log pair ----------------------------
        # A live session's own workspace directory is still on disk while it
        # runs -- _orphaned_sidecar_groups()'s first check is exactly that
        # (workspace_dir.exists()), so a faithful "live" fixture needs the
        # paired directory present, not just the log file.
        live_pid = os.getpid()  # this very process: unambiguously alive
        live_owner_repo = scratch / "live-owner-repo"
        live_owner_repo.mkdir()
        live_entry = _make_worktree_pair(tmp_root, "pr-live-verify", live_owner_repo)
        live_workspace = wb / "issue-1-implementation-live"
        live_workspace.mkdir()
        live_log = wb / "issue-1-implementation-live.session.20260101T000000.999998.log"
        live_log.write_text("live session stream\n")

        # --- orphaned worktree + log pair -----------------------------------
        dead_pid = _dead_pid()
        dead_owner_repo = scratch / "dead-owner-repo"
        dead_owner_repo.mkdir()
        orphan_entry = _make_worktree_pair(tmp_root, "pr-orphan-verify", dead_owner_repo)
        orphan_log = wb / "issue-2-implementation-dead.session.20260101T000000.999999.log"
        orphan_log.write_text("orphaned session stream\n")

        now = time.time() + 100_000  # comfortably past any create-time-race floor
        live = {live_owner_repo.resolve(): {"pid": live_pid}}

        # sweep_orphans() itself calls _live_workspaces_union() internally --
        # patch it so this probe controls exactly which owner is "live"
        # without needing a real roster file on disk.
        import unittest.mock as mock
        with mock.patch.object(spawn, "_live_workspaces_union",
                                return_value=(live, [])):
            report = spawn.sweep_orphans(
                wb, temp_roots=[tmp_root], now=now, min_age_seconds=60,
                dry_run=False)

        if live_entry.exists():
            print(f"ok: live worktree survived — {live_entry}")
        else:
            _fail(f"live worktree {live_entry} was deleted -- an owning "
                  f"session (pid {live_pid}, unambiguously alive) must "
                  f"never be swept")

        if live_log.exists():
            print(f"ok: live session log survived — {live_log}")
        else:
            _fail(f"live session log {live_log} was deleted")

        if not orphan_entry.exists():
            print(f"ok: orphaned worktree removed — {orphan_entry}")
        else:
            _fail(f"orphaned worktree {orphan_entry} (dead pid {dead_pid}) "
                  f"survived the sweep")

        if not orphan_log.exists():
            print(f"ok: orphaned session log removed — {orphan_log}")
        else:
            _fail(f"orphaned session log {orphan_log} survived the sweep")

        removed_paths = {item["path"] for item in report["tmp_worktrees"]}
        if orphan_entry in removed_paths and live_entry not in removed_paths:
            print("ok: report attributes the removal to the orphan, not the live pair")
        else:
            _fail(f"sweep_orphans() report does not cleanly separate live/orphan: "
                  f"{report['tmp_worktrees']!r}")

        # --- symmetric negative: nothing orphaned -> removes nothing --------
        empty_wb = scratch / "empty-work"
        empty_wb.mkdir()
        empty_tmp_root = scratch / "empty-tmp-root"
        empty_tmp_root.mkdir()
        empty_report = spawn.sweep_orphans(
            empty_wb, temp_roots=[empty_tmp_root], now=time.time(),
            min_age_seconds=3600, dry_run=True)
        if (not empty_report["tmp_worktrees"] and not empty_report["workspaces"]
                and not empty_report["sidecars"]):
            print("ok: empty environment reports zero candidates in every category")
        else:
            _fail(f"empty environment unexpectedly reported candidates: "
                  f"{empty_report!r}")

        import io
        import contextlib
        buf = io.StringIO()
        # sweep_orphans_cli() resolves its own temp roots via
        # _sweep_temp_roots() (real /tmp) when not told otherwise -- pin it
        # to the scratch root so this assertion is about the empty
        # environment this probe built, not whatever this host's own /tmp
        # happens to hold.
        with mock.patch.object(spawn, "_sweep_temp_roots",
                                return_value=[empty_tmp_root]), \
                contextlib.redirect_stdout(buf):
            spawn.sweep_orphans_cli(empty_wb, dry_run=True)
        cli_out = buf.getvalue()
        if "지울 후보 없음" in cli_out or "없음" in cli_out:
            print("ok: --dry-run says explicitly there is nothing to remove")
        else:
            _fail(f"--dry-run on an empty environment did not say so explicitly: "
                  f"{cli_out!r}")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    if failures:
        sys.exit(1)
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
