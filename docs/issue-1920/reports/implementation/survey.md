# Current-state survey — issue-1920, implementation family wave

## Checkout

`git clone git@github.com:tokenmaxxxer/skill-repository.git /tmp/skill-repository-1920`
(fresh clone, isolated from the `/tmp/skill-repository` working tree, which
carries unrelated uncommitted state from a concurrent issue-1906 branch).
`origin/main` HEAD: `692ab0a` ("Author procedural bodies for wave 2a: devrel
family (issue-1911) (#35)") — matches the commit named in the issue body.

canonical: git log --oneline -1 origin/main (run in /tmp/skill-repository-1920)
— `692ab0a`.

## Frozen recipe (source)

`docs/issue-1790/reports/implementation.md`, "WAVE RECIPE" section
(pilot record, #1790): insert `## Trigger`/`## Procedure`/`## Output shape`
between the framing paragraph and `## Rules`, each Procedure step citing
rule number(s); rewrite `description:` from the authored Trigger; append
skill directory name to `scripts/procedure_authored_skills.txt`; run
manifest checker, full-tree checker, and a rule-retention grep sweep before
committing.

## Target family: implementation (3 skills, per issue scope)

The issue names exactly 3 skills to touch (not the 5 `implementation-*`
skills that exist in the tree — `implementation-audit` and
`implementation-blueprint` are explicitly excluded as "personal" skills,
i.e. not part of this role-source-allowlist mapping):

canonical: skill-repository/skills/ directory listing (run in
/tmp/skill-repository-1920) — `ls skills | grep implementation-` shows 5
directories: `implementation-audit`, `implementation-blueprint`,
`implementation-complexity-coupling-management`,
`implementation-design-pattern-selection`,
`implementation-performance-data-structure-choice`. Only the latter 3 are
in scope.

### Frontmatter / body shape check (per recipe step 1)

```
$ cd /tmp/skill-repository-1920
$ for s in implementation-complexity-coupling-management implementation-design-pattern-selection implementation-performance-data-structure-choice; do echo "=== $s ==="; grep -n "^## " skills/$s/SKILL.md; done
=== implementation-complexity-coupling-management ===
15:## Rules
98:## Counter-example tests
=== implementation-design-pattern-selection ===
14:## Rules
67:## Counter-example tests
=== implementation-performance-data-structure-choice ===
16:## Rules
67:## Counter-example tests
```
canonical: grep -n "^## " skills/<name>/SKILL.md, run live in
/tmp/skill-repository-1920 for each of the 3 target skills.

None of the 3 skills carries `## Trigger`, `## Procedure`, or
`## Output shape` — all 3 headings are absent in all 3 files. Per the
recipe's no-op clause (step 1), this means all 3 are live-authoring
candidates; none qualifies for a no-op/empty-state record.

### Rule inventory (what the retention sweep must protect)

- `implementation-complexity-coupling-management/SKILL.md`: `## Rules`
  lines 15-96, 9 numbered rules (rules 5 and 6 marked REMOVAL), plus a
  `## Counter-example tests` section (lines 98-111, 2 counter-examples)
  after the rules — this section is untouched by the recipe (it sits after
  `## Rules`, not between the framing paragraph and `## Rules`).
- `implementation-design-pattern-selection/SKILL.md`: `## Rules` lines
  14-65, 6 numbered rules (rules 5 and 6 marked REMOVAL), plus
  `## Counter-example tests` (lines 67-81, 2 counter-examples).
- `implementation-performance-data-structure-choice/SKILL.md`: `## Rules`
  lines 16-64, 6 numbered rules (rules 5 and 6 marked REMOVAL), plus
  `## Counter-example tests` (lines 67-80, 2 counter-examples).

canonical: skill-repository/skills/implementation-*/SKILL.md read in full
(3 files, /tmp/skill-repository-1920), line ranges above cite the actual
`## Rules` / `## Counter-example tests` heading positions per file.

Total pre-change rule count across the 3 skills: 9 + 6 + 6 = 21 numbered
rule lines. derived: grep -c '^[0-9]\+\.' skills/<name>/SKILL.md per file
(9, 6, 6), run live in /tmp/skill-repository-1920.

### `description:` frontmatter (rewrite target, per recipe step 3)

All 3 currently carry the template form the pilot record flagged as the
rewrite trigger:
- `implementation-complexity-coupling-management`: "Use when you need
  guidance on Complexity / coupling management. Applies to the
  complexity-coupling-management axis."
- `implementation-design-pattern-selection`: "Use when you need guidance
  on Design-pattern selection. Applies to the design-pattern-selection
  axis."
- `implementation-performance-data-structure-choice`: "Use when you need
  guidance on Performance-degradation prevention: data structure,
  algorithm, and. Applies to the performance-data-structure-choice axis."

canonical: skill-repository/skills/implementation-*/SKILL.md frontmatter
(`description:` field), read live in /tmp/skill-repository-1920 for the 3
target files.

### Manifest state

`scripts/procedure_authored_skills.txt` (origin/main, 692ab0a) lists 172
entries from prior waves (pilot's 9 plus waves 2-... through the devrel
family) and contains none of the 3 target skill names yet.

canonical: grep -F -e implementation-complexity-coupling-management -e
implementation-design-pattern-selection -e
implementation-performance-data-structure-choice
scripts/procedure_authored_skills.txt (run live in
/tmp/skill-repository-1920) — no match, exit 1.

### Checker baseline (pre-change)

```
$ cd /tmp/skill-repository-1920 && python3 scripts/check_skill_conformance.py
234 skills checked
$ echo "exit: $?"
exit: 0
```
canonical: python3 scripts/check_skill_conformance.py (no --manifest,
run live in /tmp/skill-repository-1920, pre-change baseline).

## Scout-directive skip record

Skip condition applies: this task's spec (frozen recipe in
docs/issue-1790/reports/implementation.md, WAVE RECIPE section) leaves no
open design decision — the shape of the sections, the rule-citation
convention, the description-rewrite rule, and the manifest/check sequence
are all fixed by the pilot record and reused verbatim per the issue's own
instruction ("Apply the frozen recipe verbatim"). No exemplar/product
research applies to writing decision-rule prose for an already-frozen
authoring template. Scouting is skipped under the "spec leaves no design
decision open" condition.

## What the proposal must cover

- Author `## Trigger`/`## Procedure`/`## Output shape` into all 3 target
  skill bodies, each Procedure step citing rule numbers from that skill's
  own `## Rules` list.
- Rewrite each skill's `description:` from its own authored Trigger text.
- Append the 3 skill directory names to `scripts/procedure_authored_skills.txt`.
- Re-run the checker in both manifest and full-tree modes, and the
  rule-retention grep sweep, before committing — the same four checks the
  pilot ran, scoped to this wave's 3 skills.
- Write set stays inside the 3 skill directories +
  `scripts/procedure_authored_skills.txt`; no checker-logic change per the
  issue's non-goals.
