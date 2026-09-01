"""Issue #2960: `_workspace_clean_state()` used to ask "is `git status
--porcelain` empty?" -- one build-artifact scrap (or a basename the
harness didn't know about) pinned an entire workspace forever, and a
tree containing only deletions (D) of already-pushed content was treated
identically to a tree with real unpushed work. Fix: the predicate now
asks "what would be lost" -- unpushed commits, stash entries, in-progress
merge/rebase state, staged/unstaged content diffs (M/A/R/C/U), and
untracked files not matched by `.gitignore` (via `git check-ignore`,
not a basename whitelist) all count as "something to lose"; a tree
whose only local changes are deletions is safe only when the commit
holding that content is already pushed.

Decision table (priority order -- first true row wins, matching the
function's short-circuit structure):

  # | live | unreadable | merge/rebase | stash | content-diff | untracked-not-ignored | ahead (unpushed) | D-only | -> reason
  1 |  T   |     -      |      -       |   -   |      -       |          -             |        -         |   -    | live
  2 |  F   |     T      |      -       |   -   |      -       |          -             |        -         |   -    | unknown
  3 |  F   |     F      |      T       |   -   |      -       |          -             |        -         |   -    | dirty (merge)
  4 |  F   |     F      |      F       |   T   |      -       |          -             |        -         |   -    | dirty (stash)
  5 |  F   |     F      |      F       |   F   |      T       |          -             |        -         |   -    | dirty (content)
  6 |  F   |     F      |      F       |   F   |      F       |          T             |        -         |   -    | dirty (untracked)
  7 |  F   |     F      |      F       |   F   |      F       |          F             |        T         |   T    | dirty (unpushed) -- d_only_pushed negative
  8 |  F   |     F      |      F       |   F   |      F       |          F             |        F         |   T    | safe -- d_only_pushed positive
  9 |  F   |     F      |      F       |   F   |      F       |          F             |        F         |   F    | safe (fully clean)

Rows 1-2, and the cross-checkout "unknown" liveness union, are already
covered by tests/test_cross_checkout_prune_liveness.py; this file covers
rows 3-9 plus the legacy stale-remote-tracking fetch/re-check regression
that predates this issue (kept working, not reintroduced).

  python3 -m pytest tests/test_workspace_clean_state_predicate.py -v
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True,
                        text=True)
    assert r.returncode == 0, f"git {args} in {cwd} failed: {r.stderr}"
    return r


def _make_pushed_repo(path: Path) -> Path:
    """A workspace with one committed+pushed file and nothing else -- the
    baseline every test in this file starts from before adding the one
    condition under test."""
    path.mkdir(parents=True)
    _git(["init", "-q"], path)
    _git(["config", "user.email", "test@example.com"], path)
    _git(["config", "user.name", "Test"], path)
    (path / "f.txt").write_text("x\n")
    _git(["add", "f.txt"], path)
    _git(["commit", "-q", "-m", "init"], path)
    remote = path.parent / (path.name + "-remote.git")
    _git(["init", "-q", "--bare", str(remote)], path.parent)
    _git(["remote", "add", "origin", str(remote)], path)
    _git(["push", "-q", "-u", "origin", "HEAD"], path)
    return remote


class WorkspaceCleanStatePredicateTest(unittest.TestCase):
    """Rows 3-9 of the decision table above -- each test isolates exactly
    one condition against the pushed-and-clean baseline."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.root = Path(self._td.name)

    def _clean_state(self, w: Path):
        return spawn._workspace_clean_state(w, live={}, unreadable=None)

    # -- baseline: fully clean and pushed (row 9) --------------------

    def test_fully_clean_pushed_worktree_is_safe(self):
        w = self.root / "clean"
        _make_pushed_repo(w)
        reason, detail = self._clean_state(w)
        self.assertIsNone(reason, detail)

    # -- row 7/8: D-only trees, the issue's headline case ------------

    def test_d_only_pushed_is_safe(self):
        """A worktree whose only local change is an uncommitted deletion
        of a file that's part of an already-pushed commit has nothing to
        lose -- the content survives in the pushed commit."""
        w = self.root / "d-only-pushed"
        _make_pushed_repo(w)
        (w / "f.txt").unlink()
        reason, detail = self._clean_state(w)
        self.assertIsNone(reason, detail)

    def test_d_only_unpushed_commit_is_dirty(self):
        """Same D-only worktree shape, but the commit holding the deleted
        file's content was never pushed -- deleting the workspace would
        lose it. The D-only shape must not shortcut the ahead check."""
        w = self.root / "d-only-unpushed"
        remote = _make_pushed_repo(w)
        (w / "g.txt").write_text("y\n")
        _git(["add", "g.txt"], w)
        _git(["commit", "-q", "-m", "unpushed"], w)  # never pushed
        (w / "f.txt").unlink()
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("미push", detail)

    # -- row 3: in-progress merge/rebase ------------------------------

    def test_in_progress_merge_is_dirty(self):
        w = self.root / "merge-in-progress"
        _make_pushed_repo(w)
        _git(["checkout", "-qb", "side"], w)
        (w / "f.txt").write_text("side\n")
        _git(["commit", "-qam", "side change"], w)
        _git(["checkout", "-q", "master"], w)
        (w / "f.txt").write_text("main\n")
        _git(["commit", "-qam", "main change"], w)
        subprocess.run(["git", "-C", str(w), "merge", "side"],
                       capture_output=True, text=True)  # expected conflict
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("merge/rebase", detail)

    # -- row 4: stash entries -----------------------------------------

    def test_stash_entry_is_dirty(self):
        w = self.root / "stashed"
        _make_pushed_repo(w)
        (w / "f.txt").write_text("changed\n")
        _git(["stash", "push", "-q"], w)
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("stash", detail)

    # -- row 5: staged/unstaged content diffs (M/A/R) ------------------

    def test_unstaged_modification_is_dirty(self):
        w = self.root / "modified-unstaged"
        _make_pushed_repo(w)
        (w / "f.txt").write_text("changed\n")
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("내용 변경", detail)

    def test_staged_addition_is_dirty(self):
        w = self.root / "staged-add"
        _make_pushed_repo(w)
        (w / "new.txt").write_text("new\n")
        _git(["add", "new.txt"], w)
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("내용 변경", detail)

    def test_rename_is_dirty(self):
        w = self.root / "renamed"
        _make_pushed_repo(w)
        _git(["mv", "f.txt", "renamed.txt"], w)
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("내용 변경", detail)

    # -- row 6: untracked files not matched by gitignore ---------------

    def test_untracked_file_not_ignored_is_dirty(self):
        w = self.root / "untracked"
        _make_pushed_repo(w)
        (w / "scratch.txt").write_text("scratch\n")
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("미추적", detail)

    def test_untracked_file_matched_by_gitignore_is_safe(self):
        """The replacement for the basename whitelist: a repo's own
        `.gitignore` is authoritative, not a hardcoded name list -- an
        untracked file this workspace's `.gitignore` excludes has
        nothing to lose."""
        w = self.root / "gitignored"
        _make_pushed_repo(w)
        (w / ".gitignore").write_text("*.scratch\n")
        _git(["add", ".gitignore"], w)
        _git(["commit", "-q", "-m", "add gitignore"], w)
        _git(["push", "-q"], w)
        (w / "build.scratch").write_text("noise\n")
        reason, detail = self._clean_state(w)
        self.assertIsNone(reason, detail)

    def test_untracked_file_not_on_old_basename_whitelist_is_dirty(self):
        """Regression guard for the issue's must-not: a file that used to
        slip through the removed `_HARNESS_NOISE_BASENAMES` whitelist
        (e.g. `__pycache__`) is dirty here unless THIS repo's own
        `.gitignore` says otherwise -- classification is check-ignore
        driven, not name driven."""
        w = self.root / "old-whitelist-name"
        _make_pushed_repo(w)
        pycache = w / "__pycache__"
        pycache.mkdir()
        (pycache / "f.cpython-310.pyc").write_bytes(b"\x00")
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("미추적", detail)

    # -- ahead (unpushed commits) on an otherwise clean tree -----------

    def test_unpushed_commit_on_clean_tree_is_dirty(self):
        w = self.root / "ahead"
        _make_pushed_repo(w)
        (w / "g.txt").write_text("y\n")
        _git(["add", "g.txt"], w)
        _git(["commit", "-q", "-m", "unpushed"], w)
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("미push", detail)

    def test_stale_remote_tracking_ref_is_refreshed_by_fetch(self):
        """Pre-existing legacy behavior (kept, not reintroduced by this
        fix, accessibility-rulebook issue-19): a workspace's local
        remote-tracking knowledge can be stale -- the exact commit it
        looks "ahead" of already exists on the remote under a ref this
        workspace hasn't learned about yet. On an otherwise clean tree,
        the predicate's one fetch-and-recheck must resolve `ahead` back
        to empty rather than leaving the workspace stuck dirty forever."""
        w = self.root / "stale-tracking"
        _make_pushed_repo(w)
        (w / "h.txt").write_text("z\n")
        _git(["add", "h.txt"], w)
        _git(["commit", "-q", "-m", "not pushed under this branch name"], w)
        commit = _git(["rev-parse", "HEAD"], w).stdout.strip()
        # Push the exact same commit to the remote under a different
        # branch name, then discard the local knowledge of that ref --
        # simulates a local remote-tracking ref that is stale relative
        # to what the remote actually has.
        _git(["push", "-q", "origin", f"HEAD:refs/heads/shadow"], w)
        _git(["update-ref", "-d", "refs/remotes/origin/shadow"], w)
        ahead_before = _git(
            ["log", "--branches", "--not", "--remotes", "--oneline"], w
        ).stdout.strip()
        self.assertIn(commit[:7], ahead_before,
                       "test setup must reproduce a falsely-ahead commit")
        reason, detail = self._clean_state(w)
        self.assertIsNone(reason, detail)


if __name__ == "__main__":
    unittest.main()
