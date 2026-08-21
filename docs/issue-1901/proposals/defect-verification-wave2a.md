---
status: proposed
files:
  - skill-repository:skills/defect-verification-reproduction-evidence-quality/SKILL.md
  - skill-repository:skills/defect-verification-independence-from-upstream-verdicts/SKILL.md
  - skill-repository:skills/defect-verification-severity-band-assignment/SKILL.md
  - skill-repository:skills/defect-verification-evidence-artifact-completeness/SKILL.md
  - skill-repository:scripts/procedure_authored_skills.txt
  - docs/issue-1901/reports/implementation.md
---

## Request

Author `## Trigger` / `## Procedure` / `## Output shape` sections onto the defect-verification skill family (4 skills) in `tokenmaxxxer/skill-repository`, per the WAVE RECIPE frozen in docs/issue-1790/reports/implementation.md, and append the 4 skill directory names to `scripts/procedure_authored_skills.txt`. Deliver as a skill-repository PR plus a record in this repo, repeating the pilot's four checks (manifest checker exit 0, rule-retention sweep with zero rule-line loss, scoped `git diff --stat`, full-tree checker exit 0).

## Constraints

- Apply the frozen recipe verbatim (docs/issue-1790/reports/implementation.md `## WAVE RECIPE`) — no checker-logic changes, no hooks, no other family touched (issue #1901 non-goals).
- Write set bounded to the 4 defect-verification SKILL.md files + `scripts/procedure_authored_skills.txt` in skill-repository, plus this repo's own `docs/issue-1901/` tree — nothing else in the skill-repository PR.
- Zero rule-line loss: every pre-change numbered rule line in each of the 4 files' `## Rules` section must survive unchanged into the post-change body.
- Phase-2 must re-fetch `origin/main` in `/tmp/skill-repository` before editing (survey found the local checkout one wave ahead of `origin/main`; canonical: docs/issue-1901/reports/implementation/survey.md, "Skill-repository checkout state" section).

## Rationale

**Chosen approach:** reuse the #1790 pilot recipe unmodified, applying it to all 4 skills in one wave (mirroring how #1892 and #1884 each did one wave per family), and adopt the check-command wording refinements #1892 introduced (checks 2 and 4) rather than #1790's original wording.

**Alternative considered and rejected — re-derive the recipe from scratch for this family:** the defect-verification family's skills follow the same `## Rules`-only body shape the survey found in every skill examined (no headings, `description:` in the same "Use when you need guidance on X" template) as the families #1790, #1884, and #1892 already authored. canonical: docs/issue-1901/reports/implementation/survey.md, per-skill findings table. Re-deriving Trigger/Procedure/Output-shape conventions independently for this family would produce a structurally different result across the corpus with no compensating benefit, and the issue explicitly asks for the frozen recipe applied verbatim — rejected.

**Alternative considered and rejected — use #1790's original check wording instead of #1892's refined wording:** #1790's rule-retention sweep used ad hoc 50-char-substring grepping and its diff scoping used `git diff --stat --cached` (a local staged-snapshot view). #1892's record shows both were tightened to a `git show origin/main:<path>` per-file comparison (sweep) and `git diff --stat origin/main..HEAD -- .` (a real-upstream-scoped diff) after #1892 hit a staleness problem the `--cached` form didn't catch. canonical: docs/issue-1892/reports/implementation.md `## Rationale for deviations`. Since this survey independently found the local skill-repository checkout is already one wave ahead of `origin/main` (same staleness shape), reusing #1790's less-robust wording was rejected in favor of #1892's.

## What will be done

1. Phase-2 (post-approval): in `/tmp/skill-repository`, fetch and rebase/re-check `origin/main`, then for each of the 4 defect-verification skills: insert `## Trigger` / `## Procedure` / `## Output shape` between the framing paragraph and `## Rules`, with Procedure steps citing that skill's existing rule numbers; rewrite `description:` from the authored Trigger, keeping the "use when" substring; leave every `## Rules` line unchanged.
2. Append the 4 skill directory names to `scripts/procedure_authored_skills.txt`.
3. Run, in order: manifest checker (`--manifest scripts/procedure_authored_skills.txt`), full-tree checker (no flag), rule-retention sweep (`git show origin/main:<path>` vs. working tree, filtered to numbered rule lines + `source:` counts), and scoped `git diff --stat origin/main..HEAD -- .` — paste all four outputs into this repo's `docs/issue-1901/reports/implementation.md`.
4. Open the skill-repository PR carrying only the 5 file changes listed in this proposal's `files:` frontmatter (skill-repository side), and land the phase-2 record in this repo's PR.

## Out of scope

- Any family other than defect-verification (per issue #1901 non-goals).
- Checker logic changes or hooks changes (per issue #1901 non-goals).
- Re-deriving or altering the WAVE RECIPE itself.
- Wave partitioning/sequencing decisions for families beyond this one (owned by the #1790 record's "Proposed wave partition" section, not this issue).

## How you'll know it worked

- The four checks from phase-2 step 3 all pasted into `docs/issue-1901/reports/implementation.md`, each showing: manifest checker exit 0, full-tree checker exit 0 ("234 skills checked" baseline plus the 4 newly authored), rule-retention sweep reporting zero missing rule lines across all 4 files, and `git diff --stat origin/main..HEAD -- .` listing exactly the 4 SKILL.md paths + `scripts/procedure_authored_skills.txt`.
- No path outside those 5 appears in the skill-repository PR's diff.
