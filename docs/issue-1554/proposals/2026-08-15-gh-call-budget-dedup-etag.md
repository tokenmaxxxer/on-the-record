---
status: proposed
files:
  - gates/closure_sweep.py
  - spawn.py
  - tests/test_board_sweep_budget_carryover.py
  - tests/test_board_sweep_cross_workspace_lock.py
  - tests/test_board_sweep_etag.py
---

## Request

#1554: board-wide sweeps (closure-sweep/spawn-coverage/spawn-on-pr) make an
unbounded number of gh calls per tick, and one watchdog instance per
role-session workspace each runs its own board-wide sweep against the same
repo — together these exhaust the 5000/hr gh quota under concurrent sessions.
Operator direction added two more requirements: prefer signals derivable from
local state with zero gh calls, and use ETag/If-None-Match conditional
requests for the board-list calls so an unchanged board costs ~0 quota.

## Constraints

- Watch-coverage is inviolable: a sweep category deferred by budget must be
  re-queued and reached within `ceil(board/B)` ticks, never dropped.
  (issue body, "Binding constraint")
- Per-session health watchers stay per-session — only the board-wide sweeper
  gets cross-workspace dedup.
- Local-only signals (`accumulation_trend`, `requirement_drift`) must never
  be gated by budget/backoff — issue #1498's existing contract for them.

## Rationale

Considered making the cross-workspace lock live under each workspace's own
`STATE_ROOT`/runs/ directory (extending the existing `watchdog_lock_acquire`
lock path). Rejected: that path is rooted at `Path(__file__).resolve().parent`
— the *checkout* the running spawn.py was loaded from — which is exactly why
the gap exists (survey.md): every workspace has its own checkout, so a lock
under each one's own `runs/` can never see another workspace's lock file, no
matter how the acquire function itself is changed. The lock has to live at a
location that is the same physical path regardless of which checkout is
running it. `_repo_identity(root)` (spawn.py:4094) already derives a pure-local,
gh-free key for the *target repo being swept* (not the checkout); keying the
lock file's location off that identity, under a fixed directory outside any
single workspace, is the minimal change that actually closes the gap.

Considered adding conditional requests only to `issue_state_index_all`
(the highest-volume board-list call). Chose to add the same conditional
wrapper to `_pr_index_all` as well, since `find_violations` bills both calls
every tick and the acceptance check ("a tick over an unchanged board consumes
0 REST quota") requires both to 304 together, not just one.

## What will be done

- gates/closure_sweep.py:
  - A per-tick call-budget queue: `board_sweep_categories()` names the
    orderable list `["spawn-on-pr", "closure-sweep", "spawn-coverage"]`
    (matching `_board_wide_sweep`'s existing sequence). A new
    `runs/board_sweep_queue.json` state file holds a persisted cursor of
    categories still owed from a budget-exhausted tick. `next_categories(root,
    budget)` pops up to `budget` categories off the front of the pending
    queue (refilling from the full category list when empty — i.e. a new
    sweep round begins) and persists the remainder for the next tick. This is
    the carry-over: nothing is dropped, only deferred.
  - `issue_state_index_all` and a parallel `_pr_index_all` gain
    ETag/If-None-Match conditional re-fetch, mirroring `spawn._issue_comments`'s
    existing cache shape (`.git/gh-read-cache/...json`): first call bills and
    caches the ETag + body; a cached-and-unchanged call sends
    `If-None-Match` and, on 304, returns the cached body without incrementing
    the billed-call count.
- spawn.py:
  - `_board_wide_sweep` is rewired to ask `closure_sweep.next_categories(root,
    call_budget)` for this tick's categories instead of always running all
    three; categories not selected this tick are skipped (already re-queued
    by `next_categories`) and produce a `[watchdog] board-sweep: <category>
    이월 (예산)` line so the deferral is visible, not silent.
  - A new `_cross_workspace_board_sweep_lock_acquire(repo_root)` builds its
    lock path from `_workspace_base().parent / "locks" / f"board-sweep-
    {_repo_identity(repo_root)}.lock"` — fixed relative to `MUSTER_WORK_DIR`
    (or its default), independent of which checkout is executing, so all
    workspaces sweeping the same repo identity contend for the same file. It
    reuses the existing pid+start_time liveness check
    (`_alive`/`_proc_start_time`) so a crashed holder's lock is reclaimed.
    `_board_wide_sweep_all` acquires this lock per target repo before calling
    `_board_wide_sweep`; on failure to acquire, it prints one
    `[watchdog] board-sweep: <repo> 건너뜀 (다른 워크스페이스가 스윕 중)`
    line and skips that repo this tick (next tick retries — coverage isn't
    lost, it's rate-limited to one sweeper).
- Three new hermetic tests (fake `gh`/subprocess stubs, no network):
  test_board_sweep_budget_carryover.py asserts a 3-category sweep with
  budget=1 needs 3 ticks and every category runs exactly once across them
  (req 1 + req 3 — no category silently dropped); test_board_sweep_
  cross_workspace_lock.py spawns two lock attempts over a shared locks dir
  and asserts the second defers; test_board_sweep_etag.py asserts
  If-None-Match is sent on the second call and 0 calls are billed on an
  unchanged fixture, while a first-ever call (no cache) bills once.

## Out of scope

- Leader election beyond a liveness-checked lock file (no distributed
  consensus — matches the issue's own phrasing, "lock or leader election").
- Changing per-session health-watcher behavior (`roster_watchdog` for a
  single entry) — issue requirement 2 explicitly keeps those per-session.
- Extending ETag conditional requests to `spawn_coverage._list_open_issues`
  or other non-board-list gh call sites beyond `closure_sweep.py`'s two
  board-list calls — those are separate call sites the issue's acceptance
  check does not name.

## Accumulation

The new subprocess `gh api` calls added (the ETag-conditional variants of
`issue_state_index_all`/`_pr_index_all`, and the cross-workspace lock's plain
file I/O, which issues no gh call at all) are each a single named helper in
gates/closure_sweep.py / spawn.py, not an inline call site repeated per
caller — the existing call sites (`find_violations`, `_board_wide_sweep`)
keep calling through these same two helpers, so this does not add new shape-1
(inline subprocess/gh call) instances per issue #512's accumulation
tracker; if this pattern is needed N more times (another board-list call
site wanting conditional requests), each future site should call the same
`issue_state_index_all`/`_pr_index_all` helpers rather than re-inlining the
`gh api -i` + ETag-cache dance, keeping shape-1 site count flat.

## How you'll know it worked

- `python3 -m pytest tests/test_board_sweep_budget_carryover.py
  tests/test_board_sweep_cross_workspace_lock.py tests/test_board_sweep_etag.py
  tests/test_gh_quota_guard.py tests/test_watchdog_local_signals.py -q`
  passes.
- The three new tests directly encode the three added acceptance checks from
  the issue (carry-over completeness, second-workspace defers, 0-billed-call
  304 on an unchanged board with first-tick-bills-once on an empty cache).
