---
subject: issue-1199
role: accessibility
kind: scout-brief
---

# Scout brief: Claude Code plugin/skill ecosystem for accessibility (2026-08-14 amendment rework)

kind: scout-brief
subject: issue-1199

canonical: this session's own WebSearch/WebFetch calls (2026-08-14) and
`curl https://api.github.com/repos/<owner>/<repo>` star counts (this
session) — the landed 2026-08-13 fold-in
(`docs/issue-1199/reports/accessibility/scout-brief.md`) surveyed only
domain tools (axe-core, Lighthouse, Pa11y, Stark, Microsoft
Accessibility Insights for Web); the 2026-08-14 amendment requires this
separate Claude Code plugin/skill sweep before the fold-in counts.

## Mode

4 parallel WebSearch angles run in one turn (marketplace/general,
adoption-evidence/GitHub, Owl-Listener author line, gotalab/uxaudit
line) — genuine concurrent fan-out, not serialized.

canonical: this session's own 4-way parallel WebSearch batch plus one
follow-up `curl api.github.com` batch, both this turn — the combined
sweep results surfaced the same two exemplars from independent angles
(marketplace search and author-line search both surfaced Owl-Listener;
adoption-evidence search and gotalab-line search both surfaced
Community-Access/accessibility-agents as the top-starred result). This
brief accordingly uses one sweep round plus one adoption-evidence
lookup round (2 of the 5 allowed scout stages, well under the 3min
wall-clock cap).

## Category must-bes (from the surveyed field)

- **Domain decomposition, not criterion-ID decomposition**: the
  highest-adoption plugin (Community-Access/accessibility-agents, 390
  GitHub stars, canonical: `curl https://api.github.com/repos/
  Community-Access/accessibility-agents`, this session) splits
  accessibility work into eleven named interaction-pattern specialists
  (aria, modal/focus-trap, contrast, keyboard, live-region, forms,
  alt-text/headings, tables, links, plus a coordinating lead and a
  guided-audit wizard) rather than working straight down a WCAG SC-
  number list (canonical: this session's WebFetch of
  https://github.com/Community-Access/accessibility-agents, README
  specialist table). Two of its named domains — modal-specialist
  (focus trap + focus-return) and live-region-controller (dynamic-
  content announcement) — are patterns a generic SC-ID checklist can
  silently under-specify even when the underlying criterion (2.4.3,
  4.1.3) is nominally "in scope."
- **AI/automation stance**: the same repo's README states, canonical:
  this session's WebFetch of the same URL — "AI and automated tools
  are not perfect... cannot replace testing with real screen readers."
  This independently confirms, from inside the plugin ecosystem, the
  automated-scan-ceiling rule this role's prior domain-tool round
  already adopted (playbook rule 5.3, canonical:
  `docs/issue-1199/reports/accessibility.md`, "Deliverable/rule
  upgrade mapping" section, read this session) — no new action needed
  for this must-be.
- **Decisions get recorded, not just outcomes**: Owl-Listener/
  inclusive-design-skills (93 stars, canonical: `curl
  https://api.github.com/repos/Owl-Listener/inclusive-design-skills`,
  this session; author of designer-skills, already used as an
  exemplar by the interaction-design rework round, canonical: `git
  show 70ca1890:docs/issue-1199/proposals/2026-08-14-interaction-
  design-plugin-tool-landscape-rework.md`, read this session) ships a
  dedicated "Accessibility Decisions" plugin (6 skills/3 commands,
  canonical: this session's WebFetch of
  https://github.com/Owl-Listener/inclusive-design-skills) applying
  Architecture-Decision-Record discipline specifically to
  accessibility tradeoffs — "documents design rationale... solves lost
  context and undocumented tradeoffs."
- **Multi-modal input, not keyboard-only**: the same repo's "Inclusive
  Interaction" plugin (7 skills/3 commands, canonical: same WebFetch)
  designs explicitly for keyboard, voice, gesture, and switch control,
  not keyboard alone.

## Performance axes the field competes on

1. Pattern-specificity of checks (named interaction pattern vs.
   generic SC-ID) — accessibility-agents leads here.
2. Rationale capture for tradeoffs/exclusions (ADR-style) vs. bare
   verdict-only entries — inclusive-design-skills leads here.
3. Input-modality breadth in manual-check guidance (keyboard+voice+
   switch vs. keyboard-only) — inclusive-design-skills leads here.

## Adopt / skip

Adopt (traced to the findings above): (a) named focus-trap-and-return
+ live-region-announcement checks for interaction-heavy patterns, from
accessibility-agents' modal-specialist/live-region-controller domain
split; (b) rationale capture on not-applicable/tradeoff scope notes,
from inclusive-design-skills' Accessibility Decisions plugin.

Skip: accessibility-agents' full eleven-specialist multi-agent
architecture (this role does not orchestrate sub-agents; it produces
one evaluation record) and inclusive-design-skills' full 40-skill/
18-command catalog wholesale (scout-directive's "never clone the
exemplar" rule) — the two judgments above are adopted, not the tools'
own mechanics. gotalab/uxaudit (51 stars), masuP9/a11y-specialist-
skills (55 stars), and airowe/claude-a11y-skill (14 stars) surveyed as
lower-adoption secondary confirmation only (canonical: this session's
`curl api.github.com` batch) — their check catalogs (axe-core/jsx-a11y
wrapping, WCAG 2.2 A/AA scan-fix-verify workflow) restate the
automated-scan-ceiling must-be already covered; no new learning drawn
from them.

## Gap line

Already met by the current rulebook: automated-scan-ceiling rule
(playbook 5.3), AT evidence tool+version naming (5.1), machine-
suggestion draft-only rule (5.2), standing keyboard tab-stop +
focus-visible manual-check pair (canonical:
`docs/issue-1199/reports/accessibility.md`, "Deliverable/rule upgrade
mapping" section, read this session). Missing, and what this rework's
proposal targets: (1) no named check items for the two interaction
patterns named above — focus-trap/return, live-region announcement
(canonical: this session's WebFetch of
https://github.com/Community-Access/accessibility-agents, cited
earlier in this brief) — distinct from the generic SC list; (2)
not-applicable/tradeoff scope notes currently state only the exclusion
boundary, not the design rationale behind a deliberate tradeoff.

## Sources

- [Community-Access/accessibility-agents](https://github.com/Community-Access/accessibility-agents) — 390 stars
- [Owl-Listener/inclusive-design-skills](https://github.com/Owl-Listener/inclusive-design-skills) — 93 stars
- [gotalab/uxaudit](https://github.com/gotalab/uxaudit) — 51 stars
- [masuP9/a11y-specialist-skills](https://github.com/masuP9/a11y-specialist-skills) — 55 stars
- [airowe/claude-a11y-skill](https://github.com/airowe/claude-a11y-skill) — 14 stars
