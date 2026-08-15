Subject: issue-1199

# Scout brief — marketing role, Claude Code plugin-ecosystem sweep (2026-08-14 amendment)

Current-state gap (from this role's own prior tool-landscape attempt, this
session, restored via `git diff --cached` in
tokenmaxxxer/marketing-rulebook before it was reset): the pre-amendment
round surveyed general marketing-domain tools (a self-hosted
analytics/attribution platform, a self-hosted marketing-automation
platform, a behavioral-analytics toolkit) — none is a Claude Code
plugin/skill. Per the 2026-08-14 operator amendment, that round fails
issue-1199 Acceptance criterion 1 outright, so this sweep re-targets the
Claude Code plugin/skill ecosystem specifically.

Sweep angles run (batched-sequential in this session — WebSearch calls
issued one after another, not concurrently; stating this per the
scout-directive's fallback-disclosure requirement): (1) general
"Claude Code plugin marketing skill" marketplace search, (2) targeted
"claude code skill/plugin marketing copywriting positioning" search.
2 stages total (sweep + one deepening/verification round via WebFetch +
GitHub API), well under the 5-stage/3min budget.

## Must-bes (from the strongest hits, adoption-evidence gated)

- **coreyhaines31/marketingskills** — 44,319 stars, 6,959 forks
  (canonical: `curl -s https://api.github.com/repos/coreyhaines31/marketingskills`,
  run this session). Direct domain match: 50+ skills spanning CRO,
  copywriting, SEO, analytics, growth engineering. Design move: every
  skill reads a single shared `product-marketing.md` context file first
  — quoting the repo's own docs (WebFetch, run this session): "The
  `product-marketing` skill is the foundation — every other skill checks
  it first to understand your product, audience, and positioning before
  doing anything."
- **alirezarezvani/claude-skills**, marketing-skill/copywriting section —
  24,435 stars, 3,434 forks (canonical: `curl -s
  https://api.github.com/repos/alirezarezvani/claude-skills`, run this
  session; already the primary adoption exemplar for the capacity-planning
  role's rework per docs/issue-1199/reports/conformance-review.md). The
  `marketing-context` skill loads "brand voice, ICP, and positioning
  context" from a shared file and is explicitly "the foundation before
  writing — NOT a substitute for" the copywriting skill itself
  (WebFetch of the skill's own page, run this session). The
  `copywriting` skill separately requires four named contexts gathered
  before writing copy: "Page purpose and desired action," "Audience
  profile and objections," "Product differentiation and proof points,"
  and "Traffic source and visitor knowledge" (same WebFetch, quoting the
  list verbatim).

## Performance axes the field competes on

1. Whether positioning/ICP context is centralized and checked once vs.
   re-derived per artifact (both exemplars above converge on
   centralize-and-check-first).
2. Whether copy is gated on the *reader's* starting knowledge (traffic
   source / awareness stage), not just on the product's own positioning.

## Adopt / skip

- **Adopt**: positioning-statement consistency across this rulebook's own
  canvas/segment/channel fields (mirrors the shared-context pattern both
  exemplars converge on) — no new file/store needed, just a
  same-source-as-ICP requirement on the existing positioning-statement
  checklist line.
- **Adopt**: an explicit audience-awareness/traffic-source line before
  copy claims, mechanically checkable via the existing keyword-presence
  pattern the messaging-gate.sh file already uses for other lines.
- **Skip**: building a literal shared `product-marketing.md`-style
  context file/store — that is new infrastructure, out of this bounded
  fold-in's scope (mirrors this rulebook's own existing precedent of
  declining to build a competitor-tracking store for `market_category`).

## Gap line

The rulebook's messaging checklist already requires a positioning
statement and per-segment value themes (STP/ICP + Dunford canvas), but
had no rule tying that positioning statement back to the same source the
target-segment ICP uses, and no rule about the reader's starting
awareness before copy is written — both gaps directly match what the two
surveyed exemplars treat as baseline hygiene.

## Segment fit

This role's methodology already has copy-writing and segment
methodology as separate checklists (messaging doc vs. target segment);
the surveyed pattern (shared context, gated on reader awareness) fits as
a cross-reference rule plus one new checklist line, not a new section —
proportionate to a rulebook methodology page, not a full context-store
build.

Sources:
- https://github.com/coreyhaines31/marketingskills
- https://api.github.com/repos/coreyhaines31/marketingskills
- https://github.com/alirezarezvani/claude-skills
- https://api.github.com/repos/alirezarezvani/claude-skills
- https://alirezarezvani.github.io/claude-skills/skills/marketing-skill/copywriting/
