"""issue #2749: `self-update.sh` used to run `git pull --ff-only`
unconditionally on every `SessionStart` firing -- the working-tree merge
that actually swaps the code hooks execute from, at a moment nobody
decided (reflog evidence: repeated fast-forwards the orchestrator never
issued, while sessions were running -- see the issue body and
docs/issue-2670/reports/.../implementation.md's final comment, "the
hazard here was the pull, not the merge"). The fix: this hook now only
`git fetch`s (refs/objects only, never the working tree) and records
whether the checkout is behind -- it never merges. Advancing the working
tree moved to the session-count-gated `spawn.py self-update`
(test/test_self_update_pull_gate.py).

This test runs the real shipped hook (`bash
on-the-record/hooks/self-update.sh`) against real git checkouts and
asserts the working tree never moves, no matter what state the remote is
in, while `.pull-check` still records the true state loudly in every
case (issue #910 finding #4's bar).

Run: python3 -m pytest test/test_self_update_working_tree_untouched.py -q
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "self-update.sh"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args],
                           capture_output=True, text=True, check=True)


def _run_hook(checkout: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(["bash", str(HOOK_PATH)], input="{}",
                           capture_output=True, text=True, env=env, timeout=30)


class SelfUpdateWorkingTreeUntouchedTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        origin = base / "origin.git"
        origin.mkdir()
        _git(origin, "init", "--bare", "-q")

        src = base / "seed"
        src.mkdir()
        _git(src, "init", "-q")
        _git(src, "config", "user.email", "t@example.com")
        _git(src, "config", "user.name", "t")
        (src / "spawn.py").write_text("# seed\n")
        _git(src, "add", "spawn.py")
        _git(src, "commit", "-q", "-m", "seed")
        _git(src, "branch", "-M", "main")
        _git(src, "remote", "add", "origin", str(origin))
        _git(src, "push", "-q", "-u", "origin", "main")

        self.checkout = base / "checkout"
        _git(base, "clone", "-q", str(origin), str(self.checkout))
        _git(self.checkout, "checkout", "-q", "-B", "main", "origin/main")
        _git(self.checkout, "branch", "-q", "--set-upstream-to=origin/main", "main")

        self.origin = origin
        self.src = src

    def tearDown(self):
        self._tmp.cleanup()

    def _head(self) -> str:
        return _git(self.checkout, "rev-parse", "HEAD").stdout.strip()

    def test_up_to_date_records_ok_and_does_not_touch_tree(self):
        before = self._head()

        result = _run_hook(self.checkout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._head(), before)
        self.assertEqual((self.checkout / ".pull-check").read_text().strip(), "pull=ok")

    def test_behind_origin_never_merges_and_records_deferred(self):
        (self.src / "new.txt").write_text("x\n")
        _git(self.src, "add", "new.txt")
        _git(self.src, "commit", "-q", "-m", "advance")
        _git(self.src, "push", "-q", "origin", "main")
        before = self._head()

        result = _run_hook(self.checkout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._head(), before,
                          "self-update.sh must never merge into the working tree")
        self.assertFalse((self.checkout / "new.txt").exists(),
                          "the new origin commit's file must not appear in the "
                          "working tree -- that would mean a merge ran")
        marker = (self.checkout / ".pull-check").read_text().strip()
        self.assertEqual(marker, "pull=deferred:1-behind-origin")

    def test_unreachable_origin_records_failed_fetch_not_silence(self):
        _git(self.checkout, "remote", "set-url", "origin",
             "file:///nonexistent/does/not/exist")
        before = self._head()

        result = _run_hook(self.checkout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._head(), before)
        marker = (self.checkout / ".pull-check").read_text().strip()
        self.assertTrue(marker.startswith("pull=failed:fetch:"), marker)


if __name__ == "__main__":
    unittest.main()
