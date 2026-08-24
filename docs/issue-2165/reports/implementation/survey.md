---
issue: 2165
role: implementation
---

# issue-2165 — current-state survey

## Scope

issue #2165 reports that `execution-observation`/`conformance-review`
observer roles for a subject called `issue-513`, in an external target
repo this session has no log/runtime access to (a "live finding" relayed
from a separate consumer session), were respawned by the
spawn-on-pr/watchdog machinery roughly every 2-3 minutes for ~6 hours
(50+ times), the large majority after the subject's own `implementation`
PR had already merged. Task: find the gap in the merged-subject skip
check and close it, with a regression test reproducing the shape.

## The coverage-check code path

`missing_verification()` is the function the watchdog calls every tick
(via `spawn_missing_for_pr()`) to find `(subject, role)` pairs to spawn.
canonical: gates/spawn_on_pr.py:151-209

The watchdog invokes it once per tick under the `"spawn-on-pr"` category.
canonical: watchdog.py:897-900

For each subject with a missing observer role, it resolves the
subject's own `<subject>/implementation` branch PR number.
canonical: gates/spawn_on_pr.py:180-181

If no PR number is found, the subject is skipped.
canonical: gates/spawn_on_pr.py:182-183

It then requires the subject's issue to still be `OPEN` — fail-*closed*
on `gh` failure (an unknown-state subject is treated as not-open).
canonical: gates/spawn_on_pr.py:64-72,184-186

It then resolves that branch's PR state and, if `"MERGED"`, prints the
skip line, writes a `spawn_on_pr_skip_merged` ledger event, and skips
the subject.
canonical: gates/spawn_on_pr.py:187-195

`_pr_number_for_branch`/`_pr_state_for_branch` prefer a tick-shared bulk
PR index (one `gh api .../pulls` sweep) when available.
canonical: gates/spawn_on_pr.py:75-88

The bulk index is only shared for a tick when both `spawn-on-pr` and
`closure-sweep` are due that same tick; otherwise each falls back to its
own per-branch resolution.
canonical: watchdog.py:889-895

When no bulk index is available, `_pr_state_for_branch` falls back to
two separate `gh` calls: one for the number, one for MERGED.
canonical: gates/spawn_on_pr.py:90-112

If the second call errors while the first succeeded, the function fails
open to `"OPEN"` per its own docstring.
canonical: gates/spawn_on_pr.py:96-102

Stated intent (same docstring): never *guess* merged — the tradeoff is
that a real merge can go briefly undetected on any one `gh` error.
canonical: gates/spawn_on_pr.py:108-112

## What already guards against naive repeat-spawn (issue #1476)

`spawn_missing_for_pr()` also carries a park/backoff mechanism: once a
`(subject, role)` pair is spawned, its `pr_number` and `blocked` state
persist to `runs/spawn_on_pr_parked.json`.
canonical: gates/spawn_on_pr.py:45-54,300-407

`blocked` comes from an `APPROVE issue-<n>/<role>` allowlisted-comment
check.
canonical: gates/spawn_on_pr.py:256-260

On a later tick, if `pr_number` is unchanged and the pair is still
blocked, the pair parks instead of respawning.
canonical: gates/spawn_on_pr.py:263-274

A regression test already covers a multi-tick replay of this shape for
a *non-merged* subject: tick 1 spawns, ticks 2-5 (same PR, still
blocked) all assert `spawned == []`.
canonical: tests/test_spawn_on_pr_park.py:75-94

I reproduced this park behavior directly against a *merged* subject
with one flaky `gh` call: 10 ticks through `spawn_missing_for_pr()`,
`_pr_open_or_merged_for_branch` returning a stable PR number,
`_merged_pr_for_branch` flaking (`None`) on every other call.
canonical: throwaway repro run this session, `/tmp/repro_2165.py` (not
part of the repo tree), full output below.

```
[spawn-on-pr] issue-513: subject PR 이 이미 merged — 옵저버 스폰 건너뜀 (missing=['execution-observation', 'conformance-review'])
tick 1: pairs=[] spawned_so_far=0
tick 2: pairs=[('issue-513', 'execution-observation'), ('issue-513', 'conformance-review')] spawned_so_far=2
tick 3: pairs=[] spawned_so_far=2
tick 4: pairs=[] spawned_so_far=2
tick 5: pairs=[] spawned_so_far=2
tick 6: pairs=[] spawned_so_far=2
tick 7: pairs=[] spawned_so_far=2
tick 8: pairs=[] spawned_so_far=2
tick 9: pairs=[] spawned_so_far=2
tick 10: pairs=[] spawned_so_far=2
TOTAL SPAWNED: 2
```

Total spawns stayed at 2 (one per role) across all 10 ticks.
canonical: repro output above.

The first successful spawn immediately parks the pair, and the park key
(`pr_number`) never changes across ticks.
canonical: gates/spawn_on_pr.py:397-406

So a single intermittently failing `gh` call does not by itself
reproduce an unbounded respawn — the park mechanism already bounds it.
canonical: repro output above; gates/spawn_on_pr.py:340-369

## The actual gap: merge-confirmation is re-derived live every tick, never remembered

The park mechanism only engages after a pair has already been spawned
once; until then there is no park record for the pair.
canonical: gates/spawn_on_pr.py:340-369 (lookup keyed on
`park_state.get(key)`), 397-406 (only place a record is created)

`missing_verification()`'s merge-skip branch reads and writes no
cross-tick state at all.
canonical: gates/spawn_on_pr.py:187-195

So every tick's `pr_state == "MERGED"` check is re-derived from
scratch, from whatever `gh` (or the bulk index) returns that tick.
canonical: gates/spawn_on_pr.py:168-186 (fresh `pr_index`/`issue_states`
fetch or param each call, no memoization)

This session cannot access the external target repo's logs to confirm
#513's exact per-tick `gh`-flakiness recurrence rate — a genuine
evidence gap this survey does not close.

What the repro and the code both establish instead is the design gap:
merge is a terminal fact once true, but the code re-derives it live,
successfully, every tick, forever — no persisted memory of a prior
positive confirmation.
canonical: gates/spawn_on_pr.py:151-209 (full function body, no
persistence of a positive `pr_state == "MERGED"` result anywhere)

## Existing precedent for a "confirmed-once, remembered-forever" cache

`closure_sweep.py` already uses exactly this shape for a related
problem: a subject classified once as out-of-scope is never
reclassified on a later tick, via a small repo-local, gitignored JSON
set file alongside `runs/spawn_on_pr_parked.json`.
canonical: gates/closure_sweep.py:297-316,366-377

## Proposed fix

Detailed in the accompanying proposal: a sibling sticky-cache file,
`runs/spawn_on_pr_merged_seen.json`, following the same shape as
`closure_sweep.py`'s out-of-index-seen cache.
canonical: gates/closure_sweep.py:297-316 (pattern being mirrored)

It would record subjects once confirmed `pr_state == "MERGED"`, checked
before any further `gh`-dependent work, skipped unconditionally
thereafter.
canonical: gates/spawn_on_pr.py:187-195 (the one call site this would
wrap)

## Alternatives considered (Rationale in the proposal names the rejected one and why)

- Collapse the two-call fallback into one `gh` call. Reduces the chance
  of a miss but, per the repro above, a single flaky call is already
  bounded by the existing park mechanism — this alone would not
  demonstrably close the reported 50+-cycle gap.
- Make the park mechanism itself the merge source of truth. Rejected in
  the proposal — see its Rationale.
