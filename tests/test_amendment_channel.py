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

import contextlib
import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "on-the-record" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
import amendment_channel as ac  # noqa: E402


REPO_A = "acme/widgets"
REPO_B = "acme/gadgets"
REPO_A_URL = "https://github.com/%s.git" % REPO_A
REPO_B_URL = "https://github.com/%s.git" % REPO_B

BASH_TOOL_RESPONSE_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "amendment_channel" / "bash_tool_response.json"
)


def _bash_tool_response(stdout: str, stderr: str = "") -> dict:
    """The real Claude Code `Bash` `tool_response` shape (issue #3129
    repair round 7; see `BASH_TOOL_RESPONSE_FIXTURE`'s own `captured_from`
    field for provenance), `stdout`/`stderr` substituted in.

    Creation Method (test-authoring-isolation-and-fixture-strategy rule
    1.1/1.2): every write-path fixture below builds its `tool_response`
    through this instead of a bare string. PR #3205 found the entire
    pre-round-7 suite constructed `tool_response` as a bare string, which
    is why 79 tests and both required gate probes passed against code
    (round 5/6's `fullmatch` check) that never matched a real payload --
    see `RealBashToolResponseShapeIsHandled` below for the dedicated
    regression test.
    """
    with open(BASH_TOOL_RESPONSE_FIXTURE, "r", encoding="utf-8") as f:
        template = json.load(f)["template"]
    payload = dict(template)
    payload["stdout"] = stdout
    payload["stderr"] = stderr
    return payload


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=str(cwd), check=True,
                    capture_output=True, text=True, timeout=30)


def _make_issue_repo(root: Path, issue: str, name: str = "repo",
                      origin: str = REPO_A_URL) -> Path:
    """A git checkout on branch `issue-<n>/some-role` with an `origin`
    remote set, so `repo_slug_for_cwd()` resolves. `origin=None` builds a
    repo with NO remote configured -- the unresolvable-slug case."""
    repo = root / name
    repo.mkdir(parents=True)
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "probe@example.com", cwd=repo)
    _git("config", "user.name", "probe", cwd=repo)
    _git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
    _git("checkout", "-q", "-b", "issue-%s/some-role" % issue, cwd=repo)
    if origin:
        _git("remote", "add", "origin", origin, cwd=repo)
    return repo


def _register_pid(roster_dir: Path, work, pid: int = None,
                   bad_start_time: bool = False) -> str:
    """issue #3129 repair round 5: write a fake `spawn.py` roster
    (`active.json`'s own shape) naming `pid` (default: THIS test
    process's own real pid) as registered against `work` -- the fixture
    every write-path test below now needs in place of a bare `cwd`.

    Tests run AS the OS process being registered (or spawn a real
    child/grandchild of it, see `AncestryWalkAgainstRealProcesses`), so
    `registered_repo_for_pid()`'s real `/proc` ancestry walk finds this
    entry for real -- nothing in this file mocks `/proc`.
    `bad_start_time=True` writes a `start_time` that cannot match the
    live process at `pid`, exercising the pid-reuse guard.
    """
    pid = pid if pid is not None else os.getpid()
    roster_dir.mkdir(parents=True, exist_ok=True)
    roster_path = roster_dir / "active.json"
    entry = {"pid": pid, "work": str(work)}
    if bad_start_time:
        entry["start_time"] = "not-a-real-start-time"
    else:
        live = ac._proc_start_time(pid)
        if live is not None:
            entry["start_time"] = live
    roster_path.write_text(json.dumps({"issue-1/some-role": entry}))
    return str(roster_path)


def _empty_roster(roster_dir: Path) -> str:
    """A roster naming no pid at all -- the "session never started
    through spawn.py" shape, round-4 caveat 2 / round-5's own explicit
    fail-closed requirement."""
    roster_dir.mkdir(parents=True, exist_ok=True)
    roster_path = roster_dir / "active.json"
    roster_path.write_text(json.dumps({}))
    return str(roster_path)


class MarkerReadWrite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")

    def tearDown(self):
        self.tmp.cleanup()

    def test_read_marker_missing_is_none(self):
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "1"))

    def test_write_then_read_round_trips(self):
        v = ac.write_amendment(self.state_dir, REPO_A, "42", note="hello")
        self.assertEqual(v, 1)
        marker = ac.read_marker(self.state_dir, REPO_A, "42")
        self.assertEqual(marker["version"], 1)
        self.assertEqual(marker["note"], "hello")

    def test_repeated_writes_increment_monotonically(self):
        versions = [ac.write_amendment(self.state_dir, REPO_A, "7") for _ in range(3)]
        self.assertEqual(versions, [1, 2, 3])

    def test_corrupt_marker_file_reads_as_absent_not_a_crash(self):
        path = ac.marker_path(self.state_dir, REPO_A, "9")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("{not json")
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "9"))
        # a write after a corrupt file self-heals rather than compounding
        # the corruption
        v = ac.write_amendment(self.state_dir, REPO_A, "9")
        self.assertEqual(v, 1)

    def test_marker_missing_version_field_reads_as_absent(self):
        path = ac.marker_path(self.state_dir, REPO_A, "5")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"note": "no version here"}, f)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "5"))

    def test_write_amendment_returns_none_when_state_dir_is_unwritable(self):
        # A file sitting where the state dir needs to be a directory makes
        # os.makedirs fail -- OSError, not an uncaught crash.
        blocker = os.path.join(self.tmp.name, "blocker")
        with open(blocker, "w") as f:
            f.write("x")
        self.assertIsNone(ac.write_amendment(blocker, REPO_A, "1"))

    def test_different_repos_get_independent_markers(self):
        """The repair itself: two repos, same issue number, do not share a
        marker file -- an amendment in one must not be readable through
        the other's key."""
        ac.write_amendment(self.state_dir, REPO_A, "42", note="repo A's correction")
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_B, "42"))
        marker_a = ac.read_marker(self.state_dir, REPO_A, "42")
        self.assertEqual(marker_a["note"], "repo A's correction")


class FiresOncePerAmendment(unittest.TestCase):
    """The first named design constraint: a notice fires once per
    amendment, not once per tick."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_marker_no_notice(self):
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "1"))

    def test_first_check_after_amendment_fires(self):
        ac.write_amendment(self.state_dir, REPO_A, "1", note="fix the brief")
        notice = ac.check_notice(self.state_dir, "sess-1", REPO_A, "1")
        self.assertIsNotNone(notice)
        self.assertIn("#1", notice)
        self.assertIn("fix the brief", notice)

    def test_many_subsequent_ticks_stay_quiet(self):
        ac.write_amendment(self.state_dir, REPO_A, "1")
        first = ac.check_notice(self.state_dir, "sess-1", REPO_A, "1")
        self.assertIsNotNone(first)
        for _ in range(50):
            self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "1"))

    def test_second_amendment_fires_again_exactly_once(self):
        ac.write_amendment(self.state_dir, REPO_A, "1", note="first")
        n1 = ac.check_notice(self.state_dir, "sess-1", REPO_A, "1")
        self.assertIn("first", n1)
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "1"))

        ac.write_amendment(self.state_dir, REPO_A, "1", note="second")
        n2 = ac.check_notice(self.state_dir, "sess-1", REPO_A, "1")
        self.assertIn("second", n2)
        for _ in range(10):
            self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "1"))

    def test_notices_are_per_session_independently(self):
        ac.write_amendment(self.state_dir, REPO_A, "1")
        n_a = ac.check_notice(self.state_dir, "sess-A", REPO_A, "1")
        n_b = ac.check_notice(self.state_dir, "sess-B", REPO_A, "1")
        self.assertIsNotNone(n_a)
        self.assertIsNotNone(n_b)
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-A", REPO_A, "1"))
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-B", REPO_A, "1"))

    def test_two_amendments_before_absorption_coalesce_into_one_notice(self):
        """State-transition gap (test-derivation): S1 (unabsorbed) --write_amendment--> S1
        is a real transition -- the orchestrator can amend twice before the
        worker's next tool call. The session must still see exactly one
        notice (not a crash, not two), carrying the LATEST correction --
        an older, superseded correction does not need its own separate
        notice."""
        ac.write_amendment(self.state_dir, REPO_A, "1", note="first")
        ac.write_amendment(self.state_dir, REPO_A, "1", note="second, supersedes first")
        notice = ac.check_notice(self.state_dir, "sess-1", REPO_A, "1")
        self.assertIsNotNone(notice)
        self.assertIn("second, supersedes first", notice)
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "1"))

    def test_notices_are_per_issue_independently(self):
        ac.write_amendment(self.state_dir, REPO_A, "1")
        ac.write_amendment(self.state_dir, REPO_A, "2")
        self.assertIsNotNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "1"))
        self.assertIsNotNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "2"))
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "1"))
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "2"))


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
        ac.write_amendment(self.state_dir, REPO_A, "3")
        self.assertIsNotNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "3"))
        # a brand-new call (as a fresh PostToolUse invocation would be --
        # this module keeps no in-process cache) still reads the persisted
        # seen file, not a lucky re-run of the same process
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "3"))

    def test_stale_marker_read_directly_does_not_report_unabsorbed_after_seen(self):
        version = ac.write_amendment(self.state_dir, REPO_A, "3", note="only correction")
        ac.check_notice(self.state_dir, "sess-1", REPO_A, "3")
        # the marker itself is untouched (still there for anyone else to
        # read) but this session's own view of it is absorbed
        marker = ac.read_marker(self.state_dir, REPO_A, "3")
        self.assertEqual(marker["version"], version)
        self.assertIsNone(ac.check_notice(self.state_dir, "sess-1", REPO_A, "3"))


class GhCommandDetection(unittest.TestCase):
    """`record_amendment_from_response()`'s SHAPE gate: is this Bash call
    a `gh issue edit ... --body...` invocation at all. `self.success_url`
    names the SAME repo as `self.orch_cwd`'s own `origin`, so these tests
    exercise detection/note-extraction only -- repo/issue attribution
    itself is covered separately in `RecordAmendmentFromResponse` below."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")
        # a real checkout with a resolvable `origin` -- the orchestrator's
        # own cwd when it runs `gh issue edit` is always a real checkout
        self.orch_cwd = str(_make_issue_repo(Path(self.tmp.name), "999",
                                              name="orch-repo"))
        self.roster_path = _register_pid(Path(self.tmp.name) / "roster",
                                          self.orch_cwd)
        self.success_url = "https://github.com/%s/issues/55" % REPO_A

    def tearDown(self):
        self.tmp.cleanup()

    def _record(self, cmd, tool_name="Bash", tool_response=None):
        return ac.record_amendment_from_response(
            self.state_dir, tool_name, cmd, self.orch_cwd,
            _bash_tool_response(self.success_url) if tool_response is None else tool_response,
            roster_path=self.roster_path,
        )

    def test_body_flag_writes_marker_with_note(self):
        result = self._record('gh issue edit 55 --body "corrected: do X"')
        self.assertIsInstance(result, ac.AmendmentWritten)
        marker = ac.read_marker(self.state_dir, REPO_A, "55")
        self.assertIsNotNone(marker)
        self.assertEqual(marker["note"], "corrected: do X")

    def test_body_equals_form_writes_marker(self):
        self._record("gh issue edit 55 --body=inline-text")
        marker = ac.read_marker(self.state_dir, REPO_A, "55")
        self.assertEqual(marker["note"], "inline-text")

    def test_body_file_equals_form_reads_note_from_file(self):
        note_path = os.path.join(self.tmp.name, "note2.txt")
        with open(note_path, "w") as f:
            f.write("equals-form body file text")
        self._record("gh issue edit 55 --body-file=%s" % note_path)
        marker = ac.read_marker(self.state_dir, REPO_A, "55")
        self.assertEqual(marker["note"], "equals-form body file text")

    def test_body_file_form_reads_note_from_file(self):
        note_path = os.path.join(self.tmp.name, "note.txt")
        with open(note_path, "w") as f:
            f.write("full corrected body text")
        self._record("gh issue edit 55 --body-file %s" % note_path)
        marker = ac.read_marker(self.state_dir, REPO_A, "55")
        self.assertEqual(marker["note"], "full corrected body text")

    def test_non_body_edit_does_not_write_a_marker(self):
        result = self._record("gh issue edit 55 --add-label bug")
        self.assertIsInstance(result, ac.AmendmentSkipped)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "55"))

    def test_unrelated_bash_command_does_not_write_a_marker(self):
        result = self._record("git status", tool_response="")
        self.assertIsInstance(result, ac.AmendmentSkipped)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "1"))

    def test_non_bash_tool_is_ignored(self):
        result = self._record('gh issue edit 55 --body "x"', tool_name="Write")
        self.assertIsInstance(result, ac.AmendmentSkipped)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "55"))

    def test_unwritable_state_dir_surfaces_a_stderr_diagnostic(self):
        """silent-failure-audit finding (issue #3129): write_amendment's
        own OSError catch correctly fails open for the orchestrator's tool
        call, but a discarded return value left the failure with zero
        trace anywhere. `record_amendment_from_response`/`_report_write_
        result` must not repeat that -- one stderr line, still
        non-blocking."""
        blocker = os.path.join(self.tmp.name, "blocker")
        with open(blocker, "w") as f:
            f.write("x")
        result = ac.record_amendment_from_response(
            blocker, "Bash", 'gh issue edit 55 --body "x"', self.orch_cwd,
            _bash_tool_response(self.success_url), roster_path=self.roster_path,
        )
        self.assertIsInstance(result, ac.MarkerWriteFailed)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            ac._report_write_result(result)
        self.assertIn("issue #55", stderr.getvalue())
        self.assertIn("not see this correction", stderr.getvalue())

    def test_unresolvable_repo_does_not_write_a_marker_and_logs_to_stderr(self):
        """issue #3128's shape, applied here: when the session's own
        REGISTERED work directory (issue #3129 round 5: `spawn.py`'s
        roster `work` field, no longer `cwd`) has no resolvable repo (no
        `origin` remote), the write must not fall back to a shared bucket
        -- it must not write ANY marker, and the failure must be
        observable (stderr), not silently dropped."""
        no_origin_work = str(_make_issue_repo(Path(self.tmp.name), "999",
                                               name="no-origin-repo", origin=None))
        no_origin_roster = _register_pid(Path(self.tmp.name) / "roster2",
                                          no_origin_work)
        result = ac.record_amendment_from_response(
            self.state_dir, "Bash", 'gh issue edit 55 --body "x"',
            self.orch_cwd, _bash_tool_response(self.success_url),
            roster_path=no_origin_roster,
        )
        self.assertIsInstance(result, ac.NoRegisteredRepo)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            ac._report_write_result(result)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "55"))
        self.assertFalse(os.path.isdir(self.state_dir),
                          "no marker of any kind should have been written")
        self.assertIn("registered repo", stderr.getvalue())


class RecordAmendmentFromResponse(unittest.TestCase):
    """issue #3129 round-4 redesign: the write side's repo+issue
    attribution now comes ENTIRELY from (a) this session's own registered
    repo (`repo_slug_for_cwd(cwd)`) and (b) the edited issue's own URL in
    `tool_response` -- never from parsing the command text (see module
    docstring, redesign section, and PR #3170's independent verification
    of the command-text parser this replaces)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")
        self.session_cwd = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="session-checkout", origin=REPO_A_URL))
        # issue #3129 round 5: this session's registered repo now comes
        # from spawn.py's own roster (this process's pid -> `work`), never
        # from `cwd` -- registering `self.session_cwd` here reproduces the
        # same REPO_A attribution the old cwd-based fixture gave, but via
        # the new trust root.
        self.roster_path = _register_pid(Path(self.tmp.name) / "roster",
                                          self.session_cwd)

    def tearDown(self):
        self.tmp.cleanup()

    def _record(self, cmd, tool_response, cwd=None, roster_path=None):
        return ac.record_amendment_from_response(
            self.state_dir, "Bash", cmd, cwd or self.session_cwd, tool_response,
            roster_path=self.roster_path if roster_path is None else roster_path)

    def test_matching_repo_writes_marker_keyed_to_url_issue_number(self):
        url = "https://github.com/%s/issues/42" % REPO_A
        result = self._record('gh issue edit 42 --body "fixed brief"',
                               _bash_tool_response(url))
        self.assertIsInstance(result, ac.AmendmentWritten)
        self.assertEqual(result.repo, REPO_A)
        self.assertEqual(result.issue, "42")
        marker = ac.read_marker(self.state_dir, REPO_A, "42")
        self.assertEqual(marker["note"], "fixed brief")

    def test_issue_number_comes_from_the_url_never_the_command_text(self):
        """The command names issue 42 textually but the URL (the tool's
        own report of what it actually did) names 999 -- the marker must
        key to 999, proving the command text is not read for the issue
        number either, only for the shape gate."""
        url = "https://github.com/%s/issues/999" % REPO_A
        result = self._record('gh issue edit 42 --body "fixed brief"',
                               _bash_tool_response(url))
        self.assertIsInstance(result, ac.AmendmentWritten)
        self.assertEqual(result.issue, "999")
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "42"))
        self.assertIsNotNone(ac.read_marker(self.state_dir, REPO_A, "999"))

    def test_mismatched_repo_is_a_policy_violation_no_marker_written(self):
        url = "https://github.com/%s/issues/42" % REPO_B
        result = self._record('gh issue edit 42 --body "fixed brief"',
                               _bash_tool_response(url))
        self.assertIsInstance(result, ac.RepoMismatch)
        self.assertEqual(result.registered_repo, REPO_A)
        self.assertEqual(result.url_repo, REPO_B)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_B, "42"))
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "42"))
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            ac._report_write_result(result)
        text = stderr.getvalue()
        self.assertIn(REPO_A, text)
        self.assertIn(REPO_B, text)
        self.assertIn("POLICY VIOLATION", text)

    def test_no_url_in_response_is_fail_closed_no_marker(self):
        """`gh`'s output shape changed, or the human/model only echoed a
        confirmation sentence instead of the real stdout -- either way, no
        URL means no attribution, never a guess."""
        result = self._record('gh issue edit 42 --body "fixed brief"',
                               _bash_tool_response("Edited issue #42"))
        self.assertIsInstance(result, ac.NoIssueUrlInResponse)
        self.assertEqual(result.registered_repo, REPO_A)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "42"))
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            ac._report_write_result(result)
        self.assertIn("no parseable", stderr.getvalue())

    def test_empty_tool_response_is_fail_closed_no_marker(self):
        result = self._record('gh issue edit 42 --body "fixed brief"', "")
        self.assertIsInstance(result, ac.NoIssueUrlInResponse)

    def test_none_tool_response_is_fail_closed_no_marker(self):
        result = self._record('gh issue edit 42 --body "fixed brief"', None)
        self.assertIsInstance(result, ac.NoIssueUrlInResponse)

    def test_no_proc_on_platform_is_fail_closed_with_a_distinct_notice(self):
        """issue #3281: macOS has no `/proc` at all, so the ancestry walk
        cannot even attempt to run -- this must be reported as its own
        runtime-visible notice (`NoProcOnPlatform`), distinct from
        `NoRegisteredRepo` (a Linux ancestry MISS with `/proc` present but
        no match), so an operator on a Mac sees "this platform can't do
        this" rather than a message that reads like a per-session fluke."""
        url = "https://github.com/%s/issues/42" % REPO_A
        real_isdir = os.path.isdir
        with unittest.mock.patch(
                "os.path.isdir",
                side_effect=lambda p: False if p == "/proc" else real_isdir(p)):
            result = self._record('gh issue edit 42 --body "fixed brief"',
                                   _bash_tool_response(url))
        self.assertIsInstance(result, ac.NoProcOnPlatform)
        self.assertNotIsInstance(result, ac.NoRegisteredRepo)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "42"))
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            ac._report_write_result(result)
        text = stderr.getvalue()
        self.assertIn("no /proc", text)
        self.assertIn("macOS", text)

    def test_no_registered_repo_is_fail_closed_not_skip_silently(self):
        """issue #3129 round-4 caveat 2, round-5 mechanism: a session with
        no roster registration at all (not started through spawn.py) must
        fail CLOSED -- no marker, loud stderr -- never skip silently as if
        amendments simply don't apply here."""
        url = "https://github.com/%s/issues/42" % REPO_A
        result = self._record('gh issue edit 42 --body "fixed brief"',
                               _bash_tool_response(url),
                               roster_path=_empty_roster(Path(self.tmp.name) / "no-roster"))
        self.assertIsInstance(result, ac.NoRegisteredRepo)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "42"))
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            ac._report_write_result(result)
        self.assertIn("registered repo", stderr.getvalue())

    def test_cd_does_not_move_the_registered_repo(self):
        """issue #3129 repair round 5, the core fix: PR #3191's
        independent verification of round 4 found that an ordinary,
        standalone `cd` -- run as its own Bash call, not chained with the
        `gh issue edit` call -- silently re-registered the session's
        `cwd`-derived "registered repo" to whatever repo it had just
        `cd`'d into (Claude Code's own hook docs: `cwd` is live, it is
        "the new directory after Claude runs cd"). The registration this
        round uses instead (`spawn.py`'s own roster, keyed off this
        process's kernel-tracked ancestry) does not read `cwd` for
        attribution AT ALL -- so passing a `cwd` naming a DIFFERENT repo
        than the one this session is actually registered to must not move
        the result even one bit: the edit still attributes to the
        REGISTERED repo (REPO_A), and an edit actually landing in the
        drifted-to repo (REPO_B) is still a policy violation, not a
        silent re-registration."""
        drifted_cwd = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="drifted-into-repo-b", origin=REPO_B_URL))

        # same repo as the edit actually landed in (URL says REPO_A) --
        # attribution must still succeed, using the REGISTERED repo, even
        # though `cwd` now points at a REPO_B checkout.
        url_a = "https://github.com/%s/issues/42" % REPO_A
        result_a = self._record('gh issue edit 42 --body "fixed brief"',
                                 _bash_tool_response(url_a), cwd=drifted_cwd)
        self.assertIsInstance(result_a, ac.AmendmentWritten,
                               "cwd drift must not change which repo this "
                               "session is registered to: %r" % (result_a,))
        self.assertEqual(result_a.repo, REPO_A)

        # the drifted-to repo (matching cwd, NOT the registration) must
        # still be refused as a cross-repo policy violation -- round 4's
        # whole worked example, still closed after round 5's mechanism
        # swap.
        url_b = "https://github.com/%s/issues/43" % REPO_B
        result_b = self._record('gh issue edit 43 --body "other edit"',
                                 _bash_tool_response(url_b), cwd=drifted_cwd)
        self.assertIsInstance(result_b, ac.RepoMismatch,
                               "an edit landing in the repo cwd drifted "
                               "to (not the registered repo) must still "
                               "be refused: %r" % (result_b,))
        self.assertEqual(result_b.registered_repo, REPO_A)
        self.assertEqual(result_b.url_repo, REPO_B)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_B, "43"))

    def test_failed_edit_error_text_containing_a_url_is_not_a_success(self):
        """PR #3191's Angle 2 finding: a genuinely FAILED `gh issue edit`
        (the edit was NOT applied) whose error text happens to quote an
        unrelated issue's URL, in the session's OWN registered repo, must
        not be silently mistaken for that edit's own success report."""
        failure_text = (
            "HTTP 422: Validation Failed. See "
            "https://github.com/%s/issues/7 for the field format example. "
            "(edit 42 was NOT applied)" % REPO_A
        )
        result = self._record('gh issue edit 42 --body "fixed brief"',
                               _bash_tool_response(failure_text))
        self.assertIsInstance(result, ac.NoIssueUrlInResponse,
                               "a failed edit's error text must never be "
                               "mistaken for a success report: %r" % (result,))
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "7"))
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "42"))

    def test_two_urls_in_a_response_is_not_a_success(self):
        """PR #3191's lower-severity Angle 2 finding, closed as a
        structural consequence of the same `fullmatch` fix: a response
        naming more than one URL is not `gh`'s own bare success output
        either, so it must not attribute to the FIRST (possibly wrong)
        match."""
        two_urls = "note: also touched https://github.com/%s/issues/5\n%s" % (
            REPO_B, "https://github.com/%s/issues/42" % REPO_A)
        result = self._record('gh issue edit 42 --body "fixed brief"',
                               _bash_tool_response(two_urls))
        self.assertIsInstance(result, ac.NoIssueUrlInResponse)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_B, "5"))
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "42"))


class RealBashToolResponseShapeIsHandled(unittest.TestCase):
    """issue #3129 repair round 7, following PR #3205's independent
    verification of round 6: every fixture in this suite BEFORE this round
    constructed `tool_response` as a bare string, so 79 passing tests and
    two passing gate probes never caught that `_issue_url_from_response`'s
    `fullmatch` (round 5) never matches a real Claude Code `Bash`
    `tool_response` -- a structured object
    (`BASH_TOOL_RESPONSE_FIXTURE`, live-captured against Claude Code
    2.1.258, see its own `captured_from` field), never the bare string
    `hook_input.tool_response_text()`'s docstring assumed. This class
    drives `record_amendment_from_response` with that literal captured
    shape directly, below the `_bash_tool_response()` Creation Method every
    other test above now also uses -- this class exists so the regression
    itself has one dedicated, unambiguous home. Confirmed this round to
    FAIL against the round-6 tip (`fc8e23aa`/`6d604d90`) before the
    `_response_stdout_text()` fix landed; see this round's record for the
    pre-fix run."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")
        self.session_cwd = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="session-checkout", origin=REPO_A_URL))
        self.roster_path = _register_pid(Path(self.tmp.name) / "roster",
                                          self.session_cwd)

    def tearDown(self):
        self.tmp.cleanup()

    def test_real_dict_shaped_tool_response_writes_a_marker(self):
        url = "https://github.com/%s/issues/42" % REPO_A
        result = ac.record_amendment_from_response(
            self.state_dir, "Bash", 'gh issue edit 42 --body "fixed brief"',
            self.session_cwd, _bash_tool_response(url),
            roster_path=self.roster_path)
        self.assertIsInstance(
            result, ac.AmendmentWritten,
            "a real Bash tool_response (dict-shaped: stdout/stderr/"
            "interrupted/isImage/noOutputExpected) must record an "
            "amendment for a genuinely successful edit -- got %r; this is "
            "the exact defect PR #3205 found round 6 missing entirely"
            % (result,))
        self.assertEqual(result.repo, REPO_A)
        self.assertEqual(result.issue, "42")
        marker = ac.read_marker(self.state_dir, REPO_A, "42")
        self.assertEqual(marker["note"], "fixed brief")

    def test_real_dict_shaped_failure_text_is_still_refused(self):
        """Strictness must survive the shape fix: a failed edit's error
        text, carried in the real dict shape's own `stdout` field, must
        still be refused -- never a bare URL substring pass."""
        failure_text = (
            "HTTP 422: Validation Failed. See "
            "https://github.com/%s/issues/7 for the field format example. "
            "(edit 42 was NOT applied)" % REPO_A
        )
        result = ac.record_amendment_from_response(
            self.state_dir, "Bash", 'gh issue edit 42 --body "fixed brief"',
            self.session_cwd, _bash_tool_response(failure_text),
            roster_path=self.roster_path)
        self.assertIsInstance(result, ac.NoIssueUrlInResponse)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "7"))
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "42"))

    def test_stderr_field_is_never_consulted_for_the_url(self):
        """A URL sitting only in `stderr` (never `stdout`) must not count
        -- `gh issue edit`'s own success report is stdout-only; treating
        stderr as an alternate source would let a warning line coexist
        with a URL and still pass."""
        url = "https://github.com/%s/issues/42" % REPO_A
        response = _bash_tool_response("", stderr=url)
        result = ac.record_amendment_from_response(
            self.state_dir, "Bash", 'gh issue edit 42 --body "fixed brief"',
            self.session_cwd, response, roster_path=self.roster_path)
        self.assertIsInstance(result, ac.NoIssueUrlInResponse)

    def test_bare_string_tool_response_is_still_accepted(self):
        """Back-compat path (issue #3129 round 7): a bare string
        `tool_response` -- the shape every pre-round-7 fixture assumed, no
        longer known to occur in a real Claude Code `Bash` call, but kept
        as a defensive fallback -- must still resolve exactly as before."""
        url = "https://github.com/%s/issues/42" % REPO_A
        result = ac.record_amendment_from_response(
            self.state_dir, "Bash", 'gh issue edit 42 --body "fixed brief"',
            self.session_cwd, url, roster_path=self.roster_path)
        self.assertIsInstance(result, ac.AmendmentWritten)


class RegisteredRepoForPid(unittest.TestCase):
    """issue #3129 repair round 5: direct coverage of
    `registered_repo_for_pid()` itself -- the new trust root -- below the
    level of `record_amendment_from_response()`. Nothing here mocks
    `/proc`; every case drives the real kernel-backed ancestry walk."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.roster_dir = Path(self.tmp.name) / "roster"
        self.repo = _make_issue_repo(Path(self.tmp.name), "1", origin=REPO_A_URL)

    def tearDown(self):
        self.tmp.cleanup()

    def test_this_process_own_registration_resolves(self):
        roster_path = _register_pid(self.roster_dir, self.repo)
        self.assertEqual(
            ac.registered_repo_for_pid(os.getpid(), roster_path=roster_path),
            REPO_A)

    def test_no_roster_file_at_all_resolves_to_none(self):
        missing = str(self.roster_dir / "does-not-exist.json")
        self.assertIsNone(ac.registered_repo_for_pid(os.getpid(), roster_path=missing))

    def test_empty_roster_resolves_to_none(self):
        roster_path = _empty_roster(self.roster_dir)
        self.assertIsNone(ac.registered_repo_for_pid(os.getpid(), roster_path=roster_path))

    def test_roster_entry_for_a_different_pid_does_not_match(self):
        # a real, currently-nonexistent pid (0 is never a valid userland
        # pid) -- this process's own ancestry must never happen to walk
        # through it.
        roster_path = _register_pid(self.roster_dir, self.repo, pid=0)
        self.assertIsNone(ac.registered_repo_for_pid(os.getpid(), roster_path=roster_path))

    def test_mismatched_start_time_is_treated_as_pid_reuse_not_a_match(self):
        """The pid-reuse guard: an entry recorded for THIS pid number but
        with a `start_time` that does not match the live process wearing
        it now must not be trusted -- same guard `roster.py`'s own
        `_paired_liveness()` already applies to liveness checks."""
        roster_path = _register_pid(self.roster_dir, self.repo, bad_start_time=True)
        self.assertIsNone(ac.registered_repo_for_pid(os.getpid(), roster_path=roster_path))

    def test_missing_start_time_field_still_trusts_the_pid_match(self):
        roster_path = self.roster_dir / "active.json"
        self.roster_dir.mkdir(parents=True, exist_ok=True)
        roster_path.write_text(json.dumps(
            {"issue-1/role": {"pid": os.getpid(), "work": str(self.repo)}}))
        self.assertEqual(
            ac.registered_repo_for_pid(os.getpid(), roster_path=str(roster_path)),
            REPO_A)

    def test_corrupt_roster_file_resolves_to_none_not_a_crash(self):
        self.roster_dir.mkdir(parents=True, exist_ok=True)
        roster_path = self.roster_dir / "active.json"
        roster_path.write_text("{not json")
        self.assertIsNone(
            ac.registered_repo_for_pid(os.getpid(), roster_path=str(roster_path)))

    def test_no_proc_on_this_platform_resolves_to_none(self):
        """macOS (issue #2924's precedent) -- no `/proc` at all means no
        ancestry walk is possible; this must fail closed, never fall back
        to any other signal."""
        roster_path = _register_pid(self.roster_dir, self.repo)
        real_isdir = os.path.isdir
        with unittest.mock.patch(
                "os.path.isdir",
                side_effect=lambda p: False if p == "/proc" else real_isdir(p)):
            self.assertIsNone(
                ac.registered_repo_for_pid(os.getpid(), roster_path=roster_path))

    def test_registered_work_dir_with_no_origin_resolves_to_none(self):
        no_origin = str(_make_issue_repo(Path(self.tmp.name), "1",
                                          name="no-origin", origin=None))
        roster_path = _register_pid(self.roster_dir, no_origin)
        self.assertIsNone(ac.registered_repo_for_pid(os.getpid(), roster_path=roster_path))


class AncestryWalkAgainstRealProcesses(unittest.TestCase):
    """issue #3129 repair round 5, test-depth-audit pass: the unit tests
    above all hit `registered_repo_for_pid()`'s dict lookup at hop 0
    (this test process's own pid IS the registered pid). That alone does
    not prove the ANCESTRY WALK itself works -- the actual mechanism this
    round relies on, since a real hook subprocess is never the exact
    registered pid, only a descendant of it. This spawns a real child
    process and asks IT to resolve ITS OWN parent's (this test's)
    registration, driving a genuine multi-process `/proc` walk."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = _make_issue_repo(Path(self.tmp.name), "1", origin=REPO_A_URL)
        self.roster_path = _register_pid(Path(self.tmp.name) / "roster", self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_child_process_resolves_its_parents_registration(self):
        script = (
            "import sys, os\n"
            "sys.path.insert(0, %r)\n"
            "import amendment_channel as ac\n"
            "print(ac.registered_repo_for_pid(os.getpid(), roster_path=%r) or '')\n"
        ) % (str(HOOKS_DIR), self.roster_path)
        r = subprocess.run([sys.executable, "-c", script],
                            capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), REPO_A,
                          "a child process could not resolve its own "
                          "parent's roster registration: stdout=%r stderr=%r"
                          % (r.stdout, r.stderr))

    def test_a_grandchild_process_still_resolves_the_registration(self):
        """Two hops: this test -> child shell -> grandchild python. Proves
        the walk does not stop at the first ancestor."""
        script = (
            "import sys, os\n"
            "sys.path.insert(0, %r)\n"
            "import amendment_channel as ac\n"
            "print(ac.registered_repo_for_pid(os.getpid(), roster_path=%r) or '')\n"
        ) % (str(HOOKS_DIR), self.roster_path)
        r = subprocess.run(
            ["sh", "-c", "%s -c %s" % (sys.executable, shlex.quote(script))],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), REPO_A,
                          "a grandchild process could not resolve an "
                          "ancestor's roster registration: stdout=%r stderr=%r"
                          % (r.stdout, r.stderr))


class PreviouslyBrokenShapesAreNowIrrelevant(unittest.TestCase):
    """PR #3170's independent verification found repair round 3's
    command-text parser still missed 5 of 9 un-enumerated shapes:
    `pushd`, a quoted `cd` path containing a space, a subshell wrapping
    only `gh`, `--repo=` before the issue number, and a `GH_REPO=`
    env-var prefix. Under this round's redesign none of these shapes
    matter anymore -- the command text is consulted only for the shape
    gate, never for attribution -- so each becomes trivially Present
    here, driven through the same `record_amendment_from_response`
    entrypoint, each wrapped with a normal-looking `tool_response`.
    Proves the new seam does not care about the command's shape at all
    for attribution purposes, by construction rather than by enumeration.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")
        self.session_cwd = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="session-checkout", origin=REPO_A_URL))
        self.roster_path = _register_pid(Path(self.tmp.name) / "roster",
                                          self.session_cwd)
        self.url = "https://github.com/%s/issues/42" % REPO_A

    def tearDown(self):
        self.tmp.cleanup()

    def _assert_writes_marker(self, cmd):
        result = ac.record_amendment_from_response(
            self.state_dir, "Bash", cmd, self.session_cwd,
            _bash_tool_response(self.url), roster_path=self.roster_path)
        self.assertIsInstance(result, ac.AmendmentWritten,
                               "cmd=%r result=%r" % (cmd, result))
        self.assertIsNotNone(ac.read_marker(self.state_dir, REPO_A, "42"))

    def test_pushd_chain(self):
        self._assert_writes_marker(
            "pushd /somewhere/else && gh issue edit 42 --body 'fixed brief' && popd")

    def test_cd_to_quoted_path_with_a_space(self):
        self._assert_writes_marker(
            "cd \"/path with a space/checkout\" && gh issue edit 42 "
            "--body 'fixed brief'")

    def test_subshell_wrapping_only_gh(self):
        self._assert_writes_marker(
            "cd /somewhere/else && (gh issue edit 42 --body 'fixed brief')")

    def test_repo_flag_before_the_issue_number(self):
        self._assert_writes_marker(
            "gh issue edit --repo=owner/other-repo 42 --body 'fixed brief'")

    def test_gh_repo_env_var_prefix(self):
        self._assert_writes_marker(
            "GH_REPO=owner/other-repo gh issue edit 42 --body 'fixed brief'")

    def test_cd_inside_a_quoted_body_string_is_never_mistaken_for_a_real_cd(self):
        """Not one of PR #3170's 5, but the same principle from the other
        direction: text that LOOKS like shell syntax embedded in the body
        DATA must not confuse anything, because none of the command is
        parsed for attribution purposes at all anymore."""
        cmd = "gh issue edit 42 --body 'cd /nonexistent && rm -rf /'"
        result = ac.record_amendment_from_response(
            self.state_dir, "Bash", cmd, self.session_cwd,
            _bash_tool_response(self.url), roster_path=self.roster_path)
        self.assertIsInstance(result, ac.AmendmentWritten)
        marker = ac.read_marker(self.state_dir, REPO_A, "42")
        self.assertEqual(marker["note"], "cd /nonexistent && rm -rf /")


class MainExitCodeReflectsWriteOutcome(unittest.TestCase):
    """issue #3129 round-4: a fail-closed write outcome must be visible as
    a nonzero exit code from `amendment_channel.py`'s own process. The
    shipped `.sh` wrapper (`amendment-channel.sh`) still unconditionally
    exits 0 on its own trailing line -- a PostToolUse hook must never
    block a tool call -- but invoking the python module directly, as
    these tests and the gates probes both can, must not paper over the
    failure with a silent 0."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")
        self.repo = _make_issue_repo(Path(self.tmp.name), "1", origin=REPO_A_URL)
        # issue #3129 round 5: `amendment_channel.py` here runs as a real
        # DIRECT CHILD subprocess of this test process (`subprocess.run`
        # below) -- registering THIS test process's own real pid as
        # `spawn.py` would have exercises the real `/proc` ancestry walk
        # (one genuine hop: child -> this test's pid), not a same-pid
        # dict-lookup shortcut.
        self.roster_path = _register_pid(Path(self.tmp.name) / "roster", self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def _run_main(self, payload, roster_path=None):
        env = dict(os.environ, OTR_AMENDMENT_STATE_DIR=self.state_dir,
                   OTR_ROSTER_PATH=self.roster_path if roster_path is None else roster_path)
        module = str(HOOKS_DIR / "amendment_channel.py")
        return subprocess.run(
            [sys.executable, module], input=json.dumps(payload),
            capture_output=True, text=True, env=env, timeout=30,
        )

    def test_successful_write_exits_zero(self):
        url = "https://github.com/%s/issues/42" % REPO_A
        payload = {"session_id": "orch-sess", "tool_name": "Bash",
                   "tool_input": {"command": 'gh issue edit 42 --body "fixed brief"'},
                   "cwd": str(self.repo), "tool_response": _bash_tool_response(url)}
        r = self._run_main(payload)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_quiet_non_gh_call_exits_zero(self):
        payload = {"session_id": "sess-1", "tool_name": "Read", "tool_input": {},
                   "cwd": str(self.repo)}
        r = self._run_main(payload)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_repo_mismatch_exits_nonzero_with_stderr(self):
        url = "https://github.com/%s/issues/42" % REPO_B
        payload = {"session_id": "orch-sess", "tool_name": "Bash",
                   "tool_input": {"command": 'gh issue edit 42 --body "fixed brief"'},
                   "cwd": str(self.repo), "tool_response": _bash_tool_response(url)}
        r = self._run_main(payload)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("POLICY VIOLATION", r.stderr)

    def test_no_registered_repo_exits_nonzero_with_stderr(self):
        """issue #3129 round 5: a session with no roster registration at
        all (this real subprocess's own ancestry pid never appears in the
        roster) must fail closed -- driven through the real binary, real
        subprocess, real (empty) roster file, not a mocked lookup."""
        url = "https://github.com/%s/issues/42" % REPO_A
        payload = {"session_id": "orch-sess", "tool_name": "Bash",
                   "tool_input": {"command": 'gh issue edit 42 --body "fixed brief"'},
                   "cwd": str(self.repo), "tool_response": _bash_tool_response(url)}
        r = self._run_main(payload,
                            roster_path=_empty_roster(Path(self.tmp.name) / "no-roster"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("registered repo", r.stderr)

    def test_no_url_in_response_exits_nonzero_with_stderr(self):
        payload = {"session_id": "orch-sess", "tool_name": "Bash",
                   "tool_input": {"command": 'gh issue edit 42 --body "fixed brief"'},
                   "cwd": str(self.repo),
                   "tool_response": _bash_tool_response("Edited issue #42")}
        r = self._run_main(payload)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no parseable", r.stderr)


class RepoSlugForCwd(unittest.TestCase):
    """test-derivation pass (issue #3129 repair): equivalence partitions
    over the `origin` remote URL shape `repo_slug_for_cwd()` must parse.
    The prior coverage only exercised the https:// form indirectly through
    `record_amendment_from_response`/`run_hook` -- this adds the SSH forms
    `spawn.py`'s own `_workspace_target_path()` explicitly handles
    elsewhere in this repo, plus the not-a-URL-shape-at-all boundary."""

    def test_https_origin_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_issue_repo(Path(tmp), "1",
                                     origin="https://github.com/acme/widgets.git")
            self.assertEqual(ac.repo_slug_for_cwd(str(repo)), "acme/widgets")

    def test_git_at_ssh_origin_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_issue_repo(Path(tmp), "1",
                                     origin="git@github.com:acme/widgets.git")
            self.assertEqual(ac.repo_slug_for_cwd(str(repo)), "acme/widgets")

    def test_ssh_scheme_origin_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_issue_repo(Path(tmp), "1",
                                     origin="ssh://git@github.com/acme/widgets.git")
            self.assertEqual(ac.repo_slug_for_cwd(str(repo)), "acme/widgets")

    def test_no_origin_remote_resolves_to_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_issue_repo(Path(tmp), "1", origin=None)
            self.assertIsNone(ac.repo_slug_for_cwd(str(repo)))

    def test_unparseable_origin_resolves_to_none_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_issue_repo(Path(tmp), "1",
                                     origin="/local/path/not/a/url/shape")
            self.assertIsNone(ac.repo_slug_for_cwd(str(repo)))

    def test_non_git_directory_resolves_to_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(ac.repo_slug_for_cwd(tmp))

    def test_missing_directory_resolves_to_none(self):
        self.assertIsNone(ac.repo_slug_for_cwd("/no/such/path/at/all"))

    def test_empty_cwd_resolves_to_none(self):
        self.assertIsNone(ac.repo_slug_for_cwd(""))


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
        ac.write_amendment(self.state_dir, REPO_A, "88", note="brief was wrong")
        first = ac.run_hook(self._payload(), self.state_dir)
        self.assertIsNotNone(first)
        self.assertIn("brief was wrong", first)
        second = ac.run_hook(self._payload(), self.state_dir)
        self.assertIsNone(second)

    def test_orchestrator_bash_call_in_this_same_run_hook_writes_the_marker(self):
        # the orchestrator's own checkout of the SAME repo (same `origin`,
        # different local path/branch from the worker's) -- realistic
        # shape: orchestrator and worker are separate processes/checkouts.
        # issue #3129 round 5: this process's own roster registration
        # (not `cwd`) names orch_repo as the write's registered repo.
        orch_repo = _make_issue_repo(Path(self.tmp.name), "1", name="orch-repo")
        roster_path = _register_pid(Path(self.tmp.name) / "roster", orch_repo)
        cmd = 'gh issue edit 88 --body "new brief"'
        url = "https://github.com/%s/issues/88" % REPO_A
        payload = self._payload(session_id="orch-sess", tool_name="Bash",
                                 tool_input={"command": cmd}, cwd=str(orch_repo),
                                 tool_response=_bash_tool_response(url))
        # the orchestrator's own cwd is not on issue #88's branch, so this
        # call itself gets no notice back -- it only records the marker
        self.assertIsNone(ac.run_hook(payload, self.state_dir, roster_path))
        marker = ac.read_marker(self.state_dir, REPO_A, "88")
        self.assertIsNotNone(marker)
        self.assertEqual(marker["note"], "new brief")

    def test_missing_session_id_is_quiet_not_a_crash(self):
        payload = json.dumps({"tool_name": "Read", "tool_input": {}, "cwd": str(self.repo)})
        ac.write_amendment(self.state_dir, REPO_A, "88")
        self.assertIsNone(ac.run_hook(payload, self.state_dir))

    def test_cross_repo_amendment_does_not_leak_to_an_unrelated_repo(self):
        """The repair itself, driven through the real `run_hook` entrypoint
        (not the lower-level functions): two independent repos both happen
        to use `issue-42/some-role` for issue #42 -- a real, unremarkable
        naming collision since branch names are chosen by convention, not
        by repo. An orchestrator amendment in repo A must not reach a
        worker in repo B, even though both are watching the identical
        issue number on the identical branch shape."""
        issue = "42"
        repo_a_worker = _make_issue_repo(Path(self.tmp.name), issue,
                                          name="repo-a-worker", origin=REPO_A_URL)
        repo_b_worker = _make_issue_repo(Path(self.tmp.name), issue,
                                          name="repo-b-worker", origin=REPO_B_URL)
        orch_in_repo_a = _make_issue_repo(Path(self.tmp.name), "1",
                                           name="repo-a-orch", origin=REPO_A_URL)

        roster_path = _register_pid(Path(self.tmp.name) / "roster", orch_in_repo_a)
        amend_cmd = 'gh issue edit %s --body "repo A correction"' % issue
        amend_url = "https://github.com/%s/issues/%s" % (REPO_A, issue)
        amend_payload = json.dumps({
            "session_id": "orch-sess", "tool_name": "Bash",
            "tool_input": {"command": amend_cmd}, "cwd": str(orch_in_repo_a),
            "tool_response": _bash_tool_response(amend_url),
        })
        self.assertIsNone(ac.run_hook(amend_payload, self.state_dir, roster_path))

        def worker_payload(cwd):
            return json.dumps({"session_id": "worker-sess", "tool_name": "Read",
                                "tool_input": {}, "cwd": str(cwd)})

        notice_b = ac.run_hook(worker_payload(repo_b_worker), self.state_dir)
        self.assertIsNone(
            notice_b,
            "repo B's worker saw a notice from repo A's amendment -- "
            "cross-repo leak: %r" % notice_b,
        )
        notice_a = ac.run_hook(worker_payload(repo_a_worker), self.state_dir)
        self.assertIsNotNone(notice_a,
                              "repo A's own worker should still see its own amendment")
        self.assertIn("repo A correction", notice_a)

    def test_two_repos_with_unresolvable_slugs_do_not_collide(self):
        """issue #3128's shape: two DIFFERENT repos that both fail to
        resolve a slug (no `origin` remote) must not collapse into one
        shared bucket either -- neither should ever see a notice, since
        neither write nor read has anywhere to (legitimately) put one."""
        issue = "42"
        repo_x = _make_issue_repo(Path(self.tmp.name), issue,
                                   name="unresolvable-x", origin=None)
        repo_y = _make_issue_repo(Path(self.tmp.name), issue,
                                   name="unresolvable-y", origin=None)

        roster_path = _register_pid(Path(self.tmp.name) / "roster", repo_x)
        amend_cmd = 'gh issue edit %s --body "correction for x"' % issue
        amend_payload = json.dumps({
            "session_id": "orch-sess", "tool_name": "Bash",
            "tool_input": {"command": amend_cmd}, "cwd": str(repo_x),
        })
        ac.run_hook(amend_payload, self.state_dir, roster_path)

        def worker_payload(cwd):
            return json.dumps({"session_id": "worker-sess", "tool_name": "Read",
                                "tool_input": {}, "cwd": str(cwd)})

        self.assertIsNone(ac.run_hook(worker_payload(repo_y), self.state_dir))
        self.assertIsNone(ac.run_hook(worker_payload(repo_x), self.state_dir))


class HookScriptShippedAndExecutable(unittest.TestCase):
    def test_hook_script_exists_and_is_executable(self):
        script = HOOKS_DIR / "amendment-channel.sh"
        self.assertTrue(script.is_file(), script)
        self.assertTrue(os.access(script, os.X_OK), "%s is not executable" % script)

    def test_module_file_exists(self):
        self.assertTrue((HOOKS_DIR / "amendment_channel.py").is_file())


if __name__ == "__main__":
    unittest.main()
