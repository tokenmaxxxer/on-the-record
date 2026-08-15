# issue #745 — conformance-review current-state survey (phase 1)

## Board condition check

Per the marketplace conformance-review role spec (issue-521): an
implementation commit landed on the branch AND no conformance-review
record exists yet for this commit sha.

- canonical: `git log -1 --format=%H 22e162ed` and `git log --oneline -5`, both run in this session. Landed implementation commit `22e162ed44368c09989aa191664c7dd586d29a89` (subject "issue-745: Item 3 three-axis execution-observation skip-eligibility") is merged to main at `1425c881d0ec4d7124d73be013db5dde14589f17`.
- canonical: `find docs/issue-745 -type f | sort`, run in this session. That command lists only proposals/item3-execution-observation-conditioning.md, proposals/product-discovery.md, reports/implementation.md, reports/product-discovery.md, and the reports/product-discovery subtree — no reports/conformance-review.md file exists yet for this subject, so the board condition holds.

## Target artifact and spec

- Artifact under review: reports/implementation.md under docs/issue-745
  (commit 22e162ed). code_under_review: gates/skip_eligibility.py,
  gates/test_skip_eligibility.py, gates/spawn_on_pr.py,
  tests/test_spawn_on_pr.py, plus a row added to
  docs/specs/enforcement-boundary.md.
- Governing spec: proposals/item3-execution-observation-conditioning.md
  under docs/issue-745 (status: proposed, approved out-of-band via issue
  comment "APPROVE issue-745/implementation" per the implementation
  record's own upstream-basis section) — a diff/risk-conditioned
  execution-observation spawn-eligibility rule on three axes (size,
  reversibility, claim vocabulary).

## Scouting skip record

Skip condition: this task is a fidelity check of delivered code against
an already-approved, fully specified proposal (a fixed three-axis rule
with named thresholds, paths, and a regex source) — the proposal leaves
no open design decision for this review to steer toward; there is no
product-facing direction call for this role to scout comparable systems
for. Scouting skipped under the "spec literally leaves no design decision
open" condition.

## What phase 2 will check

Requirement list extracted from the proposal (verdicts deferred to phase
2, gated on approval per contract v3 s19):

1. Axis 1 (size): non-docs added+removed lines >= 50 trips population R.
2. Axis 2 (reversibility): diff touches gates/*.py,
   on-the-record/hooks/*.sh or hooks.json, roles/*.json, a migration
   path, or deletes any path — trips population R.
3. Axis 3 (claim vocabulary): the landing record OR PR body trips
   claim_scan.CLAIM_RE — trips population R.
4. Skip-eligible (population S) only when ALL three axes read low-risk.
5. Classification is written to a ledger so population membership is
   reproducible from ledger + diff history alone (measurement-window
   requirement).
6. Issue #476's fabrication_survival_rate guardrail machinery stays
   untouched by this change.
7. Test coverage exists for each axis's trip boundary, including the
   exact-50 size boundary and the deletion-regardless-of-path rule.
