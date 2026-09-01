"""Issue #2981: the crashed-verdict respawn path
(lifecycle.py::_auto_respawn_check, reached via `spawn._auto_respawn_check`)
did not check whether the subject already had a deliverable PR before
respawning -- a crashed-but-actually-fine session was respawned over an
issue whose first PR already covered it, and that issue ended up with five
competing PRs.

This is deliberately NOT about the verdict being unreliable (issue #2969's
separate scope, untouched here): even a *correct* `crashed` verdict must
not respawn over an existing deliverable. The gate under test
(`gates/spawn_on_pr.py::subject_has_deliverable()`, consulted from
`lifecycle.py::_auto_respawn_check()` via `lifecycle._subject_has_deliverable()`)
holds regardless of whether the verdict computation itself is right.

Two layers, both against real entry points (only `gh`/network is mocked at
the process boundary -- same idiom as
test/test_reconcile_crash_verdict_race.py, which this file's respawn-path
fixtures are modeled on):

  1. `SubjectHasDeliverableTest` -- `subject_has_deliverable()` itself,
     covering the four equivalence partitions over subject deliverable
     state (test-derivation skill: partition by "does this subject already
     have a *real* deliverable" -- no PR / record-only PR / open deliverable
     PR / merged deliverable PR) plus the gh-lookup-error case.
  2. `AutoRespawnConsultsDeliverableGateTest` -- `spawn._auto_respawn_check()`,
     proving the respawn path actually consults (1) before acting on a
     `crashed` verdict: skips when a deliverable is found, proceeds when
     not (including on lookup error -- fail-open toward respawn, never a
     silent skip), and reports the skip by PR number every time it fires.

  python3 -m pytest tests/test_respawn_deliverable_gate.py -q
"""
from __future__ import annotations

import contextlib
import io
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
import spawn_on_pr  # noqa: E402
import closure_sweep  # noqa: E402
import check_runner  # noqa: E402

lifecycle._sp = spawn

DEAD_PID = 999999999  # never a real pid (test_unrecovered_commit_count.py convention)


def _git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a],
                           capture_output=True, text=True, check=True)


def _write_record(root: Path, issue: int, slug: str, *, verifies_subject: bool = False,
                   author: str = "someone") -> None:
    """Drops a landed board record directly on disk -- `board()` reads
    `docs/issue-<n>/reports/*.md` straight off the filesystem (no commit/
    push needed), so this is enough to make it show up as "landed"."""
    rep = root / "docs" / f"issue-{issue}" / "reports"
    rep.mkdir(parents=True, exist_ok=True)
    lines = ["---", "loop_state: landed", f"author: {author}"]
    if verifies_subject:
        lines.append("verifies_subject: true")
    lines.append("---\n\nbody\n")
    (rep / f"{slug}.md").write_text("\n".join(lines))


class SubjectHasDeliverableTest(unittest.TestCase):
    """Partition-level tests of
    `gates/spawn_on_pr.py::subject_has_deliverable()` -- the check the
    respawn path now consults."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        self.subject = "issue-9001"

    # --- partition 1: no PR at all for the subject -----------------------

    def test_respawn_proceeds_without_deliverable_when_no_pr_exists(self):
        with mock.patch.object(closure_sweep, "_pr_index_all", return_value=({}, True)):
            result = spawn_on_pr.subject_has_deliverable(self.root, self.subject)
        self.assertIsNone(result)

    # --- partition 2: only a record-only (verification/measurement) PR ---
    #     exists -- the important must-not case: this must NOT be treated
    #     as a deliverable.

    def test_respawn_proceeds_without_deliverable_when_only_record_only_pr_open(self):
        pr_index = {"issue-9001/independent-verification-1":
                    {"number": 5, "state": "OPEN", "body": ""}}
        with mock.patch.object(closure_sweep, "_pr_index_all", return_value=(pr_index, True)), \
             mock.patch.object(check_runner, "pr_diff_paths",
                                return_value=["docs/issue-9001/reports/"
                                              "independent-verification-1.md"]):
            result = spawn_on_pr.subject_has_deliverable(self.root, self.subject)
        self.assertIsNone(result)

    def test_respawn_proceeds_without_deliverable_when_only_adversarial_review_pr_open(self):
        # issue #2981 (PR #3006's live-reproduced gap): a record-only branch
        # under this repo's OTHER real record-only naming convention (not
        # the literal `independent-verification-<N>` slug the old regex
        # matched) must be excluded too -- the decision is diff content, not
        # any one hardcoded slug.
        pr_index = {"issue-9001/adversarial-review-abc12345":
                    {"number": 6, "state": "OPEN", "body": ""}}
        with mock.patch.object(closure_sweep, "_pr_index_all", return_value=(pr_index, True)), \
             mock.patch.object(check_runner, "pr_diff_paths",
                                return_value=["docs/issue-9001/reports/"
                                              "adversarial-review-abc12345.md"]):
            result = spawn_on_pr.subject_has_deliverable(self.root, self.subject)
        self.assertIsNone(result)

    def test_respawn_proceeds_without_deliverable_when_only_record_only_pr_merged(self):
        # landed (merged) but self-declares verifies_subject: true -- board()
        # must not resolve this as the subject's deliverable either.
        _write_record(self.root, 9001, "independent-verification-1",
                      verifies_subject=True)
        with mock.patch.object(closure_sweep, "_pr_index_all", return_value=({}, True)):
            result = spawn_on_pr.subject_has_deliverable(self.root, self.subject)
        self.assertIsNone(result)

    # --- partition 3: an open deliverable PR exists -----------------------

    def test_respawn_skips_existing_deliverable_when_pr_open(self):
        pr_index = {"issue-9001/implementation": {"number": 42, "state": "OPEN", "body": ""}}
        with mock.patch.object(closure_sweep, "_pr_index_all", return_value=(pr_index, True)), \
             mock.patch.object(check_runner, "pr_diff_paths",
                                return_value=["gates/spawn_on_pr.py"]):
            result = spawn_on_pr.subject_has_deliverable(self.root, self.subject)
        self.assertEqual(result, {"number": 42, "branch": "issue-9001/implementation",
                                  "state": "OPEN"})

    # --- partition 4: a merged deliverable PR exists ----------------------

    def test_respawn_skips_existing_deliverable_when_pr_merged(self):
        _write_record(self.root, 9001, "implementation")
        with mock.patch.object(spawn, "_pr_open_or_merged_for_branch", return_value=77):
            result = spawn_on_pr.subject_has_deliverable(self.root, self.subject)
        self.assertEqual(result, {"number": 77, "branch": "issue-9001/implementation",
                                  "state": "MERGED"})

    # --- lookup error: must default to "no deliverable", never to "skip" -

    def test_respawn_proceeds_without_deliverable_on_gh_lookup_error(self):
        with mock.patch.object(closure_sweep, "_pr_index_all", return_value=(None, False)):
            result = spawn_on_pr.subject_has_deliverable(self.root, self.subject)
        self.assertIsNone(result)


class AutoRespawnConsultsDeliverableGateTest(unittest.TestCase):
    """`spawn._auto_respawn_check()` (the actual respawn path) against the
    real crash-fixture shape from test/test_reconcile_crash_verdict_race.py
    -- a dead wrapper pid so `session_end_verdict()` genuinely returns
    `crashed`, then the deliverable gate decides what happens next."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        self.remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        self.work = self.tmp / "on-the-record-issue-9002-demo"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.work)], check=True)
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        (self.work / "a.txt").write_text("1")
        _git(self.work, "add", "a.txt")
        _git(self.work, "commit", "-q", "-m", "c1")
        self.branch = "issue-9002/demo"
        _git(self.work, "branch", "-m", self.branch)
        _git(self.work, "push", "-q", "-u", "origin", self.branch)
        self.events_path = spawn._events_path(str(self.work))
        self.events_path.write_text(
            '{"ts": 1, "type": "session-start", "detail": {"pid": %d}}\n' % DEAD_PID)

    def _entry(self):
        return {"pid": DEAD_PID, "work": str(self.work),
                "before_head": _git(self.work, "rev-parse", "HEAD").stdout.strip(),
                "log": None, "issue": 9002, "skill": "demo", "expects_pr": False,
                "wrapper_pid": DEAD_PID}

    def test_respawn_skips_existing_deliverable_when_open_pr_found(self):
        found = {"number": 4242, "branch": "issue-9002/implementation", "state": "OPEN"}
        with mock.patch.object(spawn, "_subject_has_deliverable", return_value=found), \
             mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap:
            spawn._auto_respawn_check("issue-9002/demo", self._entry(), {})
        respawn_or_cap.assert_not_called()

    def test_respawn_skips_existing_deliverable_when_merged_pr_found(self):
        found = {"number": 4243, "branch": "issue-9002/implementation", "state": "MERGED"}
        with mock.patch.object(spawn, "_subject_has_deliverable", return_value=found), \
             mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap:
            spawn._auto_respawn_check("issue-9002/demo", self._entry(), {})
        respawn_or_cap.assert_not_called()

    def test_respawn_proceeds_without_deliverable_when_gate_finds_none(self):
        with mock.patch.object(spawn, "_subject_has_deliverable", return_value=None), \
             mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap:
            spawn._auto_respawn_check("issue-9002/demo", self._entry(), {})
        respawn_or_cap.assert_called_once()

    def test_respawn_proceeds_without_deliverable_still_respawns_genuine_crash(self):
        # equivalent of test/test_reconcile_crash_verdict_race.py's genuine-
        # crash counterpart, but for this new gate: absence of a deliverable
        # (the ordinary case) must never suppress a real recovery.
        entry = self._entry()
        with mock.patch.object(spawn, "_subject_has_deliverable", return_value=None), \
             mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap:
            spawn._auto_respawn_check("issue-9002/demo", entry, {})
        respawn_or_cap.assert_called_once()
        args, _kwargs = respawn_or_cap.call_args
        self.assertEqual(args[2], 9002)  # issue
        self.assertEqual(args[3], "demo")  # skill

    def test_respawn_skip_is_reported_names_the_pr_in_stderr_and_ledger(self):
        found = {"number": 5150, "branch": "issue-9002/implementation", "state": "OPEN"}
        stderr = io.StringIO()
        with mock.patch.object(spawn, "_subject_has_deliverable", return_value=found), \
             mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap, \
             mock.patch.object(spawn, "ledger_write") as ledger_write, \
             contextlib.redirect_stderr(stderr):
            spawn._auto_respawn_check("issue-9002/demo", self._entry(), {})
        respawn_or_cap.assert_not_called()
        self.assertIn("5150", stderr.getvalue())
        ledger_write.assert_called_once()
        logged = ledger_write.call_args[0][0]
        self.assertEqual(logged["event"], "respawn_skipped_existing_deliverable")
        self.assertEqual(logged["pr_number"], 5150)
        self.assertEqual(logged["issue"], 9002)

    def test_respawn_skip_is_reported_never_silent_even_without_pr_number(self):
        # a landed deliverable whose PR number could not be resolved (e.g.
        # a stale board() snapshot) still names *something* identifying --
        # the branch -- rather than saying nothing.
        found = {"number": None, "branch": "issue-9002/implementation", "state": "MERGED"}
        stderr = io.StringIO()
        with mock.patch.object(spawn, "_subject_has_deliverable", return_value=found), \
             mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap, \
             contextlib.redirect_stderr(stderr):
            spawn._auto_respawn_check("issue-9002/demo", self._entry(), {})
        respawn_or_cap.assert_not_called()
        self.assertIn("issue-9002/implementation", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
