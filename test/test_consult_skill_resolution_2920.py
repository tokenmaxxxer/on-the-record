"""이슈 #2920: consult 의 스킬 축 해석이 은퇴한 role 축(가족-접두어
컨벤션)을 통해 돌지 않고, `--skills`/`resolve_skill_source()`와 같은
정확한-이름 해석을 쓰는지 검증한다.

1. 실제 리프 스킬 이름은 `--skills` 가 마운트하는 것과 정확히 같은
   디렉터리를 마운트한다(`resolve_skill_source()`와 `resolve_consult_skill_source()`
   가 같은 이름에서 같은 skill_dirs 를 낸다).
2. retired role 이름(실제 디렉터리가 아니라 다른 스킬 이름의 접두어일
   뿐인 이름)은 더 이상 그 접두어를 공유하는 스킬 전체를 묶어 싣지
   않는다 — POLICY 베이스라인만 남고, 그 이름은 `"unresolved"` 에 그대로
   나타난다(silent empty mount 가 아니라 visible).
3. 콤마로 구분한 멀티 스킬 consult 가 지원된다 — `--skills a,b`와 같은
   문법.
4. 모르는 이름(오타/자유 형식 질문 문구)은 `sys.exit` 하지 않는다 —
   consult 의 인자는 자유 형식이라는 #2569 결정을 relitigate 하지 않는다.
5. hooks/ 를 든 스킬은 여전히 fail-closed(마운트 전 거부) — `--skills`
   검증을 약화하지 않는다.
6. judge 세션의 플러그인 선택(`_readonly_plugin_dirs()`)도 같은 정확한-
   이름 해석을 쓴다 — family-prefix 로 다른 스킬을 끌어오지 않는다.
7. `consult_cmd()`가 돌려주는 판단 JSON 자체에 마운트/미해결 스킬
   정보가 실려, 호출자가 stderr 로그나 트레이스 파일을 따로 열어보지
   않아도 empty-mount 상태를 본다.
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
import consult

consult._sp = spawn


class ConsultSkillResolutionParityTest(unittest.TestCase):
    def setUp(self):
        self._saved_static_policy_skills = spawn.skills._STATIC_POLICY_SKILLS
        spawn.skills._STATIC_POLICY_SKILLS = {"policy-skill"}
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        for name in ("policy-skill", "adversarial-review", "code-architecture",
                     "conformance-review-verdict-assignment",
                     "conformance-review-finding-record", "hooked-skill"):
            (self.repo_root / name).mkdir()
        (self.repo_root / "hooked-skill" / "hooks").mkdir()

    def tearDown(self):
        spawn.skills._STATIC_POLICY_SKILLS = self._saved_static_policy_skills
        self._tmpdir.cleanup()

    def test_real_leaf_skill_name_matches_skills_flag_resolution(self):
        via_consult = spawn.resolve_consult_skill_source(
            "adversarial-review", self.repo_root)
        via_skills = spawn.resolve_skill_source(
            "adversarial-review,policy-skill", self.repo_root)
        self.assertEqual(set(via_consult["skills"]), set(via_skills["skills"]))
        self.assertEqual(set(via_consult["skill_dirs"]), set(via_skills["skill_dirs"]))
        self.assertEqual(via_consult["unresolved"], [])

    def test_second_real_leaf_skill_name_also_matches(self):
        via_consult = spawn.resolve_consult_skill_source(
            "code-architecture", self.repo_root)
        self.assertIn("code-architecture", via_consult["skills"])
        self.assertIn("policy-skill", via_consult["skills"])
        self.assertEqual(via_consult["unresolved"], [])

    def test_retired_family_prefix_name_mounts_only_policy_and_is_unresolved(self):
        # "conformance-review" is not itself a directory -- only a shared
        # prefix of two real leaf skills. The retired
        # resolve_skill_family_source() used to scan for that prefix and
        # mount both; this must no longer happen.
        result = spawn.resolve_consult_skill_source(
            "conformance-review", self.repo_root)
        self.assertEqual(result["skills"], ["policy-skill"])
        self.assertNotIn("conformance-review-verdict-assignment", result["skills"])
        self.assertNotIn("conformance-review-finding-record", result["skills"])
        self.assertEqual(result["unresolved"], ["conformance-review"])

    def test_nonexistent_name_is_unresolved_not_fatal(self):
        result = spawn.resolve_consult_skill_source(
            "totally-bogus-xyz", self.repo_root)
        self.assertEqual(result["skills"], ["policy-skill"])
        self.assertEqual(result["unresolved"], ["totally-bogus-xyz"])

    def test_multi_skill_csv_consult_mounts_both(self):
        result = spawn.resolve_consult_skill_source(
            "adversarial-review,code-architecture", self.repo_root)
        self.assertIn("adversarial-review", result["skills"])
        self.assertIn("code-architecture", result["skills"])
        self.assertEqual(result["unresolved"], [])

    def test_mixed_resolved_and_unresolved_csv_reports_only_the_miss(self):
        result = spawn.resolve_consult_skill_source(
            "adversarial-review,conformance-review", self.repo_root)
        self.assertIn("adversarial-review", result["skills"])
        self.assertEqual(result["unresolved"], ["conformance-review"])

    def test_hooked_skill_still_fails_closed(self):
        with self.assertRaises(SystemExit):
            spawn.resolve_consult_skill_source("hooked-skill", self.repo_root)


class JudgeReadonlyPluginDirsNoFamilyExpansionTest(unittest.TestCase):
    """`_readonly_plugin_dirs()`(judge 세션의 플러그인 선택)도 같은
    정확한-이름 해석을 쓴다 -- family-prefix 로 다른 스킬을 안 끌어온다."""

    def setUp(self):
        self._saved_static_policy_skills = spawn.skills._STATIC_POLICY_SKILLS
        spawn.skills._STATIC_POLICY_SKILLS = {"policy-skill"}
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        for name in ("policy-skill", "conformance-review-verdict-assignment"):
            (self.repo_root / name).mkdir()
        self._saved_skill_repo_root = spawn._skill_repo_root
        spawn._skill_repo_root = lambda: self.repo_root
        self._saved_core_plugin_dirs = spawn.core_plugin_dirs
        spawn.core_plugin_dirs = lambda: []

    def tearDown(self):
        spawn.skills._STATIC_POLICY_SKILLS = self._saved_static_policy_skills
        spawn._skill_repo_root = self._saved_skill_repo_root
        spawn.core_plugin_dirs = self._saved_core_plugin_dirs
        self._tmpdir.cleanup()

    def test_retired_role_name_no_longer_pulls_in_family_members(self):
        out = spawn._readonly_plugin_dirs("conformance-review")
        names = [d.name for d in out]
        self.assertNotIn("conformance-review-verdict-assignment", names)
        self.assertIn("policy-skill", names)

    def test_exact_leaf_skill_name_mounts_itself(self):
        out = spawn._readonly_plugin_dirs("conformance-review-verdict-assignment")
        names = [d.name for d in out]
        self.assertIn("conformance-review-verdict-assignment", names)


class AppendConsultTraceMountedFieldTest(unittest.TestCase):
    """`_append_consult_trace()` 는 `mounted`/`unresolved` 를 안 넘기면
    이전과 바이트 단위로 같은 줄을 낸다(기존 skill_judge/judge 트레이스
    호출부가 안 건드려짐) -- 넘기면 그 정보가 durable 트레이스에 남는다,
    이전엔 stderr 의 `muster_skills=` 한 줄에만 있어 배경 fork 기본
    경로의 O_TRUNC 로그 파일이 다음 실행 전까지만 살아있었다."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.trace_path = Path(self._tmpdir.name) / "consult-log.md"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_no_mounted_or_unresolved_is_byte_identical_to_before(self):
        consult._append_consult_trace(
            self.trace_path, "2026-01-01T00:00:00+00:00", "some-skill", None,
            "a question", "ok: an answer")
        text = self.trace_path.read_text(encoding="utf-8")
        self.assertNotIn("mounted=", text)
        self.assertNotIn("unresolved=", text)

    def test_mounted_and_unresolved_appear_when_given(self):
        consult._append_consult_trace(
            self.trace_path, "2026-01-01T00:00:00+00:00", "some-skill", None,
            "a question", "ok: an answer",
            mounted="work-in-english", unresolved="some-skill")
        text = self.trace_path.read_text(encoding="utf-8")
        self.assertIn("mounted='work-in-english'", text)
        self.assertIn("unresolved='some-skill'", text)


class ConsultCmdSurfacesResolutionInVerdictTest(unittest.TestCase):
    """`consult_cmd()`가 돌려주는 판단 JSON 에 `skills_mounted`/
    `skills_unresolved` 가 실린다 — selector 가 어떤 스킬에도 안 맞아도
    호출자가 answer/confidence 와 같은 자리에서 그 사실을 본다."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.cwd = self._tmpdir.name
        self._saved_trace_path = consult._consult_trace_path
        self._saved_commit_trace = consult._sp._commit_consult_trace
        self._saved_cmd_and_env = consult._sp._consult_cmd_and_env
        consult._consult_trace_path = lambda issue, cwd=None: Path(self.cwd) / "trace.md"
        consult._sp._commit_consult_trace = lambda *a, **k: None

    def tearDown(self):
        consult._consult_trace_path = self._saved_trace_path
        consult._sp._commit_consult_trace = self._saved_commit_trace
        consult._sp._consult_cmd_and_env = self._saved_cmd_and_env
        self._tmpdir.cleanup()

    def _fake_env(self, mounted, unresolved):
        env = {}
        if mounted:
            env["MUSTER_SKILLS"] = mounted
        if unresolved:
            env["MUSTER_SKILLS_UNRESOLVED"] = unresolved
        return env

    def test_unresolved_selector_is_visible_on_the_returned_verdict(self):
        consult._sp._consult_cmd_and_env = (
            lambda skill, cwd, model, task_text=None, issue=None, **kw:
            (["cat"], self._fake_env("work-in-english", "conformance-review"), None))
        session_json = json.dumps({"result": json.dumps(
            {"answer": "some judgement", "confidence": "low", "caveats": []})})
        with mock.patch.object(
                consult.subprocess, "run",
                lambda *a, **k: subprocess.CompletedProcess(
                    a, 0, stdout=session_json, stderr="")):
            verdict = consult.consult_cmd("conformance-review", "a question", cwd=self.cwd)
        self.assertEqual(verdict["skills_mounted"], ["work-in-english"])
        self.assertEqual(verdict["skills_unresolved"], ["conformance-review"])

    def test_exact_skill_name_reports_no_unresolved(self):
        consult._sp._consult_cmd_and_env = (
            lambda skill, cwd, model, task_text=None, issue=None, **kw:
            (["cat"], self._fake_env("work-in-english,adversarial-review", ""), None))
        session_json = json.dumps({"result": json.dumps(
            {"answer": "some judgement", "confidence": "low", "caveats": []})})
        with mock.patch.object(
                consult.subprocess, "run",
                lambda *a, **k: subprocess.CompletedProcess(
                    a, 0, stdout=session_json, stderr="")):
            verdict = consult.consult_cmd("adversarial-review", "a question", cwd=self.cwd)
        self.assertEqual(set(verdict["skills_mounted"]),
                          {"work-in-english", "adversarial-review"})
        self.assertEqual(verdict["skills_unresolved"], [])


if __name__ == "__main__":
    unittest.main()
