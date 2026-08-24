---
issue: 2180
role: implementation
loop_state: landed
upstream:
  - path: on-the-record/monitors/poll-heartbeat.sh
    sha: same-commit
  - path: on-the-record/monitors/test_poll_heartbeat.py
    sha: same-commit
code_under_review: same-commit
type: fix
breaking: false
verdict: pass
---

# issue-2180 — implementation record

## What was done

Build-now bypass (CORE_BUILD_NOW=1): delivered directly on
issue-2180/implementation, no separate phase-1 proposal round.

Changed `on-the-record/monitors/poll-heartbeat.sh`'s embedded delta-filter
(the Python heredoc that turns `roster_watchdog()`'s raw stdout into each
tick's Monitor-visible output). canonical: on-the-record/monitors/poll-heartbeat.sh
diff in this commit, the `returned-pr:` branch inside the `for key in
order:` loop and the `else:` bound branch right after it.

1. A `returned-pr:` entry whose issue number has never been surfaced
   before (tracked in a persisted `surfaced_returned_pr_issues` set,
   keyed by the bare `#<issue>` token rather than the phase-qualified
   diff key) now also gets an extra line under a different bracket tag,
   `[new-returned-pr]`, prepended ahead of everything else that tick
   would print (`new_pr_markers + to_emit`). The original `[returned-pr]`
   line is still emitted too, unchanged, immediately after it. Keying by
   issue number rather than the diff key was a fix to a before-landing
   warrant-hunt finding — see Open findings.
   canonical: acceptance run below, `ok  t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line`
   and `ok  t_returned_pr_phase_transition_does_not_refire_new_marker`.
2. The #1732 30-minute bound branch now writes one collapsed line
   instead of repeating every currently-open `[returned-pr]` line:
   `[returned-pr-pending] N PR(s) still awaiting review: #A, #B, ...`.
   canonical: acceptance run below, `ok  t_heartbeat_bound_with_returned_pr_emits_only_those_lines`.

Also updated `on-the-record/monitors/test_poll_heartbeat.py`:
- Rewrote `t_heartbeat_bound_with_returned_pr_emits_only_those_lines`
  (the #1732 pin) for the new collapsed-line shape.
- Added `t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line`
  (acceptance check 1).
- Added `t_returned_pr_new_marker_does_not_repeat_on_later_tick`
  (acceptance check 2).
- Added `t_returned_pr_first_ever_tick_treats_every_open_pr_as_new`
  (empty-state clause).
- Added `t_returned_pr_phase_transition_does_not_refire_new_marker`
  (regression pin for the warrant-hunt finding below).
canonical: acceptance run below — all five names appear with `ok`.

No changes to `relay.py` or `watchdog.py`. canonical: relay.py:102-113
(`_print_returned_pr_surfaced`, the raw `[returned-pr]` line's only
producer) and watchdog.py:1346 (its only call site), read via this
session's own grep/Read calls; the diff for this commit touches only the
two `on-the-record/monitors/` paths above.

## Why

The delta-filter is the one place that already tracks per-key
tick-to-tick state for every tag, including `returned-pr:` (age-stripped
comparison from #1719, unmodified condition — only the branch body was
extended). canonical: on-the-record/monitors/poll-heartbeat.sh, the
pre-existing `AGE_STRIP_RE`-based comparison in the same loop this
change edits. Both causes the issue names are shape/suppression problems
in that layer, not in how `relay.py` composes the raw line or where
`watchdog.py` places it in its own stdout, so fixing it there keeps the
existing `[returned-pr]` tag's exact text stable for
`gates/test_poll_heartbeat_delta.py`'s independent #1719 regression pin.
canonical: acceptance run below, `ok  t_returned_pr_line_no_longer_always_emits_when_unchanged`.

Two designs were considered for the "distinct signal" half:
- **Rename** the tag on first sighting (no duplicate line). Rejected:
  both test files carry pre-existing first-tick assertions of the exact
  substring `"[returned-pr] issue #N"`, which a rename would break.
  canonical: this session's own grep of both test files for that literal
  substring, run before writing the fix, which located those
  pre-existing assertions.
- **Prepend, don't replace** (the approach taken): purely additive, one
  marker per genuinely-new key, always the first line(s) of that tick's
  output.

For "stop repeating," dropping the line entirely (the issue's other
offered option) was rejected because #1732 added the 30-minute bound so
the Monitor channel never goes silent that long while a PR is still
outstanding; dropping it would silently regress that guarantee.
canonical: the `poll-heartbeat.sh` comment directly above the bound
block ("issue #1732: ... Only the undisposed-PR set #1719 req#1 attached
to this bound stays visible"), left unmodified by this commit and read
by this session before editing. A collapsed count line keeps that
guarantee while dropping the full-line repeat.

The issue's optional third suggestion (aging-line escalation) is not
implemented — it is phrased as a "consider," not a requirement.
canonical: `gh issue view 2180` output read this session — the
Acceptance section's four bullets do not name it.

Skip note (survey-order-directive): no separate survey/proposal file was
written — CORE_BUILD_NOW=1 authorizes direct delivery (contract v3 s19a),
and the fix required no open design decision beyond the two choices
argued above, resolved inline in this record.

## Upstream basis

- Issue #2180, read via `gh issue view 2180` — names the two causes, the
  acceptance checks, the empty-state clause, and the canonical test file.
- `on-the-record/monitors/poll-heartbeat.sh` (same-commit) — the file
  modified.
- `on-the-record/monitors/test_poll_heartbeat.py` (same-commit) — the
  canonical test file the issue names; existing conventions (`_run_tick`,
  `_force_last_emit_epoch`, the fake-spawn.py harness) reused unchanged.
- `gates/test_poll_heartbeat_delta.py` (unmodified, read for impact
  analysis) — the sibling #1117/#1719 regression suite.
- `relay.py` (function `_print_returned_pr_surfaced`) and `watchdog.py`
  (its call site inside `roster_watchdog()`) — read only, not modified;
  the raw line's origin and call site.

## Open findings

Resolved (not open), one before-landing warrant-hunt finding. canonical:
docs/issue-2180/reports/implementation/2026-08-24-hunt-returned-pr-signal-shape.md,
the hunt record written by the dispatched `warrant-hunter` agent this
session.

Finding: the initial implementation keyed the `[new-returned-pr]`
one-shot marker off the same diff key as the plain `[returned-pr]` line
diffing (`returned-pr:issue #N (phaseX)`), which bakes in the phase
label. Since `relay.py`'s `_undispositioned_role_prs` reclassifies one
`gh pr list` entry's phase in place as it goes from unapproved to
approved (same PR number/url, new phase label), a phase1->phase2
transition on an already-surfaced, still-open PR was a brand-new diff
key and re-fired the marker as if it were a new PR. canonical: this
session's own `sed -n '57,100p' relay.py` read of
`_undispositioned_role_prs`, confirming `phase` is derived per-PR-object
from `_ci._approved_roles_on_issue`, not a separate PR.

Fix: `is_new_pr` detection now tracks a persisted
`surfaced_returned_pr_issues` set keyed by the bare `#<issue>` token
(extracted via the same `ISSUE_TOKEN_RE` already used for the bound's
collapsed-line labels), independent of the phase-qualified diff key; the
set is pruned each tick to issue tokens still present in the current
returned-pr set. The plain `[returned-pr]` line's own re-emission on a
phase change is unaffected (still driven by the pre-existing,
phase-qualified diff key — a phase transition is genuinely new line
content and correctly still re-emits). canonical: acceptance run below,
`ok  t_returned_pr_phase_transition_does_not_refire_new_marker`.

## What did not work

None.

## Skill check

other mounted skills: not triggered — this change is a scoped bugfix to
one existing bash+embedded-Python file's diff/suppression logic plus its
test suite; no coupling/cohesion threshold, GoF-pattern decision,
data-structure/performance tradeoff, or multi-module structure decision
arose that the four mapped skills
(implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice, implementation-blueprint)
cover.

## Next steps

None — loop_state is terminal (landed).

Executed acceptance evidence. canonical: this turn's own transcript —
each command below was run directly by this session at landing time,
raw stdout pasted verbatim, no summarization.

acceptance: `python3 on-the-record/monitors/test_poll_heartbeat.py` —
result:
```
ok  t_board_sweep_lock_skip_treated_as_no_change
ok  t_heartbeat_arms_watchdog_when_due
ok  t_heartbeat_attaches_on_board_repo
ok  t_heartbeat_bound_with_no_returned_pr_emits_nothing
ok  t_heartbeat_bound_with_returned_pr_emits_only_those_lines
ok  t_heartbeat_orchestrate_off_alone_still_stops_monitor
ok  t_heartbeat_refuses_to_arm_on_non_git_root
ok  t_heartbeat_respects_kill_switch
ok  t_heartbeat_respects_monitor_only_kill_switch
ok  t_heartbeat_skips_attachment_on_non_board_repo
ok  t_heartbeat_skips_watchdog_when_not_due
ok  t_heartbeat_surfaces_empty_roster_report
ok  t_heartbeat_surfaces_induced_dead_poller
ok  t_patrol_crashed_role_tick_still_prints_summary_line
ok  t_patrol_kill_switch_still_prints_disabled_line_only
ok  t_patrol_promotion_tick_still_prints_summary_line
ok  t_patrol_quiet_tick_with_roles_emits_no_summary_line
ok  t_patrol_tick_skips_when_checkout_vanishes_mid_sleep
ok  t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior
ok  t_returned_pr_first_ever_tick_treats_every_open_pr_as_new
ok  t_returned_pr_new_item_emits_on_due_tick
ok  t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line
ok  t_returned_pr_new_marker_does_not_repeat_on_later_tick
ok  t_returned_pr_phase_transition_does_not_refire_new_marker
ok  t_returned_pr_unchanged_set_produces_no_output_on_due_tick
ok  t_unkeyed_line_content_change_still_emits
ok  t_unkeyed_line_insertion_suppresses_unchanged_lines_below

27/27 passed
```
exit code 0. This 27-test run (post warrant-hunt fix, one more test than
the initial 26-test cut) was captured directly in this session's own
transcript at landing time.

acceptance: `python3 gates/test_poll_heartbeat_delta.py` — this is the
sibling #1117/#1719 suite, exercising the unchanged `[returned-pr]` tag
only (never the new marker or the bound's collapsed line) — its clean
run is the "existing watchdog/Monitor behavior otherwise unchanged"
check's evidence. result:
```
ok  t_anomaly_rc_produces_no_crash_label
ok  t_change_after_suppression_emits
ok  t_changed_tick_emits
ok  t_clean_rc_produces_neither_label
ok  t_dead_session_line_always_emits_even_unchanged
ok  t_fresh_state_first_tick_always_emits
ok  t_identical_second_tick_suppressed
ok  t_non_due_tick_produces_no_output
ok  t_only_changed_line_emitted_not_full_report
ok  t_reserved_sentinel_rc_produces_crash_label
ok  t_returned_pr_line_no_longer_always_emits_when_unchanged
ok  t_signal_death_rc_produces_crash_label
ok  t_watchdog_anomaly_bullets_survive_round_trip

13/13 passed
```
exit code 0.

acceptance: `bash -n on-the-record/monitors/poll-heartbeat.sh` — checks
for syntax breakage from the heredoc edits (only Python code was
inserted inside the existing `<<'PY'` body; no surrounding bash comment
text was touched, relevant given the file's documented bash-3.2
apostrophe-count parsing quirk in that region). result:
```
SYNTAX OK
```
exit code 0.

acceptance: broader unrelated-suite regression check, run only to catch
a regression in files outside this change's scope: `python3 -m pytest
tests/test_poll_watchdog_log.py tests/test_monitor_liveness.py
tests/test_monitor_alive_gc.py on-the-record/hooks/test_monitor_notice.py
tests/test_spawn_observation_recovery.py -q`. result:
```
182 passed, 6 xfailed, 1 xpassed in 522.13s (0:08:42)
```
exit code 0.
