---
issue: 2165
role: execution-observation
---

# issue-2165 — execution-observation current-state survey

## Scout skip record

Scouting is skipped for this proposal round: the spec leaves no design
decision open (scout-directive's second mandatory skip condition).
canonical: roles/specs/execution-observation.spec.json, read this session —
its own gate_c_status field states "N/A — mechanical aggregation, not
investigative finding... there is no discretionary finding step to ground
a lens-based method for," and its recomputation rule fixes the verdict
method (worst case across cited results) independent of any judgment call
this proposal round could make instead. There is no exemplar field, product
category, or comparable-system pattern for this role's own output shape to
scout against — the output shape (EARL 1.0 subject/test/result/assertedBy)
is itself fixed by the spec file, not a design choice open to this round.

## Current state: issue #2165 and its implementation branch

canonical: gh issue view 2165, read this session — the issue reports
observer roles (execution-observation, conformance-review) respawning 50+
times over 6 hours via spawn_on_pr's watchdog, most respawns after the
subject's own implementation PR had already merged; asks to close the gap
in missing_verification()'s merge-skip check and add a regression test.

canonical: git log origin/main..origin/issue-2165/implementation --oneline,
read this session — four commits landed on branch issue-2165/implementation,
none yet merged to main: eaa98d5d (consult-trace), 0d71f567 (phase-1
survey+proposal: a sticky merged-confirmation cache mirroring
closure_sweep.py's out-of-index-seen pattern), ce01c9e0 (a self-logged
phase-1/phase-2 write-set deviation, reverted before commit, never landed),
e2fdec45 (phase-2 delivery: MERGED_SEEN_STATE_REL,
load_merged_seen/_save_merged_seen, the merged-seen skip in
missing_verification(), and two new regression tests in
tests/test_spawn_on_pr.py).

canonical: gh pr view 2170 --json state,mergeable,author, read this session
— PR #2170 (issue-2165/implementation) is open, author JiwonJung94, mergeable.

canonical: gh issue view 2165 --comments, read this session — a comment
whose entire body is exactly "APPROVE issue-2165/implementation" from
JiwonJung94 (listed in docs/specs/approvers.md) precedes the session-end
comment naming PR #2170 opened — the phase-2 approval that gated the
implementation role's own delivery.

## This role's own record state

The pre-existing skeleton at docs/issue-2165/reports/execution-observation.md
carries empty subject/test/result/assertedBy frontmatter and unfilled
section bodies — no execution-observation record for commit
e2fdec458f6d43671458844e1259ec0de91b95ff exists yet. canonical: find docs
-path "*/issue-2165/reports/*" -maxdepth 3, read this session — output:
docs/issue-2165/reports (dir) and
docs/issue-2165/reports/execution-observation.md only; no
docs/issue-2165/proposals/ directory and no
docs/issue-2165/reports/execution-observation/ subdirectory exist yet on
this branch.

## Write surfaces this round expects to touch

- docs/issue-2165/reports/execution-observation/survey.md (this file)
- docs/issue-2165/proposals/execution-observation.md (phase 1, this round)
- docs/issue-2165/reports/execution-observation.md (phase 2, once approved
  — this role's sole write_scope entry per
  roles/specs/execution-observation.spec.json)

## Precedent read

canonical: docs/issue-659/proposals/execution-observation.md, read this
session — the same role's own phase-1 proposal for a prior issue, showing
the established shape (Intent, Constraints, a build-plan section, Out of
scope, a verification section) for this role's proposal round and
confirming the file-list convention (survey, proposal, and the target
record all listed under the proposal's own `files:` frontmatter).
