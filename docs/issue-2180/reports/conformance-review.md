---
issue: 2180
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2180/reports/conformance-review/survey.md
    sha: same-commit
  - path: docs/issue-2180/proposals/2026-08-24-conformance-review-issue-2180.md
    sha: same-commit
subject: on-the-record/monitors/poll-heartbeat.sh, on-the-record/monitors/test_poll_heartbeat.py @ abdb5ac0
test: issue #2180 "## Acceptance" bullets 1-4 plus its standalone empty-state clause
result: cantTell
assertedBy: conformance-review (issue-2180/conformance-review session)
---

# issue-2180 — conformance-review record

## What was done

Audited `issue-2180/implementation`'s delivery (originally PR #2181,
tip `3e67434d`, landed on `main` as `abdb5ac0` during this review's own
phase-2 session) against issue #2180's own "Fix"/"Acceptance"/
empty-state text, per the phase-1 requirement extraction in
`docs/issue-2180/reports/conformance-review/survey.md` §2 (REQ-1..
REQ-7). This session re-ran every independent verification command a
second time against the landed `abdb5ac0:on-the-record/monitors/
poll-heartbeat.sh:1` tip (the phase-1 survey's own runs were against
the pre-merge `issue-2180/implementation` branch), by temporarily
bringing the two touched files into this working tree and restoring it
afterward:

```
$ git checkout origin/main -- on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/test_poll_heartbeat.py
$ git diff --stat HEAD -- on-the-record/monitors/
 on-the-record/monitors/poll-heartbeat.sh      |  65 +++++++++++++--
 on-the-record/monitors/test_poll_heartbeat.py | 111 +++++++++++++++++++++++++-
 2 files changed, 167 insertions(+), 9 deletions(-)
```
canonical: git checkout origin/main -- ... && git diff --stat HEAD -- ... — pasted live run above (executed-unit), this session's own phase-2 replay

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
canonical: python3 on-the-record/monitors/test_poll_heartbeat.py — pasted live run above (executed-unit), this session's own phase-2 replay against `origin/main`'s checked-out files
acceptance: python3 on-the-record/monitors/test_poll_heartbeat.py — result: pass — every line above reads `ok`, reproducing the phase-1 survey's own count with no difference.

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
canonical: python3 gates/test_poll_heartbeat_delta.py — pasted live run above (executed-unit), this session's own phase-2 replay against `origin/main`'s checked-out files
acceptance: python3 gates/test_poll_heartbeat_delta.py — result: pass — every line above reads `ok`, reproducing the phase-1 survey's own count with no difference; this is the sibling #1117/#1719 regression suite exercising the unchanged `[returned-pr]` tag only.

```
$ bash -n on-the-record/monitors/poll-heartbeat.sh
$ echo "EXIT:$?"
EXIT:0
```
canonical: bash -n on-the-record/monitors/poll-heartbeat.sh — pasted live run above (executed-unit), this session's own phase-2 replay
acceptance: bash -n on-the-record/monitors/poll-heartbeat.sh — result: pass — exit code 0, no syntax error.

```
$ git diff HEAD..origin/main --stat -- relay.py watchdog.py
$ grep -n "_print_returned_pr_surfaced" relay.py
102:def _print_returned_pr_surfaced(blockers: list[dict], source: str) -> None:
$ grep -n "roster_watchdog\|_print_returned_pr_surfaced" watchdog.py
1280:def roster_watchdog(auto_respawn: bool = False, all_scope: bool = False,
1346:        _sp._print_returned_pr_surfaced(blockers, source="watchdog")
```
canonical: three commands above — pasted live run above (executed-unit), this session's own phase-2 replay. The first command's empty output shows `relay.py`/`watchdog.py` carry no diff between this working tree and `origin/main`; the raw `[returned-pr]` line's only producer and only call site both sit outside this issue's diff.

```
$ git checkout HEAD -- on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/test_poll_heartbeat.py
$ git status --short -- on-the-record/monitors/
```
canonical: git checkout HEAD -- ... && git status --short — pasted live run above (executed-unit); the second command's empty output shows the working tree was restored before this record was written.

## Why

Conformance-review's own reason to exist is independent audit, not
restating a builder's account of their own work — the phase-1
proposal (`docs/issue-2180/proposals/
2026-08-24-conformance-review-issue-2180.md`, "Rationale") already
rejected taking the implementation record's pasted evidence on trust,
and it surfaced a real discrepancy that way (REQ-6 below). Phase-2
re-ran the identical independent-verification commands a second time,
this time against the tree state actually reachable at
`abdb5ac0:on-the-record/monitors/poll-heartbeat.sh:1` (the subject
moved from an open branch to a landed commit between the two phases of
this same review) rather than resting on the phase-1 numbers alone.

## Upstream basis

- `docs/issue-2180/reports/conformance-review/survey.md` (this issue's
  phase-1, same commit set as this proposal) — requirement extraction
  (REQ-1..REQ-7) and the first independent test re-execution, against
  the pre-merge `issue-2180/implementation` branch.
- `abdb5ac0:on-the-record/monitors/poll-heartbeat.sh:1` and
  `abdb5ac0:on-the-record/monitors/test_poll_heartbeat.py:1` — the
  audited subject, re-verified fresh this session (see fenced commands
  above).

## Findings

---
requirement: REQ-1 — a newly-returned PR (issue number not previously
  surfaced) produces a distinct, unmistakable signal line on the tick
  it first appears, with an emission shape that differs from the
  routine `[returned-pr]` heartbeat line.
spec_ref: issue #2180, "## Acceptance" bullet 1
verdict: Present
evidence: `abdb5ac0:on-the-record/monitors/poll-heartbeat.sh:390` —
  `new_pr_markers.append(line.replace("[returned-pr]", "[new-returned-pr]", 1))`,
  placed ahead of the routine line; test
  `abdb5ac0:on-the-record/monitors/test_poll_heartbeat.py:646`
  `t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line`,
  independently re-run this session, `ok` line for this test in the
  fenced run above (this record's own evidence section, not re-pasted
  here).
rationale: the marker uses a distinct bracket tag (`[new-returned-pr]`
  vs `[returned-pr]`), is emitted first, and the test asserts both the
  tag and its position — directly matching the acceptance bullet's
  wording; independently reproduced fresh this session against the
  landed commit.
---
requirement: REQ-2 — an already-surfaced PR does not re-emit the same
  full `[returned-pr]` line on a subsequent tick.
spec_ref: issue #2180, "## Acceptance" bullet 2
verdict: Present
evidence: `abdb5ac0:on-the-record/monitors/poll-heartbeat.sh:420` —
  the already-surfaced branch skips re-appending the full line; test
  `abdb5ac0:on-the-record/monitors/test_poll_heartbeat.py:671`
  `t_returned_pr_new_marker_does_not_repeat_on_later_tick`,
  independently re-run this session, `ok` in the fenced run above
  (this record's own evidence section, not re-pasted here).
rationale: the test runs two ticks for the same issue number and
  asserts empty stdout on tick two (only the `age=` token changed) —
  exactly the acceptance bullet's wording, reproduced fresh this
  session.
---
requirement: REQ-3 — the "already-surfaced" state tracked for REQ-2
  persists across a `phase1`->`phase2` transition of the same PR (same
  issue number), not reset by a change in the phase label baked into
  the raw line's text.
spec_ref: issue #2180, "## Acceptance" bullet 2 (implied edge case; see
  the REQ-3 entry in `docs/issue-2180/reports/conformance-review/
  survey.md` §2 for the requirement-extraction rule-5 basis for
  keeping it as its own line)
verdict: Present
evidence: `abdb5ac0:on-the-record/monitors/poll-heartbeat.sh:358` —
  `surfaced_issues = set(prev.get("surfaced_returned_pr_issues", []))`
  is keyed by issue number only, not by the full line text; test
  `abdb5ac0:on-the-record/monitors/test_poll_heartbeat.py:693`
  `t_returned_pr_phase_transition_does_not_refire_new_marker`,
  independently re-run this session, `ok` in the fenced run above
  (this record's own evidence section, not re-pasted here).
rationale: the test runs `phase1` then `phase2` for the same issue
  number, asserts `[new-returned-pr]` fires once (tick one only) while
  the plain `[returned-pr]` line still re-emits on tick two for the
  genuine phase-label content change — exactly this requirement's
  scenario, reproduced fresh this session against the landed commit.
---
requirement: REQ-4 — existing watchdog/Monitor behavior is otherwise
  unchanged.
spec_ref: issue #2180, "## Acceptance" bullet 3
verdict: Present
evidence: the `git diff HEAD..origin/main --stat -- relay.py
  watchdog.py` fenced command above (empty output) — the raw
  `[returned-pr]` line's only producer,
  `abdb5ac0:relay.py:102` (`_print_returned_pr_surfaced`), and its only
  call site, `abdb5ac0:watchdog.py:1346` (inside `roster_watchdog` at
  `abdb5ac0:watchdog.py:1280`), both sit outside this issue's diff; the
  `python3 gates/test_poll_heartbeat_delta.py` fenced run above (every
  line `ok` — derived: the fenced run earlier in this record's own
  evidence section);
  `bash -n on-the-record/monitors/poll-heartbeat.sh` fenced run above
  (exit 0).
rationale: the two directly-relevant regression surfaces — the
  relay.py/watchdog.py diff and the sibling `#1117/#1719` regression
  suite exercising the unchanged `[returned-pr]` tag — both reproduce
  with no difference against the landed commit, and the diff
  introduces no syntax break.
---
requirement: REQ-5 — a first-ever tick with no prior surfaced-marker
  state file treats every currently-open `returned-pr` entry as new
  (each gets its own marker exactly once), then is suppressed on the
  immediately following unchanged tick.
spec_ref: issue #2180, standalone "empty state:" clause (below "##
  Acceptance")
verdict: Present
evidence: `abdb5ac0:on-the-record/monitors/test_poll_heartbeat.py:718`
  `t_returned_pr_first_ever_tick_treats_every_open_pr_as_new` — asserts
  no prior `runs/poll_heartbeat_last_state.json`, both `#22` and `#40`
  marked new on tick one, tick two (unchanged) emits nothing;
  independently re-run this session, `ok` in the fenced run above
  (this record's own evidence section, not re-pasted here).
rationale: the test's own setup and assertions match the empty-state
  clause's wording exactly, reproduced fresh this session against the
  landed commit with no difference.
---
requirement: REQ-6 — executed acceptance evidence is present in the
  record: actual commands and their raw output, not summarized.
spec_ref: issue #2180, "## Acceptance" bullet 4 ("Executed acceptance
  evidence in the record (#2137)")
verdict: Surface
evidence: the implementation role's own record (read this session via
  `git show abdb5ac0~3:docs/issue-2180/reports/implementation.md`, the
  fixup-commit-adjacent parent carrying that role's own phase-2
  content) carries four `acceptance:` blocks with real commands and
  pasted output. Three reproduce line-for-line on this session's own
  independent replay above (the `test_poll_heartbeat.py` run, the
  `test_poll_heartbeat_delta.py` run, the `bash -n` check — derived:
  the two fenced runs earlier in this record's own evidence section).
  The fourth — a five-file broader-suite `pytest
  tests/test_poll_watchdog_log.py tests/test_monitor_liveness.py
  tests/test_monitor_alive_gc.py on-the-record/hooks/
  test_monitor_notice.py tests/test_spawn_observation_recovery.py -q`
  command — is quoted verbatim from that record, read this session:

  > 182 passed, 6 xfailed, 1 xpassed in 522.13s (0:08:42)

  The phase-1 survey's own independent run of the identical command
  against the pre-merge branch is fenced there as ending in a
  different split instead (derived: the fenced pytest run in
  `docs/issue-2180/reports/conformance-review/survey.md` §5) — same
  total clean-run tally and same total xfail-adjacent tally, different
  internal split between the two xfail-adjacent categories.
rationale: the record's evidence blocks are real, executed, and in the
  right shape for REQ-6's own wording — not a fabrication or
  summarization finding — but one of the four does not, on independent
  replay, establish the exact split it states, which is short of a
  full match: something exists at the right name and shape but the
  specific claim inside it does not independently reproduce.
  Attributed to REQ-6 (the evidentiary requirement) rather than REQ-4
  (scope-boundary), since REQ-4's own two directly-relevant suites
  reproduce exactly and nothing here shows the diff itself changed
  watchdog/Monitor behavior.
---
requirement: REQ-7 — (flagged unverifiable-as-written, not a binding
  acceptance criterion) "Consider whether the aging line (`age=77.5h`)
  should itself escalate."
spec_ref: issue #2180, "## Fix" section, third bullet
verdict: Unverifiable
evidence: the issue's own "## Fix" section states no threshold or
  required shape for this suggestion — "Consider whether..." is
  explicitly non-binding language, leaving no checkable bar to hold
  any implementation against. The implementation role's own record
  (read this session via `git show
  abdb5ac0~3:docs/issue-2180/reports/implementation.md`) states
  plainly the escalation was not built because the issue phrases it as
  a suggestion, not a requirement.
rationale: `Unverifiable` rather than `Absent`, because the gap is in
  the requirement's own checkability (no stated threshold), not in
  evidence that something required is missing — the
  requirement-extraction skill's rule 2 flags exactly this class of
  item as non-binding rather than silently dropping it or inventing an
  acceptance bar the issue itself never set.
---

Recomputed `result` (worst case across the six scored entries
REQ-1..REQ-6, per the role spec's own recomputation rule — a failing
outcome outranks an uncertain one, which outranks an inapplicable one,
which outranks an untested one, which outranks a fully-clean outcome):
REQ-1 Present, REQ-2 Present, REQ-3 Present, REQ-4 Present, REQ-5
Present, REQ-6 Surface — the one non-clean entry (REQ-6) drives the
overall value to `cantTell`. REQ-7's `Unverifiable` maps to
`inapplicable`, which does not change this outcome.

## Open findings

1. **Broader-suite xfail/xpass split does not line up identically
   across independent replays** (REQ-6 above). The five-file `pytest`
   command's total clean-run tally and total xfail-adjacent tally both
   agree between this review's own runs and the implementation
   record's own transcript (`182` and `7` respectively in both); only
   the internal split between `xfailed` and `xpassed` differs (6+1 in
   the implementation record's transcript vs 7+0 in the phase-1
   survey's own replay, `docs/issue-2180/reports/
   conformance-review/survey.md` §6). `grep -n xfail` across the five
   files (this session, not re-pasted here) locates exactly seven
   `@pytest.mark.xfail(...)`-decorated tests, none of which appear in
   the `origin/main..issue-2180/implementation` diff (survey.md §1).
   Consistent with one timing/race-dependent test among those seven
   flipping outcome category between runs — a pre-existing flake, not
   a regression this issue's diff introduces. Resolution path: none
   needed for issue #2180 itself; a candidate for a separate
   flaky-test issue against whichever of the seven `xfail`-marked
   tests in `on-the-record/hooks/test_monitor_notice.py` or
   `tests/test_spawn_observation_recovery.py` is timing-dependent — out
   of this review's own scope to pin down further.
2. **`pr-preflight.sh`'s amendments-reconciled check has no legitimate
   satisfaction path for a phase-1 PR** (`docs/issue-2180/reports/
   conformance-review/survey.md` §8-9,
   `docs/issue-2180/reports/conformance-review/deviation-log.md`).
   Logged against the tooling, not against issue #2180's diff; already
   reconciled in the phase-1 survey and reported to the user at that
   session's end. Resolution path: a fix to `pr-preflight.sh` itself
   (route the check to the phase-1 survey/proposal home when
   `phase1`), out of this review's own write set to make.

## What did not work

None — both independent re-verification runs this review carried out
(phase-1 against the pre-merge `issue-2180/implementation` branch,
phase-2 this session against the landed `abdb5ac0` tip) reproduced
cleanly on their first attempt; no fallback approach was needed.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; produced the REQ-1..REQ-7 split in
`docs/issue-2180/reports/conformance-review/survey.md` §2 — one
obligation per line, dimension-tagged, backward-traced to the issue's
own "Fix"/"Acceptance"/empty-state text, REQ-3 kept as its own
conditional item per rule 5, REQ-7 flagged unverifiable-as-written per
rule 2.

skill-verdict: conformance-review-verification-method-selection —
applied: invoked; set the method per requirement — Test (independently
re-run twice: pre-merge branch in phase-1, landed `main` tip in
phase-2) for REQ-1/REQ-2/REQ-3/REQ-4/REQ-5, Inspection for REQ-4's
relay.py/watchdog.py-untouched check and REQ-6's evidence-shape check,
Analysis-adjacent grep-based characterization for the REQ-6
discrepancy's root cause.

skill-verdict: conformance-review-verdict-assignment — applied:
invoked; used to assign REQ-1..REQ-7's verdicts above (five `Present`,
one `Surface`, one `Unverifiable`) and to attach the REQ-6 discrepancy
to REQ-6 itself rather than downgrading REQ-4.

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every evidence field above cites `sha:path:line`, re-pinned
to `abdb5ac0` (the landed commit) this session, superseding the
phase-1 survey's pre-merge `3271d8f8`/`f33a7a62` citations where the
same content now lives at the landed sha.

skill-verdict: conformance-review-finding-record — applied: invoked;
used directly to write the seven finding blocks above — field list
`requirement`/`spec_ref`/`verdict`/`evidence`/`rationale` per
requirement, exactly one verdict from the five-value set per block, no
`Present`/`Surface`/`Unverifiable` written without its required
evidence pointer (REQ-7's evidence names the missing threshold rather
than a diff pointer, per the skill's own exception for
`Unverifiable`).

skill-verdict: conformance-review-sampling-derivation — not-applicable:
full enumeration of the issue's seven derived line items is feasible
at this size (survey.md §9) — no stratified sample is needed.

skill-verdict: conformance-review-severity-classification —
not-applicable: this review's scope was not explicitly extended into
risk-weighting a recorded finding; no severity band was requested.

## Next steps

None — `loop_state` reaches this role's terminal value (`reported`)
with this record. The two open findings above each carry their own
resolution path, out of this review's own scope to pursue further.
