---
issue: 2298
role: conformance-review
loop_state: audited
upstream:
  - path: scripts/cache_coverage.py
    sha: f95ff9431b349367a66ca86ae3723f6301bf1338
  - path: docs/issue-2298/reports/performance-engineering.md
    sha: f95ff9431b349367a66ca86ae3723f6301bf1338
  - path: docs/issue-2298/reports/performance-engineering/deviation-log.md
    sha: 8ebe7874480f11f51b24efd250a713c530da71e9
subject: PR #2329 (issue-2298/performance-engineering), head commit 8ebe7874480f11f51b24efd250a713c530da71e9
test: issue #2298, `## Ask` (4 items) + `## Acceptance` (gate / empty state / provenance)
result: failed
assertedBy: issue-2298/conformance-review session (Jiwon Jung), builder-blind independent re-execution
---

# issue-2298 — conformance-review record

## What was done

Builder-blind conformance review of PR #2329 against issue #2298's frozen
`## Ask` and `## Acceptance`. Extracted 10 discrete, dimension-tagged
requirements (R1-R10 in the requirement blocks below, canonical: R1-R10
below) from the issue text. Checked each by independent re-execution
rather than by re-citing the PR's own pasted provenance: fetched the PR
head into a separate worktree (`git fetch origin pull/2329/head:pr-2329-review
&& git worktree add /tmp/pr2329-check pr-2329-review`, commit
`8ebe7874480f11f51b24efd250a713c530da71e9`), ran the declared gate there,
re-ran `scripts/cache_coverage.py`'s core functions directly against a
live real session log the PR's own report does not cite
(`on-the-record-issue-2298-performance-engineering.session.20260825T130232.2938760.log`),
independently re-derived the diet's parse-equivalence claim against
`trajectory_analyzer.analyze()`, and confirmed on disk that the 12 named
external consumer projects and the cited 0-byte empty-state log genuinely
exist. Full derivation of each check is in the requirement blocks below,
each carrying its own `derived:`/`canonical:` tag and command output.

## Why

The role protocol requires this review to check the artifact, not the
builder's account of it. Re-executing every checkable claim in a separate
worktree against data the PR's own report did not cite (a different,
still-growing session log; a fresh worktree clone) is what makes the
Present verdicts below trustworthy rather than a restatement of the PR
description. That independent re-execution is what surfaced the one gap
this review found (canonical: R7 below) — the declared gate
(`tests/test_behavior_metrics.py`) ran and passed (canonical: R7 below,
`derived: python3 -m pytest tests/test_behavior_metrics.py -q` -> `7
passed`), but inspecting what that file actually tests (canonical: R7
below) showed it does not establish what the Acceptance line implies it
establishes.

## Upstream basis

- `scripts/cache_coverage.py` — the code under review; untracked on this
  branch, read via `git show pr-2329-review:scripts/cache_coverage.py`
  (canonical) and executed directly from the `/tmp/pr2329-check` worktree
  checked out from that same ref, sha `f95ff9431b349367a66ca86ae3723f6301bf1338`.
- `pr-2329-review:docs/issue-2298/reports/performance-engineering.md` and
  `pr-2329-review:docs/issue-2298/reports/performance-engineering/deviation-log.md`
  — untracked on this branch (canonical: `git show
  pr-2329-review:docs/issue-2298/reports/performance-engineering.md`, this
  session, confirms the content quoted in R3/R9/R10 below); sha
  `f95ff9431b349367a66ca86ae3723f6301bf1338` /
  `8ebe7874480f11f51b24efd250a713c530da71e9` respectively.
- `tests/test_behavior_metrics.py` and `scripts/behavior_metrics.py`, both
  tracked on this branch, pre-existing at commit `99271246` (issue #1504)
  — read to determine what the declared Acceptance gate actually exercises
  (canonical: R7 below).
- `trajectory_analyzer.py` (issue #2214), tracked on this branch — reused
  directly (not reimplemented) to independently re-verify the diet's
  parse-equivalence claim (canonical: R5 below).
- Real session logs under `$MUSTER_WORKSPACE_ROOT`, sha: n/a (log files,
  not repo-tracked commits) — used for independent re-execution, distinct
  from the specific logs the PR's own report cites (canonical: R1/R9/R10
  below).

## Open findings

- OF-1 (blocks a clean pass, canonical: R7 below): the declared Acceptance
  gate `tests/test_behavior_metrics.py` passes but carries zero coverage
  of `scripts/cache_coverage.py` (derived: `grep -rn cache_coverage
  tests/` from `/tmp/pr2329-check`, this session, no matches — see R7).
  Resolution path: either extend the test suite with coverage for
  `usage_turns`/`cache_summary`/`diet_events`/`diet_log_bytes`, or correct
  the issue's Acceptance `gate:` line to name a file that actually covers
  this delivery.
- OF-2 (not blocking; carried forward from the PR's own record, canonical:
  `pr-2329-review:docs/issue-2298/reports/performance-engineering.md:159-171`,
  re-verified in R9 below): `static_payload_fraction` on
  `my-travel-issue-5-product-discovery` measured highest of the sampled
  sessions, still inside the SLO floor stated in that record. No
  independent action needed; noted so a future larger-sample re-run
  doesn't re-discover it as new.

## Next steps

None beyond OF-1's resolution path above — `loop_state: audited` is
terminal for this record kind: all 10 extracted requirements carry a
verdict below (canonical: R1-R10 below), none deferred pending further
access.

## What did not work

My first attempt to reproduce the PR's exact host-session table row
failed: the cited session log
(`on-the-record-issue-2298-performance-engineering.session.20260825T130232.2938760.log`)
had grown since the PR's report was written — an append-only log, not a
snapshot (derived: `ls -la` on that path, this session, showed 771128
bytes vs. the 498424-byte before-size the PR's report cites for the same
path, canonical: R10 below). Re-running against the grown file
necessarily produced different absolute numbers than the PR's cited row
(this session: 67 turns / 0.9817 hit share; PR's report: 38 turns / 0.971
— canonical: R9 below). This is expected drift on an append-only log, not
a discrepancy in the code; switched to verifying the *mechanism*
(cache_summary, diet_log_bytes, parse-equivalence) produces correct,
self-consistent output on this later log state instead of trying to match
the PR's exact row.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2298's `## Ask` and `## Acceptance` sections (one Ask item bundled an "if X, do Y" conditional) into the 10 one-obligation-per-line, dimension-tagged requirement blocks below (canonical: R1-R10 below — count derived by direct enumeration of the `---`-delimited blocks in this file); kept Ask #1's conditional fallback clause as its own item (R2) with the dependency stated inline rather than merging or dropping it; no summary line met the 3+-subpoint drop threshold.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used Test/Demonstration (independent re-execution of `cache_coverage.py` and the named gate, in a separate worktree, against data the PR itself did not cite) for R1, R5, R7, R8, R10; Inspection (reading the diff/code directly) for R4, R6; Analysis (log-format grep + cross-referencing external project directories) for R2, R3, R9 (canonical: R1-R10 below).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Surface (not Present) to R7 per rule 1 — the named gate exists and passes, but does not fire on the condition the Acceptance line names (validating this delivery); re-checked that call once against the current artifact (grep rerun, pytest rerun) per rule 6 before finalizing, since a stale/false-positive grep was plausible (canonical: R7 below).
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every verdict below cites file:line/hunk plus the commit sha actually read (`f95ff943...` or `8ebe7874...`), and evidence was independently re-derived (fresh worktree, a session log the PR's own report doesn't cite) rather than re-citing the PR's own pasted output as if it were this review's evidence (canonical: R1-R10 below).
skill-verdict: conformance-review-finding-record — applied: invoked; wrote the per-requirement `---`-delimited blocks below into this same file, each carrying requirement/spec_ref/verdict/evidence/rationale (and spec_vs_built where the verdict is not Present) (canonical: R1-R10 below).
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration was feasible (PR touches 2 new files + 1 report; issue names 10 extractable requirements total, canonical: R1-R10 below) — no sampling scope needed.
skill-verdict: conformance-review-severity-classification — not-applicable: scope was not explicitly extended into risk-weighting; this is ordinary fidelity-checking against a frozen Acceptance.
skill-verdict: implementation-audit — not-applicable: this session already runs the dedicated conformance-review-* skill family for the same builder-blind evaluator function issue #2298's role protocol assigns; implementation-audit's separate two-session builder-claim-extraction protocol is not part of this issue's workflow.
other mounted skills: not triggered (dataviz, code-review, simplify, security-review, run, and the remaining catalog entries do not apply to a read-only conformance review of an already-written PR).

---
requirement: Ask #1 (primary) — measure per-session cache-hit share and static-payload fraction from real session logs in consumer conditions
spec_ref: issue #2298, `## Ask`, item 1, first clause
verdict: Present
evidence: |
  `scripts/cache_coverage.py:341-400` (`usage_turns`, `cache_summary`,
  `session_cache_summary`) at sha `f95ff9431b349367a66ca86ae3723f6301bf1338`.
  Independently re-run this session in `/tmp/pr2329-check` against a live
  host log the PR's own report does not cite:

  derived: `python3 -c "import sys; sys.path.insert(0,'scripts'); import cache_coverage as cc; print(cc.session_cache_summary('<host-log>'))"`
  ```
  {'turns': 67, 'total_input_tokens': 134, 'total_cache_read_input_tokens': 6595198,
   'total_cache_creation_input_tokens': 122673, 'cache_hit_share': 0.9817,
   'static_payload_fraction': 0.0171, 'no_repetition': False, ...}
  ```

  Separately confirmed the 12 external consumer projects the PR's report
  claims to have sampled genuinely exist:

  derived: `for p in arcade-dodger my-travel tm-dicequest skill-repository soongsil-course-registration project-rich legal-compliance-rulebook northpole-harness-fixture performance-dashboard repo-status-board tm-webfolio pilot-devdigest; do ls -d $MUSTER_WORKSPACE_ROOT/*$p*; done`, this session:
  ```
  /home/jwjung/.tokenmaxxxer/work/arcade-dodger-issue-1-implementation
  /home/jwjung/.tokenmaxxxer/work/my-travel-issue-11-product-discovery
  /home/jwjung/.tokenmaxxxer/work/tm-dicequest-issue-1-product-discovery
  /home/jwjung/.tokenmaxxxer/work/skill-repository-issue-111-observability
  /home/jwjung/.tokenmaxxxer/work/soongsil-course-registration-issue-15-implementation
  /home/jwjung/.tokenmaxxxer/work/project-rich-issue-113-implementation
  /home/jwjung/.tokenmaxxxer/work/legal-compliance-rulebook-issue-13-legal-compliance
  /home/jwjung/.tokenmaxxxer/work/northpole-harness-fixture-issue-20-implementation
  /home/jwjung/.tokenmaxxxer/work/performance-dashboard-issue-12-implementation
  /home/jwjung/.tokenmaxxxer/work/repo-status-board-issue-58-implementation
  /home/jwjung/.tokenmaxxxer/work/tm-webfolio-issue-3-brand-design
  /home/jwjung/.tokenmaxxxer/work/pilot-devdigest-issue-4-implementation
  ```
  (12 of 12 resolved — none missing.)
rationale: independent re-execution against data the PR did not cite reproduced a sane, internally-consistent cache_hit_share, and the 12 external projects the PR's report claims to have sampled are real, not fabricated — the requirement's core obligation (measure real consumer-condition data, not simulate it) is met.
---
requirement: Ask #1 (conditional) — if consumer sessions can't be sampled directly, reproduce the consumer shape locally instead
spec_ref: issue #2298, `## Ask`, item 1, second clause
verdict: Present
evidence: R1's evidence above (canonical: R1 above) shows direct sampling of 12 real external-project sessions succeeded, so this clause's trigger condition never arose in this delivery.
rationale: this is a disjunctive fallback ("if X can't be done, do Y"); X (direct sampling) succeeded per R1, so Y is not owed. Recorded as its own item per extraction rule 5 rather than silently dropped, since its applicability is itself a check, not an assumption.
---
requirement: Ask #2 — per-turn content that repeatedly lands in cache_creation on every turn, and stabilize-or-remove it if any is found
spec_ref: issue #2298, `## Ask`, item 2
verdict: Present
evidence: |
  `scripts/cache_coverage.py:372-393` (`cache_summary`'s
  `static_payload_fraction` = cache_creation on turns after the first,
  over the full denominator) at sha `f95ff9431b349367a66ca86ae3723f6301bf1338`:
  ```python
  repeat_creation = sum(t["cache_creation_input_tokens"] for t in turns[1:])
  static_payload_fraction = (repeat_creation / denom) if (denom and n > 1) else 0.0
  ```
  Measured across 13 sessions, canonical:
  `pr-2329-review:docs/issue-2298/reports/performance-engineering.md:158-171`
  (untracked on this branch; PR #2329's branch, sha `f95ff9431b...`),
  range 0.0085-0.0834 (`static_frac` column), none breaching the record's
  own `slo_target: cache_hit_share >= 0.90` floor.
rationale: the requirement's obligation is find-then-fix-if-found; the measurement was actually run (not asserted) across 13 real sessions and no session showed cache-creation repetition severe enough to cross the SLO floor, so no fix is owed by this requirement. The separate turn-count double-count the PR found and fixed is a distinct, non-cache-coverage defect (the cited record itself states "not a cache-coverage defect, ratios were unaffected") and is not counted as this requirement's evidence.
---
requirement: Ask #3 (primary) — session logs should record the repeated per-turn field the issue's own "164 times" example names, once (or by reference) rather than per-turn
spec_ref: issue #2298, `## Consumer observation` (the "164 times" example) + `## Ask`, item 3, first clause
verdict: Present
evidence: |
  `scripts/cache_coverage.py:447-476` (`_diet_obj`/`diet_events`) strips
  `description`/`subagent_type` from `task_progress` heartbeat ticks, sha
  `f95ff9431b349367a66ca86ae3723f6301bf1338`.

  derived: `grep -c '"subagent_type"' <real session log>`, this session:
  ```
  881
  ```
  (one real log alone carries 881 `subagent_type` occurrences from
  `task_progress` re-stamps, the same shape as the issue's "164 times"
  example.)

  derived: `grep -c '"input_schema"' <same log>`, this session:
  ```
  0
  ```
  (no literal tool-JSON-schema block appears anywhere in this log format —
  ruling out the alternative reading that Ask #3 names a separate,
  unaddressed repeat class the diet missed.)
rationale: the issue's own motivating example and this session's independent grep of a real log both point at the same field pair (`task_progress`'s `subagent_type`/`description`) as the only repeated "schema-shaped" content actually present in this log format — there is no separate literal tool-schema block in these logs to have missed.
---
requirement: Ask #3 (constraint) — the diet must not lose the analyzer's (#2214) ability to parse events
spec_ref: issue #2298, `## Ask`, item 3, second clause
verdict: Present
evidence: |
  Independently re-derived in `/tmp/pr2329-check` (not reusing the PR's
  own pasted comparison): ran `trajectory_analyzer.analyze()` on the live
  host session log (current, later state than the PR's report cites) and
  again on the same log passed through `cache_coverage.diet_events()`,
  dumped to a temp file.

  derived: `orig = ta.analyze(LOG); diet_result = ta.analyze(dieted_tmp_path); diet_result['session_log'] = orig['session_log']; print('equal:', orig == diet_result)`, this session:
  ```
  equal: True
  ```
rationale: this review did not accept the PR's byte-for-byte-equivalence claim from its pasted output; it re-derived the same comparison independently against a different, later state of the same log family and got the same result, which is stronger evidence than re-citing the builder's own run.
---
requirement: Ask #4 — frozen no-side-effects constraint applies verbatim (no change to what spawn.py tees, what the CLI sends per turn, or any production ledger/gate path)
spec_ref: issue #2298, `## Ask`, item 4
verdict: Present
evidence: |
  derived: `gh pr view 2329 --json files -q '.files[].path'`, this session:
  ```
  docs/issue-2298/reports/performance-engineering.md
  docs/issue-2298/reports/performance-engineering/deviation-log.md
  scripts/cache_coverage.py
  ```
  All 3 touched paths are new files; none is `spawn.py`, any `hooks/` or
  `gates/` path, or any other existing production file.
rationale: the diff's file list is the direct check for this requirement — a constraint about what is *not* touched is verified by enumerating the full touched-path set and confirming none of it is a live/production path, done directly this session rather than trusting the PR's own "read-only, post-hoc" characterization.
---
requirement: Acceptance — gate: `tests/test_behavior_metrics.py` (this file's pass/fail is the declared acceptance gate for this delivery)
spec_ref: issue #2298, `## Acceptance`, `gate:` line
verdict: Surface
evidence: |
  `tests/test_behavior_metrics.py:1-72` (tracked on this branch, commit
  `99271246`, issue #1504) imports `scripts/behavior_metrics.py` and tests
  only:
  ```
  def test_recheck_count_from_fixture_ledger():
  def test_recheck_count_distinguishes_different_subjects():
  def test_zero_commit_session_flagged():
  def test_round_trip_counts_group_by_issue():
  def test_wait_poll_time_aggregates_per_issue():
  def test_extract_recheck_entries_reads_real_deviation_log():
  def test_extract_wait_poll_entries_reports_gap_not_derivable():
  ```
  none of which reference cache, usage, tokens, or diet.

  derived: `grep -rn "cache_coverage" tests/` from `/tmp/pr2329-check`, this session:
  ```
  (no matches, exit code 1)
  ```

  derived: `python3 -m pytest tests/test_behavior_metrics.py -q` from `/tmp/pr2329-check` (PR head), this session:
  ```
  7 passed in 25.50s
  ```
  The gate genuinely passes — matching the PR's own reported count — but
  no test in the repository imports or exercises
  `scripts/cache_coverage.py`; this gate would pass identically had that
  module never been written, or been written with an inverted
  `cache_hit_share` formula.
rationale: per conformance-review-verdict-assignment rule 1, Surface (not Present) is correct when matching-shaped evidence exists (a named gate, and it does pass) but a check of what it actually covers shows it does not fire on the condition the requirement names — here, "validate this delivery." This is the review's one substantive finding; it is a gap in the Acceptance criterion's chosen gate, not a defect in the delivered `scripts/cache_coverage.py`, which this review's own independent re-execution (R1/R3/R4/R5/R8/R10) found correct.
spec_vs_built: Acceptance names `tests/test_behavior_metrics.py` as the gate for this delivery; what was actually delivered is a gate that passes trivially (it predates and is disjoint from the new module, evidence above) plus manual "executed-live" provenance in the PR's own record that this review independently reproduced and found accurate (R1/R8/R9/R10) — real validation happened, but not through the named automated gate, and the PR adds no automated coverage for `scripts/cache_coverage.py` to any test file.
---
requirement: Acceptance — empty state: a single-turn session has no repetition; measurement reports it as such without dividing by zero
spec_ref: issue #2298, `## Acceptance`, `empty state:` line
verdict: Present
evidence: |
  derived: `python3 -c "..."` re-running `cache_summary([])` and a
  1-turn input directly against `scripts/cache_coverage.py` in
  `/tmp/pr2329-check`, this session:
  ```
  {'turns': 0, 'total_input_tokens': 0, 'total_cache_read_input_tokens': 0,
   'total_cache_creation_input_tokens': 0, 'cache_hit_share': 0.0,
   'static_payload_fraction': 0.0, 'no_repetition': True}
  {'turns': 1, 'total_input_tokens': 5, 'total_cache_read_input_tokens': 0,
   'total_cache_creation_input_tokens': 1200, 'output_tokens': 10,
   'cache_hit_share': 0.0, 'static_payload_fraction': 0.0, 'no_repetition': True}
  ```
  No exception, no division by zero, in either the 0-turn or 1-turn case.

  derived: `ls -la /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-473-conformance-review.session.20260814T150333.71405.log`, this session:
  ```
  -rw-rw-r-- 1 jwjung jwjung 0  8월 14 15:03 on-the-record-issue-473-conformance-review.session.20260814T150333.71405.log
  ```
  confirming the PR's cited real 0-byte empty-state log is not fabricated.
rationale: ran the exact edge-case inputs the requirement names against the actual code (not the PR's pasted transcript of the same commands) and got the required behavior; also confirmed the "real, not constructed" empty-state artifact the PR's record claims genuinely exists at 0 bytes.
---
requirement: Acceptance — provenance (executed-live), part 1: paste the measured cache-hit share / static-fraction table from real logs (host + cold-cache reproduction)
spec_ref: issue #2298, `## Acceptance`, `provenance:` line, first clause
verdict: Present
evidence: |
  canonical: `pr-2329-review:docs/issue-2298/reports/performance-engineering.md:158-171`
  (untracked on this branch; PR #2329's branch, sha `f95ff9431b...`):
  ```
  project                                turns hit_share static_frac no_rep calls  reps
  on-the-record-issue-2298-performance-engineering (host, this session)  38  0.971   0.026  False   0   0
  arcade-dodger-issue-6-performance-engineering    31    0.9699      0.0174  False     0     0
  my-travel-issue-5-product-discovery       67    0.9081      0.0834  False     9    81
  ```
  (13-row table total, first 3 rows shown; full table has all 12 external
  projects + host + 1 empty-state row.) Independently spot-checked this
  session: all 12 named external projects exist (R1 evidence above); a
  host-log re-run on this review's own later log state produced a
  comparable, sane `cache_hit_share` (0.9817, R1 evidence) in the same
  range as the table's row values (0.908-0.989).
rationale: the table is real measured output, not fabricated — corroborated by independently re-running the same measurement function against genuine data the PR's own report does not cite, and getting output of the same shape and plausible range.
---
requirement: Acceptance — provenance (executed-live), part 2: before/after log-size comparison for the schema diet on the same session replayed
spec_ref: issue #2298, `## Acceptance`, `provenance:` line, second clause
verdict: Present
evidence: |
  canonical: `pr-2329-review:docs/issue-2298/reports/performance-engineering.md:220`
  (untracked on this branch; PR #2329's branch, sha `f95ff9431b...`):
  ```
  {"before_bytes": 498424, "after_bytes": 489367, "reduction_pct": 1.82}
  ```
  (host session, same-session before/after; two further sessions at lines
  223 and 226 show 3.26% and 2.02% reductions.)

  Independently re-run in `/tmp/pr2329-check` against the host log's
  current (grown) state:

  derived: `cache_coverage.diet_log_bytes(<host log>)`, this session:
  ```
  {'before_bytes': 770577, 'after_bytes': 755469, 'reduction_pct': 1.96}
  ```
  same-session before/after, reduction percentage in the same 1.8-3.3% band
  the PR's report shows across its three cited sessions.
rationale: `--diet` compares one path's own before/after state, satisfying "the same session replayed" literally; independent re-run against a later state of the same log family reproduced a reduction percentage consistent with the PR's cited range, which is stronger evidence the mechanism is real rather than a hand-typed number.
