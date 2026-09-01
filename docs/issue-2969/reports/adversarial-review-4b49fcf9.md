---
issue: 2969
role: adversarial-review-4b49fcf9
author: adversarial-review-4b49fcf9
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 34b8b0f4a9b7609b47eb9a99039d0ea000280be5
loop_state: landed
type: fix
breaking: false
verdict: fail
upstream:
  - path: watchdog.py
    sha: 34b8b0f4a9b7609b47eb9a99039d0ea000280be5
  - path: lifecycle.py
    sha: 34b8b0f4a9b7609b47eb9a99039d0ea000280be5
  - path: spawn.py
    sha: 34b8b0f4a9b7609b47eb9a99039d0ea000280be5
---

# issue-2969 — adversarial-review-4b49fcf9 record

## What was done

Independently verified PR #2990 (branch
`issue-2969/silent-failure-audit+test-derivation-bb5cc534`, head
`34b8b0f4a9b7609b47eb9a99039d0ea000280be5`) — the watchdog
verdict-confidence fix for issue #2969. Fetched the PR head into an
isolated `git worktree` under the plugin-managed `$MUSTER_TEMP_ROOT`
(`git fetch origin pull/2990/head:pr-2990-head && git worktree add
"$MUSTER_TEMP_ROOT/pr-2990" pr-2990-head`) and re-ran every issue-#2969
acceptance check myself inside it, without citing PR #2990's own
pasted numbers as evidence. `tests/test_liveness_pid_reuse.py`
(untracked) and
`docs/issue-2969/reports/silent-failure-audit+test-derivation-bb5cc534.md`
(untracked) exist only inside that `pr-2990-head` worktree/branch —
both are untracked on this session's own
`issue-2969/adversarial-review-4b49fcf9` tree, present solely in the
fetched worktree.

Re-run results, each executed live in the isolated worktree this turn —

acceptance: `python3 -m pytest tests/ -k health_verdict_confirmed_vs_unconfirmed -q` — result:
```
6 passed in 0.91s
```
acceptance: `python3 -m pytest tests/ -k liveness_pid_reuse -q` — result:
```
6 passed in 0.87s
```
acceptance: `python3 -m pytest tests/ -k flapping_verdict -q` — result:
```
7 passed in 0.86s
```
acceptance: `python3 -m pytest tests/ -k destructive_action_requires_consecutive -q` — result:
```
4 passed in 0.92s
```

All four match PR #2990's claimed counts exactly, reproduced independently in a fresh worktree.

canonical: `git diff main...HEAD -- watchdog.py lifecycle.py spawn.py`, read in full this turn inside the isolated worktree (merge-base `167cc19a`) — `must not` list audit against that diff:

- **Unconfirmed liveness resolved by guessing in neither direction**: `_paired_liveness()` (`watchdog.py`) returns `"dead"` only when `_sp._alive(pid)` is false or the paired start_time provably mismatches, `"alive"` only when it provably matches, and `"unconfirmed"` whenever the pairing cannot be established (`recorded_start_time is None`, or the current-side `_proc_start_time()` read fails). `diagnose_health()` routes `"unconfirmed"` to a dedicated `LIVENESS-UNCONFIRMED` / `next_action: "resume-watch"` return, placed before both the `HEALTHY-*` branch and the `if liveness == "dead":` branch — neither guess is made. acceptance: `python3 -m pytest tests/test_liveness_pid_reuse.py (untracked) -k diagnose_health_reports_third_state_not_healthy_or_dead -q` — result:
```
1 passed in 0.87s
```
Not violated.
- **`DEAD-UNRECOVERED-COMMITS` / `DEAD-REMOTE-STATE-UNKNOWN` / `STALLED-*` / `subagent_in_flight` survive intact**: derived: `git show 0ec5bf96 -- watchdog.py | grep -c '^-'` — result: `5` (exactly 5 lines removed by the diff: the old `alive =`/`if not alive:` header, the old single-`HEALTHY` return, the old `!= "HEALTHY"` dedup comparison — none inside a `DEAD-*`/`STALLED-*` branch body). derived: `grep -n "STALLED-FLAT-PROGRESS\|STALLED-HEARTBEAT-ONLY" watchdog.py` — result: both still return literal `"resume-watch"` for `next_action`, unedited lines. derived: `git diff main...HEAD --name-only` — result: `trajectory_analyzer.py` (where `subagent_in_flight()` is defined and used) is absent from the changed-file list, so that guard cannot have been touched. Not violated.
- **No advisory sub-state newly reaches kill/refuse/gate-block**: same two `grep`/`git show` citations above — `STALLED-FLAT-PROGRESS`/`STALLED-HEARTBEAT-ONLY`'s `next_action` lines are unedited. The new `"flapping"` flag is attached uniformly via the `_diagnosis()` closure and only changes what `roster_watchdog()` prints (`[flapping] ...`); it never sets or reads a `next_action` field and is not consulted by `_auto_respawn_check()`. Not violated.
- **mtime not claimed as confirmed root cause**: derived: `grep -n mtime watchdog.py` inside the worktree — result: the only `mtime` hits are inside the two pre-existing, untouched anomaly checks (signal 1's `st_mtime`, signal 6's watcher-silence check); zero inside the new `_confirmed_progress_seen()`, which uses `log_path.stat().st_size` instead. The function's own docstring and the PR's delivery record both name the mtime hypothesis explicitly unconfirmed rather than asserting it. Not violated.
- **No kill/respawn on a single verdict snapshot**: `lifecycle._auto_respawn_check()` now requires `RESPAWN_CONSECUTIVE_CONFIRMATIONS` (2) consecutive `"crashed"` verdicts, tracked via a `crash_confirms` counter riding the same `respawn_state.json`-backed dict, before reaching `_respawn_or_cap()`; any intervening non-`"crashed"` verdict resets the counter to 0. acceptance: `python3 -m pytest test/test_reconcile_crash_verdict_race.py -q` — result:
```
17 passed in 0.71s
```
derived: `grep -n "roster_kill(" *.py | grep -v test` — result: only the `def` in `lifecycle.py` and one CLI-dispatch call site in `spawn.py` — the only other destructive path stays CLI-only, never verdict-triggered. Not violated.

**macOS `/proc`-absence audit** (issue #2924's degradation) — canonical: `watchdog.py`'s `_proc_start_time()`/`_paired_liveness()`, read directly this turn in the worktree:
```
def _proc_start_time(pid: int) -> str | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
        return None
    ...

def _paired_liveness(pid: int, recorded_start_time: str | None) -> str:
    if not _sp._alive(pid):
        return "dead"
    if recorded_start_time is None:
        return "unconfirmed"
    cur_start = _proc_start_time(pid)
    if cur_start is None:
        return "unconfirmed"
    return "alive" if cur_start == recorded_start_time else "dead"
```
On macOS `_proc_start_time()` returns `None` on every call — at roster-registration time (`spawn.py`'s two call sites then record `"start_time": None`) and at re-check time. `_paired_liveness()` tests `if recorded_start_time is None: return "unconfirmed"` *before* ever calling `_proc_start_time(pid)` again — a macOS entry can never reach a `None == None` comparison. This is the exact shape issue #2924 (`71167c3a`) had to patch in `watchdog_lock_acquire()`, where `_proc_start_time(other_pid) == other_start` was vacuously true whenever both sides were `None`, silently accepting a reused pid as "already running" — derived: `git show 71167c3a -- watchdog.py` — result: that commit added a `degraded_note` specifically for the `other_start is None` case, printed inline rather than left in a docstring. PR #2990's `_paired_liveness()` avoids that trap by ordering (never comparing two `None`s) rather than by patching after the fact, and its `LIVENESS-UNCONFIRMED` detail string names the platform cause inline (`"...시작시각 미기록 또는 /proc 부재..."`), matching #2924's own precedent of surfacing the degradation at the print site. acceptance: `python3 -m pytest tests/test_liveness_pid_reuse.py (untracked) -k proc_unavailable_degrades_to_unconfirmed -q` — result:
```
1 passed in 0.86s
```
No gap found here.

**Regression found, outside the issue's explicit must-not list**: the state-string rename (`"HEALTHY"` -> `"HEALTHY-CONFIRMED"` / `"HEALTHY-UNCONFIRMED"`) silently disables issue #2906's repeat-suppression feature in `on-the-record/monitors/poll_heartbeat_delta.py`, a file not touched anywhere in this diff — derived: `git diff main...HEAD --name-only` — result: `poll_heartbeat_delta.py` absent from the changed-file list. canonical: `poll_heartbeat_delta.py:189`, read directly this turn (this file is tracked and pre-existing on this session's own tree too, not PR-only — derived: `ls on-the-record/monitors/poll_heartbeat_delta.py on-the-record/monitors/test_poll_heartbeat.py` — result: both present on this session's own `issue-2969/adversarial-review-4b49fcf9` tree):
```
            if state_token == "HEALTHY":
                pm = POLL_REPORT_STATE_RE.match(prev_line) if prev_line else None
                prev_state = pm.group(1) if pm else None
                changed = prev_state != "HEALTHY" or (
```
That special case exists to suppress re-emitting a healthy poll-report line when only the "last tool activity" timestamp changed — the exact noise issue #2906 built this to suppress. Every other state falls through to a raw `prev_line != line` comparison, which activity-timestamp drift trips on nearly every tick. Reproduced live against this PR's own unmodified `poll_heartbeat_delta.py` — derived: running the script twice with `POLL_HEARTBEAT_TEXT` set to two ticks of an otherwise-identical `HEALTHY-UNCONFIRMED` line differing only in the embedded "last tool call" timestamp — result:
```
$ POLL_HEARTBEAT_TEXT="[poll-report] issue-500/implementation: HEALTHY-UNCONFIRMED — issue-500/implementation: 이상 신호 없음(로그 성장은 확인되지 않음), RUNNING — 손댄 파일 없음; 마지막 도구 호출: Read file0.py (10:00:00 UTC)" python3 on-the-record/monitors/poll_heartbeat_delta.py /tmp/phd_test/state.json 1000
[poll-report] issue-500/implementation: HEALTHY-UNCONFIRMED — issue-500/implementation: 이상 신호 없음(로그 성장은 확인되지 않음), RUNNING — 손댄 파일 없음; 마지막 도구 호출: Read file0.py (10:00:00 UTC)
$ POLL_HEARTBEAT_TEXT="[poll-report] issue-500/implementation: HEALTHY-UNCONFIRMED — issue-500/implementation: 이상 신호 없음(로그 성장은 확인되지 않음), RUNNING — 손댄 파일 없음; 마지막 도구 호출: Read file1.py (10:01:00 UTC)" python3 on-the-record/monitors/poll_heartbeat_delta.py /tmp/phd_test/state.json 1060
[poll-report] issue-500/implementation: HEALTHY-UNCONFIRMED — issue-500/implementation: 이상 신호 없음(로그 성장은 확인되지 않음), RUNNING — 손댄 파일 없음; 마지막 도구 호출: Read file1.py (10:01:00 UTC)
```
Tick 2 re-emits even though only the activity timestamp changed. derived: the same two-tick sequence run with the state literal reverted to bare `"HEALTHY"` (simulating pre-PR behavior against the identical, unmodified script) — result: tick 2 produced no stdout output (correctly suppressed), confirming the divergence is caused by the rename, not the script. canonical: `on-the-record/monitors/test_poll_heartbeat.py:448-462`'s `_healthy_report()` helper, read directly this turn:
```
def _healthy_report(idx: int, workspace: str = "손댄 파일 없음") -> str:
    """issue #2906: mirrors watchdog.py's real `[poll-report] <key>:
    HEALTHY — <key>: ...
    return (
        f"[poll-report] issue-500/implementation: HEALTHY — "
```
This hand-writes the literal string `"HEALTHY"` into its fixture text rather than calling `watchdog.diagnose_health()`, so it stays fully decoupled from the real state name and continues to pass mechanically after the rename, exercising a string `diagnose_health()` can no longer actually produce. Neither PR #2990's diff, its delivery record's must-not audit, nor its full-repo regression claim (`638 passed`) surfaces this — the drift is between two files, one of which the PR never touches, and the coupling between them is untested. This is a genuine, reproducible operational regression: a running, unremarkable session now emits a `[poll-report]` line on every ~60s poll tick indefinitely instead of once until something actually changes — a full recurrence of the notification-spam issue #2906 fixed, silently reopened by an unrelated rename.

## Why

The task asked me not to trust PR #2990's own claimed results and to audit the diff against the issue's must-not list rather than accept its record at face value. Re-running the four acceptance checks and reading the diff directly in an isolated worktree is what makes the must-not audit independent. Going one step further — grepping the whole tree for every other literal-`"HEALTHY"` consumer instead of stopping once `watchdog.py`/`lifecycle.py`/`spawn.py` (the three files the diff touches) checked out clean — is what surfaced the `poll_heartbeat_delta.py` regression, which is exactly the class of defect an adversarial review exists to catch and that the deliverable's own author had no structural incentive to go looking for outside the three files it edited.

I set `verdict: fail` despite all four acceptance checks passing and every explicit must-not item being honored, because the regression above is real, reproducible against the PR's own unmodified code (see the two derived: reproductions above), and operationally consequential (indefinite notification spam on every healthy session, reopening a previously-fixed issue). Sections 1-4 of the issue's fix are each independently sound on their own must-not/acceptance terms — this is a "changes requested on the whole PR before merge" finding, not a rejection of the four acceptance points.

## What did not work

None — canonical: this session's own tool-call sequence this turn (worktree fetch, four acceptance re-runs, diff-scoped must-not audit, then the wider grep that found the regression, all reported under "What was done" above) — every acceptance check reproduced on first execution in the isolated worktree, no scope-exceeded stop, no alternative-swap, nothing written and then undone. The regression finding was surfaced within the originally-scoped diff-audit step (widening the must-not grep to other consumers of the renamed literal), not a detour outside the assigned verification task.

## Upstream basis

- `watchdog.py` / `lifecycle.py` / `spawn.py` at `34b8b0f4a9b7609b47eb9a99039d0ea000280be5` (PR #2990's head, `issue-2969/silent-failure-audit+test-derivation-bb5cc534`; untracked on this session's own tree, exists only in the `pr-2990-head` worktree fetched this turn) — sha: `34b8b0f4a9b7609b47eb9a99039d0ea000280be5`
- `docs/issue-2969/reports/silent-failure-audit+test-derivation-bb5cc534.md` (untracked) — PR #2990's own delivery record; same worktree, same untracked status as above — read for its claims but not cited as evidence for any acceptance result above — sha: `34b8b0f4a9b7609b47eb9a99039d0ea000280be5`
- `on-the-record/monitors/poll_heartbeat_delta.py` and `on-the-record/monitors/test_poll_heartbeat.py` (pre-existing, untouched by PR #2990, tracked on both `main` and the PR branch; read and executed live this turn) — sha: `34b8b0f4a9b7609b47eb9a99039d0ea000280be5`
- issue #2924 / commit `71167c3a` (read via `git show 71167c3a` from inside the same worktree's own history) for the precedent this PR's macOS-degradation handling follows — sha: `71167c3a194d7471ca0b079c45d4ae2390259643`

## Open findings

1. **`on-the-record/monitors/poll_heartbeat_delta.py:189`'s `state_token == "HEALTHY"` special case never matches after this rename**, silently disabling issue #2906's repeat-suppression for every genuinely healthy session — full reproduction and root-cause citation under "What was done" above (`poll_heartbeat_delta.py`/`test_poll_heartbeat.py` are tracked, pre-existing files on this session's own tree — derived: `ls on-the-record/monitors/poll_heartbeat_delta.py on-the-record/monitors/test_poll_heartbeat.py` — result: both present). Resolution path: update that comparison to `state_token in ("HEALTHY-CONFIRMED", "HEALTHY-UNCONFIRMED")` (mirroring the two-name update `roster_watchdog()`'s own dedup comparison in `watchdog.py` already received in this PR), and replace `on-the-record/monitors/test_poll_heartbeat.py`'s `_healthy_report()` hand-written fixture text with the real new state name (or generate it via `watchdog.diagnose_health()` so a future rename cannot silently decouple the two files again). Should land before PR #2990 merges, or as an immediate same-day follow-up if the operator judges the issue-#2969 fix itself too valuable to hold on this one line.
2. Not independently re-verified: PR #2990's claimed full-repo regression count (`638 passed`, `16 pre-existing failures unchanged`). acceptance: `python3 -m pytest test/test_reconcile_crash_verdict_race.py test/test_workspace_progress_tracking.py -q` — result:
```
23 passed in 0.94s
```
I re-ran the four named acceptance checks plus this pair of directly-touched pre-existing test files, not the entire `test/ tests/` tree, since the task scoped this verification to the issue's named acceptance checks and the must-not audit rather than a full-suite re-run. Residual risk is low: nothing outside the three audited files plus their own test files was touched by this diff, other than the `poll_heartbeat_delta.py` coupling already found by direct grep (Open finding 1) rather than by re-running the full suite.

## Next steps

acceptance: `python3 -m pytest tests/ -k "health_verdict_confirmed_vs_unconfirmed or liveness_pid_reuse or flapping_verdict or destructive_action_requires_consecutive" -q` (fresh combined re-run, executed for this section) — result:
```
23 passed in 0.95s
```
Human/operator decision needed on Open finding 1: hold PR #2990 for the `poll_heartbeat_delta.py` comparison fix plus the `test_poll_heartbeat.py` fixture correction before merging, or merge issue #2969's fix now and track the notification-spam regression as an immediate fast-follow. Either path is acceptable; landing PR #2990 unmodified while treating its own `638 passed` claim as "no regressions found" is not, since this record reproduces one that suite does not detect.

## Rationale for deviations

This session applied the adversarial-review skill's methodology (independent blind re-derivation instead of trusting PR #2990's own claims) throughout "What was done" above without first calling the Skill tool to load it — a miss against the invoke-before-apply obligation. canonical: the Stop hook's own skill-verdict-guard notice this turn (`skill-verdict-guard: zero-invocation ... this session mounted 3 skill(s) ... and invoked none of them via the Skill tool`), received after PR #2999 was already opened — corrected in-session by invoking the skill via the Skill tool (loading `/home/jwjung/skill-registry/skills/adversarial-review/SKILL.md` in full) before amending this record, rather than leaving the record's "applied: invoked" claim inaccurate. Reading the loaded skill confirmed the methodology already followed (fresh-context evaluator, no trust in the builder's own claims, cite specific locations) matches this session's role verifying PR #2990 — no change to the verification's substance or verdict resulted from the late read.

### skill-verdict

- skill-verdict: adversarial-review — applied: invoked; loaded via the Skill tool this turn (`/home/jwjung/skill-registry/skills/adversarial-review/SKILL.md`, in full) — canonical: this session's own audit sequence reported under "What was done" above (fresh-worktree re-derivation of all four acceptance results instead of citing PR #2990's pasted numbers, plus the whole-tree grep for other consumers of the renamed `"HEALTHY"` literal) — that widened grep is what surfaced the `poll_heartbeat_delta.py` regression that neither the PR's diff nor its own record's must-not audit found. Invocation happened after most of that audit work, not before (see "Rationale for deviations" above) — the methodology was applied correctly, the invoke-before-apply ordering was not.
- work-in-english: not-applicable — the assigned task text was in English; this record is authored in English throughout (directive-enforced by the core hook layer regardless of this session's own invocation).
- verify-finding-record: not-applicable — that skill's target path is `docs/issue-<n>/reports/defect-verification.md`, a distinct record kind from this adversarial-review verification record; this session produced no `defect-verification.md` file.
