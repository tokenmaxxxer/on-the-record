"""이슈 #2241 stage 2 (docs/issue-2241/proposals/2026-08-25-stage-2-
consult-skill-source-confirmation.md): #1955 가 은퇴시킨 역할-소스
허용목록/rulebook 해석 경로가 다시 들어오지 않는지 지키는 회귀 가드.

두 절반:
1. 정적 스캔 — #1955 커밋(5494b62b)이 spawn.py 에서 지운 rulebook/
   allowlist 식별자들이 `consult.py` 소스 텍스트 어디에도 없다.
2. 동작 확인 — `_readonly_plugin_dirs()`(judge 세션이 붙일 플러그인을
   고르는 자리)가 `role` 이 `_ROLE_SKILLS` 에 있든 없든 언제나
   `resolve_role_source()` 한 경로로만 간다 — "매핑 안 된 역할" 이라는
   상태 자체가 없다는 #1955 의 불변식이 이 자리에서도 깨지지 않는다.
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn

CONSULT_PY = Path(__file__).resolve().parent.parent / "consult.py"

# #1955(5494b62b)이 spawn.py 에서 지운, rulebook/allowlist 해석 경로 고유의
# 식별자들 — 오늘 살아있는 코드의 다른 이름과 겹치지 않는 것들만 골랐다
# (예: `_role_source_roster_fields` 는 시그니처를 바꿔 살아남은 함수라 제외).
_FORBIDDEN_IDENTIFIERS = [
    "rulebook_checkout",
    "checkout_version",
    "ensure_rulebook",
    "rulebook_source",
    "rulebook_dir",
    "_role_source_allowlist",
    "rulebook_version",
]


class NoRulebookIdentitySourceStaticScanTest(unittest.TestCase):
    def test_consult_py_never_names_a_retired_rulebook_identifier(self):
        text = CONSULT_PY.read_text(encoding="utf-8")
        for name in _FORBIDDEN_IDENTIFIERS:
            self.assertIsNone(
                re.search(rf"\b{re.escape(name)}\b", text),
                f"consult.py 가 은퇴한 rulebook 식별자 {name!r} 를 다시 "
                "쓰고 있다 — #1955 가 지운 allowlist/rulebook 해석 경로가 "
                "재도입된 것으로 보인다.")


class ReadonlyPluginDirsAlwaysSkillRepoTest(unittest.TestCase):
    """`_readonly_plugin_dirs()`는 role 이 `_ROLE_SKILLS`에 있든 없든
    `resolve_role_source()`가 리턴한 skill_dirs 를 그대로 앞에 싣는다 —
    두 경우가 서로 다른 코드 경로(하나는 rulebook, 하나는 skill-repo)로
    갈라지면 이 테스트가 실패한다."""

    def setUp(self):
        self._saved_role_skills = spawn._ROLE_SKILLS
        self._saved_core_plugin_dirs = spawn.core_plugin_dirs
        spawn.core_plugin_dirs = lambda: []

    def tearDown(self):
        spawn._ROLE_SKILLS = self._saved_role_skills
        spawn.core_plugin_dirs = self._saved_core_plugin_dirs

    def test_mapped_role_reaches_resolve_role_source(self):
        calls = []
        real = spawn.resolve_role_source

        def spy(role, repo_root):
            calls.append(role)
            return real(role, repo_root)

        spawn.resolve_role_source = spy
        try:
            spawn._ROLE_SKILLS = {"implementation": ["work-in-english"]}
            spawn._readonly_plugin_dirs("implementation")
        finally:
            spawn.resolve_role_source = real
        self.assertEqual(calls, ["implementation"])

    def test_unmapped_role_still_reaches_resolve_role_source(self):
        calls = []
        real = spawn.resolve_role_source

        def spy(role, repo_root):
            calls.append(role)
            return real(role, repo_root)

        spawn.resolve_role_source = spy
        try:
            spawn._ROLE_SKILLS = {}
            out = spawn._readonly_plugin_dirs("no-such-role")
        finally:
            spawn.resolve_role_source = real
        # "매핑 안 된 역할"은 rulebook 경로로 새지 않고, skill_dirs 0개짜리
        # skill-repo 결과로 떨어진다(#1955) — 여기서도 같은 함수가 불렸다.
        self.assertEqual(calls, ["no-such-role"])
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()
