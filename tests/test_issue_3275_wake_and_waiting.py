"""A polling session is WAITING, and every wake carries an inspection contract.

Two defects, one root: the harness could tell alive from dead but not
advancing from waiting, and nothing told the orchestrator what a wake was for.

The operator noticed both before any instrument did -- "why do the consumer
sessions keep sitting still" -- while the poll-report for that same session
read `HEALTHY-CONFIRMED — 로그 성장 확인됨`. It was polling a background
dispatch in a loop: log growing, workspace untouched for minutes.

  python3 -m pytest tests/test_issue_3275_wake_and_waiting.py -q
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))

import session_progress  # noqa: E402


def _log(tmp: Path, calls) -> Path:
    """A session log in the real transcript shape: one JSON event per line."""
    p = tmp / "session.log"
    with p.open("w", encoding="utf-8") as f:
        for name, command in calls:
            args = {"command": command} if command is not None else {}
            f.write(json.dumps({
                "type": "assistant",
                "message": {"content": [
                    {"type": "tool_use", "name": name, "input": args}]},
            }) + "\n")
    return p


class PollingIsWaitingNotHealthyTest(unittest.TestCase):
    """The production shape, from the live issue-3245 session."""

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.addCleanup(self._t.cleanup)

    def test_the_real_polling_loop_is_waiting(self):
        log = _log(self.tmp, [
            ("Bash", "ps aux | grep run_pair.py"),
            ("Bash", "tail -c 1000 /tmp/pair2_run_r4.log"),
            ("Bash", "ps aux | grep -E 'run_pair.py|spawn.py --skills'"),
            ("Bash", "ls -la /tmp/pair1_run_r4.log"),
        ])
        self.assertEqual(session_progress.classify(log, workspace_changed=None),
                         session_progress.WAITING)

    def test_a_session_writing_files_is_advancing(self):
        log = _log(self.tmp, [
            ("Bash", "ps aux | grep run_pair.py"),
            ("Write", None),
        ])
        self.assertEqual(session_progress.classify(log, workspace_changed=None),
                         session_progress.ADVANCING)

    def test_a_changed_workspace_wins_over_the_log(self):
        log = _log(self.tmp, [("Bash", "ps aux")])
        self.assertEqual(session_progress.classify(log, workspace_changed=True),
                         session_progress.ADVANCING)

    def test_git_commit_is_not_observation(self):
        """`git status` reads; `git commit` does not. Keying on the leading
        verb rather than a substring is what keeps these apart."""
        log = _log(self.tmp, [("Bash", "git commit -m 'work'")])
        self.assertNotEqual(session_progress.classify(log, workspace_changed=None),
                            session_progress.WAITING)

    def test_a_redirect_is_never_read_only(self):
        """`ls > file` starts with an observation verb and writes anyway."""
        log = _log(self.tmp, [("Bash", "ls -la > /tmp/out.txt")])
        self.assertNotEqual(session_progress.classify(log, workspace_changed=None),
                            session_progress.WAITING)

    def test_a_chained_command_is_never_read_only(self):
        log = _log(self.tmp, [("Bash", "ps aux | grep x && rm -rf /tmp/x")])
        self.assertNotEqual(session_progress.classify(log, workspace_changed=None),
                            session_progress.WAITING)

    def test_gh_pr_merge_is_not_observation(self):
        log = _log(self.tmp, [("Bash", "gh pr merge 1 --squash")])
        self.assertNotEqual(session_progress.classify(log, workspace_changed=None),
                            session_progress.WAITING)

    def test_gh_pr_view_is_observation(self):
        log = _log(self.tmp, [("Bash", "gh pr view 1"), ("Bash", "gh issue list")])
        self.assertEqual(session_progress.classify(log, workspace_changed=None),
                         session_progress.WAITING)


class UnknownIsNotWaitingTest(unittest.TestCase):
    """The asymmetry that matters: misreporting a working session as idle
    invites an operator to interrupt real work. Unprovable means UNKNOWN."""

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.addCleanup(self._t.cleanup)

    def test_a_missing_log_is_unknown(self):
        self.assertEqual(
            session_progress.classify(self.tmp / "nope.log", workspace_changed=None),
            session_progress.UNKNOWN)

    def test_no_log_path_at_all_is_unknown(self):
        self.assertEqual(session_progress.classify(None, workspace_changed=None),
                         session_progress.UNKNOWN)

    def test_an_empty_log_is_unknown_not_waiting(self):
        log = _log(self.tmp, [])
        self.assertEqual(session_progress.classify(log, workspace_changed=None),
                         session_progress.UNKNOWN)

    def test_an_unrecognised_command_is_unknown_not_waiting(self):
        log = _log(self.tmp, [("Bash", "python3 scripts/run_the_experiment.py")])
        self.assertEqual(session_progress.classify(log, workspace_changed=None),
                         session_progress.UNKNOWN)

    def test_an_unrecognised_tool_is_unknown_not_waiting(self):
        log = _log(self.tmp, [("Task", None)])
        self.assertEqual(session_progress.classify(log, workspace_changed=None),
                         session_progress.UNKNOWN)

    def test_a_corrupt_log_is_unknown_not_waiting(self):
        p = self.tmp / "session.log"
        p.write_text("not json at all\n{broken\n", encoding="utf-8")
        self.assertEqual(session_progress.classify(p, workspace_changed=None),
                         session_progress.UNKNOWN)


class WakeContractIsInjectedTest(unittest.TestCase):
    """The contract must reach every session that installs the plugin, which
    means the always-on directive -- not this repository's own habits."""

    def test_the_contract_file_exists(self):
        self.assertTrue((ROOT / "on-the-record" / "directive"
                          / "wake-inspection.md").is_file())

    def test_the_always_on_directive_names_it(self):
        src = (ROOT / "on-the-record" / "hooks" / "directive.sh").read_text(
            encoding="utf-8")
        self.assertIn("D/wake-inspection.md", src)
        self.assertIn("EVERY WAKE IS YOUR TURN TO LOOK", src)

    def test_the_contract_names_the_three_states(self):
        doc = (ROOT / "on-the-record" / "directive"
               / "wake-inspection.md").read_text(encoding="utf-8")
        for state in ("advancing", "waiting", "stalled"):
            self.assertIn(state, doc)

    def test_the_watchdog_reports_the_waiting_state(self):
        src = (ROOT / "watchdog.py").read_text(encoding="utf-8")
        self.assertIn("WAITING-ON-DISPATCH", src)
        self.assertIn("_session_progress_state", src)


if __name__ == "__main__":
    unittest.main()
