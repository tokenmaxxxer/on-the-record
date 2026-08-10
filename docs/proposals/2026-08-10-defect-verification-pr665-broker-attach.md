---
status: proposed
files:
  - docs/issue-653/reports/defect-verification.md
---

## Intent
Independently verify PR #665 (`implementation: broker-attach Closes
trailer at merge`, issue #653): confirm, by actual execution against a
hand-built harness (not the PR's own pytest fixtures), whether
contract-guard.sh's phase-2 merge check really auto-attaches a missing
`Closes #<issue>` trailer before allowing the merge, and really denies
only when that `gh pr edit` write itself fails.

## Constraints
- Two attempts only, per the phase-1 survey (docs/issue-653/reports/defect-verification/survey.md):
  green auto-attach path, red write-failure-still-denies path. Both
  self-devised, no qa/review record exists for this issue to cite from.
- Reproduction must run the actual `on-the-record/hooks/contract-guard.sh`
  script from PR #665's tip against an independently constructed fake
  `gh` + fixture repo — not a re-read of the PR's own
  test_contract_guard.py results, to avoid re-litigating the author's own
  verdict as if it were the attempt.
- No fix, no code change to contract-guard.sh or any other source file —
  this role reports outcomes and, if reproduced, files a finding
  addressed to coding; it does not patch.

## Rationale
Issue #653 asks specifically for verification that the broker-attach
behavior is real (attaches before merge) and that the deny fallback is
real (only fires on write failure), not merely asserted in the PR
description. The PR's own tests already exercise this via its own fixture
harness; an independent harness, built without reading that harness's
implementation details, is the check that catches a self-consistent but
wrong test double.

## What will be done
- Execute attempt 1 and attempt 2 from the survey against
  `on-the-record/hooks/contract-guard.sh` at PR #665's tip, using a
  hand-built fake `gh` shim and fixture repo constructed independently of
  `test_contract_guard.py`.
- Record each outcome (reproduced / not-reproduced / blocked) in
  docs/issue-653/reports/defect-verification.md, with evidence pointers
  (exact commands run, captured stdout/stderr/exit codes).
- If either attempt reproduces a defect (auto-attach doesn't actually
  attach, or write-failure doesn't actually deny), file a finding
  addressed to coding with severity per the deterministic band lookup.

## Out of scope
- Any other behavior of contract-guard.sh not touched by PR #665 (e.g.
  target-repo resolution, round-scoping) — already covered by existing
  tests cited in the survey, not re-derived here.
- Fixing anything found.

## How you'll know it worked
Both attempts have a recorded outcome with an evidence pointer (exact
command + captured output), and docs/issue-653/reports/defect-verification.md
states a verdict consistent with those outcomes.

## What did not work
(none yet — appended live if something breaks during the build)
