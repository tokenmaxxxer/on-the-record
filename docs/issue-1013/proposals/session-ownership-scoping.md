---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
---

Subject: issue-1013

## Intent

An operator running two or more on-the-record orchestrator sessions on one
machine should see, be gated by, and get auto-respawned only for the role
sessions their own orchestrator spawned — not another concurrent session's.
The current-state survey
(`docs/issue-1013/reports/product-discovery/2026-08-12-survey.md`) found
four of the issue's five symptoms trace to the same root cause: `spawn.py`'s
roster/watchdog/gate/auto-respawn code paths iterate the machine-global
roster with no filter on the `session_id` field already stored per entry
(spawn.py:5427, 5516). The fifth symptom (interleaved `poll-watchdog.log`)
lives outside `spawn.py` and is out of this proposal's write set.

## Constraints (carried from the issue and role directives)

- Preserve the observation-loss invariant (issue's own wording): scoping
  must never make a session's work permanently unwatched — an orphaned
  entry (owner session dead/unresolvable) must still surface, under
  default scope, not only under `--all`.
- Empty-state parity (issue's own acceptance): a single-session machine
  (no `ORCHESTRATOR_SESSION_ID_ENV` ever set, so every entry's
  `session_id` is `None`) behaves exactly as today — `None == None` is a
  legitimate self-match, not "ownerless, hide it."
- Reuse the existing `--all` flag (spawn.py:4497-4499, already defined for
  `watch --all`) for the explicit cross-session view, rather than
  inventing a second flag with the same meaning.
- `_watcher_looks_real()`'s issue+role cmdline identity check (#559) is
  additive, not replaced — session ownership is a reporting-scope filter
  layered on top, watcher staleness itself stays keyed on issue+role.
- A PR carries no `session_id` of its own (GitHub object); ownership for
  the undisposed-PR gate has to be approximated via the roster entry that
  produced the PR's branch, not read directly off the PR.

## What will be done (design, for phase-2 to build)

**A. Shared "own entries" filter.** One new helper,
`_roster_own(d: dict, all_scope: bool) -> dict`, used by every roster-
scanning path below. Computes the caller's own id as
`os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None` and returns:
- if `all_scope`: `d` unchanged (today's behavior, the explicit `--all`
  escape hatch the issue asks for).
- else: entries where `e.get("session_id") == own_id` (covers the
  empty-state `None == None` case), unioned with orphaned entries (see D)
  — orphans always surface regardless of scope, per the observation-loss
  invariant.

**B. `roster_watchdog()` scoping (symptom 1).** `roster_watchdog(auto_respawn=False,
all_scope=False)` filters `d = _roster_load()` through `_roster_own()`
before the `for key, e in sorted(d.items())` loop (spawn.py:2494-2497)
runs. The board-wide sweep (`_board_wide_sweep`, spawn.py:2492) is
issue/PR-scoped already, not roster-scoped, and stays unchanged — it does
not name a session either way, so it is not part of this leak.

**C. Undisposed-PR gate scoping (symptom 2).** `_undispositioned_role_prs()`
gains a second exclusion alongside `exclude_issue`: build a
`branch -> session_id` map from the current live+recently-dead roster
(same helper as B, `_roster_own()` with `all_scope=False`), and skip any
open PR whose `headRefName` matches a roster entry owned by the calling
session. A PR from an issue this session never spawned still blocks, per
today's behavior — the fix narrows the exclusion, it does not remove the
gate. `--despite-returned` (spawn.py:4494) remains the manual override for
either case, unchanged.

**D. Auto-respawn + orphan surfacing (symptom 3).** Inside
`roster_watchdog()`'s dead-entry branch (spawn.py:2513), after `_roster_own()`
filtering, an entry is **orphaned** when its `session_id` is non-`None`,
not equal to the caller's own id, AND its owning session is itself
unresolvable (best-effort: no live process for that session — approximated
the same way `_alive()`/`_watcher_looks_real()` already approximate
liveness elsewhere in this file, since an orchestrator session has no pid
recorded today; the phase-2 build task is to decide the concrete
resolvability check, e.g. via a lightweight session-heartbeat file written
alongside the roster entry). Orphaned entries print under a distinct
`[orphaned]` label (never silently dropped) but are **never** auto-
respawned by a session that did not own them — `auto_respawn` only fires
`_auto_respawn_check()` on entries the caller owns. This directly answers
symptom 3: a dead entry belonging to another session's already-merged PR
is reported, not respawned, by this session.

**E. Watcher identity join (symptom 4).** `roster_ps()`'s watcher-status
line gains a session comparison: when `ws_entry`'s owning roster entry's
`session_id` is non-`None` and differs from the caller's own id, the
printed line reads `워처: pid N (다른 세션 소유)` instead of implying local
ownership — additive to the existing DEAD/UNWATCHED states, not a
replacement for `_watcher_looks_real()`'s liveness check.

**F. CLI surface.** `spawn.py watchdog --all` and `spawn.py watchdog
--auto-respawn --all` reuse the existing `--all` argparse flag
(spawn.py:4497), threading `all_scope=True` into `roster_watchdog()`.
Without `--all`, both subcommands default to own-scope per A-E.

## Out of scope

- Building A-F's code (phase-2, pending approval).
- Symptom 5 (interleaved `poll-watchdog.log`) — no such file/constant
  exists inside `spawn.py` (survey's derived grep, no hits); it is written
  by a calling harness/cron layer outside this file's write set.
- A durable session-liveness registry beyond the roster's existing
  `session_id` field — phase-2 picks the concrete orphan-resolvability
  check (D) within the existing data shapes, not a new persistent store.

## How this will be known to work

- `tests/test_spawn.py` gains a two-session-scoping case (issue's own
  acceptance): two roster entries with distinct `session_id`s; default
  `roster_watchdog()`/gate/auto-respawn calls touch only the entry
  matching the caller's own `ORCHESTRATOR_SESSION_ID_ENV`; `--all`
  surfaces both; an entry whose owning session is unresolvable surfaces as
  `[orphaned]` under default scope instead of being silently dropped.
- A single-session-machine case (no `ORCHESTRATOR_SESSION_ID_ENV` set,
  all entries `session_id: None`) asserts identical output to today's
  unscoped behavior — the empty-state parity constraint.
- A hunt dispatch on this proposal checks specifically for the
  observation-loss failure mode: an orphan that scoping makes silently
  disappear from every default-scope report.

## Prioritization

Only one candidate solution shape was developed (the shared `_roster_own()`
filter applied at four call sites A-D plus the CLI surface F) — the survey's
opportunity-solution tree section considered narrower alternatives (e.g.
scoping only the watchdog poll-report, leaving the PR gate and
auto-respawn unscoped) but rejected them because three of the four
symptoms in the issue's own operator report trace to the same
missing-filter root cause, and a partial fix would leave the most
disruptive symptom (auto-respawn duplicating merged work, symptom 3)
unaddressed. RICE/ICE comparison across solution variants is not
applicable here — there is exactly one proposed design, not multiple
opportunity/solution candidates being weighed against each other.

## Accumulation

This is a scoping-filter addition (A) applied at four existing call sites
(B-E) plus one CLI thread-through (F), not a new subsystem — no new
persistent state format, no new file, no new roster schema field (the
`session_id` field this composes with already exists, spawn.py:5427/5516).
The accumulation cost is one shared ~10-15 line helper function reused
four times, versus four independent ad-hoc filters; phase-2 should build
`_roster_own()` once and thread it through B-E rather than reimplementing
the `session_id`-equality-with-`None`-match logic at each call site.

## What did not work

None.
