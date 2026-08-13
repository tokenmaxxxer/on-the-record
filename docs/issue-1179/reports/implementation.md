---
code_under_review:
  - spawn.py
  - gates/test_clean_reconcile_safety.py
  - docs/handbooks/setup.md
  - docs/issue-1179/decisions/shared-checkout-dedup.md
type: feature
breaking: false
verdict: unreviewed
loop_state: landed
---

# Implementation record — issue-1179

## What was done

Wired `roster_clean()`'s existing safe-delete logic (spawn.py:4894, unchanged behavior) into an
automatic, default-on, spawn-time sweep, per northpole req#7 and issue-1179's four requirements:

1. **Automatic lifecycle cleanup**: extracted the per-workspace safety check
   (`_workspace_clean_state()`) and the archive-or-delete step (`_delete_workspace()`) out of
   `roster_clean()` into shared functions. Added `auto_sweep(wb, max_age_days, max_bytes, now)`, which
   calls the same safety check, and wired one call into `_spawn_one()`'s `issue is not None` branch
   (right before `issue_workspace()` creates the new clone), wrapped in `try/except` so a sweep failure
   never blocks a spawn.
2. **Bound policy**: two-stage bound — reap safe workspaces older than `MUSTER_CLEAN_MAX_AGE_DAYS`
   (default 14) unconditionally, then if the remaining safe workspaces still total more than
   `MUSTER_CLEAN_MAX_BYTES` (default 5GiB), reap the oldest remaining ones until under bound.
   `MUSTER_CLEAN_AUTO` (default on) disables the automatic path without touching the manual `clean` CLI
   verb.
3. **Safety preserved**: the automatic path and `roster_clean()` call the identical
   `_workspace_clean_state()`/`_delete_workspace()` functions — a live session (roster pid alive) or a
   dirty tree (uncommitted changes or commits not on any remote) is never touched by either path; sibling
   session logs whose ledger outcome is outside `LANDED_OUTCOMES` are archived to `.archived-logs/`, not
   deleted, by both paths.
4. **Shared-checkout dedup decision**: recorded in `docs/issue-1179/decisions/shared-checkout-dedup.md`
   — accept `git clone --reference <mirror>` for `issue_workspace()`'s target-repo clone as the direction,
   reject `git worktree` (breaks the per-workspace remote isolation `issue_workspace()` exists for), defer
   the actual build to a follow-up issue (requirement 4 is phase-1-scoped per the issue text).

## Why

northpole req#7: a plugin-only, default-on consumer install must not require the operator to know about
or run a cleanup command. The operator hit real disk exhaustion (measured 11GB/317 dirs on this
machine) because `spawn.py clean` was manual-only. Reusing `roster_clean()`'s existing safety logic via
extraction — rather than writing a second, parallel safe-delete implementation for the automatic path —
means one future safety fix or test covers both the manual and automatic call sites, instead of the two
drifting apart (see the proposal's Rationale for the two rejected alternatives: a separate `auto-clean`
CLI verb, and an age-only bound with no size cap).

## Upstream / basis

docs/issue-1179/proposals/automatic-lifecycle-cleanup.md (commit 57b391f)

## Accumulation

See the proposal's `## Accumulation` section — `auto_sweep()`/`_delete_workspace()` are single shared
functions called once per spawn.

## What did not work

None.

## Open findings

None.

## Doc-placement ladder (completed)

- [x] Env vars (`MUSTER_CLEAN_AUTO`, `MUSTER_CLEAN_MAX_AGE_DAYS`, `MUSTER_CLEAN_MAX_BYTES`) documented
  in `docs/handbooks/setup.md` (Korean and English sections), same turn as the code that reads them.
- [x] Design decision (shared-checkout dedup, requirement 4) recorded in
  `docs/issue-1179/decisions/shared-checkout-dedup.md`.

## Test run

acceptance: python3 gates/test_clean_reconcile_safety.py — result:
```
$ python3 gates/test_clean_reconcile_safety.py
....[auto-sweep] 지움 1
...[auto-sweep] 지움 1
.....
----------------------------------------------------------------------
Ran 8 tests in 0.327s

OK
```
4 pre-existing #1124 regression tests (unchanged behavior after the `roster_clean()` extraction) plus 4
new `AutoSweepTest` cases (age bound, size bound oldest-first, live-session exemption, dirty-workspace
exemption).

## Live measurement (issue's second acceptance check)

acceptance: python3 -c "... spawn._workspace_clean_state() over every ~/.tokenmaxxxer/work entry ..." —
result:
```
safe-to-delete: 24 dirs, 0.75 GB
kept (live/dirty): 294 dirs
```

acceptance: du -sh ~/.tokenmaxxxer/work; python3 -c "... spawn.auto_sweep(...) at default bounds ..."; du -sh ~/.tokenmaxxxer/work — result:
```
before: 11G  /home/jwjung/.tokenmaxxxer/work
auto_sweep() result: {'removed': 0, 'failed': 0}
after:  11G  /home/jwjung/.tokenmaxxxer/work
```

acceptance: the two fenced results directly above — result: at default bounds, nothing was reclaimed on
this run because none of the safe-to-delete workspaces are older than 14 days and their combined size is
under the 5GiB bound, so neither bound fired yet. This is the actual outcome measured this turn, not the
issue text's assumed one.

Reading the two fenced results together, the residue split on this specific machine leans toward
workspaces #1124 keeps because they carry uncommitted or unpushed work, not workspaces that are safe to
delete. The bound policy this change adds only ever touches the safe subset — it must not reach the
protected subset, by #1124's own guarantee. Left as an open note for whoever looks at residue growth
next: most of this machine's accumulated directories fall into the protected, dirty/abandoned category,
which sits outside this issue's automatic-sweep scope.
