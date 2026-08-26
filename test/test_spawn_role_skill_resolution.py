"""이슈 #1955 (이슈 #1758 phase 5 이행): role-source-allowlist/rulebook 해석
경로 은퇴 뒤 무조건적 skill-repo 해석의 acceptance 1-3 을 검증한다.

1. 모든 역할이 룰북 플러그인 디렉터리 없이(mount-layout), skill-repo
   가이던스 스킬만 붙는다 — "매핑 안 됨" 이라는 상태 자체가 더 이상
   없다.
2. 이름 모르는 스킬, 또는 hooks/ 를 들고 있는 스킬로 매핑되면
   워크스페이스/브랜치 전에 fail-closed.
3. 로스터 엔트리가 resolution_source(항상 skill-repo) +
   resolution_skills/resolution_skill_sha 를 싣는다.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class RoleSkillsResolutionTest(unittest.TestCase):
    """헬퍼 함수 단위 테스트: 매핑된 역할은 skill-repo 소스로 풀리는 정상
    경로 + 두 fail-closed 거절(모르는 이름, hooks/ 있는 스킬)."""

    def setUp(self):
        self._saved_role_skills = spawn._ROLE_SKILLS
        self.repo_tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tmpdir.name)
        (self.repo_root / "alpha").mkdir()
        (self.repo_root / "beta").mkdir()
        (self.repo_root / "hooked").mkdir()
        (self.repo_root / "hooked" / "hooks").mkdir()

    def tearDown(self):
        spawn._ROLE_SKILLS = self._saved_role_skills
        self.repo_tmpdir.cleanup()

    def test_mapped_role_resolves_to_skill_repo_source(self):
        spawn._ROLE_SKILLS = {"implementation": ["alpha", "beta"]}
        result = spawn.resolve_role_source("implementation", self.repo_root)
        self.assertEqual(result["source"], "skill-repo")
        self.assertEqual(result["skills"], ["alpha", "beta"])
        self.assertEqual(result["skill_dirs"],
                          [self.repo_root / "alpha", self.repo_root / "beta"])
        self.assertIsNotNone(result["skill_sha"])

    def test_role_absent_from_mapping_resolves_to_empty_skill_repo(self):
        # "매핑 안 된 역할"이라는 상태는 더 이상 없다 — 그냥 스킬 0개인
        # skill-repo 소스다(이슈 #1955: rulebook 소스로 떨어지는 경로 자체가
        # 없다).
        spawn._ROLE_SKILLS = {}
        result = spawn.resolve_role_source("implementation", self.repo_root)
        self.assertEqual(result, {"source": "skill-repo", "skill_dirs": [],
                                   "skills": [], "skill_sha": None})

    def test_missing_named_skill_exits_nonzero(self):
        spawn._ROLE_SKILLS = {"implementation": ["alpha", "ghost"]}
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolve_role_source("implementation", self.repo_root)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)

    def test_skill_with_hooks_dir_exits_nonzero(self):
        spawn._ROLE_SKILLS = {"implementation": ["hooked"]}
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolve_role_source("implementation", self.repo_root)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)


class MountLayoutTest(unittest.TestCase):
    """acceptance 1: 모든 역할은 룰북 --plugin-dir 도, 스킬 hooks/ 마운트도
    없다 — spawn_cmd 에 룰북 plugins 리스트가 아예 안 실린다(_spawn_one()
    은 항상 plugins=[] 를 넘긴다, 이슈 #1955)."""

    def setUp(self):
        self._saved_token = spawn._resolve_gh_token
        spawn._resolve_gh_token = lambda: None

    def tearDown(self):
        spawn._resolve_gh_token = self._saved_token

    def test_mapped_role_excludes_rulebook_plugin_dir(self):
        skill_dirs = [Path("/tmp/skill-repo/alpha")]
        cmd, env = spawn.spawn_cmd(
            "/tmp/settings.json", "implementation", False,
            core_plugins=[Path("/tmp/core")], plugins=[],
            model="sonnet", skill_dirs=skill_dirs,
            skill_repo_sha_value="abc1234")
        self.assertNotIn("/tmp/rulebook", cmd)
        self.assertIn(str(skill_dirs[0]), cmd)
        for d in skill_dirs:
            self.assertFalse((Path(d) / "hooks").is_dir())


class RefusalBeforeWorkspaceTest(unittest.TestCase):
    """acceptance 2: 역할이 모르는 스킬을 물거나(hooks/ 포함), 이름 자체가
    없으면 워크스페이스/브랜치 생성 전에 non-zero exit — 스텁으로
    issue_workspace()/checkout_issue_branch() 가 절대 안 불렸음을 증명."""

    def setUp(self):
        self._saved_role_skills = spawn._ROLE_SKILLS

        self.repo_tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tmpdir.name)
        (self.repo_root / "alpha").mkdir()
        (self.repo_root / "hooked").mkdir()
        (self.repo_root / "hooked" / "hooks").mkdir()

        self._saved_env = os.environ.pop("MUSTER_SKILL_REPO", None)
        os.environ["MUSTER_SKILL_REPO"] = str(self.repo_root)

        self._workspace_called = False
        self._branch_called = False

        def fake_workspace(*a, **k):
            self._workspace_called = True
            return "/tmp/should-not-be-created"

        def fake_branch(*a, **k):
            self._branch_called = True
            return "should-not-be-created"

        self._saved_workspace = spawn.issue_workspace
        self._saved_branch = spawn.checkout_issue_branch
        spawn.issue_workspace = fake_workspace
        spawn.checkout_issue_branch = fake_branch

        self.assertIn("implementation", spawn.role_data(),
                       "이 테스트는 실제 spawn_roles.json 의 implementation 스펙을 읽는다")

    def tearDown(self):
        spawn._ROLE_SKILLS = self._saved_role_skills
        spawn.issue_workspace = self._saved_workspace
        spawn.checkout_issue_branch = self._saved_branch
        if self._saved_env is None:
            os.environ.pop("MUSTER_SKILL_REPO", None)
        else:
            os.environ["MUSTER_SKILL_REPO"] = self._saved_env
        self.repo_tmpdir.cleanup()

    def test_missing_named_skill_exits_before_workspace(self):
        spawn._ROLE_SKILLS = {"implementation": ["alpha", "ghost"]}
        with self.assertRaises(SystemExit) as ctx:
            spawn._spawn_one(str(self.repo_root), "implementation", "task",
                              True, issue=1955)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)
        self.assertFalse(self._workspace_called)
        self.assertFalse(self._branch_called)

    def test_skill_with_hooks_exits_before_workspace(self):
        spawn._ROLE_SKILLS = {"implementation": ["hooked"]}
        with self.assertRaises(SystemExit) as ctx:
            spawn._spawn_one(str(self.repo_root), "implementation", "task",
                              True, issue=1955)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)
        self.assertFalse(self._workspace_called)
        self.assertFalse(self._branch_called)


class RecordFieldsTest(unittest.TestCase):
    """acceptance 3: 로스터 엔트리 shape — resolution_source 는 항상
    skill-repo, resolution_skills/resolution_skill_sha 를 늘 싣는다(매핑
    안 된 역할이라는 상태가 없으므로 rulebook 분기 자체가 없다)."""

    def setUp(self):
        self._saved_role_skills = spawn._ROLE_SKILLS
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        (self.repo_root / "alpha").mkdir()

    def tearDown(self):
        spawn._ROLE_SKILLS = self._saved_role_skills
        self._tmpdir.cleanup()

    def test_mapped_roster_fields(self):
        spawn._ROLE_SKILLS = {"implementation": ["alpha"]}
        role_source = spawn.resolve_role_source("implementation", self.repo_root)
        fields = spawn._role_source_roster_fields(role_source)
        self.assertEqual(fields["resolution_source"], "skill-repo")
        self.assertEqual(fields["resolution_skills"], ["alpha"])
        self.assertIsNotNone(fields["resolution_skill_sha"])

    def test_empty_state_no_mapping_still_skill_repo_shape(self):
        spawn._ROLE_SKILLS = {}
        role_source = spawn.resolve_role_source("implementation", self.repo_root)
        self.assertEqual(role_source["source"], "skill-repo")
        fields = spawn._role_source_roster_fields(role_source)
        self.assertEqual(fields, {"resolution_source": "skill-repo",
                                   "resolution_skills": [],
                                   "resolution_skill_sha": None})


if __name__ == "__main__":
    unittest.main()
