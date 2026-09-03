"""이슈 #2001/#2040: family 세트는 그대로 두고(add-only), 스폰 태스크 텍스트와
크로스-패밀리 스킬의 SKILL.md "Use ..." 트리거 문장을 BM25(이슈 #2040 —
raw 겹침-카운트 대체)로 채점해 상위 후보를 skill_judge 자문에 넘기고,
자문이 조건-매치로 고른 것만(최대 K=2) 추가로 마운트한다.

acceptance: 매치되는 태스크는 마운트 목록이 정확히 그 스킬만큼(최대 K=2)
늘고 디렉티브에도 실린다; 매치 안 되는 태스크는 마운트/디렉티브가 오늘과
바이트 단위로 동일하다 — 둘 다 라이브(serial, -o addopts='')로 검증한다.
"""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn

sys.path.insert(0, str((spawn.ROOT / "gates").resolve()))
import gh_rest


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

    def test_former_family_skill_now_matches_like_any_other_candidate(self):
        # implementation-blueprint used to live in the retired _ROLE_SKILLS
        # role->skill table (issue #2561) and was excluded from the
        # cross-family candidate pool on that basis. Issue #2507 (commit
        # 0879f12a) removed that exclusion outright: a fixed role->skill
        # table no longer defines "family", so there's no reason to narrow
        # the pool by role -- the corpus's only remaining filter is the
        # match itself. Same corpus, same query as the other single-skill
        # cases above: it now clears the BM25 floor and is returned.
        d = self._skill(
            "implementation-blueprint",
            "Use whenever you are about to produce non-trivial code "
            "spanning multiple modules landing pages contrast accessible.")
        matches = spawn._cross_family_skill_matches(
            "Build a landing page contrast accessible module.",
            "implementation", self.repo_root)
        self.assertEqual(matches, [d])

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
        delivery_calls = []

        def spy_roster_register(key, entry):
            roster_calls.append((key, dict(entry)))
            return real_roster_register(key, entry)

        def spy_spawn_cmd(settings, skill, unattended, core_plugins, plugins,
                          model, skill_dirs, skill_repo_sha_value, **kwargs):
            spawn_cmd_calls.append(list(skill_dirs))
            return (["cat"], {})

        def spy_launch_delivery(cwd, issue, skill, skills_csv, deferred_task_text):
            delivery_calls.append((cwd, issue, skill, skills_csv, deferred_task_text))

        skill_source = {"source": "skill-repo", "skill_dirs": [],
                       "skills": [], "skill_sha": None}

        # 이슈 #2040: 크로스-패밀리 선택이 이제 BM25 + skill_judge 자문을
        # 거친다 — 이 테스트들은 BM25 프리필터 자체(매치/비매치, 결정론)를
        # 검증하는 게 목적이라, 자문 단계는 "BM25 상위를 그대로 받아들인다"
        # 로 스텁해 오늘의 테스트 기대치(마운트 = BM25 top-k)를 그대로
        # 재사용한다. 자문 자체의 판단/트레이스/fail-open 동작은
        # ConsultJudgeStageTest 가 별도로 검증한다.
        # 이슈 #3230: `_spawn_one` 은 이제 이 스텁을 스스로는 절대 안
        # 부른다(디스패치 안에서 동기 호출이 없다) -- 그래도 남겨 둔다:
        # `spy_launch_delivery` 가 실제로 `_launch_cross_family_delivery`
        # 호출을 가로챈다는 것 자체가 이 스텁이 이제 죽은 코드라는 걸
        # 증명하는 역할도 한다(호출됐다면 delivery_calls 가 비어 있을 리
        # 없다).
        def stub_with_consult(task_text, skill, repo_root, issue, cwd, k=2, model=None,
                              home=None, target_repo_root=None, skills_csv=None):
            return (spawn._cross_family_skill_matches(task_text, skill, repo_root, k=k),
                    "completed")

        with mock.patch.object(spawn, "_cross_family_skill_matches_with_consult",
                               stub_with_consult), \
             mock.patch.object(spawn, "issue_workspace",
                               lambda cwd, issue, skill: str(work)), \
             mock.patch.object(spawn, "_checkout_named_branch",
                               lambda cwd, br: "b"), \
             mock.patch.object(spawn, "resolve_static_policy_source",
                               lambda repo_root: skill_source), \
             mock.patch.object(spawn, "_skill_repo_root",
                               lambda: skill_repo_root), \
             mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
             mock.patch.object(spawn, "core_version", lambda: "v0"), \
             mock.patch.object(spawn, "_clean_auto_enabled", lambda: False), \
             mock.patch.object(spawn, "spawn_cmd", spy_spawn_cmd), \
             mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
             mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
             mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
             mock.patch.object(spawn, "_undispositioned_skill_prs",
                               lambda root, exclude_issue=None: ([], True)), \
             mock.patch.object(spawn, "roster_register", spy_roster_register), \
             mock.patch.object(spawn, "ledger_write", lambda *a, **k: None), \
             mock.patch.object(spawn, "_launch_cross_family_delivery",
                               spy_launch_delivery), \
             mock.patch.object(gh_rest, "fetch_issue",
                               lambda repo, issue: {"body": task_text, "title": "t",
                                                     "owner": "acme", "repo": "widget"}):
            rc = spawn._spawn_one(str(work), "implementation", task_text,
                                  unattended=True, issue=issue, bounded=False,
                                  no_wait=True)
        self.assertEqual(rc, 0)
        log_path = roster_calls[-1][1]["log"]
        delivered = Path(log_path).read_text()
        return delivered, spawn_cmd_calls[-1], delivery_calls

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

    def test_matching_task_defers_the_match_to_delivery_instead_of_mounting_it(self):
        # 이슈 #3230: 매치되는 스킬이 있어도 디스패치 시점 마운트는 이제
        # 항상 비어 있다(fail-open, "nothing at all") -- 실제 판정은
        # `_launch_cross_family_delivery()` 에 위임돼 Popen 뒤 detached
        # 서브프로세스에서 돈다. 이 테스트가 예전에 검증하던 "매치되면
        # 그 자리에서 마운트된다"는 불변식은 의도적으로 사라졌다(라운드의
        # 설계 변경 그 자체) -- 대신 위임이 실제로 일어났는지(cwd/issue/
        # skill/task_text 가 맞는 인자로) 검증한다.
        with tempfile.TemporaryDirectory() as td, \
             tempfile.TemporaryDirectory() as skills_td:
            work = self._prep_repo(td)
            skill_repo_root = Path(skills_td)
            task_text = ("Redesign the landing page and fix its ARIA role "
                         "and contrast pair.")
            self._seed_cross_family_skill(skill_repo_root)
            delivered, mounted, delivery_calls = self._run(
                work, task_text, skill_repo_root, issue=2001)
        self.assertNotIn("accessibility-aria-and-contrast-rules", delivered)
        self.assertIn("스킬 판정 보류(이슈 #3230)", delivered)
        self.assertEqual(mounted, [])
        self.assertEqual(len(delivery_calls), 1)
        d_cwd, d_issue, d_skill, d_skills_csv, d_task_text = delivery_calls[0]
        self.assertEqual(d_cwd, str(work))
        self.assertEqual(d_issue, 2001)
        self.assertEqual(d_skill, "implementation")
        self.assertEqual(d_task_text, task_text)

    def test_non_matching_task_mounts_and_directive_byte_identical_to_baseline(self):
        with tempfile.TemporaryDirectory() as td_a, \
             tempfile.TemporaryDirectory() as td_b, \
             tempfile.TemporaryDirectory() as skills_td:
            skill_repo_root = Path(skills_td)
            self._seed_cross_family_skill(skill_repo_root)

            work_a = self._prep_repo(td_a, "work-a")
            delivered_a, mounted_a, _calls_a = self._run(
                work_a, "Refactor the internal batching pipeline.",
                skill_repo_root, issue=2001)

            work_b = self._prep_repo(td_b, "work-b")
            delivered_b, mounted_b, _calls_b = self._run(
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
                               lambda skill, cwd, model, **kw: (["cat"], {}, None)), \
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
                               lambda skill, cwd, model, **kw: (["cat"], {}, None)), \
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
        stderr = io.StringIO()
        with mock.patch.object(spawn, "_skill_judge_consult",
                               side_effect=RuntimeError("consult boom")), \
             contextlib.redirect_stderr(stderr):
            matches, outcome = spawn._cross_family_skill_matches_with_consult(
                "Build a landing page that needs contrast accessible review.",
                "implementation", self.repo_root, 2040, str(self.work), k=2)
        bm25_top2 = spawn._cross_family_skill_matches(
            "Build a landing page that needs contrast accessible review.",
            "implementation", self.repo_root, k=2)
        self.assertEqual(matches, bm25_top2)
        self.assertEqual(matches, [d1, d2])
        self.assertEqual(outcome, "fail-open")
        self.assertIn("skill_judge 자문 실패", stderr.getvalue())

    def test_no_bm25_candidates_skips_consult_entirely(self):
        self._skill("some-skill", "Use when deploying a widget frobnicator.")
        stderr = io.StringIO()
        with mock.patch.object(spawn, "_skill_judge_consult") as m, \
             contextlib.redirect_stderr(stderr):
            matches, outcome = spawn._cross_family_skill_matches_with_consult(
                "Completely unrelated vocabulary here.", "implementation",
                self.repo_root, 2040, str(self.work))
        m.assert_not_called()
        self.assertEqual(matches, [])
        self.assertEqual(outcome, "no-candidates")
        self.assertIn("skill_judge 자문 안 함", stderr.getvalue())

    def test_completed_outcome_prints_distinguishable_line(self):
        """이슈 #2679: fail-open 만 로그를 남기면 "이 줄이 없다"가 성공과
        not-invoked 둘 다를 뜻하게 된다 — 완료도 자기 줄을 낸다, 실패
        줄과 구분되는 문구로."""
        picked_dir = self._skill(
            "aaa-skill", "Use when a landing page needs contrast accessible review.")
        session_json = json.dumps({"result": json.dumps({
            "picked": ["aaa-skill"], "rejected": [], "reasons": {}})})
        stderr = io.StringIO()
        with mock.patch.object(spawn, "_consult_cmd_and_env",
                               lambda skill, cwd, model, **kw: (["cat"], {}, None)), \
             mock.patch.object(spawn.subprocess, "run",
                               lambda *a, **k: subprocess.CompletedProcess(
                                   a, 0, stdout=session_json, stderr="")), \
             contextlib.redirect_stderr(stderr):
            matches, outcome = spawn._cross_family_skill_matches_with_consult(
                "Build a landing page that needs contrast accessible review.",
                "implementation", self.repo_root, 2040, str(self.work), k=2)
        self.assertEqual(outcome, "completed")
        self.assertEqual(matches, [picked_dir])
        line = stderr.getvalue()
        self.assertIn("skill_judge 자문 완료", line)
        self.assertNotIn("자문 실패", line)
        self.assertNotIn("자문 안 함", line)

    def test_fast_path_fills_all_slots_prints_distinguishable_line(self):
        """이슈 #2679 (before-landing hunt finding): fast-path 만으로 k 슬롯이
        다 차면 판단(consult)을 아예 안 부르고 조용히 돌아왔다 —
        no-candidates 와 같은 "안 부름" 상태인데 자기 줄이 없었다."""
        self._skill(
            "exact-phrase-skill",
            'Use when the task says "please run the reproduction now" verbatim.')
        with mock.patch.object(spawn, "_skill_judge_consult") as m:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                matches, outcome = spawn._cross_family_skill_matches_with_consult(
                    "please run the reproduction now", "implementation",
                    self.repo_root, 2040, str(self.work), k=1)
        m.assert_not_called()
        self.assertEqual(outcome, "fast-path:exact-phrase-skill")
        line = stderr.getvalue()
        self.assertIn("skill_judge 자문 안 함", line)
        self.assertIn("fast-path", line)
        self.assertIn("슬롯이 다 참", line)

    def test_fast_path_partial_fill_with_no_remaining_candidates_prints(self):
        """이슈 #2679 send-back (독립 검증에서 재현): fast-path 가 슬롯 일부만
        채우고(remaining>0) BM25 후보 중 fast-path 픽을 뺀 나머지가 0개면
        `outcome_prefix` 가 있다는 이유로 print 가 통째로 건너뛰어졌다 —
        위 fast-path-fills-all-slots 갈래와 outcome 문자열 모양이 같은데
        (both "fast-path:<이름들>") 이 갈래만 조용했다."""
        self._skill(
            "exact-phrase-skill",
            'Use when the task says "please run the reproduction now" verbatim.')
        with mock.patch.object(spawn, "_skill_judge_consult") as m:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                matches, outcome = spawn._cross_family_skill_matches_with_consult(
                    "please run the reproduction now", "implementation",
                    self.repo_root, 2040, str(self.work), k=2)
        m.assert_not_called()
        self.assertEqual(outcome, "fast-path:exact-phrase-skill")
        line = stderr.getvalue()
        self.assertIn("skill_judge 자문 안 함", line)
        self.assertIn("fast-path", line)
        self.assertNotIn("슬롯이 다 참", line)
        self.assertIn("남은 BM25 후보 0개", line)


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

    def test_unqualified_name_with_diverging_tiers_still_fails_closed_when_pins_given(self):
        # 이슈 #3127 blocker A: `skills_csv` 에 다른 이름의 한정자가 있어도
        # (또는 아예 없어도) 한정자 없는 이름은 오늘과 동일하게 fail-closed
        # 로 남는다 — 완화는 명시적으로 소스를 지정한 이름에만 적용된다.
        self._skill(self.repo_root, "dup-skill", "Use when reviewing code quality.")
        self._skill(self.home / ".claude" / "skills", "dup-skill",
                   "Use when a landing page needs contrast review.")
        with self.assertRaises(SystemExit):
            spawn._cross_family_candidate_corpus(
                "implementation", self.repo_root, home=self.home,
                target_repo_root=self.target_repo,
                skills_csv="skill-repo:some-other-skill")

    def test_explicit_source_qualifier_pins_the_named_skill_and_skips_conflict(self):
        # 이슈 #3127 blocker A: `--skills skill-repo:dup-skill` 처럼 사용자가
        # 소스를 이미 명시했다면, 그 이름이 다른 tier(내용이 다른)에도
        # 걸려도 cross-family 코퍼스 빌드는 그걸 "겹침"으로 보지 않는다 —
        # 한정자가 가리키는 소스 하나로만 좁힌다(primary `--skills` 해석,
        # `resolved_skill_sources()` 의 `source_filter` 와 같은 규칙).
        d_repo = self._skill(self.repo_root, "dup-skill", "Use when reviewing code quality.")
        self._skill(self.home / ".claude" / "skills", "dup-skill",
                   "Use when a landing page needs contrast review.")
        corpus = spawn._cross_family_candidate_corpus(
            "implementation", self.repo_root, home=self.home,
            target_repo_root=self.target_repo,
            skills_csv="skill-repo:dup-skill")
        matches = [(name, d, source) for name, d, source in corpus if name == "dup-skill"]
        self.assertEqual(matches, [("dup-skill", d_repo, "skill-repo")])

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
                               lambda skill, cwd, model, **kw: (["cat"], {}, None)), \
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
