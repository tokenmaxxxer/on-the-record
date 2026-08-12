---
status: proposed
files:
  - docs/issue-908/reports/defect-verification.md
---

## Intent

Issue #908 step 1 asks defect-verification to reproduce and pin, with
canonical file:line evidence, where in `spawn.py`'s spawn lifecycle a
dying delegation fails to leave a roster/record trace or emit an event,
and to confirm the poll-resume path retries blindly rather than off a
detected death. No fix.

## Constraints

- No fix: `spawn.py` is not in the write set. Only the finding-record
  file is.
- Severity must follow the deterministic band lookup (Critical/High ->
  blocking; Medium/Low/Unknown -> advisory) once phase 2 writes the
  finding, never freehand.
- The finding must cite an evidence pointer (repro steps / commit sha /
  run output / log excerpt), never a paraphrase — canonical:
  `docs/issue-908/reports/defect-verification/current-state-survey.md`
  (this session's phase-1 survey) already carries that evidence.

## What will be done (phase 2, on approval)

Write `docs/issue-908/reports/defect-verification.md`: restate the two
reproduced attempts from the phase-1 survey (spawn.py:4982-5134
unguarded span; spawn.py:2373/2382/2395 roster-only iteration) as one
finding addressed to `coding`, assign severity via the deterministic
band lookup, and close the record per contract v3 s19/§20 field
requirements (`what was done`, `why`, `upstream`, `kind:`,
`loop_state:`, `open findings`).

## Out of scope

Any fix to `spawn.py` (issue #908 step 2, assigned to implementation).
Building a hermetic live-kill reproduction harness (left as a note for
step 2, per the phase-1 survey's Accumulation section).

## How you'll know it worked

`docs/issue-908/reports/defect-verification.md` exists, cites the exact
`spawn.py` line numbers pinned in the phase-1 survey, states outcome
`reproduced` for both attempts with evidence pointers, and assigns a
severity band without freehand override.

## What did not work

None.
