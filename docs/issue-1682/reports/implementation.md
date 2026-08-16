---
code_under_review:
  - gates/gh_delta.py
  - gates/test_gh_delta.py
  - gates/gh_cache.py
  - gates/test_gh_cache.py
type: feature
breaking: false
verdict: pending
loop_state: landed
---

# issue-1682 phase-2: change-cursor probe + shared ETag cache

canonical: commit f21d5209 (this branch, `git show --stat f21d5209`) —
gates/gh_delta.py, gates/gh_cache.py, gates/test_gh_delta.py,
gates/test_gh_cache.py added there.

## Summary of work

Built `gates/gh_delta.py` (change-cursor probe hitting `repos/{slug}/issues`
for both `resource="issues"` and `resource="pulls"`) and `gates/gh_cache.py`
(shared on-disk ETag/body read-through cache), each with a unit-only pytest
module (injected `run`, no network, `tmp_path`-scoped cache/cursor roots).

## Why

canonical: `gh issue view 1682 --comments` output read this session — the
second-to-last comment on the thread (author JiwonJung94, posted after PR
#1683 merged) carries the ACCEPTANCE AMENDMENT and 5 BINDING PHASE-2
CONDITIONS, and the final comment is `APPROVE issue-1682/implementation`.

Basis: `docs/issue-1682/proposals/change-cursor-shared-cache.md` (phase-1
proposal). This build follows the binding conditions from that comment
directly:

1. Pagination: `fetch_delta` loops pages (`per_page`-bounded, follows the
   `Link: rel="next"` header) instead of reading only page 1; a burst larger
   than one page is never silently dropped. A `max_pages` cap exists as a
   circuit breaker; exceeding it is classified `full-rescan`, never a silent
   truncation. Covered by
   `test_gh_delta.py::test_pagination_follows_pages_burst_over_30_never_dropped`
   and `::test_page_overflow_beyond_max_pages_classifies_full_rescan`.
2. Cursor advance: the persisted cursor (`since`) is
   `max(item["updated_at"] for item in all items observed this tick)`, never
   the caller's local clock (`gh_delta.py` `fetch_delta`, the
   `updated_ats`/`new_since` block). `since` is an inclusive (`>=`) filter so
   a boundary item can be re-observed on the next tick — documented in
   `fetch_delta`'s docstring as accepted duplicate tolerance, not a bug.
   `last_reconciliation` in the cursor file plus `reconcile_interval_hours`
   (default 24) forces a periodic full-rescan independent of corruption —
   covered by `test_periodic_reconciliation_forces_full_rescan_even_without_corruption`.
3. Pulls: `fetch_delta` never calls `GET /pulls` (which has no `since`).
   Both `resource="issues"` and `resource="pulls"` hit `repos/{slug}/issues`,
   then client-filter on the `pull_request` key's presence/absence — covered
   by `test_pulls_resource_hits_issues_endpoint_no_since_symmetry_bug` and
   `test_issues_resource_excludes_pull_requests`.
4. Cache concurrency: `gh_cache.cached_get` and `gh_delta.fetch_delta`'s
   cursor persistence both write via temp-file + `os.replace` (atomic
   rename) — covered by `test_gh_cache.py::test_cache_write_is_atomic_no_stray_temp_files`.
5. `gh_cache.cached_get`'s two-consumers fixture matches the amended
   acceptance literally: first consumer = one unconditional fetch; second
   consumer sharing `cache_root` = one conditional revalidation (304 in the
   fixture) that is itself counted as the "one underlying fetch" per the
   amendment, and the second consumer's returned body comes from the disk
   cache, not a re-fetched body — covered by
   `test_two_consumers_second_gets_304_revalidation_from_disk`.

Plus the original phase-1 fixtures (no-change tick = exactly 1 probe + 0
detail fetches, cold cache = today's behavior, cursor corruption ->
full-rescan) — all present in `test_gh_delta.py`/`test_gh_cache.py`.

## Upstream basis

canonical: `gh issue view 1682 --comments` output read this session,
comment: "[watch] issue-1682/implementation: session-end: PR
https://github.com/tokenmaxxxer/on-the-record/pull/1683 opened", followed
by the phase-1-merged approval comment.

docs/issue-1682/proposals/change-cursor-shared-cache.md (PR #1683).

## What did not work

None — first implementation matched the design; no discarded approach
mid-build.

## Doc placement

No env var / config key / new dependency / migration / setup-script change
in this write set. No decisions-doc entry needed: module contract matches
the phase-1 proposal's `files:`/section list (see the file diff cited
above); no alternative was swapped mid-build.

## Open findings

canonical: this session's own warrant-hunter dispatch (agent
abf9398db1f8b5767) and its returned finding text, this turn.

Zero open findings remain.

closed_checks:
- warrant-hunter run (this turn, agent abf9398db1f8b5767), canonical: its
  returned finding text — found `_atomic_write_json` in both
  `gates/gh_cache.py` and `gates/gh_delta.py` called `tempfile.mkstemp()`
  outside its own `try/except OSError`, so a write-path OSError
  (permission-denied cache dir, disk full) crashed the caller instead of
  failing open.
  canonical: acceptance: `python3 -m pytest gates/test_gh_delta.py gates/test_gh_cache.py -q` — result: PASS (13 passed in 0.84s, re-run after wrapping `mkdir`+`mkstemp` in their own `try/except OSError: return` in both files, commit f21d5209's `_atomic_write_json` in each file).

## Next steps

Wiring `gh_delta`/`gh_cache` into `closure_sweep.py`/watchdog ticks, and the
live 10-minute quiet-window measurement, are out of scope per the
proposal's `## Out of scope` — left for a sequenced follow-up issue. This
write set's own scope has no further step.

## Resolution path

canonical: acceptance: `python3 -m pytest gates/test_gh_delta.py gates/test_gh_cache.py -q` — result: PASS (13 passed in 0.84s).
