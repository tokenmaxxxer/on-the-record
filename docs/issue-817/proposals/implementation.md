---
status: proposed
files:
  - harness/driver.py
  - harness/test_driver.py
  - docs/issue-817/reports/implementation.md
---

# Proposal — issue #817 step 2, implementation

## Request

Fix the harness-fidelity gap the merged step-1 diagnosis (PR#820)
pinned: `harness/driver.py`'s `instantiate_fixture_target` only
`shutil.copytree`s the fixture, so the instantiated copy has no `.git`
ancestry, unlike any real installed target. This makes
`deliverable-guard.sh`'s git-root-absence branch fire and silently
allow the un-delegated write — not because the guard is wrong, but
because the harness fixture doesn't look like a real target. Make the
fixture a real git repo and add a regression test.

## Constraints

- Do not change `deliverable-guard.sh` — the step-1 record confirms it
  is correct for real targets (denies with rc=2 and its redirect
  message whenever `.git` is reachable).
- The fix must make `instantiate_fixture_target`'s output faithfully
  mirror a real installed target's git ancestry (a real repo with a
  reachable root), not fake or special-case the guard's check.

## Rationale

Considered patching `deliverable-guard.sh` to also deny when no git
root is found (treat root-absence as "deny" instead of "allow"). Rejected:
the step-1 record shows this branch exists deliberately for sessions
genuinely working outside any git tree (rc=0 there is correct
behavior for that population), and the #776 harness's job is to
measure a *representative* target session, not to special-case the
guard around a fixture defect. Fixing the fixture to be faithful is the
one change that fixes the measurement without changing guard behavior
for real targets or non-git sessions.

## What will be done

- Add `git init` + an initial commit (`git add -A && git commit`) to
  `instantiate_fixture_target` in `harness/driver.py`, after the
  `shutil.copytree` call, so the returned `dest_dir` is a real git
  repo with a reachable root.
- Add `harness/test_driver.py` with a test that calls
  `instantiate_fixture_target` into a temp dir and asserts `git
  rev-parse --show-toplevel` run inside it succeeds and resolves to
  that dir (i.e., the fixture has a reachable git root).
- Write `docs/issue-817/reports/implementation.md`, this role's
  phase-2 record, citing PR#820 as the upstream basis and the new test
  run as evidence.

## Accumulation

This adds one `git init` + one commit subprocess sequence to
`instantiate_fixture_target`, the harness's single fixture-instantiation
entry point — not an inline call repeated across N call sites. If N
more harness fixtures need the same faithfulness fix in the future,
they go through this same function (there is only one), so there is no
per-call-site accumulation to bound.

## Out of scope

- Any change to `on-the-record/hooks/deliverable-guard.sh`.
- Re-running the #776 harness end-to-end (step 3 execution-observation,
  separate role/issue per the #817 execution plan).
- Cause A (#810), already resolved separately.

## How you'll know it worked

`harness/test_driver.py`'s new test passes, proving the instantiated
fixture has a reachable `.git` root; manually running
`deliverable-guard.sh` against a direct write inside a freshly
instantiated fixture now exits non-zero with the deny/redirect message
instead of silently exiting 0.
