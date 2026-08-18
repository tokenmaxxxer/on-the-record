---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
type: fix
breaking: false
verdict: accept
loop_state: committing
---

# Implementation record — issue #1734

## What was done

Implemented the approved phase-1 proposal
`docs/issue-1734/proposals/2026-08-18-content-derived-fixed-line-keys.md`
(basis: phase-1 PR #1735, approved via the exact-string issue comment
`APPROVE issue-1734/implementation`) per its plan section.

Rebased `issue-1734/implementation` onto `origin/main` first, per the
invoking prompt — issue #1732 (merge commit `3e3a95e0`) had landed on
main and removed the adjacent `healthy = sum(...)` "monitoring active"
heartbeat block (`f2bde8c0`) that the proposal's Constraints section
named as the second key call site to update. The rebase (`git rebase
origin/main`) was clean, no conflicts: #1732 touches the `to_emit`-empty/
1800s-bound branch (poll-heartbeat.sh:326-341 pre-rebase), disjoint from
this issue's keying loop (poll-heartbeat.sh:244-291).
canonical: `git show origin/main:on-the-record/monitors/poll-heartbeat.sh | grep -n '__fixed__'` (this session, executed live) — output: `281:        key = "__fixed__"` only; the old `healthy` filter line naming the same key is already gone from main.

`on-the-record/monitors/poll-heartbeat.sh` changes:
- Added `import hashlib` to the heredoc's import block (alongside
  `json`/`os`/`re`/`sys`).
- Added `FIXED_TAG_RE = re.compile(r"^\[([^\]]+)\]\s*([^:]+):")` next to
  `TAG_RE`/`ENTRY_RE`/`BULLET_RE`/`BOARD_SWEEP_LOCK_SKIP_RE`, with a
  comment citing issue #1734 and explaining the content-derived-key
  rationale.
- Replaced the `else: key = "__fixed__"` branch with: compute
  `line_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()[:12]`;
  match `FIXED_TAG_RE`; if it matches, `key =
  f"fixed:{fm.group(1)}:{fm.group(2).strip()}:{line_hash}"`; otherwise
  `key = f"fixed:hash:{line_hash}"`. The same-tick collision-ordinal
  block below it (`while f"{key}~{n}" in curr: ...`) is unchanged and
  now reaches only genuinely byte-identical same-tick lines.
- The proposal's Constraints item to update `poll-heartbeat.sh:333`'s
  `healthy = ...` filter turned out moot post-rebase: #1732 already
  deleted that whole branch of the emit block, and the rebase carried
  that deletion forward.
  canonical: `grep -n '__fixed__' on-the-record/monitors/poll-heartbeat.sh` (this session, executed live, same output pasted under Acceptance check 3 below) — no remaining `__fixed__`-prefix filter anywhere in the file.
- `bash -n on-the-record/monitors/poll-heartbeat.sh` re-verified clean
  after every edit — the heredoc's documented bash-3.2
  apostrophe-count-parity landmine (survey.md) tripped once during
  drafting; see `## What did not work`.

`on-the-record/monitors/test_poll_heartbeat.py` changes: added two
tests near the existing `t_board_sweep_lock_skip_treated_as_no_change`
delta-suppression test, using the existing `_run_tick(checkout, home,
report)` two-tick harness, matching the proposal's test plan:
- `t_unkeyed_line_insertion_suppresses_unchanged_lines_below` (Acceptance
  check 1): tick 1 sends two unkeyed lines (a `[spawn-on-pr]`-tagged line
  and a freeform line); tick 2 inserts one new unkeyed line at the top,
  the original two byte-identical. Asserts tick 2's stdout, stripped,
  equals exactly the inserted line.
- `t_unkeyed_line_content_change_still_emits` (Acceptance check 2): tick
  1 and tick 2 send the same `[spawn-on-pr]`-tagged line with different
  trailing content. Asserts tick 2's full changed line text appears in
  stdout.

## Why

Per the issue: unkeyed lines (matching none of `TAG_RE`/`ENTRY_RE`/
`BULLET_RE`) were keyed by appearance-order ordinal (a single fixed
placeholder key literal plus `~N`), so inserting or dropping one such
line shifted every following line onto a different ordinal; the delta
comparison then compared each shifted line against a *different* line's
previous text and classified unchanged content as changed, re-emitting
it and waking the orchestration session for a full model turn on every
tick where the unkeyed-line block's membership changed even slightly.

## Basis

docs/issue-1734/proposals/2026-08-18-content-derived-fixed-line-keys.md,
approved via phase-1 PR #1735 and the issue comment
`APPROVE issue-1734/implementation`.

## Acceptance

Check 1 — two consecutive ticks whose unkeyed-line block differs only by
one line being inserted at the top emit only that inserted line:
canonical: python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -v -k t_unkeyed_line_insertion_suppresses_unchanged_lines_below -o addopts="" — result: PASS
```
on-the-record/monitors/test_poll_heartbeat.py::t_unkeyed_line_insertion_suppresses_unchanged_lines_below PASSED [100%]
1 passed in 0.65s
```

Check 2 — a line whose own content changes between ticks is still
emitted:
canonical: python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -v -k t_unkeyed_line_content_change_still_emits -o addopts="" — result: PASS
```
on-the-record/monitors/test_poll_heartbeat.py::t_unkeyed_line_content_change_still_emits PASSED [100%]
1 passed in 0.63s
```

Check 3 — `grep -n '__fixed__' monitors/poll-heartbeat.sh` shows no
appearance-order ordinal keying for the unkeyed-line class:
canonical: `grep -n '__fixed__' on-the-record/monitors/poll-heartbeat.sh; echo "exit:$?"` (this session, executed live) — output below.
```
$ grep -n '__fixed__' on-the-record/monitors/poll-heartbeat.sh; echo "exit:$?"
exit:1
```

Check 4 — the existing delta-suppression and patrol suites, run together:
canonical: python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py gates/test_poll_heartbeat_delta.py gates/test_poll_heartbeat_patrol.py -v -o addopts="" — result: PASS (37 passed, 1 pre-existing failure out of scope per the issue's own carve-out, pasted below)
```
============================= test session starts ==============================
platform darwin -- Python 3.11.8, pytest-8.4.1, pluggy-1.6.0
collected 38 items

on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_arms_watchdog_when_due PASSED [  2%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_skips_watchdog_when_not_due PASSED [  5%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_respects_kill_switch PASSED [  7%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_respects_monitor_only_kill_switch PASSED [ 10%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_orchestrate_off_alone_still_stops_monitor PASSED [ 13%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_surfaces_empty_roster_report PASSED [ 15%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_surfaces_induced_dead_poller PASSED [ 18%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_refuses_to_arm_on_non_git_root PASSED [ 21%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_skips_attachment_on_non_board_repo PASSED [ 23%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_attaches_on_board_repo PASSED [ 26%]
on-the-record/monitors/test_poll_heartbeat.py::t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior FAILED [ 28%]
on-the-record/monitors/test_poll_heartbeat.py::t_returned_pr_unchanged_set_produces_no_output_on_due_tick PASSED [ 31%]
on-the-record/monitors/test_poll_heartbeat.py::t_returned_pr_new_item_emits_on_due_tick PASSED [ 34%]
on-the-record/monitors/test_poll_heartbeat.py::t_board_sweep_lock_skip_treated_as_no_change PASSED [ 36%]
on-the-record/monitors/test_poll_heartbeat.py::t_unkeyed_line_insertion_suppresses_unchanged_lines_below PASSED [ 39%]
on-the-record/monitors/test_poll_heartbeat.py::t_unkeyed_line_content_change_still_emits PASSED [ 42%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_bound_with_no_returned_pr_emits_nothing PASSED [ 44%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_bound_with_returned_pr_emits_only_those_lines PASSED [ 47%]
on-the-record/monitors/test_poll_heartbeat.py::t_patrol_quiet_tick_with_roles_emits_no_summary_line PASSED [ 50%]
on-the-record/monitors/test_poll_heartbeat.py::t_patrol_promotion_tick_still_prints_summary_line PASSED [ 52%]
on-the-record/monitors/test_poll_heartbeat.py::t_patrol_crashed_role_tick_still_prints_summary_line PASSED [ 55%]
on-the-record/monitors/test_poll_heartbeat.py::t_patrol_kill_switch_still_prints_disabled_line_only PASSED [ 57%]
gates/test_poll_heartbeat_delta.py::t_identical_second_tick_suppressed PASSED [ 60%]
gates/test_poll_heartbeat_delta.py::t_changed_tick_emits PASSED          [ 63%]
gates/test_poll_heartbeat_delta.py::t_change_after_suppression_emits PASSED [ 65%]
gates/test_poll_heartbeat_delta.py::t_fresh_state_first_tick_always_emits PASSED [ 68%]
gates/test_poll_heartbeat_delta.py::t_only_changed_line_emitted_not_full_report PASSED [ 71%]
gates/test_poll_heartbeat_delta.py::t_dead_session_line_always_emits_even_unchanged PASSED [ 73%]
gates/test_poll_heartbeat_delta.py::t_non_due_tick_produces_no_output PASSED [ 76%]
gates/test_poll_heartbeat_delta.py::t_watchdog_anomaly_bullets_survive_round_trip PASSED [ 78%]
gates/test_poll_heartbeat_delta.py::t_returned_pr_line_no_longer_always_emits_when_unchanged PASSED [ 81%]
gates/test_poll_heartbeat_delta.py::t_anomaly_rc_produces_no_crash_label PASSED [ 84%]
gates/test_poll_heartbeat_delta.py::t_signal_death_rc_produces_crash_label PASSED [ 86%]
gates/test_poll_heartbeat_delta.py::t_reserved_sentinel_rc_produces_crash_label PASSED [ 89%]
gates/test_poll_heartbeat_delta.py::t_clean_rc_produces_neither_label PASSED [ 92%]
gates/test_poll_heartbeat_patrol.py::t_patrol_invoked_only_on_nth_tick PASSED [ 94%]
gates/test_poll_heartbeat_patrol.py::t_kill_switch_suppresses_and_traces PASSED [ 97%]
gates/test_poll_heartbeat_patrol.py::t_no_board_role_zero_side_effects PASSED [100%]

=================================== FAILURES ===================================
_______ t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior ________
AssertionError: poll-heartbeat.sh should exit 0: .../on-the-record/monitors/poll-heartbeat.sh: line 163: flock: command not found
  .../poll-heartbeat.sh: line 138: .../home/.claude/tokenmaxxxer/poll-watchdog.log: No such file or directory
  .../poll-heartbeat.sh: line 163: flock: command not found (x4 more)
  .../poll-heartbeat.sh: line 435: POLL_HEARTBEAT_PATROL_ROLES[@]: unbound variable
=========================== short test summary info ============================
FAILED on-the-record/monitors/test_poll_heartbeat.py::t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior
======================== 1 failed, 37 passed in 17.74s =========================
```

The one failure above is the pre-existing macOS stock-bash gap (no
`flock` binary) that the issue's own Acceptance provenance carves out of
scope, on condition of showing it fails the same way on `main`.
canonical: git worktree add /tmp/otr-main-check origin/main && python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py::t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior gates/test_poll_heartbeat_delta.py gates/test_poll_heartbeat_patrol.py -v -o addopts="" — result: PASS (same failure signature on main, pasted below)
```
FAILED on-the-record/monitors/test_poll_heartbeat.py::t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior
  AssertionError: poll-heartbeat.sh should exit 0: .../poll-heartbeat.sh: line 163: flock: command not found
  ... line 419: POLL_HEARTBEAT_PATROL_ROLES[@]: unbound variable
1 failed, 16 passed in 9.72s
```
Only the source line number differs (435 vs 419, unrelated line-count
drift between the two trees) — the stderr shape otherwise matches the
branch run above. Worktree removed afterward (`git worktree remove
/tmp/otr-main-check --force`).

Test-tier note (issue #1518, observe-only): `.on-the-record/test-tiers.json`
exists in this repo, but the issue's own Acceptance section pins the
exact three-suite `pytest` invocation shown above rather than the
repo-wide `fast`/`slow` tiers; that targeted command was run in place of
the tiered command, per the Acceptance section's own provenance
requirement, not as a silent substitute for it.

## What did not work

- Expected: the first `FIXED_TAG_RE` explanatory comment (with the old
  key literal spelled out in prose and an odd net apostrophe count added
  to the heredoc) to satisfy a syntax check. Actual: `bash -n` reported
  `line 427: unexpected EOF while looking for matching '''` — the file's
  own documented bash-3.2 heredoc apostrophe-parity landmine
  (survey.md).
  canonical: bash -n on-the-record/monitors/poll-heartbeat.sh — result: FAIL (first draft) — output: `line 427: unexpected EOF while looking for matching '''`, `line 436: syntax error: unexpected end of file`.
  Reworded the comment to drop the literal old-key string (also needed
  for Acceptance check 3's grep to show zero output) and to add zero net
  apostrophes; the re-run in Acceptance check 3 above shows the fixed
  state.

## Open findings

None.

## Next steps

Commit this record together with the code and test changes, push the
branch, and open the phase-2 delivery PR carrying `Closes #1734` with
the Acceptance section above reflected in the PR body.

## Resolution path

Not applicable — no open finding.

## loop_state

`committing` — code, tests, and this record are finished and about to be
committed and pushed as the phase-2 delivery PR carrying `Closes #1734`.
