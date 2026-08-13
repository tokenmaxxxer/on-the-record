---
status: proposed
files:
  - spawn.py
  - gates/test_requirement_drift.py
---

## Request

The requirement-drift watchdog check flags digest requirements marked
`enforced` (delivered, with a live enforcement check path) as drifted
purely for lacking a citation in an open issue/PR. Stop that: only
`open` (not-yet-delivered) requirements should need a live citation to
avoid flagging.

## Constraints

- Skip condition per scout-directive: pure bugfix, no design decision
  open — no scout brief written.
- Vanished check-path handling stays the registry's job
  (`gates/requirement_digest.py`); this fix does not duplicate it.
- Write set stays inside `spawn.py::requirement_drift()` and its test
  file — no edits to `gates/requirement_linkage.py`, the spawn.py
  watcher regions used by other in-flight issues, or gate-lib/terse
  areas.

## Rationale

Considered adding a second gate in `gates/requirement_digest.py` that
re-checks citations at digest-render time, so `requirement_drift()`
would not need to change at all. Rejected: `requirement_digest.py`
renders from the raw registry and has no concept of "open issue/PR
citation" — that's a live `gh` query, which is exactly what
`requirement_drift()` already does per tick. Splitting the citation
check into a second module would duplicate the `gh` listing cost this
function's own docstring budgets against, for no benefit.

Chosen approach: capture the digest status text that the regex in
`requirement_drift()` already matches but discards, and filter
`unmentioned_live` down to `open`-status ids before printing. Minimal
diff, no new I/O, keeps the advisory contract (prints only, never
touches `anomaly_count`) unchanged.

## What will be done

- In `spawn.py::requirement_drift()`, change the digest-line regex to
  capture the status group, store it in `live_entries` alongside
  paraphrase/source, and restrict the "drifted" print loop to entries
  whose status is `open`. `enforced` entries with no citation no longer
  print.
- Add unit tests to `gates/test_requirement_drift.py`: an `enforced`
  entry with no citation does not flag; an `open` entry with no
  citation still flags; an empty digest produces no flags.

## Accumulation

This change adds no new `gh`/subprocess call and no new per-tick I/O —
it only changes which already-parsed digest ids get printed after the
existing single `gh issue list`/`gh pr list` pair. As more `enforced`
requirements accumulate in the digest, this fix keeps their per-tick
cost identical to today (they're already parsed into `live_entries`);
it removes their contribution to printed drift noise instead of adding
work. If a future requirement needs status-aware filtering to expand
beyond `enforced`/`open` (a third status value), that would touch this
same filter line again — not a growing list of special cases.

## Out of scope

- Any change to `gates/requirement_digest.py`'s stale/check-path logic.
- Any change to `gates/requirement_linkage.py` or the PR-body citation
  gate.
- Any other function inside `spawn.py`.

## How you'll know it worked

- `python3 -m pytest gates/test_requirement_drift.py -q` passes,
  including the new cases.
- Manually reasoned trace: an `enforced` digest line with no citing
  open issue/PR produces no drift print; an `open` digest line in the
  same conditions still prints exactly as before.
