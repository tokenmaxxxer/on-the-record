"""Advancing / waiting / stalled for one live session (issue #3275).

`HEALTHY-CONFIRMED` used to mean "the session's log file grew since the last
observation". That is a liveness proxy, not a progress measure: a session
waiting on a background dispatch polls it in a loop (`ps aux | grep ...`,
`tail`, repeated status checks), grows its log forever, and never advances.
Such a session scored maximally healthy while producing nothing, and the
operator noticed it as "why do the consumer sessions keep sitting still"
before any instrument did.

Log growth answers "is it breathing". It cannot answer "is it getting
anywhere". This module separates the two, so three states stay three:

- ``ADVANCING`` -- the workspace gained or changed real content since the
  last observation.
- ``WAITING``   -- the log grew, but every tool call behind that growth only
  observed. Alive, not advancing. Reported, never counted as healthy
  progress.
- ``STALLED``   -- nothing grew at all. Left to the callers that already
  detect it; this module reports ``UNKNOWN`` rather than claiming it.

Deliberately conservative in one direction: a session is called ``WAITING``
only when the evidence positively says so (recent tool calls exist and all of
them observe). Anything unreadable, absent or ambiguous returns ``UNKNOWN``,
never ``WAITING`` -- misreporting a working session as idle invites an
operator to interrupt real work, which costs more than a missed nudge. That
asymmetry is the same one this repository applies to every other check that
can fail to observe: absence of evidence is not evidence of absence.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ADVANCING = "ADVANCING"
WAITING = "WAITING"
UNKNOWN = "UNKNOWN"

# How many trailing tool calls decide the verdict. Small enough that a
# session which just started polling is caught quickly; large enough that one
# incidental `ls` between two real edits cannot flip a working session to
# WAITING.
TAIL_TOOL_CALLS = 8

# Bytes of the log tail parsed. A session log line is JSON per event and can
# be large; this bounds the read without needing the whole file.
TAIL_BYTES = 200_000

# Tools that never change anything by themselves.
_OBSERVE_ONLY_TOOLS = frozenset({"Read", "Glob", "Grep", "TaskOutput", "NotebookRead"})

# Tools that change things. Their presence is enough to say "not merely
# observing", regardless of what the command text looks like.
_MUTATING_TOOLS = frozenset({"Write", "Edit", "NotebookEdit", "MultiEdit"})

# A Bash command counts as observation-only when its *first* word is one of
# these and it contains no shell operator that could hide a mutation. Keyed on
# the leading command rather than a substring search, so `git commit` is never
# mistaken for observation because the word "status" appears later in it.
_OBSERVE_ONLY_COMMANDS = frozenset({
    "ps", "ls", "tail", "head", "cat", "stat", "pgrep", "pwd", "wc",
    "find", "grep", "echo", "date", "df", "du", "sleep", "which", "test",
})

# Sub-commands of `git` and `gh` that only read.
_OBSERVE_ONLY_SUBCOMMANDS = {
    "git": frozenset({"status", "log", "diff", "show", "branch", "remote",
                       "rev-parse", "ls-files", "ls-remote", "config"}),
    "gh": frozenset({"pr", "issue", "api", "repo", "run"}),  # narrowed below
}

# `gh pr merge`, `gh issue create` etc. mutate; only these read.
_GH_READ_VERBS = frozenset({"view", "list", "diff", "checks", "status"})

# Any of these means the command may do more than it appears to.
_SHELL_OPERATORS = re.compile(r"(?:\|\||&&|[;>]|\$\(|`)")


def _looks_observe_only(command: str) -> bool:
    """True only when the command demonstrably cannot change anything."""
    cmd = (command or "").strip()
    if not cmd:
        return False
    # A pipeline into a pager/filter is still observation; a redirect or a
    # chained command is not, because the tail can mutate.
    if _SHELL_OPERATORS.search(cmd):
        return False
    parts = cmd.split()
    head = parts[0]
    if head == "cd" and len(parts) > 2:
        # `cd X <something>` -- the something decides.
        head = parts[2]
        parts = parts[2:]
    if head in _OBSERVE_ONLY_COMMANDS:
        return True
    if head in ("git", "gh") and len(parts) > 1:
        sub = parts[1]
        if head == "git":
            return sub in _OBSERVE_ONLY_SUBCOMMANDS["git"]
        # gh <noun> <verb>
        if sub in _OBSERVE_ONLY_SUBCOMMANDS["gh"]:
            verb = parts[2] if len(parts) > 2 else ""
            return verb in _GH_READ_VERBS
    return False


def recent_tool_calls(log_path: Path | None, limit: int = TAIL_TOOL_CALLS
                       ) -> list[tuple[str, str]]:
    """The last `limit` (tool_name, command_or_empty) pairs from a session log.

    Returns an empty list on any unreadable or absent log -- the caller must
    treat that as UNKNOWN, not as evidence of idleness.
    """
    if not log_path:
        return []
    try:
        with open(log_path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - TAIL_BYTES))
            blob = f.read()
    except (OSError, ValueError):
        return []
    calls: list[tuple[str, str]] = []
    for raw in blob.decode("utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(ev, dict) or ev.get("type") != "assistant":
            continue
        message = ev.get("message")
        if not isinstance(message, dict):
            continue
        for block in message.get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = str(block.get("name") or "")
            args = block.get("input")
            command = ""
            if isinstance(args, dict):
                command = str(args.get("command") or "")
            calls.append((name, command))
    return calls[-limit:]


def classify(log_path: Path | None, workspace_changed: bool | None) -> str:
    """ADVANCING / WAITING / UNKNOWN for one session.

    `workspace_changed` is the caller's own answer to "did this session's
    workspace gain or change content since the last observation". `None`
    means the caller could not tell, which is not the same as `False`.
    """
    if workspace_changed:
        return ADVANCING
    calls = recent_tool_calls(log_path)
    if not calls:
        return UNKNOWN
    for name, command in calls:
        if name in _MUTATING_TOOLS:
            return ADVANCING
        if name in _OBSERVE_ONLY_TOOLS:
            continue
        if name == "Bash":
            if _looks_observe_only(command):
                continue
            # A Bash call we cannot prove is read-only may well have done
            # work; refuse to call this session idle on it.
            return UNKNOWN
        # Any other tool (Task, Monitor, web fetches, MCP calls...) is not
        # something this module can classify. Say so.
        return UNKNOWN
    # Every one of the recent calls demonstrably only observed.
    return WAITING


def describe(state: str) -> str:
    if state == ADVANCING:
        return "진행 중(산출물 변화 확인됨)"
    if state == WAITING:
        return ("대기 중 — 최근 도구 호출이 전부 관측 전용이다. "
                "살아있지만 나아가고 있지는 않다")
    return "판정 불가(관측 근거 부족) — 대기로 단정하지 않는다"
