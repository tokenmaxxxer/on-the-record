"""Regression test for issue #2637 (adversarial-review, aba56a87 +
rejected-fix PR #2653): the `^`-anchored PRODUCT_CAPTURE_PRIORITIES_DIR_RE
exemption added to close a src/-rooted bypass must not also deny a
legitimate priorities-shard write whose `file_path` arrives absolute —
the same shape call-shape-guard.sh, accumulation-claim-guard.sh, and
record-claim-guard.sh already treat as ordinary input — while still
denying the src/-rooted bypass regardless of how the write is phrased.

`cwd` is an independent axis of every case below (repo root, and a
subdirectory `src/`) rather than always matching the fixture's repo root.
That axis is not incidental: a first fix attempt matched the exemption
regex against a *cwd*-relative form, so a session that `cd src` before
its write handed the guard a relative form that landed back inside the
exemption — the identical src/-rooted bypass the anchor was written to
close, just with `cwd` doing the steering instead of `file_path`. PR
#2653 rejected that fix and supplied the reproduction reused verbatim in
`test_absolute_bypass_via_subdirectory_cwd_stays_denied` below (the exact
payload that got `rc=0 EXEMPT` against the rejected fix). Without `cwd`
as its own axis, 8/8 green here previously proved nothing about that
bypass — every case shared one implicit cwd.

Runs the real shipped hook (`bash on-the-record/hooks/deliverable-guard.sh`)
via a real PreToolUse JSON payload on stdin, against a real git checkout —
same harness shape as test/test_approval_gate_carriers.py.

Run: python3 -m pytest test/test_deliverable_guard_priorities_shard.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "deliverable-guard.sh"

# Historically deliverable-guard.sh exempted any path with a literal
# "tmp" path segment (issue #787 H1), which would have made every
# absolute-path case below exit 0 via that unrelated exemption instead of
# the priorities-shard regex this test targets, if the fixture lived
# under the system tempdir (usually /tmp). That segment exemption was
# removed (issue #2661) but the fixture still avoids the system tempdir,
# since nothing about this test needs it.
_FIXTURE_BASE = Path.home() / ".otr-dg-test-fixture"


def _init_repo(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "src").mkdir(exist_ok=True)


def _run_gate(repo: Path, file_path: str, cwd: str | None = None):
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path},
        "cwd": cwd if cwd is not None else str(repo),
        "session_id": "test-sess",
    })
    env = dict(os.environ)
    env.pop("TOKENMAXXXER_SPAWNED", None)
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload, capture_output=True, text=True,
        cwd=repo, env=env, timeout=30,
    )


def _assert_denied_as_deliverable_path(test_case, result):
    """rc==2 alone can't distinguish "denied because it's a deliverable
    path in a board repo" from "the hook crashed" — its own `trap`
    (deliverable-guard.sh line 42) remaps ANY unexpected nonzero exit to
    2 as well. Require the actual policy-denial message on stderr."""
    test_case.assertIn(
        "deliverable path in a board repo", result.stderr, result.stderr)
    test_case.assertNotIn("Traceback", result.stderr, result.stderr)


class DeliverableGuardPrioritiesShardTest(unittest.TestCase):
    def setUp(self):
        _FIXTURE_BASE.mkdir(parents=True, exist_ok=True)
        self._tmp = tempfile.TemporaryDirectory(dir=str(_FIXTURE_BASE))
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        _init_repo(self.repo)
        self.src_cwd = str(self.repo / "src")

    # --- legitimate shard writes: EXEMPT, independent of cwd -----------

    def test_relative_shard_write_is_exempt_at_repo_root_cwd(self):
        r = _run_gate(self.repo, "docs/reports/product/priorities/x.md",
                      cwd=str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_absolute_shard_write_is_exempt_at_repo_root_cwd(self):
        r = _run_gate(
            self.repo, str(self.repo / "docs/reports/product/priorities/x.md"),
            cwd=str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_absolute_shard_write_is_exempt_from_subdirectory_cwd(self):
        # A legitimate shard write is still absolute-path-anchored to the
        # real target directory even when the session's cwd is a
        # subdirectory — cwd must not affect this legitimate case either.
        r = _run_gate(
            self.repo, str(self.repo / "docs/reports/product/priorities/x.md"),
            cwd=self.src_cwd)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_absolute_issue_scoped_shard_write_is_exempt(self):
        r = _run_gate(
            self.repo,
            str(self.repo
                / "docs/issue-99/reports/product/priorities/x.md"),
            cwd=str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_absolute_shard_write_with_dotdot_is_exempt(self):
        r = _run_gate(
            self.repo,
            str(self.repo
                / "foo/../docs/reports/product/priorities/x.md"),
            cwd=str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_absolute_legacy_priorities_file_still_exempt(self):
        r = _run_gate(
            self.repo, str(self.repo / "docs/reports/product/priorities.md"),
            cwd=str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)

    # --- src/-rooted bypass: DENIED across every calling shape ---------

    def test_relative_src_rooted_bypass_stays_denied_at_repo_root_cwd(self):
        r = _run_gate(
            self.repo, "src/docs/reports/product/priorities/hack.md",
            cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    def test_absolute_src_rooted_bypass_stays_denied_at_repo_root_cwd(self):
        r = _run_gate(
            self.repo,
            str(self.repo / "src/docs/reports/product/priorities/hack.md"),
            cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    def test_relative_bypass_via_subdirectory_cwd_stays_denied(self):
        # cwd=<repo>/src, file_path relative ("docs/reports/product/
        # priorities/hack.md") — normalizes, relative to cwd, to the same
        # src/-rooted target as the two cases above. Never exercised
        # before cwd became its own axis.
        r = _run_gate(
            self.repo, "docs/reports/product/priorities/hack.md",
            cwd=self.src_cwd)
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    def test_absolute_bypass_via_subdirectory_cwd_stays_denied(self):
        # The exact payload PR #2653 reproduced against the rejected fix:
        # cwd=<repo>/src, file_path=<repo>/src/docs/reports/product/
        # priorities/hack.md (absolute). Against the anchor-only commit
        # this was rc=2 DENIED; against the rejected fix it was rc=0
        # EXEMPT — the bypass this case pins shut.
        r = _run_gate(
            self.repo,
            str(self.repo / "src/docs/reports/product/priorities/hack.md"),
            cwd=self.src_cwd)
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    def test_real_deliverable_write_still_denied(self):
        r = _run_gate(self.repo, "src/foo.py", cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    # --- issue #2661: the removed scratch/tmp/.git/plugin-cache segment
    # exemption no longer waves through a deliverable path merely because
    # one of its segments is named "tmp" or "scratch" -----------------

    def test_src_rooted_tmp_segment_no_longer_exempt(self):
        r = _run_gate(self.repo, "src/tmp/module.py", cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    def test_docs_rooted_tmp_segment_no_longer_exempt(self):
        r = _run_gate(self.repo, "docs/tmp/note.md", cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    def test_tmp_prefixed_approvers_lookalike_no_longer_exempt(self):
        # Not just the removed segment check: "tmp/docs/specs/approvers.md"
        # also used to slip through EXEMPT_SUFFIXES' unanchored
        # `n.endswith("docs/specs/approvers.md")` (a second, independent
        # bug found while verifying this issue) — one directory short of
        # the actual sanctioned file.
        r = _run_gate(self.repo, "tmp/docs/specs/approvers.md",
                      cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    def test_genuine_approvers_md_still_exempt(self):
        r = _run_gate(self.repo, "docs/specs/approvers.md",
                      cwd=str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_scratch_segment_no_longer_exempt(self):
        r = _run_gate(self.repo, "scratch/notes.md", cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    # --- issue #2637 round 4 / issue #2659: the git-root walk's bare-name
    # trust is closed, a real nested repo still steers it -------------
    # PR #2658 found the `.git`-probing walk this exemption's cwd/abs-path
    # resolution depends on (`_git_root_from`, and the separate
    # board-repo activation walk it mirrored) trusted
    # `os.path.isdir(<probe>/".git")` as proof of "this is the repo
    # root" — a signal the very session this hook is meant to gate could
    # plant with an ordinary `mkdir`/`ln -s` before the guarded
    # Write/Edit call, since this hook only ever inspects Write/Edit/
    # MultiEdit/NotebookEdit tool calls, never plain Bash filesystem
    # mutation. Also: `.git` in a linked worktree is a FILE (a "gitdir:
    # <path>" pointer), which `os.path.isdir` never matches at all, so a
    # worktree wasn't just steerable — it fell through to "no root
    # found" and disabled the priorities-shard denial outright.
    #
    # issue #2659 replaced both walks with `git rev-parse` (see
    # `_git_root_from`/`_run_git` in the hook): it parses a `.git` FILE
    # the way git itself does (closing the worktree/submodule miss), and
    # — unlike the old walk — does not accept a bare `.git`
    # directory/symlink with no real git content as a repo boundary
    # either, so it keeps walking up past a planted one and finds the
    # actual root (verified live, docs/issue-2659 record). The four
    # cases below that used to be `expectedFailure` for exactly this
    # planted-`.git` shape now pass for real; they are kept (decorator
    # removed) as the regression coverage for the fix.
    #
    # What is NOT closed: a session that runs a genuine `git init` in a
    # subdirectory before the guarded write still steers both walks,
    # because that subdirectory is then a real, independent git
    # repository from git's own perspective, not a bare name `os.path.
    # isdir`/`git rev-parse` can tell apart from the outer one. That
    # narrower class is pinned below as `expectedFailure` — a decision
    # for issue #2637 (three prior fixes already rejected for the
    # priorities-shard exemption), not a fifth resolution attempt here.

    def test_bypass_via_planted_git_directory_should_be_denied(self):
        (self.repo / "src" / ".git").mkdir(parents=True)
        r = _run_gate(
            self.repo,
            str(self.repo / "src/docs/reports/product/priorities/hack.md"),
            cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    def test_bypass_via_planted_git_symlink_should_be_denied(self):
        elsewhere = self.repo.parent / "elsewhere"
        elsewhere.mkdir()
        (self.repo / "src" / ".git").symlink_to(elsewhere)
        r = _run_gate(
            self.repo,
            str(self.repo / "src/docs/reports/product/priorities/hack.md"),
            cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    def test_bypass_inside_linked_worktree_should_be_denied(self):
        (self.repo / "README.md").write_text("x")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-q", "-m", "init"],
            cwd=self.repo, check=True)
        wt = self.repo.parent / "wt"
        subprocess.run(
            ["git", "worktree", "add", "-q", str(wt), "-b", "wtbranch"],
            cwd=self.repo, check=True)
        r = _run_gate(
            wt, str(wt / "src/docs/reports/product/priorities/hack.md"),
            cwd=str(wt))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    def test_bypass_via_planted_git_directory_reaches_exempt_suffixes(self):
        (self.repo / "src" / ".git").mkdir(parents=True)
        r = _run_gate(
            self.repo,
            str(self.repo / "src/docs/specs/approvers.md"),
            cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)

    @unittest.expectedFailure
    def test_bypass_via_nested_git_init_reaches_exempt_priorities_dir(self):
        (self.repo / "src").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=self.repo / "src",
                        check=True)
        r = _run_gate(
            self.repo,
            str(self.repo / "src/docs/reports/product/priorities/hack.md"),
            cwd=str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        _assert_denied_as_deliverable_path(self, r)


if __name__ == "__main__":
    unittest.main()
