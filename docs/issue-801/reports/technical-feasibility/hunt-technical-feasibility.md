---
proposal: docs/issue-801/proposals/technical-feasibility.md
---

# Hunt record — technical-feasibility

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: commit 3acaede (docs/issue-801/proposals/technical-feasibility.md, survey.md, scout-brief.md), 346 lines / 3 files
cap_seconds: 180
tier: size:200+
diff_stat_lines: 346
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:20:00Z

Checked for a mechanism the proposal's research missed that would let a plugin self-grant
scheduling/permission capability at install time (falsifying the "structurally absent from
the schema" and "requires an already-running process" claims):

- `on-the-record/hooks/hooks.json` — all registered hook events (SessionStart, UserPromptSubmit,
  PreToolUse, PostToolUse, Stop) are session-scoped; none fire independent of a live session
  process, matching the proposal's "cannot keep armed once the process exits" claim.
- `spawn.py` grep for env vars / self-arming timers (`roster_watchdog`, `_await_bounded`, `watch
  --follow`, crontab/systemd/launchctl/`atexit`/background-daemon patterns): no self-arming path
  found; every watchdog entrypoint is invoked either from CLI (`spawn.py watchdog`) or from inside
  an already-running `watch --follow`/spawn loop, consistent with the proposal's finding at
  spawn.py:2026, 2873, 3721-3733.
- No `.mcp.json`/plugin manifest field in `on-the-record/.claude-plugin/plugin.json` or
  `hooks.json` exposes a `permissions`, cron, or persistent-timer key.
- Cross-issue precedent (grep across docs/issue-782, docs/issue-73, docs/issue-132,
  docs/reports/2026-08-07-hunt-idle-deadlock-watchdog-exit-code.md) independently reaches the same
  conclusion in prior, unrelated investigations: no cron/systemd/launchd/scheduler primitive is
  reachable from this repo or from a Claude Code plugin, and roster_watchdog has no scheduled
  caller anywhere in the tree.

Could not construct a command + wrong-output reproduction showing an install-time
self-granted scheduling capability. The proposal's own live documentation lookup (plugins.md /
scheduled-tasks.md) is externally sourced and not independently re-verifiable offline in this
session, but nothing in the local repo (spawn.py, hooks.json, plugin.json, or prior unrelated
issue investigations) contradicts it. No reproduction, no finding.
