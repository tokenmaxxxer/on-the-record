# issue-835 — research survey: plugin Monitor for default-on ~60s poll/health/report

market_argument_supplied: false

This is Step 1 (research) for issue #835 only. It reads the specification (a plugin-shipped
`monitors/monitors.json` that auto-starts on user-scope install and ticks the existing #829
poll/health/report loop ~every 60s, no `/loop`, no manual setup) without the market/product
argument that motivated it. No verdict is stated here; the proposal
(docs/issue-835/proposals/technical-feasibility.md) converges the four probes below into a
decision.

## Current-state survey

`find . -iname "monitors.json" -not -path "*/node_modules/*"` returns zero results anywhere in
this repository — canonical: shell check, this repo, executed live 2026-08-11, zero hits. No
plugin in this repo has ever declared a Monitor; `on-the-record/.claude-plugin/plugin.json`
carries only `name`/`description`/`author` and no `experimental.monitors` field —
<source: on-the-record/.claude-plugin/plugin.json:1-8>. So today's architecture has zero capacity
to absorb this spec: nothing to extend, and the poll machinery it would call has never been
called from anywhere but a hook process.

That poll machinery already exists and is exactly what issue #782/#829 built:
- `poll_due()` (path:spawn.py:1953-1978) is an atomic check-and-stamp against
  `runs/poll_state.json` with a 60s TTL (`POLL_INTERVAL_SEC = 60`, path:spawn.py:1952) — whichever
  caller asks first inside a 60s window gets `True` (and re-stamps); every other caller inside the
  same window gets `False`. This is a **caller-agnostic dedup gate** — it does not know or care
  whether the caller is a hook, a human, or (per this issue) a Monitor tick.
- `poll_rearm_arm_if_due()` (path:on-the-record/hooks/poll-rearm.sh:39-46) calls
  `spawn.py poll-due`; if and only if that returns due, it backgrounds
  `spawn.py watchdog --auto-respawn` via `nohup ... &`, logging to
  `~/.claude/tokenmaxxxer/poll-watchdog.log`.
- Two hook events already call `poll_rearm_arm_if_due()` today: `UserPromptSubmit`
  (path:on-the-record/hooks/directive.sh:37) and `Stop`
  (path:on-the-record/hooks/stop-poll-rearm.sh:31-34) — both turn-boundary events, per
  path:on-the-record/hooks/hooks.json:11-19,70-81. Neither fires while a session is alive but
  between turns (waiting on a long tool call, or simply idle with no new user message) — this is
  the exact quiet-gap issue #835 is asked to close.
- `roster_watchdog()` (path:spawn.py:2232) is the one-shot scan `spawn.py watchdog` runs each
  tick — observe-only over live role sessions, with `--auto-respawn` capped before requiring a
  human intervention (per `_auto_respawn_check()`, referenced path:spawn.py:2966).

Deploy/runtime config surface: no new env var is required — `poll_rearm_arm_if_due()` already
honors `ORCHESTRATE_OFF` as a kill switch (checked by both existing callers before sourcing
poll-rearm.sh, per path:on-the-record/hooks/stop-poll-rearm.sh:28) and `TOKENMAXXXER_CHECKOUT` as
an optional dev override (path:on-the-record/hooks/poll-rearm.sh:26-27); a Monitor-based caller
would need no new variable, only to source the same script.

## Probe 1 — technical (spike-report + reversibility)

**Question (spike_goal):** does a plugin-shipped Monitor actually auto-start on a user-scope
install; does its command's own `sleep`-based tick fire on a real ~60s cadence; what happens on a
host where the Monitor tool is unavailable; and how should it call the existing poll/watchdog
machinery so it does not double-poll against the #829 turn-driven hooks?

**Findings**, gathered live via WebFetch of the current product documentation on 2026-08-11 (no
cached/remembered claim used):

1. Auto-start on install is documented product behavior, not something the plugin's own code
   must arrange: "Background monitors let your plugin watch logs, files, or external status in
   the background... Claude Code starts each monitor automatically when the plugin is active, so
   you don't need to instruct Claude to start the watch" — <source:
   https://code.claude.com/docs/en/plugins.md, fetched live 2026-08-11>. The `when` field's
   default is `"always"`: "starts it at session start and on plugin reload" —
   <source: https://code.claude.com/docs/en/plugins-reference.md, "Monitors" section, fetched
   live 2026-08-11>. This directly answers the issue's sub-question (1): yes, a shipped Monitor
   auto-starts, with no `/loop` and no skill invocation needed, as long as `when` is left at its
   default (or explicitly set to `"always"`).
2. Cadence is **not** a platform primitive — a monitor is one persistent shell `command`; nothing
   in the schema enforces an interval. Anthropic's own reference examples are open-ended loops
   (`tail -F ./logs/error.log`, a `poll-deploy.sh` script) with no built-in tick period —
   <source: https://code.claude.com/docs/en/plugins-reference.md, "Monitors" section, example
   `monitors/monitors.json`, fetched live 2026-08-11>. So sub-question (2) — does a sleep-based
   tick fire on ~60s cadence — resolves to: **yes, but only because the command itself sleeps for
   60s per iteration; the platform guarantees the process stays alive for the session's lifetime
   ("Each monitor runs a shell command for the lifetime of the session"), not that any particular
   cadence is honored** — <source: same>. A monitor script that runs `while true; do <tick>;
   sleep 60; done` gets a real ~60s cadence as a direct consequence of `sleep 60` executing in a
   process the platform keeps alive, not from any Monitor-specific timer feature.
3. Unavailable-host behavior (sub-question 3): "Plugin monitors use the same mechanism as the
   Monitor tool and share its availability constraints. They run only in interactive CLI
   sessions, run unsandboxed at the same trust level as hooks, and are skipped on hosts where the
   Monitor tool is unavailable" — <source: https://code.claude.com/docs/en/plugins-reference.md,
   "Monitors" section, fetched live 2026-08-11>. "Skipped" is silent — no plugin-visible error or
   fallback signal is documented. This is the same host-must-be-alive constraint established for
   `ScheduleWakeup` and cron/launchd/systemd equivalents — canonical:
   docs/issue-801/reports/technical-feasibility/survey.md, Probe 1, re-read live this session.
   Monitors add a new trigger path, not a new escape from that boundary.
4. Scope restriction: for project-scope skills-directory plugins, "Background monitors do not
   load," while "Personal-scope plugins have none of these restrictions" —
   <source: https://code.claude.com/docs/en/plugins-reference.md, "Skills-directory plugins"
   section, fetched live 2026-08-11>. This documented restriction is stated for the
   skills-directory install path specifically; this repo's `on-the-record` plugin installs via a
   marketplace, not a skills-directory. The doc does not state a marketplace-project-scope
   equivalent explicitly — flagged as `unverifiable: no doc section covers marketplace
   project-scope Monitor loading directly` — so the design below targets user-scope only, matching
   the issue's own framing, and does not assert project-scope behavior either way.
5. Coexistence with #829 (sub-question 4): `poll_due()`'s TTL gate (path:spawn.py:1953-1978) is
   caller-agnostic — a third caller (a Monitor tick) hitting `poll_rearm_arm_if_due()` inside the
   same 60s window as a recent `UserPromptSubmit`/`Stop` firing gets `due=False` and is a no-op,
   exactly the same de-dup the two existing hook callers already rely on (see Current-state
   survey above). No new coordination code is needed; the Monitor becomes a third caller of the
   same gate, on the exact reuse seam the issue asks for.

**Reversibility tag:** two-way — adding `monitors/monitors.json` (plus a thin wrapper script that
loops `sleep 60` and calls `poll_rearm_arm_if_due`) is deleted or the `monitors/` directory removed
without residual state beyond `runs/poll_state.json`, which the two existing turn-driven hooks
already own and continue to manage unmodified if the Monitor is removed —
<source: path:on-the-record/hooks/poll-rearm.sh:39-46>.

**Result:** `pass: <findings 1-3, 5 above>` — auto-start, ~60s cadence (script-driven, not
platform-guaranteed), and unavailable-host degrade-to-nothing are all documented and directly
verifiable against the current product docs; the reuse seam (a third caller of
`poll_rearm_arm_if_due`) requires no new coordination code. Finding 4 (project-scope Monitor
loading via a marketplace install specifically) is marked `unverifiable: <reason above>` and the
design is scoped to user-scope accordingly, matching the issue's own ask.

## Probe 2 — prior_art (build-vs-buy)

No third-party library or vendor choice applies — the question is again a platform-capability
boundary (what a Monitor can and cannot do), not a library selection — canonical:
docs/issue-801/reports/technical-feasibility/survey.md, Probe 2, re-read live this session, same
finding shape for the adjacent `ScheduleWakeup`/Routines question. Framed the same way, against
the two real options this repo already has:

| Option | Health evidence | Verdict |
|---|---|---|
| **Buy**: a new polling engine inside the Monitor script (bespoke interval/dedup logic) | Would duplicate `poll_due()`'s existing atomic TTL gate — <source: path:spawn.py:1953-1978> | Rejected — the issue explicitly asks to reuse, not duplicate, and a second dedup mechanism would itself be a double-poll risk |
| **Build**: reuse `poll_rearm_arm_if_due()` (path:on-the-record/hooks/poll-rearm.sh:39-46) as the Monitor tick's only body | Already exists, already used by two independent callers (`directive.sh`, `stop-poll-rearm.sh`), already covers the coexistence requirement by construction (TTL gate) | Only real option; the Monitor script needs nothing beyond a `sleep 60` loop calling this existing function |

**Result:** `pass: <evidence above>` — the reuse seam is the only viable design; no external
library evaluation is applicable.

## Probe 3 — legal_regulatory (license-scan + DPIA-before-processing)

No new third-party dependency is introduced — the Monitor script would be pure shell calling
already-vendored, already-licensed repo code (`spawn.py`, `poll-rearm.sh`). No new personal-data
category is processed — the poll/watchdog loop reads local repo/session state (branch names,
event logs, `runs/poll_state.json`) already local to the operator's own machine — this is the
same no-new-data-category finding — canonical:
docs/issue-801/reports/technical-feasibility/survey.md, Probe 3, re-read live this session —
reached for the adjacent watchdog mechanism. DPIA-before-processing does not trigger.

**Result:** `pass: no new dependency, no new data category — no license or regulatory surface
introduced` — <source: on-the-record/.claude-plugin/plugin.json (no added deps), spawn.py
(existing, already-licensed repo code)>.

## Probe 4 — threat_model (STRIDE, one row per element/category/trust boundary)

| Element | Trust boundary | STRIDE category | Threat | Disposition |
|---|---|---|---|---|
| `monitors/monitors.json` Monitor process (unsandboxed, hook trust level) | plugin install → user's running session | Elevation of Privilege | A Monitor `command` runs unsandboxed at hook trust level — <source: https://code.claude.com/docs/en/plugins-reference.md, "Monitors" section> — so a malicious/compromised marketplace plugin could ship a Monitor that does more than poll | **accepted** — out of scope for this issue: unsandboxed-at-hook-trust-level is the platform's own stated design for all monitors, identical to the trust level this repo's existing hooks (`directive.sh` etc.) already run at; the design below adds no privilege beyond what `poll-rearm.sh` already exercises |
| `runs/poll_state.json` TTL gate | three concurrent callers (UserPromptSubmit, Stop, Monitor tick) → one file | Tampering / Race | Two callers racing inside the same tick could both read `last_poll` before either writes, double-spawning a watchdog | **mitigated** — `poll_due()` already takes an `fcntl.flock` exclusive lock around the read-modify-write (path:spawn.py:1959-1978); a Monitor caller inherits this without new code |
| `spawn.py watchdog --auto-respawn` background spawn from a Monitor tick | quiet-gap tick → live role sessions | Denial of Service (runaway respawn) | A Monitor ticking every 60s indefinitely could, over a long session, spawn many more watchdog invocations than the two turn-driven hooks alone would | **mitigated** — `--auto-respawn` is already capped before requiring a human, independent of caller identity — canonical: docs/issue-801/reports/technical-feasibility/survey.md, Probe 4 table row 2, re-read live this session; this repo's current watchdog entry point is path:spawn.py:2232 |
| Silent skip on hosts without the Monitor tool | plugin capability surface → operator expectation | Repudiation / reliability | An operator on a host where Monitors are unavailable (e.g. web/Slack) sees no error and may believe the ~60s heartbeat is running when it is not — canonical: https://code.claude.com/docs/en/plugins-reference.md, "Monitors" section, "skipped on hosts where the Monitor tool is unavailable" | **deferred** — the proposal's design keeps the #829 turn-driven hooks unconditionally active rather than superseded; that design choice, not any signal from the Monitor itself, is what closes the "operator is misled" risk |
| Project-scope install of the same plugin | project-scope trust gate → Monitor loading | Elevation of Privilege / undefined behavior | Documented behavior for project-scope *skills-directory* plugins is "Background monitors do not load" — <source: https://code.claude.com/docs/en/plugins-reference.md, "Skills-directory plugins" section>; marketplace project-scope behavior is not documented explicitly (Probe 1 finding 4) | **deferred** — the design targets user-scope only per the issue's own framing; project-scope behavior is unverified and out of this issue's scope to resolve |

## Grading summary

| Probe | Result |
|---|---|
| technical | pass — auto-start, cadence mechanism, unavailable-host skip, and the coexistence reuse seam are all doc-verified; one sub-finding (project-scope marketplace loading) is unverifiable and scoped out accordingly |
| prior_art | pass — reusing `poll_rearm_arm_if_due()` is the only viable design; no new polling engine |
| legal_regulatory | pass — no new dependency/data-category surface |
| threat_model | all five rows disposed (2 mitigated, 1 accepted, 2 deferred to explicit design/scope choices recorded in the proposal) |

## Empirical limitation, stated plainly

This survey's "empirical" basis is a live fetch of the current product documentation
(code.claude.com/docs, both pages fetched 2026-08-11) plus live repo inspection — it is **not** a
live observation of a running Monitor ticking inside an actual fresh user-scope install, because
this session is a headless, non-interactive role session with no ability to launch a second
interactive Claude Code session to install the plugin and watch a Monitor tick in real time. The
issue's execution-observation phase is the one that must paste raw tick timestamps from a live
session, per the issue's own Acceptance criteria — canonical: gh issue view 835, "Execution plan"
and "Acceptance" sections, read live this session. This survey establishes what the documented
contract guarantees and what it does not, so the implementation and execution-observation phases
know what to build and what still needs a live run to confirm.
