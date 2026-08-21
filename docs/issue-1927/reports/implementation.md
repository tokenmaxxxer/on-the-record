---
code_under_review:
  - docs/issue-1927/reports/implementation.md
loop_state: landed
type: feature
breaking: false
verdict: pass
---

canonical: commit `3c509dc` on branch `issue-1927-accessibility-procedural-body` in
tokenmaxxxer/skill-repository (pushed; PR
https://github.com/tokenmaxxxer/skill-repository/pull/41)

## What was done

Authored the procedural body for the single-skill family
`accessibility-aria-and-contrast-rules` in `tokenmaxxxer/skill-repository`,
applying the WAVE RECIPE frozen in the #1790 pilot record verbatim:

- Inserted `## Trigger` / `## Procedure` / `## Output shape` sections
  between the framing paragraph and `## 1. ARIA role selection`, with
  Procedure steps citing the rule numbers (`Rule 1.1`–`Rule 5.4`) they
  draw on.
- Rewrote `description:` as a sentence derived from the authored Trigger
  content, keeping the checker's trigger-marker substring ("use when" /
  "Use when").
- Appended `accessibility-aria-and-contrast-rules` to
  `scripts/procedure_authored_skills.txt` (incremental append, file not
  reordered or rewritten).
- Ran the four required checks live from a fresh clone of
  `tokenmaxxxer/skill-repository` (branch
  `issue-1927-accessibility-procedural-body`, off `origin/main`, avoiding
  the dirty `/tmp/skill-repository` checkout flagged in
  docs/issue-1927/reports/implementation/survey.md's "Checkout state"
  section).
- Opened tokenmaxxxer/skill-repository#41 carrying the two-file diff.

Check 1 — manifest-scoped checker, executed live:

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
exit: 0
```
acceptance: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt — result: exit 0, "234 skills checked" (fenced immediately above)

Check 2 — rule-retention sweep, executed live:

```
$ grep -c "^\*\*Rule " skills/accessibility-aria-and-contrast-rules/SKILL.md
15
$ grep -n "^\*\*Rule " skills/accessibility-aria-and-contrast-rules/SKILL.md
75:**Rule 1.1 — Do not assign a role you cannot fully implement.**
87:**Rule 1.2 [REMOVAL] — Remove ARIA roles that cloak native semantics.**
102:**Rule 1.3 — Use ARIA to add state, not to replace role/name.**
112:**Rule 2.1 [REMOVAL] — Remove `aria-label`/`aria-labelledby` that
129:**Rule 2.2 — Prefer visible text as the accessible name source.**
140:**Rule 2.3 [REMOVAL] — Remove reliance on `title`/`placeholder` for
154:**Rule 3.1 — Body/standard text contrast threshold.**
161:**Rule 3.2 — Large-text contrast threshold.**
168:**Rule 3.3 [REMOVAL/exception] — When a contrast fix is not required.**
180:**Rule 4.1 — Focus order must follow logical/reading structure, not
189:**Rule 4.2 [REMOVAL] — Never remove the visual focus indicator via
212:**Rule 5.1 — Name the assistive technology, not the generic phrase.**
225:**Rule 5.2 — A machine-suggested accessible name or alt text is a
244:**Rule 5.3 — Automated-scan evidence alone does not license an
262:**Rule 5.4 — A tradeoff-driven `not-applicable` scope note states the
```
canonical: docs/issue-1927/reports/implementation/survey.md, "Rule inventory" section (pre-change count of 15 rule lines, read during phase-1 survey)
acceptance: rule-retention sweep — result: 15 rule lines found post-change (fenced immediately above) — matches the pre-change count of 15: zero rule-line loss.

Check 3 — `git diff --stat` scoped to the write set, executed live:

```
$ git diff --stat
 scripts/procedure_authored_skills.txt              |  1 +
 .../accessibility-aria-and-contrast-rules/SKILL.md | 63 +++++++++++++++++++++-
 2 files changed, 63 insertions(+), 1 deletion(-)
```
acceptance: git diff --stat — result: only skills/accessibility-aria-and-contrast-rules/SKILL.md and scripts/procedure_authored_skills.txt changed (fenced immediately above)

Check 4 — full-tree checker, executed live:

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
exit: 0
```
acceptance: python3 scripts/check_skill_conformance.py (full tree, no flag) — result: exit 0, "234 skills checked" (fenced immediately above)

## Why

Requirement 1 of issue #1927 (`docs/issue-1790/reports/implementation.md`
WAVE RECIPE section) calls for this family's procedural body to be
authored per the frozen recipe verbatim and delivered as a
skill-repository PR plus this record, with the four checks re-run and
pasted live.

## Upstream / basis

- docs/issue-1927/proposals/accessibility-aria-and-contrast-rules-procedural-body.md
  (approved via issue comment `APPROVE issue-1927/implementation`)
- docs/issue-1790/reports/implementation.md (WAVE RECIPE, frozen pattern)
- docs/issue-1927/reports/implementation/survey.md (pre-change rule
  inventory, checkout-state note)

## What did not work

None.

## Open findings

None.

## Deliverables

- tokenmaxxxer/skill-repository#41 (commit `3c509dc` on
  `issue-1927-accessibility-procedural-body`): the skill's authored
  procedural body and manifest extension.
- This record.
