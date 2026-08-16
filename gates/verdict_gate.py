#!/usr/bin/env python3
"""검증자-비대칭 머지 정책 — issue #1669 (northpole req#6). 리뷰어의
자유 텍스트 검증(MERGE/CHANGES)을 오케스트레이터 행동으로 바꾸되, LLM
검증 하나만으로는 절대 머지를 승인하지 않는다: CHANGES 는 항상
respawn; MERGE 는 결정론적 게이트(`gates/merge_gate.py`'s
`evaluate()`)가 허용하고 테스트도 통과해야만 ALLOW_MERGE, 그 외에는
전부 HOLD. 검증 파싱은 fail-closed — 애매하거나 손상되었거나
주입(injection)된 텍스트는 항상 HOLD 로 떨어진다.

  python3 gates/verdict_gate.py <pr> <subject> [--repo <경로>]

verdict 텍스트는 stdin 으로 읽는다.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import merge_gate  # noqa: E402

_MERGE_RE = re.compile(r"\bMERGE\b")
_CHANGES_RE = re.compile(r"\bCHANGES\b")
_NEGATION_RE = re.compile(
    r"\b(do\s+not|don'?t|never|no)\s+MERGE\b", re.IGNORECASE)
_QUOTE_MARKERS = ("> ", "“", '"', "quoted", "인용")


def _parse_verdict(text: str | None) -> str | None:
    """자유 텍스트에서 리뷰어 검증을 뽑는다. 애매하면(양쪽 다 있거나,
    부정형이거나, 인용된 것처럼 보이면) `None` — fail-closed."""
    if not text:
        return None
    stripped = text.strip()
    if not stripped:
        return None

    upper = stripped.upper()
    has_merge = bool(_MERGE_RE.search(upper))
    has_changes = bool(_CHANGES_RE.search(upper))

    if has_merge and has_changes:
        return None
    if _NEGATION_RE.search(stripped):
        return None
    if has_merge:
        # 리뷰어가 스스로 남긴 것이 아니라 PR 본문 등에서 인용/재인용된
        # 것처럼 보이는 텍스트는 신뢰하지 않는다.
        lowered = stripped.lower()
        if any(marker.lower() in lowered for marker in _QUOTE_MARKERS):
            return None
        return "MERGE"
    if has_changes:
        return "CHANGES"
    return None


def classify(reviewer_verdict: str | None, merge_gate_result: dict,
             tests_pass: bool) -> str:
    """`"ALLOW_MERGE" | "RESPAWN" | "HOLD"`. 순수 함수 — 네트워크 없음."""
    verdict = _parse_verdict(reviewer_verdict)
    if verdict == "CHANGES":
        return "RESPAWN"
    if verdict == "MERGE":
        if merge_gate_result.get("allowed") and tests_pass:
            return "ALLOW_MERGE"
        return "HOLD"
    return "HOLD"


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: verdict_gate.py <pr> <subject> [--repo <경로>]")
        return 1
    pr, subject = int(sys.argv[1]), sys.argv[2]
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()
    verdict_text = sys.stdin.read()

    gate_result = merge_gate.evaluate(repo, repo, pr, subject)
    comment = merge_gate.latest_check_runner_comment(repo, pr)
    tests_pass = False
    if comment is not None:
        result = merge_gate.parse_check_runner_result(comment)
        tests_pass = bool(result and result["passed"] == result["total"])

    action = classify(verdict_text, gate_result, tests_pass)
    print(f"판정: PR #{pr} ({subject}) -> {action}")
    for reason in gate_result["reasons"]:
        print(f"  - {reason}")
    return 0 if action == "ALLOW_MERGE" else 1


if __name__ == "__main__":
    sys.exit(main())
