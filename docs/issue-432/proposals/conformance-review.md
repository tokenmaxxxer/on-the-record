---
status: proposed
files:
  - docs/issue-432/reports/conformance-review/survey.md
  - docs/issue-432/proposals/conformance-review.md
---

# issue #432 step 1 — conformance-review survey (phase 1)

Intent: audit the merged fix for `spawn._issue_comments`'s stale-shape
call sites (commit `daa2d27d`, PR #433, `issue-432/implementation` ->
`main`) against what the implementation role's own record
(`docs/issue-432/reports/implementation.md`) claims was done, and
classify each falsifiable requirement as Present/Surface/Absent/
Incorrect/Unverifiable. Survey-only phase — the full verdict report is
phase 2, gated on this proposal's approval.

Constraints: this role classifies spec-vs-artifact conformance only — it
does not fix the target artifact, does not judge design merit, and does
not duplicate the fix work already scoped away in the implementation
record's own "Scope 3" (cross-record on #398/#290, explicitly not
resolved by #432).

What will be done:
`docs/issue-432/reports/conformance-review/survey.md` extracts 8
falsifiable requirements from the implementation record (both fixed call
sites unpack the tuple shape, the `ok=False` -> post-anyway decision,
the exhaustive call-site sweep, the regression tests, the full suite
passing, the Scope-3 exclusion, and the diff's file scope), each
grounded in the merged diff (`git show daa2d27d --stat`) or the
implementation record itself.

Out of scope: phase 2's actual per-requirement verdict table
(`docs/issue-432/reports/conformance-review.md`), which is gated on this
proposal's approval per contract v3 s19.

How it will be known to have worked: the survey names all 8
requirements with a `canonical:` source for each (implementation record
or merged diff), and every `_issue_comments(` call site in the repo is
independently re-enumerated (not just quoted from the implementation
record) as evidence for the exhaustive-sweep requirement.

## What did not work

None.
