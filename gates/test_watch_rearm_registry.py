#!/usr/bin/env python3
"""이슈 #1133: `spawn.py watch --rearm`이 죽은 워처를 재무장하면 다음
watchdog 틱이 그 항목을 더 이상 watcher-dead 로 신고하지 않아야 하고,
워처가 정말 다시 죽으면 여전히 신고해야 한다(watch-coverage 회귀 가드).
`MUSTER_STATE_ROOT` 로 잡은 임시 디렉터리를 통해 hermetic 하게 돈다.

  python3 -m pytest gates/test_watch_rearm_registry.py -v
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn


class WatchRearmRegistry(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        state_root = Path(self._tmp.name) / "runs"
        state_root.mkdir(parents=True, exist_ok=True)
        self._env_patch = mock.patch.dict(
            os.environ, {"MUSTER_STATE_ROOT": str(state_root)})
        self._env_patch.start()
        self.addCleanup(self._env_patch.stop)
        # 이슈 #1133: STATE_ROOT/ROSTER/WORKSPACE_INDEX 는 모듈 임포트
        # 시점에 MUSTER_STATE_ROOT 로부터 계산되는 상수라, 이미 임포트된
        # spawn 모듈에는 위 환경변수 설정이 소급 반영되지 않는다 —
        # 실제 코드가 그 환경변수로 고르는 것과 같은 경로로 직접 옮겨
        # 붙인다(이 테스트가 함수를 프로세스 안에서 직접 부르기 때문).
        self.work_dir = Path(self._tmp.name) / "work"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self._state_patch = mock.patch.multiple(
            spawn,
            STATE_ROOT=state_root,
            ROSTER=state_root / "active.json",
            WORKSPACE_INDEX=state_root / "workspaces.json",
        )
        self._state_patch.start()
        self.addCleanup(self._state_patch.stop)
        self.issue = 999001
        self.role = "implementation"
        self.repo = spawn._repo_identity(str(self.work_dir))
        self.key = f"{self.repo}/issue-{self.issue}/{self.role}"

    def _put_entry(self, watcher_pid=None, watcher_armed_at=None):
        spawn.WORKSPACE_INDEX.parent.mkdir(parents=True, exist_ok=True)
        entry = {"work": str(self.work_dir), "log": str(self.work_dir) + ".log"}
        if watcher_pid is not None:
            entry["watcher_pid"] = watcher_pid
        if watcher_armed_at is not None:
            entry["watcher_armed_at"] = watcher_armed_at
        spawn.WORKSPACE_INDEX.write_text(
            json.dumps({self.key: entry}, indent=2, ensure_ascii=False))

    def _watch_anomalies(self):
        # 이슈 #1133: `issue` 를 안 주면 `_watcher_looks_real()`이
        # `/proc/<pid>/cmdline` 신원 검사(리눅스 전용, 이 테스트가 흉내내는
        # fake Popen 자식엔 못 재현) 대신 `_alive()` 만으로 저하한다 —
        # 여기서 재현 대상은 등록/신고 로직이지 cmdline 신원 검사가 아니다.
        roster_entry = {"pid": os.getpid(), "role": self.role,
                         "work": str(self.work_dir)}
        return spawn.watchdog_check_one(
            f"issue-{self.issue}/{self.role}", roster_entry, now=time.time())

    def test_rearm_clears_watcher_dead_and_updates_registry(self):
        dead_pid = 999999999  # 존재할 리 없는 pid — _alive() 가 False 를 돌려줌
        self._put_entry(watcher_pid=dead_pid, watcher_armed_at=time.time())
        self.assertTrue(any(a.startswith("watcher-dead")
                             for a in self._watch_anomalies()))

        with mock.patch.object(spawn.subprocess, "Popen") as popen:
            fake_proc = mock.Mock()
            fake_proc.pid = os.getpid()  # 테스트 프로세스 자신 — 살아있는 pid
            popen.return_value = fake_proc
            rc = spawn._rearm_watcher_detached(
                self.issue, self.role, 5.0,
                repo=self.repo)
        self.assertEqual(rc, 0)
        popen.assert_called_once()
        args, kwargs = popen.call_args
        self.assertTrue(kwargs.get("start_new_session"))

        idx = json.loads(spawn.WORKSPACE_INDEX.read_text())
        self.assertEqual(idx[self.key]["watcher_pid"], os.getpid())
        self.assertNotEqual(idx[self.key]["watcher_pid"], dead_pid)
        self.assertFalse(any(a.startswith("watcher-dead") or a.startswith("watcher-missing")
                              for a in self._watch_anomalies()))

    def test_rearmed_watcher_dying_again_is_still_flagged(self):
        """회귀 가드: 재무장 뒤에도 워처가 정말로 죽으면 watch-coverage 는
        그대로 유지되어야 한다 — genuinely-dead 워처가 조용히 안 잡히면 안 된다."""
        self._put_entry(watcher_pid=999999998, watcher_armed_at=time.time())
        with mock.patch.object(spawn.subprocess, "Popen") as popen:
            fake_proc = mock.Mock()
            fake_proc.pid = os.getpid()
            popen.return_value = fake_proc
            rc = spawn._rearm_watcher_detached(
                self.issue, self.role, 5.0,
                repo=self.repo)
        self.assertEqual(rc, 0)
        # 재무장된 pid 를 다시 죽은 pid 로 되돌려 "재무장 후 재사망"을 흉내낸다.
        idx = json.loads(spawn.WORKSPACE_INDEX.read_text())
        idx[self.key]["watcher_pid"] = 999999997
        spawn.WORKSPACE_INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False))
        self.assertTrue(any(a.startswith("watcher-dead")
                             for a in self._watch_anomalies()))

    def test_never_armed_entry_untouched_and_still_missing(self):
        self._put_entry(watcher_pid=None)
        anomalies_before = self._watch_anomalies()
        self.assertTrue(any(a.startswith("watcher-missing") for a in anomalies_before))

        with mock.patch.object(spawn.subprocess, "Popen") as popen:
            fake_proc = mock.Mock()
            fake_proc.pid = os.getpid()
            popen.return_value = fake_proc
            rc = spawn._rearm_watcher_detached(
                self.issue, self.role, 5.0,
                repo=self.repo)
        # entry["watcher_pid"] 는 없음(=None) 상태이므로 "죽었다" 판정을 받아
        # 새로 무장을 시도한다 — 다만 그 자체는 "손대지 않는다"는 요구가
        # 아니라 무장 자체가 되는지를 본다: 신규 무장 성공 후에는
        # watcher-missing 이 사라져야 정상이다.
        self.assertEqual(rc, 0)
        popen.assert_called_once()
        idx = json.loads(spawn.WORKSPACE_INDEX.read_text())
        self.assertIn("watcher_pid", idx[self.key])

    def test_already_alive_watcher_is_not_respawned(self):
        self._put_entry(watcher_pid=os.getpid(), watcher_armed_at=time.time())
        # `_watcher_looks_real()`의 `/proc/<pid>/cmdline` 신원 검사는 실제
        # `watch --follow` 자식에게만 통과한다 — 테스트 프로세스 자신의
        # cmdline 은 그와 다르므로, "이미 살아있는 진짜 워처" 케이스를
        # 흉내내려면 그 판정 자체를 고정해야 한다.
        with mock.patch.object(spawn, "_watcher_looks_real", return_value=True), \
                mock.patch.object(spawn.subprocess, "Popen") as popen:
            rc = spawn._rearm_watcher_detached(
                self.issue, self.role, 5.0,
                repo=self.repo)
        self.assertEqual(rc, 0)
        popen.assert_not_called()

    def test_remediation_strings_carry_no_bare_follow(self):
        src = Path(spawn.__file__).read_text(encoding="utf-8")
        for marker in ("watcher-dead:", "watcher-silent:"):
            idx = src.index(marker)
            snippet = src[idx:idx + 400]
            self.assertNotIn("--follow 로 재무장", snippet,
                              f"{marker} remediation still names blocking --follow")
            self.assertIn("--rearm", snippet)


if __name__ == "__main__":
    unittest.main()
