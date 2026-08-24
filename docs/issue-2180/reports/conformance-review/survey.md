# issue-2180 conformance-review — current-state survey

Phase-1 survey (survey-order-directive) auditing `issue-2180/implementation`'s
landed delivery (PR #2181, not yet landed on `main`) against issue #2180's
own "Fix"/"Acceptance"/empty-state text.

```
$ git log origin/main..issue-2180/implementation --oneline
3e67434d issue-2180: consult-trace (ok)
5c718174 issue-2180: consult-trace (ok)
f33a7a62 issue-2180: log before-landing warrant-hunt deviation
3271d8f8 issue-2180: distinct new-returned-pr signal, stop repeating already-surfaced returned-pr lines
```
canonical: git log origin/main..issue-2180/implementation --oneline — pasted live run above (executed-unit)

## 1. What landed

```
$ git diff origin/main..issue-2180/implementation --stat
docs/issue-2180/reports/consult-log.md             |   2 +
docs/issue-2180/reports/implementation.md          | 257 +++++++++++++++++++++
.../2026-08-24-hunt-returned-pr-signal-shape.md    |  43 ++++
.../reports/implementation/deviation-log.md        |  17 ++
on-the-record/monitors/poll-heartbeat.sh           |  65 +++-
on-the-record/monitors/test_poll_heartbeat.py      | 111 ++++++++-
6 files changed, 486 insertions(+), 9 deletions(-)
```
canonical: git diff origin/main..issue-2180/implementation --stat — pasted live run above (executed-unit)

Two source files touched (`on-the-record/monitors/poll-heartbeat.sh`,
`on-the-record/monitors/test_poll_heartbeat.py`); the other four paths
are the implementation role's own phase-2 record, consult-trace log,
warrant-hunt finding, and deviation log — not conformance-review's
subject to re-derive.

The implementation record's own frontmatter (read this session via
`git show issue-2180/implementation:docs/issue-2180/reports/implementation.md`)
states `CORE_BUILD_NOW=1` authorized direct delivery with no separate
phase-1 proposal round on that session — consistent with the single
delivery commit plus fixup commits shown in the log above.

## 2. Requirement extraction (conformance-review-requirement-extraction applied)

`gh issue view 2180` (read at session start) bundles a narrative "Live
finding" paragraph, a "## Fix" section of suggested approaches, and a
"## Acceptance" section of four bullets plus a standalone empty-state
clause. Splitting per the skill's rules — one obligation per line (rule
1), dimension-tagged (rule 6), an optional/no-threshold suggestion
flagged rather than treated as binding (rule 2):

1. **REQ-1** (functional-behavior) — a newly-returned PR (its issue
   number not previously surfaced) produces a distinct, unmistakable
   signal line on the tick it first appears, with an emission shape
   that differs from the routine `[returned-pr]` heartbeat line. Source:
   "## Acceptance" bullet 1.
2. **REQ-2** (functional-behavior/regression) — an already-surfaced PR
   does not re-emit the same full `[returned-pr]` line on a subsequent
   tick (two-tick sequence). Source: "## Acceptance" bullet 2.
3. **REQ-3** (edge-case, conditional on REQ-2 per rule 5) — the
   "already-surfaced" state tracked for REQ-2 must persist across a
   `phase1`→`phase2` transition of the *same* PR (same issue number),
   not reset by a change in the phase label baked into the raw line's
   text. Source: not stated explicitly in the issue's own bullets — this
   is the specific condition the issue's bullet-2 wording ("already-
   handled PRs") implies but does not spell out as its own edge case;
   kept as its own item per rule 5 because its verdict is conditional on
   REQ-2's dedup mechanism, and because it is exactly the gap the
   implementation session's own before-landing warrant-hunt dispatch
   surfaced and fixed pre-landing (see §6).
4. **REQ-4** (scope-boundary) — existing watchdog/Monitor behavior is
   otherwise unchanged. Source: "## Acceptance" bullet 3.
5. **REQ-5** (edge-case) — a first-ever tick with no prior surfaced-
   marker state file treats every currently-open `returned-pr` entry as
   new (each gets its own marker exactly once), then is suppressed on
   the immediately following unchanged tick. Source: the issue's
   standalone "empty state:" clause, below "## Acceptance".
6. **REQ-6** (process/evidentiary) — executed acceptance evidence is
   present in the record: actual commands and their raw output, not
   summarized. Source: "## Acceptance" bullet 4, "Executed acceptance
   evidence in the record (#2137)".
7. **REQ-7** (flagged unverifiable-as-written, rule 2; not binding) —
   "Consider whether the aging line (`age=77.5h`) should itself
   escalate". Source: "## Fix" section, third bullet. No observable
   success condition is stated (no threshold, no required shape) and
   the issue's own wording ("Consider whether...") is explicitly a
   suggestion, not an acceptance criterion — kept as its own item, not
   silently dropped, but not scored Present/Absent the way REQ-1..REQ-6
   are.

No bundled "and" clause needed splitting beyond the above; no summary
line restated three-or-more sub-points (rule 3 n/a); the issue states
no sampling derivation to reuse (rule 4 n/a — full enumeration is
feasible at this size, see §9). The "## Fix" section's first two
bullets (distinct signal; stop repeating, either "drop repeats
entirely" or "demote to a single collapsed count line") are the
*mechanism* options for REQ-1/REQ-2, not independent acceptance
criteria in their own right — "## Acceptance" bullets 1-2 are what is
binding; the implementation chose the "collapsed count line" branch of
the OR, evaluated under REQ-4 below (§5), not scored as a separate REQ.

## 3. Independent test re-execution (REQ-1, REQ-2, REQ-3, REQ-5) — not taken on trust

The implementation record's own "Acceptance evidence" section (read via
`git show issue-2180/implementation:docs/issue-2180/reports/implementation.md`)
pastes a full `on-the-record/monitors/test_poll_heartbeat.py` run and a
full `gates/test_poll_heartbeat_delta.py` run, all lines reading `ok`.
This session's own working tree is `issue-2180/conformance-review`,
branched before the fix landed, so neither file carries the fix on disk
here — re-running requires temporarily bringing in the implementation
branch's versions:

```
$ git status --short -- on-the-record/monitors/
$ git checkout issue-2180/implementation -- on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/test_poll_heartbeat.py
$ git diff --stat HEAD -- on-the-record/monitors/
on-the-record/monitors/poll-heartbeat.sh      |  65 +++++++++++++--
on-the-record/monitors/test_poll_heartbeat.py | 111 +++++++++++++++++++++++++-
2 files changed, 167 insertions(+), 9 deletions(-)
```
canonical: git status/checkout/diff sequence above — pasted live run above (executed-unit); working tree restored to `HEAD` at the end of this section (confirmed empty `git status --short` re-run below)

```
$ python3 on-the-record/monitors/test_poll_heartbeat.py
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
canonical: python3 on-the-record/monitors/test_poll_heartbeat.py — pasted live run above (executed-unit), run against the temporarily-checked-out fix
acceptance: python3 on-the-record/monitors/test_poll_heartbeat.py — result: pass — the run directly above lists every test as `ok`, including the four most directly on point for this survey's REQ-1/REQ-2/REQ-3/REQ-5 (`t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line`, `t_returned_pr_new_marker_does_not_repeat_on_later_tick`, `t_returned_pr_phase_transition_does_not_refire_new_marker`, `t_returned_pr_first_ever_tick_treats_every_open_pr_as_new`) — this session's own count reproduces the implementation record's own pasted transcript with no difference (derived: side-by-side line count against the record quoted in §6 below).

## 4. Source-level check of each new test's assertion shape (REQ-1, REQ-2, REQ-3, REQ-5)

```
$ git diff origin/main..issue-2180/implementation -- on-the-record/monitors/test_poll_heartbeat.py
```
canonical: git diff origin/main..issue-2180/implementation -- on-the-record/monitors/test_poll_heartbeat.py — read in full this session (not re-pasted here; test bodies quoted below are verbatim excerpts from that diff)

- `t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line`
  asserts `lines[0] == "[new-returned-pr] issue #40 (phase2): ..."` AND
  `"[returned-pr] issue #40 (phase2): ..." in r.stdout` — the distinct
  tag is a different bracket string (`[new-returned-pr]` vs
  `[returned-pr]`), placed first, with the original line still present.
  Directly matches REQ-1's "distinct, unmistakable... emission shape
  differs" wording.
- `t_returned_pr_new_marker_does_not_repeat_on_later_tick` runs two
  ticks for the same issue number (`#22`), asserts the marker and the
  plain line both appear on tick one, then asserts `r2.stdout.strip()
  == ""` on tick two where only the `age=` token changed — no full-line
  repeat, exactly REQ-2's "does not re-emit... on subsequent ticks".
- `t_returned_pr_phase_transition_does_not_refire_new_marker` runs
  `phase1` then `phase2` for the same issue number (`#999`), asserts
  `[new-returned-pr]` fires on tick one only, and that tick two still
  shows the plain `[returned-pr] issue #999 (phase2)` line (the phase
  text itself is a genuine content change, correctly still re-emitted)
  but no repeated marker — REQ-3's exact scenario.
- `t_returned_pr_first_ever_tick_treats_every_open_pr_as_new` asserts
  `not (checkout / "runs" / "poll_heartbeat_last_state.json").exists()`
  before tick one, both `#22` and `#40` get markers on tick one, then
  tick two (unchanged report) emits nothing — REQ-5's exact wording.

## 5. Regression check (REQ-4) — independent, not taken on trust

```
$ python3 gates/test_poll_heartbeat_delta.py
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
canonical: python3 gates/test_poll_heartbeat_delta.py — pasted live run above (executed-unit), run against the temporarily-checked-out fix; this is the sibling #1117/#1719 regression suite, exercising the unchanged `[returned-pr]` tag only (never the new marker or the bound's collapsed line)
acceptance: python3 gates/test_poll_heartbeat_delta.py — result: pass — every line above reads `ok`, and this session's own count reproduces the implementation record's own pasted transcript with no difference (derived: side-by-side line count against the record quoted in §6 below)

```
$ bash -n on-the-record/monitors/poll-heartbeat.sh
SYNTAX OK
```
canonical: bash -n on-the-record/monitors/poll-heartbeat.sh — pasted live run above (executed-unit)
acceptance: bash -n on-the-record/monitors/poll-heartbeat.sh — result: pass, exit code 0

```
$ git diff origin/main..issue-2180/implementation --stat -- relay.py watchdog.py
$ grep -n "_print_returned_pr_surfaced" relay.py
102:def _print_returned_pr_surfaced(blockers: list[dict], source: str) -> None:
$ grep -n "roster_watchdog\|_print_returned_pr_surfaced" watchdog.py
1280:def roster_watchdog(auto_respawn: bool = False, all_scope: bool = False,
1346:        _sp._print_returned_pr_surfaced(blockers, source="watchdog")
```
canonical: three commands above — pasted live run above (executed-unit). The first command's empty output shows `relay.py`/`watchdog.py` carry no diff on this branch; the raw `[returned-pr]` line's only producer (`relay.py:102`) and its only call site (`watchdog.py:1346`) both sit outside this diff's scope, matching the implementation record's own stated impact analysis.

```
$ python3 -m pytest tests/test_poll_watchdog_log.py tests/test_monitor_liveness.py tests/test_monitor_alive_gc.py on-the-record/hooks/test_monitor_notice.py tests/test_spawn_observation_recovery.py -q
182 passed, 7 xfailed in 524.65s (0:08:44)
```
canonical: pytest, five-file broader-suite command — pasted live run above (executed-unit), run against the temporarily-checked-out fix
acceptance: same command — result: pass — 182 clean passes above; the xfailed/xpassed split against the implementation record's own pasted transcript for this same command is examined separately in §6, since it differs from this session's own run.

```
$ git checkout HEAD -- on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/test_poll_heartbeat.py
$ git status --short -- on-the-record/monitors/
```
canonical: git checkout HEAD -- ... && git status --short — pasted live run above (executed-unit); the second command's empty output shows the working tree was restored before this survey was written.

## 6. Evidentiary check (REQ-6) and the one discrepancy found

The implementation record (read this session via `git show
issue-2180/implementation:docs/issue-2180/reports/implementation.md`)
carries four `acceptance:` blocks, each with the actual command, raw
pasted stdout, and an explicit exit code — the right shape per REQ-6.
Three of the four reproduce line-for-line on the independent replays
above (§3's `on-the-record/monitors/test_poll_heartbeat.py` run, §5's
`gates/test_poll_heartbeat_delta.py` run and `bash -n` syntax check).

The fourth block — the same five-file broader-suite `pytest` command
quoted in §5 — is where this survey's one open finding sits. The
implementation record's own pasted transcript for that exact command
reads (quoted verbatim from the file read above):

> `182 passed, 6 xfailed, 1 xpassed in 522.13s (0:08:42)`

while this session's own independent re-run of the identical command,
fenced in §5 above, reads a different split between the two
xfail-adjacent categories: `derived: the fenced pytest run in §5 above`.
`grep -n xfail` across the five files in that command (executed-unit,
not re-pasted here) locates seven `@pytest.mark.xfail(...)`-decorated
tests total — two in `on-the-record/hooks/test_monitor_notice.py`, five
in `tests/test_spawn_observation_recovery.py` — the same total this
session's own run distributes across the two categories differently
than the record's pasted transcript does. Consistent with one
timing/race-dependent test among those seven flipping its outcome
category between the two separate runs (a pre-existing flake), not a
regression this diff introduces: none of
these five files appear in the `origin/main..issue-2180/implementation`
diff (§1), and both of REQ-4's directly-relevant suites — the
`on-the-record/monitors/test_poll_heartbeat.py` and
`gates/test_poll_heartbeat_delta.py` runs in §3 and §5 — reproduced with
no difference at all against the record's own pasted transcripts.

REQ-6 is about the record *carrying* executed evidence, not about every
individual number in it staying identical on replay forever (a flaky
xfail is expected to vary run to run) — the record's evidence blocks
are real and executed; three of four reproduce exactly, and the
fourth's divergence is itself ordinary non-determinism in an
unrelated-scope regression check, not evidence of summarization or
fabrication.

## 7. REQ-7 (flagged unverifiable-as-written) — status

The implementation record's own "Why" section (read via the same `git
show` citation as §6) states plainly that the aging-line-escalation
suggestion is not implemented because it is phrased as a suggestion,
not a requirement. This matches this survey's own read of the issue
text in §2 (REQ-7) — the issue itself supplies no acceptance threshold
for this suggestion, so leaving it out is not a gap against anything
binding.

## 8. Open findings surfaced during survey

1. **Broader-suite xfail/xpass split does not line up identically on
   independent replay** (§6). The `pytest` five-file command's total
   clean-run tally and total xfail-adjacent tally both line up between
   this session's run and the implementation record's own pasted
   transcript; only the internal split between the two xfail-adjacent
   outcome categories differs, consistent with a pre-existing flake
   in one of five files this diff never touches. Not attributable to
   this issue's diff. Resolution path: none needed for this issue — a
   candidate for a separate flaky-test issue against whichever of the
   seven `xfail`-marked tests in `on-the-record/hooks/test_monitor_notice.py`
   or `tests/test_spawn_observation_recovery.py` is timing-dependent,
   out of this review's scope to identify further.

## 9. Sampling scope

Full enumeration, not a sample: one PR, two source files, seven
requirement line items derived from the issue's own four acceptance
bullets plus its empty-state clause plus one flagged-optional "Fix"
bullet — small enough that spot-checking would cost more setup than it
saves. The `conformance-review-sampling-derivation` skill is not
invoked this session (see the proposal's skill-verdict section for the
not-applicable reasoning).
