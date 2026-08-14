---
status: proposed
files:
  - spawn.py
  - gates/closure_sweep.py
  - gates/spawn_on_pr.py
  - gates/spawn_coverage.py
  - tests/test_gh_quota_guard.py
  - docs/handbooks/gh-quota-guard.md
---

## Request

GraphQL-backed `gh` calls (`gh pr view/list/merge`, `gh issue create/view`,
...) hit 0/5000 remaining on 2026-08-14 even though issue #1459 already cut
REST read cost. The watchdog's board-wide sweep and gate helpers kept
attempting bulk/lookup calls at full frequency with no quota awareness,
blocking orchestration issue-creation and forcing a fail-closed spawn
refusal. Two issue comments add binding design input: (a) local-first
triggering — decide *when* to call gh from local state, but a gh response
always overrides local inference once fetched (no-local-override); (b) an
operator directive making per-subject gh lookups in a sweep forbidden
outright — sweeps must resolve via bulk list + local join under a hard
per-tick call budget, and exceeding that budget is itself a defect signal.

## Constraints

- Requirements 1/2 must be immediately verifiable; 3/4/5 need concrete
  numeric defaults fixed now, not left open (issue's own binding
  constraint).
- Must not change read semantics of existing bulk-index helpers
  (`_pr_index_all`, `issue_state_index_all`, `_list_open_issues`) — only
  gate *whether/when* they run.
- Must not overlap or require sequencing against #1497's write set
  (monitors/poll-heartbeat.sh, hooks/directive.sh, hooks/stop-poll-rearm.sh)
  — survey confirmed zero file overlap and #1497 is unimplemented.
- Must not touch `pytest.ini` or `tests/test_spawn.py` (issue #1490 in
  flight).
- No-local-override invariant: local state may decide *when* a gh call
  fires; it must never replace or outrank the gh response once received.
- Per req 5: a sweep over N subjects must cost O(pages) bulk-list calls,
  never O(N) per-subject calls; a hard per-tick call-count budget
  (single digits) is enforced and logged as a defect signal when exceeded,
  not silently retried.

## Rationale

**Chosen approach: promote the existing `rate_limit_remaining` guard out of
`closure_sweep.py`'s standalone CLI `main()` into a shared quota-guard
module (new functions inside `gates/closure_sweep.py`, imported by
`spawn.py`'s `_board_wide_sweep`), and add backoff/budget state tracked in
a small JSON file under `runs/`.**

Alternative considered and rejected: build a wholly new
`gates/gh_quota_guard.py` module rather than extending
`gates/closure_sweep.py`. Rejected because `closure_sweep.py` already
owns `rate_limit_remaining`, `_pr_index_all`, and `issue_state_index_all`
— the three primitives every other gh-calling gate in the write set
(`spawn_on_pr`, `spawn_coverage`, `_board_wide_sweep`) already imports
from it. A second module would either duplicate `rate_limit_remaining` (two
sources of truth for "is quota healthy") or force every caller to import
from two places for one coherent concern. The frozen write set already
names `gates/closure_sweep.py` as the surface for req 1-3's quota/backoff
logic (issue's requirement text ties requirement 1's "shared helper" to
the same call graph #1 already improved), so extending it in place keeps
one call graph, one source of truth, and avoids introducing a new
import edge into every caller for no semantic gain.

A second alternative considered for req 5 (per-tick budget): count actual
subprocess invocations globally via a monkeypatch/wrapper around
`subprocess.run`. Rejected as over-engineered for this write set — every
gh-calling function in scope already funnels through a small, enumerable
set of call sites (3 in `_board_wide_sweep`, plus whatever
`spawn_on_pr`/`spawn_coverage` add); a per-tick budget can be enforced by
having `_board_wide_sweep` count its own known call sites and report an
overage, without a global subprocess interception layer that would also
have to special-case tests and non-gh subprocess calls (git, etc).

## What will be done

**Requirement 1 — quota helper as precondition (gates/closure_sweep.py):**
`_board_wide_sweep` (spawn.py) calls `closure_sweep.rate_limit_remaining`
first. Floor default: **500** (reuses the existing
`_RATE_LIMIT_GUARD_THRESHOLD` constant already used by `closure_sweep.py`'s
own CLI `main()` — same floor, now applied on the watchdog path too, so
the codebase has one quota-floor number, not two). Below floor:
`_board_wide_sweep` skips all three gh-calling signals
(`spawn_on_pr.spawn_missing_for_pr`, `closure_sweep.find_violations`,
`spawn_coverage._list_open_issues`), emits exactly one report line (e.g.
`[watchdog] board-sweep: 미집계 (rate-limit, remaining=<n>)`, matching
`closure_sweep.py main()`'s existing message shape), and returns without
attempting any of the three calls — zero gh calls made, per the acceptance
test's "with mocked remaining below floor, the sweep performs zero gh
calls" requirement. Local-only signals (`accumulation_trend`,
`requirement_drift`) still run — they cost no gh quota.

**Requirement 2 — REST migration:** survey found no GraphQL-backed `gh`
subcommand left in the frozen write set's watchdog/gate read paths — every
read already goes through `gh api` (REST) or `gh issue/pr list --json`
(REST-backed list endpoints, not the GraphQL API). `test_gh_quota_guard.py`
encodes this as a standing regression test (`test_graphql_free_watchdog_reads`)
that asserts, via recorded subprocess command lines in the read paths
under test, that no bare `gh issue view`/`gh pr view`/`gh pr merge`
GraphQL-backed subcommand appears — closing req 2 as "verified, not
migrated" since the write set has nothing left to migrate.

**Requirement 3 — sweep backoff (gates/closure_sweep.py +
spawn.py state):** a new `runs/gh_quota_backoff.json` state file keyed by
sweep name, tracking `{interval_ticks, consecutive_rate_limit_errors}`.
Initial interval: **1 tick** (no backoff, current behavior). On a
rate-limit error (bulk call fails with `ok=False` while remaining was
already below floor, or `rate_limit_remaining` itself reports below floor),
interval doubles, capped at **max 8 ticks**. A tick where
`current_tick_count % interval != 0` is skipped entirely (zero gh calls,
one skip-reason log line). On the next successful sweep, interval resets
to 1. Numbers chosen to keep backoff bounded (max 8-tick skip is a few
minutes to an hour depending on tick cadence, never unbounded) while still
meaningfully cutting call volume during a sustained outage.

**Requirement 4 — re-check backoff (gates/closure_sweep.py, reusable
helper; gates/spawn_on_pr.py adopts it for `parked_report`):** a generic
`recheck_backoff(state, key, changed: bool) -> bool` helper (same
`runs/gh_quota_backoff.json` state file, distinct key namespace) — a
subject not changed across **3 consecutive** re-checks is polled at a
doubling interval capped at **16 ticks**; any observed change resets it to
1. 3-consecutive-no-change matches the issue's stated
"repeated no-change results" acceptance language as the concrete trigger
count; 16-tick cap chosen as 2x requirement 3's cap since re-check subjects
(e.g. `parked_report` entries) are lower-urgency than the primary sweep.

**Requirement 5 — per-tick call budget + bulk reads:** `_board_wide_sweep`
already resolves all subjects via the two existing bulk-list calls
(`issue_state_index_all`, `_pr_index_all`) joined locally against
`spawn.board(root)` — confirmed by survey, no per-subject lookup exists in
the current call graph. This proposal adds an explicit budget: default
**8 calls per tick** (single-digit per the operator directive; current
steady-state usage is ~3 calls, headroom for the rate-limit probe call
itself plus any comment-posting calls in `--post` mode). A new
`gates/closure_sweep.py` counter (`count_gh_calls` context manager or
explicit call-site tally passed to `_board_wide_sweep`) tracks calls made
during one sweep; exceeding 8 emits a `[watchdog] board-sweep: 예산 초과
(N건 > 8)` line as a reported anomaly (counted like other anomaly signals
in `_board_wide_sweep`'s return count), not a silent retry or crash.

**Local-first complement:** no change to *what* `_board_wide_sweep` fetches
from gh (issue/PR state stays gh-authoritative, no-local-override
preserved) — requirements 1/3/4/5 collectively gate *when* it fetches,
which is exactly the frequency axis the local-first comment asks
complements (not replaces) the cost-per-call axis already covered by
requirements 1-3.

**Tests:** `tests/test_gh_quota_guard.py` implements all five acceptance
tests named in the issue (`test_bulk_loop_skipped_below_floor`,
`test_graphql_free_watchdog_reads`, `test_sweep_backoff_on_rate_limit`,
`test_recheck_backoff`, `test_sweep_call_budget`), each mocking
`subprocess.run` to assert call counts/command lines without hitting the
network.

**Docs:** `docs/handbooks/gh-quota-guard.md` records the four numeric
defaults (500 floor, 1/8-tick sweep backoff, 3-consecutive/16-tick
re-check backoff, 8-call/tick budget) and the state file path/schema, per
the doctrine ladder (new state file = handbook entry same turn).

## Accumulation

This change adds gh-calling/subprocess-adjacent code (the budget counter,
`rate_limit_remaining` call site, backoff-state read/write) but does not
add new *inline* per-subject subprocess/gh call sites — it wraps the
existing, already-bulk `_pr_index_all`/`issue_state_index_all`/
`_list_open_issues` call sites with a shared floor/backoff/budget guard
in `gates/closure_sweep.py`, called once from `_board_wide_sweep`. If this
guard pattern needs to be added to N more per-tick sweeps later (e.g. if
#1497's stamp-staleness check or a future sweep also wants
quota-awareness), each addition is one call to the shared
`rate_limit_remaining`/backoff-state helpers already added here, not a
new inline `subprocess.run(["gh", ...])` call — so repeated adoption grows
call-site count linearly (one guard call per new sweep) but does not grow
`accumulation.py`'s tracked shape-1 (inline subprocess/gh call) count,
since the guard itself is the shared-helper shape shape-1 exists to
distinguish from.

## Out of scope

- Requirement 2's literal file-by-file migration work — survey found
  nothing left to migrate in the frozen write set; if a GraphQL-backed
  call is later found elsewhere, that is a new issue.
- #1497's Monitor-tick quiet-emission and liveness-stamp work — zero file
  overlap, tracked separately.
- Any change to `pytest.ini` or `tests/test_spawn.py` (issue #1490 hold).
- A general subprocess-call interception/telemetry layer — the per-tick
  budget is enforced by explicit call-site counting in the known,
  enumerable set of gh-calling functions, not a global wrapper.
- Migrating `spawn_on_pr`/`spawn_coverage`'s own CLI entry points (outside
  `_board_wide_sweep`) to the new floor guard — only the watchdog tick path
  (`_board_wide_sweep`) is in scope per the issue's observed defect.

## How you'll know it worked

- `tests/test_gh_quota_guard.py`'s five tests pass, each asserting the
  behavior named in the issue's acceptance criteria (zero calls below
  floor; no GraphQL-backed subcommand in watchdog/gate reads; backoff
  interval doubling/reset on rate-limit; re-check interval growth on
  repeated no-change; ≤8 calls per sweep over 400 synthetic subjects).
- `docs/handbooks/gh-quota-guard.md` states the four numeric defaults so a
  future reader does not have to re-derive them from code.
- `_board_wide_sweep` emits the budget-overage line as a defect signal
  (not a crash, not a silent retry) when a synthetic test forces the
  8-call ceiling to be exceeded.
