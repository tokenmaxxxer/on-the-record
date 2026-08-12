---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: feature
breaking: false
verdict: pending
loop_state: landed
---

Subject: issue-1013

## What was done

canonical: this session's own working-tree diff (`git diff --stat` on
this branch: `spawn.py` +62/-5, `tests/test_spawn.py` +158) and its own
edits to spawn.py/tests/test_spawn.py made this turn.

Built blocks A-F of session-ownership scoping per
docs/issue-1013/proposals/session-ownership-scoping.md (blocks A-F
section) and docs/issue-1013/proposals/session-ownership-scoping-build.md
(this role's own build-authorization proposal):

- **A.** `_roster_own(d: dict, all_scope: bool) -> dict` (spawn.py, new
  helper right before `_watcher_looks_real`) — `all_scope=True` returns
  `d` unchanged; otherwise keeps entries whose `session_id` equals the
  caller's own id (`os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None`)
  or is `None` (empty-state parity: `None == None` self-match).
- **B.** `roster_watchdog(auto_respawn=False, all_scope=False)` now loads
  the full roster (`d_all`), filters it through `_roster_own()` into `d`,
  and scans `d` exactly as before.
- **C.** `_undispositioned_role_prs()` builds an own-scope roster key set
  via `_roster_own(_roster_load(), all_scope=False)` and skips any open
  PR whose `headRefName` matches one of those keys, in addition to the
  existing `exclude_issue` skip.
- **D.** Inside `roster_watchdog()`, when not `all_scope`, dead entries
  present in `d_all` but filtered out of `d` (foreign `session_id`) print
  under a `[orphaned]` label and are counted as anomalies; they sit
  outside the main scan loop entirely, so `_auto_respawn_check()` is never
  called on them.
- **E.** `roster_ps()`'s watcher-status line compares the owning entry's
  `session_id` against the caller's own id; a live, real watcher owned by
  a different (non-`None`) session prints
  `워처: pid N  armed M분 전  (다른 세션 소유)` instead of the
  `follow=True` line implying local ownership.
- **F.** `spawn.py watchdog --all` threads `all_scope=a.all` into
  `roster_watchdog()`, reusing the existing `--all` argparse flag
  (spawn.py:4549).
- `tests/test_spawn.py` gained a `RosterOwnershipScoping` test class.

derived: python3 -m pytest tests/test_spawn.py -k RosterOwnershipScoping -q
```
7 passed, 465 deselected in 0.41s
```
covering: `_roster_own` unit behavior (own+None-sid kept, `--all`
unchanged, empty-state parity with env unset), `roster_watchdog`
default-vs-`--all` scope with orphan surfacing, `_undispositioned_role_prs`
own-branch exclusion, `roster_ps` other-session watcher labeling, and the
CLI `--all` thread-through.

## Why

canonical: docs/issue-1013/proposals/session-ownership-scoping.md
("Intent" and planned-changes sections) and the issue's own operator
report read via `gh issue view 1013` this session.

Multi-session confusion on one machine: global roster/watchdog code paths
never filtered on the already-stored `session_id` field, so concurrent
orchestrator sessions saw, blocked, and auto-respawned each other's work.
One shared helper reused at four call sites plus a CLI thread-through
addresses this, rather than four independent ad-hoc filters.

## Upstream basis

- based on: docs/issue-1013/proposals/session-ownership-scoping.md
  (product-discovery phase-1 design, landed via PR #1016)
- based on: docs/issue-1013/proposals/session-ownership-scoping-build.md
  (this role's own phase-1 build-authorization proposal)

## Acceptance verification

canonical: python3 -m pytest tests/test_spawn.py -q — executed this turn
in this working tree.
acceptance: python3 -m pytest tests/test_spawn.py -q — result: pass
```
472 passed in 33.90s
```
No SKIPPED lines in the pasted output.

canonical: python3 -m py_compile spawn.py — executed this turn in this
working tree.
acceptance: python3 -m py_compile spawn.py — result: pass (exit 0, no
output)

## Open findings

canonical: docs/issue-1013/reports/product-discovery/2026-08-12-hunt-session-ownership-scoping.md
(product-discovery role's own after-proposal hunt record, read this
session).

The upstream design's own open finding stands and is out of this build's
write set: nothing in the repository ever sets `ORCHESTRATOR_SESSION_ID`,
so `_roster_own()` degenerates to `None == None` self-matching for every
real invocation today.

canonical: docs/issue-1013/reports/implementation/2026-08-12-hunt-session-ownership-scoping-build.md
(this session's own before-landing warrant-hunt record, agent a7b3394cfb0998b10).

This session's own before-landing hunt sharpens that same degenerate case
for block C specifically: since `_roster_own()` treats a `session_id`-less
entry as "own" (empty-state parity), and no launcher ever sets
`ORCHESTRATOR_SESSION_ID` today, `_undispositioned_role_prs()` currently
excludes ANY roster entry's branch from the undisposed-PR gate, not only
entries this exact calling session actually spawned — narrowing gate C
further than intended in the concurrent-session case, until the env var
is wired. This is the same root open finding as above (no
`ORCHESTRATOR_SESSION_ID` set-point exists anywhere in the repository),
manifesting as a gate-narrowing side effect specific to block C rather
than a new, independent defect.

resolution path: out of this build's frozen write set by design (the
`ORCHESTRATOR_SESSION_ID` set-point is a launcher/harness concern,
per docs/issue-1013/proposals/session-ownership-scoping.md's own "Out of
scope" section) — actionable only by a future companion issue that mints
and exports a real per-session id; not fixable by further edits to
`_undispositioned_role_prs()`, `_roster_own()`, or `roster_watchdog()`
under this proposal's write set.

## What did not work

None.

## Doc placement

- No new env var, config key, dependency, or migration introduced.
- No public signature/wire-format change and no library-or-format choice
  over a named alternative beyond the landed design.
- No benchmark/investigation numbers produced beyond this record and the
  hunt record noted above.

canonical: this session's own edits (`git diff --stat`, cited above) —
no docs/handbooks/, docs/issue-1013/decisions/, or docs/issue-1013/reports/
(other than this file and the hunt record) files were touched this turn.

## Verification artifacts

closed_checks:
  - name: py_compile
    code_sha: (working tree, pre-commit)
  - name: full_test_suite
    code_sha: (working tree, pre-commit)

## Next steps

- Commit this record together with spawn.py/tests/test_spawn.py on
  `issue-1013/implementation`, push, and open the phase-2 delivery PR
  carrying `Closes #1013`, and state the before-landing hunt finding
  above plainly in that PR's body.
