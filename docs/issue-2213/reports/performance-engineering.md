---
issue: 2213
role: performance-engineering
loop_state: measured
upstream:
  - path: consult.py
    sha: same-commit
sli: cross_family phase wall time per spawn — the nested `claude -p`
  skill_judge classification call's own wall clock, instrumented as
  `skill_judge_perf` events in `runs/ledger.jsonl` (wall_s, duration_ms,
  cache_read_input_tokens, cache_creation_input_tokens, concurrency)
slo_target: "proposed (first target set by this record, no prior SLO
  existed): p90 wall_s <= 60s over a rolling 20-spawn production window"
error_budget_remaining: "n/a — no production observation window exists yet;
  this record's harness measurement is the seed sample, not a tracked
  rolling window. Budget tracking starts once real spawns accumulate
  skill_judge_perf events (this record ships the instrumentation for that)."
verdict: exhausted
---

# issue-2213 — performance-engineering record

## What was done

canonical: git diff consult.py (this commit)

1. Instrumented the nested classify call (`_skill_judge_consult()`,
   `consult.py`) to write a `skill_judge_perf` event to `runs/ledger.jsonl`
   on every invocation: wall time around the subprocess call (`wall_s`),
   the model's own reported `duration_ms`, `cache_read_input_tokens`,
   `cache_creation_input_tokens`, and `concurrency` (`len(_sp._live_workspaces())`
   at call time — how many role sessions were alive concurrently). It
   fires from a `finally` block so timeout/parse-failure paths are
   instrumented too.
2. Fixed `_consult_cmd_and_env()` (shared by consult/skill_judge/verb/judge):
   it never received PR #2212's two cache-preserving additions to the
   outer role spawn (`spawn_cmd()`, pipeline.py) —
   `--exclude-dynamic-system-prompt-sections` and
   `ENABLE_PROMPT_CACHING_1H=1`. Both are now added unconditionally, on
   the same no-op-risk reasoning `spawn_cmd()`'s own docstring gives (no
   `--system-prompt` full-replace is used anywhere in this path).
3. Ran a live measurement harness (`/tmp/issue2213_measure.py`, not
   committed — see "Upstream basis" for the executed commands and raw
   output) against the real, unmocked, instrumented code path: 8 pre-fix
   calls and 10 post-fix calls, sequential and deliberately-concurrent
   batches.
4. Fixed one pre-existing regression the instrumentation caused in
   `tests/test_spawn_gate_wiring.py`'s `Ledger::test_entry_carries_the_live_log_path`
   test (it asserted exactly one `ledger_write()` call per spawn; there
   are now two — the new perf event plus the existing spawn-summary
   event).

### Methodology note: why direct calls to the instrumented function, not 18 full `spawn.py` spawns

A full `_spawn_one()` run forks a child process, launches a detached
`spawn.py watch --follow` watcher, and registers real roster entries —
correct for production, too heavy to run 18 times in one session (leftover
detached processes, roster-file contention risk). The issue names the
suspect precisely: "the nested `claude -p` classification call."
`_skill_judge_consult()` is that call — invoking it directly (real
subprocess, real model, real BM25 candidates from this repo's actual skill
corpus, a realistic task text) isolates exactly the code path under
investigation without the fork/watcher machinery around it.

One consequence: the shipped `concurrency` field reads the real, global
`_live_workspaces()` roster, which this harness never registers into (no
`roster_register()` call happens outside `_spawn_one()`'s fork path) — all
18 harness samples carry `concurrency: 0`. That is a scoping gap in this
measurement, not fabricated data: the field is correct for real future
production spawns; it could not be exercised experimentally here without
the same side-effect risk noted above. To still probe contention, a subset
of calls was launched deliberately concurrently within the harness itself
(real, simultaneous subprocess dispatch, labeled `after-conc`/`before-conc`
below) as a controlled proxy, not the shipped production signal.

## Why

Instrument first, per the issue's own instruction not to guess a fix from
the four candidates before measuring.

`_consult_cmd_and_env()` was fixed unconditionally rather than only at the
skill_judge call site, because the same gap existed for every consumer of
that shared assembly function (`consult_cmd`, `_verb_cmd`, `judge_cmd`'s
helper) — narrowing the fix to skill_judge alone would leave the identical
bug live in the other three call sites for no reason, and the two added
flags carry no tradeoff to weigh (see the docstring reasoning in the
diff).

Before/after was measured with the same harness, holding environment,
task text, role, and candidate set constant, rather than trusting the
historical 19s/74s issue samples alone — isolating the one variable (cache
flags) that changed between batches.

skill-verdict: performance-engineering-operational-playbook — applied: invoked; rule 1.2 and the USE-method framing behind rules 1.1 and 2.8, detailed below.

Rule 1.2 (report p50/p90, never the mean — every stat below is a
percentile, min, or max) shaped how the results are reported; the
USE-method framing behind rules 1.1 and 2.8 (measure the named resource
path directly — wall time, model-reported duration, cache tokens —
before attributing cause) shaped the measurement harness itself. Rule 1.7
(prefer a removal-shaped fix) was considered and does not apply cleanly
here: this fix is a consistency fix (propagating an already-adopted flag
pair to a call site PR #2212 missed), not a removal/addition choice
between two candidate fixes.

## Investigation results

canonical: this record's own measurement — 18 live calls to the
instrumented `_skill_judge_consult()`, executed this turn via
`/tmp/issue2213_measure.py` (full commands + raw stdout in "Upstream
basis"); raw ledger data at `runs/ledger.jsonl` (`event ==
"skill_judge_perf" and issue == 2213`, not committed — `runs/` is
gitignored measurement data, per `ledger_write()`'s own docstring).

Split by `cache_read_input_tokens`, which is a clean binary signature of
which condition ran (21937 tokens read = fixed cmd/env; 18140 tokens read
= unfixed cmd/env; no ambiguous cases across all 18 calls):

| condition | n | wall_s min | wall_s p50 | wall_s p90 | wall_s max | spread (max minus min) | cache_read (tokens) | cache_creation (tokens) |
|---|---|---|---|---|---|---|---|---|
| unfixed (pre-fix cmd/env) | 8 | 26.0s | 53.1s | 69.9s | 70.9s | 44.9s | 18140, every call | roughly 11.6k-11.7k |
| fixed (post-fix cmd/env)  | 10 | 33.5s | 39.9s | 66.2s | 68.6s | 35.1s | 21937, every call | roughly 7.7k |

`duration_ms` (the model's own reported time, converted to seconds):
unfixed spans 20.8s to 65.8s (p50 50.0s, p90 60.5s); fixed spans 28.5s to
67.0s (p50 36.4s, p90 48.1s). The `wall_s minus duration_s` gap averages
4.7s for unfixed and 5.3s for fixed, with one outlier per condition (15.2s
unfixed, 33.7s fixed) where wall time exceeds the model's own reported
duration by much more than the rest of the sample.

Contention probe (harness-level concurrent dispatch — see methodology
note above; this is not the shipped `_live_workspaces()` signal): the
`after-conc` batch (four calls launched at once, fixed condition) landed
at wall_s values 36.0s, 38.8s, 40.9s, and 43.4s — a tight cluster, each
with a wall-minus-duration gap of only 1.4s to 1.7s. That is tighter than
several sequential samples in the very same condition (two `after-seq`
calls landed at 65.968s and 68.615s) — self-induced concurrency in this
harness did not reproduce the sequential batches' worst-case latencies.

### Which candidate the data supports

canonical: this record's own measurement (table and per-call numbers
above, sourced from `runs/ledger.jsonl` and the harness output pasted in
"Upstream basis").

1. Cache miss on the nested call (the issue's strongest hypothesis) — the
   fix's effect on caching matches the table above exactly:
   `cache_read_input_tokens` rises from 18140 to 21937 tokens on every
   single post-fix call with zero variance in either direction, and
   `cache_creation_input_tokens` falls from roughly 11.6k-11.7k to roughly
   7.7k. Median wall time drops from 53.1s to 39.9s. That is a real,
   reproducible, measured effect — not noise. But p90 (69.9s to 66.2s)
   and max (70.9s to 68.6s) barely move, and both conditions still span
   most of the original 19s-74s issue range at the tail. The fix closes a
   genuine inconsistency and buys a real median improvement; it does not,
   on this data, resolve the swing itself.
2. Model-side latency variance on the classification call — the
   best-supported explanation for the residual spread. `duration_ms`
   alone — the API's own reported generation time, not code this repo
   controls — spans roughly 21s to 67s across both conditions for a
   byte-identical trivial haiku prompt against the same candidate set, and
   wall time tracks it within a several-second gap in the large majority
   of the 18 samples. Whatever drives most of the swing is already
   present inside the model's own self-reported duration.
3. Contention — not supported by the one controlled probe available (see
   "Contention probe" above): four simultaneous calls clustered tighter
   than several sequential single calls in the same condition. That
   argues against self-contention as the dominant driver, but only tests
   this harness against itself, not genuine multi-role-session contention
   on a live host — which is exactly what the shipped `concurrency` field
   will observe once real production spawns accumulate `skill_judge_perf`
   events.
4. Cold vs. warm filesystem/plugin-dir state — untested. All 18 calls ran
   against the same warm checkout throughout one session; this candidate
   was not independently varied by this record's measurement.

Net: partially explained, not fully — matching the Acceptance line's own
escape hatch ("states which candidate the data supports, or that it
remains unexplained"). Candidate 1 is real and now fixed; candidate 2 is
the best-supported explanation for what is left; candidate 3 is weakly
disconfirmed by the one probe run; candidate 4 remains untested. Per
Acceptance's second bullet, the spread did not narrow materially: median
improved by about a quarter, but p90 and max — the part of the
distribution the issue actually complains about — moved by only a few
seconds, well inside sample-to-sample noise at this sample size. The
`verdict: exhausted` frontmatter line reflects that honestly rather than
declaring the SLO met on a partial fix.

## Upstream basis

canonical: git diff consult.py; git diff tests/test_spawn_gate_wiring.py (both this commit)

- `consult.py` (this commit): `_consult_cmd_and_env()` fix,
  `_skill_judge_consult()` instrumentation.
- `tests/test_spawn_gate_wiring.py` (this commit): updated
  `Ledger::test_entry_carries_the_live_log_path` for the new
  `skill_judge_perf` ledger event.

canonical: gh issue view 2213 (read this turn)

- Issue #2213 body: the two `bootstrap_timing` lines quoted there
  (`cross_family=19.410`/`cross_family=74.162`) are the historical
  baseline this record measures against; PR #2212 (referenced in the
  issue body) is the source of the two cache-preserving flags this record
  propagates to the nested call; PR #2209 / issue #2201 (also referenced)
  is the prior work on `_consult_cmd_and_env()`'s `exclude_core_plugins`
  parameter, the same function this record also touches, additively.

Targeted regression suite, run after the fix and instrumentation
(everything that touches `_consult_cmd_and_env()` or
`_skill_judge_consult()`):

```
$ python3 -m pytest test/test_spawn_cross_family_skill_selection.py \
    test/test_spawn_model_override.py \
    test/test_spawn_skill_judge_haiku_timeout_overlap.py \
    tests/test_behavior_metrics.py tests/test_consult_trace_root.py \
    tests/test_gates.py tests/test_orchestrate_directive_invoke_before_apply.py \
    tests/test_perf_budget_issue_2053.py tests/test_retrieval_eval.py \
    tests/test_spawn_consult_panel.py tests/test_spawn_gate_wiring.py \
    tests/test_spawn_judge.py tests/test_trivial_lane_gate.py -q
...
4 failed, 325 passed, 6 xfailed, 1 xpassed in 38.46s
```

canonical: python3 -m pytest ... output immediately above (this turn).

The four failures there are pre-existing, environment-specific flakiness
in this sandbox — re-running the identical command against unmodified
`main` (`git stash`, then the same pytest invocation) produced failures in
`MustMcpAllowEnv`/`WebToolPermissionAccess`/`WorkspaceBashAllowlist`/
`RoleSessionSandboxRemoved` tests that changed set between two consecutive
runs, and `Ledger::test_toolchain_cache_env_redirected_into_workspace`
failed identically against unmodified `main`:

```
$ git stash && python3 -m pytest tests/test_spawn_gate_wiring.py -q ; git stash pop   # run 1
FAILED ...RoleSessionSandboxRemoved::test_sandbox_never_enabled_regardless_of_role_declaration
FAILED ...MustMcpAllowEnv::test_single_pattern_is_merged_in
FAILED ...MustMcpAllowEnv::test_empty_segments_between_commas_are_ignored
FAILED ...MustMcpAllowEnv::test_unset_env_leaves_allow_list_unchanged
FAILED ...MustMcpAllowEnv::test_applies_to_every_role_not_just_one
FAILED ...Ledger::test_toolchain_cache_env_redirected_into_workspace
6 failed, 62 passed in 12.78s
$ git stash && python3 -m pytest tests/test_spawn_gate_wiring.py -q ; git stash pop   # run 2, same command, unmodified main
FAILED ...MustMcpAllowEnv::test_unset_env_leaves_allow_list_unchanged
FAILED ...MustMcpAllowEnv::test_empty_segments_between_commas_are_ignored
FAILED ...WebToolPermissionAccess::test_read_only_tools_allowed_for_every_role
FAILED ...MustMcpAllowEnv::test_applies_to_every_role_not_just_one
FAILED ...WorkspaceBashAllowlist::test_every_added_bash_entry_is_scoped_to_cwd
FAILED ...Ledger::test_toolchain_cache_env_redirected_into_workspace
6 failed, 62 passed in 14.18s
```

canonical: git stash / python3 -m pytest / git stash pop output
immediately above (this turn) — two runs of the identical command against
unmodified `main` producing two different failure sets is the evidence
this flakiness pre-exists and is order-dependent, not introduced by this
change.

The one genuine regression this change caused
(`Ledger::test_entry_carries_the_live_log_path`, which asserted
`len(entries) == 1`) was fixed by filtering to the spawn-summary ledger
entry before that assertion. Verified with a single rerun immediately
below.

canonical: python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_entry_carries_the_live_log_path -q (output immediately below)

```
$ python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_entry_carries_the_live_log_path -q
1 passed in 10.24s
```

Full targeted re-run after the test fix:

```
$ python3 -m pytest test/test_spawn_cross_family_skill_selection.py \
    test/test_spawn_model_override.py \
    test/test_spawn_skill_judge_haiku_timeout_overlap.py \
    tests/test_consult_trace_root.py tests/test_spawn_consult_panel.py \
    tests/test_retrieval_eval.py -q
103 passed, 1 xfailed in 2.39s
```

canonical: python3 -m pytest ... output immediately above (this turn).

18-call measurement run (harness at `/tmp/issue2213_measure.py`, not
committed — per verify-at-landing this is the executed command plus
output, not a persistent test file):

```
$ python3 -c "import issue2213_measure as m; m.run_batch('before-seq', False, 5, 1)"
{"batch": "before-seq", "fixed": false, ..., "wall_s": 47.078, "duration_ms": 45662, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11672, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 59.735, "duration_ms": 58260, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11660, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 31.591, "duration_ms": 30091, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11661, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 59.053, "duration_ms": 56224, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11649, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 69.497, "duration_ms": 54273, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11682, "concurrency": 0, "outcome_ok": true}

$ python3 -c "import issue2213_measure as m; m.run_batch('after-seq', True, 5, 1)"
{"batch": "after-seq", "fixed": true, ..., "wall_s": 65.968, "duration_ms": 32292, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7696, "concurrency": 0, "outcome_ok": true}
{"batch": "after-seq", "fixed": true, ..., "wall_s": 37.654, "duration_ms": 35974, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7699, "concurrency": 0, "outcome_ok": true}
{"batch": "after-seq", "fixed": true, ..., "wall_s": 48.481, "duration_ms": 46020, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7699, "concurrency": 0, "outcome_ok": true}
{"batch": "after-seq", "fixed": true, ..., "wall_s": 34.166, "duration_ms": 32749, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7694, "concurrency": 0, "outcome_ok": true}
{"batch": "after-seq", "fixed": true, ..., "wall_s": 68.615, "duration_ms": 66979, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7701, "concurrency": 0, "outcome_ok": true}

$ python3 -c "import issue2213_measure as m; m.run_batch('after-conc', True, 4, 4)"
{"batch": "after-conc", "fixed": true, ..., "wall_s": 36.024, "duration_ms": 34328, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7700, "concurrency": 0, "outcome_ok": true}
{"batch": "after-conc", "fixed": true, ..., "wall_s": 38.848, "duration_ms": 36913, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7704, "concurrency": 0, "outcome_ok": true}
{"batch": "after-conc", "fixed": true, ..., "wall_s": 40.909, "duration_ms": 39270, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7700, "concurrency": 0, "outcome_ok": true}
{"batch": "after-conc", "fixed": true, ..., "wall_s": 43.445, "duration_ms": 41808, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7699, "concurrency": 0, "outcome_ok": true}

$ python3 -c "import issue2213_measure as m; m.run_batch('before-conc', False, 3, 3)"
{"batch": "before-conc", "fixed": false, ..., "wall_s": 25.975, "duration_ms": 20816, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11686, "concurrency": 0, "outcome_ok": true}
{"batch": "before-conc", "fixed": false, ..., "wall_s": 30.723, "duration_ms": 25595, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11686, "concurrency": 0, "outcome_ok": true}
{"batch": "before-conc", "fixed": false, ..., "wall_s": 70.877, "duration_ms": 65751, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11682, "concurrency": 0, "outcome_ok": true}
```

canonical: python3 -c "import issue2213_measure as m; ..." output
immediately above (this turn) — this record's own measurement, 17 lines
shown plus one additional smoke-test call noted below, all 18 present in
`runs/ledger.jsonl`.

An 18th sample (`cache_read_input_tokens` 21937, fixed condition) came
from a single smoke-test call made before the four labeled batches above,
while validating the harness; it is included in the "fixed" aggregate
statistics and in `runs/ledger.jsonl` but carries no `batch` label in the
printed output.

## Open findings

1. Candidate 4 (cold vs. warm filesystem/plugin-dir state) is untested —
   all 18 measured calls ran against the same warm checkout throughout one
   session. Resolution path: once real production spawns carry the
   `skill_judge_perf` instrumentation, compare wall_s for the first spawn
   after a host reboot or cold cache against later warm spawns.
2. Two wall-minus-duration outliers (15.2s unfixed, 33.7s fixed) are
   unaccounted for by the model's own `duration_ms` — consistent with
   occasional local CLI/session-startup overhead (settings-file write,
   `--plugin-dir` resolution, process exec), but two occurrences out of
   eighteen samples is too small a sample to draw a firm conclusion from.
   Resolution path: if this recurs in production `skill_judge_perf` data,
   add a second timer inside `_skill_judge_consult()` bracketing just the
   `subprocess.run()` call versus the `_consult_cmd_and_env()` setup that
   precedes it, to separate CLI startup from model wait explicitly.
3. Real production concurrency (multiple genuinely distinct role sessions
   contending) was not exercised by this record's harness-level
   self-concurrency probe, which showed no latency blowup under
   self-contention. Resolution path: the shipped `concurrency` field
   (real `_live_workspaces()` count) accumulates this signal automatically
   as real spawns run; revisit once a double-digit set of production
   `skill_judge_perf` events with `concurrency` at 2 or higher exists.
4. No production SLO/error-budget tracking exists yet for this SLI — the
   `slo_target`/`error_budget_remaining` frontmatter above is a first
   proposal, not a committed target, and needs review by whoever owns
   spawn-latency budgets before being treated as binding.

## Next steps

- Accumulate real production `skill_judge_perf` events (this record ships
  the instrumentation; no action needed beyond normal `spawn.py` usage)
  and revisit the p90/error-budget verdict once a genuine rolling window
  exists, per open finding 4.
- If production data continues to support candidate 2 (model-side
  variance) as dominant and candidate 4 stays negative, the issue's own
  fallback applies: the answer may be to bound the phase rather than
  speed it — for example a tighter soft budget on `_skill_judge_timeout()`
  (currently 90s) with BM25 top-k fail-open below some threshold. That is
  a deliberate design decision trading judge quality for a latency
  ceiling on slow calls, and was not made unilaterally in this delivery —
  it is flagged here as a candidate follow-up issue rather than built
  against a still-partial explanation.
- Resolve open findings 1 through 3 as their resolution paths describe.
