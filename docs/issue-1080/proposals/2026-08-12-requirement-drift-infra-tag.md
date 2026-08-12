---
status: proposed
files:
  - spawn.py
  - gates/test_requirement_drift.py
---

Pure bugfix (scout-directive skip condition): `requirement_drift`'s
unreferenced-open check must mirror `gates/requirement_linkage.py::
check_issue_body`'s existing, already-designed `_INFRA_TAG` exception —
no new design decision, so scouting and the current-state survey are
skipped per the scout-directive's mandatory skip condition.

## Request

`spawn.py::requirement_drift` flags every open issue/PR citing no
requirement ID, but does not honor the sanctioned
`infrastructure/no-direct-requirement` tag that
`gates/requirement_linkage.py::check_issue_body` already accepts —
producing a permanent false positive on tagged items (e.g. issue #745).

## Constraints

- Reuse the existing `_INFRA_TAG` literal from `gates/requirement_linkage.py`
  rather than duplicating the string, so the two checks cannot drift apart.
- No change to `unmentioned_live` semantics or drift's advisory/non-blocking
  contract.

## Rationale

Considered duplicating the literal `"infrastructure/no-direct-requirement"`
directly in `spawn.py` instead of importing `_requirement_linkage`. Rejected:
`spawn.py` already lazy-imports `gates/requirement_linkage` elsewhere
(`require_requirement_linkage`, line ~1048) via the same
`sys.path.insert(0, gates/)` pattern, so importing and reading
`_requirement_linkage._INFRA_TAG` keeps the two checks tied to one
source of truth instead of two copies that could silently diverge.

## What will be done

In `requirement_drift`'s open-issue/PR loop, skip appending an item to
`unreferenced_open` when its title/body contains `_INFRA_TAG` (imported
from `gates/requirement_linkage.py`), matching `check_issue_body`'s
existing exception.

## Out of scope

- Changing `check_issue_body` itself.
- Any other drift-report false-positive class.

## Accumulation

This adds one more `sys.path.insert(0, gates/)` + lazy-import of
`gates/requirement_linkage` inside `spawn.py`, matching the pattern
already used by `require_requirement_linkage` (line ~1046-1048). If
future watchdog checks need more shared literals from `gates/`, the
existing pattern is to import the module and read its attribute
directly (as done here for `_INFRA_TAG`), not to copy the literal — so
N more such checks stay tied to one source of truth per literal instead
of accumulating divergent string copies. No new per-item file or list
is introduced; the cost stays O(1) additional import per watchdog tick,
same order as the existing `require_requirement_linkage` import.

## How you'll know it worked

`python3 -m pytest gates/test_requirement_drift.py -v` — a unit test
shows an open item carrying `infrastructure/no-direct-requirement` is
excluded from `unreferenced_open`, an untagged item is still included,
and the empty-tagged-items case leaves drift output unchanged.
