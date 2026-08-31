---
issue: 2915
role: diagnose-first+observability-methodology-selection-1f7123db
author: diagnose-first+observability-methodology-selection-1f7123db
skills: diagnose-first (skill-repository(c05de12)), observability-methodology-selection (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2915/reports/adversarial-review-708b12ce.md
    sha: 4677971899e70dd63d51f4d76cf6f52c8ad25470
  - path: docs/handbooks/monitor-liveness.md
    sha: same-commit
---

# issue-2915 — diagnose-first+observability-methodology-selection-1f7123db record

## What was done

Round 3 on issue #2915, responding to the independent adversarial review
of round 2 (`docs/issue-2915/reports/adversarial-review-708b12ce.md`,
landed via PR #2931). canonical: `gh pr view 2931`, this turn — result:
`state: MERGED`. Brought over round 1 and round 2's own work
(`issue-2915/diagnose-first+observability-methodology-selection-f198342c`,
still open as PR #2917) onto this branch via `git cherry-pick` of its
seven commits (`974b0f12 02958772 e755ffea 0cbf3dc9 db8b355c 2fc615fd
93e67494`) — derived: `git diff HEAD
origin/issue-2915/diagnose-first+observability-methodology-selection-f198342c
-- docs/handbooks/monitor-liveness.md on-the-record/monitors`, this
turn, result: empty diff (byte-identical) — before making round 3's own
changes on top, per this round's instruction to base on PR #2917's
content while committing to this session's own branch.

**Finding 1 (MAJOR), resolved by withdrawing the bound claim, not by
building a consumer.** Re-confirmed the review's central fact
independently before deciding: derived: `grep -rn "monitor-heartbeat"
--include="*.py" --include="*.sh" --include="*.md" .`, this turn — the
only hits are the emitting code (`poll_heartbeat_delta.py:251,273`), its
own comment, its two tests, and the handbook's own prose; no code in
`relay.py`, `hook_fires.py`, `watchdog.py`, `spawn.py`, or any
`on-the-record/hooks/*.sh` reads a `[monitor-heartbeat]` line or alerts
on its absence — matching the review's own enumeration exactly. Also
re-confirmed the pre-existing staleness-check call sites are unchanged:
derived: `grep -rn
"_monitor_liveness_check_and_notify\|poll_heartbeat_alive.json\|MONITOR_LIVENESS_STALE_SECONDS"
--include=*.sh --include=*.py .`, this turn — exactly the same two
production call sites round 2 enumerated (`directive.sh:272`,
`stop-poll-rearm.sh:133`), plus `poll-heartbeat.sh:159`'s alive-stamp
write.

Constructed the literal dead-monitor scenario the issue's acceptance
check asks for — a genuine kill, not a synthetic "still alive but quiet"
tick — derived: a from-scratch script
(`/tmp/issue2915r3/dead_monitor_scenario.py`, not committed, not any
prior round's harness) that runs the real, unmodified
`on-the-record/monitors/poll_heartbeat_delta.py` for a 1h warm-up
(healthy roster, real 120s-aligned ticks), then simply stops invoking it
— no more ticks, no more touches of the alive-stamp file — and checks,
at +1h/+3h/+24h/+388min (the #1497/#2182 incident length) past that
point, whether anything surfaces the death without a turn. Result, this
turn:
```
Phase 1 (ALIVE, healthy, 1h warm-up): stdout events at [0, 1800, 3600]

Phase 2: Monitor killed at t=3600s (no further invocations)
Frozen alive-stamp at death: {'last_tick': 3600}
  at now=death+3600 (+1h): ... 0 surfacing events regardless of how large this horizon grows.
  at now=death+10800 (+3h): ... 0 surfacing events regardless of how large this horizon grows.
  at now=death+86400 (+24h): ... 0 surfacing events regardless of how large this horizon grows.
  at now=death+23280 (+388min ...): ... 0 surfacing events regardless of how large this horizon grows.

Phase 4: a turn FINALLY arrives at death+3h (arbitrary -- could as easily never arrive).
   [orchestrate][MONITOR-DEAD] poll-heartbeat monitor dead since ... (age=10800.0s, threshold=360.0s)  (17.6ms once invoked)
```
This confirms the review's finding directly rather than by re-reading
it: the beacon cannot detect its own emitter's death, because nothing
in this repo watches for its absence independent of a turn, and the
turn-driven staleness check (already real, already correct, unchanged by
round 2) never runs without one.

Considered, and rejected with a stated reason, the "build a real
consumer" branch of the finding's either/or: any consumer this repo
could build would have to wake on the same turn-driven hook path the
pre-existing `poll_heartbeat_alive.json` staleness check already uses —
canonical: `on-the-record/monitors/poll-heartbeat.sh:148-159` (`touch`/
`_alive_stamp_write`, "written on EVERY iteration regardless of the
due/not-due outcome"). That stamp is strictly finer-grained than a
beacon that only updates every ~1800-1920s, so a beacon-absence consumer
would be a strictly weaker, redundant duplicate of a check that already
exists — new code and surface area for zero marginal detection benefit,
against this issue's own "no overhead increase, no new bugs" invariants.
A true bound on actual-death detection needs an OS-level
scheduled-execution primitive external to the session
(`docs/issue-801/proposals/technical-feasibility.md`'s "Hard boundary"),
already named as the single termination point by round 1 and round 2
alike — not a new regress, the same one, restated rather than reopened.

Edited `docs/handbooks/monitor-liveness.md`'s "Issue #2915" section
(same commit) to withdraw the "worst-case detection latency for a dead
Monitor ... bounded at ~1800s" sentence, replace it with the honest
scope (a silence-while-alive bound, not a death-detection bound),
reconcile it explicitly with the adjacent, unmodified "Structural limit:
full-idle death cannot self-heal" section it previously stood in
unacknowledged tension with, and correct the "what remains unbounded"
paragraph's too-sharp empty-roster-vs-non-empty-roster line (both are
equally unbounded for actual Monitor death, per the review's own last
paragraph on Finding 1) — derived: `git diff --stat
docs/handbooks/monitor-liveness.md`, this turn, result: `1 file changed,
88 insertions(+), 15 deletions(-)`.

**Finding 2 (MINOR), fixed in the same edit.** Corrected every place in
the handbook's new prose that stated the silence-duration bound as a
flat "~1800s (30 minutes)" to "~1800s plus up to one tick interval
(~1920s with the real 120s loop)" — canonical:
`on-the-record/monitors/poll_heartbeat_delta.py:218` (`if now -
last_emit_epoch >= 1800:`) and `on-the-record/monitors/poll-heartbeat.sh:184`
(`sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-120}"`) — the `>=`
threshold fires on the first tick at or past the bound, not exactly at
it. Did not re-derive the review's own jitter measurement (max gap
1852s on an irregular-spacing harness) since it is already independently
reproduced and cited there; used its conclusion (1800+120=1920s worst
case with the real loop) directly.

**Test suite: no regression.** derived: `python3 -m pytest
on-the-record/monitors/test_poll_heartbeat.py -q`, this turn, result:
`35 passed` — unchanged from the review's own count, since this round
touched no code, only the handbook.

Neither of this round's two skills changed anything about *what* to fix
(both were consulted before acting, per skill-verdict below), but
diagnose-first's Stage 3 (reversibility) is the frame the "build a
consumer vs. withdraw" decision above actually followed: building a
consumer is a low-value, easily-later-undone addition (reversible), but
the review's stated bar ("do not resolve it by rewording the claim while
leaving the mechanism unchanged") requires the *reason* for not building
one to be argued, not asserted — the redundancy argument above is that
argument, not a bare restatement of "it's out of scope."

## Why

The review's Finding 1 is not a wording problem, it is a category error:
round 2 measured "how long can a live, healthy, suppressed Monitor stay
silent" and reported it as "how long until a dead Monitor's death is
detected." Those are different quantities with different worst cases (the
first is now ~1920s; the second is, and remains, unbounded), and the
review's own grep-based consumer search plus the handbook's own adjacent
"Structural limit" section both independently support that the second
quantity cannot be shortened by anything this repo's code can do without
an OS-level scheduled wake, which is out of scope and already documented
as such. Given that, "give the beacon a real consumer" was evaluated
concretely (what would it wake on, how would it differ from the
already-existing alive-stamp check) rather than dismissed by assumption,
and rejected because it would add code for a signal strictly weaker than
one that already exists — not because building things is undesirable in
general. Withdrawing the claim and stating the true scope is therefore
the substantive fix, not a rewording of the same false claim: the
sentence's truth value changes (from an unbuilt, false "bounded" claim to
a true, narrower "silence-while-alive is bounded, death-detection is
not" claim), and it stops contradicting the handbook's own adjacent
section instead of leaving that tension unacknowledged.

This also matches the issue's own must-not list: no periodic
content-free notification was reintroduced (round 2's beacon is
content-carrying and untouched by this round); no watch-family signal
was made blockable, droppable, or advisory-only (nothing in the watch
path was touched); no session is unobserved for longer after this round
than before it (the silence-while-alive property round 2 built is
unchanged and still real; the death-detection property was unbounded
before round 2 and remains unbounded now — not lengthened, and this
round is explicit that it is not shortened either, rather than claiming
a shortening that was never built); and the "does the staleness function
return the right answer when called" question is not conflated with
"does anything call it" — the dead-monitor construction above measures
the second question directly, via a genuine kill, not a synthetic quiet
tick.

**diagnose-first was applicable and was invoked** (see skill-verdict
below): the task was "decide between building a consumer and withdrawing
a claim," a Stage-3 (reversibility/option-comparison) question with a
Stage-2 evidence requirement (is the claimed cause of the false bound —
"no consumer exists" — actually verified, not assumed) satisfied by the
grep re-confirmation above, and the decision documented with its
rationale rather than asserted.

**observability-methodology-selection was judged not applicable** and
was not invoked (see skill-verdict below): no new signal-bearing surface
is being added and no RED/USE/Golden-Signals dashboard choice or
redundant-overview removal arises from a detection-latency documentation
correction.

## What did not work

None — derived: `git diff --stat docs/handbooks/monitor-liveness.md`,
this turn, result: `1 file changed, 88 insertions(+), 15 deletions(-)`
applied cleanly, and `python3 -m pytest
on-the-record/monitors/test_poll_heartbeat.py -q`, this turn, result:
`35 passed`. The dead-monitor construction script, the re-confirmation
greps, the handbook edit, and this test re-run each ran to their stated
result on the first attempt; no approach here was started and abandoned.

## Upstream basis

- `docs/issue-2915/reports/adversarial-review-708b12ce.md` (landed via
  PR #2931, merge sha `4677971899e70dd63d51f4d76cf6f52c8ad25470`) — the
  independent review this round responds to point by point (Finding 1
  MAJOR, Finding 2 MINOR).
- `docs/handbooks/monitor-liveness.md` — edited in this same commit
  (`sha: same-commit`).
- `issue-2915/diagnose-first+observability-methodology-selection-f198342c`
  (PR #2917, still open) — its seven commits cherry-picked onto this
  branch as the base for this round's own edits; verified byte-identical
  on the touched files before editing (see "What was done" above).
- Read directly, this turn, not restated from any prior round's record:
  `on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/poll_heartbeat_delta.py`,
  `on-the-record/hooks/directive.sh`,
  `on-the-record/hooks/stop-poll-rearm.sh`,
  `docs/issue-2906/reports/adversarial-review-30a89443.md`,
  `docs/issue-801/proposals/technical-feasibility.md`.
- `gh issue view 2915` (fetched this turn) — the acceptance checks this
  round's dead-monitor construction directly targets.

## Open findings

None. canonical: `docs/issue-2915/reports/adversarial-review-708b12ce.md`
(read in full this turn) — its two open findings are both addressed in
this same commit: Finding 1 (MAJOR) — derived: `git diff
docs/handbooks/monitor-liveness.md`, this turn, the "Round 2's claim
here was wrong and is withdrawn" paragraph replacing the withdrawn bound
claim — by withdrawing the false bound claim and stating the true scope,
with the reasoning for not building a consumer stated rather than
assumed; Finding 2 (MINOR) — derived: same diff, the "~1920s with the
real 120s loop" correction — by correcting the worst-case number from a
flat 1800s everywhere the handbook states it as a bound. Finding 3
(already confirmed a non-issue inside `adversarial-review-708b12ce.md`
itself, canonical: that record's own "Finding 3 (confirmed non-issue)"
section) required no action from this round.

## Next steps

None — `loop_state: landed`. This round's own deliverable (the handbook
correction) is not itself re-submitted for another adversarial-review
round by this session; per role scope, a future independent review of
this PR, if the orchestrator schedules one, is the next possible loop
iteration, not something this record schedules itself.
