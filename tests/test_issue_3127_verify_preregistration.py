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
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "issue-3127"))
import verify_preregistration as vp  # noqa: E402


def _completed(stdout="", returncode=0):
    return subprocess.CompletedProcess(args=[], returncode=returncode,
                                        stdout=stdout, stderr="")


def _fake_gh_runner(commit_shas, files_by_sha, owner_repo="acme/widgets"):
    """A `gh` stand-in: no network, no subprocess -- just enough of the
    `gh pr view --json commits` / `gh repo view` / `gh api .../commits/SHA`
    surface for `_resolve_via_pr_history` to run its real logic against a
    scripted commit history."""
    import json

    def runner(args):
        if args[:2] == ["repo", "view"]:
            return _completed(stdout=owner_repo + "\n")
        if args[:2] == ["pr", "view"]:
            payload = json.dumps({"commits": [{"oid": s} for s in commit_shas]})
            return _completed(stdout=payload)
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
    falls back to on a same-commit collision."""

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
                           "bbb2": [vp.RESULTS_PATH]})
        ok, msg = vp._resolve_via_pr_history(self.repo_root, gh)
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
                           "bbb2": [vp.PREREG_PATH]})
        ok, msg = vp._resolve_via_pr_history(self.repo_root, gh)
        self.assertFalse(ok)
        self.assertIn("does NOT show", msg)

    def test_violation_same_pr_commit_is_refused(self):
        """A second violation shape: both paths first appear in the same
        PR commit (index tie) -- still not strictly-before, still refused."""
        self._write_prereg("verification_pr: 3131")
        gh = _fake_gh_runner(
            commit_shas=["aaa1"],
            files_by_sha={"aaa1": [vp.PREREG_PATH, vp.RESULTS_PATH]})
        ok, msg = vp._resolve_via_pr_history(self.repo_root, gh)
        self.assertFalse(ok)

    def test_missing_verification_pr_field_fails_closed(self):
        self._write_prereg("status: registered")
        gh = _fake_gh_runner(commit_shas=["aaa1"], files_by_sha={})
        ok, msg = vp._resolve_via_pr_history(self.repo_root, gh)
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

        ok, msg = vp._resolve_via_pr_history(self.repo_root, gh)
        self.assertFalse(ok)
        self.assertIn("failed", msg)

    def test_gh_repo_view_failure_fails_closed(self):
        self._write_prereg("verification_pr: 3131")

        def gh(args):
            return _completed(returncode=1, stdout="")

        ok, msg = vp._resolve_via_pr_history(self.repo_root, gh)
        self.assertFalse(ok)

    def test_path_absent_from_pr_history_fails_closed(self):
        self._write_prereg("verification_pr: 3131")
        gh = _fake_gh_runner(commit_shas=["aaa1"],
                              files_by_sha={"aaa1": ["some/other/file.txt"]})
        ok, msg = vp._resolve_via_pr_history(self.repo_root, gh)
        self.assertFalse(ok)
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

    def test_legitimate_pr_history_resolves_the_collision(self):
        self._commit_both_files_together("verification_pr: 3131")
        gh = _fake_gh_runner(
            commit_shas=["aaa1", "bbb2"],
            files_by_sha={"aaa1": [vp.PREREG_PATH],
                           "bbb2": [vp.RESULTS_PATH]})
        ok, msg = vp.verify(self.repo_root, gh_runner=gh)
        self.assertTrue(ok, msg)

    def test_constructed_violation_is_refused_end_to_end(self):
        """The demonstration the repair required: build a repo state where
        the local commit collapses ordering (the squash shape) AND the
        underlying PR history -- the only remaining evidence -- shows the
        result was actually introduced first. `verify()` must return
        non-ok, not fall back to accepting the collapsed commit as proof
        of nothing-wrong."""
        self._commit_both_files_together("verification_pr: 3131")
        gh = _fake_gh_runner(
            commit_shas=["aaa1", "bbb2"],
            files_by_sha={"aaa1": [vp.RESULTS_PATH],
                           "bbb2": [vp.PREREG_PATH]})
        ok, msg = vp.verify(self.repo_root, gh_runner=gh)
        self.assertFalse(ok)
        self.assertIn("does NOT show", msg)


if __name__ == "__main__":
    unittest.main()
