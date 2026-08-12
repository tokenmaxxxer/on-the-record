---
code_under_review:
  - gates/flows.py
  - spawn.py
  - tests/test_flows.py
  - docs/specs/flows-schema.md
type: feature
breaking: false
# canonical: python3 -m pytest tests/test_spawn.py tests/test_flows.py
verdict: pass
loop_state: landed
---

## What was done
Implemented the approved phase-1 proposal
`docs/issue-1035/proposals/2026-08-12-decision-queue-session-scope.md`:
`flows_payload()` in `gates/flows.py` now takes an `all_scope: bool =
False` parameter. It loads the roster once (`spawn._roster_load()`)
and, before appending an item to `decision_queue`, applies
`spawn._roster_own`'s own ownership predicate to that item's
`issue-<n>/<role>` key — items owned by another session's `session_id`
are excluded by default; items with no matching roster entry at all
stay visible (observation-loss invariant, same as `_roster_own`);
`all_scope=True` returns every item unfiltered. The `flows()` CLI
wrapper gained a matching `all_scope: bool = False` parameter.
`spawn.py`'s `flows` CLI dispatch now forwards the existing `--all`
flag's parsed value through as `all_scope`. `docs/specs/flows-
schema.md` section 2.1 documents the default scoping and the `--all`
escape.

## Why
Requirement R001 (multi-session confusion, same family as #1013):
`decision_queue` was built repo-wide with no session-ownership filter,
so a foreign session's aged decision-queue item could trip this
session's `decision-queue-stopgate.sh` Stop hook on items it does not
own and must not act on. Basis: docs/issue-1035/proposals/2026-08-12-
decision-queue-session-scope.md (approved).

## What did not work
None.

## Rationale for deviations
None — the build followed the approved proposal's execution section
without divergence.

## Doc placement
- docs/specs/flows-schema.md section 2.1 — updated in this commit
  (contract doc for `decision_queue`'s versioned shape, per the
  proposal's execution section).

## Acceptance verification
canonical: python3 -m pytest tests/test_flows.py -k decision -v
```
tests/test_flows.py::DecisionQueueSessionScope::test_all_scope_lists_both_own_and_foreign PASSED
tests/test_flows.py::DecisionQueueSessionScope::test_foreign_session_aged_item_excluded_by_default PASSED
tests/test_flows.py::DecisionQueueSessionScope::test_own_session_aged_item_still_included_by_default PASSED
3 passed
```
canonical: python3 -m pytest tests/test_flows.py -k decision — three new
acceptance cases green.

canonical: python3 -m pytest tests/test_spawn.py tests/test_flows.py
```
491 passed
```
canonical: python3 -m pytest tests/test_spawn.py tests/test_flows.py —
full-suite regression check green, 0 skipped.

## Hunt
Dispatched `warrant-hunter` (subagent_type, model sonnet) at this
before-landing transition, stance 3 ("assume the write set cannot carry
this work"), 120s cap for the ~120-line diff across gates/flows.py,
spawn.py, tests/test_flows.py, docs/specs/flows-schema.md. Result: NO
FINDING — recorded in
docs/issue-1035/reports/implementation/2026-08-12-hunt-decision-queue-session-scope.md.

## Open findings
None.
