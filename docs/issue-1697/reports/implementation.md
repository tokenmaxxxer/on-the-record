---
code_under_review:
  - gates/spawn_on_pr.py
  - tests/test_spawn_on_pr.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Added three functions to `gates/spawn_on_pr.py` and wired them into
`missing_verification()`:

- `resolve_live_base(root)` — fetches `origin` and returns the resolved
  base ref's current sha, called once per `spawn_missing_for_pr` live
  batch right before spawning.
- `_pr_state_for_branch(root, branch, pr_index)` — mirrors
  `_pr_number_for_branch` but returns the PR state string.
canonical: gates/spawn_on_pr.py (this session's own edit, see diff)
  Used to skip (with `ledger_write` + a printed line) a subject whose
  own PR state is MERGED.
- `_implementation_session_active(root, subject)` — checks
  `spawn._roster_load()`/`spawn._alive()` for a live
  `<subject>/implementation` pid.
canonical: gates/spawn_on_pr.py (this session's own edit, see diff)
  Used to defer (with `ledger_write` + a printed line) a subject whose
  implementation session is still RUNNING.

canonical: gates/spawn_on_pr.py:63-73 (read directly)
Issue-closed skip was already implemented (`_issue_is_open`) — no
change made there.

Added 7 unit tests to `tests/test_spawn_on_pr.py`: a moved-main fixture
(bare-git clone, advance origin after clone, assert `resolve_live_base`
returns the new sha, not the stale cached one) plus a fetch-failure
case; a merged-subject-PR skip test and its open-PR companion; an
active-implementation-session defer test and its dead-roster-entry
companion (a stale pid must not defer forever).

## Why

canonical: gh issue view 1697 --comments (first comment, ## Acceptance section)
Issue #1697 acceptance requires (a) branch base resolved from live
origin/main at spawn, unit-tested with a moved-main fixture, and (b)
observer spawns skipped and logged under a merged/closed condition,
unit-tested.

canonical: gh issue view 1697 --comments (second comment, 2026-08-17, issue-1696 reproduction)
The issue's second comment extends the skip condition to defer while
the subject's own implementation session is still running — that
in-flight window is what produced the stale-base revert class this
issue exists to close.

## Upstream

Based on: docs/issue-1697/proposals/spawn-hygiene.md

## Test run

derived: `python3 -m pytest -q tests/test_spawn_on_pr.py`

```
19 passed in 0.96s
```

Fast-tier command per `.on-the-record/test-tiers.json`
(`python3 -m pytest -q -m "not slow"`) was not run in full — the write
set (`gates/spawn_on_pr.py`, `tests/test_spawn_on_pr.py`) does not
match the slow-tier trigger classes (`spawn.py`,
`tests/test_spawn.py`, `on-the-record/hooks/*.sh`,
`on-the-record/hooks/test_*.py`), so the targeted module run above is
the acceptance-relevant evidence; the repo-wide fast suite was not
executed this session (tiering-gap note, test-tier-directive).

## What did not work

None.

## Open findings

None.
