"""이슈 #2001/#2040: family 세트는 그대로 두고(add-only), 스폰 태스크 텍스트와
크로스-패밀리 스킬의 SKILL.md "Use ..." 트리거 문장을 BM25(이슈 #2040 —
raw 겹침-카운트 대체)로 채점해 상위 후보를 skill_judge 자문에 넘기고,
자문이 조건-매치로 고른 것만(최대 K=2) 추가로 마운트한다.

acceptance: 매치되는 태스크는 마운트 목록이 정확히 그 스킬만큼(최대 K=2)
늘고 디렉티브에도 실린다; 매치 안 되는 태스크는 마운트/디렉티브가 오늘과
바이트 단위로 동일하다 — 둘 다 라이브(serial, -o addopts='')로 검증한다.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class TokenizeTest(unittest.TestCase):
    def test_lowercases_splits_nonalnum_and_drops_stopwords(self):
        self.assertEqual(
            spawn._tokenize("Use when a Landing Page needs Contrast."),
            {"landing", "page", "needs", "contrast"})

    def test_empty_text_yields_empty_set(self):
        self.assertEqual(spawn._tokenize(""), set())
        self.assertEqual(spawn._tokenize("a the or and is an use when"), set())


class Bm25CrossFamilySkillMatchesTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _skill(self, name, use_sentence):
        d = self.repo_root / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            f"description: >-\n"
            f"  Intro text. {use_sentence}\n"
            "---\n\n# body\n", encoding="utf-8")
        return d

    def test_matching_skill_clears_threshold_and_is_returned(self):
        d = self._skill(
            "accessibility-aria-and-contrast-rules",
            "Use when deciding an ARIA role, an accessible name, or a "
            "text/background contrast pair on a landing page.")
        matches = spawn._cross_family_skill_matches(
            "Build a landing page and check its contrast against WCAG.",
            "implementation", self.repo_root)
        self.assertEqual(matches, [d])

    def test_single_shared_token_still_scores_positive_under_bm25(self):
        # 이슈 #2040: BM25 floor 는 score>0(질의-문서 토큰 1개 이상 겹침) —
        # raw-overlap 시절의 고정 임계값(>=2) 은 더 이상 없다. 단어 하나
        # 겹침으로 여기서 스코어링되는 저품질 후보를 걷어내는 건 이제
        # skill_judge 자문 단계의 몫(ConsultJudgeStageTest 참고).
        d = self._skill("some-other-skill",
                        "Use when reviewing generic code quality issues.")
        matches = spawn._cross_family_skill_matches(
            "Write some code today.", "implementation", self.repo_root)
        self.assertEqual(matches, [d])

    def test_no_shared_token_no_match(self):
        self._skill("some-other-skill",
                     "Use when reviewing generic quality issues.")
        matches = spawn._cross_family_skill_matches(
            "Deploy the widget frobnicator.", "implementation", self.repo_root)
        self.assertEqual(matches, [])

    def test_family_skill_never_returned_as_cross_family_candidate(self):
        # implementation-blueprint is already in _ROLE_SKILLS['implementation']
        self._skill(
            "implementation-blueprint",
            "Use whenever you are about to produce non-trivial code "
            "spanning multiple modules landing pages contrast accessible.")
        matches = spawn._cross_family_skill_matches(
            "Build a landing page contrast accessible module.",
            "implementation", self.repo_root)
        self.assertEqual(matches, [])

    def test_k_cap_with_three_clearing_candidates_keeps_top_two(self):
        self._skill("zzz-skill-c",
                     "Use when a landing page needs contrast accessible review.")
        self._skill("aaa-skill-a",
                     "Use when a landing page needs contrast accessible review.")
        self._skill("mmm-skill-b",
                     "Use when a landing page needs contrast accessible review.")
        matches = spawn._cross_family_skill_matches(
            "Build a landing page that needs contrast accessible review.",
            "implementation", self.repo_root, k=2)
        self.assertEqual(len(matches), 2)
        # tie-break by name asc when scores are equal
        self.assertEqual([d.name for d in matches],
                         ["aaa-skill-a", "mmm-skill-b"])

    def test_no_trigger_line_skill_never_matches(self):
        d = self.repo_root / "no-desc-skill"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nname: no-desc-skill\n---\n",
                                    encoding="utf-8")
        matches = spawn._cross_family_skill_matches(
            "landing page contrast accessible", "implementation",
            self.repo_root)
        self.assertEqual(matches, [])


class SpawnOneCrossFamilyAcceptanceTest(unittest.TestCase):
    """acceptance: 라이브 `_spawn_one()` 을 통한 두 케이스 — 매치/비매치."""

    def setUp(self):
        self._old_roster = spawn.ROSTER
        self._old_idx = spawn.WORKSPACE_INDEX
        self._td = tempfile.TemporaryDirectory()
        spawn.ROSTER = Path(self._td.name) / "active.json"
        spawn.WORKSPACE_INDEX = Path(self._td.name) / "workspaces.json"

    def tearDown(self):
        spawn.ROSTER = self._old_roster
        spawn.WORKSPACE_INDEX = self._old_idx
        self._td.cleanup()

    def _prep_repo(self, td, name="work"):
        work = Path(td) / name
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

    def _run(self, work, task_text, skill_repo_root, *, issue=2001):
        roster_calls = []
        real_roster_register = spawn.roster_register
        spawn_cmd_calls = []

        def spy_roster_register(key, entry):
            roster_calls.append((key, dict(entry)))
            return real_roster_register(key, entry)

        def spy_spawn_cmd(settings, role, unattended, core_plugins, plugins,
                          model, skill_dirs, skill_repo_sha_value, **kwargs):
            spawn_cmd_calls.append(list(skill_dirs))
            return (["cat"], {})

        role_source = {"source": "skill-repo", "skill_dirs": [],
                       "skills": [], "skill_sha": None}

        # 이슈 #2040: 크로스-패밀리 선택이 이제 BM25 + skill_judge 자문을
        # 거친다 — 이 테스트들은 BM25 프리필터 자체(매치/비매치, 결정론)를
        # 검증하는 게 목적이라, 자문 단계는 "BM25 상위를 그대로 받아들인다"
        # 로 스텁해 오늘의 테스트 기대치(마운트 = BM25 top-k)를 그대로
        # 재사용한다. 자문 자체의 판단/트레이스/fail-open 동작은
        # ConsultJudgeStageTest 가 별도로 검증한다.
        def stub_with_consult(task_text, role, repo_root, issue, cwd, k=2, model=None,
                              home=None, target_repo_root=None):
            return (spawn._cross_family_skill_matches(task_text, role, repo_root, k=k),
                    "completed")

        with mock.patch.object(spawn, "_cross_family_skill_matches_with_consult",
                               stub_with_consult), \
             mock.patch.object(spawn, "issue_workspace",
                               lambda cwd, issue, role: str(work)), \
             mock.patch.object(spawn, "checkout_issue_branch",
                               lambda cwd, issue, role: "b"), \
             mock.patch.object(spawn, "resolve_role_source",
                               lambda role, repo_root: role_source), \
             mock.patch.object(spawn, "_skill_repo_root",
                               lambda: skill_repo_root), \
             mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
             mock.patch.object(spawn, "core_version", lambda: "v0"), \
             mock.patch.object(spawn, "_clean_auto_enabled", lambda: False), \
             mock.patch.object(spawn, "spawn_cmd", spy_spawn_cmd), \
             mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
             mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
             mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
             mock.patch.object(spawn, "_undispositioned_role_prs",
                               lambda root, exclude_issue=None: ([], True)), \
             mock.patch.object(spawn, "roster_register", spy_roster_register), \
             mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
            rc = spawn._spawn_one(str(work), "implementation", task_text,
                                  unattended=True, issue=issue, bounded=False,
                                  no_wait=True)
        self.assertEqual(rc, 0)
        log_path = roster_calls[-1][1]["log"]
        delivered = Path(log_path).read_text()
        return delivered, spawn_cmd_calls[-1]

    def _seed_cross_family_skill(self, root):
        d = root / "accessibility-aria-and-contrast-rules"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\n"
            "name: accessibility-aria-and-contrast-rules\n"
            "description: >-\n"
            "  Use when deciding an ARIA role, an accessible name, or a\n"
            "  text/background contrast pair for a landing page redesign.\n"
            "---\n\n# body\n", encoding="utf-8")
        return d

    def test_matching_task_gains_exactly_that_skill_in_mounts_and_directive(self):
        with tempfile.TemporaryDirectory() as td, \
             tempfile.TemporaryDirectory() as skills_td:
            work = self._prep_repo(td)
            skill_repo_root = Path(skills_td)
            skill_dir = self._seed_cross_family_skill(skill_repo_root)
            delivered, mounted = self._run(
                work,
                "Redesign the landing page and fix its ARIA role and "
                "contrast pair.",
                skill_repo_root)
        self.assertIn("accessibility-aria-and-contrast-rules", delivered)
        self.assertEqual(mounted, [skill_dir])

    def test_non_matching_task_mounts_and_directive_byte_identical_to_baseline(self):
        with tempfile.TemporaryDirectory() as td_a, \
             tempfile.TemporaryDirectory() as td_b, \
             tempfile.TemporaryDirectory() as skills_td:
            skill_repo_root = Path(skills_td)
            self._seed_cross_family_skill(skill_repo_root)

            work_a = self._prep_repo(td_a, "work-a")
            delivered_a, mounted_a = self._run(
                work_a, "Refactor the internal batching pipeline.",
                skill_repo_root, issue=2001)

            work_b = self._prep_repo(td_b, "work-b")
            delivered_b, mounted_b = self._run(
                work_b, "Refactor the internal batching pipeline.",
                skill_repo_root, issue=2001)

        self.assertEqual(delivered_a, delivered_b)
        self.assertEqual(mounted_a, mounted_b)
        self.assertEqual(mounted_a, [])
        self.assertNotIn("accessibility-aria-and-contrast-rules", delivered_a)


class ConsultJudgeStageTest(unittest.TestCase):
    """이슈 #2040: BM25 상위 후보를 skill_judge 자문에 넘기는 단계 —
    picked/rejected/reasons 트레이스 로깅과, 자문 에러시 BM25 top-k
    fail-open 을 검증한다."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        self.work = Path(self._tmpdir.name) / "work"
        self.work.mkdir()
        run = lambda *a: subprocess.run(a, cwd=str(self.work), capture_output=True,
                                        text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (self.work / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")

    def tearDown(self):
        self._tmpdir.cleanup()

    def _skill(self, name, use_sentence):
        d = self.repo_root / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            f"description: >-\n"
            f"  Intro text. {use_sentence}\n"
            "---\n\n# body\n", encoding="utf-8")
        return d

    def _trace_text(self, issue=2040):
        # issue #2333: 트레이스는 이제 세션별 샤드 파일에 있다 — 애그리게이터가
        # 재구성하는 오늘까지의 단일-뷰를 읽는다.
        return spawn._consult_log_aggregate(issue, cwd=str(self.work))

    def test_success_logs_picked_rejected_reasons_and_returns_picked_paths(self):
        picked_dir = self._skill(
            "accessibility-aria-and-contrast-rules",
            "Use when deciding an ARIA role for a landing page.")
        rejected_dir = self._skill(
            "model-routing",
            "Use this skill on EVERY non-trivial task in any domain.")
        candidates = [(picked_dir.name, picked_dir, "skill-repo"),
                      (rejected_dir.name, rejected_dir, "skill-repo")]
        session_json = json.dumps({"result": json.dumps({
            "picked": ["accessibility-aria-and-contrast-rules"],
            "rejected": [{"name": "model-routing",
                          "reason": "trigger is deliberately maximal, no condition match"}],
            "reasons": {"accessibility-aria-and-contrast-rules":
                        "task literally asks for ARIA role on a landing page"},
        })})
        with mock.patch.object(spawn, "_consult_cmd_and_env",
                               lambda role, spec, cwd, model, **kw: (["cat"], {}, None)), \
             mock.patch.object(spawn.subprocess, "run",
                               lambda *a, **k: subprocess.CompletedProcess(
                                   a, 0, stdout=session_json, stderr="")):
            picked, detail = spawn._skill_judge_consult(
                "Build a landing page and fix its ARIA role.", "implementation",
                candidates, 2040, str(self.work))
        self.assertEqual(picked, [picked_dir])
        self.assertEqual(detail["picked"], ["accessibility-aria-and-contrast-rules"])
        self.assertEqual(detail["rejected"][0]["name"], "model-routing")
        trace = self._trace_text()
        self.assertIn("verb=skill_judge", trace)
        self.assertIn("accessibility-aria-and-contrast-rules", trace)
        self.assertIn("model-routing", trace)
        # 이슈 #2124 (judge prompt diet): 후보 줄은 이름 + 트리거 문장만 —
        # #2055 의 소스 라벨은 판단 프롬프트에서 뺐다(트레이스에도 그
        # 다이어트된 질문 원문이 그대로 남는다).
        self.assertNotIn("[skill-repo]", trace)

    def test_consult_error_raises_and_still_traces(self):
        candidates = [("some-skill", self.repo_root / "some-skill", "skill-repo")]
        with mock.patch.object(spawn, "_consult_cmd_and_env",
                               lambda role, spec, cwd, model, **kw: (["cat"], {}, None)), \
             mock.patch.object(spawn.subprocess, "run",
                               lambda *a, **k: subprocess.CompletedProcess(
                                   a, 1, stdout="", stderr="boom")):
            with self.assertRaises(RuntimeError):
                spawn._skill_judge_consult(
                    "some task", "implementation", candidates, 2040, str(self.work))
        self.assertIn("verb=skill_judge", self._trace_text())

    def test_fail_open_to_bm25_topk_on_consult_error(self):
        d1 = self._skill("aaa-skill",
                         "Use when a landing page needs contrast accessible review.")
        d2 = self._skill("bbb-skill",
                         "Use when a landing page needs contrast accessible review.")
        with mock.patch.object(spawn, "_skill_judge_consult",
                               side_effect=RuntimeError("consult boom")):
            matches, outcome = spawn._cross_family_skill_matches_with_consult(
                "Build a landing page that needs contrast accessible review.",
                "implementation", self.repo_root, 2040, str(self.work), k=2)
        bm25_top2 = spawn._cross_family_skill_matches(
            "Build a landing page that needs contrast accessible review.",
            "implementation", self.repo_root, k=2)
        self.assertEqual(matches, bm25_top2)
        self.assertEqual(matches, [d1, d2])
        self.assertEqual(outcome, "fail-open")

    def test_no_bm25_candidates_skips_consult_entirely(self):
        self._skill("some-skill", "Use when deploying a widget frobnicator.")
        with mock.patch.object(spawn, "_skill_judge_consult") as m:
            matches, outcome = spawn._cross_family_skill_matches_with_consult(
                "Completely unrelated vocabulary here.", "implementation",
                self.repo_root, 2040, str(self.work))
        m.assert_not_called()
        self.assertEqual(matches, [])
        self.assertEqual(outcome, "no-candidates")


class FourSurfaceCandidateCorpusTest(unittest.TestCase):
    """이슈 #2055: `_bm25_cross_family_scores` 의 후보 코퍼스가 skill-repository
    하나가 아니라 네 소스(skill-repository/설치된 플러그인/`~/.claude/skills`/
    타깃 저장소 `.claude/skills`) 를 본다 — 각 tier 를 하나씩 심어(tier-seeded)
    BM25 스코어링과 source 라벨을 검증한다."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name) / "skill-repo"
        self.repo_root.mkdir()
        self.home = Path(self._tmpdir.name) / "home"
        self.home.mkdir()
        self.target_repo = Path(self._tmpdir.name) / "target"
        (self.target_repo / ".claude" / "skills").mkdir(parents=True)
        (self.home / ".claude" / "skills").mkdir(parents=True)
        self._plugin_install = Path(self._tmpdir.name) / "plugin-install"
        (self._plugin_install / "skills").mkdir(parents=True)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _skill(self, root, name, use_sentence):
        d = root / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            f"description: >-\n"
            f"  Intro text. {use_sentence}\n"
            "---\n\n# body\n", encoding="utf-8")
        return d

    def _installed_plugins_json(self):
        return json.dumps({"plugins": {"acme@marketplace": [
            {"installPath": str(self._plugin_install), "version": "1.0.0"}]}})

    def test_all_four_tiers_score_and_carry_source_label(self):
        d1 = self._skill(self.repo_root, "skill-repo-skill",
                         "Use when a landing page needs contrast review.")
        d2 = self._skill(self._plugin_install / "skills", "plugin-skill",
                         "Use when a landing page needs contrast review.")
        d3 = self._skill(self.home / ".claude" / "skills", "local-user-skill",
                         "Use when a landing page needs contrast review.")
        d4 = self._skill(self.target_repo / ".claude" / "skills", "local-repo-skill",
                         "Use when a landing page needs contrast review.")
        # 설치된 플러그인 인덱스는 `~/.claude/plugins/installed_plugins.json`
        # 을 직접 읽으므로, home 을 임시 디렉터리로 스왑하고 그 파일을 써둔다.
        plugins_json = self.home / ".claude" / "plugins" / "installed_plugins.json"
        plugins_json.parent.mkdir(parents=True, exist_ok=True)
        plugins_json.write_text(self._installed_plugins_json(), encoding="utf-8")
        with mock.patch.object(spawn.Path, "home", lambda: self.home):
            scored = spawn._bm25_cross_family_scores(
                "Build a landing page and review its contrast.", "implementation",
                self.repo_root, home=self.home, target_repo_root=self.target_repo)
        by_name = {name: (d, source) for _, name, d, source in scored}
        self.assertEqual(by_name["skill-repo-skill"], (d1, "skill-repo"))
        self.assertEqual(by_name["plugin-skill"], (d2, "plugin"))
        self.assertEqual(by_name["local-user-skill"], (d3, "local-user"))
        self.assertEqual(by_name["local-repo-skill"], (d4, "local-repo"))

    def test_same_name_two_tier_conflict_fails_closed_naming_both_sources(self):
        self._skill(self.repo_root, "dup-skill", "Use when reviewing code quality.")
        self._skill(self.home / ".claude" / "skills", "dup-skill",
                   "Use when a landing page needs contrast review.")
        with self.assertRaises(SystemExit) as ctx:
            spawn._cross_family_candidate_corpus(
                "implementation", self.repo_root, home=self.home,
                target_repo_root=self.target_repo)
        msg = str(ctx.exception)
        self.assertIn("dup-skill", msg)
        self.assertIn("skill-repo", msg)
        self.assertIn("local-user", msg)

    def test_same_name_identical_content_across_tiers_dedupes_without_fail_closed(self):
        # 실제 운영 환경에서는 `~/.claude/skills` 가 skill-repository 를 그대로
        # 미러링해두는 경우가 흔하다 — 내용이 같으면 fail-closed 가 아니라
        # 조용히 하나로 합쳐진다(어느 tier 를 골라도 채점 결과가 같다).
        self._skill(self.repo_root, "mirrored-skill", "Use when reviewing code quality.")
        self._skill(self.home / ".claude" / "skills", "mirrored-skill",
                   "Use when reviewing code quality.")
        corpus = spawn._cross_family_candidate_corpus(
            "implementation", self.repo_root, home=self.home,
            target_repo_root=self.target_repo)
        self.assertEqual(len([n for n, _, _ in corpus if n == "mirrored-skill"]), 1)

    def test_hooks_carrying_candidate_is_rejected_from_corpus(self):
        d = self._skill(self.home / ".claude" / "skills", "hooked-skill",
                        "Use when reviewing code quality.")
        (d / "hooks").mkdir()
        corpus = spawn._cross_family_candidate_corpus(
            "implementation", self.repo_root, home=self.home,
            target_repo_root=self.target_repo)
        self.assertEqual([n for n, _, _ in corpus if n == "hooked-skill"], [])

    def test_score_reaches_judge_question_labeled(self):
        d1 = self._skill(self.home / ".claude" / "skills", "local-user-skill",
                         "Use when a landing page needs contrast review.")
        candidates = [("local-user-skill", d1, "local-user")]
        session_json = json.dumps({"result": json.dumps({
            "picked": ["local-user-skill"], "rejected": [], "reasons": {}})})
        work = Path(self._tmpdir.name) / "work"
        work.mkdir()
        run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True,
                                        text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (work / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        captured = {}

        def fake_run(*a, **k):
            if "input" not in captured and k.get("input") is not None:
                captured["input"] = k.get("input")
            return subprocess.CompletedProcess(a, 0, stdout=session_json, stderr="")

        with mock.patch.object(spawn, "_consult_cmd_and_env",
                               lambda role, spec, cwd, model, **kw: (["cat"], {}, None)), \
             mock.patch.object(spawn.subprocess, "run", fake_run):
            spawn._skill_judge_consult(
                "landing page contrast", "implementation", candidates, 2055,
                str(work))
        # 이슈 #2124 (judge prompt diet): 이름 + 트리거 문장만 — #2055 의
        # 소스 라벨은 더 이상 판단 질문에 실리지 않는다.
        self.assertIn("local-user-skill", captured["input"])
        self.assertNotIn("[local-user]", captured["input"])

    def test_timing_over_four_tier_corpus_stays_within_budget(self):
        # 이슈 #2053 예산: 스폰당 cross_family 단계가 초 단위로 튀면 안
        # 된다 — 로컬 fs 읽기뿐인 네 tier 스코어링은 1초 안에 끝나야 한다.
        for i in range(20):
            self._skill(self.repo_root, f"skill-repo-{i}",
                       "Use when reviewing generic code quality issues.")
            self._skill(self.home / ".claude" / "skills", f"local-user-{i}",
                       "Use when reviewing generic code quality issues.")
        import time
        start = time.monotonic()
        spawn._bm25_cross_family_scores(
            "Review the code quality of this module.", "implementation",
            self.repo_root, home=self.home, target_repo_root=self.target_repo)
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main()
