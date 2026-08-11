# North Pole Requirements

The project's north star — 7 requirements stated verbatim by the operator on
2026-08-11 (issue #748). This is the single condensed home for them
(serving requirement #2 and requirement #6 below). Each requirement is
recorded faithfully from the issue body, with a traceability note pointing
to at least one existing mechanism that currently serves it, or an explicit
`GAP` when nothing does yet.

Source: [issue #748](https://github.com/tokenmaxxxer/on-the-record/issues/748).

## 1. Orchestration to completion

> Orchestration to completion — user states requirements →
> on-the-record-installed session working in a TARGET repo orchestrates
> delegation to specialized roles → identifies bottlenecks/obstacles →
> resolves foreseeable risks → achieves the requirement → reports.

**Traceability:** `on-the-record/hooks/stop-gate.sh` checks that an
orchestrator's approval-shaped reply names its issue, states a change, and
states a risk/tradeoff before the turn ends. `gates/spawn_coverage.py`
reports an open issue that was published but never spawned to any role
session, catching orchestration that stalls before delegation starts.
`gates/remediation_spawn.py` turns an open `docs/issue-<n>/decisions/
remediation-*.md` finding into a fixed-template spawn task, closing the
loop from obstacle back to delegated fix.

## 2. Full record-ability

> Full record-ability — every decision, proposal, and deliverable from the
> session and its spawned sub-agents is documented in the repo, so a new
> session or new person continues the work with zero onboarding.

**Traceability:** the warrant directive (`docs/proposals/` /
`docs/issue-<n>/proposals/`) requires a proposal-first record with a
frozen write set before any work starts, and a `## What did not work`
section appended live during the build. `on-the-record/hooks/record-scaffold.sh`
scaffolds `docs/issue-<n>/reports/<role>.md` from `roles/<role>.json`'s
declared `record_fields`. `on-the-record/hooks/record-claim-guard.sh` (via
`gates/record_lint.py`) refuses a record that omits required fields or
leaves an unverifiable claim uncited. This document itself
(`docs/specs/northpole.md`) is a direct instance of the mechanism this
requirement demands.

## 3. Real-wired verification

> Real-wired verification — not mockups / doc-only research / code-analysis
> tests, but actually building and running the real wired program,
> analyzing the gap between the working program and the user's requirement,
> and closing it.

**Traceability:** `gates/reexecution_gate.py` re-runs a claimed command
itself, in a SHA-pinned worktree, rather than trusting the session's own
narration of having run it — the verdict artifact
(`.reexecution/<issue>-<role>.json`) is written by the gate, not the
audited session (per its own docstring, ADR §3/§5).
`on-the-record/hooks/role-test-claim-guard.sh` refuses a test-pass claim
that drops pasted `SKIPPED` lines or states a count mismatching the pasted
output — both push against doc-only or narrated verification.

## 4. Autonomous completion + human-legible reporting

> Autonomous completion + human-legible reporting — role sessions reach the
> goal with no human intervention; and the path is explained so a human
> understands: what problem each task solved, what the result was, what
> changed, what became possible, and what limits remain — how the change
> set advanced toward requirement satisfaction.

**Traceability:** the role-handoff contract's two-phase flow (phase 1
proposal, phase 2 build on Approve — see the interaction-protocol
SessionStart directive) lets a role session run phase 2 to completion
without further human turns once approved.
`on-the-record/hooks/report-framing-check.sh` and `stop-gate.sh` structurally
check that an orchestrator's reply frames what changed and what risk
remains, rather than a bare "done." `gates/risk_report.py` classifies
reversibility/impact so a report can state limits in the same fixed
vocabulary every time.

## 5. Problems are not pushed back to the human

> Problems are not pushed back to the human — a mid-course problem is
> solved by spawning the role-appropriate agent(s) to research AND discuss
> the fix WITH those agents, producing a working deliverable that truly
> satisfies the requirement; the whole process (decisions and discussion
> included) is transparently recorded in the repo.

**Traceability:** `gates/remediation_spawn.py` converts an open remediation
finding directly into a spawn task instead of surfacing it to the human.
`on-the-record/hooks/delegated-judgment-gate.sh` auto-approves/auto-rejects a
candidate decision via a named multi-role panel rule
(`panel-unanimous-support-v1`) when depth and impact axes clear, escalating
only when a precondition is missing — keeping routine mid-course judgment
off the human's desk while still recording it.
`docs/issue-<n>/decisions/` is the transparent record of the discussion
this requirement demands.

## 6. Condensed requirement management

> Condensed requirement management — on-the-record records what the user
> asked for in a condensed, managed form (not scattered), so that even as
> records and sessions multiply, work never drifts from the goal.

**Traceability:** `docs/specs/requirements.md` is an append-only registry of
operator-stated requirements, each tied to an executable check
(`gates.requirement_registry`, wired into `gates/ci.py`) that fails when
the check path disappears from HEAD — a requirement quietly losing its
enforcement is caught mechanically. This document
(`docs/specs/northpole.md`) is the condensed home for the north-star
requirements specifically, closing the gap issue #748 identified (no
northpole.md existed anywhere in the repo before this commit).

## 7. Inviolable constraint — default-on, plugin-only, no explicit invocation

> Inviolable constraint — default-on, plugin-only, no explicit invocation —
> all of the above must hold in ANY target session where on-the-record is
> installed, NOT as a band-aid in the on-the-record repo or one chat
> session. The user only installs the plugin. No forced CI setup or GitHub
> Actions — hooks and plugin elements only. Everything works by default on
> install; the user must NOT have to explicitly invoke a specific skill for
> the requirements to hold.

**Traceability:** `on-the-record/hooks/hooks.json` wires every enforcement
hook (`session-role-bind.sh`, `directive.sh`, `contract-guard.sh`,
`pr-preflight.sh`, `record-claim-guard.sh`, `approval-gate.sh`,
`stop-gate.sh`, etc.) to lifecycle events (`SessionStart`,
`UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`) — these fire on
every session where the plugin is installed, with no skill invocation
required. `on-the-record/.claude-plugin/plugin.json` declares the plugin
itself as the distribution unit (install-only, no per-repo CI setup). All
of these are Claude Code hooks/plugin elements, not GitHub Actions or other
forced CI.

## Gaps

None of the 7 requirements are unmarked; each names at least one existing
mechanism above. Coverage is partial in places (noted inline) but no
requirement is a bare `GAP`.
