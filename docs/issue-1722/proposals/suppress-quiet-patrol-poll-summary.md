---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
---

## Request

Scouting skip: pure bugfix — issue #1722 names the exact line and the
exact acceptance checks (`docs/issue-1722/reports/implementation/survey.md`
"Scouting").

After #1719, `poll-heartbeat.sh` is quiet on a due tick when nothing
changed — except the patrol block's own trace. `[patrol-poll] checked N
role(s), 0 promotion(s)` prints unconditionally every
`POLL_HEARTBEAT_PATROL_EVERY_N` ticks (default 5, i.e. every 10 minutes),
deliberately outside the #1220 delta-suppression state (#1598 patrol
wiring E2). Because every Monitor line wakes the receiving session for a
full model turn, this one line keeps waking the orchestrator every 10
minutes with nothing to act on. #1722 asks that this summary line print
only when there's something to act on (a promotion, a crash, or the
kill-switch), while the patrol itself keeps running and logging exactly
as today.

## Constraints

- A patrol-due tick with zero promotions and no crashed/disabled role
  must write nothing to Monitor stdout for patrol (issue Acceptance
  check 1) — the patrol still runs (`gates/patrol_promote.py` is still
  invoked per role) and its crash-path logging to
  `~/.claude/tokenmaxxxer/poll-watchdog.log` is unaffected.
- A patrol-due tick with at least one promotion, a crashed role, or the
  kill-switch (`.on-the-record/patrol-disabled`) must keep printing its
  existing `[patrol-poll] ...` line(s) unchanged (issue Acceptance
  check 2).
- Untouched: `POLL_HEARTBEAT_PATROL_EVERY_N`'s cadence, the per-role
  crash line, the per-role promotion line, and the `disabled, skipped`
  line (issue empty-state clause).
- Minimal diff (task instruction): no new files, no new state.

## Rationale

**Crash + zero-promotions interaction on the summary line.** Two
readings of "print the summary line only when M > 0" were on the table:

1. **Gate strictly on `_patrol_promotions != 0`** (rejected): the
   simplest reading of the task's short paraphrase. But issue Acceptance
   check 1's suppression condition is explicitly conjunctive — "zero
   promotions *and* no crashed/disabled role" — meaning a crash alone
   (even with 0 promotions) is *not* one of the conditions under which
   the summary line disappears. A promotions-only gate would newly
   suppress the summary line on a crashed/zero-promotions tick, which
   contradicts check 2's "still prints its existing line(s) unchanged"
   for the crashed case (before this fix, the summary line was
   unconditional, so "unchanged" includes it).
2. **Gate on `_patrol_promotions != 0 OR any role crashed this tick`**
   (chosen): add a single `_patrol_crashed` flag, set when any role's rc
   is non-zero, and print the summary line when promotions are nonzero
   or a crash occurred. This satisfies both acceptance checks literally:
   suppressed only in the conjunctive zero-promotions-and-no-crash case,
   and unchanged whenever a promotion or crash happened. The
   `.on-the-record/patrol-disabled` kill-switch case is unaffected
   either way — it's an early branch (line 367) that never reaches the
   role loop or the summary line printf, in both the current code and
   this change.

**Failure signal.** If this proposal is wrong, the signal is either of
the two new `on-the-record/monitors/test_poll_heartbeat.py` assertions
failing against the actual `poll-heartbeat.sh` output, or a live session
still seeing the summary line on an otherwise-silent due tick after this
lands.

## What will be done

- In `poll-heartbeat.sh`'s patrol block (lines 365-401): initialize
  `_patrol_crashed=0` alongside the existing `_patrol_checked`/
  `_patrol_promotions` counters; set it to `1` in the existing non-zero-rc
  branch (line 376-383, otherwise untouched); wrap the final
  `printf '[patrol-poll] checked ...'` (line 399) in
  `if [ "${_patrol_promotions}" != "0" ] || [ "${_patrol_crashed}" = "1" ]; then ... fi`.
  Every other line in the block (the per-role crash printf, the per-role
  promotion printf, the disabled/skipped printf, `_poll_watchdog_log_append`
  calls) is untouched.
- In `on-the-record/monitors/test_poll_heartbeat.py`:
  - Rewrite `t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior`'s
    final assertion: it currently pins the pre-fix always-print behavior
    (`"[patrol-poll] checked 0 role(s), 0 promotion(s)" in r.stdout`) for
    a zero-roles/zero-promotions/no-crash tick; assert the line's absence
    instead (`"[patrol-poll] checked" not in r.stdout`), matching issue
    Acceptance check 1.
  - Add a roles-configured fixture: a fake `spawn.py` exposing `ROLES`
    with its poll-due/watchdog CLI dispatch guarded behind
    `if __name__ == "__main__":` (so a plain `import spawn` for `ROLES`
    doesn't also trigger the existing fixture's module-level
    `sys.exit(0)`, per the survey's "What already tests this file"), and
    a fake `gates/patrol_promote.py` whose behavior (quiet / promote /
    crash) is selected via an env var, mirroring the existing
    `FAKE_WATCHDOG_REPORT` env-var-selected-fixture pattern already used
    by `_run_heartbeat`/`_run_tick`. Both fixtures are written through a
    single new shared helper (`_run_patrol_tick`), not one raw
    `subprocess.run` per new test (see Accumulation).
  - Add four new cases against that fixture: (a) roles configured, all
    quiet (zero promotions, no crash) -> no `[patrol-poll] checked` line,
    and `gates/patrol_promote.py` was actually invoked per role (proves
    "the patrol still runs" per Acceptance check 1's parenthetical); (b)
    a promotion -> the summary line prints with the correct counts,
    unchanged; (c) a crashed role -> both the per-role crash line and the
    summary line print, unchanged; (d) the kill-switch file present ->
    only `[patrol-poll] disabled, skipped` prints, no summary line,
    unchanged.

## Out of scope

- Any change to `gates/patrol_promote.py` itself, `POLL_HEARTBEAT_PATROL_EVERY_N`'s
  cadence semantics, or the #1220 delta-suppression state file — all
  named as unchanged by the issue's own empty-state clause.
- Adding new logging: the crash path's existing
  `_poll_watchdog_log_append` call is the only patrol-related log write
  today and is left exactly as-is; no new log-append call is added for
  the quiet or promotion cases.
- The due-branch (#1220/#1719) delta-suppression logic — patrol's
  trace is deliberately outside that state file (#1598 E2) and stays
  outside it.

## Accumulation

`on-the-record/monitors/test_poll_heartbeat.py` already sits at 3 raw
`subprocess.run(...)` call sites with no single shared invocation helper
(`_run_heartbeat`, `_run_tick`, and one standalone call inside
`t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior` that
predates both helpers and builds its own `env` dict inline) — crossing
`accumulation-claim-guard.sh`'s shape-1 threshold (this file had only 2
qualifying sites before #1719 added `_run_tick`). If new fixture needs
keep getting added as one more standalone `subprocess.run` block instead
of reuse, each carries its own copy-pasted env-dict setup
(`TOKENMAXXXER_CHECKOUT`, `FAKE_SPAWN_MARKER`, `POLL_HEARTBEAT_MAX_TICKS`,
`POLL_HEARTBEAT_SLEEP_SECONDS`, `HOME`, `CLAUDE_ROLE` pop) that drifts out
of sync as the script's own env surface changes (as already happened
once: `_run_tick` added `FAKE_POLL_DUE`/`FAKE_WATCHDOG_REPORT` handling
that the older standalone call site never picked up).

This proposal's four new patrol cases add exactly one new helper
(`_run_patrol_tick`), not four more raw call sites — the raw-call-site
count stays at 3 after this change, not 3+4. If patrol/heartbeat test
coverage keeps growing, the next N additions should extend
`_run_patrol_tick` (or consolidate it with `_run_tick`) rather than adding
a fifth standalone `subprocess.run`; past that point the three existing
non-consolidated call sites are the pre-existing debt this change does
not attempt to pay down (touching them is outside this issue's write
set).

## How you'll know it worked

- `python3 on-the-record/monitors/test_poll_heartbeat.py` — all tests
  pass, including the rewritten zero-roles case and the four new
  roles-configured cases.
