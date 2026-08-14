---
status: proposed
files:
  - docs/issue-1080/reports/execution-observation.md
---

Scope statement precedes this proposal (see
docs/issue-1080/reports/execution-observation/survey.md, written first,
per SURVEY-FIRST ORDER). Scout-directive skip condition: this role's
deliverable is an EARL-style observation record over an already-landed
artifact, not a product-shaped build with an open design decision —
scouting best-in-class comparable systems has no target here, so it is
skipped per the "spec literally leaves no design decision open"
condition.

## Request

Issue #1080 requires an `execution-observation` record for the commits
landed on `issue-1080/implementation` (PR #1094, PR #1096) — no such
record exists yet (confirmed in the survey via `ls
docs/issue-1080/reports/`).

## Constraints

- Never edit `spawn.py`, `gates/test_requirement_drift.py`, or anything
  under `docs/issue-1080/reports/implementation*` or
  `docs/issue-1080/proposals/2026-08-12-*` — those belong to the
  observed role, not this one.
- Write only `docs/issue-1080/reports/execution-observation.md` (this
  role's sole write_scope per `roles/specs/execution-observation.spec.json`).

## Rationale

The alternative — folding the record into a bare summary with no
per-level breakdown — was rejected because the role directive requires
three distinct verdict levels (outcome / trajectory / step), each with
adjacent citations, and the EARL spec requires per-claim
subject/test/result/assertedBy/mode fields; collapsing them would fail
both the role directive's and the spec's own requirements.

## What will be done

`docs/issue-1080/reports/execution-observation.md` will be written
(phase 2, after this proposal is approved) rendering all three verdict
levels against the evidence already gathered in the survey:

- **outcome**: recomputed via `roles/specs/execution-observation.spec.json`'s
  worst-case-over-cited-step-results rule, checked against the
  implementation record's own cited acceptance commands (`pytest
  gates/test_requirement_drift.py -v`, `ast.parse` on `spawn.py`),
  re-run this session against the current branch tip.
- **trajectory**: three named checks (scouted-when-required,
  surveyed-before-proposing, approved-by-human), each judged against
  PR #1094's diff and the `APPROVE issue-1080/implementation` issue
  comment already located in the survey.
- **step**: judged against the two `spawn.py` hunks in PR #1096's diff
  identified in the survey's DIFF-SCOPE section, plus both hunt records
  already read (the pre-landing unguarded-import finding, resolved
  before merge; the after-proposal PR-body-exemption finding, left
  open by the observed role's own design and re-checked against the
  current branch tip).

## Out of scope

- Editing or re-executing any of the observed role's artifacts.
- Filing a follow-up GitHub issue for the open step-level finding —
  that is the human's call, not this role's.

## Accumulation

Not accumulation-cost-shaped: this is a one-shot record for one
observed commit range, not a per-item list or loop that grows with
scale.

## How you'll know it worked

`docs/issue-1080/reports/execution-observation.md` exists on this
branch, states an independence statement before any verdict language,
addresses all three verdict levels (marking not-applicable with a
reason where relevant), cites a source adjacent to every verdict
sentence, and sets `loop_state: handed-off`.
