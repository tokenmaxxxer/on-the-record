---
code_under_review:
  - gates/ci.py
  - gates/test_closes_gate_ci.py
  - tests/test_gates.py
  - tests/test_test_tier_contract.py
  - pytest.ini
  - .on-the-record/test-tiers.json
  - gates/test_boundary.py
  - gates/test_generated_paths.py
  - gates/test_role_utilization_report.py
  - gates/test_clean_reconcile_safety.py
  - gates/test_consult_json_parse.py
  - gates/test_consult_verdict_parsing.py
  - gates/test_product_capture_vs_deliverable_guard.py
  - on-the-record/hooks/test_monitor_notice.py
  - tests/test_spawn.py
  - tests/test_check_run_artifact.py
kind: execution-observation
loop_state: handed-off
---

This record observes whether issue #1619's fix restores the full pytest suite to a binary (green-or-explicitly-dispositioned) signal, by checking out the landed commit on branch issue-1619/implementation into an isolated worktree and live-firing the fast test tier against it — not by re-executing the implementation role's own task.

## Independence statement

This session did not author or edit gates/ci.py, any test_*.py file, pytest.ini, or .on-the-record/test-tiers.json. No edit was made to the implementation role's own record path or any other role's record this session; the only file this session wrote is this record. The test run was executed against a separate git worktree (/tmp/otr-obs-1619) checked out from the implementation commit, not against this session's own branch.

## Scope statement

Subject: issue #1619 ("20 pre-existing test failures on main — full pytest suite red independent of recent PRs"), observing the implementation role's landed commit on branch issue-1619/implementation.

canonical: `gh pr view 1648 --json number,state,headRefName,baseRefName` (read this session)
```
{"baseRefName":"main","headRefName":"issue-1619/implementation","state":"OPEN"}
```
PR #1648 is open with the fix commit landed on its own branch, not yet on main.

canonical: `git log --oneline -1 origin/issue-1619/implementation` (read this session)
```
e6a5bf04 fix(issue-1619): disposition all 20+ pre-existing suite failures, add test-tier contract
```

What was read to arrive at this scope, in order: `gh issue view 1619` (full issue body and all four comments, read first); `gh pr view 1648` (body, file list, state); then the implementation role's own record on the checked-out commit; then a live pytest run against that worktree.

## Verdict

### outcome

canonical: `python3 -m pytest -q -m "not slow"` (run this session, in worktree /tmp/otr-obs-1619 at commit e6a5bf04)
```
2065 passed, 19 xfailed, 2 xpassed in 24.02s
```
canonical: `python3 -m pytest -q -m "not slow"` (same run cited immediately above, this session)
PR #1648's body claims "2065 passed, 20 xfailed, 1 xpassed" — this session's own run above differs by one xfail-vs-xpass, so the run was repeated with -rX to identify the extra xpass.

canonical: `python3 -m pytest -q -m "not slow" -rX` (run this session, in worktree /tmp/otr-obs-1619)
```
XPASS tests/test_gates.py::t_rulebook_version_is_recorded - issue #1619: environment-specific -- fails whenever the on-the-record plugin's own working tree (this checkout) has uncommitted changes at the moment spawn.rulebook_version() runs, since it stamps '+커밋안됨' into the version string. Passes on a clean checkout. Not a suite bug -- an active dev session is inherently dirty.
XPASS tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_find_violations_result_unchanged_with_prebuilt_issue_states_zero_violations - issue #1619: same concurrent-board-sweep-lock flakiness as test_find_violations_result_unchanged_with_prebuilt_issue_states above.
2065 passed, 19 xfailed, 2 xpassed in 20.90s
```
The two XPASS reason strings quoted above name the same "environment-specific" and "concurrent-board-sweep-lock" categories the PR body's own text already discloses (three env-dependent xfails, three concurrency-lock xfails). This session's worktree is a fresh clean checkout with no concurrent lock, exactly the condition each reason string says flips xfail to xpass — disclosed environment-dependent behavior reproducing correctly, not an undisclosed discrepancy.

canonical: `grep -rln 'xfail' gates/test_boundary.py gates/test_generated_paths.py gates/test_role_utilization_report.py gates/test_clean_reconcile_safety.py gates/test_product_capture_vs_deliverable_guard.py gates/test_consult_json_parse.py gates/test_consult_verdict_parsing.py on-the-record/hooks/test_monitor_notice.py tests/test_check_run_artifact.py tests/test_gates.py tests/test_spawn.py` (run this session, in worktree /tmp/otr-obs-1619)
```
gates/test_boundary.py
gates/test_generated_paths.py
gates/test_role_utilization_report.py
gates/test_clean_reconcile_safety.py
gates/test_product_capture_vs_deliverable_guard.py
gates/test_consult_json_parse.py
gates/test_consult_verdict_parsing.py
on-the-record/hooks/test_monitor_notice.py
tests/test_check_run_artifact.py
tests/test_gates.py
tests/test_spawn.py
```
canonical: spot-reads of the matched marker lines (this session: gates/test_consult_verdict_parsing.py:58, gates/test_role_utilization_report.py:64, gates/test_generated_paths.py:121, gates/test_boundary.py:77, tests/test_check_run_artifact.py:128, gates/test_consult_json_parse.py:46,248, on-the-record/hooks/test_monitor_notice.py:48,80, tests/test_gates.py:97,919,962,989,1713,1730, gates/test_clean_reconcile_safety.py:83, tests/test_spawn.py:4454,4513,5451,5580,9706,11064)
Each of these 20 xfail sites carries an in-file `xfail(reason=...)` string. Acceptance check 2 (every irreducibly-failing test individually marked xfail with an in-file reason) is bar-met on this evidence.

canonical: `python3 -m pytest -q gates/test_closes_gate_ci.py tests/test_gates.py tests/test_test_tier_contract.py` (run this session, in worktree /tmp/otr-obs-1619)
```
166 passed, 5 xfailed, 1 xpassed in 13.87s
```
Zero failures in gates/test_closes_gate_ci.py, which the issue's second comment cites as 13-failing byte-identical-to-main before this fix — this run above independently verifies the PR body's "real fix, not xfail" claim for the pr_reference._pr_view -> gh_rest.fetch_pr_body regression, and the same run collecting tests/test_test_tier_contract.py alongside it verifies its collection-collision fix.

canonical: `.on-the-record/test-tiers.json` contents (read this session, in worktree /tmp/otr-obs-1619)
```
fast: python3 -m pytest -q -m "not slow"  (budget_seconds: 300)
slow: python3 -m pytest -q -m slow
```
The fast command is byte-identical to the command run above, whose wall-clock (24.02s, 20.90s on repeat, both cited above) is under the stated 300s budget, addressing the tiering gap the issue's first comment cross-references to #1518.

canonical: the four pytest/grep runs cited above in this section (this session's own runs)
Verdict on the step's own specific ask ("does the landed fix restore a binary suite signal"): each of the acceptance checks re-run above is bar-met.

### trajectory

canonical: `find docs/issue-1619 -type f` (run this session, in worktree /tmp/otr-obs-1619)
```
docs/issue-1619/reports/implementation.md
```
Only the implementation role's own record exists; no scout-brief or judgment record path — consistent with the issue's `validity-consult-skip: trivial` tag and "infrastructure/no-direct-requirement" label read from `gh issue view 1619` above, so no product/design consult was expected for a test-suite hygiene fix and the absence of scout-brief/judgment paths is not a trajectory defect.

## Findings

canonical: the acceptance runs cited in "outcome" above (this session's own runs)
No findings. The landed commit's own claims were independently reproduced against a clean worktree, and the one numeric difference (19 vs. 20 xfailed) resolved to the PR's own disclosed environment-dependent disposition category, not to an undisclosed gap.

## Recomputed overall result

canonical: `python3 -m pytest -q -m "not slow"` (this session's own run, cited in full in "outcome" above; see also the -rX and gates/test_closes_gate_ci.py runs cited alongside it)
Per the spec's worst-case-among-cited-results rule: every cited acceptance entry above resolved bar-met; none resolved failed, cantTell, inapplicable, or untested. Overall result: PASS.

canonical: `gh pr view 1648 --json state,mergedAt` (read this session)
```
{"mergedAt":null,"state":"OPEN"}
```
PR #1648 had not merged to main as of this observation; this record observes the branch commit's own execution correctness only, and does not assert the PR has landed on main.
