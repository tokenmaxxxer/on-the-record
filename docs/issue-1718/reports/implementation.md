---
code_under_review:
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/test_decision_queue_stopgate.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #1718

## What was done

Executed the approved phase-1 proposal
(`docs/issue-1718/proposals/2026-08-17-decision-queue-stopgate-active-scope-fix.md`)
verbatim, per the human APPROVE issue-1718/implementation comment on the
issue:

1. `on-the-record/hooks/decision-queue-stopgate.sh` — added
   `if stop_hook_active: sys.exit(0)` immediately after `stop_hook_active`
   is computed (before role resolution and before `decision_queue` is
   even read), so a `stop_hook_active: true` turn is silent on every
   branch — waiting-declaration, tier1, tier2.
2. Same file — right after the existing `decision_queue` empty check,
   added a filter: build `_local_issues` from `flows["sessions"]` and
   `flows["ledger"]` entries' `"issue"` fields, drop any queue item whose
   `issue` is not in that set, re-check emptiness.
3. `on-the-record/hooks/test_decision_queue_stopgate.py` — added
   `spawn_record_issues` to `_run()` (defaults to a `sessions` entry per
   queue issue, so pre-existing tests are unaffected unless they opt in
   with an explicit value), replaced `t_stop_hook_active_never_blocks_tier2`
   with `t_stop_hook_active_emits_nothing_for_tier2` (asserts empty
   stdout, not the old advisory-degrade shape), and added
   `t_stop_hook_active_emits_nothing_for_tier1`,
   `t_stop_hook_active_emits_nothing_for_waiting_declaration`,
   `t_stop_hook_active_emits_nothing_even_with_primed_tier2_latch`,
   `t_unscoped_item_is_silently_skipped`, `t_ledger_only_item_still_surfaces`,
   `t_mixed_queue_surfaces_only_scoped_item`.

canonical: on-the-record/hooks/decision-queue-stopgate.sh and
on-the-record/hooks/test_decision_queue_stopgate.py (both read and
edited in full this session)

canonical: `python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py -v -p no:cacheprovider -o addopts=""` — result: 23 passed
```
on-the-record/hooks/test_decision_queue_stopgate.py::t_empty_queue_is_silent PASSED [  4%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_under_1h_item_is_silent PASSED [  8%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_1h_to_4h_item_gets_additional_context PASSED [ 13%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_4h_plus_item_blocks PASSED [ 17%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_mixed_tiers_reports_only_tier2_block PASSED [ 21%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_orchestrate_off_is_silent PASSED [ 26%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_role_session_is_silent PASSED [ 30%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_unset_spoof_with_bound_role_stays_silent PASSED [ 34%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_no_snapshot_falls_back_to_live_env PASSED [ 39%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_waiting_declaration_over_fresh_queue_blocks PASSED [ 43%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_queue_relay_that_closes_turn_is_not_blocked_by_new_branch PASSED [ 47%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_consecutive_waiting_declaration_second_stop_not_blocked PASSED [ 52%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_waiting_declaration_block_reason_names_queue_items_and_escape PASSED [ 56%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_latch_resets_after_non_waiting_stop_catches_later_stall PASSED [ 60%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_stop_hook_active_emits_nothing_for_tier2 PASSED [ 65%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_same_tier2_snapshot_twice_second_stop_not_blocked PASSED [ 69%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_tier2_content_change_may_block_again PASSED [ 73%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_stop_hook_active_emits_nothing_for_tier1 PASSED [ 78%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_stop_hook_active_emits_nothing_for_waiting_declaration PASSED [ 82%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_stop_hook_active_emits_nothing_even_with_primed_tier2_latch PASSED [ 86%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_unscoped_item_is_silently_skipped PASSED [ 91%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_ledger_only_item_still_surfaces PASSED [ 95%]
on-the-record/hooks/test_decision_queue_stopgate.py::t_mixed_queue_surfaces_only_scoped_item PASSED [100%]

23 passed in 2.10s
```
No SKIPPED lines in this run.

Both issue-named acceptance checks are covered directly:
`t_stop_hook_active_emits_nothing_for_tier1/tier2/waiting_declaration/primed_latch`
for the first ("emits nothing at all ... regardless of queue age"), and
`t_unscoped_item_is_silently_skipped`/`t_ledger_only_item_still_surfaces`/
`t_mixed_queue_surfaces_only_scoped_item` for the second (checkout-scope
filter).

## Why

`Stop` `additionalContext` is inject-and-resume in this harness, not
passive, so any emission on an already-forced (`stop_hook_active: true`)
turn re-triggers another Stop and loops until the harness's
consecutive-block cap ends the turn — observed 9 forced turns per reply.
The prior fix (issue #1021) wired `stop_hook_active` into only two of
the hook's branches, leaving the tier1 branch and tier2's own
advisory-degrade path (the branch actually implicated by the transcript
evidence) still emitting. Separately, `decision_queue` items surfaced
regardless of whether this checkout ever spawned the underlying work,
because `gates/flows.py`'s `_own_item()` cannot deny ownership when its
local roster has no observation of an item — a deliberate default for a
different consumer (#1035) that this hook was riding without an
independent filter of its own.

upstream: docs/issue-1718/proposals/2026-08-17-decision-queue-stopgate-active-scope-fix.md

## What did not work

Attempted the full repo-wide `slow` test tier
(`.on-the-record/test-tiers.json`'s `slow` command,
`python3 -m pytest -q -m slow`), since this diff matches its declared
`trigger_change_classes` (`on-the-record/hooks/*.sh`,
`on-the-record/hooks/test_*.py`). Expected: completion within a few
minutes. Actual: the run (real subprocess-spawn and real
git-clone/checkout lifecycle tests across the whole repo, unrelated to
this issue's own scope) was still running after 13 minutes with zero
output; stopped it rather than block this single-shot turn indefinitely
on unrelated repo-wide coverage.
derived: `ps -o pid,etime -p 49599` → `13:10` elapsed, no stdout yet, immediately before stopping the task.
This is a tiering-gap observation about the `slow` tier's own budget (it
declares no `budget_seconds`, unlike `fast`'s 300s default). The
`canonical:`-cited 23-passed run above, against the file the issue names
in both acceptance checks, is unaffected by this gap.

## Open findings

None.

## Doc placement

- No env var, no dependency, no config key, no migration introduced —
  nothing routes to a handbook.
- No library-or-format choice over a named alternative and no public
  signature/wire-format change beyond the hook's own stdout shape — the
  proposal's `## Rationale` already recorded the two alternatives
  considered and rejected (filtering in `gates/flows.py` instead of the
  hook; leaving tier1 unpatched); nothing further belongs under
  docs/issue-1718/decisions/.
- No benchmark/investigation numbers produced beyond the test-tier
  observation captured under `## What did not work` above.

## loop_state

landed
