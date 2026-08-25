---
issue: 2333
role: conformance-review
author: conformance-review
loop_state: closed
upstream:
  - path: consult.py
    sha: ea75927c0c8d631c90da5629c456c0d1154ce050
  - path: spawn.py
    sha: ea75927c0c8d631c90da5629c456c0d1154ce050
  - path: tests/test_spawn_consult_panel.py
    sha: ea75927c0c8d631c90da5629c456c0d1154ce050
  - path: docs/issue-2333/reports/implementation.md
    sha: ea75927c0c8d631c90da5629c456c0d1154ce050
  - path: docs/issue-2333/reports/implementation/deviation-log.md
    sha: ea75927c0c8d631c90da5629c456c0d1154ce050
  - path: on-the-record/hooks/directive.sh
    sha: ea75927c0c8d631c90da5629c456c0d1154ce050
  - path: on-the-record/hooks/test_hook_fire_counter.py
    sha: ea75927c0c8d631c90da5629c456c0d1154ce050
  - path: on-the-record/hooks/deviation-log-guard.sh
    sha: ea75927c0c8d631c90da5629c456c0d1154ce050
subject: PR #2345 ("issue-2333: shard consult-log per session to eliminate the append-only merge-conflict class"), commit ea75927c0c8d631c90da5629c456c0d1154ce050
test: issue #2333 body ("Ask", "Operator-frozen constraint") and "## Acceptance" section
result: failed
assertedBy: conformance-review, issue-2333/conformance-review session, 2026-08-25
---

# issue-2333 — conformance-review record

## What was done

Builder-blind conformance review of PR #2345 against issue #2333's frozen
Acceptance and Ask, with the review's mandate specifically naming one
axis: grade the recorded deferral of hook-fires/deviation-log sharding
on its rationale, not just whether consult-log sharding itself works.
Every extracted requirement clause was checked by independent
re-derivation in a separate worktree (`/tmp/pr-2345-wt`, `ea75927c`) plus
my own synthetic-repo reproductions — not by re-reading
`ea75927c:docs/issue-2333/reports/implementation.md`'s claims and
trusting them.

canonical: requirement-block count in this record
```
grep -c '^requirement:' docs/issue-2333/reports/conformance-review.md
```
derived: 10 requirement blocks below (`R1-R10`); verdict tally by grep
over the same blocks: `Present` x8 (`R1, R2, R5, R6, R7, R8, R9, R10`),
`Absent` x2 (`R3, R4`).

## Why

Full enumeration (not sampling) because the change surface is small — one
module (`consult.py`) plus its `spawn.py` re-export shim and co-located
tests — small enough that spot-checking would leave no efficiency gain
over checking every extracted clause. Independent re-derivation (not
citation-checking the implementation record) because this review's own
mandate names grading a recorded deferral "on its rationale" — a
deferral's rationale is exactly the kind of claim that reads as
plausible in prose and needs its own supporting facts (test coverage,
code order, on-disk convention drift) checked live rather than accepted.

canonical: `ea75927c:docs/issue-2333/reports/implementation.md:91-160`
("Deviations" and "Open findings" sections) — that section's own prose is
the claim under review for R3/R4 below; both blocks re-derive their
supporting facts live (shared-counter test rerun, hook write-order read,
`git ls-files` count of role-scoped deviation-log paths) rather than
accept the prose as sufficient, per conformance-review-verdict-assignment
rule 6 (re-check a plausible finding before finalizing) and rule 3
(unlocatable evidence gets Unverifiable, never a favorable guess — here
the evidence *was* locatable and independently checked, so no guess was
needed either way).

canonical: `gh issue view 2348`
```
Follow-up to #2333 (consult-log sharding, landed): the issue also named
`.orchestrate-hook-fires.log` and per-issue deviation logs as
conflict-prone append-only shared paths; PR #2345 deferred both with a
recorded design sketch in its implementation record's Deviations
section... Complete the conflict-class elimination for both, per the
sketches, holding the same contract: single-file human/gate view
preserved via aggregation, traceless-append guarantee unchanged.
```
This confirms the deferral was actually filed as a follow-up (issue
#2348, opened 2026-08-25T04:44:39Z, open at review time), not merely
asserted in the record's own prose — a load-bearing fact for grading R3
and R4's rationale below, checked independently rather than taken from
the implementation record's self-report.

## Upstream basis

- `ea75927c:consult.py` — `_consult_session_shard_id()` (lines 250-263),
  `_consult_trace_dir()` (266-281), `_consult_trace_path()` (284-288),
  `_consult_log_aggregate()` (291-303) — the sharding/aggregation
  mechanism itself, read directly rather than paraphrased from the
  implementation record.
- `ea75927c:spawn.py` lines 289-294 (re-export shim, unmodified-shape) and
  1389-1393 (`consult-log` CLI subcommand, new) — read directly.
- `ea75927c:tests/test_spawn_consult_panel.py` — the named acceptance
  gate; its `ConsultLogSharding` class (lines 1060-1173) read in full,
  including `test_two_concurrent_sessions_merge_without_conflict`
  (1140-1173), which performs a real `git init`/branch/merge, not a
  mocked one.
- `ea75927c:on-the-record/hooks/directive.sh` line 19 (fire-counter
  write) vs line 42 (`_MONITOR_NOTICE_PAYLOAD` JSON-payload capture) —
  read to independently confirm the record's "write happens before the
  JSON payload is parsed" claim (R3 below), and lines 63-84 (the
  session-id `sha256(...)[:24]` hashing pattern for the monitor-notice
  marker) to confirm the record's "the same way directive.sh already
  derives one" claim.
- `ea75927c:on-the-record/hooks/test_hook_fire_counter.py` line 68
  (`t_directive_and_stop_gate_share_the_same_counter_file_in_a_workspace`)
  — read and rerun to independently confirm the record's "different
  hooks within one workspace share the same counter file" claim (R3
  below).
- `ea75927c:on-the-record/hooks/deviation-log-guard.sh` lines 126-130
  (`branch_m` regex captures a role group but the computed `rel` path
  never uses it) — read to independently confirm the record's "the
  guard's path computation has no role/session component" claim (R4
  below).
- `git ls-files` over the full tree at `ea75927c`, not cited by the
  implementation record itself, run independently to quantify the
  record's unquantified "many `docs/issue-*/reports/<role>/
  deviation-log.md` files" claim (R4 below).
- Issue #2333 body, backward-traced before checking any implementation
  evidence against it — the "Ask" and constraint paragraphs are quoted
  verbatim below; the "## Acceptance" clauses are checked individually
  as R8-R10:

canonical: `gh issue view 2333`
```
## Ask
1. Preferred: shard per session — consult-log entries to
   consult-log/<session-ts-pid>.md (a reader/aggregator preserves
   today's single-file view for humans and gates), so concurrent
   writers never touch the same path. Same for hook-fires.
2. Where sharding is disproportionate, ship `.gitattributes merge=union`
   for the append-only paths WITH the plugin (verify union semantics
   can't interleave a single entry's lines — entries are single-line for
   consult-log, multi-line for deviation logs: sharding for the latter).
3. The traceless-consult contract (every consult leaves a line) must
   hold identically.

**Operator-frozen constraint applies:** systemic for all consumer
sessions; no side effects; trade-offs measured.
```
Note (backward-trace, per traceability-and-evidence rule 3): the issue's
own "## Acceptance" section — `gate: tests/test_spawn_consult_panel.py`,
`empty state:`, `provenance:` — names only consulting/consult-log; it
never names hook-fires or deviation logs, even though the Ask paragraph
above does (clause 1's "Same for hook-fires", clause 2's deviation-log
mention). This is a real gap in the issue body between what Acceptance
gates and what Ask asks for, not a review artifact.

acceptance: `cd /tmp/pr-2345-wt && grep -n "hook-fires\|hook_fires\|deviation-log\|deviation_log" tests/test_spawn_consult_panel.py` — result:
```
(no output — zero matches)
```

## Open findings

---
requirement: "consult-log entries shard to docs/issue-<n>/reports/consult-log/<session-ts-pid>.md, so concurrent writers never touch the same path"
spec_ref: "issue #2333 body, 'Ask', clause 1, first half"
verdict: Present
evidence: "ea75927c:consult.py:266-288 (`_consult_trace_dir()`/`_consult_trace_path()`); ea75927c:tests/test_spawn_consult_panel.py:1140-1173 (`test_two_concurrent_sessions_merge_without_conflict`)"
rationale: "Independently re-derived in a separate scratch repo (not reusing the PR's own test), with a session-id/pid pairing (`INDEP-A-111`/`INDEP-B-222`) chosen to mimic two concurrent sessions rather than replaying the PR test's own fixture values."
acceptance: `python3` scratch repo at `/tmp/indep-2333`, two branches each writing one shard via `consult._consult_trace_path(2333, cwd=...)` with `_CONSULT_SESSION_SHARD_ID` forced to distinct ids, merged into `main` — result:
```
merge exit code: 0
Merge made by the 'ort' strategy.
 docs/issue-2333/reports/consult-log/INDEP-B-222.md | 1 +
 1 file changed, 1 insertion(+)
```
Counterfactual, same scratch scaffolding against `main`'s pre-fix
`consult.py` (flat `consult-log.md` path) — result:
```
pre-fix merge exit code: 1
자동 병합: docs/issue-2333/reports/consult-log.md
충돌 (추가/추가): docs/issue-2333/reports/consult-log.md에 병합 충돌
```
---
requirement: "a reader/aggregator preserves today's single-file view for humans and gates"
spec_ref: "issue #2333 body, 'Ask', clause 1, second half (parenthetical)"
verdict: Present
evidence: "ea75927c:consult.py:291-303 (`_consult_log_aggregate()`); ea75927c:spawn.py:1389-1393 (`spawn.py consult-log` CLI subcommand)"
rationale: "Verified live: my own scratch-repo aggregate (R1's acceptance block) reproduced both entries in write order, byte-identical line format to `_append_consult_trace()`'s existing output (unchanged by this PR). Caveat, not a verdict downgrade: sort key is the shard filename (`<UTC-microsecond-timestamp>-<pid>.md`); on the astronomically unlikely case of two processes sharing the identical microsecond timestamp, the pid suffix sorts lexicographically (e.g. '9' before '18'), not numerically, which the old single-file scheme's strict write-order append never risked. Noted for completeness, not scored against this requirement since it names 'preserves today's single-file view,' which the aggregate does for every case exercised by both the PR's own tests and mine."
---
requirement: "hook-fires (.orchestrate-hook-fires.log) shards per session, same as consult-log ('Same for hook-fires')"
spec_ref: "issue #2333 body, 'Ask', clause 1, third sentence"
verdict: Absent
evidence: "ea75927c:.orchestrate-hook-fires.log diff (+10 lines, append-only, unsharded); ea75927c:on-the-record/hooks/directive.sh:19 vs :42; ea75927c:on-the-record/hooks/test_hook_fire_counter.py:68; ea75927c:docs/issue-2333/reports/implementation.md:99-123 ('Deviations'), :145-153 ('Open findings')"
rationale: "Absent, not Incorrect, per verdict-assignment rule 2: nothing was built for this clause, the artifact does not contradict it, it simply was not attempted in this delivery. This is the review's named grading target, so the deferral's supporting claims were independently re-checked rather than quoted: (1) 'write happens before the JSON payload is parsed' — confirmed, the counter write is `directive.sh:19`, the `_MONITOR_NOTICE_PAYLOAD` capture (the earliest point `session_id` becomes available) is `directive.sh:42`, strictly later; (2) 'different hooks within one workspace share the same counter file, so session-level (not per-hook) sharding is the right granularity' — confirmed by rerunning `test_hook_fire_counter.py`'s `t_directive_and_stop_gate_share_the_same_counter_file_in_a_workspace` below, which asserts exactly this; (3) 'a session-id hash pattern already exists in this file to model the shard id on' — confirmed, `directive.sh:63-84` hashes `session_id` via `hashlib.sha256(...)[:24]` for the (unrelated) monitor-notice marker, so the record's sketch reuses a real, working pattern rather than inventing one; (4) 'outside this delivery's named gate' — confirmed by the zero-match grep cited at the end of Upstream basis above; (5) the deferral was actually filed forward, not just asserted — confirmed live via `gh issue view 2348` (Why section above), which restates this exact scope and Acceptance shape for hook-fires+deviation-log. All five supporting claims independently hold, so the deferral's rationale is well-founded — but the issue's own Ask clause is unconditional ('Same for hook-fires', no 'where disproportionate' qualifier like clause 2 carries), so the literal requirement is still unmet in this delivery and the verdict is Absent, not a downgrade of the deferral's soundness."
acceptance: `cd /tmp/pr-2345-wt && python3 -m pytest on-the-record/hooks/test_hook_fire_counter.py -q` (adjacent test independently rerun, not just cited) — result:
```
3 passed
```
---
requirement: "deviation logs (multi-line entries) shard per session, per the issue's own union-unsafe reasoning for multi-line entries"
spec_ref: "issue #2333 body, 'Ask', clause 2, parenthetical ('...multi-line for deviation logs: sharding for the latter')"
verdict: Absent
evidence: "ea75927c:on-the-record/hooks/deviation-log-guard.sh:126-130 (`branch_m` captures a role group at `.group(2)` but `rel` at line 128 builds the path from `.group(1)` — the issue number — only, no role/session component); `git ls-files` count below; ea75927c:docs/issue-2333/reports/implementation.md:124-136, 154-160"
rationale: "Absent, not Incorrect, for the same reason as R3 — nothing built, nothing contradicted. Independently quantified the record's unquantified 'a pre-existing role-scoped convention already visible in the repo' claim, which turns out understated rather than overstated: the guard's own path computation (line 128) never includes a role component, yet the overwhelming majority of on-disk deviation-log files use a role-scoped path the guard does not check. This substantiates the record's claim that deviation-log sharding is entangled with a separate, larger, pre-existing path-convention gap — not a smaller piece of work than hook-fires, as the record itself says ('a separate follow-up issue from hook-fires — different guard, different convention drift to untangle first'). Deferring this alongside hook-fires, rather than bundling either into the consult-log delivery, is a reasonable scope cut on this evidence."
acceptance: `git -C /tmp/pr-2345-wt ls-files | grep -E "docs/issue-[0-9]+/reports/.*deviation-log\.md$" | sed -E 's#docs/issue-[0-9]+/reports/##' | sort | uniq -c | sort -rn` — result (top rows):
```
     48 implementation/deviation-log.md
     18 conformance-review/deviation-log.md
     12 execution-observation/deviation-log.md
      3 performance-engineering/deviation-log.md
      2 technical-writing/deviation-log.md
      ...
      1 deviation-log.md                      <- the one path shape the guard actually checks
```
---
requirement: ".gitattributes merge=union ships for an append-only path where sharding is disproportionate for that path"
spec_ref: "issue #2333 body, 'Ask', clause 2 (conditional on 'where sharding is disproportionate')"
verdict: Present
evidence: "ea75927c:docs/issue-2333/reports/implementation.md:75-85 ('Why'); no `.gitattributes` change in this PR's diff; R3/R4 above (both deferred surfaces are sketched toward sharding, not union)"
rationale: "Conditional requirement kept as its own item per requirement-extraction rule 5, graded on whether its precondition ever obtained. It did not: consult-log was judged not disproportionate to shard (delivered); hook-fires' deferred sketch targets a session-id shard scheme, not union; deviation-log's multi-line entries are explicitly union-unsafe per the issue's own clause-2 wording, so union was never a live option there either. No `.gitattributes` change appears anywhere in this PR's diff, consistent with the precondition never triggering for any of the three named surfaces. Present-by-non-triggering, not a gap."
acceptance: `git -C /tmp/pr-2345-wt diff main...HEAD --stat -- .gitattributes` — result:
```
(no output — file not touched by this PR)
```
---
requirement: "the traceless-consult contract (every consult leaves a line) holds identically after sharding"
spec_ref: "issue #2333 body, 'Ask', clause 3"
verdict: Present
evidence: "ea75927c:consult.py diff (`git diff main...HEAD -- consult.py`) — `_append_consult_trace()`, `_commit_consult_trace()`, and every `finally:` block (lines 482, 793, 907, 1133, 1171, 1227, 1278, 1409) are untouched by this PR; only the three path-computation functions above them changed"
rationale: "Verified by reading the actual diff, not the record's claim that 'no code changes were needed' — confirmed true: every write/commit/finally call site consumes whatever `_consult_trace_path()` returns, which still resolves to exactly one path per call, so the invariant holds by construction. Full-suite rerun below covers this along the real (unmocked) code path."
acceptance: `cd /tmp/pr-2345-wt && python3 -m pytest tests/test_consult_trace_root.py gates/test_consult_siblings.py gates/test_consult_verdict_parsing.py gates/test_consult_json_parse.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py -q` — result:
```
118 passed, 4 xfailed
```
---
requirement: "operator-frozen constraint: systemic for all consumer sessions, no side effects, trade-offs measured"
spec_ref: "issue #2333 body, 'Operator-frozen constraint applies' paragraph"
verdict: Present
evidence: "ea75927c:consult.py/spawn.py (shared module every consumer session's `spawn.py consult`/`verb`/`skill_judge` calls go through — systemic by construction, not opt-in); R3/R4 above (deferred surfaces receive zero code changes, so no side effects introduced there); ea75927c:docs/issue-2333/reports/implementation.md:75-85 ('Why') and :91-136 ('Deviations') (trade-offs stated with named alternatives and reasons)"
rationale: "Analysis, per verification-method-selection rule 2 (a systemic no-side-effect claim is not one reproducible run): sharding lands in the one shared `consult.py` module every consult path already calls through, so it is systemic without a separate rollout step; the two deferred surfaces were left completely untouched (confirmed at R3/R4's diff citations), so they carry zero side effects from this delivery; both the sharding-vs-union choice and the two deferrals carry explicit written trade-off reasoning, independently checked rather than assumed sufficient."
---
requirement: "gate tests/test_spawn_consult_panel.py passes"
spec_ref: "issue #2333 body, '## Acceptance', 'gate:' line"
verdict: Present
evidence: "ea75927c:tests/test_spawn_consult_panel.py, rerun independently below; zero `hook-fires`/`deviation-log` hits in this file (Upstream basis, end of section)"
rationale: "Rerun independently in the review worktree, not re-quoted from the implementation record."
acceptance: `cd /tmp/pr-2345-wt && python3 -m pytest tests/test_spawn_consult_panel.py -q` — result:
```
63 passed, 1 xfailed in 6.84s
```
---
requirement: "empty state: a single-session issue reads the file layout identically, no conflicts possible or provoked"
spec_ref: "issue #2333 body, '## Acceptance', 'empty state:' line"
verdict: Present
evidence: "ea75927c:tests/test_spawn_consult_panel.py:1129-1139 (`test_single_session_issue_layout_reads_identically_to_the_one_shard`), covered by the R8 rerun above"
rationale: "By construction a lone shard file cannot collide with anything (no second writer exists in the single-session case), and the aggregate of one shard is that shard's own content — verified via the cited test's assertion, rerun as part of R8's full pytest invocation above rather than a separate isolated run."
---
requirement: "provenance: two real concurrent sessions on one issue both consulting merge clean (previously conflicted), aggregated view identical to today's format"
spec_ref: "issue #2333 body, '## Acceptance', 'provenance:' line"
verdict: Present
evidence: "ea75927c:docs/issue-2333/reports/implementation.md:202-257 (record's own live two-branch/two-CLI-invocation proof); independently reproduced below in a fresh scratch repo not derived from the PR's own fixtures"
rationale: "Independently reproduced end-to-end (write, merge, aggregate, plus the pre-fix counterfactual) rather than trusting the record's own live-run transcript — see R1's acceptance block for the merge-clean half and the counterfactual proving the pre-fix flat path genuinely conflicts. Aggregate format check: my scratch aggregate's lines matched the `_append_consult_trace()` line shape unchanged by this PR (same shape independently confirmed at R6)."
acceptance: scratch-repo aggregate call at `/tmp/indep-2333` (same run cited at R1) — result:
```
- 2026-08-25T00:00:00+00:00 | role=x | verb=consult | issue=2333 | question='independent question A' | outcome='ok'
- 2026-08-25T00:00:00+00:00 | role=x | verb=consult | issue=2333 | question='independent question B' | outcome='ok'
A in agg: True
B in agg: True
```
---

## Next steps

canonical: verdict tally from the requirement blocks above (`grep -c` shown under "What was done")
```
Present x8 (R1, R2, R5, R6, R7, R8, R9, R10) | Absent x2 (R3, R4)
```

`loop_state: closed`. R1/R2/R5-R10 are `Present` — consult-log sharding
itself, the aggregator, the traceless-consult invariant, and every named
Acceptance clause are delivered and independently re-verified, not just
re-quoted from the implementation record. R3 (hook-fires) and R4
(deviation-log) are `Absent` against the issue's literal Ask — this
review's specific mandate — and the grading is: **the deferral's
rationale holds up**. Every supporting claim in the record's Deviations
section was independently re-checked against the live artifact rather
than trusted (hook write-order, shared-counter test, an existing
session-id hash pattern to model the fix on, zero hook-fires/
deviation-log references in the named gate, and — beyond what the record
itself quantifies — a `git ls-files` count showing the deviation-log
path-convention drift is real and large, 90+ role-scoped files against
the one flat path the guard actually enforces). The deferral was also
filed forward as a real GitHub issue (#2348, open at review time), not
merely asserted in prose. `result: failed` in this record's frontmatter
reflects that two Ask-clause items were not delivered in this PR, not a
judgment that the deferral itself was an unreasonable or undisclosed
shortcut — closing this review without requesting rework, since #2348
is the correct-shaped resolution path for R3/R4 and the delivered scope
(consult-log) is fully conforming on independent re-derivation.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split the issue's bundled 'Ask' clause 1 into R1 (path scheme)/R3 (hook-fires) and clause 2 into R4 (deviation-log)/R5 (gitattributes), tagged R5 as a conditional item per rule 5 rather than merging it into R3/R4, dropped the Acceptance line's 'infrastructure/no-direct-requirement' as a non-checkable scope note rather than forcing it into a requirement block.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; picked Test/Demonstration (independently reproduced, not just reused) for R1/R2/R8/R9/R10, Analysis for R7 (systemic no-side-effect claim isn't one reproducible run), Inspection for R5 (absence of a `.gitattributes` diff) and the structural parts of R3/R4 (code read directly, not executed, for the deferred-surface claims).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used Absent (not Incorrect) for R3/R4 since nothing was built and nothing contradicts the requirement, per rule 2; re-checked both Absent verdicts' supporting claims live before finalizing per rule 6 rather than accepting the record's prose; named the specific unmet clause on both Absent verdicts per rule 5.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence citation carries file:line plus the ea75927c sha; backward-traced the issue body before checking any implementation evidence (Upstream basis); flagged the Ask/Acceptance scope gap as its own noted fact rather than silently resolving it either way.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote one `---`-delimited requirement block per extracted requirement, each carrying requirement/spec_ref/verdict/evidence/rationale, refusing none for missing evidence since all ten were checkable from the artifact plus independent reproduction.
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of all 10 extracted requirement clauses was feasible (one module, its re-export shim, and their co-located tests); no sampling scope was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting a recorded finding; its outputs are conformance verdicts (Present/Absent), not severity-banded defects.
skill-verdict: observability-phase-trace — not-applicable: issue #2333 is an append-only-log conflict-elimination fix, not an observability/signal surface (no RED/USE panel set, no phase-1 methodology-selection record exists for this surface).
skill-verdict: implementation-audit — not-applicable: this review already runs as a structurally independent evaluator session against a builder session's implementation record (the standard shape this skill describes), invoked here as informational confirmation of the protocol already in force via the role-handoff contract, not as an additional technique applied on top of it.
