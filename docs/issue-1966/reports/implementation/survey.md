---
subject: issue-1966
kind: survey
---

# Current-state survey: heartbeat-masked-hang blind spot

## What was checked

- `on-the-record/monitors/poll-heartbeat.sh` (435 lines): the Monitor tick
  loop. It calls `python3 spawn.py watchdog --auto-respawn` every due tick
  and prints/dedups the resulting report. It does not itself classify
  session health — it is a caller, not the classifier.
- `spawn.py:diagnose_health()` (spawn.py:2278-2340): the actual
  HEALTHY/STALLED/DEADLOCKED/DEAD-ERRORED classifier (issue #782). For a
  live entry (`_alive(pid)` true), it checks `_deadlock_signature()` first,
  then falls straight to:
  ```
  if any(a.startswith("log-silence") or a.startswith("watcher-silent")
         for a in anomalies):
      return {"state": "STALLED", ...}
  return {"state": "HEALTHY", ...}
  ```
  — i.e. HEALTHY is the fallback whenever neither `log-silence` nor
  `watcher-silent` fired.
- `spawn.py:watchdog_check_one()` (spawn.py:2109-2225): produces the
  `anomalies` list `diagnose_health()` consumes. Signal 1 (spawn.py:2126-2131)
  is `log-silence`, and it is purely mtime-based: `silent_min = (now -
  log_path.stat().st_mtime) / 60`, flagged only if `silent_min >
  WATCHDOG_SILENCE_MIN` (90). Any write to the log file — including a
  `tool_progress` heartbeat line — resets mtime and defeats this check.
  None of signals 2-6 (delegation phrasing, denied-tool-calls,
  no-commits-late, watcher-missing/dead/silent) inspect line *content* for
  a heartbeat-vs-substantive distinction; they either regex-match specific
  phrases or check unrelated files (git HEAD, watcher log).
- `_count_structural_denials()` (spawn.py:3614-3646) is the one existing
  precedent for structurally parsing the session-log JSONL instead of
  scanning raw text: it line-splits, `json.loads` per line (swallowing
  `ValueError` for a truncated trailing line — the same live-tail
  tolerance a heartbeat classifier will need), filters
  `obj.get("type") == "user"`, and inspects `tool_result` content blocks.
  This is the closest existing structural-JSONL-parsing pattern to model a
  new classifier on.
- No existing code in `spawn.py`, `on-the-record/monitors/`, or
  `on-the-record/hooks/` references `tool_progress` or `heartbeat` as a
  session-log line type/tag. Repo-wide grep for `tool_progress`/`heartbeat`
  (excluding poll-heartbeat.sh's own name and unrelated
  monitor-alive-marker comments) returns nothing — this is genuinely new
  classification surface, not a rename of an existing check.
- No local fixture or sample session-log JSONL in the tree currently
  contains a `tool_progress` line (checked `docs/issue-776/reports/
  execution-observation/*.jsonl`, the only transcript-shaped `.jsonl`
  files under version control) — the classifier's tests will need a
  synthetic fixture built from the shape the issue itself describes
  (only `tool_progress` heartbeat lines for >N minutes of timestamps vs.
  interleaved substantive lines), not a captured real log.
- Live JSONL session-log lines already have an established shape the repo
  parses structurally: `{"type": ..., "message": {...}, "timestamp":
  ...}` — `_count_structural_denials()` reads `type` and nested
  `message.content` blocks. The issue's own scope note says "a log whose
  lines carry no distinguishable heartbeat tag is classified HEALTHY with
  an explicit unmeasurable note" — i.e. the classifier must not assume
  every session log actually contains `tool_progress`/heartbeat-tagged
  lines (older transcripts, or logs where the harness never emits that
  event type, must degrade gracefully rather than false-stall).
- `WATCHDOG_SILENCE_MIN = 90` (spawn.py:2090) is the existing tunable
  threshold constant for the sibling log-silence check — same file-scope
  module constant pattern to follow for the new N-minute
  heartbeat-only-window threshold (issue's own text: "start ~15-20,
  tunable").
- `diagnose_health()`'s return contract (`{"state", "next_action",
  "detail"}`) is consumed at spawn.py:3341 (`roster_watchdog()`):
  ```
  if health["state"] is not None and health["state"] != "HEALTHY":
  ```
  — this is a plain state-name inequality check, not a hardcoded
  enum/switch, so introducing a new state value here composes without
  editing `roster_watchdog()`'s dispatch itself, *provided* the new state
  is handled the same non-blocking way STALLED already is (STALLED's own
  `next_action` is `"resume-watch"`, never a kill/refusal/gate path —
  precedent for "advisory-only" already exists in this exact function).
  `next_action="resume-watch"` for STALLED only triggers watch re-arming
  in `roster_watchdog()`, never a session kill, spawn refusal, or gate
  block. canonical: spawn.py:3333-3341 (`roster_watchdog()` health-branch
  read directly, no kill/refusal call reachable from it).
- `DiagnoseHealth` test class in `tests/test_spawn.py` (~line 10616
  onward) is the existing test home for `diagnose_health()` state
  transitions (`test_healthy_when_alive_and_no_anomalies`,
  `test_stalled_when_alive_but_idle_past_threshold`, etc.) — the natural
  place to add heartbeat-vs-substantive fixture tests, following the same
  `tempfile.TemporaryDirectory()` + hand-written JSONL-log-file fixture
  pattern already used there.

## Gap this issue closes

`diagnose_health()` currently has exactly one path to `STALLED` while
alive (`log-silence`/`watcher-silent`, both silence-based) and one
fallback path to `HEALTHY` (anything else). A session whose child process
is hung but which keeps emitting `tool_progress` heartbeat lines never
trips `log-silence` (mtime keeps moving) and is classified HEALTHY
indefinitely — the observed 2026-08-22 issue-1959 pytest-xdist futex hang.
No existing signal inspects log *content* for a heartbeat-vs-substantive
distinction.
