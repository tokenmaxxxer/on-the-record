---
issue: 2278
role: conformance-review
loop_state: reported
upstream:
  - path: gates/check_runner.py
    sha: 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8
  - path: gates/test_check_runner.py
    sha: 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8
  - path: docs/issue-2278/reports/implementation.md
    sha: 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8
subject: PR #2283 (branch issue-2278/implementation, head 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8) against issue #2278's frozen Acceptance section
test: issue #2278 Acceptance section (gate / empty-state / provenance lines) plus the Ask section's two behavioral clauses
result: passed
assertedBy: conformance-review (issue-2278/conformance-review session)
---

# issue-2278 — conformance-review record

## What was done

Builder-blind conformance review of PR #2283 against issue #2278's
frozen Acceptance section, and the Ask section clauses that Acceptance
itself references. Full enumeration, not sampling — the change is a
single function's inverted branch plus three pinned regression tests,
well within one review pass (conformance-review-sampling-derivation:
not applicable, see skill-verdict below).

Extracted nine checkable requirements — R1-R4 from the Ask section's
substantive behavior, R5-R8 from the Acceptance section's gate /
empty-state / provenance lines, R9 from issue #2278's own
operator-frozen amendment comment (issuecomment-5403812868, posted
after this session started — see Amendments reconciled below) — picked
a verification method for each, and independently re-executed every
piece of evidence PR #2283's own record claims, in a clean worktree at
the PR's actual head commit, rather than relying on the pasted
transcripts in docs/issue-2278/reports/implementation.md (out-of-scope
in this worktree — that record lives only on branch
issue-2278/implementation). All nine requirements verdict Present; two
non-blocking notes are recorded under Open findings.

### R1 — invert the default to `judgment` for non-path backticks

- spec_ref: issue #2278 Ask section, paragraph 1 ("Invert the default...
  a `check:`/`gate:` line whose backticked content is not a path... must
  downgrade to `judgment`... never FAIL as file-existence")
- verdict: Present
- evidence: 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8:gates/check_runner.py:154-157
  — `parse_checks()`'s final branch reads `elif _looks_like_path(cmd):
  file-existence` / `else: judgment`, replacing the prior unconditional
  `else: file-existence`.
- rationale: the only default branch reachable when a backtick is
  neither a recognized command nor `_MEASUREMENT_LANGUAGE` now returns
  `judgment` unless `_looks_like_path` is true — matching the
  requirement literally.

### R2 — path-shaped-but-missing backticks still genuinely fail

- spec_ref: issue #2278 Ask section, paragraph 1 ("Keep genuine
  missing-artifact FAILs: if the criterion's backtick names a path shape
  (contains `/` or a known extension) that is absent, that is still a
  real FAIL")
- verdict: Present
- evidence: 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8:gates/check_runner.py:89-101
  (`_PATH_EXTENSIONS`, `_looks_like_path()`), exercised independently in
  Executed evidence, "R2/R8 constructed-missing-path".
- rationale: `_looks_like_path` returns true for `/`-containing or
  known-extension tokens; those still route to `file-existence`, which
  `run_checks` rejects when the path is absent from disk — shown by
  direct execution below, not taken on the PR's word.

### R3 — regression-pin both live counterexamples

- spec_ref: issue #2278 Ask section, paragraph 2 ("Regression-pin both
  live counterexamples above as test cases")
- verdict: Present
- evidence: 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8:gates/test_check_runner.py:284-292
  (`t_cross_family_bare_identifier_classifies_as_judgment_not_file_existence`,
  issue #2213/PR #2255) and
  41be748d4d6a7dd2cd0a10039b004a0cb84f06b8:gates/test_check_runner.py:295-301
  (`t_work_in_english_skill_name_classifies_as_judgment_not_file_existence`,
  issue #2208/PR #2218).
- rationale: both regression tests exist in `gates/test_check_runner.py`,
  name the originating issue/PR pair in their docstring, and assert
  `judgment` classification for the exact backtick strings issue #2278's
  body names.

### R4 — regression-pin a genuine missing-file case

- spec_ref: issue #2278 Ask section, paragraph 2 ("plus a genuine
  missing artifact case, in `gates/test_check_runner.py`")
- verdict: Present
- evidence: 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8:gates/test_check_runner.py:304-313
  (`t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails`)
  — asserts `file-existence` classification and a `fail` status for a
  `.json`-extension-shaped missing path.
- rationale: satisfies the paragraph-2 requirement in-repo. See Open
  finding 1 for a wording nuance against the Acceptance section's own
  literal example.

### R5 — Acceptance gate line

- spec_ref: issue #2278 Acceptance section, line 1 — the `gate:` line
  naming `gates/test_check_runner.py`
- verdict: Present
- evidence: 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8:gates/test_check_runner.py:1
  — independently re-run at PR head; see Executed evidence, "R5 gate
  run".
- rationale: the named gate passes at the PR's actual head commit,
  executed by this review session, not copied from the PR body.

### R6 — empty state: no-backtick classification unchanged

- spec_ref: issue #2278 Acceptance section, line 2 ("empty state: an
  Acceptance section with no backticked tokens at all — classification
  unchanged from today")
- verdict: Present
- evidence: independently constructed and run against both module
  versions; see Executed evidence, "R6 empty-state old-vs-new".
- rationale: no-backtick classification is byte-identical old-vs-new,
  shown by direct execution against both module versions rather than by
  assuming the touched branch is unreachable without a backtick.

### R7 — provenance: re-run against the two live counterexamples' real bodies

- spec_ref: issue #2278 Acceptance section, line 3, clause 1
  ("provenance: executed-live — re-run `check_runner` for PR
  #2255/issue #2213 and PR #2218/issue #2208 after the change and paste
  real output showing both former FAILs now judgment-classified")
- verdict: Present
- evidence: independently re-run against live-fetched issue bodies; see
  Executed evidence, "R7 live provenance re-run".
- rationale: both named former FAILs reclassify to `judgment` against
  the issues' real, current bodies fetched independently this turn —
  this matches PR #2283's own claimed comparison without depending on
  it.

### R8 — provenance: constructed missing-path case still fails

- spec_ref: issue #2278 Acceptance section, line 3, clause 2 ("and a
  constructed criterion naming a genuinely missing tests/...py path
  still FAILing")
- verdict: Present
- evidence: independently constructed; see Executed evidence, "R2/R8
  constructed-missing-path".
- rationale: the literal path-shaped case still fails as required.
  Routing note: this particular slash-shaped case resolves through the
  pre-existing `looks_like_command` bare-`.py` branch (unmodified by
  this PR), not through the new `_looks_like_path`/`file-existence`
  branch this PR actually touched — see Open finding 1.

### R9 — operator-frozen constraint: systemic, no side effects across any target repo

- spec_ref: issue #2278, comment issuecomment-5403812868 (2026-08-25
  operator-frozen amendment) — "must hold systemically for every
  session that installs on-the-record and works against any target
  repo... and must land without side effects: no added per-spawn
  overhead or steady-state load, no new conflict surfaces..., no
  stall/deadlock modes, no consumer-tree pollution"
- verdict: Present
- evidence: 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8:gates/check_runner.py:89-101,154-157
  — the diff adds one module-level constant set (`_PATH_EXTENSIONS`,
  built once at import) and one pure string-predicate function
  (`_looks_like_path`, no I/O, no filesystem writes, no new files); the
  only change to `parse_checks()`'s control flow is swapping one
  unconditional `else` branch for an `elif`/`else` pair over
  already-in-memory strings.
- rationale: this reasoning stays confined inside `check_runner.py`'s
  own classifier — it never writes to a target repo's tree, never
  touches `.on-the-record/`'s append-log or any other shared state,
  and adds no loop or wait construct (so no new stall/deadlock
  surface). Its per-call cost is one set-membership lookup on a fixed
  small extension set plus a string `rsplit`/`in` check — the same
  order of cost the pre-existing `_MEASUREMENT_LANGUAGE` regex check
  right next to it already pays every classifier call, so there is no
  added per-spawn overhead or steady-state load beyond what the
  classifier already did. Nothing in the diff is specific to this
  checkout — the extension set and the path-shape rule are generic —
  so the behavior holds identically against any target repo
  `check_runner.py` is pointed at.

## Executed evidence (independently reproduced by this review, not copied from the PR)

All runs below were executed by this review session in a detached
worktree at PR #2283's actual head commit
(41be748d4d6a7dd2cd0a10039b004a0cb84f06b8), created via `git worktree
add /tmp/pr2283-review origin/issue-2278/implementation --detach`.

**R5 gate run:**

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
28 passed in 18.80s
```
(pytest-asyncio fixture-loop-scope deprecation warnings repeated across
workers were elided from the pasted block above; zero SKIPPED lines
were present in the raw run.)

acceptance: `python3 -m pytest gates/test_merge_gate.py gates/test_requirement_met.py -q` — result:
```
......................................................                   [100%]
54 passed in 6.97s
```
(downstream `merge_gate`/`requirement_met` consumers of `parse_checks`/
`run_checks`, checked here for completeness beyond the Acceptance
section's own named gate.)

**R6 empty-state old-vs-new:**

acceptance: `python3` script loading `gates/check_runner.py` at parent
commit `08b396f3` (old, pre-#2278) and at PR head `41be748d` (new),
classifying a no-backtick line — result:
```
OLD: [{'type': 'judgment', 'raw': 'the output looks correct and matches expectations'}]
NEW: [{'type': 'judgment', 'raw': 'the output looks correct and matches expectations'}]
byte-identical: True
```

**R7 live provenance re-run:**

acceptance: classifier comparison — old module (parent commit
`08b396f3`) vs PR module (`41be748d`) — run against the real, current
`gh issue view 2213 --json body` output and the real, current
`gh issue view 2208 --json body` output, both fetched this turn —
result:
```
--- issue #2213 OLD ---
  file-existence - per-spawn `cross_family` timing plus `cache_read_input_tokens` and concurrency count are r
--- issue #2213 NEW ---
  judgment - per-spawn `cross_family` timing plus `cache_read_input_tokens` and concurrency count are r

--- issue #2208 OLD ---
  judgment - the judge's historical abstention rate is reported as a number with the query that produce
  test - `tests/test_retrieval_eval.py` passes with negative clauses stripped from the BM25 field,
  file-existence - `work-in-english` is bound statically for the roles that need it and no longer appears in
--- issue #2208 NEW ---
  judgment - the judge's historical abstention rate is reported as a number with the query that produce
  test - `tests/test_retrieval_eval.py` passes with negative clauses stripped from the BM25 field,
  judgment - `work-in-english` is bound statically for the roles that need it and no longer appears in
```
Both named former `file-existence` classifications are `judgment` under
the PR's module, against the issues' real bodies fetched independently
this turn — the two live counterexamples issue #2278 names are closed.

**R2/R8 constructed-missing-path:**

acceptance: `parse_checks`+`run_checks` against an untracked,
deliberately nonexistent path — result:
```
classification: [('test', 'python3 -m pytest tests/test_genuinely_missing_thing_2278.py')]
run result: fail
```
The extension-shaped (no-slash) branch of this same guarantee — the
branch this PR's `_looks_like_path` change actually touches — is pinned
in-repo by `t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails`,
named in the `ok -` list of the R5 gate run above.

## Why

Verify-at-landing (contract v3): a deliverable is code plus EXECUTED
acceptance evidence. This review re-derives every piece of evidence PR
#2283's record claims from a clean worktree at the PR's actual head
commit, rather than accepting the builder's pasted transcripts — per
this role's verdict-assignment rule 6 ("the verdict came from looking
at the artifact, not from the builder's account of their own intent")
and the finding-record skill's own checklist item to the same effect.
Every one of R5-R8's independent re-executions above matched PR #2283's
record claims classification-for-classification and pass-count for
pass-count, so no gap turned up between the claimed evidence and what
actually runs.

## Upstream basis

- PR #2283, branch `issue-2278/implementation`, head commit
  41be748d4d6a7dd2cd0a10039b004a0cb84f06b8 — `gates/check_runner.py`,
  `gates/test_check_runner.py`, and
  docs/issue-2278/reports/implementation.md (this last path is
  out-of-scope in this review session's own worktree — it lives only on
  branch issue-2278/implementation, read via `git show
  origin/issue-2278/implementation:docs/issue-2278/reports/implementation.md`).
- Issue #2278's frozen body (`gh issue view 2278`) — the Problem, Ask,
  and Acceptance sections.
- Live-fetched, current bodies of issue #2213 and issue #2208
  (`gh issue view 2213 --json body` and `gh issue view 2208 --json
  body`, this turn) — used to independently reproduce the provenance
  requirement (R7) instead of trusting PR #2283's own pasted
  comparison.
- Independent execution: a detached worktree at PR head
  (`/tmp/pr2283-review`), used for every Executed-evidence run above.

## Open findings

1. **Acceptance clause R8's literal example versus what regression-pins
   the changed branch** (non-blocking). Issue #2278's Acceptance line 3
   literally names a genuinely missing tests/...py-shaped path as the
   constructed FAIL example. A slash-shaped `.py` path never actually
   reaches the branch this PR changed — `parse_checks` routes it through
   the pre-existing `looks_like_command` bare-`.py` detection (wrapped
   with `pytest`) before `_looks_like_path` is ever consulted, since
   that earlier branch already claims any single-token `.py`-suffixed
   command. PR #2283's own in-repo regression pin for the branch it
   actually touched instead uses a `.json`-extension path with no
   slash — the only shape that is both path-like (via
   `_PATH_EXTENSIONS`) and not already claimed by `looks_like_command`.
   Both this review's R8 run and PR #2283's own record independently
   demonstrate the slash-`.py` case still fails behaviorally, so the
   Acceptance clause's outcome is satisfied — this finding is only that
   the literal example wording names a branch the PR did not touch,
   while the branch it did touch is proven by a differently-shaped
   example. Resolution path: none required to close #2278; an optional
   follow-up would rephrase future Acceptance examples to name the
   extension-only shape directly, or add one more in-repo regression
   test using an actual slash-`.py`-shaped missing path so the literal
   wording and the pinned test shape line up.
2. **upstream: sha for docs/issue-2278/reports/implementation.md**
   (non-blocking, procedural; that path is out-of-scope in this
   worktree — see the Upstream basis section above). That file lands in
   the same commit as the code it documents (41be748d), so its
   `upstream:` sha in this record's frontmatter is the real 40-char
   commit hash rather than `same-commit` — per contract §1,
   `same-commit` applies when the cited path lands in *this* record's
   own commit, not the PR-under-review's commit. Noted only for
   traceability precision; does not change any verdict above.

## Amendments reconciled

amendments-reconciled: issuecomment-5403812868 — the operator-frozen
constraint posted on issue #2278 after this session started (systemic
across any target repo, no added per-spawn overhead, no new conflict
surface, no stall/deadlock mode, no consumer-tree pollution) is graded
above as requirement R9, verdict Present. No trade-off needed stating,
since the diff this review inspected is a pure, generic classifier
branch with no filesystem writes, no shared-state touch, and no added
control-flow loop.

## Next steps

None — `loop_state: reported` (terminal for the `review-record` kind).

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2278's Ask/Acceptance prose into 8 dimension-scoped requirement items (R1-R4 functional-behavior from Ask, R5-R8 scope-boundary/provenance from Acceptance) before rendering any verdict.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used Inspection for the static branch-shape checks (R1-R4) and independently re-run Test/Analysis for the executable and live-provenance checks (R5-R8), reusing the existing pytest suite per rule 4 instead of deriving a parallel manual check.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Present to all 8 requirements only after independently re-executing each piece of claimed evidence rather than trusting PR #2283's own record (rule 6), and named the routing nuance under Open finding 1 instead of silently shifting a verdict on a plausible near-miss.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every verdict above cites file:line-range plus the exact commit sha read (41be748d4d6a7dd2cd0a10039b004a0cb84f06b8), and the issue #2278 body checked against is the frozen version this session read via `gh issue view 2278`.
skill-verdict: conformance-review-finding-record — applied: invoked; every requirement block carries requirement/spec_ref/verdict/evidence/rationale, written solo (no evidence was unreachable), all inside this one file.
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of all 8 requirements against a 3-file, single-function diff was feasible in a single review sweep; no sampling scope was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: no finding above needed risk-weighting beyond its recorded verdict; scope was not extended into severity banding.
skill-verdict: implementation-audit — not-applicable: this session ran issue #2278's own conformance-review role (five-verdict finding-record format against a frozen Acceptance section), not the separate builder-then-independent-evaluator Implementation Audit protocol; the cross-family match was keyword-only.
other mounted skills: not triggered
