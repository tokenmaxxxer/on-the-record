---
status: proposed
files:
  - docs/issue-835/proposals/technical-feasibility.md
  - docs/issue-835/reports/technical-feasibility/survey.md
  - docs/issue-835/reports/technical-feasibility/scout-brief.md
---

# Proposal — plugin Monitor for default-on ~60s poll/health/report (issue #835, phase 1: design)

market_argument_supplied: false

## Intent

Empirically confirm, against the current Claude Code plugin platform, that a plugin-shipped
Monitor (`monitors/monitors.json`) auto-starts on a user-scope install, ticks on a real ~60s
cadence, degrades cleanly where the Monitor tool is unavailable, and can call the existing #829
poll/health/report machinery without double-polling — then recommend the exact `monitors.json`
shape and the reuse seam into `spawn.py`'s poll-due/roster_watchdog machinery. No code changes in
this step.

## Constraints found so far

- req #7 (carried from #801/#829): zero user action beyond installing the plugin; no `/loop`.
- A Monitor auto-starts at session start by default (`when: "always"`) with no plugin code needed
  to arrange it — <source: https://code.claude.com/docs/en/plugins.md>; see survey.md Probe 1
  finding 1.
- Cadence is not a platform primitive — only the monitor script's own `sleep` loop produces a
  ~60s tick, inside a process the platform keeps alive for the session's lifetime —
  <source: https://code.claude.com/docs/en/plugins-reference.md, "Monitors" section>; survey.md
  Probe 1 finding 2.
- Monitors are skipped silently on hosts where the Monitor tool is unavailable, with no
  plugin-visible signal — <source: same>; survey.md Probe 1 finding 3.
- The existing `poll_due()` TTL gate (path:spawn.py:1953-1978) is caller-agnostic and already
  de-dups two independent turn-driven callers (`directive.sh`, `stop-poll-rearm.sh`); a Monitor
  tick becomes a third caller of the same gate with no new coordination code — survey.md Probe 1
  finding 5, Probe 2.
- Documented project-scope Monitor restrictions apply to the skills-directory install path
  specifically; marketplace project-scope behavior is not documented and is treated as
  `unverifiable` — survey.md Probe 1 finding 4.
- The session-bound hard boundary from issue #801 is unchanged: a Monitor dies with its session
  and does not survive session death or reboot — externally blocked, same as #801's finding —
  canonical: docs/issue-801/reports/technical-feasibility/survey.md, "Hard boundary" section
  (proposal), re-read live this session.

## Timebox and acceptance criteria

**Timebox:** this phase-1 investigation was scoped to a single research pass (1 day, within the
1-3 day spike convention) — already executed live 2026-08-11 via live WebFetch of
code.claude.com/docs (plugins.md, plugins-reference.md) plus direct repo inspection (spawn.py,
on-the-record/hooks, `find` for monitors.json). No further timebox is requested for phase 1; a
phase-2 implementation timebox is scoped separately at approval, and must include a live
execution-observation run per the issue's own step-3 requirement.

**Acceptance criteria (from the issue, carried forward):** a feasibility record cites an actual
live-checked answer to each of the four empirical sub-questions (auto-start, ~60s cadence
mechanism, unavailable-host behavior, coexistence with #829); recommends the exact
`monitors.json` shape and the specific `spawn.py`/hook function it reuses (not a new engine);
restates the session-bound boundary explicitly. Provenance: this phase-1 pass is
documentation-and-repo-verified (cited above); a live interactive-session tick observation is
deferred to the issue's own execution-observation step and is not claimed here (survey.md,
"Empirical limitation" section).

## Candidates considered

1. **A Monitor script that loops `sleep 60` and calls the existing `poll_rearm_arm_if_due()`
   (path:on-the-record/hooks/poll-rearm.sh:39-46) as its only body** — **chosen**. Reuses the
   exact atomic TTL gate and background-watchdog spawn the two turn-driven hooks already call;
   adds a third caller, not a new mechanism (survey.md Probe 2). Coexistence with #829 is
   free — `poll_due()`'s lock-protected TTL check already de-dups any caller inside the same 60s
   window (path:spawn.py:1953-1978, 1959-1978).
2. **A Monitor script with its own bespoke interval/dedup logic, independent of `poll_due()`** —
   rejected: would duplicate the existing atomic TTL gate and introduce a second source of truth
   for "is a poll due," which is itself a double-poll risk against the #829 hooks — survey.md
   Probe 2 table, row 1.
3. **Rely on the Monitor alone and drop the #829 turn-driven hooks** — rejected: Monitors are
   silently skipped on hosts where the Monitor tool is unavailable, with no plugin-visible
   fallback signal (survey.md Probe 1 finding 3; STRIDE row 4, "deferred"/degrade design). Dropping
   the turn-driven hooks would leave those hosts with zero polling, worse than today.
4. **Set the Monitor's `when` to `"on-skill-invoke:<skill>"` instead of the default `"always"`**
   — rejected: reintroduces exactly the manual-trigger requirement (a skill must be invoked
   first) that req #7 and this issue explicitly rule out — <source:
   https://code.claude.com/docs/en/plugins-reference.md, "Monitors" section, optional-fields
   table>.

## Recommended `monitors.json` shape and reuse seam

```json
[
  {
    "name": "poll-heartbeat",
    "command": "\"${CLAUDE_PLUGIN_ROOT}/monitors/poll-heartbeat.sh\"",
    "description": "60s poll-due/watchdog heartbeat (issue #829 machinery, reused)",
    "when": "always"
  }
]
```

`monitors/poll-heartbeat.sh` (implementation-phase file, not written in this step) sources
`on-the-record/hooks/poll-rearm.sh` and runs:

```sh
while true; do
  sleep 60
  if CHECKOUT="$(poll_rearm_resolve_checkout "$0")"; then
    poll_rearm_arm_if_due "$CHECKOUT" && echo "poll tick: due, watchdog armed" || echo "poll tick: skipped (within TTL)"
  fi
done
```

This is the exact reuse seam the issue asks for: the Monitor never calls `roster_watchdog` or
`poll_due` directly — it calls the same `poll_rearm_arm_if_due()` the two existing hooks call
(path:on-the-record/hooks/poll-rearm.sh:39-46), so the atomic TTL gate in `poll_due()`
(path:spawn.py:1953-1978) is the single de-dup point across all three callers. The `echo` line is
what turns the tick into a per-cycle report — each stdout line from a Monitor's `command` is
delivered to Claude as a notification during the session (<source:
https://code.claude.com/docs/en/plugins.md>) — satisfying the issue's "report" requirement without
any new reporting code.

## Verdict

**Decision: go**

Building the Monitor-based heartbeat is a two-way, in-repo change with no external blocker: every
mechanism it needs (auto-start, the TTL gate, the watchdog spawn) already exists and is
doc-confirmed. `verdict_provisional: feasible` — the one in-repo-resolvable prerequisite for phase
2 is that it must add `monitors/poll-heartbeat.sh` and `monitors/monitors.json` as new files under
this proposal's write set (not yet listed above because this phase-1 pass recommends but does not
create them), and must demonstrate the live tick empirically per the issue's own step-3
requirement — this is a scope/sequencing note, not a blocking external condition.

## Hard boundary (restated, unchanged from #801)

A Monitor is session-bound: it runs only for the lifetime of the session that started it and does
not survive that session's death or reboot — <source: https://code.claude.com/docs/en/plugins-
reference.md, "Monitors" section, "for the lifetime of the session">. This does not change or
relax issue #801's finding that true install-only self-wake surviving session death remains
externally blocked (no plugin API for OS-level scheduling, no plugin-settings `permissions` key)
— canonical: docs/issue-801/reports/technical-feasibility/proposal.md's "Hard boundary" section
title, and docs/issue-801/reports/technical-feasibility/survey.md Probe 1, both re-read live this
session. A Monitor narrows the *turn-boundary* quiet gap #829 could not close; it does not close
the *session-death* gap #801 already named as externally blocked.

## Measurement design

Phase 2, if approved, must record: raw tick timestamps from a live interactive session with the
plugin installed at user scope and no `/loop` typed, showing ~60s spacing between ticks (the
issue's own Acceptance provenance requirement, `executed-live`); and a run on a host/mode where
the Monitor tool is absent, showing the existing #829 turn-driven hooks still poll and nothing
errors. Both runs' raw output get pasted into the phase-2 record, not summarized only.

## What did not work

None.
