---
status: proposed
files:
  - docs/issue-1199/proposals/2026-08-13-issue-retrospective-tool-landscape.md
---

# issue-1199 (issue-retrospective): tool-landscape fold-in

kind: proposal
subject: issue-1199

## Background

Issue #1199 (northpole req#1/req#5) asks every role to survey the
plugins/tools its domain's practitioners actually use and fold
distilled learnings, natively, into a bounded rulebook section — no
tool catalog, no "learned from X" attribution in the public rulebook.
Read basis: `docs/issue-1199/reports/issue-retrospective/survey.md` and
`docs/issue-1199/reports/issue-retrospective/scout-brief.md` (both
written this turn). Round-end value gates (A procedure-value, B
blind-onboarding, per `docs/handbooks/round-end-value-gates.md` in the
rulebook repo) will be walked at record-writing time in phase 2, as
this role's contract requires for every record; this proposal itself
adds no new content there beyond naming that it will happen.

## Target reader

A phase-2 implementing session (this role) editing
`tokenmaxxxer/issue-retrospective-rulebook` directly — no new file, a
small number of edits to the operating-content surfaces that already
govern this role's behavior.

## Proposed changes (native, no tool-attribution)

Per the scout brief's adopt list:

1. `issue-retrospective/hooks/directive.sh` (`produces`, phase-2 step 2,
   section (1) Timeline) — add: build the timeline forward from the
   earliest known record entry, not backward from the resolved outcome
   (hindsight-bias guard); prefer the earlier-timestamped entry when
   two records disagree.
2. `issue-retrospective/hooks/directive.sh` (`produces`, section (4)
   What we learned) — add: state the learning as narrative
   understanding, kept distinct from the action-item list that follows
   it.
3. `issue-retrospective/hooks/directive.sh` (`produces`, section (5)
   Action items) — add: each item also names how its completion would
   be verified, alongside the existing owner + concrete-change
   requirement.
4. `docs/handbooks/round-end-value-gates.md` — add a short §C
   documenting the timeline sourcing preference (earliest-timestamped
   entry wins) as a third non-blocking checklist question alongside A
   and B.
5. `README.md` — one pointer line to §C, mirroring the existing
   Additionally-block convention.

No new gate logic; no `.sh` mechanical gate script touched (out of
scope, same boundary the brand-design and technical-writing units
already drew). No tool/repo name appears in any of the five edits — the
adoption-evidence trail stays only in this repo's scout brief and the
phase-2 record.

## Synthesis

Not a paste of the survey or scout brief: the survey's five sibling
records converge on one operating rule (edit the named target in the
same delivery; never name a tool/repo inside the public rulebook), and
the scout brief's three angles converge on one methodology rule
(forward-built timeline as a hindsight-bias guard; learning kept
distinct from action items). Combining both convergences yields the
five concrete edits above — each edit satisfies both the delivery-
mechanics convergence (real file, same session) and the methodology
convergence (a genuinely new rule, not a restated existing one).

## Adopted norms (sourced rationale)

- Apply-not-reference: adopted because
  `docs/issue-1199/reports/technical-writing.md`'s own "Retrofit"
  section shows the cost of not doing this (a second delivery cycle) —
  cited in the survey above.
- No tool-attribution in the public rulebook: adopted because three
  independent sibling records (brand-design, ux-engineering,
  technical-writing's second delivery) converge on the same operator
  amendment — cited in the survey above.
- Forward-chronological timeline / hindsight-bias guard: adopted
  because it is the one rule three independently-searched sources
  (Rootly, incident.io, PagerDuty) converge on for timeline
  construction — cited in the scout brief's Sources list.
- Learning/action-item separation: adopted because it is the Howie/
  Jeli guide's own stated design move, distinct from (and not already
  covered by) this role's existing plural-contributing-factors rule —
  cited in the scout brief's Sources list.

## Rationale

- Directly answers the sibling-record survey's gap (this role's own
  rulebook had no fold-in yet) and the scout brief's Gap line (the
  field's live-capture must-be doesn't transfer; the ordering and
  learning/action-item-separation moves do).
- Edits the named upgrade targets in the same delivery (applied, not
  referenced), per the technical-writing retrofit precedent already
  read in the survey.
- No tool-attribution framing anywhere in the rulebook, per the
  ux-engineering/technical-writing precedent already read in the
  survey.

## Out of scope

- Any other role's tool-landscape unit.
- The issue's 43-item tracker beyond this role's own row.
- Gate `.sh` logic changes.

## Approval

Awaiting a PR review Approve (two-account mode) or an issue-level
`APPROVE issue-1199/issue-retrospective` comment (single-account mode)
from a `docs/specs/approvers.md` account before phase 2 begins, per
contract v3 s19. This comment was already posted (JiwonJung94,
2026-08-13T07:36:50Z, exact string `APPROVE issue-1199/issue-retrospective`,
canonical: `gh issue view 1199 --json comments`, read this session) —
phase 2 proceeds in the same session per contract v3 s19's approval
path, which does not require a PR to already exist before the approval
comment lands.
