---
status: approved
files:
  - docs/issue-1165/reports/content-design/current-state-survey.md
  - docs/issue-1165/reports/content-design/scout-brief.md
  - docs/issue-1165/reports/content-design/tier2-new-user-checklist.md
  - docs/issue-1165/reports/content-design.md
---

# issue-1165: content-design human-comprehensibility criterion for screens (proposal)

kind: proposal
subject: issue-1165

Proposal: docs/issue-1165/proposals/content-design-screens-comprehensibility.md

Decision: reuse this role's already-landed NN/g heuristics and
Halvorson quad (`roles/specs/content-design.spec.json`) as the tiering
frame rather than choosing a new methodology, because the gap this
step closes is operationalization, not methodology selection -> a new
framework here would duplicate a sourcing decision this role already
made.

## Intent

Step 1 of issue-1165 (parallel with technical-writing, disjoint write
sets): design the human-comprehensibility criterion for SCREENS and
other user-facing surfaces, in the three tiers the issue body's
requirement 2 specifies, grounded in this role's already-landed
methodology (NN/g heuristics, Halvorson content strategy quad —
canonical: `roles/specs/content-design.spec.json`). Basis: the issue
body's requirement 2 (tier split), requirement 4 (anti-nitpick bound),
and the operator's stated bar quoted in the issue ("an app screen must
be intuitive to a NEW user").

Approval note: the issue's own comment thread already carries the
exact single-account approval string `APPROVE issue-1165/content-design`
(posted 2026-08-13T04:00:01Z, account `JiwonJung94`, an
`docs/specs/approvers.md` account) ahead of this PR's creation, so this
proposal is filed already `status: approved` and its phase-2 record
lands in the same commit/PR rather than waiting on a separate review
round.

## Constraints stated so far

- Screens here means target-project user-facing surfaces, not
  on-the-record's own UI — `docs/specs/ui-surfaces.md` declares this
  repo's own glob list `none`, canonical: read this turn.
- Write set stays inside this role's existing `write_scope`
  (`docs/issue-<n>/reports/content-design.md`,
  `docs/issue-<n>/reports/content-design/*.md`) — no edits to
  `gates/quality_bar.py` or the 7 landing-order role specs; folding
  tier-2 checklists into those is step 2 (implementation), a different
  step in this issue's own 실행 계획.
- Write sets stay disjoint from technical-writing's parallel
  document/record-side step-1 deliverable — this proposal's `files:`
  list touches only `docs/issue-1165/reports/content-design*` and
  `docs/issue-1165/proposals/content-design-*`.
- Tier-2/tier-3 verdicts must name which checklist item failed and what
  a passing shape looks like (issue requirement 4).

## What will be done

- `docs/issue-1165/reports/content-design/tier2-new-user-checklist.md`:
  the tier-2 named human-review checklist for screens — intuitive-
  first-screen test and can-a-new-user-complete-the-primary-task-
  unaided test, each item citing its NN/g heuristic and stating the
  accept/reject shape.
- `docs/issue-1165/reports/content-design.md`: the phase-2 record
  carrying the tier-1 structural rules (where automatable, for
  screens), the tier-3 sampled-review protocol, and the hand-off
  boundary to interaction-design when a finding requires a screen/flow
  structure change rather than a content fix.

## Out of scope

- Wiring these tiers into `gates/quality_bar.py`, the 7 role specs, or
  any hook — that is step 2 (implementation) per this issue's own
  실행 계획, not this step.
- The document/record-facing human-comprehensibility rules
  (record-scaffold, PR-body framing) — technical-writing's parallel
  step-1 deliverable, disjoint write set.
- Numeric severity scoring for tier-2 findings (scout-brief "skip"
  line) — accept/reject with a named failing item only.

## How you will know it worked

- The tier-2 checklist file exists, each item names an NN/g heuristic
  or the Halvorson quad element it is grounded in, and states both the
  failing condition and the passing shape (issue requirement 4).
- The phase-2 record's tier-1 rules are stated as structural checks (a
  reviewer or a future automated check could evaluate them against a
  screen's markup/copy without subjective judgment), matching
  requirement 2's "automatable" framing for tier 1.
- The tier-3 protocol states a concrete, tunable sampling frequency
  rather than "per-artifact" (issue requirement 2's consult caveat).

## What did not work

None.
