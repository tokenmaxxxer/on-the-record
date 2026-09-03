"""The amendment channel could not be used by an orchestrator (#3283).

Repo attribution walks the caller's process ancestry against spawn.py's
roster, deliberately, so a worker cannot forge it via cwd or argv. An
orchestrator was started by the operator, not by spawn.py, so it has no
registered ancestor -- and the channel refused it. Three corrections were
lost that way on 2026-09-03.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "on-the-record" / "hooks"))

import amendment_channel as ac  # noqa: E402
import spawn  # noqa: E402


def _roster(entries: dict) -> str:
    p = Path(tempfile.mkdtemp()) / "roster.json"
    p.write_text(json.dumps(entries), encoding="utf-8")
    return str(p)


class TheOperatorCanNameTheRepoTest(unittest.TestCase):
    def setUp(self):
        self.state = tempfile.mkdtemp()

    def test_a_session_with_no_registered_ancestor_can_amend(self):
        r = ac.amend_as_orchestrator(self.state, "owner/target", "9",
                                     roster_path=_roster({}))
        self.assertIsInstance(r, ac.AmendmentWritten)
        self.assertEqual(ac.read_marker(self.state, "owner/target", "9")
                         ["version"], 1)

    def test_the_marker_records_the_note(self):
        ac.amend_as_orchestrator(self.state, "owner/target", "9",
                                 note="use the decoy arm",
                                 roster_path=_roster({}))
        self.assertEqual(
            ac.read_marker(self.state, "owner/target", "9")["note"],
            "use the decoy arm")

    def test_repeated_amendments_bump_the_version(self):
        for _ in range(3):
            ac.amend_as_orchestrator(self.state, "owner/target", "9",
                                     roster_path=_roster({}))
        self.assertEqual(ac.read_marker(self.state, "owner/target", "9")
                         ["version"], 3)


class AWorkerMayNotUseThisPathTest(unittest.TestCase):
    """The property that identifies a worker is what denies it the override."""

    def setUp(self):
        self.state = tempfile.mkdtemp()
        me = os.getpid()
        self.registered = _roster({"issue-9/x": {
            "pid": me, "start_time": spawn._proc_start_time(me),
            "work": str(ROOT), "repo": "owner/registered"}})

    def test_a_registered_caller_is_refused(self):
        r = ac.amend_as_orchestrator(self.state, "owner/asserted", "9",
                                     roster_path=self.registered)
        self.assertIsInstance(r, ac.WorkerMayNotAssertRepo)

    def test_nothing_is_written_when_refused(self):
        ac.amend_as_orchestrator(self.state, "owner/asserted", "9",
                                 roster_path=self.registered)
        self.assertIsNone(ac.read_marker(self.state, "owner/asserted", "9"))

    def test_an_unresolvable_workspace_is_still_a_worker(self):
        # First draft keyed on "did a repo slug resolve", so a worker whose
        # workspace has no parseable origin was read as an orchestrator and
        # could assert any repo it liked.
        me = os.getpid()
        roster = _roster({"issue-9/x": {
            "pid": me, "start_time": spawn._proc_start_time(me),
            "work": "/nonexistent-not-a-git-repo", "repo": "owner/registered"}})
        r = ac.amend_as_orchestrator(self.state, "owner/asserted", "9",
                                     roster_path=roster)
        self.assertIsInstance(r, ac.WorkerMayNotAssertRepo)

    def test_ancestry_detection_is_independent_of_slug_resolution(self):
        me = os.getpid()
        roster = _roster({"k": {"pid": me,
                                "start_time": spawn._proc_start_time(me),
                                "work": "/nonexistent"}})
        self.assertTrue(ac.has_registered_ancestor(me, roster_path=roster))
        self.assertIsNone(ac.registered_repo_for_pid(me, roster_path=roster))


if __name__ == "__main__":
    unittest.main()
