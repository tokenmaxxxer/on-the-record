---
code_under_review:
  - skill-repository/skills/defect-verification-reproduction-evidence-quality/SKILL.md
  - skill-repository/skills/defect-verification-independence-from-upstream-verdicts/SKILL.md
  - skill-repository/skills/defect-verification-severity-band-assignment/SKILL.md
  - skill-repository/skills/defect-verification-evidence-artifact-completeness/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# Implementation record: procedural-body wave 2a — defect-verification family

subject: issue-1901

## What was done

Authored `## Trigger` / `## Procedure` / `## Output shape` sections for
all 4 `defect-verification-*` skills in `tokenmaxxxer/skill-repository`,
per the recipe frozen in `docs/issue-1790/reports/implementation.md`
(#1790 pilot) and reused unchanged by every prior wave-2a family. Each
Procedure step cites the rule number(s) it draws on from the skill's own
`## Rules` section (both live and `**REMOVAL**`-marked rules folded into
a "retire ... (rule N), and retire ... (rule M)" step, matching the
precedent set in `capacity-planning-safety-buffer-sizing-by-criticality`).
Each skill's `description:` was rewritten as a sentence derived from its
new `## Trigger` section, keeping the "use when" trigger-marker
substring the checker requires. The 4 skill directory names were
appended to `scripts/procedure_authored_skills.txt`.

Basis: `docs/issue-1901/proposals/defect-verification-wave2a.md`
(approved via the exact-string `APPROVE issue-1901/implementation`
comment from JiwonJung94, an approvers.md-listed account matching the
phase-1 PR #1905 author — single-account mode; canonical: `gh issue view
1901 --json comments -q '.comments[-1].body'`, executed live this
session — result: last comment body exactly
`APPROVE issue-1901/implementation`) and
`docs/issue-1901/reports/implementation/survey.md`.

## Why

Applies the same frozen procedural-body recipe every prior wave-2a
family (most recently localization #1892, brand-design #1896's proposal,
marketing #1900) has used, keeping the navigational-layer framing
(Procedure steps cite rules, they don't restate rule content) and the
checker/manifest mechanism unchanged, per the issue's own non-goals (no
checker-logic change, no other family, no hooks). Adopts #1892's refined
check-command wording (checks 2 and 4, `origin/main`-scoped rather than
`--cached`) per the proposal's Rationale.

## What did not work

acceptance: `python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt` — result: exit 0 on the first authored version of all 4 skills (Check 1 below).
acceptance: `python3 scripts/check_skill_conformance.py` — result: exit 0 on the first run (Check 2 below).
acceptance: the rule-retention sweep (Check 3 below) — result: `missing=0` for all 4 files on the first sweep.
Nothing failed and needed a retry. The one snag was a self-inflicted `Edit` duplication of the `evidence-artifact-completeness` skill's "Research trail:" opening phrase while inserting the new headings; caught and corrected by re-reading the file before running the checks, so it never reached a check run or a commit.

## Rationale for deviations

None. The phase-1-approved plan's steps 1-4 (author headings citing
rule numbers, rewrite `description:`, append to the manifest, run the
four checks in order) were followed as proposed. The skill-repository
checkout (`/tmp/skill-repository`) was re-fetched against `origin/main`
before editing, per proposal constraint 4; `origin/main` at fetch time
was `1b04844` (marketing family, issue-1900) — already the head the
session's role-mapping note names as the skill-repository reference
point, so no rebase/cherry-pick step (unlike #1892's) was needed.

## Checks — executed live from the skill-repository checkout (`/tmp/skill-repository`, `origin/main` = `1b04844`)

### Check 1 — manifest checker

acceptance: `python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt` — result: exit 0

```
234 skills checked
exit=0
```

### Check 2 — full-tree checker

acceptance: `python3 scripts/check_skill_conformance.py` — result: exit 0

```
234 skills checked
exit=0
```

### Check 3 — rule-retention sweep

acceptance: per-file comparison of `git show origin/main:<path>` vs. the
working-tree file, `missing` = count of pre-change `^[0-9]+\. `-pattern
lines absent verbatim from the post-change file, plus a `source: http`
citation-line count per file — run in `/tmp/skill-repository` — result:
`missing=0` in all 4 files (canonical: the derived fence directly
below, this session's own live command output):

```
defect-verification-reproduction-evidence-quality: pre_rules=13 post_rules=24 missing=0 pre_source=9 post_source=9
defect-verification-independence-from-upstream-verdicts: pre_rules=10 post_rules=19 missing=0 pre_source=8 post_source=8
defect-verification-severity-band-assignment: pre_rules=11 post_rules=21 missing=0 pre_source=7 post_source=7
defect-verification-evidence-artifact-completeness: pre_rules=10 post_rules=19 missing=0 pre_source=2 post_source=2
```

canonical: the same fence directly above. `post_rules` exceeds
`pre_rules` in every row because the new `## Procedure` section's own
numbered steps match the same `^[0-9]+\. ` pattern the sweep uses to
find `## Rules` rule-start lines; the sweep's substance is the
`missing=0` field, not the raw `post_rules` count. derived: sum of the
`pre_rules` values above = 44 (13+10+11+10); derived: sum of the
`pre_source` values above = 26 (9+8+7+2).

### Check 4 — scoped `git diff --stat`

acceptance: `git diff --stat origin/main..HEAD -- .` (run in
`/tmp/skill-repository`) — result: lists exactly the 4 family SKILL.md
paths plus the manifest, nothing else

```
 scripts/procedure_authored_skills.txt                                        |  4 ++
 skills/defect-verification-evidence-artifact-completeness/SKILL.md            | 44 +++++++++++++++++-
 skills/defect-verification-independence-from-upstream-verdicts/SKILL.md       | 43 +++++++++++++++++-
 skills/defect-verification-reproduction-evidence-quality/SKILL.md             | 45 +++++++++++++++++-
 skills/defect-verification-severity-band-assignment/SKILL.md                  | 48 +++++++++++++++++-
 5 files changed, 180 insertions(+), 4 deletions(-)
```

## Open findings

None.

## Deliverables

- tokenmaxxxer/skill-repository#33 (commit `c96b8ed` on branch
  `issue-1901-wave2a-defect-verification`, opened against `main`): the 4
  defect-verification skill bodies, manifest extension. canonical: `gh pr
  view 33 --repo tokenmaxxxer/skill-repository --json url`, executed live
  this session — result:
  `https://github.com/tokenmaxxxer/skill-repository/pull/33`.
- This record.
