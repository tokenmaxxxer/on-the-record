# Survey: test-authoring-isolation-and-fixture-strategy procedural body

## Write surface

Target checkout: `/tmp/skill-repository`, branch `main` at fetch time.
Family: single-skill family `test-authoring-isolation-and-fixture-strategy`
(no siblings under `test-authoring-*` in `skills/` — this is a one-skill
family unlike the pilot's 3+6-skill families).

## Frontmatter shape (pre-change)

canonical: skills/test-authoring-isolation-and-fixture-strategy/SKILL.md
(read live in /tmp/skill-repository, checked out at main)

```
---
name: test-authoring-isolation-and-fixture-strategy
description: Use when you need guidance on Operational playbook — isolation & fixture strategy.
---
```

canonical: skills/test-authoring-isolation-and-fixture-strategy/SKILL.md
(read live in /tmp/skill-repository, main) — body has no `## Trigger`,
`## Procedure`, or `## Output shape` headings, confirmed by grep:

```
$ grep -n "^## " skills/test-authoring-isolation-and-fixture-strategy/SKILL.md
```
derived: `grep -n "^## " skills/test-authoring-isolation-and-fixture-strategy/SKILL.md`
run live in /tmp/skill-repository — output: `## A. Fixture construction`,
`## B. pytest / xUnit fixture scope selection`, `## C. Test isolation /
independence`, `## D. Database-backed fixture strategy`, `## E. Test double
selection`, `## Conflicts noted`. No Trigger/Procedure/Output-shape
heading present. This skill is a live-edit target, not a no-op.

## Rule inventory (pre-change)

canonical: skills/test-authoring-isolation-and-fixture-strategy/SKILL.md
(read live in /tmp/skill-repository, main) — 21 numbered rule lines
across 5 lettered sections (A-E), each already carrying a `Source:`
citation and, where applicable, a `[REMOVAL]` marker:

- A. Fixture construction — 6 rules (1-6; rule 5 is `[REMOVAL]`)
- B. pytest/xUnit fixture scope selection — 4 rules (7-10; rule 9 is `[REMOVAL]`)
- C. Test isolation / independence — 4 rules (11-14; rule 12 is `[REMOVAL]`)
- D. Database-backed fixture strategy — 3 rules (15-17; rule 16 is `[REMOVAL]`)
- E. Test double selection — 4 rules (18-21; rule 20 is `[REMOVAL]`)

Total 21 rules, 5 marked `[REMOVAL]`. A `## Conflicts noted` section
follows the rule sections and must be preserved untouched (it is not part
of the Trigger/Procedure/Output-shape insertion point, which per the
frozen recipe sits between the framing paragraph and the first `## Rules`
-equivalent heading — here that is `## A. Fixture construction`).

## Manifest state

canonical: scripts/procedure_authored_skills.txt (read live in
/tmp/skill-repository, main) — 234 lines total (matches
`check_skill_conformance.py`'s "234 skills checked" full-tree count from
the #1790 pilot record), does not yet contain
`test-authoring-isolation-and-fixture-strategy`.

## Checker script

canonical: scripts/check_skill_conformance.py (read live in
/tmp/skill-repository, main) — unchanged since the #1790 pilot's
`--manifest <path>` opt-in addition; no logic change needed or in scope
here (issue #1950 non-goal 3: "checker logic changes" excluded).

## Recipe fit

The frozen WAVE RECIPE (docs/issue-1790/reports/implementation.md, `##
WAVE RECIPE` section) generalizes directly to this single-skill family:
steps 1-5 (no-op check, section insertion, description rewrite, manifest
append, four-check verification) require no adaptation. The only
family-specific difference from the pilot is scale — 1 skill / 21 rules
here vs. 9 skills / 89 rules in the pilot — which does not change the
procedure, only the size of the diff and the sweep output.

## Skip-condition check

Neither scout-directive skip condition applies on its face (this is not a
pure bugfix and the recipe leaves an authoring decision open — where
exactly to draw section boundaries in `## Trigger`/`## Procedure`), but
the recipe itself is frozen per #1790 and this issue's own text mandates
applying it "verbatim." Scouting is therefore scoped narrowly: no
external sweep was run for this wave, because the design question (what
shape a Trigger/Procedure/Output-shape section takes) was already settled
by the #1790 pilot and its record is the recipe source of authority named
directly in this issue. This survey substitutes an internal-recipe
re-read for an external sweep — see the proposal's Rationale for why no
alternative shape was considered.
