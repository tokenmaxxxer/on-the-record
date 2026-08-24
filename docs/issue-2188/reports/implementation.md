---
issue: 2188
role: implementation
loop_state: landed
upstream:
  - path: roster.py
    sha: 188ceb3e4328fad06d8ab79aca19d2b787f42015
code_under_review: same-commit
type: fix
breaking: false
verdict: pass
---

# issue-2188 — implementation record

## What was done

Widened `roster._lease_progress_indicator()` (the value `lease_renew()`
compares across renewals to decide `flat-progress`) so it also folds in the
byte size of the session's own transcript log (`entry["log"]`), in addition
to the existing `events.jsonl` line count and workspace HEAD SHA:

```python
return (f"{_sp._event_count(_sp._events_path(work))}:"
        f"{_sp._git_head(work) or ''}:{log_size}")
```

Added two regression tests to `tests/test_watch_hardening.py`
(`FlatProgressRenewal`):

- `test_tool_call_activity_without_commits_is_not_flat` — simulates the
  issue-2186 shape: a session's transcript log grows every lease-renewal
  tick (as it would from `Read`/`Grep`/`sed`/`TaskOutput`/... tool calls)
  while `events.jsonl` and HEAD stay untouched. Asserts `lease_renew()`
  returns no anomalies across `LEASE_FLAT_RENEWALS_K + 2` renewals.
- `test_true_stall_with_no_log_growth_still_flags` — the acceptance
  criterion's regression guard: a session whose log never grows (no tool
  calls at all) across `LEASE_FLAT_RENEWALS_K + 1` renewals still trips
  `flat-progress`, so the widening doesn't blind the check.

## Why

Investigated the indicator's actual definition first (issue's own
"Investigate" ask). `_lease_progress_indicator()` was
`event_count(events.jsonl):git_head` only.

canonical: `grep -n "STALLED-FLAT-PROGRESS\|flat.progress" watchdog.py roster.py` (this session) — result:
```
roster.py:203:def lease_renew(key: str, entry: dict, root: Path = None,
roster.py:228:    if flat >= _sp.LEASE_FLAT_RENEWALS_K:
watchdog.py:283:    if any(a.startswith("flat-progress") for a in anomalies):
watchdog.py:290:        return {"state": "STALLED-FLAT-PROGRESS", ...}
```
located `roster.py:192` (`_lease_progress_indicator`), `roster.py:203-233`
(`lease_renew`), `watchdog.py:283-293` (`diagnose_health`'s
`STALLED-FLAT-PROGRESS` branch) — the pre-fix indicator was exactly
`event_count(events.jsonl):git_head`, and the threshold is
`LEASE_FLAT_RENEWALS_K` (unchanged, =3) consecutive renewals with that
string unchanged.

`events.jsonl` is append-only, but per `events.py`'s `_append_event()` call
sites (read directly) it only grows on a `Write`/`Edit` tool call to a new
file path (`spawn.py:3000-3005`), a `Bash` command starting with one of
`_PROGRESS_BASH_PREFIXES` (`spawn.py:3006-3011`), or a permission-denial
being classified (gate/harness/sandbox refusal).

canonical: `grep -n "_PROGRESS_BASH_PREFIXES" spawn.py events.py` (this session) — result:
```
events.py:69:_PROGRESS_BASH_PREFIXES = ("git commit", "git push", "gh pr create",
spawn.py:219:_PROGRESS_BASH_PREFIXES = events._PROGRESS_BASH_PREFIXES
spawn.py:3007:                            if command.startswith(_PROGRESS_BASH_PREFIXES):
```
`spawn.py:3007` is the tuple's single consumer — no Read/Grep/generic-Bash/
`TaskOutput` call reaches `_append_event()` at all.

That list is deliberately narrow by design — the code comment at
`events.py:66-68` names issue #180 explicitly: exploratory calls
(`ls`/`grep`/`cat`) are excluded on purpose so that *stream* stays a
"what happened" artifact log, not a liveness signal. But `lease_renew()`
(issue #2101 mechanism 2) reused that same narrow stream as its liveness
signal, which is the underlying problem: any session phase that doesn't
produce a commit-shaped Bash call or a fresh Write/Edit path — reading
source, running `TaskOutput` blocking waits on delegated work, review-only
observer roles — leaves the indicator completely flat, and 3 renewals
later `diagnose_health()` reports `STALLED-FLAT-PROGRESS` on a
demonstrably healthy, actively-working session. This matches the shape of
every observation cited in the issue (issues #2156, #2164-#2166, #2185,
#2186), each of whose flagged sessions' last tool call was neither a
Write/Edit nor a commit-shaped Bash command.

Chose to widen the *lease indicator* specifically (`roster.py`), not the
shared `events.jsonl` progress stream (`events.py`/`spawn.py`) that issue
#180 deliberately narrowed for a different consumer.

canonical: `grep -n '"progress"' watchdog.py spawn.py gates/role_spec_shape.py` (this session) — result:
```
watchdog.py:188:        (e.get("ts", -1) for e in events if e.get("type") == "progress"),
gates/role_spec_shape.py:29:_LOOP_BUCKETS = {"progress", "terminal", "refusal", "error"}
spawn.py:2043:                loop_state = (enum.get("progress") or [flat[0]])[0]
spawn.py:3004:                                _append_event(events_path, "progress",
spawn.py:3009:                                _append_event(events_path, "progress",
```
`watchdog.py:188` reads `type == "progress"` events for
`_deadlock_signature()`'s "same refusal repeating since the last real
progress event" window — a second, distinct consumer of the same narrow
stream, which the survey above establishes still needs "exploratory calls
don't count" to hold: broadening `_PROGRESS_BASH_PREFIXES` or the
Write/Edit path-dedup would have reopened issue #180's problem for that
consumer as a side effect of fixing this one.

The session's own transcript log (`entry["log"]`, already read every tick
by `watchdog_check_one()` for the `log-silence` signal — `spawn.py:878,
884-889`) is append-only and grows on every tool call regardless of kind,
so folding its size into the lease indicator gives `lease_renew()` a true
"any activity happened" signal without touching the narrower stream
`_deadlock_signature()` depends on.

Considered making the indicator equal to `log_path.stat().st_mtime`
instead of size: mtime is a coarser signal (multiple tool-call boundaries
can land on the same wall-clock second, and mtime resolution/rounding
varies by filesystem), whereas the log is strictly append-only so its
byte size is monotonic and exact — chose size for that reason.

## Upstream basis

- `roster.py` at `188ceb3e4328fad06d8ab79aca19d2b787f42015` (this branch's
  HEAD before this change) — `_lease_progress_indicator()`,
  `lease_renew()`, `_declared_wait_valid()`.
- `events.py` at the same sha — `_PROGRESS_BASH_PREFIXES`, `_append_event()`
  call sites, the issue-#180 code comment explaining why exploratory Bash
  calls are excluded from the shared progress stream.
- `watchdog.py` at the same sha — `diagnose_health()`'s
  `STALLED-FLAT-PROGRESS` branch, `_deadlock_signature()` (the other
  consumer of the `"progress"` event type, left untouched).
- The pre-written record skeleton for this subject (issue #2135), filled
  in place per this session's instructions.

## Open findings

None.

canonical: `python3 -m pytest tests/test_watch_hardening.py -q -k test_tool_call_activity_without_commits_is_not_flat` (this session) — result: 1 passed.
canonical: `python3 -m pytest tests/test_watch_hardening.py -q -k test_true_stall_with_no_log_growth_still_flags` (this session) — result: 1 passed.
## Acceptance verification
- issue-2186-shape tool-call activity across several lease renewals does not trip STALLED-FLAT-PROGRESS — checked: pytest-test_tool_call_activity_without_commits_is_not_flat — result: pass: 1 passed, see canonical citations above
- a genuinely stalled session (no tool calls, no log growth) still trips flat-progress across K renewals — checked: pytest-test_true_stall_with_no_log_growth_still_flags — result: pass: 1 passed, see canonical citations above

## Executed acceptance evidence

canonical: `python3 -m pytest tests/test_watch_hardening.py -q` (this session, after the fix and the two new regression tests) — result:
```
..........................                                               [100%]
26 passed in 11.53s
```
0 failed, no SKIPPED lines. Hand-typed count (26) matches the pasted summary count exactly.

canonical: `python3 -m pytest tests/test_watch_hardening.py tests/test_checkpoint_mode.py -q` (this session, full sweep of every test file that references `lease_renew`/`_lease_progress_indicator`/`flat-progress`, per `grep -rln` over `tests/`) — result:
```
..............................................                           [100%]
46 passed in 377.40s (0:06:17)
```
0 failed, no SKIPPED lines. Hand-typed count (46) matches the pasted summary count exactly.

## Acceptance criteria (from the issue)

canonical: `python3 -m pytest tests/test_watch_hardening.py -q -k test_tool_call_activity_without_commits_is_not_flat` (this session) — result: 1 passed. Satisfies "a session actively issuing tool calls without committing does NOT produce STALLED-FLAT-PROGRESS — regression test simulating the issue-2186 shape (reading source across several lease renewals)": the test grows the transcript log every renewal (the issue-2186 shape) with `events.jsonl`/HEAD untouched, and asserts zero anomalies across `LEASE_FLAT_RENEWALS_K + 2` renewals.

canonical: `python3 -m pytest tests/test_watch_hardening.py -q -k test_true_stall_with_no_log_growth_still_flags` (this session) — result: 1 passed. Satisfies "a session that genuinely stalls (no tool calls, no log growth, lease renewing) IS still reported — regression guard": the test never writes the log across `LEASE_FLAT_RENEWALS_K + 1` renewals and asserts a `flat-progress` anomaly still fires.

- "Executed acceptance evidence in the record (#2137)" — see
  "Executed acceptance evidence" above.

The issue's own "Investigate" asks (pin down the indicator's definition;
sample sessions for a true-positive-rate estimate) are answered above via
the code reads cited with `canonical:` tags; a fresh live-session sample
was not re-run this turn — the issue's own 5+ cited observations (issues
#2156, #2164-#2166, #2185, #2186), each already checked by the issue's
author against process state and last tool call, served as the measured
baseline instead of re-deriving a new sample.

## What did not work

None — the fix landed as the first approach tried. See "Why" for the one
alternative weighed and set aside before writing any code (broadening the
shared `events.jsonl` progress stream instead of the lease indicator).

## Next steps

None — terminal.

canonical: `python3 -m pytest tests/test_watch_hardening.py tests/test_checkpoint_mode.py -q` (this session, same run cited under "Executed acceptance evidence" above) — result: 46 passed, 0 failed, 0 skipped, `loop_state: landed`, `verdict: pass`.

skill-verdict: other mounted skills: not triggered — this was a
localized, single-module function fix (widen one indicator's inputs) with
no coupling/cohesion threshold crossed, no GoF-pattern decision, no
performance-cliff data-structure choice, and no multi-module structural
design decision, so none of `implementation-complexity-coupling-management`,
`implementation-design-pattern-selection`,
`implementation-performance-data-structure-choice`, or
`implementation-blueprint` applied; none were invoked via the Skill tool.
