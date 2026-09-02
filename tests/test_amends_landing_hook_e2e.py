"""Issue #3134 repair round 4: PR #3168's independent verification found
that `gates/amends_landing.py::land()` is sound but the `PostToolUse`
trigger that calls it automatically, `on-the-record/hooks/amends-landing-
apply.sh`, was not -- its command-shape check matched `gh pr merge
--help`, and its old "no failure marker in the tool_response text"
success heuristic treated that non-merge command as a successful merge.
PR #3168 reproduced a real clone+push to a scratch remote's default
branch in response to `gh pr merge --help`.

This file drives the REAL hook script with realistic `PostToolUse`
payloads -- the exact gap PR #3168 named: "The new e2e test never drives
the hook script itself (only calls `land()` directly), so this defect
has zero test coverage." A fake `gh` on `PATH` answers `gh pr view --json
state,mergedAt` (the new authoritative signal the fixed hook requires);
everything else -- `git`, the real `gates/amends_landing.py` -- is real.

  python3 -m pytest tests/test_amends_landing_hook_e2e.py -q
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = ROOT / "on-the-record" / "hooks"
HOOK = HOOKS_DIR / "amends-landing-apply.sh"

FAKE_GH_SCRIPT = """#!/usr/bin/env bash
# fake `gh` for tests -- only implements `gh pr view ... --json state,mergedAt`,
# the one subcommand amends-landing-apply.sh's fixed trigger calls.
if [ "$1" = "pr" ] && [ "$2" = "view" ]; then
  if [ -n "${FAKE_GH_EXIT:-}" ] && [ "${FAKE_GH_EXIT}" != "0" ]; then
    echo "${FAKE_GH_STDERR:-no such pull request}" >&2
    exit "${FAKE_GH_EXIT}"
  fi
  json="${FAKE_GH_JSON:-}"
  [ -n "$json" ] || json='{}'
  printf '%s' "$json"
  exit 0
fi
echo "fake gh: unsupported invocation: $*" >&2
exit 1
"""


def _git(*args, cwd):
    r = subprocess.run(["git", "-C", str(cwd), *args],
                        capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r.stdout


class AmendsLandingHookEndToEndTest(unittest.TestCase):
    """Builds a bare remote + a local checkout (`origin` pointed at it,
    matching what `gh pr merge` runs against for real), then invokes the
    real hook binary with a realistic `PostToolUse` payload for each
    scenario and asserts on the remote's own tip commit -- the only
    ground truth for "did this push."
    """

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())

        fake_bin = self._tmp / "fakebin"
        fake_bin.mkdir()
        gh_path = fake_bin / "gh"
        gh_path.write_text(FAKE_GH_SCRIPT, encoding="utf-8")
        gh_path.chmod(gh_path.stat().st_mode | stat.S_IEXEC)
        self._fake_bin = fake_bin

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _build_fixture(self, name: str, with_edge: bool) -> tuple[Path, Path]:
        """A bare remote + a local checkout with `origin` set to it and
        `origin/HEAD` resolvable (what the hook's own remote/branch
        resolution needs) -- optionally carrying one unresolved `amends:`
        edge, landed and pushed, exactly what a merged correcting PR's
        checkout looks like right before the landing step runs."""
        base = self._tmp / name
        bare = base / "remote.git"
        work = base / "work"
        base.mkdir()

        subprocess.run(["git", "init", "-q", "--bare", str(bare)],
                        check=True, capture_output=True)

        work.mkdir()
        _git("init", "-q", "-b", "main", cwd=work)
        _git("config", "user.email", "t@t", cwd=work)
        _git("config", "user.name", "t", cwd=work)

        target_dir = work / "docs" / "issue-97001" / "reports"
        target_dir.mkdir(parents=True)
        (target_dir / "target.md").write_text(
            "---\nissue: 97001\nrole: target-record\n---\n\n"
            "# issue-97001 record\n\n"
            "## Limitation\n\nThe claim in this section is wrong.\n",
            encoding="utf-8",
        )
        (work / "docs" / "specs").mkdir(parents=True, exist_ok=True)
        sys.path.insert(0, str(ROOT / "gates"))
        import amends_index as _amends_index_for_fixture
        _amends_index_for_fixture.update(work)

        _git("add", "-A", cwd=work)
        _git("commit", "-q", "-m", "initial landed tree", cwd=work)

        if with_edge:
            corrector_dir = work / "docs" / "issue-97002" / "reports"
            corrector_dir.mkdir(parents=True)
            (corrector_dir / "corrector.md").write_text(
                "---\nissue: 97002\nrole: corrector\n"
                "amends: docs/issue-97001/reports/target.md#limitation"
                "  # verified independently: it is actually right"
                "\n---\n\n## Correction\n\ntext\n",
                encoding="utf-8",
            )
            _git("add", "-A", cwd=work)
            _git("commit", "-q", "-m", "issue-97002: correction", cwd=work)

        _git("push", "-q", str(bare), "main", cwd=work)
        subprocess.run(["git", "-C", str(bare), "symbolic-ref", "HEAD",
                         "refs/heads/main"], check=True, capture_output=True)

        _git("remote", "add", "origin", str(bare), cwd=work)
        _git("fetch", "-q", "origin", cwd=work)
        _git("remote", "set-head", "origin", "-a", cwd=work)

        return bare, work

    def _bare_tip(self, bare: Path) -> str:
        return _git("rev-parse", "main", cwd=bare).strip()

    def _run_hook(self, run_cwd: Path, command: str, tool_response: str,
                  gh_json: str | None = None, gh_exit: str | None = None,
                  session_id: str = "hook-e2e") -> subprocess.CompletedProcess:
        payload = json.dumps({
            "tool_name": "Bash",
            "session_id": session_id,
            "cwd": str(run_cwd),
            "tool_input": {"command": command},
            "tool_response": tool_response,
        })
        env = {
            "PATH": f"{self._fake_bin}:/usr/bin:/bin:/usr/local/bin",
            "HOME": os.environ.get("HOME", "/tmp"),
        }
        if gh_json is not None:
            env["FAKE_GH_JSON"] = gh_json
        if gh_exit is not None:
            env["FAKE_GH_EXIT"] = gh_exit
        return subprocess.run(
            ["bash", str(HOOK)], input=payload, env=env,
            capture_output=True, text=True, timeout=60, cwd=str(run_cwd),
        )

    def test_help_invocation_never_pushes(self):
        # class A ("not a merge, nothing to do"): `--help` matches the
        # command shape but never merges anything -- silent, exit 0, zero
        # stderr lines (the designed quiet outcome, not an absorbed
        # failure -- see test_ordinary_non_gh_command_produces_zero_stderr
        # for the anti-spam guard this must not violate).
        bare, work = self._build_fixture("help", with_edge=True)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge --help",
            tool_response="Usage: gh pr merge [<number> | <url> | <branch>] [flags]\n...",
            gh_json='{"state": "MERGED", "mergedAt": "2026-09-02T00:00:00Z"}',
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual("", r.stderr, "class A must produce zero stderr lines")
        self.assertEqual(
            before, self._bare_tip(bare),
            "`gh pr merge --help` must never push a landing-step commit -- "
            "PR #3168 reproduced exactly this as a real push to main",
        )

    def test_ordinary_non_gh_command_produces_zero_stderr(self):
        # Given an ordinary Bash command with nothing to do with `gh pr
        # merge` at all, when the hook runs on it, then it must produce
        # ZERO stderr lines and exit 0 -- this is the anti-spam guard for
        # class A: every single Bash call in a session reaches this hook,
        # so a stderr line on each one would bury the real signal.
        bare, work = self._build_fixture("ordinary", with_edge=True)
        before = self._bare_tip(bare)
        for command in ("ls", "echo hi"):
            r = self._run_hook(work, command, tool_response="hi\n")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(
                "", r.stderr,
                f"ordinary command {command!r} must produce zero stderr "
                f"lines from this hook, got: {r.stderr!r}",
            )
        self.assertEqual(before, self._bare_tip(bare))

    def test_failed_merge_never_pushes(self):
        # issue #3134 repair round 5, gap 2, class C ("was a merge,
        # confirmed not merged"): must now exit nonzero with exactly one
        # stderr line -- PR #3175 found this path silent (`exit 0`, no
        # stderr) before this round.
        bare, work = self._build_fixture("failed", with_edge=True)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge 42 --squash",
            tool_response="X Failed to merge pull request #42: Pull "
                           "Request is not mergeable: the merge commit "
                           "cannot be cleanly created.",
            gh_json='{"state": "OPEN", "mergedAt": null}',
        )
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertEqual(
            1, len([ln for ln in r.stderr.splitlines() if ln.strip()]),
            f"expected exactly one stderr line, got: {r.stderr!r}",
        )
        self.assertEqual(
            before, self._bare_tip(bare),
            "a merge `gh pr view` itself reports as still OPEN must never push",
        )

    def test_successful_merge_zero_edges_never_pushes(self):
        bare, work = self._build_fixture("clean", with_edge=False)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge 42 --squash",
            tool_response="Merged pull request #42 (some unrelated PR) "
                           "into main from feature-branch",
            gh_json='{"state": "MERGED", "mergedAt": "2026-09-02T00:00:00Z"}',
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            before, self._bare_tip(bare),
            "a genuine merge with no amends: edges has nothing to apply -- "
            "must not push an empty landing-step commit",
        )

    def test_genuine_merge_with_edge_pushes_the_backlink(self):
        bare, work = self._build_fixture("edge", with_edge=True)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge 42 --squash",
            tool_response="Merged pull request #42 (issue-97002: "
                           "correction) into main from issue-97002-branch",
            gh_json='{"state": "MERGED", "mergedAt": "2026-09-02T00:00:00Z"}',
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        after = self._bare_tip(bare)
        self.assertNotEqual(
            before, after,
            "a genuine merge with an unresolved amends: edge must push "
            "the landing-step backlink commit -- this is the only "
            "scenario of the four that should push",
        )
        landed_target = _git("show", "main:docs/issue-97001/reports/"
                              "target.md", cwd=bare)
        self.assertIn("> **Amended**", landed_target)

    # -- issue #3134 repair round 5: repo-match x decline-class decision
    # table (PR #3175's two gaps). Registered repo is always the bare
    # remote built by `_build_fixture` for the `work` checkout passed as
    # `run_cwd`; "-R"/"--repo"/"--repo="/an inline `GH_REPO=` prefix/a
    # `cd` to a second, DIFFERENT checkout each name a repo outside that
    # remit and must be refused before any `gh pr view` confirmation call
    # -- write nothing, exactly one stderr line naming both repos, nonzero
    # exit. --------------------------------------------------------------

    def _assert_repo_refused(self, work, bare, command, tool_response,
                              registered_needle, target_needle):
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, command, tool_response=tool_response,
            gh_json='{"state": "MERGED", "mergedAt": "2026-09-02T00:00:00Z"}',
        )
        self.assertNotEqual(r.returncode, 0, r.stdout)
        lines = [ln for ln in r.stderr.splitlines() if ln.strip()]
        self.assertEqual(
            1, len(lines),
            f"expected exactly one stderr line, got: {r.stderr!r}",
        )
        self.assertIn(registered_needle.lower(), lines[0].lower())
        self.assertIn(target_needle.lower(), lines[0].lower())
        self.assertEqual(
            before, self._bare_tip(bare),
            "an out-of-remit repo target must never push",
        )

    def test_dash_R_flag_naming_another_repo_is_refused(self):
        # Given a merge naming another repo via `-R`, when the hook runs,
        # then it refuses: nothing written, one stderr line naming both
        # repos, nonzero exit.
        bare, work = self._build_fixture("mismatch-dashr", with_edge=True)
        self._assert_repo_refused(
            work, bare, "gh pr merge 42 -R other-owner/other-repo",
            "Merged pull request #42 into main",
            registered_needle="mismatch-dashr", target_needle="other-owner/other-repo",
        )

    def test_dash_dash_repo_flag_naming_another_repo_is_refused(self):
        bare, work = self._build_fixture("mismatch-longrepo", with_edge=True)
        self._assert_repo_refused(
            work, bare, "gh pr merge 42 --repo other-owner/other-repo",
            "Merged pull request #42 into main",
            registered_needle="mismatch-longrepo", target_needle="other-owner/other-repo",
        )

    def test_dash_dash_repo_equals_flag_naming_another_repo_is_refused(self):
        bare, work = self._build_fixture("mismatch-eqrepo", with_edge=True)
        self._assert_repo_refused(
            work, bare, "gh pr merge 42 --repo=other-owner/other-repo",
            "Merged pull request #42 into main",
            registered_needle="mismatch-eqrepo", target_needle="other-owner/other-repo",
        )

    def test_GH_REPO_env_prefix_naming_another_repo_is_refused(self):
        # The only observable form of "GH_REPO env var" here: Claude's
        # Bash tool does not persist exported env vars across calls, so a
        # real `GH_REPO=...` override can only show up as an inline
        # prefix on the one command that used it.
        bare, work = self._build_fixture("mismatch-ghrepo-env", with_edge=True)
        self._assert_repo_refused(
            work, bare, "GH_REPO=other-owner/other-repo gh pr merge 42",
            "Merged pull request #42 into main",
            registered_needle="mismatch-ghrepo-env", target_needle="other-owner/other-repo",
        )

    def test_cd_into_another_checkout_then_merge_is_refused(self):
        # A `cd DIR && gh pr merge` where DIR is a checkout of a
        # DIFFERENT repo (different `origin`) -- the shape PR #3175 named
        # as outside this hook's remit alongside `-R`.
        bare, work = self._build_fixture("mismatch-cd-registered", with_edge=True)
        other_bare, other_work = self._build_fixture("mismatch-cd-other", with_edge=False)
        self._assert_repo_refused(
            work, bare, f"cd {other_work} && gh pr merge 42",
            "Merged pull request #42 into main",
            registered_needle="mismatch-cd-registered", target_needle="mismatch-cd-other",
        )
        # the OTHER checkout's own remote must be untouched too
        self.assertEqual(
            self._bare_tip(other_bare),
            _git("rev-parse", "main", cwd=other_bare).strip(),
        )

    def test_dash_R_flag_naming_the_registered_repo_still_lands(self):
        # Feasible column the matrix must not false-positive on: `-R`
        # naming the SAME repo the session is registered against is not
        # an out-of-remit merge and must still land the backlink.
        bare, work = self._build_fixture("same-repo-dashr", with_edge=True)
        registered_url = _git("remote", "get-url", "origin", cwd=work).strip()
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, f"gh pr merge 42 -R {registered_url}",
            tool_response="Merged pull request #42 (issue-97002: "
                           "correction) into main from issue-97002-branch",
            gh_json='{"state": "MERGED", "mergedAt": "2026-09-02T00:00:00Z"}',
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(
            before, self._bare_tip(bare),
            "-R naming the session's own registered repo must still land",
        )

    # -- decline classes A/B/C as their own test functions ----------------

    def test_class_B_confirmation_gh_exit_failure_declines_once(self):
        # Given a merge command, when `gh pr view` itself exits nonzero
        # (auth failure/network error), then the hook declines with
        # exactly one stderr line and a nonzero exit -- distinct wording
        # from class C (confirmed not merged): this is "confirmation
        # could not run" at all.
        bare, work = self._build_fixture("class-b-exit", with_edge=True)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge 42 --squash",
            tool_response="Merged pull request #42 into main",
            gh_exit="1", gh_json="",
        )
        self.assertNotEqual(r.returncode, 0, r.stdout)
        lines = [ln for ln in r.stderr.splitlines() if ln.strip()]
        self.assertEqual(1, len(lines), f"got: {r.stderr!r}")
        self.assertIn("confirmation failed", lines[0])
        self.assertEqual(before, self._bare_tip(bare))

    def test_class_B_confirmation_malformed_json_declines_once(self):
        # Given a merge command, when `gh pr view` exits 0 but its stdout
        # is not valid JSON, then the hook declines with exactly one
        # stderr line and a nonzero exit -- same class B as an auth
        # failure: confirmation could not run, not "confirmed unmerged".
        bare, work = self._build_fixture("class-b-json", with_edge=True)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge 42 --squash",
            tool_response="Merged pull request #42 into main",
            gh_json="not-json-at-all",
        )
        self.assertNotEqual(r.returncode, 0, r.stdout)
        lines = [ln for ln in r.stderr.splitlines() if ln.strip()]
        self.assertEqual(1, len(lines), f"got: {r.stderr!r}")
        self.assertIn("confirmation failed", lines[0])
        self.assertEqual(before, self._bare_tip(bare))

    def test_class_C_confirmed_not_merged_declines_once(self):
        # Given a merge command, when `gh pr view` succeeds and reports a
        # state other than MERGED, then the hook declines with exactly
        # one stderr line and a nonzero exit. (Also covered end-to-end by
        # test_failed_merge_never_pushes above; this is the class's own
        # minimal Given-When-Then case.)
        bare, work = self._build_fixture("class-c", with_edge=True)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge 42 --squash",
            tool_response="Merged pull request #42 into main",
            gh_json='{"state": "CLOSED", "mergedAt": null}',
        )
        self.assertNotEqual(r.returncode, 0, r.stdout)
        lines = [ln for ln in r.stderr.splitlines() if ln.strip()]
        self.assertEqual(1, len(lines), f"got: {r.stderr!r}")
        self.assertIn("not merged", lines[0])
        self.assertEqual(before, self._bare_tip(bare))


if __name__ == "__main__":
    unittest.main()
