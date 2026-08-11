# issue-801 — research survey: install-only ~60s self-poll / self-wake under req #7

market_argument_supplied: false

This is Step 1 (research) for issue #801 only. It reads the specification (req #7: hooks,
directives, and a plugin-shipped `settings.json` only — no `/loop` typed, no CI, default-on on
install alone) without the market/product argument that motivated req #7. No verdict is stated
here; the proposal (docs/issue-801/proposals/technical-feasibility.md) converges the four probes
below into a decision.

## Current-state survey

`find . -iname "settings.json" -not -path "*/node_modules/*"` returns zero results anywhere in
this repository, including under `on-the-record/` (the plugin actually shipped) —
<source: shell check, this repo, executed live 2026-08-11>. The plugin ships only
`on-the-record/hooks/hooks.json` (SessionStart/UserPromptSubmit/PreToolUse/PostToolUse/Stop hook
wiring) and `on-the-record/.claude-plugin/plugin.json` (name/description/author only) —
<source: on-the-record/hooks/hooks.json:1-70, on-the-record/.claude-plugin/plugin.json:1-6>. So
today's architecture has **zero capacity** to absorb a permissions-shipping settings.json: none
exists to extend, and (per the technical probe below) the shipped-settings.json mechanism does not
support a `permissions` key at all yet.

The only quiet-gap-adjacent mechanism that exists is `spawn.py`'s watchdog/watch machinery:
- `roster_watchdog()` (path:spawn.py:2026) is a one-shot scan over all live role sessions,
  invoked as the `spawn.py watchdog` CLI subcommand (path:spawn.py:3764-3765) — it is dispatched
  from the CLI arg parser exactly like every other subcommand (`ps`, `reconcile`, `flows`), with
  no internal loop, no timer, no self-rearm. It runs once and returns.
- `_await_bounded()` (path:spawn.py:2873) is a **blocking, in-process** poll with a
  `stall_timeout_min` ceiling; `watch --follow` (path:spawn.py:3076-3108) repeatedly calls it
  inside one already-running foreground process to stream events until session-end or
  `--max-wait` elapses (path:spawn.py:3721-3733, issue #645).
- Both require an already-running process — a human's terminal, or an orchestrator session that
  is itself alive — to exist first. Neither self-arms; both are re-armed by something already
  executing (a human running `spawn.py watch` again, per the in-code guidance strings at
  path:spawn.py:2937, 2942, 3105, 3164: "다시 spawn.py watch 로 재무장하라").

Deploy/runtime config surface: none applicable — no env vars govern a scheduling capability
anywhere in spawn.py or on-the-record/hooks (grep for `SCHEDULE|CRON|WAKE` in both trees returned
no matches beyond the watchdog naming above) — <source: shell check, this repo, executed live
2026-08-11>.

## Probe 1 — technical (spike-report + reversibility)

**Question (spike_goal):** can a plugin-shipped `settings.json` default-permission unblock a
self-wake tool call (`ScheduleWakeup`/cron/timer) with zero user action beyond install, and can
`spawn.py`'s watchdog shape close the quiet-gap without one?

**Findings**, gathered live via the Claude Code product-documentation agent (claude-code-guide,
which reads code.claude.com/docs directly) on 2026-08-11:

1. Plugin `settings.json` auto-merges into the effective session config at plugin-enable time —
   no `--settings` flag or extra user step needed beyond having the plugin installed/enabled —
   but **the schema currently supports only the `agent` and `subagentStatusLine` keys**, not
   `permissions` — <source: https://code.claude.com/docs/en/plugins.md>. This is the load-bearing
   fact: there is no field in a plugin-shipped settings.json today into which a
   `permissions.allow` entry for `ScheduleWakeup` (or any tool) could even be placed. The
   allowlist-unblock question in the issue is therefore not "blocked by the classifier" but
   **structurally absent from the schema** — a stronger and different finding than a classifier
   veto.
2. `ScheduleWakeup` exists as a session tool and is not itself gated by the interactive permission
   classifier the way a destructive Bash command is — but it is **session-scoped**: "Tasks only
   fire while Claude Code is running and idle" and "stop when you start a new one" —
   <source: https://code.claude.com/docs/en/scheduled-tasks.md>. A quiet gap where the session
   itself has stalled or died is exactly the case `ScheduleWakeup` cannot cover, because the
   mechanism requires the same session to still be alive to receive its own wakeup.
3. `permissions.allow` entries do pre-approve most tool calls, with named exceptions — explicit
   `ask` rules, org-configured-`ask` connector tools, and MCP tools marked
   `requiresUserInteraction` still prompt regardless of an allow entry —
   <source: https://code.claude.com/docs/en/permissions.md#permission-modes>. This establishes
   that *if* `ScheduleWakeup` had a permissions surface, an allow-rule could in principle
   pre-approve it (it is not in the named-exception classes) — but finding 1 means this is moot:
   there is no field to write the rule into.
4. Persistent, cross-restart scheduling (surviving the session/terminal closing) exists only as
   Anthropic-hosted **Routines**, which the user must explicitly create — no plugin can
   auto-create one — <source: https://code.claude.com/docs/en/scheduled-tasks.md>. This is an
   explicit design boundary in the product, not an oversight: "Plugins cannot create cron jobs,
   launchd entries, or systemd timers" and cannot "background a process across terminal close."

**Reversibility tag:** two-way / low-cost to test further — nothing here required a repo write;
re-confirming against a newer `code.claude.com/docs` snapshot is cheap and non-destructive if the
schema changes (feasibility-reversibility-tag convention).

**Result:** `fail: <evidence above>` — a plugin-shipped settings.json cannot default-allow
`ScheduleWakeup`/cron/timer today, because `permissions` is not a supported plugin-settings key
(<source: https://code.claude.com/docs/en/plugins.md>), independent of whatever the classifier
would otherwise decide. `spawn.py`'s watchdog shape (`roster_watchdog`, `_await_bounded`) cannot
close the quiet-gap **install-only** either, because every invocation requires an already-running
process to have started it — none of it self-arms — <source: path:spawn.py:2026,
path:spawn.py:2873, path:spawn.py:3764>.

## Probe 2 — prior_art (build-vs-buy)

There is no external library/vendor dependency to select between for this capability — the
question is a platform-capability boundary (what Claude Code plugins can self-grant), not a
library choice. Framed as build-vs-buy against the two platform-native options:

| Option | Health evidence | Verdict |
|---|---|---|
| **Buy**: Anthropic-hosted Routines (cron on Anthropic's infra) | First-party, documented, actively maintained feature — <source: https://code.claude.com/docs/en/scheduled-tasks.md> | Solves persistence but requires **explicit user setup**, which req #7 rules out ("no CI... default-on... user doing nothing but installing") |
| **Build**: repo-owned watchdog (spawn.py `roster_watchdog`/`watch --follow`) | Already exists, actively used (issue #132, #247, #645 references in-code) — <source: path:spawn.py:2026, path:spawn.py:2873> | Solves the turn/session-alive case; does not solve true install-only cross-restart wake without an external arming step (cron entry, or a long-lived `watch --follow` process someone already started) |

Neither option clears req #7 alone; both are legitimate components of a best-effort design (see
proposal). No OpenSSF-Scorecard-style health check applies — neither option is a third-party
package with its own release cadence to score.

**Result:** `pass: <evidence above>` for "no better third-party alternative exists" — the two
real options are both already surfaced above, and no additional vendor search would change which
one to combine (repo's own spawn.py watchdog + Anthropic Routines are the only two mechanisms
that exist in the product at all, confirmed via probe 1's sources).

## Probe 3 — legal_regulatory (license-scan + DPIA-before-processing)

No new third-party dependency is introduced by any candidate design (all mechanisms are either
first-party Claude Code product features or already-vendored repo code under this project's
existing license). No personal data is processed by a scheduling/watchdog mechanism — it reads
repo/session state (branch names, event logs) already local to the operator's own machine, not
end-user data — so DPIA-before-processing does not trigger.

**Result:** `pass: no new dependency, no new data category — no license or regulatory surface
introduced by any candidate` — <source: on-the-record/.claude-plugin/plugin.json (no added deps),
spawn.py (existing, already-licensed code)>.

## Probe 4 — threat_model (STRIDE, one row per element/category/trust boundary)

| Element | Trust boundary | STRIDE category | Threat | Disposition |
|---|---|---|---|---|
| Plugin-shipped `settings.json` (hypothetical `permissions` key, if the schema grows one later) | plugin install → user's effective permission set | Elevation of Privilege | A plugin silently pre-approves a sensitive tool class (e.g. `ScheduleWakeup`, or worse, arbitrary Bash) with no user review at install | **mitigated** — moot today (schema doesn't support `permissions` at all, probe 1), and if it later did, the existing named-exception classes (`ask` rules, `requiresUserInteraction`) already fence off the highest-risk tool classes per Anthropic's own docs — <source: https://code.claude.com/docs/en/permissions.md#permission-modes> |
| `roster_watchdog()` / `spawn.py watchdog` CLI | external caller (human or cron) → repo state | Tampering | An externally-arranged cron entry invoking `spawn.py watchdog --auto-respawn` unattended could respawn sessions on stale/attacker-modified repo state if the invoking environment is compromised | **accepted** — out of scope for this issue: the cron entry itself is created by the user, who already controls the machine and repo; `--auto-respawn` already caps at 2 automatic respawns before requiring a human (path:spawn.py:3741-3743) |
| A long-lived `watch --follow` foreground process | quiet gap (no user input) → orchestrator turn | Denial of Service | A stalled/deadlocked spawned session is invisible to the orchestrator until the *next* event or user prompt, per the issue's own problem statement | **deferred** — this is exactly the gap issue #801 asks the proposal to close; disposition depends on which candidate design is accepted (see proposal) |
| `ScheduleWakeup` tool call inside a live session | session process → future turn | Repudiation / reliability | A scheduled wakeup silently never fires if the session process itself has already died (product boundary, probe 1 finding 2) | **accepted** — documented product behavior ("stop when you start a new one"), not a defect this repo can fix; the best-effort design must not assume `ScheduleWakeup` survives session death |

## Grading summary

| Probe | Result |
|---|---|
| technical | fail — install-only default-permission self-wake is not achievable; watchdog shape needs external arming |
| prior_art | pass — no third option exists; the two real mechanisms are both already identified |
| legal_regulatory | pass — no new dependency/data-category surface |
| threat_model | all four rows disposed (2 mitigated/accepted-equivalent, 1 accepted, 1 deferred to the proposal's design choice) |
