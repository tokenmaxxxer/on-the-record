"""이슈 #1758 (skill-axis 프로그램 phase 3/4 mechanism): 전이용
role-source-allowlist 매핑의 acceptance 1-3 을 검증한다.

1. 매핑된 역할은 룰북 플러그인 디렉터리 없이(mount-layout), skill-repo
   가이던스 스킬만 붙는다 — 매핑 안 된 역할은 argv/env 가 이전과
   byte-identical.
2. 이름 모르는 스킬, 또는 hooks/ 를 들고 있는 스킬로 매핑되면
   워크스페이스/브랜치 전에 fail-closed.
3. 로스터 엔트리가 resolution_source(항상) + resolution_skills/
   resolution_skill_sha(매핑) 또는 resolution_rulebook_sha(비매핑) 를 싣는다.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class RoleSourceAllowlistTest(unittest.TestCase):
    """헬퍼 함수 단위 테스트: 파일 부재 = 빈 매핑, 매핑 안 된 역할은
    rulebook 소스로 값이 못박힌다."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_absent_file_returns_empty_mapping(self):
        self.assertEqual(spawn._role_source_allowlist(self.root), {})

    def test_present_file_returns_parsed_mapping(self):
        specs = self.root / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "role-source-allowlist.json").write_text(
            json.dumps({"implementation": ["alpha"]}))
        self.assertEqual(spawn._role_source_allowlist(self.root),
                          {"implementation": ["alpha"]})

    def test_unmapped_role_resolves_to_rulebook_source(self):
        result = spawn.resolve_role_source("implementation", self.root, None)
        self.assertEqual(result, {"source": "rulebook", "skill_dirs": [],
                                   "skills": [], "skill_sha": None})

    def test_empty_allowlist_file_resolves_to_rulebook_source(self):
        specs = self.root / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "role-source-allowlist.json").write_text("{}")
        result = spawn.resolve_role_source("implementation", self.root, None)
        self.assertEqual(result["source"], "rulebook")


class MappedRoleResolutionTest(unittest.TestCase):
    """매핑된 역할이 skill-repo 소스로 풀리는 정상 경로 + 두 fail-closed
    거절(모르는 이름, hooks/ 있는 스킬)."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        specs = self.root / "docs" / "specs"
        specs.mkdir(parents=True)
        self.allowlist_path = specs / "role-source-allowlist.json"

        self.repo_tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tmpdir.name)
        (self.repo_root / "alpha").mkdir()
        (self.repo_root / "beta").mkdir()
        (self.repo_root / "hooked").mkdir()
        (self.repo_root / "hooked" / "hooks").mkdir()

    def tearDown(self):
        self._tmpdir.cleanup()
        self.repo_tmpdir.cleanup()

    def _write_allowlist(self, mapping):
        self.allowlist_path.write_text(json.dumps(mapping))

    def test_mapped_role_resolves_to_skill_repo_source(self):
        self._write_allowlist({"implementation": ["alpha", "beta"]})
        result = spawn.resolve_role_source(
            "implementation", self.root, self.repo_root)
        self.assertEqual(result["source"], "skill-repo")
        self.assertEqual(result["skills"], ["alpha", "beta"])
        self.assertEqual(result["skill_dirs"],
                          [self.repo_root / "alpha", self.repo_root / "beta"])
        self.assertIsNotNone(result["skill_sha"])

    def test_missing_named_skill_exits_nonzero(self):
        self._write_allowlist({"implementation": ["alpha", "ghost"]})
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolve_role_source("implementation", self.root, self.repo_root)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)

    def test_skill_with_hooks_dir_exits_nonzero(self):
        self._write_allowlist({"implementation": ["hooked"]})
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolve_role_source("implementation", self.root, self.repo_root)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)


class MountLayoutTest(unittest.TestCase):
    """acceptance 1: 매핑된 역할은 룰북 --plugin-dir 도, 스킬 hooks/ 마운트도
    없다; 매핑 안 된 역할은 --skills 없이도 있이도 이전(#1742)과 argv/env가
    byte-identical."""

    def setUp(self):
        self._saved_token = spawn._resolve_gh_token
        spawn._resolve_gh_token = lambda: None

    def tearDown(self):
        spawn._resolve_gh_token = self._saved_token

    def test_mapped_role_excludes_rulebook_plugin_dir(self):
        # skill-repo 소스로 풀린 경우 spawn_cmd 에 룰북 plugins 리스트가
        # 아예 안 실린다 — _spawn_one() 은 mapped 일 때 plugins=[] 를 넘긴다.
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

    def test_unmapped_role_argv_env_byte_identical_to_pre_1758(self):
        # 매핑 안 된 역할: resolve_role_source() 가 빈 skill_dirs 를 주므로
        # all_skill_dirs == 기존 --skills 만의 skill_dirs 와 값이 같다 —
        # spawn_cmd() 입력이 이전(#1742)과 동일해 argv/env 가 그대로다.
        cmd_pre1758, env_pre1758 = spawn.spawn_cmd(
            "/tmp/settings.json", "implementation", False,
            core_plugins=[Path("/tmp/core")], plugins=[Path("/tmp/rulebook")],
            model="sonnet", skill_dirs=[], skill_repo_sha_value=None)
        with tempfile.TemporaryDirectory() as root_dir:
            role_source = spawn.resolve_role_source(
                "implementation", Path(root_dir), None)
        skill_dirs = []
        all_skill_dirs = list(skill_dirs) + [
            d for d in role_source["skill_dirs"] if d not in skill_dirs]
        cmd_1758, env_1758 = spawn.spawn_cmd(
            "/tmp/settings.json", "implementation", False,
            core_plugins=[Path("/tmp/core")], plugins=[Path("/tmp/rulebook")],
            model="sonnet", skill_dirs=all_skill_dirs,
            skill_repo_sha_value=None or role_source["skill_sha"])
        self.assertEqual(cmd_pre1758, cmd_1758)
        self.assertEqual(env_pre1758, env_1758)


class RefusalBeforeWorkspaceTest(unittest.TestCase):
    """acceptance 2: 매핑된 역할이 모르는 스킬을 물거나(hooks/ 포함), 이름
    자체가 없으면 워크스페이스/브랜치 생성 전에 non-zero exit — 스텁으로
    issue_workspace()/checkout_issue_branch() 가 절대 안 불렸음을 증명."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        specs = self.root / "docs" / "specs"
        specs.mkdir(parents=True)
        self.allowlist_path = specs / "role-source-allowlist.json"

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

        role_spec_path = spawn.ROOT / "roles" / "implementation.json"
        self.assertTrue(role_spec_path.is_file(),
                         "이 테스트는 실제 roles/implementation.json 스펙을 읽는다")

    def tearDown(self):
        spawn.issue_workspace = self._saved_workspace
        spawn.checkout_issue_branch = self._saved_branch
        if self._saved_env is None:
            os.environ.pop("MUSTER_SKILL_REPO", None)
        else:
            os.environ["MUSTER_SKILL_REPO"] = self._saved_env
        self._tmpdir.cleanup()
        self.repo_tmpdir.cleanup()

    def _write_allowlist(self, mapping):
        self.allowlist_path.write_text(json.dumps(mapping))

    def test_missing_named_skill_exits_before_workspace(self):
        self._write_allowlist({"implementation": ["alpha", "ghost"]})
        with self.assertRaises(SystemExit) as ctx:
            spawn._spawn_one(str(self.root), "implementation", "task", True,
                              issue=1758)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)
        self.assertFalse(self._workspace_called)
        self.assertFalse(self._branch_called)

    def test_skill_with_hooks_exits_before_workspace(self):
        self._write_allowlist({"implementation": ["hooked"]})
        with self.assertRaises(SystemExit) as ctx:
            spawn._spawn_one(str(self.root), "implementation", "task", True,
                              issue=1758)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)
        self.assertFalse(self._workspace_called)
        self.assertFalse(self._branch_called)


class RecordFieldsTest(unittest.TestCase):
    """acceptance 3: 로스터 엔트리 shape — resolution_source 는 항상 있고,
    매핑 여부로 나머지 필드가 갈린다(빈 상태: 매핑 파일 부재 -> rulebook)."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        (self.repo_root / "alpha").mkdir()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_unmapped_roster_fields(self):
        with tempfile.TemporaryDirectory() as root_dir:
            role_source = spawn.resolve_role_source(
                "implementation", Path(root_dir), None)
        fields = spawn._role_source_roster_fields(role_source, "abc1234")
        self.assertEqual(fields, {"resolution_source": "rulebook",
                                   "resolution_rulebook_sha": "abc1234"})

    def test_mapped_roster_fields(self):
        with tempfile.TemporaryDirectory() as root_dir:
            root = Path(root_dir)
            specs = root / "docs" / "specs"
            specs.mkdir(parents=True)
            (specs / "role-source-allowlist.json").write_text(
                json.dumps({"implementation": ["alpha"]}))
            role_source = spawn.resolve_role_source(
                "implementation", root, self.repo_root)
        fields = spawn._role_source_roster_fields(role_source, "unused")
        self.assertEqual(fields["resolution_source"], "skill-repo")
        self.assertEqual(fields["resolution_skills"], ["alpha"])
        self.assertIsNotNone(fields["resolution_skill_sha"])

    def test_empty_state_absent_mapping_file_matches_rulebook_shape(self):
        with tempfile.TemporaryDirectory() as root_dir:
            role_source = spawn.resolve_role_source(
                "implementation", Path(root_dir), None)
        self.assertEqual(role_source["source"], "rulebook")
        fields = spawn._role_source_roster_fields(role_source, "deadbee")
        self.assertIn("resolution_source", fields)
        self.assertNotIn("resolution_skills", fields)
        self.assertNotIn("resolution_skill_sha", fields)


if __name__ == "__main__":
    unittest.main()
