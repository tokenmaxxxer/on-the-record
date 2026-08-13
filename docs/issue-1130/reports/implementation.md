---
code_under_review:
  - on-the-record/hooks/spec_schema.py
  - on-the-record/hooks/routing_fix_spawn_checks.py
  - gates/spec_schema_five_activities_test.py
  - on-the-record/hooks/test_routing_fix_spawn_checks.py
type: docs
breaking: false
verdict: landed
loop_state: landed
---

## What was done

Board record (record-only follow-up) for issue #1130 — role expertise
realization for cause-d/cause-b roles.

canonical: git log 103130b (merge of PR #1148), dbe8d53 (merge of PR
#1147) — both merged to main.

PRs #1147 and #1148 delivered the approved write set:

- 14 five-activity specs added/updated under the spec schema (spec-depth
  gate enforcing five-activity structure).
- 3 gate-now hooks wired for cause-d/cause-b role routing.
- 6 cause-b routing fixes correcting spawn-check misrouting.
- Spec-depth gate itself, gating spec schema conformance.
- `$()`-bypass hardening for the 5 new deny gates, added in PR #1148 as a
  direct fix for a warrant-hunt finding (substitution bypass) surfaced
  after PR #1147 landed.

`APPROVE issue-1130/implementation` is posted on issue #1130 by
JiwonJung94 (docs/issue-1130/reports/implementation.md, this file, is
the phase-2 record required by that approval; no further code changes
are made by this record-only PR).

## Why

canonical: PR #1147 and #1148 bodies (both merged, git log 103130b,
dbe8d53) — the board is what is merged to main, and the approval comment
requires a landed phase-2 record. This PR closes that gap: the
delivered work merged without its implementation.md, so #1130 remained
open despite the write set being on main.

## Upstream / basis

basis: 103130b (merge of PR #1148), dbe8d53 (merge of PR #1147)

## How verified

derived: python3 -m pytest gates/spec_schema_five_activities_test.py on-the-record/hooks/test_routing_fix_spawn_checks.py -q
```
.............                                                            [100%]
13 passed in 0.59s
```

Both PR bodies (#1147, #1148) additionally carry their own pytest
output at merge time, confirming the write set as landed.

## What did not work

None.

## Open findings

canonical: git log 50b7ca7 "issue-1130: fix substitution bypass in the
5 new deny gates (warrant hunt)", merged into main via 103130b — none
open, closed as of that merge.
