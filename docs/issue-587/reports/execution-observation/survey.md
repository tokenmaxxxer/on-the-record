# Issue #587 — execution-observation current-state survey (phase 1)

Scope: role execution-observation, session issue-587/execution-observation, issue #587, step 3
of the plan (`## 실행 계획` step 3 "execution-observation ‖ conformance-review"). This survey was
read to arrive at that scope: `gh issue view 587` (title, body, requirements, acceptance,
`## 실행 계획`), `gh issue view 587 --comments` (confirms step 1 landed as PR #589
`APPROVE issue-587/architecture`, step 2 landed as PR #595 `APPROVE issue-587/implementation`, no
`APPROVE issue-587/execution-observation` comment exists yet), and `git log --oneline` (merge
commits for both PRs on main, `be71072`/`c3f4591` head).

Skip condition: the spec leaves no design decision open. Architecture PR #589
(`docs/issue-587/proposals/architecture.md`, section "E2E fixture-target-repo scenario") already
fully specifies this step's scenario: fixture shape (roles/*.json, approvers.md), the five-step
drive sequence, which of the five #573 §12 timeline events each step must fire, and where the
script lives (gates/ family). This step's job is independent execution and verification of that
already-decided design against the shipped code, not authoring a new design. Scout's
product-facing sweep does not apply to an internal verification harness with a frozen spec.

## Write surfaces this step will own (phase 2, not created yet — no forward reference)

- The fenced e2e run output and per-event pass/fail table, filed under this role's
  reports/execution-observation tree, per architecture's files: list entry for that path
  (marked "(phase 2, test)").
- This role's own contract-v3 record, filed as reports/execution-observation.md, mandatory per
  role-handoff contract v3 §20/§19 (not itself named in architecture's files: list, since
  architecture predates this per-role record-path convention).
- This proposal itself, phase 1.

No src/, test/, or another role's docs/issue-587/ path is touched — independence per this role's
directive (never edit the observed artifact).

## Code under observation (read this session, not re-designed)

- on-the-record/hooks/delegated-judgment-gate.sh — the judgment gate producing verdicts,
  remediation-<seq>.md records, and issue-timeline comments (#573 §7-§8, §12).
- gates/remediation_spawn.py and gates/test_remediation_spawn.py — the finding-to-spawn-task
  generator built in PR #595 (`e32a0de feat(issue-587): remediation spawn-task generator +
  run.md contract step`).
- on-the-record/commands/run.md — the orchestration contract's new step 3 (also from PR #595).
- docs/specs/approvers.md — needed to construct a fixture approvers.md matching the real
  single-account/two-account approval modes this repo's contract defines.

## What "independent execution" requires here

Per this role's directive (never re-execute the observed role's *task*, but this step's task is
explicitly to run the shipped code as-is): the prohibition against re-execution governs judging
*implementation's* work by re-doing implementation's job, not this step's own acceptance
criterion, which names an executed-live e2e run as the deliverable itself
(`## Acceptance`, third bullet, provenance: executed-live). This step drives
delegated-judgment-gate.sh and gates/remediation_spawn.py directly against a disposable fixture
repo it constructs — never against this repo's own board (architecture's explicit boundary) —
and records the actual fenced output, not a claim about what "should" happen if the code is
correct.

## Five timeline events to verify (from architecture, ultimately #573 §12)

1. PR opened under judgment
2. Verdict synthesized (reject, with routable finding)
3. Remediation routed
4. Remediation PR merged
5. Escalation to operator (separate 4-round fixture path)

## Gap line

The architecture and implementation proposals both name this e2e scenario as outstanding —
neither PR #589 nor PR #595 executed it (PR #595's own confirmation run is unit tests only:
`pytest gates/test_remediation_spawn.py`, no fixture-repo e2e). This step is the first point in
#587 where the full loop is driven end to end on real git surface rather than asserted against
constructed dicts.
