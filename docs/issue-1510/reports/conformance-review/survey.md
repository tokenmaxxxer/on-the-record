---
subject: issue-1510
role: conformance-review
kind: survey
loop_state: current
---

# Current-state survey: issue-1510/implementation delivery (PR #1513)

## Board condition check
canonical: `gh pr list --search "1510" --state all`, run this session:
```
1513	issue-1510: widen poll-heartbeat cadence 60s -> 120s with scaled staleness constants	issue-1510/implementation	OPEN
```
canonical: `gh pr view 1513 --json state`, run this session — state:
OPEN, not yet merged to main.
canonical: `git show origin/main:docs/issue-1510 2>&1`, run this
session — no docs/issue-1510 tree exists on main yet; no prior
conformance-review record exists anywhere for this issue.
Spawn trigger: spawn_on_pr.py fired on PR #1513's creation, per this
session's invocation ("PR 생성 시 자동 스폰됨").

## Target artifact
- on-the-record/monitors/poll-heartbeat.sh (1-line default-value edit)
- on-the-record/hooks/directive.sh (1-line default-value edit)
- spawn.py (1-line default-value edit)
- tests/test_heartbeat_cadence.py (new file, 32 lines)
- tests/test_spawn.py (new class NoConcurrencyCap, 27 lines added)

canonical: `gh pr view 1513 --json files`, run this session — file list
and add/delete counts match the five entries above plus three
docs/issue-1510/** files (proposal, implementation record, survey) not
under this role's review scope (own-role output, not build artifact).

## Spec
issue #1510 body: 4 numbered Requirements, 3 Acceptance items, one
"Affected constants" inventory naming exact file:line locations for
each of the three constants. canonical: `gh issue view 1510`, read this
session.

## Requirement list (phase-1 extraction, verdicts deferred to phase 2)
1. Change the three constants together in one PR.
2. Tick-cadence coupling test: MONITOR_LIVENESS_STALE_SECONDS default
   >= 3x POLL_HEARTBEAT_SLEEP_SECONDS default, asserted by a test.
3. No-concurrency-cap regression test: N stub spawns admitted
   concurrently, never refused for count reasons; a spec sentence
   records the WHY (operator decision 2026-08-15) beside the test
   reference; RESPAWN_MAX_ATTEMPTS family stays explicitly out of
   scope.
4. No tick-count dependency introduced (#1497 epoch-seconds stamps,
   #1508 ordering) — a non-regression requirement.
- Acceptance 1: a heartbeat-cadence test named
  test_defaults_scaled_together in tests/test_heartbeat_cadence.py,
  executed-unit provenance — to be run live in phase 2.
- Acceptance 2: a no-concurrency-cap test named test_no_concurrency_cap
  (or equivalent) in tests/test_spawn.py, empty-state (zero running
  sessions) case covered, executed-unit provenance — to be run live in
  phase 2.
- Acceptance 3: MONITOR_ALIVE_TOUCH_CADENCE_SECONDS == 120 with the
  existing GC assert (MONITOR_ALIVE_STALE_THRESHOLD_SECONDS >
  MONITOR_ALIVE_TOUCH_CADENCE_SECONDS) unbroken — to be re-checked live
  in phase 2.

This is the full requirement list; no sampling derivation is needed —
the change is three single-line constant edits plus two new/extended
test files, small enough for 100% inspection rather than a sampled
subset.

## Scout-directive skip record
Skipped. Reason: this task is a literal spec-vs-build conformance
check against issue #1510's own numbered Requirements and Acceptance
items — file:line locations, a numeric ratio assertion, and a
regression-test-exists check — leaving no product/design decision open
for this role to scout a field on; the pure-bugfix/no-design-decision
skip condition applies.
