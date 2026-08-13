# Survey — issue #1142

Scope: pure bugfix (scout-directive skip condition — a filter-logic
correction inside one existing function, no design decision open; no
scout brief written).

## Where the drift check lives

`spawn.py::requirement_drift()` is called once per watchdog tick from
`_board_wide_sweep()`. Advisory only — prints, never adds to
`anomaly_count`.

Current logic, read directly from spawn.py:
1. Reads `docs/specs/requirement-digest.md`, builds `live_entries: {id:
   (paraphrase, source_issue)}` from lines matching
   `^- (R\d+): (.+?) \[\S+\] \(source: #(\d+)\)$`. The `[\S+]` group
   (digest status: `enforced` or `open`) is matched by the regex but
   never captured into a group — that is the bug's root cause.
   `live_ids` is the resulting entry-id set.
2. Lists open issues and PRs via `gh`, collects every `R\d+` id
   mentioned anywhere in title+body into `mentioned_reqs`.
3. `unmentioned_live = live_ids - mentioned_reqs` — every live digest
   id with no open-issue/PR citation gets printed as drifted,
   regardless of its digest status.

## Where check-path liveness is already computed

`gates/requirement_digest.py` marks a registry entry's status `stale`
in `update()`/`_rewrite_stale()` when its `check` path no longer
exists at HEAD, and `render()` excludes `stale` entries from the
digest. A vanished check path therefore never reaches
`requirement_drift()`'s `live_entries` at all — issue requirement 3
("vanished check path stays the registry check's job") is satisfied by
this existing behavior; nothing in `requirement_drift()` needs to
duplicate it.

## The actual gap

`requirement_drift()` treats `enforced` and `open` digest entries the
same: any live id with no citation flags. The status text is present
in the line the function already parses but is discarded by the
non-capturing group. Capturing it lets the function skip citation-based
flagging for `enforced` entries while leaving `open` entries flagged
exactly as before.

## Existing test coverage

canonical: gates/test_requirement_drift.py (read this turn)
The file's three existing tests build a fabricated digest fixture using
a placeholder status literal that the current code never inspects, and
cover infra-tag exclusion plus the referenced/unreferenced-open cases.
None assert on digest status. New tests need digest fixtures using the
real status literals to exercise the new branch.

## Write set (frozen for the proposal)

- spawn.py — requirement_drift() only (status-aware filtering).
- gates/test_requirement_drift.py — new unit tests per Acceptance.
- docs/issue-1142/reports/implementation/survey.md — this file.
- docs/issue-1142/proposals/ — the phase-1 proposal.
- docs/issue-1142/reports/implementation.md — phase-2 record, written
  only after approval.

Everything else spawn.py contains, and gates/requirement_linkage.py,
stay untouched — outside this issue's scope per the task brief.
