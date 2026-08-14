---
status: proposed
files:
  - docs/issue-1098/reports/conformance-review.md
---

## Intent

Conformance review of issue-1098's landed commit (7df3f55, squash-merged
to main as 1ce4a7ff) against the two northpole requirements the issue
itself cites: req#3 (real-wired verification) and req#5 (problems are
not pushed back to the human).

## Constraints already stated so far

- YOU-DECIDE role: a per-requirement verdict (Present|Surface|Absent|
  Incorrect|Unverifiable), never a holistic quality judgment, never a
  fix.
- Two-phase flow (contract v3 s19): this proposal and the current-state
  survey (docs/issue-1098/reports/conformance-review/survey.md, already
  committed) are the only phase-1 output; the EARL-shaped verdict record
  itself is phase-2, gated on an approvers.md Approve.

## What will be done (phase 2, once approved)

Write docs/issue-1098/reports/conformance-review.md with one EARL-shaped
`test` entry per requirement (per roles/specs/conformance-review.spec.json):

- req#3: `result` derived from whether `landing_obligation.py`'s
  resolution path is actually driven by `reexecution_gate.py`'s
  live-rerun verdicts (survey finding: yes, composes correctly) —
  expected verdict Present.
- req#5: `result` derived from whether the full "failing obligation ->
  role agent spawned, no operator prompt" chain is closed. The survey
  found the state-tracking and the trigger-matching halves both landed
  (issue-1098 and issue-1102 respectively), but the evaluator that would
  act on a match (`spawn.py roles-due`) is advisory-only by its own
  author's comment, and no hook invokes it automatically — expected
  verdict Surface (a real, composable step short of the requirement's
  own "no operator prompting" bar).

Overall record `verdict` recomputed as the worst case across the two
entries per the spec's `recomputation` rule (Surface, since one entry is
Surface and the other Present).

## Out of scope

- Fixing the advisory-only spawn gap — hands off to whichever role
  (architecture/implementation) owns `spawn.py`'s `roles-due` autospawn
  decision; this role only reports the gap.
- Re-auditing issue-1102's own commit on its own merits — it is cited
  here only as the composing half of req#5's chain for issue-1098's
  subject.

## How you will know it worked

The phase-2 record's `axis_evaluation`/`test` entries each resolve to a
real repo path or command already reproduced in the survey; the overall
`verdict` matches the worst-case entry per the spec's recomputation
rule; `review-traceability`'s `finding-record` skill is used to record
each verdict rather than free-form prose.
