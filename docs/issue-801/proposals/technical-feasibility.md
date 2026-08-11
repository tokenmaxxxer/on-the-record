---
status: proposed
files:
  - docs/issue-801/proposals/technical-feasibility.md
  - docs/issue-801/reports/technical-feasibility/survey.md
  - docs/issue-801/reports/technical-feasibility/scout-brief.md
---

# Proposal — install-only autonomous ~60s self-poll/self-wake (issue #801, phase 1: design)

market_argument_supplied: false

## Intent

Determine whether on-the-record can reach true install-only (no `/loop` typed, no CI, plugin
elements only) ~60s self-polling and self-wake for quiet gaps, per req #7, and if not, name the
hard boundary and recommend the least-fragile maximal-autonomy design that still reaches a plain
target session, not only the orchestrator's own.

## Constraints found so far

- req #7: zero user action beyond installing the plugin; hooks/directives/plugin-shipped
  `settings.json` only.
- Plugin `settings.json` today supports only the `agent` and `subagentStatusLine` keys — no
  `permissions` key exists to place an allow-rule into
  (<source: https://code.claude.com/docs/en/plugins.md>; see survey.md Probe 1 finding 1).
- `ScheduleWakeup` is session-scoped: it stops when the session ends and does not fire once the
  process has died (<source: https://code.claude.com/docs/en/scheduled-tasks.md>; survey.md Probe
  1 finding 2) — it cannot by itself cover "session stalled/dead, no human present."
- Persistent cross-restart scheduling exists only as Anthropic-hosted Routines, which the user
  must explicitly create — disqualified by req #7's zero-extra-setup requirement
  (<source: https://code.claude.com/docs/en/scheduled-tasks.md>).
- `spawn.py`'s watchdog/watch machinery (`roster_watchdog`, `_await_bounded`, `watch --follow`)
  already exists in-repo and is the closest thing to a quiet-gap mechanism, but every path into it
  requires an already-running process — none of it self-arms (path:spawn.py:2026,
  path:spawn.py:2873, path:spawn.py:3721-3733).

## Timebox and acceptance criteria

**Timebox:** this phase-1 investigation was scoped to a single research pass (1 day, within the
1-3 day spike convention) — already executed live 2026-08-11 via direct repo inspection
(spawn.py, on-the-record/hooks, `find`/`grep` for settings.json and scheduling env vars) plus one
live Claude Code documentation lookup (claude-code-guide agent reading code.claude.com/docs). No
further timebox is requested for phase 1; phase 2 (implementation) timebox, if the verdict below
is accepted, is scoped separately at approval.

**Acceptance criteria (from the issue, carried verbatim):** a feasibility record states, with
evidence (actual settings.json permission behavior + a run), whether a plugin-shipped default
permission enables self-wake without `/loop`; if yes, an implemented loop self-polls a quiet
in-flight session within ~60s with no user input; if no, the shipped watchdog/best-effort design
is implemented and demonstrably attends a quiet stalled session. Empty state: no in-flight
sessions ⇒ the loop/watchdog idles with no spurious wake, asserted. Provenance: executed-live.

## Candidates considered

1. **Plugin-shipped `settings.json` permission allowlist for `ScheduleWakeup`/cron** — rejected:
   the plugin-settings schema does not have a `permissions` field at all today
   (<source: https://code.claude.com/docs/en/plugins.md>); there is nothing to allowlist into.
   Not a classifier-policy question, a schema-absence question — the strongest and cleanest
   reject reason of the four candidates.
2. **Anthropic-hosted Routine, plugin-triggered creation** — rejected: creating a Routine is a
   user-visible, user-confirmed act by product design (<source:
   https://code.claude.com/docs/en/scheduled-tasks.md>); a plugin cannot silently provision one,
   so this fails req #7's "user does nothing but install" bar even though it would technically
   solve persistence.
3. **`spawn.py` watchdog as a self-arming OS-level daemon (cron/launchd/systemd timer written by
   the plugin at install)** — rejected: this is exactly the write class every comparable system
   surveyed (VS Code tasks, Chrome `alarms`) treats as requiring explicit, visible user consent,
   not a silent install-time write (scout-brief.md, Adopt/Skip section); Claude Code plugins have
   no OS-level scheduling primitive either (<source: https://code.claude.com/docs/en/scheduled-
   tasks.md>, "Plugins cannot create cron jobs, launchd entries, or systemd timers").
4. **Hybrid best-effort: turn-driven poll (UserPromptSubmit hook, existing #782 dual-channel) +
   Stop-hook re-arm nudge + `spawn.py`'s existing `watch --follow`/`_await_bounded` used by
   whichever process (orchestrator or a human) is already alive** — **chosen**. Does not achieve
   true quiet-gap coverage when *nothing* is alive (no candidate does, per the hard boundary
   below), but it is the only candidate that (a) requires zero extra user setup beyond install,
   (b) is buildable entirely with elements already in this repo, and (c) demonstrably narrows the
   quiet-gap window to "however long the last live process's `stall_timeout_min`/`--max-wait`
   window is," rather than "unbounded until the next human message," which is the issue's actual
   complaint.

## Verdict

**Decision: conditional**

**Conditions (blocking, external to this repo):**
- True install-only, zero-classifier-friction `ScheduleWakeup`/cron self-wake that survives the
  triggering session's own death is blocked externally: it requires Anthropic to add a
  `permissions` (or equivalent scheduling-grant) key to the plugin `settings.json` schema, which
  this repo cannot self-grant (<source: https://code.claude.com/docs/en/plugins.md>). Until that
  ships, req #7's literal ask ("self-wake on plugin-install-alone, no `/loop` typed, no CI") is
  not achievable in full.

**Scope constraint (go, resolvable within this repo — candidate 4):** implementing the hybrid
best-effort design (turn-driven poll + Stop-hook re-arm + reuse of `spawn.py`'s existing
`watch --follow`/`_await_bounded`/`roster_watchdog`) is a two-way, low-cost, in-repo change with
no external blocker, and is recommended to proceed to phase 2 regardless of when/whether the
external condition above resolves. `verdict_provisional: feasible-with-conditions` — the
in-repo-resolvable prerequisite is that phase 2 must demonstrate the ~60s bound empirically (a
real `watch --follow` run against a deliberately stalled session), not merely assert it, per the
issue's Acceptance provenance requirement.

## Hard boundary (explicit answer to the issue's question)

A plugin **cannot**, by itself:
1. add a `permissions`-style grant via its shipped `settings.json` — the schema does not expose
   that field (only `agent`/`subagentStatusLine` today);
2. create any OS-level scheduled-execution primitive (cron/launchd/systemd timer) — no plugin API
   for this exists;
3. keep a session's `ScheduleWakeup` armed once that session's own process has exited — the
   mechanism is explicitly session-scoped and stops at session end;
4. provision an Anthropic-hosted Routine without a visible, explicit user action.

What a plugin **can** do, install-only, with zero extra user setup: ship hooks that fire on every
turn/tool-use/session-start/stop (already true of this repo), and reuse any already-running
process's own blocking-poll loop (`watch --follow`) to shrink the detection window for a quiet
stalled session down to that process's own `stall_timeout_min`/`--max-wait` ceiling. That is the
maximal autonomy reachable under req #7 today.

## Measurement design

Phase 2, if approved, must record (per the issue's Acceptance and this repo's provenance
convention): the actual wall-clock gap between a deliberately stalled target session and the
watch/watchdog process noticing it, across at least one live run; and an idle-state run (no
in-flight sessions) showing zero spurious wakes. Both runs' raw output get pasted into the
phase-2 record, not summarized only.

## What did not work

None.
