#!/usr/bin/env python3
"""Secondary instrumentation for a skills-on arm's session log (issue #3041).

Reads the stream-json transcript produced by `run_pair.sh` and reports, per
the issue's Scope bullet, the figures that must never be used as *scoring*
inputs but are recorded alongside the score for later diagnosis:

  - skill_opens: how many Skill tool calls happened
  - first_open_fraction: position of the first Skill call among ALL tool
    calls (any tool), as a fraction of the total tool-call count
  - interleaved_2plus: whether 2+ distinct skills opened in an interleaved
    order (A,B,A) rather than adjacent runs (A,A,B,B); None if fewer than 2
    distinct skills opened

Usage: python3 scripts/issue-3041/instrument.py <session.jsonl> [...]
"""
from __future__ import annotations
import json
import sys


def analyze(path: str) -> dict:
    tool_seq = []  # list of (tool_name, skill_name_or_None)
    try:
        fh = open(path, "r", errors="replace")
    except OSError as exc:
        return {"log": path, "status": "unmeasured", "reason": str(exc)}
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("type") != "assistant":
                continue
            for c in d.get("message", {}).get("content", []):
                if c.get("type") == "tool_use":
                    name = c.get("name")
                    skill = c.get("input", {}).get("skill") if name == "Skill" else None
                    tool_seq.append((name, skill))

    total = len(tool_seq)
    if total == 0:
        return {"log": path, "status": "unmeasured", "reason": "no-tool-calls"}

    skill_positions = [i for i, (n, _s) in enumerate(tool_seq) if n == "Skill"]
    opens = len(skill_positions)
    first_open_fraction = round((skill_positions[0] + 1) / total, 3) if opens else None

    skill_names_in_order = [s for (n, s) in tool_seq if n == "Skill"]
    distinct = []
    for s in skill_names_in_order:
        if s not in distinct:
            distinct.append(s)

    interleaved = None
    if len(distinct) >= 2:
        runs = 1
        for i in range(1, len(skill_names_in_order)):
            if skill_names_in_order[i] != skill_names_in_order[i - 1]:
                runs += 1
        interleaved = runs > len(distinct)

    return {
        "log": path,
        "status": "measured",
        "total_tool_calls": total,
        "skill_opens": opens,
        "distinct_skills": distinct,
        "first_open_fraction": first_open_fraction,
        "interleaved_2plus": interleaved,
    }


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(json.dumps(analyze(p)))
