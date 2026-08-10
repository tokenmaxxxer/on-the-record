---
loop_state: phase-1-survey
---

# Current-state survey: issue #623 post-landing verification program

Subject: #623. Like #628, this issue names no single observed
role/session — it assigns the execution-observation session directly
(its own 실행 계획: `step 1 execution-observation ‖ conformance-review`)
across the day's stacked surfaces. Observed artifacts read this
session: `gh issue view 623 --json body,comments` (full body + the
operator's install-path-parity addition), and #628's merged phase-1 PR
(`gh pr view 632`, MERGED) — its diff (`gh pr diff 632`) read in full:
`docs/issue-628/proposals/2026-08-10-execution-observation-silent-failure-hunt.md`,
`docs/issue-628/reports/execution-observation/survey.md`, and
`docs/reports/2026-08-10-hunt-execution-observation-silent-failure-hunt.md`.

## #628 coordination (input, not duplication)

`gh issue view 628 --json state` shows OPEN — only #628's phase-1
(survey + proposal, PR #632, merged) has landed; a `find` over the
repo tree confirms only the two phase-1 files above exist under
`docs/issue-628`, so #628's phase-2 fixture-drive hunt record has not
been written yet and has no findings to fold in. This survey therefore
treats #628's proposal as the *plan* for a parallel, narrower hunt
(silent-failure signature classes a-h, no metrics), and #623 as the
broader program (side-effect interaction table across all stacked
surfaces AND per-metric measured-pass/fail/deferred table) — the two
overlap on which PRs get driven but not on what is asked of the drive.
#623 Scope A explicitly also covers cross-surface *interaction* (hook
stacking, latency, false_reject) that #628 does not ask for; #628's
signature-class hunt (dead code, ROOT-vs-target, fabricated citations)
is not #623's job to re-derive. Once #628 produces its own phase-2
record, phase 2 of #623 must cite it by commit SHA for any surface both
issues name, rather than re-driving that surface from scratch.

## Install-path parity (operator addition) — what it changes

The operator comment requires Scope A's drive to run against the
**marketplace-installed** plugin surface, not the repo checkout.
Confirmed from `on-the-record/hooks/hooks.json`: every hook command is
`${CLAUDE_PLUGIN_ROOT}/hooks/<script>.sh` — so hook *invocation* always
resolves via this env var, but a hook's *internal* path math (e.g.
`$CLAUDE_PLUGIN_ROOT/hooks/../../gates`) differs between the dev
checkout (where `gates/` sits at repo root, sibling to `hooks/`) and the
installed cache layout. #556 (`gh issue view 556`, read this session)
documents the concrete install cache path pattern
`~/.claude/plugins/cache/tokenmaxxxer/on-the-record/<hash>/` — a
directory containing only what the plugin packages (no `gates/`
checkout at all, per #556's body: "packaging: in the deployed plugin
cache, hook scripts ... resolve `$CLAUDE_PLUGIN_ROOT/hooks/../../gates`,
which does not exist in the cache layout"). #556 closed with a fix
merged; whether that fix actually holds under a *newly* constructed
cache-layout fixture (not #556's own test's fixture) is unverified —
exactly the operator's point that install-only environment variables
remain unverified beyond #556's own PR.

## Scope named

- Scope A (side effects): the eleven stacked surfaces named in the
  issue body — #566, #476, #573/#597, #586, #587, core#189, #577,
  #576, #608, #600, #619 — driven on (a) a fixture target repo under
  install-path conditions (simulated `CLAUDE_PLUGIN_ROOT` cache layout,
  no repo-root `gates/`) and (b) this repo's own flows, per the
  operator's install-path-parity requirement.
- Scope B (metrics): every registered metric named in the issue body
  (#476 wiring_coverage_rate, #566 unrecorded_requirement_rate /
  false_flag_rate, #573 decision_fatigue_reduction_rate /
  auto_decision_reversal_rate, #587 five-event e2e, #609/#600/#608/#619
  acceptance re-runs) reported measured-pass/measured-fail/
  deferred-with-reason.

## Write surfaces this session touches (thin/unknown before execution)

- Whether each hook script's internal path resolution (gates/ import,
  any relative path math beyond `${CLAUDE_PLUGIN_ROOT}`) survives a
  constructed cache-layout fixture with no `gates/` at repo-root —
  unknown until phase 2 builds that fixture and drives each hook.
- Hook-stacking side effects (multiple PreToolUse hooks now chained per
  `hooks.json`: contract-guard, pr-preflight, claim-scan-preflight,
  spec-index-preflight, impact-guard, delegated-judgment-gate all fire
  on one Bash call) — latency and false-reject behavior under that full
  chain is unmeasured until phase 2 drives it.
- Per-metric corpus size (session counts feeding wiring_coverage_rate,
  false_flag_rate, etc.) — unknown until phase 2 queries the actual
  session/PR corpus; several are expected to defer per the issue's own
  hedge ("#573 ... likely deferred, state so").

## Scout skip record

Scouting is skipped: issue #623 is fully prescriptive — it names the
eleven surfaces, the two scopes, every metric to measure, and the
reporting format (measured-pass/measured-fail/deferred-with-reason; a
per-surface side-effect table) with no open design decision about what
kind of program to build. Skip condition "spec literally leaves no
design decision open" applies.
