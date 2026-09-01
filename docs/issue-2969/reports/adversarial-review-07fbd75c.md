---
issue: 2969
role: adversarial-review-07fbd75c
author: adversarial-review-07fbd75c
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: 34b8b0f4a9b7609b47eb9a99039d0ea000280be5:docs/issue-2969/reports/silent-failure-audit+test-derivation-bb5cc534.md
    sha: 34b8b0f4a9b7609b47eb9a99039d0ea000280be5
---

# issue-2969 — adversarial-review-07fbd75c record

skill-verdict: adversarial-review — applied: invoked; this record is a structurally independent evaluator of PR #2990 (issue-2969's own deliverable) — own git worktrees off both the PR head and `origin/main`, own re-run of every acceptance check, own diff audit and own live repro of a defect the PR's record does not mention, rather than accepting the PR's claimed test-plan output.

## What was done

Independent verification of PR #2990 (branch `issue-2969/silent-failure-audit+test-derivation-bb5cc534`, tip `34b8b0f4a9b7609b47eb9a99039d0ea000280be5`) — canonical: `gh pr view 2990` (state: OPEN), read this session.

1. Fetched the PR head into an isolated worktree (`git fetch origin pull/2990/head:pr-2990-verify && git worktree add /tmp/pr-2990-verify-3836911 pr-2990-verify`) and re-ran all 4 of issue #2969's acceptance checks myself — derived:
```
$ python3 -m pytest tests/ -k health_verdict_confirmed_vs_unconfirmed -q
6 passed in 0.88s
$ python3 -m pytest tests/ -k liveness_pid_reuse -q
6 passed in 0.84s
$ python3 -m pytest tests/ -k flapping_verdict -q
7 passed in 0.87s
$ python3 -m pytest tests/ -k destructive_action_requires_consecutive -q
4 passed in 0.90s
```
All 4 acceptance requirements met.

2. Full-repo regression, independently — derived: `python3 -m pytest test/ tests/ -q -m "not slow"` on the PR worktree — result: `16 failed, 638 passed, 3 xfailed`; same command on a fresh `origin/main` worktree (tip `f737b6c8`, fetched this session) — result: `16 failed, 640 passed, 3 xfailed`. `diff` of the two sorted `FAILED`-line sets — result: exit 0 (identical) — the 16 failures are pre-existing on `main`, not introduced by this PR (the 640-vs-638 base-passed delta is `main` having advanced past the PR's fork point, not a regression).

3. Audited the diff (`git diff main...HEAD --stat` inside the PR worktree = 11 files, 737 insertions/8 deletions across `watchdog.py`/`lifecycle.py`/`spawn.py` + 5 test files + 2 doc files) against the issue's must-not list, each independently re-derived rather than trusting the PR's own record:
   - **Unconfirmed liveness resolved by guessing in neither direction**: confirmed. `watchdog.py`'s new `_paired_liveness()` returns `"unconfirmed"` before any HEALTHY/DEAD branch when a pid is alive but the start-time pairing cannot be established; `diagnose_health()` routes that straight to `"LIVENESS-UNCONFIRMED"` / `next_action: "resume-watch"` — canonical:
```
34b8b0f4a9b7609b47eb9a99039d0ea000280be5:watchdog.py (diagnose_health):
    liveness = _paired_liveness(pid, entry.get("start_time"))
    if liveness == "unconfirmed":
        return _diagnosis({"state": "LIVENESS-UNCONFIRMED", "next_action": "resume-watch",
                "detail": f"{key}: pid {pid} 살아있으나 시작시각 짝짓기를 세울 수 "
```
     (read this session in the PR worktree). Also confirmed the macOS case specifically (see item 4 below).
   - **`DEAD-UNRECOVERED-COMMITS`/`DEAD-REMOTE-STATE-UNKNOWN`/`STALLED-*`/`subagent_in_flight` survive intact**: confirmed — derived: `grep -n "DEAD-UNRECOVERED-COMMITS\|DEAD-REMOTE-STATE-UNKNOWN\|STALLED-HEARTBEAT-ONLY\|STALLED-FLAT-PROGRESS" watchdog.py` in the PR worktree still finds all four states with `next_action: "resume-watch"` unchanged; `grep -rn subagent_in_flight` finds it only in `trajectory_analyzer.py`, a file absent from the PR's `git diff main...HEAD --stat` file list — untouched by this PR.
   - **No advisory sub-state newly reaches kill/refuse/gate-block**: confirmed — `STALLED-FLAT-PROGRESS`/`STALLED-HEARTBEAT-ONLY` both still return `next_action: "resume-watch"`, neither line touched by the diff; the PR's new `"flapping"` flag only changes what `roster_watchdog()` prints (`anomaly_count` is a reporting/exit-code tally returned to the CLI, never itself fed into `_auto_respawn_check()` — derived: `grep -n "roster_watchdog(\|anomaly_count" watchdog.py spawn.py` in the PR worktree, traced by hand).
   - **No mtime-as-confirmed-root-cause claim**: confirmed — derived: `grep -n mtime watchdog.py` inside the PR worktree — the only `mtime` hits are the two pre-existing, untouched anomaly checks; `_confirmed_progress_seen()` uses `log_path.stat().st_size` only, and its own docstring calls the mtime hypothesis explicitly unconfirmed.

4. macOS constraint (`/proc` absent, issue #2924): checked what the new pid+start-time pairing does when start time cannot be read. `_proc_start_time()` (`watchdog.py`) opens `/proc/{pid}/stat`, catching `FileNotFoundError`/`OSError` -> `None` — on macOS this is unconditional. `spawn.py`'s two `roster_register()` call sites record `"start_time": _proc_start_time(<pid>)` at spawn time, so on macOS every roster entry's `recorded_start_time` is `None` from the start; `_paired_liveness()` checks `if recorded_start_time is None: return "unconfirmed"` before ever comparing, so macOS sessions land on `"unconfirmed"` deterministically and can never hit the `None == None` "always looks like a match" trap that issue #2924's own fix (`watchdog_lock_acquire()`, a pre-existing, different function this PR does not touch) had to work around — canonical: `34b8b0f4a9b7609b47eb9a99039d0ea000280be5:watchdog.py` `_proc_start_time()`/`_paired_liveness()`, read this session. `34b8b0f4a9b7609b47eb9a99039d0ea000280be5:tests/test_liveness_pid_reuse.py`'s `test_liveness_pid_reuse_proc_unavailable_degrades_to_unconfirmed` exercises exactly this by mocking `_proc_start_time` to return `None` — derived: `python3 -m pytest tests/test_liveness_pid_reuse.py -k proc_unavailable -q` in the PR worktree — result: `1 passed`. No runtime-visible degradation *message* is added on macOS for this specific path (unlike `watchdog_lock_acquire()`'s pre-existing #2924 notice); the returned `"LIVENESS-UNCONFIRMED"` detail string already says "시작시각 미기록 또는 /proc 부재" (start time unrecorded or /proc absent), visible in `[poll-report]` output either way — not a defect, just narrower than #2924's dedicated lock-path notice.

## Why

Verify-at-landing per contract: the PR's own record claims specific pass counts and a "zero regressions" full-repo sweep. Re-deriving each number independently in a fresh worktree, rather than reading the claim, is the only way to catch a claim that is true for the command actually run but incomplete for the system as a whole. That is exactly what happened here (finding 1 below): the PR's regression sweep (`test/ tests/`) is real and its 638-passed/16-pre-existing-failed result reproduces exactly — derived: `python3 -m pytest test/ tests/ -q -m "not slow"`, this session, in the PR worktree — result: `16 failed, 638 passed, 3 xfailed`, matching the PR's own claimed count — but that glob does not cover `on-the-record/monitors/`, where a live consumer of the exact string this PR renames turned out to break silently (reproduced live in finding 1, not merely inferred).

## Upstream basis

- `34b8b0f4a9b7609b47eb9a99039d0ea000280be5` (PR #2990 head) — the subject of this verification; diff audited via `git diff main...HEAD` inside `/tmp/pr-2990-verify-3836911`.
- `34b8b0f4a9b7609b47eb9a99039d0ea000280be5:docs/issue-2969/reports/silent-failure-audit+test-derivation-bb5cc534.md` (PR #2990's own delivery record) — read for its claimed results, cross-checked rather than trusted.
- `f737b6c8` (`origin/main` at verification time) — the pre-PR baseline used for the regression diff and the failing-test-set comparison.
- issue #2969 itself (`gh issue view 2969`, read this session) — source of the 4 acceptance checks and the must-not list audited above.

## Open findings

### 1. CONFIRMED — PR #2990 silently defeats issue #2906's HEALTHY noise-suppression in the poll-heartbeat monitor

`on-the-record/monitors/poll_heartbeat_delta.py:189` (pre-existing, untouched by this PR — confirmed above) special-cases the exact literal string `"HEALTHY"` to strip only the trailing last-tool-activity clause before comparing two poll-report ticks, so a session that keeps calling tools without anything anomalous happening does not re-notify every tick (issue #2906, comment at `on-the-record/monitors/poll_heartbeat_delta.py:43-61` names this explicitly: "defeating #1220 for exactly the case... that has nothing for the orchestrator to act on"). PR #2990 renames `watchdog.py`'s healthy state from `"HEALTHY"` to `"HEALTHY-CONFIRMED"`/`"HEALTHY-UNCONFIRMED"` (`34b8b0f4a9b7609b47eb9a99039d0ea000280be5:watchdog.py`, `diagnose_health()` residual branch) but never touches `on-the-record/monitors/poll_heartbeat_delta.py` — derived: `git diff main...HEAD --stat` in the PR worktree lists no `on-the-record/` path — whose comparison is `if state_token == "HEALTHY":` (line 189) — a literal-string check that can never match either new state name.

Live repro, reusing the project's own test harness (`on-the-record/monitors/test_poll_heartbeat.py`'s `_run_tick`/`_make_checkout`, both pre-existing) but feeding a report string built from the PR's actual new detail text instead of the stale fixture's pre-PR `"HEALTHY"` wording — derived, this session, `python3` script importing `test_poll_heartbeat` and calling `_run_tick` four times with a `[poll-report] ...: HEALTHY-UNCONFIRMED — ...` line whose only per-tick difference is the trailing timestamp:
```
tick0 stdout: '[poll-report] issue-500/implementation: HEALTHY-UNCONFIRMED — ... 마지막 도구 호출: Read file0.py (10:00:00 UTC)\n...'
tick1 stdout: '[poll-report] issue-500/implementation: HEALTHY-UNCONFIRMED — ... 마지막 도구 호출: Read file1.py (10:01:00 UTC)\n'
tick2 stdout: '[poll-report] issue-500/implementation: HEALTHY-UNCONFIRMED — ... 마지막 도구 호출: Read file2.py (10:02:00 UTC)\n'
tick3 stdout: '[poll-report] issue-500/implementation: HEALTHY-UNCONFIRMED — ... 마지막 도구 호출: Read file3.py (10:03:00 UTC)\n'
```
Every tick re-emits to stdout (the Monitor channel this repo arms in every interactive session — `README.md:108-110`: "is armed in every interactive session of any repo with the plugin installed") even though only the trailing timestamp changed, reproducing precisely the pre-#2906 noise. Contrast: the pre-existing test `t_healthy_poll_report_with_drifting_detail_suppresses_after_first_tick` in `on-the-record/monitors/test_poll_heartbeat.py` still passes on the PR worktree — derived: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q` in the PR worktree — result: `37 passed` — only because its `_healthy_report()` fixture helper (`on-the-record/monitors/test_poll_heartbeat.py:448-459`) hardcodes the pre-PR `"HEALTHY"` / `"최근 로그 성장"` wording rather than importing it from `watchdog.py` — the fixture's own docstring claims it "mirrors watchdog.py's real ... shape", which is no longer true after this PR. This blind spot is why neither the PR's own regression sweep (scoped to `test/ tests/`, which does not include `on-the-record/monitors/`) nor `on-the-record/monitors/test_poll_heartbeat.py` itself (which never calls into `watchdog.py`) caught it.

Severity: high in practice — `HEALTHY-UNCONFIRMED` (the common case: no anomaly, but log growth not confirmed this tick) is likely the majority per-tick state for an idle-but-fine session, so this silently re-arms exactly the notification spam issue #2906 was written to kill, for every interactive session using this plugin. Resolution path: either change `on-the-record/monitors/poll_heartbeat_delta.py`'s `state_token ==` check to match `state_token.startswith("HEALTHY")` (or an explicit set of the two new names) and update `on-the-record/monitors/test_poll_heartbeat.py`'s `_healthy_report()` fixture to the PR's real detail text, or import the state-name constants from `watchdog.py` instead of hardcoding a string the module no longer produces. Not covered by any of issue #2969's 4 written acceptance checks or its must-not list, so it does not fail the letter of the acceptance criteria — but it is a real, reproduced regression this PR introduces.

### 2. The PR's own record overstates where destructive action is gated — `_self_trigger_respawn()` reaches the same sink from a single outcome, ungated

The PR's record (`34b8b0f4a9b7609b47eb9a99039d0ea000280be5:docs/issue-2969/reports/silent-failure-audit+test-derivation-bb5cc534.md`) states: "`_auto_respawn_check()` (the only place a watchdog verdict automatically triggers a destructive action — `_respawn_or_cap()` -> `_spawn_one()`; `roster_kill()` is human-CLI-only, never verdict-triggered, so it needed no change)". This is not accurate: `lifecycle.py`'s `_self_trigger_respawn()` (called from `spawn.py:5079` in the PR worktree, itself inside `_spawn_one()`'s own end-of-session handling) also calls `_sp._respawn_or_cap()` directly and unconditionally on a single outcome classification (`uncommitted-work`/`failed-no-commit`/`silent-failure`) — canonical:
```
34b8b0f4a9b7609b47eb9a99039d0ea000280be5:lifecycle.py (_self_trigger_respawn):
    if outcome not in _sp._ABANDONED_WORK_OUTCOMES:
        return
    state = _sp._respawn_state_load()
    trigger = ("self-triggered-causeless" if outcome == "silent-failure"
               else "self-triggered-abandoned")
    _sp._respawn_or_cap(roster_key, work, issue, skill, log, session_start_ts, state,
                    trigger, single_phase)
```
(read this session in the PR worktree; `git diff main...HEAD -- lifecycle.py` there shows no hunk touching this function's body — this pre-existing function, also present on `main` at `lifecycle.py:538`, is unmodified by this PR). Its own docstring confirms this is a deliberately separate path specifically because the watchdog-tick crashed-verdict path *cannot* see this case: "`roster_watchdog()`/`_auto_respawn_check()` 의 crashed 판정은 이 경우에 절대 못 걸린다" (that crashed-verdict path can never fire here). Neither this function nor its call site gained a `RESPAWN_CONSECUTIVE_CONFIRMATIONS`-style gate in this PR, and `34b8b0f4a9b7609b47eb9a99039d0ea000280be5:tests/test_destructive_action_requires_consecutive.py` only exercises `_auto_respawn_check`/`spawn._auto_respawn_check`, never `_self_trigger_respawn` — derived: `grep -n _self_trigger_respawn tests/test_destructive_action_requires_consecutive.py` in the PR worktree — result: no match.

Mitigating factor, not a dismissal: this path's "single snapshot" is a session's own synchronous end-of-life outcome classification, not an external poll of another process's ambiguous liveness (the pid-reuse/staleness risk the issue's field report and consult were about) — so it is a different risk shape, arguably lower-risk, than the watchdog-tick path the issue's incident narrative describes. Whether it should be in scope is a judgment call the PR never makes explicitly; what is not a judgment call is that the record's "the only place" claim is false as written. Issue #2969's acceptance check 4 (`destructive_action_requires_consecutive`) and its must-not line are both satisfied literally (the check only names the watchdog-tick path, which is correctly gated), so this does not fail the written acceptance criteria — but it is a gap between the record's stated completeness and the actual code, worth a maintainer decision (gate this path too, or narrow the record's claim) rather than silent reliance on the inaccurate claim.

## Next steps

None required to record this verification — `loop_state: landed`. Findings 1 and 2 above are follow-up items for whoever lands or amends PR #2990: finding 1 (live regression, reproduced) is the stronger candidate for a blocking fix before merge; finding 2 (record accuracy / possible scope gap) is a judgment call for a maintainer, not a reproduced defect in the gated path itself.

skill-verdict: adversarial-review — applied: invoked; see the invocation line under the title above.
other mounted skills: not triggered (work-in-english is directive-only, enforced by the core hook layer, not something this session invoked via the Skill tool; conformance-review-finding-record does not apply — this record is an adversarial-review verdict, not a docs/issue-<n>/reports/conformance-review.md finding).
