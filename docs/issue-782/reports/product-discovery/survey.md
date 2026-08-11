---
subject: issue-782
role: product-discovery
kind: survey
---

# Current-state survey (issue #782)

## Background / context

The orchestration pipeline today advances on `spawn.py watch --follow`
push-events only (`on-the-record/hooks/directive.sh`'s watch/re-arm
block). Directly observed 2026-08-11: an execution-observation session
opened PR #781 and kept running, but its follow-watch stalled on its
first line and never emitted a completion notification — the orchestrator
found the PR only via a manual `gh pr list`. This is not a fresh gap:
`spawn.py` already carries a full poll/reconcile primitive set —
`reconcile()` (`spawn.py:1644`), `_build_expected`/`_build_observed`
(`spawn.py:1717`/`1730`), `watchdog_check_one()` (`spawn.py:1904`),
`roster_watchdog()` (`spawn.py:2026`), `roster_ps()` (`spawn.py:1838`) —
but every one of these is CLI-invoked (`spawn.py watchdog`, `spawn.py ps`),
never hook-driven. Nothing in `on-the-record/hooks/hooks.json` fires it
automatically. The 2026-08-11 stall is exactly the failure mode this
predicts: the polling machinery existed and would have caught the missed
event, but nobody was running it.

## Problem, stated without any solution attached (JTBD)

- **Job performer:** the on-the-record-installed orchestration session,
  acting on behalf of the operator who never re-reads logs by hand.
- **Job:** to learn, within a bounded delay, that a spawned role session
  has reached a state requiring the orchestrator's next action (PR opened,
  gate refusal, session end, crash) — regardless of whether the
  notification mechanism watching for that state happens to be working at
  the time.
- **Circumstance:** the orchestrator currently has exactly one channel
  (`spawn.py watch --follow`) wired to fire automatically per
  `directive.sh`'s re-arm instructions; that channel is a live network/log
  stream and can silently stall (observed 2026-08-11) with no self-
  detection, and nothing independent is watching whether it's still
  working.
- **Desired outcome:** the orchestrator detects a completed or stalled
  role session within a bounded interval no matter which single mechanism
  fails, without acting twice on the same detected event.

The issue names a solution shape already (dual-channel: event + polling,
both first-class) — that shape is carried into the proposal below, but
the problem above is the reason it's needed: a single channel, however
well hardened, cannot distinguish "nothing happened" from "the channel
itself died," and 2026-08-11 is a directly observed instance of exactly
that failure.

## Where this sits on the opportunity-solution tree

- **Outcome:** a spawned role session's completion or failure is always
  detected by the orchestrator within a bounded interval (northpole req #1
  completion, req #4 autonomy).
- **Opportunity:** the event channel (`watch --follow`) is the orchestrator's
  ONLY default-driven observation path; the poll/reconcile primitives that
  already exist in `spawn.py` are correctness-complete but not wired to
  run without an explicit CLI invocation, so they cannot catch a watch
  failure in practice.
- **Candidate solutions:** (a) wire the existing poll/reconcile primitives
  into `directive.sh` (fires on every `UserPromptSubmit`, req #7's own
  no-explicit-invocation mechanism) on a bounded cadence, independent of
  watch state, merged with watch's own events through one idempotent
  reconcile keyed on issue/role/target; (b) harden `watch --follow` alone
  (e.g. retry-on-stall) with no independent poll cadence; (c) a standalone
  cron/systemd poller outside the plugin.
- **Discriminating assumption test:** does a bounded-cadence poll tick,
  driven by a hook that already fires on every orchestrator turn with no
  skill invocation, detect a completion that an armed-but-stalled watch
  process structurally cannot — and does merging its output with watch's
  output through one keyed reconcile avoid acting twice on the same
  completion? The proposal's design is exactly this, made concrete.

## Order-constraint note

This current-state survey is written before the proposal (contract v3
s19 / scout directive). The proposal carries the scout-brief's adopt/skip
findings and is written after this survey.

## Write-surface unknowns this survey identifies (aimed the scout sweep)

- Whether the existing `reconcile()` next-action vocabulary (`respawn`,
  `resume-watch`, `manual-review`, `none` — closed set, ADR Decision 3,
  `spawn.py:1644`) is sufficient for the issue's four divergence
  scenarios, or whether a completion actually detected by poll (not a
  session-health repair) needs a distinct action lane so it doesn't get
  forced into the health-repair vocabulary.
- Whether cadence-driving through `directive.sh` (a per-turn hook) can
  satisfy "bounded cadence regardless of whether any event fired" when the
  orchestrator itself may go quiet between turns, or whether the poll tick
  needs its own background process analogous to the watch process spawn.py
  already arms.
Both are addressed in `scout-brief.md` (same directory) and carried into
the proposal's design choices.
