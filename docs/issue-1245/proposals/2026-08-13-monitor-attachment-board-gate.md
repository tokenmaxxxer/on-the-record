---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
---

## Request

#1219's landed fix anchors the watchdog's *scan* to the session's target
repo once it runs. The operator's separate, still-open widened ask from
that issue (posted mid-build, deferred out of #1219's own write set): a
session on a foreign repo that is not an on-the-record board (no
`docs/specs/approvers.md`) should never get the plugin Monitor attached at
all — no roster/alive-marker registration, no ticks — not merely "scan
output that happens to be empty or scoped."

## Constraints

- Board-repo sessions (target repo has `docs/specs/approvers.md`) keep
  today's behavior byte-for-byte: same alive marker, same tick cadence,
  same due-tick watchdog invocation and output shape.
- Tests must assert absence of registration *artifacts*
  (`.orchestrate-monitor-alive/`, `runs/poll_heartbeat_last_state.json`,
  `~/.claude/tokenmaxxxer/poll-watchdog.log`), not merely absence of stdout
  — per the issue's explicit acceptance framing and the #1219 incident
  (absence-of-visible-output tests already proved insufficient once).
- No new `gh`/network call, no new dependency — the board check is a local
  file-presence test against a constant path already used elsewhere
  (`spawn.py`'s `MARKER = "docs/specs/approvers.md"`).
- `ORCHESTRATE_OFF=1`'s existing kill switch and the `CHECKOUT`-unresolvable
  early-exit both keep taking priority over (i.e., run before) the new
  board check — they are existing "never attach" paths this change must not
  narrow.

## Rationale

Considered duplicating the check inside `spawn.py`'s `roster_watchdog()` /
CLI `watchdog` dispatch instead of in `poll-heartbeat.sh`. Rejected: by the
time `spawn.py watchdog` runs, the Monitor has already attached — the
`.orchestrate-monitor-alive/` marker (the registration artifact
`directive.sh` reads back to decide whether to show the degradation notice)
is written by `poll-heartbeat.sh` itself, before `spawn.py` is ever
invoked, and only on a *due* tick does `spawn.py watchdog` run at all.
Gating inside `spawn.py` would still leave every non-due tick's marker
write and cadence loop running unconditionally for a non-board target
repo — exactly the "machinery the session never asked for" the issue names
as the prior cost. The only point that sees every tick, including the
very first one, before any registration artifact is written, is the top of
`poll-heartbeat.sh` — so the gate belongs there.

## What will be done

- In `on-the-record/monitors/poll-heartbeat.sh`, add a board-presence check
  immediately after the existing `ORCHESTRATE_OFF` kill switch and
  `CHECKOUT`-unresolvable early-exit, and *before* the
  `.orchestrate-monitor-alive` marker write: if
  `"$(pwd -P)/docs/specs/approvers.md"` is not a regular file, print one
  line (`poll tick: skipped (target repo is not an on-the-record board)`,
  matching the existing early-exit's echo-and-`exit 0` shape) and exit 0
  without creating the marker directory, without entering the tick loop,
  and without touching `runs/poll_heartbeat_last_state.json` or
  `~/.claude/tokenmaxxxer/poll-watchdog.log`.
- Board-repo sessions (target repo carries `docs/specs/approvers.md`) fall
  through unchanged to the existing marker write and loop.
- In `on-the-record/monitors/test_poll_heartbeat.py`, add:
  - a non-board fixture case: run with `cwd=<fresh tmp dir, no
    docs/specs/approvers.md>`, assert the process exits 0, assert
    `<cwd>/.orchestrate-monitor-alive` does not exist afterward, and assert
    no `poll_heartbeat_last_state.json`/`poll-watchdog.log` were written;
  - a board fixture case: same run shape but with
    `<cwd>/docs/specs/approvers.md` created first, asserting the existing
    due-tick behavior (marker created, watchdog invoked, captured report in
    stdout) is unchanged from today's baseline cases.

## Out of scope

- `on-the-record/hooks/directive.sh`'s degradation-notice logic (issue
  #947) — it already only fires when a session's own alive marker is
  absent/stale; a non-board session correctly never writing that marker
  falls through that existing logic unchanged, no separate code path
  needed for it.
- `spawn.py roster_watchdog()` / `require_board()` / the CLI `watchdog`
  subcommand — untouched; #1219's root-anchoring fix there stands, and this
  issue's gate sits strictly upstream of ever reaching that code for a
  non-board target repo.
- `monitors.json`'s `"when": "always"` manifest declaration — static
  per-install Claude Code config, not a per-session decision point; the
  gate has to live in the script the manifest points at.

## How you'll know it worked

- `python3 on-the-record/monitors/test_poll_heartbeat.py` passes, including
  the two new fixture cases.
- The non-board fixture case fails red against today's
  `poll-heartbeat.sh` (asserting `.orchestrate-monitor-alive` is absent
  would currently fail, since the marker is written unconditionally) and
  passes green after the change.
