---
issue: 2298
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2298/reports/performance-engineering.md
    sha: f95ff9431b349367a66ca86ae3723f6301bf1338
  - path: scripts/cache_coverage.py
    sha: f95ff9431b349367a66ca86ae3723f6301bf1338
subject: PR #2329 (issue-2298, "measure consumer-condition cache coverage, fix usage double-count, diet log repeats"), commits f95ff9431b34/8ebe7874480f, branch issue-2298/performance-engineering, parent 972997f44277
test: independent re-execution of 3 of the 12 cache_hit_share consumer-session measurements, the per-turn message.id double-count repro, and the diet parse-equivalence oracle cited in docs/issue-2298/reports/performance-engineering.md (untracked in this tree -- lives on branch issue-2298/performance-engineering at commit f95ff9431b34, PR #2329) -- commands and outputs below, run in a fresh git worktree checkout of the PR branch, against real session logs under $MUSTER_WORKSPACE_ROOT, independent of the PR's own pasted output
result: passed
assertedBy: execution-observation session for issue-2298, independent of PR #2329's authoring (performance-engineering) session
---

# issue-2298 — execution-observation record

## What was done

canonical: `git fetch origin pull/2329/head:pr-2329-review` and
`git worktree add /tmp/pr2329-review pr-2329-review` -- an independent
checkout of the PR's `scripts/cache_coverage.py` and its
`trajectory_analyzer.py` dependency, never the PR's pasted transcripts
taken as given. Spawning prompt scoped this observation to three
specific re-executions (not every claim in the record): the
`cache_hit_share` measurement on 3 of the record's 12 sampled consumer
sessions, the ~1.8x per-turn double-count repro, and the diet
parse-equivalence oracle.

### Declared gate — reproduced

acceptance: `python3 -m pytest tests/test_behavior_metrics.py -q` (PR
worktree) -- result:
```
7 passed in 0.89s
```
matches the record's cited count. `tests/test_behavior_metrics.py`
predates this PR (`git log` shows it introduced by issue-1504, commit
`99271246`) and this PR does not modify it -- confirms the declared gate
is a real pre-existing acceptance surface, not authored to pass.

acceptance: `python3 -m pytest tests/test_trajectory_analyzer.py -q` --
result:
```
29 passed in 0.92s
```
matches the record's "unaffected" claim.

acceptance: `python3 -m py_compile scripts/cache_coverage.py` -- result:
`compile OK`, matches.

### cache_hit_share on 3 of the 12 consumer sessions — confirmed exact

canonical: for each project name the record cites, resolved the actual
session-log file under `$MUSTER_WORKSPACE_ROOT` independently (some
project workspaces have more than one `.session.<ts>.<pid>.log`
generation; the record's numbers matched the *earliest* generation in
every case checked) and re-ran `scripts/cache_coverage.py <path> --json`
from the PR worktree.

`arcade-dodger-issue-6-performance-engineering`
(`.session.20260822T125032.3927558.log`, first generation):
```
{"turns": 31, "total_cache_read_input_tokens": 2284036,
 "total_cache_creation_input_tokens": 70907, "cache_hit_share": 0.9699,
 "static_payload_fraction": 0.0174, "no_repetition": false}
```
Record claims: turns=31, hit_share=0.9699, static_frac=0.0174 — exact
match. (The second generation on this workspace, `.20260822T125858...`,
gives turns=16/hit_share=0.953 — a different session; the record's row
is unambiguously the first generation.)

`my-travel-issue-5-product-discovery`
(`.session.20260820T093412.3707972.log`, first generation):
```
{"turns": 67, "total_cache_read_input_tokens": 3356925,
 "total_cache_creation_input_tokens": 339390, "cache_hit_share": 0.9081,
 "static_payload_fraction": 0.0834, "no_repetition": false,
 "distinct_task_calls": 9, "progress_repeats": 81}
```
Record claims: turns=67, hit_share=0.9081, static_frac=0.0834, calls=9,
reps=81 — exact match, including the `subagent_field_repetition`
9-real-calls/81-heartbeat-repeats pair (the literal 164-vs-1 misread
class from the issue body).

`tm-dicequest-issue-75-implementation` (only one generation exists):
```
{"turns": 106, "total_cache_read_input_tokens": 12139748,
 "total_cache_creation_input_tokens": 134874, "cache_hit_share": 0.989,
 "static_payload_fraction": 0.0085, "no_repetition": false}
```
Record claims: turns=106, hit_share=0.989, static_frac=0.0085 — exact
match.

All 3 sampled rows reproduce bit-for-bit from the raw session logs,
independent of the record's own pasted table.

### ~1.8x double-count repro — phenomenon confirmed on independently-sourced data

canonical: the record's own host numbers (turns 61→38,
`cache_hit_share` 0.9675→0.9710 on its authoring session's log) cannot
be bit-for-bit reproduced after the fact -- that log is a live, growing
tee (`spawn.py`'s `_session_log_path()`) that kept accumulating lines
after the PR's authoring session took its measurement and continued to
commit/push/open the PR; re-running `cache_coverage.py` against that
same path today gives `turns=67, hit_share=0.9817` against the file's
*current* length, not the number the record captured mid-session. This
is a property of "host, live" measurement claims in this record kind
(the same class of non-reproducibility issue-2207's execution-observation
hit on shared-host full-suite counts), not a defect in
`cache_coverage.py`, and re-deriving the exact original figure is not
possible from a mutated, uncommitted log file. It is also outside this
session's delegated scope (which asked for the *repro*, not a
bit-exact replay of that specific session's now-stale numbers) -- see
Open findings.

What *is* independently checkable is the mechanism and its order of
magnitude, on a fresh host log this session's own spawn produced (this
session's own live tee, cold-cache from this session's own spawn --
genuinely independent data, not the PR author's session):

acceptance: the record's own `message.id`-grouping one-liner, run
verbatim against this session's own log
(`on-the-record-issue-2298-execution-observation.session.20260825T132244.4096458.log`)
-- result:
```
messages with >1 content-block line: 13 of 17
max blocks per message: 2 usage-mismatch cases: 0
naive per-line count: 30 deduped message.id count: 17
```
30/17 ≈ 1.76x -- same mechanism, same order of magnitude as the record's
claimed ~1.8x (61/34 ≈ 1.79x).

acceptance: `usage_turns`/`cache_summary` before vs. after the
`message.id` dedupe, same log, direct module calls (not the CLI's final
JSON, to isolate exactly what the dedupe changes):
```
naive (no dedupe): turns=32, cache_hit_share=0.9624, static_payload_fraction=0.033
deduped (usage_turns): turns=18, cache_hit_share=0.9655, static_payload_fraction=0.0262
```
32/18 ≈ 1.78x. Confirms the fix is real and reproduces on independently-
generated data, not just the one session the PR happened to measure on.

### Diet parse-equivalence oracle — confirmed on 2 independently-chosen sessions

canonical: re-ran the oracle (`trajectory_analyzer.analyze()` on the
original vs. `diet_events()`-dieted event stream, same session, diffed)
on two sessions chosen by this observation session, not the two the
record used: this session's own live host log, and
`my-travel-issue-5-product-discovery` (chosen because it's the one
sampled session with real `task_progress` heartbeat repeats, so it
exercises *both* diet paths -- the `task_progress` field-strip and the
`usage` dedupe -- not just the usage path):
```
.../on-the-record-issue-2298-execution-observation.session.....log -> equal: True
.../my-travel-issue-5-product-discovery.session.20260820T093412.3707972.log -> equal: True
```
Both `orig == diet` (after normalizing the expected `session_log`
temp-path diff) -- confirms the diet loses no field
`trajectory_analyzer.analyze()` reads, on sessions independent of the
two the record cited.

canonical: independently verified the diet's stated recoverability
precondition for `my-travel-issue-5-product-discovery` rather than
trusting the claim -- every one of its 81 `task_progress` events carries
a non-null `task_id`, and every `task_progress` `task_id` has a matching
`task_started` event to join back to:
```
task_progress count 81
task_started count 9
task_progress missing task_id 0
progress ids not in started ids: set()
```

acceptance: `--diet` before/after bytes, `my-travel-issue-5-product-discovery`
(same log the record used) -- result:
```
{"before_bytes": 881781, "after_bytes": 853068, "reduction_pct": 3.26}
```
exact match to the record. On this session's own host log (a different
log than the record's, since that one is a moving target -- see above):
`before_bytes=202487, after_bytes=198463, reduction_pct=1.99` -- same
code path, consistent order of magnitude, independent log.

### Empty-state — confirmed exact, including on a real 0-byte artifact

acceptance: `cache_summary([])` and the 1-turn all-`cache_creation` case
-- byte-identical output to the record's pasted REPL transcript.

canonical: located the real 0-byte session log the record cites
(`on-the-record-issue-473-conformance-review.session.20260814T150333.71405.log`,
confirmed 0 bytes via `ls -la`) and ran both `cache_coverage.py <path>`
and `cache_coverage.py --diet <path>` against it directly (the record
only pastes the summary result, not the diet path on this file) --
both return without division by zero:
```
summary: turns=0, cache_hit_share=0.0, static_payload_fraction=0.0, no_repetition=true
diet:    before_bytes=0, after_bytes=0, reduction_pct=0.0
```

## Why

canonical: this role's job is to re-derive the delegated claims from raw
sources independently, not to trust the builder's pasted transcript
([[defect-verification-independence-from-upstream-verdicts]]) --
re-running found every one of the three delegated re-executions holds:
the 3 sampled `cache_hit_share` rows reproduce bit-for-bit from the raw
logs (including the `subagent_field_repetition` 9/81 pair), the
double-count mechanism and its ~1.8x order of magnitude reproduce on
this session's own independently-generated log (not just the PR
author's), and the parse-equivalence oracle holds on two sessions this
session chose rather than the two the record cited -- one of which
(`my-travel`) is the stronger case since it's the only sampled session
that exercises both diet paths at once.

canonical: the one thing this session could *not* reproduce bit-for-bit
-- the record's own host row (61→38 turns, 0.9675→0.9710) -- is a
scoping and methodology finding, not a code defect: `spawn.py`'s session
log is a live, growing tee, so a "host, live" figure captured mid-session
is inherently a snapshot of a moving target and cannot be replayed after
the session that produced it has kept writing to that same file. This
session substituted its own live log for the mechanism/magnitude check
instead, which is independent, reproducible evidence for the same claim
(the fix is real) without depending on a now-stale number.

## Upstream basis

- `docs/issue-2298/reports/performance-engineering.md` (untracked in
  this tree -- lives on branch issue-2298/performance-engineering at
  commit f95ff9431b349367a66ca86ae3723f6301bf1338, PR #2329) -- the
  record under observation.
  sha: f95ff9431b349367a66ca86ae3723f6301bf1338
- `scripts/cache_coverage.py`, `trajectory_analyzer.py` at commit
  f95ff9431b349367a66ca86ae3723f6301bf1338 (this PR, untracked in this
  tree, checked out separately via `git worktree` at
  `/tmp/pr2329-review`) -- read and executed directly, never via the
  PR's pasted diff/output alone.
  sha: f95ff9431b349367a66ca86ae3723f6301bf1338
- Real session logs under `$MUSTER_WORKSPACE_ROOT`
  (`arcade-dodger-issue-6-performance-engineering`,
  `my-travel-issue-5-product-discovery`,
  `tm-dicequest-issue-75-implementation`,
  `on-the-record-issue-473-conformance-review` [0-byte empty-state],
  and this session's own
  `on-the-record-issue-2298-execution-observation` live log) -- read and
  parsed directly by this session, independent of the record's own
  pasted script output.
  sha: n/a (log files, not repo-tracked commits)

## Open findings

- canonical: the record's host row (turns=38, `cache_hit_share`=0.971,
  `static_payload_fraction`=0.026) cannot be re-derived from the log
  path it cites today, because that log is a live tee that kept growing
  after the authoring session measured it (current re-run:
  turns=67, hit_share=0.9817 against the same path). This was outside
  this session's delegated scope (3 of 12 *consumer* sessions, not the
  host row) and is not a code defect -- `cache_coverage.py` is a
  deterministic pure function of its input events; the input itself
  moved. Resolution path: none needed for this PR's merits; a future
  session citing a "host, live" row from any record of this kind should
  treat it as a point-in-time snapshot, not a re-derivable fact, unless
  the exact log is preserved (e.g. copied) at measurement time.
- canonical: `to_ledger_event()` is a template, not wired into
  `ledger_write`/`spawn.py` (record's own stated scope limit, confirmed
  by reading `scripts/cache_coverage.py` -- no call site exists) --
  resolution path unchanged from the record: a future issue, if
  standing ledger wiring is wanted.

## Next steps

None — `loop_state: handed-off` is terminal for this role.

## What did not work

Attempted to re-derive the record's exact host-row numbers (61→38
turns) from the same log path it cites; not possible, because that log
is a live, growing artifact that continued past the point the record's
authoring session measured it (see Open findings). Substituted this
session's own live log for an independent mechanism/magnitude check
instead, which is what this role's delegated scope actually asked for.
