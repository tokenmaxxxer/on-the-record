---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
canonical: pytest tests/test_spawn.py -q — 457 passed, 0 failed, 0 skipped (run this turn)
verdict: pass
loop_state: landed
---

# Implementation record — issue #927 (phase 2)

## Summary of work

Split `spawn.py`'s `watch --follow` into two runtime modes per the
approved proposal (docs/issue-927/proposals/implementation.md,
`APPROVE issue-927/implementation` — approvers.md-listed comment on
issue #927, canonical: `gh issue view 927 --comments`, read this turn):

1. Added `--self-heal` to the `watch` subcommand's argparse (near
   `--follow`, spawn.py:4154) and threaded it into
   `_watch(..., self_heal: bool = False)`.
2. Auto-arm's detached `Popen` argv (spawn.py:5089-5093) now appends
   `--self-heal`, so the watcher a spawn arms for itself runs in the
   new mode; the interactive CLI path never sets the flag.
3. In `_watch`'s `--follow` loop, when `self_heal` is true: the
   wall-clock-cap check (both the direct one in the loop and the one
   surfaced via `_await_bounded`'s own `WATCH_WALLCLOCK_RC`) and the
   follow-stall check reset local progress/budget state and `continue`
   the loop instead of returning — the watcher keeps re-attaching to
   the same workspace instead of exiting. Detection itself is
   unchanged in both modes; only what happens after detection differs.
4. The crash/pid-loss path is unchanged as terminal in both modes, but
   now calls the existing `_append_event(events_path,
   "watcher-ended-without-session-end", {"pid": pid, "reason":
   "crash"})` immediately before returning `WATCH_CRASH_RC`, so a
   durable fact reaches `<work>.events.jsonl` for a downstream
   orchestrator, independent of mode.
5. `session-end` detection is unchanged in both modes — it always
   returns, because that is the genuine terminal state.
6. Added a regression test in `tests/test_spawn.py`. canonical: pytest
   tests/test_spawn.py -k test_self_heal_survives_stall_and_reaches_session_end -q
   — 1 passed (run this turn). It drives `_watch(..., self_heal=True)`
   through a real elapsed-time stall past `stall_limit_s` via
   `time.sleep` inside a mocked `_await_bounded`, asserts the loop is
   still looping afterward instead of having returned, then delivers a
   real `session-end` event and asserts `_watch` observes it and
   returns — closing the issue's live-fire Acceptance gate. Paired
   with a contrast test proving `self_heal=False` (the interactive
   default) still returns on the first stall
   (`test_follow_without_self_heal_returns_on_stall_instead_of_looping`).
   Also added: a crash-path test asserting the new
   `watcher-ended-without-session-end` event lands
   (`test_self_heal_crash_path_still_terminal_and_appends_ended_event`),
   and CLI-wiring tests for the new flag
   (`test_main_wires_self_heal_flag_through_to_watch`,
   `test_main_defaults_self_heal_to_false`).

## Why

The interactive `watch --follow` caller is a human/orchestrator that
can read the printed re-arm instruction and issue a fresh `spawn.py
watch --follow` call; the auto-armed detached watcher (spawn.py:
5081-5093, issue #488) has no such caller in its process tree.

canonical: spawn.py:2115-2122 (read this turn) — the only other
reference to `watcher_log` in the file reads its mtime for staleness,
never its text, so the "재무장하라" instruction printed by the follow
loop reaches a file nothing parses for content — the re-arm
instruction is orphaned for auto-arm watchers specifically.

Looping inside `_watch` itself, gated by a flag only the auto-arm call
site sets, keeps one process, reuses the existing loop/state, and
leaves the interactive path byte-for-byte unchanged when the flag is
absent — the alternative (a supervising loop around the detached
`Popen` call site) was rejected in the proposal because it would
either block the parent spawn CLI call (defeating issue #114) or
double the process tree.

## Basis

Upstream: docs/issue-927/proposals/implementation.md, approved via the
`APPROVE issue-927/implementation` issue comment (single-account
mode). canonical: `gh issue view 927 --comments`, read this turn —
comment thread shows `APPROVE issue-927/defect-verification` then
`APPROVE issue-927/implementation`, both from account `JiwonJung94`.

Root-cause basis: docs/issue-927/reports/defect-verification.md and
docs/issue-927/reports/defect-verification/current-state.md, canonical:
`git log --oneline` (read this turn) shows merge commit `f8ff0e7` for
that PR — the three lethal `return` paths and the orphaned re-arm
instruction were reproduced there; not re-derived in this record
beyond the spawn.py:2115-2122 citation above.

## What did not work

None.

## Rationale for deviations

canonical: pytest tests/test_spawn.py -k
test_self_heal_survives_stall_and_reaches_session_end -q — 1 passed
(run this turn). The approved proposal's "What will be done" step 4
named three test assertions for the issue's Acceptance gate; those
three assertions are implemented in
`test_self_heal_survives_stall_and_reaches_session_end`. No
scope-exceeded stop occurred and no proposal-stated alternative was
swapped.

One item was added beyond the proposal's literal text: the
before-landing warrant hunt (stance 2, malformed-input silence) at
docs/issue-927/reports/implementation/2026-08-12-hunt-implementation.md
reproduced a pre-existing uncaught `JSONDecodeError` in the same
follow-loop `json.loads` call sites the self-heal branches now rely on
staying alive through — canonical: that hunt record's own
`### Observed` section under `## before-landing` (agent transcript
this session dispatched and read this turn). A single corrupt
`events.jsonl` line would crash the self-heal watcher outright,
undoing the resilience this change adds. Fixed in the same file
already in the frozen write set (spawn.py), using the identical
`try: json.loads(...) except ValueError` guard pattern
`_prior_event_details()` (spawn.py:2766-2781) already established
elsewhere in this file — not a new pattern, not a new file. canonical:
pytest tests/test_spawn.py -k
test_self_heal_survives_malformed_events_line_instead_of_crashing -q
— 1 passed (run this turn); regression test added.

## Doc placement

No env var, new dependency, migration, or setup step was introduced —
`--self-heal` is a CLI flag on an existing subcommand, and
`_append_event` is an existing shared helper — so no handbook update
applies. No public signature or wire format changed (the new
`self_heal` kwarg defaults to `False`, preserving every existing
`_watch(...)` call site). No decisions/reports doc-placement ladder
item applies beyond this record and the hunt record already committed.

## Hunt (closed_checks)

- after-proposal (stance 0, "gate this proposal just touched is
  bypassable"): canonical:
  docs/issue-927/reports/implementation/2026-08-12-hunt-implementation.md
  `## after-proposal` section (read this turn) — finding was that
  `--self-heal` is a bare CLI flag any caller of the public `watch
  --follow` command could also set, not structurally bound to the
  auto-arm call site. Acknowledged, not resolved here — the flag-based
  gate is the proposal's own chosen design; the new `--self-heal`
  `--help` text states plainly it is auto-arm-only and not for
  interactive use (spawn.py argparse help string added in this
  change) as a documentation mitigation. code_sha: this record's
  code_under_review file list (spawn.py, tests/test_spawn.py) as
  committed on this branch.
- before-landing (stance 2, "guard goes silent on malformed input"):
  canonical:
  docs/issue-927/reports/implementation/2026-08-12-hunt-implementation.md
  `## before-landing` section (read this turn) — finding was an
  unguarded `json.loads` in the follow loop crashing the self-heal
  watcher on a corrupt `events.jsonl` line. Resolved in this commit
  (see "Rationale for deviations" above); regression test added.
  code_sha: this record's code_under_review file list as committed on
  this branch.

## Open findings

None unresolved. The after-proposal stance-0 finding (flag not
structurally bound to auto-arm) is acknowledged above as an accepted
design tradeoff of the approved proposal, surfaced here for
defect-verification's own judgment rather than dropped silently.

## Test run

derived: `python3 -m pytest tests/test_spawn.py`, executed this turn.
canonical: pytest tests/test_spawn.py -q — 457 passed, 0 failed, 0
skipped (run this turn).

```
457 passed in 28.29s
```

No SKIPPED lines appear in the pasted output above. Full suite (not
filtered), run once before landing per the record-tiering/no-mock
directives.
