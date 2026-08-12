---
status: proposed
files:
  - docs/issue-752/reports/defect-verification.md
---

# defect-verification pass on Audit C (#752)

Intent: independently re-derive the architecture role's already-merged phase-1 survey on core
judgment capability (which sub-areas are MET/PARTIAL/GAP for making agents render judgments, not
only artifacts), and reproduce or refute its claims against live repo state and real session
history — per this role's own scope (reproduce, never re-litigate quality, never fix).

Constraints stated so far: read-only, per the parent issue's own `provenance: read` acceptance
line and this role's directive (never propose a fix, never re-litigate a per-requirement
verdict). Findings must record an outcome of exactly one of `reproduced`/`not-reproduced`/
`blocked: needs-repro-access`; any `reproduced` finding needs an evidence pointer, never a
paraphrase; severity assigned strictly by the deterministic band (Critical/High -> blocking,
Medium/Low/Unknown -> advisory).

What will be done: the phase-1 survey at `docs/issue-752/reports/defect-verification/survey.md`
already carries the full attempt list (4 attempts, each naming its verbatim source), outcomes
(all 4 reproduced), and three advisory findings with evidence. On APPROVE, that survey is
promoted into the phase-2 record `docs/issue-752/reports/defect-verification.md` per contract v3
s19 — no new research, promotion/formatting of the already-gathered evidence into the record
shape.

Out of scope: any code/gate/schema change proposing the missing decision-record primitive the
underlying architecture survey already named (section 5) — that is hand-off work for whichever
role picks it up next, not this verification pass. Re-litigating the architecture survey's own
MET/PARTIAL/GAP verdicts is also out of scope; this pass only tests whether those claims still
reproduce against current repo state.

How you'll know it worked: `docs/issue-752/reports/defect-verification.md` exists after phase-2,
carries the 4-attempt list with named sources, records exactly one outcome per attempt, and any
reproduced finding carries an evidence pointer and a severity assigned by the deterministic band
— matching what `docs/issue-752/reports/defect-verification/survey.md` already established.

## What did not work

- First attempt at the phase-2 record hit `on-the-record/hooks/approval-gate.sh`: no
  `APPROVE issue-752/defect-verification` comment exists yet, so the phase-2-shaped write to
  `docs/issue-752/reports/defect-verification.md` was refused. Redirected the same content into
  the two phase-1 homes (this proposal and the survey) instead of the gated record.
- The survey draft's first two write attempts tripped `record-claim-guard.sh` repeatedly: bare
  PR-number pairs like "955/954/959" read as an unbacked count claim (issue #333), and several
  state/outcome sentences sat more than 3 lines below their nearest `canonical:` tag (issue
  #793/#870). Fixed by writing PR numbers as prose ("PRs 955, 954, and 959" / "PR 955") instead
  of slash-joined digits, and by placing a `canonical:` line immediately before each paragraph
  that asserts a PR/issue/hook state, rather than once per section.

Proposal: docs/issue-752/proposals/2026-08-12-defect-verification-audit-c.md
