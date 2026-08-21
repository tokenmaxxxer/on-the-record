---
code_under_review:
  - spawn.py
  - tests/test_watchdog_freshness.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implementing the approved proposal
(`docs/issue-1755/proposals/watchdog-freshness-alert-dedup.md`,
approved via `APPROVE issue-1755/implementation`): add a
`state_path` parameter to `watchdog_freshness_check` that dedups the
freshness alert message per HEAD transition using a small JSON state
file, and wire the CLI `watchdog` role callsite to use it.

## Why

basis: docs/issue-1755/proposals/watchdog-freshness-alert-dedup.md

The watchdog re-prints its code-freshness alert every ~2min tick
(separate CLI subprocess invocations) until the process restarts,
because there is no persistence across ticks. State-file dedup (same
pattern as `WATCHDOG_LOCK_PATH`) survives across the per-tick
subprocess calls and reuses an established persistence pattern.

## What did not work

None.

## Open findings

None.

## Doc placement ladder

- No env var, config key, new dependency, migration, or setup step
  introduced — nothing to place in a handbook.
- No public-signature/wire-format change beyond the additive
  `watchdog_freshness_check(state_path=...)` parameter already recorded
  in the proposal — no separate decision doc needed.
- No benchmark/investigation numbers produced.

## Test run (fast tier)

canonical: pytest output pasted below, executed this session
acceptance: python3 -m pytest -q -m "not slow" tests/test_watchdog_freshness.py — result: pass

```
..........                                                               [100%]
10 passed in 0.85s
```

## loop_state

landed
