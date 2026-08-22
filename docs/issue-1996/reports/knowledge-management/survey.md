---
Subject: issue-1996
---

# Current-state survey: skill-repository against issue #1996's three deliverables

Target repo: sibling checkout at `/home/jwjung/skill-registry` (git remote `origin` = `git@github.com:tokenmaxxxer/skill-repository.git`), currently on branch `fix-1950`, clean working tree.
canonical: `cd /home/jwjung/skill-registry && git remote -v && git status` output (read directly) — remote origin git@github.com:tokenmaxxxer/skill-repository.git (fetch/push), branch fix-1950, clean

## Deliverable 1 — kubernetes-workload family

No `kubernetes-workload` family and no directory matching `*k8s*`/`*kubernetes*`/`*probe*`/`*hpa*`/`*pdb*` exists under `skills/`.
`derived: ls /home/jwjung/skill-registry/skills | grep -i kubernetes` — no output

This matches the issue's framing ("the library's biggest measured gap; no infra-manifest family exists") — full gap: every planned skill slug (requests-limits-decision, probe-selection, pdb-sizing, hpa-behavior, production-readiness-checklist) is net-new, none exist under `skills/` today.
canonical: `ls /home/jwjung/skill-registry/skills` full listing (read directly) — no directory name matches any planned skill slug

## Deliverable 2 — brand-design-icon-system-svg

No `icon` directory exists anywhere under `skills/`, including within the existing `brand-design-*` family (brand-consistency-governance, brand-identity-strategy, color-visibility, logo-clear-space-size, typography-pairing).
`derived: ls /home/jwjung/skill-registry/skills | grep -i icon` — no output

Full gap — net-new skill, sibling to the existing `brand-design-*` skills.

## Deliverable 3 — anchor-citation edits

Per-target findings ([[scout-brief]] has the same evidence with canonical citations; repeated here for the proposal to draw from directly):

1. `api-design-error-design` — **already covered**. Carries a per-rule `source:` citation to RFC 9457 (`https://www.rfc-editor.org/rfc/rfc9457.html`) as the named envelope standard, including the `application/problem+json` shape.
canonical: skills/api-design-error-design/SKILL.md:22,64 (read directly)

2. `api-design-payload-design` — **partially covered, edit needed**. Already carries the Stripe-style cursor-over-offset decision rule (rule 1, citing sequinstream.com and Stripe docs), but has zero mention of idempotency keys anywhere in the file.
`derived: grep -in idempotenc /home/jwjung/skill-registry/skills/api-design-payload-design/SKILL.md` — no output

3. `api-design-http-semantics` — **already covered**. Carries multiple per-rule `source:` citations to RFC 9110 (`https://www.rfc-editor.org/rfc/rfc9110.html`).
canonical: skills/api-design-http-semantics/SKILL.md:55,57 (read directly)

4. `release-engineering-semver-bump-selection` / `release-engineering-changelog-entry-categorization` — **not covered, edit needed**. Neither file mentions Conventional Commits.
`derived: grep -in "conventional commit" /home/jwjung/skill-registry/skills/release-engineering-semver-bump-selection/SKILL.md /home/jwjung/skill-registry/skills/release-engineering-changelog-entry-categorization/SKILL.md` — no output

5. `accessibility-aria-and-contrast-rules` — **not covered, edit needed**. No mention of accname, "first rule of ARIA", or a W3C accname citation.
`derived: grep -in "accname" /home/jwjung/skill-registry/skills/accessibility-aria-and-contrast-rules/SKILL.md` — no output

## Repo conventions to follow (from existing SKILL.md files and the check script)

- Frontmatter: `name:` (must equal the directory name), `description:` beginning with a condition-concrete "Use when..." trigger clause, plus repo-observed `axis:` and `rule_count_floor:` fields on the API/release-engineering families.
canonical: skills/api-design-http-semantics/SKILL.md:1-6 (read directly)
- Body: `## Trigger` and `## Procedure` headings (checked by `scripts/check_skill_conformance.py --manifest`), an opening "Research trail" line naming every source consulted, and every individual rule ending in `source: <URL>`.
canonical: skills/api-design-error-design/SKILL.md:10,64 (read directly)
- The conformance script is the closest thing to "the repo's own check script" the issue's acceptance criterion asks to run live: it validates frontmatter `name`/`description` shape and, in `--manifest` mode, the `## Trigger`/`## Procedure`/`## Output shape` headings. It does not check for a "Use when" substring specifically, nor for source-URL citation — those two acceptance sub-checks (description contains "Use when", cites a listed source URL) have no existing script coverage and will need either extending `check_skill_conformance.py` or a small standalone validator, to be built in phase 2.
canonical: /home/jwjung/skill-registry/scripts/check_skill_conformance.py:1-20 (read directly)

## Scope note

This on-the-record repo's own scope for issue #1996 is `docs/` only (records/proposal); all skill content described above is authored into the sibling skill-repository checkout and PRed there in phase 2, per the issue body's explicit scope line.
