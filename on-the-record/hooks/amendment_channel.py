#!/usr/bin/env python3
"""Amendment channel (issue #3129): the local-file bridge that lets an
orchestrator's mid-flight issue-body edit reach a spawned worker session
that already read the issue once at spawn and never re-reads it.

Two channels exist today and both fail for a spawned worker: cross-session
messages require the RECIPIENT's user to approve, and a headless worker has
nobody to approve them, so every message expires undelivered; amending the
issue body reaches `check_runner` (which re-reads the body to score) but
not the running process, which never re-reads it either.

The seam this uses instead: `PostToolUse` fires on every tool call in a
worker session and its output lands in that session's context
(`hookSpecificOutput.additionalContext`). This module is invoked from that
hook on every tool call, so it must never call `gh` (a network round trip
on every tool use is the same tick-budget cost that made the watchdog
delta-gated) and must never raise (a PostToolUse hook that crashes fails
open per `fail-open-wrapper.sh`, silently dropping the one channel this
issue exists to add -- every public function here returns a value instead,
same total-function contract as `hook_input.py` next to it).

State (two local JSON files, issue #3129's design choice):

  MARKER  <state_dir>/issue-<n>.marker.json      {"version": int, ...}
  SEEN    <state_dir>/seen/<session>__issue-<n>.json   {"absorbed_version": int}

`version` is an explicit monotonic counter written into the marker's
*content*, not read off the filesystem's mtime -- mtime granularity differs
between Linux (sub-second) and macOS (historically 1s on some filesystems),
so two writes in the same tick could be indistinguishable by mtime alone.
The state machine that gives the two behaviors the issue calls "the
substance of the work":

  fires once per amendment   -- a notice only fires when marker.version is
                                 STRICTLY GREATER than this session's last
                                 absorbed_version for that issue.
  stops after absorption      -- the moment a notice is about to fire, this
                                 session's SEEN file is updated to
                                 marker.version FIRST, so a second call
                                 with no new amendment (version unchanged)
                                 compares equal and stays quiet. A new
                                 `gh issue edit ... --body` bumps version
                                 again and the cycle repeats.

Never a blocking gate: the caller only ever gets a string to fold into
context, or None. Nothing here can deny a tool call.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_input  # noqa: E402

STATE_DIR_ENV = "OTR_AMENDMENT_STATE_DIR"

# Matches `gh issue edit 123 ...` anywhere a shell would start a new
# command (start of string, or after `;`/`&&`/`||`/`|`) -- deliberately
# permissive about what comes after the issue number since the body flag
# is checked separately.
_GH_ISSUE_EDIT_RE = re.compile(
    r"(?:^|[;&|]\s*)gh\s+issue\s+edit\s+(\d+)\b"
)
_BODY_FLAG_RE = re.compile(r"--body(?:-file)?(?:=|\s|$)")
_BRANCH_ISSUE_RE = re.compile(r"^issue-(\d+)\b")
_NOTE_MAX = 2000


def default_state_dir() -> str:
    override = os.environ.get(STATE_DIR_ENV)
    if override:
        return override
    return os.path.join(os.environ.get("TMPDIR", "/tmp"), "otr-amendment")


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def marker_path(state_dir: str, issue: str) -> str:
    return os.path.join(state_dir, "issue-%s.marker.json" % _safe(str(issue)))


def seen_path(state_dir: str, session_id: str, issue: str) -> str:
    return os.path.join(
        state_dir, "seen", "%s__issue-%s.json" % (_safe(session_id), _safe(str(issue)))
    )


def _atomic_write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.tmp.%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def read_marker(state_dir: str, issue: str) -> Optional[dict]:
    """The current amendment marker for `issue`, or None if absent/corrupt.

    Never raises: a missing file, a permission error, or malformed JSON all
    read as "no amendment" (fail open) rather than crashing the caller's
    PostToolUse hook.
    """
    try:
        with open(marker_path(state_dir, issue), "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("version"), int):
        return None
    return data


def write_amendment(state_dir: str, issue: str, note: str = "") -> Optional[int]:
    """Bump the amendment marker for `issue` and return the new version.

    Called from the orchestrator's own PostToolUse call when it edits an
    issue body. Read-increment-write is not atomic across processes (two
    concurrent orchestrators amending the same issue in the same instant
    could race), but the failure mode of a lost increment here is a missed
    notice tick, not a wrong one -- the next amendment still bumps version
    past whatever a worker last absorbed. Returns None on any local I/O
    failure (never raises): a write that cannot land degrades to "the
    worker keeps its stale brief", the same shape as if this channel did
    not exist -- never a crash of the orchestrator's own hook.
    """
    try:
        existing = read_marker(state_dir, issue)
        version = (existing.get("version") if existing else 0) + 1
        data = {
            "version": version,
            "written_at": datetime.now(timezone.utc).isoformat(),
            "note": note[:_NOTE_MAX],
        }
        _atomic_write_json(marker_path(state_dir, issue), data)
        return version
    except OSError:
        return None


def _read_seen(state_dir: str, session_id: str, issue: str) -> int:
    try:
        with open(seen_path(state_dir, session_id, issue), "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return 0
    if not isinstance(data, dict):
        return 0
    v = data.get("absorbed_version")
    return v if isinstance(v, int) else 0


def _write_seen(state_dir: str, session_id: str, issue: str, version: int) -> None:
    _atomic_write_json(seen_path(state_dir, session_id, issue), {"absorbed_version": version})


def format_notice(issue: str, marker: dict) -> str:
    note = marker.get("note") or ""
    written_at = marker.get("written_at", "unknown time")
    base = (
        "[amendment] issue #%s was amended by the orchestrator at %s -- "
        "re-read it before continuing. This is advisory: decide whether "
        "the correction is right, do not halt on it." % (issue, written_at)
    )
    if note:
        base += " Note: %s" % note
    return base


def check_notice(state_dir: str, session_id: str, issue: str) -> Optional[str]:
    """Fire the notice for `issue` at most once per amendment for `session_id`.

    Returns the notice text the first time this session observes a marker
    version it has not yet absorbed, and None on every subsequent call
    until a NEW amendment bumps the version again. Never raises: any local
    I/O failure here just means this tick stays quiet and the next tool
    call re-checks the same comparison (version still unabsorbed), so a
    transient failure delays a notice by one tick instead of losing it or
    crashing the hook.
    """
    try:
        marker = read_marker(state_dir, issue)
        if marker is None:
            return None
        version = marker["version"]
        seen = _read_seen(state_dir, session_id, issue)
        if version <= seen:
            return None
        # Absorb BEFORE returning: the write below is what makes this
        # amendment stop being announced on the very next call, even if
        # nothing downstream reads the return value.
        _write_seen(state_dir, session_id, issue, version)
        return format_notice(issue, marker)
    except OSError:
        return None


def _extract_note(command: str, cwd: str) -> str:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return ""
    for i, tok in enumerate(tokens):
        if tok in ("--body", "--body-file") and i + 1 < len(tokens):
            value = tokens[i + 1]
        elif tok.startswith("--body="):
            value = tok[len("--body="):]
        elif tok.startswith("--body-file="):
            value = tok[len("--body-file="):]
        else:
            continue
        if tok in ("--body-file",) or tok.startswith("--body-file="):
            path = value if os.path.isabs(value) else os.path.join(cwd or ".", value)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read(_NOTE_MAX)
            except OSError:
                return ""
        return value[:_NOTE_MAX]
    return ""


def issue_for_cwd(cwd: str) -> Optional[str]:
    """The issue number this session's own branch names, or None.

    A worker session's branch is always `issue-<n>/<role>` (spawn.py's own
    naming convention). Local `git` plumbing only -- no network -- so this
    costs one fast subprocess call per tool use, not a `gh` round trip.
    """
    if not cwd or not isinstance(cwd, str) or not os.path.isdir(cwd):
        return None
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    m = _BRANCH_ISSUE_RE.match(r.stdout.strip())
    return m.group(1) if m else None


def maybe_write_from_command(state_dir: str, tool_name: str, command: str, cwd: str) -> None:
    """Detect `gh issue edit <n> ... --body|--body-file ...` and bump that
    issue's marker. Fires on the command text alone (no `tool_response`
    success check) -- this channel is advisory, and a false-positive bump
    from a failed `gh` call costs a worker one extra (harmless, non-
    blocking) re-read, not a wrong decision.
    """
    if tool_name != "Bash" or not command:
        return
    m = _GH_ISSUE_EDIT_RE.search(command)
    if not m or not _BODY_FLAG_RE.search(command):
        return
    issue = m.group(1)
    note = _extract_note(command, cwd)
    write_amendment(state_dir, issue, note=note)


def run_hook(payload_text: object, state_dir: Optional[str] = None) -> Optional[str]:
    """The full PostToolUse behavior: maybe record an amendment, maybe
    return a notice string for the caller to print. Never raises."""
    state_dir = state_dir or default_state_dir()
    payload = hook_input.parse_payload(payload_text)
    if isinstance(payload, hook_input.Unparseable):
        return None
    data = payload.data
    cwd = data.get("cwd")
    cwd = cwd if isinstance(cwd, str) else ""
    session_id = data.get("session_id")

    try:
        maybe_write_from_command(
            state_dir, payload.tool_name, hook_input.tool_command(payload), cwd
        )
    except Exception:  # pragma: no cover - defense in depth; see module docstring
        pass

    if not isinstance(session_id, str) or not session_id or not cwd:
        return None
    try:
        issue = issue_for_cwd(cwd)
    except Exception:  # pragma: no cover
        return None
    if not issue:
        return None
    return check_notice(state_dir, session_id, issue)


def main() -> int:
    try:
        payload_text = sys.stdin.read()
    except Exception:
        return 0
    try:
        notice = run_hook(payload_text)
    except Exception:
        return 0
    if notice:
        out = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": notice}}
        try:
            sys.stdout.write(json.dumps(out))
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
