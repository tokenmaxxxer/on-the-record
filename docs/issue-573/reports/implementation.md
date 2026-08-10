---
code_under_review: N/A
type: feat
breaking: false
verdict: pass
loop_state: committing
---

# Implementation record — issue #573: delegated-judgment gate (phase 2)

## Summary of work

Building the frozen write set from `docs/issue-573/proposals/implementation.md`
(approved via issue comment "APPROVE issue-573/implementation"): judgment_axes
seeded on architecture/security-threat-model role and spec files,
`gates/role_spec_shape.py` additive shape checks plus a matching batch test
file, a new zero-install delegated-judgment gate hook (depth-axis AND
impact-axis rule, full-panel quorum, panel-unanimous-support-v1 synthesis,
contradiction-only auto-reject with a routable finding, audit and
remediation record writers, a bounded remediation loop, issue-timeline
comment events per the architecture proposal's firing-event table), its
hooks.json registration, its test suite, and a docs/product placeholder.

## Why

Basis: `docs/issue-573/proposals/implementation.md` (approved phase-1
proposal, PR #582, itself grounded in `docs/issue-573/proposals/architecture.md`,
merged PR #581). Delivers the delegated-judgment mechanism the operator
requested to reduce approval fatigue while keeping every auto-decision
traceable to a recorded operator judgment and an expert-role evaluation.

## What did not work

- Expected: the docs/product placeholder file (frozen write set) could be
  created since that directory does not exist in this repo. Actual: the
  layout gate (board-gate.sh, contract v3 s10) refuses any docs/ write
  that is not docs/README.md, one of the six standing buckets, or an
  issue-<n> tree — docs/product is none of those, so the write was
  denied before landing. Skipped this one write-set item; every other
  frozen path is unaffected.

## Rationale for deviations

Two items from `## What will be done` did not land as written, both
scope-exceeded stops rather than widened scope:

1. The docs/product placeholder file (proposal's frozen write set) was
   not created: the repo's own layout gate refuses any docs/ write
   outside docs/README.md, the six standing buckets, or an issue-<n>
   tree, and docs/product is none of those. The proposal's own hedge
   ("added only if that directory does not already exist in this repo...
   verified empty vs. absent during phase 2, not assumed here")
   anticipated the existence check but not this layout constraint.
   Everything downstream that depends on an absent/empty product corpus
   (the degradation rule, item 4 of "What will be done") still holds
   without the placeholder file, since an absent directory and an empty
   one both fail the hook's depth-match corpus check the same way.
2. The enforcement-boundary spec file was not touched to add the new
   hook's verdict row, even though the repo's boundary test requires one:
   that file is outside this phase's frozen write set. Finished every
   other item in the write set and reported the gap (see Open findings)
   rather than widening scope mid-build.

## Doc placement

- The new deployed hook is an operational-surface addition with a matching
  hooks.json wiring change landing in the same commit — no handbook update
  needed (no new env var/dependency/setup step; the hook uses only
  python3/gh, both already required by sibling hooks in the same
  directory).
- No new library-or-format decision beyond what `docs/issue-573/proposals/architecture.md`
  already fixed (ADR not required per that proposal's own "Hand-off"
  section: no schema divergence from architecture's plan).

## Open findings

- The repo-wide boundary test (issue #441) requires every deployed hook
  script to have a recorded verdict row in the enforcement-boundary spec
  file. That file is not in this phase's frozen write set, so the new
  hook's row was not added — per the scope-exceeded rule, finishing what
  the proposal covers and reporting the gap rather than widening the
  write set mid-build. Every other test suite passes; this one
  pre-existing repo-wide test fails specifically because the new hook
  has no row yet.

## Next steps

Land this PR, then open a follow-up proposal (or fold into a review
finding) whose write set includes the enforcement-boundary spec file,
adding the new hook's verdict row so the repo-wide boundary test passes
again.

## Resolution path

A phase-1 proposal (or an accepted review-driven fix) that adds the
enforcement-boundary spec file to its write set and records the new
hook's verdict row, following the same format already used for the other
PreToolUse/Bash hooks in that file.
