"""Wall-clock and token/cost backstops (issue #2961).

Intended to replace the 200-turn `--max-turns` cap (removed from
spawn.py/pipeline.py/directive_assembly.py in this same change) as the
thing that bounds a session's worst case, each backstop independently
(either alone sufficient — this is meant to be the hard financial/
wall-clock bound, unlike the observe-only composite runaway signal in
`runaway_signal.py`, which requires a conjunction of signals and never
terminates anything). As shipped, no live caller invokes
`backstop_verdict()` below — the thresholds exist and are derived, but
turn count is the only thing that no longer terminates a session; nothing
here does yet. Wiring an enforcing caller is deliberately out of scope
for this slice.

Thresholds are DERIVED from recorded observation, not chosen freehand
(Acceptance): `trajectory_analyzer.harness_fields()` over the 90 finished
session logs on disk under `$MUSTER_WORKSPACE_ROOT` at derivation time
(2026-09-01) — all `terminal_reason: completed`, none turn-capped — gives
`duration_ms` max 3,064,830 (~51.1min) / p99 2,837,129, and `total_cost_usd`
max 13.73 / p99 12.99. Each backstop below is 1.5x the observed max,
rounded up to a clean unit: generous headroom above the longest diligent
session actually observed, while still bounding the unbounded case. Full
derivation script + output:
docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md.

`total_cost_usd` is only ever present on the terminal `result` event
(confirmed against the same 90 logs — see the record above), so it cannot
be read from a still-growing live-tee log. Cumulative token usage
(input + output + cache_creation + cache_read, summed across every
`assistant` event seen so far) is the live-computable proxy for the same
resource axis; its own threshold is pegged the same way, off the token
totals of the same 90-session corpus (max 86,752,151, 1.5x rounded up).
"""
from __future__ import annotations

# 90-session corpus, 2026-09-01 (see module docstring for the derivation).
WALL_CLOCK_BACKSTOP_MS = 5_400_000        # 90min; max observed 3,064,830ms * 1.5
TOKEN_COST_BACKSTOP_TOKENS = 150_000_000  # max observed 86,752,151 tokens * 1.5, rounded


def wall_clock_exceeded(elapsed_ms: float,
                         threshold_ms: int = WALL_CLOCK_BACKSTOP_MS) -> bool:
    return elapsed_ms >= threshold_ms


def token_cost_exceeded(cumulative_tokens: int,
                         threshold_tokens: int = TOKEN_COST_BACKSTOP_TOKENS) -> bool:
    return cumulative_tokens >= threshold_tokens


def cumulative_tokens(events: list[dict]) -> int:
    """Sum of input+output+cache_creation+cache_read tokens across every
    `assistant` event seen so far — computable on a still-growing
    live-tee log, unlike `total_cost_usd` (terminal-event-only; see
    module docstring)."""
    total = 0
    for ev in events:
        if ev.get("type") != "assistant":
            continue
        usage = (ev.get("message", {}) or {}).get("usage") or {}
        total += ((usage.get("input_tokens") or 0)
                  + (usage.get("output_tokens") or 0)
                  + (usage.get("cache_creation_input_tokens") or 0)
                  + (usage.get("cache_read_input_tokens") or 0))
    return total


def backstop_verdict(elapsed_ms: float, events: list[dict]) -> dict:
    """Both backstops evaluated independently; `terminate` is true when
    EITHER fires. Pure function — deciding, not killing: an enforcing
    caller would be what actually kills the process, but as shipped
    nothing in production calls this function; wiring one in (e.g. into
    the watchdog poll loop) is out of scope for this slice."""
    tokens = cumulative_tokens(events)
    wall = wall_clock_exceeded(elapsed_ms)
    cost = token_cost_exceeded(tokens)
    return {
        "terminate": wall or cost,
        "wall_clock_exceeded": wall,
        "token_cost_exceeded": cost,
        "elapsed_ms": elapsed_ms,
        "cumulative_tokens": tokens,
    }
