---
issue: 2904
role: silent-failure-audit-efd0df1c
author: silent-failure-audit-efd0df1c
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: spawn.py, watchdog.py, test/test_session_completion_heartbeat.py
type: fix
breaking: no
verdict: pass
loop_state: landed
upstream:
  - path: none — CORE_BUILD_NOW=1 was set by the spawner (checked: `printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW"`, result `CORE_BUILD_NOW=1`), so this delivered directly under contract v3 s19a with no phase-1 proposal round to cite.
    sha:
---

# issue-2904 — silent-failure-audit-efd0df1c record

## What was done

canonical: `gh issue view 2904 --repo tokenmaxxxer/on-the-record` (this session, read before starting) — the acceptance criteria and the "establish before building" requirement (why does `poll-report` emit `COMPLETED` for some sessions and not the #2894 verification) came from this read.

**Root cause (established, not assumed).** `poll-report`'s existing `COMPLETED` line lives inside `roster_watchdog()`'s dead-entry scan, which only runs for keys still present in the roster (`for key, e in sorted(d.items())`, watchdog.py). A session that exits normally removes its own roster entry synchronously, in the same process, before that scan ever gets a chance to see it:

```python
        rc = proc.wait()
        roster_remove(roster_key)
    finally:
```
(spawn.py:4792-4794, inside `_spawn_one()`, unconditional on outcome)

and the dead-entry scan that would otherwise print `COMPLETED` is unreachable once the roster is already empty:

```python
    if not d:
        print("돌고 있는 스킬 세션 없음")
        if not anomaly_count:
            print("이상 신호 없음")
        return anomaly_count
```
(watchdog.py:1654-1658, `roster_watchdog()`, this is an early return before the dead-entry loop)

derived: `grep -n "_spawn_one(" spawn.py`, this session — exactly one call site (spawn.py:2782, the CLI `spawn` subcommand dispatch), with `bounded=a.issue is not None`, so every issue-driven spawn (including the #2894 verification session) takes this same self-removing tail. The existing `COMPLETED` label is therefore not a completion signal in general — it is a crash-race fallback that only fires when the *owning process itself* dies before reaching its own `roster_remove()` call. The #2894 session exited cleanly, so it never hit that fallback. Answer to the issue's "establish before building" question: **the signal exists in a form (`_post_session_end_comment()`, lifecycle.py:263, already posts a durable GitHub issue comment naming the PR at the same point in `_spawn_one()`'s tail) but does not reach the heartbeat/Monitor channel at all** — a bridging gap, not a total absence of instrumentation.

**The 23:24–23:32 eight-minute gap is the same defect, not a second one.** `on-the-record/monitors/poll_heartbeat_delta.py` deliberately allows up to 1800s (30 minutes) of full silence when nothing changed and nothing is in the always-emit set:
```python
        last_emit_epoch = int(prev.get("last_emit_epoch", 0) or 0)
        if now - last_emit_epoch >= 1800:
```
(poll_heartbeat_delta.py:180-181) — an 8-minute quiet window is inside that designed allowance, not a violation of the stated 120s cadence (that cadence governs how often the watchdog *runs*, not how often it *prints*; issue #1220's delta-suppression is what makes a due-but-unchanged tick silent by design). Once this fix lands, a completion landing inside that window stops it from being silent — same root cause, one fix, not two.

**Fix.** Added a small durable queue (`spawn.PENDING_COMPLETIONS`, `runs/pending-completions.jsonl`) that `_spawn_one()` writes to at the exact point it already knows the completion fact (issue, skill, session id, PR number, final outcome) — spawn.py:4903-4913, right after the existing `sid = ...` line, guarded by `if issue is not None:`. `roster_watchdog()` drains this queue as the very first thing it does (watchdog.py:1576-1601), *before* the `if not d:` early return, and prints the existing `[poll-report] {key}: COMPLETED — ...` line format so it passes through `poll_heartbeat_delta.py`'s existing `ALWAYS_RE` (which already matches `COMPLETED`) unchanged. No new `gh`/git call, no new polling cadence, no new anomaly weight for a genuine completion (mirrors the existing dead-scan `COMPLETED` line, which also does not increment `anomaly_count`).

**Self-audit finding (silent-failure-audit skill, invoked this session) and fix.** The first version of the write/read functions let `open()`/`fcntl.flock()` raise `OSError` uncaught. On the write side that would have crashed `_spawn_one()`'s completion tail (gate-report/self-trigger-respawn/`session-end` comment) over a disk hiccup on a purely observational side-channel; on the read side, a queue the watchdog could not read would have returned `[]` and looked byte-identical to "nothing completed" — reproducing, inside the very fix for issue #2904, the exact defect class the issue is about. Fixed: `_record_session_completion()` (spawn.py:1048-1070) now catches `OSError` and prints an advisory instead of raising; `_drain_pending_completions()` (spawn.py:1078-1108) now returns `(entries, error)` and `roster_watchdog()` reports a non-`None` error as its own anomaly line (`[poll-report-drain-failed] ...`, watchdog.py:1592-1595) instead of silently returning an empty list.

## Why

The issue's framing ("this is the fourth instance in one night of a check whose clean output is indistinguishable from never having looked") applies at two levels here, and both needed fixing in the same change:

1. The outer defect: a session finishing and "no anomaly this tick" produced the same heartbeat. Fixed by making completion a distinct, always-emitted fact fed from the one place that already knows it (`_spawn_one()`'s own tail), rather than inferred later from roster-entry absence (which cannot work once the entry removes itself).
2. The inner defect (self-audit finding): the queue bridging that fact to the heartbeat could itself fail in a way that reads as "nothing to report." Distinguishing "no completions" from "couldn't check" (`_drain_pending_completions()`'s `(entries, error)` return) is the same principle applied one layer down — a silent `except OSError: return []` here would have been a second copy of the identical failure shape, this time inside the fix itself.

Placement choice: the drain runs before `roster_watchdog()`'s `if not d:` early return specifically because that is the common shape after this fix (a session finishes, removes its own roster entry, and the very next tick sees a fully empty roster) — putting the drain after that return, or inside the `for key, e in sorted(d.items())` loop, would have reproduced the original bug for exactly the case this issue reports.

Alternative considered and rejected: teaching the orchestrator to actively poll for finished sessions each turn (e.g. a directive instruction to check `gh pr list` or scan for new comments). Rejected per the issue's explicit non-goal — that is per-turn overhead paid on every turn to catch an event that already knows when it happened (issue #2135's shape), and it would not fix the underlying gap for any consumer other than the orchestrator's own prompt loop (the Monitor heartbeat itself would still say nothing).

## What did not work

None.

## Upstream basis

No phase-1 proposal exists for this issue — `CORE_BUILD_NOW=1` was set by the spawner (checked: `printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW"`, result `CORE_BUILD_NOW=1`), so contract v3 s19a's build-now bypass applies and this record is the only artifact.

## Open findings

None. derived: `python3 -m pytest test/test_session_completion_heartbeat.py -q`, this session, result: `7 passed` — the write/read hardening found during this session's own silent-failure-audit pass (uncaught `OSError` in the two new fallible sites, see "What was done") landed in the same commit as the feature it was found in, and is exercised by two cases in that file's `PendingCompletionsQueueTest` class (test_write_failure_is_advisory_not_raised, test_read_failure_is_reported_as_error_not_silent_empty).

## Next steps

None — `loop_state: landed`.

## Verification

skill-verdict: silent-failure-audit — applied: invoked; ran the skill's procedure against this change's own two new fallible-operation sites (`_record_session_completion`'s file/lock write, `_drain_pending_completions`'s file/lock read-and-clear) — both were originally Silently-Absorbed-shaped (an uncaught `OSError` on write would abort the caller's remaining tail; a caught-and-swallowed `OSError` on read would return `[]` indistinguishably from a genuinely empty queue) and both are now Handled (write: advisory print, execution continues; read: `(entries, error)` so the caller reports a real anomaly instead of quiet emptiness) — see "What was done" and the two new tests in `test/test_session_completion_heartbeat.py`.
other mounted skills: not triggered (only `silent-failure-audit` was mounted for this session; `work-in-english` guidance applies via core hook enforcement, not a Skill-tool invocation).

Four standing invariants, each executed this session:

1. No return of the retired role axis. derived: `git stash && python3 gates/retirement_count.py > /tmp/retire_before2.txt 2>&1; git stash pop && python3 gates/retirement_count.py > /tmp/retire_after2.txt 2>&1; diff <(sed -E 's/^[a-zA-Z0-9._\/-]+:[0-9]+:/FILE:LINE:/' /tmp/retire_before2.txt) <(sed -E 's/^[a-zA-Z0-9._\/-]+:[0-9]+:/FILE:LINE:/' /tmp/retire_after2.txt)`, this session, result: identical content modulo line-number drift from this diff's own insertions — no new `role`/`roles` token introduced (also checked directly: `git diff | grep -iE '\brole'` → no output).
2. No new bug — failing-test set vs origin/main as sets of names. derived: `python3 -m pytest . -q` run once on `origin/main` (HEAD at `fa52c0c81d3c529e6e39b8e9b9a6c876fc263423`, before any edit) and once after this change, from the repo root both times, result both runs: `17 failed, 665 passed, 3 xfailed` before / `17 failed, 672 passed, 3 xfailed` after (672 = 665 + 7 new tests in `test/test_session_completion_heartbeat.py`); `diff <(sort before-FAILED-names) <(sort after-FAILED-names)` → no output, i.e. the two 17-item failing-test-name sets are identical (all 17 are pre-existing sandbox/network failures, e.g. `fatal: 'origin' does not appear to be a git repository`, unrelated to this change).
3. No overhead increase — a quiet tick stays as quiet as today. derived: this session's own reproduction, `roster_watchdog()` called against a fully-empty roster with an empty completions queue, before and after this change, via `python3 -c "..."` scripts run in this session (both a mocked-dependency call into `watchdog.roster_watchdog()` and, for the delta layer, direct subprocess calls into `on-the-record/monitors/poll_heartbeat_delta.py`) — result before/after: identical stdout (`돌고 있는 스킬 세션 없음` / `이상 신호 없음`, `rc: 0`); a second-tick run of `poll_heartbeat_delta.py` with unchanged input beyond one newly-queued completion emits only the new `[poll-report] ...: COMPLETED` line and nothing else (the prior tick's unchanged `돌고 있는 스킬 세션 없음`/`이상 신호 없음` lines did not re-print).
4. Monitor/watch machinery unbroken and not quieter. derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_reconcile_crash_verdict_race.py on-the-record/monitors/test_poll_heartbeat.py test/test_unrecovered_commit_count.py test/test_session_completion_heartbeat.py -q`, this session, result: `58 passed` (53 pre-existing plus 5, in an earlier pass before the self-audit hardening added 2 more tests to the new file — a final full-suite run reflects `672 passed` overall with all 7 of the new file's tests included); no existing anomaly line's condition or wording was touched — the two edited functions (`_record_session_completion`, `_drain_pending_completions`) and the one new call site in `roster_watchdog()` are additive, and the watchdog-adjacent test files above pass unchanged.
