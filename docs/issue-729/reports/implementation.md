---
code_under_review:
  - test/check-write-set-conflicts.test.sh
  - test/claim-scan-preflight.test.sh
  - test/test_bootstrap_timing.py
  - test/test_latency_report.py
  - test/test_portability_audit_table.py
  - test/test_side_effect_round.py
  - test/test_silent_failure_repros.py
  - test_approve_scope.py
  - test_flows.py
  - test_gates.py
  - test_issue_bundling.py
  - test_repo_scope_gate.py
  - test_spawn.py
  - test_spec_index.py
  - test_vocab_coherence_roles.py
  - shape_contracts.py
  - spawn.py
  - docs/handbooks/operations.md
  - docs/handbooks/test-fixture-shape-contracts.md
  - docs/specs/reconciled-index.md
  - docs/handbooks/test-layout.md
type: refactor
breaking: "false"
verdict: pass
loop_state: coding
---

# Implementation record — issue-729 (consolidate test homes)

## Upstream

Basis: `docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md`
(phase-1, merged to main via PR #739). Approved via issue-level comment
`APPROVE issue-729/implementation` (single-account mode, jjongkwann,
listed in `docs/specs/approvers.md`), followed by a non-reverting
feedback comment narrowing this PR to move-only (split of `test_spawn.py`
deferred to a follow-up issue, to be filed once the move lands).

## What was done

In progress — this section is filled in as the move lands. See
`loop_state` above for current phase.

## Why

Root-level test scatter (`test/`, nine root `test_*.py`/`shape_contracts.py`
files, plus colocated `gates/`/`on-the-record/hooks/` tests) makes it hard
for a new test author to know where a file belongs. The proposal
consolidates `test/` and the root `test_*.py` files into one `tests/`
home, leaving `gates/`/`on-the-record/` colocation and root `conftest.py`
untouched (import-mechanics reasons — see proposal Rationale (b)/(c)).

## What did not work

None yet.

## Open findings

None yet.

Resolution path: none open; will be filled in if the acceptance checks
below turn up a discrepancy.

## Next steps

Execute the proposal's "What will be done" list, then run the three
"How you'll know it worked" checks and record their actual output.
