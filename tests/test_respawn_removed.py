"""Automatic respawn of crashed sessions is gone; the observation is not.

On 2026-09-03 one spawned session on issue #3245 became 90 sessions in
about twenty minutes, exhausted the account's GitHub API budget, and could
not be stopped from inside the tool: `spawn.py kill` removes the roster
entry, but the kill itself reads as a crash, which is the respawn path's
own trigger. `runs/respawn_state.json` from that machine showed the cap was
not holding either -- 90 of its 93 keys came from that one incident and 83
of the 93 recorded no attempt count at all, because since issue #2432 the
roster key carries a per-lease disambiguator that the respawn call did not
pass through, so most respawns minted a fresh key and a fresh budget.

The retry was removed rather than re-capped: outside that incident the same
state file held three keys in total, all from the same night, so the
feature had no record of ever helping.

What these tests pin down is the distinction that matters -- **removing the
retry must not remove the report**. A crashed session must still be
detected, still be commented on the issue, still emit its ledger event, and
still leave its workspace and log on disk. A silent removal would trade a
runaway for an observation loss, which is the worse of the two.

Layers, all against real entry points (only `gh`/network is mocked at the
process boundary, the idiom of tests/test_respawn_deliverable_gate.py,
whose crash fixture this file reuses):

  1. `NoRelaunchTest` -- `_record_dead_session()` never starts a process, on
     either of its two triggers, and stays idempotent per dead session.
  2. `StillReportsTest` -- the same call still comments, still writes its
     ledger event, and leaves workspace and log untouched.
  3. `WatchdogObservesUnconditionallyTest` -- the dead-entry scan no longer
     hides behind the retired `--auto-respawn` flag.
  4. `NoRetryBudgetTest` -- nothing is left that could be read as an
     allowance of retries.

  python3 -m pytest tests/test_respawn_removed.py -q
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))

import lifecycle  # noqa: E402
import spawn  # noqa: E402

lifecycle._sp = spawn

DEAD_PID = 999999999  # never a real pid


def _git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a],
                           capture_output=True, text=True, check=True)


class _CrashFixture(unittest.TestCase):
    """A real git workspace whose session pid is dead, so the production
    verdict path genuinely returns `crashed` rather than a mocked string."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        self.remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        self.work = self.tmp / "on-the-record-issue-9101-demo"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.work)], check=True)
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        (self.work / "a.txt").write_text("1")
        _git(self.work, "add", "a.txt")
        _git(self.work, "commit", "-q", "-m", "c1")
        _git(self.work, "branch", "-m", "issue-9101/demo")
        _git(self.work, "push", "-q", "-u", "origin", "issue-9101/demo")
        self.log = self.tmp / "session.log"
        self.log.write_text("session output that must survive\n")
        # `.task.txt` is what the old respawn replayed. Present on purpose:
        # its absence would make "nothing relaunched" trivially true for
        # the wrong reason.
        (Path(str(self.work) + ".task.txt")).write_text("do the work")
        self.events_path = spawn._events_path(str(self.work))
        self.events_path.write_text(
            '{"ts": 1, "type": "session-start", "detail": {"ts": 77}}\n')
        self.key = "issue-9101/demo-a1b2c3d4"

    def _call(self, state=None, trigger="watchdog-observed-crashed",
              issue_state=("OPEN", True)):
        with mock.patch.object(spawn, "_subject_issue_state", return_value=issue_state), \
             mock.patch.object(spawn, "_issue_comments", return_value=([], True)), \
             mock.patch.object(spawn, "_repo_slug", return_value="o/r"), \
             mock.patch.object(lifecycle.subprocess, "run") as gh_run, \
             mock.patch.object(spawn, "_spawn_one") as spawn_one, \
             mock.patch.object(spawn, "ledger_write") as ledger:
            gh_run.return_value = subprocess.CompletedProcess([], 0, "", "")
            lifecycle._record_dead_session(
                self.key, str(self.work), 9101, "demo", str(self.log),
                77, {} if state is None else state, trigger, False)
        return spawn_one, ledger, gh_run


class NoRelaunchTest(_CrashFixture):

    def test_watchdog_trigger_starts_no_process(self):
        spawn_one, _, _ = self._call()
        spawn_one.assert_not_called()

    def test_self_trigger_starts_no_process(self):
        spawn_one, _, _ = self._call(trigger="self-triggered-abandoned")
        spawn_one.assert_not_called()

    def test_a_present_task_file_is_not_replayed(self):
        """The old path read `.task.txt` and re-ran it. The file is there;
        nothing may consume it."""
        spawn_one, _, _ = self._call()
        spawn_one.assert_not_called()
        self.assertTrue(Path(str(self.work) + ".task.txt").exists())

    def test_one_report_per_dead_session_not_one_per_tick(self):
        """Repeated watchdog ticks over the same dead session must not
        stack up reports -- the per-session claim still holds."""
        _, first_ledger, _ = self._call()
        _, second_ledger, _ = self._call()
        self.assertEqual(first_ledger.call_count, 1)
        self.assertEqual(second_ledger.call_count, 0)

    def test_closed_subject_still_short_circuits_before_any_comment(self):
        with mock.patch.object(spawn, "_flag_stale_returned_branch") as flag:
            spawn_one, ledger, gh_run = self._call(issue_state=("CLOSED", True))
        spawn_one.assert_not_called()
        flag.assert_called_once()
        ledger.assert_not_called()


class StillReportsTest(_CrashFixture):
    """Removing the retry must not remove the observation."""

    def test_posts_a_comment_naming_the_key(self):
        _, _, gh_run = self._call()
        bodies = [str(c.args[0]) for c in gh_run.call_args_list]
        self.assertTrue(any("comments" in b for b in bodies), bodies)

    def test_comment_says_it_will_not_restart(self):
        _, _, gh_run = self._call()
        payload = " ".join(str(c) for c in gh_run.call_args_list)
        self.assertIn("not respawned", payload)

    def test_writes_a_ledger_event_that_names_the_absence_of_respawn(self):
        _, ledger, _ = self._call()
        events = [c.args[0] for c in ledger.call_args_list]
        self.assertEqual([e["event"] for e in events], ["crash_observed_no_respawn"])
        self.assertEqual(events[0]["issue"], 9101)

    def test_workspace_and_log_survive(self):
        self._call()
        self.assertTrue(self.work.exists())
        self.assertEqual(self.log.read_text(), "session output that must survive\n")

    def test_the_death_is_recorded_in_the_event_file(self):
        self._call()
        kinds = [json.loads(l)["type"]
                 for l in self.events_path.read_text().splitlines() if l.strip()]
        self.assertIn("respawn-attempt", kinds)

    def test_gh_failure_is_reported_not_swallowed(self):
        """A comment that could not be posted must say so -- an unposted
        human-intervention warning that looks like a posted one is the
        silent-failure shape this repository keeps finding."""
        import io, contextlib
        buf = io.StringIO()
        with mock.patch.object(spawn, "_subject_issue_state", return_value=("OPEN", True)), \
             mock.patch.object(spawn, "_issue_comments", return_value=([], True)), \
             mock.patch.object(spawn, "_repo_slug", return_value="o/r"), \
             mock.patch.object(lifecycle.subprocess, "run") as gh_run, \
             mock.patch.object(spawn, "_spawn_one"), \
             mock.patch.object(spawn, "ledger_write"), \
             contextlib.redirect_stderr(buf):
            gh_run.return_value = subprocess.CompletedProcess([], 1, "", "boom")
            lifecycle._record_dead_session(self.key, str(self.work), 9101, "demo",
                                      str(self.log), 77, {},
                                      "watchdog-observed-crashed", False)
        self.assertIn("게시 실패", buf.getvalue())


class WatchdogObservesUnconditionallyTest(unittest.TestCase):
    """The dead-entry scan used to be gated behind `--auto-respawn`. Gating
    the *observation* behind the retry flag is what made a death invisible
    whenever the flag was off; only the relaunch was ever destructive."""

    def test_watchdog_source_no_longer_gates_the_check_on_the_flag(self):
        src = (ROOT / "watchdog.py").read_text(encoding="utf-8")
        self.assertNotIn("if auto_respawn:", src)
        self.assertIn("_sp._auto_respawn_check(key, e, respawn_state)", src)

    def test_poll_heartbeat_no_longer_passes_the_retired_flag(self):
        src = (ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh").read_text(
            encoding="utf-8")
        self.assertNotIn("--auto-respawn", src)

    def test_the_flag_is_still_accepted_so_old_callers_do_not_crash(self):
        r = subprocess.run([sys.executable, str(ROOT / "spawn.py"),
                            "watchdog", "--auto-respawn", "--help"],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)


class NoRetryBudgetTest(unittest.TestCase):

    def test_no_allowance_remains_for_anything_still_reading_the_caps(self):
        self.assertEqual(spawn.RESPAWN_MAX_ATTEMPTS, 0)
        self.assertEqual(spawn.RESPAWN_ABSOLUTE_MAX, 0)

    def test_consecutive_confirmation_guard_survives(self):
        """Issue #2969's guard is about verdict accuracy, not about
        retrying -- a single snapshot was measured misjudging live sessions
        as dead, and that error now produces a false report instead of a
        false relaunch. Still worth two observations."""
        self.assertEqual(spawn.RESPAWN_CONSECUTIVE_CONFIRMATIONS, 2)


if __name__ == "__main__":
    unittest.main()
