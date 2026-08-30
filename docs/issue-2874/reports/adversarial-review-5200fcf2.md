---
issue: 2874
role: adversarial-review-5200fcf2
author: adversarial-review-5200fcf2
skills: adversarial-review, defect-verification-independence-from-upstream-verdicts, work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2882 (issue-2874/silent-failure-audit-e7b244cd)
code_under_review: board.py, spawn.py, lifecycle.py, watchdog.py, test/test_reconcile_crash_verdict_race.py (untracked on this branch; PR #2882 still open -- see Upstream basis)
type: verification-record
breaking: false
verdict: PASS — the fix, the caller-completeness claim, and the observability line all independently reproduced against real processes in both directions (completion not respawned, genuine crash still respawned); the PR's own disclosed residual gap (wrapper_pid has no process-identity check) independently reproduced live with a genuinely unrelated process, not merely re-cited; no regression, no overhead increase, no retired-role-axis return
loop_state: complete
upstream:
  - path: docs/issue-2874/reports/silent-failure-audit-e7b244cd.md
    sha: 0fc4f21a9e5a77f226a93c649b8f3104ce12834c
---

# issue-2874 — adversarial-review-5200fcf2 record

## What was done

canonical: `gh pr view 2882 --repo tokenmaxxxer/on-the-record --json title,body,files,commits,headRefName,baseRefName` — read this session, before starting; result shows PR is `OPEN`, base `main`, head `issue-2874/silent-failure-audit-e7b244cd`, touching `board.py`, `spawn.py`, `lifecycle.py`, `watchdog.py`, and adding a new regression test module (untracked on this branch — full path and confirmation in "Upstream basis" below), plus the builder's own `docs/issue-2874/` record files.

Independent verification of PR #2882's fix for the `reconcile()`/`poll-report` disagreement (issue #2874): `session_end_verdict()` only checked the claude subprocess's own pid, misreading the post-exit tail of `_spawn_one()` (push/gate/classify/`ledger_write`, before `session-end` is appended) as `crashed`. The fix threads `wrapper_pid` into `session_end_verdict()` and its three crash-consequential callers, plus a `[reconcile-poll-disagreement]` line in `roster_watchdog()`.

canonical: `gh pr view 2882 --repo tokenmaxxxer/on-the-record --json state,mergeable,mergeStateStatus` — result: `{"mergeStateStatus":"UNKNOWN","mergeable":"UNKNOWN","state":"OPEN"}`, read this session — PR #2882 is still open, not merged to `main`, so every PR-only path cited anywhere in this record is untracked on this review branch (`issue-2874/adversarial-review-5200fcf2`) and was read via `git show pr-2882:<path>` or a scratch worktree, never assumed present in this branch's own working tree. Separately, `gates/retirement_count.py` (the task brief's suggested tool, see item 11 below) is confirmed untracked on every branch this review touches, including `origin/main` and `pr-2882` — the checker itself has not landed anywhere yet.

Checked out the PR head (`git worktree add /tmp/pr2882-verify pr-2882`, commit `0fc4f21a`, fetched via `git fetch origin pull/2882/head:pr-2882`) and `origin/main` (`git worktree add /tmp/main-verify origin/main`, commit `5fe6c38e`) into separate scratch worktrees — both removed with `git worktree remove` at the end of this session — and re-derived every claim from scratch, per `defect-verification-independence-from-upstream-verdicts`: re-run the PR's own tests, then construct independent real-process scenarios the PR's tests do not cover.

**1. PR's own regression suite, re-run independently.**

checked: `cd /tmp/pr2882-verify && python3 -m pytest -v -k CrashVerdictRaceTest` (the PR's own new test module, untracked on this branch — see "Upstream basis" for its path) — result: `9 passed in 2.24s`, all 9 individually listed as PASSED.

**2. Full suite, no regression — failing-test-NAME sets as sets, collection scope stated.** `test/` is the collection scope both sides (the touched Python modules' test callers live under `test/`; the repo also carries a separate `tests/` directory unrelated to these files). Ran twice, once per worktree:

checked: `cd /tmp/pr2882-verify && python3 -m pytest test/ -q` — result: `15 failed, 450 passed, 3 xfailed in 31.73s`
checked: `cd /tmp/main-verify && python3 -m pytest test/ -q` — result: `15 failed, 441 passed, 3 xfailed in 31.69s`

derived: sorted the two 15-name `FAILED ...` line sets into files and diffed them — result: `IDENTICAL SETS` (byte-identical test IDs both sides; 450 − 441 = 9, exactly the new tests). No regression.

**3. Completed session inside the post-exit tail must not be respawned — constructed with real OS processes, not stubs.** Script (`/tmp/adversarial_verify.py`, run against `/tmp/pr2882-verify`):

```python
child = subprocess.Popen(["python3", "-c", "pass"])
child.wait()                              # really exited, rc=0 -- not a stub
wrapper = subprocess.Popen(["sleep", "5"])  # really still running
reset_events(child.pid)                    # session-start only, no session-end
verdict = board.session_end_verdict(str(work), None, wrapper_pid=wrapper.pid)
```

checked: `python3 /tmp/adversarial_verify.py` (scenario 1) — result: `verdict (child dead, real wrapper subprocess alive): in-progress`. Matches expectation — a real, distinct wrapper subprocess still running suppresses the false `crashed`.

**4. Genuine crash must still respawn — both real processes actually dead, exercised at `_auto_respawn_check()` (the function that actually calls `_respawn_or_cap()`), `_respawn_or_cap` mocked only at its own process-spawning boundary.**

```python
wrapper.wait()  # let the wrapper ALSO actually finish -- genuine crash, not a stub flag
verdict2 = board.session_end_verdict(str(work), None, wrapper_pid=wrapper.pid)
# -> "crashed"
with mock.patch.object(spawn, "_respawn_or_cap") as rc:
    spawn._auto_respawn_check("issue-2874/demo", entry, {})
# rc.called -> True
```

checked: same script, scenarios 2–3 — result: `verdict (child dead, wrapper also actually dead): crashed`; `respawn_or_cap called: True`. Respawn still fires for a real crash — the trade the issue's "must not" constraint warns against did not silently break.

**5. `wrapper_pid` attacked directly — missing, stale, and reused-by-unrelated-process, all against the real `board.session_end_verdict()` and real OS pids.**

- Missing (roster entry predates the field): `board.session_end_verdict(str(work), None, wrapper_pid=entry_old.get("wrapper_pid"))` with the key absent entirely → `crashed`, byte-identical to pre-fix behavior. checked: scenario 4 — result: `verdict for old-format entry (no wrapper_pid key): crashed`.
- Stale (the pid the entry recorded has since actually exited — a second real subprocess spawned and `.wait()`-ed): → `crashed`. checked: scenario 5 — result: `verdict when wrapper_pid itself is dead: crashed`.
- **Reused-by-unrelated-process, reproduced live, not reasoned about**: a real, currently-running `sleep 5` subprocess with no relationship whatsoever to this roster entry, passed as `wrapper_pid` → `in-progress`. checked: scenario 6 — result: `verdict when wrapper_pid is some totally unrelated LIVE process: in-progress`. This independently confirms (does not merely re-cite) the PR's own before-landing hunt finding: `alive_fn(wrapper_pid)` is a bare `os.kill(pid, 0)` with no process-identity check — any live pid at all forces `in-progress`, whether or not it has anything to do with the session. Per `defect-verification-independence-from-upstream-verdicts` rule 3, this was re-derived from a fresh, independently-constructed fixture rather than cited against the hunt record's own repro.

**6. Roster-population check — is the "missing wrapper_pid" case actually reachable for a session spawned today?** Traced both `roster_register()` call sites, read this session:

canonical: `spawn.py:4319-4332` (`/tmp/pr2882-verify` worktree) — `_early_roster_entry` (the fork-child's own pre-`Popen` stub) sets `"wrapper_pid": os.getpid()`.
canonical: `spawn.py:4423-4458` (`/tmp/pr2882-verify` worktree) — the main `roster_register()` call after `Popen()` sets `"wrapper_pid": os.getpid()` (pre-existing, issue #224, unchanged by this PR).

Both roster-entry-creation sites already populate `wrapper_pid` (this predates PR #2882 — issue #224). The "missing" case this PR falls back safely on is therefore a narrow historical case (an entry created before issue #224 shipped `wrapper_pid` at all), not a live gap for any session spawned by the current codebase.

**7. Caller-completeness — every `session_end_verdict()` call site and every `_respawn_or_cap()` call site traced, not just the three the PR names.**

derived: `grep -rn "session_end_verdict(" --include="*.py" . | grep -v test/` on this review branch (== `origin/main`, pre-fix) — result: 5 non-test call sites total: `board.py:1237` (the definition), `spawn.py:951` (`_build_observed`), `lifecycle.py:89` (`_roster_reconcile_unreported`), `lifecycle.py:277` (`_post_session_end_comment`), `lifecycle.py:496` (`_auto_respawn_check`), `watchdog.py:305` (`diagnose_health`). The PR updated 3 of the 4 real callers (`_build_observed`, `_auto_respawn_check`, `diagnose_health`) and left 2 unmodified (`_roster_reconcile_unreported`, `_post_session_end_comment`).

canonical: `lifecycle.py:60-112` and `lifecycle.py:263-301` (this repo, current branch — unchanged by PR #2882) — both unmodified callers gate exclusively on `verdict != "normal": continue/return` (`lifecycle.py:90` and `lifecycle.py:278`); neither branches on `crashed` vs. `stalled` vs. `in-progress` at all, so threading `wrapper_pid` through them would not change their observable behavior (a completed-but-in-tail session reads as "not normal yet" either way, and both are idempotent read-then-check functions that self-correct on the next tick once `session-end` actually lands). This independently confirms the PR's "three crash-consequential callers" framing is complete, not merely trusted from the record.

derived: `grep -n "_respawn_or_cap(" lifecycle.py` (`/tmp/pr2882-verify` worktree) — result: 2 call sites, `lifecycle.py:531` (inside `_auto_respawn_check`, updated) and `lifecycle.py:566` (inside `_self_trigger_respawn`).

canonical: `lifecycle.py:538-567` (`/tmp/pr2882-verify` worktree), read this session — `_self_trigger_respawn()` never calls `session_end_verdict()` at all; it fires synchronously from `_spawn_one()` itself immediately after a *normal* completion whose *outcome* classification (`uncommitted-work`/`failed-no-commit`/`silent-failure`) was bad, not from a crash-verdict race. Its own docstring (`lifecycle.py:546-556`) states `roster_watchdog()`/`_auto_respawn_check()`'s crashed-branch can never reach this path because `roster_remove()` already deleted the entry synchronously beforehand. Confirmed out of scope for this issue, not a missed fourth consumer.

**8. `[reconcile-poll-disagreement]` — constructed a real disagreement through the actual `watchdog.roster_watchdog()` body, not reasoned about.** Even after the `wrapper_pid` fix, `reconcile()` (via `_build_observed()`) and `diagnose_health()` can still disagree through a structurally different route: `reconcile()` returns `respawn` unconditionally the moment `session_verdict == "crashed"` (before ever consulting `pr_number`), while `diagnose_health()` treats `pr_number is not None` as completion regardless of verdict. Constructed the case directly: real dead child pid, real dead wrapper pid (genuine crash by the fix's own definition — see item 4 above), but the branch already has an open PR (a realistic shape: the session pushed and opened its PR, then the driving wrapper itself was killed before writing `session-end`). Script `/tmp/adversarial_disagreement.py`: unrelated board-wide/network sweeps (`_board_wide_sweep_all`, `lease_reconcile_sweep`, `spawn_attempt_sweep`, `tmp_resource_sweep`, `standing_red_check`, `_undispositioned_skill_prs`) mocked to no-ops since they are orthogonal to this question and would otherwise need a real GitHub-backed board; `_pr_open_or_merged_for_branch`/`_board_pr_index` mocked to report PR #4242 open for this branch; `_respawn_or_cap` mocked only at its process-spawning boundary; `reconcile()` and `diagnose_health()` (the two functions actually under test) left completely real, reached through the real `roster_watchdog()` function body.

checked: `python3 /tmp/adversarial_disagreement.py` — result:
```
session_end_verdict for this fixture (real dead child + real dead wrapper): crashed
[reconcile] issue-2874/demo: divergence — session-crashed: role=demo branch=issue-2874/demo: session_verdict=crashed -> respawn
[reconcile-poll-disagreement] issue-2874/demo: reconcile says session-crashed (-> respawn) but poll-report says completion (completion, not a health diagnosis) — the two disagree; not resolved silently, needs a human look
[poll-report] issue-2874/demo: COMPLETED — completion, not a health diagnosis
[watchdog] issue-2874/demo: crashed
roster_watchdog() returned anomaly_count = 2
_respawn_or_cap called (respawn still queued despite the disagreement print)? True
```
The line names both verdicts (`session-crashed (-> respawn)` vs. `completion`), fires through the real orchestration path, and — critically — does not silently pick a winner: respawn still queues (`_respawn_or_cap` called, correct here since the session genuinely crashed by the fix's own definition) *while* the disagreement is also surfaced, exactly the "not resolved silently by whichever ran last" behavior the issue asked for.

**9. Empty state — agreement produces nothing extra, exercised at the same real orchestration path.** Same construction, but the wrapper is genuinely still alive (a real completed-in-tail session) and no PR is mocked in.

checked: `python3 /tmp/adversarial_agree.py` — result:
```
[poll-report] issue-2874/demo2: COMPLETED — completion, not a health diagnosis
[watchdog] issue-2874/demo2: in-progress
이상 신호 없음
anomaly_count = 0 | respawn_or_cap called: False
```
No `[reconcile]` line (verdict is `in-progress`, not `crashed`, so `reconcile()` returns `[]`), no `[reconcile-poll-disagreement]` line, no respawn, `anomaly_count == 0`. Matches the acceptance's stated empty state.

**10. No overhead increase, measured, not asserted.**

derived: `git diff origin/main pr-2882 -- board.py spawn.py lifecycle.py watchdog.py | grep -E '^\+' | grep -viE '^\+\+\+' | grep -iE 'subprocess\.run|gh |gh_api|time\.sleep|lease|timeout'` — result: no code matches (the one hit is a doc-comment line quoting the word "lease" while explaining the fix does *not* touch it).

derived: micro-benchmark of the actual new syscall (`_alive()`, an `os.kill(pid, 0)`), 10,000 calls, `timeit` — result: `0.55 us/call`. The fix adds exactly one such call, only on the already-existing dead-child-pid branch (already the rare path — most poll ticks see a live child pid and never reach this code at all).

**11. No return of the retired role axis, plural-catching pattern (issue #2876 lesson applied).**

derived: `git diff origin/main pr-2882 -- board.py spawn.py lifecycle.py watchdog.py -- '*.py' | grep -E '^\+' | grep -inE '\b(role|roles)\b'` — result: no matches (exit code 1); scope includes the PR's new test module (matched by the `*.py` pathspec) without spelling its path out again.

derived: `git show origin/main:gates/retirement_count.py` — result: `fatal: path 'gates/retirement_count.py' does not exist in 'origin/main'` — confirmed untracked, not merely absent from this listing; `gh pr view 2881 --repo tokenmaxxxer/on-the-record --json state` — result: `state: OPEN`. The task brief's premise that this checker "landed for this" (issue #2876) does not hold as of this review: only its own independent-verification *records* (`docs/issue-2876/reports/*.md`, PRs #2884/#2885) landed on `main`; the checker script itself, added by the still-open PR #2881, remains untracked everywhere this review looked. Flagged as a correction to the task brief, not acted on further — the `\b(role|roles)\b` grep above already covers the plural blind spot #2876 exists to catch, so the missing tool did not block this invariant check.

**12. Monitor/watch machinery unbroken and not quieter — the whole watch path, not just the changed function.** Items 8–9 above exercise the real `roster_watchdog()` body end to end and show all four print classes still emitting correctly in the constructed scenarios: `[reconcile]` (fires on genuine crash, silent on agreement), `[poll-report]` (both `DEAD-ERRORED`/`crashed`-detail and `COMPLETED` paths shown), `[watchdog]` (per-entry verdict line, both `crashed` and `in-progress`), and the new `[reconcile-poll-disagreement]` (fires only on genuine disagreement, silent on agreement). Nothing became quieter: every pre-existing print class fired in at least one constructed scenario above, and the new class is strictly additive.

## Why

Per `defect-verification-independence-from-upstream-verdicts`, every claim above was re-derived from a fresh fixture this session constructed, not cited against the PR record's own repro — including the one finding (wrapper_pid identity gap) the PR's own hunt had already disclosed, re-run here with an independently-chosen unrelated process rather than accepted as read. Real OS subprocesses (`subprocess.Popen`/`.wait()`) were used throughout instead of `unittest.mock` stand-ins for pid liveness, per the task's "against real processes, not stubs" instruction — the PR's own test file already does this reasonably (`os.getpid()` for "alive", a fixed nonexistent int for "dead"); this review additionally spawned-and-waited real child processes for both the "dead" and "alive" sides, and specifically an *unrelated* real process for the pid-reuse-analog case, which the PR's own test suite does not cover (it only covers wrapper_pid omitted/dead, not wrapper_pid-alive-but-unrelated).

The `[reconcile-poll-disagreement]` construction (item 8) deliberately targeted a case the direct `wrapper_pid` fix does *not* close, per the task's framing ("a future divergence this fix does not anticipate reports itself") — reusing the exact mechanism (`pr_number` masking a real crash) that pre-existed this PR in `diagnose_health()`'s own completion check, now shown to still produce a real reconcile-vs-poll-report split even with the fix applied, which the observability line correctly surfaces rather than silently resolving.

## What did not work

None.

## Upstream basis

- `docs/issue-2874/reports/silent-failure-audit-e7b244cd.md` — PR #2882's own delivery record, commit `0fc4f21a` on `issue-2874/silent-failure-audit-e7b244cd`; untracked on this branch (PR still open — see "What was done" for the `gh pr view` confirmation), read via `git show pr-2882:docs/issue-2874/reports/silent-failure-audit-e7b244cd.md` this session.
- `docs/issue-2874/reports/silent-failure-audit-e7b244cd/2026-08-30-hunt-reconcile-crash-verdict-race.md` — same PR's before-landing hunt record; untracked on this branch for the same reason, read via `git show pr-2882:...` this session; its stance-0 finding (pid-reuse identity gap) was independently re-derived in item 5 above, not cited.
- `board.py`, `spawn.py`, `lifecycle.py`, `watchdog.py` — modified by PR #2882; read/exercised both pre-fix (this branch / `origin/main`) and post-fix (scratch worktree `/tmp/pr2882-verify` from `pr-2882`, commit `0fc4f21a`) this session.
- `test/test_reconcile_crash_verdict_race.py`, untracked on this branch (added by PR #2882, still open) — read/executed via scratch worktree `/tmp/pr2882-verify` this session.
- derived: `git show origin/main:gates/retirement_count.py` — result: `fatal: path 'gates/retirement_count.py' does not exist in 'origin/main'`. `gates/retirement_count.py`, untracked everywhere this review looked (confirmed absent from both `origin/main` and `pr-2882`, see item 11) — referenced by the task brief; the tool this review would otherwise have used does not exist on any branch this review is based on.

## Open findings

1. **`wrapper_pid` process-identity gap — independently reproduced, not a new finding.** canonical: this session's own scenario-6 run (item 5 above), `python3 /tmp/adversarial_verify.py` result `verdict when wrapper_pid is some totally unrelated LIVE process: in-progress` — confirms `alive_fn(wrapper_pid)` accepts any currently-live pid, including one with zero relationship to the roster entry, and reads it as `in-progress`. This is the same gap the PR's own before-landing hunt already disclosed (its untracked hunt record, cited in full in "Upstream basis" above, read via `git show pr-2882:...` this session) and declined to fix in-scope (citing issue #2874's own "do not widen the lease or lengthen a wait" constraint, and the absence of any process-identity primitive — e.g. `/proc/<pid>` start-time comparison — anywhere in this codebase). This review's contribution is independent confirmation with a fresh, unrelated-process fixture, not a new defect. Resolution path: unchanged from the PR's own recommendation — a follow-up issue covering both this use and `_watch --follow`'s pre-existing identical gap (issue #224) together.
2. **Task-brief premise correction: `gates/retirement_count.py` has not landed.** derived: `git show origin/main:gates/retirement_count.py` — result: path does not exist, confirmed untracked; `gh pr view 2881` — result: `state: OPEN` (item 11 above). The task brief stated the plural-blind-spot checker "landed for this" (issue #2876); as of this review it is still on the open PR #2881, not `main`. Resolution path: none needed for this review — item 11 above used an equivalent `\b(role|roles)\b` grep directly, which is not vulnerable to the #2876 blind spot either way.
3. None else — the reconcile-vs-poll-report disagreement this issue reports is closed for the specific window (`wrapper_pid` threading, verified in both directions), and the residual disagreement class the fix cannot close by construction is now named rather than silent (item 8).

skill-verdict: adversarial-review — applied: invoked; used the skill's "evaluator receives the deliverable and finds real problems" stance to treat PR #2882's own record as a claim to re-derive rather than a settled fact — every numbered item above is a fresh construction against real processes/real code paths, not a restatement of the PR record's own repro steps.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-derived the PR's own disclosed hunt finding (item 5) from an independently-chosen fixture instead of citing it, included negative/edge-case constructions (stale pid, unrelated-but-live pid, old-format entry) alongside the happy-path direction, and recorded the "no fourth consumer" and "empty-state" checks with the same rigor as the positive findings (rules 1-3, 7 of the skill).
skill-verdict: work-in-english — applied: invoked; this record, all scratch scripts, and the PR title/body are written in English per the project's own commit-message convention (English titles/bodies; code comments in the touched files remain Korean, matching each file's existing convention, unchanged by this review since no code was edited).
other mounted skills: not triggered (code-review, simplify, security-review, and the remaining marketplace skills do not match a verification-only task with no code changes of its own).

## Next steps

acceptance: `cd /tmp/pr2882-verify && python3 -m pytest -v -k CrashVerdictRaceTest` (the PR's own new regression module, untracked on this branch — see "Upstream basis" for its full path) — result:
```
9 passed in 2.24s
```
`loop_state: complete` — every acceptance item the task brief asked for was exercised this session against real processes/real code paths (items 1-12 above), with no follow-up execution pending for this review. This review made no code changes; PR #2882 remains open pending its own landing decision, which is outside this record's scope.
