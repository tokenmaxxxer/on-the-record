# Idle self-wake is CLI-only by harness constraint; IDE sessions get a one-time notice, not a fix

## Status

Accepted (issue #947, northpole req#7)

## Context

`on-the-record/monitors/poll-heartbeat.sh` is the plugin's idle self-wake
channel — a Claude Code Monitor that ticks every 60s independent of any
prompt. Per Claude Code's own documentation
(docs/specs/platform-capabilities.md, "Claude Code plugin Monitors"):
plugin Monitors run **only in interactive CLI sessions**. On a host where
the Monitor tool is unavailable (IDE-extension sessions), the platform
simply never invokes `poll-heartbeat.sh` — no error, no signal, nothing.

Turn-driven wake (the UserPromptSubmit/Stop poll-rearm hooks,
`on-the-record/hooks/directive.sh` and `on-the-record/hooks/stop-poll-rearm.sh`)
still runs in every session type, so an IDE session is not left with zero
wake capability — but it silently loses the *idle* channel with no
operator-visible signal that this happened.

## Decision

There is no plugin-side fix: no flag, setting, or environment variable
turns Monitors on in an IDE-extension session (confirmed by grep across
`on-the-record/hooks/*.sh` and `on-the-record/gates/*.py` for any
entrypoint/session-type signal, and independently by issue #947's own
investigation) — this is a harness-level constraint outside this plugin's
reach, not a bug to patch.

Instead: make the degradation observable. `poll-heartbeat.sh` writes a
workspace-scoped alive marker before entering its sleep loop.
`directive.sh` tracks this session's own start time (keyed by
`session_id`) and, once a grace window has passed with no alive marker
dated at or after that start time, prints a one-time notice that idle
self-wake is unavailable and turn-driven wake is the active mode.

## Consequences

- IDE-extension sessions get a one-time, operator-visible notice instead
  of silent capability loss — satisfies req#7's "no silent capability
  loss" standard for this specific channel.
- CLI sessions, where the Monitor does start, never see the notice: the
  alive marker appears well inside the grace window.
- This does not close the underlying gap (idle self-wake structurally
  absent in IDE sessions) — only the visibility of it. Closing the gap
  itself would require a Claude Code platform change, not a plugin
  change.

## Citation

https://code.claude.com/docs/en/plugins-reference.md#monitors (mirrored
in docs/specs/platform-capabilities.md, "Claude Code plugin Monitors")
