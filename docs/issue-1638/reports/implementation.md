---
code_under_review:
  - roles/specs/content-design.spec.json
  - roles/specs/brand-design.spec.json
  - roles/specs/technical-writing.spec.json
  - roles/specs/pr-communications.spec.json
  - roles/specs/devrel.spec.json
  - roles/specs/localization.spec.json
  - roles/specs/knowledge-management.spec.json
  - roles/specs/user-discovery.spec.json
  - gates/spec_schema_five_activities_test.py
  - docs/issue-1638/proposals/quality-bar-batch-2.md
type: feature
breaking: false
verdict: bar-met
loop_state: landed
---

## What was done

canonical: `docs/issue-1638/proposals/quality-bar-batch-2.md` read directly on this branch, frontmatter `status: proposed`, body's `files:` list.

Implemented the approved phase-1 proposal exactly: each of the 8
content/design/communication family specs (content-design, brand-design,
technical-writing, pr-communications, devrel, localization,
knowledge-management, user-discovery) got a `quality_bar` array of 4-5
criteria decomposed from that spec's own `source_standard`, each entry
carrying `criterion`, `verification_method`, `evidence_grade`,
`verified_source`; a shared trailing `human_comprehensibility_verdict`
entry identical to the one already used by all 13 landed roles; and
`"bar-not-met"` appended to `loop_state.refusal`. Non-automatable
criteria use a `human-review-checklist: <question>` verification_method,
per the proposal's own §0-derived rule. `devrel`'s and one
`user-discovery` criterion use `evidence_grade: "practitioner-consensus"`
/ `"practitioner-consensus (contested framing)"` (existing vocabulary
already used elsewhere in `roles/specs/*.spec.json`, canonical: `grep -rn evidence_grade roles/specs/*.spec.json` output showing those exact strings already in use), matching those two
specs' own `source_standard` fields, which already state their sources
are convergent practice / an explicit extension, not a ratified
standard.

`QUALITY_BAR_ROLES` in `gates/spec_schema_five_activities_test.py` got
the 8 role names appended under a new `# issue #1638 batch 2
(content/design/communication family)` comment, matching the existing
batch-1 comment pattern. The file's two stale `36`-count comments
(predating batch-1's landing) were corrected to `22`, since 43 total
specs minus the now 21 `QUALITY_BAR_ROLES` is 22.

Fixed the arithmetic typo in the proposal doc's "How you'll know it
worked" section: "35 non-batch roles" corrected to "22" (43 total minus
21 `QUALITY_BAR_ROLES` is 22, not 35).

## Why

canonical: `gh issue view 1638` output this turn — issue text requests batch-2 decomposition per the phase-1 proposal approved and merged as PR #1640.

Phase-1 proposal for issue #1638 was approved; phase-2 delivers exactly
what it committed to, per the role-handoff contract's two-phase flow.

## Upstream basis

docs/issue-1638/proposals/quality-bar-batch-2.md

## Test run

canonical: `python3 -m pytest gates/spec_schema_five_activities_test.py -q`, executed this turn.
derived: `python3 -m pytest gates/spec_schema_five_activities_test.py -q`
```
........                                                                 [100%]
8 passed in 0.86s
```
canonical: `python3 -m pytest gates/spec_schema_five_activities_test.py -q` (executed this turn, output immediately above) — all 8 collected tests pass, including
`test_every_quality_bar_role_has_nonempty_quality_bar_array`,
`test_every_quality_bar_role_has_bar_not_met_refusal_state`, and
`test_no_other_spec_carries_a_quality_bar_yet` (the boundary test,
green for the remaining 22 non-batch roles since only the 9 files in
the frozen write set were touched).

canonical: `python3 -c "import json; json.load(open(...))"` loop, executed this turn.
derived: `for f in content-design brand-design technical-writing pr-communications devrel localization knowledge-management user-discovery; do python3 -c "import json; json.load(open('roles/specs/$f.spec.json'))" && echo "$f OK"; done`
```
content-design OK
brand-design OK
technical-writing OK
pr-communications OK
devrel OK
localization OK
knowledge-management OK
user-discovery OK
```
canonical: `python3 -c "import json; json.load(open(...))"` loop (executed this turn, output immediately above) — all 8 edited spec files parsed clean as valid JSON.

Test-tier note: no `.on-the-record/test-tiers.json` exists at repo root
(checked this turn: `cat .on-the-record/test-tiers.json` -> "그런 파일이나
디렉터리가 없습니다" / no such file), so no fast/slow tiering applies; only
the single test file named by the task and the proposal's own "How
you'll know it worked" section was run, matching the frozen write set's
scope.

## What did not work

None — no edit was written then undone or replaced during this session.

## Open findings

None open at delivery.

## closed_checks

- check: JSON validity of all 8 edited spec files (canonical: `python3 -c "import json; json.load(open(...))"` loop, executed this turn, output above) — code_under_review: roles/specs/content-design.spec.json, roles/specs/brand-design.spec.json, roles/specs/technical-writing.spec.json, roles/specs/pr-communications.spec.json, roles/specs/devrel.spec.json, roles/specs/localization.spec.json, roles/specs/knowledge-management.spec.json, roles/specs/user-discovery.spec.json
- check: `gates/spec_schema_five_activities_test.py` pytest run (canonical: `python3 -m pytest gates/spec_schema_five_activities_test.py -q`, executed this turn, output above, 8 collected, 8 passed) — code_under_review: gates/spec_schema_five_activities_test.py

## Amendment (PR #1645 review)

canonical: `gh pr view 1645 --comments` output this turn — reviewer flagged `roles/specs/brand-design.spec.json` `quality_bar` entries 3-4 (`clear_space_and_minimum_size_stated_numerically`, `correct_and_incorrect_usage_examples_present`) as claiming `evidence_grade: "validated"` with a `verified_source` naming no checkable primary/practitioner source and no trace to the spec's `source_standard` (DTCG, which covers token format only, not logo-usage rules).

Fixed: downgraded both entries' `evidence_grade` to `"practitioner-consensus"` and rewrote `verified_source` to state the gap explicitly (no specific practitioner document cited; the numeric-value and correct/incorrect-pairing requirements reflect widespread practitioner convention, not a named primary source) — devrel-style, matching the existing `"practitioner-consensus"` vocabulary already used elsewhere in `roles/specs/*.spec.json`.

derived: `python3 -c "import json; json.load(open('roles/specs/brand-design.spec.json'))"`
```
(no output — parses clean)
```

canonical: `python3 -m pytest gates/spec_schema_five_activities_test.py -q`, executed this turn after the amendment.
derived: `python3 -m pytest gates/spec_schema_five_activities_test.py -q`
```
........                                                                 [100%]
8 passed in 0.86s
```
