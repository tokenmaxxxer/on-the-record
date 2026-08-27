---
issue: 2511
role: silent-failure-audit+observability-explorability-6f5691f7
author: silent-failure-audit+observability-explorability-6f5691f7
loop_state: landed
upstream: []
---

# issue-2511 — silent-failure-audit+observability-explorability-6f5691f7 record

skill-verdict: silent-failure-audit — applied: invoked; audited the new `_halt_condition_cleared()`/`spawn_attempt_sweep()` error paths (spawn.py, roster.py). The audit's trace-forward step (Step 3 of the procedure) found the broad `except Exception: return False` swallowed the *recheck itself* crashing with no signal, indistinguishable from "genuinely still blocked". Fixed by adding a stderr line on that branch before returning the same conservative `False`:
```python
    except Exception as e:
        print(f"[spawn-attempt] recheck 자체가 예외로 실패했다(class={cls!r}): "
              f"{type(e).__name__}: {e} — 조건은 보수적으로 '아직 안 풀림'으로 "
              f"본다.", file=sys.stderr)
        return False
```
canonical: `grep -n -A4 "except Exception as e:" spawn.py | head -5` output (spawn.py `_halt_condition_cleared`, commit 026d3ff2)

skill-verdict: observability-explorability — applied: invoked; asked whether the resolved-and-pruned design still supports ad-hoc post-hoc questions ("which class resolves fastest", "how long did this halt stay live"). Per the skill's rule 1 (retain raw dimensional data behind any panel, not just aggregates), added `class` to the `spawn_attempt_halt_reported` ledger event and `attempted_ts`+`class` to `spawn_attempt_resolved_reported`, so `runs/ledger.jsonl` alone answers those questions without re-parsing `attempt_id` or re-running the classifier offline.
canonical: `grep -n "ledger_write" roster.py | grep -i spawn_attempt` output (roster.py, commit 026d3ff2) — shows both `spawn_attempt_halt_reported` and `spawn_attempt_resolved_reported` ledger_write calls now carrying `"class"`

## What was done

Build-now bypass (`CORE_BUILD_NOW=1`, spawner-set) — delivered directly on this branch, no phase-1 proposal round.

Fixed the watchdog's `[spawn-attempt]` sweep (`roster.spawn_attempt_sweep()`, `roster.py`) replaying a resolved spawn-attempt halt on every tick as if it were still live — issue #2511. Before this change, a `"halted"` outcome's recorded `detail` string was reprinted verbatim, gated only by a 15-minute report-cadence ledger key, never by whether the blocking condition still held:

```python
# roster.py, pre-fix — canonical: git show 96699800:roster.py, lines 494-517
for attempt_id, a in sorted(attempts.items()):
    outcome = outcomes.get(attempt_id)
    if outcome is not None:
        if outcome.get("outcome") != "halted":
            continue  # "session-log": bootstrap succeeded, not our concern
        reason = outcome.get("detail", "")
    ...
    if not _sp.ledger_check_and_stamp(f"spawn-attempt-halt:{attempt_id}", now=now):
        continue
    reported_subjects.add(subject)
    count += 1
    print(f"[spawn-attempt] {subject}: spawn halted pre-workspace: {reason}")
```
canonical: `git show 96699800:roster.py | sed -n '494,517p'` output (pre-fix HEAD of this branch)

Changes landed in commit `026d3ff2` — `spawn.py`, `roster.py`, and a new test file `test/test_spawn_attempt_staleness.py`:

1. `_record_spawn_attempt()` (spawn.py) now also durably records the `cwd` the spawn was invoked with (previously only `issue`/`role`/`pid`/`ts`) — the re-check for two of the five classes needs the repo-root path a halt happened against, and that path is not otherwise recoverable from the halt message alone.
2. `spawn._classify_halt_reason(reason)` (spawn.py) maps a `"halted"` outcome's `detail` string to one of five known failure classes by matching it against the fixed `sys.exit` message templates that actually produce these halts (`board.py`'s requirement-linkage/acceptance-gate checks, `spawn.py`'s ENOSPC/inode capacity check and workspace-origin-mismatch check, `board.py`'s `require_repo_root` `-C` checks) — or `"unknown"` if none match.
3. `spawn._halt_condition_cleared(cls, attempt, reason)` (spawn.py) re-checks that specific class's blocking condition *right now* — see "Why" below for the per-class method and the reason time-alone is never used.
4. `roster.spawn_attempt_sweep()` (roster.py) calls this re-check before ever reprinting a `"halted"` entry. Cleared → a `spawn_attempt_resolved` event is appended once, a one-line `"halt RESOLVED at <time>"` notice prints once, and the entry is pruned on the next `_prune_spawn_attempts()` pass (extended to treat resolved+halted the same as `"session-log"`: no further retention purpose once resolved). Still blocked → the existing halt line prints exactly as before, now carrying the original attempt's timestamp (`attempted at <ISO time>`).
5. `_load_spawn_attempts()` (spawn.py) now returns a third dict, `resolved` (keyed by `attempt_id`, from `spawn_attempt_resolved` events) — both call sites (`roster.spawn_attempt_sweep`, `spawn._prune_spawn_attempts`) updated for the 3-tuple.
6. Observability follow-up (see skill-verdict above): `class` added to the `spawn_attempt_halt_reported` ledger event; `class` + `attempted_ts` added to `spawn_attempt_resolved_reported`.
7. `test/test_spawn_attempt_staleness.py` — per-class classification, per-class re-check (cleared / still-blocked / conservative-on-unparseable), and an end-to-end sweep test reproducing the issue's own live shape (see "Upstream basis" and Open Finding 2).

canonical: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` — result: `25 passed in 0.89s` (item 7's full count)

## Why

**The replay bug's actual mechanism**, cited above: the report gate (`ledger_check_and_stamp`, 15-minute TTL) throttles *how often* a line reprints, but never asks whether the underlying condition is still true. Once a halt's TTL window lapses, the exact same `detail` string prints again — forever, regardless of whether anyone fixed it. Because the watchdog's own poll cadence (`POLL_HEARTBEAT_SLEEP_SECONDS`, default 120s) is far shorter than that 15-minute TTL, a long-blocked halt still surfaces on effectively every heartbeat once the TTL rolls over, exactly as the issue describes.
derived: `grep -n 'sleep_seconds=' on-the-record/monitors/poll-heartbeat.sh` → `sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-120}"`; `grep -n 'RECONCILE_LEDGER_TTL_SEC =' plumbing.py` → `RECONCILE_LEDGER_TTL_SEC = 15 * 60`

**Per-class staleness determination** (acceptance bullet 3) — all five classes use **re-check**, never elapsed-time-alone, because every one of them names a condition that does not resolve itself with the passage of time:

- **requirement-tag** (`이슈 #<n> 가 요구 연결이 없다`): re-fetches the issue body via `gates/requirement_linkage.py`'s `check(root, issue)` (the exact same gh-backed check `board.require_requirement_linkage` used to raise the halt) and treats an empty violation list as cleared. A missing tag does not appear on its own — only a human editing the issue body clears it, so only asking the same question again can detect that.
- **acceptance-format**: same shape, via `gates/acceptance_gate.py`'s `check(root, issue)`.
- **enospc** (disk/inode capacity halt): re-runs `shutil.disk_usage`/`os.statvfs` against the same probed path extracted from the halt message, against the same `MUSTER_MIN_FREE_BYTES`/`MUSTER_MIN_FREE_INODES` thresholds `_spawn_capacity_check` used. Disk fills and frees independently of wall-clock time; a duration-based "it's probably been cleaned up by now" guess could easily fire while the disk is still full.
- **workspace-origin-mismatch**: re-runs `git -C <work> remote get-url origin` against the workspace path parsed out of the halt message and re-compares against the expected origin with the same normalization `issue_workspace()` uses. If the conflicting workspace directory no longer exists at all, the specific conflict that produced the halt cannot recur against that path, so this one case counts as cleared without a live git call — matching the issue's own observed example ("halted on an origin mismatch for a workspace directory that no longer exists").
- **cwd-invalid** (the `-C` class from the issue-2576 fixture, added here as the issue text's task description directed): re-runs the exact three checks `board.require_repo_root()` performs against the attempt's recorded `cwd` — directory exists, is a git repo, and is that repo's own top-level (not a subdirectory) — since a bad `-C` argument is corrected by a human retyping it, not by time passing.
- **unknown** (anything not matching the five fixed message templates): never reported as cleared. If a `sys.exit` message wording ever drifts out of sync with `_HALT_CLASS_PATTERNS`, the safe failure mode is "keeps reporting as before this fix" (the pre-fix behavior), never "silently marks a still-broken spawn resolved."

The must-not this design honors throughout: **no branch ever marks a halt resolved on elapsed time alone**, and every re-check that cannot positively confirm the condition cleared (missing `cwd`, unparseable message, an exception during the check itself) returns `False` (still blocked) — the conservative direction is always toward continuing to report, never toward going quiet on an unconfirmed guess. This is also why the still-blocked path is functionally untouched: the same `ledger_check_and_stamp` cadence, the same per-tick subject dedup, the same message — only now with the attempt's own timestamp appended, satisfying acceptance bullet 2 without changing how loud a genuinely-blocked halt stays.

**Why the live #2576 fixture became a fifth class, not just a validation case**: the task's own live incident (an orchestrator spawn for #2576 halting on `-C 가 존재하지 않는 디렉터리다: tokenmaxxxer/on-the-record`, then succeeding after the argument was corrected, then a later heartbeat still replaying the resolved halt) is exactly the replay bug in the wild, and its blocking condition — does this path exist, is it a repo, is it that repo's root — is re-checkable with the same shape as the other four classes. Treating it as one more entry in `_HALT_CLASS_PATTERNS` rather than a special case kept the mechanism uniform.
canonical: `gh issue view 2511` output (body's 2026-08-26 #2576 incident narrative)

## Upstream basis

None — build-now bypass (`CORE_BUILD_NOW=1`) skipped the phase-1 proposal/survey round for this issue, so no phase-1 proposal or survey artifact was ever created this cycle for this issue's docs tree. The upstream input was the GitHub issue body itself.
canonical: `gh issue view 2511` output (state: OPEN, body containing the Ask/Non-goals/Acceptance sections and the 2026-08-26 #2576 incident narrative this fix uses as its live fixture)

## Open findings

1. **Message-string/regex coupling has no shared source of truth.** `_HALT_CLASS_PATTERNS` (spawn.py) matches literal prefixes of `sys.exit` messages defined independently in `board.py`/`spawn.py`. If either side's wording changes without the other being updated, the affected class silently reclassifies as `"unknown"` and that class's halts permanently fail to ever resolve automatically (falling back to the pre-fix "always still blocked" behavior for that class only — never the unsafe direction, but a maintenance trap with no test that would catch drift in the *production* message strings themselves, since `test/test_spawn_attempt_staleness.py`'s classification tests use copied literal strings rather than triggering the real `sys.exit` call sites). Resolution path: none opened in this session — flagged here as future work; out of scope for this fix's write set.
   derived: `git show 026d3ff2 --stat -- board.py` — result: empty output (board.py not touched by this commit)
2. **The `-C`/cwd-invalid live demonstration substitutes a faithful reproduction for the actual production incident.** This session's `STATE_ROOT` is scoped to an isolated per-session worktree checkout with no `MUSTER_STATE_ROOT` override and no `runs/spawn-attempts.jsonl` of its own.
   derived: `printenv MUSTER_STATE_ROOT` — result: unset; `python3 -c "import spawn; print(spawn.SPAWN_ATTEMPTS_PATH.exists())"` — result: `False`
   so the exact live #2576 spawn-attempts.jsonl entry described in the issue body is not reachable from this session to demonstrate against directly. `SpawnAttemptSweepReplayFixTest::test_live_halt_stops_replaying_once_the_condition_clears` (in `test/test_spawn_attempt_staleness.py`) reproduces the identical message template, the identical class, and the identical fix-then-reheartbeat sequence against a real temporary git repository (not mocked away — its `_git_repo()` helper actually shells out to `git init`), which is the strongest available live-equivalent given that constraint. Resolution path: none needed — documented here so the demonstration's scope is not overstated.
3. **Unrelated pre-existing test failures**, same set before and after this change.
   derived: `git stash -u && python3 -m pytest test/ tests/test_tmp_resource_gc.py -q 2>&1 | tail -3` — result: `15 failed, 267 passed`; `git stash pop`; `python3 -m pytest test/ tests/test_tmp_resource_gc.py -q 2>&1 | tail -3` — result: `15 failed, 292 passed` (292 = 267 baseline-passing + 25 new; the 15 failing test names are byte-identical in both runs)
   Resolution path: none — pre-existing and out of this issue's scope (test/test_spawn_cross_family_skill_selection.py, test/test_spawn_skill_judge_haiku_timeout_overlap.py, test/test_spawn_artifact_skill_pairing.py, test/test_convention_equivalence.py, test/test_local_dependency_env.py — order-dependent flakiness noted elsewhere in repo history, not touched by this diff).

## Next steps

None — loop_state is terminal (`landed`).

canonical: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` — result: `25 passed in 0.89s`
Acceptance requirement met — checked: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` — result: `25 passed`, covering all three acceptance bullets:
- bullet 1 (a cleared halt stops replaying as live) — `SpawnAttemptSweepReplayFixTest::test_live_halt_stops_replaying_once_the_condition_clears`
- bullet 1's must-not (a still-blocked halt keeps reporting) — `SpawnAttemptSweepReplayFixTest::test_still_blocked_halt_keeps_reporting_at_full_volume`
- bullet 2 (attempt timestamp on every reported line) — `SpawnAttemptSweepReplayFixTest::test_report_line_carries_the_original_attempt_timestamp`
- bullet 3 (per-class staleness method + why time-alone can't apply) — documented above in "Why"; enforced in code by every branch of `spawn._halt_condition_cleared` returning `False` (never resolved) on anything short of a positive re-check, covered by `HaltConditionCleared*Test` classes

canonical: `python3 -m pytest test/ tests/test_tmp_resource_gc.py -q` — result: `15 failed, 292 passed`
acceptance: `python3 -m pytest test/ tests/test_tmp_resource_gc.py -q` — result: `15 failed, 292 passed` (15 pre-existing/unrelated per Open Finding 3, 0 regressions, 25 new tests passing)
