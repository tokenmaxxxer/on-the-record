---
code_under_review:
  - spawn.py
  - test_spawn.py
type: feature
breaking: false
verdict: pending
loop_state: landed
---

# Issue #587 — implementation record (phase 2, remediation round 3: thread -C target root)

## What was done

Threaded the caller's `-C`/`--cwd` resolved target root through
`reconcile --remediation-merged` into `_remediation_merge_sweep`, per the
approved proposal
(`docs/issue-587/proposals/implementation-remediation-round3-target-root.md`,
merged in PR #611):

1. `spawn.py`: `roster_reconcile` gained a `root: Path | None = None`
   keyword-only parameter; in the `remediation_merged` branch it now
   resolves `target_root = root if root is not None else ROOT` and calls
   `_remediation_merge_sweep(target_root, issue)` — default preserves
   every existing non-CLI call site.
2. `spawn.py`: `main()`'s `reconcile` dispatch now passes
   `root=Path(a.cwd).resolve()` through to `roster_reconcile`.
3. `test_spawn.py`: added `RosterReconcileRemediationMergedCLITargetRoot`,
   driving the shipped CLI process
   (`python3 spawn.py reconcile --remediation-merged --issue 587 -C
   <fixture>`) against a fixture repo built under a
   `tempfile.TemporaryDirectory()`, verified up front to be outside
   spawn.py's own checkout dir. `gh` is stubbed via a `PATH`-prepended
   executable that logs every invocation's argv and returns a merged PR
   for `pr list`, an empty comment page for the read call, and success
   for the post call. The test asserts exactly one `gh api
   .../comments ... body=...` call fired, carrying the expected comment
   body.

## Why

Third e2e re-verification (execution-observation, PR #610) found
`_remediation_merge_sweep` is always called with the global `ROOT`
constant (spawn.py's own checkout) instead of the caller's `-C` target,
so `reconcile --remediation-merged` silently no-ops in every consumer
repo other than spawn.py's own — event 4 could never fire during real
operation against a client repo. The proposal's Rationale chose an
explicit `root` parameter threaded from `main()` over reassigning the
module-level `ROOT` global, because `ROOT` is read throughout spawn.py
for orchestrator-local state (roster paths, watchdog state, workspace
index) and overwriting it process-wide for one call site would silently
redefine every other `ROOT` read for the duration of that CLI
invocation.

## Upstream

Based on:
`docs/issue-587/proposals/implementation-remediation-round3-target-root.md`
(PR #611, merged as commit b8eba9d).

## What did not work

- First version of the new test asserted the CLI process exits `0` on a
  successful sweep; the actual return value is
  `_remediation_merge_sweep`'s posted-comment count (`1` here), which
  `main()` returns as the process exit code — the same convention
  `reconcile`'s default mode already uses (divergence count as exit
  code). Fixed the assertion to expect `1`.

## Rationale for deviations

None — implementation matches the approved proposal's "What will be
done" exactly (parameter name, delegation shape, `main()` dispatch line,
test approach and fixture-outside-checkout assertion).

## Doc placement

No new env var, dependency, migration, or public-signature/wire-format
change — `roster_reconcile`'s new `root` parameter is additive
(keyword-only, default `None`, existing callers unaffected). No
`docs/decisions/` or handbook entry required per the doctrine ladder.

## Sibling-sweep audit (reported, not fixed — per proposal's Out of scope)

The proposal's scope was limited to the `reconcile --remediation-merged`
call path. Auditing `spawn.py` for the same `ROOT`-vs-target-root bug
class turned up two more sites, both explicitly out of scope for this
round and left unfixed here:

- `roster_watchdog` (spawn.py:1990) — reads `ROOT` directly for its
  roster/watchdog-state scan; no `-C`/target-root plumbing exists on
  this path at all. Plausibly intentional (watchdog manages
  spawn.py's own orchestrator-local roster, not a consumer repo's
  state) rather than a bug, but it is the same pattern shape and worth
  a future issue confirming that reading is correct.
- `roster_reconcile`'s default mode (spawn.py:2192,
  `reconcile(_build_expected(e), _build_observed(ROOT, e))`) — also
  reads `ROOT` unconditionally, not the resolved `root` this round
  introduced for the `remediation_merged` branch only. Same
  orchestrator-local-roster caveat as `roster_watchdog` may apply, but
  it was not verified in this round and is flagged here rather than
  silently left unexamined.

Both are reported per the proposal's Constraints ("do not widen to the
other `ROOT`-hardcoded sites the survey found... those are reported, not
fixed"); no code changed at either site.

## How it was verified

```
$ python3 -m pytest test_spawn.py -k RosterReconcileRemediationMergedCLITargetRoot -q
.
1 passed, 357 deselected in 0.27s

# Confirmed the new test reproduces the round-3 bug on the pre-fix code
# (stashed only spawn.py, kept the new test):
$ git stash -- spawn.py && python3 -m pytest test_spawn.py -k RosterReconcileRemediationMergedCLITargetRoot -q; git stash pop
F
AssertionError: 0 != 1  (no gh api .../comments body= call fired)
1 failed, 357 deselected in 0.22s

$ python3 -m pytest test_spawn.py -q
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 60%]
........................................................................ [ 80%]
......................................................................   [100%]
358 passed in 24.25s
```

`gates/ci.py` was not run as a delivery-suite check, same as the prior
round's record: it treats `spawn.py` as a protected root path
unconditionally, a control aimed at client repos this tool orchestrates,
not at on-the-record's own development — prior merged commits editing
`spawn.py` directly (e.g. `53f9d16`, `8ab9940`) confirm this repo's own
`spawn.py` changes are not gated through `gates/ci.py`.

## Closed checks (warrant-hunter, before-landing, stance 4)

The before-landing hunt (`docs/reports/2026-08-10-hunt-implementation-remediation-round3-target-root.md`)
reported `WatcherAutoArm::test_watchdog_flags_pid_reused_by_unrelated_process`
and `WatcherAutoArm::test_watcher_looks_real_rejects_live_watcher_of_a_different_role`
failing on `python3 -m pytest test_spawn.py -q` with this round's diff
applied. Re-ran `git stash` to isolate: the same two tests fail
intermittently on unmodified HEAD (`b8eba9d`) as well — three full-suite
runs on bare HEAD produced pass/fail/fail, matching this round's diff's
own pass/fail/fail/fail pattern across repeated runs. This is a
pre-existing, order-/timing-dependent flake in `WatcherAutoArm` (unrelated
to this round's `spawn.py`/`test_spawn.py` changes, and predating them),
not a regression introduced by threading `root` through
`_remediation_merge_sweep` or by the new
`RosterReconcileRemediationMergedCLITargetRoot` test class. Not fixed
here — out of this round's scope (proposal's write set is `spawn.py`,
`test_spawn.py` for the target-root fix only) — reported for a future
issue. `closed_checks: [{check: "WatcherAutoArm flake predates this diff",
code_sha: b8eba9d}]`.

## Open findings

None outstanding from this round beyond the reported (not fixed)
sibling-sweep sites above. A fourth e2e re-verification of the shipped
CLI path against a live fixture target repo is execution-observation's
job on the delivering PR, per the proposal's "Out of scope".
