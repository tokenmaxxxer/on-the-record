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

## before-landing — stance 0: assume the gate/check just touched is bypassable — find the bypass

Verdict: FINDING — a genuine denial JSONL line written to the log in two separate flushes, with a watchdog scan landing between them, is silently dropped forever (never counted in either scan) because `watchdog_check_one` advances `offset` to `fh.tell()` on every scan even when the trailing bytes are a truncated/partial line, and `_count_structural_denials` silently `continue`s on `json.loads` failure.
Kind: silent-failure
Seed: spawn.py `_count_structural_denials` + `watchdog_check_one` signal-3 (offset-tracked JSONL scan), replacing `_DENIAL_RE.findall(text)`
cap_seconds: 120
tier: default
diff_stat_lines: ~60 (spawn.py + tests/test_spawn.py)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```python
import json, tempfile, os, spawn

d = tempfile.mkdtemp()
log = os.path.join(d, "log.jsonl")
denial_obj = {
    "type": "user",
    "message": {"content": [{
        "type": "tool_result",
        "is_error": True,
        "content": [{"type": "text", "text": "Permission to use this tool has been denied by gate."}]
    }]}
}
line = json.dumps(denial_obj) + "\n"

with open(log, "w") as f:
    f.write(line[:40])          # partial write — line cut mid-JSON

entry = {"log": log, "work": None, "ts": 0}
state = {}
print(spawn.watchdog_check_one("k", entry, now=1000, state=state))  # scan lands mid-write

with open(log, "a") as f:
    f.write(line[40:])          # rest of the line arrives afterward

print(spawn.watchdog_check_one("k", entry, now=1001, state=state))  # scan resumes past the split point
```

### Observed
```
scan1 anomalies: []
offset after scan1: 40
scan2 anomalies: []
offset after scan2: 181
```
The real `is_error` denial (with a `_classify_refusal_text`-matching message) is never surfaced in either scan — `denied-tool-calls` never fires even though `WATCHDOG_DENIAL_THRESHOLD` denials of this exact form occurred.

### Expected
The denial should be counted in one of the two scans (or the offset should not advance past an incomplete trailing line, so the next scan re-reads and completes it). Since spawn logs are actively appended to by a live subprocess while the watchdog polls concurrently, a scan landing between two writes of the same JSONL record is a realistic production timing, not a contrived edge case — and it silently defeats signal 3 for exactly the denial it was reintroduced (issue #994) to detect.
