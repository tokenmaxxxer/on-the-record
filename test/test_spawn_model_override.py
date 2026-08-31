"""이슈#1736: `resolved_skill_model()`의 CLI 오버라이드 우선순위
(--model > MUSTER_SKILL_MODEL > role_model.txt > "sonnet") 정밀도 레벨별
단위 테스트."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class ResolvedSkillModelPrecedenceTest(unittest.TestCase):
    """우선순위 레벨 하나당 테스트 하나: CLI > env > file > default.

    `spawn.SKILL_MODEL_CONFIG`는 레포 루트의 실제 `role_model.txt`를 가리키는
    모듈 전역 경로다 — pytest-xdist(`-n auto`, pytest.ini)가 테스트를
    여러 프로세스에 흩뿌리므로, 그 경로를 그대로 쓰면 이 파일 안의
    테스트끼리도 서로 다른 워커에서 같은 파일을 동시에 쓰고 지워 경합한다.
    테스트마다 고유한 임시 파일로 가리키게 바꿔 그 경합을 없앤다."""

    def setUp(self):
        self._saved_env = os.environ.pop("MUSTER_SKILL_MODEL", None)
        self._saved_config_path = spawn.SKILL_MODEL_CONFIG
        self._tmpdir = tempfile.TemporaryDirectory()
        spawn.SKILL_MODEL_CONFIG = Path(self._tmpdir.name) / "role_model.txt"

    def tearDown(self):
        if self._saved_env is None:
            os.environ.pop("MUSTER_SKILL_MODEL", None)
        else:
            os.environ["MUSTER_SKILL_MODEL"] = self._saved_env
        spawn.SKILL_MODEL_CONFIG = self._saved_config_path
        self._tmpdir.cleanup()

    def test_cli_wins_over_env_and_file(self):
        os.environ["MUSTER_SKILL_MODEL"] = "sonnet"
        spawn.SKILL_MODEL_CONFIG.write_text("haiku")
        self.assertEqual(spawn.resolved_skill_model("opus"), "opus")

    def test_env_wins_over_file_when_no_cli(self):
        os.environ["MUSTER_SKILL_MODEL"] = "opus"
        spawn.SKILL_MODEL_CONFIG.write_text("haiku")
        self.assertEqual(spawn.resolved_skill_model(), "opus")

    def test_file_wins_over_default_when_no_cli_or_env(self):
        spawn.SKILL_MODEL_CONFIG.write_text("haiku")
        self.assertEqual(spawn.resolved_skill_model(), "haiku")

    def test_default_when_nothing_set(self):
        self.assertEqual(spawn.resolved_skill_model(), "sonnet")

    def test_cli_whitespace_only_falls_through(self):
        # 이슈#35/#93 과 같은 이유 — 공백만 있는 오버라이드는 미설정과
        # 동일하게 취급돼야 한다, "--model '   '" 이 나가면 안 된다.
        os.environ["MUSTER_SKILL_MODEL"] = "opus"
        self.assertEqual(spawn.resolved_skill_model("   "), "opus")


if __name__ == "__main__":
    unittest.main()
