---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
# canonical: python3 -m pytest tests/test_spawn.py -k watcher_dead
verdict: pass
loop_state: landed
---

## What was done

Built the approved phase-1 proposal
(docs/issue-1043/proposals/2026-08-12-watcher-dead-follow-attribution.md)
on current `main`: `_watch()` (spawn.py, `follow=True` branch, right
before the follow loop starts) now reads the workspace index entry's
current `watcher_pid` and checks it with the existing
`_watcher_looks_real(watcher_pid, issue, follow_role)`. Only when that
check is `False` (no watcher recorded, or the recorded one is
dead/not-a-real-watcher for this issue+role) does the follow process
register itself as the watcher via `_workspace_index_put(issue,
follow_role, work, str(log_path), watcher_pid=os.getpid(),
watcher_armed_at=time.time())`. When a live watcher (auto-armed or an
earlier follow) already covers the session, this invocation does not
overwrite it — following the read-before-write guard the proposal
already specified to close the after-proposal hunt finding (unconditional
overwrite letting a transient manual follow clobber a live auto-armed
watcher).

`_workspace_index_put()`'s existing whole-entry-replace contract means
registering the follow process's pid also clears the stale pid from the
roster entry for free — no separate cleanup step needed.

Added two regression cases to `tests/test_spawn.py`'s `WatchFollow`
class (named to match the acceptance's `-k watcher_dead` filter):
- `test_watcher_dead_stale_pid_cleared_by_live_follow_registration`: a
  stale dead auto-armed `watcher_pid` is pre-registered, then
  `spawn._watch(180, "implementation", 5.0, follow=True)` runs to
  session-end; asserts the workspace index's `watcher_pid` is now
  `os.getpid()` and `watchdog_check_one()` raises neither
  `watcher-dead` nor `watcher-missing`.
- `test_watcher_dead_or_missing_still_fires_with_no_watcher_registered`:
  control case — no watcher registered at all (setUp's default entry,
  no `watcher_pid`) — `watchdog_check_one()` still raises
  `watcher-missing`/`watcher-dead`, guarding against the fix being too
  permissive.

## Why

R001 (default-on integrity / watch-coverage regression guard, per
issue #1043's requirement linkage) — the roster watchdog was flagging
`watcher-dead` from stale auto-armed pids on nearly every tick even
while a live `watch --follow` actively covered the session, eroding
trust in real coverage-loss signals. Attributing liveness to any live
watcher for the session (auto-armed or follow), and clearing stale pids
on replacement, removes the chronic false positive without weakening
detection of the genuinely-uncovered case.

## Upstream basis

docs/issue-1043/proposals/2026-08-12-watcher-dead-follow-attribution.md

## Doc-placement ladder

- No env var, dependency, migration, or setup step was added — nothing
  to place in a handbook.
- No library-or-alternative choice or public-signature/wire-format
  change beyond what the proposal's own `## Rationale` already recorded
  — no new decisions entry needed under this issue's decisions bucket.
- No benchmark/investigation numbers produced — no separate reports
  entry beyond this record itself.

## What did not work

None.

## Acceptance verification

canonical: python3 -m pytest tests/test_spawn.py -k watcher_dead
```
$ python3 -m pytest tests/test_spawn.py -k watcher_dead
collected 477 items / 475 deselected / 2 selected

tests/test_spawn.py ..                                                   [100%]

====================== 2 passed, 475 deselected in 0.21s =======================
```
Full-suite run, same code, no narrower filter —

canonical: python3 -m pytest tests/test_spawn.py
```
$ python3 -m pytest tests/test_spawn.py
collected 477 items
...
============================= 477 passed in 33.48s =======================
```
No `SKIPPED` lines appear in either pasted output.

## Hunt (before-landing)

Dispatched one background `warrant-hunter` (stance 0: assume the gate
just touched is bypassable — find the bypass), cap 120s (diff 21-200
lines tier), against docs/issue-1043/reports/implementation/hunt-2026-08-12-watcher-dead-follow-attribution.md.

canonical: hunter agent aefda5677b97f8d71's report, this session (2026-08-12)

Result: the read-before-write guard in `_watch()` reads
`watcher_pid`/`_watcher_looks_real()` outside any lock before calling
`_workspace_index_put()` (which itself locks). Two concurrent
`--follow` processes for the same issue+role can both observe "no live
watcher" and both write; the second call's `_workspace_index_put()`
overwrites the first's registration.

Judged non-blocking for this delivery: both writers in the reproduced
race are genuinely live, real (`_watcher_looks_real()`-passing) follow
processes — unlike the earlier after-proposal hunt result, no writer
here exits before a watchdog tick reads the entry, so the race itself
produces no incorrect `watcher-dead`/`watcher-missing` flag; the
surviving registration remains a live, valid watcher. The underlying
check-then-write pattern is not new to this change — it is the same
pattern the pre-existing auto-arm call site already uses against
`_workspace_index_put()`'s internal lock. Reconciling concurrent
watcher claims (e.g. compare-and-swap, or refusing a second follow
registration outright) is a design decision beyond this proposal's
frozen write set and its stated out-of-scope items (`watch --all`
per-session registration, periodic re-registration); it is carried
forward as an open item below rather than folded into this fix.

## Open findings

- TOCTOU race in `_watch()`'s watcher-claim read-before-write (see
  Hunt section above) — two concurrent `--follow` invocations for the
  same issue+role can race on `_workspace_index_put()`; not a
  regression of the chronic-false-positive defect this issue reports,
  but an unreconciled concurrent-claim gap.
- resolution path: a future issue proposing either a compare-and-swap
  primitive in `_workspace_index_put()` or an explicit single-follow-
  owner invariant, scoped and proposed independently since it touches
  the shared write helper beyond this proposal's frozen write set.
