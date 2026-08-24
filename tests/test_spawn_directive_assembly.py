"""이슈 #1978: --single-phase 신호 → CORE_BUILD_NOW=1 + 계약 문장 주입,
그리고 마운트된 스킬 이름 옆 "Use ..." 트리거 문장 인라인. 둘 다 신호/스킬이
없으면 오늘의 프롬프트/env 와 바이트 단위로 동일해야 한다.

이슈 #1981: `_spawn_one()` 의 조립된 디렉티브에는 체크포인트-커밋 문장이
들어가야 하고, `consult_cmd()`/`panel_cmd()` (커밋을 하지 않는 모드) 의
조립된 프롬프트에는 들어가면 안 된다."""
from _spawn_test_support import *  # noqa: F401,F403

_CHECKPOINT_COMMIT_MARKER = "체크포인트 커밋"


class DirectiveAssemblyBase(unittest.TestCase):
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

    def _run(self, work, role_source, captured_env, *, single_phase=False,
             issue=31, captured_spawn_cmd=None):
        roster_calls = []
        real_roster_register = spawn.roster_register

        def spy_roster_register(key, entry):
            roster_calls.append((key, dict(entry)))
            return real_roster_register(key, entry)

        real_popen = spawn.subprocess.Popen

        def spy_popen(cmd, **k):
            captured_env.update(k.get("env") or {})
            return real_popen(cmd, **k)

        # Issue #2204: spawn_cmd's kwargs (notably `append_system_prompt`)
        # carry the content that used to be an inline "Read <file>" pointer
        # in the stdin task text — callers that need to assert on it pass
        # a dict here instead of reading it out of `delivered`.
        def spy_spawn_cmd(*a, **k):
            if captured_spawn_cmd is not None:
                captured_spawn_cmd.update(k)
            return (["cat"], {})

        with mock.patch.object(spawn, "issue_workspace",
                               lambda cwd, issue, role: str(work)), \
             mock.patch.object(spawn, "checkout_issue_branch",
                               lambda cwd, issue, role: "b"), \
             mock.patch.object(spawn, "resolve_role_source",
                               lambda role, repo_root: role_source), \
             mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
             mock.patch.object(spawn, "core_version", lambda: "v0"), \
             mock.patch.object(spawn, "_clean_auto_enabled", lambda: False), \
             mock.patch.object(spawn, "spawn_cmd", spy_spawn_cmd), \
             mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
             mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
             mock.patch.object(spawn.subprocess, "Popen", spy_popen), \
             mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
             mock.patch.object(spawn, "_undispositioned_role_prs",
                               lambda root, exclude_issue=None: ([], True)), \
             mock.patch.object(spawn, "roster_register", spy_roster_register), \
             mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
            rc = spawn._spawn_one(str(work), "implementation", "원래 맡긴 일.\n",
                                  unattended=True, issue=issue, bounded=False,
                                  no_wait=True, single_phase=single_phase)
        self.assertEqual(rc, 0)
        log_path = roster_calls[-1][1]["log"]
        return Path(log_path).read_text()

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


_NO_SKILLS = {"source": "skill-repo", "skill_dirs": [], "skills": [],
              "skill_sha": None}


class SinglePhaseSignal(DirectiveAssemblyBase):
    @pytest.mark.slow
    def test_flag_produces_contract_line_and_core_build_now(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            env = {}
            delivered = self._run(work, _NO_SKILLS, env, single_phase=True)
        self.assertIn("Build-now bypass (contract v3 s19a)", delivered)
        self.assertIn("CORE_BUILD_NOW=1, set by the spawner, never by you", delivered)
        self.assertIn("skip the proposal round and deliver directly", delivered)
        self.assertEqual(env.get("CORE_BUILD_NOW"), "1")

    @pytest.mark.slow
    def test_without_flag_is_byte_identical_to_today(self):
        with tempfile.TemporaryDirectory() as td_a, \
             tempfile.TemporaryDirectory() as td_b:
            work_a = self._prep_repo(td_a)
            env_a = {}
            delivered_signal_off = self._run(work_a, _NO_SKILLS, env_a,
                                             single_phase=False)
        self.assertNotIn("Build-now bypass", delivered_signal_off)
        self.assertNotIn("CORE_BUILD_NOW", env_a)

        # 재실행 — 두 번 모두 신호 없이 만든 디렉티브가 바이트 단위로 같다.
        with tempfile.TemporaryDirectory() as td_c:
            work_c = self._prep_repo(td_c)
            env_c = {}
            delivered_again = self._run(work_c, _NO_SKILLS, env_c,
                                        single_phase=False, issue=31)
        self.assertEqual(delivered_signal_off, delivered_again)


class SkillTriggerLines(DirectiveAssemblyBase):
    def _skill_dir_with_trigger(self, root: Path) -> Path:
        d = root / "implementation-blueprint"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\n"
            "name: implementation-blueprint\n"
            "description: >-\n"
            "  Situational code-architecture selection. Use whenever you are\n"
            "  about to produce non-trivial code spanning multiple modules.\n"
            "---\n\n# blueprint\n", encoding="utf-8")
        return d

    def _skill_dir_without_description(self, root: Path) -> Path:
        d = root / "no-trigger-skill"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\nname: no-trigger-skill\n---\n\n# body\n", encoding="utf-8")
        return d

    @pytest.mark.slow
    def test_mounted_skill_directive_contains_name_and_trigger_line(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            skill_dir = self._skill_dir_with_trigger(Path(td) / "skills")
            role_source = {"source": "skill-repo", "skill_dirs": [skill_dir],
                           "skills": ["implementation-blueprint"], "skill_sha": "abc123"}
            delivered = self._run(work, role_source, {})
        self.assertIn("implementation-blueprint", delivered)
        self.assertIn(
            "Use whenever you are about to produce non-trivial code "
            "spanning multiple modules.", delivered)

    @pytest.mark.slow
    def test_skill_with_no_trigger_line_is_still_listed_by_name(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            skill_dir = self._skill_dir_without_description(Path(td) / "skills")
            role_source = {"source": "skill-repo", "skill_dirs": [skill_dir],
                           "skills": ["no-trigger-skill"], "skill_sha": "abc123"}
            delivered = self._run(work, role_source, {})
        self.assertIn("no-trigger-skill", delivered)

    @pytest.mark.slow
    def test_zero_mounted_skills_directive_unchanged(self):
        with tempfile.TemporaryDirectory() as td_a, \
             tempfile.TemporaryDirectory() as td_b:
            work_a = self._prep_repo(td_a, "work-a")
            delivered_a = self._run(work_a, _NO_SKILLS, {})
            work_b = self._prep_repo(td_b, "work-b")
            delivered_b = self._run(work_b, _NO_SKILLS, {})
        self.assertEqual(delivered_a, delivered_b)
        self.assertNotIn("Use ", delivered_a)


class SkillVerdictObligationLine(SkillTriggerLines):
    """issue #2039: next to the mounted-skill list, the directive must
    state the per-mounted-skill skill-verdict obligation — and stay
    silent (byte-unaffected) when no skill is mounted."""

    @pytest.mark.slow
    def test_mounted_skill_directive_states_verdict_obligation(self):
        # Issue #2135 diet: the inline text is the condensed obligation
        # index; the full #2039 prose is materialized as a workspace file.
        # Issue #2204: no inline "Read <file>" pointer any more — the full
        # prose instead rides --append-system-prompt (zero Read round
        # trips), still backed by the same workspace file for reference.
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            skill_dir = self._skill_dir_with_trigger(Path(td) / "skills")
            role_source = {"source": "skill-repo", "skill_dirs": [skill_dir],
                           "skills": ["implementation-blueprint"], "skill_sha": "abc123"}
            captured = {}
            delivered = self._run(work, role_source, {},
                                  captured_spawn_cmd=captured)
            section = (work / ".on-the-record" / "directive"
                       / "skill-obligations.md").read_text(encoding="utf-8")
        self.assertIn("skill-verdict:", delivered)
        self.assertIn("applied:", delivered)
        self.assertIn("not-applicable:", delivered)
        self.assertNotIn(".on-the-record/directive/skill-obligations.md",
                         delivered)
        system_prompt = captured["append_system_prompt"]
        self.assertIn("스킬-verdict 의무(이슈 #2039)", system_prompt)
        self.assertIn("정확히 하나씩 남겨야 한다", system_prompt)
        self.assertIn("스킬-verdict 의무(이슈 #2039)", section)
        self.assertIn("정확히 하나씩 남겨야 한다", section)

    @pytest.mark.slow
    def test_zero_mounted_skills_directive_omits_verdict_obligation(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            delivered = self._run(work, _NO_SKILLS, {})
        self.assertNotIn("스킬-verdict 의무", delivered)
        self.assertNotIn("skill-verdict:", delivered)


class InvokeBeforeApplyObligation(SkillTriggerLines):
    """issue #2062: next to the mounted-skill list, the directive must
    state that an APPLICABLE skill has to be invoked via the Skill tool
    (loading its full SKILL.md) before it is applied, and the
    skill-verdict obligation text must require an invocation marker on
    applied: lines — silent (byte-unaffected) when no skill is mounted."""

    @pytest.mark.slow
    def test_mounted_skill_directive_states_invoke_before_apply(self):
        # Issue #2135 diet: full #2062 prose in the workspace section file;
        # the inline index keeps the invocation-marker invariant.
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            skill_dir = self._skill_dir_with_trigger(Path(td) / "skills")
            role_source = {"source": "skill-repo", "skill_dirs": [skill_dir],
                           "skills": ["implementation-blueprint"], "skill_sha": "abc123"}
            delivered = self._run(work, role_source, {})
            section = (work / ".on-the-record" / "directive"
                       / "skill-obligations.md").read_text(encoding="utf-8")
        self.assertIn("invoked;", delivered)
        self.assertIn("invoke-before-apply(이슈 #2062)", section)
        self.assertIn("SKILL.md 를 로드해야 한다", section)

    @pytest.mark.slow
    def test_zero_mounted_skills_directive_omits_invoke_before_apply(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            delivered = self._run(work, _NO_SKILLS, {})
        self.assertNotIn("invoke-before-apply", delivered)
        self.assertNotIn("invoked;", delivered)


class ArtifactSmokeCoInjection(DirectiveAssemblyBase):
    """issue #2073: the spawn task gains at most two conditional lines,
    derived from the issue body already in hand (no new fetch) — an
    artifact-smoke trigger when `runtime-artifacts:` is declared (or the
    advisory scorer fires with no declaration), and a live-screen
    verification line when the issue is design-bearing with a declared
    storyboard. Absent both conditions the returned text is empty, so the
    assembled task is byte-identical to today's."""

    def test_declared_runtime_artifacts_produce_the_trigger_line(self):
        body = "runtime-artifacts:\n- dist/bundle.js\n- dist/index.html\n"
        out = spawn._artifact_smoke_task_lines(body)
        self.assertIn("ARTIFACT-SMOKE(이슈 #2073)", out)
        self.assertIn("dist/bundle.js", out)
        self.assertIn("dist/index.html", out)
        self.assertIn("docs/specs/artifact-smoke-contract.md", out)
        self.assertNotIn("VISUAL-VERIFICATION", out)

    def test_design_bearing_storyboard_produces_the_verification_line(self):
        body = ("design-bearing-override: yes\n\n"
                "design-artifacts:\n- assets/storyboard.md\n")
        out = spawn._artifact_smoke_task_lines(body)
        self.assertIn("VISUAL-VERIFICATION(이슈 #2073)", out)
        self.assertIn("screen-verified:", out)
        self.assertIn("assets/storyboard.md", out)
        self.assertNotIn("ARTIFACT-SMOKE", out)

    def test_both_conditions_produce_both_lines(self):
        body = ("runtime-artifacts:\n- dist/bundle.js\n\n"
                "design-bearing-override: yes\n\n"
                "design-artifacts:\n- assets/storyboard.md\n")
        out = spawn._artifact_smoke_task_lines(body)
        self.assertIn("ARTIFACT-SMOKE(이슈 #2073)", out)
        self.assertIn("VISUAL-VERIFICATION(이슈 #2073)", out)

    def test_design_bearing_without_a_storyboard_stays_silent(self):
        body = ("design-bearing-override: yes\n\n"
                "design-artifacts:\n- assets/user-flow.md\n")
        self.assertEqual(spawn._artifact_smoke_task_lines(body), "")

    def test_storyboard_without_design_bearing_stays_silent(self):
        body = ("design-bearing-override: no\n\n"
                "design-artifacts:\n- assets/storyboard.md\n")
        self.assertEqual(spawn._artifact_smoke_task_lines(body), "")

    def test_mechanical_issue_body_is_byte_identical(self):
        for body in ("게이트 하나를 고친다.\n", "", None):
            self.assertEqual(spawn._artifact_smoke_task_lines(body), "")

    def test_undeclared_but_artifact_smelling_body_gets_the_advisory_line(self):
        body = ("이 이슈는 browser 로 여는 generated single-file bundle 을 "
                "dist/ 아래에 배송한다.\n")
        out = spawn._artifact_smoke_task_lines(body)
        self.assertIn("ARTIFACT-SMOKE(이슈 #2073)", out)
        self.assertIn("`runtime-artifacts:` 선언이 없다", out)

    @pytest.mark.slow
    def test_assembled_directive_is_unchanged_when_the_body_is_unavailable(self):
        """gh 조회가 안 되는(=body None) 스폰에서는 이 블록이 아무 것도
        붙이지 않는다 — 조립된 과제가 오늘과 바이트 단위로 같다."""
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            delivered = self._run(work, _NO_SKILLS, {})
        self.assertNotIn("ARTIFACT-SMOKE", delivered)
        self.assertNotIn("VISUAL-VERIFICATION", delivered)


class SkillTriggerLineHelper(unittest.TestCase):
    def test_extracts_use_sentence_from_folded_description(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "s"
            d.mkdir()
            (d / "SKILL.md").write_text(
                "---\nname: s\ndescription: >-\n"
                "  Some intro text. Use whenever X happens or Y is true.\n"
                "---\n", encoding="utf-8")
            self.assertEqual(spawn._skill_trigger_line(d),
                             "Use whenever X happens or Y is true.")

    def test_returns_none_when_no_use_sentence(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "s"
            d.mkdir()
            (d / "SKILL.md").write_text(
                "---\nname: s\ndescription: just some text.\n---\n",
                encoding="utf-8")
            self.assertIsNone(spawn._skill_trigger_line(d))

    def test_returns_none_when_no_skill_md(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(spawn._skill_trigger_line(Path(td)))


class CheckpointCommitDirectiveLine(DirectiveAssemblyBase):
    """이슈 #1981: 검증부터 하고 나중에 커밋하는 습관이 세션을 좌초시킨
    사고(#1959 s2, #1978 ph2) 를 뒤집는 체크포인트-커밋 규칙 한 줄."""

    @pytest.mark.slow
    def test_spawn_one_directive_contains_checkpoint_commit_line(self):
        # Issue #2204: the rule's full prose (검증/amend detail) no longer
        # has an inline "Read <file>" pointer in the stdin task — it rides
        # --append-system-prompt (zero Read round trips) instead, still
        # backed by the same workspace section file for reference.
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            captured = {}
            self._run(work, _NO_SKILLS, {}, captured_spawn_cmd=captured)
            section = (work / ".on-the-record" / "directive"
                       / "completion-and-landing.md").read_text(encoding="utf-8")
        system_prompt = captured["append_system_prompt"]
        self.assertIn(_CHECKPOINT_COMMIT_MARKER, system_prompt)
        self.assertIn("검증", system_prompt)
        self.assertIn(_CHECKPOINT_COMMIT_MARKER, section)
        self.assertIn("검증", section)
        self.assertIn("amend", section)


class CheckpointCommitAbsentFromNoCommitModes(unittest.TestCase):
    """자문(consult)/패널(panel) 은 커밋을 하지 않는 별도 조립 경로다 —
    체크포인트-커밋 문장이 여기 새어들면 안 된다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self._patches = []
        self._patch(spawn, "resolve_role_source",
                    lambda role, repo_root: {"source": "skill-repo",
                        "skill_dirs": [Path("/fake/plugin")],
                        "skills": ["fake"], "skill_sha": "abc1234"})
        self._patch(spawn, "core_plugin_dirs", lambda: [])
        root = self.root
        self._patch(spawn, "_consult_trace_path",
                    lambda issue, cwd=None: (root / "docs" / f"issue-{issue}" / "reports" / "consult-log.md"
                                   if issue is not None else root / "docs" / "consult-log.md"))

    def _patch(self, obj, name, value):
        orig = getattr(obj, name)
        setattr(obj, name, value)
        self._patches.append((obj, name, orig))
        self.addCleanup(lambda: setattr(obj, name, orig))

    def test_consult_cmd_prompt_omits_checkpoint_commit_line(self):
        captured_prompts = []
        real_run = spawn.subprocess.run

        def spy_run(cmd, **kw):
            captured_prompts.append(kw.get("input"))
            verdict_json = ('괜찮다.\n'
                             '{"answer": "괜찮다", "confidence": "medium", "caveats": []}')
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout=json.dumps({"result": verdict_json, "is_error": False}),
                stderr="")

        self._patch(spawn.subprocess, "run", spy_run)
        spawn.consult_cmd("implementation", "질문", cwd=str(self.root))
        prompts = [p for p in captured_prompts if p]
        self.assertTrue(prompts)
        for prompt in prompts:
            self.assertNotIn(_CHECKPOINT_COMMIT_MARKER, prompt)

    def test_run_panel_session_prompt_omits_checkpoint_commit_line(self):
        """`panel_cmd()` 기본 launcher `_run_panel_session()` 이 조립하는
        프롬프트도 커밋을 하지 않는 판정 세션이므로 체크포인트-커밋 문장이
        새어들면 안 된다."""
        captured_prompts = []

        def spy_run(cmd, **kw):
            captured_prompts.append(kw.get("input"))
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout=json.dumps({"type": "result", "result":
                    '{"answer": "ok", "confidence": "medium", "caveats": []}'}) + "\n",
                stderr="")

        self._patch(spawn.subprocess, "run", spy_run)
        self._patch(spawn, "role_settings", lambda role, cwd=None, **k: {})
        spawn._run_panel_session("implementation", "requirements-engineering",
                                 "질문", str(self.root))
        self.assertTrue(captured_prompts)
        for prompt in captured_prompts:
            self.assertNotIn(_CHECKPOINT_COMMIT_MARKER, prompt)
