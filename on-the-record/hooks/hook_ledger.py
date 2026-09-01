#!/usr/bin/env python3
"""Fail-open ledger for hook crashes (issue #2093).

Platform semantics are fixed: exit 0 = success, exit 2 = block, every other
nonzero -- including the 1 a traceback produces -- is non-blocking.  A
crashing guard therefore *cannot* be made to fail closed.  What it can stop
doing is failing **silently**: every fail-open leaves one JSON line here, so
"guard X skipped" becomes a readable fact instead of an absence.

Location follows the existing hook-authored ledger precedent
(`contract-guard.sh`'s provenance log): a single env-overridable JSONL under
`~/.claude/on-the-record/`, not a repo-relative `runs/` path -- a hook
crashing in a consumer repo would otherwise scatter ledgers across every
checkout, where no watchdog can find them.

Standard library only, and the whole write is wrapped: logging must never
become a new deny path or change a verdict.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Optional, Sequence

__all__ = ["ledger_path", "input_digest", "record_fail_open"]

DEFAULT_LEDGER = os.path.join("~", ".claude", "on-the-record", "fail-open.jsonl")


def ledger_path() -> str:
    """The ledger file path: `$OTR_FAIL_OPEN_LEDGER`, else the default."""
    try:
        override = os.environ.get("OTR_FAIL_OPEN_LEDGER") or ""
        return os.path.expanduser(override or DEFAULT_LEDGER)
    except Exception:
        return ""


def input_digest(raw: object) -> str:
    """A short, stable, non-reversible fingerprint of the crashing input.

    The payload can carry anything the session typed, so the ledger records a
    digest, never the input itself.
    """
    try:
        if raw is None:
            data = b""
        elif isinstance(raw, (bytes, bytearray)):
            data = bytes(raw)
        else:
            data = str(raw).encode("utf-8", "replace")
        return "sha256:" + hashlib.sha256(data).hexdigest()[:16]
    except Exception:
        return "sha256:unavailable"


def record_fail_open(
    hook: str,
    argv: Optional[Sequence[str]] = None,
    digest: str = "",
    exit_code: Optional[int] = None,
    reason: str = "",
    fallback_fired: bool = False,
) -> bool:
    """Append one fail-open line to the ledger.  Returns True if it landed.

    Never raises, and never signals failure by any route other than the
    return value: a ledger that cannot be written must not change what a
    guard decided.

    issue #2962: `exit_code` and `fallback_fired` are recorded as their own
    fields, never folded into one merged "success" string -- a wrapper that
    survived a crash and a hook that actually succeeded must stay
    distinguishable by a reader who never sees the crash itself.
    """
    try:
        path = ledger_path()
        if not path:
            return False
        line = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": "fail-open",
            "hook": str(hook),
            "argv": [str(a) for a in (argv or [])],
            "digest": str(digest),
            "exit_code": exit_code,
            "reason": str(reason),
            "fallback_fired": bool(fallback_fired),
        }
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


if __name__ == "__main__":  # pragma: no cover - CLI shim for fail-open-wrapper.sh
    import sys

    _hook = sys.argv[1] if len(sys.argv) > 1 else ""
    _exit = sys.argv[2] if len(sys.argv) > 2 else ""
    _reason = sys.argv[3] if len(sys.argv) > 3 else ""
    _fallback = sys.argv[4] if len(sys.argv) > 4 else ""
    _argv = sys.argv[5:]
    try:
        _code = int(_exit)
    except ValueError:
        _code = None
    _raw = ""
    try:
        _raw = os.environ.get("OTR_FAIL_OPEN_INPUT", "")
    except Exception:
        _raw = ""
    record_fail_open(
        _hook, _argv, input_digest(_raw), _code, _reason,
        fallback_fired=_fallback in ("1", "true", "True"),
    )
    sys.exit(0)
