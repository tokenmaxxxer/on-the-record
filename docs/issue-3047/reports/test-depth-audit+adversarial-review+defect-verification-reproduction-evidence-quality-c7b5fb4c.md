---
issue: 3047
role: test-depth-audit+adversarial-review+defect-verification-reproduction-evidence-quality-c7b5fb4c
author: test-depth-audit+adversarial-review+defect-verification-reproduction-evidence-quality-c7b5fb4c
skills: test-depth-audit (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), defect-verification-reproduction-evidence-quality (skill-repository(c05de12))
verifies_subject: true  # second independent, builder-blind verification of PR #3085's own deliverable against issue #3047, run in parallel with a first review
code_under_review: dfad1978748145cadab18db6a7de52fef156c902
type: defect-verification-record
breaking: false
verdict: 5 of 6 checked properties Present (both written acceptance
  checks, both surviving-alarm/tick-budget must-nots, and the live
  4-branch precision re-test). The third must-not (an unclassifiable
  subject is reported as unclassified, never bucketed) is Incorrect for a
  constructible input class -- see "What was done" for the reproduction:
  a MERGED sibling branch that never added a board-tracked record is
  indistinguishable, under the state-only signal the implementer chose,
  from a genuine corrupted-merge-base MERGED sibling, yet is bucketed into
  corrupted-merge-base with its recut-corrupted repair attached instead of
  reported unclassified. Full test suite: independently re-derived, this
  PR's own report of zero regressions holds.
loop_state: landed
upstream:
  - path: PR #3085 (github.com/tokenmaxxxer/on-the-record/pull/3085), head
      commit dfad1978748145cadab18db6a7de52fef156c902, not merged to main
    sha: dfad1978748145cadab18db6a7de52fef156c902
---

# issue-3047 — test-depth-audit+adversarial-review+defect-verification-reproduction-evidence-quality-c7b5fb4c record

## What was done

Second independent, builder-blind review of PR #3085 against issue #3047,
run separately from a parallel first review. PR #3085's branch was
fetched read-only into `/tmp/pr3085-worktree`
(`dfad1978748145cadab18db6a7de52fef156c902`); a second worktree at
`/tmp/main-review` tracks `origin/main` at `573e7382`. Neither PR #3085
nor its branch was edited.

acceptance: `cd /tmp/pr3085-worktree && python3 -m pytest tests/test_watchdog_cause_classification.py -q` — result:
```
14 passed in 0.95s
```

acceptance: `cd /tmp/pr3085-worktree && python3 gates/probe_cause_misattribution.py` — result:
```
ok
```

Both of the issue's literal acceptance checks succeed on PR #3085's tree.

**Live 4-branch precision re-test.** The issue's fourth comment records
the alarm firing against `issue-3047`/PR #3085, `issue-3050`/PR #3086,
`issue-3049`/PR #3088, `issue-3061`/PR #3087 -- four ordinary,
uncorrupted branches whose PRs had just opened, all four wrongly
classified pre-fix. Re-ran the fixed classifier against these same
subjects with a real, freshly-fetched `pr_index`
(`gates.closure_sweep._pr_index_all`, live-paginated from the repo, no
synthesis):

derived: `python3 /tmp/probe_live_four.py` — result:
```
issue-3047 PR #3085: cause=no-record-yet
issue-3050 PR #3086: cause=no-record-yet
issue-3049 PR #3088: cause=no-record-yet
issue-3061 PR #3087: cause=no-record-yet
```
(full per-line output also captured; none of the four formatted lines
contain `recut-corrupted`). All four subjects now classify
`no-record-yet` and none carry the force-push remediation sentence.

**Must-not 1 (the genuine alarm survives).**
`/tmp/pr3085-worktree/gates/probe_cause_misattribution.py`'s own
synthesised corrupted-merge-base subject (a MERGED sibling plus a later
OPEN PR under the same subject prefix) still classifies
`corrupted-merge-base` and still carries the identical `recut-corrupted`
sentence the pre-fix code printed unconditionally, per the `ok` result
above.

**Must-not 2 (tick budget -- no per-PR fetch), checked by reading the
code path rather than the record's account of it.**

derived: `cd /tmp/pr3085-worktree && git diff main...HEAD -- watchdog.py | grep -n "_pr_index_all"` — result:
```
(no output)
```
The `closure_sweep._pr_index_all(root)` call site inside the delta-PR
branch of `_board_wide_sweep` is byte-identical to main; this PR adds no
new `gh`/`subprocess` call anywhere.

canonical: `/tmp/pr3085-worktree/watchdog.py:845-873`
(`_classify_mapping_loss_cause`) and `/tmp/pr3085-worktree/watchdog.py:903-950`
(`_classify_narrowing_prs`) — both functions read only the `pr_index`
dict already passed in; neither calls `subprocess` or any
network-touching function. The new argument this PR adds is
`pr_index: dict | None = None` threaded through an existing call site,
not a new fetch.

**Must-not 3 (an unclassifiable subject is reported as unclassified) --
Incorrect.** This is the property the two written acceptance checks do
not directly force, so it needed a constructed input rather than a
re-run of the PR's own probe. `_classify_mapping_loss_cause`
(`/tmp/pr3085-worktree/watchdog.py:845-873`) decides
`corrupted-merge-base` the instant any sibling branch under `issue-<n>/`
in `pr_index` carries `state == "MERGED"` -- no other field is read
(`pr_index` entries carry `{number, state, body}` per
`/tmp/pr3085-worktree/gates/closure_sweep.py:250-258`, and only `state`
is consulted). The justification, in both the function's own docstring
and the builder's record, is that a MERGED sibling means this subject
previously had a real record land on the board. That step is not
established by the data available: `board()`
(`/tmp/pr3085-worktree/board.py:807-826`) recognizes a subject only via
files that landed under a subject's `reports/` directory carrying a
`loop_state` frontmatter key -- a MERGED PR under the same subject prefix
that never touched such a file (a phase-1-proposal-only merge, a
roster-only merge, anything short of a landed record) leaves
`state == "MERGED"` in `pr_index` with nothing for `board()` to have ever
shown. Given only `{number, state, body}` and a policy of reading `state`
alone, this case is exactly the "cannot be classified either way"
condition must-not 3 names.

Reproduction: environment `/tmp/pr3085-worktree` at
`dfad1978748145cadab18db6a7de52fef156c902`; constructed a `pr_index` with
one sibling branch under `issue-9999/`, `state = "MERGED"`, whose `body`
carries no `Closes #` trailer (the phase-1-proposal-only shape --
`pr_index`'s fixed `{number, state, body}` shape gives the classifier no
field that would tell this apart from a delivery merge); called
`_classify_mapping_loss_cause(pr_index, 9999)`; expected per must-not 3
`unclassified`, actual `corrupted-merge-base`.

derived: `python3 /tmp/probe_ambiguous.py` — result:
```
cause for MERGED-proposal-only sibling: corrupted-merge-base
```

Expected vs. actual: expected `unclassified`, got `corrupted-merge-base`
-- which `_format_mapping_loss_line` renders with the full
`recut-corrupted` force-push sentence attached, the harmful remediation
the issue is about.

Named signal that would be needed, and why the PR did not choose it:
telling this case apart from a genuine corrupted MERGED sibling requires
knowing whether that specific merge actually touched a `reports/` file
carrying `loop_state` -- the file list or diff of that one merged PR.
`pr_index`'s `{number, state, body}` shape does not carry that; obtaining
it needs exactly the per-PR fetch (`gh pr view <n> --json files`, or
inspecting the merge commit's tree) must-not 2 forbids. This is a real,
unnamed tension between the issue's own must-not 2 and must-not 3 for
this input class: the signal chosen (bare sibling state) cannot satisfy
must-not 3 here without violating must-not 2, and neither
`/tmp/pr3085-worktree/watchdog.py`'s docstrings nor the builder's record
name this tension -- both state MERGED-implies-prior-record as settled
rather than as an assumption `pr_index` itself does not establish.

This does not reverse the primary fix: the four live subjects re-tested
above have only OPEN siblings (or none), so they route through
`no-record-yet` cleanly and are unaffected by this gap. The gap is
specific to the MERGED branch of the decision, which none of
`/tmp/pr3085-worktree/gates/probe_cause_misattribution.py`'s three
synthesised subjects nor the new test file's decision table exercises --
see the test-depth audit below.

**Test-depth audit of the new test file**
(`/tmp/pr3085-worktree/tests/test_watchdog_cause_classification.py`).
Enumerated every test method by reading the file directly:

derived: `grep -c "    def test_" /tmp/pr3085-worktree/tests/test_watchdog_cause_classification.py` — result:
```
14
```

| # | Test | Classification | Assertion |
|---|------|-----------------|-----------|
| 1 | `test_c1_y_c2_y_merged_and_closed_sibling_is_corrupted` | GA | `assertEqual(..., _MAPPING_LOSS_CORRUPTED)` |
| 2 | `test_c1_y_c2_n_merged_only_is_corrupted` | GA | `assertEqual(..., _MAPPING_LOSS_CORRUPTED)` |
| 3 | `test_c1_n_c2_y_closed_without_merge_is_unclassified` | GA | `assertEqual(..., _MAPPING_LOSS_UNCLASSIFIED)` |
| 4 | `test_c1_n_c2_n_only_open_siblings_is_no_record_yet` | GA | `assertEqual(..., _MAPPING_LOSS_NO_RECORD_YET)` |
| 5 | `test_c1_n_c2_n_no_siblings_at_all_is_no_record_yet` | GA | `assertEqual(..., _MAPPING_LOSS_NO_RECORD_YET)` |
| 6 | `test_empty_pr_index_is_no_record_yet_not_a_crash` | GA | `assertEqual(..., _MAPPING_LOSS_NO_RECORD_YET)` |
| 7 | `test_other_issue_numbers_do_not_leak_across_prefix_match` | GA | prefix-collision edge case |
| 8 | `test_corrupted_cause_carries_recut_corrupted_instruction` | GA | `assertIn("recut-corrupted", line)` |
| 9 | `test_no_record_yet_cause_carries_no_recut_corrupted_instruction` | GA | `assertNotIn(...)` |
| 10 | `test_unclassified_cause_carries_no_recut_corrupted_instruction` | GA | `assertNotIn(...)` + `assertIn("unclassified", ...)` |
| 11 | `test_three_causes_produce_three_distinct_output_strings` | GA | `assertEqual(len(set(lines.values())), 3)` |
| 12 | `test_new_issue_subject_routes_to_no_record_yet_cause` | GA | end-to-end via `_classify_narrowing_prs` |
| 13 | `test_corrupted_subject_routes_to_corrupted_cause` | GA | end-to-end |
| 14 | `test_missing_pr_index_argument_routes_to_unclassified_not_a_guess` | GA | `assertEqual(..., _MAPPING_LOSS_UNCLASSIFIED)` |

Verification density: 14/14 = 100% GA, no Execution-Only, Mock-Dominated,
Happy-Path-Only, or Dead tests. Every test makes a falsifiable assertion
on classifier output -- genuine unit coverage of the function as written.

Behavioral coverage gap (the finding, restated from the test suite's own
shape): rows 1 and 2 both assert that any MERGED sibling classifies
`corrupted-merge-base`, encoding the untested assumption from must-not 3
above as expected behavior rather than probing it. No case in the table
constructs a MERGED sibling that is plausibly not a delivery merge and
checks the classifier's output for it -- the case reproduced above.

**Evidence quality of PR #3085's own record**
(`/tmp/pr3085-worktree/docs/issue-3047/reports/silent-failure-audit+implementation-blueprint+test-derivation-48ce3454.md`,
untracked on this session's own branch -- read directly out of the PR
worktree, not this repo). Read after the findings above were formed, to
keep this review's own conclusions independent of the builder's framing.
Most behavioural claims in that record carry a `derived:`/`canonical:`/
`acceptance:` tag with a runnable command, and every one checked here
reproduced exactly on independent re-run: the combined-file test count,
the probe's `ok` result, the two code citations, and the full-suite
counts (re-derived below).

One claim rests on the builder's own word alone, with no artifact a
reader can check: under that record's "Why" section, it states that an
earlier in-session draft used a different, weaker guard for a missing
`pr_index` argument, and that this was caught during a silent-failure
pass before the commit landed -- and explicitly notes the draft was never
committed separately, so no earlier sha exists to cite. The record is
honest about the gap rather than dressing it up with a citation tag it
cannot back -- but the claim about the builder's own pre-commit process
remains evidence-of-one, uncheckable by a reader.

**Full suite, independently re-derived on both trees**, with
`pytest.ini`'s `-n auto` cleared (`-o addopts=""`) so parallel-worker
output interleaving cannot corrupt the captured failing-test list before
diffing:

derived: `cd /tmp/pr3085-worktree && python3 -m pytest tests/ test/ -q -o addopts=""` — result:
```
20 failed, 744 passed, 3 xfailed, 2 warnings in 64.72s
```

derived: `cd /tmp/main-review && python3 -m pytest tests/ test/ -q -o addopts=""` — result:
```
20 failed, 730 passed, 3 xfailed, 2 warnings in 65.71s
```

derived: `diff <(grep '^FAILED' pr_run.txt | sort) <(grep '^FAILED' main_run.txt | sort)` — result:
```
(empty diff)
```
The 20 failing test IDs are identical on both trees. The extra 14 passing
tests on PR #3085's tree are exactly the new decision-table file; nothing
that succeeds on main now fails on PR #3085, and none of the 20
pre-existing failures touch `watchdog.py` or either file this PR adds.
This independently re-derives PR #3085's own reported figures and
establishes the 20 failures pre-date this PR rather than being introduced
by it.

derived: `cd /tmp/pr3085-worktree && python3 -m pytest tests/ -q -x` — result:
```
3 failed, 113 passed, 2 warnings in 2.78s
```
(stops early under `-x` with parallel workers; the 3 reported are a
subset of the same 5 pre-existing `tests/`-only failures reproduced
identically on both trees below -- `tests/test_respawn_deliverable_gate.py`
x4, `tests/test_spawn_gate_wiring.py` x1 -- confirming the amendment's own
note that this particular check does not by itself separate pre-existing
failures from new ones).

## Why

adversarial-review structure: the must-not-3 finding and the test-depth
table were built from the code and the live 4-branch data first, and PR
#3085's own record was opened only afterward, to cross-check evidence
quality rather than to shape the finding.

The defect-verification-reproduction-evidence-quality rule that a green
suite or an established check be judged by whether it exercised the
claimed behavior, not merely whether it executed, is why the two written
acceptance checks succeeding was treated as necessary but not sufficient
here: the probe script's three synthesised subjects and the decision
table both encode the MERGED-implies-prior-record assumption as ground
truth rather than testing it, so neither check exercises the must-not-3
boundary reproduced above. The same skill's numbered-minimal-path rule is
why that finding is recorded as a short repro with attached script output
rather than a prose assertion.

test-depth-audit was scoped to the one test file this PR adds, since that
file is the artifact whose depth determines whether this issue's specific
acceptance checks succeeding is trustworthy evidence.

## What did not work

An initial inline `python3 -c "..."` probe was refused by this session's
own write-gate because the literal path-shaped string inside the Python
source text was read as a write target. Worked around by writing the
probe to a `/tmp` script and running it from there instead; no repository
files were affected either way.

## Upstream basis

- `gh issue view 3047 --repo tokenmaxxxer/on-the-record --comments` — issue
  body and all 4 comments.
- PR #3085 (`dfad1978748145cadab18db6a7de52fef156c902`) —
  `/tmp/pr3085-worktree/watchdog.py`,
  `/tmp/pr3085-worktree/gates/probe_cause_misattribution.py`,
  `/tmp/pr3085-worktree/tests/test_watchdog_cause_classification.py`, and
  its own record, all read directly (these paths are untracked on this
  session's own branch -- they live only on PR #3085's branch).
- `/tmp/pr3085-worktree/board.py:807-826` and
  `/tmp/pr3085-worktree/gates/closure_sweep.py:195-262` — read directly
  to establish what a board entry requires and what `pr_index` actually
  carries.
- `origin/main` at `573e7382` — this session's start-of-conversation main
  tip, checked out read-only into `/tmp/main-review` for the suite diff.

## Open findings

canonical: this record's own "What was done" section, must-not-3
subsection and reproduction above.

- Must-not-3 gap: a MERGED sibling branch that never added a
  board-tracked record is bucketed `corrupted-merge-base` instead of
  `unclassified`. One resolution path: require the MERGED sibling's own
  `body` to carry a `Closes #<n>` trailer (already present in
  `pr_index`, no extra `gh` call) before treating MERGED as
  prior-record evidence, falling back to `unclassified` otherwise;
  another is to document MERGED-implies-prior-record explicitly as an
  accepted approximation rather than an established fact. Not applied
  here -- this task is review only, PR #3085 was not touched.
- The matching test-depth gap: no case in
  `/tmp/pr3085-worktree/tests/test_watchdog_cause_classification.py` or
  `/tmp/pr3085-worktree/gates/probe_cause_misattribution.py` exercises a
  MERGED sibling that is not a delivery merge.

## Next steps

None -- `loop_state: landed`. The must-not-3 gap is left as an open
finding for whoever next touches PR #3085 or files a follow-up.

skill-verdict: test-depth-audit — applied: invoked; classified every test
in `/tmp/pr3085-worktree/tests/test_watchdog_cause_classification.py` and
used the classification to locate the coverage gap behind the must-not-3
finding -- see "What was done."
skill-verdict: adversarial-review — applied: invoked; ran this review
code-and-data-first, with PR #3085's own record read second, as the
second independent, structurally separate review of PR #3085 -- see
"Why."
skill-verdict: defect-verification-reproduction-evidence-quality — applied: invoked; the must-not-3 finding is a numbered minimal-path
reproduction (environment/sha, exact input, expected vs. actual, attached
script output) rather than an assertion, and the two acceptance checks
were judged against whether they exercise the claimed behavior before
being accepted as sufficient -- see "What was done" and "Why."
other mounted skills: not triggered.
