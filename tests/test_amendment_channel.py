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
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "on-the-record" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
import amendment_channel as ac  # noqa: E402


REPO_A = "acme/widgets"
REPO_B = "acme/gadgets"
REPO_A_URL = "https://github.com/%s.git" % REPO_A
REPO_B_URL = "https://github.com/%s.git" % REPO_B


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
        self.success_url = "https://github.com/%s/issues/55" % REPO_A

    def tearDown(self):
        self.tmp.cleanup()

    def _record(self, cmd, tool_name="Bash", tool_response=None):
        return ac.record_amendment_from_response(
            self.state_dir, tool_name, cmd, self.orch_cwd,
            self.success_url if tool_response is None else tool_response,
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
            self.success_url,
        )
        self.assertIsInstance(result, ac.MarkerWriteFailed)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            ac._report_write_result(result)
        self.assertIn("issue #55", stderr.getvalue())
        self.assertIn("not see this correction", stderr.getvalue())

    def test_unresolvable_repo_does_not_write_a_marker_and_logs_to_stderr(self):
        """issue #3128's shape, applied here: when the orchestrator's own
        cwd has no resolvable repo (no `origin` remote), the write must not
        fall back to a shared bucket -- it must not write ANY marker, and
        the failure must be observable (stderr), not silently dropped."""
        no_origin_cwd = str(_make_issue_repo(Path(self.tmp.name), "999",
                                              name="no-origin-repo", origin=None))
        result = ac.record_amendment_from_response(
            self.state_dir, "Bash", 'gh issue edit 55 --body "x"',
            no_origin_cwd, self.success_url,
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

    def tearDown(self):
        self.tmp.cleanup()

    def _record(self, cmd, tool_response, cwd=None):
        return ac.record_amendment_from_response(
            self.state_dir, "Bash", cmd, cwd or self.session_cwd, tool_response)

    def test_matching_repo_writes_marker_keyed_to_url_issue_number(self):
        url = "https://github.com/%s/issues/42" % REPO_A
        result = self._record('gh issue edit 42 --body "fixed brief"', url)
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
        result = self._record('gh issue edit 42 --body "fixed brief"', url)
        self.assertIsInstance(result, ac.AmendmentWritten)
        self.assertEqual(result.issue, "999")
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "42"))
        self.assertIsNotNone(ac.read_marker(self.state_dir, REPO_A, "999"))

    def test_mismatched_repo_is_a_policy_violation_no_marker_written(self):
        url = "https://github.com/%s/issues/42" % REPO_B
        result = self._record('gh issue edit 42 --body "fixed brief"', url)
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
                               "Edited issue #42")
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

    def test_no_registered_repo_is_fail_closed_not_skip_silently(self):
        """issue #3129 round-4 caveat 2: a session with no resolvable
        registered repo (not started through spawn.py, or `cwd` is not a
        git checkout at all) must fail CLOSED -- no marker, loud stderr --
        never skip silently as if amendments simply don't apply here."""
        no_repo_cwd = self.tmp.name  # a plain directory, not even git init'd
        url = "https://github.com/%s/issues/42" % REPO_A
        result = self._record('gh issue edit 42 --body "fixed brief"', url,
                               cwd=no_repo_cwd)
        self.assertIsInstance(result, ac.NoRegisteredRepo)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "42"))
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            ac._report_write_result(result)
        self.assertIn("registered repo", stderr.getvalue())


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
        self.url = "https://github.com/%s/issues/42" % REPO_A

    def tearDown(self):
        self.tmp.cleanup()

    def _assert_writes_marker(self, cmd):
        result = ac.record_amendment_from_response(
            self.state_dir, "Bash", cmd, self.session_cwd, self.url)
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
            self.state_dir, "Bash", cmd, self.session_cwd, self.url)
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

    def tearDown(self):
        self.tmp.cleanup()

    def _run_main(self, payload):
        env = dict(os.environ, OTR_AMENDMENT_STATE_DIR=self.state_dir)
        module = str(HOOKS_DIR / "amendment_channel.py")
        return subprocess.run(
            [sys.executable, module], input=json.dumps(payload),
            capture_output=True, text=True, env=env, timeout=30,
        )

    def test_successful_write_exits_zero(self):
        url = "https://github.com/%s/issues/42" % REPO_A
        payload = {"session_id": "orch-sess", "tool_name": "Bash",
                   "tool_input": {"command": 'gh issue edit 42 --body "fixed brief"'},
                   "cwd": str(self.repo), "tool_response": url}
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
                   "cwd": str(self.repo), "tool_response": url}
        r = self._run_main(payload)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("POLICY VIOLATION", r.stderr)

    def test_no_registered_repo_exits_nonzero_with_stderr(self):
        url = "https://github.com/%s/issues/42" % REPO_A
        payload = {"session_id": "orch-sess", "tool_name": "Bash",
                   "tool_input": {"command": 'gh issue edit 42 --body "fixed brief"'},
                   "cwd": self.tmp.name, "tool_response": url}
        r = self._run_main(payload)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("registered repo", r.stderr)

    def test_no_url_in_response_exits_nonzero_with_stderr(self):
        payload = {"session_id": "orch-sess", "tool_name": "Bash",
                   "tool_input": {"command": 'gh issue edit 42 --body "fixed brief"'},
                   "cwd": str(self.repo), "tool_response": "Edited issue #42"}
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
        # shape: orchestrator and worker are separate processes/checkouts
        orch_repo = _make_issue_repo(Path(self.tmp.name), "1", name="orch-repo")
        cmd = 'gh issue edit 88 --body "new brief"'
        url = "https://github.com/%s/issues/88" % REPO_A
        payload = self._payload(session_id="orch-sess", tool_name="Bash",
                                 tool_input={"command": cmd}, cwd=str(orch_repo),
                                 tool_response=url)
        # the orchestrator's own cwd is not on issue #88's branch, so this
        # call itself gets no notice back -- it only records the marker
        self.assertIsNone(ac.run_hook(payload, self.state_dir))
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

        amend_cmd = 'gh issue edit %s --body "repo A correction"' % issue
        amend_url = "https://github.com/%s/issues/%s" % (REPO_A, issue)
        amend_payload = json.dumps({
            "session_id": "orch-sess", "tool_name": "Bash",
            "tool_input": {"command": amend_cmd}, "cwd": str(orch_in_repo_a),
            "tool_response": amend_url,
        })
        self.assertIsNone(ac.run_hook(amend_payload, self.state_dir))

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

        amend_cmd = 'gh issue edit %s --body "correction for x"' % issue
        amend_payload = json.dumps({
            "session_id": "orch-sess", "tool_name": "Bash",
            "tool_input": {"command": amend_cmd}, "cwd": str(repo_x),
        })
        ac.run_hook(amend_payload, self.state_dir)

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
