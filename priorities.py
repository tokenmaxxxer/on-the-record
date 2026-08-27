"""issue #2637: per-entry sharding for `docs/reports/product/priorities.md`
(issue #566's product-capture log), the same conflict-elimination shape
issue #2333 shipped for `consult-log.md` and issue #2348 extended to
`.orchestrate-hook-fires.log`/`deviation-log.md` (`hook_fires.py`,
`deviation_log.py`) — applied here to a fourth append-only artifact. Two
concurrent sessions each recording their own operator-decision entry
collided on this one file even when their actual deliverables were
disjoint and correct (observed live: PR #2632 landed, PR #2633 then hit
`CONFLICTING / DIRTY` solely on this file — issue #2637 body).

Shape mirrors `consult.py`'s `_consult_trace_dir()`/`_consult_trace_path()`/
`_consult_log_aggregate()` almost exactly (`docs/reports/product/priorities/`,
issue-scoped variant `docs/issue-<n>/reports/product/priorities/`,
`<timestamp>-<pid>.md` shard names, fixed-width UTC
`%Y%m%dT%H%M%S%f` so filename sort is chronological sort, directory-glob
aggregate reader). One deliberate difference from every #2333/#2348
precedent: the design contract for this issue is one file PER ENTRY, not
one shard file per SESSION — a product-capture entry is a single one-shot
scribing act (the orchestrator records one operator decision and moves
on), not a burst of repeated appends the way a session's several
`consult()`/deviation-log calls can be. `_priorities_entry_path()`
therefore never caches/reuses a filename the way `consult.py`'s
`_CONSULT_SESSION_SHARD_ID` or `deviation_log.py`'s
`_deviation_log_shard_id()` do — every call mints a fresh one. The write
path needs no orchestrator or coordinator: a session calls
`_priorities_entry_path()` (or `spawn.py priorities-path`) for its own
unique path and writes its own entry directly with its own Write/Edit
call, exactly like `_consult_trace_path()`/`_deviation_log_path()`.

No-loss migration: the pre-existing flat `docs/reports/product/priorities.md`
(10 entries as of issue #2637) is left exactly as-is on disk, frozen, never
appended to again — the same "old file stops being written, stays
readable" treatment `docs/reports/consult-log.md` got after issue #2333
(that file still exists, untouched, alongside the new `consult-log/`
directory). Unlike consult-log's reader, which only ever aggregates the
new directory (the old file's content is not required to appear in
`_consult_log_aggregate()`'s output), THIS reader is deliberately
compatible with both: `read_priorities()` prepends the legacy flat file's
full content (if present) ahead of the new directory's shards, so no
existing entry silently drops out of the reader's view. This is a genuine,
stated divergence from the #2333/#2348 precedent, not an invented third
convention — it exists solely to satisfy issue #2637's explicit "do not
lose or reorder any existing entry" requirement, which #2333/#2348 never
had to satisfy (neither `hook_fires.py` nor `deviation_log.py` had
pre-existing historical content to preserve at migration time; `consult.py`
did, but nothing required its reader to keep surfacing it going forward).
No entry is rewritten, re-timestamped, or re-split to make this work — the
legacy file's bytes are read verbatim and never written to again.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path


def _priorities_root(cwd: str | None) -> Path:
    return Path(cwd).resolve() if cwd else Path(".").resolve()


def _priorities_legacy_path(issue: int | None, cwd: str | None = None) -> Path:
    """The pre-#2637 flat file this directory replaces going forward —
    frozen in place, read but never written to again."""
    root = _priorities_root(cwd)
    if issue is None:
        return root / "docs" / "reports" / "product" / "priorities.md"
    return root / "docs" / f"issue-{issue}" / "reports" / "product" / "priorities.md"


def _priorities_dir(issue: int | None, cwd: str | None = None) -> Path:
    """Issue-scoped when an issue is known, else the standard `reports/`
    bucket — same issue-keyed-vs-not split `consult-log`/`deviation-log`
    already use. Same basename as the legacy file, extension dropped
    (`priorities.md` -> `priorities/`), matching `consult-log.md` ->
    `consult-log/`."""
    root = _priorities_root(cwd)
    if issue is None:
        return root / "docs" / "reports" / "product" / "priorities"
    return root / "docs" / f"issue-{issue}" / "reports" / "product" / "priorities"


def _priorities_entry_path(issue: int | None = None, cwd: str | None = None) -> Path:
    """A fresh path for exactly one new entry. Every call mints a new
    filename — never reused, unlike `consult.py`'s per-process shard cache
    (see module docstring: one file per entry here, not one file per
    session). `<timestamp>-<pid>.md`, timestamp `%Y%m%dT%H%M%S%f` UTC
    (fixed-width, microsecond resolution) — identical formula to
    `consult.py`'s `_consult_trace_path()` — so filename sort is
    chronological sort; pid keeps two entries minted in the same
    microsecond by two different processes from colliding. Creates the
    directory (not the file) so a caller can write immediately after."""
    d = _priorities_dir(issue, cwd)
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    return d / f"{ts}-{os.getpid()}.md"


def read_priorities(issue: int | None = None, cwd: str | None = None) -> list[str]:
    """Entries in order (legacy flat-file content, if any, first — it
    predates every shard by construction — then new per-entry shards in
    filename/chronological order). Empty list — not an exception — only
    when NEITHER the legacy file nor the shard directory exists: no entry
    has ever been captured. This is the ONLY silent-empty case (the
    `legacy.is_file()` / `d.is_dir()` checks immediately below). Any other
    failure — permission denied on the directory, an unreadable/malformed
    shard file — is NOT caught here: `read_text()` is deliberately left
    unwrapped by any try/except, so PermissionError/UnicodeDecodeError/etc.
    propagate to the caller as real exceptions instead of being folded
    into the same empty result a merely-absent directory produces
    (silent-failure-audit: directory/file absence is the one legitimate
    empty state; everything else must surface)."""
    entries: list[str] = []
    legacy = _priorities_legacy_path(issue, cwd)
    if legacy.is_file():
        entries.append(legacy.read_text(encoding="utf-8"))
    d = _priorities_dir(issue, cwd)
    if d.is_dir():
        entries.extend(p.read_text(encoding="utf-8") for p in sorted(d.glob("*.md")))
    return entries


def priorities_aggregate(issue: int | None = None, cwd: str | None = None) -> str:
    """Reader/aggregator reconstructing the pre-#2637 single-file
    `docs/reports/product/priorities.md` view — concatenates
    `read_priorities()`'s entries in order. Empty string (not an
    exception) in the same no-capture-yet case `read_priorities()` treats
    as empty."""
    return "".join(read_priorities(issue, cwd))
