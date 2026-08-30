"""issue #2795: DEAD-UNRECOVERED-COMMITS fired for a session whose commits
were already on the remote -- the old `_session_commit_count()` only ever
compared local `before_head`/`after_head` HEAD landmarks and never asked the
remote at all, so "no PR yet" was silently read as "not pushed". This
reproduces the exact false positive (remote head == local head, still
alarmed) against the real `_unrecovered_commit_count()` / `diagnose_health()`
entry points and checks the fix along both required directions: the false
positive is now silent, and a genuinely-unpushed commit is still reported --
plus the third state (remote state undeterminable) that must not collapse
into either.

Workspace/branch naming deliberately does NOT match (`work-dir` vs
`issue-9001/demo`), reproducing this repo's real convention
(`issue_workspace()` names the directory `<repo>-issue-<n>-<skill>`, dashes,
while the branch is `issue-<n>/<skill>`, slash) -- a naive `Path(work).name`
branch guess would query the wrong ref and reintroduce this same false
positive by a different route.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import board  # noqa: E402
import spawn  # noqa: E402
import watchdog  # noqa: E402

board._sp = spawn
watchdog._sp = spawn


def _git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a],
                           capture_output=True, text=True, check=True)


class UnrecoveredCommitCountTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        self.remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        # dash-joined dir name vs slash branch name, matching real convention
        self.work = self.tmp / "on-the-record-issue-9001-demo"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.work)], check=True)
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        (self.work / "a.txt").write_text("1")
        _git(self.work, "add", "a.txt")
        _git(self.work, "commit", "-q", "-m", "c1")
        self.branch = "issue-9001/demo"
        _git(self.work, "branch", "-m", self.branch)
        _git(self.work, "push", "-q", "-u", "origin", self.branch)
        self.before_head = _git(self.work, "rev-parse", "HEAD").stdout.strip()

    def _commit(self, name):
        (self.work / name).write_text(name)
        _git(self.work, "add", name)
        _git(self.work, "commit", "-q", "-m", name)
        return _git(self.work, "rev-parse", "HEAD").stdout.strip()

    def test_false_positive_pushed_commits_report_zero(self):
        self._commit("b.txt")
        after_head = self._commit("c.txt")
        _git(self.work, "push", "-q", "origin", self.branch)
        result = board._unrecovered_commit_count(
            str(self.work), self.before_head, after_head, self.branch)
        self.assertEqual(result, 0)

    def test_genuinely_unpushed_commit_still_counted(self):
        pushed_head = self._commit("b.txt")
        _git(self.work, "push", "-q", "origin", self.branch)
        unpushed_head = self._commit("c-unpushed.txt")
        result = board._unrecovered_commit_count(
            str(self.work), pushed_head, unpushed_head, self.branch)
        self.assertEqual(result, 1)

    def test_no_upstream_branch_counts_as_fully_unrecovered(self):
        _git(self.work, "checkout", "-q", "-b", "issue-9002/no-upstream")
        new_head = self._commit("d.txt")
        result = board._unrecovered_commit_count(
            str(self.work), self.before_head, new_head, "issue-9002/no-upstream")
        self.assertEqual(result, 1)

    def test_unreachable_remote_reports_unknown_not_healthy_or_stranded(self):
        pushed_head = self._commit("b.txt")
        _git(self.work, "push", "-q", "origin", self.branch)
        unpushed_head = self._commit("c-unpushed.txt")
        _git(self.work, "remote", "set-url", "origin", "/nonexistent/path.git")
        result = board._unrecovered_commit_count(
            str(self.work), pushed_head, unpushed_head, self.branch)
        self.assertEqual(result, board.UNPUSHED_STATUS_UNKNOWN)
        self.assertNotEqual(result, 0)
        self.assertNotIsInstance(result, int)

    def _crashed_entry(self, before_head):
        pid = 999999999
        events_path = spawn._events_path(str(self.work))
        events_path.write_text(
            '{"ts": 1, "type": "session-start", "detail": {"pid": %d}}\n' % pid)
        return {"pid": pid, "work": str(self.work), "before_head": before_head,
                "log": None, "issue": 9001, "skill": "demo"}

    def test_diagnose_health_silent_after_successful_push(self):
        self._commit("b.txt")
        after_head = self._commit("c.txt")
        _git(self.work, "push", "-q", "origin", self.branch)
        entry = self._crashed_entry(self.before_head)
        commit_count = board._unrecovered_commit_count(
            str(self.work), self.before_head, after_head,
            board._current_branch(self.work))
        health = watchdog.diagnose_health(self.branch, entry, root=self.work,
                                           commit_count=commit_count, pr_index={})
        self.assertEqual(health["state"], "DEAD-ERRORED")
        self.assertNotEqual(health["state"], "DEAD-UNRECOVERED-COMMITS")

    def test_diagnose_health_still_reports_genuine_strand(self):
        pushed_head = self._commit("b.txt")
        _git(self.work, "push", "-q", "origin", self.branch)
        unpushed_head = self._commit("c-unpushed.txt")
        entry = self._crashed_entry(pushed_head)
        commit_count = board._unrecovered_commit_count(
            str(self.work), pushed_head, unpushed_head,
            board._current_branch(self.work))
        health = watchdog.diagnose_health(self.branch, entry, root=self.work,
                                           commit_count=commit_count, pr_index={})
        self.assertEqual(health["state"], "DEAD-UNRECOVERED-COMMITS")
        self.assertIn("1개", health["detail"])

    def test_diagnose_health_unknown_remote_is_its_own_state(self):
        pushed_head = self._commit("b.txt")
        _git(self.work, "push", "-q", "origin", self.branch)
        unpushed_head = self._commit("c-unpushed.txt")
        entry = self._crashed_entry(pushed_head)
        health = watchdog.diagnose_health(
            self.branch, entry, root=self.work,
            commit_count=board.UNPUSHED_STATUS_UNKNOWN, pr_index={})
        self.assertEqual(health["state"], "DEAD-REMOTE-STATE-UNKNOWN")
        self.assertNotIn(health["state"], ("DEAD-ERRORED", "DEAD-UNRECOVERED-COMMITS"))


if __name__ == "__main__":
    unittest.main()
