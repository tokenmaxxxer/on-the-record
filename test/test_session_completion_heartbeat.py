"""Issue #2904: a session that finishes normally removes its own roster
entry in `_spawn_one()`'s tail (spawn.py, right after `proc.wait()`) --
before the NEXT `roster_watchdog()` tick ever runs. The existing dead-scan
`[poll-report] ...: COMPLETED` line (watchdog.py) only fires for a session
whose *owning process itself* crashed before reaching that self-removal --
a rare race, not the common exit path. For the common path, nothing ever
told the Monitor heartbeat that a session finished; the orchestrator's
"진행 중입니다" answer during that gap was never contradicted.

This tests the fix directly: `_spawn_one()`'s tail records the completion
fact (issue/skill/session/PR/outcome) to a small queue
(`spawn.PENDING_COMPLETIONS`) the moment it is known, and the very next
`roster_watchdog()` tick drains that queue into the same
`[poll-report] ...: COMPLETED` line -- even on a tick where the roster is
now completely empty (the exact case the old dead-scan loop can never
reach, since it only iterates over registered roster entries)."""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402
import watchdog  # noqa: E402


class PendingCompletionsQueueTest(unittest.TestCase):
    """Pure queue semantics: write, one-shot drain, empty-state."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.orig_path = spawn.PENDING_COMPLETIONS
        spawn.PENDING_COMPLETIONS = Path(self._tmpdir.name) / "pending-completions.jsonl"

    def tearDown(self):
        spawn.PENDING_COMPLETIONS = self.orig_path
        self._tmpdir.cleanup()

    def test_empty_state_drains_nothing(self):
        self.assertEqual(spawn._drain_pending_completions(), ([], None, 0))

    def test_recorded_completion_drains_once(self):
        spawn._record_session_completion("issue-2894/verification", 2894,
                                         "verification", "sess-abc", 2897,
                                         "progressed")
        entries, err, _dropped = spawn._drain_pending_completions()
        self.assertIsNone(err)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["issue"], 2894)
        self.assertEqual(entries[0]["pr_number"], 2897)
        self.assertEqual(entries[0]["session_id"], "sess-abc")
        # one-shot: draining again returns nothing new
        self.assertEqual(spawn._drain_pending_completions(), ([], None, 0))

    def test_pr_missing_is_recorded_as_none_not_dropped(self):
        spawn._record_session_completion("issue-1/implementation", 1,
                                         "implementation", "sess-xyz", None,
                                         "refused")
        entries, err, _dropped = spawn._drain_pending_completions()
        self.assertIsNone(err)
        self.assertEqual(len(entries), 1)
        self.assertIsNone(entries[0]["pr_number"])

    def test_write_failure_is_advisory_not_raised(self):
        """silent-failure-audit self-review finding: the queue is a pure
        observation side-channel -- a disk/permission failure writing to
        it must never propagate out of `_spawn_one()`'s completion tail
        (it would abort push/gate-report/self-trigger-respawn for a
        session that otherwise finished fine)."""
        with mock.patch.object(Path, "mkdir",
                               side_effect=OSError("disk full")):
            spawn._record_session_completion("issue-9/x", 9, "x", None,
                                              None, "progressed")
        # no exception raised -- and nothing was queued
        self.assertEqual(spawn._drain_pending_completions(), ([], None, 0))

    def test_read_failure_is_reported_as_error_not_silent_empty(self):
        """Same shape this issue is about, one layer down: a queue the
        watchdog can't read must not look identical to a queue that is
        genuinely empty -- the caller needs to tell "nothing happened"
        apart from "couldn't check.\""""
        spawn._record_session_completion("issue-9/x", 9, "x", None, None,
                                         "progressed")
        with mock.patch.object(Path, "read_text",
                               side_effect=OSError("permission denied")):
            entries, err, _dropped = spawn._drain_pending_completions()
        self.assertEqual(entries, [])
        self.assertIsNotNone(err)


class RosterWatchdogEmitsCompletionTest(unittest.TestCase):
    """Regression for the exact gap: a fully-drained roster (the common
    shape right after a session's own self-removal) must still surface a
    queued completion -- the old dead-scan loop is inside the `for key, e
    in sorted(d.items())` scan and never runs at all once `d` is empty
    (`roster_watchdog()`'s `if not d:` early return, watchdog.py)."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.orig_path = spawn.PENDING_COMPLETIONS
        spawn.PENDING_COMPLETIONS = Path(self._tmpdir.name) / "pending-completions.jsonl"
        self._patchers = [
            mock.patch.object(spawn, "_roster_load", lambda: {}),
            mock.patch.object(spawn, "_board_wide_sweep_all", lambda root, d_all: 0),
            mock.patch.object(spawn, "lease_reconcile_sweep", lambda root, d_all: 0),
            mock.patch.object(spawn, "spawn_attempt_sweep", lambda d_all: 0),
            mock.patch.object(spawn, "tmp_resource_sweep", lambda: None),
            mock.patch.object(spawn, "standing_red_check", lambda root: []),
            mock.patch.object(spawn, "_undispositioned_skill_prs",
                              lambda root: ([], True)),
            mock.patch.object(spawn, "_print_returned_pr_surfaced",
                              lambda blockers, source: None),
            mock.patch.object(spawn, "_roster_own", lambda d_all, all_scope: {}),
        ]
        for p in self._patchers:
            p.start()

    def tearDown(self):
        for p in self._patchers:
            p.stop()
        spawn.PENDING_COMPLETIONS = self.orig_path
        self._tmpdir.cleanup()

    def test_completion_surfaces_even_with_fully_empty_roster(self):
        spawn._record_session_completion("issue-2894/verification", 2894,
                                         "verification", "sess-abc", 2897,
                                         "progressed")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = watchdog.roster_watchdog(root=Path(self._tmpdir.name))
        out = buf.getvalue()
        self.assertIn("[poll-report] issue-2894/verification: COMPLETED", out)
        self.assertIn("issue #2894", out)
        self.assertIn("session sess-abc", out)
        self.assertIn("PR #2897", out)
        # completion is informational, not an anomaly -- must not flip the
        # exit code (roster_watchdog()'s rc is the anomaly count, per its
        # own docstring/spawn.py:2445 contract).
        self.assertEqual(rc, 0)

    def test_no_completion_emits_nothing_extra(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            watchdog.roster_watchdog(root=Path(self._tmpdir.name))
        out = buf.getvalue()
        self.assertNotIn("COMPLETED", out)
        self.assertNotIn("poll-report", out)


if __name__ == "__main__":
    unittest.main()
