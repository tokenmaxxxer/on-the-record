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

## Amendment 2 — convention-conformance/familiarity (2026-08-13)

Revision requested on PR #1170 (operator comment, amendment 2 on issue
#1165, posted while this step's original PR was open): add
convention-conformance/familiarity as a first-class screen-side
principle, web-verified per the same standard as the document-side
counterpart (technical-writing's amendment 2,
`docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md`,
merged in PR #1168 — this section mirrors its clause shape for
cross-role consistency, per the review comment's own instruction).

Screen-side grounding, each with its source:

- **Jakob's Law** — users spend most of their time on *other* sites/
  apps and transfer expectations built there to a new product; a
  screen that matches imported navigation/form conventions costs the
  new user less orientation effort than a bespoke one (Nielsen Norman
  Group, canonical: `https://www.nngroup.com/videos/jakobs-law-internet-ux/`,
  `https://lawsofux.com/jakobs-law/`). Screen-side reading: a new user
  who has used one mobile app's tab bar, back-gesture, or form-submit
  pattern before arrives at this screen with that shape already
  expected; departing from it silently spends the intuitive-first-
  screen test's (tier-2 item 1) attention budget on re-orientation
  instead of the task.
- **Principle of least astonishment** — an interface element should
  behave the way a user, familiar with the platform's own conventions,
  would expect it to behave; the platform's own written convention
  families (Material Design, Apple's Human Interface Guidelines) are
  the closest primary-source statement of what "expected" means for a
  screen (canonical: `https://m3.material.io/foundations`,
  `https://developer.apple.com/design/human-interface-guidelines`).
- **Norman's mental models** — a user builds a mental model from prior
  exposure to similar interfaces and expects a new one to match it
  (Don Norman, *The Design of Everyday Things*; canonical secondary
  source: `https://www.nngroup.com/articles/mental-models/`). Same
  source the document-side amendment already grounds in, extended here
  from document shape to screen/flow shape.
- **Processing fluency** — a familiar, easily-processed structure is
  judged more usable and more trustworthy for the same content
  (Schwarz et al., canonical:
  `https://www.renascence.io/journal/fluency-heuristic-judging-by-ease-of-processing`).
  Directly transfers from the document-side amendment: a screen in a
  recognized navigation/form pattern is not just faster to use, it
  reads as more trustworthy for the same functionality.

**Deliverable addition — convention-baseline clause**, folded into
tier 1 and tier 2:

- **Tier 1 (new checkable rule, `pattern_family_named`)** — every
  screen names, in a fixed metadata slot (this role: an added
  `convention_family` note alongside the screen's existing content
  spec, e.g. "Material navigation drawer", "HIG modal sheet", "common
  email/password login form"), which pattern family its primary
  navigation/form structure follows. `verification_method`: automated
  presence check only (field non-empty) — which family is the "right"
  one is not automatable, same split as tier 1's other rules. A screen
  whose convention family is `none-applicable` is legal only paired
  with a one-line stated reason (deviation-with-reason), mirroring the
  document-side rule's `none-applicable` escape and the existing
  `unverifiable:` escape-line convention.
- **Tier 2 (new checklist item 4, convention-conformance test)** —
  added to `tier2-new-user-checklist.md`: does the primary flow match
  imported (Material/HIG/common navigation-form) expectations, and if
  it deviates, is the deviation stated with a reason? Filed as its own
  item below, same citation discipline as items 1-3 (names the pattern
  family, states what specifically doesn't match, states a passing
  shape).

This amendment does not touch tier 3, the hand-off boundary, or §4-
equivalent reconciliation (this step has no separate reconciliation
section — content-design's required fields, per
`roles/specs/content-design.spec.json`, already generalize to the new
`convention_family` note the same way tier 1's other rules do).

## What did not work

None.
