# Survey — issue #947 (northpole req#7 gap: IDE-session monitor fallback)

## What already exists

- `on-the-record/monitors/monitors.json` registers one monitor,
  `poll-heartbeat`, `"when": "always"`, running
  `on-the-record/monitors/poll-heartbeat.sh`. Its own header already states
  the hard boundary: "Claude Code plugin Monitors... run only in
  interactive CLI sessions" (docs/specs/platform-capabilities.md) and "On
  a host where the Monitor tool is unavailable, the platform never invokes
  this script at all."
  (canonical: on-the-record/monitors/poll-heartbeat.sh lines 24-28)
- Turn-driven wake is carried by two hooks that both call the shared
  `poll_rearm_arm_if_due()` in `on-the-record/hooks/poll-rearm.sh`:
  `directive.sh` (UserPromptSubmit) and `stop-poll-rearm.sh` (Stop). Both
  fire in every session type, including IDE-extension sessions per
  issue #947's own comment thread.
  (canonical: gh issue view 947 --comments, body text "Turn-driven wake
  (UserPromptSubmit/Stop poll-rearm hooks) still works there")
- `directive.sh` already has a proven per-workspace one-time-notice
  pattern: `GREETED_MARKER="$(pwd -P)/.orchestrate-greeted"` (issue #1006)
  — checked once per prompt, gated on file existence, `touch`ed
  immediately so the notice never repeats.
  (canonical: on-the-record/hooks/directive.sh lines 33-38) This is the
  exact shape req#7 block 1 (operator-visible one-time notice) needs; no
  new mechanism has to be invented.
- No existing code detects "is a plugin Monitor actually alive in this
  session".
  derived: `grep -rln "CLAUDE_CODE_ENTRYPOINT\|IDE\|entrypoint" on-the-record/hooks/*.sh on-the-record/gates/*.py`
  ```
  (no matches besides comment-only hits already reviewed)
  ```
- `poll-heartbeat.sh` writes no marker/state file of its own today — it
  only shells out to `spawn.py poll-due` / `spawn.py watchdog
  --auto-respawn` on a due tick, after an initial 60s `sleep`.
  (canonical: on-the-record/monitors/poll-heartbeat.sh lines 44-53)

## The actual detection problem

Issue #947's own comment thread
(canonical: gh issue view 947 --comments, comment beginning "CORRECTION
(2026-08-12 10:55, same fresh session)") reports the original premise was
partly wrong: a monitor process was later observed running in the same
session where an earlier check had seen nothing (canonical: same comment,
"appeared by 10:54"). A single absent-process snapshot is therefore not
by itself sufficient evidence of structural unavailability — it can also
be early-session startup timing, and a fallback must not fire a
false-positive notice during that window.

The only ground-truth signal available to hook-side code that a monitor
process actually launched in *this* session is a marker the monitor
script itself writes when it starts running (before its first
sleep/tick) — nothing else in the current codebase observes plugin
Monitor process lifecycle from hook-side code (same grep as above).
Comparing "did the monitor ever write its start-marker" against "has
enough turns elapsed that it should have by now, were monitors available"
is the same before/after shape `GREETED_MARKER` already uses for the
first-contact notice, applied to a different marker and a delayed check
instead of an immediate one.

## Write surfaces this proposal expects

- `on-the-record/monitors/poll-heartbeat.sh` — write a start-marker on
  launch (before the sleep loop), keyed per-workspace like
  `GREETED_MARKER`, so this session's directive hook can observe it.
- `on-the-record/hooks/directive.sh` — add a delayed (not first-prompt)
  check: if enough prompts have elapsed with no start-marker present, emit
  the one-time degradation notice, mirroring the existing
  `GREETED_MARKER` gating pattern, and record the check so it fires at
  most once per workspace.
- a new pytest file under on-the-record/hooks/ (name:
  test_monitor_notice.py, not yet created) — exercises the notice logic
  directly (no live Monitor process needed): given no start-marker and
  the grace threshold elapsed, notice fires exactly once; given a
  start-marker present, it never fires. This is the `gates/`/`tests/`
  artifact the issue's Acceptance section calls for.
- `docs/decisions/` — a short ADR recording that idle self-wake is
  CLI-only by harness constraint (the issue's citation:
  https://code.claude.com/docs/en/plugins-reference.md#monitors), so the
  degraded-mode notice has a documented reason to point to instead of
  restating the constraint inline every time.

## Alternatives considered while surveying

- Detect IDE vs CLI directly via an environment variable at session
  start. Rejected as infeasible: no such env var/flag turned up in the
  hook/gate sources (derived grep above), and the issue's own comment
  thread states the same finding independently ("no flag/setting enables
  monitors in IDE sessions" — canonical: gh issue view 947 --comments).
- Poll `ps`/`pgrep` for the `poll-heartbeat.sh` process from `directive.sh`
  instead of a written marker. Rejected: process-table introspection is
  less portable across the CLI/IDE host environments this plugin already
  has to run in (macOS/Linux sandboxes, containers with restricted `ps`),
  whereas a plain file write/read is host-agnostic and matches the
  existing `GREETED_MARKER` mechanism already proven in this file.
