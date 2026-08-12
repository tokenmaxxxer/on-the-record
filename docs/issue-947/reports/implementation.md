---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/test_monitor_notice.py
  - docs/decisions/2026-08-12-monitor-cli-only-fallback.md
type: feature
breaking: false
canonical: acceptance: python3 -m pytest on-the-record/hooks/test_monitor_notice.py -v — result: UNMEASURED-with-reason: no acceptance command on record in docs/specs/acceptance-commands.md; full pytest transcript below
verdict: pass
loop_state: landed
---

canonical: acceptance: python3 -m pytest on-the-record/hooks/test_monitor_notice.py -v — result: UNMEASURED-with-reason: no acceptance command on record in docs/specs/acceptance-commands.md; full pytest transcript in Acceptance evidence section below
## Acceptance verification
- proposal's own stated acceptance test — checked: on-the-record/hooks/test_monitor_notice.py::test_stale_marker_from_earlier_session_does_not_suppress_notice — result: pass
- issue #947's own named acceptance gate — checked: gates/test_monitor_unavailable_notice.py — result: unverifiable: that exact path was never in this proposal's frozen write set (docs/issue-947/proposals/monitor-unavailable-notice.md files: lists on-the-record/hooks/test_monitor_notice.py, not that path); the approved proposal's own "How you'll know it worked" section substitutes test_monitor_notice.py as the acceptance-criteria test artifact, and that is what was built and run instead (see line above).

## Acceptance evidence

canonical: acceptance: python3 -m pytest on-the-record/hooks/test_monitor_notice.py -v — result: UNMEASURED-with-reason: no acceptance command on record in docs/specs/acceptance-commands.md; full pytest transcript below
```
$ python3 -m pytest on-the-record/hooks/test_monitor_notice.py -v
on-the-record/hooks/test_monitor_notice.py::test_first_observation_records_start_and_prints_no_notice PASSED [ 16%]
on-the-record/hooks/test_monitor_notice.py::test_no_notice_inside_grace_window PASSED [ 33%]
on-the-record/hooks/test_monitor_notice.py::test_notice_fires_once_past_grace_with_no_alive_marker PASSED [ 50%]
on-the-record/hooks/test_monitor_notice.py::test_no_notice_when_alive_marker_fresh_for_this_session PASSED [ 66%]
on-the-record/hooks/test_monitor_notice.py::test_stale_marker_from_earlier_session_does_not_suppress_notice PASSED [ 83%]
on-the-record/hooks/test_monitor_notice.py::test_session_ids_that_a_char_substitution_sanitizer_would_collide_stay_independent PASSED [100%]
6 passed in 7.46s
```

canonical: acceptance: python3 -m pytest on-the-record/hooks/ -q — result: UNMEASURED-with-reason: no acceptance command on record in docs/specs/acceptance-commands.md; full pytest transcript below
```
$ python3 -m pytest on-the-record/hooks/ -q
415 passed in 35.43s
```

## Summary of work

Building a workspace-scoped alive marker written by `poll-heartbeat.sh` before its sleep loop, and a `directive.sh` grace-window check that surfaces a one-time degradation notice when this session's own Monitor never wrote it.
(canonical: docs/issue-947/proposals/monitor-unavailable-notice.md, merged PR #1081 — `gh pr view 1081 --json state,mergedAt` state=MERGED)
Approved via the exact-string comment `APPROVE issue-947/implementation` (canonical: `gh issue view 947 --comments`, last comment body).

## Why

Northpole req#7: idle self-wake must not silently degrade with no operator-visible signal. Plugin Monitors are CLI-only per platform docs; IDE-extension sessions lose idle self-wake with no notice today.
(canonical: docs/specs/platform-capabilities.md lines 26-49, "Claude Code plugin Monitors" section)

## Upstream / basis

docs/issue-947/proposals/monitor-unavailable-notice.md (PR #1081, merged — canonical: `gh pr view 1081 --json state,mergedAt`)

## What was done

1. `on-the-record/monitors/poll-heartbeat.sh` — before the `sleep`/tick loop starts, `mkdir -p`/`touch`es a workspace-scoped alive marker at `.orchestrate-monitor-alive/alive` (relative to the Monitor's own CWD). Verified this turn with a bounded run (`POLL_HEARTBEAT_MAX_TICKS=1`) from a scratch temp dir: the marker file appeared.
2. `on-the-record/hooks/directive.sh` — new block, placed after the `ORCHESTRATE_OFF`/`CLAUDE_ROLE` guards and before checkout resolution: reads the UserPromptSubmit JSON payload's `session_id`, records this session's first-seen timestamp on first observation, and — once `MONITOR_NOTICE_GRACE_SECONDS` (default 600) has elapsed with no session-scoped "already notified" marker — prints the one-time degradation notice unless the alive marker exists with an mtime at or after this session's own start time. `session_id` is turned into a marker-file-safe token via a truncated SHA-256 hash (see resolved_findings below), not char substitution.
3. `on-the-record/hooks/test_monitor_notice.py` (new) — 6 subprocess-driven tests exercising the decision logic in isolation (`TOKENMAXXXER_CHECKOUT` points at this repo so no network clone is attempted): first-observation records start with no notice; no notice inside the grace window; notice fires exactly once past grace with no alive marker and never repeats; no notice when the alive marker is fresh for this session; a stale marker from an earlier session (mtime before this session's start) does NOT suppress the notice; and two distinct session_ids that a char-substitution sanitizer would have collided stay independently notified (regression test for the resolved finding below).
4. `docs/decisions/2026-08-12-monitor-cli-only-fallback.md` (new) — ADR recording the CLI-only constraint and the marker-based fallback, citing the platform doc.
5. This record.

## resolved_findings

- finder: warrant-hunter (before-landing dispatch)
  record: docs/issue-947/reports/implementation/2026-08-12-hunt-monitor-unavailable-notice-before-landing.md
  finding, per the "Observed"/"Expected" sections of the hunt record named above: the originally-implemented `safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)` char-substitution sanitizer collapses distinct session_ids that differ only in stripped characters (e.g. `"sess/a"` and `"sess?a"` both -> `sess_a`) onto the same marker-file token, so one real session's `-notified`/`-start` marker can silently answer for a different, unrelated, genuinely-monitor-unavailable session.
  resolution: `directive.sh`'s heredoc now derives the marker token via `hashlib.sha256(session_id...).hexdigest()[:24]` instead of char substitution — collision-free regardless of the session_id's characters. Added `test_session_ids_that_a_char_substitution_sanitizer_would_collide_stay_independent` to `test_monitor_notice.py`, reproducing the hunter's exact `"sess/a"`/`"sess?a"` pair and asserting both sessions get their own independent notice.
  canonical: acceptance: python3 -m pytest on-the-record/hooks/test_monitor_notice.py -v — result: UNMEASURED-with-reason: no acceptance command on record in docs/specs/acceptance-commands.md; full pytest transcript below
  status: resolved, re-cleared this session; see Acceptance evidence section above for the full pytest transcript.

## Rationale for deviations

The proposal's step 1 says the alive marker is "keyed by `session_id`, available the same way `session-role-bind.sh` reads it from its hook payload." `session-role-bind.sh` reads `session_id` from a `SessionStart` hook's JSON stdin payload (canonical: on-the-record/hooks/session-role-bind.sh lines 27-51). `poll-heartbeat.sh` is a plugin **Monitor**, not a hook invocation — `on-the-record/monitors/monitors.json` declares it as a bare `command` (canonical: on-the-record/monitors/monitors.json lines 1-7), with no documented stdin JSON contract (canonical: docs/specs/platform-capabilities.md lines 26-49, no payload shape stated), and blocking on a `cat` read inside a long-lived background loop risks hanging the Monitor forever if no payload is ever piped. Reading stdin in `poll-heartbeat.sh` was therefore rejected as unsafe to implement against an unverified contract.

Implemented instead: the alive marker (`.orchestrate-monitor-alive/alive`) is workspace-scoped only (no session token), written by `poll-heartbeat.sh` via a plain `touch`, and staleness across sessions is resolved on the `directive.sh` side by mtime comparison — `directive.sh` *does* reliably receive `session_id` (UserPromptSubmit hook JSON stdin, the same contract other on-the-record hooks already read from — canonical: on-the-record/hooks/retry-loop-bound.sh lines 53-86, `payload.get("session_id")`) and uses it to record this session's own first-seen timestamp (`.orchestrate-monitor-alive/.session-<hash>-start`). The alive marker only counts as "this session's monitor" if its mtime is at or after that session's own recorded start time — an older mtime cannot belong to a monitor that started after this session began, which is the same "no stale cross-session evidence" guarantee the warrant-hunt finding required.
(canonical: docs/issue-947/reports/implementation/2026-08-12-hunt-monitor-unavailable-notice.md)

Also, a separate `monitor_notice.py` helper file was considered to keep the Python logic out of a heredoc, but the proposal's frozen write set names no such file — the decision logic is instead inlined in `directive.sh` via a `python3 - <<'PY'` heredoc, matching the existing pattern already used in `retry-loop-bound.sh`, so no path outside the frozen write set was touched.

## What did not work

The alive-marker token was first implemented via `re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)` char substitution (mirroring `session-role-bind.sh`'s existing convention, canonical: on-the-record/hooks/session-role-bind.sh line 55). The before-landing warrant hunt found this collapses distinct session_ids onto the same token, causing silent cross-session notice suppression (canonical: docs/issue-947/reports/implementation/2026-08-12-hunt-monitor-unavailable-notice-before-landing.md). Replaced with a SHA-256-hash-derived token before landing — see resolved_findings above.

## Open findings

None outstanding — the one finding raised (warrant-hunter, before-landing) is resolved per resolved_findings above.

## Next steps

Nothing outstanding on this build; next action is opening the delivery PR carrying `Closes #947`.

## Resolution path

Not applicable — no open findings remain against this build.
