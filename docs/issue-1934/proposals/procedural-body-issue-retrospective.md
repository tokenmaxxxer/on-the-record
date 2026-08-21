---
status: proposed
files:
  - /tmp/skill-repository/skills/issue-retrospective-timeline-comprehensibility-and-subtraction-rules/SKILL.md
  - /tmp/skill-repository/scripts/procedure_authored_skills.txt
---

## Request

Author the procedural body (`## Trigger` / `## Procedure` / `## Output
shape`) for the single skill
`issue-retrospective-timeline-comprehensibility-and-subtraction-rules` in
tokenmaxxxer/skill-repository, applying the WAVE RECIPE frozen in
docs/issue-1790/reports/implementation.md verbatim: insert the three
sections between the framing paragraph and `## Rules`, rewrite
`description:` from the authored Trigger, extend
`scripts/procedure_authored_skills.txt` with this skill's name, and run
the pilot's four checks (manifest checker, rule-retention sweep,
`git diff --stat` scoped to those two paths, full-tree checker) before
landing. Non-goals per the issue: any other family, checker logic
changes, hooks.

## Constraints

- Write set is exactly the two files listed in frontmatter — no path
  outside the skill body and the manifest gets touched (issue
  requirement 2).
- Every rule line present in the skill body before the change (15 rules,
  canonical: docs/issue-1934/reports/implementation/survey.md, "Target
  skill's current shape") must still be present, unchanged in content,
  after the change — the recipe adds sections, it does not edit rule
  text.
- `description:` must keep a checker trigger-marker substring ("Use
  when") — `scripts/check_skill_conformance.py`'s `TRIGGER_MARKERS` list
  requires it (canonical: /tmp/skill-repository/scripts/check_skill_conformance.py,
  read during survey).
- Both checker invocations (`--manifest scripts/procedure_authored_skills.txt`
  and the full-tree run with no flag) must exit 0 after the change.

## Rationale

Considered authoring a bespoke Trigger/Procedure/Output-shape shape for
this skill instead of mirroring the cross-family precedent
(`architecture-interface-contract-shape`, read in survey) — rejected
because the issue explicitly calls for applying the frozen recipe
"verbatim," and the recipe's own step 2 wording (concrete conditions,
ordered steps citing rule numbers, output-shape framing) is precedent-
derived from that same pilot family; diverging from the only available
worked example would reintroduce the per-skill judgment the recipe was
frozen specifically to remove across the wave.

Considered treating the single-skill family as exempt from the
"distinguish from sibling axes" language in recipe step 2 and skipping
`## Trigger` narrative distinction entirely — rejected because the
skill's own `axes:` frontmatter (convention, subtraction,
comprehensibility) shows it already carries three internal axes even
without sibling skills; a Trigger section can and should distinguish
this skill's records-only retrospective moment from adjacent record-
writing moments (e.g. mid-incident postmortem drafting) rather than
being omitted, keeping the wave's every-skill-gets-a-Trigger invariant
intact.

## What will be done

1. Read the skill body (already done in survey) and confirm no
   `## Trigger`/`## Procedure`/`## Output shape` headings exist yet —
   authoring applies, not a no-op.
2. Insert `## Trigger`, `## Procedure`, and `## Output shape` between the
   framing paragraph and `## Rules`: Trigger names the concrete moment
   (composing or reading a records-only cross-role retrospective for a
   subject issue); Procedure is an ordered list whose steps cite rule
   numbers from the existing 15-rule `## Rules` section (timeline-first
   drafting citing rule 1, structural-not-personal causal language
   citing rule 2, the 2-5-item contributing-factors cap citing rules 3/9,
   owned/impact-scoped action items citing rules 4/10/15, the fixed
   five-section layout citing rule 13, the two subtraction passes citing
   rules 8/9/10/11); Output shape names what the applied skill produces
   (a five-section retrospective record body: Timeline, Impact summary,
   Contributing factors, What we learned, Action items).
3. Rewrite `description:` as a sentence derived from the authored
   Trigger text, keeping the "Use when" trigger-marker substring.
4. Append `issue-retrospective-timeline-comprehensibility-and-subtraction-rules`
   to `scripts/procedure_authored_skills.txt`.
5. Run, from the skill-repository checkout, and paste into the phase-2
   record: `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), the
   rule-retention sweep (grep/diff confirming all 15 pre-change rule
   lines survive), `git diff --stat` scoped to the two write-set paths,
   and `python3 scripts/check_skill_conformance.py` with no flag (expect
   exit 0).
6. Open the skill-repository PR carrying only those two paths' diff, and
   record the four pasted check outputs plus the `git diff --stat` output
   in `docs/issue-1934/reports/implementation.md` (phase 2, after
   Approve).

## Out of scope

- Any other skill or family (the issue is single-skill scope).
- Any change to `scripts/check_skill_conformance.py` or
  `scripts/normalize_skill_frontmatter.py` (checker logic is frozen for
  this wave).
- Any hook change in either repository.
- Editing existing rule text/wording in the target skill's `## Rules`
  section — only additive sections and the manifest line are in scope.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0 from the skill-repository
  checkout, with the target skill included in the manifest.
- `python3 scripts/check_skill_conformance.py` (full tree, no flag) exits
  0.
- A rule-retention sweep shows all 15 pre-change rule lines
  (canonical: docs/issue-1934/reports/implementation/survey.md) present,
  verbatim, post-change.
- `git diff --stat` in the skill-repository checkout shows changes to
  exactly the two write-set paths and no others.
