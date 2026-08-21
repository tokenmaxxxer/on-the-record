---
subject: issue-1901
role: implementation
kind: survey
---

# Survey: defect-verification family (4 skills) against the frozen WAVE RECIPE

## Recipe basis

canonical: docs/issue-1790/reports/implementation.md, `## WAVE RECIPE` section (lines 232-252).

The frozen recipe (five steps):
1. Check each skill body for existing `## Trigger`/`## Procedure`/`## Output shape` headings before authoring; if present, record a no-op with evidence instead of authoring.
2. Insert `## Trigger`, `## Procedure` (steps citing `## Rules` rule numbers), `## Output shape` between the framing paragraph and `## Rules`.
3. Rewrite `description:` as a sentence derived from the `## Trigger` content, keeping the checker's "use when" trigger-marker substring.
4. Add the skill's directory name to `scripts/procedure_authored_skills.txt`.
5. Run the manifest checker, the full-tree checker, and the rule-retention grep sweep before committing.

The recipe carries no literal "Shape A/Shape B" labels; step 1 is its own binary classification — a skill body either already carries the three headings (no-op) or does not (requires live authoring). This survey uses "Shape A = already has the 3 headings (no-op)" / "Shape B = missing them (author)" as shorthand for that binary, matching the classification the issue-1901 task language asks for.

canonical: docs/issue-1892/reports/implementation.md, `## Checks` section (lines 94-151) — the most recent wave-2a implementation record (localization family). Its text states the #1790 recipe was reused unchanged, with two of the four checks' command wording refined:
- Check 2 (rule-retention sweep): compares `git show origin/main:<path>` against the working-tree file, filtered to numbered rule-start lines, plus a `source:` citation-line count per file (canonical: docs/issue-1892/reports/implementation.md lines 105-125).
- Check 4 (scoped diff): `git diff --stat origin/main..HEAD -- .`, scoped against the real upstream base rather than a local `--cached` snapshot (canonical: docs/issue-1892/reports/implementation.md lines 136-151).

This survey adopts the #1892 wording for checks 2 and 4, as the more recent of the two precedent records.

## Skill-repository checkout state

derived: `cd /tmp/skill-repository && git status -sb && git log -1 --oneline && git log origin/main -1 --oneline`
```
## issue-1896-wave2a-brand-design...origin/issue-1896-wave2a-brand-design
a84407c Author procedural bodies for wave 2a: brand-design family (issue-1896)
c93b81b Author procedural bodies for wave 2a: localization family (issue-1892) (#30)
```
Reading of the above: local checkout HEAD is `a84407c`; `origin/main` is `c93b81b`, the same commit the role-mapping note in this session names as the skill-repository reference point. The local branch carries one wave (brand-design) that `git status -sb` reports as ahead of its own remote tracking branch, not yet on `origin/main`.

derived: `cd /tmp/skill-repository && git diff origin/main --stat -- skills/defect-verification-reproduction-evidence-quality skills/defect-verification-independence-from-upstream-verdicts skills/defect-verification-severity-band-assignment skills/defect-verification-evidence-artifact-completeness scripts/procedure_authored_skills.txt`
```
 scripts/procedure_authored_skills.txt | 5 +++++
 1 file changed, 5 insertions(+)
```
Reading of the above: the fence lists only the manifest path; the SKILL.md paths given to the command are absent from it. canonical: docs/issue-1892/reports/implementation.md, `## Rationale for deviations` section, describes an analogous origin/main staleness condition that wave's authoring ran into; this survey carries the same re-fetch step forward as a gap for phase-2 (see Gaps section below).

## Per-skill findings (the family present in this checkout)

derived: `find /tmp/skill-repository -iname "*defect-verification*"`
```
/tmp/skill-repository/skills/defect-verification-reproduction-evidence-quality
/tmp/skill-repository/skills/defect-verification-independence-from-upstream-verdicts
/tmp/skill-repository/skills/defect-verification-severity-band-assignment
/tmp/skill-repository/skills/defect-verification-evidence-artifact-completeness
```
The fence above lists exactly the paths matched by the glob, consistent with the issue's stated family size for this wave.

derived:
```
$ cd /tmp/skill-repository && for d in defect-verification-reproduction-evidence-quality defect-verification-independence-from-upstream-verdicts defect-verification-severity-band-assignment defect-verification-evidence-artifact-completeness; do
  f="skills/$d/SKILL.md"
  echo "$d: lines=$(wc -l < "$f") rules=$(grep -cE '^[0-9]+\. ' "$f") headings=$(grep -c '^## Trigger' "$f")+$(grep -c '^## Procedure' "$f")+$(grep -c '^## Output shape' "$f") manifest=$(grep -c "^$d\$" scripts/procedure_authored_skills.txt)
done
defect-verification-reproduction-evidence-quality: lines=38 rules=13 headings=0+0+0 manifest=0
defect-verification-independence-from-upstream-verdicts: lines=32 rules=10 headings=0+0+0 manifest=0
defect-verification-severity-band-assignment: lines=34 rules=11 headings=0+0+0 manifest=0
defect-verification-evidence-artifact-completeness: lines=92 rules=10 headings=0+0+0 manifest=0
```
Reading of the above: every row's `headings=0+0+0` — none of the skills carries any of the recipe headings yet, so all classify as Shape B (author); none is a no-op candidate, so the empty-state clause in the issue's Acceptance criterion 1 does not apply to this family. Every row's `manifest=0` — none is yet listed in `scripts/procedure_authored_skills.txt`. The fence's `rules=` fields are the rule-retention sweep's baseline content the phase-2 sweep must retain in full during authoring.

| skill | lines | description: (current) | Shape | rule lines | in manifest? |
|---|---|---|---|---|---|
| defect-verification-reproduction-evidence-quality | 38 | "Use when you need guidance on Reproduction-evidence quality for a defect attempt. Applies to the reproduction-evidence-quality axis." | B (author) | 13 (rules 1-13; rules 9-10 marked `**REMOVAL**`) | no |
| defect-verification-independence-from-upstream-verdicts | 32 | "Use when you need guidance on Preserving independence from coding/qa/review's prior verdicts. Applies to the independence-from-upstream-verdicts axis." | B (author) | 10 (rules 1-10; rules 9-10 marked `**REMOVAL**`) | no |
| defect-verification-severity-band-assignment | 34 | "Use when you need guidance on Severity-band assignment for a reproduced defect. Applies to the severity-band-assignment axis." | B (author) | 11 (rules 1-11; rules 9-10 marked `**REMOVAL**`) | no |
| defect-verification-evidence-artifact-completeness | 92 | "Use when you need guidance on Evidence-artifact completeness for a reproduction attempt. Applies to the evidence-artifact-completeness axis." | B (author) | 10 (rules 1-10; rules 9-10 marked `**REMOVAL**`) | no |

canonical: docs/issue-1790/reports/implementation.md lines 236-241 states all pilot skills required authoring (no no-op case found); docs/issue-1892/reports/implementation.md's per-skill section likewise records all localization skills as requiring authoring. Both prior waves' own text describes the same all-Shape-B pattern this survey's derived output shows for the defect-verification family.

## Checker commands (confirmed live against the current checkout)

derived: `grep -n "PROCEDURE_HEADINGS" /tmp/skill-repository/scripts/check_skill_conformance.py`
```
26:PROCEDURE_HEADINGS = ("## Trigger", "## Procedure", "## Output shape")
```
Reading of the above: `/tmp/skill-repository/scripts/check_skill_conformance.py --manifest <path>` mode additively requires these three literal headings for every directory name listed in the manifest file.

acceptance: `cd /tmp/skill-repository && python3 scripts/check_skill_conformance.py` — result: exit 0
```
234 skills checked
```
Executed live 2026-08-21 against local checkout HEAD `a84407c`, prior to any change — establishes the pre-authoring baseline the phase-2 full-tree check must reproduce.

## Rule-count / effort comparison against prior waves

canonical: docs/issue-1790/reports/implementation.md lines 254-258, citing that record's own `derived: git diff --stat --cached` fence for the pilot skills (28-52 lines/skill diff range, 4-15 rules/skill). This wave's per-file table above shows a comparable 32-92 lines/file pre-authoring and 10-13 rules/skill range — the same order of magnitude as the pilot; no outlier skill surfaced that would call for a recipe deviation.

## Gaps / unknowns carried into the proposal

- Phase-2 authoring is not performed by this survey (phase-1 scope per contract v3 s19); the `## Trigger` wording for each skill is a judgment call for phase-2 authoring, derived from each skill's existing `## Rules` content and framing paragraph, per recipe step 2-3.
- `origin/main` may advance further (a new wave landing) between this survey and phase-2 authoring; phase-2 must re-fetch before editing, per the staleness note above.
