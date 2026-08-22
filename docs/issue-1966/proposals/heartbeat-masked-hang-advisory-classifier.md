---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
---

## Request

Close the heartbeat-masked hang blind spot in stall detection. Today
`spawn.py:diagnose_health()` classifies a live session HEALTHY on raw log
growth alone (via `watchdog_check_one()`'s `log-silence` signal, which is
mtime-only). A hung child process that keeps emitting `tool_progress`
heartbeat lines (observed live 2026-08-22, issue-1959: a pytest-xdist
worker stuck 22 minutes on a futex) resets mtime every heartbeat, so
`log-silence` never fires and the session stays HEALTHY indefinitely — a
human operator spotted the hang before any watchdog did. Add a
heartbeat-vs-substantive line classifier: N consecutive minutes (start
~15-20, tunable) of heartbeat-only log growth raises a new ADVISORY stall
sub-state. Per the frozen watch-coverage principle, this new signal must
stay strictly advisory — never a session kill, spawn refusal, or gate
block.

## Constraints

- Scope, per the issue body: `on-the-record/monitors/`, `spawn.py`,
  `tests/`, `gates/`, `docs/`. The survey found the actual classification
  logic lives entirely in `spawn.py` (`diagnose_health()` /
  `watchdog_check_one()`); `on-the-record/monitors/poll-heartbeat.sh` only
  calls into it and needs no change to carry the new signal (it already
  echoes `roster_watchdog()`'s full report text verbatim).
- Advisory-only, structurally: the new state's `next_action` must not be
  reachable from any kill/refusal/gate code path — same shape as the
  existing STALLED state's `next_action="resume-watch"`.
- A log whose lines carry no distinguishable heartbeat tag must classify
  HEALTHY with an explicit unmeasurable note, never silently STALLED
  (issue's own empty-state clause) — the classifier must degrade
  gracefully on transcripts that predate/never emit `tool_progress`.
- Threshold must be a tunable module constant, following the
  `WATCHDOG_SILENCE_MIN` precedent (spawn.py:2090), not a hardcoded
  literal buried in the check.
- No new `gh`/git call types (existing constraint `diagnose_health()`'s
  docstring already states and the survey confirmed still holds for this
  addition — the check is pure log-content parsing).
- Fixture-based tests, asserted in a live test run, covering: (a) a
  heartbeat-only-for->N-minutes fixture → new advisory sub-state; (b) a
  fixture with interleaved substantive lines → HEALTHY; (c) advisory-only
  structural assertion (no kill/refusal/gate path reachable).

## Rationale

Two shapes were considered for where the heartbeat/substantive
distinction lives:

1. **A new signal inside `watchdog_check_one()`, surfaced through
   `diagnose_health()`'s existing state-branch composition** (chosen).
   `watchdog_check_one()` already re-parses the same scanned log slice for
   several signals (denial counting, delegation phrasing) — adding a
   heartbeat/substantive line-classification pass over the same `text`
   variable is a same-shape addition, not a new scanning mechanism. The
   new state (e.g. `STALLED-HEARTBEAT-ONLY`) plugs into
   `diagnose_health()`'s existing `if state != "HEALTHY"` composition at
   its one consumer site (spawn.py:3341) with no change to
   `roster_watchdog()`'s dispatch.

2. **A wholly separate classifier module/function invoked directly by
   `poll-heartbeat.sh` or a new gate under `gates/`, alongside
   `diagnose_health()`.** Rejected: this would require a second log-read
   pass over the same session log (the survey found `watchdog_check_one()`
   already tracks scan-offset state per key to avoid re-reading — a
   parallel classifier would either duplicate that offset bookkeeping or
   re-scan the whole log every tick) and a second place for
   `roster_watchdog()` to merge two independent verdicts into one report
   line, doubling the surface that must stay advisory-only instead of
   reusing the one surface (`diagnose_health()`) already proven advisory
   by the existing STALLED precedent.

For the substantive/heartbeat *distinction* itself, structural JSONL
line-type parsing was chosen over text/regex matching, following the
`_count_structural_denials()` precedent (spawn.py:3614) that replaced an
earlier word-match denial counter after it produced a 89-reported/0-actual
false-positive rate (issue #994, cited in that function's own docstring).
A line is heartbeat iff it structurally parses as `type: "tool_progress"`
with the heartbeat-marker field the issue names; anything else that
parses as a session-log event line counts as substantive. Lines that fail
to parse (truncated tail, non-JSONL content) are treated the same
tolerant way `_count_structural_denials()` already treats them —
skipped, not counted as either.

## What will be done

- Add a module constant `WATCHDOG_HEARTBEAT_ONLY_MIN` (default in the
  15-20 range the issue specifies) next to `WATCHDOG_SILENCE_MIN`
  (spawn.py:2090), overridable the same way existing watchdog thresholds
  are, for test tunability.
- Add a small helper (e.g. `_classify_log_lines_heartbeat_only(text, now,
  window_min)`) that: parses each JSONL line structurally; buckets lines
  with a parseable timestamp into heartbeat-only vs. substantive vs.
  unparseable; and returns whether the most recent `window_min` minutes
  of *parseable, timestamped* activity contains only heartbeat lines (and
  at least one heartbeat line — an empty/all-unparseable window is not a
  heartbeat-only window). If no line in scope carries a distinguishable
  heartbeat tag at all, returns an explicit "unmeasurable" result rather
  than a heartbeat-only verdict.
- Wire this helper into `watchdog_check_one()` as a new anomaly signal
  (e.g. `heartbeat-only-growth: ...`), scanned over the same offset-based
  `text` slice already read for signals 2-4 (no new log read).
- Extend `diagnose_health()`'s state branch: when `heartbeat-only-growth`
  fires and no other STALLED-triggering anomaly already fired, return the
  new advisory sub-state (name TBD at build time, e.g.
  `"STALLED-HEARTBEAT-ONLY"`) with a `next_action` value that is
  observe-only (mirroring STALLED's `"resume-watch"`, or a distinct
  observe-only action name if `resume-watch`'s watch-rearm semantics
  don't fit — build-time judgment, no kill/refusal/gate action either
  way). When the log is unmeasurable for heartbeat tagging, the existing
  HEALTHY-with-plain-log-growth path is left untouched (explicit
  unmeasurable note carried in `detail`, not silently STALLED).
- Add fixture-based tests to the existing `DiagnoseHealth` class in
  `tests/test_spawn.py`: (a) synthetic JSONL fixture with only
  `tool_progress` heartbeat lines spanning >N minutes of timestamps →
  asserts the new advisory state; (b) same fixture with substantive lines
  interleaved → asserts HEALTHY; (c) a structural assertion that the new
  state's `next_action` (and any code path reachable from it) never
  triggers a kill/spawn-refusal/gate-block — e.g. asserting the action
  name is in the same allowed advisory set STALLED's `resume-watch`
  already belongs to, or a direct check that no kill/refusal function is
  called when the module is exercised with the new state.
- Update `diagnose_health()`'s and `watchdog_check_one()`'s docstrings to
  document the new signal/state, following the existing per-signal
  comment convention in that function.

## Out of scope

- Changing `on-the-record/monitors/poll-heartbeat.sh` — it already
  passes through `roster_watchdog()`'s report text verbatim; the new
  advisory line rides the existing report/delta-suppression pipeline with
  no script change needed.
- Any `gates/` change — no existing gate consumes `diagnose_health()`'s
  state directly in a way that would need updating for a new advisory
  value (confirmed by the survey finding `roster_watchdog()`'s only
  dispatch is the plain `!= "HEALTHY"` inequality at spawn.py:3341).
- Retroactively reclassifying past sessions or backfilling heartbeat tags
  onto historical logs.
- Changing `WATCHDOG_SILENCE_MIN` or any existing signal's threshold.
- Auto-respawn or auto-kill wiring for the new state — explicitly
  forbidden by the acceptance criteria (advisory-only, no code path to a
  kill/refusal/block).

## Accumulation

This adds exactly one new signal function and one new module constant to
`spawn.py`, called from the one existing `watchdog_check_one()` scan loop
— it does not add a per-role/per-repeat inline `subprocess`/`gh` call or
touch any `roles/*.json`-style repeated-file list. If a future issue adds
more content-classification signals of this kind (e.g. distinguishing
further sub-categories of non-substantive log growth beyond
`tool_progress` heartbeats), the shared helper introduced here
(`_classify_log_lines_heartbeat_only`, structurally parsing the same
offset-scanned `text` slice) is the extension point — additional signals
should branch inside it or call a shared line-classification primitive it
exposes, rather than each adding its own ad hoc JSONL-parsing loop next to
signals 2-6 in `watchdog_check_one()`. No accumulation risk in the
repeated-file sense applies to this change.

## How you'll know it worked

- `pytest tests/test_spawn.py -k DiagnoseHealth` passes, including the
  two new fixture tests (heartbeat-only-for->N-minutes → advisory state;
  interleaved substantive → HEALTHY) and the advisory-only structural
  test, run live.
- Manual/live check: constructing a synthetic log matching the observed
  issue-1959 hang shape (only `tool_progress` lines, timestamps spanning
  >N minutes) and calling `diagnose_health()` against it returns the new
  advisory state, not HEALTHY.
- Grep-level check: the new state's `next_action` value does not appear
  in any kill/spawn-refusal/gate-block code path in `spawn.py`.
