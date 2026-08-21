---
subject: issue-1911
kind: survey
---

# Current-state survey: devrel family (3 skills), wave 2a

## Skill-repository checkout state

Fresh clone made for this issue at `/tmp/skill-repository-1911`, branch
`issue-1911-wave2a-devrel`, from `origin/main`. canonical: `git log --oneline -3`
in that checkout:

```
d110b90 Author procedural bodies for wave 2a: defect-verification family (issue-1901) (#33)
1b04844 Author procedural bodies for wave 2a: marketing family (issue-1900) (#32)
e62e9bd Author procedural bodies for wave 2a: brand-design family (issue-1896) (#31)
```

This matches the `d110b90` checkout SHA named in the invoking prompt — the
fresh clone is not stale relative to `origin/main`. canonical:
docs/issue-1901/reports/implementation/survey.md, "Skill-repository checkout
state" section — that prior survey found the then-shared `/tmp/skill-repository`
checkout one wave ahead of `origin/main`. Using a dedicated fresh clone per
issue (this survey's approach) avoids that staleness class entirely; no
rebase/re-fetch step is needed in phase-2 for this wave.

## Family membership

`find . -iname "devrel*" -maxdepth 3` in the checkout lists exactly 3
directories: `skills/devrel-channel-convention`,
`skills/devrel-program-subtraction`, `skills/devrel-content-comprehensibility`.
canonical: `find . -iname "devrel*" -maxdepth 3` output in the fresh
checkout (above). This matches the issue's Requirement 1 ("All 3 devrel-*
skills"). canonical: gh issue view 1911 (body text) — the issue body's
opening line ("Family: devrel (10 skills...)") conflicts with its own
Requirements section ("All 3 devrel-* skills") and Acceptance criteria (both
say 3), and with the on-disk count of 3 found by the `find` sweep just
cited. This survey treats "3" as authoritative (matching Requirements,
Acceptance, and the on-disk count) and flags the body opening-line's "10" as
a stale/inconsistent figure rather than silently resolving it.

## Per-skill findings table

| skill | `## Trigger`/`## Procedure`/`## Output shape` present? | `## Rules` heading | numbered rule lines | `description:` template |
|---|---|---|---|---|
| devrel-channel-convention | absent | present (line 16) | 8 | `Use when you need guidance on Channel and format convention. Applies to the channel-convention axis.` |
| devrel-program-subtraction | absent | present (line 15) | 8 | `Use when you need guidance on Program subtraction (removal/omission decision rules). Applies to the program-subtraction axis.` |
| devrel-content-comprehensibility | absent | present (line 16) | 8 | `Use when you need guidance on Content comprehensibility (cognitive load / schema theory). Applies to the content-comprehensibility axis.` |

canonical: `grep -n "^## " <file>` and `grep -cE "^[0-9]+\." <file>` run per
file in the fresh checkout (see per-skill greps run this session). All 3
skills are the same `## Rules`-only body shape already authored across
#1790, #1884, #1892, and #1901 — no skill in this family is already
procedure-shaped, so the issue's empty-state clause ("a family skill already
procedure-shaped is recorded as no-op") does not apply to any of the 3; all
3 require authoring.

Frontmatter across all 3 already carries `axis:` and `rule_count_floor: 8`
(matching the 8 counted rule lines in each file) — consistent with the
frozen recipe's step 3 (rewrite `description:` only; other frontmatter
fields untouched).

## Manifest state

`scripts/procedure_authored_skills.txt` has 167 lines; `grep -i devrel` on
it returns nothing — none of the 3 devrel skills are yet listed, consistent
with none being already authored. canonical: `wc -l
scripts/procedure_authored_skills.txt` and `grep -i devrel
scripts/procedure_authored_skills.txt` run in the fresh checkout.

## Checker baseline (pre-change)

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ python3 scripts/check_skill_conformance.py
234 skills checked
```

Both exit 0 pre-change (baseline for phase-2 comparison).

## WAVE RECIPE applicability

The frozen recipe (docs/issue-1790/reports/implementation.md `## WAVE
RECIPE`) and the #1901 proposal's check-wording refinements (canonical:
docs/issue-1901/proposals/defect-verification-wave2a.md `## Rationale`,
second alternative) both apply unmodified to this family: same body shape,
same checker, same manifest file, same non-goals (no checker/hook changes,
no other family touched).
