kind: survey
subject: issue-1165

# issue-1165 (technical-writing) — current-state survey

## What exists today

- `gates/quality_bar.py` (canonical, read this turn): a pure classifier
  (`classify(bar_scoped, verdict, record_author_account,
  producer_account, consecutive_bar_not_met_count)` →
  `BAR_MET|BAR_NOT_MET|ESCALATE|NO_BAR_SCOPED`) landed by #1156.
  Anti-circularity is structural: record author account and producing
  account must differ. `REJECT_CAP = 3` bounds the rejection loop before
  `ESCALATE`. It has no concept of criteria content yet — criteria live
  in each role's `roles/specs/<role>.spec.json` `quality_bar` array as
  the phase-1 design already landed by `docs/issue-1156/proposals/
  per-role-quality-bars.md`.
- That proposal's decomposition shape (canonical: `docs/issue-1156/
  proposals/per-role-quality-bars.md` §0, read this turn) is the pattern
  #1165 must reuse for `human_comprehensibility`: each criterion is
  `{criterion, verification_method}`; non-automatable criteria get
  `verification_method: human-review-checklist` with the checklist
  question stated, never a silently-lowered bar; every criterion traces
  to a role's own already-cited `source_standard`.
- `roles/specs/technical-writing.spec.json` (canonical, read this turn):
  `source_standard: "Diataxis, https://diataxis.fr/"`. `required_fields`
  today: `doc_id` (ref), `quadrant` (enum: tutorial/how-to/reference/
  explanation), `content` (string). No `quality_bar` array exists yet on
  this spec — #1156 did not decompose technical-writing (it scoped the 7
  landing-order roles + a domain-only stub for the remaining 36;
  technical-writing was one of the 36).
- `on-the-record/hooks/record-scaffold.sh` (canonical, read this turn):
  scaffolds `docs/issue-<n>/reports/<role>.md` frontmatter from a role's
  declared record fields, plus a fixed body shape: `## Summary of work`,
  `## Why`, `## What did not work`, `## Open findings`, `## Next steps`,
  `## Resolution path`. This body shape already leads with a Summary
  section before rationale/detail — but nothing today bounds section
  size, caps consecutive enumeration, or requires the summary itself to
  state what/why/so-what in a lead sentence rather than restating the
  diff.
- `on-the-record/hooks/report-framing-check.sh` (canonical, read this
  turn): a Stop hook that regex-matches an orchestrator's PR/board
  report reply for four framing elements (resolved problem, prior cost,
  newly possible, still broken). This is the closest existing mechanism
  to a "new reader can state what changed/why/what's next" check, but it
  runs on the orchestrator's chat reply, not on record *files*, and it is
  keyword-regex, not a structural rule (no lead-summary-first check, no
  enumeration cap, no section-size bound).
- `gates/record_lint.py` (via `record-claim-guard.sh`) checks *citation*
  shape (bare counts, unverifiable escapes, canonical tags) — orthogonal
  to comprehensibility structure; it does not check whether a section is
  legible, only whether a claim in it is sourced.
- No existing gate anywhere in `gates/` or `on-the-record/hooks/` checks:
  lead-with-the-point ordering, section-size bounds, or a cap on
  consecutive unstructured enumeration. This is the actual gap #1165
  step (a) (quality_bar machinery gaining `human_comprehensibility`)
  must fill — my assignment (technical-writing, step 1) is the
  document-side design of that criterion; #1156's per-role
  `verification_method` pattern is the mechanism it should be expressed
  through once landed.

## Reconciliation surface (issue requirement 3)

Required-field record contracts (`roles/specs/*.spec.json`
`required_fields`, enforced by `record-scaffold.sh` + `record_lint.py`)
and structure rules operate on different axes and do not collide by
construction: required fields are a *presence* contract (is the field
there, does it resolve, is its enum value valid); structure rules are a
*prose-shape* contract that applies only inside the human-facing prose
sections a required field carries as free text (e.g. `content` on
technical-writing, `## Summary of work`/`## Why` on any role's delivery
record) — never to the field list itself, frontmatter, or structured
fields like `doc_id`/`quadrant`/`code_under_review` (a path list, not
prose). §2 of the proposal below states this explicitly per-field.
