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
check the stamp's age against a threshold, default **180 seconds** (3x
the 60s poll interval; overridable for tests via
`MONITOR_LIVENESS_STALE_SECONDS`). A missing stamp — the Monitor never
started this session, or this checkout has no `runs/` history yet — is
treated as stale from the very first check.

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
