# Monitor liveness: stamp, staleness threshold, re-arm directive

Issue #1497. Companion to docs/handbooks/hooks.md and
docs/decisions/2026-08-12-monitor-cli-only-fallback.md — this page covers
the disambiguation layer added on top of the existing poll/watchdog
machinery (#801, #922, #1220, #1280), not a replacement for it.

## The problem this closes

`poll_due()` (spawn.py) is a single shared TTL gate with three callers:
`poll-heartbeat.sh` (the plugin Monitor's own tick loop) and the two
turn-driven hooks (`directive.sh`, `stop-poll-rearm.sh`, via
`poll-rearm.sh`). Whichever caller asks first inside a given 60s window
wins; the others see `due=False` and do nothing observable. This means
`runs/poll_state.json`'s `last_poll` records "a tick happened somewhere,"
never "the Monitor's own loop is still iterating." A busy orchestrator
session firing turn hooks every minute can keep winning that race
indefinitely, leaving the Monitor's own due-branch silent — indistinguishable,
from outside the Monitor process, from the Monitor having actually died
(the 2026-08-14 incident this issue traces to).

## The liveness stamp

`on-the-record/monitors/poll-heartbeat.sh`'s tick loop writes
`runs/poll_heartbeat_alive.json` (`{"last_tick": <epoch seconds>}`) on
**every** loop iteration, unconditional on the `poll_due()` outcome —
sleep, stamp, then check due. The write is `flock`-guarded (a sibling
`.lock` file) the same way `poll_due()` itself is guarded in spawn.py, so
a stamp write can never race a concurrent reader mid-write. This file is
owned solely by the Monitor's tick loop; no other caller ever writes it,
which is what makes it able to answer "is the Monitor's own loop still
iterating" — a question `poll_state.json`'s shared `last_poll` cannot
answer, since a hook tick and a Monitor tick both touch it.

## Staleness threshold and the re-arm directive

`directive.sh` (UserPromptSubmit) and `stop-poll-rearm.sh` (Stop) each
check the stamp's age against a threshold — `directive.sh` defaults to
**360 seconds**, `stop-poll-rearm.sh` defaults to **180 seconds** (3x
`watchdog.POLL_INTERVAL_SEC` = 60s, the unrelated `spawn.py poll-due()`
TTL gate these same two hooks also arm — NOT `poll-heartbeat.sh`'s own
120s tick-loop sleep, a distinct interval; both are overridable for
tests via `MONITOR_LIVENESS_STALE_SECONDS`). A missing stamp — the
Monitor never started this session, or this checkout has no `runs/`
history yet — is treated as stale from the very first check.

**These numbers bound how fast this turn-driven check flags a stale
stamp once invoked (measured: ~29ms, issue #2915). They do not bound
how often the check gets invoked, or how quickly an actually dead
Monitor's death reaches the orchestrator.** See "Structural limit"
below: during a genuinely healthy, quiet stretch, nothing in this repo
bounds this check's invocation. `poll_heartbeat_delta.py`'s separate
1800s-bound beacon (issue #2915 round 2) does not close that gap
either — a dead tick loop cannot emit the beacon that would announce
its own absence. See "Issue #2915" under "Structural limit" for the
full argument.

When stale, the hook emits one line:

```
[orchestrate][MONITOR-DEAD] poll-heartbeat monitor dead since <ts> -- ACTION
REQUIRED before anything else this turn: re-arm it via the Monitor tool with
persistent: true (command: <checkout>/on-the-record/monitors/poll-heartbeat.sh)
-- a re-arm without persistent: true dies again in 5 minutes, the Monitor
tool's own default timeout_ms
```

De-dup state lives in `runs/poll_heartbeat_staleness_state.json`, keyed
by the stale stamp's own last-seen tick value (or a fixed key when the
stamp is missing entirely) — so the same staleness episode notifies
exactly once, not once per turn while it persists. A fresh stamp clears
the recorded episode silently on the next check, so a later, genuinely
new death gets its own notification.

### Issue #2182: salience and the persistent:true gap

Two gaps closed on top of the above, both found live in a 2026-08-24
session where the notice printed but the orchestrator initially missed
it:

- **Salience collision**: the notice previously shared the plain
  `[orchestrate]` tag with the always-present, byte-stable per-turn
  directive block that immediately follows it (whose own first line
  also starts `[orchestrate] You are the orchestration session...`). An
  orchestrator pattern-matching past hundreds of identical repeats of
  that block could skim right over a single preceding line with the
  same prefix. The tag is now `[orchestrate][MONITOR-DEAD]`, and a
  standing bullet in the always-on invariants block (`directive.sh`'s
  per-turn injection) tells the orchestrator this exact tag is an
  immediate-action signal, not routine noise — the same shape as the
  #878 async-completion rule.
- **The re-arm-without-`persistent:true` trap**: the Monitor tool's own
  default `timeout_ms` is 300000 (5 minutes) unless the caller passes
  `persistent: true`. The old notice text ("re-arm via Monitor tool")
  did not say this, so a literal, unqualified re-arm would silently die
  again 5 minutes later — reproducing the exact failure the notice was
  raised for, in a loop invisible to anyone who did not already know the
  tool's default. The notice and the standing invariant now both spell
  out `persistent: true` explicitly.

This repo cannot arm the *initial* auto-started plugin Monitor with a
`persistent` flag — `monitors.json` (issue #835) has no such field, and
the auto-start itself is a platform capability documented as
unmechanizable from repo code (`docs/specs/platform-capabilities.md`).
The fix therefore targets the one thing this repo does control: the
text of the re-arm instruction the orchestrator acts on, both at the
moment it is printed and in the standing rule that governs how it is
read.

Both hooks respect the existing `ORCHESTRATE_OFF=1` kill switch and
`CLAUDE_ROLE` exclusion (a spawned role session is never the
orchestrator) before running this check at all — the staleness check is
gated the same way the hooks' existing `poll_rearm_arm_if_due()` call
already is.

This is an **observe-and-direct** backstop, not an auto-fix: the hook
cannot itself re-arm a plugin Monitor (Monitors are armed once at session
start; nothing in this repo can trip one from inside a hook), so the
directive line's only job is to tell the orchestrator to re-arm it via
the Monitor tool that same turn.

## Structural limit: full-idle death cannot self-heal

Both `directive.sh` and `stop-poll-rearm.sh` are **turn-driven** — they
only fire on a UserPromptSubmit or Stop event, i.e. when the session
receives or finishes handling a user turn. If the Monitor dies during a
fully idle stretch (no user turn arriving at all, and no Monitor left to
tick), nothing in this repo observes that death or emits the re-arm
directive until the next turn actually happens. This is the same hard
boundary already recorded for the broader poll/watchdog mechanism in
docs/issue-801/proposals/technical-feasibility.md's "Hard boundary"
section (no plugin-shipped `settings.json` permissions key grants a
session-independent wake) — the liveness stamp and staleness directive
built here narrow the *detection* gap once a turn arrives, they do not
remove the *turn-driven* dependency itself. A true session-independent
wake would require an OS-level scheduled-execution primitive
(cron/launchd/systemd timer) external to this session, which is out of
scope here and would need its own issue if wanted.

### Issue #2915: the 360s/180s numbers were never an enforced upper bound

This section's own logic above already said the check only runs when a
turn happens. Issue #2915 quantified what that means during a
**healthy, quiet** stretch specifically (roster alive, nothing anomalous
— as opposed to fully idle with a dead roster), because a second
mechanism, independent of the turn-driven hooks, used to *also* force a
turn on close to the Monitor's own cadence, and that mechanism's history
is what actually determined whether 360s/180s held in practice:

- **2026-08-13 (#1220) - 2026-08-18 (#1732):** a fully-suppressed due
  tick (nothing changed) still forced one no-op "monitoring active"
  notification every 1800s (30min) as a backstop — already 5-10x looser
  than the 360s/180s figures below, but finite.
- **2026-08-18 (#1732):** that 1800s backstop was removed outright
  ("monitor liveness is already covered by the separate alive marker" —
  true only if something reads that marker on a bounded cadence, which
  nothing did). From this point, a healthy/unchanging roster entry forces
  *no* tick to print anything, ever — zero notifications, zero forced
  turns, no upper bound. This is **13 days** before the #2905/#2913
  episode below (`date -d 2026-08-31 +%s` minus `date -d 2026-08-18 +%s`
  = 1123200s / 86400 = 13), not twelve — round 1 of this issue's own
  record stated twelve, an arithmetic error corrected in round 2.
- **2026-08-30 (#2905) - 2026-08-31 (#2913):** a one-day window where an
  unrelated change (a per-tick last-tool-activity timestamp appended to
  the `[poll-report]` HEALTHY line) accidentally defeated the delta
  suppression, so nearly every ~120s Monitor tick emitted and forced a
  turn — incidentally invoking the staleness check on roughly that
  cadence, and incidentally functioning as an unintentional liveness
  signal that masked the #1732 gap for that one day. #2913 correctly
  removed this noise (87.8% of a measured transcript's notifications
  carried no actionable content). Removing it did not introduce the
  turn-gated-only detection gap — that dates to #1732, 13 days earlier —
  but it did make that pre-existing, latent gap operationally live again
  for the first time since 2026-08-18, by removing the accidental signal
  that had been incidentally covering it. Round 1 of this issue's own
  record framed #2913 as "correctly reverted an accidental cadence, not a
  new regression," which is true only in the narrow sense that #2913 did
  not *create* the gap; it elides that #2913 is what made the gap live
  again in practice, which this correction restates plainly.

**Measured before (round 1, issue #2915, executed-live against the
pre-round-2 build):** 30 simulated ticks of `poll_heartbeat_delta.py` fed
an unchanging `HEALTHY` report over a 3600s (60-minute) span emitted on
tick 0 only (the unconditional first-tick emit) and were silent for the
remaining 29 — one number, two equivalent phrasings of the same run: "1
of 30 ticks emit" (Test plan) and, counting only the 29 ticks *after* the
unconditional tick-0 emit, "0 of 29" (Summary) — both describe the same
measured run, not two different measurements. Separately, the staleness
check itself, once a turn does invoke it, correctly flags a stale
(1000s-old) stamp in ~29ms wall-clock — negligible next to the 360s/180s
figures, and unchanged by round 2 (no code in `directive.sh` or
`stop-poll-rearm.sh` was touched).

**Round 1 verdict:** the 360s/180s bound was never a code-enforced
maximum detection latency during a healthy, quiet, tracked-roster stretch
— worst case, unbounded, bounded only by whichever unrelated event (a
real user turn, or a different Monitor producing actual content) happens
next. Round 1 shipped this measurement and a handbook correction with
**no code change**, reasoning that the two apparent structural fixes were
each foreclosed: a low-frequency content-free "still alive" ping is
exactly what #2913 (and, 13 days earlier, #1732) removed, and an
OS-level scheduled wake is outside this repo's platform boundary
(`docs/issue-801/proposals/technical-feasibility.md`). An independent
adversarial review of round 1
(`docs/issue-2915/reports/adversarial-review-a74dca2a.md`) found that
conclusion unsupported against this issue's own acceptance bar ("any
change must be shown to shorten, not lengthen, the measured latency") —
a PR shipping zero code cannot satisfy "shorten" by construction — and
named a concrete, previously-existing, cheap candidate mitigation round 1
never evaluated: the #1220-era ~1800s unconditional backstop `#1732`
removed. Round 1 treated "periodic" and "content-free" as the same thing
— its "the two structural fixes are either explicitly forbidden... or
already documented as an out-of-scope platform boundary" reasoning
lumped any periodic beacon in with the issue's own content-free-ping
must-not without checking whether a periodic-but-content-carrying beacon
was available; it is, and round 2 below is it.

**Round 2 fix, measured (issue #2915, executed-live against the current
build):** `on-the-record/monitors/poll_heartbeat_delta.py`'s existing
1800s bound-check branch (previously: emit an undisposed-PR summary if
one exists, else stay silent) now also emits a `[monitor-heartbeat]`
line per non-empty tracked roster entry, carrying that entry's real
current state (not a static phrase), when nothing else fired for 1800s.
A genuinely empty roster (`poll-report:roster`'s own sentinel key,
`t_heartbeat_bound_with_no_returned_pr_emits_nothing`) is excluded and
stays exactly as silent as #1732 left it — this fix narrows the gap for
a *tracked, healthy, quiet* roster specifically, the scenario round 1's
own simulation measured, not the fully-idle/nothing-tracked case, which
remains genuinely unbounded (see below). Re-running round 1's own
simulation shape (30 ticks, 3600s) against the new build: 2 of 30 ticks
emit — tick 0 (unconditional first-tick, unchanged from round 1) and
tick 15 (the 1800s bound, new) — and extending the same simulation to 90
ticks (10800s / 3h) shows the emission strictly repeating every 1800s
(gaps: 1800s, 1800s, 1800s, 1800s, 1800s — measured, not assumed).
**Round 2's claim here was wrong and is withdrawn (issue #2915 round
3, executed-live against the current build):** round 2 originally stated
this as "worst-case detection latency for a dead Monitor ... is now
bounded at ~1800s ... an external orchestrator watching the Monitor's
stdout stream can infer death from the absence of an expected
`[monitor-heartbeat]` line." That sentence measured the wrong quantity
and directly contradicted the "Structural limit: full-idle death cannot
self-heal" section immediately above, without ever reconciling the two.
The `[monitor-heartbeat]` line can only be emitted *by the tick loop
that is itself the thing being checked for liveness* — a tick loop that
has actually died cannot emit one more line to announce its own death.
No inference from absence is possible without a consumer that watches
for that absence on some schedule independent of the dead process, and
no such consumer exists: re-checked this session (`grep -rn
"monitor-heartbeat" --include="*.py" --include="*.sh" --include="*.md"
.`), the only hits are the emitting code, its own comments, its tests,
and this handbook's own prose describing the intended consumer — no
code in `relay.py`, `hook_fires.py`, `watchdog.py`, `spawn.py`, or any
`on-the-record/hooks/*.sh` reads a `[monitor-heartbeat]` line, tracks
time since the last one, or alerts on its absence.

Constructed and measured directly (not reasoned about): a genuine kill,
not a synthetic "still alive but quiet" tick — a healthy roster ticks
normally for a 1h warm-up, then the tick loop is simply never invoked
again (no more calls to `poll_heartbeat_delta.py`, no more touches of
`poll_heartbeat_alive.json` — this is what an actual process death looks
like from the rest of the repo's point of view) and zero further turns
arrive. Checked at +1h, +3h, +24h, and +388min (the #1497/#2182 incident
length) past the moment of death: 0 surfacing events at every horizon,
because the turn-driven staleness check (`directive.sh`/
`stop-poll-rearm.sh`) is never invoked without a turn, and no turn
occurred. Elapsed wall-clock from actual death to surfaced-to-orchestrator
is therefore bounded only by whenever some unrelated event next forces a
turn — 0s if one is already in flight, unbounded if the session goes
fully idle — exactly as round 1 measured and exactly what the
"Structural limit" section above already says. Once a turn does arrive,
the pre-existing check correctly flags staleness in ~18-29ms
(re-confirmed here; not new, not in question).

Building a real absence-consumer would not close this gap either: the
only wake mechanism any consumer in this repo can use is the same
turn-driven hook path the pre-existing `poll_heartbeat_alive.json` +
staleness check already runs on, and that stamp is written on *every*
tick unconditionally (`poll-heartbeat.sh:159`, "written on EVERY
iteration regardless of the due/not-due outcome"), independent of
whether anything emits — strictly finer-grained than a beacon that only
updates every ~1800-1920s. A beacon-absence consumer would be a
strictly weaker, redundant duplicate of a check that already exists,
adding code and surface area for zero marginal detection benefit. The
chain terminates where round 1 and round 2 both already named it, and
where it stops here too: a true bound on actual-death detection needs an
OS-level scheduled-execution primitive (cron/launchd/systemd timer)
external to the session, which no plugin-shipped `settings.json`
permissions key can grant (`docs/issue-801/proposals/
technical-feasibility.md`'s "Hard boundary") — not a new open regress,
the same single, already-documented termination point.

**What round 2's beacon actually is, stated plainly:** a real
improvement to a *different* property — the Monitor's stdout channel no
longer goes dark for an unbounded stretch while the Monitor is alive and
healthy. Worst case is ~1800s plus up to one tick interval (~1920s with
the real 120s loop, not a flat 1800s — the `>= 1800` threshold check in
`poll_heartbeat_delta.py:218` fires on the first tick at or past the
bound, not exactly at it), down from unbounded since #1732. Per independent,
already-established evidence
(`docs/issue-2906/reports/adversarial-review-30a89443.md:196-198,208-211`),
non-empty Monitor stdout does force a task-notification/turn while the
Monitor is alive, so this likely does restore a turn-forcing cadence
during healthy stretches — at ~1920s granularity, narrower in scope than
the noisy ~120s cadence #2913 correctly removed. That is a genuine,
useful aliveness/observability property, described here as exactly that
and nothing more: an aliveness/observability improvement, not a
dead-Monitor detection-latency bound.

**What remains unbounded, disclosed rather than left implicit:** for the
literal failure mode this issue is about — the Monitor process itself
dying — *both* the empty-roster case and the non-empty tracked-roster
case are equally unbounded, for the identical reason (no consumer can
observe the absence of output from a process that no longer runs).
Round 2 drew too sharp a line between the two, disclosing the empty case
as unbounded while claiming the non-empty case was fixed; it was not.
The one real distinction that does hold: a fully-idle stretch with an
*empty* tracked roster (nothing spawned, no returned PRs) emits nothing
past the 1800s mark even while the Monitor is alive — confirmed by
re-running the same simulation against `EMPTY_ROSTER_REPORT`
(`[poll-report] roster: empty` / `[poll-report] quiet, nothing in
flight`): only tick 0 emits, ticks 1-29 stay silent, matching round 1's
original finding exactly for that scenario. This is deliberate, not an
oversight: `t_heartbeat_bound_with_no_returned_pr_emits_nothing` pins
that an empty roster must stay silent past the bound (#1732's own
acceptance check), and a periodic ping with nothing real to report would
be the content-free line #2913/#1732 both removed. A session with zero
spawned work and zero pending PRs has, by definition, nothing this
mechanism can say that a reader could act on. For actual-death detection
specifically, the only honest mitigation for either case (empty or
non-empty roster) remains the already-documented, out-of-scope OS-level
scheduled wake named just above.

**Call-site scope, disclosed:** round 1's enumeration ("exactly two call
sites") was bounded to `hooks.json`'s production wiring
(`directive.sh:272`, `stop-poll-rearm.sh:133`) and is accurate for that
scope. `tests/run-orchestrate-tests.sh:18` also execs `directive.sh`
directly, outside any `hooks.json` trigger, purely to test its
stdout-injection behavior — since the staleness-check function runs
unconditionally near the bottom of `directive.sh`, that test invocation
also exercises it. Test-only, not reachable from a live session, and
does not change the production-path conclusions above; named here so the
call-site count reads as scoped rather than exhaustive.

## Quiet ticks (requirement 1)

Already implemented by #1117/#1220 before this issue: a due tick's
watchdog report is line-keyed-diffed against
`runs/poll_heartbeat_last_state.json`; unchanged lines are suppressed,
changed/new lines print, and a fixed always-emit category (crash/
orphaned/resume/returned-pr/session-status keywords) bypasses
suppression every tick. A not-due tick, and a fully-suppressed due tick,
print nothing to the Monitor channel — the full watchdog report always
still lands in `~/.claude/tokenmaxxxer/poll-watchdog.log` regardless.
This issue added no new suppression code for requirement 1, only tests
(`tests/test_monitor_liveness.py::test_quiet_tick_emits_nothing` and
`::test_delta_tick_emits_only_delta`) that pin the existing behavior so a
future edit to that diff block cannot silently regress it.
