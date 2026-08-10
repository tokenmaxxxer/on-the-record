---
code_under_review:
  - spawn.py
  - test_spawn.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Extended `_ABANDONED_WORK_OUTCOMES` (spawn.py:2648) from
`("uncommitted-work", "failed-no-commit")` to include `"silent-failure"`, so
a causeless silent-failure now auto-continues through the existing
`_self_trigger_respawn()` -> `_respawn_or_cap()` path, bounded by
`RESPAWN_MAX_ATTEMPTS`. `_self_trigger_respawn()` now passes a distinct
`trigger` string — `"self-triggered-causeless"` for `silent-failure`,
unchanged `"self-triggered-abandoned"` for the two prior outcomes — so
`_respawn_or_cap()`'s log line and `_post_crash_comment()`'s body keep the
two failure shapes distinguishable at the cap. Updated the docstring at
spawn.py:2651-2666 to state that only `refused`/`waiting-on-human` stay
excluded now, and that a `silent-failure` reaching this function has
already passed through `fail_closed_downgrade()`'s upgrade/downgrade check.

Extended `test_spawn.py::SelfTriggeredRespawn`: `test_fires_on_silent_failure_with_distinct_trigger`
asserts `silent-failure` calls `_respawn_or_cap()` with trigger
`"self-triggered-causeless"`; `test_does_not_fire_on_legitimate_stops` had
`silent-failure` removed from its non-firing list (it now fires) and keeps
`refused`/`waiting-on-human` asserting no call. `Classify` needed no new
cases — it already names `silent-failure` correctly (test_spawn.py:970-973);
this change only alters what happens after the name is assigned, per the
proposal's Out-of-scope section.

## Why

Implements the approved phase-1 proposal
(docs/issue-675/proposals/2026-08-10-causeless-silent-failure-auto-continue.md)
for issue #675: a spawned session that ends its turn early with no PR, no
refusal record, and no waiting-on-human marker previously required a human
to notice and manually respawn it. `refused` and `waiting-on-human` remain
legitimate stops and are untouched.

## Upstream

Based on: docs/issue-675/proposals/2026-08-10-causeless-silent-failure-auto-continue.md

## What did not work

None.

## Doc placement

- No new env var, config key, dependency, or migration introduced — no
  handbook update required.
- No public signature or wire-format change, and the chosen approach
  (extend `_ABANDONED_WORK_OUTCOMES` in place, add a distinguishing
  `trigger` string) was already recorded with its rejected alternatives in
  the phase-1 proposal's `## Rationale` — no separate
  docs/issue-675/decisions/ entry needed.
- No benchmark/investigation numbers produced.

## How it was verified

derived: `python3 -m pytest test_spawn.py -k "Classify or SelfTriggeredRespawn" -q`
```
15 passed, 345 deselected in 0.34s
```

## Open findings

None.
