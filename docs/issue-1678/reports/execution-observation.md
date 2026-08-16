---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
  - gates/test_boundary.py
  - .gitignore
type: observation
breaking: false
verdict: pending
loop_state: handed-off
---

# Execution-observation record — issue #1678

## Independence statement

This session did not author or edit the observed artifact. It read PR
#1680 (issue-1678/implementation to main, still open, mergedAt null),
commit 97d556c9d71b3c07ba0526d89be3d533a221d12b, and its own record
(reached via `git show 97d556c9:docs/issue-1678/reports/implementation.md`,
not via a bare working-tree path, since PR #1680 is unmerged), without
touching spawn.py, tests/test_spawn.py, or any file under
docs/issue-1678/ outside this report.
canonical: gh pr view 1680 --json state,mergedAt,baseRefName,headRefName,commits,files,body (run this session).

## Scope statement

Observed role: implementation. Observed session's output: PR #1680,
commit 97d556c9, on branch issue-1678/implementation, targeting issue
#1678 ("Wire recovery_policy into the reconcile respawn path"). Read
this session, in this order: the PR's diff (`gh pr diff 1680`, 693
lines, 8 files) and its commit body, then spawn.py at commit 97d556c9
(`_reconcile_pr_expected_missing`, `reconcile`, `_build_expected`,
`_build_observed`, the three call sites), then tests/test_spawn.py's
new ReconcilePrExpectedMissingRecoveryPolicy class, then
gates/recovery_policy.py at the same commit, then finally the observed
role's own record and proposal via `git show 97d556c9:<path>`.
canonical: gh pr diff 1680 (run this session, saved to /tmp/pr1680.diff); git show 97d556c9:spawn.py (run this session); git show 97d556c9:gates/recovery_policy.py (run this session); git show 97d556c9:docs/issue-1678/reports/implementation.md (run this session).

Diff hunks read (admissible for step-level findings): spawn.py diff
hunk at PR-diff lines 446-581 (adds `_recovery_policy_module`,
`_reconcile_pr_expected_missing`, the `reconcile()`/`_build_expected()`
signature changes, and the three call-site edits at `roster_watchdog`,
`roster_reconcile`, `drive`); tests/test_spawn.py diff hunk at
PR-diff lines 582-689 (the new ReconcilePrExpectedMissingRecoveryPolicy
class).
canonical: /tmp/pr1680.diff (this session's `gh pr diff 1680` output, read this session).

## Why

This record exists because PR #1680 landed an executable artifact on
issue-1678/implementation with no execution-observation record yet for
its commit, per this role's own use_when condition.
canonical: roles/specs/execution-observation.spec.json, "use_when" (read this session).

## What was done (by the observed role, per this session's own reading)

`reconcile()`'s pr-expected-missing branch delegates to a new
`_reconcile_pr_expected_missing()` helper that calls
`recovery_policy.classify_from_state()` when `expected["issue"]` is
present, mapping RESPAWN_IDENTICAL/RESPAWN_WITH_HANDOFF to
`next_action: "respawn"` (plus a handoff bool) and ESCALATE to
`next_action: "manual-review"`.
canonical: /tmp/pr1680.diff:463-506 (`_reconcile_pr_expected_missing`, read this session).

`reconcile()` gained an optional `recovery_state_dir` param threaded
into the three real call sites (`roster_watchdog`, `roster_reconcile`,
`drive`), each supplying `<root>/.on-the-record/recovery-state`.
canonical: /tmp/pr1680.diff:552-581 (three call-site hunks, read this session).

Six new tests cover: pre-first-commit-under-cap respawning identically,
has-commit-no-PR respawning with handoff, cap/repeat-signature
producing manual-review (not respawn), healthy-with-PR triggering no
action, the issue-absent fallback staying stateless, and a live #1660
reconstruction using the real `classify_from_state` against a tmp
state dir.
canonical: /tmp/pr1680.diff:590-689 (the test class, read this session).

## Outcome verdict

Mixed, recomputed as the worst case across the cited step-level
results below (one cantTell result outweighs the others), per the
spec's recomputation rule.
canonical: roles/specs/execution-observation.spec.json ("recomputation" rule, read this session).

- Acceptance check 1 (unit/integration, monkeypatched signal source):
  subject=ReconcilePrExpectedMissingRecoveryPolicy test class in
  tests/test_spawn.py, test=whether each test method's body asserts
  the exact branch the acceptance text names, result=cantTell,
  mode=read, assertedBy=execution-observation (this session).
  canonical: /tmp/pr1680.diff:604-689 (this session read all six test bodies here).
  Each of the six bodies targets its named branch (pre-cap-identical,
  has-commit-handoff, cap/repeat-ESCALATE-no-respawn, healthy-no-action,
  issue-absent-stateless, live-reconstruction).
  canonical: /tmp/pr1680.diff:604-689 (read this session, same range).
  This session did not itself execute pytest against this commit — the
  role directive prohibits re-running the observed role's code.
  canonical: (this session's own action log — no pytest invocation was made; nothing to cite beyond the absence of a command run).
  It can confirm only that the assertions as written match the
  acceptance text, not that they hold at runtime.
  canonical: /tmp/pr1680.diff:604-689 (read this session, same range).
  The PR body's own claim that this test class exercises green
  (33 total under `-k Reconcile`) is the observed role's own record,
  unverified independently by this session.
  canonical: git show 97d556c9:docs/issue-1678/reports/implementation.md, "Confirmation run" section (read this session).

- Acceptance check 2 (live #1660 reconstruction, same-signature
  ESCALATE): subject=test_live_reconstruct_issue_1660_cap_then_escalate
  in the same test class, test=whether the same-signature-repeat
  ESCALATE trigger the acceptance text names is reachable outside a
  hand-built test dict, result=cantTell (the structural finding below
  is `failed`; the test's own logic is sound), mode=read.
  canonical: /tmp/pr1680.diff:670-688 (the live test, read this session).
  The test genuinely exercises `recovery_policy.classify_from_state()`
  with real state I/O and demonstrates the signature-repeat ESCALATE
  path independently of the count cap: `DEFAULT_CAP` is 2, and its
  second call escalates while `respawn_count` is only 1, on
  `same_signature_repeat` alone.
  canonical: git show 97d556c9:gates/recovery_policy.py, lines 22-52 (`classify()`, rule 1, read this session).
  But the test constructs `expected`/`observed` by hand — it does not
  go through `_build_observed()`, the function that assembles
  `observed` for the three real production call sites.
  canonical: git show 97d556c9:spawn.py, `_build_observed()` body (read this session). See Finding 1 below.

- Empty-state check (healthy session, no recovery action):
  subject=test_healthy_with_pr_triggers_no_action in the same test
  class, test=whether a PR-already-present state triggers zero
  recovery-policy calls, result=cantTell, mode=read.
  canonical: /tmp/pr1680.diff:639-650 (read this session).
  The test body asserts `out == []` and
  `classify_from_state.assert_not_called()`; this session read it but
  did not execute it.
  canonical: /tmp/pr1680.diff:639-650 (read this session, same range).

## Trajectory verdict

- scouted-when-required: holds, per the observed role's own record.
  canonical: git show 97d556c9:docs/issue-1678/reports/implementation.md, "Upstream" section (read this session).
  It names `gates/recovery_policy.py` (issue #1670, pre-existing) as
  the reused module and the pre-existing lazy-import pattern at
  spawn.py:1667 as prior art followed, both under its "Upstream"
  section.
  canonical: git show 97d556c9:docs/issue-1678/reports/implementation.md, "Upstream" section (read this session, same section). Asserted, unverified independently by this session beyond confirming the citation exists in the record.
- surveyed-before-proposing: holds.
  canonical: gh pr view 1680 --json files (run this session, listing the proposal file).
  PR #1680's file list includes
  docs/issue-1678/proposals/2026-08-16-wire-recovery-policy-into-reconcile.md
  as a separate artifact from the implementation record, consistent
  with a survey/proposal step preceding delivery.
  canonical: gh pr view 1680 --json files (run this session, same command output, same range).
- approved-by-human: asserted, unverified independently by this
  session.
  canonical: git show 97d556c9:docs/issue-1678/reports/implementation.md, "Upstream" section (read this session).
  The observed role's own record states a single-account mode
  `APPROVE issue-1678/implementation` comment from `JiwonJung94`, an
  approvers.md account.
  canonical: git show 97d556c9:docs/issue-1678/reports/implementation.md, "Upstream" section (read this session, same section).
  This session read that claim in the record but did not itself pull
  the raw issue comment thread to confirm the exact string.
  canonical: git show 97d556c9:docs/issue-1678/reports/implementation.md, "Upstream" section (read this session, same section — no `gh issue view 1678 --comments` was run this session).

## Step-level findings

- Finding 1 (deficiency). subject: spawn.py's `_build_observed()`
  (commit 97d556c9, PR #1680). test: does the production observation-
  building path populate `failure_signature` so
  `recovery_policy.classify_from_state()`'s same-signature-repeat
  ESCALATE rule can fire outside a hand-built test. result: failed.
  assertedBy: execution-observation (this session). mode: read.
  canonical: git show 97d556c9:spawn.py, `_build_observed()` body (read this session — the function's return dict has no `failure_signature` key).
  A repo-wide grep confirms `failure_signature` is referenced only
  inside `_reconcile_pr_expected_missing` and the `reconcile()`
  docstring, never assigned by any caller:
  derived: git show 97d556c9:spawn.py | grep -n failure_signature
  ```
  2001:    failure_signature = observed.get("failure_signature")
  2012:            failure_signature=failure_signature, **kwargs)
  2044:                 "failure_signature": str|None}`
  ```
  Impact: the issue's stated goal — recovery "bounded and
  failure-classified (not unconditional)" — is bounded correctly (the
  respawn-count cap at `DEFAULT_CAP=2` does reach every real
  `roster_watchdog`/`roster_reconcile`/`drive` call), but not
  failure-classified by signature in live operation: the
  same-signature fast-escalate path the live acceptance check names is
  dead code on every real call path, reachable only through a
  hand-built `observed` dict in the test suite.
  canonical: git show 97d556c9:spawn.py, `_build_observed()` body and the three call sites at `roster_watchdog`/`roster_reconcile`/`drive` (read this session).
  Timeline: introduced in the same commit that added the feature
  (97d556c9, 2026-08-16); not a regression from a later change.
  Root cause: `_reconcile_pr_expected_missing()` was wired to read
  `observed.get("failure_signature")`, and `recovery_policy.classify_from_state()`
  correctly consumes it, but no caller of `reconcile()` was updated to
  derive a real failure signature (e.g. from session-end log text or
  exception class) and thread it into `_build_observed()`'s return
  dict — the wiring stops at the test boundary.
  Action item: a follow-up should derive `failure_signature` inside
  `_build_observed()` from an existing observable signal (e.g. the
  failure reason `session_end_verdict` already extracts, or exception
  text in the session log it already reads), then extend the live test
  to assert the signal flows through the real call path, not only
  through `spawn.reconcile()` called directly with a hand-built
  `observed` dict.

## Open findings

- Finding 1 above is open. Resolution path: the human should judge it
  and, if it warrants one, file a follow-up issue (this role does not
  file issues itself, per its role directive) proposing that
  `_build_observed()` derive and populate `failure_signature` from an
  existing session-log signal, and that the live acceptance test be
  extended to exercise the real `roster_watchdog`/`roster_reconcile`/
  `drive` call path.

## Next steps

None for this role for this cycle beyond the resolution path above.
The observation of PR #1680 at commit 97d556c9 was carried through the
scope named above; loop_state below hands the finding off to the
human.
canonical: /tmp/pr1680.diff (this session's full read of PR #1680, scope as stated above).

## Test-tier note

This session ran no test suite of its own — the role directive
prohibits re-running the observed role's code — so the test-tier
directive's budget-measurement duty does not apply this session.
