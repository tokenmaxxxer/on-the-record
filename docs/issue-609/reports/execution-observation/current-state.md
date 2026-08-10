---
kind: current-state-survey
loop_state: running
---

# Current-state survey — issue #609, step 4 (execution-observation)

## Scope

Role `execution-observation`, session on branch `issue-609/execution-observation`,
observing issue #609 ("Triage spec-stage open decisions through the
judgment-axis panel before they reach the operator"), specifically PR #633
("issue-609: spec-stage open-decision triage (implementation, phase 2)",
merged as `2c78126cd932ee548d5fb5bca6c20b2906ba1aed`, tip commit
`e2a625120f61e2aefcf3abfe48f3cb5b83bb451c`).

What was read to arrive at this scope, this session: `gh issue view 609`
(full body + comment trail — confirms steps 1-3 approved and merged, step 4
open); `gh pr view 633 --json files,mergeCommit` (file list + merge SHA);
`docs/issue-609/reports/implementation.md` (the observed role's own phase-2
record, full text); `on-the-record/hooks/delegated-judgment-gate.sh` (the
shipped triage block, read only — not edited); the shipped test
`on-the-record/hooks/test_delegated_judgment_gate_triage.py` (full text,
read as a pattern reference for how to drive the hook, not modified);
`docs/issue-609/proposals/product-discovery.md` (the registered
effectiveness metric and decision rule); `find docs -path
"*/decisions/triage-*.md"` and `git log --oneline --all --grep=triage`
(confirms zero production triage records exist repo-wide).

## What is already shipped (PR #633, merged)

1. `gates/role_spec_shape.py` — `check_open_decision_item(entry)`,
   validating `item`/`source_role`/`source_path`/`candidate_axes` shape.
2. `roles/specs/requirements-engineering.spec.json` — `open_decision_item`
   added to `required_fields`.
3. `on-the-record/hooks/delegated-judgment-gate.sh` — a new triage block
   inside the `gh pr create` branch: for each `open_decision_item` found in
   a changed `docs/issue-<n>/reports/*.md` file, routes to owning role(s)
   via `judgment_axes ∩ candidate_axes`, looks up each owning role's latest
   `axis_evaluation`, escalates on threshold-exceeded (reused
   `not (DEPTH and LOW_IMPACT)`) OR panel-conflict (mixed
   supports/contradicts), writes a `triage-<sequence>.md` audit record
   under `docs/issue-<n>/decisions/`.
4. Two new test files (`gates/test_role_spec_shape_open_decision.py`,
   `on-the-record/hooks/test_delegated_judgment_gate_triage.py`) already
   covering, per the observed role's own record's Verification-run section:
   shape validation, empty-corpus degradation, panel-conflict escalation,
   single-owner-supports resolution.

## What step 4 (this role) is asked to add, per the issue body

Acceptance criterion 2, verbatim: "On a fixture spec with mixed open
decisions, in-scope items receive owning-role evaluations and only
above-threshold items escalate, each with evaluations attached. check: e2e
fixture drive with fenced output. empty state: an empty docs/product
corpus degrades to full escalation."

Acceptance criterion 3: "Pre-registered effectiveness metric measured at
step 4 (fraction of open decisions resolved without operator involvement;
guardrail: operator-reversal rate on triaged items) ... check: step-4
record states measured value vs threshold. empty state: empty measurement
corpus -> effect-not-demonstrated branch."

The observed role's own fixture tests already exercise these three
outcomes individually; this role's job is an *independent* fixture drive
against the shipped entrypoint (not a re-read of the observed role's
tests) that specifically demonstrates the **mixed** case — multiple open
decisions of different dispositions in one spec, driven in one run — plus
the effectiveness-metric measurement itself, which the observed role's own
record explicitly deferred to this step under its "What was NOT done"
section: "The `open_decision_triage_rate`/`open_decision_misroute_rate`
effectiveness measurement itself (step 4, execution-observation)."

## Unknowns / gaps this survey found

- No production `triage-*.md` record exists anywhere in the repo tree
  (confirmed via `find`) — the registered effectiveness metric
  (`open_decision_triage_rate ≥ 30%`, `open_decision_misroute_rate ≤ 5%`,
  per `docs/issue-609/proposals/product-discovery.md`) has no real corpus
  to measure against yet. This is a gap the proposal below must address
  directly (it maps to the acceptance criterion's own named empty state,
  not a defect to fix).
- The shipped hook has no importable module form (zero-install
  constraint, confirmed in the observed role's test docstring) — driving
  it requires extracting the heredoc source the same way its own test
  does; there is no other supported entrypoint.
