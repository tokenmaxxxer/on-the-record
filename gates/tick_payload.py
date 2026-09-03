"""What every wake carries (issue #3293, stage 2).

`poll_heartbeat_delta.py` suppresses any line identical to the previous
tick. That answers "did this line change" and cannot answer "does this
matter", because the second requires knowing what a session was supposed to
be doing -- which the orchestrator knows and a regex does not.

Three defects went unreported through it on 2026-09-03, each found only by
opening files by hand, two of them after the round had already dispatched:
a control arm shipped with the real skill's guidance still in its front
matter; the two arms mounted 352 files against 2; and the mount instrument
keyed on a hardcoded path and reported `mounted: []` for arms that had
mounted correctly. Every tick through all three said HEALTHY-CONFIRMED. Note
the shape -- each was a session doing exactly what it was told and producing
a wrong artifact, which is the case a difference-based filter is blindest to.

So the tick stops deciding and starts delivering: per session, what it wrote
and what it ran, every tick, unsuppressed. And when nothing is running, what
is still outstanding -- because "done" and "nobody started the next thing"
are different states that look identical when the room simply goes quiet.

Cost is the real constraint, not an afterthought. Measured on a live roster:
two sessions, 7 and 51 changed files, 8 and 2 tool calls => ~587 tokens per
tick, ~17.6K/hour, ~141K over eight hours. That is the term that dominates
agent cost, so the caps below are load-bearing, and a capped block always
says it was capped -- a silent truncation would reintroduce the very thing
this module removes.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

MAX_FILES_PER_SESSION = 12
MAX_CALLS_PER_SESSION = 8
MAX_COMMAND_CHARS = 100
IDLE_ITEMS_PER_LABEL = 4

# Paths the harness writes on its own schedule. A change confined to these
# is bookkeeping, not the session getting anywhere. Same list
# `gates/session_progress.py` applies -- imported from there rather than
# copied, so the two cannot drift.
try:  # pragma: no cover - import shape differs by caller
    from session_progress import _HARNESS_WRITTEN
except ImportError:  # pragma: no cover
    _HARNESS_WRITTEN = ("/.on-the-record/", "/.git/", "/runs/",
                        "/reports/consult-log/")


# The separator after the cd may be `&&`, `;`, or a bare newline -- the
# newline form is what sessions actually emit most often, and omitting it
# left the live payload still showing nothing but the cd.
_CD_PREFIX_RE = re.compile(
    r"^cd\s+(?:'[^']*'|\"[^\"]*\"|\S+)[ \t]*(?:&&|;|\n)\s*")


def _strip_workspace_cd(command: str) -> str:
    """Drop a leading `cd <workspace> &&` so the actual command survives.

    Spawned sessions prefix nearly every Bash call with a cd into their own
    workspace, whose path is ~90 characters. On the first live tick of this
    payload that prefix consumed the entire display budget: six different
    commands all rendered as the same truncated `cd .../work/video_producer-…`,
    so the orchestrator could see that the session ran something and not
    what. Removing the prefix -- and only a prefix that is exactly a cd
    followed by a separator -- puts the budget back on the part that
    carries the judgment.
    """
    stripped = _CD_PREFIX_RE.sub("", command, count=1)
    return stripped if stripped else command


def changed_files(work: Path, since_ts: float, now: float | None = None
                   ) -> tuple[list[str], int]:
    """(paths changed since `since_ts`, total found before capping).

    Returns the total separately so the caller can say "showing 12 of 51"
    rather than quietly showing 12.
    """
    out: list[str] = []
    total = 0
    try:
        for p in Path(work).rglob("*"):
            rel = "/" + str(p).replace(str(work), "").lstrip("/")
            if any(seg in rel for seg in _HARNESS_WRITTEN):
                continue
            try:
                if not p.is_file() or p.stat().st_mtime <= since_ts:
                    continue
            except OSError:
                continue
            total += 1
            if len(out) < MAX_FILES_PER_SESSION:
                out.append(rel.lstrip("/"))
    except OSError:
        return out, total
    return out, total


def collapse_calls(calls: list[tuple[str, str]]) -> list[str]:
    """Tool calls as display lines, consecutive identical ones collapsed.

    Six `ps aux | grep` calls in a row IS the waiting signal; printing it
    once with a count states it without spending six lines on it.
    """
    rendered: list[str] = []
    for name, command in calls:
        text = _strip_workspace_cd((command or "").strip()).replace("\n", " ; ")
        if len(text) > MAX_COMMAND_CHARS:
            text = text[:MAX_COMMAND_CHARS] + "…"
        line = f"{name}: {text}" if text else name
        if rendered and rendered[-1].split(" ×")[0] == line:
            prev = rendered[-1]
            n = int(prev.split(" ×")[1]) + 1 if " ×" in prev else 2
            rendered[-1] = f"{line} ×{n}"
        else:
            rendered.append(line)
    return rendered


def session_block(key: str, entry: dict, since_ts: float, state_verdict: str,
                   recent_calls: list[tuple[str, str]]) -> list[str]:
    """One session's unsuppressed activity, as display lines."""
    work = entry.get("work")
    lines = [f"[session] {key}: {state_verdict}"]
    if not work:
        lines.append("    (no workspace recorded -- cannot list changes)")
    else:
        files, total = changed_files(Path(work), since_ts)
        if total == 0:
            lines.append("    files: none since last tick")
        else:
            shown = f"{len(files)} of {total}" if total > len(files) else str(total)
            lines.append(f"    files ({shown}):")
            lines.extend(f"      {f}" for f in files)
            if total > len(files):
                lines.append(f"      … {total - len(files)} more not shown "
                             f"(cap {MAX_FILES_PER_SESSION})")
    if not recent_calls:
        lines.append("    calls: none readable")
    else:
        shown_calls = collapse_calls(recent_calls[-MAX_CALLS_PER_SESSION:])
        extra = len(recent_calls) - MAX_CALLS_PER_SESSION
        lines.append("    calls:")
        lines.extend(f"      {c}" for c in shown_calls)
        if extra > 0:
            lines.append(f"      … {extra} earlier not shown "
                         f"(cap {MAX_CALLS_PER_SESSION})")
    return lines


def idle_block(outstanding: dict) -> list[str]:
    """What a tick carries when nothing is running.

    Never a "monitoring active" placeholder -- issue #1732 removed exactly
    that, and it must not come back. Either there is outstanding work, and
    it is named, or there is not, and saying so is itself the signal that
    the goal may be complete and the monitor can be stopped.
    """
    lines = ["[idle] no sessions running"]
    named = False
    for label, items in sorted(outstanding.items()):
        if not items:
            continue
        named = True
        # Capped hard and low. The first live idle tick listed 26 board
        # branches at ~700 tokens -- on an idle roster, which is the tick
        # that repeats most. The orchestrator needs to know outstanding
        # work exists and roughly what it is; the full list is one `gh`
        # call away when it decides to look.
        head = [str(i) for i in items[:IDLE_ITEMS_PER_LABEL]]
        more = len(items) - len(head)
        lines.append(f"    {label} ({len(items)}): {', '.join(head)}"
                     + (f" … +{more}" if more > 0 else ""))
    if not named:
        lines.append("    nothing outstanding was found -- if that is right, "
                     "the goal is done and this monitor can be stopped "
                     "(spawn.py monitor-stop --owner <token>)")
    return lines
