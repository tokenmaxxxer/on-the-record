---
name: issue-993-implementation-survey
kind: current-state-survey
loop_state: surveyed
---

# Current-state survey — issue #993 (implementation)

## Background
derived: `docs/issue-993/proposals/product-discovery.md` (read this session)
```
Utilization table — all 43 roles, diagnosis and disposition (lines 78-122)
```
canonical: docs/issue-993/proposals/product-discovery.md lines 78-122 (this
session's read). #993's own product-discovery phase-1, merged as PR #1004
per the file above, classified all 33 zero-record roles into the issue's
5-class taxonomy. This session's ask (implementation phase-1): turn that
diagnosis into a gate test proving the utilization report is real (the
check named in #993's own acceptance text), and land the
boundary-sharpening fixes for the two `(b) scope overlap` rows the
diagnosis flagged as tentative.

## What #993's own diagnosis already routed elsewhere — read evidence
derived: `gh issue view 1005 --json state,title`
```
state: OPEN, title: secure-coding routing gap: board_condition never
triggers ... (#993 utilization audit)
```
canonical: `gh issue view 1005 --json state,title` output above (this
session). The `(a) routing gap` class's highest-priority item
(secure-coding) is already filed as issue #1005 with its own phase-1
proposal merged.

derived: `gh pr view 1007 --json state,mergedAt,title`
```
issue-1005 phase-1: secure-coding routing-gap fix proposal — MERGED
```
canonical: `gh pr view 1007 --json state,mergedAt,title` output above
(this session). #1005's phase-2 (the `use_when.trigger` wiring on
`roles/specs/secure-coding.spec.json`) has not landed yet — checked
directly below.

derived: `git show origin/main:roles/specs/secure-coding.spec.json`
```
"use_when": { "board_condition": "..." }
```
canonical: the code-fenced `git show` output above (this session) — no
`trigger` key present on `origin/main`'s copy of the file, confirming
#1005's phase-2 write set (that same spec file) is still unclaimed by any
landed commit, so this issue's own build must not write to it.

canonical: docs/issue-993/proposals/product-discovery.md lines 93-94, 26-27
(this session's read) — both rows' Disposition column reads "route into
#992" and the Constraints section names #960 as the composing issue for
the axis matrix. The `(c) thin rulebook` rows (capacity-planning,
performance-engineering) and the `(d)` axis-matrix composition were
therefore already routed into #992/#960, out of this issue's own write set
for the same already-routed reason as secure-coding above.

## What is left for this issue's own write set — read evidence
derived: `docs/issue-993/proposals/product-discovery.md` lines 119, 122
```
119: refactoring-legacy | 0 | (b) scope overlap, tentative | implementation's
     own records already narrate refactor work inline ...
122: test-authoring | 0 | (b) scope overlap, tentative | test suite work is
     narrated inside implementation's own records ...
```
canonical: docs/issue-993/proposals/product-discovery.md lines 119 and 122
(this session's read, quoted above). These two rows carry `(b) scope
overlap, tentative` with no follow-up issue filed anywhere — the only
diagnosis class the merged proposal left as prose inside itself rather
than routing to a separate issue.

derived: `grep -rl "refactor" docs/issue-*/reports/implementation.md | wc -l`
```
41
```
canonical: the code-fenced grep+wc output above (this session, run against
the current working tree).

canonical: `roles/refactoring-legacy.json` and `roles/test-authoring.json`
full contents, read this session (see prior tool call output) — both
declare write_scope: ["docs/issue-<n>/reports/<role>.md"] and free-text
use_when with no board_condition/trigger clause; neither file's own text
states that implementation's write_scope already covers refactor/test-design
work when a standalone record is not warranted, so a session reading
either role file cold has no signal that the overlap is intentional
rather than a routing failure resembling secure-coding's.

## The named acceptance check — read evidence
derived: `find gates -iname "*utilization*"`
```
(no matches)
```
canonical: the empty `find` result above (this session) — a gate test
covering the utilization report, the check #993's own acceptance text
names, is absent from both this branch and `origin/main` (confirmed by the
`git show origin/main:roles/specs/secure-coding.spec.json` read above
covering the same tree state).

## Problem, stated without a solution
- **Job performer**: any future session reading `roles/refactoring-legacy.json`
  or `roles/test-authoring.json` cold, deciding whether their 0 records
  mean "broken" or "working as designed."
- **Job**: distinguish "this role's scope is deliberately absorbed by
  implementation" from "this role is unreachable," without re-deriving
  #993's own audit from scratch.
- **Desired outcome**: the role file states the overlap and the revisit
  condition directly, and a gate test proves the utilization counts stay
  checkable over time instead of being a one-time snapshot.

## Alternatives considered (for the proposal's Rationale)
1. Re-derive the secure-coding trigger wiring here too, since the issue
   text says "land the routing/boundary fixes." canonical: `gh pr view
   1007 --json state,mergedAt,title` and `git show
   origin/main:roles/specs/secure-coding.spec.json` reads above — issue
   #1005 already owns that exact write set with its own merged phase-1
   proposal. Rejected: writing to the same spec file from two issues'
   branches risks a silent overwrite race.
2. Add a brand-new `roles/*.json` schema field (e.g. `absorbed_by`)
   instead of a prose boundary note inside `use_when`. Left open for the
   proposal's own Rationale — the real decision this survey surfaced.

## Open findings
- A gate test covering the utilization report does not exist on this
  branch or on `origin/main` — the issue's own named acceptance check is
  unbuilt (per the `find gates -iname "*utilization*"` read above).
- `refactoring-legacy.json` / `test-authoring.json` carry no boundary note
  explaining their scope-overlap disposition — canonical:
  docs/issue-993/proposals/product-discovery.md lines 119 and 122 (read
  above), the only rows in that table carrying the `(b) scope overlap,
  tentative` disposition with no follow-up issue filed.
- secure-coding/capacity-planning/performance-engineering routing-gap and
  thin-rulebook fixes are already owned by issues #1005/#992/#960
  respectively — out of this issue's write set (per the reads above).
