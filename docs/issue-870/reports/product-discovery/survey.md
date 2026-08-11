---
subject: issue-870
kind: current-state-survey
---

# Current-state survey — generalize fake-success detection (issue #870)

## Background / context

canonical: docs/issue-793/proposals/verify-before-claim.md (read this session)

`on-the-record` already ships a `PreToolUse` hook
(`gates/record_lint.py`, function `canonical_source_claim_check`,
landed for issue #793) on `Write|Edit|MultiEdit` against
`docs/issue-*/reports/**`: it refuses a STATE or DEFECT claim ("X
halted", "N of M checks pass") unless a `canonical: <source>` tag sits
within 3 lines above it. That is citation-presence enforcement for
claims about current state, scoped to records under `docs/`.

canonical: docs/issue-776/proposals/2026-08-11-northpole-e2e-harness-design.md (read this session)

Separately, the #776 harness (`harness/`) actually builds and executes
a fixture target's deliverable end to end and scores 7 requirements
against real execution — but it lives entirely inside a purpose-built
evaluation harness for on-the-record's own requirements, driven
deliberately by an operator, not inside a target repo's normal delivery
flow, and not attached to any hook.

canonical: docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md (read this session)

#831 shipped a one-time, attended setup step (`ensure_target_remote`)
for a different per-target unknown (the GitHub remote): offer once,
record a `ledger_write` event when the operator accepts, then rely on
that recorded event afterward instead of re-asking. That is the closest
existing precedent for "ask the operator once for a target-specific
fact the plugin cannot infer on its own, then treat the answer as
durable."

canonical: docs/issue-787/reports/execution-observation/rerun.md, docs/issue-776/reports/execution-observation/run3.md (read this session, headings scanned)

This session's own git history names four re-run records (commit
subjects for PRs #845, #855, #867; #787's rerun.md independently) in
which repeated harness attempts against the same nominal scenario
produced different verdicts across attempts — the concrete, in-repo
instance of what the issue calls a fake success: a claim of done/PASS
that traced back to stale state, a non-faithful stand-in for the real
target, or a skimmed signal, rather than to an actual, current,
executed check against the real target. The common thread across all
of them, per the issue text, is not "no citation was given" (already
mechanically gated) but "the citation, or the claim it backs, was not
itself produced by an executed check against live current state" — a
different, so far ungated, failure shape.

## The problem, stated without a solution attached (JTBD tuple)

- **Job performer**: any Claude Code session (role or orchestrator)
  working in a target repo that has `on-the-record` installed as a
  plugin, at the moment it is about to assert that a requirement or
  task is met, done, or PASS.
- **Job**: decide, and record, whether a piece of work is actually
  finished — before that decision propagates outward (a record gets
  written, a PR gets opened, an issue-close is requested, a caller
  trusts the claim and builds on it).
- **Circumstance**: the same pressures that produced every fake success
  already observed in this repo apply — finishing a long task, reusing
  a plausible-looking prior transcript or state, working against a
  stand-in instead of the real target, skimming a signal rather than
  reading it in full — often with the session itself headless and
  single-shot, so no human shares the process to catch a wrong claim
  before it lands.
- **Desired outcome**: a claim of met/done/PASS not backed by an
  actual, current, executed check against the real target is caught —
  refused, flagged, or downgraded to an explicit unmeasured state — by
  the installed plugin itself, without the session's own diligence
  being the only thing between a false claim and its consequences; a
  claim that IS genuinely backed passes without added friction.

The issue text already names three candidate mechanisms (a/b/c) under
"requirement / judgment to make (delegate)" — read here as the issue's
own decomposition of the solution space to evaluate, not as an
instruction to adopt all three verbatim; the JTBD above is the problem
those candidates are answers to, restated with no mechanism preferred.

## Where this sits in the opportunity-solution tree

- **Outcome**: fake successes on target-repo work (a claimed met/done
  that is not real) drop toward zero across any installed session, not
  only within this repo's own harness attempts.
- **Opportunity**: the gap between "a claim carries a citation" (#793,
  already gated — citation presence) and "the citation is itself an
  executed-live check against current state, for an outcome/done claim
  specifically" (not gated) — the same shape as #793's own opportunity
  statement, one layer up: from state/defect claims to outcome/done
  claims, and from citation presence to citation kind.
- **Candidate solutions** (the issue's own a/b/c, to be scored, not
  assumed): (a) extend the write-time citation gate to outcome claims
  and require the cited source be an executed-live run, not a
  read/summary; (b) a per-target acceptance command, set once
  (matching #831's one-time-setup shape), actually executed before
  "done" is accepted, degrading to `UNMEASURED-with-reason` when
  absent; (c) an independent adversarial role that re-checks a
  done-claim before accept.
- **Discriminating assumption test**: which of (a)/(b)/(c), alone or in
  combination, can be built as default-on plugin hooks with no forced
  CI (req #7) and no false PASS on an unmeasurable target — settled by
  the proposal's feasibility section (hook event capabilities, per the
  scout brief) and RICE table below.

## Scout-brief hand-off

`docs/issue-870/reports/product-discovery/scout-brief.md` — official
Claude Code hooks event catalog, which event types can block a tool
call vs. a turn/session/task end, and how plugin `hooks.json` composes
with project/user hooks. Feeds directly into which of (a)/(b)/(c) is
mechanically feasible plugin-only, in the proposal.
