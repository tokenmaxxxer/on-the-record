"""Post-hoc trajectory analyzer over a session's raw stream-json log
(issue #2214).

`spawn.py`'s `_session_log_path()` already tees every session's
`--output-format stream-json` output to `<work>.session.<ts>.<pid>.log` —
this module is the first thing that reads it back for anything beyond a
live tee. Two things it recovers:

1. Harness-native fields the CLI already computes and hands back on the
   terminal `result` event — `permission_denials`, `subagent_stats`,
   `num_turns`, `usage.iterations`, `terminal_reason` — instead of a
   session re-deriving a worse signal from transcript text (this repo's
   own watchdog signal 3 already made that exact move for denials, see
   `events.py:_count_structural_denials`, issue #994/#246/#126 — there is
   no raw "denied"-word regex left anywhere in this repo to retire).
2. Thrash/repetition metrics that are pure functions of the same log:
   repeated `(tool, input)` calls, repeated `Read` offsets, edits per
   file, and the tool mix over time.

Advisory-only (issue #2214 Acceptance): every function here returns data,
never raises on a degenerate log, and nothing in this module can
terminate a session — the thresholds below only ever label a report, and
a session legitimately blocked on its own subagent is labeled
`blocked_on_subagent`, never `stalled`.

Calibration (OpenHands `StuckDetector`, source-read v0 `controller/stuck.py`
@0.39.2 / V1 `sdk/conversation/stuck_detector.py`, cited by issue #2214):
identical action->observation 4x, identical action->error 3x, agent
monologue (no observation between) 3x, alternating A/B/A/B ping-pong 6x,
scanned over the last `MAX_EVENTS_TO_SCAN_FOR_STUCK_DETECTION` tool calls.

Run: python3 trajectory_analyzer.py <path-to-session-log>
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# Thresholds are the OpenHands-calibrated table from issue #2214 — do not
# invent new ones.
STUCK_REPEAT_OBSERVATION = 4
STUCK_REPEAT_ERROR = 3
STUCK_MONOLOGUE = 3
STUCK_PING_PONG = 6
MAX_EVENTS_TO_SCAN_FOR_STUCK_DETECTION = 20

_SUBAGENT_TOOL_NAMES = {"Task", "Agent"}


def parse_session_log(path) -> list[dict]:
    """Line-delimited JSON stream-json log -> list of event dicts. A
    missing file, an empty file, or a malformed/truncated trailing line
    (the live tee can be caught mid-write) all degrade to fewer events,
    never an exception — this is what makes the empty-state case (a fresh
    spawn that errored at admission, zero tool calls) analyze cleanly."""
    events = []
    p = Path(path)
    if not p.exists():
        return events
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if isinstance(obj, dict):
                events.append(obj)
    return events


def _tool_result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def tool_use_events(events: list[dict]) -> list[dict]:
    """Every assistant `tool_use` block, flattened to
    `{index, tool_use_id, name, input}` in stream order."""
    out = []
    for i, ev in enumerate(events):
        if ev.get("type") != "assistant":
            continue
        for block in (ev.get("message", {}).get("content") or []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                out.append({"index": i, "tool_use_id": block.get("id"),
                            "name": block.get("name"), "input": block.get("input") or {}})
    return out


def tool_result_index(events: list[dict]) -> dict:
    """`tool_use_id -> {"is_error", "text", "index", "tool_use_result"}` for
    every `tool_result` block seen. A `tool_use_id` absent from this index
    means the stream ended (or was truncated) before its result arrived.
    `tool_use_result` is the event-level sibling object the CLI attaches
    next to a `tool_result` block (e.g. `{"isAsync": true, "status":
    "async_launched", ...}` for a backgrounded `Agent`/`Task` dispatch) —
    `subagent_in_flight()` needs it to tell "launched" from "settled"."""
    out = {}
    for i, ev in enumerate(events):
        if ev.get("type") != "user":
            continue
        for block in (ev.get("message", {}) or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            tid = block.get("tool_use_id")
            if tid is None:
                continue
            out[tid] = {"is_error": bool(block.get("is_error")),
                        "text": _tool_result_text(block.get("content")),
                        "index": i,
                        "tool_use_result": ev.get("tool_use_result")}
    return out


def _task_notification_tool_use_ids(events: list[dict]) -> set:
    """`tool_use_id`s that reached a terminal `task_notification` system
    event (`status` completed/failed/stopped) — the signal a backgrounded
    `Agent`/`Task` dispatch has actually settled, as opposed to the
    synthetic "launched" `tool_result` it gets immediately on dispatch."""
    return {ev.get("tool_use_id") for ev in events
            if ev.get("type") == "system" and ev.get("subtype") == "task_notification"
            and ev.get("tool_use_id") is not None}


def final_result_event(events: list[dict]) -> dict | None:
    """The terminal `result` event, if the stream reached one — absent on
    a still-running or crashed/truncated session log."""
    for ev in reversed(events):
        if ev.get("type") == "result":
            return ev
    return None


def _denial_tool_counts(denials: list) -> dict:
    """`tool_name -> count` across `permission_denials` — the "counts,
    tool names" half of the default summary form (issue #2214 PR #2221
    review finding 2). A non-dict entry (a known `permission_denials`
    shape failure, issue #246) counts as "unknown" rather than being
    dropped, so this sums to exactly `denial_count`."""
    counts = Counter(d.get("tool_name", "unknown") if isinstance(d, dict) else "unknown"
                     for d in denials)
    return dict(counts)


def _summarize_denials(denials: list) -> list:
    """`permission_denials` entries with the verbatim `tool_input` payload
    stripped — a denied `Edit`/`Write` carries its full `old_string`/
    `new_string`/`content` in `tool_input`, which is what inflates the
    default report to tens of KB per denial (issue #2214 PR #2221 review
    finding 2). Every other field (tool_name, tool_use_id, ...) is kept.
    A non-dict entry is passed through unchanged (nothing to strip) so
    this stays the same length as `denials`, matching `denial_count`."""
    return [{k: v for k, v in d.items() if k != "tool_input"} if isinstance(d, dict) else d
            for d in denials]


def harness_fields(events: list[dict], include_raw_denials: bool = False) -> dict:
    """The free fields issue #2214 names, read straight off the terminal
    `result` event rather than re-derived from transcript text. All-empty
    defaults when no `result` event exists yet (live/truncated log) —
    this is a `None`/`[]` state, not an error.

    `permission_denials` defaults to a summary form — each entry with its
    verbatim `tool_input` stripped, plus `denial_tool_counts` — since a
    denied `Edit`/`Write` reproduces its whole payload otherwise. Pass
    `include_raw_denials=True` (CLI: `--include-raw-denials`) for the
    verbatim form."""
    result = final_result_event(events)
    if result is None:
        return {"permission_denials": [], "denial_count": 0,
                "denial_tool_counts": {},
                "subagent_stats": None, "num_turns": None,
                "usage_iterations": [], "terminal_reason": None,
                "total_cost_usd": None, "duration_ms": None,
                "duration_api_ms": None, "errors": []}
    denials = result.get("permission_denials")
    denials = denials if isinstance(denials, list) else []
    usage = result.get("usage") or {}
    iterations = usage.get("iterations")
    return {"permission_denials": denials if include_raw_denials else _summarize_denials(denials),
            "denial_count": len(denials),
            "denial_tool_counts": _denial_tool_counts(denials),
            "subagent_stats": result.get("subagent_stats"),
            "num_turns": result.get("num_turns"),
            "usage_iterations": iterations if isinstance(iterations, list) else [],
            "terminal_reason": result.get("terminal_reason"),
            "total_cost_usd": result.get("total_cost_usd"),
            "duration_ms": result.get("duration_ms"),
            "duration_api_ms": result.get("duration_api_ms"),
            "errors": result.get("errors") or []}


def _normalized_input(tool_input: dict) -> str:
    return json.dumps(tool_input, sort_keys=True, ensure_ascii=False)


def repeated_tool_calls(events: list[dict]) -> dict:
    """Groups tool_use blocks by `(name, normalized input)` and reports
    the ones crossing the OpenHands-calibrated repeat thresholds —
    identical action->observation >= 4, identical action->error >= 3.
    A `tool_use` with no matching result yet (still in flight) is excluded
    from both counts, not counted as a non-error repeat."""
    uses = tool_use_events(events)
    results = tool_result_index(events)
    by_key_ok = Counter()
    by_key_err = Counter()
    examples = {}
    for u in uses:
        r = results.get(u["tool_use_id"])
        if r is None:
            continue
        key = (u["name"], _normalized_input(u["input"]))
        examples.setdefault(key, {"name": u["name"], "input": u["input"]})
        if r["is_error"]:
            by_key_err[key] += 1
        else:
            by_key_ok[key] += 1
    obs_flagged = [{"tool": examples[k]["name"], "input": examples[k]["input"], "count": c}
                   for k, c in by_key_ok.items() if c >= STUCK_REPEAT_OBSERVATION]
    err_flagged = [{"tool": examples[k]["name"], "input": examples[k]["input"], "count": c}
                   for k, c in by_key_err.items() if c >= STUCK_REPEAT_ERROR]
    return {"observation_repeats": obs_flagged, "error_repeats": err_flagged}


def repeated_read_offsets(events: list[dict]) -> list[dict]:
    """Repeated `(file_path, offset)` pairs across `Read` tool calls —
    informational count (the issue asks for the number, not a verdict), so
    the only floor is "more than once"."""
    counts = Counter()
    for u in tool_use_events(events):
        if u["name"] != "Read":
            continue
        fp = u["input"].get("file_path")
        if fp is None:
            continue
        offset = u["input"].get("offset", 0)
        counts[(fp, offset)] += 1
    return [{"file_path": fp, "offset": off, "count": c}
            for (fp, off), c in counts.items() if c > 1]


def edits_per_file(events: list[dict]) -> dict:
    """`Edit`/`Write`/`NotebookEdit` call counts, keyed by target path."""
    counts = Counter()
    for u in tool_use_events(events):
        if u["name"] not in ("Edit", "Write", "NotebookEdit"):
            continue
        fp = u["input"].get("file_path") or u["input"].get("notebook_path")
        if fp is None:
            continue
        counts[fp] += 1
    return dict(counts)


def tool_mix_over_time(events: list[dict], bucket_size: int = 10) -> list[dict]:
    """Tool-name histogram per bucket of `bucket_size` consecutive tool
    calls — a coarse view of how the tool mix shifts across a session."""
    uses = tool_use_events(events)
    buckets = []
    for i in range(0, len(uses), bucket_size):
        chunk = uses[i:i + bucket_size]
        buckets.append(dict(Counter(u["name"] for u in chunk)))
    return buckets


def agent_monologue_runs(events: list[dict], min_repeats: int = STUCK_MONOLOGUE) -> int:
    """Longest run of consecutive assistant turns that emit text with no
    `tool_use` block at all (OpenHands "agent monologue" rule — narration
    with no observation between). Returns 0 unless the run reaches
    `min_repeats`."""
    run = 0
    max_run = 0
    for ev in events:
        if ev.get("type") != "assistant":
            continue
        blocks = (ev.get("message", {}).get("content") or [])
        has_tool_use = any(isinstance(b, dict) and b.get("type") == "tool_use" for b in blocks)
        has_text = any(isinstance(b, dict) and b.get("type") == "text" for b in blocks)
        if has_text and not has_tool_use:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
    return max_run if max_run >= min_repeats else 0


def ping_pong_signal(events: list[dict], min_len: int = STUCK_PING_PONG,
                      window: int = MAX_EVENTS_TO_SCAN_FOR_STUCK_DETECTION) -> bool:
    """OpenHands alternating A/B/A/B ping-pong rule: within the last
    `window` tool calls, a two-tool alternation at least `min_len` calls
    long."""
    uses = tool_use_events(events)[-window:]
    names = [u["name"] for u in uses]
    if len(names) < min_len:
        return False
    run = 1
    best = 1
    for i in range(1, len(names)):
        if names[i] != names[i - 1] and (i < 2 or names[i] == names[i - 2]):
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best >= min_len


def subagent_in_flight(events: list[dict]) -> bool:
    """True when the session is legitimately waiting on its own subagent —
    the case issue #2214 requires never be reported as stalled. Three
    independent checks, any sufficient:
    (a) a foreground `Task`/`Agent` tool_use with no matching `tool_result`
        yet (works on a still-running or truncated log with no terminal
        `result` event);
    (b) a backgrounded dispatch (`tool_use_result.isAsync` true on its
        `tool_result` — the CLI acks a background launch immediately, so
        "has a tool_result" alone under-counts in-flight subagents) whose
        `tool_use_id` never reaches a terminal `task_notification` system
        event;
    (c) once a `result` event exists, `subagent_stats.spawned` exceeding
        the settled total (`completed` + `failed` + `killed.*`).
    """
    uses = tool_use_events(events)
    results = tool_result_index(events)
    settled_notifications = _task_notification_tool_use_ids(events)
    for u in uses:
        if u["name"] not in _SUBAGENT_TOOL_NAMES:
            continue
        r = results.get(u["tool_use_id"])
        if r is None:
            return True
        tur = r.get("tool_use_result") or {}
        if tur.get("isAsync") and u["tool_use_id"] not in settled_notifications:
            return True
    result = final_result_event(events)
    if result is not None:
        stats = result.get("subagent_stats") or {}
        spawned = stats.get("spawned", 0) or 0
        completed = stats.get("completed", 0) or 0
        failed = stats.get("failed", 0) or 0
        killed = stats.get("killed") or {}
        killed_total = (sum(v for v in killed.values() if isinstance(v, int))
                        if isinstance(killed, dict) else 0)
        if spawned > (completed + failed + killed_total):
            return True
    return False


def analyze(path, include_raw_denials: bool = False) -> dict:
    """Top-level entry: parse `path` and return the full advisory report.
    Never raises — a log with zero tool calls (fresh spawn that errored at
    admission), or a path that does not exist on disk, both degrade every
    metric to its empty form, not an exception; this lenient, non-raising
    form is a deliberate library-level contract for callers that want to
    treat "nothing to read" uniformly (e.g. a batch sweep over many
    candidate paths). It is `main()` below — not this function — that
    enforces the CLI's stricter "missing path is an error" behavior
    (issue #2214 PR #2221 review finding 1), by checking existence before
    ever calling this function.

    `blocked_on_subagent` and the thrash signals below are reported
    independently, not one gating the other — a warrant-hunter dispatched
    before landing (docs/issue-2214/reports/implementation/2026-08-24-hunt-trajectory-analyzer.md)
    found that gating `stalled` behind `not blocked_on_subagent` lets a
    crashed/silently-dead backgrounded subagent (an async-launch ack with
    no `task_notification` ever arriving) hold `blocked_on_subagent` True
    forever, which permanently zeroed the whole report — discarding real,
    unrelated thrash for the rest of the session. `subagent_in_flight()`
    by construction contributes zero repeat/monologue/ping-pong signal on
    its own (an in-flight dispatch has no settled `tool_result` to count),
    so a session that is purely waiting still reports `stalled: False`
    without needing this gate — the gate was defending against a case
    that structurally cannot occur, at the cost of one that does.
    """
    events = parse_session_log(path)
    blocked = subagent_in_flight(events)
    repeats = repeated_tool_calls(events)
    monologue = agent_monologue_runs(events)
    ping_pong = ping_pong_signal(events)
    stalled_reasons = []
    if repeats["observation_repeats"]:
        stalled_reasons.append("repeated-action-observation")
    if repeats["error_repeats"]:
        stalled_reasons.append("repeated-action-error")
    if monologue:
        stalled_reasons.append("agent-monologue")
    if ping_pong:
        stalled_reasons.append("ping-pong")
    return {
        "session_log": str(path),
        "event_count": len(events),
        "harness_fields": harness_fields(events, include_raw_denials=include_raw_denials),
        "repeated_tool_calls": repeats,
        "repeated_read_offsets": repeated_read_offsets(events),
        "edits_per_file": edits_per_file(events),
        "tool_mix_over_time": tool_mix_over_time(events),
        "agent_monologue_max_run": monologue,
        "ping_pong_detected": ping_pong,
        "blocked_on_subagent": blocked,
        "advisory": {
            "stalled": bool(stalled_reasons),
            "reasons": stalled_reasons,
            "note": "advisory only — never terminates a session",
        },
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trajectory_analyzer.py",
        description="Post-hoc trajectory analyzer over a session's raw "
                     "stream-json log (issue #2214).")
    parser.add_argument("session_log",
                         help="path to a <work>.session.<ts>.<pid>.log file")
    parser.add_argument("--include-raw-denials", action="store_true",
                         help="include verbatim tool_input payloads in "
                              "permission_denials (large; summarized by default)")
    return parser


def main(argv=None) -> int:
    """CLI entry. `argparse` owns `--help`/usage/missing-argument handling
    (it exits the process itself on those, as it always does), so a flag
    like `--help` can no longer be silently consumed as the log path
    (issue #2214 PR #2221 review finding 1). A path that does not exist
    on disk is a distinct, explicit error here — non-zero exit, message
    on stderr — never the same all-zero report a genuinely empty (e.g.
    0-byte) on-disk log produces; see `analyze()`'s docstring for why
    that leniency is kept at the library level."""
    argv = argv if argv is not None else sys.argv[1:]
    args = _build_arg_parser().parse_args(argv)
    path = Path(args.session_log)
    if not path.exists():
        print(f"error: session log not found: {path}", file=sys.stderr)
        return 1
    if not path.is_file():
        # A directory (or other non-regular-file path, e.g. a device
        # file) passes .exists() — without this check it reaches
        # parse_session_log()'s p.open() and crashes with an unhandled
        # IsADirectoryError instead of the intended clean CLI error
        # (before-landing warrant-hunt, docs/issue-2214/reports/
        # implementation/2026-08-25-hunt-pr2221-fixes.md).
        print(f"error: session log is not a regular file: {path}", file=sys.stderr)
        return 1
    report = analyze(path, include_raw_denials=args.include_raw_denials)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
