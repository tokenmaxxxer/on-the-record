---
proposal: docs/issue-994/proposals/2026-08-12-structural-denial-counting.md
---

# Hunt record — structural-denial-counting

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: NO FINDING
Seed: docs/issue-994/proposals/2026-08-12-structural-denial-counting.md; spawn.py:2000-2100, 2680-2780, 5440-5620; tests/test_spawn.py Watchdog class (~3503-3700) and issue-232 classifier tests (~2499-2680)
cap_seconds: 60
tier: default
diff_stat_lines: docs-only (proposal not yet implemented)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:00:55Z

Checked for: (a) other consumers of `_DENIAL_RE`-style word matching over
transcripts outside spawn.py (grepped hooks/, gates/, harness/driver.py for
"denied"/"denial" — none parse spawn.py's watchdog signal string or
`_DENIAL_RE`; hits are unrelated `permission_denials`/`.permission_denials`
metrics fields in gates/delegation_metrics.py and harness/driver.py docs
prose); (b) whether `watchdog_check_one`'s log file (`entry["log"]`) is the
same JSONL transcript the issue-232 live-stream classifier
(`_classify_refusal_text`/`_tool_result_text`, spawn.py:5502-5619) parses —
confirmed identical (`roster_register(..., "log": str(log_path))` at
spawn.py:5455, same `log_path` opened for `proc.stdout` at spawn.py:5528);
(c) whether the proposed structural parse needs cross-tick state the offset
mechanism doesn't carry (e.g. `tool_use_names` built by the live-stream loop
to correlate tool_result->tool_use across lines) — the proposal explicitly
scopes signal-3 to classifying `is_error` `tool_result` blocks directly via
`_classify_refusal_text`, without needing `tool_use_id`->name correlation,
so no persisted state beyond the existing `offset` is required; (d) whether
a doc/spec documents this signal's word-match semantics and would go stale —
`docs/issue-327/decisions/watchdog-exit-code.md` mentions `denied-tool-calls`
descriptively but is a historical decision record, not a spec consumed by
code or tests, so going stale there is not a build-blocking gap; (e) whether
test_spawn.py already has inline JSONL tool_result fixture patterns to reuse
for the Watchdog rewrite without a new fixture-helper file — confirmed,
issue-232's classifier tests (test_spawn.py:2499-2680) already build
`tool_use`/`tool_result`/`result` JSONL lines inline with `json.dumps`, the
same shape the proposal's rewritten Watchdog tests need.

No file outside {spawn.py, tests/test_spawn.py, docs/issue-994/reports/implementation.md}
is required to deliver "How you'll know it worked". No reproduction found;
stance yields no finding.

## before-landing — stance 1: assume this change and another plugin's rule/gate cancel each other — find the pair

Verdict: NO FINDING
Seed: git diff HEAD -- spawn.py / tests/test_spawn.py (watchdog signal-3 structural denial counting + offset-commit truncation fix)
cap_seconds: 120
tier: default
diff_stat_lines: 97 insertions(+), 9 deletions(-) across spawn.py (~57) and tests/test_spawn.py (~49)
started_at: 2026-08-12T12:54:38+09:00
ended_at: 2026-08-12T12:56:00+09:00

Checked for another consumer of the same state that could cancel or duplicate
this change's effect: grepped the whole repo (gates/, on-the-record/hooks/,
runs/rulebooks/*/hooks) for `watchdog_state`, `watchdog_check_one`, and
`offset` — `WATCHDOG_STATE` / `own_state[key]["offset"]` is read and written
only inside spawn.py itself (`watchdog_check_one`, called from
`_roster_health_diagnose` and `roster_watchdog`, both of which already pass a
pre-computed `anomalies` to avoid the documented double-consume-offset
footgun — that guard is untouched by this diff). `_DENIAL_RE` had exactly one
production use site (removed) and only appears afterward in a test's log
fixture string, not as a live reference anywhere else — `grep -rn
"_DENIAL_RE"` confirms no other module imports or reads it. `_deadlock_signature`
(the other "repeated denial" signal, DEADLOCKED state) reads a completely
different source (`.events.jsonl` structured events, not the session log
text/offset), so it neither races with nor depends on the new
`_count_structural_denials`/offset-truncation logic. No other gate/hook file
in the repo reads the session log by byte offset or references
`WATCHDOG_DENIAL_THRESHOLD`. Found no pair of rules that cancel each other;
stopping without a repro per the one-rule policy.
