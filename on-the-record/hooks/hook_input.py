#!/usr/bin/env python3
"""Shared total input-parsing library for every registered hook (issue #2093).

The class of defect this exists to close: each hook grew its own ad-hoc
payload decode plus its own `cd <path> &&` extraction, and an edge input --
an unexpanded `~`, a heredoc body, unbalanced quotes, unicode, an empty or
100KB command, a missing `tool_input` -- could raise past the `json.loads`
try/except every hook already had.  Because the hook runtime treats any
nonzero-and-not-2 exit as non-blocking, the traceback made the guard skip
*silently*.

The contract of this module, and the only thing callers may rely on:

    NO FUNCTION HERE RAISES.  Ever.  For any `str`, `bytes`, `None`, or
    arbitrary object argument.

Failure is a returned value with a machine-readable `reason`, never an
exception, so the invalid state is unrepresentable past the parse boundary
instead of depending on ~58 call sites each remembering to catch.

Placement: this file lives next to the hooks, not under `gates/`, because a
zero-install hook cannot assume `gates/` exists in the consumer repo (see
`pr-preflight.sh` lines 7-9) -- and the consumer checkout is exactly where
the crash class bites.  Import direction is one-way and total: standard
library only.  Never import `gates/`, never import another hook.

Entry points take a **string**, never stdin: the survey found the payload
reaches python through an env var in the majority of hooks.
"""
from __future__ import annotations

import json
import os
import re
import shlex
from typing import NamedTuple, Optional, Union

__all__ = [
    "Payload",
    "Unparseable",
    "CdTarget",
    "NoCdTarget",
    "OpaqueCommand",
    "parse_payload",
    "tool_command",
    "cd_target",
    "cd_target_dir",
    "usable_dir",
    "resolved_cwd",
]

# A command longer than this is not parsed structurally.  Not a correctness
# limit -- a blast-radius limit: shlex over a 100KB pasted blob is the one
# input shape that turns a microsecond guard into a visible stall.
MAX_STRUCTURAL_COMMAND = 32768


class Payload(NamedTuple):
    """A successfully decoded hook payload."""

    data: dict

    @property
    def tool_name(self) -> str:
        name = self.data.get("tool_name")
        return name if isinstance(name, str) else ""

    @property
    def tool_input(self) -> dict:
        ti = self.data.get("tool_input")
        return ti if isinstance(ti, dict) else {}


class Unparseable(NamedTuple):
    """The payload could not be decoded into a hook payload object."""

    reason: str


class CdTarget(NamedTuple):
    """The command carries a leading `cd <path> &&`; `path` is user-expanded."""

    path: str


class NoCdTarget(NamedTuple):
    """The command was parsed and carries no leading `cd <path> &&`."""

    reason: str = "no-cd-prefix"


class OpaqueCommand(NamedTuple):
    """The command could not be structurally trusted; treat as unknown cwd."""

    reason: str


ParseResult = Union[Payload, Unparseable]
CdResult = Union[CdTarget, NoCdTarget, OpaqueCommand]

_CD_RE = re.compile(r"^\s*cd\s+(\S+)\s*&&")


def _as_text(raw: object) -> Union[str, Unparseable]:
    """Coerce anything to `str`, or explain why it cannot be one."""
    if raw is None:
        return Unparseable("none-input")
    if isinstance(raw, str):
        return raw
    if isinstance(raw, (bytes, bytearray)):
        try:
            return bytes(raw).decode("utf-8", "replace")
        except Exception:  # pragma: no cover - decode(errors="replace") cannot raise
            return Unparseable("undecodable-bytes")
    return Unparseable("non-text-input")


def parse_payload(raw: object) -> ParseResult:
    """Decode a hook payload.  Returns `Payload` or `Unparseable(reason)`.

    Accepts `str`, `bytes`, `None`, or any object.  Never raises.
    """
    text = _as_text(raw)
    if isinstance(text, Unparseable):
        return text
    if not text.strip():
        return Unparseable("empty-input")
    try:
        obj = json.loads(text)
    except (ValueError, RecursionError):
        return Unparseable("malformed-json")
    except Exception:
        # json.loads over hostile input has exactly one documented failure
        # mode, but this boundary's whole promise is that it is total -- an
        # undocumented one must not become a traceback in a consumer session.
        return Unparseable("json-decode-error")
    if not isinstance(obj, dict):
        return Unparseable("non-dict-payload")
    return Payload(obj)


def tool_command(payload: object) -> str:
    """The Bash `tool_input.command` string, or `""` when there is none.

    Accepts a `Payload`, an `Unparseable`, a raw dict, or anything else.
    """
    if isinstance(payload, Unparseable):
        return ""
    if isinstance(payload, Payload):
        data = payload.tool_input
    elif isinstance(payload, dict):
        ti = payload.get("tool_input")
        data = ti if isinstance(ti, dict) else {}
    else:
        return ""
    cmd = data.get("command")
    return cmd if isinstance(cmd, str) else ""


def _has_heredoc(command: str) -> bool:
    # `<<` starts a heredoc; `<<<` is a here-string.  Both make the text that
    # follows *data*, not command syntax, so a `cd` inside it is not a `cd`.
    return "<<" in command


def _quotes_balanced(command: str) -> bool:
    try:
        shlex.split(command)
    except ValueError:
        return False
    except Exception:
        return False
    return True


def cd_target(command: object) -> CdResult:
    """Resolve a leading `cd <path> &&` prefix out of a Bash command string.

    Returns `CdTarget(path)` with `~` expanded, `NoCdTarget(reason)` when the
    command is well-formed and carries no such prefix, or
    `OpaqueCommand(reason)` when the command cannot be structurally trusted
    (heredoc body, unbalanced quotes, oversize).  Never raises.
    """
    text = _as_text(command)
    if isinstance(text, Unparseable):
        return OpaqueCommand(text.reason)
    if not text.strip():
        return NoCdTarget("empty-command")
    if len(text) > MAX_STRUCTURAL_COMMAND:
        return OpaqueCommand("oversize-command")
    if _has_heredoc(text):
        return OpaqueCommand("heredoc")
    if not _quotes_balanced(text):
        return OpaqueCommand("unbalanced-quotes")
    m = _CD_RE.match(text)
    if not m:
        return NoCdTarget()
    raw_path = m.group(1)
    # Strip one layer of matching quotes the regex's `\S+` swept up, then
    # expand `~` -- the omission that made a `cd ~/x && ...` command resolve
    # to a literal "~/x" directory that does not exist (issue #2092).
    if len(raw_path) >= 2 and raw_path[0] == raw_path[-1] and raw_path[0] in "'\"":
        raw_path = raw_path[1:-1]
    try:
        expanded = os.path.expanduser(raw_path)
    except Exception:
        return OpaqueCommand("expanduser-failed")
    if not expanded:
        return NoCdTarget("empty-cd-path")
    return CdTarget(expanded)


def usable_dir(path: object) -> bool:
    """True when `path` is a string naming an existing directory.  Never raises.

    A `cd` target is *claimed*, not verified: `cd ~/work/repo && ...` names a
    directory that may not exist in this process's world at all.  Feeding that
    claim straight to `subprocess(cwd=...)` raises `FileNotFoundError` deep
    inside a guard -- the exact crash-then-skip-silently shape this issue
    exists to close, and the one the conformance matrix caught in
    `contract-guard.sh` on the tilde-cd-merge case.
    """
    if not isinstance(path, str) or not path:
        return False
    try:
        return os.path.isdir(path)
    except Exception:
        return False


def cd_target_dir(command: object) -> Optional[str]:
    """The command's `cd` target, but only when it exists as a directory.

    Returns `None` otherwise -- which every call site already handles as
    "no target repo override, use my own cwd".  Never raises.
    """
    result = cd_target(command)
    if not isinstance(result, CdTarget):
        return None
    return result.path if usable_dir(result.path) else None


def resolved_cwd(command: object, default: object = None) -> str:
    """The directory a command acts on: its `cd` target, else `default`.

    `default` defaults to the current process cwd.  Never raises: an
    unreadable cwd degrades to `""`, which callers already treat as
    "nothing to do" (`[ -n "$target_cwd" ] || exit 0`).
    """
    result = cd_target(command)
    if isinstance(result, CdTarget):
        return result.path
    if isinstance(default, str):
        return default
    try:
        return os.getcwd()
    except Exception:
        return ""
