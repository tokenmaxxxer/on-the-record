---
status: proposed
files:
  - docs/issue-754/reports/defect-verification.md
---

## Intent

Issue #754 asks for a detailed, read-only audit of automated
problem-resolution composition against northpole req #5, verified
independently rather than re-litigating the merged architecture
survey's (PR #761) verdicts — classifying each sub-area MET/PARTIAL/GAP
with file:line evidence, ranked by northpole-centrality and observed
failure frequency.

## Constraints stated so far

- Read-only: no code or mechanism changes (issue #754 `provenance:
  read`).
- Write scope limited to `docs/issue-754/**`.
- Every PARTIAL/GAP must name the concrete missing mechanism and a
  rank; a sub-area with no serving mechanism is recorded GAP, never
  omitted.
- Never `gh pr merge`.

## What will be done

Phase-1 research is complete:
`docs/issue-754/reports/defect-verification/survey.md` independently
re-derives the architecture survey's two structural claims against
current HEAD (both reproduced), and adds two self-devised attempts:
whether the #958 deviation loop actually reaches a spawned role session
(reproduced as a gap — it does not, `on-the-record/hooks/
directive.sh:10` exits before emitting the loop whenever `CLAUDE_ROLE`
is set), and whether the merged poll-heartbeat.sh (#922) is a
counter-example (not-reproduced — it is a reporting surface, not a
composition primitive).

Phase-2 (this proposal, on approval) writes
`docs/issue-754/reports/defect-verification.md` per role-handoff
contract v3 s19's required record shape: restates the survey's
attempts/outcomes and MET/PARTIAL/GAP classification, and closes with
the record's required fields (what was done, why, upstream basis,
kind, loop_state, open findings referencing the survey's Finding 1/2).

## Out of scope

- Fixing the identified gaps — this pass only records and ranks them;
  remediation is role-appropriate follow-up work the ranking seeds.
- Re-litigating the architecture survey's step-by-step loop
  description or its scoping of issue-authorship/merge as deliberate
  human gates (this pass independently re-checked both and found no
  evidence to revise them).

## How you will know it worked

`docs/issue-754/reports/defect-verification.md` exists, records every
attempt's outcome (reproduced/not-reproduced/blocked), classifies each
sub-area MET/PARTIAL/GAP with file:line evidence, and every PARTIAL/GAP
names a concrete missing mechanism and a rank — matching issue #754's
acceptance criteria.

## Hunt record

after-proposal: docs-only, no before-landing dispatch — every path
touched by this transition is under `docs/`, so the after-proposal
warrant-hunter dispatch is skipped per the docs-only fast path.

## What did not work

- First survey draft's Attempt 4 opening spanned 3 lines before its
  `canonical:` tag and separately buried its tail sentence >3 lines
  past the nearest canonical citation — `record-claim-guard.sh`'s
  state/defect-claim check (issue #793 mirror) refused both. Fixed by
  compressing Attempt 4's header to one line immediately followed by
  its canonical grep, and adding a second canonical citation ahead of
  the tail sentence.
- The classification section's original table format put the
  farthest-out MET row's outcome claim more than 3 lines from any
  canonical tag, tripping both the #793 state-claim check and the #870
  execution-evidence check. Fixed by converting the table to a bullet
  list with each MET/PARTIAL/GAP verdict's canonical citation inline in
  the same bullet.
