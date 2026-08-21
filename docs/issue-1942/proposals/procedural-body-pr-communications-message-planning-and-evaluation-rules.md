---
status: proposed
files:
  - skill-repository/skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural body for pr-communications-message-planning-and-evaluation-rules

## Request

Author the single skill
`pr-communications-message-planning-and-evaluation-rules` in
`tokenmaxxxer/skill-repository` per the frozen wave recipe (docs/
issue-1790/reports/implementation.md, WAVE RECIPE section, from the #1790
pilot): insert `## Trigger` / `## Procedure` / `## Output shape` at the
top of the body (Procedure steps citing rule numbers), rewrite
`description:` from the authored Trigger section, extend
`scripts/procedure_authored_skills.txt` incrementally, with zero
pre-existing rule-line loss. Guidance-only wave; no checker-logic or
hook changes.

## Constraints

- Family-bounded: only this one skill's `SKILL.md` plus
  `scripts/procedure_authored_skills.txt` may be touched in the
  skill-repository PR (issue's own non-goals list: no other family, no
  checker-logic changes, no hooks).
- Every one of the 13 pre-existing numbered rule lines under `## Rules`
  (survey's Rule-retention baseline) must remain present, byte-identical,
  post-change.
- `description:` must keep a trigger-marker substring the checker relies
  on ("use when"), per the frozen recipe's step 3.
- The four checks from the #1790 pilot record repeat for this wave:
  manifest checker (exit 0), rule-retention sweep (13/13 retained),
  `git diff --stat` scoped to the two files above, full-tree checker
  (exit 0) — all executed live from the skill-repository checkout and
  pasted into the phase-2 record.

## Rationale

Considered following `performance-engineering-operational-playbook`'s
(issue #1937) axis-grouped, one-Procedure-step-per-axis pattern, since
this skill's own frontmatter already carries a 6-entry `axes:` list —
rejected because the survey's Body shape section found the body itself
is a flat numbered `## Rules` list with no layer/axis subheadings, unlike
performance-engineering's body which is structurally split into `## Layer
A/B/C`. Grouping the Procedure by the frontmatter's axes without a
matching body structure would require inventing subheadings the recipe
does not call for, purely to mirror a sibling skill whose body shape
differs from this one's. The survey's Pattern precedent instead found
`upstream-defect-report-comprehensibility` (#1790 pilot) — a flat
`## Rules`-list skill authored with one Procedure step per rule (or small
rule cluster) citing its own rule number(s) directly — a closer match to
this skill's actual body shape, so that per-rule-citing pattern is used
here instead.

Also considered dropping the three REMOVAL-marked rules (3, 10, 13) from
Procedure entirely and only covering them in Output shape as a caveat —
rejected because the pilot skills folded their own REMOVAL rules into
Procedure steps as ordinary steps (e.g. api-design-http-semantics rule
11-12), and treating REMOVAL rules as second-class in Procedure would
under-cite three of the skill's own 13 rules against the recipe's "each
Procedure step citing rule number(s)" requirement, risking a rule read as
orphaned relative to the navigational layer even though its text is
still retained verbatim in `## Rules`.

## What will be done

1. Insert `## Trigger` / `## Procedure` / `## Output shape` between the
   existing framing paragraph and `## Rules`, following
   `upstream-defect-report-comprehensibility`'s flat-list shape:
   - `## Trigger`: name the concrete conditions spanning the skill's six
     axes — choosing a channel before naming the audience (rule 1),
     structuring more than one core/supporting message (rules 2-3, 13),
     an unsupported or badly-sequenced persuasive claim (rules 4-6), a
     live-incident or Q&A-approval situation (rules 7-10), and defining
     or reporting success criteria (rules 11-12) — each clause citing its
     rule number(s).
   - `## Procedure`: one numbered step per rule or small adjacent rule
     cluster (13 rules -> steps grouped as roughly 1; 2-3; 4; 5; 6; 7; 8;
     9; 10; 11; 12; 13, adjusted during authoring if a tighter grouping
     reads more clearly), each step citing the rule number(s) it draws
     on, preserving the existing rule order.
   - `## Output shape`: what applying the skill produces — a cited
     condition -> choice -> source decision for the communications
     activity at hand, plus, where a REMOVAL-category rule applies, which
     item gets cut rather than added.
2. Rewrite `description:` as a single sentence derived from the authored
   Trigger section's opening clause, keeping "use when".
3. Append `pr-communications-message-planning-and-evaluation-rules` to
   `scripts/procedure_authored_skills.txt`.
4. Run, live, from `/tmp/skill-repository`: `check_skill_conformance.py
   --manifest scripts/procedure_authored_skills.txt` (expect exit 0);
   the rule-retention grep sweep (expect 13/13 lines retained); `git diff
   --stat` (expect only the two files above); the full-tree
   `check_skill_conformance.py` with no flag (expect exit 0). Paste all
   four outputs into `docs/issue-1942/reports/implementation.md`.
5. Open the skill-repository PR carrying this one skill's diff plus the
   manifest line, referencing issue #1942 (no Closes/Fixes trailer at
   this phase-1 stage).

## Out of scope

- Any other skill family (issue's own non-goals).
- `scripts/check_skill_conformance.py` logic changes (issue's own
  non-goals) — the manifest-gated check added in #1790 is reused as-is.
- Hooks (issue's own non-goals).
- Restructuring the existing flat `## Rules` list into axis-grouped
  subheadings (see Rationale) or touching `## Counter-example` /
  `## Open gap`.
- Rewording any existing rule's condition/choice/Source text — only new
  sections are inserted and `description:` is rewritten.

## How you'll know it worked

The four executed-live checks from `## What will be done` step 4 all
pass as specified (manifest checker exit 0, 13/13 rules retained, `git
diff --stat` showing only the skill's `SKILL.md` and the manifest file,
full-tree checker exit 0), pasted into the phase-2 record together with
the skill-repository PR link — matching issue #1942's Acceptance criteria
1 and 2 verbatim.
