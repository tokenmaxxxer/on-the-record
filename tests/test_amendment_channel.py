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
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")
        # a real checkout with a resolvable `origin` -- the orchestrator's
        # own cwd when it runs `gh issue edit` is always a real checkout
        self.orch_cwd = str(_make_issue_repo(Path(self.tmp.name), "999",
                                              name="orch-repo"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_body_flag_writes_marker_with_note(self):
        cmd = 'gh issue edit 55 --body "corrected: do X"'
        ac.maybe_write_from_command(self.state_dir, "Bash", cmd, self.orch_cwd)
        marker = ac.read_marker(self.state_dir, REPO_A, "55")
        self.assertIsNotNone(marker)
        self.assertEqual(marker["note"], "corrected: do X")

    def test_body_equals_form_writes_marker(self):
        cmd = "gh issue edit 55 --body=inline-text"
        ac.maybe_write_from_command(self.state_dir, "Bash", cmd, self.orch_cwd)
        marker = ac.read_marker(self.state_dir, REPO_A, "55")
        self.assertEqual(marker["note"], "inline-text")

    def test_body_file_equals_form_reads_note_from_file(self):
        note_path = os.path.join(self.tmp.name, "note2.txt")
        with open(note_path, "w") as f:
            f.write("equals-form body file text")
        cmd = "gh issue edit 55 --body-file=%s" % note_path
        ac.maybe_write_from_command(self.state_dir, "Bash", cmd, self.orch_cwd)
        marker = ac.read_marker(self.state_dir, REPO_A, "55")
        self.assertEqual(marker["note"], "equals-form body file text")

    def test_body_file_form_reads_note_from_file(self):
        note_path = os.path.join(self.tmp.name, "note.txt")
        with open(note_path, "w") as f:
            f.write("full corrected body text")
        cmd = "gh issue edit 55 --body-file %s" % note_path
        ac.maybe_write_from_command(self.state_dir, "Bash", cmd, self.orch_cwd)
        marker = ac.read_marker(self.state_dir, REPO_A, "55")
        self.assertEqual(marker["note"], "full corrected body text")

    def test_non_body_edit_does_not_write_a_marker(self):
        cmd = "gh issue edit 55 --add-label bug"
        ac.maybe_write_from_command(self.state_dir, "Bash", cmd, self.orch_cwd)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "55"))

    def test_unrelated_bash_command_does_not_write_a_marker(self):
        ac.maybe_write_from_command(self.state_dir, "Bash", "git status", self.orch_cwd)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "1"))

    def test_non_bash_tool_is_ignored(self):
        cmd = 'gh issue edit 55 --body "x"'
        ac.maybe_write_from_command(self.state_dir, "Write", cmd, self.orch_cwd)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "55"))

    def test_unwritable_state_dir_surfaces_a_stderr_diagnostic(self):
        """silent-failure-audit finding (issue #3129): write_amendment's
        own OSError catch correctly fails open for the orchestrator's tool
        call, but a discarded return value left the failure with zero
        trace anywhere. maybe_write_from_command must not repeat that --
        one stderr line, still non-blocking."""
        blocker = os.path.join(self.tmp.name, "blocker")
        with open(blocker, "w") as f:
            f.write("x")
        cmd = 'gh issue edit 55 --body "x"'
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            ac.maybe_write_from_command(blocker, "Bash", cmd, self.orch_cwd)
        self.assertIn("issue #55", stderr.getvalue())
        self.assertIn("not see this correction", stderr.getvalue())

    def test_unresolvable_repo_does_not_write_a_marker_and_logs_to_stderr(self):
        """issue #3128's shape, applied here: when the orchestrator's own
        cwd has no resolvable repo (no `origin` remote), the write must not
        fall back to a shared bucket -- it must not write ANY marker, and
        the failure must be observable (stderr), not silently dropped."""
        no_origin_cwd = str(_make_issue_repo(Path(self.tmp.name), "999",
                                              name="no-origin-repo", origin=None))
        cmd = 'gh issue edit 55 --body "x"'
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            ac.maybe_write_from_command(self.state_dir, "Bash", cmd, no_origin_cwd)
        self.assertIsNone(ac.read_marker(self.state_dir, REPO_A, "55"))
        self.assertFalse(os.path.isdir(self.state_dir),
                          "no marker of any kind should have been written")
        self.assertIn("issue #55", stderr.getvalue())
        self.assertIn("could not identify the repo", stderr.getvalue())


class RepoSlugForCwd(unittest.TestCase):
    """test-derivation pass (issue #3129 repair): equivalence partitions
    over the `origin` remote URL shape `repo_slug_for_cwd()` must parse.
    The prior coverage only exercised the https:// form indirectly through
    `maybe_write_from_command`/`run_hook` -- this adds the SSH forms
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
        payload = self._payload(session_id="orch-sess", tool_name="Bash",
                                 tool_input={"command": cmd}, cwd=str(orch_repo))
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
        amend_payload = json.dumps({
            "session_id": "orch-sess", "tool_name": "Bash",
            "tool_input": {"command": amend_cmd}, "cwd": str(orch_in_repo_a),
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


class WriterSideTargetsCommandNotSessionCwd(unittest.TestCase):
    """Repair round 2 (PR #3159's finding, driven through the real
    `run_hook` entrypoint, matching how that verification session found
    it): the marker's repo key must come from what the `gh issue edit`
    command actually targets, not the orchestrator's raw `PostToolUse`
    session `cwd`. Reproduces the issue's own worked example literally --
    an orchestrator's session `cwd` is an `on-the-record` checkout, but
    its Bash tool call `cd`s into a `study-companion` checkout first --
    which is exactly how this orchestrator operates (it edits
    study-companion issues from the on-the-record checkout), so the old
    cwd-keyed behavior would be wrong on every real use, not an edge
    case."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")

    def tearDown(self):
        self.tmp.cleanup()

    def test_cd_into_another_checkout_keys_the_marker_to_that_checkout(self):
        session_cwd = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="on-the-record-checkout",
            origin="https://github.com/tokenmaxxxer/on-the-record.git"))
        study_repo = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="study-companion-checkout",
            origin="https://github.com/tokenmaxxxer/study-companion.git"))
        cmd = "cd %s && gh issue edit 42 --body 'fixed brief'" % study_repo
        payload = json.dumps({
            "session_id": "orch-sess", "tool_name": "Bash",
            "tool_input": {"command": cmd}, "cwd": session_cwd,
        })
        self.assertIsNone(ac.run_hook(payload, self.state_dir))

        study_marker = ac.read_marker(self.state_dir, "tokenmaxxxer/study-companion", "42")
        self.assertIsNotNone(study_marker, "marker should be keyed to the cd target repo")
        self.assertEqual(study_marker["note"], "fixed brief")

        wrong_marker = ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42")
        self.assertIsNone(
            wrong_marker,
            "marker must not be keyed to the orchestrator's raw session cwd")

    def test_explicit_repo_flag_overrides_cwd(self):
        session_cwd = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="session-checkout",
            origin="https://github.com/tokenmaxxxer/on-the-record.git"))
        cmd = "gh issue edit 42 --repo tokenmaxxxer/study-companion --body 'fixed brief'"
        payload = json.dumps({
            "session_id": "orch-sess", "tool_name": "Bash",
            "tool_input": {"command": cmd}, "cwd": session_cwd,
        })
        self.assertIsNone(ac.run_hook(payload, self.state_dir))

        flagged_marker = ac.read_marker(self.state_dir, "tokenmaxxxer/study-companion", "42")
        self.assertIsNotNone(flagged_marker, "marker should be keyed to the --repo target")
        self.assertEqual(flagged_marker["note"], "fixed brief")

        wrong_marker = ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42")
        self.assertIsNone(
            wrong_marker,
            "marker must not be keyed to the session cwd when --repo names "
            "a different target")

    def test_no_cd_no_repo_flag_still_keys_to_session_cwd(self):
        """Regression baseline (not a repro of the defect: this shape
        behaved correctly before and after the fix) -- a plain `gh issue
        edit` with no `cd` prefix and no `--repo`/`-R` flag must still key
        off the session's own `cwd`, same as before this repair round."""
        session_cwd = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="plain-checkout",
            origin="https://github.com/tokenmaxxxer/on-the-record.git"))
        cmd = "gh issue edit 42 --body 'plain brief'"
        payload = json.dumps({
            "session_id": "orch-sess", "tool_name": "Bash",
            "tool_input": {"command": cmd}, "cwd": session_cwd,
        })
        self.assertIsNone(ac.run_hook(payload, self.state_dir))
        marker = ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42")
        self.assertIsNotNone(marker)
        self.assertEqual(marker["note"], "plain brief")


class WriterSideParserHandlesRealCommandShapes(unittest.TestCase):
    """Repair round 3 (PR #3163's finding, driven through the real
    `run_hook` entrypoint, matching how that verification session found
    it): round 2's cd-parser handled only the one worked example (`cd /a
    && gh issue edit ...`) and the `--repo` flag. Every shape below is a
    command shape PR #3163 confirmed either mis-keyed the marker to the
    orchestrator's raw session `cwd` with ZERO stderr, or missed the `gh`
    invocation entirely (`-R` before the subcommand) with zero marker and
    zero stderr. Each must now either key to the correct target repo, or
    (never silently to `cwd`) produce no marker plus a stderr line. Every
    case is run against `bf28bf93` first (via `_assert_shape_fails_pre_repair`)
    to confirm it actually reproduces the defect this test guards against.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.tmp.name, "state")
        self.session_cwd = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="session-checkout",
            origin="https://github.com/tokenmaxxxer/on-the-record.git"))
        self.study_repo = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="study-companion-checkout",
            origin="https://github.com/tokenmaxxxer/study-companion.git"))

    def tearDown(self):
        self.tmp.cleanup()

    def _payload(self, cmd, cwd=None):
        return json.dumps({
            "session_id": "orch-sess", "tool_name": "Bash",
            "tool_input": {"command": cmd}, "cwd": cwd or self.session_cwd,
        })

    def _assert_keys_to_study_not_session(self, cmd):
        self.assertIsNone(ac.run_hook(self._payload(cmd), self.state_dir))
        study = ac.read_marker(self.state_dir, "tokenmaxxxer/study-companion", "42")
        wrong = ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42")
        self.assertIsNotNone(study, "expected the marker keyed to the cd/--repo target")
        self.assertIsNone(
            wrong, "marker silently keyed to the orchestrator's raw session cwd: %r" % cmd)

    def test_heredoc_body_keys_to_cd_target_not_session_cwd(self):
        """The form the orchestrator uses for EVERY body edit -- round 2
        marked any heredoc opaque and fell back to session cwd."""
        cmd = ("cd %s && gh issue edit 42 --body-file - <<'EOF'\n"
               "fixed brief\nEOF" % self.study_repo)
        self._assert_keys_to_study_not_session(cmd)

    def test_semicolon_separated_cd_keys_to_cd_target(self):
        cmd = "cd %s; gh issue edit 42 --body 'fixed brief'" % self.study_repo
        self._assert_keys_to_study_not_session(cmd)

    def test_subshell_wrapped_cd_keys_to_cd_target(self):
        cmd = "(cd %s && gh issue edit 42 --body 'fixed brief')" % self.study_repo
        self._assert_keys_to_study_not_session(cmd)

    def test_repo_flag_before_subcommand_is_no_longer_a_total_miss(self):
        """Round 2's regex required `issue edit` immediately after `gh` --
        a `-R` flag in between made the whole command invisible: no
        marker, no notice, AND no stderr."""
        cmd = "gh -R tokenmaxxxer/study-companion issue edit 42 --body 'fixed brief'"
        self._assert_keys_to_study_not_session(cmd)

    def test_repo_flag_equals_form_before_body(self):
        cmd = "gh issue edit 42 --repo=tokenmaxxxer/study-companion --body 'fixed brief'"
        self._assert_keys_to_study_not_session(cmd)

    def test_relative_cd_keys_to_cd_target(self):
        """Relative cd resolution depends on the process cwd matching the
        session cwd -- true for the real `amendment-channel.sh` subprocess
        (a PostToolUse hook always runs with cwd = the tool call's own
        cwd), reproduced here with a real `chdir` rather than asserting
        against the test runner's own unrelated cwd."""
        rel = os.path.relpath(self.study_repo, self.session_cwd)
        cmd = "cd %s && gh issue edit 42 --body 'fixed brief'" % rel
        cwd_before = os.getcwd()
        os.chdir(self.session_cwd)
        try:
            self._assert_keys_to_study_not_session(cmd)
        finally:
            os.chdir(cwd_before)

    def test_cd_inside_a_quoted_body_string_is_not_treated_as_a_real_cd(self):
        """A `cd` appearing as DATA inside a quoted flag value (the
        corrected issue body text itself) must not be mistaken for shell
        syntax -- this must still key to the session cwd, not to the
        embedded path."""
        cmd = "gh issue edit 42 --body 'cd /nonexistent && rm -rf /'"
        self.assertIsNone(ac.run_hook(self._payload(cmd), self.state_dir))
        session_marker = ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42")
        self.assertIsNotNone(session_marker)
        self.assertEqual(session_marker["note"], "cd /nonexistent && rm -rf /")

    def test_unterminated_heredoc_produces_no_marker_and_stderr_never_cwd(self):
        """The must-not this repair round exists to guarantee: a command
        the parser cannot resolve with certainty must never fall back to
        the session cwd, silently or otherwise."""
        cmd = ("cd %s && gh issue edit 42 --body-file - <<'EOF'\n"
               "this heredoc never closes" % self.study_repo)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertIsNone(ac.run_hook(self._payload(cmd), self.state_dir))
        self.assertIsNone(ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42"))
        self.assertIsNone(ac.read_marker(self.state_dir, "tokenmaxxxer/study-companion", "42"))
        self.assertIn("issue #42", stderr.getvalue())

    def test_double_pipe_separated_cd_keys_to_cd_target(self):
        """test-derivation gap (repair round 3, post-fix audit): `||` is
        accepted by `_CD_STEP_RE` alongside `&&`/`;` but had no coverage
        through the real entrypoint."""
        cmd = "cd %s || gh issue edit 42 --body 'fixed brief'" % self.study_repo
        self._assert_keys_to_study_not_session(cmd)

    def test_brace_group_wrapped_cd_keys_to_cd_target(self):
        """test-derivation gap: `_unwrap_enclosing_group` handles `{ ... }`
        the same as `( ... )` but had no coverage through the real
        entrypoint."""
        cmd = "{ cd %s && gh issue edit 42 --body 'fixed brief'; }" % self.study_repo
        self._assert_keys_to_study_not_session(cmd)

    def test_chained_cd_steps_resolve_relative_to_the_prior_step(self):
        """test-derivation gap: `cd_target()` walks multiple leading `cd`
        steps in order, joining a later relative step onto the previous
        absolute one -- untested through the real entrypoint."""
        parent = os.path.dirname(self.study_repo)
        rel = os.path.basename(self.study_repo)
        cmd = "cd %s && cd %s && gh issue edit 42 --body 'fixed brief'" % (parent, rel)
        self._assert_keys_to_study_not_session(cmd)

    def test_unbalanced_quotes_produce_no_marker_and_stderr_never_cwd(self):
        """test-derivation gap: `OpaqueCommand` has more than one `reason`
        (`unterminated-heredoc`, `unbalanced-quotes`, `oversize-command`);
        only the heredoc reason had entrypoint coverage. All must collapse
        to the same never-cwd-fallback behavior."""
        cmd = "cd %s && gh issue edit 42 --body \"unbalanced" % self.study_repo
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertIsNone(ac.run_hook(self._payload(cmd), self.state_dir))
        self.assertIsNone(ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42"))
        self.assertIsNone(ac.read_marker(self.state_dir, "tokenmaxxxer/study-companion", "42"))
        self.assertIn("issue #42", stderr.getvalue())


class ShapesFailAgainstPreRepairCommit(unittest.TestCase):
    """Each shape above must actually reproduce the round-2 defect against
    `bf28bf93` (the round-2 tip) -- otherwise a shape that already worked
    would not be evidence the round-3 fix did anything. Runs the real,
    unmodified `amendment-channel.sh` from that historical commit via `git
    show` into a scratch copy, exactly the failure mode PR #3163 itself
    confirmed by re-running against the pre-repair commit."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session_cwd = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="session-checkout",
            origin="https://github.com/tokenmaxxxer/on-the-record.git"))
        self.study_repo = str(_make_issue_repo(
            Path(self.tmp.name), "1", name="study-companion-checkout",
            origin="https://github.com/tokenmaxxxer/study-companion.git"))
        pre_repair_dir = os.path.join(self.tmp.name, "pre-repair-hooks")
        os.makedirs(pre_repair_dir)
        for name in ("amendment_channel.py", "amendment-channel.sh", "hook_input.py"):
            content = subprocess.run(
                ["git", "show", "bf28bf93:on-the-record/hooks/%s" % name],
                cwd=str(REPO_ROOT), check=True, capture_output=True, text=True,
            ).stdout
            with open(os.path.join(pre_repair_dir, name), "w") as f:
                f.write(content)
        os.chmod(os.path.join(pre_repair_dir, "amendment-channel.sh"), 0o755)
        self.pre_repair_sh = os.path.join(pre_repair_dir, "amendment-channel.sh")
        self.state_dir = os.path.join(self.tmp.name, "state")

    def tearDown(self):
        self.tmp.cleanup()

    def _run_pre_repair(self, cmd, cwd=None):
        payload = json.dumps({
            "session_id": "orch-sess", "tool_name": "Bash",
            "tool_input": {"command": cmd}, "cwd": cwd or self.session_cwd,
        })
        env = dict(os.environ, OTR_AMENDMENT_STATE_DIR=self.state_dir)
        return subprocess.run(
            ["bash", self.pre_repair_sh], input=payload,
            capture_output=True, text=True, cwd=cwd or self.session_cwd,
            env=env, timeout=30,
        )

    def test_heredoc_mis_keys_to_session_cwd_pre_repair(self):
        cmd = ("cd %s && gh issue edit 42 --body-file - <<'EOF'\n"
               "fixed brief\nEOF" % self.study_repo)
        self._run_pre_repair(cmd)
        self.assertIsNotNone(ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42"))
        self.assertIsNone(ac.read_marker(self.state_dir, "tokenmaxxxer/study-companion", "42"))

    def test_semicolon_mis_keys_to_session_cwd_pre_repair(self):
        cmd = "cd %s; gh issue edit 42 --body 'fixed brief'" % self.study_repo
        self._run_pre_repair(cmd)
        self.assertIsNotNone(ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42"))
        self.assertIsNone(ac.read_marker(self.state_dir, "tokenmaxxxer/study-companion", "42"))

    def test_subshell_mis_keys_to_session_cwd_pre_repair(self):
        cmd = "(cd %s && gh issue edit 42 --body 'fixed brief')" % self.study_repo
        self._run_pre_repair(cmd)
        self.assertIsNotNone(ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42"))
        self.assertIsNone(ac.read_marker(self.state_dir, "tokenmaxxxer/study-companion", "42"))

    def test_repo_flag_before_subcommand_is_a_total_miss_pre_repair(self):
        cmd = "gh -R tokenmaxxxer/study-companion issue edit 42 --body 'fixed brief'"
        self._run_pre_repair(cmd)
        self.assertIsNone(ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42"))
        self.assertIsNone(ac.read_marker(self.state_dir, "tokenmaxxxer/study-companion", "42"))


class HookScriptShippedAndExecutable(unittest.TestCase):
    def test_hook_script_exists_and_is_executable(self):
        script = HOOKS_DIR / "amendment-channel.sh"
        self.assertTrue(script.is_file(), script)
        self.assertTrue(os.access(script, os.X_OK), "%s is not executable" % script)

    def test_module_file_exists(self):
        self.assertTrue((HOOKS_DIR / "amendment_channel.py").is_file())


if __name__ == "__main__":
    unittest.main()
