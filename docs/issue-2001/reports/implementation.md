---
code_under_review:
  - spawn.py
  - test/test_spawn_cross_family_skill_selection.py
  - docs/issue-2001/reports/implementation/replay-table.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# issue-2001 phase-2 implementation record

## What was done

canonical: 51a28873 (this branch's phase-2 commit, diff against 65a74bc0).

Delivered the phase-2 build approved via `APPROVE issue-2001/implementation`
(basis: `docs/issue-2001/proposals/task-aware-cross-family-skill-selection.md`,
upstream commit 65a74bc0).

- Added `_tokenize(text)`, `_TOKEN_RE`, `_STOPWORDS`,
  `_CROSS_FAMILY_MIN_OVERLAP`, and `_cross_family_skill_matches(task_text,
  role, repo_root, k=2)` to `spawn.py` right after `_skill_trigger_line`.
  The scorer tokenizes (lowercase, non-alphanumeric split, small stopword
  list), excludes any candidate already in the role's `_ROLE_SKILLS`
  family list, skips candidates with no `_skill_trigger_line()`, scores by
  distinct-token overlap, keeps overlap >= 2, sorts by `(score desc, name
  asc)`, and returns the top `k`. Zero-match returns `[]`.
- Wired the result into `_spawn_one()`: captured the function's original
  `task` parameter as `_cross_family_task_text` before any directive text
  is appended (so scoring reads the actual issue/task text, not text this
  function itself later appends); computed `cross_family_dirs` inside the
  `role_source["source"] == "skill-repo"` branch via
  `_cross_family_skill_matches(_cross_family_task_text, role,
  _skill_repo_root())`; appended matched skills' `name — trigger-line`
  entries to the existing family-skill listing paragraph, with a trailing
  clause naming which entries were cross-family additions (empty string
  when `cross_family_dirs` is empty, preserving byte-identity); appended
  the same directories to `all_skill_dirs` so they are mounted via
  `--plugin-dir`, not just named in the directive.
- Added `test/test_spawn_cross_family_skill_selection.py`: unit tests for
  `_tokenize` and `_cross_family_skill_matches` (matching case,
  sub-threshold case, family-exclusion case, K=2 cap with 3 candidates
  clearing threshold — tie-broken by name, no-trigger-line case), plus a
  live `_spawn_one()` acceptance test class covering both acceptance
  cases: a matching fixture task gains exactly the matched skill in both
  the mount list (captured via a `spawn_cmd` spy) and the directive text;
  a non-matching fixture task produces a byte-identical directive and an
  empty mount-list addition across two independent runs.
- Wrote `docs/issue-2001/reports/implementation/replay-table.md`: replayed
  the scorer against all 16 distinct issue+role sessions with a session
  log dated 2026-08-22 in `tokenmaxxxer/on-the-record` (`gh issue view`
  fetched live per row), recording would-have-added skills and a
  plausibility judgment per row.

## Why

Per the consult recorded in the issue body (2026-08-22,
requirements-engineering: add-only first, K=1-2, family set intact,
replay-before-ship) and the proposal's Rationale: reused
`_skill_trigger_line()`'s existing extraction instead of a second
mechanism, and chose deterministic keyword-overlap scoring over
TF-IDF/embeddings because the issue explicitly asked for "deterministic
keyword scoring, no network, no new deps" (proposal, alternative 1
rejected on that basis).

## Upstream

basis: docs/issue-2001/proposals/task-aware-cross-family-skill-selection.md,
commit 65a74bc0.

canonical: `gh issue view 2001 --comments` output read this session — PR
#2002 (phase-1) merged to main, and the issue-comment body posted by
JiwonJung94 (approvers.md) reads exactly `APPROVE issue-2001/implementation`
(single-account mode: PR author and approver are the same account).

## Acceptance verification

`derived:`
```
$ python3 -m pytest test/test_spawn_cross_family_skill_selection.py -o addopts='' -v
test/test_spawn_cross_family_skill_selection.py::TokenizeTest::test_empty_text_yields_empty_set PASSED
test/test_spawn_cross_family_skill_selection.py::TokenizeTest::test_lowercases_splits_nonalnum_and_drops_stopwords PASSED
test/test_spawn_cross_family_skill_selection.py::CrossFamilySkillMatchesTest::test_below_threshold_single_shared_token_no_match PASSED
test/test_spawn_cross_family_skill_selection.py::CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate PASSED
test/test_spawn_cross_family_skill_selection.py::CrossFamilySkillMatchesTest::test_k_cap_with_three_clearing_candidates_keeps_top_two PASSED
test/test_spawn_cross_family_skill_selection.py::CrossFamilySkillMatchesTest::test_matching_skill_clears_threshold_and_is_returned PASSED
test/test_spawn_cross_family_skill_selection.py::CrossFamilySkillMatchesTest::test_no_trigger_line_skill_never_matches PASSED
test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive PASSED
test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline PASSED
9 passed in 0.32s
```

`derived:`
```
$ python3 -m pytest tests/test_spawn_directive_assembly.py test/test_spawn_skills_mount.py test/test_spawn_role_skill_resolution.py -o addopts=''
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
1 failed, 50 passed in 1.11s
```

canonical: the `git stash` re-run below (this session's own live
reproduction against the pre-change tree).

`derived:`
```
$ git stash && python3 -m pytest tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today -o addopts=''; git stash pop
1 failed in 0.19s
```
The failure reproduces identically with this branch's diff removed, so
it predates this change; it is an ambient-environment leak (this live
session's own `CORE_BUILD_NOW=1` env var bleeds into the test's captured
subprocess env), not a regression from this commit's diff.

## Test-tier note

No `.on-the-record/test-tiers.json` file exists at this repo's root — ran
the acceptance test file directly and the three named existing suites
directly (not the full `pytest` collection), scoped to the write set and
its immediate neighbors per the acceptance line's own command shape; a
full-suite wall-clock measurement was not taken since the tiering config
this directive asks to check for is absent and this session did not run
a silent full suite.

## What did not work

None.

## Open findings

canonical: `severity_count`/`model_routing_count` lines of the derived
replay script output in
docs/issue-2001/reports/implementation/replay-table.md.

`derived:`
```
severity_count 16 of 16
model_routing_count 5 of 16
```
- The replay table's "Open finding" section: with the shipped
  min-overlap-2 threshold, `conformance-review-severity-classification`
  and `model-routing` clear the threshold on the counts pasted above,
  both false positives driven by generic vocabulary in their trigger
  sentences rather than genuine cross-family relevance. Per the
  proposal's explicit Out-of-scope line, this iteration does not retune
  the threshold; resolution path: a follow-up issue should either raise
  the min-overlap threshold, add per-skill trigger-sentence quality
  review, or broaden the current 8-word stopword list, informed by this
  replay table's data before any change ships.
- canonical: the `git stash` re-run in the Acceptance verification
  section above. The `SinglePhaseSignal::test_without_flag_is_byte_identical_to_today`
  failure (ambient `CORE_BUILD_NOW` env leak into the test's captured
  env) reproduces on the pre-change tree per that re-run, so it is
  unrelated to this issue's scope and was not fixed here — resolution
  path: a follow-up issue should have that test's fixture explicitly
  unset `CORE_BUILD_NOW` before asserting its absence, rather than
  relying on an unpolluted ambient environment.

next steps: none for this issue — the two open findings above are scoped
to follow-up issues per their resolution paths, not remaining work on
this branch.
