"""이슈 #2241 stage 2 (docs/issue-2241/proposals/2026-08-25-stage-2-
consult-skill-source-confirmation.md): #1955 가 은퇴시킨 역할-소스
허용목록/rulebook 해석 경로가 다시 들어오지 않는지 지키는 회귀 가드.

정적 스캔 — #1955 커밋(5494b62b)이 spawn.py 에서 지운 rulebook/
allowlist 식별자들이 `consult.py` 소스 텍스트 어디에도 없다.
"""
import re
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
