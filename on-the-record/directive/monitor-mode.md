<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. -->

Wake modes (issue #947, northpole req#7; byte-stable form per issue #2102):

- Turn-driven wake via the UserPromptSubmit/Stop poll hooks is ALWAYS
  active — every user turn and every Stop event trips the same poll/
  watchdog arming.
- Idle self-wake is a plugin Monitor (poll-heartbeat) and runs only in
  interactive CLI sessions (docs/specs/platform-capabilities.md;
  docs/decisions/2026-08-12-monitor-cli-only-fallback.md). In an
  IDE-extension or otherwise non-CLI session the Monitor never starts and
  idle self-wake silently degrades to turn-driven-only.
- Detection: directive.sh checks, past a grace window
  (MONITOR_NOTICE_GRACE_SECONDS, default 600s), whether the
  poll-heartbeat alive marker was touched at or after this session's own
  first-seen timestamp. When it was not, the degradation notice is
  written ONCE per session to `.orchestrate-wake-notice` in the
  workspace root — it is never printed into the per-turn injection
  (issue #2102: the conditional inline line was the sole byte-stability
  variance of the injected directive).
- What to do when `.orchestrate-wake-notice` exists: treat idle
  self-wake as unavailable this session; rely on turn-driven wake, and
  do not expect poll-heartbeat to interject during idle periods. Tell
  the user once if idle-latency expectations matter to the current work.
- A separate, actionable staleness line (`[orchestrate] poll-heartbeat
  monitor dead since ... -- re-arm via Monitor tool`, issue #1497 req 3)
  can still appear when a previously-armed Monitor dies mid-session; it
  is de-duped per staleness episode and asks you to re-arm via the
  Monitor tool that turn.
