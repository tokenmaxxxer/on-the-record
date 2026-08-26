---
status: proposed
files:
  - docs/issue-2403/reports/conformance-review.md
---

## Request

Conformance-review PR #2452 (`issue-2403/implementation`) against issue
#2403's 5 acceptance checks, and land the verdict in
`docs/issue-2403/reports/conformance-review.md`.

## Constraints

- `CLAUDE_ROLE=conformance-review`, no `CORE_BUILD_NOW`, no
  `CORE_CHECKPOINT` — this session runs the default two-phase
  role-handoff contract: this proposal, then a human Approve, then the
  record write in a later session.
- The record file itself (`docs/issue-2403/reports/conformance-review.md`)
  is execution-surface output under this repo's approval-gate — it cannot
  be written this session without an Approve.
- The record-format directive requires `code_under_review:`,
  `loop_state:`, `type:`, `breaking:`, `verdict:` frontmatter plus a
  `## What did not work` heading even when empty.

## Rationale

Considered doing a lighter pass — reading the implementation record's own
pasted test output and code diff, and rendering verdicts from that alone
— rather than independently re-running every test and building fresh
live-conflict scenarios of my own. Rejected: acceptance check 1 mandates
"demonstrated live against a deliberately-stale branch" as the
verification method itself, and check 3 explicitly disclaims "not an
assertion that it is faster" — both require the reviewer's own
independent re-derivation, not trust in the implementer's paste. The
current-state survey (`docs/issue-2403/reports/conformance-review/survey.md`,
already on disk) was built with that heavier bar instead of the lighter
one: every test class the implementation record cites was independently
re-run in a worktree of the implementation branch, two of the four
historical cost timestamps were independently re-derived from `gh pr
view` rather than trusted, and two fresh scratch-repo scenarios (never
used in the implementation's own fixtures) were built to demonstrate the
staleness probe and the mechanical rebase end to end.

## What will be done

Once approved, write `docs/issue-2403/reports/conformance-review.md`
carrying a Present/Surface/Absent/Incorrect/Unverifiable verdict for each
of the 5 requirement items already extracted and checked in the survey
(1a/1b staleness detection, 2 mechanical rebase, 3a/3b cost measurement,
4 distinct staleness expression, 5a/5b no weakened verification), citing
the survey's own evidence rather than re-deriving it, plus the
record-shape-mandated frontmatter and `## What did not work` heading and
the mandatory `skill-verdict:` lines for
`conformance-review-requirement-extraction` and
`conformance-review-verification-method-selection` (both invoked this
session) and `conformance-review-finding-record`,
`conformance-review-verdict-assignment`,
`conformance-review-traceability-and-evidence` (invoked when the record
itself is written, phase 2). `conformance-review-sampling-derivation`
and `conformance-review-severity-classification` stay not-applicable —
full enumeration was feasible and no risk-weighting pass was requested.

## Out of scope

- No code changes to `gates/merge_gate.py`, `spawn.py`, or any file under
  `code_under_review` — this role only reviews and records, it does not
  patch.
- No action on PR #2452 itself (no review comment, no merge) — this
  role's write scope is its own record file.
- Re-measuring the four historical incidents beyond the two already
  independently re-derived in the survey (#2368, #2396) — the other two
  (core#304/#307, #2348/#2388) were not re-queried this session; the
  survey notes which were checked.

## How you'll know it worked

`docs/issue-2403/reports/conformance-review.md` exists, carries a verdict
for each of the 5 acceptance checks with a citation back to this
proposal's survey evidence (not bare assertion), and its own frontmatter
`verdict:` reflects the worst-case result across the 5 items per this
role's convention.
