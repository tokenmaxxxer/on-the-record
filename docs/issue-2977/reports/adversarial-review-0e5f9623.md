---
issue: 2977
role: adversarial-review-0e5f9623
author: adversarial-review-0e5f9623
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2985's own deliverable, author differs from subject's author
loop_state: landed
upstream:
  - path: on-the-record/monitors/poll-heartbeat.sh
    sha: 34d89a7f357774757d20e17e7b2204107aeb1ffe
  - path: on-the-record/monitors/test_poll_heartbeat.py
    sha: 34d89a7f357774757d20e17e7b2204107aeb1ffe
---

# issue-2977 — adversarial-review-0e5f9623 record

## What was done

Independently verified PR #2985 (`issue-2977/observability-signal-golden+test-derivation-f23c9fec`,
head `34d89a7f357774757d20e17e7b2204107aeb1ffe` — canonical: `gh pr view 2985
--json headRefName,headRefOid,baseRefName` output this turn), which bounds
the lock-reclaim logging in `on-the-record/monitors/poll-heartbeat.sh`'s
`_alive_stamp_write()` acquire loop. Per the task instruction not to trust
the PR's claimed results, its head was fetched into an isolated worktree
and every check below was re-run from there, not copied from the PR's own
record: `git fetch origin pull/2985/head:pr-2985-verify && git worktree
add /tmp/verify-2985 pr-2985-verify` — derived: `git -C /tmp/verify-2985
log --oneline -1` — result: `34d89a7f issue-2977: append deviation-log
entry for the freelunch inline-vs-delegate call` (confirms the worktree
sits at the PR head, not a stale checkout).

Acceptance checks, run in that isolated worktree:

acceptance: `python3 -m pytest on-the-record/monitors/ -k reclaim_output_bounded -q` — result:
```
1 passed in 1.09s
```

acceptance: `python3 -m pytest on-the-record/monitors/ -k reclaim_suppression_reports_count -q` — result:
```
1 passed in 0.99s
```

acceptance: `python3 -m pytest on-the-record/monitors/ -k force_reclaim_never_suppressed -q` — result:
```
1 passed in 1.14s
```

acceptance: `python3 -m pytest on-the-record/monitors/ -q` (full module, regression check) — result:
```
40 passed in 24.35s
```

Diff audit against the issue's must-not list — canonical: `gh pr diff
2985` output (505 lines, read in full this turn, not summarized from the
PR's own description):

1. **"do not reduce output by removing the reclaim logging outright"** —
   not violated. derived: `sed -n '182,200p'
   /tmp/verify-2985/on-the-record/monitors/poll-heartbeat.sh` — result:
   ```
   _reclaim_log_bounded() {
     local _msg="$1"
     local _window="${_reclaim_log_window:-5}"
     local _now
     _now="$(date +%s)"
     _reclaim_collapsed_count=$((_reclaim_collapsed_count + 1))
     if [ "${_reclaim_last_logged_ts}" -eq 0 ] || [ "$((_now - _reclaim_last_logged_ts))" -ge "${_window}" ]; then
       _poll_watchdog_log_append "$(printf '%s (bounded: %s reclaim event(s) counted in this window)' "${_msg}" "${_reclaim_collapsed_count}")"
       _reclaim_last_logged_ts="${_now}"
       _reclaim_collapsed_count=0
     fi
   }
   ```
   Both the `dead` and `forming` branches inside the acquire loop's retry
   `case` still call a logging path (`_reclaim_log_bounded`, which itself
   still calls `_poll_watchdog_log_append`) on every event; nothing was
   deleted, only routed through a collapsing wrapper.
2. **"do not suppress the max-age force-reclaim line under any rate
   bound"** — not violated. derived: `sed -n '378,386p'
   /tmp/verify-2985/on-the-record/monitors/poll-heartbeat.sh` — result:
   ```
       while ! ( set -o noclobber; printf '%s' "$$" >"${_lockfile}" ) 2>/dev/null; do
         _tries=$((_tries + 1))
         if [ "$(($(date +%s) - _wait_started))" -ge "${_alive_stamp_lock_max_age}" ]; then
           # silent-failure-audit (issue #2919): logged, not just broken --
           # this is a deliberate override of the liveness check, not a
           # normal reclaim, and must say so rather than read identically
           # to the `dead` branch below.
           _poll_watchdog_log_append "$(printf '[alive-stamp-lock] lockfile %s exceeded max wait %ss (owner pid %s) -- force-reclaimed independent of liveness check (zombie/reap-uncertainty safety valve, not a normal stale-lock reclaim)' "${_lockfile}" "${_alive_stamp_lock_max_age}" "$(cat "${_lockfile}" 2>/dev/null)")"
           rm -f "${_lockfile}" 2>/dev/null || true
   ```
   The valve's call site still calls `_poll_watchdog_log_append` directly,
   never `_reclaim_log_bounded` — confirmed by this excerpt and by the
   dedicated `t_force_reclaim_never_suppressed_issue_2977` test in the
   acceptance block above. Independent reasoning on top of that: the
   excerpt shows the valve fires only once
   `$(($(date +%s) - _wait_started))` reaches `_alive_stamp_lock_max_age`
   (default 60s per `local _alive_stamp_lock_max_age="${POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE:-60}"`,
   derived: `grep -n '_alive_stamp_lock_max_age=' /tmp/verify-2985/on-the-record/monitors/poll-heartbeat.sh` —
   result: `local _alive_stamp_lock_max_age="${POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE:-60}"`),
   and on firing it resets `_wait_started` and `continue`s the loop — so a
   single contending process cannot re-trigger it more than once per
   ~60s, an order of magnitude below the per-second dead/forming stream
   the issue reports. Leaving it unbounded therefore does not reopen the
   same flood.
3. **"do not make any watch-class monitor refusable, blockable, or
   disable-by-default"** — not violated. derived: `grep -n '^+'
   /tmp/pr2985.diff | grep -iE 'exit|disable|refus|block|ORCHESTRATE'` —
   result:
   ```
   367:+    assert r.returncode == 0, f"harness script must exit cleanly: {r.stderr}"
   ```
   The only hit across the full diff is a test-harness assertion in
   `test_poll_heartbeat.py`, not production code — no new exit path,
   disable flag, or gating condition was added to `poll-heartbeat.sh`
   itself.
4. **"do not assume the flood is caused by the other watchdog noise
   defects"** — not violated. The `_reclaim_log_bounded`/`_reclaim_log_flush`
   excerpt cited under point 1 above uses only local state
   (`_reclaim_collapsed_count`, `_reclaim_last_logged_ts`,
   `_reclaim_log_window`) scoped to a single `_alive_stamp_write`
   invocation; it reads, waits on, or references no other watchdog
   component. The fix holds regardless of whether other noise sources
   also contribute.

## Why

Verification approach followed the adversarial-review skill (invoked
this session: treat the maker's self-report as unverified, re-derive
independently) and the defect-verification-independence-from-upstream-
verdicts skill (invoked this session: re-derive from primary evidence in
a fresh worktree rather than citing a prior record's posted result
lines). Every acceptance-check result and diff-audit citation above was
produced by a command run this turn against the fetched PR head, not
copied from the PR's own record.

Per the independence skill's rule 2 (deliberately include an edge case,
not only happy-path checks), scrutiny went beyond re-running the three
named acceptance tests to look for a case the PR's own test suite does
not cover: what happens to a collapsed-but-not-yet-flushed reclaim count
if the process holding the wait loop dies before the window elapses or
the loop exits. That produced Open finding 1 below.

## What did not work

None.

## Upstream basis

Both `sha:` entries above are the PR #2985 head commit
`34d89a7f357774757d20e17e7b2204107aeb1ffe` — canonical: `gh pr view 2985
--json headRefOid` output this turn, cross-checked against `git -C
/tmp/verify-2985 log --oneline -1` (same sha) inside the isolated
worktree fetched via `git fetch origin pull/2985/head:pr-2985-verify`.
PR #2985's own record file lives on its own branch
(`issue-2977/observability-signal-golden+test-derivation-f23c9fec`) —
untracked on this record's own branch
(`issue-2977/adversarial-review-0e5f9623`), since the two branches have
not been merged into each other — canonical: `gh pr view 2985 --json
body` output this turn, not a local file read on this branch.

## Open findings

1. **Non-durable collapse window (non-blocking, does not violate any of
   the four must-nots)**: derived: `sed -n '292,296p'
   /tmp/verify-2985/on-the-record/monitors/poll-heartbeat.sh` — result:
   ```
       local _reclaim_log_window="${POLL_HEARTBEAT_RECLAIM_LOG_WINDOW:-5}"
       local _reclaim_collapsed_count=0
       local _reclaim_last_logged_ts=0
       local _alive_stamp_lock_retry_sleep="${POLL_HEARTBEAT_ALIVE_LOCK_RETRY_SLEEP:-1}"
   ```
   `_reclaim_collapsed_count` and `_reclaim_last_logged_ts` are `local`
   shell variables scoped to a single `_alive_stamp_write()` call. A
   dead/forming reclaim event folded into that counter is only made
   durable (written to the log) when either the collapse window elapses
   (default 5s) or the acquire loop exits normally and
   `_reclaim_log_flush` runs. If the process is killed (SIGKILL, or
   reaped by the host platform) while a nonzero count sits in-memory
   inside that window, the tally for those events is lost with no trace
   in the log — the same "silently dropped" failure mode the issue's
   second acceptance criterion exists to prevent, narrowed from "every
   event" to "events accumulated but not yet flushed within one window's
   width of a mid-wait kill." None of the three acceptance tests
   exercise this path — all three only exercise the loop's normal-exit
   flush (confirmed by reading `t_reclaim_output_bounded_issue_2977`,
   `t_reclaim_suppression_reports_count_issue_2977`, and
   `t_force_reclaim_never_suppressed_issue_2977` in full via `gh pr diff
   2985` this turn — none simulate a mid-loop kill). This does not
   violate any of the issue's four explicit must-nots (none mention
   process-kill durability), so it is not a blocking defect against this
   issue's stated acceptance criteria, but it narrows the "never silently
   drop a reclaim signal" property the issue argues for in its rationale.
   No resolution path filed; flagging for whoever next touches this
   monitor.
2. **Per-process bound, not a global bound (disclosed by the PR itself,
   not a hidden defect)**: derived: `sed -n '153,161p'
   /tmp/verify-2985/on-the-record/monitors/poll-heartbeat.sh` — result:
   ```
   # issue #2977: a contended alive-stamp-lock can drive the `dead`/`forming`
   # reclaim branches inside _alive_stamp_write's acquire loop into a
   # per-iteration log stream (up to ~1/s per contending process, more in
   # aggregate across concurrently contending processes) -- enough to push
   # the Monitor past its own output limit and silence every other signal it
   # would otherwise surface. This does NOT apply to the max-age
   # force-reclaim valve (the safety-valve line, logged directly via
   # _poll_watchdog_log_append, unchanged, never routed through here) or to
   # the release-skipped path -- neither repeats per-iteration inside a
   # single wait, so neither is the flood source this bounds.
   ```
   `_reclaim_collapsed_count` is local to each `_alive_stamp_write`
   invocation, so N processes concurrently contending on the same lock
   still each emit independently once per window — aggregate output can
   still grow with the number of contenders even though each contender's
   own stream is bounded. The PR's own comment above states this
   directly, and none of the issue's three acceptance checks exercise
   multi-process contention (all three drive a single sequence of calls
   from one process). Not a violation of anything on the must-not list —
   the issue's own report describes a single contended lock — but
   flagging since the repo's stated invariant is that observation must
   never go silent, and this is the scenario under which the fix's bound
   could, in principle, still be outrun.

## Next steps

None — loop_state is terminal (landed). Both open findings above are
non-blocking with respect to issue #2977's stated acceptance criteria
and must-not list.

Verdict: PR #2985 satisfies issue #2977 as written. acceptance: all
three named checks re-run independently in the isolated worktree at the
PR head, plus the full module — result:
```
reclaim_output_bounded: 1 passed in 1.09s
reclaim_suppression_reports_count: 1 passed in 0.99s
force_reclaim_never_suppressed: 1 passed in 1.14s
full module (on-the-record/monitors/): 40 passed in 24.35s
```
(the individual commands and per-check results are in the acceptance
blocks under "What was done" above; this block restates the outcome
summary with its own fenced evidence per this section's own citation
requirement). The diff audit under "What was done" found no violation of
any of the issue's four must-not clauses. Two non-blocking open findings
recorded above for follow-up; neither is required to close by this
issue's acceptance criteria or must-not list.

skill-verdict: adversarial-review — applied: invoked; used as the
governing protocol for treating PR #2985's own claimed results as
unverified until independently re-derived (isolated worktree, fresh
`pytest` runs, full diff read rather than summary), per the task's
explicit instruction not to trust the PR's claimed results.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; used rule 2
(include an edge case, not only happy-path checks) to look past the
three named acceptance tests for the process-kill-mid-window durability
gap (Open finding 1), and rule 3 (re-derive rather than cite) to re-run
every check against the fetched head — canonical: the four `acceptance:`
blocks under "What was done" above, each produced by this session's own
`pytest` invocation this turn — instead of citing the PR record's own
posted pass/fail lines.
other mounted skills: work-in-english not invoked as a Skill-tool call
this session (record and commit already written in English per its
stated guidance without needing to load the file); verify-finding-record
judged not-applicable — its target path/skeleton
(`docs/issue-<n>/reports/defect-verification.md`, reproduced/
not-reproduced outcome block) does not match this task's pre-written
adversarial-review record skeleton or its verification-of-a-fix framing.
