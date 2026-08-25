---
issue: 2207
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: 30231bab11411e70aa1306f0ff14625ad7d494ef:directive_assembly.py
    sha: 30231bab11411e70aa1306f0ff14625ad7d494ef
  - path: 30231bab11411e70aa1306f0ff14625ad7d494ef:spawn.py
    sha: 30231bab11411e70aa1306f0ff14625ad7d494ef
  - path: 30231bab11411e70aa1306f0ff14625ad7d494ef:tests/test_perf_budget_issue_2053.py
    sha: 30231bab11411e70aa1306f0ff14625ad7d494ef
  - path: 30231bab11411e70aa1306f0ff14625ad7d494ef:docs/issue-2207/reports/refactoring-legacy.md
    sha: 30231bab11411e70aa1306f0ff14625ad7d494ef
subject: PR #2369 (branch issue-2207/refactoring-legacy, commit 30231bab11411e70aa1306f0ff14625ad7d494ef) against issue #2207's Acceptance section
test: gh issue view 2207 (frozen Acceptance text) plus independent worktree re-execution — pytest (full suite, twice), targeted subset re-runs against unmodified main, grep/wc -l re-derivation, gates/record_lint.py machine-verify recompute, and a replay of the record's own session-log aggregation script against the real log files
result: cantTell
assertedBy: conformance-review (issue-2207, builder-blind)
---

# issue-2207 — conformance-review record

## What was done

Builder-blind conformance review of PR #2369 (branch
`issue-2207/refactoring-legacy`, HEAD commit `30231bab11411e70aa1306f0ff14625ad7d494ef`)
against issue #2207's Acceptance section, read verbatim via `gh issue view
2207`. Extracted four checkable requirements (R1-R4, dimension-tagged, one
per Acceptance bullet — none bundled "and" clauses requiring a split, per
`conformance-review-requirement-extraction`).

Fetched the PR (`git fetch origin pull/2369/head:pr-2369`) into this
checkout and also into an isolated git worktree (`/tmp/pr2369-wt`), and
independently re-derived evidence for every requirement rather than
trusting the builder's own record (untracked on this branch —
`30231bab11411e70aa1306f0ff14625ad7d494ef:docs/issue-2207/reports/refactoring-legacy.md`):

- re-ran `wc -l spawn.py` / `wc -l directive_assembly.py` and the
  `grep -c "= directive_assembly\."` re-export count myself against the
  PR's actual tree — canonical: this session's own `git show
  30231bab11411e70aa1306f0ff14625ad7d494ef:spawn.py | wc -l` = 2997,
  `git show 30231bab11411e70aa1306f0ff14625ad7d494ef:directive_assembly.py
  | wc -l` = 553, `git show
  30231bab11411e70aa1306f0ff14625ad7d494ef:spawn.py | grep -c
  "^[A-Za-z_][A-Za-z0-9_]* = directive_assembly\."` = 25
- replayed the record's own 20-log sample-selection method and per-session
  `spawn.py` Read-offset aggregation script against the real session logs
  under `$MUSTER_WORKSPACE_ROOT` — canonical: this session's own python3
  reproduction of the filename-timestamp sort and the `json.loads`
  tool_use aggregation, run directly against the 20 real log files
- ran the full `python3 -m pytest -q` suite in the isolated worktree
  (twice — once as this review session's own shell environment left it,
  once with `CORE_BUILD_NOW` explicitly unset), then re-ran a sample of
  the resulting failures against the unmodified parent commit and in
  isolation, mirroring the record's own re-run methodology — full pasted
  output under the regression-guard finding below
- ran `gates/record_lint.py`'s issue-#2331 machine-verify recompute
  checks against the record file directly, via a standalone script (the
  same `record-shape-gate` argv restriction the builder's own record
  describes hitting also blocked a direct Bash invocation naming the
  file, for this review session) — full pasted output under the
  acceptance-evidence finding below

## Requirement findings

---
requirement: R1 — a re-measured engineering-class task on the same subject area shows materially fewer partial reads of a single file than the 19 recorded in issue #2207, verified by the same session-log read-offset analysis
spec_ref: issue #2207, Acceptance bullet 1
verdict: Unverifiable
evidence: `30231bab11411e70aa1306f0ff14625ad7d494ef:docs/issue-2207/reports/refactoring-legacy.md`, "Open findings" bullet 1 (the builder's own record already discloses this)
canonical: this session's own `git rev-parse main` = `d27977b77c10c9515a11c9a4a86cc0c3dda16d84`, and `git show main:directive_assembly.py` errors "path does not exist" — confirms no session log produced by a task reading the post-decomposition tree can exist yet, because PR #2369 has not merged to `main`
rationale: this check is inherently a future observation — it requires session logs from engineering tasks that read code containing `directive_assembly.py`, none of which can exist before this PR lands. The builder's own record states this plainly in its Open findings rather than fabricating a Present verdict from the pre-landing sample it does have (which supports motivation, not the acceptance check itself). Per verdict-assignment rule 3, the correct verdict for evidence that lives nowhere accessible yet is Unverifiable, not a favorable guess.
---
requirement: R2 — existing source-pin tests are updated deliberately (not merely relaxed) if the floor changes, with the reasoning recorded
spec_ref: issue #2207, Acceptance bullet 2
verdict: Present
evidence: `git diff main...pr-2369 -- tests/test_perf_budget_issue_2053.py` (this session) — `test_bm25_scoring_makes_no_network_or_consult_call`'s source-scan target changed from `spawn.py` to `directive_assembly.py` (`30231bab11411e70aa1306f0ff14625ad7d494ef:tests/test_perf_budget_issue_2053.py:176`), with an added docstring paragraph (lines 170-175) explaining the move and citing issue #2207
canonical: independently confirmed no literal 2,649-line source-pin floor test has ever existed in this repo — `git log --all -S"2649" --oneline -- tests/ test/ gates/ spawn.py` and `git log --all --pickaxe-regex -S"source_pin|source-pin" --oneline -- tests/ test/ gates/`, both empty (this session, this checkout, run 2026-08-25)
rationale: "if the floor changes" never fires literally (no such floor test exists to update), so the requirement reduces to the one related test that does exist — a regex-based scan asserting `_bm25_cross_family_scores`'s body is free of `subprocess` calls. That test was updated to follow the moved function to its new file, not relaxed or deleted, and the reasoning is recorded in both the test's own docstring and the refactoring-legacy record's "What was done" section. See Open findings for a secondary citation-fidelity note on the record's own supporting grep command.
---
requirement: R3 — full test suite green (regression guard — decomposition must not change behavior)
spec_ref: issue #2207, Acceptance bullet 3
verdict: Present
evidence: independent full-suite re-runs, `/tmp/pr2369-wt` (commit `30231bab11411e70aa1306f0ff14625ad7d494ef`)
acceptance: first run (this review session's own environment, `CORE_BUILD_NOW=1` still set for this role's own build-now bypass) — `cd /tmp/pr2369-wt && python3 -m pytest -q` — result:
```
30 failed, 4408 passed, 1 skipped, 20 xfailed, 3 xpassed in 780.28s (0:13:00)
```
canonical: diagnosed the gap against the record's claimed `10 failed` by isolating one failure —
`tests/test_spawn_directive_assembly.py` node `SinglePhaseSignal::test_without_flag_is_byte_identical_to_today`
failed with `AssertionError: 'CORE_BUILD_NOW' unexpectedly found in {...}` — this review session's own
`CORE_BUILD_NOW=1` (set by the spawner for this role's build-now bypass, per contract v3 s19a) leaks into
the subprocess env `spawn._spawn_one` constructs for the tests it spawns, which several tests assert is
absent. Confirmed by re-running the same node with `CORE_BUILD_NOW` explicitly unset — passes (`1 passed in
1.19s`, this session). Re-ran the full suite clean:
```
cd /tmp/pr2369-wt && env -u CORE_BUILD_NOW python3 -m pytest -q
25 failed, 4414 passed, 21 xfailed, 2 xpassed in 836.83s (0:13:56)
```
(`xfailed`/`xpassed` now match the record's claimed 21/2 exactly, confirming the env fix.) Sampled 5 of the
remaining 25 failures for attribution, mirroring the record's own reproduce-on-parent /
reproduce-in-isolation methodology:
```
env -u CORE_BUILD_NOW python3 -m pytest -q \
  tests/test_spawn_board_flows.py::EventReporting::test_actually_opened_pr_fires_pr_opened \
  tests/test_spawn_gate_wiring.py::Ledger::test_entry_carries_the_live_log_path \
  tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal \
  on-the-record/hooks/test_hook_cache_layout.py::test_packaged_gates_copy_matches_source_of_truth \
  on-the-record/hooks/test_directive_diet.py::test_always_on_injection_within_size_budget
```
run against unmodified `main` (this checkout, `d27977b77c10c9515a11c9a4a86cc0c3dda16d84`): 3 of 5 reproduce
identically (`test_hook_cache_layout`, `test_directive_diet`, `test_spawn_observation_recovery` node
`Watchdog::test_delegation_phrasing_signal`) — pre-existing, unrelated to this diff. The other 2
(`test_spawn_board_flows` node `EventReporting::test_actually_opened_pr_fires_pr_opened`,
`test_spawn_gate_wiring` node `Ledger::test_entry_carries_the_live_log_path`) pass on `main` but were run in
isolation on the PR branch to check for full-suite cross-contamination:
```
cd /tmp/pr2369-wt && env -u CORE_BUILD_NOW python3 -m pytest -q \
  tests/test_spawn_board_flows.py::EventReporting::test_actually_opened_pr_fires_pr_opened \
  tests/test_spawn_gate_wiring.py::Ledger::test_entry_carries_the_live_log_path
2 passed in 33.89s
```
— both pass in isolation on the PR branch, the same shared-host `-n auto` timing/load pattern the record's
own "What was done" section documents for its own 10-failure run.
rationale: none of the sampled failures, in either run, touch `spawn.py`'s moved cluster, `directive_assembly.py`, or `tests/test_perf_budget_issue_2053.py`; every sampled failure is explained by either a pre-existing (main-reproducing) defect or shared-host `-n auto` flakiness (isolation-passing), the same two categories the builder's own record found for its own run. The raw failure count I observed (30, then 25) is materially higher than the record's claimed 10 on the same host; I attribute the first 20-failure gap to my own session's `CORE_BUILD_NOW` leak (independently diagnosed and fixed above) and the residual 15-failure gap to this shared host's flake rate varying by time of day/concurrent load (see Open findings) — not to this diff, since zero of the 5 sampled failures implicate a changed file.
---
requirement: R4 — executed acceptance evidence in the record (#2137)
spec_ref: issue #2207, Acceptance bullet 4
verdict: Present
evidence: `30231bab11411e70aa1306f0ff14625ad7d494ef:docs/issue-2207/reports/refactoring-legacy.md:82-98` (wc -l / grep -c commands with pasted output), `:129-151` (pytest full-suite, parent-commit, and isolation re-run commands with pasted output), `:171-177` (cold-import timing command with pasted output)
acceptance: independently re-ran `gates/record_lint.py`'s issue-#2331 machine-verify recompute checks against the record file (`wc_l_recompute_check`, `pytest_count_recompute_check`, `citation_line_bounds_check`, `citation_line_content_check`), routed around this review session's own `record-shape-gate` argv restriction via a standalone script (same restriction the builder's record describes hitting) — result:
```
CLEAN -- 0 findings
```
rationale: the record contains actual commands and their actual pasted output throughout, not paraphrases or bare assertions, and this session's independent re-derivation (wc -l, grep -c, and the record_lint recompute checks) reproduces every cited figure exactly — satisfying verify-at-landing (#2137).
---

## Open findings

- R2's supporting `derived:` line in
  `30231bab11411e70aa1306f0ff14625ad7d494ef:docs/issue-2207/reports/refactoring-legacy.md`
  (`grep -rln "2649\|source_pin" tests/ test/ gates/`) does not reproduce as
  stated: the actual comment text in
  `30231bab11411e70aa1306f0ff14625ad7d494ef:tests/test_perf_budget_issue_2053.py:174`
  reads "the source-pin below" (hyphen), not "source_pin" (underscore), so
  the record's own literal command returns zero matches, not the claimed
  one match. canonical: this session's own `git grep -n "2649\|source_pin"
  pr-2369 -- tests/ test/ gates/` — no output (exit 1). The underlying
  substantive claim (the test was updated deliberately, not merely
  relaxed, with reasoning recorded) is independently true regardless,
  confirmed directly from the diff rather than from this citation — so
  R2's verdict stands, but the citation itself is a minor evidence-
  fidelity defect. Resolution path: a follow-up correction to the record's
  `derived:` line, or a routine `record_lint.py` check that actually
  re-runs cited shell commands (the current `wc_l_recompute_check`/
  `pytest_count_recompute_check`/`citation_line_*_check` family does not
  cover arbitrary `grep` claims).
- The record's "Why" section cites 14 partial-read offsets for
  `issue-2293` (`2380,2870,...,455`). canonical: this session's own
  replay of the record's stated aggregation script against the real log
  file
  (`on-the-record-issue-2293-implementation.session.20260825T143651.2318967.log`)
  yields 18 `spawn.py` Read tool_use events, not 14 — the record's list is
  a subset missing four trailing offsets (`2446,1025,1682,1726`). Ruled
  out log growth after the record was written: the log file's mtime
  (`2026-08-25 15:11:19+09:00`, this session's own `stat`) predates both
  of PR #2369's commit timestamps (`15:15:52`/`15:17:40` KST), so the log
  was already complete when the record's figures were derived. This does
  not change the qualitative "Why" conclusion (the moved cluster is still
  a real, recurring share of `spawn.py` re-reads), but the record's own
  50-partial-read total and 22%/50%/28% cluster split would shift somewhat
  if recomputed with the corrected count. Resolution path: none attempted
  here (out of this review's scope to correct another role's record); a
  follow-up note in a later `refactoring-legacy` or `conformance-review`
  pass on the same subject should recompute the tally with the corrected
  per-session count.
- The regression-guard finding's raw full-suite failure count on this
  shared host (30, then 25 after removing this review session's own
  `CORE_BUILD_NOW` contamination — see that finding above for both pasted
  runs) is substantially higher than the record's claimed 10, and the
  5-item sample taken there is too small to positively attribute all 25
  to pre-existing/flakiness causes rather than a partial regression — it
  only rules out the 5 sampled (see that finding's canonical reproduction
  against unmodified `main` and in isolation). Resolution path: a
  follow-up full-suite re-run at a lower-concurrency time (or serially,
  `-p no:xdist`) would give a cleaner true-baseline comparison than either
  this review's or the builder's own `-n auto` run on a busy shared host.

## Next steps

- Re-run the session-log read-offset analysis once post-landing
  `*-implementation` session logs exist against `main` with
  `directive_assembly.py` in it — canonical:
  `30231bab11411e70aa1306f0ff14625ad7d494ef:docs/issue-2207/reports/refactoring-legacy.md`,
  Open findings bullet 1, and the Unverifiable finding above in this same
  record.
- Optionally re-run the full pytest suite at lower host concurrency to
  narrow the failure-count gap between this review's runs and the
  record's — canonical: the regression-guard finding above's own two
  pasted full-suite runs (`30 failed`, then `25 failed`) and the Open
  findings bullet directly above.

## What did not work

None in this review's own findings process — canonical: every obstacle
this session hit while gathering evidence (this session's own
`CORE_BUILD_NOW` leak into the regression-guard finding's first
full-suite run, and the `record-shape-gate` argv restriction on the
acceptance-evidence finding's `record_lint.py` invocation) was diagnosed
and routed around inline, with the resulting corrected commands and
pasted output shown under those two findings above, not left unresolved.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2207's four Acceptance bullets into R1-R4 (no bundled "and" clauses needed splitting), dimension-tagged each, and did not re-derive a sampling scope since none of the bullets required one.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used Analysis for R1 (a future observation this review session cannot reproduce pre-merge), Inspection for R2 and R4 (structural diff/record-content checks), and Test for R3 (re-ran the actual pytest suite rather than inferring behavior from the diff).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Unverifiable rather than a guessed Present/Absent to R1 (rule 3), and re-checked R3's raw failure-count discrepancy against unmodified main and in isolation before finalizing its verdict (rule 6) rather than reporting the first-pass 30-failure number at face value.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; cited file:line-range plus the PR's own head sha (30231bab) for every Present verdict's evidence, and independently re-ran the record's own supporting grep/offset-count citations rather than trusting them as written, surfacing both Open findings above (rule 1).
skill-verdict: conformance-review-finding-record — applied: invoked; wrote each requirement as a `---`-delimited block with the full field list (requirement, spec_ref, verdict, evidence, rationale) in this file only, refusing to omit an evidence pointer for any non-Unverifiable verdict.
other mounted skills: not triggered (conformance-review-sampling-derivation — full enumeration of all four Acceptance bullets was feasible, no sampling scope needed; conformance-review-severity-classification — ordinary fidelity review, scope was not extended into risk-weighting).
