---
kind: proposal
loop_state: proposed
---

# Proposal — issue #609, step 4 (execution-observation)

## Verdict levels to be checked, and against what evidence

This is a phase-1 proposal; no verdict is rendered here. Phase 2 will
render all three of the role's mandated verdict levels:

- **outcome** — whether PR #633 (subject issue-609, merged
  `2c78126cd932ee548d5fb5bca6c20b2906ba1aed`) satisfies issue #609's three
  acceptance criteria, recomputed as the worst case across cited
  step-level results, per `roles/specs/execution-observation.spec.json`'s
  recomputation rule.
- **trajectory** — whether the phase-1→phase-2 path across steps 1-4
  (product-discovery PR #614, architecture PR #618, implementation PR #627
  phase-1 / PR #633 phase-2) followed contract v3 s19: scouted where
  required, surveyed before proposing, obtained real human approval at
  each gate — checked against the issue's own comment trail
  (`gh issue view 609`) and each PR's approval-gate history.
- **step** — which specific artifact, if any, is deficient among
  `on-the-record/hooks/delegated-judgment-gate.sh`, `gates/role_spec_shape.py`,
  `roles/specs/requirements-engineering.spec.json`, and their shipped
  tests — checked by directly fixture-driving the shipped gate entrypoint
  (not re-reading its own tests as proof) and by inspecting the repo tree
  for a real measurement corpus.

## Skip record (scout-directive)

Scouting is skipped. Reason: this is not product-shaped work with a
competitive field to survey, and the acceptance criteria in issue #609's
body prescribe the check mechanically (fixture e2e drive with fenced
output; measured metric vs. registered threshold where the corpus permits,
deferred-with-reason otherwise) — there is no open design decision for an
external sweep to inform.

## What will be done (phase 2, on approval)

1. Construct fixture git repos (mirroring the pattern in
   `on-the-record/hooks/test_delegated_judgment_gate_triage.py`, read this
   session but not modified) with a **mixed** open-decision spec: multiple
   `open_decision_item` entries in one record, at least one single-owner
   `supports` case (expect `resolved`), at least one multi-owner
   conflicting-verdict case (expect `escalated`), and the threshold gate
   cleared (`docs/product/*.md` corpus present, only `docs/`-tier paths
   touched).
2. Construct a second fixture repo with an empty `docs/product/` corpus and
   no `roles/*.json`, to drive the empty-corpus degradation branch.
3. Extract the shipped hook's heredoc Python source the same way its own
   test does, and execute it via `python3 -c` against both fixtures —
   driving `on-the-record/hooks/delegated-judgment-gate.sh` directly, not
   re-executing the observed role's build steps.
4. Record fenced JSON output from both runs in the phase-2 record.
5. Check the repo tree for real production `docs/issue-*/decisions/triage-*.md`
   records to determine whether the registered effectiveness metric
   (`open_decision_triage_rate ≥ 30%`, `open_decision_misroute_rate ≤ 5%`,
   per `docs/issue-609/proposals/product-discovery.md`) can be measured
   this step; state the measured value against the threshold if the corpus
   permits, or the deferred-with-reason branch if it does not.
6. Render the three verdict levels in
   `docs/issue-609/reports/execution-observation.md`, with the
   independence statement preceding any verdict language, and recommend
   either closing #609 (if the effect is demonstrated) or a remediation
   round (if the corpus does not permit measurement this step).

## Out of scope

- Re-implementing or editing any part of the shipped triage mechanism.
- Re-running the observed role's own test suite as this role's evidence
  (its own tests are cited, not treated as this role's verification).
- Any change to `roles/specs/`, `gates/`, or `on-the-record/hooks/`.
- Filing a new GitHub issue — any deficiency found returns as a finding in
  this role's own record; the human files an issue if they judge it
  warranted.
