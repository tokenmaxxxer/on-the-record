---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
---

# Proposal — issue #927 implementation, step 1

## Request

The auto-armed detached `watch --follow` watcher `spawn.py` spawns per
spawn (spawn.py:5089-5091) plain-`return`s on stall (spawn.py:3556) and
wall-clock cap (spawn.py:3496) instead of the session actually ending —
the process dies, but nothing re-arms it, so downstream `session-end`
notifications silently stop while the session keeps running. Fix:
separate interactive `watch --follow` (caller re-arms, current
behavior unchanged) from auto-arm's own watcher (must self-heal —
loop and re-attach until a genuine `session-end` or a confirmed process
crash), via a mode flag. Crash (confirmed pid loss) still ends the
watcher, but now leaves a durable "ended without session-end" event.
Add a live-fire regression test proving an auto-arm watcher survives a
stall and still delivers the eventual real `session-end`.

## Constraints

- docs/issue-927/proposals/defect-verification.md (merged, PR #932)
  already verified the root cause live; this proposal implements its
  named fix shape, not a new diagnosis.
- Observation-loss regression guards are inviolable (issue text: "관측-손실
  회귀 가드는 불가침") — the fix must not weaken or remove any existing
  stall/wall-clock/crash detection; it only adds a self-heal loop and
  a durable crash-path event on top of what already fires.
- Interactive `watch --follow`'s current return-and-let-caller-rearm
  behavior must not change — only the auto-arm call path gains the
  loop, gated by a new flag.
- Write set stays inside `spawn.py` (survey confirmed it is the sole
  file constructing the auto-arm argv or referencing
  `WATCH_CRASH_RC`/`WATCH_WALLCLOCK_RC`) plus `tests/test_spawn.py` for
  the new live-fire regression test.

## Rationale

Considered making the auto-arm *caller* (the forked spawn.py parent)
poll `_watch`'s exit code and re-exec it in a shell loop, instead of
teaching `_watch` itself to loop. Rejected: the parent already returns
immediately after `Popen`-ing the detached watcher
(spawn.py:5093-5107) specifically so the spawning CLI call doesn't
block (issue #114, cited at spawn.py:5081-5083) — adding a supervising
loop there would mean either blocking that parent (defeating #114) or
spawning a second detached supervisor process, doubling the process
tree and the crash-detection surface for no benefit over looping
inside the one process that already owns the `while True:` and the
stall/progress state. Looping inside `_watch` itself, gated by a flag
the auto-arm call site sets, keeps one process, reuses the existing
loop and state, and leaves the interactive path byte-for-byte
unchanged when the flag is absent.

## What will be done

1. Add `--self-heal` to the `watch` subcommand's `argparse` parser
   (near `--follow`, spawn.py:4154) and thread it into `_watch(...,
   self_heal: bool = False)`.
2. In the auto-arm `Popen` argv (spawn.py:5089-5091), append
   `"--self-heal"` so the detached watcher it launches runs in the new
   mode; the interactive CLI path never sets this flag.
3. In `_watch`'s `--follow` loop (spawn.py:3475-3556), when
   `self_heal` is true:
   - wall-clock cap (spawn.py:3494-3497) and follow-stall
     (spawn.py:3553-3556): instead of returning, reset the loop's local
     progress/budget state (`last_progress`, and — for wall-clock — a
     fresh `follow_start`/`follow_budget_s` window) and `continue` the
     `while True:` loop, so the watcher keeps re-attaching to the same
     workspace's events/offset/log rather than exiting. Detection
     (the stall/wall-clock checks themselves) is untouched — only what
     happens after detection changes for this mode.
   - crash / pid loss (spawn.py:3548-3550): unchanged as a terminal
     exit in both modes (a dead session process ends the watcher
     either way), but immediately before `return WATCH_CRASH_RC`, call
     `_append_event(events_path, "watcher-ended-without-session-end",
     {"pid": pid, "reason": "crash"})` (using the existing
     `_append_event` helper, spawn.py:2760-2763, and the `events_path`
     already in scope, spawn.py:3437) so the fact reaches
     `<work>.events.jsonl` for a downstream orchestrator, independent
     of mode (both interactive and self-heal crash exits get this —
     it's a durable fact about the session, not a re-arm decision).
   - `session-end` detection (spawn.py:3505-3511) is unchanged in both
     modes: it always returns, ending the watcher, because that is the
     actual desired terminal state.
4. Add a regression test in `tests/test_spawn.py` that: (1) drives a
   real subprocess (or the smallest fixture that exercises `_watch`
   with `self_heal=True` end-to-end, matching the style of existing
   `test_follow_*` tests) through a stall past `stall_limit_s`, (2)
   asserts the watcher process/loop is still alive/looping afterward
   instead of having returned, and (3) then delivers a real
   `session-end` event and asserts `_watch` observes it and returns.
   This closes Finding 6 of the survey and the issue's Acceptance gate.

## Out of scope

- Any change to interactive `watch --follow`'s behavior when
  `--self-heal` is absent — it keeps returning on all three conditions
  exactly as today.
- Changing watchdog signal-5/signal-6 detection (spawn.py:2093-2123) —
  self-heal only changes what the watcher itself does after its own
  stall/wall-clock detection fires; the roster-side watchdog is
  unrelated read-only context (survey Finding 5).
- A durable event on the wall-clock/stall self-heal path — those are
  not terminal in self-heal mode, so there is no "ended" fact to
  record there; only the crash path (which is still terminal) gets the
  new event.
- issue #908's own silent-death gap (cited by the issue as an adjacent
  concern) beyond the one crash-path durable event this proposal adds.

## Accumulation

This proposal adds one new call site of the existing shared
`_append_event` helper (spawn.py:2760-2763) and one new `argparse`
flag — it does not introduce a new inline `subprocess`/`gh` invocation
pattern, and it does not touch any repeated-file-list surface (e.g.
`roles/*.json`). Future additional watcher exit conditions would follow
the same shape already established here (detect via existing loop
state, then either `continue` under `self_heal` or `_append_event` +
`return`), so no new accumulation cost is introduced by this change.

## How you'll know it worked

The new `tests/test_spawn.py` test (item 4) passes, proving an
auto-arm-mode watcher survives a stall boundary and still delivers a
subsequent real `session-end` — the exact shape of the issue's
Acceptance gate. Existing `test_follow_*`/`test_still_bounded_by_*`/
`test_max_wait_unset_*` tests continue passing unchanged, proving
interactive-mode behavior (the default, `self_heal=False`) is
unaffected. `python3 -m pytest tests/test_spawn.py` is run once, output
pasted into the phase-2 record, before landing.
