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

**These numbers bound how fast the check flags a stale stamp once
invoked (measured: ~29ms, issue #2915), not how often the check gets
invoked.** See "Structural limit" below — as of this writing, invocation
during a genuinely healthy, quiet stretch is not bounded by anything in
this repo.

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
  turns, no upper bound.
- **2026-08-30 (#2905) - 2026-08-31 (#2913):** a one-day window where an
  unrelated change (a per-tick last-tool-activity timestamp appended to
  the `[poll-report]` HEALTHY line) accidentally defeated the delta
  suppression, so nearly every ~120s Monitor tick emitted and forced a
  turn — incidentally invoking the staleness check on roughly that
  cadence. #2913 correctly removed this noise (87.8% of a measured
  transcript's notifications carried no actionable content); doing so
  reverted the system to the #1732-onward state, not a new one.

**Measured (issue #2915, executed-live against the current build):**
30 simulated ticks of `poll_heartbeat_delta.py` fed an unchanging
`HEALTHY` report over a 3600s (60-minute) span emitted on tick 0 only
(the unconditional first-tick emit) — 0 of the remaining 29 ticks
produced any stdout, i.e. zero Monitor notifications and zero forced
turns across the full simulated hour. Separately, the staleness check
itself, once a turn does invoke it, correctly flags a stale (1000s-old)
stamp in ~29ms wall-clock — negligible next to the 360s/180s figures.
**Verdict: the 360s/180s bound was never a code-enforced maximum
detection latency; it is, and since 2026-08-18 has been, the latency of
the check itself once some turn-triggering event happens to occur.**
During a stretch with only a healthy `poll-heartbeat.sh` Monitor and no
other live watch/roster traffic, the current build's worst-case
detection latency for a dead monitor is unbounded — bounded only by
whichever unrelated event (a real user message, or a different Monitor
producing actual content) happens next. This is not worse than the
388-minute #1497/#2182 incident this mechanism was built to catch (that
incident is still caught the moment *any* turn fires), but it is not the
360s/180s the handbook previously implied either, and has not been since
12 days before the #2905/#2913 episode this issue was filed to look at.

No fix ships with this finding: the two structural options — (a) a new
low-frequency content-free "still alive" notification, or (b) an
OS-level scheduled wake outside this session — are respectively exactly
what #2913 correctly removed (issue #2915's own must-not list forbids
reintroducing it under another name) and the already-documented,
already-out-of-scope hard boundary two paragraphs up. Filed as a
follow-up rather than attempted here (see issue #2915's record's "Open
findings").

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
