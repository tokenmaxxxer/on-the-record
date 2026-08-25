---
issue: 2312
role: implementation
loop_state: landed
upstream:
  - path: (none — build-now bypass, CORE_BUILD_NOW=1; no proposal round)
    sha:
code_under_review:
  - watchdog.py
type: fix
breaking: none
verdict: pass
---

# issue-2312 — implementation record

## What was done

Changed `roster_watchdog()` in watchdog.py (dead-entry branch, around
line 1547 onward) so a dead active.json entry's terminal-state print
line stops re-appearing on every poll tick forever:

- Added a pid-scoped `state[f"{key}:{pid}:reported_terminal"]` flag that
  gates the dead-entry `[poll-report] {key}: {label} — ...` print, so it
  fires exactly once per dead-entry instance. The flag is pid-scoped
  (not just key-scoped) so a respawned session that later reuses the
  same roster key is reported again — that is a new instance, not a
  repeat of the old one.
- On the first print, if the entry has `expects_pr` falsy and `issue` is
  None (nothing left to watch — the issue's own "safe immediately"
  criterion), the entry is retired right away via `roster_remove(key)`.
  Otherwise the entry stays in the roster (still dead, still watchable
  for PR-ready resume) with the print suppressed on every later tick.
- Persist `state` immediately after setting the flag
  (`_sp._watchdog_state_save(state)`), instead of relying solely on the
  single save call at the very end of `roster_watchdog()`. This closes a
  gap surfaced by the before-landing warrant hunt for this change
  (stance 0, "assume the gate just touched is bypassable"): with only
  the end-of-tick save, any *other* roster entry raising later in the
  same tick (e.g. a `diagnose_health` failure) silently discarded the
  just-set flag before it ever reached disk, so the print went back to
  reappearing every tick on the very next poll — the exact defect this
  issue exists to close. The early save makes this entry's flag survive
  regardless of what happens to any other entry processed later in the
  same tick.

derived: python3 -m pytest tests/test_poll_watchdog_log.py -q, and the
two `spawn.roster_watchdog()` live-tick scripts quoted verbatim under
## Acceptance evidence below.

## Why

The existing code already had the right shape for a one-time cache
(`state[f"{key}:dead_report"]`, gated by a 15-minute
`ledger_check_and_stamp` TTL that throttles the expensive
`diagnose_health()` recompute) — but the `print()` call itself sat
outside that gate by design (the ledger TTL governs recheck cost, not
report cadence), so every tick re-printed the cached terminal state
unconditionally forever. Reusing the same `state` dict for a
`reported_terminal` flag, gated purely on "has this dead instance's
terminal state already been printed", is the smallest change matching
the issue's own Ask ("report a terminal state once, then either remove
the entry ... or mark reported_terminal and skip the print thereafter")
without touching the unrelated TTL/recheck-cost mechanism.

Pid-scoping (rather than clearing the flag on respawn) was chosen
because nothing in `roster_register()`/`_respawn_or_cap()` currently
clears any per-key `state` entries on respawn — adding a clear-on-
respawn hook would touch code outside this defect's locus. Scoping the
flag by pid instead needs no new integration point: a respawn always
gets a new pid, so the flag naturally does not carry over to the new
instance.

## What did not work

None.

## Upstream basis

None — build-now bypass (`CORE_BUILD_NOW=1`), no proposal file for this
delivery. Basis is the issue #2312 body itself (consumer report, Ask,
and Acceptance).

## Open findings

One before-landing warrant-hunter finding (stance 0), written to
docs/issue-2312/reports/implementation/2026-08-25-hunt-dead-active-json-retire.md
(committed together with this record): an unrelated roster entry's
unhandled exception in the same tick discarded the just-set
`reported_terminal` flag, because `state` was only persisted once, at
the very end of `roster_watchdog()`.

Resolution path: this same commit adds the early
`_sp._watchdog_state_save(state)` call described under ## What was done
above. Re-running the hunter's own repro shape (a two-entry roster, one
entry's `diagnose_health` raising every tick) against the patched code
shows the flag now survives — see ## Acceptance evidence below for the
raw output. No findings remain open.

derived: the repro re-run quoted verbatim under ## Acceptance evidence.

## Next steps

None — this record's loop_state is now terminal (`landed`).

## Acceptance evidence

acceptance: python3 -m pytest tests/test_poll_watchdog_log.py -q — result:
```
....                                                                     [100%]
4 passed in 14.51s
```
This gate is unaffected by the change above (no dead roster entries are
involved in that suite), which is the empty-state / byte-identical-
output requirement from the issue's Acceptance section.

acceptance: python3 -m pytest tests/test_spawn_observation_recovery.py tests/test_spawn_board_flows.py tests/test_standing_red_watch.py tests/test_watch_hardening.py tests/test_spawn_pipeline.py -q — result:
```
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
2 failed, 418 passed, 4 xfailed, 1 xpassed in 632.14s (0:10:32)
```
Both failures reproduce identically with this commit's watchdog.py
change `git stash`-ed out (same two assertions, same diffs), so they
pre-date and are independent of this change:
```
$ git stash && python3 -m pytest tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch -q
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
2 failed in 6.98s
$ git stash pop
```

acceptance: python3 -u a live-tick script driving the real spawn.roster_watchdog() three times over a dead entry with nothing to watch (expects_pr False, issue None) — result:
```
--- tick 1 stdout ---
[watchdog] board-sweep: work — 로스터 타깃 레포지만 보드 아님(docs/specs/approvers.md 없음), 건너뜀
[poll-report] issue-9999/implementation: COMPLETED — completion, not a health diagnosis
이상 신호 없음

--- tick 2 stdout ---
돌고 있는 역할 세션 없음
이상 신호 없음

--- tick 3 stdout ---
돌고 있는 역할 세션 없음
이상 신호 없음

COMPLETED occurrences across 3 ticks: 1
active.json after 3 ticks: {}
```
The terminal-state line prints on tick 1 only, and the entry is retired
(removed) from active.json by tick 2 — matching the issue's Acceptance
provenance requirement (three real ticks, one print, entry
removed/marked).

acceptance: python3 -u the same live-tick script over a dead entry with something to watch (issue 8888, expects_pr True) — result:
```
--- tick 1 stdout ---
[reconcile] issue-8888/implementation: divergence — pr-expected-missing: role=implementation branch=work: expects_pr=True pr_number=None session_verdict='normal' policy=RESPAWN_IDENTICAL -> respawn
[poll-report] issue-8888/implementation: COMPLETED — completion, not a health diagnosis

--- tick 2 stdout ---
이상 신호 없음

--- tick 3 stdout ---
이상 신호 없음

COMPLETED occurrences across 3 ticks: 1
active.json after 3 ticks (entry retained, not removed): dict_keys(['issue-8888/implementation'])
```
Same one-print behavior, but the entry stays in active.json (not
retired) because it still has an issue/PR that may need tracking.

acceptance: python3 -u the before-landing hunter's own repro shape (two dead roster entries, one entry's diagnose_health raising RuntimeError on every tick) re-run against this commit's patched watchdog.py — result:
```
tick 1: crashed=True 'issue-1/a: COMPLETED' printed 1x state_on_disk_has_flag=True
tick 2: crashed=True 'issue-1/a: COMPLETED' printed 0x state_on_disk_has_flag=True
tick 3: crashed=True 'issue-1/a: COMPLETED' printed 0x state_on_disk_has_flag=True
tick 4: crashed=True 'issue-1/a: COMPLETED' printed 0x state_on_disk_has_flag=True
```
Even though `issue-2/b`'s diagnose_health raises on every one of the
four ticks (the shape that defeated the flag before the early save was
added), `issue-1/a`'s terminal print fires on tick 1 only and the flag
is durable on disk from tick 1 onward — the finding under ## Open
findings above no longer reproduces.

skill-verdict: implementation-blueprint — not-applicable: single-file, ~25-line fix inside one existing function, no new module/structure decision.
skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion metric crossed, no accessor chain, no import-direction change.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern decision involved, a state-flag plus early-return only.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no new data structure/algorithm/cache tradeoff introduced (reused the existing state dict/JSON-file mechanism).
other mounted skills: not triggered
