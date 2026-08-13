#!/usr/bin/env python3
"""이슈 #1124 — `spawn.py clean`/`reconcile --unreported` 안전성 회귀.

  python3 gates/test_clean_reconcile_safety.py
"""
from __future__ import annotations
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


def _bare_workspace(wb: Path, name: str) -> Path:
    """미커밋 변경도, unpushed 커밋도 없는(=삭제 대상) 워크스페이스."""
    w = wb / name
    w.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=w, check=True)
    return w


def _pushed_workspace_with_bytes(wb: Path, origin_dir: Path, name: str,
                                  filename: str, size: int) -> Path:
    """커밋한 데이터가 fake origin 에 push 까지 돼서, `git log --branches
    --not --remotes` 가 비어있는(=미push 커밋 없음) clean 워크스페이스를
    만든다 — auto_sweep 의 크기 bound 테스트에 쓸 파일 크기를 통제하려면
    `_bare_workspace()` 의 무커밋 상태로는(아무 파일이나 있으면 git
    status 가 dirty 를 잡는다) 안 된다."""
    subprocess.run(["git", "init", "-q", "--bare", str(origin_dir)], check=True)
    w = wb / name
    w.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=w, check=True)
    subprocess.run(["git", "-C", str(w), "remote", "add", "origin", str(origin_dir)],
                    check=True)
    (w / filename).write_bytes(b"x" * size)
    subprocess.run(["git", "-C", str(w), "add", filename], check=True)
    subprocess.run(["git", "-C", str(w), "-c", "user.email=t@t.test",
                    "-c", "user.name=t", "commit", "-q", "-m", "data"], check=True)
    subprocess.run(["git", "-C", str(w), "push", "-q", "origin", "main"], check=True)
    return w


class CleanReconcileSafetyTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self.state_root = self.tmp / "state"
        self.wb = self.tmp / "work"
        self.wb.mkdir()

        self._orig_root = spawn.ROOT
        self._orig_roster = spawn.ROSTER
        self._orig_idx = spawn.WORKSPACE_INDEX
        spawn.ROOT = self.root
        spawn.ROSTER = self.state_root / "active.json"
        spawn.WORKSPACE_INDEX = self.state_root / "workspaces.json"

    def tearDown(self):
        spawn.ROOT = self._orig_root
        spawn.ROSTER = self._orig_roster
        spawn.WORKSPACE_INDEX = self._orig_idx
        self._tmp.cleanup()

    def _write_ledger(self, entries: list[dict]) -> None:
        d = self.root / "runs"
        d.mkdir(parents=True, exist_ok=True)
        with (d / "ledger.jsonl").open("w", encoding="utf-8") as fh:
            for e in entries:
                fh.write(json.dumps(e) + "\n")

    # (a) reconcile: 삭제된(존재하지 않는) 워크스페이스는 크래시가 아니라 skip.
    def test_reconcile_unreported_skips_missing_workspace(self):
        missing_work = str(self.tmp / "gone-workspace")
        spawn.WORKSPACE_INDEX.parent.mkdir(parents=True, exist_ok=True)
        spawn.WORKSPACE_INDEX.write_text(json.dumps({
            "on-the-record/issue-1110/implementation": {
                "work": missing_work, "log": missing_work + ".session.log",
            },
        }))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            total = spawn._roster_reconcile_unreported()
        self.assertEqual(total, 0)
        self.assertIn("건너뜀", buf.getvalue())

    # (b) clean: refused 등 non-landed outcome 의 로그는 archive, 워크스페이스는 지운다.
    def test_clean_archives_non_landed_log(self):
        w = _bare_workspace(self.wb, "on-the-record-issue-99-refused")
        log = self.wb / (w.name + ".session.20260813.1.log")
        log.write_text("refusal reason\n")
        self._write_ledger([{"log": str(log), "outcome": "refused"}])

        rc = spawn.roster_clean(self.wb, None)
        self.assertEqual(rc, 0)
        self.assertFalse(w.exists())
        self.assertFalse(log.exists())
        archived = self.wb / ".archived-logs" / log.name
        self.assertTrue(archived.exists())
        self.assertEqual(archived.read_text(), "refusal reason\n")

    # (c) clean: landed(progressed) outcome 은 오늘처럼 로그까지 삭제.
    def test_clean_deletes_landed_log(self):
        w = _bare_workspace(self.wb, "on-the-record-issue-100-landed")
        log = self.wb / (w.name + ".session.20260813.2.log")
        log.write_text("landed session\n")
        self._write_ledger([{"log": str(log), "outcome": "progressed"}])

        rc = spawn.roster_clean(self.wb, None)
        self.assertEqual(rc, 0)
        self.assertFalse(w.exists())
        self.assertFalse(log.exists())
        self.assertFalse((self.wb / ".archived-logs" / log.name).exists())

    # (d) 빈 상태: ledger.jsonl 없음, work dir 비어있음, roster/workspace 인덱스 없음.
    def test_empty_state_noops_cleanly(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = spawn.roster_clean(self.wb, None)
            total = spawn._roster_reconcile_unreported()
        self.assertEqual(rc, 0)
        self.assertEqual(total, 0)
        self.assertEqual(spawn._ledger_log_outcomes(), {})
        # 빈 상태에서 auto_sweep 도 크래시 없이 no-op.
        result = spawn.auto_sweep(self.wb, max_age_days=14, max_bytes=5 * 1024**3)
        self.assertEqual(result, {"removed": 0, "failed": 0})


# 이슈 #1179 — 자동(스폰-타임) 스윕: 나이/크기 bound, 살아있는/dirty 워크스페이스 예외.
class AutoSweepTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self.state_root = self.tmp / "state"
        self.wb = self.tmp / "work"
        self.wb.mkdir()

        self._orig_root = spawn.ROOT
        self._orig_roster = spawn.ROSTER
        self._orig_idx = spawn.WORKSPACE_INDEX
        spawn.ROOT = self.root
        spawn.ROSTER = self.state_root / "active.json"
        spawn.WORKSPACE_INDEX = self.state_root / "workspaces.json"

    def tearDown(self):
        spawn.ROOT = self._orig_root
        spawn.ROSTER = self._orig_roster
        spawn.WORKSPACE_INDEX = self._orig_idx
        self._tmp.cleanup()

    def _set_mtime(self, w: Path, days_ago: float, now: float) -> None:
        ts = now - days_ago * 86400
        os.utime(w, (ts, ts))

    def test_age_bound_reaps_older_than_max_age(self):
        now = 2_000_000_000.0
        old = _bare_workspace(self.wb, "on-the-record-issue-1-implementation")
        self._set_mtime(old, days_ago=30, now=now)
        fresh = _bare_workspace(self.wb, "on-the-record-issue-2-implementation")
        self._set_mtime(fresh, days_ago=1, now=now)

        result = spawn.auto_sweep(self.wb, max_age_days=14,
                                   max_bytes=5 * 1024**3, now=now)
        self.assertEqual(result["removed"], 1)
        self.assertFalse(old.exists())
        self.assertTrue(fresh.exists())

    def test_size_bound_reaps_oldest_first(self):
        now = 2_000_000_000.0
        w1 = _pushed_workspace_with_bytes(
            self.wb, self.tmp / "origin1", "on-the-record-issue-1-implementation",
            "big.bin", 2000)
        self._set_mtime(w1, days_ago=3, now=now)
        w2 = _pushed_workspace_with_bytes(
            self.wb, self.tmp / "origin2", "on-the-record-issue-2-implementation",
            "big.bin", 2000)
        self._set_mtime(w2, days_ago=2, now=now)
        w3 = _pushed_workspace_with_bytes(
            self.wb, self.tmp / "origin3", "on-the-record-issue-3-implementation",
            "big.bin", 2000)
        self._set_mtime(w3, days_ago=1, now=now)

        one_size = spawn._dir_size_bytes(w1)
        # bound 는 셋 다 합친 것보다 작지만 둘은 들어갈 만큼 — 가장 오래된
        # w1 만 지워도 나머지 둘은 bound 안에 들어간다.
        bound = int(one_size * 2.5)
        result = spawn.auto_sweep(self.wb, max_age_days=365,
                                   max_bytes=bound, now=now)
        self.assertEqual(result["removed"], 1)
        self.assertFalse(w1.exists())
        self.assertTrue(w2.exists())
        self.assertTrue(w3.exists())

    def test_live_session_exempt_from_auto_sweep(self):
        now = 2_000_000_000.0
        w = _bare_workspace(self.wb, "on-the-record-issue-1-implementation")
        self._set_mtime(w, days_ago=30, now=now)
        spawn.ROSTER.parent.mkdir(parents=True, exist_ok=True)
        spawn.ROSTER.write_text(json.dumps({
            "on-the-record/issue-1/implementation": {
                "work": str(w), "issue": 1, "role": "implementation",
                "pid": os.getpid(),
            },
        }))

        result = spawn.auto_sweep(self.wb, max_age_days=14,
                                   max_bytes=5 * 1024**3, now=now)
        self.assertEqual(result["removed"], 0)
        self.assertTrue(w.exists())

    def test_dirty_workspace_exempt_from_auto_sweep(self):
        now = 2_000_000_000.0
        w = _bare_workspace(self.wb, "on-the-record-issue-1-implementation")
        (w / "uncommitted.txt").write_text("wip\n")
        self._set_mtime(w, days_ago=30, now=now)

        result = spawn.auto_sweep(self.wb, max_age_days=14,
                                   max_bytes=5 * 1024**3, now=now)
        self.assertEqual(result["removed"], 0)
        self.assertTrue(w.exists())

    # 이슈 #1179 재오픈: 훅이 심는 자체 부기 마커(untracked)만 있는
    # 레거시 워크스페이스는 "미보존 작업"이 아니다 — 지워도 된다.
    def test_harness_marker_only_workspace_is_swept(self):
        now = 2_000_000_000.0
        w = _bare_workspace(self.wb, "on-the-record-issue-1-implementation")
        (w / ".warrant-hunt.count").write_text("3\n")
        (w / ".pull-check").write_text("pull=ok\n")
        self._set_mtime(w, days_ago=30, now=now)

        result = spawn.auto_sweep(self.wb, max_age_days=14,
                                   max_bytes=5 * 1024**3, now=now)
        self.assertEqual(result["removed"], 1)
        self.assertFalse(w.exists())

    # 진짜 미보존 파일과 harness 마커가 같이 있으면 여전히 dirty.
    def test_real_untracked_file_still_exempt_alongside_marker(self):
        now = 2_000_000_000.0
        w = _bare_workspace(self.wb, "on-the-record-issue-1-implementation")
        (w / ".warrant-hunt.count").write_text("3\n")
        (w / "real-work.txt").write_text("wip\n")
        self._set_mtime(w, days_ago=30, now=now)

        result = spawn.auto_sweep(self.wb, max_age_days=14,
                                   max_bytes=5 * 1024**3, now=now)
        self.assertEqual(result["removed"], 0)
        self.assertTrue(w.exists())

    # 레거시 워크스페이스는 생성 뒤 다시 fetch 된 적이 없어, 브랜치가
    # origin 에 이미 머지됐어도 local remote-tracking ref 가 그걸 몰라
    # "ahead" 로 영원히 오판된다 — auto_sweep 이 fetch 로 갱신하고
    # 재판정해야 지워진다.
    def test_stale_remote_tracking_ref_refreshed_before_ahead_check(self):
        now = 2_000_000_000.0
        origin_dir = self.tmp / "origin4"
        subprocess.run(["git", "init", "-q", "-b", "main", "--bare",
                        str(origin_dir)], check=True)
        w = self.wb / "on-the-record-issue-1-implementation"
        w.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", "-b", "topic"], cwd=w, check=True)
        subprocess.run(["git", "-C", str(w), "remote", "add", "origin",
                        str(origin_dir)], check=True)
        (w / "f.txt").write_text("x\n")
        subprocess.run(["git", "-C", str(w), "add", "f.txt"], check=True)
        subprocess.run(["git", "-C", str(w), "-c", "user.email=t@t.test",
                        "-c", "user.name=t", "commit", "-q", "-m", "work"],
                       check=True)
        # 브랜치를 push 하지 않고, 대신 origin 쪽에서 같은 커밋이 main 으로
        # 들어온 상태를 흉내낸다(스쿼시 머지 뒤 이 워크스페이스가 한번도
        # fetch 되지 않은 상황) — origin bare repo 의 main 을 이 워크스페이스의
        # HEAD 로 직접 옮긴다.
        subprocess.run(["git", "-C", str(w), "push", "-q", "origin",
                        "topic:main"], check=True)
        # push 는 origin 에 객체를 올리지만 로컬 remote-tracking ref
        # (refs/remotes/origin/main) 는 갱신 안 한다(다른 브랜치로 push
        # 했으므로) — 스쿼시 머지 뒤 한번도 fetch 되지 않은 레거시
        # 워크스페이스를 흉내낸다. fetch 전에는 "ahead" 로 보인다.
        self._set_mtime(w, days_ago=30, now=now)

        result = spawn.auto_sweep(self.wb, max_age_days=14,
                                   max_bytes=5 * 1024**3, now=now)
        self.assertEqual(result["removed"], 1)
        self.assertFalse(w.exists())


if __name__ == "__main__":
    unittest.main()
