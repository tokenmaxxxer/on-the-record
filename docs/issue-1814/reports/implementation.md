---
code_under_review:
  - spawn.py
  - gates/flows.py
  - on-the-record/hooks/approval-gate.sh
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/contract-guard.sh
  - test/test_convention_equivalence.py
  - test/test_branch_role_field.py
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# issue-1814 phase-2: explicit branch-role carrier, dual-read + fallback

canonical: gh issue view 1814, docs/issue-1814/proposals/branch-role-carrier.md

## Summary of work

canonical: eab641c9 (`git show --stat eab641c9`)

Delivered the approved phase-1 proposal
(docs/issue-1814/proposals/branch-role-carrier.md) per its delivery
checklist:

1. `spawn.py`:
   - New `_write_role_sidecar(work, issue, role)` writes
     `.on-the-record/role.json` (`{"role": ..., "issue": ...}`) into the
     spawned workspace. Called at all 3 return points of
     `issue_workspace()` (src==work reuse, work-dir reuse, fresh clone).
   - `ensure_pushed()`'s PR-body template now appends a `role: <role>`
     trailer line when it opens a PR on the role's behalf.
2. `on-the-record/hooks/approval-gate.sh`,
   `on-the-record/hooks/pr-preflight.sh`,
   `on-the-record/hooks/contract-guard.sh`: each now reads
   `.on-the-record/role.json` at the resolved workspace root *before* its
   original `git rev-parse --abbrev-ref HEAD` + branch-regex parse; on
   any read/parse/shape failure (or, for contract-guard.sh, an
   issue-number mismatch against the merge's own subject issue) it falls
   through unchanged to that original regex. The original fallback lines
   are untouched, verbatim, in all three files.
3. `gates/flows.py`: new `_ROLE_TRAILER_RE` + `_role_from_pr(pr,
   branch_match)` reads a `role:` trailer line out of the PR body
   `gh pr list` already returns (flows.py:57); the `pr_by_branch` grouping
   loop calls it instead of using the branch match's role group directly,
   falling back to that group when the trailer is absent or the body
   isn't a string.
4. `test/test_convention_equivalence.py`: additions-only new test class
   `BranchRoleFieldDualReadEquivalenceTest` — see Acceptance verification
   #1 below.
5. New `test/test_branch_role_field.py` — test method count:
   derived: `grep -c "^    def test_" test/test_branch_role_field.py`
   ```
   17
   ```
   Covers carrier write shape (sidecar JSON shape + call-site count,
   PR-body trailer via a live `ensure_pushed()` call against a local
   bare-repo origin + fake `gh`); per-site live-fire dual-read for the 3
   shell hooks (real script via `subprocess`, real PreToolUse JSON via
   stdin, fake `gh` on PATH, a real git checkout) — each site's "sidecar
   present" case deliberately sets the branch to a role that diverges
   from the sidecar's role, so a passing case is proof the carrier was
   actually read, not merely tolerated; each site also has a dedicated
   carrier-absent fresh-workspace case pinned as byte-identical to
   pre-#1814 behavior; `gates/flows.py`'s trailer read/fallback/absence
   cases as direct unit tests plus one exercising the real
   `pr_by_branch`-shaped call site.

## Why

Requirements engineering (issue #1814 body) and risk-management consult
(docs/reports/consult-log.md 2026-08-21) named the 4 duplicated
branch-role regex copies as the highest-risk consumer of the #1792
migration's replacement-field plan; the phase-1 proposal's Rationale
picked the per-site carrier pairing (workspace sidecar for the 3 local
shell hooks, PR-body trailer for `gates/flows.py`, both written by
`spawn.py` at spawn time) because the 4 sites do not share one reachable
medium — see the proposal's Rationale for the full per-carrier rejection
reasoning (co-injected directive file, pure-trailer-for-all).

## Upstream basis

docs/issue-1814/proposals/branch-role-carrier.md (approved via issue
comment `APPROVE issue-1814/implementation`, single-account mode, per
role-handoff contract v3 s19); docs/issue-1814/reports/implementation/survey.md.

## Acceptance verification

1. Equivalence harness green, additions only.

   canonical: python3 -m pytest test/test_convention_equivalence.py -q
   ```
   .............................                                            [100%]
   29 passed in 0.85s
   ```

   canonical: git diff --stat -- test/test_convention_equivalence.py (against parent commit 4b76a7e3)
   ```
   $ git diff --stat -- test/test_convention_equivalence.py
    test/test_convention_equivalence.py | 48 +++++++++++++++++++++++++++++++++++++
    1 file changed, 48 insertions(+)
   $ git diff -- test/test_convention_equivalence.py | grep -c '^-[^-]'
   0
   ```
   Additions only: 48 insertions, 0 deletions, 0 removed-content lines.

2. All four sites dual-read + fallback, `test/test_branch_role_field.py`
   green including live-fire hook invocations for the 3 shell hooks.

   canonical: python3 -m pytest test/test_branch_role_field.py -q
   ```
   .................                                                        [100%]
   17 passed in 0.91s
   ```

   canonical: python3 -m pytest test/test_branch_role_field.py -v -k "DualRead"
   ```
   ApprovalGateDualReadTest::test_sidecar_present_drives_role_decode_over_decoy_branch PASSED
   ApprovalGateDualReadTest::test_no_sidecar_decoy_branch_falls_open_unchanged PASSED
   ApprovalGateDualReadTest::test_absent_carrier_fresh_workspace_matches_pre_1814_behavior PASSED
   PrPreflightDualReadTest::test_sidecar_present_resolves_role_over_decoy_branch PASSED
   PrPreflightDualReadTest::test_no_sidecar_decoy_branch_stays_phase1_and_denies_authored_closes PASSED
   PrPreflightDualReadTest::test_absent_carrier_fresh_workspace_matches_pre_1814_behavior PASSED
   ContractGuardDualReadTest::test_sidecar_present_resolves_role_over_decoy_branch PASSED
   ContractGuardDualReadTest::test_no_sidecar_decoy_branch_is_record_false_no_closes_attached PASSED
   ContractGuardDualReadTest::test_absent_carrier_fresh_workspace_matches_pre_1814_behavior PASSED
   ```
   These are the live-fire hook run outputs: real shipped `.sh` scripts,
   invoked via `subprocess.run(["bash", <hook>.sh], input=<real
   PreToolUse JSON>, ...)`, a fake `gh` on PATH, and a real git checkout
   per case. Each "sidecar present" case sets the branch to a role that
   diverges from the sidecar's own role, so passing is direct evidence
   the carrier drove the decode rather than being merely tolerated; each
   hook's "absent carrier, fresh workspace" case is the acceptance item's
   named empty state.

## Regression check

canonical: python3 -m pytest on-the-record/hooks/test_approval_gate.py on-the-record/hooks/test_pr_preflight.py on-the-record/hooks/test_contract_guard.py -q
```
$ python3 -m pytest on-the-record/hooks/test_approval_gate.py on-the-record/hooks/test_pr_preflight.py on-the-record/hooks/test_contract_guard.py -q
.............................................................            [100%]
61 passed in 1.44s

$ python3 -m pytest tests/test_flows.py -q
................                                                         [100%]
16 passed in 0.82s
```
The pre-#1814 hook test suites and `gates/flows.py`'s own suite ran
green, unmodified, against these 4 edits.

`tests/test_spawn.py` (broader spawn.py suite, `-k "workspace or
ensure_pushed or role"`) hangs under `timeout 45`.

derived: `git stash && timeout 45 python3 -m pytest tests/test_spawn.py -q -k "workspace or ensure_pushed or role"; echo EXIT:$?; git stash pop`
```
EXIT:143
```
Ran identically against unmodified `main`-parent (4b76a7e3, via
`git stash`) — pre-existing, not introduced by this change. Not one of
this issue's cited acceptance checks; noted here rather than silently
skipped.

## Test-tier directive note (issue #1518)

derived: `test -f .on-the-record/test-tiers.json; echo $?`
```
1
```
No test-tiers.json at this repo's root — ran the two acceptance-cited
targeted suites directly (0.85s / 0.91s combined, well under any
plausible budget) rather than a full-repo run; the `tests/test_spawn.py`
hang above is the one full-suite-adjacent data point available this
session.

## What did not work

None.

## Open findings

None outstanding — `test/test_convention_equivalence.py`'s
`test_hooks_read_role_json_sidecar_before_falling_back` covers a marker
check only (source contains `.on-the-record`/`role.json`), not full logic
equivalence; the logic itself is pinned by
`test/test_branch_role_field.py`'s live-fire cases.
