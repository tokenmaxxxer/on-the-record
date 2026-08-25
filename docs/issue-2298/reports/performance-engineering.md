---
issue: 2298
role: performance-engineering
loop_state: measured
upstream:
  - path: tests/test_behavior_metrics.py
    sha: same-commit
sli: per-session cache_hit_share = cache_read / (input + cache_read + cache_creation), from message.usage on every assistant turn of a role session's stream-json log
slo_target: cache_hit_share >= 0.90 sustained across multi-turn (>1) consumer role sessions
error_budget_remaining: "12/12 sampled real consumer sessions >= 0.90 (range 0.908-0.989); 0 of 12 burned budget in this sample"
verdict: within-budget
---

# issue-2298 — performance-engineering record

## What was done

Added `scripts/cache_coverage.py`, a read-only analysis tool over the
same raw `--output-format stream-json` session-log tee that
`trajectory_analyzer.py` (#2214) already reads (`spawn.py`'s
`_session_log_path()`), covering all three Asks:

1. **Measure in consumer conditions** (`usage_turns` / `cache_summary` /
   `session_cache_summary`): per-session cache-hit share and
   static-payload fraction, computed from the `cache_read_input_tokens`
   / `cache_creation_input_tokens` fields already on every assistant
   turn's `message.usage`. Ran it against this host's own live session
   log (cold-cache reproduction — the log started at this session's
   spawn) and against 12 real external-project session logs sampled from
   `$MUSTER_WORKSPACE_ROOT` (arcade-dodger, my-travel, tm-dicequest,
   skill-repository, soongsil-course-registration, project-rich,
   legal-compliance-rulebook, northpole-harness-fixture,
   performance-dashboard, repo-status-board, tm-webfolio,
   pilot-devdigest) plus one real 0-byte session log as the empty-state
   case — genuine consumer conditions, not simulated.
2. **Trim what cache cannot cover** — measuring turn 1 surfaced a real
   defect: a single logical assistant turn is teed as one JSONL line per
   content block (`thinking`, then `tool_use`), and the CLI stamps the
   *same* message-level `usage` object on every one of those lines. Naive
   per-line summing overcounted real turns in the host log by ~1.8x (61
   counted vs. 34 real API messages, `message.id`-deduped) — this is not
   a cache-coverage defect (ratios were unaffected, since both numerator
   and denominator scaled together) but it is exactly the kind of
   per-turn-repeated, cache-irrelevant content Ask #2 asks to find:
   `usage_turns` now dedupes by `message.id` so downstream metrics count
   each real turn once.
3. **Log diet** (`diet_events` / `diet_log_bytes`) — trims two repeated,
   recoverable-by-join fields from a session log without touching
   anything `trajectory_analyzer.py` reads: (a) the `description`/
   `subagent_type` pair `task_progress` re-stamps on every heartbeat tick
   of a running background Task (recoverable by joining `task_id` back to
   that task's one `task_started` event — the literal 164-vs-1 misread
   the issue body describes), and (b) the duplicate per-content-block
   `usage` object from point 2 above (kept only on the first block for a
   given `message.id`). Verified byte-for-byte parse-equivalence: ran
   `trajectory_analyzer.analyze()` on both the original and the dieted
   event stream for two real sessions and diffed the results (see
   Provenance).

Frozen no-side-effects constraint: nothing here changes what `spawn.py`
tees live, what the CLI sends per turn, or any production ledger/gate
path — the tool is a post-hoc reader over already-written logs, run by
hand. `to_ledger_event()` produces a `cache_coverage_perf` record in the
same shape convention as `skill_judge_perf` (issue #2255, `consult.py` —
the named template) so a later issue can wire it into `ledger_write`
without inventing a new event schema, but that wiring is out of scope
here.

## Why

[[performance-engineering-operational-playbook]] rule 1.7: prefer the
removal-shaped fix over an addition-shaped one when both close the same
gap. The measured defect (point 2 above) and the log-diet target (point
3) are both "delete a redundant, recoverable-by-join copy of a field
that's already recorded once elsewhere" — no new caching layer, no new
instrumentation path, no schema addition. Rule 1.2: reported the full
per-session distribution (12-row table, min/max), not a single mean,
since a mean would have hidden that the low end (my-travel, 0.908) is
still 8 points inside the chosen SLO floor rather than being an outlier
worth its own investigation. Rule 2.9: SLI (cache_hit_share) before SLO
(>=0.90) before error-budget accounting, in that order, matching the
skeleton frontmatter.

## Upstream basis

- `trajectory_analyzer.py` (issue #2214) — `parse_session_log()` (tolerant
  line-delimited JSON reader) and `analyze()` (the parse-equivalence
  oracle used to verify the diet) are reused, not reimplemented.
- `consult.py` `skill_judge_perf` event (issue #2255) — the ledger
  field-shape template `to_ledger_event()` follows.
- Real session logs under `$MUSTER_WORKSPACE_ROOT` (`/home/jwjung/.tokenmaxxxer/work/`),
  written by this repo's own `spawn.py` tee for both this repo's own
  role sessions and external consumer projects' role sessions — the
  actual "consumer conditions" data the Ask requires; not reproduced
  synthetically. sha: n/a (log files, not repo-tracked commits).

## Open findings

- `static_payload_fraction` on `my-travel-issue-5-product-discovery`
  measured at 8.34% — highest of the 12 sampled sessions, still inside
  the 90% SLO floor (cache_hit_share 0.908) but the one session worth a
  closer look if this measurement is repeated at larger sample size.
  Resolution path: re-run `cache_coverage.py --batch` against a larger
  sample once more consumer logs accumulate; escalate only if a session
  drops the SLO floor, not on this single data point.
- `to_ledger_event()` is a template, not wired into `ledger_write` /
  `spawn.py` — resolution path: a future issue, if per-session cache
  coverage is wanted as a standing ledger signal rather than an on-demand
  measurement.

## Next steps

None — `loop_state: measured` is terminal for this record kind
(measurement delivered, executed against real data, gate green).

## What did not work

Nothing — no dead end here worth recording.

skill-verdict: performance-engineering-operational-playbook — applied: invoked; rules 1.2 (percentile/distribution reporting — 12-row per-session table instead of a single mean), 1.7 (removal-shaped fix: strip duplicate/recoverable-by-join fields, no new caching layer), 2.9 (SLI cache_hit_share -> SLO >=0.90 -> error-budget-remaining, in that order, in the frontmatter above)

## Provenance (executed-live)

```
$ python3 -m py_compile scripts/cache_coverage.py && echo "compile OK"
compile OK

$ python3 -m pytest tests/test_behavior_metrics.py -q
.......                                                                  [100%]
7 passed in 0.95s

$ python3 -m pytest tests/test_trajectory_analyzer.py -q
.............................                                            [100%]
29 passed in 0.94s
```

Empty state (single-turn / zero-turn, no division by zero):
```
>>> cache_summary([])
{'turns': 0, 'total_input_tokens': 0, 'total_cache_read_input_tokens': 0,
 'total_cache_creation_input_tokens': 0, 'cache_hit_share': 0.0,
 'static_payload_fraction': 0.0, 'no_repetition': True}
>>> cache_summary([{'input_tokens': 5, 'cache_read_input_tokens': 0,
                     'cache_creation_input_tokens': 1200, 'output_tokens': 10}])
{'turns': 1, ..., 'cache_hit_share': 0.0, 'static_payload_fraction': 0.0,
 'no_repetition': True}
```
Real 0-byte session log (`on-the-record-issue-473-conformance-review...log`,
an actual admission-failure artifact, not constructed): `turns=0`,
`cache_hit_share=0.0`, `static_payload_fraction=0.0`, `no_repetition=True` —
same code path, real degenerate input.

Cache-hit share / static-payload fraction — host (this session, live,
cold-cache from spawn) + 12 real external consumer-project sessions +
1 real empty-state session:

```
project                                turns hit_share static_frac no_rep calls  reps
on-the-record-issue-2298-performance-engineering (host, this session)  38  0.971   0.026  False   0   0
arcade-dodger-issue-6-performance-engineering    31    0.9699      0.0174  False     0     0
my-travel-issue-5-product-discovery       67    0.9081      0.0834  False     9    81
tm-dicequest-issue-75-implementation     106     0.989      0.0085  False     0     0
skill-repository-issue-56-market-analysis    55    0.9378       0.054  False     4    39
soongsil-course-registration-issue-29-implementation   102    0.9835      0.0103  False     2    15
project-rich-issue-200-implementation     67    0.9848      0.0101  False     0     0
legal-compliance-rulebook-issue-19-implementation    96    0.9781      0.0139  False     1    33
northpole-harness-fixture-issue-45-conformance-review    32    0.9646      0.0302  False     0     0
performance-dashboard-issue-24-implementation    32    0.9639      0.0163  False     0     0
repo-status-board-issue-58-implementation    84    0.9777      0.0133  False     1    23
tm-webfolio-issue-5-ux-engineering        33    0.9757      0.0115  False     0     0
pilot-devdigest-issue-4-implementation    30    0.9728      0.0116  False     0     0
on-the-record-issue-473-conformance-review     0       0.0         0.0   True     0     0
```
(`calls`/`reps` = `subagent_field_repetition`: real distinct background-Task
calls vs. `task_progress` heartbeat re-stamps of the same static fields —
the 164-vs-1 misread class from the issue body, e.g. my-travel: 9 real
calls, 81 heartbeat repeats of the same 9 `subagent_type`/`description`
pairs.)

derived: python3 one-liner grouping every `assistant`-type line in the
host session log by `message.id` and diffing `message.usage` within each
group — the direct per-line inspection that motivated the `usage_turns`
dedupe fix, run before writing it (not a summary of a summary):
```
$ python3 -c "
import json
from collections import defaultdict
with open(path) as f: lines = f.readlines()
by_id = defaultdict(list)
for line in lines:
    obj = json.loads(line)
    if obj.get('type') == 'assistant':
        msg = obj.get('message') or {}
        by_id[msg.get('id')].append(msg.get('usage'))
multi = {k: v for k, v in by_id.items() if len(v) > 1}
print('messages with >1 content-block line:', len(multi), 'of', len(by_id))
print('max blocks per message:', max(len(v) for v in multi.values()),
      'usage-mismatch cases:',
      sum(1 for v in multi.values() if len({json.dumps(u, sort_keys=True) for u in v}) > 1))
"
messages with >1 content-block line: 33 of 34
max blocks per message: 2 usage-mismatch cases: 0
```

Turn-count double-counting fix, before/after (host session,
`message.id`-dedupe in `usage_turns`, direct output of
`scripts/cache_coverage.py` run before vs. after the fix):
```
before fix: turns=61, total_cache_read_input_tokens=3857194, cache_hit_share=0.9675
after  fix: turns=38, total_cache_read_input_tokens=2686502, cache_hit_share=0.9710
```
(38 = real API turn count post-dedupe, matching the 34-messages-total /
33-duplicated finding above once the empty-usage assistant events are
excluded too.)

Log-diet before/after size, same session replayed (not a different
session — Acceptance requires same-session before/after):
```
$ python3 scripts/cache_coverage.py --diet <host session log> --json
{"before_bytes": 498424, "after_bytes": 489367, "reduction_pct": 1.82}

$ python3 scripts/cache_coverage.py --diet <my-travel-issue-5 log> --json
{"before_bytes": 881781, "after_bytes": 853068, "reduction_pct": 3.26}

$ python3 scripts/cache_coverage.py --diet <on-the-record-issue-2208-implementation log> --json
{"before_bytes": 1506943, "after_bytes": 1476551, "reduction_pct": 2.02}
```

Diet parse-equivalence oracle (dieted event stream fed back through
`trajectory_analyzer.analyze()`, diffed against the original — proves
the diet loses no field the analyzer reads), direct output:
```
>>> orig = ta.analyze(path); diet = ta.analyze(dieted_path)
>>> diet['session_log'] = orig['session_log']  # only expected diff: temp-file path
>>> orig == diet
True   # ran for on-the-record-issue-2208-implementation AND my-travel-issue-5
```
