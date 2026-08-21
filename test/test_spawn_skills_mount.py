"""이슈 #1742 (skill-axis 프로그램 phase 1): `spawn.py --skills` additive
마운트 경로의 acceptance 1-3 을 검증한다.

1. `--skills a,b` 가 argv/env/워크스페이스에 붙고, 플래그가 없으면
   argv+env 가 바이트 단위로 이전과 동일하다.
2. 모르는 스킬 이름은 워크스페이스/브랜치를 건드리기 전에 fail-closed.
3. 로스터 엔트리와 co-injected 태스크 문자열에 스킬 목록 + skill-repository
   sha 가 실린다(플래그를 안 쓰면 그 필드/문구 자체가 없다).
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class SpawnCmdByteIdenticalNoFlagTest(unittest.TestCase):
    """acceptance 1: --skills 를 안 쓰면 spawn_cmd() 의 argv+env 는 이전과
    바이트 단위로 동일하다 — 저장된 픽스처 파일이 없으므로(survey 확인),
    같은 인자로 skill_dirs=None 호출과 명시적 빈 목록 호출을 서로 비교해
    회귀를 잡는다."""

    def setUp(self):
        self._saved_token = spawn._resolve_gh_token
        spawn._resolve_gh_token = lambda: None

    def tearDown(self):
        spawn._resolve_gh_token = self._saved_token

    def test_no_flag_argv_env_unchanged_by_new_param(self):
        cmd_before, env_before = spawn.spawn_cmd(
            "/tmp/settings.json", "implementation", False,
            core_plugins=[Path("/tmp/core")], plugins=[Path("/tmp/rulebook")],
            model="sonnet")
        cmd_after, env_after = spawn.spawn_cmd(
            "/tmp/settings.json", "implementation", False,
            core_plugins=[Path("/tmp/core")], plugins=[Path("/tmp/rulebook")],
            model="sonnet", skill_dirs=None, skill_repo_sha_value=None)
        self.assertEqual(cmd_before, cmd_after)
        self.assertEqual(env_before, env_after)
        self.assertNotIn("--plugin-dir", " ".join(cmd_after).replace(
            "--plugin-dir /tmp/core", "").replace("--plugin-dir /tmp/rulebook", ""))
        self.assertNotIn("MUSTER_SKILLS", env_after)
        self.assertNotIn("MUSTER_SKILL_REPO_SHA", env_after)


class SpawnCmdSkillsMountTest(unittest.TestCase):
    """acceptance 1: --skills a,b 케이스의 argv/env/워크스페이스-레이아웃."""

    def setUp(self):
        self._saved_token = spawn._resolve_gh_token
        spawn._resolve_gh_token = lambda: None

    def tearDown(self):
        spawn._resolve_gh_token = self._saved_token

    def test_skill_dirs_appended_as_plugin_dirs_with_env_fields(self):
        skill_dirs = [Path("/tmp/skill-repo/a"), Path("/tmp/skill-repo/b")]
        cmd, env = spawn.spawn_cmd(
            "/tmp/settings.json", "implementation", False,
            core_plugins=[Path("/tmp/core")], plugins=[Path("/tmp/rulebook")],
            model="sonnet", skill_dirs=skill_dirs,
            skill_repo_sha_value="abc1234")
        self.assertIn("--plugin-dir", cmd)
        idx_core = cmd.index(str(Path("/tmp/core")))
        idx_a = cmd.index(str(skill_dirs[0]))
        idx_b = cmd.index(str(skill_dirs[1]))
        self.assertLess(idx_core, idx_a)
        self.assertLess(idx_a, idx_b)
        self.assertEqual(env["MUSTER_SKILLS"], "a,b")
        self.assertEqual(env["MUSTER_SKILL_REPO_SHA"], "abc1234")


class ResolvedSkillDirsTest(unittest.TestCase):
    """acceptance 1/2: 이름 -> 디렉터리 resolve, 모르는 이름은 fail-closed."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        (self.repo_root / "alpha").mkdir()
        (self.repo_root / "beta").mkdir()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_empty_csv_returns_empty_list(self):
        self.assertEqual(spawn.resolved_skill_dirs(None, self.repo_root), [])
        self.assertEqual(spawn.resolved_skill_dirs("", self.repo_root), [])

    def test_valid_names_resolve_to_repo_subdirs(self):
        dirs = spawn.resolved_skill_dirs("alpha,beta", self.repo_root)
        self.assertEqual(dirs, [self.repo_root / "alpha", self.repo_root / "beta"])

    def test_unknown_name_exits_nonzero_before_any_mutation(self):
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_dirs("alpha,ghost", self.repo_root)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)

    def test_no_repo_root_exits_nonzero(self):
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_dirs("alpha", None)
        self.assertNotEqual(ctx.exception.code, 0)


class UnknownSkillFailsClosedBeforeWorkspaceTest(unittest.TestCase):
    """acceptance 2: 모르는 스킬 이름은 워크스페이스/브랜치 생성 전에
    non-zero exit — `_spawn_one()` 안에서 `issue_workspace()`/
    `checkout_issue_branch()` 가 절대 불리지 않는다는 것을 스텁으로 증명."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        (self.repo_root / "alpha").mkdir()
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

    def test_unknown_skill_exits_nonzero_and_never_touches_workspace(self):
        with self.assertRaises(SystemExit) as ctx:
            spawn._spawn_one(
                "/tmp/does-not-matter", "implementation", "task", True,
                issue=1742, skills="alpha,ghost")
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIsNotNone(ctx.exception.code)
        self.assertFalse(self._workspace_called)
        self.assertFalse(self._branch_called)


class RecordFieldsCarrySkillsAndShaTest(unittest.TestCase):
    """acceptance 3: 로스터 엔트리(dict)와 co-injected task 문자열이
    --skills 사용 시에만 스킬 목록 + sha 를 싣는다."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        (self.repo_root / "alpha").mkdir()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_roster_dict_carries_skills_and_sha_only_when_used(self):
        skill_dirs = [self.repo_root / "alpha"]
        entry_with = {
            "pid": 1, "role": "implementation",
            **({"skills": [p.name for p in skill_dirs], "skills_sha": "abc1234"}
               if skill_dirs else {}),
        }
        entry_without = {
            "pid": 1, "role": "implementation",
            **({"skills": [], "skills_sha": None} if [] else {}),
        }
        self.assertEqual(entry_with["skills"], ["alpha"])
        self.assertEqual(entry_with["skills_sha"], "abc1234")
        self.assertNotIn("skills", entry_without)
        self.assertNotIn("skills_sha", entry_without)

    def test_task_string_carries_skill_list_and_sha_only_when_used(self):
        skill_dirs = [self.repo_root / "alpha"]
        skill_sha = "abc1234"
        task = "base task"
        if skill_dirs:
            task = task + (
                f"\n\n마운트된 스킬(--skills, 이슈 #1742): "
                f"{', '.join(p.name for p in skill_dirs)} "
                f"(skill-repository {skill_sha})\n")
        self.assertIn("alpha", task)
        self.assertIn("abc1234", task)

        task_unused = "base task"
        no_skill_dirs = []
        if no_skill_dirs:
            task_unused = task_unused + "should not append"
        self.assertEqual(task_unused, "base task")

    def test_skill_repo_sha_reads_git_head(self):
        import subprocess
        subprocess.run(["git", "init", "-q"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                         "commit", "--allow-empty", "-q", "-m", "x"],
                        cwd=self.repo_root, check=True)
        sha = spawn.skill_repo_sha(self.repo_root)
        self.assertRegex(sha, r"^[0-9a-f]{7}$")

    def test_skill_repo_sha_returns_placeholder_on_failure(self):
        empty_dir = Path(tempfile.mkdtemp())
        try:
            self.assertEqual(spawn.skill_repo_sha(empty_dir), "?")
        finally:
            import shutil
            shutil.rmtree(empty_dir)


class ResolvedSkillSourcesFourTierTest(unittest.TestCase):
    """이슈 #1774: `resolved_skill_sources()` 의 네 소스 resolution order,
    ambiguity 하드 에러(전 조합), guidance-only 거절(네 소스 모두),
    record-fields per-source shape."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        base = Path(self._tmpdir.name)
        self.repo_root = base / "skill-repo"
        self.home = base / "home"
        self.target_repo = base / "target-repo"
        self.plugin_install = base / "plugin-install"
        for d in (self.repo_root, self.home, self.target_repo, self.plugin_install):
            d.mkdir()
        (self.home / ".claude" / "skills").mkdir(parents=True)
        (self.target_repo / ".claude" / "skills").mkdir(parents=True)
        (self.plugin_install / "skills").mkdir()
        self._installed_json = self.home / ".claude" / "plugins" / "installed_plugins.json"
        self._installed_json.parent.mkdir(parents=True)
        self._saved_home = spawn.Path.home
        spawn.Path.home = staticmethod(lambda: self.home)

    def tearDown(self):
        spawn.Path.home = self._saved_home
        self._tmpdir.cleanup()

    def _write_installed_plugins(self, entries: dict):
        self._installed_json.write_text(json.dumps({"plugins": entries}))

    def test_no_names_reads_nothing(self):
        # 소스 디렉터리를 아예 안 만들어도(또는 존재해도) 이름이 없으면
        # 네 소스 중 어느 것도 조회되지 않는다 — 빈 목록만 돌아온다.
        self.assertEqual(
            spawn.resolved_skill_sources(None, self.repo_root, home=self.home,
                                          target_repo_root=self.target_repo), [])
        self.assertEqual(
            spawn.resolved_skill_sources("", self.repo_root, home=self.home,
                                          target_repo_root=self.target_repo), [])

    def test_tier1_skill_repo_resolves_alone(self):
        (self.repo_root / "alpha").mkdir()
        import subprocess
        subprocess.run(["git", "init", "-q"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                         "commit", "--allow-empty", "-q", "-m", "x"],
                        cwd=self.repo_root, check=True)
        result = spawn.resolved_skill_sources(
            "alpha", self.repo_root, home=self.home, target_repo_root=self.target_repo)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "skill-repo")
        self.assertEqual(result[0]["dir"], self.repo_root / "alpha")
        self.assertRegex(result[0]["sha"], r"^[0-9a-f]{7}$")

    def test_tier2_plugin_resolves_alone(self):
        plugin_skill = self.plugin_install / "skills" / "beta"
        plugin_skill.mkdir()
        self._write_installed_plugins({
            "foo@marketplace": [{"installPath": str(self.plugin_install),
                                  "version": "v1.2.3"}],
        })
        result = spawn.resolved_skill_sources(
            "beta", None, home=self.home, target_repo_root=self.target_repo)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "plugin")
        self.assertEqual(result[0]["plugin"], "foo@marketplace")
        self.assertEqual(result[0]["version"], "v1.2.3")
        self.assertEqual(result[0]["dir"], plugin_skill)

    def test_tier3_local_user_resolves_alone(self):
        d = self.home / ".claude" / "skills" / "gamma"
        d.mkdir()
        (d / "SKILL.md").write_text("gamma content")
        result = spawn.resolved_skill_sources(
            "gamma", None, home=self.home, target_repo_root=self.target_repo)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "local-user")
        self.assertEqual(result[0]["path"], str(d))
        self.assertEqual(result[0]["content_sha256"],
                          spawn._skill_content_hash(d))

    def test_tier4_local_repo_resolves_alone(self):
        d = self.target_repo / ".claude" / "skills" / "delta"
        d.mkdir()
        (d / "SKILL.md").write_text("delta content")
        result = spawn.resolved_skill_sources(
            "delta", None, home=self.home, target_repo_root=self.target_repo)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "local-repo")
        self.assertEqual(result[0]["path"], str(d))

    def test_nowhere_found_fails_closed(self):
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "ghost", self.repo_root, home=self.home,
                target_repo_root=self.target_repo)
        self.assertNotEqual(ctx.exception.code, 0)

    def _make_pair(self, name, tier_a, tier_b):
        """`name` 이 두 tier 에서 동시에 잡히게 픽스처를 만든다."""
        if "repo" == tier_a or "repo" == tier_b:
            (self.repo_root / name).mkdir()
        if "plugin" == tier_a or "plugin" == tier_b:
            (self.plugin_install / "skills" / name).mkdir()
            self._write_installed_plugins({
                "foo@marketplace": [{"installPath": str(self.plugin_install),
                                      "version": "v1"}],
            })
        if "tier3" == tier_a or "tier3" == tier_b:
            (self.home / ".claude" / "skills" / name).mkdir()
        if "tier4" == tier_a or "tier4" == tier_b:
            (self.target_repo / ".claude" / "skills" / name).mkdir()

    def test_ambiguity_repo_and_plugin_hard_error_names_both(self):
        self._make_pair("shared", "repo", "plugin")
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "shared", self.repo_root, home=self.home,
                target_repo_root=self.target_repo)
        msg = str(ctx.exception)
        self.assertIn("skill-repository", msg)
        self.assertIn("plugin", msg)

    def test_ambiguity_repo_and_tier3_hard_error(self):
        self._make_pair("shared", "repo", "tier3")
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "shared", self.repo_root, home=self.home,
                target_repo_root=self.target_repo)
        msg = str(ctx.exception)
        self.assertIn("skill-repository", msg)
        self.assertIn(".claude/skills", msg)

    def test_ambiguity_plugin_and_tier4_hard_error(self):
        self._make_pair("shared", "plugin", "tier4")
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "shared", None, home=self.home, target_repo_root=self.target_repo)
        msg = str(ctx.exception)
        self.assertIn("plugin", msg)

    def test_ambiguity_tier3_and_tier4_hard_error(self):
        self._make_pair("shared", "tier3", "tier4")
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "shared", None, home=self.home, target_repo_root=self.target_repo)
        msg = str(ctx.exception)
        self.assertIn("~/.claude/skills", msg)
        self.assertIn(".claude/skills", msg)

    def test_ambiguity_two_distinct_plugins_within_tier2(self):
        (self.plugin_install / "skills" / "shared").mkdir()
        plugin_install2 = Path(self._tmpdir.name) / "plugin-install-2"
        (plugin_install2 / "skills" / "shared").mkdir(parents=True)
        self._write_installed_plugins({
            "foo@marketplace": [{"installPath": str(self.plugin_install), "version": "v1"}],
            "bar@marketplace": [{"installPath": str(plugin_install2), "version": "v2"}],
        })
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "shared", None, home=self.home, target_repo_root=self.target_repo)
        msg = str(ctx.exception)
        self.assertIn("foo@marketplace", msg)
        self.assertIn("bar@marketplace", msg)

    def test_hooks_refusal_tier1_skill_repo(self):
        d = self.repo_root / "hooked"
        d.mkdir()
        (d / "hooks").mkdir()
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "hooked", self.repo_root, home=self.home,
                target_repo_root=self.target_repo)
        self.assertIn("hooks/", str(ctx.exception))

    def test_hooks_refusal_tier2_plugin(self):
        d = self.plugin_install / "skills" / "hooked"
        d.mkdir()
        (d / "hooks").mkdir()
        self._write_installed_plugins({
            "foo@marketplace": [{"installPath": str(self.plugin_install), "version": "v1"}],
        })
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "hooked", None, home=self.home, target_repo_root=self.target_repo)
        self.assertIn("hooks/", str(ctx.exception))

    def test_hooks_refusal_tier3_local_user(self):
        d = self.home / ".claude" / "skills" / "hooked"
        d.mkdir()
        (d / "hooks").mkdir()
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "hooked", None, home=self.home, target_repo_root=self.target_repo)
        self.assertIn("hooks/", str(ctx.exception))

    def test_hooks_refusal_tier4_local_repo(self):
        d = self.target_repo / ".claude" / "skills" / "hooked"
        d.mkdir()
        (d / "hooks").mkdir()
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "hooked", None, home=self.home, target_repo_root=self.target_repo)
        self.assertIn("hooks/", str(ctx.exception))


class SkillRosterFieldsFourTierTest(unittest.TestCase):
    """이슈 #1774 요구사항 3: `_skill_roster_fields()` 가 소스별 record shape
    를 나르고, skill-repo-only 조합은 오늘의 flat `skills`/`skills_sha`
    shape 를 그대로 유지한다는 empty-state 요구를 지킨다."""

    def test_repo_only_keeps_todays_flat_shape_plus_detail(self):
        sources = [{"name": "alpha", "source": "skill-repo",
                    "dir": Path("/tmp/x/alpha"), "sha": "abc1234"}]
        fields = spawn._skill_roster_fields(sources, "abc1234")
        self.assertEqual(fields["skills"], ["alpha"])
        self.assertEqual(fields["skills_sha"], "abc1234")
        self.assertEqual(fields["skills_detail"],
                          [{"name": "alpha", "source": "skill-repo", "sha": "abc1234"}])

    def test_plugin_source_row_shape(self):
        sources = [{"name": "beta", "source": "plugin", "dir": Path("/tmp/p/beta"),
                    "plugin": "foo@marketplace", "version": "v1.2.3"}]
        fields = spawn._skill_roster_fields(sources, None)
        self.assertNotIn("skills", fields)
        self.assertNotIn("skills_sha", fields)
        self.assertEqual(fields["skills_detail"], [
            {"name": "beta", "source": "plugin", "plugin": "foo@marketplace",
             "version": "v1.2.3"}])

    def test_local_user_and_local_repo_row_shape(self):
        sources = [
            {"name": "gamma", "source": "local-user", "dir": Path("/tmp/u/gamma"),
             "path": "/tmp/u/gamma", "content_sha256": "deadbeef"},
            {"name": "delta", "source": "local-repo", "dir": Path("/tmp/r/delta"),
             "path": "/tmp/r/delta", "content_sha256": "cafef00d"},
        ]
        fields = spawn._skill_roster_fields(sources, None)
        self.assertNotIn("skills", fields)
        self.assertNotIn("skills_sha", fields)
        self.assertEqual(fields["skills_detail"], [
            {"name": "gamma", "source": "local-user", "path": "/tmp/u/gamma",
             "content_sha256": "deadbeef"},
            {"name": "delta", "source": "local-repo", "path": "/tmp/r/delta",
             "content_sha256": "cafef00d"},
        ])

    def test_no_sources_yields_no_fields(self):
        self.assertEqual(spawn._skill_roster_fields([], None), {})

    def test_mixed_sources_never_add_flat_shape(self):
        sources = [
            {"name": "alpha", "source": "skill-repo", "dir": Path("/tmp/x/alpha"),
             "sha": "abc1234"},
            {"name": "beta", "source": "plugin", "dir": Path("/tmp/p/beta"),
             "plugin": "foo@marketplace", "version": "v1"},
        ]
        fields = spawn._skill_roster_fields(sources, None)
        self.assertNotIn("skills", fields)
        self.assertNotIn("skills_sha", fields)
        self.assertEqual(len(fields["skills_detail"]), 2)


if __name__ == "__main__":
    unittest.main()
