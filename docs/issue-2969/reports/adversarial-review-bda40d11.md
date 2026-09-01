---
issue: 2969
role: adversarial-review-bda40d11
author: adversarial-review-bda40d11
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 46864b697e40dab9d19a16d8e1296a0a4eab8f8d
loop_state: landed
type: fix
breaking: false
verdict: pass
upstream:
  - path: lifecycle.py
    sha: 46864b697e40dab9d19a16d8e1296a0a4eab8f8d
  - path: on-the-record/monitors/poll_heartbeat_delta.py
    sha: 46864b697e40dab9d19a16d8e1296a0a4eab8f8d
  - path: on-the-record/monitors/test_poll_heartbeat.py
    sha: 46864b697e40dab9d19a16d8e1296a0a4eab8f8d
  # docs/issue-2969/reports/silent-failure-audit-daadb0ad.md is untracked
  # on this branch (issue-2969/adversarial-review-bda40d11) -- it lives on
  # branch issue-2969/silent-failure-audit-daadb0ad, not yet merged to main
  - path: docs/issue-2969/reports/silent-failure-audit-daadb0ad.md
    sha: fb309f65f29e0ff6593ca9532ccec24cba06c9bb
---

# issue-2969 — adversarial-review-bda40d11 record

## What was done

Independently re-verified PR #3005 / commit `46864b697e40dab9d19a16d8e1296a0a4eab8f8d`
(pushed directly onto PR #2990's branch,
`issue-2969/silent-failure-audit+test-derivation-bb5cc534`) — the fix round
that claims to resolve the two `verdict: fail` findings raised by two
earlier independent-verification PRs (#2999, head `fff25c97799babc954d8e261fe3536ebdaa29a84`;
#3000, head `1c5e3e0ab68979355ec5e13b6c11790240d122a5`). Did not trust PR
#3005's own pasted claims; fetched the fix commit into an isolated
`git worktree` (`/tmp/verify-2969`, since removed) and re-derived everything
from code and re-run tests myself.

**Finding 1 (regression) — genuinely fixed, and the fixture gap that let it
escape is genuinely closed.**

canonical: `git show 46864b69 -- on-the-record/monitors/poll_heartbeat_delta.py`
— the stale `if state_token == "HEALTHY":` comparison is replaced with
`if state_token is not None and state_token.startswith(HEALTHY_STATE_PREFIX):`
(`HEALTHY_STATE_PREFIX = "HEALTHY-"`), and the changed-detection now compares
`prev_state != state_token` (the two new full state names) instead of the
old `prev_state != "HEALTHY"` — so a transition *between*
`HEALTHY-CONFIRMED` and `HEALTHY-UNCONFIRMED` is itself treated as a
real, notify-worthy change, matching the added comment's stated intent.
canonical: `watchdog.py` on the fix commit's tree — `diagnose_health()`
still returns exactly `HEALTHY-CONFIRMED`/`HEALTHY-UNCONFIRMED` (lines
595/598), confirming the prefix match targets the real production state
names, not a stale assumption.

acceptance: `python3 -m pytest tests/ -k health_verdict_confirmed_vs_unconfirmed -q` (re-run live in the isolated worktree at `46864b69`) — result:
```
6 passed in 0.87s
```
acceptance: `python3 -m pytest tests/ -k liveness_pid_reuse -q` — result:
```
6 passed in 0.85s
```
acceptance: `python3 -m pytest tests/ -k flapping_verdict -q` — result:
```
7 passed in 0.81s
```
acceptance: `python3 -m pytest tests/ -k destructive_action_requires_consecutive -q` — result:
```
4 passed in 0.86s
```
acceptance: `python3 on-the-record/monitors/test_poll_heartbeat.py` — result:
```
37/37 passed
```
acceptance: `python3 -m pytest test/ tests/ -q -m "not slow"` — result:
```
16 failed, 638 passed, 3 xfailed in 31.57s
```
The 16 failures and their names match the pre-existing, unrelated set PR
#2990/#3005's own records already documented (`test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`, `test_spawn_skill_judge_haiku_timeout_overlap.py`,
`test_spawn_gate_wiring.py`, `test_local_dependency_env.py`,
`test_convention_equivalence.py`); the `638 passed` count matches exactly.
Zero new failures from this fix.

Checked the specific claim that the fixture no longer fakes the state:
`_healthy_state_token()` (added in `test_poll_heartbeat.py`) imports
`spawn`/`watchdog` and calls the real `watchdog.diagnose_health()` for the
token — canonical: `git show 46864b69 -- on-the-record/monitors/test_poll_heartbeat.py`,
read directly, not trusted from the docstring. Then verified this actually
closes the gap that let the original regression escape, rather than just
moving the same hardcoding one level down: reverted only
`poll_heartbeat_delta.py`'s fix (`git apply -R` on that file's diff alone)
while leaving the fixed fixture in place —

derived: `python3 on-the-record/monitors/test_poll_heartbeat.py` (production
fix reverted via `git apply -R`, fixture left as fixed) — result:
```
FAIL t_healthy_poll_report_with_drifting_detail_suppresses_after_first_tick
FAIL t_healthy_to_stalled_transition_still_notifies
FAIL t_healthy_workspace_change_still_notifies_despite_activity_drift
FAIL t_heartbeat_bound_not_yet_crossed_stays_silent_for_tracked_roster
FAIL t_heartbeat_bound_with_tracked_roster_emits_monitor_heartbeat
5 failed
```
derived: `git checkout -- on-the-record/monitors/poll_heartbeat_delta.py && python3 on-the-record/monitors/test_poll_heartbeat.py` (fix restored) — result:
```
37/37 passed
```
This is the decisive check the task asked for: the fixture, as fixed,
would have caught the exact regression that escaped before (the old
hardcoded-`"HEALTHY"` fixture agreed with the stale comparison and both
silently disagreed with reality). A future rename/split of `HEALTHY-*`
will now break this fixture loudly (via the real `diagnose_health()`
call) instead of staying silently pinned to today's names.

Residual, minor gap (not the regression at issue, noted for completeness):
canonical: `watchdog.py` lines 595/598 on the fix commit's tree —
`_healthy_report()`'s hardcoded detail text (`"최근 로그 성장, RUNNING"`)
does not match either real `HEALTHY-CONFIRMED` detail
(`"로그 성장 확인됨, RUNNING"`) or real `HEALTHY-UNCONFIRMED` detail
(`"이상 신호 없음(로그 성장은 확인되지 않음), RUNNING"`) — only the *state
token* was switched to the real function, not the message text. This does
not affect any of the four required acceptance checks or the finding-1
regression test above (the suppression logic keys off the state-token
prefix and the activity-clause strip, not the detail text), so it is not
a fail condition here, but it is a smaller instance of the same "fixture
text drifts from the real function" risk the fix was written to close for
the state name specifically.

**Finding 2 (false completeness claim about `_self_trigger_respawn()`) —
the record correction is accurate, and the argument for leaving the path
ungated holds up on the code, on all three legs.**

Read `lifecycle.py`'s `_self_trigger_respawn()` (lines 563-592 on the fix
commit) and its caller in `spawn.py` directly, not just the new docstring
paragraph, to adjudicate independently rather than take the documented
reasoning at face value.

1. *"Nothing alive to misjudge — the process exit was already confirmed
   via `proc.wait()`."* canonical: `spawn.py:4905-4906`:
   ```
   rc = proc.wait()
   roster_remove(roster_key)
   ```
   and `spawn.py:5079` (much later in the same function, same process),
   where `_self_trigger_respawn(...)` is called. `proc` is the direct
   `claude` child subprocess `_spawn_one()` launched and is waiting on —
   `proc.wait()` is a blocking kernel-level confirmation of that specific
   child's termination, not a liveness heuristic subject to pid-reuse or
   `/proc`-absence degradation (the class of risk `RESPAWN_CONSECUTIVE_CONFIRMATIONS`
   exists to guard against, per `_auto_respawn_check()`'s own comment at
   `lifecycle.py:513-520`, which reads a `session_end_verdict()` heuristic
   on an *externally observed*, possibly-stale roster entry). This leg is
   true: there is no "is it still alive" question left open at this call
   site, because it is the same process directly confirming its own
   child's exit, not a separate watcher inferring liveness from the
   outside.
2. *"A second confirmation is structurally impossible because
   `roster_remove()` already deleted the entry."* canonical:
   `spawn.py:4906` runs `roster_remove(roster_key)` immediately after
   `proc.wait()` returns, strictly before `_self_trigger_respawn()` is
   reached at line 5079. canonical: `lifecycle.py`'s `_auto_respawn_check()`
   (lines 489-558) is only ever invoked per still-present roster entry
   (its `crash_confirms` counter at `state[key]` only advances across
   watchdog ticks that can still see the entry); once `roster_remove()`
   deletes the key, no subsequent tick can iterate over it to accumulate
   a second `"crashed"` observation. This leg is true as a direct
   consequence of the removal ordering, not an assertion — verified by
   reading the call order, not by trusting the docstring's claim of it.
3. *"Other safeguards already bound this path (attempt-cap, claim lock)."*
   canonical: `lifecycle.py:364-485` (`_respawn_or_cap()`) — both
   `_auto_respawn_check()`'s watchdog-observed path and
   `_self_trigger_respawn()`'s self-triggered path call this same shared
   function with the same `key`, so `RESPAWN_MAX_ATTEMPTS`/
   `RESPAWN_ABSOLUTE_MAX` (checked at lines 444/447, against `state[key]`)
   and the atomic `O_CREAT|O_EXCL` claim file (lines 452-456) apply
   identically regardless of which path called it — confirmed by reading
   the shared function body, not by trusting the comment that says so.
   True.

Given all three legs check out on direct code inspection, the answer to
"does an ungated path here still leave any way for a live session to be
killed on a single observation" is no: this path never terminates a
running process at all (it only respawns-or-caps *after* `proc.wait()`
has already returned for the process being tracked), so there is no
process here that could be mistakenly killed while still alive. The
argument in the fix commit is sound engineering reasoning about a
genuinely different risk shape than the one `RESPAWN_CONSECUTIVE_CONFIRMATIONS`
was built for — not rationalization for skipping the work. Forcing the
same gate onto this path, as the corrected docstring itself notes, would
be a regression: `crash_confirms` could never reach 2 here (leg 2), so
gating this path would permanently disable the issue #247/#675
self-trigger-respawn feature rather than add a real safety margin.

canonical: `git show fb309f65:docs/issue-2969/reports/silent-failure-audit-daadb0ad.md`
(untracked on this branch, read from the commit object of branch
`issue-2969/silent-failure-audit-daadb0ad`) — the record correction
states plainly that PR #2990's "`_auto_respawn_check()` is the only
place" claim was wrong, cites `lifecycle._self_trigger_respawn()` as the
real second path, and documents the decision not to gate it rather than
silently re-asserting completeness. That correction matches what direct
code inspection above independently confirms.

## Why

Verified from the code and by running tests myself rather than by reading
the fix commit's own commit message or PR #3005's own claims, per the
task's explicit instruction not to trust the resolution claim. For
finding 1, the decisive test was reproducing the original regression
against the fixed fixture, per the two `derived:` command/result pairs
under "What was done" above (fix reverted -> failures reappear; fix
restored -> failures gone). This confirms the fixture change is a real
detection improvement, not cosmetic — matching the task's framing that a
fixture which still fakes the state means the next rename would slip
through again. For finding 2, each of the three argued legs was checked
against the actual call graph and call-order in `spawn.py`/`lifecycle.py`
independently (citations under "What was done" above), rather than
accepting the docstring's self-description of "structurally impossible."

## What did not work

None — every acceptance check and the regression-reproduction check
passed or reproduced on first execution (see the `acceptance:`/`derived:`
command-and-result pairs under "What was done" above); no scope-exceeded
stop, no alternative-swap, nothing written and then undone.

## Upstream basis

- `lifecycle.py`, `on-the-record/monitors/poll_heartbeat_delta.py`,
  `on-the-record/monitors/test_poll_heartbeat.py` at commit
  `46864b697e40dab9d19a16d8e1296a0a4eab8f8d` (PR #3005's fix, pushed to
  PR #2990's branch `issue-2969/silent-failure-audit+test-derivation-bb5cc534`)
  — sha: `46864b697e40dab9d19a16d8e1296a0a4eab8f8d`
- `docs/issue-2969/reports/silent-failure-audit-daadb0ad.md` — untracked
  on this session's own tree; lives on branch
  `issue-2969/silent-failure-audit-daadb0ad`. canonical:
  `git merge-base --is-ancestor fb309f65f29e0ff6593ca9532ccec24cba06c9bb main`
  — result: exit non-zero (not an ancestor, confirming this branch has
  not landed on main). PR #3005's own delivery record — sha:
  `fb309f65f29e0ff6593ca9532ccec24cba06c9bb`
- PR #2999 (`issue-2969/adversarial-review-4b49fcf9`,
  `fff25c97799babc954d8e261fe3536ebdaa29a84`) and PR #3000
  (`issue-2969/adversarial-review-07fbd75c`,
  `1c5e3e0ab68979355ec5e13b6c11790240d122a5`) — the two prior independent
  `verdict: fail` verifications this fix round claims to resolve; read for
  their findings but not cited as evidence for any result above — sha:
  `fff25c97799babc954d8e261fe3536ebdaa29a84` / `1c5e3e0ab68979355ec5e13b6c11790240d122a5`

## Open findings

None outstanding against the scope of this re-verification. One residual,
non-blocking observation noted above under Finding 1: `_healthy_report()`'s
hardcoded detail text in `test_poll_heartbeat.py` still doesn't match
either real `HEALTHY-*` detail string, only the state token was switched
to derive from the real function. This does not affect any required
acceptance check or the finding-1 regression test and is not being raised
as a fail condition.

## Next steps

None — `loop_state: landed`. acceptance: `python3 -m pytest tests/ -k "health_verdict_confirmed_vs_unconfirmed or liveness_pid_reuse or flapping_verdict or destructive_action_requires_consecutive" -q` (fresh combined re-run, executed for this section, on commit `46864b69`) — result:
```
23 passed in 0.90s
```
Both prior `verdict: fail` findings against PR #2990 are confirmed
resolved by commit `46864b69`: finding 1 by a real code fix plus a
fixture change verified (by the reversion test under "What was done"
above) to actually close the detection gap; finding 2 by a record
correction backed by an engineering argument that holds up under
independent adjudication of all three of its claims (also under "What
was done" above).

skill-verdict: adversarial-review — applied: invoked; structurally
independent re-verification of a fix round's claims (fetched the fix
commit into an isolated worktree, re-derived every acceptance result and
the regression-reproduction check myself, and adjudicated the
self-trigger-respawn argument against the actual call graph rather than
accepting the docstring's self-description) rather than trusting PR
#3005's or the fix commit's own claims.
other mounted skills: not triggered — work-in-english is directive-only
(enforced by the core hook layer); the remaining task-configured skills
(verify-finding-record, implementation-audit, test-depth-audit,
technical-feasibility-build-vs-buy) target record formats, requirement
audits, test-suite classification, and build-vs-buy comparisons that do
not fit this fix-round re-verification.
