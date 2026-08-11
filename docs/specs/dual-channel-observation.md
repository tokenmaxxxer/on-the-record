# Dual-channel observation (issue #782)

Design only (issue #782 step 1). Implementation is a separate,
later execution-plan step (step 2). This spec is the design's durable
home; `docs/issue-782/proposals/2026-08-11-dual-channel-observation.md`
is the proposal record that produced it.

## Problem this closes

`on-the-record/hooks/directive.sh` drives exactly one observation
channel by default: `spawn.py watch --follow`. Directly observed
2026-08-11: that channel stalled on its first line for the
issue-776/execution-observation session; the session finished and opened
PR #781, but no completion notification ever reached the orchestrator —
it found the PR only via a manual `gh pr list`. `spawn.py` already has a
complete poll/reconcile primitive set (`reconcile()`, `_build_expected`/
`_build_observed`, `watchdog_check_one()`, `roster_watchdog()`,
`roster_ps()`) that would have caught this, but every one of them is
CLI-invoked only — nothing in `hooks.json`/`directive.sh` runs them on
any cadence. Polling today is a manual escape hatch, not a first-class
channel. This spec makes it one, co-equal with watch, neither a
fallback for the other.

## 1. The polling channel

### Ground-truth set (what a poll tick reconciles against)

Reused as-is from existing `spawn.py` readers — no new `gh`/git call
types, only new call SITES:

- **Open PRs for the role/branch** — `_pr_open_or_merged_for_branch()`
  (`spawn.py:1043`-adjacent), backed by `gh pr list`.
- **Session liveness** — `roster_ps()`'s join of `runs/active.json` (the
  roster) with the workspace watcher index, via `_alive()` and
  `_watcher_looks_real()` (pid + `/proc/<pid>/cmdline` identity check
  against issue+role, not bare pid-alive).
- **Board / loop_state** — `board()`'s read of merged-main
  `docs/issue-<n>/reports/<role>.md` frontmatter.

These three are exactly `reconcile()`'s existing `observed` inputs
(`_build_observed()`, `spawn.py:1730`) — the ground-truth set does not
change; what changes is that a poll tick calls it on a schedule instead
of only when `spawn.py watchdog` is typed by hand.

### Cadence: hook-driven, bounded, no CI

Per req #7 (default-on, plugin-only, no explicit invocation, no CI): the
poll tick is driven from `directive.sh`, the same `UserPromptSubmit`
hook that already fires on every orchestrator turn
(`hooks.json:11`-`18`) with no skill invocation required — this is the
only mechanism in the repo that reaches every on-the-record-installed
session by construction, so it is the trigger surface, not a new one.

- `directive.sh` gains a poll-cadence check: read the poll tick's last-run
  timestamp (a new `runs/poll_state.json`, same shape as
  `runs/watchdog_state.json`); if stale beyond a bounded interval, run
  `spawn.py watchdog --auto-respawn` in the background
  (`run_in_background: true`, per TURN-BUDGET RULES #535 — this call
  already exceeds the ~30s foreground bar) and stamp the timestamp
  immediately (not after completion) so overlapping turns within the
  interval don't double-dispatch.
- Interval: bounded, symmetric with the existing anomaly thresholds
  already in `spawn.py` (`WATCHDOG_SILENCE_MIN = 90`,
  `WATCHDOG_NO_COMMIT_MIN = 71`) — a poll cadence looser than the anomaly
  windows it's meant to catch would let a stall sit past its own
  detection threshold before anyone checks. Set the interval well inside
  both: 15 minutes. Rationale, not measurement: an orchestrator session
  that goes 15+ minutes without a single `UserPromptSubmit` turn is
  itself idle (nothing to reconcile against yet), and 15 minutes is
  bounded well under the ADR's `--stall-timeout` default (5 min) x 3,
  giving the poll tick multiple chances inside one watch stall-timeout
  window's worth of elapsed time.
- This makes the cadence turn-driven, not wall-clock-driven: if the
  orchestrator session itself goes idle (no turns), there is no process
  ticking in the background independent of it. This is the one
  structural gap between "the orchestrator is present and driving polls
  every 15 min" and "the poll runs even if the orchestrator process
  itself is gone" — noted here rather than hidden; closing it fully would
  need a background poll daemon armed the same way `watch --follow`'s
  watcher process already is (out of scope for this design, flagged as a
  follow-up below).

### Follow-up (not this design's scope)

A background poll daemon, armed at spawn time exactly like the existing
watch watcher process (`roster_register`'s `watcher_pid` field), would
close the turn-idle gap above. Deferred: the turn-driven cadence already
satisfies the issue's Acceptance tests (a completion is detected "within
a bounded interval," not "instantly regardless of orchestrator
liveness"), and a background daemon is materially more implementation
surface (a second long-lived process to arm, track, and watchdog itself)
than issue #782 step 1 asks for. If a future issue observes a stall
during genuine orchestrator idle time, that's the trigger to build it.

## 2. Merging event and poll into one next-action stream, without double-acting

Two distinct lanes exist already in `spawn.py`'s vocabulary, and they
should stay distinct rather than being forced into one:

- **Completion-detection lane**: "a role session reached a reportable
  state" — PR opened, session ended. Either channel can detect this
  first: watch, by streaming the event live; poll, by finding the PR via
  `_pr_open_or_merged_for_branch()` or the session's
  `session_end_verdict()` on its next tick. Dedup key: `(issue, role,
  pr_number)` if a PR exists, else `(issue, role, spawn_attempt_id,
  "session-end")` — the roster entry's own `ts` (spawn timestamp,
  already recorded per `roster_register()`) serves as `spawn_attempt_id`
  with no new field needed. A bare `(issue, role, "session-end")` key
  (no attempt discriminator) would collide across respawns: after-
  proposal hunt (`docs/issue-782/reports/product-discovery/2026-08-11-hunt-2026-08-11-dual-channel-observation.md`)
  found that a role respawned inside the TTL window (exactly the
  `crashed`→`respawn` health-repair path this same spec defines) would
  have its genuinely distinct completion silently suppressed as a
  duplicate of the prior attempt's session-end — a false-negative, not a
  double-action, but equally a missed completion, which is the exact
  failure this design exists to close.
- **Health-repair lane**: `reconcile()`'s existing closed next-action set
  — `respawn`, `resume-watch`, `manual-review`, `none` (ADR Decision 3,
  `spawn.py:1644`). This lane does not change; it already takes pure
  `expected`/`observed` inputs regardless of which caller (watch's own
  re-arm logic, or a poll tick) produced them.

**Idempotent reconcile, keyed on issue/role/target:** both lanes write
through one ledger (`runs/reconcile_ledger.json`, same lock discipline as
`_roster_locked()`) before acting:

1. Compute the dedup key for the detected event/divergence (completion
   lane: `(issue, role, pr_number|"session-end")`; health-repair lane:
   `(issue, role, next_action.kind)`).
2. If the ledger has that key stamped within a bounded TTL (15 min,
   matching the poll cadence — long enough to cover the gap between an
   event firing and the next poll tick observing the same state), skip:
   the other channel already reported/acted on this.
3. Otherwise, stamp the key with the current timestamp and act (report
   the completion to the orchestrator's next reply; or execute the
   health-repair `next_action`).

This means, with the attempt-discriminated key above: watch reports a PR first → poll's next tick sees the same PR
via `_pr_open_or_merged_for_branch()`, finds the ledger key already
stamped, and stays silent (Acceptance test 3: event+poll on the same
completion → exactly one next-action). Poll finds a PR watch never
reported → ledger key absent, poll reports it, stamps the key (Acceptance
test 1). A later, genuinely late watch event for the same PR then finds
the key stamped and is a no-op, not a duplicate report (Acceptance test
2, direction reversed).

## 3. Divergence → action mapping

| Divergence (issue's four examples) | Detected by | Lane | Action |
|---|---|---|---|
| Completed PR no event saw (watch never fired or stalled) | Poll (`_pr_open_or_merged_for_branch` finds a PR with no prior ledger stamp) | Completion-detection | Report the completion (same shape as a watch-reported completion) — prompts the orchestrator's mandatory board re-read after a merge/PR event, per `directive.sh`'s existing "after EVERY merge... re-read the board" rule |
| Session died without session-end event (crash, e.g. `kill -9`) | Poll (`session_end_verdict()` returns `crashed`) | Health-repair | `reconcile()` → `respawn` (unchanged existing mapping) |
| PR merged out-of-band (human merged manually while watch still armed) | Poll (`board()`/`_pr_open_or_merged_for_branch` show merged state; watch may still be waiting) | Completion-detection | Report the completion; the stale armed watch is left to hit its own `--stall-timeout` and get re-armed or dropped per the existing watch/re-arm rule — no new action needed since the completion itself is already reported |
| Stalled-but-alive session (log-silent, process alive) | Poll (`watchdog_check_one()` signal 1, log-silence past `WATCHDOG_SILENCE_MIN`) | Health-repair | `reconcile()` → `resume-watch` (unchanged existing mapping, per the #132 standing decision: name it, don't auto-rearm silently) |

No new next-action vocabulary is needed in the health-repair lane — the
survey's open question ("does `reconcile()`'s closed set suffice")
resolves to: yes for health repair, and the completion-detection lane
(new, but not part of that closed set — it never repairs anything, it
only reports) is the one addition.

## 4. Hardening the event channel

Why watch stalled on first line, 2026-08-11 (best-effort root-cause,
no log excerpt survives to cite directly — noted as inference, not a
verified trace): `_watcher_looks_real()` already distinguishes a dead pid
from a live-but-wrong process, but nothing currently ACTS on that signal
unless a human runs `spawn.py ps` or `spawn.py watchdog` by hand — exactly
the gap section 1 closes. A watcher process can also be alive (passes
`_alive()`) but hung on I/O without emitting further lines — pid-liveness
alone does not prove forward progress.

Two hardening changes, both extending existing signals rather than
inventing new mechanisms:

- **Wire polling in (section 1) closes the primary failure mode**: a
  dead or hung watcher was previously invisible until someone thought to
  check; the 15-minute poll tick now surfaces it automatically via the
  existing `watcher-missing`/`watcher-dead` anomalies
  (`watchdog_check_one()` signal 5, `spawn.py:1975`-`1985`) as part of
  every regular tick, not only on manual invocation.
- **New watcher-silence signal, distinct from watcher-dead**: extend
  `watchdog_check_one()` with a signal comparing `watcher_armed_at`
  against the workspace index's last-event timestamp (a new field,
  stamped each time `watch --follow` emits a line) — a watcher whose pid
  is alive and passes `_watcher_looks_real()` but has emitted nothing
  since arming, past a bounded threshold, is `watcher-silent`: alive,
  correctly identified, but not producing events. This is the 2026-08-11
  failure mode specifically (the process didn't die, it just never
  produced a second line) and `_alive()`+`_watcher_looks_real()` alone
  cannot detect it — only a ground-truth comparison (has anything
  actually happened since this watcher was armed) can, which is exactly
  what the poll tick already has access to.

## Candidate comparison (RICE)

| Candidate | Reach | Impact | Confidence | Effort | RICE (R×I×C/E) |
|---|---|---|---|---|---|
| (a) Hook-driven poll cadence in `directive.sh` + ledgered reconcile merge (chosen) | every on-the-record-installed session (req #7 reach) | 3 (high — closes a directly observed, already-happened pipeline-halting failure) | 0.8 (built almost entirely from existing, already-tested primitives) | 2 | 9.6 |
| (b) Harden `watch --follow` alone (retry-on-stall), no independent poll cadence | every installed session | 1 (low — a watch that stalls for a reason retry can't see, e.g. the process itself hangs, is still a single point of failure) | 0.6 | 1.5 | 2.4 |
| (c) Standalone cron/systemd poller outside the plugin | only repos where the operator manually configures it | 0.5 (low reach defeats req #7 by construction) | 0.7 | 1 | 1.75 (rejected independent of score — violates req #7's "no forced CI setup," a hard constraint, not a tradeoff) |

(a) is selected: it is the only candidate that keeps both channels
first-class (per the issue's explicit framing) while staying inside req
#7's install-only, no-CI constraint, and it reuses primitives the survey
found already correctness-complete rather than building new ones.

## Pre-registered decision rule / guardrail

Deferred to implementation (issue #782 step 2), stated here so step 2
inherits it rather than re-deriving it: this design is validated when all
three of the issue's Acceptance tests pass against a real fixture (a
completion with no watch event; a watch-detected completion with delayed
polling; simultaneous detection) and the empty-state assertion (no
spurious action with nothing in flight) holds. Guardrail, distinct from
that primary pass/fail: the ledgered merge (section 2) must not raise the
duplicate-action rate above zero for any divergence kind above — a design
that fixes missed-completion detection while introducing double-respawns
would be a reduced-trust result, not a win, and step 2's test suite must
assert both independently.

## Accumulation

Not accumulation-cost-shaped: this is a one-time wiring change to
existing hook/CLI call sites, not a recurring resource whose per-unit
cost grows with issue count or time (the ledger is bounded by TTL
eviction, not by unbounded append). N/A.
