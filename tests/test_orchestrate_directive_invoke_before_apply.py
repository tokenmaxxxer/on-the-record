"""이슈 #2079 (issue-2062 remainder): 오케스트레이트 디렉티브
(`on-the-record/commands/run.md`) 텍스트에 invoke-before-apply(이슈 #2062)
문장과 `invoked;` 마커 요구가 두 경로 모두에 실려야 한다 — (1) 오케스트레이터
자신의 대화-단위 스킬 사용, (2) 플러그인 자신의 세 스킬
(on-the-record:consult/run/report-upstream)."""
from pathlib import Path
import unittest

RUN_MD = Path(__file__).resolve().parent.parent / "on-the-record" / "commands" / "run.md"


class OrchestrateDirectiveInvokeBeforeApply(unittest.TestCase):
    def setUp(self):
        self.text = RUN_MD.read_text(encoding="utf-8")

    def test_orchestrator_own_skill_path_states_invoke_before_apply(self):
        self.assertIn("오케스트레이터 자신의 스킬 사용", self.text)
        self.assertIn("invoke-before-apply(이슈 #2062)", self.text)
        self.assertIn("invoked;", self.text)

    def test_plugin_own_three_skills_path_states_invoke_before_apply(self):
        idx = self.text.index("플러그인 자신의 세 스킬")
        segment = self.text[idx:idx + 1200]
        self.assertIn("invoke-before-apply", segment)
        self.assertIn("invoked;", segment)
        for name in ("on-the-record:consult", "on-the-record:run",
                     "on-the-record:report-upstream"):
            self.assertIn(name, segment)

    def test_both_paths_share_the_same_invoke_before_apply_sentence_shape(self):
        occurrences = self.text.count("invoke-before-apply")
        self.assertGreaterEqual(occurrences, 2)
        self.assertGreaterEqual(self.text.count("invoked;"), 2)


if __name__ == "__main__":
    unittest.main()
