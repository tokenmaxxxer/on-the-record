---
code_under_review:
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/test_decision_queue_stopgate.py
type: fix
breaking: false
canonical: python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py -q — result: 17 passed in 1.21s
verdict: pass
loop_state: landed
---

## Summary of work

Implemented the approved phase-1 proposal
(docs/issue-1021/proposals/2026-08-12-decision-queue-stopgate-bounded-reblock.md)
on `on-the-record/hooks/decision-queue-stopgate.sh`:

- Read `stop_hook_active` from the Stop payload at the top of the
  `CHECK` python body.
- The waiting-declaration branch (issues #600/#692) now short-circuits
  when `stop_hook_active` is true: it never emits `decision: "block"`
  in that case and falls through to the age-tier logic below, matching
  its own latch-fired fallthrough shape.
- Added a second persisted latch (`tier2_last_blocked_ids`, same JSON
  state file as the waiting-declaration latch, refactored the load/save
  helpers to a shared `_load_state`/`_save_state` pair) keyed on the
  sorted `(issue, pr)` identities of items with `age_hours >= 4`. The
  tier2 branch now blocks only when `stop_hook_active` is false AND the
  current tier2 identity set differs from the persisted one; otherwise
  it degrades to an `additionalContext` advisory naming the aged items,
  and persists the new identity set whenever a block does fire.
- Added the three acceptance-named test cases to
  `on-the-record/hooks/test_decision_queue_stopgate.py`
  (`t_stop_hook_active_never_blocks_tier2`,
  `t_same_tier2_snapshot_twice_second_stop_not_blocked`,
  `t_tier2_content_change_may_block_again`), extending `_run()` with a
  `stop_hook_active` parameter wired into the JSON stdin payload the
  same way `last_assistant_message` already is.

## Why

R001 (northpole req#4 autonomy without human intervention must not
degenerate into busy-loops). Per issue #1021: the hook ignored the
Stop-hook contract's `stop_hook_active` field and re-blocked on every
turn once a decision-queue item aged past 4h, producing an unbounded
token-burning loop since aged items are by definition waiting on the
operator.

## Upstream basis

docs/issue-1021/proposals/2026-08-12-decision-queue-stopgate-bounded-reblock.md

## What did not work

None.

## Open findings

None.

## Doc placement

- No env var, config key, new dependency, or migration was added by
  this change — no handbook update required.
- No public signature or wire format changed beyond the hook's
  internal `hookSpecificOutput`/`decision` JSON shape, which was
  already documented in the hook's own header comment; the header
  comment was left as-is since the tier boundaries themselves
  (1h/4h) are unchanged.

## Acceptance verification

canonical: python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py -q
checked: python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py -q — result: pass

```
17 passed in 1.21s
```
