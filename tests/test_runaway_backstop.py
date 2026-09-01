"""Wall-clock and token/cost backstops (issue #2961 Acceptance: `-k backstop`).

`runaway_backstop.py`'s two backstops replace the 200-turn `--max-turns`
cap as the thing that terminates a runaway session; thresholds are
derived from recorded observation (see that module's docstring and
docs/issue-2961/reports/
observability-methodology-selection+test-derivation-27c16f97.md for the
derivation script/output), not chosen freehand.

  python3 -m pytest tests/test_runaway_backstop.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import runaway_backstop as rb  # noqa: E402


def _assistant_event(input_tokens=0, output_tokens=0, cache_creation=0, cache_read=0):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": "..."}],
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens,
                      "cache_creation_input_tokens": cache_creation,
                      "cache_read_input_tokens": cache_read}}}


def test_wall_clock_backstop_terminates_when_elapsed_exceeds_threshold():
    under = rb.backstop_verdict(rb.WALL_CLOCK_BACKSTOP_MS - 1, [])
    over = rb.backstop_verdict(rb.WALL_CLOCK_BACKSTOP_MS + 1, [])
    assert under["terminate"] is False
    assert over["terminate"] is True
    assert over["wall_clock_exceeded"] is True
    assert over["token_cost_exceeded"] is False


def test_token_cost_backstop_terminates_when_cumulative_tokens_exceed_threshold():
    events = [_assistant_event(input_tokens=rb.TOKEN_COST_BACKSTOP_TOKENS + 1)]
    verdict = rb.backstop_verdict(elapsed_ms=0, events=events)
    assert verdict["terminate"] is True
    assert verdict["token_cost_exceeded"] is True
    assert verdict["wall_clock_exceeded"] is False


def test_backstop_does_not_terminate_a_diligent_session_under_both_thresholds():
    events = [_assistant_event(input_tokens=1000, output_tokens=500) for _ in range(50)]
    verdict = rb.backstop_verdict(elapsed_ms=60_000, events=events)
    assert verdict["terminate"] is False


def test_cumulative_tokens_sums_all_four_usage_fields_across_assistant_events():
    events = [_assistant_event(input_tokens=1, output_tokens=2, cache_creation=3, cache_read=4),
              _assistant_event(input_tokens=10, output_tokens=20, cache_creation=30, cache_read=40)]
    assert rb.cumulative_tokens(events) == (1 + 2 + 3 + 4) + (10 + 20 + 30 + 40)


def test_backstop_thresholds_are_derived_from_observation_not_freehand():
    """Regression guard on the derivation itself (see module docstring):
    each threshold is 1.5x a specific observed-max figure, rounded up to
    a clean unit — not an arbitrary round number picked without a
    measurement behind it."""
    observed_max_duration_ms = 3_064_830
    observed_max_tokens = 86_752_151
    assert rb.WALL_CLOCK_BACKSTOP_MS >= observed_max_duration_ms * 1.5
    assert rb.WALL_CLOCK_BACKSTOP_MS < observed_max_duration_ms * 2
    assert rb.TOKEN_COST_BACKSTOP_TOKENS >= observed_max_tokens * 1.5
    assert rb.TOKEN_COST_BACKSTOP_TOKENS < observed_max_tokens * 2
