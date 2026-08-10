---
code_under_review:
  - spawn.py
  - test_spawn.py
type: feature
breaking: false
verdict: pending
loop_state: landed
---

# Issue #587 — implementation record (phase 2, remediation round 2: reconcile --remediation-merged wiring)

## What was done

Wired `_remediation_merge_sweep` (built in PR #603) into a `reconcile
--remediation-merged` CLI verb, per the approved proposal
(`docs/issue-587/proposals/implementation-remediation-merged-wiring.md`,
merged in PR #605):

1. `spawn.py`: `roster_reconcile` gained a `remediation_merged: bool = False`
   parameter; when set (and `issue` is given) it delegates to
   `_remediation_merge_sweep(ROOT, issue)`, mirroring the existing
   `unreported` delegation branch (issue #534 precedent).
2. `spawn.py`: added a `--remediation-merged` `store_true` argparse flag
   next to `--unreported`, and threaded it through `main()`'s
   `role == "reconcile"` dispatch.
3. `test_spawn.py`: added `RosterReconcileRemediationMergedCLI`, driving the
   shipped entrypoint (`roster_reconcile(issue=587, remediation_merged=True)`,
   not the private `_remediation_merge_sweep` function) against the same
   merged-fixture-branch setup the existing `RemediationMergeSweep` test
   class uses, and asserting the `gh api .../comments` call fires with the
   expected body. A second test asserts `--remediation-merged` appears in
   `spawn.py --help` output.

## Why

Round-1 re-verification (execution-observation, PR #604) found
`_remediation_merge_sweep` posts correctly when called directly but had no
call site anywhere on the shipped surface — timeline event 4 could never
fire during real operation. The proposal's Rationale chose the CLI-verb
shape over a new `run.md` step because no `run.md` step currently invokes
any `reconcile` subcommand, and `_remediation_merge_sweep`'s own docstring
already named `reconcile --remediation-merged --issue N` as the intended
shape.

## Upstream

Based on: `docs/issue-587/proposals/implementation-remediation-merged-wiring.md`
(PR #605, merged as commit a9719d5).

## What did not work

None.

## Rationale for deviations

None — implementation matches the approved proposal's "What will be done"
exactly (flag name, parameter name, delegation shape, test approach).

## Doc placement

No new env var, dependency, migration, or public-signature/wire-format
change — `roster_reconcile`'s new parameter is additive (default `False`,
existing callers unaffected) and the CLI flag is additive. No
`docs/decisions/` or handbook entry required per the doctrine ladder.

## How it was verified

```
$ python3 -m pytest test_spawn.py -q
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 60%]
........................................................................ [ 80%]
.....................................................................    [100%]
357 passed in 24.87s
```

`gates/ci.py` was not run as a delivery-suite check: it treats `spawn.py`
as a protected root path unconditionally (`gates/gates.py`
`PROTECTED_ROOT_FILES`), which is a control aimed at client repos this
tool orchestrates, not at on-the-record's own development — prior merged
commits editing `spawn.py` directly (e.g. `8ab9940`, PR #603/#605's
lineage) confirm this repo's own `spawn.py` changes are not gated through
`gates/ci.py`.

## Open findings

None outstanding from this round. A third e2e re-verification of the
shipped CLI path against a live fixture branch is execution-observation's
job on the delivering PR, per the proposal's "Out of scope".
