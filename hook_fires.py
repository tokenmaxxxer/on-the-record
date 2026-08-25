"""issue #2348: per-session sharding for the hook-fires counter (issue
#2028's append-only fire counter, `.orchestrate-hook-fires.log`), the same
conflict-elimination shape issue #2333 shipped for `consult-log.md`
(`consult.py`'s `_consult_trace_dir`/`_consult_session_shard_id`/
`_consult_trace_path`/`_consult_log_aggregate`).

The writer side is three always-on bash hooks (`directive.sh`,
`stop-gate.sh`, `stop-poll-rearm.sh`), not a long-running Python process, so
there is no process to cache a shard id on for the lifetime of a "session"
the way `consult.py` caches `_CONSULT_SESSION_SHARD_ID` per pid. Each hook
firing hashes the session_id off its own stdin JSON payload instead — the
same `sha256(session_id)[:24]` formula `directive.sh`'s pre-existing
monitor-notice marker already uses (warrant-hunt findings
docs/issue-947/reports/implementation/2026-08-12-hunt-monitor-unavailable-notice.md
and .../hunt-monitor-unavailable-notice-before-landing.md: hash, never a
character-substitution sanitizer, so distinct ids never collide). A stable
session_id maps every firing within one session to the same shard file
regardless of which of the three hooks fired or how many times; two
different sessions never share a shard, so two sessions committing their
own workspace's fires alongside their own deliverable never touch the same
path — the conflict class this issue removes.

`on-the-record/hooks/hook-fires.sh` is the bash-side sourced library the
three hook scripts call into (mirrors the existing `poll-rearm.sh`
precedent for shared cross-hook logic); it embeds the same hash formula
this module documents so the two sides stay in sync by construction (one
formula, described once, implemented in both languages because the writer
is bash and the reader/CLI is Python).
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

UNKNOWN_SHARD = "unknown"


def _hook_fires_shard_id(session_id: str | None) -> str:
    """`sha256(session_id)[:24]`, or `unknown` when session_id is missing —
    a malformed/absent payload must still get counted, just bucketed
    together rather than dropped (fails open, matching every other
    on-the-record hook's stdin-JSON handling)."""
    if not session_id:
        return UNKNOWN_SHARD
    return hashlib.sha256(session_id.encode("utf-8", "surrogatepass")).hexdigest()[:24]


def _hook_fires_dir(cwd: str | None = None) -> Path:
    """The shard directory, workspace-relative — `.orchestrate-hook-fires/`
    under the session workspace this hook fires in (never the shared
    on-the-record checkout), same per-workspace convention as the flat
    `.orchestrate-hook-fires.log` it replaces."""
    root = Path(cwd).resolve() if cwd else Path(".").resolve()
    return root / ".orchestrate-hook-fires"


def _hook_fires_path(session_id: str | None, cwd: str | None = None) -> Path:
    """The shard file this session's firings land in."""
    return _hook_fires_dir(cwd) / f"{_hook_fires_shard_id(session_id)}.log"


def _hook_fires_aggregate(cwd: str | None = None) -> str:
    """Reader/aggregator reconstructing the pre-#2348 single-file
    chronological view. Shard filenames are `sha256(session_id)[:24]`, not
    a timestamp, so — unlike `_consult_log_aggregate()`'s filename sort —
    filename order carries no time information; every line already starts
    with its own fixed-width UTC timestamp
    (`%Y-%m-%dT%H:%M:%SZ`), so sorting the merged LINES (not the files)
    reproduces chronological order exactly. Empty string, matching the old
    "file not found" empty state, when no shard has ever been written."""
    d = _hook_fires_dir(cwd)
    if not d.is_dir():
        return ""
    lines: list[str] = []
    for p in sorted(d.glob("*.log")):
        lines.extend(p.read_text(encoding="utf-8").splitlines())
    lines.sort()
    return "".join(line + "\n" for line in lines)
