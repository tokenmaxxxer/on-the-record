"""이슈 #1508: 로컬-전용 세션 관찰성 — liveness/progress/stall 판정이 gh
호출 없이 로컬 신호(로그 mtime/내용, events.jsonl, watcher pid, git 상태)
만으로 나오는지, 그리고 gh 는 PR-state 확인 한 경로로만 좁혀졌는지 검증."""
import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn  # noqa: E402


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "f.txt").write_text("1")
    subprocess.run(["git", "add", "f.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


class _GhCallRecorder:
    """`subprocess.run` 을 감싸 `gh` 로 시작하는 호출만 센다 — 다른
    subprocess(git 등) 호출은 실제로 실행되게 통과시킨다."""

    def __init__(self):
        self.calls: list[list[str]] = []
        self._real_run = subprocess.run

    def __call__(self, cmd, *args, **kwargs):
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "gh":
            self.calls.append(list(cmd))
            result = mock.Mock()
            result.returncode = 1
            result.stdout = ""
            result.stderr = ""
            return result
        return self._real_run(cmd, *args, **kwargs)


class TestLivenessVerdictsNoGh(unittest.TestCase):
    """수용 기준 1: fixture 워크스페이스별 판정 + gh 호출 0건."""

    def _entry(self, log, work=None, ts=None, before_head=None, pid=None):
        return {"log": str(log), "work": work, "ts": ts or int(time.time()),
                "before_head": before_head, "pid": pid}

    def test_fresh_log_no_anomalies_no_gh(self):
        with mock.patch("spawn.subprocess.run", new=_GhCallRecorder()) as rec, \
             self._tmp() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertEqual(out, [])
            self.assertEqual(rec.calls, [])

    def test_stale_log_signals_silence_no_gh(self):
        with mock.patch("spawn.subprocess.run", new=_GhCallRecorder()) as rec, \
             self._tmp() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            stale = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            import os
            os.utime(log, (stale, stale))
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertTrue(any("log-silence" in a for a in out))
            self.assertEqual(rec.calls, [])

    def test_dead_watcher_pid_signals_no_gh(self):
        with mock.patch("spawn.subprocess.run", new=_GhCallRecorder()) as rec, \
             self._tmp() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            work = Path(td) / "issue-1/implementation"
            _init_git_repo(work)
            ws_key = f"{spawn._repo_identity(str(work))}/k"
            with mock.patch.object(
                    spawn, "_workspace_index_load",
                    return_value={ws_key: {"watcher_pid": 999999999}}):
                out = spawn.watchdog_check_one(
                    "k", self._entry(log, work=str(work)), state={})
            self.assertTrue(any("watcher-dead" in a or "watcher-missing" in a
                                 for a in out))
            self.assertEqual(rec.calls, [])

    def test_zero_commit_aged_session_signals_no_gh(self):
        with mock.patch("spawn.subprocess.run", new=_GhCallRecorder()) as rec, \
             self._tmp() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            work = Path(td) / "issue-2/implementation"
            _init_git_repo(work)
            head = subprocess.run(
                ["git", "-C", str(work), "rev-parse", "HEAD"],
                capture_output=True, text=True).stdout.strip()
            old_ts = int(time.time()) - (spawn.WATCHDOG_NO_COMMIT_MIN + 5) * 60
            out = spawn.watchdog_check_one(
                "k", self._entry(log, work=str(work), ts=old_ts,
                                  before_head=head), state={})
            self.assertTrue(any("no-commits-late" in a for a in out))
            # git 호출은 허용(신호 4 는 로컬 git 을 쓴다) — gh 만 0건.
            self.assertEqual(rec.calls, [])

    def test_empty_workspace_set_yields_empty_verdicts_not_error(self):
        with mock.patch("spawn.subprocess.run", new=_GhCallRecorder()) as rec:
            out = spawn.watchdog_check_one(
                "k", self._entry(log=Path("/nonexistent/does-not-exist.log")),
                state={})
            self.assertEqual(out, [])
            self.assertEqual(rec.calls, [])

    @staticmethod
    def _tmp():
        import tempfile
        return tempfile.TemporaryDirectory()


class TestSignalCoverageNoRegression(unittest.TestCase):
    """수용 기준 3: phase-1 인벤토리(survey.md)가 나열한 신호 타입이 오늘도
    똑같이 도출 가능함을 회귀 테스트로 고정한다."""

    SIGNAL_TYPES = (
        "log-silence",
        "background-delegation-phrasing",
        "denied-tool-calls",
        "no-commits-late",
        "watcher-missing",
        "watcher-dead",
        "watcher-silent",
    )

    def test_every_inventoried_signal_type_still_derivable(self):
        import os
        with self._tmp() as td:
            log = Path(td) / "s.log"
            stale = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            denial_line = json.dumps({"type": "user", "message": {"content": [
                {"type": "tool_result", "is_error": True,
                 "content": "Permission to use Bash has been denied"}]}},
                ensure_ascii=False) + "\n"
            # 이슈 #2217: signal 2 는 이제 구조적 tool_use(run_in_background)
            # 만 센다 — 단어가 든 텍스트 줄이 아니라 실제 tool_use 블록이어야
            # 신호가 뜬다.
            delegation_line = json.dumps({"type": "assistant", "message": {
                "content": [{"type": "tool_use", "name": "Bash",
                             "input": {"command": "sleep 999",
                                       "run_in_background": True}}]}},
                ensure_ascii=False) + "\n"
            log.write_text(
                delegation_line
                + denial_line * spawn.WATCHDOG_DENIAL_THRESHOLD)
            os.utime(log, (stale, stale))
            work = Path(td) / "issue-3/implementation"
            _init_git_repo(work)
            head = subprocess.run(
                ["git", "-C", str(work), "rev-parse", "HEAD"],
                capture_output=True, text=True).stdout.strip()
            old_ts = int(time.time()) - (spawn.WATCHDOG_NO_COMMIT_MIN + 5) * 60
            entry = {"log": str(log), "work": str(work), "ts": old_ts,
                     "before_head": head, "pid": None}
            with mock.patch.object(spawn, "_workspace_index_load",
                                    return_value={}):
                out = spawn.watchdog_check_one("k", entry, state={})
            fired = {a.split(":", 1)[0].split(" ", 1)[0] for a in out}
            for expected in ("log-silence", "background-delegation-phrasing",
                              "denied-tool-calls", "no-commits-late"):
                self.assertTrue(
                    any(a.startswith(expected) for a in out),
                    f"signal {expected!r} did not fire; got {out}")
            self.assertTrue(fired)

    def test_watcher_missing_signal_derivable(self):
        with self._tmp() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            work = Path(td) / "issue-4/implementation"
            _init_git_repo(work)
            ws_key = f"{spawn._repo_identity(str(work))}/k"
            with mock.patch.object(
                    spawn, "_workspace_index_load",
                    return_value={ws_key: {"watcher_pid": None}}):
                out = spawn.watchdog_check_one(
                    "k", {"log": str(log), "work": str(work),
                          "ts": int(time.time()), "before_head": None,
                          "pid": None}, state={})
            self.assertTrue(any("watcher-missing" in a for a in out))

    @staticmethod
    def _tmp():
        import tempfile
        return tempfile.TemporaryDirectory()


class TestBackgroundDelegationStructural(unittest.TestCase):
    """이슈 #2217: signal 2("background-delegation-phrasing")가 어휘가
    아니라 구조적 tool_use(run_in_background) 를 세는지 검증한다."""

    def _entry(self, log, work=None, ts=None, before_head=None, pid=None):
        return {"log": str(log), "work": work, "ts": ts or int(time.time()),
                "before_head": before_head, "pid": pid}

    @staticmethod
    def _tmp():
        import tempfile
        return tempfile.TemporaryDirectory()

    def test_injected_directive_text_alone_yields_zero_anomalies(self):
        """수용 기준(empty state): 주입된 지시문과 그 외 아무것도 없는
        (막 스폰돼 아직 assistant 턴이 없는) 세션 로그는 anomaly 0건이어야
        한다."""
        with self._tmp() as td:
            log = Path(td) / "s.log"
            system_line = json.dumps(
                {"type": "system", "subtype": "hook_started",
                 "text": spawn._COMPLETION_PROSE},
                ensure_ascii=False) + "\n"
            log.write_text(system_line)
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertEqual(out, [])

    def test_own_injected_warning_in_assistant_text_does_not_trigger(self):
        """지시문 어휘가 assistant 의 평범한 텍스트 블록(도구 호출이 아닌)
        안에 나타나도 신호는 뜨지 않는다 — 문자열 매치가 아니라 구조적
        tool_use 여부만 본다."""
        with self._tmp() as td:
            log = Path(td) / "s.log"
            text_line = json.dumps({"type": "assistant", "message": {
                "content": [{"type": "text", "text": spawn._COMPLETION_PROSE}]}},
                ensure_ascii=False) + "\n"
            log.write_text(text_line)
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertFalse(
                any("background-delegation-phrasing" in a for a in out),
                f"word-match false positive; got {out}")

    def test_genuine_bash_run_in_background_tool_use_still_trips_signal(self):
        with self._tmp() as td:
            log = Path(td) / "s.log"
            line = json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Bash",
                 "input": {"command": "sleep 999",
                           "run_in_background": True}}]}},
                ensure_ascii=False) + "\n"
            log.write_text(line)
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertTrue(any("background-delegation-phrasing" in a for a in out))

    def test_genuine_agent_run_in_background_tool_use_still_trips_signal(self):
        with self._tmp() as td:
            log = Path(td) / "s.log"
            line = json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Agent",
                 "input": {"description": "background work",
                           "run_in_background": True}}]}},
                ensure_ascii=False) + "\n"
            log.write_text(line)
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertTrue(any("background-delegation-phrasing" in a for a in out))

    def test_count_structural_delegations_ignores_non_assistant_types(self):
        system_line = json.dumps(
            {"type": "system", "text": spawn._COMPLETION_PROSE},
            ensure_ascii=False)
        self.assertEqual(spawn._count_structural_delegations(system_line), 0)

    def test_count_structural_delegations_counts_tool_use_run_in_background(self):
        line = json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash",
             "input": {"command": "x", "run_in_background": True}}]}},
            ensure_ascii=False)
        self.assertEqual(spawn._count_structural_delegations(line), 1)


class TestGhOnlyForPrState(unittest.TestCase):
    """수용 기준: PR-state 확인이 pending 인 틱만 gh(벌크 경로 포함) 를
    부르고, pending 아닌 틱은 0건."""

    def test_dead_entry_with_pr_index_makes_zero_gh_calls(self):
        rec = _GhCallRecorder()
        with mock.patch("spawn.subprocess.run", new=rec):
            entry = {"pid": 999999999, "work": "/tmp/issue-9/implementation",
                     "log": None}
            pr_index = {"issue-9/implementation":
                        {"number": 42, "state": "OPEN"}}
            result = spawn.diagnose_health(
                "issue-9/implementation", entry, state={}, pr_index=pr_index)
        self.assertEqual(rec.calls, [])
        self.assertIsNone(result["state"])  # PR 있음 -> completion, 진단 대상 아님

    def test_dead_entry_without_pr_index_makes_one_gh_call(self):
        rec = _GhCallRecorder()
        with mock.patch("spawn.subprocess.run", new=rec):
            entry = {"pid": 999999999, "work": "/tmp/issue-10/implementation",
                     "log": None}
            spawn.diagnose_health("issue-10/implementation", entry, state={})
        self.assertEqual(len(rec.calls), 1)
        self.assertEqual(rec.calls[0][:3], ["gh", "pr", "list"])

    def test_pr_state_from_index_matches_open_or_merged_semantics(self):
        idx = {"b-open": {"number": 1, "state": "OPEN"},
               "b-merged": {"number": 2, "state": "MERGED"},
               "b-closed": {"number": 3, "state": "CLOSED"}}
        self.assertEqual(spawn._pr_state_from_index(idx, "b-open"), 1)
        self.assertEqual(spawn._pr_state_from_index(idx, "b-merged"), 2)
        self.assertIsNone(spawn._pr_state_from_index(idx, "b-closed"))
        self.assertIsNone(spawn._pr_state_from_index(idx, "b-missing"))


if __name__ == "__main__":
    unittest.main()
