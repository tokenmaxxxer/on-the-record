---
status: proposed
files:
  - skill-repository:skills/devrel-channel-convention/SKILL.md
  - skill-repository:skills/devrel-program-subtraction/SKILL.md
  - skill-repository:skills/devrel-content-comprehensibility/SKILL.md
  - skill-repository:scripts/procedure_authored_skills.txt
  - docs/issue-1911/reports/implementation.md
---

## Request

Author `## Trigger` / `## Procedure` / `## Output shape` sections onto the
devrel skill family (3 skills) in `tokenmaxxxer/skill-repository`, per the
WAVE RECIPE frozen in docs/issue-1790/reports/implementation.md, and append
the 3 skill directory names to `scripts/procedure_authored_skills.txt`.
Deliver as a skill-repository PR plus a record in this repo, repeating the
pilot's four checks (manifest checker exit 0, rule-retention sweep with
zero rule-line loss, scoped `git diff --stat`, full-tree checker exit 0).

## Constraints

- Apply the frozen recipe verbatim (docs/issue-1790/reports/implementation.md
  `## WAVE RECIPE`) — no checker-logic changes, no hooks, no other family
  touched (issue #1911 non-goals).
- Write set bounded to the 3 devrel SKILL.md files +
  `scripts/procedure_authored_skills.txt` in skill-repository, plus this
  repo's own `docs/issue-1911/` tree — nothing else in the skill-repository
  PR.
- Zero rule-line loss: every pre-change numbered rule line in each of the 3
  files' `## Rules` section must survive unchanged into the post-change
  body.
- Phase-2 works from the fresh clone already made for this issue at
  `/tmp/skill-repository-1911` (branch `issue-1911-wave2a-devrel`), which
  this survey confirmed is at `origin/main` HEAD (`d110b90`) — no
  rebase/re-fetch step needed, unlike #1901 which found its shared checkout
  stale. canonical: docs/issue-1911/reports/implementation/survey.md,
  "Skill-repository checkout state" section.

## Rationale

**Chosen approach:** reuse the #1790 pilot recipe unmodified, applying it
to all 3 skills in one wave (mirroring how #1892, #1884, and #1901 each did
one wave per family), and adopt #1892's check-command wording refinements
(the same refinements #1901 already adopted) for the rule-retention sweep
and diff-scoping commands rather than #1790's original wording.

**Alternative considered and rejected — re-derive the recipe from scratch
for this family:** the devrel family's 3 skills follow the same
`## Rules`-only body shape the survey found in every skill examined (no
existing headings, `description:` in the same "Use when you need guidance
on X" template) as the families #1790, #1884, #1892, and #1901 already
authored. canonical: docs/issue-1911/reports/implementation/survey.md,
per-skill findings table. Re-deriving Trigger/Procedure/Output-shape
conventions independently for this family would produce a structurally
different result across the corpus with no compensating benefit, and the
issue explicitly asks for the frozen recipe applied verbatim — rejected.

**Alternative considered and rejected — reuse the shared `/tmp/skill-repository`
checkout instead of a fresh per-issue clone:** the survey found that
checkout dirty (uncommitted changes from an unrelated in-flight issue,
wrong branch checked out) rather than merely stale. canonical:
docs/issue-1911/reports/implementation/survey.md, "Skill-repository
checkout state" section (citing the observed dirty/wrong-branch state
before the fresh clone was made). Editing on top of another issue's
uncommitted work risks cross-contaminating the diff and violating the
single-family write-set constraint; a fresh dedicated clone avoids both the
dirty-tree risk and the staleness class #1901 hit — rejected.

## What will be done

1. Phase-2 (post-approval): in `/tmp/skill-repository-1911`, for each of
   the 3 devrel skills: insert `## Trigger` / `## Procedure` / `## Output
   shape` between the framing paragraph and `## Rules`, with Procedure
   steps citing that skill's existing rule numbers; rewrite `description:`
   from the authored Trigger, keeping the "use when" substring; leave every
   `## Rules` line unchanged.
2. Append the 3 skill directory names to `scripts/procedure_authored_skills.txt`.
3. Run, in order: manifest checker (`--manifest
   scripts/procedure_authored_skills.txt`), full-tree checker (no flag),
   rule-retention sweep (`git show origin/main:<path>` vs. working tree,
   filtered to numbered rule lines + `source:` counts), and scoped `git
   diff --stat origin/main..HEAD -- .` — paste all four outputs into this
   repo's `docs/issue-1911/reports/implementation.md`.
4. Open the skill-repository PR carrying only the 4 file changes listed in
   this proposal's `files:` frontmatter (skill-repository side), and land
   the phase-2 record in this repo's PR.

## Out of scope

- Any family other than devrel (per issue #1911 non-goals).
- Checker logic changes or hooks changes (per issue #1911 non-goals).
- Re-deriving or altering the WAVE RECIPE itself.
- Wave partitioning/sequencing decisions for families beyond this one
  (owned by the #1790 record's "Proposed wave partition" section, not this
  issue).
- Correcting the issue body's stale "10 skills" opening-line figure (flagged
  in the survey; not a write-set change).

## How you'll know it worked

- The four checks from phase-2 step 3 all pasted into
  `docs/issue-1911/reports/implementation.md`, each showing: manifest
  checker exit 0, full-tree checker exit 0 (baseline 234 skills plus the 3
  newly authored), rule-retention sweep reporting zero missing rule lines
  across all 3 files, and `git diff --stat origin/main..HEAD -- .` listing
  exactly the 3 SKILL.md paths + `scripts/procedure_authored_skills.txt`.
- No path outside those 4 appears in the skill-repository PR's diff.
