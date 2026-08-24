---
issue: 2165
role: implementation
---

# issue-2165 — proposal: sticky merged-confirmation cache for spawn-on-pr

files:
- gates/spawn_on_pr.py
- tests/test_spawn_on_pr.py

## Request

Close the gap that let a subject (issue #2165's #513 shape) keep
respawning `execution-observation`/`conformance-review` observer roles
on repeated watchdog ticks after its own `implementation` PR had already
merged, and add a regression test reproducing that shape.

## Constraints

- Must not weaken `_pr_state_for_branch()`'s existing fail-open-to-`OPEN`
  behavior for subjects never yet confirmed merged — that conservatism
  (documented at gates/spawn_on_pr.py:96-102, survey) is intentional for
  the "don't guess merged" case and out of this issue's scope.
- Must not touch `_pr_open_or_merged_for_branch`/`_merged_pr_for_branch`
  in board.py — both are used well beyond spawn_on_pr.py (lifecycle.py,
  watchdog.py, spawn.py, multiple test files per the survey's grep), so
  changing their signatures/semantics is out of scope for a targeted fix.
- Must not regress the issue #1476 park/backoff mechanism
  (tests/test_spawn_on_pr_park.py) — the new cache is additive, checked
  before park logic runs, never replacing it.
- No durable test-fixture file beyond the regression test itself
  (verify-at-landing default, contract v3).

## Rationale

**Chosen approach: a sticky "confirmed-merged" cache, mirroring the
existing `closure_sweep.py` out-of-index-seen pattern** (issue #1643,
survey canonical: gates/closure_sweep.py:297-316). Once
`missing_verification()` has observed `pr_state == "MERGED"` for a
subject on any tick, that fact is written to a small repo-local,
gitignored JSON set file (`runs/spawn_on_pr_merged_seen.json`, sibling
to the existing `runs/spawn_on_pr_parked.json`) and checked before any
further `gh`-dependent work for that subject on later ticks — merged is
terminal, so a later tick's uncertain/flaky re-check can never un-skip
it again.

**Rejected alternative 1: collapse `_pr_state_for_branch()`'s two-call
fallback (`_pr_open_or_merged_for_branch` + `_merged_pr_for_branch`)
into a single `gh` call.** This would shrink the specific
partial-failure window (first call succeeds, second errors) that the
survey identified as a real, confirmed defect. Rejected as the *primary*
fix because the survey's own fault-injection repro showed a single flaky
call is already bounded to one extra spawn per role by the existing
park mechanism (issue #1476) — it does not, by itself, explain or
provably close a 50+-cycle repeat. A one-call fallback would still
re-derive "merged" live on every tick with no persisted memory, so any
*sustained* flakiness in the target environment (which this session
cannot rule out — the evidence gap noted in the survey) could still
reproduce the reported shape, just needing a higher failure rate. It
also touches the same two-call code path four other test files rely on
via `board.py`'s general-purpose helpers (per Constraints), raising the
regression surface for a change that doesn't independently prove the
fix.

**Rejected alternative 2: treat an existing park record's `blocked:
True` as sufficient to skip a subject, independent of `pr_number`
drift.** This would broaden park's role from "don't respawn an
unapproved pair with no new commits" into "don't respawn a pair at all
once blocked" — but `blocked` for an observer role is a static fact
(these roles never receive literal APPROVE comments; survey: they are
single-shot auto-spawned, not part of the two-phase checkpoint/approval
flow), so this would functionally disable re-spawn entirely after any
first attempt, including legitimate re-tries after a genuinely new
implementation commit lands (the `pr_number`-change re-arm trigger issue
#1476 explicitly built in). It also does nothing for the actual
observed gap: a subject that is never spawned even once (because it's
merged) never creates a park record in the first place, so this
alternative doesn't touch the pre-first-spawn window that's actually
broken.

## What will be done

1. In `gates/spawn_on_pr.py`, add `MERGED_SEEN_STATE_REL = Path("runs")
   / "spawn_on_pr_merged_seen.json"` next to `PARK_STATE_REL`, plus
   `load_merged_seen(root)` / `_save_merged_seen(root, seen)` helpers
   mirroring `closure_sweep._load_out_of_index_seen` /
   `_save_out_of_index_seen` (JSON list-of-strings on disk, empty set on
   missing/corrupt file — fail-safe, never fail-closed on a read error).
2. In `missing_verification()`, after the existing `missing =
   applicable_roles(subject_board)` / `if not missing: continue` check
   and before any `gh`-dependent lookup, load the merged-seen set (once
   per call, lazily, only if at least one subject needs it) and `continue`
   immediately for any subject already in it.
3. In the existing `if pr_state == "MERGED":` branch, add the subject to
   the in-memory set and persist it via `_save_merged_seen()`, alongside
   the existing `ledger_write`/print calls (unchanged).
4. Add `tests/test_spawn_on_pr.py` regression coverage reproducing
   #513's shape: (a) a low-level test driving `missing_verification()`
   across a confirmed-merge tick followed by several ticks where the
   fallback merged-check flakes, asserting the subject stays excluded
   throughout; (b) an end-to-end test driving the same sequence through
   `spawn_missing_for_pr()` (the actual watchdog entrypoint) and
   asserting zero spawns across all ticks after the first confirmation.

## Out of scope

- Determining or fixing the actual root cause of `gh` flakiness in the
  external target repo #513 ran in (no access to that environment from
  this session, per the survey's stated evidence gap).
- Collapsing the two-call fallback into one `gh` call (rejected
  alternative 1) — may be worth a follow-up issue if the sticky cache
  alone doesn't fully resolve future recurrences, but is not required to
  satisfy this issue's acceptance criterion.
- Any change to `board.py`'s `_pr_open_or_merged_for_branch`/
  `_merged_pr_for_branch`, `closure_sweep.py`, or the watchdog's tick
  scheduling.
- Backfilling `runs/spawn_on_pr_merged_seen.json` for subjects already
  merged before this change lands — the next tick that observes them
  live will populate it normally, same as any other cold-start state
  file in this module (`runs/spawn_on_pr_parked.json` has the same
  cold-start behavior today).

## How you'll know it worked

- `python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q`
  passes, including the two new regression tests, without modifying any
  existing test's assertions.
- The new end-to-end test demonstrates the issue's acceptance criterion
  directly: a subject whose PR is confirmed merged on tick 1 produces
  zero `spawn_missing_for_pr()` pairs (and zero `_spawn_one` calls) on
  every subsequent simulated tick, even when the merged-check `gh` call
  is mocked to fail on those later ticks.
