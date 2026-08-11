# Platform capabilities not derivable from this repo

This repo's gates (`gates/gates.py`, `gates/ci.py`) can only check what is
present in this repository's own tree. Some capabilities are properties of
the underlying platform (Claude Code) itself, not of this repo, and no
repo-local check can confirm or deny them — a survey that concludes "no
mechanism exists to do X" must check this file's pointer first, not just
this repo's own configured surface.

## Claude Code hook events

`on-the-record/hooks/hooks.json` currently configures three event types:
`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `Stop`. Claude Code's
hook system supports more event types than these four — the authoritative,
current list lives in Claude Code's own documentation (not mirrored here,
since it would go stale the moment the platform adds an event this repo
hasn't configured). A survey concluding "no hook can observe X" is a claim
about this repo's *configured* `hooks.json`, not about the platform's
actual capability — those are different claims, and only the first is
mechanically checkable from this repo's tree.

This fact is stated once, here, as unchecked/unmechanizable — a platform
property, not a repo-derived claim. No gate in `gates/gates.py` claims to
verify it.

## Claude Code plugin Monitors

`on-the-record/monitors/monitors.json` (issue #835) declares a Monitor,
`on-the-record/monitors/poll-heartbeat.sh`, with `"when": "always"`. Per
Claude Code's own documentation (code.claude.com/docs: plugins.md,
plugins-reference.md — not mirrored here, for the same staleness reason
as the hook-events section above):

- A plugin-shipped Monitor auto-starts when the plugin is active on a
  user-scope install — no manual step, no `/loop` needed.
- A Monitor is **session-bound**: it runs only for the lifetime of the
  session that started it and does NOT survive that session's death or
  reboot. This is the same hard boundary docs/issue-801's technical-
  feasibility survey found for install-only self-wake — a Monitor
  narrows the *turn-boundary* quiet gap between hook-driven polls; it
  does not close the *session-death* gap, which remains externally
  blocked (no plugin API for OS-level scheduling).
- Monitors load only for user-scope plugins, not project-scope.
- On a host where the Monitor tool is unavailable, the platform silently
  skips the Monitor — `poll-heartbeat.sh` is simply never invoked. The
  existing turn-driven hooks (`on-the-record/hooks/directive.sh`,
  `on-the-record/hooks/stop-poll-rearm.sh`) are unaffected by this and
  keep polling exactly as before, so behavior on such a host is
  unchanged by this feature, never worse.

As with the hook-events section above, this is a platform property, not
a repo-derived claim, and no gate in `gates/gates.py` claims to verify
it.
