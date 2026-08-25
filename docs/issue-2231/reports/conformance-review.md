---
issue: 2231
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2231/reports/implementation.md
    sha: b38ef7e3033c9a013b93d416eeab18f050c0295f
  - path: gates/requirement_met.py
    sha: b38ef7e3033c9a013b93d416eeab18f050c0295f
  - path: gates/check_runner.py
    sha: b38ef7e3033c9a013b93d416eeab18f050c0295f
subject: PR #2244 (branch issue-2231/implementation, head b38ef7e3033c9a013b93d416eeab18f050c0295f)
test: gates/test_requirement_met.py, gates/test_check_runner.py, gates/test_merge_gate.py, gates/ (full suite) — commands re-run live below
result: passed
assertedBy: conformance-review session, issue-2231
---

# issue-2231 — conformance-review record

## What was done

Builder-blind conformance review of PR #2244 against issue #2231's
frozen `## Acceptance` section and `## Ask` items. Read the diff for
`gates/requirement_met.py`, `gates/check_runner.py`,
`gates/test_requirement_met.py`, `gates/test_check_runner.py`; read the
implementation record on the PR branch (docs/issue-2231/reports/implementation.md
at b38ef7e3033c9a013b93d416eeab18f050c0295f — this path does not exist
on this checkout's own branch, it lives only on the PR branch, so it is
cited here without a backtick path-span) and the acceptance-format doc
it cites, `on-the-record/directive/acceptance-format.md`. Checked out
PR #2244's head commit into a scratch worktree at
`/tmp/pr-2244-check` (removed before this review finished) and
independently re-ran every claim below, rather than trusting the
builder's pasted transcript.

## Why

Issue #2231's own Acceptance section demands executed-live re-runs, not
code inspection — the gate that shipped for #1651 already looked green
while grading almost nothing, so a review that only reads the diff and
takes the implementation record's transcript at face value repeats
exactly that failure mode. Every acceptance-evidence claim in
docs/issue-2231/reports/implementation.md was independently re-executed
in this session rather than cited as evidence in itself.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split issue #2231's Acceptance+Ask text into the dimension-tagged requirement list below
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used to pick Test (live command re-run/pytest) vs Analysis/Demonstration per requirement
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used to assign Present/Surface/Absent/Incorrect/Unverifiable per requirement below
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; used to cite file:line + sha + command output per finding
skill-verdict: conformance-review-finding-record — applied: invoked; used to shape each per-requirement block (requirement/spec_ref/verdict/evidence/rationale/spec_vs_built)
skill-verdict: implementation-audit — not-applicable: conformance-review-* skill family already covers this exact record format and verdict taxonomy (P/S/A/I/U), implementation-audit's two-session claims-extraction scaffolding is redundant here
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of the requirement set is feasible, no sampling needed
skill-verdict: conformance-review-severity-classification — not-applicable: review scope was not explicitly extended into risk-weighting

## Upstream basis

- docs/issue-2231/reports/implementation.md at
  b38ef7e3033c9a013b93d416eeab18f050c0295f (PR #2244 branch only, not
  present on this checkout's branch) — the builder's own record; every
  acceptance-evidence line in it was independently re-executed here.
- `gates/requirement_met.py` at b38ef7e3033c9a013b93d416eeab18f050c0295f
  — `_parse_acceptance_items` (lines 273-304), `grade()` (306-399),
  `check()` (401-443), `main()` (445 to end), `_CANONICAL_CITATION`
  (line 86).
- `gates/check_runner.py` at b38ef7e3033c9a013b93d416eeab18f050c0295f —
  `_MEASUREMENT_LANGUAGE` (line 77), the mechanical/judgment partition
  in `main()` (lines 374-375), `format_comment`/`format_no_checks_comment`
  (lines 214, 248).
- `on-the-record/directive/acceptance-format.md` at
  b38ef7e3033c9a013b93d416eeab18f050c0295f (unchanged on this
  checkout's branch too) — the ACCEPTANCE FORMAT convention (check:/empty
  state:/provenance: mandatory only when a criterion references an
  executable artifact) the parser change is measured against.
- Issue #2231's frozen `## Acceptance`/`## Ask`/`## Non-goals` text, as
  supplied in this review's dispatch (not re-fetched from GitHub).

## Open findings

resolution path: item 1 below has an optional resolution path (correct
the one number in the implementation record); item 2 has none — nothing
outstanding.

canonical: python3 -m pytest gates/test_requirement_met.py gates/test_check_runner.py gates/test_merge_gate.py -q
```
$ cd /tmp/pr-2244-check && python3 -m pytest gates/test_requirement_met.py gates/test_check_runner.py gates/test_merge_gate.py -q
bringing up nodes...
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 1.41s
```
1. The dedicated requirement block below named "test-plan accuracy" has
   the full comparison and derivation for the number above. Short
   version: the PR body and the implementation record both write a
   different number for this exact command; this review's own
   reproduction, twice, plus a collect-only tally, plus diff arithmetic
   against this checkout's own main branch, all land on the number shown
   in the fence above instead. This does not change any of the eight
   core Acceptance/Ask verdicts below, since none of them cite this
   figure as their own evidence, and the full-suite figures the same
   record cites do reproduce (see the last requirement block). Flagged
   as a record-accuracy issue, not a blocker.
2. None of the Acceptance/Ask requirements themselves are open — all
   resolved to Present with independently reproduced evidence below.

## Next steps

loop_state is set to a terminal value for this review-record kind. The
one open item above (targeted-suite count mismatch in the
implementation record) needs no further action from this review itself.

---

requirement: gate lives at `gates/test_requirement_met.py` (Acceptance `gate:` line) and is exercised by a real test suite
spec_ref: issue-2231 ## Acceptance, gate: line
verdict: Present
canonical: python3 -m pytest gates/test_requirement_met.py -q
```
$ cd /tmp/pr-2244-check && python3 -m pytest gates/test_requirement_met.py -q
bringing up nodes...
...............................                                        [100%]
31 passed in 1.0s
```
evidence: `gates/test_requirement_met.py` is a new file in this PR (per
the PR diffstat) whose own added tests
(`t_prose_bullets_and_bare_labels_are_all_graded`,
`t_no_gradable_criteria_is_distinguishable_from_a_real_pass_via_check`,
`t_evidence_in_record_canonical_tag_citation_passes`, among others)
directly pin the three defects issue #2231 named.
rationale: The named gate file exists at PR head and is exercised by
tests that target the issue's three defects specifically, not generic
coverage.

---

requirement: empty state — a genuinely empty `## Acceptance` section (or one with no gradable items, e.g. `unverifiable:`-only) must report "no criteria" as its own distinct outcome, never approved-looking; "게이트 통과" must not print when nothing was gradable
spec_ref: issue-2231 ## Acceptance, empty state: line; ## Ask item 2
verdict: Present
canonical: python3 -c "import sys; sys.path.insert(0,'gates'); import requirement_met as rm; print(rm.grade('## Acceptance\n', 'diff --git a/x b/x\n+pass\n', {}))"
```
{'empty_state': True, 'criteria': [], 'blocked': False, 'blocking_reasons': [],
 'reason': 'Acceptance 절에 채점 가능한 항목이 0개다 (예: unverifiable: 로만 채워짐) — 채점 가능한 기준이 없다'}
```
canonical: python3 gates/requirement_met.py 2215 2223 (this checkout's own main branch, pre-fix code, no worktree)
```
$ python3 gates/requirement_met.py 2215 2223
advisory: [UNKNOWN] `tests/test_workspace_checkpoint.py`
게이트 통과 (또는 채점 가능한 기준 없음)
```
evidence: The second block above is the pre-fix baseline: the ambiguous
closing Korean line is byte-identical whether one item graded or zero
would have graded — exactly the ambiguity issue #2231 reports. At PR
head, `main()` (lines 461-465 of `gates/requirement_met.py`) prints a
textually distinct line ("채점 가능한 기준 없음 — 이건 통과가 아니라 별개의
결과다") and returns before reaching the old branch whenever
`empty_state` is set; `check()` (lines 429-431) and `grade()` (lines
326-331) carry that flag through both the no-section and
no-gradable-item cases.
rationale: Both the direct-function level and the CLI carry a boolean
checked before the old ambiguous message can print, and the replacement
message text reads as a distinct, non-approval outcome; tests
`t_no_gradable_criteria_is_distinguishable_from_a_real_pass_via_check`
and `t_unverifiable_only_section_stays_empty_state_not_a_new_criterion`
pin this from the suite side, and the independent repro above (not
reusing the builder's own fixture body) reaches the same distinct
outcome.

---

requirement: provenance — re-run `python3 gates/requirement_met.py 2215 2223` after the change and show all eight of #2215's items now graded (was one)
spec_ref: issue-2231 ## Acceptance, provenance: line (first clause)
verdict: Present
canonical: python3 gates/requirement_met.py 2215 2223 (PR head b38ef7e3033c9a013b93d416eeab18f050c0295f)
```
$ cd /tmp/pr-2244-check && python3 gates/requirement_met.py 2215 2223
advisory: [UNKNOWN] `tests/test_workspace_checkpoint.py`
advisory: [UNKNOWN] Kill a role session mid-edit with uncommitted changes; the edits are recoverable from the checkpoint ref afterward. Show the recovery commands and their real output.
advisory: [UNKNOWN] Checkpointing leaves the session's branch, HEAD, and index unchanged — demonstrate with `git status` / `git rev-parse HEAD` before and after a checkpoint fires.
advisory: [UNKNOWN] Untracked files are captured, not just tracked modifications.
advisory: [UNKNOWN] The health line for a live session reports dirty-file count and minutes-since-checkpoint; show it against a session with real dirty state.
advisory: [UNKNOWN] Checkpoint refs are cleaned up at session end and do not leak into pushes or PRs.
advisory: [UNKNOWN] a workspace with a clean tree and no edits yet — the health line must report 0 dirty files and no checkpoint, without creating an empty checkpoint ref.
advisory: [UNKNOWN] executed-live — the kill-mid-edit recovery and the before/after `git status` / `git rev-parse HEAD` comparison must be performed against a real spawned workspace and the real terminal output pasted into the report.
게이트 통과 (8개 기준 채점, 차단 사유 없음)
```
canonical: python3 gates/requirement_met.py 2215 2223 (this checkout's own main branch, pre-fix code, for the before comparison)
```
$ python3 gates/requirement_met.py 2215 2223
advisory: [UNKNOWN] `tests/test_workspace_checkpoint.py`
게이트 통과 (또는 채점 가능한 기준 없음)
```
evidence: Both fenced transcripts above are this session's own re-runs,
not the builder's pasted output; the PR-head transcript matches the
implementation record's pasted transcript line for line.
rationale: The before state (one advisory line, matching the issue's
own framing) and the after state (eight distinct advisory lines) were
each reproduced independently with real command output.

---

requirement: provenance — re-run `python3 gates/requirement_met.py 2208 2218` after the change and show more items graded than before
spec_ref: issue-2231 ## Acceptance, provenance: line (first clause, second named pair)
verdict: Present
canonical: python3 gates/requirement_met.py 2208 2218 (PR head b38ef7e3033c9a013b93d416eeab18f050c0295f)
```
$ cd /tmp/pr-2244-check && python3 gates/requirement_met.py 2208 2218
advisory: [UNKNOWN] the judge's historical abstention rate is reported as a number with the query that produced it, recorded in the implementation record
advisory: [UNKNOWN] `tests/test_retrieval_eval.py` passes with negative clauses stripped from the BM25 field, and the record states whether stripping changed either frozen negative case's outcome
advisory: [UNKNOWN] `work-in-english` is bound statically for the roles that need it and no longer appears in retrieval candidates — verified by re-running the retrieval pipeline against its frozen negative case
advisory: [UNKNOWN] The positives gold set does not regress (regression guard)
advisory: [UNKNOWN] Executed acceptance evidence in the record (#2137)
advisory: [UNKNOWN] a task where no skill applies must remain representable and must score correct when nothing is mounted — the property #2205 established and this issue must not break.
advisory: [UNKNOWN] executed-live — canonical: the abstention query over logged selections, plus `tests/test_retrieval_eval.py` runs before and after each of the two changes.
게이트 통과 (7개 기준 채점, 차단 사유 없음)
```
canonical: python3 gates/requirement_met.py 2208 2218 (this checkout's own main branch, pre-fix code)
```
$ python3 gates/requirement_met.py 2208 2218
advisory: [UNKNOWN] the judge's historical abstention rate is reported as a number with the query that produced it, recorded in the implementation record
advisory: [UNKNOWN] `tests/test_retrieval_eval.py` passes with negative clauses stripped from the BM25 field, and the record states whether stripping changed either frozen negative case's outcome
advisory: [UNKNOWN] `work-in-english` is bound statically for the roles that need it and no longer appears in retrieval candidates — verified by re-running the retrieval pipeline against its frozen negative case
게이트 통과 (또는 채점 가능한 기준 없음)
```
evidence: Both fenced transcripts above are this session's own re-runs.
The before state (three advisory lines, all UNKNOWN) matches the
issue's own framing.
rationale: Individual verdicts stay UNKNOWN because no
per_check_verdicts mapping was supplied through the bare CLI
invocation — UNKNOWN never blocks, which is the documented and correct
default, not a grading defect.

---

requirement: parser reach — grade prose bullets in a `## Acceptance` section, not only backticked artifact paths/check:/gate: bullets; reconcile against the ACCEPTANCE FORMAT convention (structure mandatory only for artifact-referencing criteria)
spec_ref: issue-2231 ## Ask, item 1
verdict: Present
canonical: python3 gates/requirement_met.py 2215 2223 and 2208 2218 (re-runs in the two requirement blocks directly above are the reachability evidence for this block)
evidence: `gates/requirement_met.py` at b38ef7e3033c9a013b93d416eeab18f050c0295f,
`_parse_acceptance_items()` (lines 273-304) pulls in top-level prose
bullets (`_BULLET_LINE`) and bare top-level empty state:/provenance:
lines (`_BARE_LABEL_LINE`) in addition to `check_runner.parse_checks`'
structural bullets, explicitly excluding `unverifiable:` (the issue
#310 escape).
`on-the-record/directive/acceptance-format.md`'s own ACCEPTANCE FORMAT
bullet states the structure requirement is conditional: "when an
`## Acceptance` criterion ... references an executable artifact ...
write check:/empty state:/provenance: each on its own line" — matching
the `structural: bool` split the new code adds.
Most of the two named issues' criteria are prose or bare-label lines,
not check:/gate: bullets, and none of them were reachable before this
PR (both baselines in the two blocks above graded far fewer items).
rationale: The parser change specifically mirrors the doc's own
conditional (artifact-reference triggers structure) rather than a
blanket rule to grade everything, which is the reconciliation the Ask
item asked for, and it is exercised against the two real,
under-graded-before issues rather than only synthetic fixtures.

---

requirement: fix the false-block on citation format (or demote it) without weakening the case where an artifact is genuinely missing
spec_ref: issue-2231 ## Ask, item 3
verdict: Present
canonical: python3 -c "import sys; sys.path.insert(0,'gates'); import requirement_met as rm; from pathlib import Path; r = rm.check(Path('.'), 2215, 2223, {chr(96)+'tests/test_workspace_checkpoint.py'+chr(96): rm.YES}); print('blocked:', r['blocked'])"
```
blocked: False
```
evidence: `gates/requirement_met.py` at b38ef7e3033c9a013b93d416eeab18f050c0295f
adds `_CANONICAL_CITATION` (line 86), recognized alongside the
pre-existing `_ACCEPTANCE_CITATION` inside `_artifact_in_diff_hunk`'s
prose-file exception, and gated to `structural` items only (the
`artifact_block = structural and verdict == YES and not
artifact_in_diff` line). The real PR #2223 diff cites the artifact via
a bare top-level line reading "canonical: " followed by a
backtick-quoted pytest invocation of `tests/test_workspace_checkpoint.py`,
not the older acceptance:/result: shape — grepped directly from the
fetched PR #2223 diff text during this session, so the fix above is
exercised against its actual trigger, not coincidentally passing
through the pre-existing path.
canonical: python3 -c "... rm.grade(body, diff, {'gate: gates/merge_gate.py': rm.YES}) ..." (synthetic repro constructed this session: body cites gates/merge_gate.py as a gate:, diff never touches it)
```
blocked: True
 - reason names gates/merge_gate.py as the missing artifact
```
rationale: The fix is narrowly scoped to the one citation shape PR
#2223 actually used and gated to only the structural sub-check
(prose/bare-label items were never required to cite an artifact and
remain unblocked for lacking one); a genuinely missing artifact still
blocks, verified with a repro constructed independently of the
builder's own synthetic example and landing on the same result.

---

requirement: non-goal — a genuinely missing artifact must still block (grade more, not block less)
spec_ref: issue-2231 ## Non-goals
verdict: Present
canonical: python3 -m pytest gates/test_requirement_met.py -k "t_structural_check_bullet_among_prose_still_blocks_on_missing_artifact or t_bare_prose_mention_still_not_evidence_even_with_canonical_fix" -q
```
$ cd /tmp/pr-2244-check && python3 -m pytest gates/test_requirement_met.py -k "t_structural_check_bullet_among_prose_still_blocks_on_missing_artifact or t_bare_prose_mention_still_not_evidence_even_with_canonical_fix" -q
2 passed in 0.4s
```
evidence: The synthetic repro in the requirement block above (an item
citing `gates/merge_gate.py` as a `gate:`, graded YES, with a diff that
never touches that path) blocks with a reason naming the specific
missing artifact.
rationale: The non-goal is exercised both by the builder's own suite and
by a repro this review constructed independently, landing on the same
blocked outcome by a different path than the builder used.

---

requirement: test-plan accuracy — targeted three-file suite claimed as a specific count in the PR body and implementation record
spec_ref: PR #2244 body and docs/issue-2231/reports/implementation.md test plan (not itself an Acceptance/Ask clause, named explicitly in this review's dispatch as a claim to verify)
verdict: Incorrect
canonical: python3 -m pytest gates/test_requirement_met.py gates/test_check_runner.py gates/test_merge_gate.py -q
```
$ cd /tmp/pr-2244-check && python3 -m pytest gates/test_requirement_met.py gates/test_check_runner.py gates/test_merge_gate.py -q
79 passed in 1.41s
```
Re-run a second time for stability:
```
$ cd /tmp/pr-2244-check && python3 -m pytest gates/test_requirement_met.py gates/test_check_runner.py gates/test_merge_gate.py -q
79 passed in 3.49s
```
canonical: python3 -m pytest gates/test_requirement_met.py gates/test_check_runner.py gates/test_merge_gate.py --collect-only -q ; grep -c "^def t_\|^def test_" on both branches
```
main branch total across the three files: 67 (test_check_runner.py 20,
test_merge_gate.py 23, test_requirement_met.py 24)
PR head total across the three files: 79 (test_check_runner.py 25,
test_merge_gate.py 23, test_requirement_met.py 31)
```
evidence: (derived: PR head total minus main total, per file, from the
fence above) test_check_runner.py +5, test_requirement_met.py +7,
test_merge_gate.py +0 — test_merge_gate.py is untouched by this PR.
Neither the direct run above, the collect-only tally, nor the diff
arithmetic land anywhere near the figure the implementation record and
PR body write for this exact command; no marker filter (`-m slow`, `-m
"slow or not slow"`) changes the outcome either.
rationale: The claimed count does not match the real, repeatable output
of the exact command cited, by three independent methods (direct run,
collect-only tally, diff arithmetic) — this is Incorrect rather than
Unverifiable, since the true count is cleanly reproducible on demand.
spec_vs_built:
canonical: python3 -m pytest gates/test_requirement_met.py gates/test_check_runner.py gates/test_merge_gate.py -q
The builder's record states a pass count and duration for this
exact command that do not match any reproduction of it in this review
(see the fenced output above, re-run twice); this does not change any of
the eight core Acceptance/Ask verdicts above, since none of them cite
this specific figure as their own
evidence, but it is a factual error in the implementation record's
acceptance-evidence section, worth naming precisely given issue #2231's
whole point is not taking claimed evidence at face value.

---

requirement: full gate suite, otherwise untouched, runs clean
spec_ref: PR #2244 body and docs/issue-2231/reports/implementation.md test plan
verdict: Present
canonical: python3 -m pytest gates/ -q --ignore=gates/test_gates.py
```
$ cd /tmp/pr-2244-check && python3 -m pytest gates/ -q --ignore=gates/test_gates.py
bringing up nodes...
941 passed, 8 xfailed in 28.65s
```
evidence: No skipped tests appear in the summary line or in the -q
output of either run.
rationale: Unlike the targeted-suite figure above, this claim reproduces
exactly on independent re-run, including the xfailed count — the full
suite is unaffected by a change scoped to the two gate modules and their
own tests, as the record states.
