---
status: proposed
Subject: issue-1996
files:
  - docs/issue-1996/reports/knowledge-management.md
---

# Proposal: kubernetes-workload pilot family + icon-system skill + anchor citations (skill-repository wave)

## Note on survey-order-gate path

The current-state survey for this proposal was written first, at this role's own record path `docs/issue-1996/reports/knowledge-management/survey.md` (and its scout-brief sibling), per this role's `docs/`-only, own-record-area output-layout rule. `survey-order-gate.sh` checks a single hardcoded path, `docs/issue-1996/reports/implementation/survey.md`, regardless of which role is writing — a path this `knowledge-management` role session is refused from writing into by `board-gate.sh` ("belongs to another role"). No scout-skip condition actually applies (the spec leaves real design decisions open, per [[knowledge-management-skill-repository-wave-survey]]); this note names the gate's role-name assumption mismatch as the reason its hardcoded-path check cannot be satisfied here, not a claim that scouting was skipped.

## Request

Issue #1996 asks for a research-based gap-fill wave authored into the sibling `skill-repository` checkout (not this repo — this repo's own scope is `docs/` records only) and PRed there: a new `kubernetes-workload` family of 5 skills (requests-limits-decision, probe-selection, pdb-sizing, hpa-behavior, production-readiness-checklist), a new `brand-design-icon-system-svg` skill, and edits to 5 existing skills to add standard-citation anchors (RFC 9457, Stripe cursor+idempotency pattern, RFC 9110, Conventional Commits, W3C accname). Acceptance requires every new/edited SKILL.md to parse with `name`+`description` frontmatter, a "Use when" clause in the description, at least one cited source URL from the issue's list, and any already-covered anchor to be left alone rather than redundantly edited.

## Constraints

- All skill content lands in the sibling checkout `/home/jwjung/skill-registry` (skill-repository, remote `tokenmaxxxer/skill-repository`), authored and PRed there — this repo's write set for phase 2 is limited to `docs/issue-1996/reports/knowledge-management.md` recording that work, per the issue's explicit scope line and this role's `docs/`-only output-layout rule.
- Must follow the repo's existing frontmatter/body shape (`name`, `description` with "Use when...", `axis`, `rule_count_floor`; `## Trigger`, `## Procedure`, per-rule `source:` URLs) as observed on `api-design-http-semantics`, `api-design-error-design`, `api-design-payload-design` — [[knowledge-management-skill-repository-wave-survey]] (survey.md).
- Acceptance's own check-script requirement is only partially met by the repo's existing `scripts/check_skill_conformance.py`: it validates `name`/`description` non-emptiness and (in `--manifest` mode) the `## Trigger`/`## Procedure`/`## Output shape` headings, but does not check for the "Use when" substring or for source-URL citation — those two sub-checks need either an extension to that script or a small standalone validator added in the skill-repository checkout, per the issue's "(or a small validator added alongside)" allowance.
- Empty-state rule: any anchor target whose text already carries the standard is listed as already-covered, not edited redundantly.

## Rationale

Two of the five named anchor targets (`api-design-error-design` for RFC 9457, `api-design-http-semantics` for RFC 9110) already carry per-rule `source:` citations to the exact standard sections the issue names. The alternative — editing all 5 targets uniformly regardless of current state — was rejected because the issue's acceptance criterion explicitly carries an empty-state rule against redundant edits, and duplicating an already-cited RFC reference would produce a second, possibly divergent citation of the same standard inside one skill file, which is worse than leaving the existing one alone. Only 3 of the 5 targets (payload-design's idempotency-key gap, the two release-engineering skills' Conventional Commits gap, and accessibility's accname/first-rule-of-ARIA gap) get edits under this proposal.

For the check-script requirement, the alternative of writing a brand-new validator from scratch (ignoring `check_skill_conformance.py`) was rejected: the existing script already implements the harder half (frontmatter YAML block parsing, `name`/`description` extraction) correctly and is the repo's own established check surface: extending it keeps one canonical conformance check instead of two scripts asserting overlapping things differently.

## What will be done

Phase 2 (after approval) will, in the sibling skill-repository checkout:
1. Author 5 new SKILL.md files under a new `skills/kubernetes-workload-*` naming convention (matching the repo's existing flat `family-axis` directory naming, e.g. `kubernetes-workload-requests-limits-decision`), each with decision-first rules sourced from kubernetes.io (resource management, probes, PodDisruptionBudget, HPA docs) and learnkube.com's production-best-practices guide, each rule carrying a `source:` URL per the observed convention.
2. Author 1 new `skills/brand-design-icon-system-svg/SKILL.md`, sourced from m3.material.io icon design guidance, polaris.shopify.com icon creation guidance, and WCAG 1.4.11 (non-text contrast), following the same convention as the existing `brand-design-*` skills.
3. Edit `skills/api-design-payload-design/SKILL.md` to add an idempotency-key rule (Stripe-style, cross-referencing the idempotency pattern already present in `api-design-http-semantics` rule 7 rather than duplicating its explanation).
4. Edit `skills/release-engineering-semver-bump-selection/SKILL.md` or `skills/release-engineering-changelog-entry-categorization/SKILL.md` (whichever is the better-fitting home — decided during phase 2 by re-reading both bodies) to add a Conventional Commits → semver/changelog-category mapping rule, sourced from conventionalcommits.org.
5. Edit `skills/accessibility-aria-and-contrast-rules/SKILL.md` to add accname-precedence (W3C accname-1.2) and first-rule-of-ARIA rules.
6. Leave `skills/api-design-error-design/SKILL.md` and `skills/api-design-http-semantics/SKILL.md` untouched (already-covered) and record that determination in the phase-2 record's empty-state note.
7. Extend `scripts/check_skill_conformance.py` (or add a small sibling validator) to also check for a "Use when" substring in `description` and for at least one `source:`/http(s) URL matching the issue's source list, then run it live against the full changed set and paste the output into the phase-2 record.
8. Open a PR against the skill-repository's default branch carrying items 1–7, and record its URL, the live check output, and the empty-state note in `docs/issue-1996/reports/knowledge-management.md`.

## Out of scope

- Any change to this on-the-record repo's own `src/`/`test/` (none exist for this role's work) or to any file outside `docs/issue-1996/reports/knowledge-management.md`.
- Any skill family or axis not named in the issue (no scope creep into other infra-manifest gaps beyond the 5 named kubernetes-workload skills).
- Modifying skill-repository's CI/build tooling beyond the conformance-check extension named above.
- Retroactively re-auditing skill files outside the 5 named anchor targets for the same standards.

## How you'll know it worked

- The skill-repository PR (linked in the phase-2 record) diff shows exactly 6 new SKILL.md files (5 kubernetes-workload + 1 icon-system) and edits to 3 of the 5 named anchor targets, with the other 2 explicitly listed as already-covered in the record.
- `check_skill_conformance.py` (extended) or its sibling validator, run live against the changed set, exits 0 and its output — including the "Use when" and source-URL sub-checks — is pasted into the phase-2 record per this session's record-shape and test-claim directives.
- Every new/edited SKILL.md's `description:` contains a literal "Use when" clause and at least one rule cites a URL drawn from the issue's named source list (kubernetes.io, learnkube.com, m3.material.io, polaris.shopify.com, WCAG, conventionalcommits.org, W3C accname-1.2, RFC 9457/9110).
