---
status: proposed
files:
  - docs/issue-750/reports/defect-verification.md
---

## Intent

Issue #750 asks for a detailed audit of role-session behavior (spawn to
judge to produce to record to complete) against the 7 northpole
requirements. This proposal covers the defect-verification role's slice:
independently reproduce the invoking prompt's three named candidate
defects (#947, #705, #785) plus self-devised attempts against the prior
architecture survey's own claims, and write a verified finding record
pinning which reproduce, with reproduction evidence, mapped to the
northpole requirement each blocks.

## Constraints stated so far

- Read-only reproduction; no fixes proposed (defect-verification role
  never fixes).
- Every reproduced finding carries an evidence pointer (repro steps,
  command output, or commit sha) — never a paraphrase.
- Severity assigned only by the deterministic band (Critical/High to
  blocking, Medium/Low/Unknown to advisory), never freehand.
- Write set is docs/issue-750/reports/defect-verification.md only.

## What will be done

Phase-1 reproduction is complete:
docs/issue-750/reports/defect-verification/survey.md runs 5 attempts —
3 sourced from the invoking prompt's named defects, 2 self-devised from
the prior architecture survey's own claims — against spawn.py, the
gate scripts it does and does not wire into, and the actual issues named.
Results: attempt 1 (#947) not-reproduced (mismatched issue — #947 is a
Monitor self-wake gap, not a spawn/commit defect); attempts 2 (#705) and
3 (#785) reproduced (both have merged implementation PRs but the source
issues remain OPEN, i.e. unverified closure); attempt 4 reproduced a
fail-open gap in reexecution_gate's merge-time wiring (blocks northpole
req #3); attempt 5 reproduced spawn.py copy drift that outdates the
prior survey's canonical-copy claim.

Phase-2 (this proposal, on approval) writes the final
defect-verification record at docs/issue-750/reports/defect-verification.md,
per role-handoff contract v3 s19's required shape: one finding block per
reproduced attempt, each addressed to coding, with its evidence pointer,
severity band, and the northpole requirement it blocks; the
not-reproduced and any newly-attempted outcomes recorded per the role's
three-value outcome rule; and the record's required fields (what was
done, why, upstream basis, kind, loop_state, open findings).

## Out of scope

- Fixing any reproduced defect (#705's stranding pattern, #785's
  two-phase default, or the reexecution_gate fail-open gap) — this is
  role-appropriate follow-up for coding, not this role.
- Re-litigating the prior architecture survey's MET/PARTIAL/GAP
  classification as if it were itself the attempt under test — attempts
  4-5 test specific factual claims inside that survey (caller existence,
  spawn.py line counts), not its overall verdict.
- Determining which spawn.py copy actually executes at a live spawn —
  that requires observing a live spawn, out of scope for a static
  read-only reproduction pass.

## How you will know it worked

docs/issue-750/reports/defect-verification.md exists, records an outcome
for every attempt in the phase-1 attempt list (no exceptions), a finding
block with evidence and severity for every reproduced attempt, and each
finding names the northpole requirement it blocks — matching issue
#750's acceptance criteria for the defect-verification role's slice.

## What did not work

None.
