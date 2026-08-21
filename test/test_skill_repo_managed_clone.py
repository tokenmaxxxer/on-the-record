"""이슈 #1789: `_skill_repo_root()` 의 관리 클론 fallback(env > sibling >
managed clone) acceptance 검증.

1. env 스크럽 + sibling 부재 + 관리 영역 fresh -> 관리 클론이 돌고,
   해석이 성공하며 source=skill-repo + 클론 sha.
2. env 스크럽 + sibling 부재 + clone 도달 불가 + 기존 관리 클론도 없음 ->
   fail-closed, 메시지가 세 소스를 모두 이름 붙인다.
3. env 설정 -> 관리 클론 헬퍼(git clone/pull 호출)가 불린 적 없다.
4. sibling 존재 -> 위와 동일하게 불린 적 없다.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


def _fake_clone_success(args, label, timeout=None, **kwargs):
    """`_run_net` 을 흉내낸다: git clone 요청이면 대상 디렉터리 안에 실제
    skill-repository 처럼 `skills/` 서브디렉터리를 만들고 그 밑에 스킬 하나를
    둬서 `_skill_repo_valid()` 가 참이 되게 한다."""
    if args[:2] == ["git", "clone"]:
        dest = Path(args[-1])
        (dest / "skills" / "example-skill").mkdir(parents=True, exist_ok=True)
    import subprocess
    return subprocess.CompletedProcess(args, 0, stdout="", stderr="")


def _fake_clone_failure(args, label, timeout=None, **kwargs):
    """clone 요청이 와도 아무것도 만들지 않는다 — 네트워크 도달 불가 흉내."""
    import subprocess
    return subprocess.CompletedProcess(args, 1, stdout="", stderr="unreachable")


class ManagedCloneFreshTest(unittest.TestCase):
    """acceptance 1: env 스크럽 + sibling 부재 + 관리 영역 fresh."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self._patches = [
            mock.patch.object(spawn, "ROOT", self.root),
            mock.patch.dict("os.environ", {"MUSTER_SKILL_REPO": "",
                                            "TOKENMAXXXER_RULEBOOKS": str(self.root / "no-such-sibling-parent")}),
            mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_success),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)
        # env scrubbed: unset entirely rather than empty string
        import os
        os.environ.pop("MUSTER_SKILL_REPO", None)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_managed_clone_runs_and_resolves(self):
        root = spawn._skill_repo_root()
        self.assertIsNotNone(root)
        self.assertEqual(root, self.root / "runs" / "rulebooks" / "skill-repository" / "skills")
        self.assertTrue((root / "example-skill").is_dir())

    def test_resolve_role_source_reports_skill_repo(self):
        docroot = self.root / "target"
        specs = docroot / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "role-source-allowlist.json").write_text(
            '{"implementation": ["example-skill"]}')
        result = spawn.resolve_role_source("implementation", docroot,
                                            spawn._skill_repo_root())
        self.assertEqual(result["source"], "skill-repo")
        self.assertEqual(result["skills"], ["example-skill"])
        self.assertIsNotNone(result["skill_sha"])


class ManagedCloneFailClosedTest(unittest.TestCase):
    """acceptance 1's empty state: 모든 세 소스가 실패하면 fail-closed,
    메시지가 세 소스를 모두 이름 붙인다."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        import os
        self._patches = [
            mock.patch.object(spawn, "ROOT", self.root),
            mock.patch.dict("os.environ",
                             {"TOKENMAXXXER_RULEBOOKS": str(self.root / "no-such-sibling-parent")}),
            mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_failure),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("MUSTER_SKILL_REPO", None)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_all_three_sources_unavailable_fails_closed(self):
        self.assertIsNone(spawn._skill_repo_root())
        with self.assertRaises(SystemExit) as cm:
            spawn.resolved_skill_dirs("example-skill", spawn._skill_repo_root())
        message = str(cm.exception)
        self.assertIn("MUSTER_SKILL_REPO", message)
        self.assertIn("TOKENMAXXXER_RULEBOOKS/skill-repository", message)
        self.assertIn("관리 클론", message)


class EnvSetNoNetworkTouchTest(unittest.TestCase):
    """acceptance 2: env 가 풀리면 관리 클론 헬퍼(git clone/pull)가 불린 적
    없다 — byte-identical, no network touch."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.env_dir = self.root / "env-pointed-checkout"
        self.env_dir.mkdir()
        import os
        self._patches = [
            mock.patch.object(spawn, "ROOT", self.root),
            mock.patch.dict("os.environ", {"MUSTER_SKILL_REPO": str(self.env_dir)}),
            mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_success),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_env_resolves_without_invoking_managed_clone(self):
        result = spawn._skill_repo_root()
        self.assertEqual(result, self.env_dir)
        spawn._run_net.assert_not_called()


class SiblingPresentNoNetworkTouchTest(unittest.TestCase):
    """acceptance 2: sibling 이 풀리면 관리 클론 헬퍼가 불린 적 없다."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.rulebooks_dir = self.root / "rulebooks-parent"
        self.sibling_dir = self.rulebooks_dir / "skill-repository"
        self.sibling_dir.mkdir(parents=True)
        import os
        self._patches = [
            mock.patch.object(spawn, "ROOT", self.root),
            mock.patch.dict("os.environ",
                             {"TOKENMAXXXER_RULEBOOKS": str(self.rulebooks_dir)}),
            mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_success),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("MUSTER_SKILL_REPO", None)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_sibling_resolves_without_invoking_managed_clone(self):
        result = spawn._skill_repo_root()
        self.assertEqual(result, self.sibling_dir)
        spawn._run_net.assert_not_called()


if __name__ == "__main__":
    unittest.main()
