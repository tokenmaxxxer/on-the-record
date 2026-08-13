---
subject: issue-1199
role: brand-design
kind: scout-brief
loop_state: scouted
---

# Scout brief: brand-design tool landscape (issue-1199)

Mode: parallel WebSearch, one sweep round across three angles
(diagram/docs, design-token, accessibility-linter/handoff), followed by
one targeted deepening round on adoption evidence for the two thinnest
hits.

## Category patterns observed in the surveyed tools
- A single canonical source for a value (token/color/type), never
  hand-copied into each consumer (Style Dictionary, Tokens Studio).
- A verdict expressed as a concrete yes/no per item, backed by a
  measured number, rather than a prose impression (Stark's per-element
  contrast verdicts).
- A fixed, named vocabulary (diagram-design's bounded diagram-type
  list; DTCG's token-type enum) instead of a free-form category field.
- Adoption/discoverability tracked as its own concern, separate from
  whether the artifact exists (zeroheight's usage-tracking feature).

## Performance axes the surveyed tools compete on
1. Output fidelity/consistency vs. generic templates (diagram-design's
   "no Mermaid-slop" positioning).
2. Sync/round-trip reliability between the design surface and the
   consuming codebase (Style Dictionary, Tokens Studio).
3. Downstream-usage visibility after handoff, not just artifact
   existence (zeroheight).

## Adopt / skip against this role's checklists
canonical: docs/handbooks/brand-design/methodology.md (this repo, read
this session) and the four brand-design-*/README.md files (read this
session).
- Adopt into the existing checklist wording: a fixed enum for
  diagram/asset type at handoff (mirrors diagram-design's bounded type
  list); per-element granularity on consistency verdicts, one line per
  pairing (mirrors Stark); an explicit "which downstream path/role
  actually reads this handoff" line (mirrors zeroheight's usage
  tracking); a distinct "token source-of-truth file path" line, separate
  from the applied value (mirrors Style Dictionary / Tokens Studio).
- Skip: full platform features (theming engines, CI pipelines, paid
  tiers) — outside this role's write_scope
  (`design-tokens/*.json`, `docs/issue-<n>/reports/brand-design.md`);
  the fold-in borrows the design move, not the tool.

## Segment fit
This role's phase-2 record is a text report plus token JSON, not a live
Figma file or build pipeline, so the fold-in targets checklist wording
in the four existing `brand-design-*` plugins rather than new tooling.

## Field-vs-current-checklist gap
canonical: docs/handbooks/brand-design/methodology.md, "Phase-2 record
checklist" section (read this session). The current checklist items for
asset spec, consistency check, and system-handoff paths do not yet ask
for: a fixed type enum; per-pairing granularity stated as one line per
item; a named downstream consumer; or a distinct source-of-truth path.
The tool-learnings entries below add exactly these four lines.

## Sources
- https://github.com/cathrynlavery/diagram-design
- https://trendshift.io/repositories/26141
- https://github.com/style-dictionary/style-dictionary
- https://github.com/tokens-studio/figma-plugin
- https://docs.tokens.studio/
- https://www.getstark.co/figma/
- https://www.figma.com/community/plugin/732603254453395948/stark-contrast-accessibility-ai-checker
- https://zeroheight.com/measurement/
- https://help.zeroheight.com/hc/en-us/articles/36474342079259-Increasing-design-system-adoption
