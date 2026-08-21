---
status: proposed
files:
  - skill-repository/skills/security-threat-model-threat-modeling-decision-rules/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Author procedural body for security-threat-model-threat-modeling-decision-rules

## Request

Issue #1945 asks for the single skill
`security-threat-model-threat-modeling-decision-rules` in
`tokenmaxxxer/skill-repository` to be authored per the WAVE RECIPE frozen
in #1790's record: insert `## Trigger` / `## Procedure` / `## Output
shape` at the top of the body, rewrite `description:` from the authored
Trigger text, extend `scripts/procedure_authored_skills.txt` with the
skill's name, keep every pre-existing rule line, and touch no other
family, no checker logic, no hooks. Delivered as a skill-repository PR
plus this record.

## Constraints

- Guidance-only: the frozen recipe is applied verbatim, not redesigned.
- Zero rule-line loss: every one of the 24 pre-change `**Rule ...**`
  headings (survey.md, "Rule inventory" section) must still be present,
  verbatim, after the edit.
- Write set is exactly the one skill's `SKILL.md` plus the manifest file
  — no other skill directory, no checker script, no hook.
- The manifest gets one line appended, not replaced (frozen recipe
  step 4) — the 9 pilot entries and any wave-2a entries already landed
  stay untouched.
- `description:` must keep a substring the checker's `TRIGGER_MARKERS`
  list recognizes (e.g. "use when") or the manifest check fails.
- This is a phase-1 proposal: no `CORE_BUILD_NOW=1` was set for this
  session, so this PR carries only the survey and this proposal: no
  skill-repository edit lands until a phase-2 Approve.

## Rationale

Two authoring shapes were available for the `## Trigger` section given
this family has only one skill (no sibling axes to differentiate
against, unlike the 9-skill pilot families where Trigger content
distinguished skills within the same family):

- **Rejected: restate the skill's title/description as the Trigger.**
  This is exactly the anti-pattern the frozen recipe warns against
  (step 2: "not a restatement of the title") and would produce a Trigger
  section that adds no information over the existing `description:`
  line — a no-op dressed as procedural content.
- **Chosen: differentiate against adjacent security/risk skills in the
  broader skill catalog** (`stride`, `fmea`, `risk-management-*`,
  `technical-feasibility-threat-model-disposition`), naming the concrete
  conditions (drawing a DFD, rating a specific threat, choosing a
  mitigation disposition, signing off residual risk) under which this
  skill's decision rules apply rather than a sibling's. This keeps the
  Trigger genuinely discriminating even in a single-skill family, and
  mirrors how the pilot skills' Triggers worked — separating *this*
  skill's applicability from neighboring but distinct skills, not just
  from an abstract "no skill" baseline.

No alternative recipe was considered for the section content/format
itself: the issue instructs verbatim reuse of the #1790 recipe, and the
survey found no reason (no existing partial procedural body, no
checker-logic mismatch) to deviate from it.

## What will be done

Phase 2 (after Approve) will, on branch `issue-1945-procedural-body` in
the `/tmp/skill-repository` checkout:
1. Insert `## Trigger` / `## Procedure` / `## Output shape` between the
   framing paragraph and the existing `## 1. Trust boundary scoping`
   heading in `SKILL.md`, with `## Procedure` steps citing rule numbers
   per the 6 existing axes.
2. Rewrite `description:` in the frontmatter from the new Trigger
   content, keeping a "use when"-style marker.
3. Append `security-threat-model-threat-modeling-decision-rules` to
   `scripts/procedure_authored_skills.txt`.
4. Run, and paste into `docs/issue-1945/reports/implementation.md`: the
   manifest checker (`--manifest scripts/procedure_authored_skills.txt`,
   expect exit 0), the rule-retention grep sweep against the survey's
   24-line baseline, `git diff --stat` scoped to the two write-set paths,
   and the full-tree checker with no flag (expect exit 0).
5. Open the skill-repository PR and record its number/commit here.

## Out of scope

- Any other skill or family (per the issue's non-goals).
- `scripts/check_skill_conformance.py` logic changes.
- Any hook change.
- Fixing the pre-existing `**Rule 5.6` numbering/placement quirk noted
  in the survey — it predates this wave and is not part of this
  request.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0.
- `python3 scripts/check_skill_conformance.py` (full tree, no flag)
  exits 0.
- The retention sweep shows all 24 pre-change rule lines still present,
  verbatim, post-change.
- `git diff --stat` against the skill-repository base shows only the two
  write-set paths.
- All four outputs pasted into the phase-2 record, executed live from
  the skill-repository checkout, per the issue's Acceptance criteria.
