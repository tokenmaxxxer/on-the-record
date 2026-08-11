---
subject: issue-782
role: product-discovery
kind: scout-brief
---

# Scout brief — internal comparables for dual-channel observation (issue #782)

This is infra work with no external product category to benchmark
against (no consumer market for "orchestrator observation channels");
per the scout directive's non-product carve-out, the sweep targets the
best comparable systems already in this repo instead of a web search.
Stage count: 1 sweep stage, 3 angles, run batched-sequentially in this
session (Bash/Read calls issued across sequential turns, not concurrent
tool calls in one message — stating this plainly per the directive's
fallback-disclosure requirement) + 1 judge point, no deepening needed
(the three angles converged on the same gap: primitives exist, wiring
does not). Angles: (1) existing poll/reconcile primitives in `spawn.py`,
(2) existing event-channel wiring in `on-the-record/hooks/directive.sh`,
(3) existing hook lifecycle wiring in `on-the-record/hooks/hooks.json`.

## Category must-bes (Kano)
- Idempotent reconcile keyed on stable identity, not on which channel
  saw it first: `spawn.py`'s `reconcile()` (`spawn.py:1644`) already
  takes pure `expected`/`observed` dicts and returns a closed
  `next_action` set — no channel-specific branching baked into the
  decision. This is the shape a dual-channel merge needs.
- Observe-only, never touch the session/workspace directly:
  `watchdog_check_one()` (`spawn.py:1904`) reads log mtime, roster
  fields, and git state only — the pattern any new poll tick should
  keep, so polling can never race a live session's own writes.
- Distinguish "dead" from "not this one" for liveness: `_watcher_looks_real()`
  (`spawn.py:1785`) checks `/proc/<pid>/cmdline` against `issue`+`role`,
  not just `_alive()` — a pid-alive check alone would misclassify a
  reassigned pid as a live watcher.

## Performance axes strong (internal) systems compete on
1. Default-on without explicit invocation — `directive.sh` fires on every
   `UserPromptSubmit` (`hooks.json:11-18`) with no skill call; this is the
   ONLY mechanism in the repo that reaches req #7's bar today. Anything
   the proposal adds must ride this same hook, not a new CLI flag nobody
   is told to type.
2. Bounded wait, never indefinite block — `directive.sh`'s watch/re-arm
   block explicitly caps every wait at `--stall-timeout` (default 5 min)
   and requires re-arming afterward; TURN-BUDGET RULES (#535, same file)
   push anything over ~30s to background. A poll tick must fit the same
   shape (bounded, backgroundable) to land in the same hook without
   violating it.

## Adopt / skip
- Adopt: drive the poll tick from `directive.sh` (fires every turn,
  already req #7-compliant) rather than inventing a new trigger surface.
- Adopt: reuse `reconcile()`'s existing closed next-action set for the
  session-health lane (`respawn`/`resume-watch`/`manual-review`/`none`)
  instead of inventing parallel vocabulary — extend only where the survey
  found a real gap (a completion poll detects that isn't a health repair
  at all).
- Adopt: `_watcher_looks_real`'s pid+cmdline identity check as the
  pattern for the new watcher-liveness signal the event-channel hardening
  needs.
- Skip: a standalone cron/systemd poller process outside the plugin —
  req #7 forbids "forced CI setup" and anything requiring the operator to
  configure something beyond plugin install; a hook-driven tick inside
  the existing per-turn cycle reaches every installed session for free,
  a cron job does not.

## Segment fit
on-the-record's existing pattern for "always-on, no explicit invocation"
is entirely hooks fired on Claude Code lifecycle events, never an
out-of-process daemon — the design must fit that shape exactly, not
import a general job-scheduler concept.

## Gap line
Current state already has the reconcile primitive (`reconcile()`) and the
observe-only poll primitive (`watchdog_check_one()`/`roster_watchdog()`)
that satisfy the "idempotent reconcile" and "observe-only" must-bes in
full. What's missing is exactly the "default-on without explicit
invocation" axis: nothing in `hooks.json` or `directive.sh` calls
`spawn.py watchdog` on any cadence — it is 2026-08-11's directly observed
failure, restated as a gap. The proposal's job is almost entirely wiring,
not new primitives, plus the one real new primitive the survey flagged
(a completion-detection lane distinct from `reconcile()`'s health-repair
lane) and the event-channel hardening signal.

Sources: none external — internal code reading only, paths cited inline
above (`spawn.py`, `on-the-record/hooks/directive.sh`,
`on-the-record/hooks/hooks.json`).
