# Current-state survey — issue #1719

## Scouting

Skipped: pure bugfix / spec leaves no design decision open — issue #1719's
own body gives the exact acceptance checks and the exact clause of the
existing #1220 delta-suppression block to change (remove `returned-pr`
from `ALWAYS_RE`, age-strip its comparison, treat one board-sweep skip
message as no-change). This is an internal Monitor-emission regex/logic
fix with no product-category or external-comparison surface to scout.

## Write set

- `on-the-record/monitors/poll-heartbeat.sh` — the embedded Python
  delta-suppression block (issue #1220), lines 220-308.
- `on-the-record/monitors/test_poll_heartbeat.py` — named directly by the
  issue as the file that must assert both acceptance checks.
- `gates/test_poll_heartbeat_delta.py` — carries an existing regression
  test that asserts the exact behavior #1719 supersedes (see below); it
  must be updated in the same change or it goes red.

## What exists today

canonical: on-the-record/monitors/poll-heartbeat.sh:220-308 (read directly)
The due branch's captured watchdog report is split into `[tag] key:`-keyed
lines (`TAG_RE`, line 231, covering
`poll-report|watchdog|health|reconcile|orphaned|resume|watchdog-crash|returned-pr`),
diffed against `runs/poll_heartbeat_last_state.json`'s previous tick.
Unchanged keys print nothing; new/changed keys print their line.

canonical: on-the-record/monitors/poll-heartbeat.sh:234-240 (read directly)
`ALWAYS_RE` currently matches a fixed pattern:

```
^\[(resume|orphaned|watchdog-crash|returned-pr)\]|STALLED|CRASHED|COMPLETED|watcher-dead
```

`returned-pr` is one of the four bracket-tag alternatives in that pattern
(issue #1239 req 2), so a `[returned-pr]` line prints on every due tick
regardless of whether its text changed.

canonical: spawn.py:1313-1324 (read directly)
`_print_returned_pr_surfaced` renders each undisposed PR as
`[returned-pr] issue #{issue} ({phase}): age={age}h — {url}` (line 1322).
`age` is recomputed from `createdAt` every call
(`spawn.py:1301-1308`), so it advances every tick even when the
underlying (issue, phase, url) triple is unchanged — this is what makes
the current `ALWAYS_RE` membership fire every tick: the line's *text*
changes each time purely from age, and even when the raw text happened to
be byte-identical `ALWAYS_RE` would still force the emit.

canonical: on-the-record/monitors/poll-heartbeat.sh:284-288 (read directly)
The emit decision is
`if first_tick or prev_lines.get(key) != line or ALWAYS_RE.search(line): to_emit.append(line)`
— a plain string compare of the full stored line, no field-level
normalization for any tag.

canonical: on-the-record/monitors/poll-heartbeat.sh:290-301 (read directly)
When `to_emit` is empty, a bounded ~30min heartbeat
(`now - last_emit_epoch >= 1800`) prints one fixed line
(`[heartbeat] monitoring active, {healthy} session(s) tracked, no changes`)
and nothing else — it does not currently include the current
`[returned-pr]` set, so an unchanged-but-present returned-pr item would
go fully invisible once it stops being always-emitted, unless this
heartbeat is extended to list it.

canonical: spawn.py:3086-3103 (read directly)
`_board_wide_sweep_all`'s per-target loop prints a line starting exactly
with `[watchdog] board-sweep: {label}` in two cases: not-a-board target
(line 3091) and lock-contention skip (line 3096):

```
f"[watchdog] board-sweep: {label} 건너뜀 (다른 워크스페이스가 스윕 중) — {lock_msg}"
```

A successful sweep's actual result lines (no-change/full-rescan/delta/etc,
`spawn.py:3177-3338`) are captured via `contextlib.redirect_stdout` and
re-printed with an `f"[{label}] {line}"` wrapper (`spawn.py:3101-3102`),
so they carry a different leading token than the raw `[watchdog]` prefix
by the time they reach `poll-heartbeat.sh`'s `TAG_RE`.

canonical: on-the-record/monitors/poll-heartbeat.sh:231 (read directly)
`TAG_RE` keys any line matching `^\[(watchdog|...)\]\s*([^:]+):` as
`watchdog:{group(2)}`; both the not-a-board line and the lock-skip line
key to the same `watchdog:board-sweep` since `group(2)` only captures up
to the first colon (`"board-sweep"`). Two watchdogs contending for the
same cross-workspace sweep lock (`cross_workspace_board_sweep_lock_acquire`,
`spawn.py:3094`) therefore makes this key's stored line alternate between
a real sweep-result line and the skip message tick to tick, which is a
change under plain string compare every time it happens.

## What already tests this file

canonical: on-the-record/monitors/test_poll_heartbeat.py (read directly, 337 lines)
Exercises `poll-heartbeat.sh` end-to-end via a fake `spawn.py` and
`POLL_HEARTBEAT_MAX_TICKS=1` per subprocess call; no existing test in this
file drives two ticks against the same checkout, so none currently
exercises the delta-suppression comparison itself (only single-tick
capture/attachment/patrol behavior).

canonical: gates/test_poll_heartbeat_delta.py (read directly, 333 lines)
This is the dedicated delta-suppression suite (issue #1220), and already
has the multi-tick-against-the-same-checkout harness pattern
(`_run_tick`, called 2-3x per test with the same `checkout`/`home`) that
the new returned-pr/board-sweep cases need.

canonical: gates/test_poll_heartbeat_delta.py:230-255 (read directly)
`t_returned_pr_line_always_emits_even_unchanged` asserts the exact
behavior issue #1719 supersedes: a byte-identical `[returned-pr]` line
re-emitting on ticks 2 and 3. This test breaks once `returned-pr` leaves
`ALWAYS_RE` and needs rewriting to assert the new behavior (unchanged age
-> no re-emit; a genuine set change -> emits) in the same change.

## Unknowns

canonical: on-the-record/monitors/poll-heartbeat.sh:284-306 (read directly)
The issue text does not settle whether a *disposed* returned-pr item (one
present in the previous tick's state but absent from the current tick's
report because the PR was closed/merged) should print an explicit
"removed" line. The whole diff loop (lines 284-306) has no branch that
emits a line for a key present in `prev_lines` but absent from `curr` —
for every existing category (`[health]`, `[reconcile]`, `[poll-report]`
included) a vanished key just stops appearing next tick. The proposal
treats "disposed" as covered by that same existing, uniform
absence-based behavior instead of adding a new removed-key code path.
