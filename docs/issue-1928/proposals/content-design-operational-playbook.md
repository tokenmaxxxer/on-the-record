---
status: proposed
files:
  - skill-repository/skills/content-design-operational-playbook/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Procedural-body authoring: content-design-operational-playbook (wave 2a)

basis: docs/issue-1928/reports/implementation/survey.md (current-state
survey, read before drafting this proposal).
scout-skip: scouting skipped — the recipe this proposal applies is
frozen verbatim in docs/issue-1790/reports/implementation.md (WAVE
RECIPE section, itself scouted/decided during the #1790 pilot); this
issue's own text requires "apply the frozen recipe verbatim," leaving
no open design decision for a fresh scout pass to inform.

## Request

Author the frozen procedural-body recipe (docs/issue-1790/reports/
implementation.md WAVE RECIPE) onto the single skill
`content-design-operational-playbook`: insert `## Trigger` /
`## Procedure` / `## Output shape` at the top of the body (Procedure
steps citing rule numbers), rewrite `description:` from the authored
Trigger section, and append the skill name to
`scripts/procedure_authored_skills.txt`. Guidance-only — zero rule-line
loss, no checker-logic change, no hooks.

## Constraints

- No rule text may be deleted; the survey confirms this skill is not
  already procedure-shaped (`## Trigger`/`## Procedure`/`## Output
  shape` all absent), so this is a live edit, not a no-op.
- `scripts/check_skill_conformance.py` is not touched — it already
  carries the `--manifest` opt-in check from #1790; only the manifest
  file gains one line.
- The rewritten `description:` must still satisfy the checker's
  existing trigger-marker substring test.
- Single-skill family: no other skill's file is touched.

## Rationale

One decision was open: whether to reuse the checker script or extend
it further for this issue.

**Checker reuse vs. re-extension.** Considered re-touching
`check_skill_conformance.py` to add a family-specific validation (e.g.
requiring each Procedure step to cite a rule number via regex).
Rejected: the issue's own non-goals list "checker logic changes" for
this wave — the manifest-gated check built in #1790 already covers the
Trigger/Procedure/Output-shape requirement generically, and this
family's single skill needs no new check surface. Reusing the existing
`--manifest` mechanism keeps this wave's write set to exactly the
skill body plus one manifest line, matching the issue's requirement 2
("no path outside the skill + manifest is touched").

## What will be done

1. In `skills/content-design-operational-playbook/SKILL.md`, insert a
   `## Trigger` / `## Procedure` / `## Output shape` section between
   the frontmatter and the `# Content-design operational playbook`
   heading (or immediately after it), each Procedure step citing the
   axis/rule number(s) it draws on (e.g. "check whether the field
   failure is user- or system-caused (rules 1, 5)"). All 31 existing
   numbered rules, the "Evidence trail," and the "Depth note" sections
   are preserved unchanged below, reorganized only, never deleted.
2. Rewrite the skill's `description:` from a sentence derived from the
   new `## Trigger` section, still containing a trigger-marker
   substring the checker recognizes.
3. Append `content-design-operational-playbook` to
   `scripts/procedure_authored_skills.txt`.
4. Run, live, from the skill-repository checkout: the manifest checker
   (`--manifest scripts/procedure_authored_skills.txt`), a rule-
   retention sweep (grep every pre-change numbered rule line's
   substring against the post-change file), `git diff --stat`, and the
   full-tree checker (no `--manifest` flag) — paste all four outputs
   into `docs/issue-1928/reports/implementation.md`.

## Out of scope

- Any other skill or family.
- Any change to `scripts/check_skill_conformance.py`.
- Any hook or enforcement mechanism.
- Any frontmatter field other than `description:`.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0.
- Every one of the 31 pre-change rule lines' distinguishing substring
  greps successfully in the post-change file.
- `git diff --stat` shows only `skills/content-design-operational-
  playbook/SKILL.md` and `scripts/procedure_authored_skills.txt`.
- A full-tree checker run (no `--manifest`) still exits 0 for all 235
  skills (234 + this one now in the tree, unaffected by the manifest-
  gated check for non-listed skills).
