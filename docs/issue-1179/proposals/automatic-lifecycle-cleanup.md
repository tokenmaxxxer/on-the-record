---
status: approved
files:
  - spawn.py
  - gates/test_clean_reconcile_safety.py
  - docs/handbooks/setup.md
  - docs/issue-1179/decisions/shared-checkout-dedup.md
  - docs/issue-1179/proposals/automatic-lifecycle-cleanup.md
  - docs/issue-1179/reports/implementation.md
---

# Automatic lifecycle cleanup for workspace residue — #1179

## Request

Workspace clones under `~/.tokenmaxxxer/work` accumulate unboundedly because `spawn.py clean` is
manual-only; a consumer install must not require the operator to know about or run a cleanup command
(northpole req#7). Wire the existing safe-delete logic into an automatic, default-on, spawn-time sweep,
add a size/age bound so it does not merely delay the same unbounded growth, keep issue #1124's safety
guarantees intact, and record an accept/reject decision on shared-checkout dedup.

## Constraints

- #1124's guarantees must not regress: never delete a workspace with uncommitted changes or commits not
  on `origin`; archive (not delete) sibling session logs whose ledger outcome is outside
  `LANDED_OUTCOMES`; `reconcile` keeps working over a workspace already removed by clean.
- Default-on, no user action required — a plugin-only install must self-bound its disk footprint.
- The bound must be stated and configurable (env vars, following the existing `MUSTER_*` convention).
- No behavior change to the existing manual `spawn.py clean` CLI verb — the automatic path adds a call
  site, it does not replace the manual one.
- Dedup (requirement 4) is a phase-1 decision only; it is out of scope for the code in this change (see
  `docs/issue-1179/decisions/shared-checkout-dedup.md`).

## Rationale

**Reuse `roster_clean()`'s safety checks via a shared helper, rather than writing a second, parallel
safe-delete implementation for the automatic path.** Two independent implementations of "is this
workspace safe to delete" is exactly the shape that drifts apart over time and silently reopens #1124's
guarantees in one path while a test only covers the other. Extracting the per-workspace safety check
and the actual delete-and-archive routine out of `roster_clean()` into shared functions, then having
both the manual `clean` CLI verb and the new automatic sweep call the same functions, means a future
safety fix (or test) covers both paths by construction.

**Rejected alternative: a separate `spawn.py auto-clean` CLI verb the orchestrator calls once per
tick, instead of wiring into `_spawn_one()`.** This was considered because it would be simpler to test
in isolation. Rejected because it reintroduces the exact problem requirement 1 exists to close: a verb
nobody automatically calls is manual-only cleanup with an extra flag, not automatic cleanup. The issue
explicitly asks for a spawn-time/session-start trigger; `_spawn_one()` (spawn.py:5765) is the one
chokepoint both `main()` and `drive()` already funnel every spawn through, so wiring there reaches every
spawn path without a second call site to keep in sync.

**Rejected alternative: age-only bound (no size cap).** An age-only policy ("keep 14 days") lets disk
usage still grow unbounded if spawn volume increases — the operator's actual failure mode was disk
exhaustion, a size problem, not a staleness problem. The bound combines both: sweep first by age (older
than N days, safe workspaces reaped unconditionally), then, if total safe-workspace size still exceeds
M GB after the age pass, reap the oldest remaining safe workspaces until under the size bound. Age alone
does not cap disk; size alone would reap workspaces only minutes old under high spawn volume, losing
debugging value for no disk-pressure reason — the combination bounds both axes for the reason each axis
exists.

## What will be done

- `spawn.py`: extract `roster_clean()`'s per-workspace safety check into `_workspace_clean_state(w,
  live)` (returns "live" / a not-safe reason / `None` for safe-to-delete) and its delete-plus-archive
  step into `_delete_workspace(w, wb, log_outcomes, archive_dir)`. `roster_clean()` calls both
  unchanged in behavior. Add `_workspace_base()` to replace the two existing duplicated
  `MUSTER_WORK_DIR` resolutions (and the new call site's would-be third).
- Add `auto_sweep(wb, max_age_days, max_bytes)` in `spawn.py`: lists safe-to-delete workspaces
  (`_workspace_clean_state()` returns `None`) with `mtime`, deletes those older than `max_age_days` via
  `_delete_workspace()`, then if the remaining safe workspaces' total size still exceeds `max_bytes`,
  deletes the oldest remaining ones (by `mtime`) until under bound. Wrapped in `try/except Exception`
  at the call site so a sweep failure never blocks a spawn.
- Wire one call to `auto_sweep()` into `_spawn_one()`'s `issue is not None` branch, immediately before
  `issue_workspace()` creates the new workspace (spawn.py:5803-5804), gated on `MUSTER_CLEAN_AUTO`
  (default on; `"0"`/`"false"`/`"no"`/`"off"` disables, matching the existing `MUSTER_KEEP_SSH`
  boolean-parsing convention at spawn.py:5351).
- New env vars, default-on: `MUSTER_CLEAN_AUTO` (default on), `MUSTER_CLEAN_MAX_AGE_DAYS` (default 14),
  `MUSTER_CLEAN_MAX_BYTES` (default 5 GiB). All read once per sweep call, no persisted config file.
- Tests in `gates/test_clean_reconcile_safety.py`: age-bound reaping, size-bound reaping (oldest-first),
  live-session exemption, dirty/unpushed exemption, and a re-run of the file's existing #1124 assertions
  to confirm `roster_clean()`'s observable behavior is unchanged after the extraction.
- `docs/handbooks/setup.md`: document the three new env vars in the same bilingual section style as the
  existing `MUSTER_STATE_ROOT` entry.
- `docs/issue-1179/decisions/shared-checkout-dedup.md`: requirement 4's accept/reject record (already
  written; see that file).

## Accumulation

This change adds one more spawn-time step (`auto_sweep()`) alongside the existing per-spawn subprocess
calls in `_spawn_one()`/`issue_workspace()` (git status/log/remote checks). It does not add a new
per-call-site inline `subprocess`/`gh` pattern — `auto_sweep()` and `_delete_workspace()` are single
shared functions called once per spawn, not duplicated per role or per workspace kind, so additional
roles or additional spawns do not add additional copies of this logic. If a future issue needs a second
automatic trigger point (e.g. a periodic watchdog-driven sweep in addition to spawn-time), that trigger
should call the same `auto_sweep()` function rather than re-implementing the bound logic inline — the
extraction in this change is what makes that reuse possible instead of requiring a third copy.

## Out of scope

- The `--reference` mirror-clone build for requirement 4 (recorded as a decision, deferred to a
  follow-up issue).
- Any change to `spawn.py clean`'s CLI surface or output format.
- A persisted/file-based config for the bounds — env vars only, matching every other `MUSTER_*` knob in
  this codebase.
- Sweeping anything outside the workspace directory tree (e.g. the rulebook/core shared caches) — those
  are out of #1179's stated scope (workspace residue, not rulebook cache residue).

## How you'll know it worked

- `python3 gates/test_clean_reconcile_safety.py` passes, including the new auto-sweep tests, hermetically
  under the file's existing module-override pattern.
- A terminal-outcome workspace with no uncommitted/unpushed work is reaped by `auto_sweep()`; a live
  session's and a dirty workspace are left untouched — covered by the new tests, matching the issue's
  stated acceptance check.
- `spawn.py clean`'s existing behavior and output are unchanged (same tests, extraction only).
- A before/after `du` measurement on this machine, reported in the phase-2 record, showing the automatic
  sweep reclaims the terminal majority of the measured 11GB (the issue's second acceptance check).
