"""이슈 #2061: skill_judge 자문이 (1) 세션 기본 모델이 아니라 항상 haiku
로 고정되고, (2) CONSULT_TIMEOUT(180s) 대신 SKILL_JUDGE_TIMEOUT(기본
45s, env-overridable) 을 쓰며 시간초과시 BM25 top-k 로 fail-open 하고,
(3) `_spawn_one` 안에서 워크스페이스/브랜치 셋업보다 먼저 던져지고 그
뒤에 join 되는지를 검증한다."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class SkillJudgeModelTest(unittest.TestCase):
    def test_model_is_forced_to_haiku_even_when_caller_passes_a_different_model(self):
        seen = {}

        def spy_consult_cmd_and_env(role, cwd, model, **kw):
            seen["model"] = model
            return (["cat"], {}, None)

        session_json = ('{"result": "{\\"picked\\": [], \\"rejected\\": [], '
                        '\\"reasons\\": {}}"}')
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(spawn, "_consult_cmd_and_env", spy_consult_cmd_and_env), \
             mock.patch.object(spawn.subprocess, "run",
                               lambda *a, **k: subprocess.CompletedProcess(
                                   a, 0, stdout=session_json, stderr="")):
            spawn._skill_judge_consult(
                "some task", "implementation", [], 2061, td, model="opus")
        self.assertEqual(seen["model"], "haiku")


class SkillJudgeTimeoutTest(unittest.TestCase):
    def test_default_timeout_is_90s_when_env_unset(self):
        """이슈 #2076: 45s 기본값에서 측정된 완료율이 낮아(consult-log.md
        집계) 90s 로 올렸다 — env override 는 그대로 살아있다. 이슈
        #2274 로 기본값이 조건부(p90 표본 부족시 fallback)가 됐으므로,
        이 테스트는 표본 부족(empty state)을 명시적으로 고정해 이 머신의
        실제 `runs/ledger.jsonl` 이 우연히 50건을 넘겨도 흔들리지 않게
        한다."""
        with mock.patch.dict("os.environ", {}, clear=False), \
             mock.patch.object(spawn, "_skill_judge_p90_cutoff", lambda *a, **k: None):
            spawn.os.environ.pop("SKILL_JUDGE_TIMEOUT", None)
            self.assertEqual(spawn._skill_judge_timeout(), 90)

    def test_env_override_replaces_default(self):
        with mock.patch.dict(spawn.os.environ, {"SKILL_JUDGE_TIMEOUT": "7"}):
            self.assertEqual(spawn._skill_judge_timeout(), 7.0)

    def test_env_override_wins_even_when_p90_cutoff_is_available(self):
        """이슈 #2274: 표본이 충분해 p90 컷오프가 나와도, env override 가
        여전히 최우선이다(운영자가 손으로 좁히거나 늘릴 수 있어야 한다)."""
        with mock.patch.dict(spawn.os.environ, {"SKILL_JUDGE_TIMEOUT": "7"}), \
             mock.patch.object(spawn, "_skill_judge_p90_cutoff", lambda *a, **k: 42.0):
            self.assertEqual(spawn._skill_judge_timeout(), 7.0)

    def test_p90_cutoff_used_when_env_unset_and_samples_sufficient(self):
        with mock.patch.dict("os.environ", {}, clear=False), \
             mock.patch.object(spawn, "_skill_judge_p90_cutoff", lambda *a, **k: 42.0):
            spawn.os.environ.pop("SKILL_JUDGE_TIMEOUT", None)
            self.assertEqual(spawn._skill_judge_timeout(), 42.0)

    def test_subprocess_run_receives_skill_judge_timeout_not_consult_timeout(self):
        seen_timeouts = []

        def spy_run(*a, **k):
            seen_timeouts.append(k.get("timeout"))
            return subprocess.CompletedProcess(
                a, 0, stdout='{"result": "{\\"picked\\": [], \\"rejected\\": [], '
                             '\\"reasons\\": {}}"}', stderr="")

        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(spawn.os.environ, {"SKILL_JUDGE_TIMEOUT": "7"}), \
             mock.patch.object(spawn, "_consult_cmd_and_env",
                               lambda role, cwd, model, **kw: (["cat"], {}, None)), \
             mock.patch.object(spawn.subprocess, "run", spy_run):
            spawn._skill_judge_consult("some task", "implementation", [], 2061, td)
        timed_calls = [t for t in seen_timeouts if t is not None]
        self.assertEqual(timed_calls, [7.0])
        self.assertNotIn(spawn.CONSULT_TIMEOUT, timed_calls)

    def test_timeout_expiry_fails_open_to_bm25_topk(self):
        """`_skill_judge_consult` 가 시간초과로 예외를 올리면
        `_cross_family_skill_matches_with_consult` 는 기존 error 경로와
        똑같이(#2040) BM25 top-k 로 fail-open 한다 — 새 타임아웃 경로도
        같은 fallback 을 탄다."""
        scored_dir = Path("/tmp/does-not-need-to-exist-for-this-test")
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: [(1.0, "a-skill", scored_dir, "skill-repo")]), \
             mock.patch.object(spawn, "_skill_judge_consult",
                               side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=7)):
            matches, outcome = spawn._cross_family_skill_matches_with_consult(
                "task", "implementation", Path(td), 2061, td, k=2)
        self.assertEqual(matches, [scored_dir])
        self.assertEqual(outcome, "fail-open")

    def test_a_genuinely_slow_subprocess_times_out_and_fails_open_live(self):
        """이슈 #2274 Acceptance ("live spawn where a deliberately-slowed
        judge call fails open within the bound") — mock 이 아니라 실제로
        느린 `subprocess.run` 을 한 번 돌려, `_skill_judge_timeout()` 이
        돌려준 값 안에서 진짜로 `TimeoutExpired` 가 나고
        `_cross_family_skill_matches_with_consult` 가 그걸 그대로
        BM25 top-k 로 fail-open 하는지 끝까지 확인한다."""
        scored_dir = Path("/tmp/does-not-need-to-exist-for-this-test")
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(spawn.os.environ, {"SKILL_JUDGE_TIMEOUT": "0.3"}), \
             mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: [(1.0, "a-skill", scored_dir, "skill-repo")]), \
             mock.patch.object(spawn, "_consult_cmd_and_env",
                               lambda role, cwd, model, **kw:
                               (["sleep", "5"], dict(spawn.os.environ), None)):
            matches, outcome = spawn._cross_family_skill_matches_with_consult(
                "task", "implementation", Path(td), 2274, td, k=2)
        self.assertEqual(matches, [scored_dir])
        self.assertEqual(outcome, "fail-open")


class SkillJudgePerfP90Test(unittest.TestCase):
    """이슈 #2274: `runs/ledger.jsonl` 실측 `skill_judge_perf` 분포에서
    p90 컷오프를 뽑아 `_skill_judge_timeout()` 기본값을 대체한다 —
    `_SKILL_JUDGE_PERF_MIN_EVENTS` 미만이면 오늘의 고정 기본값(90s)
    그대로다(empty state)."""

    def _write_ledger(self, path, events):
        with path.open("w", encoding="utf-8") as f:
            for e in events:
                f.write(spawn.json.dumps(e) + "\n")

    def _real_event(self, wall_s):
        return {"event": "skill_judge_perf", "wall_s": wall_s, "duration_ms": 12345,
                "outcome_ok": True}

    def _noise_event(self):
        """`subprocess.run` 을 몽키패치한 다른 세션의 유닛테스트가 이
        원장에 남기는, 진짜 모델 호출이 아닌 잡음 — `duration_ms` 가
        없다."""
        return {"event": "skill_judge_perf", "wall_s": 0.0, "duration_ms": None,
                "outcome_ok": True}

    def test_perf_samples_ignores_events_without_duration_ms(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            self._write_ledger(path, [self._real_event(10.0), self._noise_event(),
                                       self._real_event(20.0),
                                       {"event": "other_event", "wall_s": 99.0,
                                        "duration_ms": 1}])
            samples = spawn._skill_judge_perf_samples(path)
        self.assertEqual(sorted(samples), [10.0, 20.0])

    def test_perf_samples_ignores_near_zero_wall_s_even_with_duration_ms_set(self):
        """issue #2274 warrant-hunt (before-landing, stance 0): `duration_ms`
        alone isn't a safe "real call" marker — a mocked `subprocess.run`
        can echo back a fabricated `duration_ms` while `wall_s` is ~0. 50+
        of those in the shared ledger must not collapse the p90 cutoff (and
        with it `_skill_judge_timeout()`) to ~0s, which would make every
        real call fail open. Reproduces the hunter's exact PoC shape."""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            noisy = [{"event": "skill_judge_perf", "wall_s": 0.0, "duration_ms": 42,
                      "outcome_ok": True} for _ in range(60)]
            self._write_ledger(path, noisy)
            samples = spawn._skill_judge_perf_samples(path)
            cutoff = spawn._skill_judge_p90_cutoff(path)
        self.assertEqual(samples, [])
        self.assertIsNone(cutoff)

    def test_cutoff_is_none_below_min_events(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            events = [self._real_event(float(i)) for i in range(spawn._SKILL_JUDGE_PERF_MIN_EVENTS - 1)]
            self._write_ledger(path, events)
            self.assertIsNone(spawn._skill_judge_p90_cutoff(path))

    def test_cutoff_is_p90_at_min_events(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            # 1..50 초(전부 _MIN_PLAUSIBLE_JUDGE_WALL_S 이상) — 50개,
            # p90(선형보간) = 45.1
            events = [self._real_event(float(i + 1))
                      for i in range(spawn._SKILL_JUDGE_PERF_MIN_EVENTS)]
            self._write_ledger(path, events)
            cutoff = spawn._skill_judge_p90_cutoff(path)
        self.assertEqual(spawn._SKILL_JUDGE_PERF_MIN_EVENTS, 50)
        self.assertAlmostEqual(cutoff, 45.1)

    def test_missing_ledger_file_yields_no_samples(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "does-not-exist.jsonl"
            self.assertEqual(spawn._skill_judge_perf_samples(path), [])
            self.assertIsNone(spawn._skill_judge_p90_cutoff(path))

    def test_read_cost_stays_bounded_regardless_of_total_ledger_size(self):
        """issue #2274 operator-frozen constraint (2026-08-25): "no added
        per-spawn overhead or steady-state load". `runs/ledger.jsonl` is
        append-only and never rotated, so a full-file scan on every
        `_skill_judge_timeout()` call would grow with the installation's
        total lifetime event count. This pins the fix: only the last
        `_LEDGER_TAIL_READ_BYTES` bytes are ever read/parsed, so recent
        genuine samples near the end of a huge ledger are still found
        correctly, and stale genuine-shaped samples far outside the tail
        window are correctly excluded (both proving the window is real,
        not just "happens to include everything")."""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            with path.open("w", encoding="utf-8") as f:
                # stale genuine sample, far before the tail window — must
                # NOT be counted.
                f.write(spawn.json.dumps(self._real_event(999.0)) + "\n")
                # padding well past the tail-window size so the line above
                # falls outside it.
                pad_line = spawn.json.dumps({"event": "other", "pad": "x" * 200})
                for _ in range((spawn._LEDGER_TAIL_READ_BYTES // len(pad_line)) + 10):
                    f.write(pad_line + "\n")
                # genuine samples inside the tail window — must be counted.
                for i in range(spawn._SKILL_JUDGE_PERF_MIN_EVENTS):
                    f.write(spawn.json.dumps(self._real_event(float(i + 1))) + "\n")
            samples = spawn._skill_judge_perf_samples(path)
        self.assertNotIn(999.0, samples)
        self.assertEqual(len(samples), spawn._SKILL_JUDGE_PERF_MIN_EVENTS)


class SkillJudgeOverlapOrderingTest(unittest.TestCase):
    """`_spawn_one` 이 skill_judge 자문을 워크스페이스/브랜치 셋업보다
    먼저 던지고 그 join 은 셋업 뒤(cross_family 단계)에서만 일어나는지를
    코드 순서로 검증한다(이슈 #2061 acceptance: "judge launch precedes
    workspace setup ... with the join after")."""

    def _prep_repo(self, td):
        work = Path(td) / "work"
        work.mkdir()
        run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True,
                                        text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (work / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        return work

    def test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows(self):
        events = []

        class _FakeFuture:
            def __init__(self, value):
                self._value = value

            def result(self):
                events.append("join")
                return self._value

        class _FakeExecutor:
            def __init__(self, *a, **k):
                pass

            def submit(self, fn, *a, **k):
                events.append("judge-dispatch")
                return _FakeFuture(fn(*a, **k))

            def shutdown(self, wait=True):
                pass

        def fake_matches_with_consult(*a, **k):
            events.append("judge-ran")
            return [], "completed"

        role_source = {"source": "skill-repo", "skill_dirs": [],
                       "skills": [], "skill_sha": None}

        def fake_issue_workspace(cwd, issue, role):
            events.append("workspace")
            return cwd

        def fake_checkout_issue_branch(cwd, issue, role):
            events.append("branch")
            return "b"

        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            with mock.patch.object(spawn.concurrent.futures, "ThreadPoolExecutor",
                                   _FakeExecutor), \
                 mock.patch.object(spawn, "_cross_family_skill_matches_with_consult",
                                   fake_matches_with_consult), \
                 mock.patch.object(spawn, "issue_workspace", fake_issue_workspace), \
                 mock.patch.object(spawn, "checkout_issue_branch",
                                   fake_checkout_issue_branch), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: role_source), \
                 mock.patch.object(spawn, "_skill_repo_root", lambda: Path(td)), \
                 mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                 mock.patch.object(spawn, "core_version", lambda: "v0"), \
                 mock.patch.object(spawn, "_clean_auto_enabled", lambda: False), \
                 mock.patch.object(spawn, "spawn_cmd", lambda *a, **k: (["cat"], {})), \
                 mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                 mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
                 mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
                 mock.patch.object(spawn, "_undispositioned_role_prs",
                                   lambda root, exclude_issue=None: ([], True)), \
                 mock.patch.object(spawn, "roster_register", lambda *a, **k: None), \
                 mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
                spawn._spawn_one(str(work), "implementation", "task\n",
                                 unattended=True, issue=2061, bounded=False,
                                 no_wait=True)

        self.assertIn("judge-dispatch", events)
        self.assertIn("workspace", events)
        self.assertIn("join", events)
        self.assertLess(events.index("judge-dispatch"), events.index("workspace"),
                        f"judge must dispatch before workspace setup: {events}")
        self.assertGreater(events.index("join"), events.index("workspace"),
                           f"judge join must come after workspace setup: {events}")
        if "branch" in events:
            self.assertLess(events.index("judge-dispatch"), events.index("branch"),
                            f"judge must dispatch before branch setup: {events}")
            self.assertGreater(events.index("join"), events.index("branch"),
                               f"judge join must come after branch setup: {events}")


class SkillJudgeLedgerFieldTest(unittest.TestCase):
    """이슈 #2076: skill_judge 완료율을 스폰마다 측정하려면 원장
    (runs/ledger.jsonl) 에 completed/fail-open 여부가 남아야 한다 —
    `_spawn_one` 의 `ledger_write` 호출에 `skill_judge_outcome` 필드가
    실제로 실리는지 검증한다."""

    def _prep_repo(self, td):
        work = Path(td) / "work"
        work.mkdir()
        run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True,
                                        text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (work / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        return work

    def _run_spawn_one_with_outcome(self, td, work, matches_return):
        recorded = []
        role_source = {"source": "skill-repo", "skill_dirs": [],
                       "skills": [], "skill_sha": None}
        with mock.patch.object(spawn, "_cross_family_skill_matches_with_consult",
                               lambda *a, **k: matches_return), \
             mock.patch.object(spawn, "issue_workspace", lambda cwd, issue, role: cwd), \
             mock.patch.object(spawn, "checkout_issue_branch",
                               lambda cwd, issue, role: "b"), \
             mock.patch.object(spawn, "resolve_role_source",
                               lambda role, repo_root: role_source), \
             mock.patch.object(spawn, "_skill_repo_root", lambda: Path(td)), \
             mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
             mock.patch.object(spawn, "core_version", lambda: "v0"), \
             mock.patch.object(spawn, "_clean_auto_enabled", lambda: False), \
             mock.patch.object(spawn, "spawn_cmd", lambda *a, **k: (["cat"], {})), \
             mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
             mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
             mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
             mock.patch.object(spawn, "_undispositioned_role_prs",
                               lambda root, exclude_issue=None: ([], True)), \
             mock.patch.object(spawn, "roster_register", lambda *a, **k: None), \
             mock.patch.object(spawn, "ledger_write",
                               lambda entry: recorded.append(entry)):
            spawn._spawn_one(str(work), "implementation", "task\n",
                             unattended=True, issue=2061, bounded=False,
                             no_wait=True)
        return recorded

    def test_ledger_entry_records_completed_outcome(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            recorded = self._run_spawn_one_with_outcome(td, work, ([], "completed"))
        self.assertEqual(recorded[-1]["skill_judge_outcome"], "completed")

    def test_ledger_entry_records_fail_open_outcome(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            recorded = self._run_spawn_one_with_outcome(td, work, ([], "fail-open"))
        self.assertEqual(recorded[-1]["skill_judge_outcome"], "fail-open")

    def test_ledger_entry_records_not_run_when_role_source_is_not_skill_repo(self):
        role_source = {"source": "flat", "skill_dirs": [], "skills": [], "skill_sha": None}
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            recorded = []
            with mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: role_source), \
                 mock.patch.object(spawn, "_skill_repo_root", lambda: Path(td)), \
                 mock.patch.object(spawn, "issue_workspace", lambda cwd, issue, role: cwd), \
                 mock.patch.object(spawn, "checkout_issue_branch",
                                   lambda cwd, issue, role: "b"), \
                 mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                 mock.patch.object(spawn, "core_version", lambda: "v0"), \
                 mock.patch.object(spawn, "_clean_auto_enabled", lambda: False), \
                 mock.patch.object(spawn, "spawn_cmd", lambda *a, **k: (["cat"], {})), \
                 mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                 mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
                 mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
                 mock.patch.object(spawn, "_undispositioned_role_prs",
                                   lambda root, exclude_issue=None: ([], True)), \
                 mock.patch.object(spawn, "roster_register", lambda *a, **k: None), \
                 mock.patch.object(spawn, "ledger_write",
                                   lambda entry: recorded.append(entry)):
                spawn._spawn_one(str(work), "implementation", "task\n",
                                 unattended=True, issue=2061, bounded=False,
                                 no_wait=True)
        self.assertEqual(recorded[-1]["skill_judge_outcome"], "not-run")


if __name__ == "__main__":
    unittest.main()
