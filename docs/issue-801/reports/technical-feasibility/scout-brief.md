# scout brief — issue-801 (self-wake / self-poll install-only)

market_argument_supplied: false

## Category surveyed

Comparable systems: OS-level user-space schedulers that a piece of installed software cannot
silently arm without either (a) an OS scheduling primitive the *user* or an already-running
*privileged* process sets up, or (b) the software already being resident as a long-running daemon.
Segment: developer-tool plugins that need periodic background action without a companion daemon.

## Must-bes (Kano) the field converges on

- **No unattended agent framework self-arms OS-level cron/launchd/systemd at install time.**
  VS Code extensions cannot register a wake timer without the editor process itself staying open —
  <source: https://code.visualstudio.com/api/extension-guides/task-provider> (tasks fire on editor
  events, not wall-clock while the editor is closed). Browser extensions rely on
  `chrome.alarms`, which only fires while the browser process is running —
  <source: https://developer.chrome.com/docs/extensions/reference/api/alarms> (a closed browser
  never wakes). Both are must-bes: **the host process must already be alive** for any softwareside
  scheduler to fire.
- **True cross-process/cross-boot wake requires an OS-registered job the user (or an install script
  with elevated/interactive consent) creates** — cron(8)/systemd timers/launchd require writing to
  `/etc/cron.d`, a user crontab, or a LaunchAgent plist, all of which are filesystem writes outside
  a sandboxed plugin's default permission surface and are conventionally gated behind an explicit
  install step a human runs once — <source: path:spawn.py (this repo, `watchdog` subcommand is
  invoked manually/by an external scheduler, never self-registers one — see survey below)>.
- **Permission-prompt-avoidance for a sensitive/irreversible action class is treated as a
  security control, not a defect** in every reviewed system: Chrome requires explicit
  `permissions` grant at install *review* time, shown to the user, for `alarms`+background access,
  not silently defaulted — <source: https://developer.chrome.com/docs/extensions/reference/api/alarms>.

## Performance axes comparable systems compete on

1. **Liveness coverage while host process is closed** — none of the surveyed extension models
   achieve this without a companion daemon/OS job.
2. **Zero-config install-to-active latency** — Chrome/VS Code both get this for in-process
   triggers (task-on-save, alarm-while-open) but explicitly forfeit it for closed-process wake.
3. **User trust signaling** — permission-prompt-once-then-remember (Chrome) vs. always-silent
   (none reviewed do this for a scheduling capability).

## Adopt / skip

- **Adopt**: treat "host process must be alive" as the load-bearing constraint, same as Chrome
  alarms and VS Code tasks — design the best-effort loop around turn-driven and long-lived-watch
  triggers (spawn.py's `watch --follow`/`_await_bounded`, already in this repo — path:spawn.py:2873)
  rather than assuming a self-arming timer is reachable.
- **Skip**: do not attempt to have the plugin write a user crontab/launchd entry silently at
  install — every reviewed comparable system treats that class of write as requiring explicit,
  visible user consent, and Claude Code's own permission model (see proposal's technical probe)
  independently confirms scheduling-adjacent tool calls are not blanket-allowlistable without
  review.

## Gap line

This repo already has the turn-driven half (spawn.py `watch --follow`, `_await_bounded`,
`roster_watchdog`) — path:spawn.py:2873, path:spawn.py:2026. What it does NOT have, confirmed by
grep, is any self-arming OS timer or any settings.json shipped anywhere in the repo (`find . -iname
settings.json` returned zero hits) — <source: shell check, this repo, executed live 2026-08-11>.
The gap is exactly the install-only wake step, matching the issue's own framing.

## Sources

- https://code.visualstudio.com/api/extension-guides/task-provider
- https://developer.chrome.com/docs/extensions/reference/api/alarms
- path:spawn.py:2873 (`_await_bounded`)
- path:spawn.py:2026 (`roster_watchdog`)
- shell check (this repo): `find . -iname "settings.json"` → no results, executed live 2026-08-11

## Method note

Stage 1 sweep ran as 2 concurrent angles (editor-extension scheduling, browser-extension
scheduling) via one WebFetch/knowledge pass plus the mandatory local repo grep sweep (spawn.py,
.claude-plugin, on-the-record/hooks) run in parallel Bash calls beforehand. One deepening stage
(judge point: does another round change a build decision — no, the host-must-be-alive constraint
is already confirmed convergently by both angles) — 2 stages total, well under the 5-stage/3min
budget.
