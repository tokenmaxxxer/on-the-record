---
status: proposed
files:
  - docs/issue-787/reports/execution-observation/current-state.md
  - docs/issue-787/proposals/execution-observation.md
  - docs/issue-787/reports/execution-observation.md
---

# Proposal — re-run the #776 harness against the merged H1 fix (issue #787 step 3)

## Intent

Issue #787 step 3 asks this role to re-run the exact #776 baseline
harness against the same fixture and requirement, now that the
deliverable-guard H1 widening (PR #797, `dee7119`) is merged, and to
measure two pre-registered metrics named directly in this role's
assignment: `pre_write_delegation_events` (threshold >=1) and
`non_requirement_false_deny_count` on the empty-state variant (must be
exactly 0).

## Constraints

- Same fixture (`harness/fixture-target`), same representative
  requirement (`harness/driver.REPRESENTATIVE_REQUIREMENT`), same
  zero-human-intervention observation method as the baseline
  (`docs/specs/northpole-harness.md` §4).
- `provenance: executed-live` — every count cited from an actual
  captured transcript, never inferred.
- Verdict levels to check against evidence: **outcome** (spec §6's
  recomputation rule applied to this re-run's step-level results),
  **trajectory** (whether this role's own phase-1→phase-2 path was
  sound), **step** (which specific artifact — the merged hook script,
  or this harness invocation itself — is deficient, if any).

## What will be done

Instantiate two fresh fixture-target copies at paths carrying none of
the guard's own exemption segments (`scratch`, `tmp`, `.git`,
`plugin-cache`), install the on-the-record plugin project-scoped from
this repo's current `HEAD` (`df347d3`, confirmed identical to the live
plugin cache fetch), and launch two live `claude -p` sessions with
`CLAUDE_ROLE`/`ORCHESTRATE_OFF` explicitly unset from the subprocess
environment: (1) the representative requirement, to measure
`pre_write_delegation_events`; (2) a non-requirement chat prompt, to
measure `non_requirement_false_deny_count`. Re-score signals #1, #2, #5
from the captured transcripts and compare to the baseline. Report the
persist/pivot/kill decision.

## Out of scope

Editing `harness/`, `on-the-record/hooks/deliverable-guard.sh`, or any
other src/ path — this role only observes and records. Diagnosing *why*
any gap found here exists is out of scope; that routes back to a new
backlog finding, decided by the human.

## How this will be verified

`derived:` command output cited directly in
`docs/issue-787/reports/execution-observation.md`, never a restated
summary.
