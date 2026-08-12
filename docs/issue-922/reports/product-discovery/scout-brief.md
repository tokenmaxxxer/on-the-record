---
subject: issue-922
kind: scout-brief
---

# Scout brief — default-on per-cycle monitor report (issue #922)

Mode: batched-sequential WebFetch of official docs (2 stages, ~2min
wall-clock) — this is a platform-verification task, not a competitive
product sweep, so "angles" are the platform's own doc surfaces
(plugins-reference, tools-reference/Monitor tool) rather than external
exemplars. No product/competitor angle applies: the deliverable is a
protocol design against one fixed platform (Claude Code), not a market
choice.

## Must-bes extracted from the platform's own contract

- A plugin Monitor auto-starts on plugin activation, no user action
  (plugins.md, "Add background monitors to your plugin": "Claude Code
  starts each monitor automatically when the plugin is active").
- "Each stdout line from `command` is delivered to Claude as a
  notification during the session" (plugins-reference.md #monitors).
  Same primitive as the interactive `Monitor` tool: "feeds each output
  line back to Claude... Claude interjects when an event arrives"
  (tools-reference.md #monitor-tool).
- Constraint, load-bearing for #922's "any installed session" scope:
  "They run only in interactive CLI sessions... and are skipped on
  hosts where the Monitor tool is unavailable" (plugins-reference.md
  #monitors).

## Gap line

What the field (platform contract) already gives: guaranteed delivery
of stdout-as-notification into Claude's context, with no user action
required to start it (`monitors.json`, `"when": "always"`) — this repo
already has that half wired (#835, `poll-heartbeat.sh`).

What the platform does NOT give, and #922's proposal must therefore
supply or honestly flag rather than assume:
1. The doc's own verb is "Claude interjects when an event arrives" /
   Claude "can react" — delivery-to-model is guaranteed, verbatim
   relay-to-user-as-visible-text every tick is not a platform-enforced
   guarantee; it is the receiving model's discretion. #922's own
   phrasing ("the report-to-user half was never actually wired")
   undersells how much IS wired (delivery) and overstates what
   scripting alone can force (the interject decision itself).
2. Interactive-only: a headless invocation (`claude -p`, no TTY) never
   starts the Monitor at all — the platform silently omits it, same
   silent-skip behavior already documented for a Monitor-unavailable
   host. This directly bounds what the #776 harness can assert about
   headless role sessions (this very session is headless).

## Adopt / skip

- Adopt: reuse the existing delivery primitive (#835 Monitor, `when:
  "always"`) — do not build a second poller. Make `poll-heartbeat.sh`'s
  OWN stdout rich, since that stdout is the thing the platform
  contractually delivers.
- Adopt: `spawn.py`'s `roster_watchdog()` already computes exactly the
  content #922 asks for (per-session HEALTHY/STALLED/DEADLOCKED/DEAD
  states, `[poll-report]`/`[health]` lines, "돌고 있는 역할 세션 없음" /
  "이상 신호 없음" empty-state lines, auto-respawn-on-crashed as an
  existing mechanical response) — but its output currently lands in
  `poll-watchdog.log` via `nohup ... &>>log &`, never reaching
  `poll-heartbeat.sh`'s own stdout, which is the one thing the Monitor
  actually delivers. Adopt: pipe that content through instead of
  reinventing a status summarizer.
- Skip: building a second, judgment-capable auto-responder inside the
  Monitor script. The platform boundary (delivery-to-model only) plus
  #801's already-documented no-self-wake finding make a plugin-side
  autonomous "diagnose and fix" step out of reach; the proposal must
  design the honest surface-and-wait boundary instead of pretending
  around it.

Sources:
- https://code.claude.com/docs/en/plugins (Add background monitors to
  your plugin)
- https://code.claude.com/docs/en/plugins-reference (### Monitors)
- https://code.claude.com/docs/en/tools-reference (## Monitor tool)
