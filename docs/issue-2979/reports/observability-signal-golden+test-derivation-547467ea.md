---
issue: 2979
role: observability-signal-golden+test-derivation-547467ea
author: observability-signal-golden+test-derivation-547467ea
skills: observability-signal-golden (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: watchdog.py
    sha: 005a3ec68abe9b202081bc1ba0ee7f3838defcbb
  - path: gates/spawn_coverage.py
    sha: 005a3ec68abe9b202081bc1ba0ee7f3838defcbb
skill-verdict: test-derivation — applied: invoked; used the Given-When-Then + decision-table routing to derive the 3 acceptance checks' test cases — see the module docstring of tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py (committed at 51dd7e65) for the full classification/routing/coverage table
other mounted skills: observability-signal-golden not-applicable — this is watchdog self-monitoring noise/signal logic (board-sweep PR classification, spawn-coverage delta reporting), not a service-rollup dashboard aggregating children's RED/USE metrics into Golden Signals
---

# issue-2979 — observability-signal-golden+test-derivation-547467ea record

## What was done

Build-now delivery (CORE_BUILD_NOW=1, spawner-authorized; two-phase
proposal round skipped per contract v3 s19a). Fixed the two watchdog
signals issue #2979 named, both landed in commit `51dd7e65`:

1. **board-sweep no longer enumerates non-subject PRs.** Added
   `watchdog._classify_narrowing_prs()` (watchdog.py), which replaces the
   inline PR-narrowing loop inside `_board_wide_sweep()`'s
   `delta_classification == "delta"` branch. It splits PRs whose branch
   fails to resolve into two buckets instead of one:
   - branch never matched `issue-<n>/<skill>` shape at all (non-subject,
     e.g. observed `fix/verify-plugins-actually-loaded`,
     `plan/state-gate-into-core`, or a deleted branch => `None`) —
     folded into a single `N건 non-subject PR ... 집계만` count line,
     every tick, never enumerated individually, not even on the first
     tick a given PR is seen.
   - branch matches the shape but the extracted issue is not currently a
     board subject (`f"issue-{n}" not in board_now`) — a genuine subject
     mapping loss (the #2379 corrupted-merge-base class). This case keeps
     the individual line + `recut-corrupted` remediation paragraph, still
     gated by the existing `_watchdog_note_unmappable_pr()` one-shot
     marker so an unchanged repo state doesn't repeat the line tick after
     tick (the marker is keyed by PR number, so a fresh PR against the
     same subject prints again — new information, not a repeat).
   - Reused `spawn.board(root)` (already called elsewhere in the same
     function, no new gh call) as the "is this issue a live board
     subject" source of truth.

2. **spawn-coverage reports only the delta.** Added
   `watchdog._watchdog_note_spawn_coverage_delta()`, which persists the
   previous tick's uncovered-issue set (via the existing
   `watchdog_noise_state.json` cross-tick state file) and returns only
   the issues newly added since last tick. `_board_wide_sweep()`'s
   `spawn-coverage` branch now prints `새로 커버되지 않음 [...]` for the
   delta only, instead of the full standing set every tick. The full
   `uncovered` count still feeds the anomaly `count` return value
   unchanged (severity/gating untouched — only the printed line changed).
   The persisted set is replaced wholesale each tick (not a sticky
   one-shot), so an issue that gets covered and later becomes uncovered
   again resurfaces as "new" — a real state change is a real signal, not
   noise to suppress permanently.

Neither change suppresses by issue-number cutoff, age threshold, or a
hardcoded ignore list — the board-sweep split is purely
board-subject-shape + board-membership, and the spawn-coverage split is
purely previous-tick-membership.

Updated the pre-existing `test/test_watchdog_heartbeat_noise.py`
(`TestPerPrMappingFailureSuppression`, renamed to
`TestPerPrNonSubjectAggregation`): its fixture branches
(`old-feature-branch`, `another-legacy-branch`) are non-subject-shaped,
so under the corrected behavior they must never print an individual
"subject 매핑 실패" line, on any tick — the old assertions encoded exactly
the enumeration behavior issue #2979 reports as the defect. Added
`tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py` with
the 3 acceptance checks' test cases, decision-table derivation documented
in the file's module docstring —
derived: `python3 -m pytest tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py -q` — result: 12 passed.

Acceptance requirement met — checked: `python3 -m pytest tests/ -k board_sweep_non_subject_aggregated -q` — result: 4 passed
Acceptance requirement met — checked: `python3 -m pytest tests/ -k board_sweep_subject_mapping_loss_reported -q` — result: 4 passed
Acceptance requirement met — checked: `python3 -m pytest tests/ -k spawn_coverage_reports_change -q` — result: 4 passed

Regression check — checked: `python3 -m pytest tests/ -q` — result: 137 passed, 1 failed
(the 1 failure is in `tests/test_spawn_gate_wiring.py`, case
`test_pre_existing_post_tool_use_commands_are_all_still_present`,
pre-existing on this branch before this session's changes — verified by
`git stash && python3 -m pytest tests/test_spawn_gate_wiring.py -q` before this
session's commit — result: 1 failed, 26 passed, same failure — unrelated to
hooks.json wiring, not touched by this issue's work).

Regression check — checked: `python3 -m pytest test/test_watchdog_heartbeat_noise.py -q` — result: 5 passed
Regression check — checked: `python3 -m pytest gates/test_spawn_on_pr.py -q` — result: 27 passed

## Why

The two prior code paths conflated "this PR/issue's branch or state
couldn't be resolved" with "this PR/issue is a board-relevant item worth
individual attention" — every unresolved PR got the same one-shot
individual-line treatment regardless of whether it was ever a board
subject, and spawn-coverage never distinguished "still uncovered" from
"newly uncovered" (no per-tick delta tracking existed for it at all,
unlike board-sweep's existing one-shot markers). The fix adds exactly one
new boolean check to each signal (board-membership for board-sweep,
previous-tick-set membership for spawn-coverage) rather than building a
new suppression mechanism — reusing `spawn.board()` and the existing
`watchdog_noise_state.json` cross-tick state file that
`_watchdog_note_unmappable_pr`/`_watchdog_note_gh_failure` already use,
so the fix is additive to an established pattern instead of a new one.

Alternative considered and rejected: keep the single one-shot marker for
ALL unresolved-branch PRs (today's shape) and just widen the suppression
window (e.g., only print a full board-wide non-subject census on some
larger N-tick cadence). Rejected because issue #2979's must-not clause
explicitly forbids suppression by a cutoff/threshold/list — a cadence
gate is exactly that kind of threshold, and it would still eventually
enumerate #1/#7/#26 line by line every N ticks with no way to distinguish
them from a genuine #2379-class mapping loss when it does fire.

## Upstream basis

- `watchdog.py`, `gates/spawn_coverage.py` at
  `005a3ec68abe9b202081bc1ba0ee7f3838defcbb` (branch HEAD before this
  session's edits) — the board-sweep PR-narrowing loop and the
  spawn-coverage print site this issue names.
- Issue #2979 — canonical: `gh issue view 2979` output (state: OPEN) —
  acceptance checks and must-not clauses quoted verbatim above and in the
  commit/PR.
- Issue #2196 (`e1f8bda9`) and #2402 (`3af9b41f`) — prior art for the
  one-shot noise-suppression marker pattern and the `recut-corrupted`
  remediation text reused here.

## Open findings

canonical: docs/issue-2979/reports/observability-signal-golden+test-derivation-547467ea/2026-09-01-hunt-delivery.md (before-landing warrant-hunter dispatch, stance 0, tier full/180s)

`closure_sweep._pr_index_all()` (gates/closure_sweep.py:233) dedups its
branch->PR index first-wins by branch string, so when two PR numbers
share one head branch (e.g. an original PR and a later `recut-corrupted`
retry reopened from the same subject branch), the losing PR number has no
entry in the resulting `number_to_branch` reverse map `_board_wide_sweep`
builds. `_classify_narrowing_prs` cannot distinguish that "unresolved
because of dedup collision" `None` from a "genuinely never
subject-shaped" `None` (a deleted/unrelated branch) — both currently fold
into the non-printed non-subject count. Reproduced by the hunter:
`_classify_narrowing_prs(root, {100, 200}, {200: "issue-42/architecture-abc"}, board_now={})`
gives PR #200 a mapping-loss line but silently counts PR #100 (branch
dropped by the dedup) into the never-printed aggregate.

Judged out of scope for this issue rather than fixed here, for two
reasons: (1) the issue's own field observation explicitly lists `None`
branches among the examples that must be aggregated, not enumerated
("branches like fix/verify-plugins-actually-loaded, plan/state-gate-into-core,
or None. These are simply not board subjects."), so the acceptance itself
sanctions treating an unresolved branch as non-subject by default; (2)
fixing it properly means giving `_pr_index_all()` a way to report
collided/dropped PR numbers, which is a change to shared lookup
infrastructure (gates/closure_sweep.py) consumed by closure-sweep,
spawn-on-pr, and spawn-on-approve as well — exactly the "lookup-failure
defects filed separately" class this issue's must-not clause says not to
fold in here.

Resolution path: file a follow-up issue against
`closure_sweep._pr_index_all()` to have it also return the set of PR
numbers whose branch was dropped by the first-wins dedup, so
`_classify_narrowing_prs` (or any other consumer) can route those PRs to
individual-report instead of silent aggregation.

## Next steps

None — loop_state is terminal (landed). Delivered as a PR against
`main` from this branch.
