---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/hooks/directive.sh
  - spawn.py
  - tests/test_spawn.py
---

## Request

The #1245 non-board attachment gate in `poll-heartbeat.sh` currently
`exit 0`s the whole Monitor process for a non-board arm-root, which
permanently kills idle watch for the session (the process cannot be
re-armed). Demote that gate from a full exit to a sweep-exclusion: the
tick loop always runs; a non-board arm-root is excluded from the sweep
but roster-derived board targets are still swept every tick; a
non-board-root-with-empty-roster session stays alive and dormant
(no output, cheap check only), never exits. Relocate the alive marker
that `directive.sh`'s #947 notice logic reads out of the target repo, so
no files are created in a non-board repo, and fix the false
"idle self-wake unavailable" notice that relocation causes today.

## Constraints

- Board-root behavior (today's default case) must not change.
- #1275's non-git-root refusal (`exit 1` before the board check) is
  untouched — that check stays a hard exit.
- No registration artifacts (files) may be created inside a non-board
  target repo, per #1245's original intent — this is why the alive
  marker moves out, not just changes name.
- `directive.sh`'s #947 notice must read the same relocated marker the
  heartbeat writes, and must not collide across concurrent sessions
  rooted in different repos (a monitor alive in repo A must never read as
  "alive" for a session rooted in repo B).
- `_board_wide_sweep_all()`'s existing per-repo board check for roster
  targets (issue #1276) is reused, not reinvented, for the arm-root case.

## Rationale

Two designs were considered for the alive-marker relocation key:

1. **Key by resolved arm-root path (hashed), one marker per repo** — the
   chosen approach. `poll-heartbeat.sh` and `directive.sh` both already
   compute `pwd -P` independently at their own invocation points within
   the same session/workspace, so hashing that path (mirroring
   `directive.sh`'s existing `hashlib.sha256(session_id...)` pattern for
   the #1006 greeted-marker collision fix) lets both sides compute the
   identical key with no shared state file and no IPC. It also
   automatically avoids cross-repo collision: two concurrent CLI sessions
   in different repos get different marker files.
2. **Key by `session_id` instead of repo path** — rejected. `directive.sh`
   already has `session_id` from its own stdin payload, but
   `poll-heartbeat.sh` (a Monitor command) has no documented stdin JSON
   contract and no session_id available to it (the file's own #947
   comment already states this explicitly: "no session_id is available to
   a Monitor command"). Keying by something the writer side cannot
   observe is not implementable.

For the arm-root sweep-exclusion itself, the alternative of printing one
skip line per tick for a non-board arm-root (mirroring the existing
non-board roster-target skip line) was rejected: it would violate the
issue's explicit "non-board root + empty roster -> no per-tick output"
acceptance criterion in the exact case that criterion targets. Staying
fully silent for the excluded root satisfies acceptance uniformly
regardless of roster contents.

## What will be done

- `poll-heartbeat.sh`: replace the #1245 `exit 0` with setting a local
  `is_board` flag from the same `docs/specs/approvers.md` existence
  check, and fall through into the tick loop unconditionally in either
  case (only #1275's git-repo check keeps its `exit 1`). The due-tick
  `watchdog --auto-respawn` invocation is unchanged (it already delegates
  per-repo board gating to `_board_wide_sweep_all`, which this proposal
  also updates); no new `-C`/cwd plumbing is needed since the CLI default
  cwd is already the arm-root.
- `poll-heartbeat.sh`: move the alive-marker write off
  `$(pwd -P)/.orchestrate-monitor-alive/alive` to a workspace-keyed path
  under `~/.claude/tokenmaxxxer/monitor-alive/<sha256(pwd -P)[:24]>/alive`,
  computed via a small inline `python3 -c` (python3 already a hard
  dependency of this script via `spawn.py poll-due`).
- `directive.sh`: change `OTR_MN_DIR` from `$(pwd -P)/.orchestrate-monitor-alive`
  to the same `~/.claude/tokenmaxxxer/monitor-alive/<hash>/` computation
  (same hash formula, computed from `pwd -P` at hook-fire time — same cwd
  the heartbeat script sees since both run inside the same workspace).
- `spawn.py`, `_board_wide_sweep_all()`: only add `root` to the sweep
  targets when `(root / MARKER).exists()`; when it does not, `root` is
  silently excluded (no line printed) rather than unconditionally swept.
  Roster-derived targets keep their existing per-repo board check and
  skip-line behavior unchanged. Update the function's docstring, which
  currently states arm-root is "never skipped."
- `tests/test_spawn.py`: fix
  `test_board_wide_sweep_all_empty_roster_sweeps_arm_root_only` to use an
  actual board root (add `docs/specs/approvers.md`) so it keeps testing
  the board-root-empty-roster case it always meant to test. Add the named
  new cases from the issue body: non-board root + board roster entry ->
  repo-prefixed watch line for that entry; non-board root + empty roster
  -> alive and silent (the empty-state case, asserting
  `_board_wide_sweep_all` returns 0 with zero output and `_board_wide_sweep`
  never called); no file creation inside a non-board root from the
  heartbeat script's marker write; the relocated alive marker read
  correctly by `directive.sh`'s #947 logic (marker path computed off a
  non-board root still satisfies the notice-suppression check).

## Out of scope

- `poll_rearm_arm_if_due()`/`poll_rearm_validate_root()` in
  `on-the-record/hooks/poll-rearm.sh` — the turn-driven (UserPromptSubmit/
  Stop hook) watchdog re-arm path is a separate mechanism from the plugin
  Monitor heartbeat loop and issue #1280 does not ask to change it; it
  keeps its existing hard-refuse-on-non-board behavior.
- `GREETED_MARKER` (`directive.sh`'s per-workspace first-contact notice) —
  unrelated marker, out of this issue's scope.
- Any change to `roster_watchdog()`'s own scanning logic beyond the one
  `_board_wide_sweep_all()` root-inclusion check.

## How you'll know it worked

`python3 -m pytest tests/test_spawn.py -k "monitor or heartbeat or roster"`
passes, including the new #1280 cases named above (empty-state case:
non-board root + empty roster -> alive, silent, no files).
