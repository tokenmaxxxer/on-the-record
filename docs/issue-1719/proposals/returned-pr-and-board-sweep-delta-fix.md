---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
  - gates/test_poll_heartbeat_delta.py
---

## Request

Scouting skip: pure bugfix / spec leaves no design decision open — issue
#1719 already names the exact clause to change and the exact acceptance
checks (`docs/issue-1719/reports/implementation/survey.md` "Scouting").

`poll-heartbeat.sh`'s #1220 delta-suppression block puts `[returned-pr]`
in its always-emit set (`ALWAYS_RE`), so an undisposed phase-1 PR's line —
which always changes tick to tick because it carries a recomputed
`age=N.Nh` — wakes the orchestrator session on every due tick even when
nothing about the item itself changed. A second, independent source of
the same symptom: two watchdogs contending for the same board-sweep lock
make `[watchdog] board-sweep: ...` alternate between a real result and a
"다른 워크스페이스가 스윕 중" skip line, which a plain string diff reads
as a change every time it happens. #1719 supersedes #1239 req 2's "every
tick" wording for `[returned-pr]` and asks that both stop flapping the
delta state while an operator decision remains visible on arrival, on any
real change, and on the existing ~30min bounded heartbeat.

## Constraints

- `[returned-pr]` additions and removals from the tracked set must still
  emit; only an unchanged set with `age=` alone advancing may go silent
  (issue Acceptance check 1).
- The ~30min bounded heartbeat must still list the current undisposed-PR
  set even when nothing changed, so northpole req#1 ("never missed") is
  preserved without per-tick re-announcement.
- The board-sweep lock-contention skip line must be treated as no-change:
  not emitted, and the previously known board-sweep line kept in state
  rather than overwritten by the skip text (issue Acceptance check 2).
- Untouched: crash/dead/orphaned/resume always-emit categories,
  `ORCHESTRATE_OFF=1`, and the 120s cadence (issue empty-state clause).
- No new state file and no new files beyond the three above (issue:
  "Minimal diff, no new files beyond the record").

## Rationale

**Age comparison.** Two approaches were on the table for detecting a
"real" returned-pr change versus mere age drift:

1. **Regex-strip the `age=N.Nh` token before comparing the stored line
   text** (chosen): normalize both the previous and current line with
   `age=[^ ]+` -> `age=` before the equality check, keeping the existing
   one-line-keyed-state design (every category already stores/compares
   its rendered line as a single string) uniform across all tags.
2. **Parse each `[returned-pr]` line into structured fields (issue,
   phase, url) and diff those instead of text** (rejected): this would
   require a second, returned-pr-specific parser and a second shape of
   stored state, alongside the plain-string `curr`/`prev_lines` map every
   other category already uses. A one-line regex substitution reaches the
   same result without forking the file's storage model for one tag.

**Board-sweep skip handling.** Two approaches were on the table:

1. **Carry the previous line forward when the skip pattern matches**
   (chosen): when `[watchdog] board-sweep: ...` matches the lock-skip
   text, write `prev_lines[key]` (if any) back into the new state under
   the same key instead of the skip text, and never emit it. This reuses
   the existing `lines` dict with no schema change.
2. **Add a dedicated `last_real_board_sweep` field to the persisted JSON**
   (rejected): a second top-level key just for this one tag grows the
   state schema for a single edge case, where carry-forward inside the
   existing per-key comparison achieves the same "previous sweep state
   kept" outcome with no new field.

**Failure signal.** If this proposal is wrong, the signal is either of
the two new `on-the-record/monitors/test_poll_heartbeat.py` assertions
failing against the actual `poll-heartbeat.sh` output, or a live session
still seeing an unchanged returned-pr age wake it on a due tick after
this lands.

## What will be done

- In `poll-heartbeat.sh`'s embedded Python delta block: drop
  `returned-pr` from `ALWAYS_RE` (it keeps `resume`, `orphaned`,
  `watchdog-crash`, and the bare STALLED/CRASHED/COMPLETED/watcher-dead
  keywords, unchanged).
- Add an `age=[^ ]+` stripping regex, applied only when a line's tag is
  `returned-pr`: compare the age-stripped previous and current line to
  decide `changed`; a brand-new key (no previous entry) always counts as
  changed, so additions still emit. A key's disappearance from the
  current tick's report is unchanged: still nothing dedicated printed for
  it (matches every other category's existing absence-based behavior, per
  the survey's "Unknowns" note).
- Add a `BOARD_SWEEP_LOCK_SKIP_RE` matching the exact
  `[watchdog] board-sweep: ... 건너뜀 (다른 워크스페이스가 스윕 중)`
  text; when a line matches it, never add it to `to_emit`, and store
  `prev_lines.get(key, line)` (i.e. the previously known line, falling
  back to the skip text only if nothing was ever recorded) under that key
  in the new state instead of the skip text itself.
- Extend the ~30min bounded-heartbeat branch (fires only when nothing
  else emitted) to append the current tick's `[returned-pr]` lines, if
  any, after the fixed `[heartbeat] ...` line — so the undisposed-PR set
  stays visible on that existing bound even while otherwise fully
  suppressed.
- Add to `on-the-record/monitors/test_poll_heartbeat.py`, reusing the
  existing two-ticks-against-the-same-checkout pattern already
  established in `gates/test_poll_heartbeat_delta.py`'s `_run_tick`:
  (a) an unchanged returned-pr set across two ticks (same issue/phase/url,
  different `age=`) produces empty stdout on tick 2; (b) a returned-pr set
  that gains a new issue between two ticks emits the new issue's line on
  tick 2; (c) a board-sweep lock-skip line on tick 2, following a real
  sweep-result line on tick 1, is not emitted on tick 2, and a tick 3
  identical to tick 1's real result is also not emitted (state was kept,
  not flapped).
- Update `gates/test_poll_heartbeat_delta.py`'s
  `t_returned_pr_line_always_emits_even_unchanged` (lines 230-255): it
  currently asserts the exact "every tick" behavior this issue supersedes
  (issue #1239 req 2, explicitly retired by #1719's own text). Rewrite it
  to assert the superseding behavior instead — an unchanged returned-pr
  line does NOT re-emit on ticks 2/3, while a genuine set change still
  does — so the suite does not go red for a reason the issue itself
  documents as intentional.

## Out of scope

- Any change to `spawn.py`'s `_print_returned_pr_surfaced` or
  `_board_wide_sweep_all` — the line formats and sweep/lock logic they
  produce are untouched; only how `poll-heartbeat.sh` consumes those
  lines for delta purposes changes.
- The crash/dead/orphaned/resume always-emit categories, `ORCHESTRATE_OFF`,
  and the 120s/`POLL_HEARTBEAT_SLEEP_SECONDS` cadence (issue's own
  empty-state clause).
- Adding removed-key detection for any category, including `[returned-pr]`
  itself — a disposed item's line simply stops appearing, matching every
  other category's existing behavior (survey "Unknowns").
- A new persisted state file or schema field beyond the existing
  `runs/poll_heartbeat_last_state.json` `lines`/`last_emit_epoch` shape.

## How you'll know it worked

- `python3 on-the-record/monitors/test_poll_heartbeat.py` — all tests
  pass, including the three new cases described above.
- `python3 gates/test_poll_heartbeat_delta.py` — all tests pass,
  including the rewritten `t_returned_pr_line_always_emits_even_unchanged`
  and the untouched STALLED/CRASHED/watcher-dead always-emit regression
  guards (`t_dead_session_line_always_emits_even_unchanged`).
