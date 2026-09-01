"""Observe-only composite runaway signal (issue #2961).

Reuses `trajectory_analyzer`'s existing OpenHands-calibrated stall
signals rather than inventing a detector (repeated tool calls, repeated
Read offsets, agent monologue, ping-pong, `subagent_in_flight`). This
module ADDS a conjunction rule and a batch entry point over finished
session logs; it computes nothing that `trajectory_analyzer` did not
already expose.

Never terminates, throttles, or refuses anything — it only returns a
verdict describing what it saw (Acceptance: "runs observe-only"). Nothing
in this module calls `os.kill`, raises, or has any other side effect; the
wall-clock/token-cost backstops in `runaway_backstop.py` are the only
things in this slice INTENDED to end a session — as shipped, no live
caller invokes `backstop_verdict()` either, so nothing in this slice
actually ends a session yet.

Consults (docs/issue-2961 issue text): a single trajectory_analyzer
signal is not sufficient on its own — issue #2240's own session tripped
`agent_monologue`-free, ping-pong-free serial exploration (68 of 69 greps
unique) and must read as NOT a runaway, while a session that repeats one
failing edit 4x while genuinely mid-refactor should not be flagged off
that alone either. A runaway verdict requires a CONJUNCTION of at least
two independent thrash signals (never a single one — Acceptance "must
not"), and a session legitimately waiting on its own subagent is never a
runaway regardless of what else is true.
"""
from __future__ import annotations

import trajectory_analyzer as ta

MIN_SIGNALS_FOR_RUNAWAY = 2


def runaway_verdict(events: list[dict]) -> dict:
    """Pure function over one session's parsed event list. `blocked_on_subagent`
    short-circuits to a non-runaway verdict before any other signal is even
    computed — issue #2214's guarantee that a session waiting on its own
    subagent is never reported as stalled/runaway."""
    if ta.subagent_in_flight(events):
        return {"runaway": False, "signals": [], "blocked_on_subagent": True}
    repeats = ta.repeated_tool_calls(events)
    signals = []
    if repeats["observation_repeats"]:
        signals.append("repeated-action-observation")
    if repeats["error_repeats"]:
        signals.append("repeated-action-error")
    if ta.agent_monologue_runs(events):
        signals.append("agent-monologue")
    if ta.ping_pong_signal(events):
        signals.append("ping-pong")
    if ta.repeated_read_offsets(events):
        signals.append("repeated-read-offsets")
    return {
        "runaway": len(signals) >= MIN_SIGNALS_FOR_RUNAWAY,
        "signals": signals,
        "blocked_on_subagent": False,
    }


def finished_session_verdicts(session_log_paths) -> list[dict]:
    """One verdict per FINISHED session log (a log carrying a terminal
    `result` event) — the composite signal only ever records, per
    Acceptance's `runaway_signal_observe_only` check: zero finished
    sessions among the given paths means zero verdicts recorded, not an
    error and not a fallback guess. A still-running log (no `result`
    event yet) contributes nothing to the returned list."""
    out = []
    for p in session_log_paths:
        events = ta.parse_session_log(p)
        if ta.final_result_event(events) is None:
            continue
        out.append({"session_log": str(p), **runaway_verdict(events)})
    return out
