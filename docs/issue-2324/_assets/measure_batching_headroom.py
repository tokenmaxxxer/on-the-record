#!/usr/bin/env python3
"""issue-2324 — batching-headroom measurement over a session's own
stream-json transcript log.

Motivation: issue #2324 asks to instrument 10 recent transcripts, counting
turns that made exactly one small tool call when an independent adjacent
call existed, BEFORE touching the turn-economy directive. This module is
that instrument, committed so the count is reproducible (`derived:` in the
record cites this file, not a one-off shell pipeline that no longer exists
after the session ends).

Parsing note (methodological pitfall this file avoids): the harness's
stream-json log emits one top-level JSON line PER CONTENT BLOCK of a
streamed assistant message (thinking / text / tool_use), not one line per
logical turn — multiple lines can share the same `message.id`. A first
version of this measurement treated each JSONL line as its own "turn" and
undercounted batching to zero across all 10 transcripts (every transcript
looked like max 1 tool call per turn, which contradicted the turn-budget
directive already landed under issue #2262 telling sessions to batch).
Grouping by `message.id` before counting tool_use blocks per turn is the
fix; `load_turns()` below groups by id. Any reuse of this file for a
similar measurement should keep that grouping — line-by-line counting on
this log format is wrong.

Usage: `python3 docs/issue-2324/_assets/measure_batching_headroom.py <session.log> [<session.log> ...]`
"""
from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict
from typing import Any


def _is_small_bash(cmd: str) -> bool:
    """A bash call counts as "small" only if it is a single atomic command
    -- already-compounded commands (&&, ||, ;, |) are the thing the #2262
    directive asks sessions to produce, not headroom still to capture."""
    return not any(op in cmd for op in ("&&", "||", ";", "|"))


def classify_small(tool_use: dict) -> bool:
    """A tool_use block is "small" if it is a single lightweight
    investigation call: Grep/Glob/Read, or an atomic (non-compound) Bash
    command. Edit/Write/MultiEdit/Skill/Task and compound Bash are not
    "small" for this measurement's purpose."""
    name = tool_use.get("name", "")
    inp = tool_use.get("input", {})
    if name in ("Grep", "Glob", "Read"):
        return True
    if name == "Bash":
        return _is_small_bash(inp.get("command", ""))
    return False


def load_turns(path: str) -> tuple[list[list[dict]], dict[str, str]]:
    """Parse a stream-json session log into logical turns: one entry per
    distinct assistant `message.id`, holding every tool_use block emitted
    under that id (in order). Only turns with >=1 tool_use are kept.
    Also returns a tool_use_id -> tool_result-text map, used by
    `has_adjacent_batchable_pair` below to detect genuine dependency
    (the next call's input literally contains a token from the prior
    call's result, e.g. a discovered file path)."""
    by_id: "OrderedDict[str, list[dict]]" = OrderedDict()
    tool_result_texts: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("type") == "user":
                content = d.get("message", {}).get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            tid = block.get("tool_use_id")
                            c = block.get("content")
                            txt = ""
                            if isinstance(c, str):
                                txt = c
                            elif isinstance(c, list):
                                txt = " ".join(
                                    b.get("text", "") for b in c if isinstance(b, dict)
                                )
                            tool_result_texts[tid] = txt[:2000]
            if d.get("type") == "assistant":
                msg = d.get("message", {})
                mid = msg.get("id")
                content = msg.get("content", [])
                if not isinstance(content, list) or mid is None:
                    continue
                by_id.setdefault(mid, [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        by_id[mid].append(block)
    turns = [v for v in by_id.values() if v]
    return turns, tool_result_texts


def _pair_is_dependent(prev_tu: dict, next_tu: dict, results: dict[str, str]) -> bool:
    """Crude, disclosed dependency heuristic (directional, not exact --
    see PR #2841's caution that categorization method swings magnitude):
    if any >=15-char token from the prior call's tool_result appears
    verbatim in the next call's input, treat the pair as a genuine
    serial dependency (e.g. Grep found a path, Read opened that exact
    path) and exclude it from the batchable count -- this is the
    empty-state case issue #2324 requires: no forced batching where a
    real dependency exists."""
    prev_result = results.get(prev_tu.get("id"), "")
    if not prev_result:
        return False
    next_input_str = json.dumps(next_tu.get("input", {}))
    return any(
        tok in next_input_str for tok in re.findall(r"[\w./-]{15,}", prev_result)
    )


def measure(path: str) -> dict[str, Any]:
    turns, results = load_turns(path)
    total_turns = len(turns)
    multi_tool_turns = sum(1 for t in turns if len(t) > 1)
    single_small = [
        i for i, t in enumerate(turns) if len(t) == 1 and classify_small(t[0])
    ]
    single_small_set = set(single_small)
    pairs = 0
    sample_pairs = []
    for i in single_small:
        j = i + 1
        if j in single_small_set:
            prev_tu, next_tu = turns[i][0], turns[j][0]
            if not _pair_is_dependent(prev_tu, next_tu, results):
                pairs += 1
                sample_pairs.append((i, j, prev_tu.get("name"), next_tu.get("name")))
    return {
        "path": path,
        "total_turns": total_turns,
        "multi_tool_turns": multi_tool_turns,
        "single_small_call_turns": len(single_small),
        "batchable_adjacent_pairs": pairs,
        "sample_pairs": sample_pairs[:5],
    }


if __name__ == "__main__":
    rows = [measure(p) for p in sys.argv[1:]]
    print("transcript\ttotal_turns\tmulti_tool_turns\tsingle_small_call_turns\tbatchable_adjacent_pairs")
    for r in rows:
        print(
            f"{r['path'].split('/')[-1]}\t{r['total_turns']}\t{r['multi_tool_turns']}\t"
            f"{r['single_small_call_turns']}\t{r['batchable_adjacent_pairs']}"
        )
