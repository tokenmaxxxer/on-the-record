---
code_under_review:
  - spawn.py
  - gates/test_watch_rearm_registry.py
type: fix
breaking: false
# canonical: python3 -m pytest gates/test_watch_rearm_registry.py -v —
# result: 7 passed in 0.06s, no SKIPPED lines (fenced transcript below)
verdict: pass
loop_state: committing
---

canonical: fenced pytest transcript below, executed this session on the
current working tree.
acceptance: python3 -m pytest gates/test_watch_rearm_registry.py -v — result: pass, see fenced output below
```
$ python3 -m pytest gates/test_watch_rearm_registry.py -v
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_already_alive_watcher_is_not_respawned PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_autoarm_returns_immediately_surviving_caller_exit PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_never_armed_entry_untouched_and_still_missing PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearm_clears_watcher_dead_and_updates_registry PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearm_passes_repo_context_for_mismatched_cwd PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearmed_watcher_dying_again_is_still_flagged PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_remediation_strings_carry_no_bare_follow PASSED
7 passed in 0.06s
```

## Summary of work

Implements the approved proposal
docs/issue-1154/proposals/watcher-autoarm-detached.md.
canonical: docs/issue-1154/proposals/watcher-autoarm-detached.md (approved
phase-1 proposal, read this session) and spawn.py:5930-5971 (auto-arm
block read this session).
In `_spawn_one()`'s auto-arm block (spawn.py, `if child_pid > 0:`
branch), change the watcher-registered branch to return right after
registration — the same shape `_rearm_watcher_detached()` already uses
(spawn.py:3948-4009) — rather than falling through into the blocking
`_await_bounded()` call when `no_wait` is false. `_rearm_watcher_detached()`
itself is not touched by this write set. Also add `-C <resolved cwd>`
to the auto-arm watcher's argv (secondary hardening, mirrors PR #1149)
and extend gates/test_watch_rearm_registry.py with a hermetic auto-arm
caller-exit-survival case.

## Why

basis: docs/issue-1154/proposals/watcher-autoarm-detached.md (approved;
merge of PR #1157 read via `git log --oneline -5`, see canonical below).
canonical: `git log --oneline -5` output this session, showing
`1b2359a Merge pull request #1157 from tokenmaxxxer/issue-1154/implementation`.
The auto-arm path's only structural difference from the `--rearm` path
was that it stayed alive inside the spawning caller's bounded call via
`_await_bounded()`; matching `_rearm_watcher_detached()`'s immediate-return
shape removes that difference.

## Upstream

Based on: docs/issue-1154/proposals/watcher-autoarm-detached.md

## What did not work

None.

## Open findings

None.

## Next steps

The issue's Acceptance check 2 (live delivery proof: a real
`spawn.py role spawn ...` bounded-background invocation observed alive
across 2+ watchdog ticks) was not exercised this session — spawning a
real role session is outside what this single-turn session ran. The
gate-test regression case above (canonical: fenced pytest transcript)
addresses Acceptance check 1 only. Follow-up: after this PR merges, a
live spawn from a bounded background call should be observed alive
across 2+ watchdog ticks to close out check 2.

## Resolution path

N/A — no open findings; the outstanding live-delivery observation above
is a follow-up verification step, not a blocking finding against this
record.
