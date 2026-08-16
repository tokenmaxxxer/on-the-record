#!/usr/bin/env python3
"""issue #1652 (northpole req#6): 스폰 프롬프트에 이슈 제목 +
'## Acceptance' 의 'check:' 불릿을 원본(verbatim) 그대로 박아넣는
_goal_pin_block() 의 단위테스트. gh 조회 없이 순수 함수만 검사한다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn


ISSUE_BODY_WITH_ACCEPTANCE = """## Problem

Some prose about the bug.

## Acceptance
- check: unit test — the widget renders without crashing.
  provenance: executed-unit
- check: live — the widget is visible in a real browser session.
  provenance: executed-live

## Notes
Irrelevant trailing section.
"""

ISSUE_BODY_NO_ACCEPTANCE = """## Problem

Some prose about the bug, no acceptance section at all.
"""


def test_title_and_criteria_present_verbatim():
    pin = spawn._goal_pin_block("Fix the widget", ISSUE_BODY_WITH_ACCEPTANCE)
    assert "Fix the widget" in pin
    assert "unit test — the widget renders without crashing." in pin
    assert "live — the widget is visible in a real browser session." in pin
    assert "Irrelevant trailing section." not in pin


def test_fetch_failure_fallback_byte_identical_to_empty():
    # gh 조회 실패는 title=None, body=None 으로 나타난다(spawn.py 호출부의
    # try/except 와 동일한 관측 상태).
    pin_from_none = spawn._goal_pin_block(None, None)
    assert pin_from_none == ""


def test_no_acceptance_section_leaves_prompt_unchanged():
    pin = spawn._goal_pin_block("Fix the widget", ISSUE_BODY_NO_ACCEPTANCE)
    assert pin == ""
