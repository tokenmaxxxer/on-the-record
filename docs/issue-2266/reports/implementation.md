---
issue: 2266
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2266/reports/implementation/2026-08-25-hunt-poll-heartbeat-bash32-heredoc-fix.md
    sha: same-commit
  - path: on-the-record/monitors/poll-heartbeat.sh
    sha: f4ec6d70db6e894d7fd968ed07f58b1c4933ccd2
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/poll_heartbeat_delta.py
  - on-the-record/monitors/test_poll_heartbeat.py
type: fix
breaking: none — poll-heartbeat.sh's argv/env contract with the extracted
  script is unchanged from the old heredoc's own contract.
verdict: pass
---

# issue-2266 — implementation record

## What was done

Removed the recurring bash 3.2 parse-time landmine in
`on-the-record/monitors/poll-heartbeat.sh` structurally, per the issue's
ask, instead of re-balancing the heredoc body's apostrophe count as
issue #1719 originally did:

1. **Extraction, not rebalancing.** The `python3 - <<'PY' ... PY` heredoc
   that used to sit inside `diff_output="$( ... )"` no longer exists in
   this file.
   canonical: on-the-record/monitors/poll-heartbeat.sh:246
   Its body (the line-keyed delta-diff logic — unchanged bit for bit,
   only re-indented out of the heredoc's forced top-level scope and
   wrapped in `main()`) now lives in its own file,
   `on-the-record/monitors/poll_heartbeat_delta.py`. poll-heartbeat.sh
   invokes it as `python3 "${SCRIPT_DIR}/poll_heartbeat_delta.py"
   "${CHECKOUT}/runs/poll_heartbeat_last_state.json" "$(date +%s)"`,
   still passing the captured tick text via the `POLL_HEARTBEAT_TEXT`
   env var. With no heredoc left inside any `$( )` in the file, the
   landmine's precondition — a heredoc lexically nested in an unclosed
   `$( )` — is absent from this file.

2. **Regression smoke**, added to the issue's named gate
   `on-the-record/monitors/test_poll_heartbeat.py` (see "Acceptance
   evidence" below for the executed run):
   - `t_no_command_substitution_wrapped_heredoc_in_script` runs a
     depth-tracking scan, `_find_command_substitution_wrapped_heredocs`,
     over poll-heartbeat.sh's own text: it counts unmatched `$(` across
     the whole file (heredoc bodies excluded from the count) and flags
     any heredoc opener reachable while that count is still positive,
     independent of whether the `$(` and the heredoc opener share one
     physical line.
   - `t_command_substitution_wrapped_heredoc_detector_catches_multiline_shape`
     is a detector self-check against a synthetic, hand-built sample
     (never the real file) — see "What did not work" for why this
     exists.
   - `t_poll_heartbeat_bash_syntax_is_clean` runs `bash -n` under
     whatever bash the test host ships, the CI-fallback proxy the issue
     names for when a real bash 3.2 binary isn't reachable.

3. **Structural audit** of the repo's other `<<'…'` heredocs, using the
   same depth-tracking scanner as the regression smoke, over every
   git-tracked `*.sh` file — see "Acceptance evidence" for the sweep
   command and its raw output.

## Why

The issue asked explicitly for a structural removal rather than a
rebalance, because issue #1719 already anticipated and documented this
exact recurrence in its own landmine comment and issue #2181's comment
edits hit it anyway — apostrophe-parity maintenance is not a fix. Of the
two structural options the issue named (move comments out of the heredoc
body, or extract the Python to its own file), extraction was chosen
because it removes the *shape* (heredoc nested in `$( )`) entirely,
rather than leaving a heredoc-in-`$( )` construct that some future edit
(a new comment, a docstring, an apostrophe in a log message) could
re-trip regardless of how carefully today's comments are worded. A
standalone `.py` file is also easier to lint/test/read than ~190 lines
of Python quoted inside a shell heredoc, and this repo already has
precedent for a `monitors/*.py` sibling next to `monitors/*.sh`
(`on-the-record/monitors/test_poll_heartbeat.py` already lives next to
`poll-heartbeat.sh`).

## What did not work

The first cut of the regression smoke used a same-line-only regex
(`\$\(.*<<DELIM$`) to detect the landmine shape. The before-landing
warrant-hunter (stance 0) wrote a reproduction showing that a `$( )` and
its heredoc opener split across a `\`-continued line hits the same
bash-3.2 parse failure the regex was written to catch, while the regex
itself returns an empty hit list on that sample.
canonical: docs/issue-2266/reports/implementation/2026-08-25-hunt-poll-heartbeat-bash32-heredoc-fix.md:18-74

The same-line regex was replaced with the depth-tracking scanner
described above, a synthetic-sample self-check was added so the
detector's multi-line coverage can't silently regress again without a
test noticing, and the repo-wide audit was re-run with the replacement
scanner (see "Acceptance evidence" — same zero-hit result as the
original same-line sweep, over the same file set).

## Upstream basis

- Issue #2266 (this record's subject).
canonical: gh issue view 2266
- `f4ec6d70` (HEAD at session start) — base commit; the pre-fix state of
  `on-the-record/monitors/poll-heartbeat.sh` cited above as the
  `upstream.sha` for that path is this commit.
- `abdb5ac0` (issue #2181) — per the issue's own root-cause writeup, the
  commit whose comment edits changed the heredoc body's apostrophe
  count.
canonical: git log --oneline -5 -- on-the-record/monitors/poll-heartbeat.sh
- docs/issue-2266/reports/implementation/2026-08-25-hunt-poll-heartbeat-bash32-heredoc-fix.md
  (same commit, sha `same-commit`) — the before-landing hunt record and
  its Resolution section.

## Open findings

None — the warrant-hunt finding recorded above was resolved in the same
commit that introduced the gap (see "What did not work" and the hunt
record's own Resolution section).

## Next steps

None; loop_state is terminal (landed).

## Acceptance evidence (executed-live)

Gate named by the issue: `on-the-record/monitors/test_poll_heartbeat.py`.

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
ok  t_no_command_substitution_wrapped_heredoc_in_script
ok  t_command_substitution_wrapped_heredoc_detector_catches_multiline_shape
ok  t_patrol_crashed_role_tick_still_prints_summary_line
ok  t_patrol_kill_switch_still_prints_disabled_line_only
ok  t_patrol_promotion_tick_still_prints_summary_line
ok  t_patrol_quiet_tick_with_roles_emits_no_summary_line
ok  t_patrol_tick_skips_when_checkout_vanishes_mid_sleep
ok  t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior
ok  t_poll_heartbeat_bash_syntax_is_clean
ok  t_returned_pr_first_ever_tick_treats_every_open_pr_as_new
ok  t_returned_pr_new_item_emits_on_due_tick
ok  t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line
ok  t_returned_pr_new_marker_does_not_repeat_on_later_tick
ok  t_returned_pr_phase_transition_does_not_refire_new_marker
ok  t_returned_pr_unchanged_set_produces_no_output_on_due_tick
ok  t_unkeyed_line_content_change_still_emits
ok  t_unkeyed_line_insertion_suppresses_unchanged_lines_below

30/30 passed
```
canonical: python3 on-the-record/monitors/test_poll_heartbeat.py — result: PASS

Two sibling suites, carried over from before this change with no edits,
also ran clean:

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

$ python3 gates/test_poll_heartbeat_patrol.py
ok  t_kill_switch_suppresses_and_traces
ok  t_no_board_role_zero_side_effects
ok  t_patrol_invoked_only_on_nth_tick

3/3 passed
```
canonical: python3 gates/test_poll_heartbeat_delta.py — result: PASS
canonical: python3 gates/test_poll_heartbeat_patrol.py — result: PASS

No SKIPPED lines appear in any of the three runs above.

`bash -n` under this sandbox's own bash — the CI-fallback proxy tier
(this sandbox carries no macOS bash 3.2 natively):

```
$ bash --version | head -1
GNU bash, 버전 5.1.16(1)-release (x86_64-pc-linux-gnu)
$ bash -n on-the-record/monitors/poll-heartbeat.sh && echo OK
OK
```
canonical: bash -n on-the-record/monitors/poll-heartbeat.sh — result: PASS

A real bash 3.2.57(1)-release binary — the exact version string the
issue's own consumer report quotes — reached over the network via
`docker pull bash:3.2` (the official Docker Hub image; not the
CI-fallback proxy):

```
$ docker run --rm bash:3.2 bash --version | head -1
GNU bash, version 3.2.57(1)-release (x86_64-pc-linux-musl)

$ docker run --rm -v "$PWD/on-the-record:/repo/on-the-record:ro" bash:3.2 \
    bash -n /repo/on-the-record/monitors/poll-heartbeat.sh && echo OK
OK
```
canonical: bash -c "docker run --rm bash:3.2 bash -n /repo/on-the-record/monitors/poll-heartbeat.sh" — result: PASS

The same bash 3.2 container against the pre-fix file
(`git show f4ec6d70:on-the-record/monitors/poll-heartbeat.sh`), run
before starting the fix, reproducing the issue's own reported failure at
the same line number and token it quotes:

```
$ docker run --rm -v "/tmp/orig_check:/repo:ro" bash:3.2 bash -n /repo/poll-heartbeat.sh
/repo/poll-heartbeat.sh: line 515: syntax error near unexpected token `('
/repo/poll-heartbeat.sh: line 515: `      # a "0 promotion(s)" no-op every patrol_every_n ticks.'
```
canonical: bash -c "git show f4ec6d70:on-the-record/monitors/poll-heartbeat.sh > /tmp/orig_check/poll-heartbeat.sh && docker run --rm -v /tmp/orig_check:/repo:ro bash:3.2 bash -n /repo/poll-heartbeat.sh" — result: FAIL

Repo-wide structural-audit sweep (the same
`_find_command_substitution_wrapped_heredocs` logic that backs the
regression smoke), run twice — once with the original same-line regex,
once with the depth-tracking replacement — over every git-tracked
`*.sh` file:

```
scanned 188 .sh files (git-tracked)
0 command-substitution-wrapped heredocs found
```
canonical: python3 -c "import subprocess,re; exec(open('/tmp/heredoc_audit2.py').read())" — result: PASS

Both sweeps returned the same zero-hit result over the same 188-file
set: poll-heartbeat.sh's own now-removed heredoc was the only prior hit;
no other file in the tree carries the shape either request #3 or the
hunt's multi-line variant scans for.

## Skill obligations (issue #1960/#2039/#2062/#2153)

Mapped skills for this role
(implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice,
implementation-blueprint) were checked against this task; none were
invoked via the Skill tool this session:

- skill-verdict: implementation-complexity-coupling-management —
  not-applicable: no class/module coupling or cohesion metric is in
  play; this is a heredoc-to-file extraction with no caller-chain or
  import-direction change.
- skill-verdict: implementation-design-pattern-selection —
  not-applicable: no GoF-style pattern decision; nothing here is
  Strategy/Factory/Visitor/Observer/Decorator-shaped.
- skill-verdict: implementation-performance-data-structure-choice —
  not-applicable: no data structure, algorithm, or communication-scheme
  choice with a performance cliff; the extracted script's own logic is
  unchanged from the heredoc's.
- skill-verdict: implementation-blueprint — not-applicable: the issue
  itself named the two acceptable structural fixes (move comments out of
  the heredoc, or extract the Python to its own file); picking between
  them was not an open architecture decision needing the archetype
  database, and the change is one cohesive unit, not a multi-module
  design spanning independent parallel workers.

other mounted skills: not triggered.
