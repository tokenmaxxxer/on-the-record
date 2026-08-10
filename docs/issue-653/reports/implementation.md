---
code_under_review:
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/test_contract_guard.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done
Implemented the approved, revised #653 ADR (architecture branch PR #656,
`APPROVE issue-653/architecture` + `APPROVE issue-653/implementation`):
`on-the-record/hooks/contract-guard.sh`'s phase-2 merge check no longer
denies outright on a missing/wrong `Closes #<issue>` trailer. It now
builds the corrected PR body (appends the trailer if absent; would
correct a wrong digit in place if that branch were reachable) and calls
`gh pr edit <pr> --body <corrected> [-R <repo>]` before allowing the
merge. `deny(...)` fires only if that `gh pr edit` write itself fails —
demoted from primary mechanism to fallback, per the ADR.

`on-the-record/hooks/test_contract_guard.py` extends the fake `gh` shim
to handle `pr edit` (logs each call to a file the test asserts on; can be
made to fail via a per-repo `edit_fails` fixture flag). The four existing
tests that previously asserted deny-on-missing-trailer now assert
auto-attach-and-allow instead (they test what they always tested — target
repo resolution / round-scoping — through the new attach behavior). One
new test (`test_write_failure_still_denies_merge`) is the red case: the
one remaining deny path, when the `gh pr edit` write fails.

## Why
Root cause per the issue: nothing on the deployed surface attached the
`Closes #<n>` trailer; refusal (pr-preflight at create, contract-guard at
merge) only helps a session capable of correcting itself in response, and
5 same-day recurrences (one spawn-and-respawn producing 0 fixes) showed
that premise false in practice. The merge broker is the one place that
executes every merge regardless of what the spawning session wrote, so
attaching the trailer there — mechanizing the manual edit-body-then-merge
workaround — makes a decided merge deadlock-free by construction instead
of by session compliance.

## Upstream
docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md
(architecture branch `issue-653/architecture`, ADR, approved).

## Test evidence
Ran `python3 -m pytest on-the-record/hooks/test_contract_guard.py -v`,
including the new write-failure red case and the auto-attach green cases
across cwd/`cd`-prefix/round-scoping paths:

```
test_contract_guard.py::test_cross_repo_same_number_judges_target_not_cwd PASSED [  8%]
test_contract_guard.py::test_repo_flag_targets_repo_but_no_local_approvers_is_unreached PASSED [ 16%]
test_contract_guard.py::test_full_pr_url_targets_repo_but_no_local_approvers_is_unreached PASSED [ 25%]
test_contract_guard.py::test_cd_prefix_reads_target_approvers_and_attaches PASSED [ 33%]
test_contract_guard.py::test_cd_prefix_allows_when_target_pr_closes_issue PASSED [ 41%]
test_contract_guard.py::test_repo_flag_overrides_cd_prefix_when_they_disagree PASSED [ 50%]
test_contract_guard.py::test_no_repo_indicator_unchanged_cwd_behavior PASSED [ 58%]
test_contract_guard.py::test_write_failure_still_denies_merge PASSED     [ 66%]
test_contract_guard.py::test_prior_round_approval_allows_new_phase1_pr PASSED [ 75%]
test_contract_guard.py::test_same_round_approval_attaches_closes_when_missing PASSED [ 83%]
test_contract_guard.py::test_same_round_approval_with_closes_allows PASSED [ 91%]
test_contract_guard.py::test_cross_role_approval_still_gates_phase2 PASSED [100%]

============================== 12 passed in 0.97s ==============================
```

## What did not work
- Attempted a "wrong `Closes #<m>` gets corrected to the right number"
  test: the guard derives its working `issue` value directly from
  `closes_m.group(2)` when `closes_m` matches, so the `int(closes_m.
  group(2)) != issue` branch of the existing deny condition is
  unreachable through any input the hook actually sees (pre-existing
  behavior, not introduced by this change). Removed the test rather than
  assert an unreachable path; the correction code stays in
  `contract-guard.sh` as written (harmless, matches the ADR's stated
  shape) but is not exercised.

## Doc placement
- ADR/decision already lives at
  docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md
  (architecture role's phase-1 output) — no new decisions doc needed.
- No new env var, dependency, or migration introduced.

## Open findings
None.
