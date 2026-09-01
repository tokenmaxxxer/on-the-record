---
issue: 2969
role: silent-failure-audit+test-derivation-bb5cc534
author: silent-failure-audit+test-derivation-bb5cc534
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: watchdog.py, spawn.py, lifecycle.py, test/test_reconcile_crash_verdict_race.py, test/test_workspace_progress_tracking.py, tests/test_health_verdict_confirmed_vs_unconfirmed.py, tests/test_liveness_pid_reuse.py, tests/test_flapping_verdict.py, tests/test_destructive_action_requires_consecutive.py
type: fix
breaking: no
verdict: pass
loop_state: landed
upstream:
  - path: docs/issue-2969/reports/silent-failure-audit+test-derivation-bb5cc534.md
    sha: same-commit
---

# issue-2969 — silent-failure-audit+test-derivation-bb5cc534 record

## What was done

Build-now delivery (CORE_BUILD_NOW=1, contract v3 s19a) — no phase-1 proposal round. Code + tests committed at `0ec5bf96` before this record was written (record-order.md).

1. **HEALTHY split into confirmed vs. unconfirmed.** `watchdog.py`'s `diagnose_health()` residual branch (previously the single `"HEALTHY"` state, reached only after every anomaly check above it declined to fire) now returns `"HEALTHY-CONFIRMED"` when a new helper, `_confirmed_progress_seen()`, observes the session log's byte size grow since the last recorded observation for that key, and `"HEALTHY-UNCONFIRMED"` otherwise (no log, first observation with nothing to compare against, or no growth). Deliberately does not use workspace/log mtime — the field report's own preservation-commit-moved-mtime hypothesis is explicitly unconfirmed, and using mtime here would entangle this fix with that unconfirmed claim. `roster_watchdog()`'s dedup-comparison and the state-name list were updated from the single literal `"HEALTHY"` to both new names — derived: `python3 -m pytest tests/ -k health_verdict_confirmed_vs_unconfirmed -q` — result: `6 passed`.

2. **Liveness pairs pid with process start time.** New `watchdog._paired_liveness(pid, recorded_start_time)` returns `"alive"` only when `_alive()` succeeds *and* the pid's current `/proc/<pid>/stat` start time matches a `start_time` recorded at roster-registration time; `"dead"` when the pid is gone or the start time no longer matches (pid reuse); `"unconfirmed"` when the pairing cannot be established at all (no recorded `start_time` — e.g. a pre-#2969 entry — or `/proc` unavailable, issue #2924's macOS gap). `diagnose_health()` now calls this instead of raw `_sp._alive(pid)`; an `"unconfirmed"` result returns a new `"LIVENESS-UNCONFIRMED"` state (`next_action: "resume-watch"`) before any HEALTHY/DEAD branch is reached. `spawn.py`'s two `roster_register()` call sites (`_early_roster_entry` at the fork-child stub, and the final entry after `Popen()`) now record `"start_time": _proc_start_time(<pid>)` so this pairing has something to compare against for every session spawned from this commit forward — derived: `python3 -m pytest tests/ -k liveness_pid_reuse -q` — result: `6 passed`.

3. **Verdict reversal within a short window reported as its own signal.** New `watchdog._record_verdict_and_check_flapping(key, verdict_state, now, state)` keeps the last 3 `(state, ts)` observations per key; when the 1st and 3rd match, the 2nd differs from both, and the gap between the 2nd and 3rd observation is within `FLAPPING_WINDOW_SEC` (15 minutes), it flags `True`. `diagnose_health()`'s `_diagnosis()` closure attaches this as a `"flapping"` key on every non-completion verdict it returns; `roster_watchdog()` prints a dedicated `[flapping] ...` line (bypassing the per-state dedup ledger, since the point is that two already-reported states contradicted each other) — derived: `python3 -m pytest tests/ -k flapping_verdict -q` — result: `7 passed`.

4. **Destructive action requires consecutive confirmations.** `lifecycle._auto_respawn_check()` (the only place a watchdog verdict automatically triggers a destructive action — `_respawn_or_cap()` → `_spawn_one()`; `roster_kill()` is human-CLI-only, never verdict-triggered, so it needed no change) now requires `RESPAWN_CONSECUTIVE_CONFIRMATIONS` (2) consecutive "crashed" verdicts for the same key, tracked via a `crash_confirms` counter riding on the same `respawn_state.json`-backed `state` dict `_respawn_or_cap()` already persists across ticks, before calling `_respawn_or_cap()`. Any non-"crashed" verdict in between (including "stalled", unaffected — it still short-circuits to its own one-time issue comment before reaching this counter) resets the counter to 0 — derived: `python3 -m pytest tests/ -k destructive_action_requires_consecutive -q` — result: `4 passed`.

All 4 acceptance checks, exactly as written in the issue:
```
$ python3 -m pytest tests/ -k health_verdict_confirmed_vs_unconfirmed -q
6 passed in 0.93s
$ python3 -m pytest tests/ -k liveness_pid_reuse -q
6 passed in 0.87s
$ python3 -m pytest tests/ -k flapping_verdict -q
7 passed in 0.87s
$ python3 -m pytest tests/ -k destructive_action_requires_consecutive -q
4 passed in 0.94s
```

## Why

CORE_BUILD_NOW=1 (spawner-set) authorizes delivery-only per contract v3 s19a — proposal round skipped by design, not a deviation. Per survey-order.md, a full alternatives survey is also skipped: this is a bugfix against a written issue with no open design decision — the issue itself, informed by 3 unanimous consults, already specifies the mechanism for all 4 acceptance points (third-state split, pid+start_time pairing, flapping detection, consecutive-confirmation gating); there was no competing architecture to weigh.

Log-size delta (not mtime) as the confirmed-progress signal: chosen specifically because the field report's own working hypothesis was that a workspace-preservation commit moved mtime and was misread as growth. Reusing the session's own transcript log's actual byte count sidesteps the mtime dispute entirely rather than resolving it, matching the issue's must-not ("do not claim mtime was the confirmed root cause... it is not established") — derived: `grep -n mtime watchdog.py` — result: the only `mtime` references in the file are inside pre-existing, untouched anomaly checks (signal 1's `log_path.stat().st_mtime` and signal 6's watcher-silence check); `_confirmed_progress_seen()` itself contains no `mtime` reference, only `.stat().st_size`.

Consecutive-confirmation counter placed on the existing `respawn_state.json`-backed dict (not a new state file) because `_respawn_or_cap()` already reads/writes `state[key]` for `attempts`/`total_attempts`/`fingerprint` — colocating `crash_confirms` in the same dict avoids adding a second persistence boundary. Rejected alternative: a separate `watchdog_state.json`-keyed counter, discarded because that dict is already used for `_confirmed_progress_seen()`'s log-size tracking and `_record_verdict_and_check_flapping()`'s history (pure observation bookkeeping), and this gate's counter is specifically the "about to act on it" state the issue wants kept distinct — derived: `git show 0ec5bf96:lifecycle.py | sed -n '520,524p'`:
```
    confirm_prior = state.get(key, {})
    if verdict != "crashed":
        if confirm_prior.get("crash_confirms"):
            state[key] = {**confirm_prior, "crash_confirms": 0}
            _sp._respawn_state_save(state)
```

## Skill application

**silent-failure-audit** (invoked via Skill tool) — Step 1 enumerated the 3 fallible sites touched: `_paired_liveness()`'s call into `_proc_start_time()` (pre-existing, catches `FileNotFoundError`/`ProcessLookupError`/`PermissionError`/`OSError` reading `/proc/<pid>/stat`, returns `None`), `_confirmed_progress_seen()`'s `except OSError: return False` on `log_path.stat()`, and the (unchanged) `_sp._alive()` raw `os.kill(pid, 0)` guard. Step 2 classification: both `None`/`False` returns are **Handled**, not Silently Absorbed — `_paired_liveness()` maps a `None` start-time read directly to its own `"unconfirmed"` branch (a distinct, printed state), and `_confirmed_progress_seen()`'s `False` on a stat failure lands in the already-safe `"HEALTHY-UNCONFIRMED"` branch, not a false `"HEALTHY-CONFIRMED"` claim — in both cases the failure demotes to the cautious verdict the issue mandates, it does not get swallowed into a confident-sounding one. Step 3 forward trace found no downstream consequence worth naming as a table row: neither catch site can produce "continues as if succeeded" — canonical: `watchdog.py` `_paired_liveness()`/`_confirmed_progress_seen()`/`_proc_start_time()` read directly this session (see diff in "What was done").

**test-derivation** (invoked via Skill tool) — Step 1 scope gate: the issue's own Acceptance section supplied 4 written, command-shaped criteria (satisfied). Step 3a risk classification: acceptance checks 2 (liveness pairing) and 4 (destructive-action gating) are **High** (issue names a real incident: "two live sessions were killed in error" trusting a single verdict) — full EP/BVA derivation applied. Checks 1 (HEALTHY split) and 3 (flapping) are **Medium** (user/operator-facing diagnostic correctness, no direct destructive consequence on their own) — GWT scenarios plus a named state model, summary depth.

Traceability matrix:

| Acceptance criterion | Risk | Route | Partitions/states exercised | Test file | Result |
|---|---|---|---|---|---|
| HEALTHY splits into confirmed/unconfirmed | Medium | state-transition | first-observation, growth-arrives, no-growth, growth-then-stops, missing-log, empty-state (dead pid) | `tests/test_health_verdict_confirmed_vs_unconfirmed.py` | derived: `python3 -m pytest tests/ -k health_verdict_confirmed_vs_unconfirmed -q` — result: `6 passed` |
| liveness pairs pid+start_time, demotes when unconfirmable | High | EP (5 classes, 5/5 = 100% coverage) | dead; alive+match; alive+mismatch(reuse); alive+no-recorded-start; alive+unreadable-current-start | `tests/test_liveness_pid_reuse.py` | derived: `python3 -m pytest tests/ -k liveness_pid_reuse -q` — result: `6 passed` |
| verdict reversal within short window flags | Medium | state-transition (3-observation ring buffer) | <3 observations, A-B-A within window, A-B-A outside window, A-A-A stable, A-B-C no reversal, independent keys | `tests/test_flapping_verdict.py` | derived: `python3 -m pytest tests/ -k flapping_verdict -q` — result: `7 passed` |
| destructive action needs consecutive confirmations | High | BVA on the confirmation counter | N-1 confirmations (below boundary), N confirmations (at boundary), counter persists via shared state dict, non-crash verdict resets streak | `tests/test_destructive_action_requires_consecutive.py` | derived: `python3 -m pytest tests/ -k destructive_action_requires_consecutive -q` — result: `4 passed` |

Residual (out of these techniques' scope): pairwise/t-way and decision-table techniques do not apply — no requirement here combines 3+ independent parameters or multi-condition business rules. MC/DC does not apply — no safety-critical Boolean decision inside a single conditional. Non-functional dimensions (performance of the per-tick stat()/`/proc` reads under real production tick volume, concurrent-tick races on the shared `respawn_state.json`) are outside these techniques' scope and untouched by this slice — the existing `_roster_locked()`/atomic-replace patterns this change rides on are unchanged.

## Upstream basis

None — this is the first record for this issue; the issue's own Acceptance section (`gh issue view 2969`, read this session) is the sole upstream input, cited inline throughout "What was done"/"Why" above.

## Acceptance verification

canonical: this session's own executed pytest runs, reproduced together —

```
$ python3 -m pytest tests/ -k health_verdict_confirmed_vs_unconfirmed -q
6 passed in 0.93s
$ python3 -m pytest tests/ -k liveness_pid_reuse -q
6 passed in 0.87s
$ python3 -m pytest tests/ -k flapping_verdict -q
7 passed in 0.87s
$ python3 -m pytest tests/ -k destructive_action_requires_consecutive -q
4 passed in 0.94s
```

Full-repo regression, same session — derived: `python3 -m pytest test/ tests/ -q -m "not slow"` on the pre-change tree (`git stash -u`) then the post-change tree (`git stash pop`) — result: `16 failed, 615 passed, 3 xfailed` before, `16 failed, 638 passed, 3 xfailed` after (638 - 615 = 23, matching the 6+6+7+4 = 23 new test methods added); the same 16 test IDs fail on both trees (sampled 6 of them individually against the clean tree — result: identical failures, all network-git-fetch-dependent or pre-existing drift, e.g. `test/test_convention_equivalence.py`, `test/test_spawn_cross_family_skill_selection.py`, `test/test_spawn_artifact_skill_pairing.py`, `test/test_spawn_skill_judge_haiku_timeout_overlap.py`, `tests/test_spawn_gate_wiring.py`, `test/test_local_dependency_env.py` — this sandboxed checkout's `origin` remote/hooks.json state predates and is unrelated to this change). Zero regressions.

Two pre-existing tests were updated to match the new, intentional contract rather than the old one this issue targets for removal: `test/test_reconcile_crash_verdict_race.py`'s `test_auto_respawn_check_still_respawns_genuine_crash` now calls `_auto_respawn_check()` `RESPAWN_CONSECUTIVE_CONFIRMATIONS` times before asserting `_respawn_or_cap` was called (previously asserted a single call reached it — the exact single-snapshot shape acceptance check 4 requires removing); `test/test_workspace_progress_tracking.py`'s `DiagnoseHealthIncludesWorkspaceSummaryTest` now supplies a real `start_time` (so its live-pid entry still reaches the healthy path) and expects `"HEALTHY-UNCONFIRMED"` (its fixture entry has `"log": None`, so growth can never be confirmed — this is the correct new answer, not a regression) — derived: `python3 -m pytest test/test_reconcile_crash_verdict_race.py test/test_workspace_progress_tracking.py -q` — result: `23 passed`.

Syntax check — derived: `python3 -m py_compile watchdog.py spawn.py lifecycle.py` — result: clean (exit 0, no output).

## must not: verification

- Did not resolve an unconfirmed liveness state by guessing in either direction: `_paired_liveness()` returning `"unconfirmed"` routes to a dedicated `"LIVENESS-UNCONFIRMED"` / `next_action: "resume-watch"` return, before any HEALTHY or DEAD-* branch — canonical: `watchdog.py` `diagnose_health()`, the `if liveness == "unconfirmed":` block placed immediately after the `_paired_liveness()` call and before the `if liveness == "dead":` branch — derived: `python3 -m pytest tests/ -k liveness_pid_reuse -q` (includes `test_liveness_pid_reuse_diagnose_health_reports_third_state_not_healthy_or_dead`) — result: `6 passed`.
- Did not remove or weaken `DEAD-UNRECOVERED-COMMITS`/`DEAD-REMOTE-STATE-UNKNOWN`/`STALLED-*`/the `subagent_in_flight` guard — derived: `git show 0ec5bf96 -- watchdog.py | grep -c '^-'` — result: `5` (the diff removes exactly 5 lines: the old `alive =`/`if not alive:` header, the old single-`HEALTHY` return, and the old `!= "HEALTHY"` dedup comparison — none inside the DEAD-*/STALLED-* branch bodies); `subagent_in_flight` lives in `trajectory_analyzer.py` — derived: `git show 0ec5bf96 --stat | grep trajectory_analyzer` — result: no output (file not in this commit's diff).
- Did not make any advisory sub-state (`STALLED-FLAT-PROGRESS`, `STALLED-HEARTBEAT-ONLY`) newly capable of reaching kill/refuse/gate-block: neither branch's `next_action` was edited (still `"resume-watch"` — untouched lines, confirmed by the same 5-line-removed diff above); the new `"flapping"` flag is attached uniformly to every non-completion verdict via `_diagnosis()` and only changes what gets *printed*, never `next_action`.
- Did not claim mtime was the confirmed root cause of the reported misdiagnosis: `_confirmed_progress_seen()` uses `log_path.stat().st_size` (byte count), never `st_mtime` — derived: `grep -n mtime watchdog.py` — result: as cited in "Why" above, no match inside that function; the docstring explicitly names the mtime hypothesis "미확정"(unconfirmed) rather than asserting it.
- No kill or respawn triggered by a single verdict snapshot: the only automatic (non-CLI) destructive path is `_auto_respawn_check()` → `_respawn_or_cap()`, now gated on `RESPAWN_CONSECUTIVE_CONFIRMATIONS` — derived: `python3 -m pytest tests/ -k destructive_action_requires_consecutive -q` (includes `test_destructive_action_requires_consecutive_below_threshold_never_respawns`) — result: `4 passed`. `roster_kill()` remains human-CLI-only — derived: `grep -n "roster_kill(" *.py | grep -v test` — result: only the `def` itself (`lifecycle.py`) and one call site inside the CLI subcommand dispatch (`spawn.py`).

## What did not work

None — no scope-exceeded stop, no alternative-swap from an approved proposal (none existed under the build-now bypass), nothing written and then undone. One in-flight self-correction during derivation, not a deviation from delivered scope: the flapping window was initially measured from the first-ever observation of a state to its return (`t3 - t1`), which a test caught immediately (`test_flapping_verdict_reversal_within_window_flags` failed on first run — derived: `python3 -m pytest tests/test_flapping_verdict.py -q` at that point in the session — result: `1 failed, 6 passed`) — corrected to measure from when the verdict left that state to when it returned (`t3 - t2`), matching "reverses within a short window" as a round-trip duration rather than a from-first-sighting duration; fixed before this record was written, so the delivered code and the committed test both reflect the corrected version — derived: `python3 -m pytest tests/test_flapping_verdict.py -q` (post-fix) — result: `7 passed`.

## Open findings

None.

## Next steps

None — canonical: this record's own frontmatter `loop_state: landed` field, set in this same commit. A residual, explicitly out-of-scope item for a future issue: `_confirmed_progress_seen()`'s log-size tracking and `_record_verdict_and_check_flapping()`'s history both key off the roster `key` string, which is reused across respawns of the same `issue/skill` slot — a respawned session's first tick could, in principle, read the prior generation's last-seen log size or verdict history if the old key is not yet evicted from `runs/watchdog_state.json`. This is the same shape `roster_watchdog()`'s existing `reported_terminal` flag already handles by scoping to `{key}:{pid}` instead of bare `key` for its own terminal-state dedup — derived: `grep -n reported_terminal watchdog.py` — result: `terminal_key = f"{key}:{e.get('pid', 0)}:reported_terminal"`. Extending that same `pid`-scoping to the two new state-store keys this issue adds was judged out of this delivery's frozen scope — the issue's 4 acceptance checks pass without it, and the pre-existing `dead_report`/`offset` state-store keys already share this same bare-`key` reuse-window property, so this is not a new problem this change introduces, just one it does not close.

skill-verdict: silent-failure-audit — applied: invoked; enumerated/classified/traced the 3 fallible sites in `_paired_liveness()`/`_confirmed_progress_seen()`/`_proc_start_time()` (see Skill application above)
skill-verdict: test-derivation — applied: invoked; derived the 4 acceptance-criterion test files via GWT + risk-classified EP/BVA/state-transition depth (see Skill application / traceability matrix above)
other mounted skills: not triggered (work-in-english is directive-only, enforced by the core hook layer, not something this session invoked via the Skill tool)
