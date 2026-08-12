---
subject: issue-922
kind: proposal
status: proposed
---

# Proposal — default-on per-cycle monitor+respond+report (issue #922)

## Candidate comparison (RICE)

Only one candidate is realistic given the platform's own delivery
primitive (see survey OST section); scored against the rejected
alternative for the record, per this facet's own citation/prioritization
gate.

| Candidate | Reach | Impact | Confidence | Effort | RICE (R*I*C/E) |
|---|---|---|---|---|---|
| A. Route `roster_watchdog()`'s stdout through `poll-heartbeat.sh` | every user-scope installed interactive session (10) | closes the exact gap the issue names (8) | high — reuses code already proven at #782/#835 (8) | small, no new detection logic (2) | 320 |
| B. Separate file/channel operator must tail | same reach (10) | low — reintroduces "must remember to look" (3) | high the mechanism works, low it solves the job (5) | small (2) | 75 |

Evidence for Impact/Confidence scores: `derived: cat
on-the-record/monitors/monitors.json` and `spawn.py:2349-2450`
(read this session, cited in survey) — candidate A's plumbing already
exists end-to-end except the one stdout-capture hop; candidate B adds a
new surface with no platform delivery guarantee behind it (survey,
"Candidate solutions" bullet 2). Candidate A is the design carried
forward.

## What will be done (design, no code)

**Mechanism**: `poll-heartbeat.sh` synchronously captures
`roster_watchdog()`'s own per-tick text — either by calling
`spawn.py watchdog --auto-respawn` in the foreground and capturing its
stdout (instead of the current `nohup ... &>>log &` detached launch),
or by tailing `poll-watchdog.log` from the byte offset it held at the
start of this tick — and echoes that captured text, verbatim, as its
OWN stdout for this tick. That stdout is the one thing
`monitors.json`'s `"when": "always"` declaration causes the platform to
deliver to Claude as a notification (survey, plugins-reference.md
citation). No new detection code, no new mechanical-response code: the
per-session HEALTHY/STALLED/DEADLOCKED/DEAD-ERRORED classification,
the auto-respawn-on-crashed action, the auto-resume-on-ready-PR action,
and the `"돌고 있는 역할 세션 없음"`/`"이상 신호 없음"` empty-state
lines are `roster_watchdog()`'s existing behavior (survey,
spawn.py:2349-2450) — this proposal's only change is making
`poll-heartbeat.sh` forward that already-computed text instead of
letting `nohup` swallow it into an unread log.

**Report shape carried through** (already produced by
`roster_watchdog()`, unchanged): per in-flight session, one line naming
it and its health state with a one-clause reason; for each state that
is not the healthy state, the `next_action` text already attached by
`diagnose_health()`; a `[resume]`/auto-respawn line wherever
`roster_watchdog()` already took that mechanical action this tick; and,
when the roster is empty and the board-wide sweep is clean, the
existing "quiet, nothing in flight" pair of lines rather than silence.

**The honest judgment/mechanical split** (survey JTBD "desired
outcome"): mechanical actions this proposal's report can honestly claim
as DONE are exactly the ones `roster_watchdog()` already performs
autonomously and prints as having performed — auto-respawn on a
`crashed` verdict, auto-resume on a ready PR, and re-arming text
(spawn.py's own `watcher-dead`/`watcher-silent` anomaly lines already
name the exact re-arm command as remediation text, not as an action
taken — that remains a SURFACE, not a fix, because re-arming a watch is
scoped to the session that owns the watch, and the plugin cannot pick a
target session to act on behalf of per #801). Everything else —
`STALLED`, `DEADLOCKED`, `DEAD-ERRORED`, a board-wide violation, an
un-committed record — is surfaced with its existing `next_action` text
and explicitly left for the orchestrator LLM or the human, because
#801's finding stands unchanged by this proposal: a plugin process
cannot self-wake a dormant orchestrator session. No new claim is made
that this proposal closes that boundary; it only makes the boundary
VISIBLE every tick instead of invisible.

**The delivery-vs-visibility gap, stated plainly** (survey "Discriminating
assumption test"): the platform's own documentation states monitor
stdout is delivered to Claude as a notification and that Claude
"interjects... when an event arrives" — delivery into context is
platform-guaranteed by `"when": "always"`; a from-context, unprompted
chat message rendering that content as visible text on every single
quiet tick is a model-judgment call the platform does not force
scripturally. This proposal cannot close that gap with a shell script —
it can only ensure the notification CONTENT is rich whenever the model
does choose to interject, which is the maximum the named platform
primitive supports. This is stated here as the limitation, not
smoothed over.

**Interactive-only boundary, stated plainly**: per the same official
doc citation (survey), a plugin Monitor "run[s] only in interactive CLI
sessions" and is silently skipped elsewhere. A fully headless
invocation (`claude -p`, no TTY — the mode this very product-discovery
role session runs in) never starts `poll-heartbeat.sh` at all. "Any
installed session" in the issue title is therefore scoped by this
proposal to "any installed INTERACTIVE session" — the accurate claim
the platform supports — and the #776 harness spec below must exercise
an interactive session, not a headless one, to test this requirement at
all.

## Out of scope

- Building a plugin-side judgment engine that decides STALLED/
  DEADLOCKED verdicts autonomously beyond what `diagnose_health()`
  already computes — that classification logic is #782's existing
  scope, reused, not re-designed here.
- Any mechanism that makes the model's decision to interject
  mandatory-every-tick — no such platform lever is documented (survey,
  Sources); asserting otherwise would be the exact fabrication the
  issue explicitly forbids.
- Closing the #801 self-wake boundary for a dormant orchestrator
  session — unchanged, cited, not re-litigated.
- Implementation itself (phase 2, pending approval): the
  `poll-heartbeat.sh` capture-hop change and its test coverage.

## How you will know it worked

Per the issue's own acceptance check, adapted to the interactive-only
scoping this proposal makes explicit: in the #776 harness, a fresh
interactive installed session (`--plugin-dir`, no `/loop` typed, no
manual watch-arming) is driven through at least one Monitor tick;
the harness asserts that `poll-heartbeat.sh`'s captured stdout for that
tick (readable directly off the process, independent of whether the
model chose to interject text to a simulated user) contains the rich
per-session report shape described above. Two scenarios: (1) nothing in
the roster — stdout carries the "quiet, nothing in flight" pair of
lines, not silence and not a fabricated problem; (2) an induced dead
poller/stalled watch fixture — stdout carries the corresponding
`STALLED`/`watcher-dead` line AND, where `roster_watchdog()` already
auto-repairs the condition (crashed-entry respawn), the report line
confirming that action was taken; where it only surfaces (stalled/
deadlocked), the harness asserts the report says so plainly with no
claim of a fix. The harness additionally records, as a named and
accepted limitation rather than a failing assertion, that verbatim
human-visible relay of that content on a given tick is the model's
documented discretion (survey citation) and is out of this harness's
power to force — the harness proves the CONTENT was delivered to the
one channel the platform delivers to, not that a human definitely saw
text this exact second.

Empty state: no session activity anywhere in the roster and no
board-wide violation → the captured stdout is exactly the two existing
empty-state lines, never blank output and never a spurious anomaly.

## Accumulation

Not accumulation-cost-shaped: the change is a fixed, one-time capture-
hop inside an existing 60s-cadence script (foreground call or log-tail
instead of a detached `nohup`), adding no new per-session or per-turn
cost beyond what `roster_watchdog()` already pays every tick today
(survey: it already runs a board-wide sweep and a per-roster-entry scan
on the same cadence, `nohup`-detached or not). No cost scales with
session count beyond the linear per-entry scan `roster_watchdog()`
already performs.

## What did not work

None.
