---
name: issue-1682-survey
---

# Current-state survey — issue #1682

Scout skip: pure engineering pattern already fixed in-repo (issue #1554
established the ETag conditional-request convention this issue extends
from per-caller to shared); no product-facing design decision is open.
Skipping the scout sweep under scout-directive's second skip condition.

## Write set (planned new files, not yet on disk)

- gates/gh_delta.py (new) — change-cursor helper: conditional
  issues?state=all&sort=updated&since=<cursor> (+ pulls) probe, cursor
  persistence under runs/, corruption -> full-rescan classification.
- gates/test_gh_delta.py (new) — unit tests, no network (subprocess
  stubbed via injected `run`).
- gates/gh_cache.py (new) — shared on-disk read-through cache,
  ~/.tokenmaxxxer/gh-cache/, URL -> (ETag, body), used by any local
  `gh api` caller.
- gates/test_gh_cache.py (new) — unit tests: two consumers share one
  underlying fetch; 304 revalidation path; cold cache = today's
  behavior (unconditional fetch, cache populated).

Explicitly NOT touched (per issue's own scope fence): spawn.py (issue
#1678 owns it this cycle), gates/gh_budget.py — canonical: `find . -name
gh_budget.py` returned no result in this working tree at survey time,
so it does not exist yet here; issue #1681's session owns
creating/editing it, and if it lands mid-build here only NEW functions
may be added to it. gates/gh_rest.py exists already (read in full this
session — canonical: gates/gh_rest.py:1-93, functions
owner_repo/fetch_issue/fetch_issue_body/fetch_issue_title/fetch_pr_body/
fetch_pr_title, no ETag machinery in it) — new code goes in the new
sibling files above rather than editing it, to avoid any collision with
concurrent sessions touching the same file.

## Existing ETag precedent (issue #1554)

canonical: spawn.py:1284-1420 (read this session) and
gates/closure_sweep.py:73-132 (read this session).

- spawn.py:1284 `_etag_cache_path(root, number)` — per-issue-comments
  ETag cache path, local/uncommitted under `.git/`.
- spawn.py:1325 `_issue_comments(root, number)` — conditional GET:
  reads cached etag, sends If-None-Match, on 304 returns cached body
  with a zero-billed call, on 200 stores new etag+body.
- spawn.py:1401 `_split_gh_api_i_output(stdout)` — parses `gh api -i`
  output into (status, headers, body).
- gates/closure_sweep.py:73 `_board_list_etag_cache_path(root, name)` —
  same pattern, board-list scope, cache path
  `root / ".git" / "gh-read-cache" / f"board-list-{name}.json"`.
- gates/closure_sweep.py:80 `_conditional_issue_list(...)` — closest
  existing analogue to what #1682 needs: conditional
  `repos/{slug}/issues` fetch, 304 -> reuse cached raw list at 0 billed
  calls, cache write on 200, fail-open (any parse/read error ->
  unconditional re-fetch) — but this cache is per-workspace (under
  `.git/`), not shared across consumers, and it caches only "current
  full page 1", not a since=<cursor> delta.

Gap: no existing helper does (a) a cursor-based since= delta query, or
(b) a cache shared across processes/consumers rather than one
worktree's `.git/`. Both are new.

## State-file convention (runs/)

canonical: gates/closure_sweep.py:511-535,588-613 and
gates/test_claims.py:84-106 (read this session).

- gates/closure_sweep.py:511 `BACKOFF_STATE_REL = Path("runs") /
  "gh_quota_backoff.json"` — JSON state file under runs/,
  read-if-exists/fail-open, write via json.dumps + Path.write_text.
- gates/closure_sweep.py:588 `BOARD_SWEEP_QUEUE_STATE_REL` — same
  pattern for a pending-queue.
- gates/test_claims.py:84-106 fixtures write `.gitignore` content
  "runs/\n" and assert files under a `runs/` copy are treated as
  session-local/gitignored, not committed sources — runs/ is
  local/session-scoped state, never committed. The cursor file for
  #1682 follows this same convention: runs/gh_delta_cursor.json.

## Shared-cache location

Issue text specifies ~/.tokenmaxxxer/gh-cache/ (home directory, not
runs/ or .git/) — deliberately not workspace-local, since the point is
sharing across concurrent consumers (watchdog, orchestrator, sessions,
review agents) that may each have their own workspace/worktree.
canonical: `grep -rn "tokenmaxxxer/gh-cache\|Path.home()" gates/*.py
spawn.py` returned no hits this session, so no existing code writes
under ~/.tokenmaxxxer/ in this repo today. This is a new but injectable
path (a cache_root parameter, default Path.home() / ".tokenmaxxxer" /
"gh-cache", overridable by tests via tmp_path).

## No design decision left open

Cursor mechanics, ETag conditional GET, and JSON state-file persistence
are all precedented in this exact repo (#1554, closure_sweep.py,
spawn.py). The only new elements are (1) a since= query param and (2)
moving the cache root from per-workspace .git/ to a shared home
directory — both are direct, unambiguous extensions of the existing
pattern, not open design questions.
