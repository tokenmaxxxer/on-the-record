---
status: proposed
files:
  - docs/issue-817/reports/defect-verification.md
---

# Proposal — issue #817 defect-verification, step 1

## Intent

Reproduce and pin the exact code path by which
`on-the-record/hooks/deliverable-guard.sh` does not deny a plain,
un-delegated session's direct write to the #776 harness fixture's
deliverable path (issue #815's event 8). No fix — that is issue #817
step 2 (implementation), gated on this record.

## Constraints

- Cite the #787/#815 merged execution-observation record as canonical
  evidence for the transcript-side facts (event 8, zero prior denies);
  do not re-litigate its FAIL verdict.
- Check every bypass candidate the issue names (relative-`cwd`,
  role-session branch, exemption-segment over-match) before concluding;
  rule each in or out with evidence, not assumption.
- No fix, no test additions — those belong to step 2.

## What will be done

Write `docs/issue-817/reports/defect-verification/current-state.md`
(already committed alongside this proposal, phase-1 survey/homes) pinning
the confirmed mechanism: `deliverable-guard.sh`'s git-root-absence branch
(`if root is None: sys.exit(0)`) silently ALLOWs because
`harness/driver.py`'s `instantiate_fixture_target` never `git init`s the
fixture copy it produces — so the fixture workspace has no `.git`
anywhere in its ancestry, and the guard's git-root walk never finds one
to deny against.

On phase-2 approval, `docs/issue-817/reports/defect-verification.md`
(the role's own contract-mandated record — findings, severity,
loop_state) is written per `verify:finding-record` /
`verify:severity-classification`, restating this survey's confirmed
mechanism as a formal finding addressed to `coding`, with severity
assigned by the deterministic band lookup.

## Out of scope

- Any change to `deliverable-guard.sh` or `harness/driver.py` (step 2,
  implementation role).
- Re-running the #776 harness (step 3, execution-observation role).
- Cause A (#810, permission-mode denial of `spawn.py`) — separate issue.

## How you'll know it worked

`docs/issue-817/reports/defect-verification/current-state.md` names one
confirmed mechanism (file:line) with a live, reproducible command
sequence showing identical payload/file/session differing only in
`.git` ancestry presence, and rules out or confirms each of the three
candidates the issue names.

## Scout

Skip: investigative reproduction/diagnosis task with no product-facing
design decision open — the issue itself names the exact candidate
mechanisms to check; there is no external field to scout.

## What did not work

None.
