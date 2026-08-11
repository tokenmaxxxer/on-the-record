# scout brief — issue-835 (plugin Monitor for default-on ~60s poll/health/report)

market_argument_supplied: false

## Category surveyed

Comparable systems: the Claude Code plugin platform's own reference implementation of background
monitors, and this repo's own prior scout on host-must-be-alive schedulers (issue #801). Segment:
the exact same plugin-component family issue #801 already surveyed (issue #801 scout-brief.md),
narrowed to the one component #801 had not yet examined — `monitors/monitors.json`.

## Must-bes the field converges on

- **A monitor is a persistent background shell process started automatically by the host, not a
  tool Claude must be told to invoke** — "Claude Code starts each monitor automatically when the
  plugin is active" — <source: https://code.claude.com/docs/en/plugins.md, fetched live
  2026-08-11>. This is the one new capability #801 didn't have: it satisfies req #7's "no `/loop`
  typed" bar for the *turn-alive* case, something #801's turn-driven hooks (UserPromptSubmit/Stop)
  could not — those still require a turn to fire.
- **Monitors are gated by the same "host process must be alive" constraint** as the comparable
  systems (Chrome `alarms`, VS Code tasks) surveyed in
  docs/issue-801/reports/technical-feasibility/scout-brief.md's "Must-bes" section — "They run
  only in interactive CLI sessions... and are skipped on hosts where the Monitor tool is
  unavailable" — <source: https://code.claude.com/docs/en/plugins-reference.md, "Monitors"
  section, fetched live 2026-08-11>. No new escape from the session-bound boundary.
- **Elevated-write-class components (background monitors, MCP, LSP) are held to a stricter trust
  gate at project scope than at personal/user scope** — for project-scope skills-directory
  plugins, "Background monitors do not load," while "Personal-scope plugins have none of these
  restrictions" — <source: https://code.claude.com/docs/en/plugins-reference.md, "Skills-directory
  plugins" section, fetched live 2026-08-11>. This matches #801's must-be that a silent
  background-execution capability is treated as a security control requiring a trust boundary, not
  defaulted everywhere.

## Performance axes

1. **Cadence honesty** — a monitor is exactly one persistent shell `command`; nothing enforces
   ~60s except the script's own `sleep` loop. Anthropic's own reference examples (`tail -F
   ./logs/error.log`, a poll-deploy.sh) are open-ended loops with no built-in interval primitive
   — <source: https://code.claude.com/docs/en/plugins-reference.md, "Monitors" section, example
   `monitors/monitors.json`, fetched live 2026-08-11>.
2. **Idempotence under multiple triggers** — the reference schema's only anti-duplication
   mechanism is the `name` field ("Prevents duplicate processes when the plugin reloads or a
   skill is invoked again") — <source: same>. It does not itself dedup against unrelated
   triggers (e.g. a turn-driven hook also firing); that has to be the polled state, not the
   monitor declaration.
3. **Silent-degradation posture** — the doc states monitors are "skipped" (not errored) when the
   Monitor tool is unavailable, with no plugin-visible signal — <source: same>. A design that
   depends on the monitor for its only heartbeat has zero performance on that axis; a design that
   treats the monitor as one more caller into an already-idempotent poll path has full
   performance without additional code.

## Adopt / skip

- **Adopt**: point the monitor's `command` at a caller of the *existing* dedup gate
  (`poll_rearm_arm_if_due` → `spawn.py poll-due`, path:on-the-record/hooks/poll-rearm.sh:39-46)
  rather than writing a second polling engine — this is the same "build vs. self-arm" adoption
  #801 already made for the turn-driven hooks; the monitor becomes a third caller of one existing
  gate, not a parallel mechanism.
- **Adopt**: `"when": "always"` (session-start, the schema default) — matches req #7's "no manual
  step beyond install" bar; `"on-skill-invoke:<skill>"` would reintroduce a manual trigger.
- **Skip**: do not make the monitor the sole heartbeat mechanism — per the performance-axis
  finding above, hosts without the Monitor tool get nothing from it, so the existing #829
  turn-driven hooks must keep running unconditionally, not be superseded.
- **Skip**: do not attempt project-scope reliance — the reference doc's own restriction table
  shows monitors "do not load" under the scoped-skills-directory trust gate, so a project-scope
  install is documented to behave differently from user-scope; the plugin cannot compensate for
  this from inside its own manifest.

## Gap line

Issue #801's survey covers the turn-driven half completely (path:spawn.py:2873, poll_due at
path:spawn.py:1953-1978) and names the session-bound boundary as externally blocked. The gap this
issue closes is narrower: a session that is alive but has gone quiet *between* turns (no
UserPromptSubmit, no Stop) currently gets zero polling until the next turn fires — Monitors close
exactly that gap, and only that gap; they do not change #801's finding that session death/reboot
still stops everything.

## Sources

- https://code.claude.com/docs/en/plugins.md ("Add background monitors to your plugin")
- https://code.claude.com/docs/en/plugins-reference.md ("Monitors" and "Skills-directory plugins"
  sections)
- docs/issue-801/reports/technical-feasibility/scout-brief.md (prior sweep, same category)
- path:on-the-record/hooks/poll-rearm.sh:39-46 (existing dedup gate)
- path:spawn.py:1953-1978 (`poll_due`)

## Method note

Stage 1 sweep ran as 2 concurrent WebFetch calls (plugins-reference.md, plugins.md) in one turn,
aimed at the current-state survey's gap (this repo has no prior use of `monitors/monitors.json` —
canonical: `find . -iname monitors.json`, executed live this session, zero hits, see survey.md
Current-state survey section). One deepening read of the "Skills-directory plugins"
scope-restriction table (judge point: does it change a build decision — yes: the user-scope-only
framing in the issue body is doc-supported, per the same fetched source, not merely asserted).
2 stages total, under the 5-stage/3min budget.
