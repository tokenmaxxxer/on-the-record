---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/monitors.json
  - README.md
  - on-the-record/monitors/test_poll_heartbeat.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

Subject: issue-1724

## What was done

Executed `docs/issue-1724/proposals/otr-monitor-off-kill-switch.md`'s
build steps.

- In `on-the-record/monitors/poll-heartbeat.sh`: added
  `case "${OTR_MONITOR_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac`
  immediately after the existing `ORCHESTRATE_OFF` case line, and
  extended the header comment's "Kill switch: ORCHESTRATE_OFF=1" note to
  also name `OTR_MONITOR_OFF=1` as the monitor-only counterpart.
- In `on-the-record/monitors/monitors.json`: extended the `description`
  string to name `OTR_MONITOR_OFF=1` (monitor-only kill switch)
  alongside the existing `POLL_HEARTBEAT_SLEEP_SECONDS` mention.
- In `README.md`: added a `### Monitor` subsection under
  `## Interaction flow`, alongside the existing spawn/rulebook
  subsection, naming both `OTR_MONITOR_OFF=1` and
  `POLL_HEARTBEAT_SLEEP_SECONDS` as the two operator knobs and
  `.claude/settings.local.json`'s `env` block as the recommended place
  to set them, with a minimal JSON snippet showing that block's shape.
- In `on-the-record/monitors/test_poll_heartbeat.py`: extended
  `_run_heartbeat`'s env-dict construction with
  `env["OTR_MONITOR_OFF"] = env_extra.get("OTR_MONITOR_OFF", "")`
  (unconditional normalization, mirroring how it already normalizes
  `POLL_HEARTBEAT_SLEEP_SECONDS`/`POLL_HEARTBEAT_MAX_TICKS` and pops
  `CLAUDE_ROLE`), then added two new tests:
  `t_heartbeat_respects_monitor_only_kill_switch` (`OTR_MONITOR_OFF=1` ->
  `returncode == 0`, `r.stdout == ""`, the watchdog marker never
  written, and `${CHECKOUT}/runs/` never created) and
  `t_heartbeat_orchestrate_off_alone_still_stops_monitor`
  (`ORCHESTRATE_OFF=1` alone, with `OTR_MONITOR_OFF` normalized to
  unset by the fixed helper, still stops the monitor as before).

canonical: on-the-record/monitors/poll-heartbeat.sh:33-49,
on-the-record/monitors/monitors.json:5,
on-the-record/monitors/test_poll_heartbeat.py:72-90,221-276 (working
tree, this session's own edit, read directly).

derived: `git diff --stat -- on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/monitors.json README.md on-the-record/monitors/test_poll_heartbeat.py`
```
 README.md                                     | 24 +++++++++++++
 on-the-record/monitors/monitors.json          |  2 +-
 on-the-record/monitors/poll-heartbeat.sh      |  6 +++-
 on-the-record/monitors/test_poll_heartbeat.py | 49 +++++++++++++++++++++++++++
 4 files changed, 79 insertions(+), 2 deletions(-)
```
No file outside the proposal's frozen write set was touched.

## Why

Issue #1724: Claude Code has no per-monitor on/off setting, so the
plugin Monitor (`poll-heartbeat.sh`, `when: "always"`) arms in every
interactive session of any repo with the plugin installed. The existing
`ORCHESTRATE_OFF=1` kill switch stops every hook, more than an operator
who only wants a quiet session needs; `POLL_HEARTBEAT_SLEEP_SECONDS`
stretches the cadence but cannot stop due-tick output entirely. A
second, narrower, monitor-only kill switch closes that gap.

canonical: `gh issue view 1724` (executed this session).

## Upstream / basis

Based on: docs/issue-1724/proposals/otr-monitor-off-kill-switch.md
(approved via `APPROVE issue-1724/implementation` on the issue), itself
based on docs/issue-1724/reports/implementation/survey.md's current-state
read of `poll-heartbeat.sh` and `test_poll_heartbeat.py`.

## What did not work

canonical: acceptance: python3 on-the-record/monitors/test_poll_heartbeat.py — result: fail (1, pre-existing and unrelated; full output in Acceptance verification below)
None outstanding. Both new tests and the four write-set edits applied
on the first attempt with no rewrite or discarded approach along the
way.

## Acceptance verification

canonical: acceptance: python3 on-the-record/monitors/test_poll_heartbeat.py — result: fail (1, pre-existing and unrelated; full output below)

derived: `python3 on-the-record/monitors/test_poll_heartbeat.py` (this session, with this diff applied)
```
ok  t_board_sweep_lock_skip_treated_as_no_change
ok  t_heartbeat_arms_watchdog_when_due
ok  t_heartbeat_attaches_on_board_repo
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
FAIL t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior: poll-heartbeat.sh should exit 0: .../poll-heartbeat.sh: line 163: flock: command not found
ok  t_returned_pr_new_item_emits_on_due_tick
ok  t_returned_pr_unchanged_set_produces_no_output_on_due_tick

1/18 failed: ['t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior']
```
Both `t_heartbeat_respects_monitor_only_kill_switch` and
`t_heartbeat_orchestrate_off_alone_still_stops_monitor` show `ok` above.

derived: `git stash && python3 on-the-record/monitors/test_poll_heartbeat.py; git stash pop` (this session, pre-edit baseline check against unmodified HEAD)
```
1/16 failed: ['t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior']
```
canonical: derived: the two fenced `test_poll_heartbeat.py` runs immediately above (this session, pre-edit and post-edit)
The same `flock: command not found` failure appears in both fenced runs above — the unmodified pre-edit tree and this diff — a pre-existing macOS-sandbox gap (no GNU `flock` binary here), unrelated to this change.

canonical: on-the-record/monitors/monitors.json:5, README.md (new
`### Monitor` subsection) (working tree, this session's own edit, read
directly).
Acceptance checks, cross-referenced against the runs above:
- with `OTR_MONITOR_OFF=1`, `poll-heartbeat.sh` exits 0 before its first
  sleep, writes nothing to stdout, and touches no `runs/` state file:
  `t_heartbeat_respects_monitor_only_kill_switch`, `ok` above.
- `monitors.json`'s description and the README's monitor section name
  both `OTR_MONITOR_OFF=1` and `POLL_HEARTBEAT_SLEEP_SECONDS`, with
  `.claude/settings.local.json`'s `env` named as the recommended place
  to set them: `monitors.json`/`README.md` diff cited just above.
- empty state (unset or `0/false/no/off` identical to today,
  `ORCHESTRATE_OFF=1` alone still stops the monitor):
  `t_heartbeat_orchestrate_off_alone_still_stops_monitor` and the
  untouched `t_heartbeat_respects_kill_switch`, both `ok` above.

## Test-tier note (issue #1518)

```
$ cat .on-the-record/test-tiers.json
{
  "fast": { "command": "python3 -m pytest -q -m \"not slow\"", "budget_seconds": 300 },
  "slow": { "command": "python3 -m pytest -q -m slow",
    "trigger_change_classes": ["spawn.py", "tests/test_spawn.py", "on-the-record/hooks/*.sh", "on-the-record/hooks/test_*.py"] }
}
```
This change touches `on-the-record/monitors/*` and `README.md`, neither
`spawn.py` nor `on-the-record/hooks/*` — the `slow` tier's
`trigger_change_classes` do not match. Ran the direct script invocation
the issue's own Acceptance section names as the assertion mechanism
(`python3 on-the-record/monitors/test_poll_heartbeat.py`, shown above)
rather than the repo-wide `fast` tier, since the issue scopes
verification to this one file specifically.

## Hunt

Dispatched `warrant:warrant-hunter` before phase-2 completion (contract
hunt cadence), on top of the phase-1 hunt already folded into the
proposal.

canonical: docs/issue-1724/reports/implementation/2026-08-17-hunt-otr-monitor-off-kill-switch.md ("before-landing — stance 2" section, committed this session, hunter's own record)
No finding. The hunter re-verified the phase-1 finding (ambient `OTR_MONITOR_OFF` masking a regression via `_run_heartbeat`) is fixed by this diff's normalization.

canonical: docs/issue-1724/reports/implementation/2026-08-17-hunt-otr-monitor-off-kill-switch.md ("before-landing — stance 2" section, committed this session, hunter's own record)
It also confirmed the new case-guard's placement and its character-for-character match with `ORCHESTRATE_OFF`'s pattern list, and confirmed `_run_tick`/`_run_patrol_tick`'s lack of the same normalization is a pre-existing, symmetric gap shared with `ORCHESTRATE_OFF` that fails loudly rather than masking silently, so it is unrelated to this diff.

closed_checks:
- check: the new `OTR_MONITOR_OFF` case-guard sits before any
  stdout/state-touching statement in `poll-heartbeat.sh`, mirroring
  `ORCHESTRATE_OFF`'s placement.
  code_sha: on-the-record/monitors/poll-heartbeat.sh (working tree, this
  session)
- check: the two switches' case-list patterns (`""|0|false|no|off`) are
  byte-identical, no typo-driven asymmetry between them.
  code_sha: on-the-record/monitors/poll-heartbeat.sh (working tree, this
  session)
- check: `_run_heartbeat`'s new `OTR_MONITOR_OFF` normalization closes
  the phase-1-hunt masking hole; `_run_tick`/`_run_patrol_tick`'s lack of
  the same normalization is a pre-existing, symmetric gap shared with
  `ORCHESTRATE_OFF`, not a new masking defect.
  code_sha: on-the-record/monitors/test_poll_heartbeat.py (working tree,
  this session)

## Open findings

None.
