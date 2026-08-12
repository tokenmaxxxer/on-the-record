---
subject: issue-922
kind: survey
---

# Current-state survey — default-on per-cycle monitor report (issue #922)

## Background / context

canonical: docs/issue-922 (`gh issue view 922`, read this session) —
operator diagnosis (2026-08-12): the poll machinery (#782/#829
poll-rearm, #835/#841 Monitor) already ticks ~60s in any installed
session, but its "report the result to the user in writing every
cycle" half was never actually wired to reach the user — it writes to
a log, not to the user-visible channel. Judgment-needing responses
additionally need the orchestrator LLM, which the plugin cannot
self-wake (#801).

canonical: docs/specs/platform-capabilities.md ("Claude Code plugin
Monitors" section, read this session) — this repo's own spec already
records, from the same official docs re-verified this session (see
`scout-brief.md`, Sources), that a plugin Monitor auto-starts on a
user-scope install with no manual step, is session-bound (dies with
the session, no reboot survival), and is silently skipped where the
Monitor tool is unavailable.

canonical: derived: `cat on-the-record/monitors/monitors.json` (read
this session) — the only declared monitor is `poll-heartbeat`,
`"when": "always"`, running `poll-heartbeat.sh`.

canonical: on-the-record/monitors/poll-heartbeat.sh:1-58 (read this
session) — the script loops `sleep 60` then calls
`poll_rearm_arm_if_due()` and prints exactly one of two thin lines to
its OWN stdout: `"poll tick: due, watchdog armed"` or `"poll tick:
skipped (within TTL)"`. This is the entire per-tick text the platform
actually has to deliver — see below for why that matters.

canonical: derived: `grep -n "poll_rearm_arm_if_due" on-the-record/hooks/poll-rearm.sh`
(read this session, lines 54-74) — `poll_rearm_arm_if_due()` launches
`spawn.py watchdog --auto-respawn` via `nohup ... >>poll-watchdog.log
2>&1 &` — a DETACHED background process whose stdout is redirected to
a log file, not returned to the caller. `poll-heartbeat.sh` never reads
that log; it only knows whether arming happened, not what the
watchdog's scan produced.

canonical: spawn.py:2349-2450 (`roster_watchdog()`, read this session)
— this function already computes exactly the content #922 is asking
for: a `[poll-report] <key>: <state> — <detail>` line per live-or-
just-died roster entry, where `<state>` is one of a fixed small label
set (healthy / stalled / deadlocked / dead-errored / a null state
printed as a finished-session label) produced by `diagnose_health()`/
`watchdog_check_one()` (spawn.py:2025-2125, which itself detects log-
silence, watcher-missing/dead/silent, no-commits-late, denied-tool-
calls, and deadlock-signature repeats); a `[health]` escalation line
with a `next_action`; a `[resume]` line when it mechanically resumes a
headless orchestrator on a ready PR; and the literal empty-state lines
`"돌고 있는 역할 세션 없음"` / `"이상 신호 없음"` when the roster is
empty and clean — i.e. the "quiet cycle still reports nothing in
flight" requirement is already implemented in this function, just not
routed anywhere the Monitor forwards.

canonical: WebFetch https://code.claude.com/docs/en/plugins-reference,
section "### Monitors" (read this session) — official text: "Each
monitor runs a shell command for the lifetime of the session and
delivers every stdout line to Claude as a notification" and "They run
only in interactive CLI sessions... and are skipped on hosts where the
Monitor tool is unavailable."

canonical: WebFetch https://code.claude.com/docs/en/tools-reference,
section "## Monitor tool" (read this session) — official text: Monitor
"feeds each output line back to Claude, so it can react... Claude
interjects when an event arrives." The verb the platform documents is
delivery-into-context plus discretionary reaction, not a forced
verbatim relay to the human on every line.

## Problem stated without any solution attached (JTBD tuple)

The issue text names its own preferred mechanism (make the Monitor's
stdout rich) before stating the job. Restated, stripped of mechanism:

- **Job performer**: an operator who has on-the-record installed as a
  user-scope plugin and is working in a session against a target repo
  — not typing `/loop`, not manually arming anything.
- **Job**: know, at roughly the cadence something could actually go
  wrong (~60s), whether in-flight work is progressing, without having
  to remember to ask, and without having to separately trust that a
  problem which needed no judgment (dead poller, lost watch, un-
  committed record) was actually fixed rather than merely logged
  somewhere unread.
- **Circumstance**: the polling/detection machinery already exists and
  already computes per-session health and some mechanical repairs
  (#782/#829/#835 + `roster_watchdog()`); the gap is not detection or
  repair, it is that the RESULT of a tick currently lands in a log file
  (`poll-watchdog.log`) that nothing surfaces to the operator, and
  judgment-needing findings have no live orchestrator to escalate to
  inside a plugin-only, self-wake-incapable boundary (#801).
- **Desired outcome**: every ~60s tick leaves a trace the operator can
  actually read in the session — what is in flight and its health,
  what was mechanically fixed, and what still needs a human or a live
  orchestrator's judgment — including an honest "nothing in flight"
  when that is true, and an honest "delivered to Claude, whether it
  became visible text this tick was Claude's call" where the platform
  does not go further than that.

Gap note: the issue frames "make Monitor stdout rich" as if that alone
closes the loop. It closes the DELIVERY half (already platform-
guaranteed once stdout carries the content) but the job's real ask —
that a report ACTUALLY REACHES the operator's eyes every cycle — has a
second half the platform documents as discretionary ("Claude
interjects... when an event arrives"), not mandatory-every-tick. The
proposal must design for the delivery half honestly and state the
discretionary half as a named, cited limitation rather than close over
it silently.

## Where this sits in the opportunity-solution tree (OST)

- **Outcome**: operator trust that in-flight work is being watched
  without the operator having to personally poll for it (the same
  outcome #782/#829/#835/#841 were built toward).
- **Opportunity**: the "report reaches the user" leg of that outcome is
  unmet — detection and some mechanical response already exist
  (`roster_watchdog()`), but their output is captured by a log file
  instead of the one channel (Monitor-delivered stdout) the platform
  actually pipes to the model by default.
- **Candidate solutions** (this proposal evaluates, does not yet
  choose beyond the one live candidate the issue itself names as the
  key mechanism to evaluate):
  1. Route `roster_watchdog()`'s existing per-tick text through
     `poll-heartbeat.sh`'s own stdout (the issue's named candidate;
     evaluated below).
  2. A separate always-on notification channel outside the Monitor
     primitive (e.g. a file the operator is told to tail) — rejected
     up front: reintroduces the exact "operator has to remember to
     look" failure the issue is trying to close, and duplicates
     delivery machinery the platform already provides for free.
- **Discriminating assumption test**: does the Monitor's documented
  delivery guarantee ("every stdout line... to Claude as a
  notification") actually reach the human as VISIBLE TEXT on a quiet
  cycle in a fresh, `/loop`-free, headless-excluded interactive
  session — or only on cycles where Claude independently decides to
  interject? This is exactly the honest boundary the issue asks to be
  stated plainly, and it is the open discriminating test the #776
  harness must probe (see proposal, "How you will know it worked").
