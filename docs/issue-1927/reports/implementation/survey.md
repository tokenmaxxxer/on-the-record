---
subject: issue-1927
role: implementation
kind: survey
---

# Current-state survey: accessibility-aria-and-contrast-rules procedural body

## Scope

Single-skill family per the issue: `accessibility-aria-and-contrast-rules`
in `tokenmaxxxer/skill-repository`, checkout at `/tmp/skill-repository`.

canonical: /tmp/skill-repository/skills/accessibility-aria-and-contrast-rules/SKILL.md
(read in full before drafting this survey/proposal).

## Frontmatter shape

```
---
name: accessibility-aria-and-contrast-rules
description: Use when you need guidance on Operational playbook: ARIA usage, contrast, and focus (issue-1174).
---
```

`description:` is still the template form ("Use when you need guidance
on <title>") — matches the pilot's pre-authoring pattern (#1790 record,
"Frontmatter shape" section), so this skill has not yet had `description:`
derived from a Trigger section.

## Existing body structure

The body opens with a one-paragraph framing statement, then goes
straight into `## 1. ARIA role selection` (rule section). No
`## Trigger`, `## Procedure`, or `## Output shape` heading exists
anywhere in the file. canonical:
/tmp/skill-repository/skills/accessibility-aria-and-contrast-rules/SKILL.md
(grepped for `^## Trigger`, `^## Procedure`, `^## Output shape` — zero
matches). Per the frozen recipe's step 1 (no-op check), this skill
requires a live edit — it is not already procedure-shaped.

## Rule inventory (for the retention sweep baseline)

5 rule sections, 15 numbered rules total:

- `## 1. ARIA role selection` — Rule 1.1, 1.2 [REMOVAL], 1.3 (3 rules)
- `## 2. Accessible naming` — Rule 2.1 [REMOVAL], 2.2, 2.3 [REMOVAL] (3 rules)
- `## 3. Contrast (WCAG 1.4.3)` — Rule 3.1, 3.2, 3.3 [REMOVAL/exception] (3 rules)
- `## 4. Focus order and visibility` — Rule 4.1, 4.2 [REMOVAL] (2 rules),
  plus one unnumbered "Open gap" note (not a rule; carried through
  verbatim, not counted in the retention sweep's rule-line total)
- `## 5. Evidence-field specificity and provenance` — Rule 5.1, 5.2, 5.3,
  5.4 (4 rules)

Total: 15 numbered rule lines, each with its own `Condition:`/`Choice:`
(or `Why:`) block and a `Source:` citation. derived: manual count against
the fenced body quoted above from the live file read. This is the
pre-change baseline the phase-2 rule-retention sweep must reproduce in
full.

## Manifest state

```
$ grep -c accessibility /tmp/skill-repository/scripts/procedure_authored_skills.txt
0
```
canonical: grep -c accessibility scripts/procedure_authored_skills.txt
(run in /tmp/skill-repository) — the skill is not yet listed; appending
it is additive to the manifest's existing entries.

## Checkout state (collision note)

canonical: `git status` (run live in /tmp/skill-repository during this
survey) — the checkout was on branch `issue-1906-wave2a-data-modeling`
with an uncommitted, unrelated modification to
`scripts/procedure_authored_skills.txt` at survey time, not authored by
this session. The delivery step for this family will start from a
fresh clone or worktree rather than that dirty tree.

## Applicability of the frozen recipe

The #1790 pilot's WAVE RECIPE (docs/issue-1790/reports/implementation.md,
"WAVE RECIPE" section) applies verbatim: this is a single-skill family
with no existing Trigger/Procedure/Output-shape section, so it needs
authoring, not a no-op record. No design decision is open beyond
applying the frozen recipe — the recipe already specifies where the new
sections go, how `description:` is derived, and which four checks to
run.
