"""이슈 #2241 stage 0: `spawn.py --skill` — role 경로 옆에 추가한 skill 기반
호출 경로. role 경로는 이 스테이지에서 전혀 안 바뀐다(byte-identical) —
아래는 새 경로만 겨냥한다.

1. `resolve_skill_source()` 는 이름을 role→skill 표 없이 직접 해석한다.
2. role/skill 이 오늘 1:1 로 매핑되는 쌍에서 두 경로의 해석 결과가 같다.
3. role 이 없는 스킬도 skill 경로로는 풀린다(단순 role 리네임이 아님을 증명).
4. CLI(`main()`)에서 `--skill` 은 세션을 안 띄우고 해석 결과 JSON만 찍는다,
   verb 이름과 우연히 겹치는 태스크 문구도 오분기 없이 태스크로 읽힌다.
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class ResolveSkillSourceTest(unittest.TestCase):
    """`resolve_skill_source()` 단위 테스트 — `resolve_static_policy_source()`
    와 같은 반환 shape, 같은 fail-closed 규칙(모르는 이름, hooks/ 있는 스킬)."""

    def setUp(self):
        self.repo_tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tmpdir.name)
        (self.repo_root / "alpha").mkdir()
        (self.repo_root / "beta").mkdir()
        (self.repo_root / "gamma").mkdir()
        (self.repo_root / "hooked").mkdir()
        (self.repo_root / "hooked" / "hooks").mkdir()

    def tearDown(self):
        self.repo_tmpdir.cleanup()

    def test_resolves_named_skill_directly(self):
        result = spawn.resolve_skill_source("alpha", self.repo_root)
        self.assertEqual(result["source"], "skill-repo")
        self.assertEqual(result["skills"], ["alpha"])
        self.assertEqual(result["skill_dirs"], [self.repo_root / "alpha"])
        self.assertIsNotNone(result["skill_sha"])

    def test_resolves_comma_separated_names(self):
        result = spawn.resolve_skill_source("alpha,beta", self.repo_root)
        self.assertEqual(result["skills"], ["alpha", "beta"])

    def test_unknown_skill_name_exits_nonzero(self):
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolve_skill_source("ghost", self.repo_root)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)

    def test_skill_with_hooks_dir_exits_nonzero(self):
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolve_skill_source("hooked", self.repo_root)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)

    def test_skill_with_no_corresponding_role_still_resolves(self):
        # proposal acceptance: 새 경로가 role 리네임이 아니라는 증거 —
        # role 축 없는 정책 기준선(`_STATIC_POLICY_SKILLS`)에도 없는 이름이
        # skill 경로로는 풀린다.
        self.assertNotIn("gamma", spawn._STATIC_POLICY_SKILLS)
        result = spawn.resolve_skill_source("gamma", self.repo_root)
        self.assertEqual(result["skills"], ["gamma"])


class PolicySkillEquivalenceTest(unittest.TestCase):
    """이슈 #2561: role->skill 표 은퇴 뒤, role 축 없는 기준선
    (`resolve_static_policy_source()`)과 skill 경로(`resolve_skill_source()`)
    가 같은 이름에서 같은 해석 결과를 낸다."""

    def setUp(self):
        self._saved_static_policy_skills = spawn.skills._STATIC_POLICY_SKILLS
        self.repo_tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tmpdir.name)
        (self.repo_root / "alpha").mkdir()
        (self.repo_root / "beta").mkdir()

    def tearDown(self):
        spawn.skills._STATIC_POLICY_SKILLS = self._saved_static_policy_skills
        self.repo_tmpdir.cleanup()

    def test_policy_path_and_skill_path_agree_for_the_same_names(self):
        spawn.skills._STATIC_POLICY_SKILLS = {"alpha", "beta"}
        via_policy = spawn.resolve_static_policy_source(self.repo_root)
        via_skill = spawn.resolve_skill_source("alpha,beta", self.repo_root)
        self.assertEqual(via_policy["skills"], via_skill["skills"])
        self.assertEqual(via_policy["skill_dirs"], via_skill["skill_dirs"])
        self.assertEqual(via_policy["skill_sha"], via_skill["skill_sha"])
        self.assertEqual(via_policy["source"], via_skill["source"])


class SkillCliDispatchTest(unittest.TestCase):
    """`spawn.py --skill ... "<task>" --issue <n>` — 세션을 안 띄우고 해석
    결과만 찍는다. 기존 role 분기(`a.role == "init"` 등)와 우연히 겹치는
    태스크 문구도 오분기하지 않는다(이 분기가 role 분기들보다 먼저 검사돼야
    한다는 회귀 방지)."""

    def setUp(self):
        self.repo_tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tmpdir.name)
        (self.repo_root / "alpha").mkdir()
        self._saved_argv = sys.argv

    def tearDown(self):
        sys.argv = self._saved_argv
        self.repo_tmpdir.cleanup()

    def _run_main(self, argv_tail):
        sys.argv = ["spawn.py"] + argv_tail
        out = io.StringIO()
        with mock.patch.object(spawn, "_skill_repo_root", lambda: self.repo_root):
            with contextlib.redirect_stdout(out):
                rc = spawn.main()
        return rc, out.getvalue()

    def test_skill_flag_prints_resolution_without_spawning(self):
        with mock.patch.object(spawn, "checkout_issue_branch") as checkout, \
             mock.patch.object(spawn, "_spawn_one") as spawn_one:
            rc, out = self._run_main(
                ["--skill", "alpha", "do the thing", "--issue", "5"])
        self.assertEqual(rc, 0)
        checkout.assert_not_called()
        spawn_one.assert_not_called()
        payload = json.loads(out)
        self.assertEqual(payload["task"], "do the thing")
        self.assertEqual(payload["issue"], 5)
        self.assertEqual(payload["skills"], ["alpha"])
        self.assertEqual(payload["source"], "skill-repo")

    def test_task_text_colliding_with_a_role_verb_name_is_not_misrouted(self):
        # "init"/"ps"/... 는 role 경로에서 verb 로 특별 취급되는 문자열이다 —
        # `--skill` 경로에서는 그저 태스크 문구여야 한다.
        with mock.patch.object(spawn, "init_board") as init_board:
            rc, out = self._run_main(["--skill", "alpha", "init", "--issue", "5"])
        self.assertEqual(rc, 0)
        init_board.assert_not_called()
        payload = json.loads(out)
        self.assertEqual(payload["task"], "init")

    def test_missing_task_text_exits_nonzero(self):
        with self.assertRaises(SystemExit):
            self._run_main(["--skill", "alpha", "--issue", "5"])

    def test_whitespace_only_skill_value_exits_nonzero_not_false_success(self):
        # before-landing warrant hunt (이슈 #2241 stage 0): `--skill " "` 는
        # argparse 상 truthy 라 이 분기에 들어오지만, 쉼표로 쪼개면 남는
        # 이름이 없다 — `resolved_skill_dirs()`의 "이름 없으면 빈 목록"
        # 단축 경로를 그대로 타면 존재하지 않는 스킬 요청이 조용히
        # `skills: []` 성공으로 보인다. 빈 이름은 fail-closed 여야 한다.
        with self.assertRaises(SystemExit) as ctx:
            self._run_main(["--skill", " ", "do the thing", "--issue", "5"])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_comma_only_skill_value_exits_nonzero(self):
        with self.assertRaises(SystemExit):
            self._run_main(["--skill", ",,,", "do the thing", "--issue", "5"])


if __name__ == "__main__":
    unittest.main()
