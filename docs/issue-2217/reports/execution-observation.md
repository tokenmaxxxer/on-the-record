---
issue: 2217
role: execution-observation
loop_state: handed-off
upstream:
  - path: af8ddad82138d5a34c1c9adf7be2351ba99d6cc2
    sha: af8ddad82138d5a34c1c9adf7be2351ba99d6cc2
subject: af8ddad82138d5a34c1c9adf7be2351ba99d6cc2
test: python3 -m pytest tests/test_watchdog_local_signals.py -v
result: passed
assertedBy: execution-observation session, issue-2217, this turn
---

# issue-2217 — execution-observation record

## What was done

Independent execution-observation of PR #2234 (branch
issue-2217/implementation into main, head
af8ddad82138d5a34c1c9adf7be2351ba99d6cc2, state OPEN, MERGEABLE per
`gh pr view 2234 --json headRefOid,state,mergeable` this session).
This session re-ran the issue's own acceptance criteria itself, then
read the PR's own record only to confirm which gate and which log
filenames were the right targets.

canonical: gh pr view 2234 --json headRefOid,state,mergeable (this session)
```
{"baseRefName":"main","headRefOid":"af8ddad82138d5a34c1c9adf7be2351ba99d6cc2","mergeable":"MERGEABLE","state":"OPEN"}
```

Method: `git fetch origin pull/2234/head:pr-2234` then `git checkout
pr-2234 -- events.py spawn.py watchdog.py
tests/test_watchdog_local_signals.py` inside this session's own working
tree, ran every check directly, then `git checkout HEAD -- events.py
spawn.py watchdog.py tests/test_watchdog_local_signals.py` restored this
branch's tree before this record was written.

**1) The issue's named gate, re-run by this session:**

canonical: python3 -m pytest tests/test_watchdog_local_signals.py -v (this session, PR branch code checked out into this session's own tree)
```
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_genuine_agent_run_in_background_tool_use_still_trips_signal PASSED
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_fresh_log_no_anomalies_no_gh PASSED
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_empty_workspace_set_yields_empty_verdicts_not_error PASSED
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_own_injected_warning_in_assistant_text_does_not_trigger PASSED
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_stale_log_signals_silence_no_gh PASSED
tests/test_watchdog_local_signals.py::TestGhOnlyForPrState::test_dead_entry_with_pr_index_makes_zero_gh_calls PASSED
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_count_structural_delegations_ignores_non_assistant_types PASSED
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_injected_directive_text_alone_yields_zero_anomalies PASSED
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_count_structural_delegations_counts_tool_use_run_in_background PASSED
tests/test_watchdog_local_signals.py::TestSignalCoverageNoRegression::test_every_inventoried_signal_type_still_derivable PASSED
tests/test_watchdog_local_signals.py::TestGhOnlyForPrState::test_pr_state_from_index_matches_open_or_merged_semantics PASSED
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_zero_commit_aged_session_signals_no_gh PASSED
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_dead_watcher_pid_signals_no_gh PASSED
tests/test_watchdog_local_signals.py::TestGhOnlyForPrState::test_dead_entry_without_pr_index_makes_one_gh_call PASSED
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_genuine_bash_run_in_background_tool_use_still_trips_signal PASSED
tests/test_watchdog_local_signals.py::TestSignalCoverageNoRegression::test_watcher_missing_signal_derivable PASSED
16 passed in 1.29s
```
canonical: python3 -m pytest tests/test_watchdog_local_signals.py -v (same run quoted immediately above, this session)
derived: python3 -m pytest tests/test_watchdog_local_signals.py -v
Every one of the sixteen cases in that output reports PASSED
individually, no FAILED line present — this session's own from-scratch
re-run, in a clean process, of the exact command the PR's own record
names as its gate.

**2) Adjacent watchdog-file regression sweep, re-run by this session:**

canonical: python3 -m pytest tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py tests/test_watchdog_heartbeat_noise.py tests/test_poll_watchdog_log.py -q (this session, same PR branch checkout)
derived: python3 -m pytest tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py tests/test_watchdog_heartbeat_noise.py tests/test_poll_watchdog_log.py -q
```
..................................
34 passed in 1.16s
```
No failing dot in that line, no FAILED/ERROR line anywhere in the
output — this session's own re-run of the adjacent-file sweep.

**3) `_DELEGATION_RE` removal — own grep, not part of the PR's own pasted evidence:**

canonical: grep -rn "_DELEGATION_RE" --include="*.py" . (this session, PR branch checkout)
derived: grep -rn "_DELEGATION_RE" --include="*.py" .
```
(no output)
```
Zero matches anywhere in the tree for the retired regex name.

**4) Empty-state acceptance criterion, re-derived through the full production entry point rather than only the PR's own dedicated unit test:**

canonical: python3 script writing one `{"type":"system",...,"text": spawn._COMPLETION_PROSE}` JSONL line to a temp file and calling `spawn.watchdog_check_one("k", entry, state={})` (this session, PR branch checkout, own temp dir, own entry dict)
```
empty-state anomalies: []
```
An empty list — a log holding only the injected directive and nothing
else, driven through `watchdog_check_one` itself.

**5) Executed-live before/after re-run against the seven real logs the issue names — this session's own independently-written comparison script (same seven log paths the issue and the PR record both cite, script logic written fresh this session, with an added `real_calls` column not present in the PR's own script):**

canonical: python3 script comparing `re.compile(r"run_in_background|백그라운드|delegate|background worker", re.IGNORECASE)` against `spawn._count_structural_delegations`, plus a hand-written `real_run_in_background_calls()` walking each assistant `tool_use` block directly (this session, run against the real files under /home/jwjung/.tokenmaxxxer/work/)
```
log                                                                    OLD_RE  NEW     real_calls
on-the-record-issue-2204-implementation.session.20260824T222535.4130680.log True    True    ['Bash']
on-the-record-issue-2204-execution-observation.session.20260824T232057.1632735.log True    False   []
on-the-record-issue-2204-conformance-review.session.20260824T232215.1632735.log True    True    ['Agent']
on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log True    False   []
on-the-record-issue-2210-implementation.session.20260824T232302.1650855.log True    False   []
on-the-record-issue-2214-implementation.session.20260824T233348.2080038.log True    False   []
on-the-record-issue-2215-implementation.session.20260824T233302.2032422.log True    False   []
```
derived: python3 -c "seven-log OLD_RE vs spawn._count_structural_delegations comparison, output pasted verbatim above"
Reading straight down the table above: the `OLD_RE` column is `True` on
all seven rows, the `NEW` column is `True` on two rows and `False` on
five, and the `real_calls` column on those same two `True` rows names a
`Bash` call and an `Agent` call respectively — each with
`input.run_in_background` truthy. This is the same shape the PR record
claims for these seven files: every one a false positive on the old
regex, five of the seven correctly clearing under the new detector, and
the two that stay flagged tracing to an actual `run_in_background: true`
tool call rather than to vocabulary in an assistant text block.

All temp artifacts (scratch scripts, temp dirs) were removed by this
session after use;

canonical: git status --porcelain=v1 -b (this session, own repo, re-checked after `git checkout HEAD -- events.py spawn.py watchdog.py tests/test_watchdog_local_signals.py` restored the PR checkout)
```
## issue-2217/execution-observation...origin/main
 M .orchestrate-hook-fires.log
?? .on-the-record/directive/
?? docs/issue-2217/
```
Unchanged from this session's own tree at the point verification work
began — the PR-branch checkout used for items 1-5 above left no trace on
this branch.

## Why

The issue's acceptance text specifically demands executed-live evidence
against named real logs, not a description of the fix. Re-running the
exact same comparison against the exact same files from a clean process
— plus checks the PR's own script did not run: the full
`watchdog_check_one` pipeline for the empty-state criterion, a
`real_calls` breakdown naming which tool tripped signal 2 on each of the
two still-flagged logs, and a repo-wide grep for the retired regex — is
what this role adds over trusting the PR's own pasted transcript. The
PR branch was checked out directly into this session's own tree (via the
fetched `pull/2234/head` ref) rather than a separate worktree, since no
concurrent edits were needed; the unchanged `git status` above already
shows the checkout was fully reverted before this record was authored.

## Upstream basis

- PR #2234, commit af8ddad82138d5a34c1c9adf7be2351ba99d6cc2 (branch
  issue-2217/implementation), fetched this session via
  `git fetch origin pull/2234/head:pr-2234` and read directly.
- The implementation record at that same commit (read via
  `git show pr-2234:docs/issue-2217/reports/implementation.md`, this
  session, since that path is not present in this branch's own tree
  until the PR merges) — read after this session's own re-execution,
  only to line up the gate command and the seven log filenames.
- Issue #2217 itself (`gh issue view 2217`, this session) — source of
  the acceptance gate, the empty-state criterion, and the five named
  sessions (seven logs) to re-run the detector against.

## Open findings

none

## Next steps

Not applicable — `loop_state: handed-off` is this record kind's
terminal state (per `roles/execution-observation.json`'s
`record_fields.loop_state.terminal`); every claim in the PR record
checked above by this session reproduced identically against the real
files, with nothing left to hand back.

resolution path: not applicable — zero open findings, nothing pending.
