---
issue: 2315
role: implementation
loop_state: landed
upstream:
  - path: gates/gh_delta.py
    sha: 972997f44277ce5d5bc3446e6a156cbe07c4e22f
code_under_review:
  - gates/gh_delta.py
  - gates/test_gh_delta.py
type: fix
breaking: "none — fetch_delta's signature, cursor file shape, and every other classification (delta/full-rescan/error) are unchanged; only the previously-unreachable no-change-via-304 branch becomes reachable"
verdict: pass
---

# issue-2315 — implementation record

## What was done

Reordered the two checks in `fetch_delta`'s per-page probe loop
(canonical: `gates/gh_delta.py:172-183`, this session's diff) so the
page-1 HTTP status is parsed from the `-i` response before the `gh`
returncode is inspected, and a page-1 `304` short-circuits straight to
the existing `got_304 = True; break` no-change path instead of falling
into `r.returncode != 0` first. Real `gh` exits 1 on every non-2xx
response including 304 (canonical: live `gh api ... -i` call this
session, `EXIT CODE: 1` on a real 304 response — pasted in full under
Executed acceptance evidence below), so before this change the
returncode check sitting above the 304 check made the 304 branch dead
code, reachable only by a test double hard-coding `returncode=0`
(canonical: `git stash push -- gates/gh_delta.py &&
python3 -m pytest test_gh_delta.py -k "no_change or genuine_non_304" -v`
from inside `gates/`, this session — pre-fix result pasted below shows
`1 failed` on the no-change test, `AssertionError: assert 'error' ==
'no-change'`).

Updated `gates/test_gh_delta.py`'s `_response()` helper (canonical:
`gates/test_gh_delta.py:8-16`, this session's diff) to default
`returncode` to real `gh` behavior (`0` for 2xx, `1` otherwise) instead
of always `0`, which makes the existing
`test_no_change_tick_makes_exactly_one_probe_and_zero_detail_fetches`
test actually exercise the fixed ordering — confirmed by the
stash-and-rerun above, which fails against the pre-fix code once this
helper change is in place. Added `test_genuine_non_304_error_still_classifies_error`
(canonical: `gates/test_gh_delta.py:80-99`, this session's diff — a
non-304 non-2xx response, a real 401, must still classify `"error"`)
and strengthened `test_pulls_resource_hits_issues_endpoint_no_since_symmetry_bug`
(canonical: `gates/test_gh_delta.py:207-208`, this session's diff) with
explicit assertions that a cold/absent cursor sends neither `since=`
nor `If-None-Match` (the issue's "empty state" acceptance line).

## Why

The issue's own root-cause diagnosis is exact (canonical: `gh issue
view 2315`, read this session): `gh` treats 304 as a non-2xx and exits
1, and the `r.returncode != 0` check sat above the `status == 304`
check in `fetch_delta`, so every cache-valid tick returned `"error"`
and fell back to a full rescan — inverting the ETag optimization to
fail exactly when the cache is valid. The fix is exactly the issue's
Ask: "parse the `-i` status line first; treat page-1 304 as no-change
before the returncode check." No alternative design was considered —
this is a pure bugfix reordering two existing checks with no open
design decision (scout-directive and survey-order-directive skip
condition), so the phase-1 survey/proposal round was not applicable
independent of the `CORE_BUILD_NOW=1` bypass also in effect this
session (canonical: `printenv | grep CORE_BUILD_NOW`, this session —
`CORE_BUILD_NOW=1`).

## What did not work

None.

## Rationale for deviations

None — delivered exactly the issue's Ask, no scope changes.

## Upstream basis

This issue's own body (`gh issue view 2315`, read this session — no
prior implementation-role survey for this issue exists, and
`CORE_BUILD_NOW=1` was set in this session's environment, authorizing
the delivery-only bypass of the phase-1 proposal round per contract v3
s19a). Code lands on `issue-2315/implementation`, based on
`972997f44277ce5d5bc3446e6a156cbe07c4e22f`. Prior art directly
referenced: issue #1682 (the change-cursor probe `fetch_delta`
implements, canonical: `gates/gh_delta.py:1-22` module docstring),
#1688 (the `include_prs` PR-only-drop fix, same function), #2240 (the
`state_paths`-anchored cursor path, unchanged by this fix).

### Executed acceptance evidence

Acceptance gate, full pass (canonical: `python3 -m pytest
gates/test_gh_delta.py -v`, run this session):

```
10 passed in 0.93s
```

8 pre-existing tests + 2 new (`test_genuine_non_304_error_still_classifies_error`,
and the strengthened `test_pulls_resource_hits_issues_endpoint_no_since_symmetry_bug`).
Zero skipped.

Regression-proof that the tests actually catch the pre-fix bug
(canonical: `git stash push -- gates/gh_delta.py && python3 -m pytest
test_gh_delta.py -k "no_change or genuine_non_304" -v` from inside
`gates/`, then `git stash pop`, run this session — only `gh_delta.py`
stashed back to pre-fix, test file changes kept):

```
AssertionError: assert 'error' == 'no-change'
  - no-change
  + error
1 failed, 1 passed in 0.81s
```

`test_no_change_tick_makes_exactly_one_probe_and_zero_detail_fetches`
fails exactly as the issue describes (304 classified `error`) against
the pre-fix ordering; the stash was popped cleanly afterward, leaving
this commit's tree unchanged (canonical: `git status --short` after
the pop, this session — only the intended `gates/gh_delta.py` and
`gates/test_gh_delta.py` modifications remained).

**Empty state** (no cursor — acceptance line 2): covered by
`test_pulls_resource_hits_issues_endpoint_no_since_symmetry_bug`
(canonical: `gates/test_gh_delta.py:196-221`, this session's diff),
which now asserts neither `since=` nor `If-None-Match` appears in the
`gh` invocation when no cursor file exists; classification is
unchanged (`full-rescan`, cold-cursor reason, same as before this fix
— canonical: same test, `assert classification == "full-rescan"`).

**Provenance — executed-live** (acceptance line 3), against the real
`tokenmaxxxer/on-the-record` GitHub repo this checkout is a clone of
(canonical: `git remote -v`, this session —
`origin https://github.com/tokenmaxxxer/on-the-record.git`), with `gh`
authenticated as `JiwonJung94` (canonical: `gh auth status`, this
session). A `python3 -` script drove the real, unmocked
`gh_delta.fetch_delta` with no `run=` override (i.e. the real
`subprocess.run` and real `gh` binary), plus a direct `gh api ... -i`
call reproducing the raw HTTP exchange, all run this session:

1. Real cache-valid probe. Cursor primed with `since` set to the probe
   moment (so the priming call's own result was empty, giving a stable
   ETag with nothing to invalidate it), then re-probed immediately with
   that ETag (canonical: direct terminal reproduction, this session):

   ```
   $ gh api repos/tokenmaxxxer/on-the-record/issues --method GET \
       -f state=all -f sort=updated -f direction=asc -f per_page=100 \
       -f page=1 -i -f since=2026-08-25T03:49:29.685348+00:00 \
       -H 'If-None-Match: "40f975c89996a53e6489ef836ccb86f6f1629466cc6427aa42d2d25f967452f2"'
   HTTP/2.0 304 Not Modified
   ...
   gh: HTTP 304
   EXIT CODE: 1
   ```

   — real `gh`, real repo, confirms the issue's core claim live: `gh`
   exits 1 on 304. `fetch_delta` run against this exact scenario (same
   cursor, same `gh` binary, no mocking, canonical: same session's
   `python3 -` script output):

   ```
   PROBE classification: no-change items: [] gh_calls: 1
   ```

   Classification `no-change`, items `[]` (zero detail fetches),
   exactly 1 `gh` call — the exact scenario the issue reports as
   broken, now correct.

2. Real error, still classified error (acceptance line 3, second
   clause) — a nonexistent repo slug, real 404, real nonzero exit
   (canonical: same session's `python3 -` script output):

   ```
   ERROR-PROBE classification: error items: None cursor: None
   ```

   Confirms the reorder did not broaden the no-change path to swallow
   genuine failures.

**Before/after heartbeat lines** (acceptance line 3, third clause).
`watchdog.py`'s board-sweep caller (canonical: `watchdog.py:946-968`,
read this session) prints one of two literal `print(...)` lines keyed
directly off `fetch_delta`'s classification value — matched here
against the classifications actually observed above for the identical
cache-valid scenario:

- Before (pre-fix; the live 304 scenario above classified `error` per
  the stash-and-rerun evidence): `[watchdog] board-sweep: gh_delta
  프로브 실패 (error 분류) — 보수적으로 오늘의 전체 로직으로 폴백`
  (canonical: `watchdog.py:953-955`) — followed by a full-logic
  fallback, the "heartbeat noise all night" the issue's title
  references.
- After (this fix; the identical scenario classified `no-change` per
  the live PROBE evidence above): `[watchdog] board-sweep: no-change
  (delta empty) — 상세 조회/전체 재훑기 건너뜀` (canonical:
  `watchdog.py:956-961`) — detail fetches and full rescan both
  skipped, matching the operator-frozen "REDUCES load by construction"
  constraint.

**Load-reduction note** (operator-frozen constraint, canonical:
`watchdog.py:953-962`, read this session): before this fix, every
cache-valid tick fell to the `error` branch (`watchdog.py:953-955`)
and re-ran the day's full board-sweep logic (closure-sweep +
requirement-drift over the full board); after this fix, the same tick
takes the `no-change` branch (`watchdog.py:956-962`) and skips both,
running only `accumulation_trend()` (via
`_run_local_only_signals(skip_requirement_drift=True)`,
`watchdog.py:961`) — a strict reduction in `gh` call volume per
cache-valid tick.

**Regression sweep** over the wider suite (canonical: `python3 -m
pytest gates/ tests/test_watchdog_heartbeat_noise.py
tests/test_spawn_observation_recovery.py -q`, run this session):

```
1 failed, 1134 passed, 12 xfailed, 1 xpassed in 387.68s (0:06:27)
```

The 1 failure (`Watchdog::test_delegation_phrasing_signal` in
`tests/test_spawn_observation_recovery.py`) is pre-existing on this
branch's base commit, unrelated to this change — reproduced identically
with `gates/gh_delta.py` and `gates/test_gh_delta.py` stashed out
(canonical: `git stash push -- gates/gh_delta.py
gates/test_gh_delta.py && python3 -m pytest
tests/test_spawn_observation_recovery.py -k
test_delegation_phrasing_signal -q && git stash pop`, run this session
— identical `AssertionError: False is not true` with this fix stashed
out; the stash was popped cleanly afterward).

## Open findings

None.

## Next steps

None — loop_state is terminal (`landed`).

---

skill-verdict: work-in-english — applied: invoked; this record, all
commit/PR text, and code comments were written in English per the
skill (the user's own prompts and the mounted directives are Korean);
the final chat summary to the user is in Korean per the skill's report
routing.
skill-verdict: other mounted skills (implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice,
implementation-blueprint) — not-applicable: this change reorders two
existing conditional checks inside one already-small function in one
file; no coupling/cohesion metric crossed a threshold, no accessor
chain or cross-module import direction was introduced, no GoF pattern
was considered or removed, no data-structure/algorithm/communication
tradeoff was made, and the change does not span multiple modules or
files needing structural decisions.
