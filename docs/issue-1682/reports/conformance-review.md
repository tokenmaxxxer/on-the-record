---
subject: issue-1682
role: conformance-review
kind: record
loop_state: verdict-issued
upstream: docs/issue-1682/proposals/change-cursor-shared-cache.md
code_under_review:
  - gates/gh_delta.py
  - gates/test_gh_delta.py
  - gates/gh_cache.py
  - gates/test_gh_cache.py
---

# Conformance review — issue #1682 (change-cursor probe + shared ETag cache)

## What was done

Reviewed the issue-1682/implementation branch's phase-2 delivery (commit `f21d5209b24deaec6c7f8b2bd9f834bd50918ffb`, "feat(issue-1682): change-cursor probe + shared ETag cache", plus record commit `8db254f7`) against issue #1682's four acceptance checks, per-requirement verdicts below.
canonical: git show f21d5209:gates/gh_delta.py, git show f21d5209:gates/gh_cache.py, git show f21d5209:gates/test_gh_delta.py, git show f21d5209:gates/test_gh_cache.py (all read this session).

Landing status: PR #1687 (base main, head issue-1682/implementation) is state=OPEN, mergedAt=null.
canonical: `gh pr list --state all --search 1682 --json number,state,mergedAt,baseRefName,headRefName` (run this session).

This review's own board approval and the spawn condition both name the `issue-1682/implementation` branch, not `main`, as the review target, so the code below is reviewed as instructed even though it is not yet on the merged board.
canonical: `gh issue view 1682 --json comments` (comment body "APPROVE issue-1682/conformance-review", read this session).

## Why

Issue #1682 asks whether GitHub API demand was made proportional to changes via (1) a change-cursor probe and (2) a shared ETag read-through cache, replacing per-subject/per-consumer full rescans.
canonical: gh issue view 1682 (issue body, read this session).

## Per-requirement verdicts

### Check 1 (unit) — change-cursor helper

`fetch_delta()` reads a `runs/gh_delta_cursor_<resource>.json` cursor, issues one conditional `gh api repos/{slug}/issues?since=<cursor>` probe, returns only items whose `updated_at` postdates the persisted cursor, and persists the max-observed `updated_at` as the new cursor after a successful probe.
canonical: gates/gh_delta.py:99-181 (f21d5209, read this session, `fetch_delta`).

A no-change tick (304 response) makes exactly one probe call, zero further calls, and zero detail fetches. Cursor-file corruption (unparseable JSON, missing `since` key) is classified `"full-rescan"`, never silently treated as `since=None`.
canonical: gates/gh_delta.py:76-92 (`_load_cursor`), 133-141 (`forced_rescan` branch) (f21d5209, read this session).

```
$ python3 -m pytest test_gh_delta.py -q
9 passed in 0.02s
```
`derived: git archive f21d5209 gates/gh_delta.py gates/test_gh_delta.py | tar -x -C /tmp/review1682 && python3 -m pytest /tmp/review1682/gates/test_gh_delta.py -q` (run this session) — output fenced above (9 passed), includes test_no_change_tick_makes_exactly_one_probe_and_zero_detail_fetches and test_corrupted_cursor_file_classifies_full_rescan.

No network calls: every test injects a stub `run` callable in place of `subprocess.run`.
canonical: gates/test_gh_delta.py:1-32 (`fake_run`/`_response` fixtures, f21d5209, read this session).

**Verdict: Present.**

### Check 2 (unit) — shared cache serves a second consumer from disk

`cached_get()` keys an on-disk cache file by `sha256(url)` under a `cache_root` (default `~/.tokenmaxxxer/gh-cache/`, shared across consumers/worktrees); a cold call does an unconditional fetch and writes `{etag, data}`; a later call against the same `cache_root` sends `If-None-Match` and, on 304, serves `data` from the on-disk cache rather than the body-less 304 response.
canonical: gates/gh_cache.py:44-102 (f21d5209, read this session, `cached_get`).

```
$ python3 -m pytest test_gh_cache.py -q
4 passed in 0.02s
```
`derived: git archive f21d5209 gates/gh_cache.py gates/test_gh_cache.py | tar -x -C /tmp/review1682 && python3 -m pytest /tmp/review1682/gates/test_gh_cache.py -q` (run this session) — output fenced above (4 passed), includes test_two_consumers_second_gets_304_revalidation_from_disk and test_cold_cache_behaves_like_unconditional_fetch.

Scope note: the issue's literal acceptance text says "one underlying fetch across two consumers"; the operator amended this on-record before the implementation landed: "two consumers → at most ONE full-body fetch; a conditional 304 revalidation by the second consumer is permitted and counts as a cache hit."
canonical: `gh issue view 1682 --json comments` (operator comment body dated 2026-08-16, read this session).

The delivered test matches the amended text (two `run` calls: one 200 body fetch, one 304 revalidation), not the pre-amendment literal text.
canonical: gates/test_gh_cache.py:11-31 (f21d5209, read this session).

**Verdict: Present, against the on-record amended acceptance text (not the issue's original literal wording, which the operator superseded before this code was written).**

### Check 3 (live) — quiet-window call-count drop / active-drive tracking

No wiring of `gh_delta.py`/`gh_cache.py` into the watchdog tick loop or any sweep exists on this branch.
canonical: `grep -rn "gh_delta\|gh_cache" spawn.py gates/closure_sweep.py` (run this session against origin/main's copies of those two files) — zero hits in either file.

The implementation's own proposal states this explicitly as out of scope: "The live 10-minute quiet-window measurement acceptance check ... is left for the sequenced sweep-wiring follow-up once gh_delta.py is actually wired into the tick loop."
canonical: docs/issue-1682/proposals/change-cursor-shared-cache.md, "Out of scope" section (read this session).

**Verdict: Absent.** Two of the two prerequisite unit checks are met, but the acceptance criterion itself — an actual before/after `rate_limit` delta measured over a live watchdog loop — cannot be produced by unwired modules; nothing calls `fetch_delta`/`cached_get` yet. This is not a defect in the delivered diff (the proposal disclosed the deferral before building, and the operator's binding-conditions comment on PR #1683 did not object to that scope fence) but it is a stated acceptance check with no landed satisfying evidence, addressed to the implementation role as the open finding below.

### Empty-state check — cacheless first run == today's behavior

`test_cold_cache_behaves_like_unconditional_fetch` asserts a cache miss does exactly one unconditional `run` call with no `If-None-Match` header, matching pre-#1682 behavior; `fetch_delta` with no cursor file consumes the same one call a cold run would today (classified `full-rescan` rather than steady-state, but not extra calls).
canonical: gates/test_gh_cache.py:33-42 (`test_cold_cache_behaves_like_unconditional_fetch`), gates/gh_delta.py:99-181 (`forced_rescan` cold-cursor branch), f21d5209, read this session.

```
$ python3 -m pytest test_gh_cache.py -k cold -q
1 passed in 0.02s
```
`derived: git archive f21d5209 gates/gh_cache.py gates/test_gh_cache.py | tar -x -C /tmp/review1682-b && python3 -m pytest /tmp/review1682-b/gates/test_gh_cache.py -k cold -q` (run this session) — output fenced above (1 passed).

**Verdict: Present.**

## Open findings

1. Acceptance check 3 (live) has no landed satisfying evidence — the two new modules exist and are unit-tested but are not wired into any consumer (watchdog tick, `closure_sweep.py`, `spawn.py`), so the actual API-demand reduction the issue exists to deliver is not yet observable or measurable.
   canonical: `grep -rn "gh_delta\|gh_cache" spawn.py gates/closure_sweep.py` (above) — zero hits.
   canonical: docs/issue-1682/proposals/change-cursor-shared-cache.md, "Out of scope" section (read this session, cited above under Check 3).
   Resolution path: a follow-up implementation round wires `gh_delta.py`/`gh_cache.py` into the watchdog tick loop and sweeps, sequenced per that deferral, then the live #1682 acceptance check is retried.
   Addressed to: the implementation role (issue-1682/implementation or a sequenced follow-up issue) — this review role records verdicts, it does not wire the sweeps.

## Next steps

Implementation role wires `gh_delta.py`/`gh_cache.py` into the watchdog tick loop and into `closure_sweep.py`'s per-subject sweeps (the proposal's own deferred item), then re-invokes conformance-review to verdict check 3 against a live before/after `rate_limit` measurement.

## Upstream

Basis: issue-1682/implementation branch at commit `f21d5209b24deaec6c7f8b2bd9f834bd50918ffb` (phase-2 code) and `8db254f7` (its own record).
canonical: `git log --oneline --all` | grep 1682 (run this session).
