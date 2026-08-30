#!/usr/bin/env python3
"""Record-to-PR timeline decomposition (issue #2527's own method,
re-run for issue #2847).

#2527 measured one session by hand: first record Write/Edit time vs
first code Edit/Write time, a count of record Write/Edit calls, a count
of hook refusals, and a count of git-inspection (`diff`/`status`/`log`/
`show`) calls in the phase after the first record write. This module is
that same extraction made re-runnable over `trajectory_analyzer`'s
already-parsed event stream, so a later re-measurement is not a fresh
hand re-derivation each time (same shape as `session_waste_metrics.py`,
issue #2409).

  python3 scripts/record_to_pr_timeline.py <session_log>
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import trajectory_analyzer as ta  # noqa: E402
import session_waste_metrics as swm  # noqa: E402 -- reuse #2409's hook-refusal
# detector (a real `PreToolUse:<Tool> hook error: [...]: <gate>:` line) rather
# than a bare `is_error` count, which also catches non-gate failures (a grep
# with no matches, a syntax error) that #2527 did not mean by "refusal".

_RECORD_PATH_RE = re.compile(r"docs/issue-[^/]+/reports/")
_NON_CODE_PATH_RE = re.compile(r"/docs/|^docs/|/tmp/")
_GIT_INSPECT_LINE_RE = re.compile(r"^(?:[\w./-]+=\S+\s+)*git\s+(diff|status|log|show)\b")
_GIT_COMMIT_LINE_RE = re.compile(r"^(?:[\w./-]+=\S+\s+)*git\s+commit\b")


def _command_lines(command: str):
    """Split a (possibly multi-line, `&&`-joined) shell command into
    candidate statement lines. A command embedding another session's log
    text (e.g. Python source scanning a *different* transcript for the
    string "git commit") must not be mistaken for this session actually
    running `git commit` — matching is anchored to the start of a line
    (after stripping a leading `cd ...;`/`&&` segment), not a bare
    substring search over the whole string."""
    for raw_line in command.replace("&&", "\n").replace(";", "\n").splitlines():
        yield raw_line.strip()


def _ts(events, idx):
    return events[idx].get("timestamp")


def _parse_ts(ts):
    from datetime import datetime
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")


def _hook_refusal_events(events):
    """`(index, timestamp, gate)` for every real gate refusal, reusing
    #2409's `session_waste_metrics._HOOK_REFUSAL_RE` shape so "refusal"
    means the same thing here it did there — a `PreToolUse:<Tool> hook
    error: [...]: <gate>:` line, not any `is_error` tool_result (a grep
    with no hits or a syntax error is not a refusal)."""
    out = []
    for i, ev in enumerate(events):
        if ev.get("type") != "user":
            continue
        for block in (ev.get("message") or {}).get("content") or []:
            if not (isinstance(block, dict) and block.get("type") == "tool_result"
                    and block.get("is_error")):
                continue
            text = ta._tool_result_text(block.get("content"))
            m = swm._HOOK_REFUSAL_RE.search(text)
            if m:
                out.append((i, ev.get("timestamp"), m.group("gate")))
    return out


def analyze(path) -> dict:
    events = ta.parse_session_log(path)
    tu = ta.tool_use_events(events)
    tri = ta.tool_result_index(events)

    session_start = None
    for ev in events:
        if ev.get("timestamp"):
            session_start = ev["timestamp"]
            break
    session_end = None
    for ev in events:
        if ev.get("timestamp"):
            session_end = ev["timestamp"]

    refusal_events = _hook_refusal_events(events)  # (index, timestamp, gate) tuples
    refusals_total = len(refusal_events)

    first_record_write = None
    first_code_edit = None
    first_commit_attempt = None
    record_write_calls = 0
    refusals_post_record = 0
    git_inspect_post_record = 0

    for e in tu:
        idx = e["index"]
        ts = _ts(events, idx)
        is_error = bool((tri.get(e["tool_use_id"]) or {}).get("is_error"))

        if e["name"] in ("Write", "Edit", "MultiEdit"):
            fp = e["input"].get("file_path", "") or ""
            if _RECORD_PATH_RE.search(fp):
                record_write_calls += 1
                if first_record_write is None:
                    first_record_write = ts
            elif not _NON_CODE_PATH_RE.search(fp):
                if first_code_edit is None and not is_error:
                    first_code_edit = ts

        if e["name"] == "Bash":
            cmd = e["input"].get("command", "") or ""
            lines = list(_command_lines(cmd))
            if first_commit_attempt is None and any(
                    _GIT_COMMIT_LINE_RE.match(l) for l in lines):
                first_commit_attempt = ts
            if (first_record_write is not None and ts and ts >= first_record_write
                    and any(_GIT_INSPECT_LINE_RE.match(l) for l in lines)):
                git_inspect_post_record += 1

    if first_record_write is not None:
        refusals_post_record = sum(
            1 for (_idx, rts, _gate) in refusal_events
            if rts and rts >= first_record_write)

    def dt(ts):
        if ts is None or session_start is None:
            return None
        return (_parse_ts(ts) - _parse_ts(session_start)).total_seconds() / 60.0

    total_min = dt(session_end)
    return {
        "session_log": str(path),
        "session_start": session_start,
        "session_end": session_end,
        "total_minutes": total_min,
        "first_record_write": first_record_write,
        "first_record_write_min": dt(first_record_write),
        "first_code_edit": first_code_edit,
        "first_code_edit_min": dt(first_code_edit),
        "first_commit_attempt": first_commit_attempt,
        "first_commit_attempt_min": dt(first_commit_attempt),
        "order_inverted": (
            first_record_write is not None and first_code_edit is not None
            and first_record_write < first_code_edit
        ),
        "record_write_calls": record_write_calls,
        "refusals_total": refusals_total,
        "refusals_by_gate": dict(Counter(g for _i, _t, g in refusal_events)),
        "refusals_post_record": refusals_post_record,
        "git_inspect_post_record": git_inspect_post_record,
        "record_to_end_share": (
            (total_min - dt(first_record_write)) / total_min
            if total_min and dt(first_record_write) is not None and total_min > 0
            else None
        ),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session_log")
    args = ap.parse_args(argv)
    path = Path(args.session_log)
    if not path.is_file():
        print(f"error: session log not found: {path}", file=sys.stderr)
        return 1
    print(json.dumps(analyze(path), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
