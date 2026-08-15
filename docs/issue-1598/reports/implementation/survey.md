# Survey — issue #1598 (patrol wiring E2)

canonical: this session's own `sed -n '150,320p' on-the-record/monitors/poll-heartbeat.sh` read.

## Heartbeat loop (#829 machinery)

File `on-the-record/monitors/poll-heartbeat.sh`, lines 165-311: a plain
bash `while true` loop. `tick=0` at line 165 is in-process only (not
persisted across process restarts). `sleep_seconds` defaults to 120s via
`POLL_HEARTBEAT_SLEEP_SECONDS` (line 167). Each iteration: sleep, write an
aliveness stamp, call `python3 spawn.py poll-due` (line 171); if due
(rc=0), run `spawn.py watchdog --auto-respawn` and emit a
delta-suppressed report via an embedded Python block reading/writing
`runs/poll_heartbeat_last_state.json`. Tick counter increments at line
308 (`tick=$((tick + 1))`), loop-bounded for tests by
`POLL_HEARTBEAT_MAX_TICKS` (lines 166, 309-310).

"Rearm" is a distinct, TTL-based concept, not a counter: `poll_due()` in
`spawn.py` (function definition around line 2358) stamps/checks a TTL
file, shared with the turn-driven hook `poll_rearm_arm_if_due()` in
`on-the-record/hooks/poll-rearm.sh`. It has no relationship to the shell
loop's `tick` variable.

canonical: this session's own `ls on-the-record/monitors/test_poll_heartbeat.py gates/test_poll_heartbeat_delta.py` read.

Existing tests pinning this behavior: `on-the-record/monitors/test_poll_heartbeat.py`
(base harness with a fake `spawn.py` stub) and `gates/test_poll_heartbeat_delta.py`
(delta-suppression across repeated invocations against
`runs/poll_heartbeat_last_state.json`). Both drive the real
`poll-heartbeat.sh` via `subprocess.run` with `POLL_HEARTBEAT_MAX_TICKS=1`
and a shortened `POLL_HEARTBEAT_SLEEP_SECONDS`.

## gates/patrol_promote.py

canonical: this session's own `sed -n '1,60p;250,345p' gates/patrol_promote.py` read.

CLI: `python3 gates/patrol_promote.py run <repo-root> <role> [--dry-run] [--queue PATH] [--date ISO]`,
entry `main()` at line 335, core logic `run_patrol_promote(root, role,
queue_path, dry_run, now_iso)` at line 262.

ETag-conditional read is delegated to `patrol_board.find_board_issue(root, role)`
in `gates/patrol_board.py`, lines 208-262: caches etag+raw JSON at
`.git/gh-read-cache/patrol-board-{role}.json`, sends `If-None-Match`, and
treats HTTP 304 (gh exits rc=1 on 304 — status must be parsed from the `-i`
output before checking `returncode`, lines 238-240) as 0 billed calls.

"Roles without a board issue" are already handled as a zero-op return, not
an exception: in `gates/patrol_promote.py` lines 269-272, `new_body =
issue.get("body") if issue else None`; when `new_body is None` the
function returns immediately with empty `promotions`/`deferred` and no
further calls or state writes. Calling `run_patrol_promote` per role
therefore already no-ops correctly for a role with no board issue, at the
cost of the one lookup call `find_board_issue` makes (itself
ETag-conditional, so a steady-state no-board role costs 0 calls after the
first lookup populates the negative-cache etag path).

canonical: this session's own `grep -rn "patrol_promote" --include=*.py --include=*.sh .` run, zero hits outside gates/patrol_promote.py and gates/test_patrol_promote.py.

No existing caller does role-existence filtering before invoking
`patrol_promote` today — it is invoked only by its own CLI/tests, never
wired into `poll-heartbeat.sh` or `spawn.py`.

Role list to iterate: `spawn.ROLES`, defined in `spawn.py` around lines
846-852, the existing canonical role tuple used elsewhere in this repo for
per-role board scanning.

## Kill-switch `.on-the-record/patrol-disabled`

canonical: this session's own `grep -rn "patrol-disabled" .` run, zero hits repo-wide.

E1/#1597 has not landed on this branch's working tree as of this survey.
No existing kill-switch-file convention elsewhere in this repo to imitate
a string/path pattern from — a `grep -rn "disabled" gates/ on-the-record/
--include=*.py --include=*.sh` shows only unrelated uses in
`gates/patrol_board.py`, `gates/patrol_queue.py`, `gates/check_runner.py`,
none of which are a kill-switch file check. Per the issue text, this
session builds directly against the `.on-the-record/patrol-disabled` path
(plain existence check, not content) without waiting for E1, per the
issue's explicit "parallel-safe, no ordering dependency" note.

## Docs layout

canonical: this session's own `ls docs/` run.

Top-level standing buckets present: `reports/`, `proposals/`, `decisions/`,
`handbooks/`, `specs/`, matching contract v3's per-issue layout. This
issue's own tree is created fresh as part of this survey write.
