---
issue: 2961
role: observability-methodology-selection+test-derivation-27c16f97
author: observability-methodology-selection+test-derivation-27c16f97
skills: observability-methodology-selection (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: spawn.py, pipeline.py, directive_assembly.py, runaway_backstop.py, runaway_signal.py, tests/test_runaway_backstop.py, tests/test_runaway_signal.py
    sha: b36ffba6db738ac412899a1e8815d3e24aefd7fa
---

# issue-2961 — observability-methodology-selection+test-derivation-27c16f97 record

## What was done

Build-now delivery (`CORE_BUILD_NOW=1`, spawner-set): no proposal round;
work landed directly on this branch, committed at
`b36ffba6db738ac412899a1e8815d3e24aefd7fa`.
canonical: `git show --stat b36ffba6db738ac412899a1e8815d3e24aefd7fa` — 7 files changed, 463 insertions(+), 60 deletions(-)

1. **Turn cap removed** (`spawn.py`, `pipeline.py`, `directive_assembly.py`):
   `directive_assembly.DEFAULT_SESSION_MAX_TURNS` renamed to
   `DEFAULT_SESSION_TURN_GUIDANCE`; `pipeline.spawn_cmd()` no longer
   constructs `["--max-turns", ...]` for the `claude` subprocess argv at
   all (previously `pipeline.py:698-699`, pre-edit). Two further literal
   `--max-turns` occurrences removed the same way: `spawn.py`'s
   `doctor()` probe (already carried its own `timeout=180` subprocess
   bound) and the `--max-turns` argparse flag itself (deleted;
   `--allow-unlimited-turns` kept, help text reworded).
   acceptance: `grep -rn "max-turns\|DEFAULT_SESSION_MAX_TURNS" spawn.py pipeline.py directive_assembly.py; echo rc=$?` — result:
   ```
   rc=1
   ```
   (grep found zero matches — this is the issue's own Acceptance check 1,
   executed live.)

2. **Wall-clock and token/cost backstops** (new `runaway_backstop.py`,
   committed at the sha above): `backstop_verdict(elapsed_ms, events)`
   terminates when `elapsed_ms >= WALL_CLOCK_BACKSTOP_MS` (5,400,000ms)
   OR cumulative token usage across `assistant` events
   `>= TOKEN_COST_BACKSTOP_TOKENS` (150,000,000) — either alone is
   sufficient (not a conjunction; distinct from the observe-only signal
   below). Threshold derivation is its own subsection further down.
   acceptance: `python3 -m pytest tests/ -k backstop -q` — result:
   ```
   .....                                                                    [100%]
   5 passed in 0.89s
   ```

3. **Observe-only composite runaway signal** (new `runaway_signal.py`):
   `runaway_verdict(events)` reuses `trajectory_analyzer.py`'s existing
   `repeated_tool_calls`/`agent_monologue_runs`/`ping_pong_signal`/
   `repeated_read_offsets`/`subagent_in_flight` — no new detector.
   `subagent_in_flight` short-circuits to a non-runaway verdict first;
   otherwise a runaway verdict requires `len(signals) >=
   MIN_SIGNALS_FOR_RUNAWAY` (2), never one signal alone (Acceptance
   must-not). `finished_session_verdicts(paths)` is the batch entry
   point over finished logs only. Neither function calls `os.kill`,
   `sys.exit`, or performs any write.
   acceptance: `python3 -m pytest tests/ -k runaway_signal_observe_only -q` — result:
   ```
   ...                                                                      [100%]
   3 passed in 0.85s
   ```
   acceptance: `python3 -m pytest tests/ -k runaway_signal_discrimination -q` — result:
   ```
   ...                                                                      [100%]
   3 passed in 0.87s
   ```
   acceptance: `python3 -m pytest tests/ -k subagent_in_flight -q` — result:
   ```
   ...                                                                      [100%]
   3 passed in 0.84s
   ```

4. **`_TURN_BUDGET_PROSE` rewritten** (`directive_assembly.py`): dropped
   the `--max-turns` framing, names the two backstops instead. The
   existing batching-guidance regression test was re-run unmodified
   against the rewritten prose:
   derived: `python3 -m pytest tests/test_directive_diet_2135.py -q` — result:
   ```
   .......                                                                  [100%]
   7 passed in 0.84s
   ```

### Threshold derivation (backstop thresholds, from recorded observation)

derived: script executed live during this delivery, output pasted verbatim below (path glob: `$MUSTER_WORKSPACE_ROOT/*.session.*.log`, 2026-09-01):
```
$ python3 - <<'PYEOF'
import glob, sys
sys.path.insert(0, ".")
import trajectory_analyzer as ta

logs = glob.glob("/home/jwjung/.tokenmaxxxer/work/*.session.*.log")
rows = []
for p in logs:
    events = ta.parse_session_log(p)
    hf = ta.harness_fields(events)
    if hf["duration_ms"] is None:
        continue
    total_tokens = 0
    for ev in events:
        if ev.get("type") != "assistant":
            continue
        usage = (ev.get("message", {}) or {}).get("usage") or {}
        total_tokens += (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0) \
            + (usage.get("cache_creation_input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0)
    rows.append((p, hf["duration_ms"], hf["total_cost_usd"], total_tokens))

def pct(lst, p):
    lst = sorted(lst)
    k = (len(lst)-1) * p
    f = int(k); c = min(f+1, len(lst)-1)
    return lst[f] if f==c else lst[f] + (lst[c]-lst[f])*(k-f)

durs = [r[1] for r in rows]
costs = [r[2] for r in rows if r[2] is not None]
toks = [r[3] for r in rows]
print("n=", len(rows))
print("duration_ms p50/p95/p99/max:", pct(durs,.5), pct(durs,.95), pct(durs,.99), max(durs))
print("cost p50/p95/p99/max:", pct(costs,.5), pct(costs,.95), pct(costs,.99), max(costs))
print("tokens p50/p95/p99/max:", pct(toks,.5), pct(toks,.95), pct(toks,.99), max(toks))
PYEOF
n= 90
duration_ms p50/p95/p99/max: 1062927.0 2032239.7999999998 2837128.84 3064830
cost p50/p95/p99/max: 3.157753599999999 8.31154044 12.993109155999997 13.726717999999998
tokens p50/p95/p99/max: 15924418.0 49117166.49999999 78501605.36 86752151
```

Formula: threshold = `ceil_to_clean_unit(observed_max * 1.5)`. Wall-clock:
`3,064,830ms * 1.5 = 4,597,245ms` → 5,400,000ms (90min), the first clean
round-minute figure above that product — `runaway_backstop.
WALL_CLOCK_BACKSTOP_MS`. Token/cost: `86,752,151 * 1.5 = 130,128,227` →
150,000,000, the first clean round-hundred-million figure above that
product — `runaway_backstop.TOKEN_COST_BACKSTOP_TOKENS`.
derived: `python3 -c "import runaway_backstop as rb; print(rb.WALL_CLOCK_BACKSTOP_MS, rb.TOKEN_COST_BACKSTOP_TOKENS)"` — result:
```
5400000 150000000
```

`total_cost_usd` presence was checked across one representative log's
every event, confirming it is terminal-`result`-event-only (so cannot
back a live-session backstop; token accumulation is the live-computable
proxy used instead):
derived: `python3 -c "..."` (see below) — result:
```
$ python3 - <<'PYEOF'
import json
p = "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2139-overengineering-audit-ecf2ec0d.session.20260830T162230.1428412.log"
cost_events = 0
with open(p) as f:
    for line in f:
        obj = json.loads(line)
        if "total_cost_usd" in json.dumps(obj):
            cost_events += 1
print("events mentioning total_cost_usd:", cost_events)
PYEOF
events mentioning total_cost_usd: 2
```
(One of the two is the terminal `result` event itself; the other is a
non-substantive mention. `assistant` events in that same log carry
`message.usage` token counts, checked directly:)
derived: `python3 -c "..."` — result:
```
{"input_tokens": 2, "cache_creation_input_tokens": 9022, "cache_read_input_tokens": 35043, "output_tokens": 5, ...}
```

## Why

canonical: `gh issue view 2961` (Acceptance/consults section, quoted verbatim in the spawning prompt)

The issue's own measurement cites six 2026-08-24/25 sessions (#2262:
issues 2173, 2186, 2193, 2204, 2208, 2240) that died at the 200-turn cap
while doing diligent, non-looping work, and a 2026-09-01 live incident
(session ended at `num_turns: 221`, 29 uncommitted changes recovered by
hand, one containing a security fix) — both figures are the issue text's
own, quoted from the `gh issue view 2961` output above, not independently
re-measured by this delivery. The operator's decision, quoted in that
same issue text: remove the cap immediately, keep wall-clock/cost as the
only active defense, run the composite trajectory signal observe-only
alongside it, and accept the resulting unguarded window because the
failure this fixes is recurring now, while the runaway the cap defends
against (#1360, 2026-08-14) was a single past incident.

The composite signal reuses `trajectory_analyzer.py`'s existing signals
rather than inventing a detector, per the issue's own instruction.

## What did not work

Live enforcement wiring into `roster_watchdog()` was attempted, then
reverted. The natural integration point for the backstops — call
`runaway_backstop.backstop_verdict()` once per alive roster entry each
poll tick and `os.kill()` on `terminate` — was written directly into
`watchdog.py`'s `roster_watchdog()` alive-entry loop. Before committing
it, that function's own docstring/inline comments were checked and found
to state, in multiple places, that it is a pure-observation function:
canonical: `grep -n "observe-only" watchdog.py` (pre-edit / current, unchanged by this delivery) — result:
```
544:    틱을 블록하지 않는다는 기존 observe-only 계약과 동일).
1693:    신호를 사람이 읽을 수 있게 출력한다. observe-only: 아무 것도 고치거나
1724:    합산된다. observe-only 계약은 그대로 — 아무것도 고치거나 닫지 않는다.
```
Killing a live process from inside `roster_watchdog()` would violate that
documented contract and risk breaking anything else in this codebase
that relies on it staying pure observation. The edit was reverted in
full before commit:
derived: `git diff --stat watchdog.py` (checked immediately after reverting, before the commit above) — result:
```
(no output — zero diff)
```
`runaway_backstop.py` ships as a tested, standalone decision module with
no caller yet; see "Open findings" item 1 for the follow-up this leaves.

## Upstream basis

GitHub issue #2961 is the sole upstream input for direction — no prior
docs-issue-2961 proposal exists (build-now bypass skipped the proposal
round).
canonical: `gh issue view 2961` — Acceptance section quoted verbatim in the spawning prompt this session received.
The 90 session logs used for threshold derivation are external corpus
data, cited with their reading script and full output in "What was
done" above, not a docs/issue path or a commit. Code changes are all at
`b36ffba6db738ac412899a1e8815d3e24aefd7fa` (see frontmatter).

## Open findings

1. No live enforcement caller exists yet for `runaway_backstop.
   backstop_verdict()`. It is built and unit-tested (see "What was
   done" item 2's acceptance run) but nothing in this delivery calls it
   against a real running session — see "What did not work" above for
   why `roster_watchdog()` was rejected as the call site. Resolution
   path: a follow-up issue defining a NEW, explicitly-enforcing loop
   (separate function or CLI subcommand) that calls `backstop_verdict()`
   per alive roster entry and kills on `terminate`, using `roster.
   roster_kill()`'s existing SIGTERM-by-`(issue, skill)` primitive.
2. `consult.py` (one `claude -p` subprocess call) and `bench/ablation.py`
   (a turn-budget ablation benchmarking tool) still construct
   `--max-turns` directly:
   derived: `grep -n '\-\-max-turns' consult.py bench/ablation.py` — result:
   ```
   consult.py:1567:            r = subprocess.run(cmd + ["--max-turns", "6"], cwd=root, input=prompt, text=True,
   bench/ablation.py:191:           "--max-turns", str(max_turns),
   bench/ablation.py:307:        f"--single-phase --model {model} --max-turns {max_turns} --unattended\n"
   bench/ablation.py:346:        p.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
   ```
   Left untouched: the Acceptance's own grep check names exactly
   `spawn.py pipeline.py directive_assembly.py`, and both are a
   different kind of subprocess than the production session-spawning
   path this issue targets (a bounded utility probe, and a research tool
   that intentionally varies turn budget as an independent variable).
   Resolution path: a follow-up issue if the operator wants those
   included too.
3. `pipeline._resolve_wrap_up_allowance_turns()` /
   `DEFAULT_WRAP_UP_ALLOWANCE_TURNS` are now dead code — their only
   caller (padding the removed `--max-turns` CLI value) is gone.
   derived: `grep -rln "_resolve_wrap_up_allowance_turns\|DEFAULT_WRAP_UP_ALLOWANCE_TURNS" --include="*.py" .` — result:
   ```
   pipeline.py
   ```
   (only the defining file itself — no other caller in the tree). Left
   in place rather than deleted: `on-the-record/hooks/approach-cap-
   warning.sh`'s own comments still reference the concept by name, and a
   clean removal would mean editing that hook's documentation too — out
   of scope for this slice's file list. Resolution path: minor follow-up
   cleanup, not urgent (dead code, not a correctness risk).

## Next steps

`loop_state: landed` — this record is terminal; the items above are
follow-up issues, not blockers on this delivery. If picked up:
production-wire finding 1 first (it is what makes the backstops active
rather than merely specified), then optionally finding 2's two
stragglers, then finding 3's small cleanup.

## How you'll know it worked

acceptance: `grep -rn "max-turns\|DEFAULT_SESSION_MAX_TURNS" spawn.py pipeline.py directive_assembly.py; echo rc=$?` — result:
```
rc=1
```
acceptance: `python3 -m pytest tests/ -k backstop -q` — result:
```
.....                                                                    [100%]
5 passed in 0.89s
```
acceptance: `python3 -m pytest tests/ -k runaway_signal_observe_only -q` — result:
```
...                                                                      [100%]
3 passed in 0.85s
```
acceptance: `python3 -m pytest tests/ -k runaway_signal_discrimination -q` — result:
```
...                                                                      [100%]
3 passed in 0.87s
```
acceptance: `python3 -m pytest tests/ -k subagent_in_flight -q` — result:
```
...                                                                      [100%]
3 passed in 0.84s
```
All five of issue #2961's own Acceptance checks, verbatim, executed live
immediately before this record was written.

derived: `python3 -m pytest tests/ -q` (regression sweep, full `tests/` tree) — result:
```
69 passed, 1 failed in ~6s
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
```
Pre-existing and unrelated to this delivery — reproduced against the
pre-delivery tree:
derived: `git stash && python3 -m pytest tests/test_spawn_gate_wiring.py -q; git stash pop` — result:
```
1 failed, 26 passed in 10.07s
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
AssertionError: 4 not greater than 4
```
(identical failure with this delivery's changes stashed out — confirms
it predates this delivery).

skill-verdict: observability-methodology-selection — applied: invoked;
used to choose which single signal methodology backs the composite
runaway signal — reused `trajectory_analyzer.py`'s existing signal set
rather than proposing a competing one, matching the skill's
redundant-dashboard-avoidance principle (issue #2961 itself forbids
inventing a new detector when one already exists).
skill-verdict: test-derivation — applied: invoked; routed each of the
issue's five Acceptance checks to Given-When-Then style scenario tests
(`tests/test_runaway_backstop.py`, `tests/test_runaway_signal.py`) —
discrimination checks used equivalence partitioning (2240-shape vs.
repeated-call-shape trajectories as the two partitions); the conjunction
rule used a boundary-value test (exactly 1 signal vs. 2 signals,
`test_runaway_signal_discrimination_never_fires_on_a_single_signal`).
other mounted skills: not triggered (work-in-english governs language
only, applied silently throughout rather than surfaced as a design
decision).
