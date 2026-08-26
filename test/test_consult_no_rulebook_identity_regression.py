"""이슈 #2241 stage 2 (docs/issue-2241/proposals/2026-08-25-stage-2-
consult-skill-source-confirmation.md): #1955 가 은퇴시킨 역할-소스
허용목록/rulebook 해석 경로가 다시 들어오지 않는지 지키는 회귀 가드.

두 절반:
1. 정적 스캔 — #1955 커밋(5494b62b)이 spawn.py 에서 지운 rulebook/
   allowlist 식별자들이 `consult.py` 소스 텍스트 어디에도 없다.
2. 동작 확인 — `_readonly_plugin_dirs()`(judge 세션이 붙일 플러그인을
   고르는 자리)가 언제나 skill-repository 소스(이슈 #2561:
   `resolve_role_family_source()` — 고정 role->skill 표
   `_ROLE_SKILLS`/`resolve_role_source()` 은퇴 뒤, 표 없이 디렉터리 이름
   컨벤션으로 role 커버리지를 유도)로만 간다 — "매핑 안 된 역할" 이라는
   상태 자체가 없다는 #1955 의 불변식이 이 자리에서도 깨지지 않는다(이름이
   `f"{role}-"` 로 시작하는 스킬이 하나도 없어도 fail 하지 않고 POLICY
   스킬만 있는 skill-repo 결과로 떨어진다).
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
    """`_readonly_plugin_dirs()`는 `role` 이 스킬-저장소 디렉터리 이름
    접두어로 무엇을 유도하든(있음/없음 모두) 언제나 `resolve_role_family_source()`
    가 리턴한 skill_dirs 를 그대로 앞에 싣는다(이슈 #2561: role->skill 표
    은퇴 뒤 표 없이 같은 자리를 채운다) — rulebook 경로로 새는 별도
    분기가 있으면 이 테스트가 실패한다."""

    def setUp(self):
        self._saved_core_plugin_dirs = spawn.core_plugin_dirs
        spawn.core_plugin_dirs = lambda: []

    def tearDown(self):
        spawn.core_plugin_dirs = self._saved_core_plugin_dirs

    def test_mapped_role_reaches_resolve_role_family_source(self):
        calls = []
        real = spawn.resolve_role_family_source

        def spy(role, repo_root):
            calls.append(role)
            return real(role, repo_root)

        spawn.resolve_role_family_source = spy
        try:
            spawn._readonly_plugin_dirs("implementation")
        finally:
            spawn.resolve_role_family_source = real
        self.assertEqual(calls, ["implementation"])

    def test_unmapped_role_still_reaches_resolve_role_family_source(self):
        # "매핑 안 된 역할"이라는 상태는 rulebook 경로로 새지 않는다 — 이름
        # 접두어가 하나도 안 걸려도 POLICY 스킬만 있는 skill-repo 결과로
        # 떨어진다(#1955).
        calls = []
        real = spawn.resolve_role_family_source

        def spy(role, repo_root):
            calls.append(role)
            return real(role, repo_root)

        spawn.resolve_role_family_source = spy
        try:
            out = spawn._readonly_plugin_dirs("no-such-role")
        finally:
            spawn.resolve_role_family_source = real
        self.assertEqual(calls, ["no-such-role"])
        self.assertEqual([d.name for d in out if d.name == "work-in-english"],
                          ["work-in-english"])


if __name__ == "__main__":
    unittest.main()
