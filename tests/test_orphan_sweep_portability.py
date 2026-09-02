"""issue-3118 — portability of sweep-orphans' liveness check and
temp-root resolution.

`/proc/<pid>` does not exist on macOS: any liveness check shaped like
`os.path.exists(f"/proc/{pid}")` returns False for every pid there, which
would classify every live verification session as dead and delete work
in flight. `sweep_orphans()`'s liveness comes from `_live_workspaces_union()`
-> roster `_alive()`, which is `os.kill(pid, 0)` -- this module pins that
it stays that way.

macOS also gives each user a private scratch root under `$TMPDIR`
(`/var/folders/...`), not `/tmp` -- `_sweep_temp_roots()` must resolve the
platform's real temp dir via `tempfile.gettempdir()` rather than a
hardcoded `/tmp` literal, while still also sweeping literal `/tmp` (this
project's own verification briefs write `/tmp/...` paths directly).

  python3 -m pytest tests/test_orphan_sweep_portability.py -q
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

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


def _forbid_proc_reads():
    """Patches `os.path.exists` so any call that touches a `/proc` path
    raises -- everything else passes through untouched. Used to prove the
    liveness check never depends on `/proc`, which simply does not exist
    on macOS."""
    real_exists = os.path.exists

    def _guarded(path):
        if "/proc" in str(path):
            raise AssertionError(
                "liveness check must not read /proc -- it does not exist "
                "on macOS and would misclassify every live pid as dead")
        return real_exists(path)

    return mock.patch("os.path.exists", side_effect=_guarded)


def test_liveness_true_for_current_process_without_reading_proc():
    with _forbid_proc_reads():
        assert spawn._alive(os.getpid()) is True


def test_liveness_false_for_nonexistent_pid_without_reading_proc():
    dead = _dead_pid()
    with _forbid_proc_reads():
        assert spawn._alive(dead) is False


def test_liveness_used_by_worktree_scan_is_the_same_portable_check(tmp_path):
    """sweep_orphans()'s worktree scan derives liveness from
    _live_workspaces_union(), which is built on roster._alive() -- confirm
    the wiring, not just the primitive in isolation."""
    owner_repo = tmp_path / "owner-repo"
    admin = owner_repo / ".git" / "worktrees" / "wt"
    admin.mkdir(parents=True)
    entry = tmp_path / "wt"
    entry.mkdir()
    (entry / ".git").write_text(f"gitdir: {admin}\n")

    import time
    now = time.time() + 100_000
    with _forbid_proc_reads():
        live = {owner_repo.resolve(): {"pid": os.getpid()}}
        results = spawn._scan_orphan_worktrees(
            [tmp_path], live=live, unreadable=[], now=now,
            min_age_seconds=60)
    assert results == []  # live owner survives without ever touching /proc


def test_temp_root_resolution_follows_tempfile_gettempdir_not_hardcoded():
    fake_root = tempfile.mkdtemp(prefix="muster-fake-tmpdir-")
    try:
        with mock.patch("tempfile.gettempdir", return_value=fake_root):
            roots = spawn._sweep_temp_roots()
        assert Path(fake_root) in roots
    finally:
        os.rmdir(fake_root)


def test_temp_root_resolution_also_sweeps_literal_tmp():
    """The issue notes this session's own verification briefs write
    literal `/tmp/...` paths regardless of platform -- both locations
    must be swept, not just whichever `tempfile.gettempdir()` names."""
    with mock.patch("tempfile.gettempdir", return_value="/some/fake/var/folders/x"):
        roots = spawn._sweep_temp_roots()
    assert Path("/tmp") in roots
    assert Path("/some/fake/var/folders/x") in roots


def test_temp_root_resolution_dedupes_when_tmpdir_is_literal_tmp():
    """On Linux, tempfile.gettempdir() is typically /tmp itself -- must
    not sweep it twice."""
    with mock.patch("tempfile.gettempdir", return_value="/tmp"):
        roots = spawn._sweep_temp_roots()
    assert roots.count(Path("/tmp")) == 1
