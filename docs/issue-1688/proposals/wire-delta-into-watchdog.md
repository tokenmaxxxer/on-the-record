files:
  - spawn.py
  - gates/closure_sweep.py (only if find_violations truly cannot be driven by its
    existing `subjects` kwarg — survey found it already can, so likely untouched)
  - tests/test_spawn.py
  - docs/issue-1688/reports/implementation.md
  - docs/issue-1688/reports/implementation/survey.md
  - docs/issue-1688/proposals/wire-delta-into-watchdog.md

## Request

Wire `gates/gh_delta.py` and `gates/gh_cache.py` (landed in #1682, module-only
until now) into `spawn.py`'s watchdog tick path so `_board_wide_sweep` and
`requirement_drift` stop doing full per-tick `gh` rescans and instead consume
the change-delta.

## Constraints

- No shipped-code mocks: gh_delta/gh_cache calls in `spawn.py` must be real
  calls; only tests stub them.
- Keep `gates/closure_sweep.py` additive-only if touched at all.
- Don't invent a `gh_budget` module — if #1681 isn't landed, that sub-point is
  a documented no-op, not a new module.
- Don't touch package manifests, CI workflow files, or other proposals under
  `docs/proposals/*.md` (unrelated pending work).

## Rationale

Considered polling `gh_delta` from inside `gates/closure_sweep.py` directly
(e.g. having `find_violations` call `fetch_delta` itself when no `subjects`
arg is given). Rejected: `spawn.py` already owns the tick loop, backoff state,
and rate-limit guard sequencing — `gh_delta`/`gh_cache` (per #1682's own
module docstrings) are designed to be called by a consumer, not to own
scheduling. Embedding the probe inside `closure_sweep.py` would duplicate
tick-lifecycle concerns (backoff, rate-limit, call budget) that `spawn.py`
already tracks, and would make `find_violations` do two different things
(direct call vs. tick-driven call) depending on caller context — worse than
one wiring seam in the one place that already owns the tick.

Considered making `requirement_drift` always re-fetch full issue/PR bodies
for delta-changed numbers instead of caching verdicts for the unchanged rest.
Rejected: the issue's acceptance criteria explicitly ask for a verdict cache
so unchanged numbers don't need re-fetching even in delta mode — an on-disk
cache keyed by issue/PR number, atomic-written like `gh_delta`'s own
`_atomic_write_json` pattern, satisfies that without adding a second
network round trip per tick.

## Accumulation

This change does not add a new per-N inline `gh`/subprocess call site nor a
new repeated per-subject file. It replaces existing per-tick full-board `gh`
calls (in `_board_wide_sweep` and `requirement_drift`) with calls gated by a
single shared probe (`gh_delta.fetch_delta`, one call per tick, already
landed and cost-bounded by #1682's own pagination/max_pages contract) plus a
single small cache file (`runs/requirement_drift_cache.json`, one file,
whole-cache read/write via the same atomic temp+rename pattern as
`gh_delta`'s cursor file — not a per-issue file, so it does not grow a
directory of one-file-per-N artifacts). If a future issue adds more
delta-consuming call sites, they should reuse this same single-probe-per-tick
result rather than each calling `fetch_delta` independently — that is the
accumulation risk this proposal avoids by centralizing the probe at the top
of `_board_wide_sweep`.

## What will be done

1. `_board_wide_sweep(root)`: after the existing backoff/rate-limit guards
   (unchanged), call `gh_delta.fetch_delta(root, slug, "issues")` once per
   tick (the tick's single conditional probe). `slug` from `_repo_slug(root)`;
   `slug is None` (non-GitHub repo) falls back to today's full logic silently
   (pre-existing behavior, untouched).
2. classification `"no-change"`: skip closure-sweep/spawn-on-pr/spawn-coverage
   detail fetches and requirement-drift's full rescan for this tick; print a
   line containing `no-change (delta empty)`; still run
   `accumulation_trend()` (zero gh calls, unconditional per existing
   contract).
3. classification `"delta"`: build a `subjects` dict scoped to the delta's
   issue/PR numbers (cross-referenced against `spawn.board(root)`) and pass it
   to `closure_sweep.find_violations(root, subjects=..., issue_states=...)`;
   call `requirement_drift(root, changed_numbers=...)` which re-fetches only
   those numbers (via `gh_cache.cached_get`) and reuses a small on-disk
   verdict cache (`runs/requirement_drift_cache.json`) for everything else.
4. classification `"full-rescan"`: fall through unchanged to today's
   full-board closure-sweep/requirement-drift logic; print an explicit
   `full-rescan` line (gh_delta doesn't expose a reason string — log that
   plainly rather than fabricate one).
5. classification `"error"`: log that `gh_delta` itself failed, then fall
   back to today's full logic (conservative — never silently blind the sweep).
6. `gh_budget` (#1681): searched, not present in the repo — metering hook
   omitted per the issue's explicit allowance, noted in the implementation
   record.

## Out of scope

- Redesigning `gh_delta.py`/`gh_cache.py` internals (already correct per
  #1682).
- Building `gh_budget` (#1681) from scratch.
- Any change to `docs/proposals/*.md` (unrelated pending proposals).
- Narrowing `spawn-on-pr`/`spawn-coverage` to delta-only scope beyond what's
  needed for the no-change short-circuit (issue only asks for closure-sweep
  and requirement-drift narrowing on delta).

## How you'll know it worked

- `tests/test_spawn.py` gains tests asserting: (a) a no-change tick performs
  exactly one `gh_delta.fetch_delta` call and zero `closure_sweep.find_violations`
  calls, with the `no-change (delta empty)` line in stdout; (b) a 2-issue
  delta causes `find_violations` to be called with exactly those 2 subjects;
  (c) a `full-rescan` classification flows to the existing full-board logic
  with an explicit `full-rescan` line logged; (d) cold-cursor first tick is
  the same code path as (c) (no separate special case).
- `python3 -m pytest -q -m "not slow" tests/test_spawn.py` and
  `python3 -m pytest -q -m slow tests/test_spawn.py` both pass (full suite
  run and pasted in the implementation record).
