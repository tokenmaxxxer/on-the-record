---
code_under_review:
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/test_contract_guard.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #577 phase 2

## What was done

Implemented exactly `docs/issue-577/proposals/2026-08-10-round-role-scoped-phase2.md`:

- `on-the-record/hooks/contract-guard.sh`:
  - Widened the `gh pr view` call to also request `commits`, and derived
    `first_commit_at` as the earliest `committedDate` among the PR's own
    head branch commits (`None` when the list is empty — fail-open,
    unchanged from prior behavior).
  - Widened the `gh issue view` comments query's `-q` projection to
    `[.comments[] | {body, author, createdAt}]` so each comment carries
    `createdAt` alongside the fields already used.
  - Kept `prefix = "APPROVE issue-%d/" % issue` role-agnostic, matching
    the phase-approval helper's stance (issue #312) exactly as the
    proposal's Rationale requires.
  - Added `and (not first_commit_at or c.get("createdAt", "") > first_commit_at)`
    to the `phase2 = any(...)` predicate: an approval comment older than
    (or same-or-earlier than) this PR's own branch's first commit no
    longer counts toward phase-2; a missing `first_commit_at` leaves the
    predicate unchanged (fail-open per header note).
- `on-the-record/hooks/test_contract_guard.py`:
  - Extended `FAKE_GH`'s `pr view` branch to emit `commits` from the
    fixture.
  - `_approve_comment` gained optional `created_at` and `role` params,
    defaulted to preserve the 7 existing call sites' behavior unchanged.
  - Added the acceptance matrix as 4 new tests: prior-round-approval
    allows a new phase-1 PR; same-round approval denies a delivering PR
    without `Closes`; same-round approval with `Closes` allows; a
    cross-role approval (issue #312 shape) newer than the PR's first
    commit still gates phase-2 (role stays out of the scoping signal).

## Why

Per the proposal's Rationale: scoping phase-2 by time alone (approval
`createdAt` vs. the PR's own branch's first-commit `committedDate`) is the
mechanically simplest sound rule available in data the script already
fetches — no extra `gh` round trips, no divergence from the issue-312
role-agnostic phase model (cross-role handoff support).

## Upstream

Based on: `docs/issue-577/proposals/2026-08-10-round-role-scoped-phase2.md`

## Doc-placement ladder

- [x] No new env var, config key, dependency, or migration introduced —
  nothing to add to a handbook.
- [x] No public signature or wire format changed outside the two files in
  the frozen write set — no separate decision record needed; the
  proposal's own Rationale already carries the alternative-and-reason
  record for this change.
- [x] No benchmark/investigation numbers produced — no separate reports
  entry beyond this record.

## Verification run

```
$ cd on-the-record/hooks && python3 -m pytest test_contract_guard.py -v
============================= test session starts ==============================
collected 11 items

test_contract_guard.py::test_cross_repo_same_number_judges_target_not_cwd PASSED [  9%]
test_contract_guard.py::test_repo_flag_targets_repo_but_no_local_approvers_is_unreached PASSED [ 18%]
test_contract_guard.py::test_full_pr_url_targets_repo_but_no_local_approvers_is_unreached PASSED [ 27%]
test_contract_guard.py::test_cd_prefix_reads_target_approvers_and_denies PASSED [ 36%]
test_contract_guard.py::test_cd_prefix_allows_when_target_pr_closes_issue PASSED [ 45%]
test_contract_guard.py::test_repo_flag_overrides_cd_prefix_when_they_disagree PASSED [ 54%]
test_contract_guard.py::test_no_repo_indicator_unchanged_cwd_behavior PASSED [ 63%]
test_contract_guard.py::test_prior_round_approval_allows_new_phase1_pr PASSED [ 72%]
test_contract_guard.py::test_same_round_approval_denies_without_closes PASSED [ 81%]
test_contract_guard.py::test_same_round_approval_with_closes_allows PASSED [ 90%]
test_contract_guard.py::test_cross_role_approval_still_gates_phase2 PASSED [100%]

============================== 11 passed in 0.80s ==============================
```

The 7 pre-existing target-repo-resolution tests pass unchanged in
behavior; the 4 new tests cover the issue's acceptance matrix plus the
#312 cross-role regression the warrant hunt surfaced during phase 1.

## What did not work

None.

## Open findings

None.

## Rationale for deviations

None — this build tracked the approved proposal's `## What will be done`
exactly.
