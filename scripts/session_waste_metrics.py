#!/usr/bin/env python3
"""Per-turn waste breakdown over a session's raw stream-json log
(issue #2409).

The issue's own 177-session measurement named three waste classes —
exploratory Bash (62% of all Bash calls are neither pytest/git/gh),
hook refusals (6.9 `tool_result` errors/session), and redundant same-file
re-reads (105 for spawn.py, 96 for a role's own record file). This module
is the "artifact and how to regenerate it" the acceptance section asks
for: a re-runnable instrument over `trajectory_analyzer.py`'s already-
parsed event stream, not a hand re-derivation.

Reuses `trajectory_analyzer.parse_session_log`/`tool_use_events`/
`tool_result_index`/`harness_fields` rather than re-parsing the log —
this module only adds the three waste-class classifiers plus the
per-turn breakdown view.

  python3 scripts/session_waste_metrics.py <session_log> [--md]
  python3 scripts/session_waste_metrics.py --batch '<glob>' [--json]
"""
from __future__ import annotations
import argparse
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import trajectory_analyzer as ta  # noqa: E402

# `git commit ... ; git push ...` (compound calls) still count as one
# `git` call — the classifier looks at the first real command token, not
# every token in a `&&`/`;`/`|` chain, matching how the issue's own 9,555-
# call count was produced (one label per Bash tool_use).
_LEADING_ASSIGNMENT_RE = re.compile(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*")
_PYTEST_RE = re.compile(r"^(?:python3?\s+-m\s+)?pytest\b")

# Real refusal-line shape, confirmed against the 177-session corpus:
# `PreToolUse:<Tool> hook error: [<hook path>]: <gate-name>: <message>`
_HOOK_REFUSAL_RE = re.compile(
    r"PreToolUse:(?P<tool>\w+) hook error: \[(?P<hook_path>[^\]]*)\]: "
    r"(?P<gate>[\w-]+):")


def classify_bash(command: str) -> str:
    """`command` -> "pytest"|"git"|"gh"|"other", per the issue's own
    definition ("neither pytest / git / gh"). Looks at the first real
    token after stripping leading `VAR=value` env-assignment prefixes —
    a compound `cd repo && git status` is still `git`, matching how a
    session actually spends that call."""
    stripped = _LEADING_ASSIGNMENT_RE.sub("", command or "").strip()
    if _PYTEST_RE.match(stripped):
        return "pytest"
    first = stripped.split(None, 1)[0] if stripped else ""
    if first == "git":
        return "git"
    if first == "gh":
        return "gh"
    return "other"


def bash_classification_summary(events: list[dict]) -> dict:
    """Bash-call breakdown across a session: total, per-class counts, and
    the "neither pytest/git/gh" share the issue measures directly."""
    counts = Counter()
    for u in ta.tool_use_events(events):
        if u["name"] != "Bash":
            continue
        counts[classify_bash(u["input"].get("command", ""))] += 1
    total = sum(counts.values())
    other = counts.get("other", 0)
    return {
        "total": total,
        "pytest": counts.get("pytest", 0),
        "git": counts.get("git", 0),
        "gh": counts.get("gh", 0),
        "other": other,
        "other_share": (other / total) if total else None,
    }


def hook_refusals(events: list[dict]) -> dict:
    """Every `tool_result` whose text matches the real PreToolUse-refusal
    shape, counted total and broken down by gate name — the up-front-
    contract mechanism targets exactly these gate names."""
    by_gate = Counter()
    total = 0
    for ev in events:
        if ev.get("type") != "user":
            continue
        for block in (ev.get("message") or {}).get("content") or []:
            if not (isinstance(block, dict) and block.get("type") == "tool_result"
                    and block.get("is_error")):
                continue
            text = ta._tool_result_text(block.get("content"))
            m = _HOOK_REFUSAL_RE.search(text)
            if not m:
                continue
            total += 1
            by_gate[m.group("gate")] += 1
    return {"total": total, "by_gate": dict(by_gate)}


def redundant_file_reads(events: list[dict]) -> dict:
    """`Read` call counts per `file_path`, collapsed across offsets (a
    second `Read` of the same file at a different offset is still a
    redundant trip back into it) — the issue's own "105 spawn.py re-
    reads" stat counts this way, not `repeated_read_offsets`' exact-
    offset repeats. Only files read more than once are returned."""
    counts = Counter()
    for u in ta.tool_use_events(events):
        if u["name"] != "Read":
            continue
        fp = u["input"].get("file_path")
        if fp:
            counts[fp] += 1
    redundant = {fp: c for fp, c in counts.items() if c > 1}
    return {"by_file": redundant,
            "top": sorted(redundant.items(), key=lambda kv: -kv[1])[:10]}


def named_offender_counts(events: list[dict], basenames: list[str]) -> dict:
    """Re-read counts for specific basenames regardless of directory —
    the issue names `spawn.py` and "the role's own record file"
    (`implementation.md` etc.) as the top offenders to track before/after."""
    reads = redundant_file_reads(events)["by_file"]
    out = {}
    for base in basenames:
        out[base] = sum(c for fp, c in reads.items() if fp.endswith(base))
    return out


def per_turn_breakdown(events: list[dict]) -> list[dict]:
    """One row per tool_use, in stream order — "what each turn's tool
    call was for" (Acceptance item 1). `bash_class` is set only for Bash
    calls; `hook_refused` is set when that call's result matched the
    hook-refusal shape."""
    results = ta.tool_result_index(events)
    rows = []
    for i, u in enumerate(ta.tool_use_events(events)):
        row = {"turn": i, "tool": u["name"]}
        if u["name"] == "Bash":
            row["bash_class"] = classify_bash(u["input"].get("command", ""))
        elif u["name"] == "Read":
            row["file_path"] = u["input"].get("file_path")
        r = results.get(u["tool_use_id"])
        if r is not None and r["is_error"]:
            m = _HOOK_REFUSAL_RE.search(r["text"])
            row["hook_refused"] = m.group("gate") if m else False
        rows.append(row)
    return rows


def analyze(path) -> dict:
    events = ta.parse_session_log(path)
    harness = ta.harness_fields(events)
    return {
        "session_log": str(path),
        "wall_clock_ms": harness.get("duration_ms"),
        "num_turns": harness.get("num_turns"),
        "bash": bash_classification_summary(events),
        "hook_refusals": hook_refusals(events),
        "redundant_reads": redundant_file_reads(events),
        "named_offenders": named_offender_counts(
            events, ["spawn.py", "implementation.md"]),
        "per_turn": per_turn_breakdown(events),
    }


def _fmt_md(report: dict) -> str:
    b = report["bash"]
    h = report["hook_refusals"]
    other_share = "n/a" if b["other_share"] is None else f"{b['other_share']:.0%}"
    lines = [
        f"# waste report: {report['session_log']}",
        "",
        f"- wall-clock: {report['wall_clock_ms']} ms, turns: {report['num_turns']}",
        f"- Bash calls: {b['total']} (pytest={b['pytest']}, git={b['git']}, "
        f"gh={b['gh']}, other={b['other']}, other_share={other_share})",
        f"- hook refusals: {h['total']} ({', '.join(f'{k}={v}' for k, v in h['by_gate'].items()) or 'none'})",
        f"- redundant re-reads (top): "
        f"{', '.join(f'{Path(fp).name}={c}' for fp, c in report['redundant_reads']['top']) or 'none'}",
        f"- named offenders: {report['named_offenders']}",
        "",
        "| turn | tool | detail |",
        "|---|---|---|",
    ]
    for row in report["per_turn"]:
        detail = row.get("bash_class") or row.get("file_path") or ""
        if row.get("hook_refused"):
            detail += f" [REFUSED: {row['hook_refused']}]"
        lines.append(f"| {row['turn']} | {row['tool']} | {detail} |")
    return "\n".join(lines)


def batch_summary(paths: list[str]) -> dict:
    """One `analyze()` per path, plus a corpus-level rollup — the shape
    used for the issue's before/after comparison across several real
    session logs."""
    reports = [analyze(p) for p in paths]
    total_bash = sum(r["bash"]["total"] for r in reports)
    total_other = sum(r["bash"]["other"] for r in reports)
    total_refusals = sum(r["hook_refusals"]["total"] for r in reports)
    offenders = Counter()
    for r in reports:
        for name, c in r["named_offenders"].items():
            offenders[name] += c
    return {
        "sessions": len(reports),
        "bash_total": total_bash,
        "bash_other_share": (total_other / total_bash) if total_bash else None,
        "hook_refusals_total": total_refusals,
        "hook_refusals_per_session": (total_refusals / len(reports)) if reports else None,
        "named_offenders_total": dict(offenders),
        "per_session": [
            {"session_log": r["session_log"], "wall_clock_ms": r["wall_clock_ms"],
             "num_turns": r["num_turns"], "bash_total": r["bash"]["total"],
             "bash_other_share": r["bash"]["other_share"],
             "hook_refusals": r["hook_refusals"]["total"],
             "named_offenders": r["named_offenders"]}
            for r in reports
        ],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session_log", nargs="?", help="path to a single session log")
    ap.add_argument("--batch", help="glob of session logs to summarize together")
    ap.add_argument("--md", action="store_true", help="markdown per-turn breakdown (single-file mode)")
    args = ap.parse_args(argv)
    if args.batch:
        paths = sorted(glob.glob(args.batch))
        if not paths:
            print(f"error: no files match {args.batch!r}", file=sys.stderr)
            return 1
        print(json.dumps(batch_summary(paths), indent=2, ensure_ascii=False))
        return 0
    if not args.session_log:
        print("error: give a session_log path or --batch <glob>", file=sys.stderr)
        return 1
    path = Path(args.session_log)
    if not path.is_file():
        print(f"error: session log not found: {path}", file=sys.stderr)
        return 1
    report = analyze(path)
    print(_fmt_md(report) if args.md else json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
