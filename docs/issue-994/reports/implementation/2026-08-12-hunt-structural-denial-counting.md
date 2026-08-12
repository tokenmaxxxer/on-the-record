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
