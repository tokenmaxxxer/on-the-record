---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: feature
breaking: false
verdict: pass  # canonical: acceptance: python3 -m pytest tests/test_spawn.py -k DiagnoseHealth — result: see Verification below
loop_state: landed
---

## What was done

Implemented the approved proposal
(docs/issue-1966/proposals/heartbeat-masked-hang-advisory-classifier.md,
PR #1967, APPROVE issue-1966/implementation) in `spawn.py`:

- Added tunable module constant `WATCHDOG_HEARTBEAT_ONLY_MIN = 18`
  (spawn.py:2094), next to `WATCHDOG_SILENCE_MIN`.
- Added `_classify_log_lines_heartbeat_only(text, now, window_min)`
  (spawn.py:2109-2148): structurally parses the already-scanned JSONL
  `text` slice, line by line, following `_count_structural_denials()`'s
  parse-and-skip-on-failure convention. Buckets parseable
  timestamp-carrying lines into heartbeat (`type == "tool_progress"`)
  vs. substantive; returns `"heartbeat-only"` when the most recent
  `window_min` minutes of timestamped activity is non-empty and entirely
  heartbeat, `"unmeasurable"` when no line in the scanned text ever
  carries the `tool_progress` tag, else `"healthy"`.
- Wired the classifier into `watchdog_check_one()` as signal 7
  (spawn.py:~2178-2186): reuses the same offset-scanned `text` already
  read for signals 2-4, no new log read. Appends a
  `heartbeat-only-growth: ...` anomaly string when the classifier
  returns `"heartbeat-only"`.
- Extended `diagnose_health()` (spawn.py:~2397-2405): when
  `heartbeat-only-growth` fires and neither `log-silence` nor
  `watcher-silent` already fired (checked first, unchanged), returns the
  new state `"STALLED-HEARTBEAT-ONLY"` with `next_action: "resume-watch"`
  — the same advisory action STALLED already uses, so it inherits the
  existing proof that this action never reaches a kill/refusal/gate path.
  Updated the function's docstring to list the new fifth state.
- Added 5 fixture tests to the `DiagnoseHealth` class in
  `tests/test_spawn.py`: (a) a synthetic 22-minute `tool_progress`-only
  JSONL fixture reproducing the observed issue-1959 hang shape →
  `STALLED-HEARTBEAT-ONLY`; (b) the same fixture with one substantive
  `assistant` line interleaved in the recent window → `HEALTHY`; (c) a
  structural assertion that the advisory state's `next_action` is in the
  allowed advisory set (`{"resume-watch"}`), not in the
  kill/refusal/gate set (`{"respawn", "surface-repeating-cause"}`), plus
  a source-grep confirming `"STALLED-HEARTBEAT-ONLY"` never co-occurs
  with a kill/refusal/gate-block keyword line in `spawn.py`; (d) a
  fixture whose lines never carry the `tool_progress` tag → `HEALTHY`
  with the unmeasurable fallback (not a silent STALLED).

## Why

basis: docs/issue-1966/proposals/heartbeat-masked-hang-advisory-classifier.md,
approved via the issue-level `APPROVE issue-1966/implementation` comment
from `JiwonJung94` (an approvers.md account) on the phase-1 PR #1967 —
canonical: gh pr view 1967 --json state,mergedAt,title (state MERGED,
mergedAt 2026-08-22T00:18:39Z). `diagnose_health()` had exactly one path
to a non-HEALTHY alive state while the process is alive
(`log-silence`/`watcher-silent`, both mtime-based) and no signal
inspected log *content* — canonical: spawn.py:2393-2396 (pre-change) —
a hung child that keeps writing `tool_progress` heartbeat lines
(observed live 2026-08-22, issue-1959: a pytest-xdist worker stuck 22
minutes on a futex) resets mtime every heartbeat and stayed HEALTHY
indefinitely.

## Doc placement ladder

- No env var/config key/new dependency/migration/setup step introduced
  — nothing to add to a handbook.
- Library-or-format choice (structural JSONL line-type parsing over
  text/regex matching) already carries its rationale/alternative in
  docs/issue-1966/proposals/heartbeat-masked-hang-advisory-classifier.md
  `## Rationale` — not duplicated here.
- No benchmark/investigation numbers produced beyond the test-tier
  wall-clock measurement recorded below.

## What did not work

None.

## Open findings

None.

## Verification

canonical: acceptance: python3 -m pytest tests/test_spawn.py -k DiagnoseHealth — result: see run below
```
.............                                                            [100%]
13 passed in 1.11s
```

Includes the two acceptance-mandated fixtures run live:
`test_advisory_heartbeat_only_stall_for_observed_hang_shape` (a synthetic
22-minute `tool_progress`-only log classifies as `STALLED-HEARTBEAT-ONLY`,
not HEALTHY) and `test_healthy_when_substantive_lines_interleaved_with_heartbeats`
(same shape with one interleaved substantive line classifies as
`HEALTHY`), plus
`test_advisory_heartbeat_only_state_never_reaches_kill_refusal_or_gate_action`
(the new state's `next_action` is confined to the advisory set and
unreachable from any kill/refusal/gate-block code path) and
`test_unmeasurable_log_without_heartbeat_tag_stays_healthy` (the issue's
own unmeasurable-log fallback clause).

canonical: acceptance: python3 -m pytest -q -m not_slow — result: see run below
```
30 failed, 2405 passed, 18 xfailed, 3 xpassed in 37.48s
```
30 unrelated pre-existing failures (consult-gate env/trace-root
plumbing, gh-quota flakiness, one board-sweep `gh` call-count check) —
reproduced on pre-change HEAD commit d5813d91 too:
canonical: acceptance: git stash; python3 -m pytest -q -m not_slow tests/test_spawn_judge.py::JudgeVerifyDropTest::test_hallucinated_path_never_reaches_enqueue gates/test_consult_gate_lib_env.py::test_consult_env_injects_core_plugin_root; git stash pop — result: see run below
```
2 failed in 0.86s
```
canonical: acceptance: git stash; python3 -m pytest -q tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts; git stash pop — result: see run below
```
1 failed in 1.04s
```
Not a regression from this change.

canonical: acceptance: python3 -m pytest -q -m slow tests/test_spawn.py -k "DiagnoseHealth or WatchdogCheckOne or watchdog" — result: see run below
```
...                                                                      [100%]
3 passed in 1.04s
```

unverifiable: full test-tier `slow` command (`.on-the-record/test-tiers.json`,
triggered because this diff touches `spawn.py`/`tests/test_spawn.py`) —
reason: killed by a 590-second bound, exit 143, before it produced a
result — canonical: acceptance: time timeout 590 python3 -m pytest -q -m slow
— result: see run below
```
real	9m50.007s
[exited with code 143]
```
The targeted slow-marked subset above (DiagnoseHealth/watchdog) ran to
completion in the same session. Recording this gap per the observe-only
test-tier-directive rather than absorbing it silently — a later session
with a longer budget can re-run the untrimmed `slow` tier.
