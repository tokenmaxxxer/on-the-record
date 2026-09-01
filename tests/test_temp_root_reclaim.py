"""Issue #2973: sessions were creating temp repo roots (e.g. repo copies
and Rust build trees under a self-chosen `/tmp/tas-*-repos`, via a
session-picked `TAS_REPOS_ROOT`) that the plugin never knew about, so
nothing ever reclaimed them -- `~/.tokenmaxxxer/work` is swept by
`auto_sweep()`/`roster_clean()`, but that location sat entirely outside
every reclamation mechanism.

Fix: `lifecycle.session_temp_root(roster_key)` resolves a session's temp
repo root under a plugin-managed base (`lifecycle._temp_repos_base()`,
deliberately distinct from `_workspace_base()` -- widening reclamation to
`~/.tokenmaxxxer/work` is issue #2960's scope, not this one's), and
`lifecycle.sweep_temp_repos()` reclaims that base by age alone. The sweep
never depends on the session running any cleanup of its own (a session
killed mid-run still gets reclaimed once its temp root ages out), never
sweeps `/tmp` by name pattern (it only ever looks under the explicit
plugin-managed base), and never removes a temp root whose roster key is
still pid-alive.

    python3 -m pytest tests/ -k temp_root_is_managed -q
    python3 -m pytest tests/ -k temp_root_swept_without_session_cooperation -q
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class TempRootIsManagedTest(unittest.TestCase):
    """A session's temp repo root resolves to a plugin-managed location,
    not one the session chooses freely."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.base = Path(self._td.name) / "tmp-repos"
        p = mock.patch.dict(os.environ,
                             {"MUSTER_TEMP_REPOS_ROOT": str(self.base)})
        p.start()
        self.addCleanup(p.stop)

    def test_temp_root_is_managed_under_plugin_base_not_bare_tmp(self):
        root = spawn.session_temp_root("issue-42/implementation")
        self.assertTrue(
            str(root).startswith(str(self.base)),
            f"{root} must resolve under the plugin-managed base {self.base}")
        self.assertNotIn("/tmp/tas-", str(root))
        self.assertTrue(root.is_dir())

    def test_temp_root_is_managed_distinct_per_session(self):
        a = spawn.session_temp_root("issue-1/implementation")
        b = spawn.session_temp_root("issue-2/implementation")
        self.assertNotEqual(a, b)
        self.assertEqual(a.parent, self.base)
        self.assertEqual(b.parent, self.base)

    def test_temp_root_is_managed_distinct_from_workspace_base(self):
        """must not: do not widen this to touch `~/.tokenmaxxxer/work`
        reclamation -- issue #2960's scope -- so the managed temp-repos
        base has to be a different location than `_workspace_base()`."""
        self.assertNotEqual(spawn._temp_repos_base(), spawn._workspace_base())

    def test_temp_root_is_managed_defaults_outside_tmp(self):
        p = mock.patch.dict(os.environ, {}, clear=False)
        p.start()
        try:
            os.environ.pop("MUSTER_TEMP_REPOS_ROOT", None)
            default_base = spawn._temp_repos_base()
        finally:
            p.stop()
        self.assertNotEqual(default_base, Path("/tmp"))
        self.assertFalse(str(default_base).startswith("/tmp"))


class TempRootSweptWithoutSessionCooperationTest(unittest.TestCase):
    """Reclamation covers the managed temp-repos location on an age basis
    and does not depend on the session running any cleanup of its own."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.base = Path(self._td.name) / "tmp-repos"
        self.base.mkdir()

    def _age_entry(self, name: str, age_days: float, now: float) -> Path:
        d = self.base / name
        (d / "build").mkdir(parents=True)
        f = d / "build" / "artifact"
        f.write_text("x")
        mtime = now - age_days * 86400
        os.utime(f, (mtime, mtime))
        os.utime(d, (mtime, mtime))
        return d

    def test_temp_root_swept_without_session_cooperation_reclaims_dead_entry(self):
        """A session that dies at a turn limit or crashes before reaching
        its own cleanup code still has its temp root reclaimed -- the
        sweep never calls into session code, it only reads mtimes."""
        now = 2_000_000_000.0
        old = self._age_entry("adhoc-implementation-9999", age_days=30,
                               now=now)
        with mock.patch.object(spawn, "_roster_load", lambda: {}):
            outcome = spawn.sweep_temp_repos(base=self.base, max_age_days=14,
                                              now=now)
        self.assertEqual(outcome["removed"], 1)
        self.assertFalse(old.exists())

    def test_temp_root_swept_without_session_cooperation_keeps_young_entry(self):
        now = 2_000_000_000.0
        young = self._age_entry("adhoc-implementation-1111", age_days=1,
                                 now=now)
        with mock.patch.object(spawn, "_roster_load", lambda: {}):
            outcome = spawn.sweep_temp_repos(base=self.base, max_age_days=14,
                                              now=now)
        self.assertEqual(outcome["removed"], 0)
        self.assertTrue(young.is_dir())

    def test_temp_root_swept_without_session_cooperation_spares_live_session(self):
        """must not: never delete a temp root belonging to a live
        session, even if it looks old."""
        now = 2_000_000_000.0
        roster_key = "issue-5/implementation"
        live = self._age_entry(roster_key.replace("/", "-"), age_days=30,
                                now=now)
        roster = {roster_key: {"pid": os.getpid()}}
        with mock.patch.object(spawn, "_roster_load", lambda: roster), \
             mock.patch.object(spawn, "_alive", lambda pid: True):
            outcome = spawn.sweep_temp_repos(base=self.base, max_age_days=14,
                                              now=now)
        self.assertEqual(outcome["removed"], 0)
        self.assertTrue(live.is_dir())

    def test_temp_root_swept_without_session_cooperation_dead_roster_entry_still_reclaimed(self):
        """A stale roster entry (dead pid) must not block the sweep --
        same liveness contract as the existing workspace prune paths."""
        now = 2_000_000_000.0
        roster_key = "issue-6/implementation"
        old = self._age_entry(roster_key.replace("/", "-"), age_days=30,
                               now=now)
        roster = {roster_key: {"pid": 999999}}
        with mock.patch.object(spawn, "_roster_load", lambda: roster), \
             mock.patch.object(spawn, "_alive", lambda pid: False):
            outcome = spawn.sweep_temp_repos(base=self.base, max_age_days=14,
                                              now=now)
        self.assertEqual(outcome["removed"], 1)
        self.assertFalse(old.exists())

    def test_temp_root_swept_without_session_cooperation_empty_state_sweeps_zero(self):
        empty_base = self.base / "empty"
        with mock.patch.object(spawn, "_roster_load", lambda: {}):
            outcome = spawn.sweep_temp_repos(base=empty_base, max_age_days=14)
        self.assertEqual(outcome, {"removed": 0, "kept": 0, "failed": 0})

    def test_temp_root_swept_without_session_cooperation_never_touches_slash_tmp(self):
        """must not: do not sweep `/tmp` by name pattern -- the sweep only
        ever looks under the explicit `base` argument it's given."""
        now = 2_000_000_000.0
        canary = Path("/tmp") / "tas-99999-repos-canary-2973"
        canary.mkdir(exist_ok=True)
        try:
            os.utime(canary, (now - 999 * 86400, now - 999 * 86400))
            with mock.patch.object(spawn, "_roster_load", lambda: {}):
                spawn.sweep_temp_repos(base=self.base, max_age_days=14,
                                        now=now)
            self.assertTrue(
                canary.exists(),
                "sweep must never touch /tmp by name pattern")
        finally:
            canary.rmdir()


if __name__ == "__main__":
    unittest.main()
