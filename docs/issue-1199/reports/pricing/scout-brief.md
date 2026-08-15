---
kind: record
subject: issue-1199
loop_state: n/a
---

# issue-1199 (pricing): scout brief

Stages used: 2 (1 sweep + 1 deepening/verify round), batched-sequential
mode — WebSearch calls were issued as parallel tool calls within one
message for the sweep stage; the deepening stage (marketplace-page
WebFetch x2 + `gh api` verification x2 + corroborating-source search x1)
ran as a second batch. Elapsed well under the 3-stage/3-minute soft
budget once the sweep surfaced a clear, saturated signal (both search
queries converged on the same two repos independently).

## Category must-bes (from the surveyed exemplars)

- Separate packaging / metric / price-point as three distinct decisions,
  not one blended "set a price" step.
- A checkable test for whether a metering unit is a valid value metric
  (scales with delivered value), not just an assertion that it does.
- A named revisit cadence for a standing pricing decision, not an
  undefined "still valid" judgment call.

## Performance axes the exemplars compete on

- Elicitation completeness (how much context is gathered before any
  recommendation).
- Concreteness of the diagnostic test (binary/checkable vs. vague
  "align with value").
- Coverage breadth (packaging + page-audit + raise-price signals vs.
  research-method rigor alone).

## Adopt / skip

- Adopt: the value-metric checkable test, and GBB anchor/decoy tier
  structuring — this rulebook's chain has zero rules on tier assembly
  despite the role's own PRODUCES line naming "tier structure."
  Sources: coreyhaines31/marketingskills `skills/pricing/SKILL.md`
  (https://github.com/coreyhaines31/marketingskills);
  corroborated by OpenView Partners
  (https://openviewpartners.com/blog/how-to-price-your-product/).
- Adopt: an explicit revisit-cadence operationalization for
  scope-gate.md rule 2's undefined "shelf life."
  Source: RefoundAI/lenny-skills pricing-strategy skill
  (https://github.com/RefoundAI/lenny-skills), per
  https://claudemarketplaces.com/skills/refoundai/lenny-skills/pricing-strategy.
- Skip: the pricing-page teardown / AI-readability audit mode and the
  price-increase-signal checklist from tool 1 — both are real
  capabilities but fall outside this role's chain scope (which ends at
  a verdict + tier structure + rationale, not an ongoing page/GTM
  audit); folding them in would be scope creep past what
  pricing-verdict-report's PRODUCES line covers.

## Segment fit

Both surveyed skills target SaaS/product pricing decisions generally
(not conjoint/PSM research design specifically), so their fit is at the
"what to do with a fielded study's output" layer (tier assembly,
re-validity), not at the "how to run the study" layer this rulebook's
existing four files already cover in depth (and arguably exceed —
this rulebook's design-rigor.md cites primary academic/Sawtooth sources
the surveyed skills do not reach).

## Gap line

Current state (this rulebook, `playbook/*.md`) already meets: correct
research-method selection (PSM vs. CBC vs. CVA), design-gate rigor
bands, incentive-alignment cost/benefit framing, and output-labeling
discipline (preference share vs. revenue, threshold vs. optimum) — all
absent from both surveyed skills, which give no design-rigor guidance
at all.
Current state is missing: any rule on assembling a fielded verdict into
a TIER STRUCTURE (value-metric validity check, anchor/decoy placement),
and an operational definition for "prior study still valid" (scope-gate
rule 2's undefined shelf life). Both gaps map directly to the two
adopted learnings above.

Sources:
- https://github.com/coreyhaines31/marketingskills
- https://awesomeskill.ai/skill/coreyhaines31-marketingskills-pricing-strategy
- https://github.com/RefoundAI/lenny-skills
- https://claudemarketplaces.com/skills/refoundai/lenny-skills/pricing-strategy
- https://openviewpartners.com/blog/how-to-price-your-product/
