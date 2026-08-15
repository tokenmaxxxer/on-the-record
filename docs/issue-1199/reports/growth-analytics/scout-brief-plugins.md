# Scout brief: Claude Code plugin/skill ecosystem for growth-analytics (issue-1199, 2026-08-14 amendment)

canonical: this session's own tool-call transcript (three WebSearch calls
issued together in one turn, then two deepening calls — one WebSearch, one
WebFetch — read this session) for every finding below unless a more
specific citation is given inline.

Mode: parallel WebSearch fan-out, three angles in one turn (by-marketplace-
catalog, by-vendor-official-plugin, by-agent-collection), then two
deepening rounds (adoption-metric confirmation on the two strongest hits).
Stage count: this brief's own five numbered sections below correspond
1:1 to the five stages actually run (one sweep stage plus two judge points
plus two deepening rounds), within the five-stage budget. Wall-clock: well
under the three-minute budget (five total tool calls, no retries).

## Sweep angle 1 — marketplace/catalog search
Query: "Claude Code plugin growth analytics A/B testing skill github stars".
Surfaced generic marketplace aggregators (claude-code-plugins-plus-skills,
awesome-claude-code-toolkit) and named "Goose-skills" (125 growth/GTM
skills) as a growth-marketing-adjacent collection, not growth-analytics-
specific (SEO/ads/outreach, not experimentation/funnel measurement).

## Sweep angle 2 — vendor-official plugin search
Query: "Claude Code marketplace plugin product analytics funnel skill".
Surfaced **PostHog/ai-plugin** (official, listed on Anthropic's own plugin
directory at claude.com/plugins/posthog) and a standalone "Funnel Analysis"
skill on mcpmarket.com.

## Sweep angle 3 — agent-collection search
Query: "awesome-claude-plugins data analytics experimentation".
Surfaced VoltAgent's data-scientist subagent entry and a general "Data"
Anthropic plugin (SQL/warehouse-focused, not experimentation-focused).

## Judge point 1
canonical: this session's own tool-call transcript (the three sweep-angle
WebSearch results, read this session).
Overlap: PostHog's plugin surfaced independently via both angle 1 and
angle 2 context (product analytics + experiments) — the strongest
adoption signal in the sweep. A named "experiment-tracker" subagent
pattern surfaced attached to contains-studio/agents, a large general-
purpose collection, in the angle-1 result set — deepened next.

## Deepening round 1 — adoption confirmation
- PostHog/ai-plugin: [github.com/PostHog/ai-plugin](https://github.com/PostHog/ai-plugin)
  — 65 GitHub stars, official (listed on Anthropic's own plugin directory
  at claude.com/plugins/posthog), ships 30+ task-specific skills including
  `/posthog:experiments` and experiment creation/lifecycle guidance.
  canonical: this session's own WebSearch call for query "PostHog/ai-plugin
  github stars repository", read this session.
- contains-studio/agents: [github.com/contains-studio/agents](https://github.com/contains-studio/agents)
  — 12.4k GitHub stars, contains a named
  `project-management/experiment-tracker.md` subagent whose stated
  expertise is A/B testing, feature flagging, cohort analysis, and rapid
  iteration validated against real user behavior.
  canonical: this session's own WebFetch call against
  https://github.com/contains-studio/agents, read this session.

## Judge point 2 (saturation)
canonical: this session's own deepening-round results above, read this
session.
Two independent, well-adopted sources (one official-vendor-integration,
one large general-purpose agent collection) each converge on the same
must-be: growth-analytics work inside a coding-agent session should be
tied directly to the live experimentation platform / feature-flag state
(PostHog's `/posthog:experiments` command surface) and to a fast-iteration
cadence discipline (experiment-tracker's explicit "every feature validated
by real user behavior, rapid iteration" framing) — not treated as a
document-only exercise disconnected from what's actually running. A third
deepening round on marketing-funnel skills (mcpmarket Funnel Analysis) was
judged not decision-relevant: it restates the funnel-stage/segment
breakdown already covered natively by this role's own ga-funnel
methodology, adding no new build decision. Deepening stopped at this
judge point, within the five-stage budget.

## Must-bes / performance axes extracted
- Must-be: an experimentation surface plugin/skill treats the live platform
  state (running experiments, current flag configuration) as ground truth
  the AI must query before reasoning about a result, not just prose the AI
  infers from a description.
- Must-be: an experiment-tracking skill states explicit cadence/iteration
  discipline (ship, measure, decide fast) as its own named concern,
  distinct from the underlying statistics.
- Performance axis 1: direct platform-state access (PostHog's MCP/plugin
  query surface) vs. prose-only description of an experiment.
- Performance axis 2: named iteration-cadence discipline
  (experiment-tracker) vs. leaving cadence implicit in a general
  methodology.

## Gap line
canonical: docs/issue-1199/reports/growth-analytics.md (this repo, read
this session) — the "Tool-landscape survey" and rule-upgrade sections of
the landed 2026-08-13 fold-in.
This role's existing ga-trust/ga-prereg/ga-funnel methodology (native,
first-principles, per that record) already covers SRM/A-A validation plus
cross-arm exposure integrity, pre-registration discipline plus baseline-
variance accounting, and funnel segment breakdown plus corroborating
evidence.
canonical: docs/issue-1199/reports/growth-analytics.md (this repo, read
this session), same section as above.
It does NOT currently require: (a) that a trust-verdict walkthrough
confirm the reported effect against a queryable live platform state
before proceeding, distinct from the exposure-integrity check already
added in the 2026-08-13 round; or (b) that a pre-registration proposal
name its own decision-cadence commitment (how soon after the decision
rule clears will the call actually be acted on) alongside the existing
decision-rule threshold. Both gaps are targeted by the plugin-ecosystem
learnings above.

## Adopt / skip (steering only — proposal below carries the binding version)
Adopt: platform-state-grounding discipline (from PostHog) and cadence-
commitment discipline (from experiment-tracker), each as a native rule
addition, no tool name in rulebook text.
Skip: adopting PostHog's actual MCP/API integration mechanism or
contains-studio's full 40-plus-agent collection — this role produces
judgment walkthroughs, not a live-integration harness or a multi-agent
studio.

## Sources
- https://github.com/PostHog/ai-plugin
- https://github.com/contains-studio/agents
- https://github.com/contains-studio/agents/blob/main/project-management/experiment-tracker.md
- https://posthog.com/docs/model-context-protocol/claude-code
- https://mcpmarket.com/tools/skills/funnel-analysis-product-metrics
- https://claude.com/plugins/posthog
