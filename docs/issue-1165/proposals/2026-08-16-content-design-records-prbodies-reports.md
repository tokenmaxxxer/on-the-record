---
status: approved
files:
  - docs/issue-1165/reports/content-design/2026-08-16-current-state-survey-records.md
  - docs/issue-1165/reports/content-design/2026-08-16-scout-brief-records.md
  - docs/issue-1165/reports/content-design.md
---

# issue-1165 (content-design, step 1 round 2): human-facing shape of records/PR bodies/reports

kind: proposal
subject: issue-1165

Proposal: docs/issue-1165/proposals/2026-08-16-content-design-records-prbodies-reports.md

Decision: work one grain finer than technical-writing's already-landed
paragraph-level `lead_paragraph_present` rule -> a design decision
targeting sentence/clause-level citation placement inside a record's
lead prose, because the current-state survey's real specimen
(docs/issue-587/reports/implementation.md lines 15-22) shows a citation
tag splitting the point-stating sentence itself, a defect the
paragraph-existence rule cannot detect.

Approval note: the issue thread carries the exact single-account
approval string `APPROVE issue-1165/content-design` (posted
2026-08-15T15:40:43Z, account `JiwonJung94`, a `docs/specs/approvers.md`
account) after this round's 2026-08-16 research-brief comment
(2026-08-15T15:40:30Z) and before this PR's creation, so this proposal
files already `status: approved`, same precedent as this role's step-1
round-1 proposal (`docs/issue-1165/proposals/content-design-screens-comprehensibility.md`).

## Intent

Step 1 round 2 (parallel with technical-writing): design, from the
content-design lens, the human-facing shape of records/PR bodies/
reports for the universal `human_comprehensibility` criterion —
lead-with-the-point template shape, enumeration/section bounds, and
what the new-reader test looks like on this repo's own real record
forms — reconciled with required-field record contracts. Design/spec
only, per this turn's own invocation; no gate implementation.

Basis: the issue body's requirement 2 (tier split) and requirement 4
(anti-nitpick bound); the 2026-08-16 research brief (issue #1165
comment, 2026-08-15T15:40:30Z); this round's current-state survey and
scout brief (both filed alongside this proposal).

## Constraints stated so far

- Write set stays inside this role's `write_scope`
  (`docs/issue-<n>/reports/content-design.md`,
  `docs/issue-<n>/reports/content-design/*.md`) — no edits to
  `gates/quality_bar.py`, `record-scaffold.sh`, or `pr_reference.py`;
  wiring is step 2 (implementation).
- Must reconcile with, not fight, the required-field record contracts:
  `roles/specs/*.spec.json` `required_fields` and this role's own
  `content-design.spec.json` `required_fields`
  (`content_id`, `user_need`, `plain_language_check`) stay untouched —
  the template shape below governs the PROSE sections around those
  fields, never the fields themselves.
- Disjoint from technical-writing's parallel round-2 deliverable (the
  document-genre/paragraph-level design); this round works one grain
  finer, per the Decision line above.
- Tier-2/tier-3 verdicts must name the failing item and the passing
  shape (issue requirement 4), same discipline as round 1.

## What will be done

`docs/issue-1165/reports/content-design.md` gains a new dated section
(this round) stating:

1. **Lead-with-the-point template shape for records**, applied to
   `record-scaffold.sh`'s own section order (survey above): a lead
   paragraph slot before `## Summary of work` restating what/why/
   so-what in plain prose, with any `canonical:`/citation tag placed
   as a trailing clause or its own line — never interleaved inside the
   point-stating sentence, per this round's specimen finding.
2. **Enumeration/section bounds**: reuse technical-writing's
   already-landed structural-cap shape (issue requirement 2's
   "consecutive unstructured enumeration cap") applied to record
   sections specifically — a record section without a sub-heading stays
   under a stated line bound before it must break into named
   sub-sections (mirrors this role's own tier-1 screen rule 4, "no
   raw-context dumps", one surface over).
3. **New-reader test on this repo's real record forms** — demonstrated,
   not just described, against `docs/issue-587/reports/implementation.md`
   in the current-state survey above: one pass over the lead section,
   name what changed / why / what's next, flag any sentence a citation
   tag splits.
4. **PR-body spec** (added per PR #1616 blocking review comment,
   2026-08-15T15:53:19Z): apply lead-with-the-point to PR body prose
   itself, not just the gap-naming this round originally stopped at.
   `gates/pr_reference.py`'s `check_body` (function at line 29) checks
   only a phase-appropriate issue-reference trailer (`#<n>` phase-1,
   `Closes/Fixes/Resolves #<n>` phase-2); this item adds the
   content-structure design on top, still design/spec only:
   - **First-paragraph shape.** A PR body's first paragraph states the
     change, why, and what happens next (what the merge unblocks or
     what phase-2 will do), before any trailer line (`Part of #<n>`,
     `Closes #<n>`, the sandbox-relay disclosure line, etc.). Structural
     check (automatable): the first blank-line-delimited paragraph
     contains at least one clause matching a what-changed shape and one
     matching a why/next shape; a body whose first paragraph is only a
     trailer line fails.
   - **Citation-trailing placement.** Same clause-placement rule as
     item 1 above, applied to PR body prose: any `canonical:`-style or
     link-shaped citation inside the first paragraph sits as a trailing
     clause or its own line, never splitting the point-stating
     sentence — reuses this round's already-stated citation-not-
     mid-sentence structural check verbatim, one surface over.
   - **Bounds.** The first paragraph stays within the same section-size
     line bound named in item 2 above (left as the same step-2
     tunable — no separate number chosen for PR bodies this round);
     trailer lines (issue reference, phase disclosure, sandbox-relay
     note) are exempt from the paragraph bound since they are
     machine-checked fields, not prose.
   - Still names, not fixes, the gap: `check_body` gains no new
     structure check this round — wiring is step 2, unchanged from this
     round's own scope guard.
5. **Reconciliation statement** — the template shape governs prose
   framing only; `required_fields` frontmatter keys are unaffected and
   remain governed by each role's own `*.spec.json`.

## Out of scope

- Wiring into `gates/quality_bar.py`, `record-scaffold.sh`, or
  `pr_reference.py` — step 2 (implementation).
- The document-genre/paragraph-level design (technical-writing's
  parallel round-2 deliverable).
- Screens/UI (round 1's already-landed scope, unchanged this round).

## How you will know it worked

- The phase-2 record's new section states the citation-placement rule
  as a structural check (checkable without subjective judgment, same
  automatable framing as round 1's tier-1 rules).
- The new-reader test is shown run against a real landed record, not
  only described abstractly (per this session's invocation wording).
- The reconciliation statement names which required-field contract
  stays untouched and why, closing issue requirement 3's scope guard
  for this surface.
