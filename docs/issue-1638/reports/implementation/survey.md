# issue-1638 survey: quality_bar batch 2

## Write set (frozen)
- roles/specs/content-design.spec.json
- roles/specs/brand-design.spec.json
- roles/specs/technical-writing.spec.json
- roles/specs/pr-communications.spec.json
- roles/specs/devrel.spec.json
- roles/specs/localization.spec.json
- roles/specs/knowledge-management.spec.json
- roles/specs/user-discovery.spec.json
- gates/spec_schema_five_activities_test.py

## Family chosen
Content/design/communication family (8 roles), per §7 of
docs/issue-1156/proposals/per-role-quality-bars.md: content-design,
brand-design, technical-writing, pr-communications, devrel,
localization, knowledge-management, user-discovery. Each already has a
`source_standard` field naming its domain standard (read directly from
each spec, canonical). None currently carries `quality_bar` (checked:
`'quality_bar' in d` is `False` for all 8).

## Precedent shape (from landed batch-1 specs, e.g. data-modeling,
data-engineering)
Each `quality_bar` entry: `{criterion, verification_method,
evidence_grade, verified_source}` (verified_source is a URL-cited
primary source restating/correcting the claim), except a final
`human_comprehensibility_verdict` entry (no evidence_grade/
verified_source) that all landed roles share verbatim, referencing the
`human_comprehensibility_verdict` function in gates/quality_bar.py
(issue #1623).
`loop_state.refusal` gains `"bar-not-met"` appended to the existing
refusal list.

## Test boundary
`gates/spec_schema_five_activities_test.py`:
- `QUALITY_BAR_ROLES` list (currently 13 roles) gets the 8 new roles
  appended.
- `test_no_other_spec_carries_a_quality_bar_yet` iterates
  `ALL_ROLE_SPECS` (all 43 specs) and asserts specs outside
  `QUALITY_BAR_ROLES` carry no `quality_bar` key — stays green
  automatically once the 8 new roles are added to the list, since they
  will then carry `quality_bar` and be excluded from the check.
- No other spec files are touched, so byte-identity for the remaining
  22 non-batch roles holds without extra work.

## Skip condition
None — this is genuine per-criterion decomposition work requiring
domain judgment against each role's cited source_standard (scout
already ran system-wide in #1156; this batch operationalizes 8 of its
already-scouted domains at data.model-level depth, so no new scout
sweep is needed here beyond re-reading the cited sources for
criterion-writing accuracy).
