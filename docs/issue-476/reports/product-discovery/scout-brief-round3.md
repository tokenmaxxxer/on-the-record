# Scout brief — issue #476 round 3

Mode: 2 parallel WebSearch calls (stage 1 sweep, breadth only), 1
judge point, no deepening round needed (both hits converged on the same
must-bes; a third search would not change a build decision, so stage 2
stopped at judge point 1). Wall clock well under the 3-minute budget.

## Must-bes (Kano), from the field of metric-gaming / audit-theater
prevention

- **Pair every efficiency/output metric with a cost or quality metric**
  so gaming shows up as a cost somewhere, never as a free win. The
  landed 77-row set (canonical: docs/specs/enforcement-boundary.md,
  read this session) has no guardrail metric paired against citation-
  shape compliance — a role can satisfy every citation-shape rule while
  never being checked on whether the underlying work was necessary.
- **Maintain an external oracle the audited party cannot influence** —
  a frozen holdout, a second actor, or an out-of-band re-run. This is
  exactly this round's survey finding: every landed guard re-checks the
  SAME artifact the role produced; none introduces a second, blind
  actor.
- **Separation of duties**: the person/process that produces a claim
  must not be the same one that approves it. SOC2 fieldwork treats a
  self-approval as a standard finding. The current role-handoff contract
  already separates phase-1/phase-2 by human approval, but nothing
  separates "wrote the record" from "checked the record's underlying
  necessity or honesty" — record_lint.py's checks run inside the same
  session/commit that authored the claim.
- **Native, structured evidence over free-text attestation** — an
  "approved" reply in prose is not evidence; a structured, timestamped,
  independently-queryable record is. The repo's `derived:`/`canonical:`
  convention already does this for citations; it does not yet do this
  for the *spawn decision* itself (no structured record of "why was
  this role spawned, what question was open").
- **Random sampling, not just triggered checks** — an auditor samples a
  set of changes and traces each one, rather than relying solely on the
  audited party surfacing which changes to check. Every landed
  mechanism here is trigger-based (fires only on a claim-shaped
  string); none samples the population of ALL records, including ones
  that avoid claim-shaped language.

## Performance axes (2-3 dimensions strong systems compete on)

1. Whether the check can be satisfied unilaterally by the actor being
   checked (weak) vs. requires a second actor or externally-verified
   re-run (strong).
2. Whether the check fires deterministically on a triggering pattern
   (narrow, gameable-by-avoidance) vs. samples the whole population
   (broad, resistant to selective silence).
3. Whether refusing/reporting null is scored equivalently to producing
   a deliverable (aligned incentive) vs. left unscored/implicitly
   penalized (misaligned incentive, drives fabrication).

## Adopt / skip

- **Adopt**: metric pairing (a "spawn necessity" or "refusal parity"
  guardrail alongside existing citation-shape metrics) and a blind
  second-actor sampling audit, since both directly answer this round's
  survey gap and match the issue's own named candidate directions.
- **Skip, this round**: full CI-based structured-evidence platforms
  (the field's SOC2-tooling examples assume a server-side pipeline);
  this repo's zero-install/hook-only constraint (`docs/specs/
  enforcement-boundary.md`'s own verdict vocabulary) rules out anything
  requiring a persistent external service, so the proposal must stay
  within `spawn.py`/hook/commit-time surfaces, same as every landed
  mechanism.

## Gap line

The field's must-bes the current state already meets: structured,
timestamped, traceable evidence for citations (the 77-row set); a
re-execution oracle for citation claims specifically (H1/H1b, live-fire,
acceptance-real-run). Missing: a second, blind actor (no landed
mechanism introduces one); a guardrail metric on the spawn decision
itself; equal-cost treatment of refusal vs. deliverable; population-wide
(not trigger-only) sampling.

## Segment fit

One line: this is an internal reward-hacking-prevention system for an
AI-orchestration plugin, not a consumer product — the closest fit field
is compliance/audit tooling and ML eval-gaming research, not a
commercial SaaS category, so "exemplar" here means established audit
practice, not a competitor product.

## Stage / mode used

Stage 1 sweep: 2 parallel WebSearch calls in one turn (Goodhart's-law/
metric-gaming angle; SOC2 audit-theater/separation-of-duties angle).
Judge point 1: both converged on second-actor/sampling/structured-
evidence themes — no mismatch to correct, no deepening round run.

## Sources

- [Every Metric Gets Gamed. Here's When the Gamers Lose.](https://tommyclawd.substack.com/p/every-metric-gets-gamed-heres-when)
- [Gaming the Metric, Not the Harm: Certifying Safety Audits against Strategic Platform Manipulation](https://arxiv.org/html/2605.06324)
- [Goodharting Prevention in Agent Systems: When Agents Game Your Metrics](https://understandingdata.com/posts/goodharting-prevention-agent-systems/)
- [SOC 2 Audit Checklist: What Auditors Test in Fieldwork](https://soc2auditors.org/insights/soc-2-audit-checklist/)
- [The human-in-the-loop layer AI cannot replace for SOC 2 evidence](https://tallyfy.com/human-in-the-loop-soc2-evidence-tallyfy/)
