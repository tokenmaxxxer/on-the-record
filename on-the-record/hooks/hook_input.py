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
    "tool_response_text",
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

_CD_STEP_RE = re.compile(r"^\s*cd\s+(\S+)\s*(?:&&|\|\||;|\n)")
_HEREDOC_OPEN_RE = re.compile(r"<<(-)?\s*(['\"]?)(\w+)\2")


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


def tool_response_text(raw: object) -> str:
    """Coerce a `PostToolUse` `tool_response` payload field to plain text
    for a heuristic substring/regex scan, or `""` when there is nothing to
    scan.  Never raises.

    `tool_response` is usually the tool's own stdout as a plain string --
    every existing consumer in this repo already applies exactly this
    coercion ad hoc (see `gate-registration-post-guard.sh`,
    `post-landing-obligation-gate.sh`, `retry-loop-bound.sh`: each does
    `isinstance(resp, str)` else `json.dumps(resp)` else `""` inline).
    This is that same coercion, shared, for a caller (issue #3129's
    amendment channel redesign) that needs to scan `tool_response` for a
    `gh` URL rather than reimplementing the pattern a fourth time. A
    structured/dict shape is serialized with `json.dumps` so a substring
    scan still works over it; anything that cannot be serialized, or is
    simply absent, reads as `""`.
    """
    if isinstance(raw, str):
        return raw
    if raw is None:
        return ""
    try:
        return json.dumps(raw)
    except (TypeError, ValueError):
        return ""


def _quotes_balanced(command: str) -> bool:
    try:
        shlex.split(command)
    except ValueError:
        return False
    except Exception:
        return False
    return True


def _strip_heredoc_bodies(command: str) -> Optional[str]:
    """Excise every heredoc BODY (the data between a `<<[-]DELIM` line and
    its terminator line) from `command`, leaving the operator/delimiter
    token itself in place so downstream splitting still sees the redirect
    happened.  Body text is data, not shell syntax (issue #3129 repair
    round 3): a `--body-file - <<'EOF' ... EOF` body can contain the
    literal substring `cd /x &&` as part of an issue body, and that must
    never be mistaken for an actual `cd`.

    Returns the excised text, or `None` when a heredoc is opened but this
    string never contains its terminator -- undecidable where the body
    ends, so the caller must treat the whole command as structurally
    opaque rather than guess.  Never raises.
    """
    out = []
    i = 0
    n = len(command)
    while True:
        m = _HEREDOC_OPEN_RE.search(command, i)
        if not m:
            out.append(command[i:])
            break
        out.append(command[i:m.end()])
        dash, delim = m.group(1), m.group(3)
        line_end = command.find("\n", m.end())
        if line_end == -1:
            # The redirect opens but this string ends on the same line --
            # no body is present in this string to strip.
            out.append(command[m.end():])
            i = n
            break
        out.append(command[m.end():line_end + 1])
        pos = line_end + 1
        terminated = False
        while pos <= n:
            next_nl = command.find("\n", pos)
            line = command[pos:next_nl if next_nl != -1 else n]
            check_line = line.lstrip("\t") if dash else line
            if check_line == delim:
                terminated = True
                i = (next_nl + 1) if next_nl != -1 else n
                break
            if next_nl == -1:
                break
            pos = next_nl + 1
        if not terminated:
            return None
    return "".join(out)


def _unwrap_enclosing_group(text: str) -> str:
    """Strip one layer of `( ... )` or `{ ... }` when it wraps the ENTIRE
    (whitespace-trimmed) string, returning the interior.  Returns `text`
    unchanged when there is no such wrapper, the brackets are unbalanced,
    or the closing bracket is not the string's own last character (a group
    that ends before the string does, e.g. `(cd /a); other`, has a sibling
    after it -- unwrapping would silently discard that sibling instead of
    leaving it for the caller to see as "not a bare leading cd").  Never
    raises.
    """
    stripped = text.strip()
    if not stripped:
        return text
    opening = stripped[0]
    closing = {"(": ")", "{": "}"}.get(opening)
    if closing is None:
        return text
    depth = 0
    in_squote = in_dquote = False
    n = len(stripped)
    i = 0
    while i < n:
        c = stripped[i]
        if in_squote:
            if c == "'":
                in_squote = False
        elif in_dquote:
            if c == "\\":
                i += 1
            elif c == '"':
                in_dquote = False
        elif c == "'":
            in_squote = True
        elif c == '"':
            in_dquote = True
        elif c == opening:
            depth += 1
        elif c == closing:
            depth -= 1
            if depth == 0:
                return stripped[1:i] if i == n - 1 else text
        i += 1
    return text


def cd_target(command: object) -> CdResult:
    """Resolve the `cd` prefix that determines a compound Bash command's
    effective working directory when it runs, walking every leading `cd`
    step in order (`cd /a && cd b && gh ...` resolves `b` relative to `/a`)
    and unwrapping any number of enclosing `( ... )` / `{ ... }` groups
    first (`(cd /a && gh ...)` resolves the same as the unwrapped form).

    Returns `CdTarget(path)` with `~` expanded and relative later steps
    joined onto the prior step, `NoCdTarget(reason)` when the command is
    well-formed and carries no leading `cd` at all, or `OpaqueCommand
    (reason)` when the command cannot be structurally trusted (an
    unterminated heredoc, unbalanced quotes, oversize).  Never raises.

    `OpaqueCommand` is the caller's signal to treat the cwd as UNKNOWN, not
    as "use my own default" -- issue #3129 repair round 3 found a caller
    (`amendment_channel.target_repo_for_command`, since removed by that
    issue's round-4 seam redesign, which stopped parsing command text for
    a target repo at all) that funneled this result through
    `resolved_cwd()`'s generic "cd target, else default" contract and got
    a silent, plausible-looking WRONG answer instead of a visible unknown,
    because the "default" it substituted was almost always itself a
    resolvable repo.  This function stays a pure resolver -- it never
    substitutes a default -- specifically so a stricter caller can tell
    "no cd" (safe to use its own default) apart from "cd present
    but not parseable with confidence" (not safe to guess).
    """
    text = _as_text(command)
    if isinstance(text, Unparseable):
        return OpaqueCommand(text.reason)
    if not text.strip():
        return NoCdTarget("empty-command")
    if len(text) > MAX_STRUCTURAL_COMMAND:
        return OpaqueCommand("oversize-command")
    stripped = _strip_heredoc_bodies(text)
    if stripped is None:
        return OpaqueCommand("unterminated-heredoc")
    if not _quotes_balanced(stripped):
        return OpaqueCommand("unbalanced-quotes")

    resolved: Optional[str] = None
    remaining = stripped
    while True:
        unwrapped = _unwrap_enclosing_group(remaining)
        if unwrapped != remaining:
            remaining = unwrapped
            continue
        m = _CD_STEP_RE.match(remaining)
        if not m:
            break
        raw_path = m.group(1)
        # Strip one layer of matching quotes the regex's `\S+` swept up, then
        # expand `~` -- the omission that made a `cd ~/x && ...` command
        # resolve to a literal "~/x" directory that does not exist (#2092).
        if len(raw_path) >= 2 and raw_path[0] == raw_path[-1] and raw_path[0] in "'\"":
            raw_path = raw_path[1:-1]
        try:
            expanded = os.path.expanduser(raw_path)
        except Exception:
            return OpaqueCommand("expanduser-failed")
        if not expanded:
            # A malformed empty `cd` target ends the walk with whatever was
            # already resolved (or nothing, on the first step) rather than
            # manufacturing an opaque result over one bad step.
            break
        resolved = (
            expanded
            if resolved is None or os.path.isabs(expanded)
            else os.path.join(resolved, expanded)
        )
        remaining = remaining[m.end():]

    if resolved is None:
        return NoCdTarget()
    return CdTarget(resolved)


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
