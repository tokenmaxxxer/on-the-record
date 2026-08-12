---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/test_monitor_notice.py
  - docs/decisions/2026-08-12-monitor-cli-only-fallback.md
  - docs/issue-947/reports/implementation.md
---

## Request

Northpole req#7 requires idle self-wake to be visible when it silently
degrades. Plugin Monitors (the idle self-wake channel) only run in
interactive CLI sessions per official docs; in IDE-extension sessions
the session still has turn-driven wake (UserPromptSubmit/Stop hooks) but
loses idle self-wake with no signal to the operator. #947 asks for: (1)
a one-time operator-visible notice when idle self-wake is structurally
unavailable, (2) a fallback evaluation or an ADR recording the CLI-only
constraint, (3) a harness fixture that tells "CLI, should be up" apart
from "IDE, structurally unavailable."

## Constraints

- Hooks only — no CI, no manual `/loop` band-aid (per req#7 and the issue
  text).
- No env var or flag exists to directly detect IDE vs CLI session type
  (confirmed by survey.md's grep and the issue's own research); detection
  must work indirectly, from observable session-local state.
- Must not false-positive during a session's early startup window — the
  issue's own follow-up comment found the monitor process starting
  ~8 minutes into a session that first looked monitor-less.
- Must not false-negative across sessions in the same workspace — a
  marker persisting past its writing session's lifetime must never be
  read as evidence of the *current* session's own monitor being alive
  (warrant-hunt finding, docs/issue-947/reports/implementation/2026-08-12-hunt-monitor-unavailable-notice.md).
- The notice must fire once per workspace, not once per prompt (matches
  the existing `GREETED_MARKER` UX in `directive.sh`).

## Rationale

Considered detecting IDE vs CLI directly via an entrypoint/session-type
environment variable, checked once at SessionStart. Rejected: no such
variable exists in this harness (survey.md's grep across
`on-the-record/hooks/*.sh` and `on-the-record/gates/*.py` found none, and
the issue's own investigation independently reached the same conclusion)
— there is nothing to read, so this approach cannot be implemented as
stated.

Chosen instead: infer unavailability indirectly, from whether the
monitor process itself ever left a trace in this session. The monitor
script (`poll-heartbeat.sh`) is code we control, so it can write a
start-marker the instant it launches, before its first `sleep`. A hook
that already runs on every turn in every session type (`directive.sh`,
UserPromptSubmit) can then check, after a grace period, whether that
marker exists. Absence past the grace period is the best obtainable
proxy for "monitors are not running here" without a direct env signal,
and reuses `directive.sh`'s already-proven `GREETED_MARKER` gating
pattern instead of inventing a second notice mechanism.

## What will be done

1. `poll-heartbeat.sh`: before the `sleep`/tick loop starts, write a
   session-scoped marker file, keyed by `session_id` (available the same
   way `session-role-bind.sh` reads it from its hook payload) under a
   per-workspace directory — e.g.
   `.orchestrate-monitor-alive/<session_id>` — gated the same way as
   `GREETED_MARKER` — `case "${ORCHESTRATE_OFF:-}"` short-circuit stays
   first, so the kill switch still suppresses the marker write too. This
   is a deliberate departure from `GREETED_MARKER`'s workspace-lifetime,
   session-agnostic persistence: a warrant hunt against this proposal
   (docs/issue-947/reports/implementation/2026-08-12-hunt-monitor-unavailable-notice.md)
   found that reusing `GREETED_MARKER`'s convention verbatim lets a stale
   marker from an earlier CLI session in the same workspace silently
   suppress the notice in a later IDE session opened on that same
   workspace — exactly the case #947 exists to surface. Scoping the
   marker per-session closes that gap: a new session can never observe a
   prior session's marker as evidence of its own monitor being alive.
2. `directive.sh`: track elapsed wall-clock time since this session's own
   start (via the session-scoped marker directory's own bookkeeping, not
   a workspace-lifetime file) for a grace threshold chosen to safely
   exceed the observed ~8-minute startup delay. Once the threshold is
   crossed and this session's own start-marker (keyed by the same
   `session_id`, from step 1) is still absent, and a distinct
   session-scoped "already notified" marker is not yet set: print the
   one-time degradation notice ("idle self-wake is unavailable in this
   session; turn-driven wake via UserPromptSubmit/Stop hooks is the
   active mode") and set the "already notified" marker so it never
   repeats for this session.
3. `on-the-record/hooks/test_monitor_notice.py` (new): unit-tests the
   grace-threshold/marker-presence decision logic in isolation (no real
   Monitor process needed) — asserts the notice fires exactly once when
   no start-marker exists past the grace window, and never fires when a
   start-marker is present at any point. This is the acceptance-criteria
   "gates/ or tests/ artifact proving the notice fires only when monitors
   are unavailable."
4. `docs/decisions/2026-08-12-monitor-cli-only-fallback.md`: a short ADR
   recording that idle self-wake is CLI-only by harness constraint, citing
   https://code.claude.com/docs/en/plugins-reference.md#monitors, and
   pointing at the marker-based detection above as the chosen fallback
   (rather than a structural fix, since none is possible within the
   stated hooks-only constraint).
5. `docs/issue-947/reports/implementation.md`: the phase-2 record.

## Out of scope

- Making Monitors actually run in IDE-extension sessions — the issue's
  own research and this survey both confirm that is a harness-level
  constraint, not something this plugin's hooks can override.
- The #776 harness fixture's own liveness-check integration beyond the
  new unit test — wiring this detection into whatever #776 already
  built is left for that issue's own follow-up if one is filed; this
  proposal's write set stops at the notice mechanism and its direct
  test.

## How you'll know it worked

- `test_monitor_notice.py` passes and demonstrates both the fire and
  no-fire cases without a live Monitor process.
- Manual read-through: `directive.sh`'s new check follows the same
  `GREETED_MARKER`-style gating already in the file, so a CLI session
  (where the monitor's start-marker appears quickly) never sees the
  notice, and only a session where the marker stays absent past the
  grace window sees it exactly once.
