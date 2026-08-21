---
subject: issue-1937
role: implementation
kind: survey
loop_state: coding
---

# Current-state survey: performance-engineering-operational-playbook procedural body

## Scope

Skill-repository checkout: `/tmp/skill-repository`, `main` at commit
`615d169` (checked out fresh for this issue).

Target: `skills/performance-engineering-operational-playbook/SKILL.md`
(single-skill family, per issue #1937).

## Frontmatter shape

canonical: skills/performance-engineering-operational-playbook/SKILL.md
(read in /tmp/skill-repository at commit 615d169)

```
---
name: performance-engineering-operational-playbook
description: Use when you need guidance on Performance-engineering operational playbook.
subject: issue-1174
layer_program: docs/issue-1174/proposals/operational-playbook-program.md
---
```

`description:` is still the unfilled template ("Use when you need
guidance on X"), matching the pre-recipe default seen in other
not-yet-authored skills rather than a Trigger-derived sentence.
canonical: skills/performance-engineering-operational-playbook/SKILL.md
(frontmatter block above, read in /tmp/skill-repository at commit
615d169).

## Body shape

The body already uses a numbered `Layer A / Layer B / Layer C` rule
format (`**Condition:** ... **Choice:** ... **Source:** ...`), two rules
marked `[REMOVAL]` (rules 5, 6), plus an "Evidence trail" table at the
end. derived: `grep -cE "^[0-9]+\." skills/performance-engineering-operational-playbook/SKILL.md`
(run in /tmp/skill-repository at commit 615d169), result: `10`.

No `## Trigger`, `## Procedure`, or `## Output shape` heading exists
anywhere in the body. derived: `grep -E "^## (Trigger|Procedure|Output shape)" skills/performance-engineering-operational-playbook/SKILL.md`
(run in /tmp/skill-repository at commit 615d169), result: no matches
(empty output, exit 1). This skill is therefore a live-edit case under
the frozen recipe's step 1 (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section), not a no-op.

## Manifest state

canonical: scripts/procedure_authored_skills.txt (read in
/tmp/skill-repository, 193 lines total; derived: `grep -c
performance-engineering-operational-playbook scripts/procedure_authored_skills.txt`,
result: `0`)

`performance-engineering-operational-playbook` is not yet listed. The
file's most recent entries (tail of the same read) are
`content-design-operational-playbook`,
`accessibility-aria-and-contrast-rules`, and
`interaction-design-form-control-and-layout` (issues #1928, #1927,
#1932), all `-operational-playbook`- or rule-numbered-body siblings
authored under the same frozen recipe.

## Pattern precedent

canonical: skills/content-design-operational-playbook/SKILL.md (read in
/tmp/skill-repository at commit 615d169) — `content-design-operational-playbook`
(issue #1928, same `-operational-playbook` naming pattern, also grouped
into research layers/axes rather than a flat `## Rules` list) carries
`## Trigger` / `## Procedure` / `## Output shape` in that exact shape:
Trigger names concrete conditions per axis with inline rule citations
(e.g. "rules 1-10"), Procedure is one numbered step per axis citing its
rule range, and description is a single sentence pulled from Trigger's
opening clause. This skill's own three layers (A: practitioner rules
1-7, B: named methodologies 8-9, C: academic grounding 10) map onto that
same per-axis-step Procedure shape.

## Checker behavior

canonical: scripts/check_skill_conformance.py (read in
/tmp/skill-repository at commit 615d169) — `PROCEDURE_HEADINGS =
("## Trigger", "## Procedure", "## Output shape")`; `--manifest <path>`
is additive/opt-in, checking only skills listed in the given manifest
file. canonical: docs/issue-1790/reports/implementation.md (Requirement
2 block, full-tree-checker fenced command block) — that record's fenced
output shows `python3 scripts/check_skill_conformance.py` (no
`--manifest` flag) exiting 0 against the full 234-skill tree on the same
commit range where the manifest-scoped run also exited 0, evidencing
that unlisted skills are unaffected by the flag.

## Rule-retention baseline (pre-change)

derived: `grep -nE "^[0-9]+\." skills/performance-engineering-operational-playbook/SKILL.md`
executed live in /tmp/skill-repository at commit 615d169:

```
17:1. **Condition:** a service is "slow" with no prior hypothesis.
24:2. **Condition:** reporting or alerting on request latency.
31:3. **Condition:** deciding how strict an SLO/error budget should be.
39:4. **Condition:** a queue/pool/worker pool is running "hot" (util near
47:5. **[REMOVAL] Condition:** an ORM-driven code path issues one query per
58:6. **[REMOVAL] Condition:** a connection pool is periodically exhausted
67:7. **Condition:** choosing a fix among several that close the same
80:8. **Condition:** starting any performance investigation with no
88:9. **Condition:** defining what "reliable enough" means for a service
98:10. **Condition:** justifying why a wait-time or capacity claim is valid
```

derived: the count above (10 rule lines) is the pre-change baseline
that phase-2's rule-retention sweep must reproduce in full against the
post-change file before that phase's checks are considered passing.

## Skip-condition check

Neither scout-directive skip condition applies literally (this is not a
pure bugfix and the recipe leaves the exact Trigger/Procedure wording
open), but per contract v3 s19 this is phase 1 (proposal only; no
CORE_BUILD_NOW=1 in the environment) — the actual authoring, the four
live checks, and the `git diff --stat` are phase-2 deliverables that
wait for the approval gate. This survey and its companion proposal are
the full phase-1 output.
