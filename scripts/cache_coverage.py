#!/usr/bin/env python3
"""Cache coverage measurement over session stream-json logs (issue #2298).

The static payload every API turn re-sends (system prompt, tool schemas)
is exactly what prompt caching is supposed to absorb — but that has only
ever been measured on this host, never in a consumer session. This module
computes, from the fields the CLI already writes to a role session's
`--output-format stream-json` tee (`spawn.py`'s `_session_log_path()`,
also read by `trajectory_analyzer.py` for issue #2214), two things per
session:

  (a) cache_hit_share      -- share of (input + cache_read + cache_creation)
                               tokens that were served from cache
  (b) static_payload_fraction -- share of that same denominator spent on
                               cache_creation on turns *after* the first.
                               Turn 0's cache_creation is the unavoidable
                               cold-start write; a creation charge on any
                               later turn means something upstream of the
                               cache breakpoint changed and the "static"
                               payload had to be reprocessed -- the defect
                               Ask #2 asks this module to surface.

It also measures two further, unrelated repetitions the same raw log
carries:

- the `subagent_type`/`description` pair the harness re-stamps on every
  `task_progress` tick of a running background Task, which is what let a
  consumer misread one real Agent call as looking like 164 of them
  (issue body).
- a single logical assistant turn is teed as one JSONL line per content
  block (a `thinking` block, then a `tool_use` block), and the CLI stamps
  the message-level `usage` object on *every* one of those lines
  byte-identically -- found while measuring (a)/(b) on this host's own
  live session log: summing `usage` per `assistant`-type line over-counted
  real turns by ~1.8x (33 of 34 real turns were split across 2 lines).
  `usage_turns` dedupes by `message.id` so (a)/(b) count each real turn
  once; `diet_log_bytes` demonstrates trimming the redundant copies from
  the log itself.

`diet_log_bytes` trims both without touching anything
`trajectory_analyzer.py` reads (it never looks at `task_progress` fields
or at more than the last `usage` per message id -- only the terminal
`result.subagent_stats` rollup and per-line `tool_use`/`usage` blocks,
both preserved).

Run:
  python3 scripts/cache_coverage.py <session-log-path> [--json]
  python3 scripts/cache_coverage.py --batch <dir-glob> [--json]
  python3 scripts/cache_coverage.py --diet <session-log-path>
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import trajectory_analyzer as ta  # reuse the same tolerant log parser

# task_progress fields that are static per task_id -- already recorded once
# on that task's task_started event; a reader joins on task_id to recover
# them instead of paying for a fresh copy on every tick.
_STATIC_PROGRESS_FIELDS = ("description", "subagent_type")


# ---------------------------------------------------------------------------
# (a)/(b) cache coverage
# ---------------------------------------------------------------------------

def usage_turns(events: list[dict]) -> list[dict]:
    """assistant events carrying `message.usage` -> per-turn token counts,
    in stream order, one entry per real API turn. An assistant event
    without a `usage` block (e.g. a stream delta) is skipped rather than
    counted as a zero turn. A single logical turn is teed as one JSONL
    line per content block (`thinking`, then `tool_use`, ...), each
    stamped with the same message-level `usage` -- deduped here by
    `message.id` so a 2-block turn isn't counted (and summed) twice."""
    out = []
    seen_ids: set[str] = set()
    for ev in events:
        if ev.get("type") != "assistant":
            continue
        msg = ev.get("message") or {}
        usage = msg.get("usage")
        if not usage:
            continue
        mid = msg.get("id")
        if mid is not None:
            if mid in seen_ids:
                continue
            seen_ids.add(mid)
        out.append({
            "input_tokens": usage.get("input_tokens") or 0,
            "cache_read_input_tokens": usage.get("cache_read_input_tokens") or 0,
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens") or 0,
            "output_tokens": usage.get("output_tokens") or 0,
        })
    return out


def cache_summary(turns: list[dict]) -> dict:
    """Pure core over already-extracted turns. Empty state (0 or 1
    usage-bearing turn): no repetition exists yet -- both fractions report
    as 0.0 rather than dividing by zero, and `no_repetition` is True so a
    caller can tell "measured zero" apart from "nothing to measure"."""
    n = len(turns)
    total_input = sum(t["input_tokens"] for t in turns)
    total_read = sum(t["cache_read_input_tokens"] for t in turns)
    total_creation = sum(t["cache_creation_input_tokens"] for t in turns)
    denom = total_input + total_read + total_creation
    cache_hit_share = (total_read / denom) if denom else 0.0
    repeat_creation = sum(t["cache_creation_input_tokens"] for t in turns[1:])
    static_payload_fraction = (repeat_creation / denom) if (denom and n > 1) else 0.0
    return {
        "turns": n,
        "total_input_tokens": total_input,
        "total_cache_read_input_tokens": total_read,
        "total_cache_creation_input_tokens": total_creation,
        "cache_hit_share": round(cache_hit_share, 4),
        "static_payload_fraction": round(static_payload_fraction, 4),
        "no_repetition": n <= 1,
    }


def session_cache_summary(path) -> dict:
    events = ta.parse_session_log(path)
    summary = cache_summary(usage_turns(events))
    summary["path"] = str(path)
    return summary


def to_ledger_event(summary: dict, skill: str | None = None, issue: str | None = None) -> dict:
    """`skill_judge_perf` (issue #2255, consult.py) is the field-shape
    template this Ask names: ts/role/issue plus the measured metrics, so
    this can be handed straight to `ledger_write` later without inventing
    a new event convention. Not wired into the live spawn/consult path
    here -- the frozen no-side-effects constraint (issue body) rules that
    out for this delivery; this is the template the Ask calls for."""
    return {
        "event": "cache_coverage_perf",
        "ts": int(time.time()),
        "skill": skill,
        "issue": issue,
        "turns": summary["turns"],
        "cache_hit_share": summary["cache_hit_share"],
        "static_payload_fraction": summary["static_payload_fraction"],
        "no_repetition": summary["no_repetition"],
    }


# ---------------------------------------------------------------------------
# subagent_type/description repetition (log-diet target)
# ---------------------------------------------------------------------------

def subagent_field_repetition(events: list[dict]) -> dict:
    """distinct_task_calls: unique task_id count (the real number of
    background Task spawns). progress_repeats: how many task_progress
    ticks re-stamp the static subagent_type/description pair. A reader
    who greps `subagent_type` sees distinct_task_calls + progress_repeats
    hits for distinct_task_calls real calls -- the misread the issue
    body describes."""
    task_ids = set()
    repeats = 0
    for ev in events:
        if ev.get("type") != "system":
            continue
        if "subagent_type" not in ev:
            continue
        if ev.get("subtype") == "task_started":
            task_ids.add(ev.get("task_id"))
        elif ev.get("subtype") == "task_progress":
            repeats += 1
    return {"distinct_task_calls": len(task_ids), "progress_repeats": repeats}


def _diet_obj(obj: dict, seen_usage_ids: set) -> dict:
    """One event -> its dieted form. task_progress loses its static
    description/subagent_type (recoverable by joining task_id back to
    that task's task_started event). An assistant message's `usage`
    survives only on the first content-block line for its `message.id`
    (every later block for the same id carries a byte-identical copy) --
    `trajectory_analyzer.py` never reads a *second* `usage` for a
    message id, so this loses no signal it consumes."""
    if obj.get("type") == "system" and obj.get("subtype") == "task_progress":
        return {k: v for k, v in obj.items() if k not in _STATIC_PROGRESS_FIELDS}
    if obj.get("type") == "assistant":
        msg = obj.get("message") or {}
        mid = msg.get("id")
        if mid is not None and msg.get("usage"):
            if mid in seen_usage_ids:
                obj = dict(obj)
                obj["message"] = {k: v for k, v in msg.items() if k != "usage"}
            else:
                seen_usage_ids.add(mid)
    return obj


def diet_events(events: list[dict]) -> list[dict]:
    """Drop the per-tick copies of description/subagent_type from
    task_progress records, and the redundant per-content-block copies of
    an assistant message's `usage`; every other event, and every field
    `trajectory_analyzer.py` reads, is untouched."""
    seen_usage_ids: set = set()
    return [_diet_obj(ev, seen_usage_ids) for ev in events]


def diet_log_bytes(path) -> dict:
    """Before/after byte size of the schema diet, replayed line-by-line
    on one real session log. Lines the diet doesn't touch are counted at
    their original byte length (not re-serialized), so the comparison
    isn't flattered by incidental key-order/whitespace changes."""
    p = Path(path)
    before = after = 0
    if not p.exists():
        return {"path": str(path), "before_bytes": 0, "after_bytes": 0,
                "reduction_pct": 0.0}
    seen_usage_ids: set = set()
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            stripped = line.rstrip("\n")
            if not stripped:
                continue
            line_bytes = len(stripped.encode("utf-8"))
            before += line_bytes
            try:
                obj = json.loads(stripped)
            except ValueError:
                after += line_bytes
                continue
            if not isinstance(obj, dict):
                after += line_bytes
                continue
            dieted = _diet_obj(obj, seen_usage_ids)
            if dieted is obj:
                after += line_bytes
            else:
                after += len(json.dumps(dieted, ensure_ascii=False,
                                         separators=(",", ":")).encode("utf-8"))
    reduction = round(100 * (1 - after / before), 2) if before else 0.0
    return {"path": str(path), "before_bytes": before, "after_bytes": after,
            "reduction_pct": reduction}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _batch(paths: list[Path]) -> list[dict]:
    rows = []
    for p in paths:
        s = session_cache_summary(p)
        events = ta.parse_session_log(p)
        s.update(subagent_field_repetition(events))
        rows.append(s)
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", help="session log path (single-session mode)")
    ap.add_argument("--batch", metavar="GLOB", help="glob of session logs to summarize as a table")
    ap.add_argument("--diet", metavar="PATH", help="report before/after log-diet byte size for PATH")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.diet:
        result = diet_log_bytes(args.diet)
    elif args.batch:
        paths = sorted(Path().glob(args.batch)) if any(c in args.batch for c in "*?[") \
            else sorted(Path(args.batch).glob("*.log"))
        result = _batch(paths)
    elif args.path:
        result = session_cache_summary(args.path)
        events = ta.parse_session_log(args.path)
        result.update(subagent_field_repetition(events))
    else:
        ap.error("provide a path, --batch GLOB, or --diet PATH")
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
