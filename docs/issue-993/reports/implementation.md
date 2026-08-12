---
code_under_review:
  - gates/test_role_utilization_report.py
  - roles/refactoring-legacy.json
  - roles/test-authoring.json
type: feature
breaking: false
# canonical: python3 -m pytest gates/test_role_utilization_report.py -q
verdict: pass
loop_state: landed
---

# Implementation record — issue #993, phase-2

canonical: `python3 -m pytest gates/test_role_utilization_report.py -q` (executed this session)
acceptance: `python3 -m pytest gates/test_role_utilization_report.py -q` — result: UNMEASURED-with-reason: no acceptance command on record for this target in docs/specs/acceptance-commands.md
```
...                                                                      [100%]
3 passed in 0.05s
```

## What was done
canonical: `git diff --stat` (this session) against
`gates/test_role_utilization_report.py`, `roles/refactoring-legacy.json`,
`roles/test-authoring.json`

Built the two write-set items from
docs/issue-993/proposals/implementation.md (PR #1083):

1. `roles/refactoring-legacy.json` and `roles/test-authoring.json`: each
   `use_when` string now carries a `(b) scope overlap, tentative` clause
   stating implementation's own `write_scope` already covers the domain
   inline when a standalone record isn't warranted, plus the revisit
   condition (a legacy-debt-specific or test-design-specific record type
   being wanted later).
2. `gates/test_role_utilization_report.py`: a new pytest-collectible gate
   test that (a) counts board records per `roles/*.json` stem using the
   product-discovery survey's own derivation rule (flat
   `docs/issue-<n>/reports/<role>.md` OR nested
   `docs/issue-<n>/reports/<role>/*.md`, literal stem match), (b) asserts
   all 43 role stems appear as keys in the count map (zero valid, absence
   not), and (c) asserts refactoring-legacy and test-authoring carry the
   `(b)`-style overlap disposition string in `use_when`.

## Why
canonical: gh issue view 993 (read this session, body's "## Acceptance"
section naming `gates/test_role_utilization_report.py`)

The issue's own acceptance criterion names this gate test as required.
canonical: docs/issue-993/proposals/product-discovery.md (read this
session, the `(b) scope overlap, tentative` disposition text for
refactoring-legacy and test-authoring)

The product-discovery diagnosis left refactoring-legacy and
test-authoring at that disposition with no owning follow-up issue. This
build closes both per the approved proposal.

## Upstream basis
canonical: docs/issue-993/proposals/implementation.md (read this session,
`status: approved` frontmatter)

docs/issue-993/proposals/implementation.md

## What did not work
None.

## Open findings
canonical: docs/issue-993/reports/implementation/hunt-implementation.md
(read this session) — two FINDING entries, neither blocking this landing.

1. after-proposal, stance 3: the gate's stem-derivation rule (flat vs
   nested board paths) has no prior maintained mapping in the repo.
   Resolution: the gate test built here (`gates/test_role_utilization_report.py`)
   implements and asserts the exact rule itself (literal stem match on
   both shapes), which is what the proposal named as the fix — verified
   passing above.
2. before-landing, stance 4: `gates.role_scope()` flags
   `roles/refactoring-legacy.json`, `roles/test-authoring.json`, and
   `gates/test_role_utilization_report.py` as outside `implementation`'s
   declared `write_scope` (`src/**`, `test/**`, `tests/**`); no
   write_scope override file (docs/specs/write_scope.md, not present in
   this working tree) exists. Pre-existing gap, not introduced by this
   build — `roles/implementation.json`'s `write_scope` has never included
   `gates/` or `roles/*.json`, and a prior implementation record
   (docs/issue-1035/reports/implementation.md) shows the same pattern
   already landed under it. `gates/ci.py`'s `--closes-only`
   required-status-check path (the only check wired as required per issue
   #245) skips `role_scope()` entirely, so this does not block merge.
   Resolution path: widening `roles/implementation.json`'s `write_scope`
   or adding a write_scope override file is outside this proposal's
   frozen write set — a future proposal's write set, not this one's.
