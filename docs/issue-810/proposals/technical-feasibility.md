---
status: proposed
files:
  - docs/issue-810/proposals/technical-feasibility.md
  - docs/issue-810/reports/technical-feasibility/survey.md
---

# Proposal — plugin-only default-on orchestrator merge capability (issue #810, phase 1: design)

market_argument_supplied: false

## Intent

Design the plugin-only mechanism that lets the on-the-record orchestration session merge a
`landing_readiness=READY` PR to main by default after install — no manual permission grant, no
host-classifier block — while role sessions stay unable to merge (contract v3 s10 unchanged), per
northpole req #4/#7.

## Constraints found so far

- Plugin-shipped `settings.json` supports only `agent`/`subagentStatusLine` — no `permissions` key
  exists to bundle an allow-rule into (<source: https://code.claude.com/docs/en/plugins.md>; see
  survey.md Probe 1 finding 1). This reconfirms the #801/PR#804 prior finding.
- A plugin-defined `agent` (even one activated as the main thread via `settings.json`'s `agent`
  key) has its `permissionMode` frontmatter field stripped — a plugin cannot ship a
  `bypassPermissions` main-thread agent either (<source: https://code.claude.com/docs/en/sub-agents>;
  survey.md Probe 1 finding 2).
- `PreToolUse` hooks — which a plugin can ship today, exactly as this repo's ten existing deny
  gates already do — can set `hookSpecificOutput.permissionDecision: "allow"` to auto-approve a
  matched tool call, with the same capability for plugin-shipped hooks as project-level ones
  (<source: https://code.claude.com/docs/en/hooks>; survey.md Probe 1 finding 3).
- The precedence between this new allow-channel and the existing exit-code-2 deny channel, when
  both fire on the same `gh pr merge` call, is not documented anywhere in the public docs (survey.md
  Probe 1 finding 4; unverifiable beyond the docs' silence — confirmed via a targeted live fetch,
  2026-08-11).
- `gates/landing_readiness.py`'s `classify` function (path:gates/landing_readiness.py line 31) and
  `session-role-bind.sh`'s `CLAUDE_ROLE` snapshot (path:on-the-record/hooks/session-role-bind.sh
  lines 5-24) already exist as the canonical READY-predicate and orchestrator-identity primitives
  respectively — the new mechanism must call these, not reimplement them.

## Timebox and acceptance criteria

**Timebox:** this phase-1 design pass was scoped to a single research session (within the 1-3 day
spike convention), executed live 2026-08-11 via direct repo inspection (hooks.json, contract-guard.sh,
landing_readiness.py, session-role-bind.sh) plus two live code.claude.com/docs fetches (plugins
schema, sub-agents permissionMode, hooks permissionDecision). No further phase-1 timebox is
requested; phase 2 (implementation + the empirical precedence check) is scoped separately at
approval, and is itself timeboxed to one focused session — the check is a single deliberate
negative-case Bash call, not open-ended exploration.

**Acceptance criteria (from the issue, carried verbatim):** in a fresh plugin-only target, the
orchestration session merges a `landing_readiness=READY` PR to main without any user-added
permission rule, while a spawned role session attempting `gh pr merge` is still refused by the
existing gates. Empty state: no READY PR present → nothing merges, no error. Provenance:
executed-live.

## Candidates considered

1. **Plugin-shipped `settings.json` `permissions.allow` rule for `gh pr merge`** (issue's candidate
   a) — rejected: the plugin `settings.json` schema has no `permissions` key at all today
   (<source: https://code.claude.com/docs/en/plugins.md>). Not a classifier-policy question, a
   schema-absence question — there is nothing to bundle a rule into, and this is unchanged from
   the #801/PR#804 finding that motivated this issue.
2. **Headless `bypassPermissions` merge-executor session, spawned by on-the-record outside the
   interactive classifier** (issue's candidate b, literal form) — rejected: `bypassPermissions` as
   a *plugin-shipped* setting cannot be granted — a plugin agent's `permissionMode` frontmatter is
   explicitly stripped when loaded from a plugin (<source: https://code.claude.com/docs/en/sub-agents>).
   The only way to get a session into `bypassPermissions` is a CLI flag or project-level
   `settings.json`/`settings.local.json` entry the *user* or *outer invocation* controls — which is
   exactly the "user does something once" fallback (candidate 4 below), not a plugin-only mechanism.
   Spawning a separate headless process buys nothing a plugin can self-grant that an in-session hook
   (candidate 3) cannot also self-grant, and adds a second process whose own permission mode still
   has to come from somewhere non-plugin.
3. **Documented one-time user grant at install (plain fallback)** (issue's candidate c) — rejected
   as the *primary* mechanism, though kept as the honest fallback if candidate 4 is later found
   unsafe: the user would add a `permissions.allow` entry for `gh pr merge` (scoped, e.g. to a
   wrapper script path) to their own `.claude/settings.json` once, following a doc this plugin
   ships. This is unavoidable in the strict sense that it is the only mechanism guaranteed by the
   platform's own documented `permissions.allow` behavior (<source:
   https://code.claude.com/docs/en/permissions.md#permission-modes>, cited in the #801 survey) — but
   it directly fails req #7's "no forced human steps" bar, so it is not the recommended path while
   candidate 4 remains viable.
4. **Plugin-shipped `PreToolUse` hook emitting `permissionDecision: "allow"`, scoped to the
   orchestrator identity and a positive `landing_readiness=READY` check** — **chosen**. Reuses this
   repo's own existing hook-shipping pattern (ten deny gates already wired the same way in
   on-the-record/hooks/hooks.json), the existing `CLAUDE_ROLE` snapshot for orchestrator identity,
   and the existing `gates/landing_readiness.py` READY predicate. Requires zero user action beyond
   installing the plugin — the hook is wired in `hooks.json` exactly like every other gate. The one
   open risk (undocumented precedence against the existing exit-code-2 deny gates, survey.md Probe
   1 finding 4 / Probe 4 STRIDE row 3) is resolvable within this repo's own phase-2 work via a
   single empirical test, not an external dependency — see Verdict below.

## Verdict

**Decision: conditional**

**Conditions (blocking, resolvable within this repo's own phase-2 work, not external):**
- Phase 2 must empirically demonstrate, before shipping default-on, that the new allow-hook's
  `permissionDecision: "allow"` does **not** override an existing gate's exit-code-2 deny for the
  same `gh pr merge` call. Concretely: construct a call one of `contract-guard.sh` /
  `impact-guard.sh` / `plan-order-guard.sh` already denies (e.g. a batch of two `gh pr merge` calls,
  which `impact-guard.sh` denies today), enable the new allow-hook alongside it, and confirm the
  call still does not execute. Both the raw pass and fail runs' output get pasted into the phase-2
  record per this repo's provenance convention, not summarized only.
- This is not an external blocker in the `verdict: conditional` sense used for req #7-style
  platform-schema gaps (compare docs/issue-801/proposals/technical-feasibility.md, whose blocking
  condition truly requires an upstream Anthropic schema change) — it is an in-repo empirical
  verification step with no dependency outside this repository. It is listed under `conditions:`
  rather than the `verdict_provisional` body-level convention because it is genuinely blocking (the
  mechanism must not ship default-on until verified, not merely "should be demonstrated
  eventually") — the distinction from a two-way `go`-with-prerequisite is that a wrong precedence
  answer here is an Elevation-of-Privilege defect, not a quality-of-life gap.

`verdict_provisional: feasible-with-conditions` — the mechanism (candidate 4) is architecturally
sound and buildable now; it is blocked only on the one empirical check named above, which the
issue's own step 3 (execution-observation) already asks for.

## Safety argument

- **Role sessions stay blocked by construction, not by omission.** The new hook no-ops
  immediately (no JSON output, exit 0) whenever `CLAUDE_ROLE` is set — it reads the same
  `SessionStart`-snapshotted identity every other role-scoped hook in this repo already trusts
  (path:on-the-record/hooks/session-role-bind.sh lines 5-24), so a role session gets exactly the
  same (non-)treatment from this hook as it does today: still subject to the interactive
  classifier or a manual grant, never an automatic allow. Contract v3 s10 is unchanged because
  nothing about role sessions' merge path is touched.
- **The allow grant is scoped three ways, not just one.** It fires only when (a) `CLAUDE_ROLE` is
  unset (orchestrator), (b) the command is `gh pr merge` against a resolvable, explicit PR number
  (reusing contract-guard.sh's already-hardened target-repo resolution, path:on-the-record/hooks/
  contract-guard.sh lines 66-79 — no bare `gh pr merge` with an implicit "current PR" gets
  auto-allowed), and (c) `gates/landing_readiness.py`'s `classify` (path:gates/landing_readiness.py
  line 31) returns READY for that PR. Any other `gh pr merge` shape — including one that is merely
  unrecognized, not affirmatively READY — falls through to `sys.exit(0)` with no JSON, i.e. no
  change from today's classifier/manual-grant behavior. The hook only ever adds permission; it
  never removes the fallback.
- **It cannot make a bad merge easier, only a good one faster.** Every existing deny gate
  (contract-guard.sh's trailer check, impact-guard.sh's batch-merge check, plan-order-guard.sh's
  ordering check) keeps running unchanged on the exit-code-2 channel; the new hook adds a second,
  independent JSON-channel signal on top, and per the survey's STRIDE analysis the phase-2
  empirical check exists precisely to confirm those two channels compose the safe way (deny still
  wins) before this ships default-on.

## Measurement design

Phase 2, if approved, must record: the raw output of the deliberately-denied batch-merge test
described above (both with and without the new hook enabled, to show the hook did not change the
outcome), and one live run of the orchestrator merging an actual READY PR with the new hook
enabled and no manual permission rule present, per the issue's own Acceptance check. A role session
attempting `gh pr merge` in the same fixture, showing it is still refused, closes the acceptance
criterion's second half.

## What did not work

None.
