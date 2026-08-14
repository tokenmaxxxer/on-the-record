---
status: proposed
files:
  - docs/issue-1035/reports/execution-observation.md
---

## Request
Issue #1035 asks the execution-observation role to judge whether the implementation role's phase-1→phase-2 execution on issue #1035 was sound, by reading the actual landed artifacts — never by re-executing the observed task. Trigger: spawn_on_pr.py auto-spawned this session because a commit landed on `issue-1035/implementation` with no execution-observation record yet.

## Constraints
- Never edit `gates/`, `spawn.py`, `tests/`, or `docs/issue-1035/reports/implementation*` — this role's own record is the only writable surface.
- Never re-run the implementation role's task; only read its artifacts (PR #1053 diff/commits, its own record) plus this role's own live checks (pytest against the merged code, ancestry check) as evidence.
- Record all three verdict levels even when one does not apply.

## Rationale
All three verdict levels named up front, and the evidence class each will draw on — no verdict is rendered here, only the plan:
- **outcome** — did the delivered PR land what issue #1035 asked, recomputed as the worst case among the implementation record's cited step-level results (its own `canonical:`-tagged acceptance runs) plus this session's own live rerun of `tests/test_flows.py -k decision` against the current branch.
- **trajectory** — three named pass/fail/not-applicable checks: scouted-when-required (current-state survey in `docs/issue-1035/reports/implementation/survey.md`, read before the proposal existed), surveyed-before-proposing (scope statement precedes proposal-shaped language in that same survey), approved-by-human (the exact `APPROVE issue-1035/implementation` issue comment from an approvers.md account, matched against the string-equality rule).
- **step** — any specific artifact found deficient, each with subject/test/result/assertedBy in the spec's per-claim vocabulary, drawn only from diff hunks the survey already logged as touched by PR #1053 (the diff-scope rule).

## Accumulation
Not accumulation-cost-shaped — one observation record for one already-closed issue's already-merged PR, not a per-item or repeated-cost pattern.

## What will be done
Write `docs/issue-1035/reports/execution-observation.md` per the spec's required fields (`code_under_review:` as a file list, `loop_state:`, etc.), citing PR #1053's diff/commits and the implementation role's own record, plus this session's own live pytest rerun, then commit and push it in the same PR that carries this proposal.

## Out of scope
Any change to the observed artifact itself, and any new issue filing (issues are user-authored only under contract v3).

## How you'll know it worked
`docs/issue-1035/reports/execution-observation.md` exists on the branch with `loop_state: handed-off`, all three verdict levels present, and every verdict sentence citing a commit SHA, file:line, or PR comment URL.
