"""Issue #3127 repair: scripts/issue-3127/verify_preregistration.py's plain
git-ancestry check cannot survive this repo's own squash-merge landing mode
-- PR #3131 introduced the pre-registration and the results skeleton in one
squash commit, collapsing the two-commit order the check depended on, so it
fails on every branch cut from main by construction (see PR #3166's record).
The fix resolves that specific collision (same local commit for both paths)
against the originating PR's own pre-squash commit history instead, via
`gh pr view <n> --json commits` -- these tests inject a fake `gh` runner so
the ordering logic is exercised without a network call, then construct an
actual violation (a result introduced before its pre-registration in the
PR's own history) and confirm the check refuses it.

Round 2 (PR #3169 repair): the `verification_pr:` pin is attacker-controlled
working-tree content, so PR #3171's independent verification constructed a
fabricated same-commit collision pinned at an unrelated, legitimately-
ordered PR and got `ok=True` -- `_resolve_via_pr_history` never checked that
the pinned PR actually produced the colliding commit, only that some PR had
the right order somewhere in its own history. The fix binds the pin to the
colliding commit via the pinned PR's own recorded merge commit (`gh pr view
<n> --json mergeCommit`); `PinBoundToWrongCommitTest` reproduces that exact
attack shape and confirms it is now refused.

Round 3 (PR #3219 residual finding): `_first_commit_for_path` returned
`None` both when `git log` genuinely found no commit for a path AND when
the `git log` command itself failed -- `verify()` reads a `None`
results_commit as "not yet committed" and passes unconditionally, so a
git failure could silently read as a pass. `_first_commit_for_path` now
raises `GitCommandError` on a failed command instead of returning `None`,
and `verify()` catches it and fails closed. `FirstCommitForPathTest` and
`VerifyGitFailureTest` cover the distinction.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "issue-3127"))
import verify_preregistration as vp  # noqa: E402


def _completed(stdout="", returncode=0):
    return subprocess.CompletedProcess(args=[], returncode=returncode,
                                        stdout=stdout, stderr="")


def _fake_gh_runner(commit_shas, files_by_sha, merge_commit_sha,
                     owner_repo="acme/widgets"):
    """A `gh` stand-in: no network, no subprocess -- just enough of the
    `gh pr view --json commits`, `gh pr view --json mergeCommit`, `gh repo
    view`, and `gh api .../commits/SHA` surface for `_resolve_via_pr_history`
    to run its real logic against a scripted commit history.
    `merge_commit_sha` is the sha the fake PR reports as its own merge
    commit -- pass `None` to simulate an unmerged/lookup-failed PR, or an
    unrelated sha to simulate a pin that does not name the PR that actually
    produced the commit under review."""
    import json

    def runner(args):
        if args[:2] == ["repo", "view"]:
            return _completed(stdout=owner_repo + "\n")
        if args[:2] == ["pr", "view"]:
            json_field = args[args.index("--json") + 1]
            if json_field == "mergeCommit":
                merge_commit = ({"oid": merge_commit_sha}
                                 if merge_commit_sha else None)
                return _completed(stdout=json.dumps(
                    {"mergeCommit": merge_commit}))
            if json_field == "commits":
                return _completed(stdout=json.dumps(
                    {"commits": [{"oid": s} for s in commit_shas]}))
            raise AssertionError(f"unexpected --json field: {json_field}")
        if args[0] == "api":
            sha = args[1].rsplit("/", 1)[-1]
            names = "\n".join(files_by_sha.get(sha, []))
            return _completed(stdout=names)
        raise AssertionError(f"unexpected gh invocation: {args}")

    return runner


class ReadFrontmatterTest(unittest.TestCase):
    def test_parses_verification_pr(self):
        text = "---\nissue: 3127\nverification_pr: 3131\n---\nbody\n"
        self.assertEqual(vp._read_frontmatter(text), {"issue": 3127,
                                                        "verification_pr": 3131})

    def test_no_frontmatter_block_returns_empty(self):
        self.assertEqual(vp._read_frontmatter("no frontmatter here\n"), {})

    def test_unterminated_block_returns_empty(self):
        self.assertEqual(vp._read_frontmatter("---\nissue: 3127\nno closer\n"), {})


class ResolveViaPrHistoryTest(unittest.TestCase):
    """Unit-level: exercises `_resolve_via_pr_history` directly against a
    scripted, in-memory PR commit history -- the same function `verify()`
    falls back to on a same-commit collision. `COLLIDING` stands in for the
    real local same-commit sha `verify()` would pass in; each fake PR's
    `merge_commit_sha` is set to `COLLIDING` unless a test is specifically
    exercising the merge-commit bind."""

    COLLIDING = "deadbeef" * 5

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.repo_root = Path(self._tmpdir.name)
        (self.repo_root / "docs/issue-3127/decisions").mkdir(parents=True)

    def _write_prereg(self, verification_pr_line):
        prereg_dir = self.repo_root / vp.PREREG_PATH
        prereg_dir.parent.mkdir(parents=True, exist_ok=True)
        prereg_dir.write_text(
            "---\nissue: 3127\n" + verification_pr_line + "\n---\nbody\n")

    def test_legitimate_order_passes(self):
        self._write_prereg("verification_pr: 3131")
        gh = _fake_gh_runner(
            commit_shas=["aaa1", "bbb2", "ccc3"],
            files_by_sha={"aaa1": [vp.PREREG_PATH],
                           "bbb2": [vp.RESULTS_PATH]},
            merge_commit_sha=self.COLLIDING)
        ok, msg = vp._resolve_via_pr_history(self.repo_root, self.COLLIDING, gh)
        self.assertTrue(ok, msg)
        self.assertIn("strictly earlier", msg)

    def test_violation_result_committed_first_is_refused(self):
        """The constructed violation: the PR's own (pre-squash) history
        shows the results file introduced BEFORE the pre-registration --
        exactly what the ordering property forbids. The check must refuse
        this, not pass it because a later commit happens to also touch
        both paths."""
        self._write_prereg("verification_pr: 3131")
        gh = _fake_gh_runner(
            commit_shas=["aaa1", "bbb2", "ccc3"],
            files_by_sha={"aaa1": [vp.RESULTS_PATH],
                           "bbb2": [vp.PREREG_PATH]},
            merge_commit_sha=self.COLLIDING)
        ok, msg = vp._resolve_via_pr_history(self.repo_root, self.COLLIDING, gh)
        self.assertFalse(ok)
        self.assertIn("does NOT show", msg)

    def test_violation_same_pr_commit_is_refused(self):
        """A second violation shape: both paths first appear in the same
        PR commit (index tie) -- still not strictly-before, still refused."""
        self._write_prereg("verification_pr: 3131")
        gh = _fake_gh_runner(
            commit_shas=["aaa1"],
            files_by_sha={"aaa1": [vp.PREREG_PATH, vp.RESULTS_PATH]},
            merge_commit_sha=self.COLLIDING)
        ok, msg = vp._resolve_via_pr_history(self.repo_root, self.COLLIDING, gh)
        self.assertFalse(ok)

    def test_missing_verification_pr_field_fails_closed(self):
        self._write_prereg("status: registered")
        gh = _fake_gh_runner(commit_shas=["aaa1"], files_by_sha={},
                              merge_commit_sha=self.COLLIDING)
        ok, msg = vp._resolve_via_pr_history(self.repo_root, self.COLLIDING, gh)
        self.assertFalse(ok)
        self.assertIn("no integer `verification_pr:`", msg)

    def test_gh_pr_view_failure_fails_closed(self):
        self._write_prereg("verification_pr: 3131")

        def gh(args):
            if args[:2] == ["repo", "view"]:
                return _completed(stdout="acme/widgets\n")
            if args[:2] == ["pr", "view"]:
                return _completed(returncode=1, stdout="")
            raise AssertionError(f"unexpected gh invocation: {args}")

        ok, msg = vp._resolve_via_pr_history(self.repo_root, self.COLLIDING, gh)
        self.assertFalse(ok)
        self.assertIn("mergeCommit", msg)

    def test_gh_repo_view_failure_fails_closed(self):
        """`gh repo view` failing after the merge-commit bind has already
        succeeded must still fail closed (no code path lets a missing
        owner/repo silently skip the remaining checks)."""
        self._write_prereg("verification_pr: 3131")

        def gh(args):
            if args[:2] == ["pr", "view"]:
                json_field = args[args.index("--json") + 1]
                if json_field == "mergeCommit":
                    import json
                    return _completed(stdout=json.dumps(
                        {"mergeCommit": {"oid": self.COLLIDING}}))
            return _completed(returncode=1, stdout="")

        ok, msg = vp._resolve_via_pr_history(self.repo_root, self.COLLIDING, gh)
        self.assertFalse(ok)

    def test_path_absent_from_pr_history_fails_closed(self):
        self._write_prereg("verification_pr: 3131")
        gh = _fake_gh_runner(commit_shas=["aaa1"],
                              files_by_sha={"aaa1": ["some/other/file.txt"]},
                              merge_commit_sha=self.COLLIDING)
        ok, msg = vp._resolve_via_pr_history(self.repo_root, self.COLLIDING, gh)
        self.assertFalse(ok)
        self.assertIn("fail closed", msg)

    def test_pin_not_merged_fails_closed(self):
        """The pinned PR has no recorded merge commit at all (still open,
        or `gh` could not resolve it) -- there is nothing to bind the pin
        to, so this must fail closed rather than fall through to trusting
        the pin's own commit-order claim."""
        self._write_prereg("verification_pr: 3131")
        gh = _fake_gh_runner(
            commit_shas=["aaa1", "bbb2"],
            files_by_sha={"aaa1": [vp.PREREG_PATH],
                           "bbb2": [vp.RESULTS_PATH]},
            merge_commit_sha=None)
        ok, msg = vp._resolve_via_pr_history(self.repo_root, self.COLLIDING, gh)
        self.assertFalse(ok)
        self.assertIn("no recorded merge commit", msg)

    def test_pin_bound_to_unrelated_pr_is_refused(self):
        """Round-2 attack, unit level: `verification_pr:` names a real PR
        whose own (legitimate) history has the right order, but that PR's
        merge commit is NOT the colliding commit under review -- i.e. the
        attacker fabricated a local collision and pinned it at someone
        else's unrelated, already-merged PR. Before the fix this passed
        (`ok=True`) because only the referenced PR's internal order was
        checked, never whether it produced the commit in question."""
        self._write_prereg("verification_pr: 9999")
        unrelated_pr_merge_sha = "cafebabe" * 5
        gh = _fake_gh_runner(
            commit_shas=["legit1", "legit2"],
            files_by_sha={"legit1": [vp.PREREG_PATH],
                           "legit2": [vp.RESULTS_PATH]},
            merge_commit_sha=unrelated_pr_merge_sha)
        ok, msg = vp._resolve_via_pr_history(self.repo_root, self.COLLIDING, gh)
        self.assertFalse(ok)
        self.assertIn("does not match the colliding commit", msg)
        self.assertIn(self.COLLIDING, msg)
        self.assertIn(unrelated_pr_merge_sha, msg)


class FirstCommitForPathTest(unittest.TestCase):
    """Unit-level coverage of the round-3 fix: `_first_commit_for_path`
    must distinguish "git ran and found nothing" (legitimate `None`) from
    "git itself failed" (`GitCommandError`, never `None`)."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.repo_root = Path(self._tmpdir.name)

    def test_returns_none_when_command_succeeds_with_no_matching_commit(self):
        # An empty repo (no commits at all) makes `git log` itself fail
        # ("does not have any commits yet"), which is the failure case
        # this fix distinguishes -- so commit something unrelated first,
        # to isolate "command succeeded, path never appeared" from
        # "command failed".
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        unrelated = self.repo_root / "unrelated.txt"
        unrelated.write_text("x\n")
        self._git("add", "unrelated.txt")
        self._git("commit", "-q", "-m", "unrelated commit")

        self.assertIsNone(
            vp._first_commit_for_path(self.repo_root, "no/such/path.txt"))

    def _git(self, *args):
        r = subprocess.run(["git", "-C", str(self.repo_root), *args],
                            capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def test_raises_git_command_error_when_git_itself_fails(self):
        # No `git init` -- `git -C <dir> log ...` exits non-zero ("not a
        # git repository"), which must not be reported the same as "ran
        # and found nothing".
        with self.assertRaises(vp.GitCommandError) as ctx:
            vp._first_commit_for_path(self.repo_root, vp.PREREG_PATH)
        self.assertNotEqual(ctx.exception.returncode, 0)
        self.assertIn("git log", str(ctx.exception))


class VerifyGitFailureTest(unittest.TestCase):
    """End-to-end: a git command failure while resolving commit history
    must fail `verify()` closed, never be read as "not yet committed" (the
    legitimate empty-result case `verify()` treats as a pass at line
    ~284)."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.repo_root = Path(self._tmpdir.name)
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")

        prereg = self.repo_root / vp.PREREG_PATH
        prereg.parent.mkdir(parents=True)
        prereg.write_text("---\nissue: 3127\n---\nbody\n")
        self._git("add", vp.PREREG_PATH)
        self._git("commit", "-q", "-m", "commit pre-registration")

        # RESULTS_PATH deliberately left uncommitted (working-tree only) --
        # the case where, pre-fix, a git failure on this specific query
        # would have been misread as "not yet committed" and passed.
        results = self.repo_root / vp.RESULTS_PATH
        results.parent.mkdir(parents=True)
        results.write_text('{"run_status": "not_executed"}\n')

    def _git(self, *args):
        r = subprocess.run(["git", "-C", str(self.repo_root), *args],
                            capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def test_git_failure_on_results_path_fails_closed_not_read_as_pass(self):
        real_run_git = vp._run_git

        def flaky_run_git(repo_root, *args):
            if args and args[-1] == vp.RESULTS_PATH:
                return subprocess.CompletedProcess(
                    args=["git", *args], returncode=128, stdout="",
                    stderr="fatal: simulated git failure")
            return real_run_git(repo_root, *args)

        with mock.patch.object(vp, "_run_git", side_effect=flaky_run_git):
            ok, msg = vp.verify(self.repo_root)

        self.assertFalse(ok, msg)
        self.assertIn("git log", msg)
        self.assertIn("fail closed", msg)


class VerifyEndToEndCollisionTest(unittest.TestCase):
    """End-to-end through `verify()` against a real (temporary) git repo
    that reproduces the squash-collision shape live: one commit adds both
    PREREG_PATH and RESULTS_PATH, exactly like PR #3131's squash-merge did
    on this branch -- then the fallback resolves (or refuses) against an
    injected fake PR history, no network involved."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.repo_root = Path(self._tmpdir.name)
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")

    def _git(self, *args):
        r = subprocess.run(["git", "-C", str(self.repo_root), *args],
                            capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def _commit_both_files_together(self, verification_pr_line):
        prereg = self.repo_root / vp.PREREG_PATH
        results = self.repo_root / vp.RESULTS_PATH
        prereg.parent.mkdir(parents=True)
        results.parent.mkdir(parents=True)
        prereg.write_text("---\nissue: 3127\n" + verification_pr_line +
                           "\n---\nbody\n")
        results.write_text('{"run_status": "not_executed"}\n')
        self._git("add", vp.PREREG_PATH, vp.RESULTS_PATH)
        self._git("commit", "-q", "-m", "squash: both files in one commit")
        return self._git("rev-parse", "HEAD").stdout.strip()

    def test_legitimate_pr_history_resolves_the_collision(self):
        colliding = self._commit_both_files_together("verification_pr: 3131")
        gh = _fake_gh_runner(
            commit_shas=["aaa1", "bbb2"],
            files_by_sha={"aaa1": [vp.PREREG_PATH],
                           "bbb2": [vp.RESULTS_PATH]},
            merge_commit_sha=colliding)
        ok, msg = vp.verify(self.repo_root, gh_runner=gh)
        self.assertTrue(ok, msg)

    def test_constructed_violation_is_refused_end_to_end(self):
        """The demonstration the repair required: build a repo state where
        the local commit collapses ordering (the squash shape) AND the
        underlying PR history -- the only remaining evidence -- shows the
        result was actually introduced first. `verify()` must return
        non-ok, not fall back to accepting the collapsed commit as proof
        of nothing-wrong."""
        colliding = self._commit_both_files_together("verification_pr: 3131")
        gh = _fake_gh_runner(
            commit_shas=["aaa1", "bbb2"],
            files_by_sha={"aaa1": [vp.RESULTS_PATH],
                           "bbb2": [vp.PREREG_PATH]},
            merge_commit_sha=colliding)
        ok, msg = vp.verify(self.repo_root, gh_runner=gh)
        self.assertFalse(ok)
        self.assertIn("does NOT show", msg)

    def test_attack1_unrelated_pin_is_refused_end_to_end(self):
        """PR #3171's independent-verification finding, reproduced end to
        end: a fresh same-commit collision (the textbook squash shape) is
        pinned via `verification_pr:` at an old, legitimate, UNRELATED PR
        whose own real history happens to touch the two paths in the
        correct order. Before this fix `verify()` returned `ok=True` here
        -- the fallback trusted "some PR has the right order" instead of
        "the pinned PR actually produced this commit". It must now be
        refused because the unrelated PR's merge commit does not match
        the commit under review."""
        colliding = self._commit_both_files_together("verification_pr: 9999")
        gh = _fake_gh_runner(
            commit_shas=["legit1", "legit2"],
            files_by_sha={"legit1": [vp.PREREG_PATH],
                           "legit2": [vp.RESULTS_PATH]},
            merge_commit_sha="cafebabe" * 5)
        ok, msg = vp.verify(self.repo_root, gh_runner=gh)
        self.assertFalse(ok)
        self.assertIn("does not match the colliding commit", msg)

    def test_rename_into_results_path_does_not_bypass_ordering(self):
        """Warrant-hunt finding (round 2, docs/issue-3127/reports/
        implementation-blueprint+experiment-trust+silent-failure-audit-
        cc11fc03/hunt-round2-verification_pr-bind.md): `_first_commit_for_
        path` used to run `git log --diff-filter=A --follow`, and
        `--follow`'s rename-tracking made that query return EMPTY for a
        path that was introduced via a `git mv` rather than a fresh `git
        add` -- reproduced live on git 2.34.1. `verify()` reads an empty
        (None) results_commit as "results not yet committed" and returns
        True unconditionally, so committing real results content under a
        placeholder name, `git mv`-ing it to RESULTS_PATH, and only then
        committing the pre-registration (the actual violation) used to
        pass. `--follow` is dropped; this must now correctly see the
        rename as the commit that introduces RESULTS_PATH and refuse the
        out-of-order case."""
        placeholder = self.repo_root / "docs/issue-3127/_assets/placeholder.json"
        placeholder.parent.mkdir(parents=True)
        placeholder.write_text('{"run_status": "WIN"}\n')
        self._git("add", str(placeholder.relative_to(self.repo_root)))
        self._git("commit", "-q", "-m", "results content under placeholder name")

        self._git("mv",
                   str(placeholder.relative_to(self.repo_root)),
                   vp.RESULTS_PATH)
        self._git("commit", "-q", "-m", "rename to real results path")

        prereg = self.repo_root / vp.PREREG_PATH
        prereg.parent.mkdir(parents=True)
        prereg.write_text("---\nissue: 3127\n---\nprereg committed after "
                           "results already existed\n")
        self._git("add", vp.PREREG_PATH)
        self._git("commit", "-q", "-m",
                   "commit pre-registration AFTER results already exist")

        ok, msg = vp.verify(self.repo_root)
        self.assertFalse(ok, msg)


if __name__ == "__main__":
    unittest.main()
