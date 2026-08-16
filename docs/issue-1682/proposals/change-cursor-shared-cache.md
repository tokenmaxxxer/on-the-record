---
status: proposed
files:
  - gates/gh_delta.py
  - gates/test_gh_delta.py
  - gates/gh_cache.py
  - gates/test_gh_cache.py
---

## Request

Make GitHub API demand scale with actual repository changes, not with
consumers x subjects x ticks. Concretely: a change-cursor probe (one
conditional REST call per tick, delta-only) and a shared on-disk
ETag/body cache so redundant consumers hitting the same URL cost one
underlying fetch instead of N.

## Constraints

- Module + tests only, per #1682's own scope fence: no edits to
  spawn.py (issue #1678 is editing it this cycle) and no edits to
  gates/gh_budget.py (it does not exist in this tree yet — see
  survey.md — and is issue #1681's to create/own; if it lands mid-build
  here, only new functions may be added, never edits to existing ones).
- No network calls in the unit tests (contract: injected `run`
  callable, same convention gates/gh_rest.py already uses).
- Cursor and cache state must be local/session-scoped, never committed
  (runs/ for the cursor, per docs/issue-1682/reports/implementation/survey.md's
  runs/ convention; ~/.tokenmaxxxer/gh-cache/ for the shared cache, per
  the issue's own spec — both overridable via an injectable path
  parameter so tests use tmp_path).

## Rationale

Considered extending gates/closure_sweep.py's existing
`_conditional_issue_list`/`_board_list_etag_cache_path` pair in place
instead of adding new modules — rejected because that cache is
intentionally per-workspace (`root / ".git" / "gh-read-cache"`) and
caches only "current page 1", not a cursor-scoped delta; retrofitting
it to also serve as the cross-consumer shared cache and the delta
probe would require callers outside this issue's write set (anything
already calling `_conditional_issue_list`) to change their contract,
which risks exactly the collision #1682 was told to avoid with
concurrently-edited files (spawn.py, gh_budget.py). Two small new
sibling modules keep the change additive: existing callers are
untouched, and a future sweep-wiring issue can adopt gh_delta.py's
output without anyone having had to migrate mid-cycle.

Considered a webhook-push design instead of polling — rejected per the
issue's own design-research note: no public endpoint exists for this
local-first system, so an ETag-polled cursor is the standard local
equivalent (RSS/Atom, GitHub's own Events API + X-Poll-Interval use the
same shape).

## What will be done

- gates/gh_delta.py: `fetch_delta(root, slug, resource, cursor,
  run=None)` — one conditional GET (`issues` or `pulls`,
  `state=all&sort=updated&since=<cursor>`, `If-None-Match` when an ETag
  is cached) returning `(items, new_cursor, classification)`.
  Classification is one of `"delta"` (normal), `"no-change"` (304 or
  empty body — zero detail fetches follow), or `"full-rescan"` (cursor
  file missing required fields, unparseable, or timestamp obviously
  invalid — explicit, never silent). Cursor persists to
  `runs/gh_delta_cursor_<resource>.json` after every successful probe
  (advances only on a 200, not on error).
- gates/test_gh_delta.py: unit-only (injected `run` stub, no network) —
  (1) delta call returns only items at/after the stored cursor and
  writes the advanced cursor; (2) a no-change tick (stubbed 304) makes
  exactly one probe call and zero further calls (fixture asserts the
  stub's call count); (3) a corrupted cursor file (malformed JSON /
  missing `since` key) is classified `"full-rescan"`, not silently
  treated as `since=None`.
- gates/gh_cache.py: `cached_get(url, run=None, cache_root=None)` — an
  on-disk read-through cache keyed by URL, storing `{etag, body}` under
  `cache_root` (default `Path.home() / ".tokenmaxxxer" / "gh-cache"`,
  hashed filename per URL). First call: unconditional fetch, cache
  write. Later call by any consumer sharing `cache_root`: conditional
  fetch with `If-None-Match`; 304 -> serves the cached body, one
  billed call recorded (issue #1682's acceptance treats the
  revalidation request itself as the "one underlying fetch", matching
  the existing #1554 precedent's accounting in
  gates/closure_sweep.py:_conditional_issue_list).
- gates/test_gh_cache.py: unit-only — (1) two `cached_get` calls from
  independent "consumers" (separate function calls, same `cache_root`
  tmp_path) against the same URL: the underlying stubbed `run` is
  invoked once for the first (cold) fetch and once more for the
  second consumer's conditional revalidation (asserting the second
  consumer never re-fetches the body on a stubbed 304, i.e. gets it
  from disk); (2) cold-cache path (no prior cache file) behaves like an
  unconditional fetch, matching today's behavior.

## Out of scope

- Wiring gates/closure_sweep.py or spawn.py's sweeps to consume
  gh_delta.py's output (sequenced follow-up, per the issue body).
- gates/gh_budget.py (issue #1681's ownership).
- The live 10-minute quiet-window measurement acceptance check — that
  is an operational/live check run against a real watchdog loop, not
  something a module-+-tests PR can execute; it is left for the
  sequenced sweep-wiring follow-up once gh_delta.py is actually wired
  into the tick loop.

## How you'll know it worked

- `python3 -m pytest gates/test_gh_delta.py gates/test_gh_cache.py -q`
  passes, no network calls made (all `gh` invocations go through an
  injected stub `run`), and specifically covers: exactly-one-probe/
  zero-detail-fetch on a no-change tick, cursor-corruption ->
  full-rescan classification, and one-underlying-fetch-across-two-
  consumers with the 304 revalidation path.
