---
status: proposed
files:
  - docs/issue-782/reports/product-discovery/survey.md
  - docs/issue-782/reports/product-discovery/scout-brief.md
  - docs/issue-782/proposals/2026-08-11-dual-channel-observation.md
  - docs/specs/dual-channel-observation.md
---

# Dual-channel observation design (issue #782, step 1)

## Intent

Design (not build — step 2 of issue #782's execution plan) an
observation model where the event channel (`watch --follow`) and a
polling channel are both first-class, neither a fallback for the other,
so a stalled/missed watch event no longer silently halts the pipeline —
as directly observed 2026-08-11 (issue-776/execution-observation opened
PR #781, watch stalled on its first line, orchestrator found the PR only
via manual `gh pr list`).

## Constraints stated so far

- Both channels co-equal in the design, not primary/backup (issue's own
  framing, repeated in the execution plan).
- Polling channel: independent, always-on periodic reconcile against
  ground truth (open PRs, session liveness, board/loop_state), bounded
  cadence, running regardless of whether any event fired.
- The installed orchestration session must be driven to poll
  autonomously by default — hook/directive-driven, no CI, no explicit
  skill invocation (northpole req #7).
- Event and poll results merge into one next-action stream without
  double-acting — idempotent reconcile keyed on issue/role/PR.
- Divergence→action mapping covers: completed PR no event saw, session
  died without session-end, PR merged out-of-band, stalled-but-alive
  session.
- Event channel gets hardened too, not just backstopped by polling.
- Scope: design only. Building it (step 2) is separate.

## What will be done

Full design lives in `docs/specs/dual-channel-observation.md` (the write
set above). Summary:

1. **Polling channel** — reuses `spawn.py`'s existing, already
   correctness-complete ground-truth readers
   (`_pr_open_or_merged_for_branch`, `roster_ps`'s liveness join,
   `board()`) through the existing `reconcile()`/`watchdog_check_one()`
   machinery, but wires the trigger into `on-the-record/hooks/directive.sh`
   (fires on every `UserPromptSubmit`, req #7's own reach mechanism) on a
   bounded 15-minute cadence, backgrounded per TURN-BUDGET RULES #535.
   Turn-driven, not wall-clock-driven — the one structural gap (idle
   orchestrator with no poll ticking) is named and deferred to a
   follow-up background-daemon design, not hidden.
2. **Merge without double-acting** — two lanes: a new completion-
   detection lane (PR opened / session ended, dedup key `(issue, role,
   pr_number)` or, with no PR, `(issue, role, spawn_attempt_id,
   "session-end")` — the attempt discriminator is required to avoid a
   respawn colliding with its predecessor's sentinel, per the
   after-proposal hunt finding, see spec §2) and the existing health-repair lane
   (`reconcile()`'s closed `respawn`/`resume-watch`/`manual-review`/`none`
   set, dedup key `(issue, role, next_action.kind)`). Both write through
   one TTL'd ledger (`runs/reconcile_ledger.json`) before acting; whichever
   channel gets there first stamps the key, the other finds it stamped
   and stays silent.
3. **Divergence→action mapping** — a 4-row table covering the issue's
   four named scenarios, reusing `reconcile()`'s existing mapping for the
   two health-repair cases (crash→respawn, stalled→resume-watch,
   unchanged) and routing the two completion-shaped cases (missed PR,
   out-of-band merge) through the new completion-detection lane instead
   of forcing them into repair vocabulary.
4. **Event-channel hardening** — a new `watcher-silent` anomaly signal
   (armed, pid alive, `_watcher_looks_real()` passes, but no event line
   emitted since arming past a bounded threshold) distinct from the
   existing `watcher-dead` signal — this is the 2026-08-11 failure mode
   specifically, undetectable by pid-liveness alone, detectable only by
   comparing against poll's ground truth.

## Candidate comparison (RICE)

Compared during current-state survey (`survey.md`'s OST section); full
table in `dual-channel-observation.md`. Chosen: hook-driven poll cadence
+ ledgered reconcile merge (RICE 9.6) over hardening watch alone (2.4,
rejected: still a single point of failure against hangs retry can't see)
or a standalone cron/systemd poller (rejected independent of score — a
per-repo daemon defeats req #7's install-only, no-CI constraint).

## Out of scope

- Building the poll-cadence hook change, ledger, and new anomaly signal
  (issue #782 step 2, a separate role session).
- A background poll daemon armed independently of orchestrator turn
  activity (named as a follow-up in the spec, deferred — the turn-driven
  cadence already satisfies the issue's Acceptance tests).
- Any change to `reconcile()`'s existing health-repair next-action
  vocabulary — reused unchanged.

## How you'll know it worked

`docs/specs/dual-channel-observation.md` exists, is readable with no
prior context on issue #782, and contains: the polling ground-truth set
and cadence with its trigger mechanism named, the two-lane merge with its
ledger keying, the 4-row divergence→action table, the event-channel
hardening signal, the RICE comparison, and a pre-registered decision rule
+ guardrail for step 2's test suite — sufficient for an implementation
session to build it without open design decisions.

## Accumulation

Not accumulation-cost-shaped: one-time design document. N/A.

## What did not work

- Initial completion-detection dedup key was `(issue, role,
  "session-end")` with no attempt discriminator — after-proposal hunt
  (`docs/issue-782/reports/product-discovery/2026-08-11-hunt-2026-08-11-dual-channel-observation.md`)
  found this collides across a respawn inside the TTL window, silently
  suppressing a genuinely distinct completion. Fixed: key now includes
  the roster entry's spawn timestamp as `spawn_attempt_id` when no PR
  exists.
