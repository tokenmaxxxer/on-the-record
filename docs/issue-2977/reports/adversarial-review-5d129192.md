---
issue: 2977
role: adversarial-review-5d129192
author: adversarial-review-5d129192
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 34d89a7f357774757d20e17e7b2204107aeb1ffe
loop_state: landed
type: code
breaking: false
verdict: pass
upstream:
  - path: on-the-record/monitors/poll-heartbeat.sh
    sha: 34d89a7f357774757d20e17e7b2204107aeb1ffe
---

# issue-2977 — adversarial-review-5d129192 record

## What was done

Independently verified PR #2985 (branch
`issue-2977/observability-signal-golden+test-derivation-f23c9fec`, head
`34d89a7f357774757d20e17e7b2204107aeb1ffe`) — issue #2977's bound on
lock-reclaim logging in `on-the-record/monitors/poll-heartbeat.sh`.
Fetched the PR head into an isolated `git worktree`
(`git fetch origin pull/2985/head:pr-2985-verify && git worktree add
/tmp/verify-pr-2985 pr-2985-verify`) and re-ran every issue-#2977
acceptance check myself inside it, without citing PR #2985's own pasted
results as evidence.

canonical: pytest transcripts produced by this session this turn inside
`/tmp/verify-pr-2985` (not read from PR #2985's own record):

- acceptance: `python3 -m pytest on-the-record/monitors/ -k reclaim_output_bounded -q` — result: `1 passed in 1.16s`
- acceptance: `python3 -m pytest on-the-record/monitors/ -k reclaim_suppression_reports_count -q` — result: `1 passed in 1.05s`
- acceptance: `python3 -m pytest on-the-record/monitors/ -k force_reclaim_never_suppressed -q` — result: `1 passed in 1.51s`
- acceptance: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q` (full file, regression check) — result: `40 passed in 24.34s`

All three of issue #2977's own acceptance checks reproduce green, and
the pre-existing test file (including this PR's own 3 new tests)
reproduces green with no regression.

canonical: `git diff main...pr-2985-verify -- on-the-record/monitors/poll-heartbeat.sh`, read in full this turn inside `/tmp/verify-pr-2985` — `must not` list audit against that diff:

- **"do not reduce output by removing the reclaim logging outright"** — not violated. `_reclaim_log_bounded` still calls `_poll_watchdog_log_append` on every collapse-window boundary and `_reclaim_log_flush` reports any remainder once the lock is acquired; no log call was deleted, only rate-limited.
- **"Do not suppress the max-age force-reclaim line under any rate bound"** — not violated. derived: `grep -n "_poll_watchdog_log_append\|_reclaim_log_bounded\|_reclaim_log_flush" on-the-record/monitors/poll-heartbeat.sh` — result: the max-age valve line (`poll-heartbeat.sh:384`, `... force-reclaimed independent of liveness check ...`) still calls `_poll_watchdog_log_append` directly and is never routed through `_reclaim_log_bounded`; only the `dead` branch (`:402`) and the `forming`/no-owner branch (`:410`) were rerouted.
- **"Do not make any watch-class monitor refusable, blockable, or disable-by-default"** — not violated. The two new env-var overrides (`POLL_HEARTBEAT_ALIVE_LOCK_RETRY_SLEEP`, `POLL_HEARTBEAT_RECLAIM_LOG_WINDOW`) default to the pre-existing values (`1`, `5`) when unset and only affect log-line cadence/test speed; no new flag disables the monitor, `ORCHESTRATE_OFF` (pre-existing) is untouched, and the diff touches only `poll-heartbeat.sh` and its own test file — derived: `git diff main...pr-2985-verify --stat` — result: 4 files changed (the script, its test file, the PR's own record, and its own deviation-log entry; no other repo file touched).
- **"Do not assume the flood is caused by the other watchdog noise defects"** — not violated. The fix is local to `poll-heartbeat.sh`'s own acquire loop and does not reference or depend on the other watchdog noise issues; the PR's own record explicitly treats the flood as caused by local lock contention (dead/forming branches sleeping 1s and retrying per-iteration inside a single wait), consistent with the issue's stated caution that the cross-defect link is unverified.

One design point checked and found sound rather than a defect: the
release-skipped path (`poll-heartbeat.sh:474`) and the max-age valve are
both left unbounded by design, not by oversight — I verified from the
code (not from the PR's own claim) that neither actually repeats
per-iteration inside a single lock wait the way the `dead`/`forming`
branches do. The max-age valve resets its own wait-start timestamp after
firing (`poll-heartbeat.sh:383`), capping its natural rate at roughly
once per `_alive_stamp_lock_max_age` (default 60s) per contending
process, not once per retry-sleep (1s); the release-skipped path fires
at most once per `_alive_stamp_write` invocation (once per poll tick),
not inside the retry loop at all. Neither is a per-iteration flood
source, so excluding both from the bound is consistent with the actual
mechanism, not an unexamined carve-out.

One residual limitation noted, not a `must not` violation: the bound is
a rate limiter (at most one collapsed line per
`POLL_HEARTBEAT_RECLAIM_LOG_WINDOW`, default 5s), not a hard total cap.
Under contention sustained for the full lifetime of a long-running
monitor session, this source still accumulates lines indefinitely —
derived: `1 / 5 = 0.2` (post-fix line rate at the default 5s window,
vs. `1 / 1 = 1.0` pre-fix line rate at the old 1s retry-sleep cadence)
— i.e. the line rate under sustained contention drops to 20% of the
pre-fix rate; it is not reduced to zero or to a fixed total. This is
very unlikely to be a real-world problem — accepting a hard total cap
instead would have meant silently dropping the count of events past the
cap, which is exactly the alternative the PR's own "Why" section
rejects and which would break acceptance check 2 (report the count) —
so the rate-limiter design is the more defensible tradeoff, but it does
mean the fix reduces rather than structurally eliminates the flood risk
under an unbounded-duration contention scenario. See Open finding 1.

## Why

The task asked me not to trust PR #2985's own claimed results and to
scrutinize specifically whether the introduced bound could itself drop
a signal that matters, given this repo's standing rule that leaving the
system unobserved is the worst outcome and watch-class machinery must
be unblockable. canonical: the four pytest transcripts already given
above, all produced by this session this turn by executing the
commands directly inside the freshly fetched `/tmp/verify-pr-2985`
worktree — none copied from PR #2985's own record — is what grounds
this record's own conclusion as an independent re-derivation, not a
citation of the PR's claim. Auditing the diff line-by-line against each
clause of the issue's `must not` list (rather than accepting the PR
record's own point-by-point "not violated" claims) is what surfaced
that the max-age valve and release-skip exclusions are mechanistically
justified (verified from the retry-loop structure itself) rather than
merely asserted, and is also what surfaced the rate-vs-cap
residual-limitation distinction that neither the issue nor the PR
record spells out explicitly.

## What did not work

None — every acceptance check reproduced on first execution in the
isolated worktree; no deviation from the assigned verification scope.

## Upstream basis

- `on-the-record/monitors/poll-heartbeat.sh` /
  `on-the-record/monitors/test_poll_heartbeat.py` at
  `34d89a7f357774757d20e17e7b2204107aeb1ffe` (PR #2985's head, branch
  `issue-2977/observability-signal-golden+test-derivation-f23c9fec`) —
  fetched via `git fetch origin pull/2985/head:pr-2985-verify` and
  `git worktree add /tmp/verify-pr-2985 pr-2985-verify` — sha:
  34d89a7f357774757d20e17e7b2204107aeb1ffe
- issue #2977 itself (`gh issue view 2977`), read directly for its
  acceptance checks and `must not` list — sha: not applicable (not a
  repo path)

## Open findings

1. **The bound is a rate limiter, not a hard total cap — sustained
   indefinite contention still accumulates output, at a reduced but
   nonzero rate.** (`on-the-record/monitors/poll-heartbeat.sh:182-193`,
   `_reclaim_log_bounded`, read in the isolated worktree this turn). At
   the default `POLL_HEARTBEAT_RECLAIM_LOG_WINDOW=5`, a contended lock
   that never clears produces at most one collapsed log line per 5
   seconds from this source, for as long as the contention persists —
   derived: `1 / 5 = 0.2` post-fix lines/sec vs. `1 / 1 = 1.0` pre-fix
   lines/sec (see the residual-limitation paragraph under "What was
   done" above). This is a large, real improvement over the pre-fix
   rate, and is the more defensible design given the issue's own
   requirement to keep reporting counts rather than silently dropping
   them past a cap — but it does not make the output from this source
   bounded in total under an unbounded-duration contention scenario,
   only bounded in rate. Low severity: no evidence this repo runs
   monitor sessions long enough, under contention severe enough, for
   this residual rate to itself cross the output limit — this is a
   theoretical residual noted for completeness, not a reproduced
   failure. Resolution path: if a future incident shows the 5s window
   still insufficient, the fix is a config change
   (`POLL_HEARTBEAT_RECLAIM_LOG_WINDOW`) or a genuine total-lifetime cap
   with an explicit "count skipped, further counts every reporting on
   the wire" design — not a re-litigation of this PR's core approach.
2. **The collapsed log line's message text reflects whichever event
   triggered the window boundary, not a breakdown by event type**
   (`poll-heartbeat.sh:182-193`). `dead` and `forming` reclaims share
   the same `_reclaim_collapsed_count`/`_reclaim_last_logged_ts` state,
   so a window containing a mix of both types logs one message (from
   whichever event crossed the boundary) annotated with the total count
   across both types, not a per-type breakdown. This satisfies the
   issue's literal acceptance ("reports that the events occurred and
   how many") but a reader of the log could not tell from one collapsed
   line whether the counted events were all `dead`, all `forming`, or a
   mix. Cosmetic, not a `must not` violation — noted for completeness.

## Next steps

acceptance: the full acceptance set re-run in the isolated
`/tmp/verify-pr-2985` worktree this turn — derived: the `acceptance:`
lines under What was done above (1 passed / 1 passed / 1 passed / 40
passed) — result: reproduced exactly, no outstanding check to re-run.
`loop_state: landed`. Neither open finding blocks landing; both are
noted for a possible future follow-up, not a required action before
this PR merges.

### skill-verdict

- skill-verdict: adversarial-review — applied: invoked; used its
  independent-evaluator framing to re-derive every acceptance result
  from a freshly fetched worktree rather than reading PR #2985's own
  pasted output, and to push the `must not` audit past "diff says X is
  unchanged" into "is X actually mechanistically excluded from the
  flood pattern," which surfaced the rate-vs-cap residual limitation in
  Open finding 1.
- skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; treated PR #2985's own "not violated" claims
  against the `must not` list as claims to re-check from the diff
  itself rather than facts already settled, and deliberately looked for
  a negative/edge case (sustained indefinite contention) beyond the
  happy-path re-run of the three acceptance checks.
- skill-verdict: work-in-english — applied: invoked; this record is
  authored in English throughout per the task's English-language
  framing.
- skill-verdict: verify-finding-record — not-applicable: that skill
  targets outcomes written to `docs/issue-<n>/reports/defect-verification.md`; this task's record lives at
  `docs/issue-2977/reports/adversarial-review-5d129192.md` under the
  adversarial-review skill's own record shape instead.
