"""issue #3129 acceptance gate: unit tests for `amendment_channel.py`, the
local-file bridge a running worker session uses to see a mid-flight
orchestrator correction it would otherwise never re-read (it read its
issue once at spawn, and cross-session messages can never be approved for
a headless recipient -- see the issue body for the two failed channels).

Covers the module's total-function contract (never raises, see its own
docstring) plus the two design constraints the issue calls "the substance
of the work": a notice fires once per amendment, and an absorbed
amendment stops being announced until a NEW amendment bumps it again.

  python3 -m pytest tests/test_amendment_channel.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "on-the-record" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
import amendment_channel as ac  # noqa: E402


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=str(cwd), check=True,
                    capture_output=True, text=True, timeout=30)


def _make_issue_repo(root: Path, issue: str) -> Path:
    repo = root / "repo"
    repo.mkdir(parents=True)
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "probe@example.com", cwd=repo)
    _git("config", "user.name", "probe", cwd=repo)
    _git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
    _git("checkout", "-q", "-b", "issue-%s/some-role" % issue, cwd=repo)
    return repo


class MarkerReadWrite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")

    def tearDown(self):
        self.tmp.cleanup()

    def test_read_marker_missing_is_none(self):
        self.assertIsNone(ac.read_marker(self.state_dir, "1"))

    def test_write_then_read_round_trips(self):
        v = ac.write_amendment(self.state_dir, "42", note="hello")
        self.assertEqual(v, 1)
        marker = ac.read_marker(self.state_dir, "42")
        self.assertEqual(marker["version"], 1)
        self.assertEqual(marker["note"], "hello")

    def test_repeated_writes_increment_monotonically(self):
        versions = [ac.write_amendment(self.state_dir, "7") for _ in range(3)]
        self.assertEqual(versions, [1, 2, 3])

    def test_corrupt_marker_file_reads_as_absent_not_a_crash(self):
        path = ac.marker_path(self.state_dir, "9")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("{not json")
        self.assertIsNone(ac.read_marker(self.state_dir, "9"))
        # a write after a corrupt file self-heals rather than compounding
        # the corruption
        v = ac.write_amendment(self.state_dir, "9")
        self.assertEqual(v, 1)

    def test_marker_missing_version_field_reads_as_absent(self):
        path = ac.marker_path(self.state_dir, "5")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"note": "no version here"}, f)
        self.assertIsNone(ac.read_marker(self.state_dir, "5"))

    def test_write_amendment_returns_none_when_state_dir_is_unwritable(self):
        # A file sitting where the state dir needs to be a directory makes
        # os.makedirs fail -- OSError, not an uncaught crash.
        blocker = os.path.join(self.tmp.name, "blocker")
        with open(blocker, "w") as f:
            f.write("x")
        self.assertIsNone(ac.write_amendment(blocker, "1"))


class FiresOncePerAmendment(unittest.TestCase):
    """The first named design constraint: a notice fires once per
    amendment, not once per tick."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_marker_no_notice(self):
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", "1"))

    def test_first_check_after_amendment_fires(self):
        ac.write_amendment(self.state_dir, "1", note="fix the brief")
        notice = ac.check_notice(self.state_dir, "sess-1", "1")
        self.assertIsNotNone(notice)
        self.assertIn("#1", notice)
        self.assertIn("fix the brief", notice)

    def test_many_subsequent_ticks_stay_quiet(self):
        ac.write_amendment(self.state_dir, "1")
        first = ac.check_notice(self.state_dir, "sess-1", "1")
        self.assertIsNotNone(first)
        for _ in range(50):
            self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", "1"))

    def test_second_amendment_fires_again_exactly_once(self):
        ac.write_amendment(self.state_dir, "1", note="first")
        n1 = ac.check_notice(self.state_dir, "sess-1", "1")
        self.assertIn("first", n1)
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", "1"))

        ac.write_amendment(self.state_dir, "1", note="second")
        n2 = ac.check_notice(self.state_dir, "sess-1", "1")
        self.assertIn("second", n2)
        for _ in range(10):
            self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", "1"))

    def test_notices_are_per_session_independently(self):
        ac.write_amendment(self.state_dir, "1")
        n_a = ac.check_notice(self.state_dir, "sess-A", "1")
        n_b = ac.check_notice(self.state_dir, "sess-B", "1")
        self.assertIsNotNone(n_a)
        self.assertIsNotNone(n_b)
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-A", "1"))
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-B", "1"))

    def test_notices_are_per_issue_independently(self):
        ac.write_amendment(self.state_dir, "1")
        ac.write_amendment(self.state_dir, "2")
        self.assertIsNotNone(ac.check_notice(self.state_dir, "sess-1", "1"))
        self.assertIsNotNone(ac.check_notice(self.state_dir, "sess-1", "2"))
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", "1"))
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", "2"))


class AbsorbedAmendmentStopsAnnouncing(unittest.TestCase):
    """The second named design constraint: an already-absorbed amendment
    must not keep re-firing -- the never-cleared-notice defect class
    named in the issue (issue #3120)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")

    def tearDown(self):
        self.tmp.cleanup()

    def test_seen_state_survives_a_fresh_check_notice_call(self):
        ac.write_amendment(self.state_dir, "3")
        self.assertIsNotNone(ac.check_notice(self.state_dir, "sess-1", "3"))
        # a brand-new call (as a fresh PostToolUse invocation would be --
        # this module keeps no in-process cache) still reads the persisted
        # seen file, not a lucky re-run of the same process
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", "3"))

    def test_stale_marker_read_directly_does_not_report_unabsorbed_after_seen(self):
        version = ac.write_amendment(self.state_dir, "3", note="only correction")
        ac.check_notice(self.state_dir, "sess-1", "3")
        # the marker itself is untouched (still there for anyone else to
        # read) but this session's own view of it is absorbed
        marker = ac.read_marker(self.state_dir, "3")
        self.assertEqual(marker["version"], version)
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", "3"))


class GhCommandDetection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")

    def tearDown(self):
        self.tmp.cleanup()

    def test_body_flag_writes_marker_with_note(self):
        cmd = 'gh issue edit 55 --body "corrected: do X"'
        ac.maybe_write_from_command(self.state_dir, "Bash", cmd, ".")
        marker = ac.read_marker(self.state_dir, "55")
        self.assertIsNotNone(marker)
        self.assertEqual(marker["note"], "corrected: do X")

    def test_body_equals_form_writes_marker(self):
        cmd = "gh issue edit 55 --body=inline-text"
        ac.maybe_write_from_command(self.state_dir, "Bash", cmd, ".")
        marker = ac.read_marker(self.state_dir, "55")
        self.assertEqual(marker["note"], "inline-text")

    def test_body_file_form_reads_note_from_file(self):
        note_path = os.path.join(self.tmp.name, "note.txt")
        with open(note_path, "w") as f:
            f.write("full corrected body text")
        cmd = "gh issue edit 55 --body-file %s" % note_path
        ac.maybe_write_from_command(self.state_dir, "Bash", cmd, ".")
        marker = ac.read_marker(self.state_dir, "55")
        self.assertEqual(marker["note"], "full corrected body text")

    def test_non_body_edit_does_not_write_a_marker(self):
        cmd = "gh issue edit 55 --add-label bug"
        ac.maybe_write_from_command(self.state_dir, "Bash", cmd, ".")
        self.assertIsNone(ac.read_marker(self.state_dir, "55"))

    def test_unrelated_bash_command_does_not_write_a_marker(self):
        ac.maybe_write_from_command(self.state_dir, "Bash", "git status", ".")
        self.assertIsNone(ac.read_marker(self.state_dir, "1"))

    def test_non_bash_tool_is_ignored(self):
        cmd = 'gh issue edit 55 --body "x"'
        ac.maybe_write_from_command(self.state_dir, "Write", cmd, ".")
        self.assertIsNone(ac.read_marker(self.state_dir, "55"))


class IssueForCwd(unittest.TestCase):
    def test_issue_branch_resolves_issue_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_issue_repo(Path(tmp), "1234")
            self.assertEqual(ac.issue_for_cwd(str(repo)), "1234")

    def test_non_issue_branch_resolves_to_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            _git("init", "-q", cwd=repo)
            _git("config", "user.email", "a@b.c", cwd=repo)
            _git("config", "user.name", "t", cwd=repo)
            _git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
            self.assertIsNone(ac.issue_for_cwd(str(repo)))

    def test_non_git_directory_resolves_to_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(ac.issue_for_cwd(tmp))

    def test_missing_directory_resolves_to_none(self):
        self.assertIsNone(ac.issue_for_cwd("/no/such/path/at/all"))

    def test_empty_cwd_resolves_to_none(self):
        self.assertIsNone(ac.issue_for_cwd(""))


class RunHookEndToEnd(unittest.TestCase):
    """Exercises `run_hook` (what the shipped `.sh` wrapper actually
    calls) rather than the lower-level functions directly, matching the
    contract a real PostToolUse invocation sees: a JSON payload in,
    `additionalContext` string or None out."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")
        self.repo = _make_issue_repo(Path(self.tmp.name), "88")

    def tearDown(self):
        self.tmp.cleanup()

    def _payload(self, **kwargs):
        base = {"session_id": "sess-1", "tool_name": "Read", "tool_input": {},
                "cwd": str(self.repo)}
        base.update(kwargs)
        return json.dumps(base)

    def test_unparseable_payload_returns_none(self):
        self.assertIsNone(ac.run_hook("not json at all", self.state_dir))

    def test_no_amendment_yet_is_quiet(self):
        self.assertIsNone(ac.run_hook(self._payload(), self.state_dir))

    def test_amendment_then_worker_tool_call_sees_notice_once(self):
        ac.write_amendment(self.state_dir, "88", note="brief was wrong")
        first = ac.run_hook(self._payload(), self.state_dir)
        self.assertIsNotNone(first)
        self.assertIn("brief was wrong", first)
        second = ac.run_hook(self._payload(), self.state_dir)
        self.assertIsNone(second)

    def test_orchestrator_bash_call_in_this_same_run_hook_writes_the_marker(self):
        cmd = 'gh issue edit 88 --body "new brief"'
        payload = self._payload(session_id="orch-sess", tool_name="Bash",
                                 tool_input={"command": cmd}, cwd=self.tmp.name)
        # the orchestrator's own cwd is not on an issue-<n> branch, so this
        # call itself gets no notice back -- it only records the marker
        self.assertIsNone(ac.run_hook(payload, self.state_dir))
        marker = ac.read_marker(self.state_dir, "88")
        self.assertIsNotNone(marker)
        self.assertEqual(marker["note"], "new brief")

    def test_missing_session_id_is_quiet_not_a_crash(self):
        payload = json.dumps({"tool_name": "Read", "tool_input": {}, "cwd": str(self.repo)})
        ac.write_amendment(self.state_dir, "88")
        self.assertIsNone(ac.run_hook(payload, self.state_dir))


class HookScriptShippedAndExecutable(unittest.TestCase):
    def test_hook_script_exists_and_is_executable(self):
        script = HOOKS_DIR / "amendment-channel.sh"
        self.assertTrue(script.is_file(), script)
        self.assertTrue(os.access(script, os.X_OK), "%s is not executable" % script)

    def test_module_file_exists(self):
        self.assertTrue((HOOKS_DIR / "amendment_channel.py").is_file())


if __name__ == "__main__":
    unittest.main()
