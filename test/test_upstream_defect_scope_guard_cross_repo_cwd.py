"""Regression test for issue #2669: `upstream-defect-scope-guard.sh`
resolved "this session's own git origin repo" from the PreToolUse
payload's `cwd` field alone — the harness's fixed per-session workspace
directory, which does not track a `cd` the guarded command itself
performs. A session with a genuine local checkout of a second repo it
legitimately works in (`cd <repo-B> && gh pr create --repo owner/repo-B`)
was denied regardless of the `cd`, because origin was always resolved
against the first (harness) repo.

Runs the real shipped hook (`bash on-the-record/hooks/
upstream-defect-scope-guard.sh`) via a real PreToolUse JSON payload on
stdin, against real local git checkouts — same harness shape as
test/test_deliverable_guard_priorities_shard.py.

Two directions both matter (issue #2669 Acceptance): the legitimate
cross-repo PR must now be allowed, AND the case the guard was written
for (an unrelated repo the session has no real checkout of at all) must
still be denied.

A residual gap is pinned as `expectedFailure`, not silently left
uncovered, per issue #2637's precedent that no path/git-derived
resolution a hook computes from session-reported strings before the
write can be made fully unsteerable: a session can fabricate a
throwaway local checkout with a spoofed `origin` remote and `cd` into
it, which this fix cannot and does not close.

PR #2703 independent review found a further, undisclosed regression in
the first cut of this fix: `cd`-ing into a directory that is not a git
checkout at all (`/tmp`, a nonexistent path) made origin resolution
fail for every target, and the guard's pre-existing unresolvable-origin
fail-open fallback then allowed any `--repo` target — a session-steerable
bypass of the guard's whole purpose, not a narrower gap. Covered below
by `test_cd_into_non_checkout_dir_still_denied` and
`test_cd_into_nonexistent_dir_still_denied`, alongside a control
(`test_harness_cwd_unresolvable_without_cd_still_fails_open`) proving
the pre-#2669 fail-open posture is untouched when the unresolvable
directory is the harness's own payload cwd rather than session-chosen.

An independent adversarial evaluator session (given only this diff, no
issue context) surfaced a second instance of the same session-mutable-
local-git-state class as the spoofed-origin gap above, this one
pre-dating #2669: the harness's own payload cwd is a real checkout the
session has ordinary write access to, so `git remote remove origin`
there (in an earlier call) makes a later bare `gh pr create` fail open
for any target too. Not a new regression from this fix and not fixable
without dropping the pre-#2669 fail-open fallback outright (out of
scope here) — pinned live as
`test_harness_cwd_origin_removed_bypass_should_be_denied` rather than
left silently uncovered.

Issue #2709: three more cd-adjacent shapes disclosed in prose by #2669/
#2706 (`pushd`, a `cd` inside a subshell, a chained `cd A && cd B`) but
never pinned by a test. Covered below by
`test_pushd_not_followed_still_denied`,
`test_subshell_cd_not_followed_still_denied`, and
`test_chained_cd_uses_first_target_not_final_still_denied` — all three
pin today's actual (deny) verdict, the safe direction; #2669's own
conclusion (inherited from #2637) is that this fix does not attempt to
follow them.

Run: python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "upstream-defect-scope-guard.sh"

_FIXTURE_BASE = Path.home() / ".otr-udsg-test-fixture"


def _init_repo_with_origin(root: Path, origin_url: str):
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, timeout=30)
    subprocess.run(["git", "remote", "add", "origin", origin_url],
                    cwd=root, check=True, timeout=30)


def _run_guard(command: str, cwd: str, env_extra: dict | None = None):
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd,
        "session_id": "test-sess",
    })
    env = dict(os.environ)
    env.pop("ORCHESTRATE_OFF", None)
    env.pop("CLAUDE_SKILL", None)
    env.pop("MUSTER_SKILLS", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload, capture_output=True, text=True,
        cwd=cwd, env=env, timeout=30,
    )


def _assert_denied_for_documented_reason(test_case, result):
    """rc==2 alone can't distinguish "denied per the documented policy"
    from "the hook crashed" — its own `trap` (upstream-defect-scope-
    guard.sh line 99) remaps ANY unexpected nonzero exit to 2 as well.
    Require the actual policy-denial message on stderr, per issue #2637's
    /issue #2709's own bar for what a pinning test must show."""
    test_case.assertIn("issue #1131 req#4", result.stderr, result.stderr)
    test_case.assertNotIn("Traceback", result.stderr, result.stderr)


class CrossRepoCwdDisagreementTest(unittest.TestCase):
    """Acceptance check 3: construct the harness-cwd vs. actual-checkout
    disagreement and show which one the guard now uses."""

    def setUp(self):
        _FIXTURE_BASE.mkdir(parents=True, exist_ok=True)
        self._tmp = tempfile.TemporaryDirectory(dir=str(_FIXTURE_BASE))
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        # repo A: the harness's own workspace / payload cwd.
        self.repo_a = base / "repo-a"
        _init_repo_with_origin(
            self.repo_a, "git@github.com:tokenmaxxxer/on-the-record.git")
        # repo B: a real second checkout the session legitimately works
        # in, with a pushed branch — the case #2600's env-var slice hit.
        self.repo_b = base / "repo-b"
        _init_repo_with_origin(
            self.repo_b, "git@github.com:tokenmaxxxer/tokenmaxxxer-core.git")

    def test_legitimate_cross_repo_pr_now_allowed(self):
        """Acceptance check 1: from a session whose workspace (payload
        cwd) is repo A, with a real checkout of repo B, `cd`-ing into
        repo B before `gh pr create --repo repo-B` is no longer denied."""
        cmd = (f"cd {self.repo_b} && gh pr create "
               "--repo tokenmaxxxer/tokenmaxxxer-core "
               "--title x --body y")
        r = _run_guard(cmd, cwd=str(self.repo_a))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_same_call_without_cd_still_denied(self):
        """Without the `cd`, the payload cwd (repo A) is still what
        resolves — proving the disagreement is real, not a no-op."""
        cmd = ("gh pr create --repo tokenmaxxxer/tokenmaxxxer-core "
               "--title x --body y")
        r = _run_guard(cmd, cwd=str(self.repo_a))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_unrelated_upstream_repo_still_denied(self):
        """Acceptance check 2: the case the guard was written for — a
        repo the session has no real checkout of at all — is still
        denied even from inside repo B, since repo B's own origin still
        doesn't match the unrelated target."""
        cmd = ("gh pr create --repo some-unrelated-org/upstream-repo "
               "--title x --body y")
        r = _run_guard(cmd, cwd=str(self.repo_b))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_cd_into_unrelated_repo_checkout_still_denied(self):
        """Even resolving via the `cd`-target directory, a real checkout
        whose own origin is neither repo A nor the target is denied."""
        repo_c = Path(self._tmp.name) / "repo-c"
        _init_repo_with_origin(
            repo_c, "git@github.com:some-other-org/some-other-repo.git")
        cmd = (f"cd {repo_c} && gh pr create "
               "--repo some-unrelated-org/upstream-repo --title x --body y")
        r = _run_guard(cmd, cwd=str(self.repo_a))
        self.assertEqual(r.returncode, 2, r.stderr)

    # --- issue #2709: three cd-adjacent shapes disclosed in prose by
    # #2669/#2706 ("A leading `cd <dir> &&`/`cd <dir>;`" — see the guard's
    # own `operative_cwd` docstring) but never pinned by a test: `pushd`,
    # a `cd` inside a `(...)` subshell, and a chained `cd A && cd B`. Each
    # is denied today because `operative_cwd`'s regex only matches a
    # literal leading `cd <dir>` token and only takes the FIRST such
    # match — the safe direction per the issue, so these pin deny, not an
    # aspiration. Confirmed discriminating (not tautological) against a
    # mutant `operative_cwd` that also recognizes `pushd`, strips a
    # leading `(`, and follows the LAST chained `cd`: all three flip to
    # rc=0 (allow) under that mutant, and stay rc=2 (deny) against the
    # shipped hook.
    def test_pushd_not_followed_still_denied(self):
        """`pushd <repo-b> && gh pr create --repo repo-b`, otherwise
        identical to `test_legitimate_cross_repo_pr_now_allowed`. Origin
        is resolved from the payload cwd (repo A), not the `pushd`
        target, because `operative_cwd`'s regex matches only a literal
        leading `cd`."""
        cmd = (f"pushd {self.repo_b} && gh pr create "
               "--repo tokenmaxxxer/tokenmaxxxer-core "
               "--title x --body y")
        r = _run_guard(cmd, cwd=str(self.repo_a))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_for_documented_reason(self, r)

    def test_subshell_cd_not_followed_still_denied(self):
        """`(cd <repo-b> && gh pr create --repo repo-b)` — the command
        text starts with `(`, not `cd`, so `operative_cwd`'s anchored
        regex never matches and origin is resolved from the payload cwd
        (repo A) instead of the subshell's target."""
        cmd = (f"(cd {self.repo_b} && gh pr create "
               "--repo tokenmaxxxer/tokenmaxxxer-core "
               "--title x --body y)")
        r = _run_guard(cmd, cwd=str(self.repo_a))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_for_documented_reason(self, r)

    def test_chained_cd_uses_first_target_not_final_still_denied(self):
        """`cd <repo-a> && cd <repo-b> && gh pr create --repo repo-b` —
        `operative_cwd` takes only the FIRST leading `cd` (here, back to
        repo A, whose origin is on-the-record), not the final directory
        the command actually runs `gh pr create` in (repo B, whose
        origin matches the target). Denied today because origin is
        resolved against repo A, not repo B, even though the real final
        cwd would match the target."""
        cmd = (f"cd {self.repo_a} && cd {self.repo_b} && gh pr create "
               "--repo tokenmaxxxer/tokenmaxxxer-core "
               "--title x --body y")
        r = _run_guard(cmd, cwd=str(self.repo_a))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_for_documented_reason(self, r)

    # --- PR #2703 review: the unresolvable-origin fallback existed before
    # #2669 (no git repo, no origin remote => fail open), but it only used
    # to fire on the harness's own payload cwd, which the session could
    # not choose. Once `cd`-target resolution shipped, an unresolvable
    # directory became session-steerable: `cd` into anything that is not
    # a git checkout at all, and origin resolution fails for every
    # target. These two cases must land differently.
    def test_cd_into_non_checkout_dir_still_denied(self):
        """A `cd` to a directory with no git repo at all (the most
        mundane non-checkout shape) must not buy an unconditional allow
        for any target repo — this was PR #2700's regression."""
        non_repo_dir = Path(self._tmp.name) / "not-a-checkout"
        non_repo_dir.mkdir()
        cmd = (f"cd {non_repo_dir} && gh pr create "
               "--repo some-unrelated-org/upstream-repo --title x --body y")
        r = _run_guard(cmd, cwd=str(self.repo_a))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_cd_into_nonexistent_dir_still_denied(self):
        """Same shape, a path that does not exist on disk at all."""
        cmd = ("cd /nonexistent-otr-udsg-test-path && gh pr create "
               "--repo some-unrelated-org/upstream-repo --title x --body y")
        r = _run_guard(cmd, cwd=str(self.repo_a))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_harness_cwd_unresolvable_without_cd_still_fails_open(self):
        """Without a `cd`, an unresolvable HARNESS payload cwd (not
        session-chosen) keeps the pre-#2669 fail-open posture — that
        fallback predates this fix and is not what PR #2703 flagged."""
        non_repo_dir = Path(self._tmp.name) / "harness-not-a-checkout"
        non_repo_dir.mkdir()
        cmd = ("gh pr create --repo some-unrelated-org/upstream-repo "
               "--title x --body y")
        r = _run_guard(cmd, cwd=str(non_repo_dir))
        self.assertEqual(r.returncode, 0, r.stderr)

    # --- issue #2637 precedent: the git-origin resolution this fix reads
    # is itself session-mutable filesystem state — a session can fabricate
    # a throwaway checkout with a spoofed `origin` remote pointed at the
    # target repo and `cd` into it, with zero real relationship to that
    # repo. No path/git-derived resolution a hook computes from
    # session-reported strings before the write can be made fully
    # unsteerable (docs/issue-2637/reports/silent-failure-audit+
    # architecture-interface-contract-shape-149dabd2.md). This fix does
    # not close that; pinned here as a live regression rather than left
    # silently uncovered.
    @unittest.expectedFailure
    def test_spoofed_origin_remote_bypass_should_be_denied(self):
        spoofed = Path(self._tmp.name) / "spoofed"
        _init_repo_with_origin(
            spoofed, "git@github.com:some-unrelated-org/upstream-repo.git")
        cmd = (f"cd {spoofed} && gh pr create "
               "--repo some-unrelated-org/upstream-repo --title x --body y")
        r = _run_guard(cmd, cwd=str(self.repo_a))
        self.assertEqual(r.returncode, 2, r.stderr)

    # --- adversarial review of this same fix (independent evaluator
    # session, not #2637/#2703) surfaced a second instance of the same
    # session-mutable-local-git-state class, pre-dating #2669 and
    # unrelated to the `cd`-target mechanism: the harness's own payload
    # cwd is itself a real checkout the session has ordinary write access
    # to. A session that runs `git remote remove origin` there in an
    # earlier call makes ORIGIN_REPO unresolvable on a later bare (no
    # `cd`) call, which the guard's pre-#2669 fail-open fallback then
    # allows for any target. Not a new regression from this fix (the
    # send-back's own scoping explicitly keeps the harness-cwd-
    # unresolvable case failing open, "as today"), and not fixable by
    # this guard without dropping that pre-existing fallback entirely —
    # pinned live rather than silently uncovered, same posture as the
    # spoofed-origin gap above.
    @unittest.expectedFailure
    def test_harness_cwd_origin_removed_bypass_should_be_denied(self):
        mutated = Path(self._tmp.name) / "harness-mutated"
        _init_repo_with_origin(
            mutated, "git@github.com:tokenmaxxxer/on-the-record.git")
        subprocess.run(["git", "remote", "remove", "origin"],
                        cwd=mutated, check=True, timeout=30)
        cmd = ("gh pr create --repo some-unrelated-org/upstream-repo "
               "--title x --body y")
        r = _run_guard(cmd, cwd=str(mutated))
        self.assertEqual(r.returncode, 2, r.stderr)


if __name__ == "__main__":
    unittest.main()
