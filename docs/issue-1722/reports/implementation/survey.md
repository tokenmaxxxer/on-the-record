# Current-state survey — issue #1722

## Scouting

Skipped: pure bugfix — issue #1722's own body names the exact line to
gate (`[patrol-poll] checked N role(s), M promotion(s)`) and the exact
acceptance checks, and also self-labels `validity-consult-skip: trivial`
and `design-research-skip: mechanical`. This is an internal
Monitor-emission conditional fix with no product-category or
external-comparison surface to scout.

## Write set

- `on-the-record/monitors/poll-heartbeat.sh` — the patrol-poll block,
  lines 365-401.
- `on-the-record/monitors/test_poll_heartbeat.py` — named directly by the
  issue as the file that must assert both acceptance checks.

## What exists today

canonical: on-the-record/monitors/poll-heartbeat.sh:365-401 (read directly)
Every `patrol_every_n`th tick (default 5, `POLL_HEARTBEAT_PATROL_EVERY_N`),
this block runs unconditionally (independent of the due-branch above it).
If `.on-the-record/patrol-disabled` exists it prints
`[patrol-poll] disabled, skipped` and stops — an early branch that never
reaches the role loop or the summary line, unchanged by this issue.
Otherwise it loops `POLL_HEARTBEAT_PATROL_ROLES[@]`, invoking
`gates/patrol_promote.py run <checkout> <role>` per role:

- non-zero rc (line 376): logs the crash detail to `poll-watchdog.log` via
  `_poll_watchdog_log_append` (line 382) AND unconditionally prints
  `[patrol-poll] {role}: crashed (rc=...)` to stdout (line 383) — both
  untouched by this issue.
- zero rc with non-empty output (line 384): parses it as
  `{"promotions": [...]}` and, only if the count is nonzero, prints
  `[patrol-poll] {role}: {count} promotion(s)` (line 395) — untouched.

canonical: on-the-record/monitors/poll-heartbeat.sh:399 (read directly)
After the loop, this line unconditionally prints
`[patrol-poll] checked {_patrol_checked} role(s), {_patrol_promotions} promotion(s)`
regardless of whether any promotion happened or any role crashed — this
is the line issue #1722 asks to gate on `M > 0`.

canonical: on-the-record/monitors/poll-heartbeat.sh:370-397 (read directly)
No flag currently tracks "did any role crash this tick" — `_patrol_checked`
and `_patrol_promotions` are the only running counters; a crash
increments `_patrol_checked` but never `_patrol_promotions`.

## What already tests this file

canonical: on-the-record/monitors/test_poll_heartbeat.py:301-333 (read directly, 427 lines)
`t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior` is the
only existing test exercising the patrol block. Its fake `spawn.py` has
no `ROLES` constant and force-exits (`sys.exit(0)`) at module top level
during `import spawn`, before the inline python's `print(' '.join(spawn.ROLES))`
runs — so the role-list read yields an empty array (zero configured
roles), giving `_patrol_checked=0`, `_patrol_promotions=0`, no crash. Its
final assertion, `"[patrol-poll] checked 0 role(s), 0 promotion(s)" in
r.stdout`, pins exactly the always-print behavior issue #1722 asks to
change; it goes red under the fix unless rewritten to assert the line's
absence.

No existing test in this file drives a nonzero-promotion, a crashed-role,
or a kill-switch tick through the patrol block — the fake
`spawn.py`/`gates/patrol_promote.py` fixtures for those three cases (and
for a quiet tick with roles actually configured, not just zero roles)
don't exist yet and need adding. The existing fake `spawn.py`'s
sys.exit-on-import quirk (above) makes it unusable as a base for a
roles-configured fixture — a new fixture needs the poll-due/watchdog
dispatch guarded behind `if __name__ == "__main__":` so `import spawn`
for `ROLES` doesn't also trigger `sys.exit(0)`.

## Unknowns

The issue's acceptance text leaves one point implicit: whether the
summary line should still print on a crashed-role tick with zero
promotions. Acceptance check 1 gates suppression on "zero promotions
*and* no crashed/disabled role" (conjunctive), and check 2 says a
crashed-role tick "still prints its existing `[patrol-poll] ...` line(s)
unchanged" — before this fix *all* patrol-poll lines, including the
summary, were unconditional, so "unchanged" for a crash tick reads as
including the summary line too. See proposal Rationale for the resulting
design choice.
