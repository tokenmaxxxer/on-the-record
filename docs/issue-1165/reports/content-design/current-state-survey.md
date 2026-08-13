# issue-1165: content-design current-state survey (phase 1)

kind: survey
subject: issue-1165

## What exists today

- `roles/specs/content-design.spec.json` (canonical: read this turn)
  already cites `judgment_methodology` = NN/g's 10 Usability Heuristics
  and `planning_methodology` = Halvorson's content strategy quad — the
  exact methodology sources the issue asks this step to ground in
  already landed as this role's spec fields, not something to newly
  adopt.
- `docs/specs/ui-surfaces.md` (canonical: read this turn) declares this
  repo's own `## Globs` section as the literal `none` — on-the-record
  itself has no rendered screens. The screens this criterion governs
  are on **target projects** content-design produces copy/checklists
  for, consistent with `content-design.spec.json`'s existing
  `use_when.need_detector` (fires on target-project JSX/template string
  literals).
- `docs/issue-1156/proposals/per-role-quality-bars.md` (canonical: read
  this turn) landed the `quality_bar` machinery pattern this issue's
  requirement 1 asks the human-comprehensibility criterion to join:
  `{criterion, verification_method}` entries plus a named
  human-review-checklist form "where a domain's bar cannot be
  automated ... explicitly marked as such — never a silently lowered
  bar." Tier-2/tier-3 here reuse that same checklist shape rather than
  inventing a new one.
- No tier-checklist file for screens exists anywhere in the repo tree
  yet (derived: `find docs -iname "*tier*" -path "*content-design*"` —
  empty). This step originates the artifact, it does not revise one.
- This issue's own per-issue doc tree had no prior commits before this
  session (derived: `git log --all --oneline -- 'docs/issue-1165/*'` —
  empty before this commit).

## Gaps this step must close

- No screens-specific tier-1/tier-2/tier-3 operationalization exists
  anywhere in the repo — the issue's requirement 2 is greenfield for
  the screens surface (technical-writing owns the parallel
  document/record surface; write sets are disjoint, stated per the
  inline directive).
- `content-design.spec.json`'s `required_fields` (`content_id`,
  `user_need`, `plain_language_check`) and `write_scope` already bound
  where this role's output must live; this step's deliverables use
  those existing fields rather than inventing new ones.

## Scope for this step

Design only (northpole req#4 basis, `docs/specs/northpole.md`):
tier-2 new-user checklist for screens, tier-1 structural rules where
automatable, tier-3 sampled review protocol — grounded in the
already-landed NN/g heuristics + Halvorson sources. Folding this into
`gates/quality_bar.py` / the 7 landing-order role specs is step 2
(implementation), out of this step's write set.
