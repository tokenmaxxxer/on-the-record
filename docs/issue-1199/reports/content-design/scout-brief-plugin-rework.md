---
subject: issue-1199
role: content-design
kind: scout-brief
---

# Scout brief: Claude Code plugin/skill rework (2026-08-14 amendment)

Stages used: 1 sweep (3 parallel WebSearch) + 1 deepening (2 parallel WebFetch) = 2 stages, well under the 5-stage/3min budget. Mode: parallel (WebSearch calls batched in one turn; WebFetch calls batched in one turn).

## Sweep angles run
1. "Claude Code plugin marketplace content design copywriting microcopy skill"
2. "Claude Code skill content-design OR UX writing OR copywriting github marketplace"
3. "awesome claude code plugins marketplace list stars 2026"

## Candidates and adoption evidence
canonical: `gh api repos/content-designer/ux-writing-skill --jq '{stars:.stargazers_count}'`, this session → 147
- `content-designer/ux-writing-skill` — 147 GitHub stars, purpose-built for UX writing/content design. Surfaced independently in sweep angles 1 and 2 (overlap signal).
canonical: `gh api repos/coreyhaines31/marketingskills --jq '{stars:.stargazers_count}'`, this session → 44168
- `coreyhaines31/marketingskills` — 44,168 stars, but scope is marketing copy (homepage/ads/email), not in-product content design — secondary fit only.
- `rampstackco/claude-skills` (540 stars) and `boraoztunc/skills` (253 stars) — broader lifecycle/multi-discipline collections, content-design is one sub-skill among many; not deepened (lower fit than ux-writing-skill, budget spent on the clearer match).

## Judge point 1
ux-writing-skill is the clear best-fit exemplar: purpose-built (not a marketing-copy tool wearing a content-design label), independently surfaced across both targeted search angles. Deepened via WebFetch of its SKILL.md.

## Extracted must-bes / patterns
canonical: WebFetch of https://raw.githubusercontent.com/content-designer/ux-writing-skill/main/SKILL.md, this session
- Four-phase staged edit sequence named in the fetched SKILL.md: purposeful → concise → conversational → clear, applied as sequential single-dimension review phases rather than one holistic judgment call.
- Numeric benchmarks named in the fetched SKILL.md for the concise/clear phases (8-14 words/sentence, 40-60 chars/line).
- Per-UI-element-type pattern library named in the fetched SKILL.md (button/error/notification/form) specifying format+purpose+tone as a starting template — distinct from this rulebook's existing content_id-keyed string reuse (axis 6 rule 26): this is a shape/template for a category, not a specific string.

## Judge point 2 (saturation)
Assessment (a scouting judgment call, not an outcome claim): a third search/deepening round is unlikely to change the build decision, since the two patterns above are additive to the existing rulebook axes.
canonical: Read of /tmp/content-design-rulebook/playbook/operational-playbook.md axes 1-6, this session
No axis-1-6 rule already names staged single-dimension review phases or a per-element-type template. Deepening ends here.

## Gap line
Existing rulebook axes 1-6 name: tone-of-voice axis (NN/G 4-axis, axis 5), string-level reuse by content_id (axis 6 rule 26), plain_language_check categorization (axis 6 rule 27), severity tiering (axis 6 rule 28). No axis-1-6 rule names staged single-dimension review phases with per-phase numeric benchmarks, or a per-UI-element-type starting-template library — both map to the ux-writing-skill patterns above.

## Segment fit
ux-writing-skill's four-pillar framework (purposeful/concise/conversational/clear) targets exactly this role's artifact type (in-product UX copy with decision-tied rationale), not marketing copy — direct fit, no adaptation needed beyond folding as native rules per the 2026-08-13 operator amendment (no tool-attribution catalogs).

Sources:
- https://github.com/content-designer/ux-writing-skill
- https://raw.githubusercontent.com/content-designer/ux-writing-skill/main/SKILL.md
- https://github.com/coreyhaines31/marketingskills
- https://github.com/rampstackco/claude-skills
- https://github.com/boraoztunc/skills
