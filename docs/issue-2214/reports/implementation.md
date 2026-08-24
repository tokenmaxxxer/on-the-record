---
issue: 2214
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2214/reports/implementation/2026-08-24-hunt-trajectory-analyzer.md
    sha: 3f7d93fffd4d0ee6f048219d9cdc23c34c4ec3cc
  - path: docs/issue-2214/reports/implementation/2026-08-25-hunt-pr2221-fixes.md
    sha: d613f552dce863d96a0eeae81d406243454f8a1f
code_under_review:
  - trajectory_analyzer.py
  - tests/test_trajectory_analyzer.py
  - tests/fixtures/trajectory_logs/empty_admission_error.session.log
type: fix
breaking: none
verdict: pass
---

# issue-2214 — implementation record

## What was done

Added `trajectory_analyzer.py` (commit 3f7d93fffd4d0ee6f048219d9cdc23c34c4ec3cc),
a pure, read-only, post-hoc parser for the raw `--output-format
stream-json` session logs `pipeline.py`'s `_session_log_path()` writes to
`<work>.session.<ts>.<pid>.log`. It never mutates a session and never
terminates one — advisory-only, per the issue's own requirement.

`analyze(path)` returns one JSON-able report per session log with:
- Harness-native fields, read straight off the terminal `result` event:
  `permission_denials` (+ `denial_count`), `subagent_stats`, `num_turns`,
  `usage.iterations`, `terminal_reason`, `total_cost_usd`,
  `duration_ms`/`duration_api_ms`, `errors`.
- Thrash/repetition metrics, pure functions of the log:
  `repeated_tool_calls` (grouped by `(tool, normalized input)`, flagged
  at the OpenHands-calibrated thresholds from the issue's own table —
  identical action→observation ≥4, identical action→error ≥3),
  `repeated_read_offsets` (repeated `(file_path, offset)` pairs on
  `Read` calls), `edits_per_file` (`Edit`/`Write`/`NotebookEdit` counts
  per path), `tool_mix_over_time` (tool-name histogram per 10-call
  bucket), `agent_monologue_max_run` (≥3 consecutive text-only assistant
  turns), `ping_pong_detected` (alternating A/B/A/B ≥6 calls within the
  last `MAX_EVENTS_TO_SCAN_FOR_STUCK_DETECTION=20` tool calls).
- `blocked_on_subagent` (`subagent_in_flight()`): true for a
  `Task`/`Agent` tool_use with no matching `tool_result` yet, or an
  async-launch ack (`tool_use_result.isAsync`) whose `tool_use_id` never
  reaches a terminal `task_notification` system event, or a
  `subagent_stats.spawned` count exceeding the settled total.
- `advisory.stalled` / `advisory.reasons`: derived from the thrash
  metrics, reported independently of `blocked_on_subagent` — see "What
  did not work" below for why this independence matters.

Empty-state: `parse_session_log()` degrades a missing file, an empty
file, or a malformed/truncated trailing JSONL line to fewer parsed
events, never an exception. `tests/fixtures/trajectory_logs/empty_admission_error.session.log`
(0 bytes) is in the fixture corpus for this — see the acceptance
evidence below.

CLI: `python3 trajectory_analyzer.py <session-log-path>` prints the
report as JSON.

### Follow-up: two blocking defects from the orchestrator's PR #2221 review

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/2221/comments`
(this session, PR #2221 review comment,
https://github.com/tokenmaxxxer/on-the-record/pull/2221#issuecomment-5397006661).
Both fixed in this same session, same branch. Full commands and output
for each are in "Acceptance verification" below.

1. Nonexistent log path reported as a clean empty session, `--help`
   consumed as a log path. canonical: `python3 trajectory_analyzer.py
   /nonexistent/path/xyz.log >/dev/null 2>&1; echo "exit=$?"` (review
   comment's own repro) -> `exit=0`. Root cause: `main()` fed `argv[0]`
   into `analyze()` with no argument parsing at all.
   canonical: `python3 trajectory_analyzer.py /nonexistent/path/xyz.log`
   (this session, post-fix) -> exit 1, stderr `error: session log not
   found: /nonexistent/path/xyz.log`. `main()` now uses `argparse`
   (`-h`/`--help` handled by argparse, never mistaken for a path) and
   checks `Path(session_log).exists()`/`.is_file()` before calling
   `analyze()`. `analyze()`/`parse_session_log()` keep their prior
   lenient degrade-on-missing-file behavior for library callers (only
   the CLI enforces the strict check); the 0-byte-log empty-state case
   is untouched.
2. Output was 89KB for one session. canonical: review comment's own
   repro, `python3 trajectory_analyzer.py <one real session log> | wc
   -lc` -> `283 89657`, because `permission_denials` embedded every
   denial's `tool_input` verbatim.
   canonical: `python3 trajectory_analyzer.py
   on-the-record-issue-2214-implementation.session.20260824T233348.2080038.log
   | wc -lc` (this session, post-fix, same log referenced in the
   original PR's own acceptance evidence below) -> `155 3709`, down from
   the unfixed form. `harness_fields()` gained `include_raw_denials:
   bool = False` (CLI `--include-raw-denials`); the default strips
   `tool_input` per entry and adds `denial_tool_counts`
   (`tool_name -> count`) — the summary form the review asked for.

canonical: `docs/issue-2214/reports/implementation/2026-08-25-hunt-pr2221-fixes.md`
(before-landing warrant-hunt, stance 0, this session) — found a third,
self-introduced defect in fix 1 before it shipped: `Path.exists()` is
also true for a directory, so the original `.exists()`-only guard let a
directory argument fall through into `parse_session_log()`'s `p.open()`.
canonical: `python3 trajectory_analyzer.py .` (this session, pre-fix
reproduction of the hunt finding) -> unhandled `IsADirectoryError`
traceback, not the intended clean error. Fixed in the same commit by
adding a `.is_file()` check alongside `.exists()`; see "What did not
work" and `docs/issue-2214/reports/implementation/deviation-log.md`.

## Why

The issue's Acceptance section and calibration table are fully
prescriptive — exact thresholds ("do not invent thresholds"), an exact
gate test path (`tests/test_trajectory_analyzer.py`) — and this repo
already carries a clear placement precedent: top-level pure-Python
log/event parsers (`events.py`, `watchdog.py`) alongside a `gates/*.py`
pure-function convention (e.g. `gates/delegation_metrics.py`). There was
no open design decision to scout or propose against, so per the
survey-order/scout directives' stated skip condition ("the spec leaves
no design decision open"), that round was skipped — recorded here rather
than in a separate survey file. Per contract v3 s19a build-now bypass
(`CORE_BUILD_NOW=1`, set by the spawner), the phase-1 proposal round
itself was skipped and this is a direct delivery.

`trajectory_analyzer.py` lives at the repo root, not under `gates/`,
because it is not a PreToolUse/PostToolUse enforcement gate — read-only
analysis over an already-written file, matching `events.py`/
`watchdog.py`'s placement rather than the gate-script convention.

Acceptance bullet "the text regex at spawn.py:3930 and :4007 is removed
or delegates to it": that regex does not exist in the current
`spawn.py` (3304 lines total, checked via `wc -l spawn.py`).
canonical: `grep -rn "re\.compile.*[Dd]enied" *.py` (this session,
repo root) — the only match is `events.py:81`'s narrow
`_HARNESS_REFUSAL_PATTERNS` entry, which fires only inside
`_classify_refusal_text()` on already-`is_error` `tool_result` blocks
already correlated against `permission_denials`
(`events.py:_count_structural_denials`) — not a raw-text scan over a
full transcript. `tests/test_spawn_board_flows.py`'s
`test_echoed_source_mentioning_denied_is_not_a_gate_refusal` is a
standing regression test guarding against exactly the old bug this issue
names (issues #994/#246/#126 already retired it). This new analyzer's
own `harness_fields()` reads `permission_denials` directly off the
terminal `result` event, which is the acceptance bullet's actual, still
-live requirement for the new code.

## What did not work

- First cut of `subagent_in_flight()` checked only whether a
  `Task`/`Agent` tool_use had any `tool_result` at all. canonical: `python3 trajectory_analyzer.py /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1761-implementation.session.20260821T105423.1144114.log`
  (this session, real on-disk log) — a backgrounded `Agent` dispatch gets
  an immediate synthetic `tool_result` acking the launch
  (`tool_use_result.isAsync: true, status: "async_launched"`), so "has a
  tool_result" alone under-counted in-flight subagents. Fixed by also
  requiring a terminal `task_notification` system event on the same
  `tool_use_id` (`_task_notification_tool_use_ids()`).
- First cut of `analyze()` gated all thrash-signal reporting behind
  `if not blocked:`. The before-landing warrant-hunter (stance 0)
  identified that this lets a crashed/silently-dead backgrounded
  subagent (async-launch ack seen, its `task_notification` never
  arrives) hold `blocked_on_subagent` true for the rest of the log,
  discarding real, unrelated thrash. canonical: docs/issue-2214/reports/implementation/2026-08-24-hunt-trajectory-analyzer.md
  (this session's own before-landing dispatch). Fixed by reporting
  `stalled`/`reasons` unconditionally, independent of
  `blocked_on_subagent` — an in-flight dispatch has no settled
  `tool_result` to count, so a purely-waiting session already produces
  zero repeat signal on its own; the gate was defending against a case
  that cannot occur while suppressing one that does. Regression test:
  `test_dead_subagent_does_not_permanently_suppress_unrelated_thrash`
  in `tests/test_trajectory_analyzer.py`.
- First cut of fix 1 (missing-path handling, this session) checked only
  `Path(session_log).exists()`. A before-landing warrant-hunt (stance 0)
  on this fix, canonical: `docs/issue-2214/reports/implementation/2026-08-25-hunt-pr2221-fixes.md`
  (this session's own before-landing dispatch), found that `.exists()`
  is also true for a directory, so a directory argument fell through the
  guard into `parse_session_log()`'s `p.open()` and crashed with an
  unhandled `IsADirectoryError` traceback instead of the intended clean
  error. canonical: `python3 trajectory_analyzer.py .` (this session,
  pre-fix reproduction) -> uncaught traceback. Fixed by adding a second
  guard, `if not path.is_file(): ...; return 1`, alongside `.exists()`.
  Regression test: `test_cli_directory_path_is_a_clear_error_not_a_crash`
  in `tests/test_trajectory_analyzer.py`.

## Upstream basis

- `docs/issue-2214/reports/implementation/2026-08-24-hunt-trajectory-analyzer.md`
  (sha: 3f7d93fffd4d0ee6f048219d9cdc23c34c4ec3cc, same commit as the code
  it hunted) — before-landing warrant-hunt finding described above.
- Issue #2214 (`gh issue view 2214`, read this session) — Acceptance
  section and OpenHands calibration table followed exactly.
- `events.py` / `tests/test_spawn_board_flows.py` (existing code, read
  not modified this session) — basis for the "regex already retired"
  point above.
- `pipeline.py:934` `_session_log_path()` (existing code, read not
  modified this session) — the log path/naming convention this analyzer
  targets.

## Open findings

None. canonical: `docs/issue-2214/reports/implementation/2026-08-24-hunt-trajectory-analyzer.md`
and `docs/issue-2214/reports/implementation/2026-08-25-hunt-pr2221-fixes.md`
(this session's two before-landing dispatches) — every issue either
surfaced (dead subagent permanently suppressing unrelated thrash, and
the directory-path crash in this round's own fix 1) was fixed and
regression-tested in the same commit before landing, per "What did not
work" above.

## Next steps

None; `loop_state` is terminal (`landed`). A later session could wire
this analyzer's output into the live `watchdog.py` path as an additional
advisory signal, but that is a new decision outside this issue's
Acceptance and is not started here.

## Acceptance verification

canonical: acceptance: python3 -m pytest tests/test_trajectory_analyzer.py -q — result: PASS
```
......................                                                   [100%]
22 passed in 31.07s
```
The empty-state fixture (`tests/fixtures/trajectory_logs/empty_admission_error.session.log`,
0 bytes) is exercised by `test_empty_log_on_disk_analyzes_to_all_zero_metrics`
in the run above.

canonical: acceptance: python3 trajectory_analyzer.py /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1761-implementation.session.20260821T105423.1144114.log — result: PASS
```
{
  "session_log": "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1761-implementation.session.20260821T105423.1144114.log",
  "event_count": 314,
  "harness_fields": {
    "denial_count": 3,
    "subagent_stats": {
      "spawned": 1, "started_in_background": 1, "completed": 1, "failed": 0,
      "killed": {"parent": 0, "user": 0, "system": 0},
      "by_type": {"warrant:warrant-hunter": 1}
    },
    "num_turns": 12, "terminal_reason": "completed",
    "total_cost_usd": 2.86817325, "duration_ms": 62682, "duration_api_ms": 444753,
    "errors": []
  },
  "repeated_tool_calls": {"observation_repeats": [], "error_repeats": []},
  "repeated_read_offsets": [
    {"file_path": ".../spawn.py", "offset": 5140, "count": 2}
  ],
  "edits_per_file": { "...": "6 distinct paths, counts 1-5 each" },
  "tool_mix_over_time": [ "4 buckets of up to 10 tool calls each" ],
  "agent_monologue_max_run": 0,
  "ping_pong_detected": false,
  "blocked_on_subagent": false,
  "advisory": {"stalled": false, "reasons": [], "note": "advisory only — never terminates a session"}
}
```
(Elided for length in this record only — the real permission_denials
array, edits_per_file paths, and tool_mix_over_time buckets were all
present in the actual stdout this command produced.)

Issue Acceptance bullet 3 ("session blocked on a live subagent is NOT
reported as stalled — demonstrate with a real log"): a copy of the same
real on-disk log above, truncated with `sed -n '1,181p'` at the exact
byte position right after its backgrounded `Agent` dispatch's
async-launch ack and before that dispatch's `task_notification`
completion — real session bytes, not synthesized:

canonical: acceptance: python3 trajectory_analyzer.py /tmp/issue2214_truncated_live_subagent.session.log — result: PASS
```
{
  "session_log": "/tmp/issue2214_truncated_live_subagent.session.log",
  "event_count": 181,
  "harness_fields": {"denial_count": 0, "subagent_stats": null, "num_turns": null,
                     "terminal_reason": null, "errors": []},
  "repeated_tool_calls": {"observation_repeats": [], "error_repeats": []},
  "agent_monologue_max_run": 0,
  "ping_pong_detected": false,
  "blocked_on_subagent": true,
  "advisory": {"stalled": false, "reasons": [], "note": "advisory only — never terminates a session"}
}
```
`blocked_on_subagent` is `true` and `advisory.stalled` is `false` in
this actual output.

### PR #2221 defect-fix acceptance evidence (this round)

canonical: acceptance: python3 -m pytest tests/test_trajectory_analyzer.py -q — result: PASS
```
.............................                                            [100%]
29 passed in 0.84s
```
Up from the 22-test run above; the 7 new tests are the CLI
missing-path/`--help`/directory-path cases and the denial-summary cases.

canonical: acceptance: python3 trajectory_analyzer.py /nonexistent/path/xyz.log; echo "exit=$?" — result: PASS (non-zero exit, clear stderr, matches the review's own repro shape)
```
error: session log not found: /nonexistent/path/xyz.log
exit=1
```

canonical: acceptance: python3 trajectory_analyzer.py --help — result: PASS (argparse usage, not a fake analysis report)
```
exit=0
usage: trajectory_analyzer.py [-h] [--include-raw-denials] session_log
```

canonical: acceptance: python3 trajectory_analyzer.py . — result: PASS (before-landing hunt regression check — clean error, not a crash)
```
error: session log is not a regular file: .
exit=1
```

canonical: acceptance: python3 trajectory_analyzer.py /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2214-implementation.session.20260824T233348.2080038.log | wc -lc — result: PASS
```
155 3709
```
Same real on-disk log this issue's own delivery ran against (the
`/home/jwjung/.tokenmaxxxer/work/` log referenced above), denial_count 5.
`--include-raw-denials` on the same log gives `177 34084` (verbatim
`tool_input` restored, larger by construction — see the flag's own test,
`test_include_raw_denials_flag_restores_verbatim_tool_input`, for the
exact byte-level assertion against a synthetic large payload).

## Skill obligations

skill-verdict: silent-failure-audit — applied: invoked; ran this round's
audit procedure against `main()`'s new missing-path/`--help` handling and
`parse_session_log()`'s pre-existing lenient-degrade contract — surfaced
one real Silently-Absorbed-shaped inconsistency (`_denial_tool_counts`/
`_summarize_denials` dropping non-dict `permission_denials` entries while
`denial_count` still counted them), fixed in the same commit with a
regression test (`test_malformed_denial_entry_still_counted_consistently`).

skill-verdict summary: other mounted skills — not triggered this round
either (same reasoning as the original delivery below: a scoped two-defect
bugfix inside one existing file has no coupling/cohesion threshold,
GoF-pattern trade-off, data-structure performance cliff, or multi-module
structure decision open to weigh).

Original-delivery skill-verdict summary: other mounted skills — not
triggered (this issue's spec is fully prescriptive: exact thresholds,
exact gate-test path, established module-placement precedent already in
the repo — no coupling/cohesion threshold, GoF-pattern trade-off, or
data-structure performance cliff was ever an open decision to weigh, and
this delivery is a single-file analysis script, not multi-module
structure requiring `implementation-blueprint`).
