"""issue #2348: per-session sharding for the deviation log (issue #803's
deviation loop), the same conflict-elimination shape issue #2333 shipped
for `consult-log.md` — same append-only + concurrent-writers + one-shared-
path pattern, applied to a different artifact.

Two differences from `consult.py`'s consult-log sharding drove a different
shard-id and aggregation scheme here:

1. The writer is the session itself, appending a line by hand via its own
   Edit/Write tool calls mid-task — never a subprocess `spawn.py` can cache
   a shard id inside for a process's lifetime (`consult.py`'s
   `_CONSULT_SESSION_SHARD_ID`) or a bash hook can hash from a stdin JSON
   payload it always receives (`hook_fires.py`'s `_hook_fires_shard_id()`).
   The one identity a session can read reliably and repeatedly across an
   entire session is `$CLAUDE_CODE_SESSION_ID` (present in every tool call's
   environment). `_deviation_log_shard_id()` hashes that, but ALSO prefixes
   a timestamp — reusing an existing shard already written by this session
   this issue+role, or minting one on first use — so the aggregate stays
   filename-sortable-is-chronological, `consult-log.md`'s own property.
2. A deviation-log entry can wrap several physical lines (see
   docs/issue-2207/reports/conformance-review/deviation-log.md for a real
   multi-line entry). Sharding by whole file rather than by line matters
   more here than it did for hook-fires/consult-log's one-line entries: a
   line-level interleave across two sessions' shards would splice one
   entry's continuation lines into another's. `_deviation_log_aggregate()`
   therefore concatenates whole shard files in filename order, never
   individual lines.

Also folds in a pre-existing, previously unenforced convention: many role
sessions already write `docs/issue-<n>/reports/<role>/deviation-log.md`
(role-scoped) rather than the flat `docs/issue-<n>/reports/deviation-log.md`
the guard checked for — the natural granularity once more than one role
works the same issue (implementation, conformance-review, execution-
observation, ... all landing in the same flat file would itself be a
shared append-only path, the exact class this issue eliminates). Role
comes from `$CLAUDE_SKILL` when set (the same signal board-gate's R4
already treats as authoritative for a role session's own subtree), else
there is no role component (orchestrator / no role in scope).
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path


def _deviation_log_dir(issue: int | None, role: str | None = None,
                        cwd: str | None = None) -> Path:
    """Issue-scoped + role-scoped when both are known, issue-scoped only
    when role is None, else the standard `reports/` bucket — same
    issue-keyed-vs-not split `consult-log.md`/`.orchestrate-hook-fires.log`
    already use."""
    root = Path(cwd).resolve() if cwd else Path(".").resolve()
    if issue is None:
        return root / "docs" / "reports" / "deviation-log"
    base = root / "docs" / f"issue-{issue}" / "reports"
    return (base / role / "deviation-log") if role else (base / "deviation-log")


def _deviation_log_shard_id(shard_dir: Path, session_id: str | None) -> str:
    """`<first-seen-ts>-<session-hash>` — reuses the shard this session
    already minted (matched by its hash suffix) so repeat appends within
    one session land in the same file; a session's first append mints the
    timestamp prefix. `session_id` missing/empty buckets under a fixed
    `unknown` hash rather than dropping the entry."""
    session_hash = (
        hashlib.sha256(session_id.encode("utf-8", "surrogatepass")).hexdigest()[:16]
        if session_id else "unknown"
    )
    if shard_dir.is_dir():
        for p in shard_dir.glob(f"*-{session_hash}.md"):
            return p.stem
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    return f"{ts}-{session_hash}"


def _deviation_log_session_id() -> str | None:
    return os.environ.get("CLAUDE_CODE_SESSION_ID") or os.environ.get("CLAUDE_SESSION_ID")


def _deviation_log_path(issue: int | None, role: str | None = None,
                         cwd: str | None = None, session_id: str | None = None) -> Path:
    """The shard file this session's deviation-log appends land in.
    Creates the shard directory (not the file) so a session can rely on
    the parent existing before its own Write/Edit call."""
    d = _deviation_log_dir(issue, role, cwd)
    sid = session_id if session_id is not None else _deviation_log_session_id()
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_deviation_log_shard_id(d, sid)}.md"


def _deviation_log_aggregate(issue: int | None, role: str | None = None,
                              cwd: str | None = None) -> str:
    """Reader/aggregator reconstructing the pre-#2348 single-file view —
    concatenates whole shard files (never individual lines, entries can
    wrap several) in filename order, which is chronological-by-first-
    append because the shard id embeds the session's first-seen timestamp.
    Empty string, matching the old "file not found" empty state, when no
    deviation has ever been logged under this dir."""
    d = _deviation_log_dir(issue, role, cwd)
    if not d.is_dir():
        return ""
    return "".join(p.read_text(encoding="utf-8") for p in sorted(d.glob("*.md")))
