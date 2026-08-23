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

        def spy_consult_cmd_and_env(role, spec, cwd, model):
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
    def test_default_timeout_is_45s_when_env_unset(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            spawn.os.environ.pop("SKILL_JUDGE_TIMEOUT", None)
            self.assertEqual(spawn._skill_judge_timeout(), 45)

    def test_env_override_replaces_default(self):
        with mock.patch.dict(spawn.os.environ, {"SKILL_JUDGE_TIMEOUT": "7"}):
            self.assertEqual(spawn._skill_judge_timeout(), 7.0)

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
                               lambda role, spec, cwd, model: (["cat"], {}, None)), \
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
            matches = spawn._cross_family_skill_matches_with_consult(
                "task", "implementation", Path(td), 2061, td, k=2)
        self.assertEqual(matches, [scored_dir])


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
            return []

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


if __name__ == "__main__":
    unittest.main()
