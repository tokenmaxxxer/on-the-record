---
Subject: issue-1996
---

# Scout brief

Mode: batched-sequential (single session, no parallel dispatch available for this read-only repo inspection). Stages used: 1 (sweep only — target repo's own existing skills are the field, not external competitors).

Field scouted: the skill-repository's own highest-rigor existing skills in the same `axis`/family shape as this issue's deliverables — api-design-http-semantics, api-design-error-design, api-design-payload-design; each already cites RFC/Stripe docs at rule-level.
canonical: skills/api-design-http-semantics/SKILL.md:10,55-69; skills/api-design-error-design/SKILL.md:10,64-86; skills/api-design-payload-design/SKILL.md:10,58-80 (read directly)

## Must-bes observed (Kano, from the exemplars)
- Frontmatter: `name` (matches dir name), `description` starting "Use when..." with condition-concrete triggers (not a bare title restatement), plus `axis` and `rule_count_floor` fields.
canonical: skills/api-design-http-semantics/SKILL.md:1-6 (read directly)
- Body: `## Trigger` and `## Procedure` headings (enforced by scripts/check_skill_conformance.py's `--manifest` mode), a "Research trail" line up top naming every primary/secondary source, and every individual rule line ending `source: <URL>`.
canonical: skills/api-design-error-design/SKILL.md:10,64-86 (read directly)

## Performance axes the exemplars compete on
1. Decision-first ordering — condition, imperative choice, source reasoning, not a taxonomy dump.
2. Per-rule source URL, not just a top-of-file bibliography — every individual imperative traces to a fetched primary source.
3. Explicit REMOVAL-tagged rules where the standard argues to drop a common anti-pattern (e.g. dropping a full-count field once offset-depth pain appears).
canonical: skills/api-design-payload-design/SKILL.md:76 (read directly)

## Adopt / skip
- Adopt: per-rule `source:` URL citation and the "Research trail" opening line — this is what acceptance's "cites at least one of the listed source URLs" checks against.
- Skip: don't invent a taxonomy-first structure (listing all K8s probe *types* before any decision rule) — the exemplars are decision-first, condition -> choice -> reasoning.

## Segment fit
The kubernetes-workload family and icon-system skill are new axes with no exemplar in-repo yet; api-design-http-semantics is the closest structural analog (external authoritative-doc synthesis, decision-first rules, per-rule source line) and sets the bar this issue's new skills should match.

## Gap line
Already met: the error-standard envelope citation in api-design-error-design and the HTTP-semantics RFC citation in api-design-http-semantics both already carry per-rule `source:` links to the exact RFC sections named in the issue.
canonical: skills/api-design-error-design/SKILL.md:64 (rule text cites "RFC 9457" with `source: https://www.rfc-editor.org/rfc/rfc9457.html`); skills/api-design-http-semantics/SKILL.md:55 (rule text cites "RFC 9110" with `source: https://www.rfc-editor.org/rfc/rfc9110.html`) (read directly)

Missing: an idempotency-key note is not present anywhere in api-design-payload-design (the concept currently lives only in api-design-http-semantics rule 7).
derived: `grep -in idempotenc /home/jwjung/skill-registry/skills/api-design-payload-design/SKILL.md` — no output

Missing: Conventional Commits is absent from both release-engineering-semver-bump-selection and release-engineering-changelog-entry-categorization.
derived: `grep -in "conventional.commit" /home/jwjung/skill-registry/skills/release-engineering-semver-bump-selection/SKILL.md /home/jwjung/skill-registry/skills/release-engineering-changelog-entry-categorization/SKILL.md` — no output

Missing: accname precedence / first-rule-of-ARIA is absent from accessibility-aria-and-contrast-rules.
derived: `grep -in "accname\|first rule of aria\|W3C" /home/jwjung/skill-registry/skills/accessibility-aria-and-contrast-rules/SKILL.md` — no output

Sources: skills/api-design-http-semantics/SKILL.md, skills/api-design-error-design/SKILL.md, skills/api-design-payload-design/SKILL.md, skills/release-engineering-semver-bump-selection/SKILL.md, skills/release-engineering-changelog-entry-categorization/SKILL.md, skills/accessibility-aria-and-contrast-rules/SKILL.md, scripts/check_skill_conformance.py (all read directly from /home/jwjung/skill-registry, sibling checkout of tokenmaxxxer/skill-repository)
