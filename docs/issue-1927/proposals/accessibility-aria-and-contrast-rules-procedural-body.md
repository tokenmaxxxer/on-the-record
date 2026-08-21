---
status: proposed
files:
  - skill-repository/skills/accessibility-aria-and-contrast-rules/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

## Request

Author a procedural body for the single-skill family
`accessibility-aria-and-contrast-rules` in `tokenmaxxxer/skill-repository`,
applying the WAVE RECIPE frozen in the #1790 pilot record verbatim: add
`## Trigger` / `## Procedure` / `## Output shape` sections citing rule
numbers, rewrite `description:` from the authored Trigger, extend
`scripts/procedure_authored_skills.txt` with this skill's name, retain
every pre-existing rule line, and deliver as a skill-repository PR plus
this record.

## Constraints

- Frozen recipe only — no deviation in shape, no checker-logic changes,
  no other family touched (issue's own non-goals).
- Zero rule-line loss: every one of the 15 pre-change numbered rule
  lines (survey.md, "Rule inventory") must be verified present
  post-change by a retention sweep before landing.
- Diff scope for the delivery PR: only the skill's `SKILL.md` and
  `scripts/procedure_authored_skills.txt` (issue Acceptance #2).
- Four checks required at delivery time, executed live: manifest-scoped
  checker run (exit 0), rule-retention sweep, `git diff --stat` scoped
  to those two paths, full-tree checker run (exit 0) — same shape as the
  #1790 pilot's own four checks.
- `scripts/procedure_authored_skills.txt` is extended incrementally
  (append this skill's name), never rewritten or reordered.

## Rationale

Considered authoring the procedural body directly on top of the
currently-checked-out `/tmp/skill-repository` tree (branch
`issue-1906-wave2a-data-modeling`, carrying an unrelated uncommitted
diff per survey.md's "Checkout state" section) and rejected it: landing
this family's PR from that tree risks folding an unrelated,
already-flagged-as-artifact diff on `scripts/procedure_authored_skills.txt`
into this family's commit, which would violate Acceptance #2's
path-scoping requirement. The delivery step will instead branch from a
fresh clone or worktree off `origin/main`, keeping the write set
identical to the two paths listed above.

Considered inventing a new authoring pattern specific to this family
(e.g. grouping Procedure steps by rule section rather than citing
individual rule numbers) and rejected it: the issue explicitly calls
for applying the #1790 recipe verbatim, and this skill's existing
`## 1`–`## 5` numbered-rule structure maps directly onto the recipe's
per-rule citation approach with no structural mismatch to justify a
variant.

## What will be done

1. Confirm (already done in survey.md) that no
   `## Trigger`/`## Procedure`/`## Output shape` heading exists yet —
   this is a live edit, not a no-op.
2. Insert `## Trigger` (concrete conditions distinguishing ARIA-role,
   naming, contrast, and focus decisions from adjacent skills — not a
   restatement of the title), `## Procedure` (ordered steps, each citing
   the rule number(s) from `## 1`–`## 5` it draws on), and
   `## Output shape` (what applying this skill produces — e.g. a
   role/naming/contrast/focus decision with its rule citation and
   source) between the framing paragraph and `## 1. ARIA role
   selection`.
3. Rewrite `description:` as a sentence derived from the authored
   Trigger content, keeping the checker's trigger-marker substring
   ("use when").
4. Append `accessibility-aria-and-contrast-rules` to
   `scripts/procedure_authored_skills.txt`.
5. Run the rule-retention sweep (pre-change rule lines vs. post-change
   file), the manifest-scoped checker run, `git diff --stat` scoped to
   the two write-set paths, and the full-tree checker run — all four
   executed live from the skill-repository checkout, output pasted into
   this issue's phase-2 record.
6. Open the skill-repository PR carrying the two-file diff; reference it
   from `docs/issue-1927/reports/implementation.md`.

## Out of scope

- Any family other than `accessibility-aria-and-contrast-rules`.
- Changes to `scripts/check_skill_conformance.py` or any other checker
  logic.
- Hook changes.
- Resolving the skill body's existing "Open gap" note (roving-tabindex
  vs. `tabindex` pattern) — that note is carried through verbatim, not
  authored into a new rule.

## How you'll know it worked

- The manifest-scoped checker run and the full-tree checker run both
  exit 0.
- The rule-retention sweep shows all 15 pre-change rule lines present
  post-change.
- `git diff --stat` shows only `skills/accessibility-aria-and-contrast-rules/SKILL.md`
  and `scripts/procedure_authored_skills.txt` changed.
- All four outputs are pasted into `docs/issue-1927/reports/implementation.md`
  once phase 2 opens.
