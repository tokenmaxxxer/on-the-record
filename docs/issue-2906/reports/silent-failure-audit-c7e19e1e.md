---
issue: 2906
role: silent-failure-audit-c7e19e1e
author: silent-failure-audit-c7e19e1e
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: same-commit:on-the-record/monitors/poll_heartbeat_delta.py
    sha: same-commit
  - path: same-commit:on-the-record/monitors/test_poll_heartbeat.py
    sha: same-commit
---

# issue-2906 — silent-failure-audit-c7e19e1e record

## What was done

CORE_BUILD_NOW=1 was set (spawner-provided) — proposal round skipped per
contract v3 s19a, delivered directly on this branch.

**Sequencing check**: #2904 (PR #2905, session-completion/mid-flight
signal) is merged to main — canonical: `git log --oneline | grep e516a433`
on this branch shows `e516a433 issue-2904: track spawned sessions
(completion, mid-flight files, tool activity) (#2905)` in this branch's
history. This issue builds on that landed machinery, not around it.

**Measurement first** (issue's own instruction, before any design):

canonical: the orchestrator's own live session transcript, on disk at
`~/.claude/projects/-home-jwjung-tokenmaxxxer/93c239f8-561b-41f5-b69c-ae9e757b7939.jsonl`
(101MB, 68279 JSONL records, 2026-08-23T09:18 through 2026-08-31T02:19 —
this IS the "2026-08-31 orchestrator transcript" the issue names; it is
one continuous session whose most recent activity lands on 2026-08-31,
read in full via a parsing script for this measurement). Every
Monitor-relayed heartbeat surfaces in this log as a `type:
queue-operation, operation: enqueue` record whose `content` is a
`<task-notification>` wrapping the tick's `<event>` body — this is the
concrete mechanism the issue calls "wakes the orchestrator": each such
enqueue is dequeued into a `type: user, promptSource: system` message,
which forces one full assistant turn.

derived: a parsing script (`python3 -c "..."`, iterating the transcript
line by line, regex `<event>(.*?)</event>` per enqueue record) counted
every `<task-notification>` enqueue across the full transcript and
classified its `<event>` body as anomaly-bearing (matches `STALLED|
CRASHED|COMPLETED|watcher-dead|DEAD-|DEADLOCKED|\[health\]|\[orphaned\]|
\[resume\]|\[returned-pr\]|\[standing-red\]|\[checkpoint\]|
\[watchdog-crash\]|\[poll-report-drain-failed\]|promotion\(s\)|
awaiting-approval`) or routine (no such marker) — result:

```
total task-notifications (enqueued):        2493
anomaly-bearing:                              304  (12.2%)
routine (no actionable content):             2189  (87.8%)
  of which contain a [poll-report] HEALTHY line:  377
max consecutive routine-only notifications:   197
count of runs reaching >=5 consecutive routine notifications: 95
```

87.8% of every wake the orchestrator received over this 8-day session
carried nothing it could act on, confirming the issue's premise
quantitatively rather than anecdotally — this is the "before" measurement.

**Root cause, traced** (silent-failure-audit trace-forward method — site
→ downstream consequence):

- Site: `watchdog.py:1946`, inside `roster_watchdog()` — canonical:
  ```
  print(f"[poll-report] {key}: {health['state']} — {health['detail']}")
  ```
  runs unconditionally every due tick for every live roster entry (issue
  #782 scope-expansion comment at `watchdog.py:1945`, verbatim: "dedup
  원장과 무관하게 매 틱 상태를 보고한다" — reports every tick regardless
  of the dedup ledger).
- For `state == "HEALTHY"`, `detail` is built at `watchdog.py:504-505` as
  canonical:
  ```
  return _diagnosis({"state": "HEALTHY", "next_action": "none",
          "detail": f"{key}: 최근 로그 성장, RUNNING — {workspace_summary}; {activity_summary}"})
  ```
  where `activity_summary` comes from `_last_tool_activity_summary()`
  (`watchdog.py:253-318`, added by #2904) — it names the session's most
  recent `tool_use` and an absolute timestamp, and by design (per that
  function's own docstring at `watchdog.py:262-269`) changes precisely
  when the session calls a *new* tool since the last tick.
- Downstream: `on-the-record/monitors/poll_heartbeat_delta.py`'s
  line-keyed delta suppression (#1220/#2266) keys a `[poll-report]` line
  as `poll-report:{key}` (via `TAG_RE`, `poll_heartbeat_delta.py:29`)
  and, before this fix, compared the **full line text** tick to tick
  (`changed = prev_lines.get(key) != line`). An actively-working session
  calls a new tool on essentially every poll interval, so this HEALTHY
  line was never byte-identical two ticks running — the very case #1220
  built delta-suppression to quiet (nothing anomalous happened) was the
  one case that structurally always found a "changed" line and
  re-notified. Consequence, traced to its end: the orchestrator receives
  a full task-notification, and therefore spends a full turn, on
  essentially every due tick (~120s) that any roster entry is alive and
  healthy — independent of whether anything needing a decision occurred.
  This matches the issue's `이상 신호 없음` example directly: canonical
  — that tick's `<event>` body (transcript line index 2144, timestamp
  2026-08-23T15:13:30Z) also carried a `[watchdog] issue-72/implementation:
  정상` companion line for the live entry, the same mechanism at the
  `[watchdog]` tag (a static "정상" string, not itself the leak — the
  leak is specifically the `[poll-report]` HEALTHY line's activity
  clause, confirmed separately below).

**Fix**: `on-the-record/monitors/poll_heartbeat_delta.py` — for lines
keyed `poll-report:*`, when the current state token is `HEALTHY`,
compare against the previous tick with the trailing
`; 마지막 도구 호출: ...` / `; 도구 호출 (로그|기록) 없음` clause
stripped from both sides before deciding `changed`. A transition into or
out of HEALTHY still always emits (state-token mismatch). A change to
the **workspace** portion of the detail (dirty-file set, "기록 시작함")
still always emits, because that portion is *not* stripped — this is
exactly the case #2904's own regression pin requires.

derived: `python3 -m pytest test/test_workspace_progress_tracking.py -q` output, this turn
Acceptance requirement met — checked: `python3 -m pytest test/test_workspace_progress_tracking.py -q` — result: 14 passed, 0 failed (`DeltaSuppressionForWorkspaceProgressTest::test_new_file_touched_reemits_the_changed_line` included and passing, unmodified).

Every non-HEALTHY state (STALLED,
DEADLOCKED, DEAD-ERRORED, DEAD-UNRECOVERED-COMMITS,
DEAD-REMOTE-STATE-UNKNOWN, STALLED-HEARTBEAT-ONLY,
STALLED-FLAT-PROGRESS) is untouched — same full-line compare as before
this issue. No orchestrator-side filtering: the suppression happens
before the Monitor tool ever turns the tick into a notification, not
after the orchestrator is woken. No interval change:
`POLL_HEARTBEAT_SLEEP_SECONDS` and the 60s `poll_due()` TTL are both
untouched (unread/uncalled by this diff).

**Hypothesis test** (hypothesis-testing skill, directional/early-stage
report — genuinely open go/kill/won't-fix decision per the issue's own
framing):

- Theory: stripping only the last-tool-activity clause from a HEALTHY
  `[poll-report]` line before delta-comparison will cut empty/
  non-actionable orchestrator wakes for actively-working roster entries,
  because the current full-line compare treats that ever-changing clause
  as a state change every tick even though nothing anomalous happened.
- Hypothesis: replaying a steady-state HEALTHY entry (same key, same
  workspace, only the activity clause advancing) through the fixed delta
  script over N ticks produces materially fewer Monitor notifications
  than the pre-fix script, while a STALLED transition and a real
  workspace change still notify on both trees.
- Decision rule (pre-registered before running the replay): fixed
  tree's notification count must drop well below the original tree's
  for the steady-state case, AND zero anomaly/transition cases may be
  suppressed → persist (ship). Any anomaly suppression, or no material
  drop → kill/revert.
- Measured: derived — `python3` replay script feeding N=30 identical
  synthetic HEALTHY ticks (same key, same workspace, advancing activity
  timestamp) through `git show HEAD:on-the-record/monitors/
  poll_heartbeat_delta.py` (origin/main's copy) and through this
  branch's copy, counting non-empty stdout per tick:
  ```
  OLD (origin/main):      30/30 due ticks produced a Monitor notification
  NEW (this branch):       1/30 due ticks produced a Monitor notification
  ```
  and the anomaly/transition checks
  (`t_healthy_to_stalled_transition_still_notifies`,
  `t_healthy_workspace_change_still_notifies_despite_activity_drift`,
  both in `on-the-record/monitors/test_poll_heartbeat.py`) pass — zero
  anomaly suppression observed (see test-run evidence below). Verdict:
  **persist** — registered threshold (material drop, zero anomaly
  suppression) met by the measured result (30→1, 0 anomaly
  suppressions); shipped as this fix. No override.

**Monitor-liveness check independent of the wake (issue's second
acceptance check)**: this machinery already exists, untouched by this
fix — `on-the-record/hooks/directive.sh`'s
`_monitor_liveness_check_and_notify()` (issue #1497/#2182) reads
`runs/poll_heartbeat_alive.json`, written every tick loop iteration
regardless of `poll_due()`'s outcome, and compares its age against
`MONITOR_LIVENESS_STALE_SECONDS` (default 360s = 3x the 120s poll
cadence). Confirmed executed-live by extracting the function
(`sed -n '207,271p' on-the-record/hooks/directive.sh` plus a trailing
`}`) and driving it directly — derived:

```
$ printf '{"last_tick": %s}' "$(($(date +%s) - 400))" > runs/poll_heartbeat_alive.json  # 400s > 360s bound
$ _monitor_liveness_check_and_notify "$CHECKOUT"
[orchestrate][MONITOR-DEAD] poll-heartbeat monitor dead since 2026-08-31T11:25:54+0900 -- ACTION REQUIRED before anything else this turn: re-arm it via the Monitor tool with persistent: true (command: .../on-the-record/monitors/poll-heartbeat.sh) -- a re-arm without persistent: true dies again in 5 minutes, the Monitor tool's own default timeout_ms
$ _monitor_liveness_check_and_notify "$CHECKOUT"   # same episode, called again immediately
(no output — de-duped, matches issue #1497's contract)
```

This confirms the issue's own hypothesis empirically: liveness is
already checkable on any ordinary turn-driven hook firing (no dedicated
periodic wake needed to detect a dead monitor), which is why this fix
could quiet the HEALTHY-confirmation wake without weakening liveness
detection — the two were already separated by #1497, before this issue.
The stated bound is the existing 360s threshold; not changed by this fix.

**A real event still wakes the orchestrator promptly (issue's third
acceptance check)**: unaffected — the fix touches only the HEALTHY
comparison branch. `t_healthy_to_stalled_transition_still_notifies`
(see test-run evidence below) demonstrates a HEALTHY→STALLED transition
notifies on the same tick it occurs (no added latency; cadence is still
the unchanged ~120s poll interval).

**Tests**: two new regression tests plus one guard test added to
`on-the-record/monitors/test_poll_heartbeat.py` (its existing
`t_`-prefixed, non-pytest-native convention, still collected by pytest
here — this repo's `pytest.ini` sets `python_functions = test_* t_*`):
`t_healthy_poll_report_with_drifting_detail_suppresses_after_first_tick`,
`t_healthy_to_stalled_transition_still_notifies`,
`t_healthy_workspace_change_still_notifies_despite_activity_drift`.

acceptance: `python3 on-the-record/monitors/test_poll_heartbeat.py` —
derived:
```
$ python3 on-the-record/monitors/test_poll_heartbeat.py 2>&1 | tail -3
ok  t_unkeyed_line_insertion_suppresses_unchanged_lines_below

33/33 passed
```
(30 pre-existing + 3 new, all listed above.)

acceptance: `python3 -m pytest . -q` from the repo root — derived:
```
$ python3 -m pytest . -q 2>&1 | tail -1        # this branch
17 failed, 691 passed, 3 xfailed in 34.49s
$ git stash -u && python3 -m pytest . -q 2>&1 | tail -1 && git stash pop   # origin/main baseline
17 failed, 688 passed, 3 xfailed in 34.60s
$ diff <(grep '^FAILED' new.txt | sort) <(grep '^FAILED' main.txt | sort)
(empty — identical failing-test name sets)
```
Same 17 pre-existing failures on both trees (none touching
`on-the-record/monitors/`); the +3 passed on this branch are exactly the
new tests above.

acceptance: `python3 gates/retirement_count.py` — derived:
```
$ python3 gates/retirement_count.py | wc -l        # this branch
1136
$ git stash -u && python3 gates/retirement_count.py | wc -l && git stash pop   # origin/main
1136
```
Identical match count on both trees; the only `diff` between the two
runs' output is line-number drift inside `test_poll_heartbeat.py` from
the tests appended above (same content, no new role-axis mentions
introduced).

acceptance: overhead — derived: timed 200 invocations of
`poll_heartbeat_delta.py` against identical synthetic input on both
trees:
```
origin/main:  4.450s / 200 invocations (22.25 ms/tick)
this branch:  4.436s / 200 invocations (22.18 ms/tick)
```
No measurable increase (the fix adds two regex operations per
`poll-report` line, no new I/O or subprocess calls).

## Why

The issue asks for measurement before design, and the measurement
pointed at a narrower, more mechanical cause than "redesign the wake
model": #2904 (landed just before this issue was opened) added
last-tool-activity to the HEALTHY status line specifically so a human
could tell "invested work" from "stalled" during a dirty-but-unchanged
workspace — a legitimate, wanted signal. But because that signal always
changes for an actively-working session, and the existing delta
suppression compares full line text, it defeated its own suppression
mechanism for exactly the routine case (healthy, working) that has
nothing for the orchestrator to decide. The fix is the minimal, targeted
correction of that specific defeat, not a redesign of the wake/liveness
separation the issue's hypothesis proposed — that separation
(event-driven wake via Monitor-relayed anomalies; liveness checkable via
`poll_heartbeat_alive.json` without consuming a turn) was already built
by #1497/#2182/#1220, before this issue existed (see the monitor-liveness
acceptance evidence above). Re-inventing it would have duplicated
working machinery; the actual gap was one place where a
legitimately-useful-but-always-changing detail string leaked past that
machinery's suppression. Scoping the fix to the `poll-report:` HEALTHY
branch only, and stripping only the activity clause (not the whole
line), keeps every other tag (`[watchdog]`, `[health]`, `[orphaned]`,
`[resume]`, `[returned-pr]`, `[standing-red]`, `[checkpoint]`,
`[watchdog-crash]`, board-sweep, patrol) and every non-HEALTHY
poll-report state on its pre-existing, unmodified comparison path —
satisfying "every anomaly that reaches the orchestrator today must
still reach it" by construction (nothing in their code path changed)
rather than by a fresh proof for each one.

## What did not work

The first cut of this fix suppressed any unchanged-state HEALTHY line
regardless of *which* part of `detail` changed. That was too broad: it
was caught by the existing `test/test_workspace_progress_tracking.py::
DeltaSuppressionForWorkspaceProgressTest::test_new_file_touched_reemits_the_changed_line`
regression before landing — canonical: running `python3 -m pytest
test/test_workspace_progress_tracking.py -q` against that first-cut diff
produced one failure at exactly that test (assertIn("spawn.py", out2)
failed because the fixed tree suppressed the whole HEALTHY line,
including the workspace-summary change that should have emitted). That
test asserts a HEALTHY entry whose workspace summary changes (a
newly-dirtied file) must still notify — a real, #2904-intended signal,
not noise. The fix was narrowed from "ignore all HEALTHY-line drift" to
"ignore only the last-tool-activity clause" (`POLL_REPORT_ACTIVITY_STRIP_RE`
in `poll_heartbeat_delta.py`), which satisfies both this issue's
suppression goal and #2904's existing contract; see "What was done" /
"Why" above for the corrected shape and its passing re-run. No other
approach was tried and abandoned.

## Upstream basis

- `on-the-record/monitors/poll_heartbeat_delta.py` (same commit) — the
  delta-suppression script this fix modifies; pre-existing machinery
  from #1220/#1719/#2180/#2266.
- `watchdog.py` (read, not modified) — `roster_watchdog()` (the
  `[poll-report]` print site, `watchdog.py:1946`) and `diagnose_health()`
  (the HEALTHY `detail` shape, `watchdog.py:321-505`), both from issue
  #782 and its #2904 scope-expansion.
- `docs/handbooks/monitor-liveness.md` — canonical: read in full; the
  #1497/#2182 stamp/staleness contract it documents was independently
  re-verified live by extracting and running
  `_monitor_liveness_check_and_notify()` (see the acceptance evidence
  in the "What was done" section's monitor-liveness paragraph).
- Orchestrator transcript
  `93c239f8-561b-41f5-b69c-ae9e757b7939.jsonl` (external, not a repo
  path — read-only measurement source, cited in full above).

## Open findings

- Of the 2189 routine (no-actionable-content) notifications measured,
  377 carried the `[poll-report]` HEALTHY line this fix suppresses; the
  remaining ~1812 are dominated by two other recurring patterns not
  fixed here: (a) `[watchdog] board-sweep: full-rescan (...)` firing far
  more often than a "cursor damaged / page overflow / periodic rescan"
  fallback should, suggesting the gh_delta cursor may not be persisting
  correctly for some repos, and (b) `[watchdog] accumulation-trend: no
  prior tick data (first run) — ...` recurring across many ticks instead
  of once, suggesting `_accumulation_repo_key()` may not be stable
  across ticks for some checkouts. Both are board-sweep/gh_delta-layer
  issues distinct from the `roster_watchdog()` per-entry mechanism this
  issue's acceptance criteria scope to ("`diagnose_health()`'s per-tick
  output," named explicitly in the issue text) — resolution path: a
  follow-up issue against `gh_delta`'s cursor persistence and
  `closure_sweep._accumulation_repo_key()`, quantified first with the
  same transcript-based measurement method used here.
- 104 of the routine notifications were "no live roster entries"
  (`돌고 있는 역할/스킬 세션 없음` + `이상 신호 없음`) reaching the
  Monitor channel; per `poll_heartbeat_delta.py`'s `FIXED_TAG_RE`
  content-keying this text should already delta-suppress after its
  first occurrence within one continuous `runs/` state file — recurring
  itself is evidence the state file was reset mid-session (the `#2163`
  comment in `poll-heartbeat.sh` documents one such mid-session
  checkout-refresh path). Not chased further here since it is a
  state-persistence question independent of this issue's suppression
  logic and does not affect the acceptance checks scoped to this issue.
  Resolution path: a follow-up issue, using the same transcript
  measurement method, focused specifically on
  `runs/poll_heartbeat_last_state.json`'s lifetime across a long-running
  session.

## Next steps

None — loop_state is terminal (`landed`). This branch's commit and PR
carry the fix, tests, and this record together (build-now bypass,
contract v3 s19a).

skill-verdict: silent-failure-audit — applied: invoked; traced
`watchdog.py:1946`'s unconditional `[poll-report]` print through
`_last_tool_activity_summary()`'s always-changing detail to
`poll_heartbeat_delta.py`'s full-line compare, per the trace-forward
method (site → detail construction → downstream comparison →
consequence), to locate the exact defeat of the existing #1220
suppression rather than redesigning the wake mechanism.
skill-verdict: hypothesis-testing — applied: invoked; pre-registered a
directional decision rule (material notification drop + zero anomaly
suppression → persist) before running the before/after replay, then
reported the verdict against that rule (see the hypothesis-test
paragraph in "What was done").
skill-verdict: work-in-english — applied: invoked; this record, the
code comments, and the diff are in English; only the final chat summary
to the user is Korean, per project convention.
other mounted skills: not triggered
