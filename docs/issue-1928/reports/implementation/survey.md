# Current-state survey — issue-1928 (content-design-operational-playbook)

## Write surface

Checkout: fresh clone at `/tmp/skill-repository-1928`, remote
`git@github.com:tokenmaxxxer/skill-repository.git`, branched
`issue-1928-content-design-operational-playbook` off `origin/main`
(commit `9e39be5`). A separate concurrent session already has
uncommitted WIP in `/tmp/skill-repository` on branch
`issue-1906-wave2a-data-modeling` (modifying
`scripts/procedure_authored_skills.txt`) — this survey avoids that
checkout and clones fresh instead, per agent-coordination norms
(no shared-tree collision).

Target skill: `skills/content-design-operational-playbook/SKILL.md`
(single-skill family per the issue). canonical: read of
`/tmp/skill-repository-1928/skills/content-design-operational-playbook/SKILL.md`.

## Frontmatter shape

```
---
name: content-design-operational-playbook
description: Use when you need guidance on Content-design operational playbook.
---
```

`description:` is the template form the frozen recipe targets for
rewrite (bare restatement of the title, satisfies the checker's
trigger-marker substring test only degenerately via "use when").

## Body shape

The body already carries 7 axes of numbered `Condition → Choice →
Source` rules (31 rules total, verified by counting numbered list
items 1–31 in the file), a REMOVAL-category rule in each of the 6
original axes plus the added axis-6/7 rules, and an "Evidence trail"
+ "Depth note" tail section. This is exactly the playbook shape the
frozen recipe (docs/issue-1790/reports/implementation.md WAVE RECIPE)
targets. canonical: read of
`/tmp/skill-repository-1928/skills/content-design-operational-playbook/SKILL.md`.

Grepped for the three procedure headings — none present:

```
$ cd /tmp/skill-repository-1928 && grep -n '^## Trigger\|^## Procedure\|^## Output shape' skills/content-design-operational-playbook/SKILL.md
$ echo "exit: $?"
exit: 1
```

canonical: grep run in /tmp/skill-repository-1928 (no matches, exit 1)
— confirms this skill has not been given a procedure section yet; the
acceptance criterion's empty-state/no-op clause therefore does not
apply here. This is a live edit, same as all 9 pilot skills in #1790.

## Checker script state

`scripts/check_skill_conformance.py` already carries the
`--manifest <path>` opt-in check from #1790 (checked via
`grep -n 'PROCEDURE_HEADINGS\|--manifest' scripts/check_skill_conformance.py`
— both present, unchanged since #1790). No checker-logic change is
needed or in scope for this issue (issue text: "non-goals: ... checker
logic changes, hooks").

`scripts/procedure_authored_skills.txt` currently lists prior waves'
skills (tail: `architecture-interface-contract-shape`,
`architecture-module-boundary-definition`,
`implementation-complexity-coupling-management`,
`implementation-design-pattern-selection`,
`implementation-performance-data-structure-choice`); does not yet
contain `content-design-operational-playbook`. canonical: `tail -5
scripts/procedure_authored_skills.txt` run in /tmp/skill-repository-1928.

## Alternatives considered for write surface

Reusing the pre-existing `/tmp/skill-repository` checkout (shared
across sessions in this environment) was considered and rejected: it
currently has another issue's uncommitted change staged in its working
tree (on `issue-1906-wave2a-data-modeling`), so editing there risks
cross-contaminating an unrelated in-flight session's diff. A fresh
clone isolates this issue's write set, following the same one-clone-
per-issue convention visible in the other per-issue directories present
in /tmp (`/tmp/skill-repository-1874`, `-1892`, `-1900`, etc. — listed
via `find / -maxdepth 2 -iname 'skill-repository*'`).
