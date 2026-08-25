---
issue: 2278
role: implementation
loop_state: landed
upstream:
  - path: gates/check_runner.py
    sha: same-commit
code_under_review:
  - gates/check_runner.py
  - gates/test_check_runner.py
type: fix
breaking: "none — narrows a false-FAIL, no callers depended on the old default"
verdict: pass
---

# issue-2278 — implementation record

## What was done

Inverted `check_runner.parse_checks()`'s default classification for a
`check:`/`gate:` backtick that is neither a recognized command
(`looks_like_command`) nor measurement prose (`_MEASUREMENT_LANGUAGE`):

- Added `_looks_like_path(token)` (contains `/`, or ends in a known file
  extension from a fixed `_PATH_EXTENSIONS` set) right after
  `_MEASUREMENT_LANGUAGE` in `gates/check_runner.py`.
- Changed the final branch of `parse_checks` from `else: file-existence`
  to `elif _looks_like_path(cmd): file-existence` / `else: judgment` —
  path-shaped backticks stay mechanically checked (and genuinely FAIL if
  missing); everything else (bare identifiers, skill names, prose)
  downgrades to `judgment`, scored by `requirement_met.py`'s semantic
  layer instead of the file-existence gate.
- Added three regression tests to `gates/test_check_runner.py`:
  `t_cross_family_bare_identifier_classifies_as_judgment_not_file_existence`,
  `t_work_in_english_skill_name_classifies_as_judgment_not_file_existence`,
  `t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails`.

canonical: gates/check_runner.py:79-101, 151-158 (this commit's diff, see
`git show` on the commit landing alongside this record) — the helper and
the inverted branch.

Completed-items list (doc-placement ladder):
- [x] code change lands under `gates/` (not `src/`/`test/`) — matches the
  existing convention: `check_runner.py`'s own tests live beside it in
  `gates/` (see `test_check_runner.py`'s docstring on why, from
  issue-1323), not under a top-level `test/` directory.
- [x] record lands under the issue's `reports/` bucket (this file).
- [x] no `docs/specs/*` file touched — no reconciled-index regen needed.
- [x] no operational-surface file (package manifest, CI workflow, deploy
  script) touched — the operational-surface commit rule doesn't apply.

## Why

Two live PRs (#2255/issue #2213, #2218/issue #2208) had correct,
execution-verified Acceptance criteria FAIL merge-gate review because
their backticked content (`cross_family`, `work-in-english`) isn't a
path — it's a bare identifier/skill name embedded in measurement or
verification prose that the narrow `_MEASUREMENT_LANGUAGE` keyword list
didn't happen to match. The old default (unmatched backtick →
file-existence) mechanically asserted "a file named X exists," a claim
the criterion never made, and FAILed correct work — exactly the "gate
rejects correct work" class this drive has been eliminating (see
`_MEASUREMENT_LANGUAGE`'s own issue #2231/#2233 history in the same
file). Flipping the default to `judgment` unless the backtick is
path-shaped closes this whole class of false-FAILs without touching the
narrower, already-correct `_MEASUREMENT_LANGUAGE` carve-out or the
command-detection branch (`looks_like_command`), and without weakening
genuine missing-artifact detection: a backtick that looks like a path
(has `/` or a known extension) still classifies `file-existence` and
still genuinely FAILs when the file is actually absent.

## What did not work

None.

## Upstream basis

Issue #2278 (this record's subject, canonical: `gh issue view 2278`
output quoted in this turn's tool transcript); PR #2244 (proposed this
exact inversion, per issue #2278's own body); issue #2213 / PR #2255 and
issue #2208 / PR #2218 (the two live counterexamples regression-pinned
here, canonical: `gh issue view 2213`/`gh issue view 2208` output below).

## Open findings

None.

## Next steps

None — `loop_state: landed`.

## Executed acceptance evidence

Gate: `gates/test_check_runner.py`.

acceptance: `python3 gates/test_check_runner.py` — result:
```
ok - t_all_judgment_checks_do_not_abort_run_checks_when_pre_filtered
ok - t_artifact_smoke_check_actually_runs_and_fails_on_a_broken_artifact
ok - t_artifact_smoke_check_passes_when_the_artifact_parses
ok - t_bare_artifact_path_without_measurement_language_stays_file_existence
ok - t_bare_path_still_classifies_as_file_existence
ok - t_bare_py_gate_path_is_wrapped_to_run_through_pytest
ok - t_classification_is_byte_identical_without_a_declaration
ok - t_cross_family_bare_identifier_classifies_as_judgment_not_file_existence
ok - t_declared_artifact_command_classifies_as_artifact_smoke
ok - t_format_comment_lists_skipped_judgment_items_outside_the_pass_total
ok - t_format_comment_names_the_artifact_smoke_type
ok - t_format_no_checks_comment_reports_judgment_items_distinctly
ok - t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails
ok - t_measurement_language_prose_bullet_classifies_as_judgment_not_file_existence
ok - t_node_command_without_declaration_classifies_as_test_not_file_existence
ok - t_npx_deno_bun_are_on_the_interpreter_allowlist
ok - t_py_gate_path_with_explicit_interpreter_is_left_alone
ok - t_run_checks_records_a_failure_instead_of_crashing_on_unexecutable_command
ok - t_source_level_command_stays_test_even_with_a_declaration
ok - t_unclassifiable_check_is_still_judgment_and_refused_by_the_runner
ok - t_work_in_english_skill_name_classifies_as_judgment_not_file_existence
21/21 passed
```

acceptance: `python3 -m pytest gates/test_check_runner.py -q` — result:
```
............................                                             [100%]
28 passed in 30.17s
```
derived: 28 = 21 + 7 (the `t_`-prefixed cases enumerated in the fenced
run just above, plus the file's `test_`-prefixed pytest-fixture cases);
both fenced runs report 0 SKIPPED.

Downstream consumers unaffected (`gates/requirement_met.py` reuses
`check_runner.parse_checks` directly; `gates/merge_gate.py` reuses
`check_runner.run_checks`/`format_comment`):

acceptance: `python3 -m pytest gates/test_merge_gate.py gates/test_requirement_met.py -q` — result:
```
......................................................                   [100%]
54 passed in 1.08s
```

Provenance requirement: re-ran `check_runner`'s classifier live against
the **current, real** `## Acceptance` sections of issue #2213 and issue
#2208 (fetched this turn via `gh issue view <n> --json body`), comparing
the pre-#2278 classifier (loaded from `git show HEAD:gates/check_runner.py`
as a separate module, HEAD = the parent commit before this change) against
the post-change one:

canonical: `gh issue view 2213 --json body -q .body` and
`gh issue view 2208 --json body -q .body`, both fetched live this turn —
full bodies quoted in this turn's tool transcript; the `## Acceptance`
excerpt is reproduced below via `check_runner._acceptance_section`.

acceptance: classifier comparison script (both `git show
HEAD:gates/check_runner.py` old module and the working-tree new module,
run against the live-fetched issue bodies) — result:
```
--- issue #2213 (OLD classifier, pre-#2278) ---
  [file-existence] per-spawn `cross_family` timing plus `cache_read_input_tokens` and concurrency count are r

--- issue #2213 (NEW classifier) ---
  [judgment] per-spawn `cross_family` timing plus `cache_read_input_tokens` and concurrency count are r

--- issue #2208 (OLD classifier, pre-#2278) ---
  [judgment] the judge's historical abstention rate is reported as a number with the query that produce
  [test] `tests/test_retrieval_eval.py` passes with negative clauses stripped from the BM25 field,
  [file-existence] `work-in-english` is bound statically for the roles that need it and no longer appears in

--- issue #2208 (NEW classifier) ---
  [judgment] the judge's historical abstention rate is reported as a number with the query that produce
  [test] `tests/test_retrieval_eval.py` passes with negative clauses stripped from the BM25 field,
  [judgment] `work-in-english` is bound statically for the roles that need it and no longer appears in
```

derived: both former `file-existence` classifications (which would
mechanically FAIL, since neither `cross_family` nor `work-in-english`
names a real file) are `judgment` under the new classifier, against the
issues' real, current bodies — the two live counterexamples issue #2278
names are closed.

Genuine missing-artifact FAIL, constructed live (path-shaped, absent).
`tests/test_genuinely_missing_thing_2278.py` below is a deliberately
untracked, nonexistent path (never added to git, invented solely for
this demonstration) — the point of this check is that it does NOT exist
and the runner must still FAIL it, not pass it:

acceptance: ad-hoc script exercising `check_runner.parse_checks` +
`check_runner.run_checks` against the untracked, deliberately-absent
`.py` path above — result:
```
classification: [('test', 'python3 -m pytest tests/test_genuinely_missing_thing_2278.py')]
run result: fail
```
derived: this path-shaped case routes through the pre-existing
`looks_like_command` bare-`.py` branch (git-tracked, unmodified by this
change — see `gates/check_runner.py`'s `looks_like_command`/`INTERPRETERS`
logic, present before this commit). The "path-shaped and absent → still
FAIL" guarantee for the branch this issue actually changed (the
`file-existence` default) is pinned in-repo by test function
`t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails`
in `gates/test_check_runner.py` — named explicitly in the `ok -` line
list of the `python3 gates/test_check_runner.py` fenced run above.

Empty-state check: test function
`t_classification_is_byte_identical_without_a_declaration` in
`gates/test_check_runner.py` (unmodified by this change, also named in
the `ok -` line list of the fenced run above) pins that an Acceptance
section handled without any change to the backtick-classification
default stays byte-identical. No backticked-token-free case is affected
by this change since the touched branch only ever triggers when a
backtick match exists.

skill-verdict: implementation-complexity-coupling-management — not-applicable: single-function classifier edit, no coupling/cohesion metric or check-pipeline-ordering decision involved
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern indirection question; a plain conditional-branch inversion
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data-structure/algorithm/communication-scheme choice; a set-membership check on an existing small constant set
skill-verdict: implementation-blueprint — not-applicable: single-file, single-function change, not multi-module structure and not a parallel-worker fan-out contract
other mounted skills: not triggered
