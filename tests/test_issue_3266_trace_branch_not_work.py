"""The harness's own trace branch made every workspace look unreclaimable.

`consult.py` writes consult traces onto a local `otr-consult-trace` branch
and never pushes it, so `git log --branches --not --remotes` always found a
commit that exists nowhere else. Measured on this machine: 108 workspaces
reported unpreserved work, and 95 were held by that branch alone.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)


class TheTraceBranchIsNotUnpreservedWorkTest(unittest.TestCase):
    def setUp(self):
        self.remote = Path(tempfile.mkdtemp()) / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(self.remote)],
                       check=True)
        self.w = Path(tempfile.mkdtemp()) / "w"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.w)],
                       check=True)
        for k, v in (("user.email", "t@example.invalid"), ("user.name", "t")):
            _git(self.w, "config", k, v)
        (self.w / "a.txt").write_text("one\n", encoding="utf-8")
        _git(self.w, "add", "a.txt")
        _git(self.w, "commit", "-qm", "first")
        _git(self.w, "push", "-q", "origin", "HEAD:refs/heads/main")
        _git(self.w, "branch", "--set-upstream-to=origin/main")

    def _ahead(self):
        return spawn._workspace_clean_state(self.w, {})

    def _add_trace_commit(self):
        _git(self.w, "checkout", "-q", "-b", "otr-consult-trace")
        (self.w / "trace.md").write_text("consult\n", encoding="utf-8")
        _git(self.w, "add", "trace.md")
        _git(self.w, "commit", "-qm", "consult-trace (ok)")
        _git(self.w, "checkout", "-q", "-")

    def test_a_pushed_workspace_with_only_a_trace_commit_is_reclaimable(self):
        self._add_trace_commit()
        state, detail = self._ahead()
        self.assertIsNone(state, detail)

    def test_a_real_unpushed_branch_still_blocks_reclaim(self):
        self._add_trace_commit()
        _git(self.w, "checkout", "-q", "-b", "issue-9/real")
        (self.w / "b.txt").write_text("work\n", encoding="utf-8")
        _git(self.w, "add", "b.txt")
        _git(self.w, "commit", "-qm", "real work nobody has")
        state, detail = self._ahead()
        self.assertEqual(state, "dirty")
        self.assertIn("미push 커밋", detail)

    def test_the_exclude_flag_precedes_branches(self):
        # `--exclude` applies to the ref globs that FOLLOW it; placing it
        # after `--branches` excludes nothing, which is how this defect
        # first measured as 0 workspaces instead of 95.
        src = (ROOT / "lifecycle.py").read_text(encoding="utf-8")
        for line in src.splitlines():
            if "--branches" in line and "--exclude" in line:
                self.assertLess(line.index("--exclude"),
                                line.index("--branches"), line)


if __name__ == "__main__":
    unittest.main()
