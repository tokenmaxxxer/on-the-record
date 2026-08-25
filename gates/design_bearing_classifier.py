#!/usr/bin/env python3
"""artifact-gate phase 1(#2012) — 이슈 본문이 디자인이 개입된
(design-bearing) 요청인지 분류한다: verdict + 근거(어떤 신호가
발동했는지)를 함께 돌려준다.

#2001의 크로스-패밀리 키워드 겹침 신호(spawn.py `_tokenize` +
`_cross_family_skill_matches`의 토큰화/겹침/임계값 채점 형태)를
그대로 재사용한다 — 새 탐지기를 발명하지 않는다(제안서 Rationale).
`_tokenize`는 spawn.py:7952-7961에서 그대로 복사했다: `gates/`
모듈이 `spawn.py`를 임포트하면 이 저장소의 기존 의존 방향(leaf인
`gates/` → 상위 CLI인 `spawn.py`)이 뒤집힌다(제안서 Rationale).

precision-first: 기계적(mechanical) 이슈에 대한 false positive가
false negative보다 훨씬 비싸다(제안서 Constraints) — 임계값은 이
저장소의 실제 기계적 이슈 코퍼스에서 오탐 0을 먼저 만족시키도록
잡았고, 그 다음에야 디자인 개입 코퍼스를 잡아내는지 확인했다
(docs/issue-2012/reports/implementation/corpus.md).

override path: `design-bearing-override: yes|no` 닫힌 어휘 태그가
본문에 있으면 스코어러를 완전히 우회하고, 그 사실 자체가 근거로
인용된다(design_research_consult.py #1653의 override 관례와 동일한
모양).

  python3 gates/design_bearing_classifier.py <issue-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).parent))
import gh_rest

# spawn.py:7952-7961에서 그대로 복사(제안서 What will be done) — 임포트가
# 아니라 복사인 이유는 모듈 docstring 참고.
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset({"a", "the", "use", "when", "or", "and", "is", "an"})


def _tokenize(text: str) -> set[str]:
    """소문자화 + 비영숫자 분리 + 작은 불용어 목록 제거."""
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS}


# 부모 이슈(#2012)가 직접 나열한 산출물 카테고리(storyboard, IA, flow
# diagram, user scenarios, HTML demo)에서 뽑은 고정 어휘. 코퍼스 조사
# 결과(#1596, #1742) "architecture"/"demo", "identity"/"layout" 같은
# 개별 단어는 기계적 이슈에도 우연히 등장할 수 있어 임계값을
# `_DESIGN_BEARING_MIN_OVERLAP = 3`으로 잡았다 — 이 저장소의 실제
# 기계적 코퍼스 4건 모두 겹침이 최대 2에서 멈춘다
# (corpus.md, "Threshold calibration").
_DESIGN_SIGNAL_KEYWORDS = frozenset({
    "storyboard", "information", "architecture", "flow", "diagram",
    "user", "scenario", "scenarios", "html", "demo", "wireframe",
    "landing", "page", "mockup", "visual", "brand", "identity", "ui",
    "ux", "layout",
})
_DESIGN_BEARING_MIN_OVERLAP = 3

_OVERRIDE_YES = re.compile(
    r"^\s*[-*]?\s*design-bearing-override\s*:\s*yes\b",
    re.IGNORECASE | re.MULTILINE)
_OVERRIDE_NO = re.compile(
    r"^\s*[-*]?\s*design-bearing-override\s*:\s*no\b",
    re.IGNORECASE | re.MULTILINE)


class Verdict(TypedDict):
    design_bearing: bool
    evidence: list[str]
    override: bool


def _design_bearing_score(issue_body: str) -> tuple[int, list[str]]:
    """본문을 토큰화해 디자인 신호 어휘와 교집합을 낸다. 겹침 개수와
    (결정론적 재현을 위해 정렬된) 매칭 키워드 목록을 함께 돌려준다 —
    "어떤 신호가 발동했는지"가 인용 근거다(제안서 Request)."""
    matched = sorted(_tokenize(issue_body) & _DESIGN_SIGNAL_KEYWORDS)
    return len(matched), matched


def check_issue_body(issue: int, body: str) -> Verdict:
    """이슈 본문 텍스트만으로 판정한다(네트워크 없음, 단위테스트 가능).

    닫힌 어휘 override(`design-bearing-override: yes|no`)가 있으면
    스코어러를 우회하고 그 태그 자체를 근거로 인용한다. 없으면 키워드
    겹침 점수를 매겨 임계값 이상이면 design-bearing으로 판정한다.
    """
    del issue  # 본문만으로 판정 — 이슈 번호는 호출부 로깅용
    body = body or ""
    if _OVERRIDE_YES.search(body):
        return {"design_bearing": True,
                "evidence": ["design-bearing-override: yes"],
                "override": True}
    if _OVERRIDE_NO.search(body):
        return {"design_bearing": False,
                "evidence": ["design-bearing-override: no"],
                "override": False}
    overlap, matched = _design_bearing_score(body)
    return {"design_bearing": overlap >= _DESIGN_BEARING_MIN_OVERLAP,
            "evidence": matched,
            "override": False}


def check(repo: Path, issue: int) -> Verdict | None:
    """`gh api`로 본문을 읽어 판정한다. 읽기 자체가 실패하면 None —
    호출부가 "검사 불가는 통과가 아니다"로 다뤄야 한다."""
    body = gh_rest.fetch_issue_body(repo, issue)
    if body is None:
        return None
    return check_issue_body(issue, body)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: design_bearing_classifier.py <issue-number> [--repo <경로>]")
        return 1
    try:
        issue = int(sys.argv[1])
    except ValueError:
        print(f"usage: design_bearing_classifier.py <issue-number> [--repo <경로>] "
              f"— issue-number must be an integer, got {sys.argv[1]!r}")
        return 1
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()

    verdict = check(repo, issue)
    if verdict is None:
        print(f"이슈 #{issue} 본문을 읽을 수 없다(`gh api repos/.../issues/{issue}` 실패) — "
              f"검사 불가는 통과가 아니다.")
        return 0
    print(f"design_bearing={verdict['design_bearing']} "
          f"override={verdict['override']} evidence={verdict['evidence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
