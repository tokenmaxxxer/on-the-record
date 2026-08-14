---
status: proposed
files:
  - docs/issue-1102/reports/conformance-review.md
---

# Proposal: conformance review of PR #1109 (issue-1102 obligation trigger)

## Intent

The conformance-review role's board condition (issue-521) fired: PR
#1109 landed code on `issue-1102/implementation` and no
conformance-review record exists yet for its commit sha. Render a
per-requirement verdict for northpole req#5 as delivered by that PR,
against issue #1102's own acceptance section.

## Constraints stated so far

- Per role-handoff contract v3 s19, the record file
  (`docs/issue-1102/reports/conformance-review.md`) is phase-2 output
  and waits for an approvers.md Approve (PR review Approve, or an
  issue comment reading exactly `APPROVE issue-1102/conformance-review`)
  before it is written.
- Verdict scale: Present, Surface, Absent, Incorrect, Unverifiable —
  never a holistic code-quality judgment, never a fix. Findings, if
  any, are addressed to the owning role (defect-verification for
  PR #1109's already-disclosed follow-up), never fixed here.

## What will be done

In phase 2, re-run the commands already captured live in this phase's
survey (`docs/issue-1102/reports/conformance-review/survey.md`) —
`python3 gates/test_roles_due.py` against current main, plus a direct
read of `gates/roles_due.py`'s `_matching_obligation`/`_trigger_matches`
and `roles/specs/defect-verification.spec.json`'s `use_when.trigger` —
and write one verdict per issue #1102 acceptance line:
1. failing-obligation-surfaces-role / resolved-does-not
2. empty-state (no obligations dir) → no role surfaced
3. provenance line (read-only, no check to verify)

The record will also carry forward the already-disclosed open finding
(uncommitted stand-in record can mask a failing obligation) as a
routed, not newly-discovered, finding.

## Out of scope

- Fixing the disclosed suppression-logic gap — that is
  defect-verification's or a future implementation session's work, not
  this role's.
- Re-auditing PR #1107 (phase-1 proposal-only PR) — it shipped no code.
- Any requirement beyond northpole req#5 / issue #1102's stated
  acceptance.

## How it will be known to have worked

The phase-2 record states one of Present/Surface/Absent/Incorrect/
Unverifiable per acceptance line, each backed by a `canonical:`/
`derived:` citation to a command re-run in that phase's own session
(not a re-statement of this phase's survey), matching this role's
record-format norm.
