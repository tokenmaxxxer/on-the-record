"""이슈 #2215: harness-decided 워크스페이스 체크포인트 + dirty-tree 헬스
신호. `checkpoint.py`(순수 함수)를 실제 git 레포 fixture 로 구동하고,
`watchdog.diagnose_health()`/`roster.roster_remove()` 와의 통합을 검증한다."""
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import checkpoint  # noqa: E402
import spawn  # noqa: E402
import watchdog  # noqa: E402


def _run(args, cwd, env=None, check=True):
    return subprocess.run(["git", "-C", str(cwd), *args], cwd=cwd,
                           capture_output=True, text=True, env=env, check=check)


def _init_git_repo(path: Path, branch: str = "issue-1/implementation") -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", branch], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "tracked.txt").write_text("original\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


class TestCheckpointWorkspaceEmptyState(unittest.TestCase):
    """수용 기준 (empty state): 깨끗한 트리 + 아직 edit 없음 — dirty_files=0,
    체크포인트 없음, ref 생성 안 됨."""

    def test_clean_tree_no_ref_created(self):
        with self._tmp() as td:
            work = Path(td) / "work"
            _init_git_repo(work)

            result = checkpoint.checkpoint_workspace(str(work))
            self.assertEqual(result, {"ref": None, "commit": None, "dirty_files": 0})

            health = checkpoint.checkpoint_health(str(work))
            self.assertEqual(health, {"dirty_files": 0, "minutes_since_checkpoint": None})

            show = _run(["show-ref"], work, check=False)
            self.assertNotIn("refs/checkpoints", show.stdout)

    def _tmp(self):
        import tempfile
        return tempfile.TemporaryDirectory()


class TestCheckpointWorkspaceCapture(unittest.TestCase):
    """수용 기준: 추적 파일 수정 + 추적 안 된 새 파일 모두 캡처, HEAD/브랜치/
    인덱스는 그대로."""

    def setUp(self):
        import tempfile
        self._td = tempfile.TemporaryDirectory()
        self.work = Path(self._td.name) / "work"
        _init_git_repo(self.work)

    def tearDown(self):
        self._td.cleanup()

    def test_captures_tracked_and_untracked_leaves_head_branch_index_unchanged(self):
        (self.work / "tracked.txt").write_text("modified\n")
        (self.work / "untracked.txt").write_text("new file\n")

        before_head = _run(["rev-parse", "HEAD"], self.work).stdout.strip()
        before_branch = _run(["rev-parse", "--abbrev-ref", "HEAD"], self.work).stdout.strip()
        before_status = _run(["status", "--porcelain"], self.work).stdout

        result = checkpoint.checkpoint_workspace(str(self.work))

        after_head = _run(["rev-parse", "HEAD"], self.work).stdout.strip()
        after_branch = _run(["rev-parse", "--abbrev-ref", "HEAD"], self.work).stdout.strip()
        after_status = _run(["status", "--porcelain"], self.work).stdout

        self.assertEqual(result["dirty_files"], 2)
        self.assertIsNotNone(result["commit"])
        self.assertEqual(result["ref"], "refs/checkpoints/issue-1/implementation")
        self.assertEqual(before_head, after_head, "checkpoint must not move HEAD")
        self.assertEqual(before_branch, after_branch, "checkpoint must not change branch")
        self.assertEqual(before_status, after_status, "checkpoint must not touch worktree/index")

        show_tracked = _run(["show", f"{result['commit']}:tracked.txt"], self.work)
        show_untracked = _run(["show", f"{result['commit']}:untracked.txt"], self.work)
        self.assertEqual(show_tracked.stdout, "modified\n")
        self.assertEqual(show_untracked.stdout, "new file\n")

    def test_untracked_only_still_captured(self):
        (self.work / "untracked.txt").write_text("new file\n")
        result = checkpoint.checkpoint_workspace(str(self.work))
        self.assertEqual(result["dirty_files"], 1)
        self.assertIsNotNone(result["commit"])
        show = _run(["show", f"{result['commit']}:untracked.txt"], self.work)
        self.assertEqual(show.stdout, "new file\n")


class TestKillMidEditRecovery(unittest.TestCase):
    """수용 기준: mid-edit kill 이후에도 checkpoint ref 에서 복구 가능함을
    실제 git 명령/출력으로 보인다."""

    def test_recovery_after_destructive_loss(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            _init_git_repo(work)
            (work / "tracked.txt").write_text("in-flight edit\n")
            (work / "untracked.txt").write_text("in-flight new file\n")

            ckpt = checkpoint.checkpoint_workspace(str(work))
            self.assertIsNotNone(ckpt["commit"])

            # Simulate the session being killed and its uncommitted work lost.
            _run(["checkout", "--", "tracked.txt"], work)
            _run(["clean", "-fd"], work)
            self.assertEqual(
                (work / "tracked.txt").read_text(), "original\n")
            self.assertFalse((work / "untracked.txt").exists())

            # Recovery: restore the tree from the checkpoint ref.
            recover = _run(["checkout", ckpt["ref"], "--", "."], work)
            self.assertEqual(recover.returncode, 0)

            self.assertEqual(
                (work / "tracked.txt").read_text(), "in-flight edit\n")
            self.assertEqual(
                (work / "untracked.txt").read_text(), "in-flight new file\n")


class TestCleanupCheckpointRef(unittest.TestCase):
    def test_cleanup_deletes_ref_without_touching_head(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            _init_git_repo(work)
            (work / "tracked.txt").write_text("dirty\n")
            ckpt = checkpoint.checkpoint_workspace(str(work))
            self.assertIsNotNone(ckpt["ref"])

            before_head = _run(["rev-parse", "HEAD"], work).stdout.strip()
            ok = checkpoint.cleanup_checkpoint_ref(str(work))
            after_head = _run(["rev-parse", "HEAD"], work).stdout.strip()

            self.assertTrue(ok)
            self.assertEqual(before_head, after_head)
            show = _run(["show-ref", "--verify", "--quiet", ckpt["ref"]], work, check=False)
            self.assertNotEqual(show.returncode, 0)

    def test_cleanup_on_clean_tree_is_noop(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            _init_git_repo(work)
            self.assertTrue(checkpoint.cleanup_checkpoint_ref(str(work)))

    def test_roster_remove_cleans_up_checkpoint_ref(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            _init_git_repo(work)
            (work / "tracked.txt").write_text("dirty\n")
            ckpt = checkpoint.checkpoint_workspace(str(work))
            self.assertIsNotNone(ckpt["ref"])

            roster_path = Path(td) / "active.json"
            roster_path.write_text('{}')
            import json
            roster_path.write_text(json.dumps(
                {"1/implementation/k": {"work": str(work), "pid": 0}}))

            old_roster = spawn.ROSTER
            spawn.ROSTER = roster_path
            try:
                spawn.roster_remove("1/implementation/k")
            finally:
                spawn.ROSTER = old_roster

            show = _run(["show-ref", "--verify", "--quiet", ckpt["ref"]], work, check=False)
            self.assertNotEqual(show.returncode, 0)
            self.assertNotIn("1/implementation/k", json.loads(roster_path.read_text()))


class TestDiagnoseHealthSurfacesCheckpointFields(unittest.TestCase):
    """수용 기준: 라이브 세션의 헬스 라인이 dirty-file 개수와
    minutes-since-checkpoint 를 보고한다."""

    def test_live_entry_reports_dirty_and_minutes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            _init_git_repo(work)
            (work / "tracked.txt").write_text("dirty\n")
            (work / "untracked.txt").write_text("also dirty\n")
            checkpoint.checkpoint_workspace(str(work))
            (work / "tracked.txt").write_text("more dirty after checkpoint\n")

            log = Path(td) / "s.log"
            log.write_text('{"type":"text","timestamp":"2026-08-24T00:00:00Z"}\n')
            entry = {"log": str(log), "work": str(work), "pid": os.getpid(),
                     "ts": int(time.time())}

            health = watchdog.diagnose_health("k", entry, anomalies=[])

            self.assertEqual(health["dirty_files"], 2)
            self.assertIsNotNone(health["minutes_since_checkpoint"])
            self.assertGreaterEqual(health["minutes_since_checkpoint"], 0)

    def test_clean_live_entry_reports_zero_and_none(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            _init_git_repo(work)
            log = Path(td) / "s.log"
            log.write_text('{"type":"text","timestamp":"2026-08-24T00:00:00Z"}\n')
            entry = {"log": str(log), "work": str(work), "pid": os.getpid(),
                     "ts": int(time.time())}

            health = watchdog.diagnose_health("k", entry, anomalies=[])

            self.assertEqual(health["dirty_files"], 0)
            self.assertIsNone(health["minutes_since_checkpoint"])


if __name__ == "__main__":
    unittest.main()
