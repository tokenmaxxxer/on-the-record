---
issue: 2874
role: silent-failure-audit-e7b244cd
author: silent-failure-audit-e7b244cd
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: board.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: lifecycle.py
    sha: same-commit
  - path: watchdog.py
    sha: same-commit
---

# issue-2874 — silent-failure-audit-e7b244cd record

## What was done

CORE_BUILD_NOW=1 was set (spawner env). checked: printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW" — result: CORE_BUILD_NOW=1. So this delivered directly under contract v3 s19a (build-now bypass) — no phase-1 proposal round.

**Root cause, established from the code, not assumed.** `board.session_end_verdict()` (the `normal`/`crashed`/`stalled`/`in-progress` three-way split, issue #132) only ever checked the claude subprocess's own pid (read from the `session-start` event's `detail.pid` in `events.jsonl`). That pid dies at `proc.wait()` inside `_spawn_one()`'s `for line in proc.stdout:` loop tail — normal exit, well before this same wrapper process finishes push/gate/ownership-report/classify/`ledger_write` and appends `session-end`.

canonical: spawn.py:4644-4645 (`rc = proc.wait(); roster_remove(roster_key)`) through spawn.py:4789 (`_append_event(events_path, "session-end", ...)`) — the post-processing tail this window sits inside, read in this session

A poll tick landing in that narrow window observes a dead child pid and no `session-end` yet, and `session_end_verdict()` returned `crashed` — even though the session had already succeeded and, per the issue, already opened its PR mid-stream (`pr-opened` events are appended synchronously as soon as the stream shows them, well before the loop's tail).

canonical: spawn.py:4558 (`_append_event(events_path, "pr-opened", m)`, inside the `for line in proc.stdout:` loop that runs throughout the session, not at its tail) — read in this session

canonical: board.py:1237-1282 (pre-fix) — `if not alive_fn(pid): return "crashed"` was the only signal `session_end_verdict()` consulted once `session-end` had not landed; read in this session before editing

This confirms the issue's own hypothesis precisely: liveness (`_alive(pid)` on the claude subprocess) was being used to answer a question only the session's own terminal record (`session-end` event, not yet written in this window) can answer — and `reconcile()`/`lifecycle._auto_respawn_check()` both consumed that same verdict with no cross-check, while `watchdog.diagnose_health()` (feeding `[poll-report]`) happened to already carry a *second*, independent signal (`pr_number is not None`) that masked the same bug for entries that already had a PR — which is exactly why poll-report read COMPLETED in the same tick reconcile read crashed. This is the identical failure shape issue #224's hunt already found and fixed for `_watch --follow` via a `wrapper_pid` check (the roster entry's own driving/wrapper process, which stays alive through the whole post-processing tail) — that fix was never threaded into `session_end_verdict()` itself.

canonical: events.py:805 (`pid = roster_entry.get("wrapper_pid") if roster_entry else None`), the `_watch --follow` wrapper_pid check (issue #224) this fix threads from — read in this session

**Fix — thread the same precedented `wrapper_pid` signal into `session_end_verdict()` and its three crash-consequential callers** (never widens a lease or a wait; the check is a second *identity* signal, not a longer timer):

- `board.session_end_verdict()` (`board.py:1237-1299`): new optional `wrapper_pid: int | None = None` parameter. When the child pid is dead, `session-end` hasn't landed, and `wrapper_pid` is given and still alive, the verdict is `in-progress` instead of `crashed`. Omitted (default `None`, every pre-existing caller) reproduces yesterday's behavior byte-for-byte — pure addition, proven by `test_verdict_unchanged_when_wrapper_pid_omitted` below.
- `spawn._build_observed()` (`spawn.py:945-973`, feeds `reconcile()`) now passes `entry.get("wrapper_pid")` through.
- `lifecycle._auto_respawn_check()` (`lifecycle.py:484-527`, the function whose call to `_respawn_or_cap()` is what would actually queue a real respawn) now passes `entry.get("wrapper_pid")` through.
- `watchdog.diagnose_health()` (`watchdog.py:216-361`, feeds poll-report's status line) now passes `entry.get("wrapper_pid")` through, and its dead-branch completion check was widened from `verdict == "normal"` to `verdict in ("normal", "in-progress")` — otherwise the newly-possible `in-progress` verdict would still fall through to `DEAD-ERRORED`/`respawn` for entries with no PR yet, reintroducing the same bug for the no-PR case (see "Why").
- `watchdog.roster_watchdog()` (`watchdog.py:1698-1720`): a new reconcile-poll-disagreement print fires when `reconcile()`'s divergence list for a dead entry contains a `next_action == "respawn"` entry in the *same tick* `diagnose_health()` says that entry is a completion — a residual observability net (ledger-deduped, reusing the `dead_health` value already computed this tick) so a future disagreement this specific fix does not happen to cover is reported, not silently resolved by whichever subsystem ran last.

**Verified against the real entry points, not stubs.** New `test/test_reconcile_crash_verdict_race.py` constructs the exact race (a `session-start` event, no `session-end`, a dead recorded pid) and drives `board.session_end_verdict()`, `spawn.reconcile()` fed by the real `spawn._build_expected()`/`_build_observed()`, `spawn._auto_respawn_check` (= `lifecycle._auto_respawn_check`, with `_respawn_or_cap` mocked only at its own boundary to assert call/no-call), and `watchdog.diagnose_health()` — each with an in-flight-completion case (`wrapper_pid` alive) and a genuine-crash counterpart (`wrapper_pid` also dead) side by side.

derived: grep -c "def test_" test/test_reconcile_crash_verdict_race.py -> 9

checked: python3 -m pytest test/test_reconcile_crash_verdict_race.py -q — result:
```
9 passed in 0.89s
```

**Acceptance bullet 1 (before/after verdict line), exercised live against the real `reconcile()` path**, not a stub — a synthetic roster entry for a dead child pid, no `session-end`, matching the issue's own shape (`role=adversarial-review branch=issue-2874/demo`).

derived: python3 script driving spawn.reconcile(spawn._build_expected(entry), spawn._build_observed(...)) against a fixture identical to the one in test_reconcile_crash_verdict_race.py, run twice — once with this issue's diff stashed, once with it applied — result:

```
BEFORE FIX: [{'kind': 'session-crashed', 'detail': 'role=adversarial-review branch=issue-2874/demo: session_verdict=crashed', 'next_action': 'respawn'}]
AFTER FIX:  []
```

**Acceptance bullet 2 (a completed session cannot be queued for respawn), exercised at the real `_auto_respawn_check()` path** (`_respawn_or_cap` mocked only at the boundary that would actually spawn a process).

canonical: test/test_reconcile_crash_verdict_race.py, `test_auto_respawn_check_does_not_respawn_in_flight_completion` and `test_auto_respawn_check_still_respawns_genuine_crash` — read/written in this session; the first proves `_respawn_or_cap` is never called for the in-flight-completion fixture, the second proves it is still called once for the genuine-crash counterpart (wrapper_pid dead too) — respawn keeps working for real crashes.

**Full suite, no regression** — same failing-test set before and after, as sets of test IDs. `test/` collection scope stated explicitly: `pytest .` from the repo root collects more than `pytest test/` (this repo also carries a top-level `tests/` directory with shell-driven suites); the touched files' Python test callers all live under `test/`, and the one `tests/` file that imports any of the touched modules was run separately below.

derived: python3 -m pytest . -q --collect-only (tail) -> 623 tests collected; python3 -m pytest test/ -q --collect-only (tail) -> 468 tests collected

derived: python3 -m pytest test/ -q, run twice (baseline with this issue's diff `git stash`ed, then with it applied) — result:

```
BASELINE: 15 failed, 441 passed, 3 xfailed in 32.09s
WITH FIX: 15 failed, 450 passed, 3 xfailed in 31.56s
```
450 - 441 = 9, exactly the 9 new tests added.

derived: diff of the two runs' sorted `FAILED ...` line sets — result: no diff, the 15 failing test IDs are byte-identical before and after; all 15 are pre-existing network/environment-dependent failures (`fetch 실패 — fatal: 'origin' does not appear to be a git repository` and similar) unrelated to `board.py`/`spawn.py`/`lifecycle.py`/`watchdog.py`'s reconcile/respawn/diagnose_health machinery this diff touches.

checked: python3 -m pytest tests/test_cross_checkout_prune_liveness.py -q — result:
```
14 passed in 0.86s
```

**No overhead increase** — no new subprocess/`gh`/network call anywhere in the diff (the `wrapper_pid` check reuses the same `_alive()` primitive — one extra `os.kill(pid, 0)` syscall, already the codebase's standing liveness check — and the `[reconcile-poll-disagreement]` print reuses `dead_health`, already computed and TTL-cached this tick for the pre-existing `[poll-report]` line).

derived: git diff origin/main HEAD -- board.py spawn.py lifecycle.py watchdog.py | grep -E '^\+' | grep -iE "subprocess\.run|gh pr|gh api|_run_net" — result: no matches

**No return of the retired role axis, plural-catching pattern (issue #2876).**

derived: git diff origin/main -- board.py spawn.py lifecycle.py watchdog.py test/test_reconcile_crash_verdict_race.py | grep -inE '^\+.*\b(role|roles)\b' — result: no matches

**Monitor/watch machinery unbroken and not quieter** — this issue *is* that machinery, so this is the deliverable, not a side check. The fix adds one new print class (`[reconcile-poll-disagreement]`) and narrows exactly one false-positive trigger (`session-crashed`/`DEAD-ERRORED` for a session still finishing its post-processing tail) while leaving every other `[reconcile]`/`[poll-report]`/`[watchdog]` branch, and the genuine-crash path through all of them, covered by the counterpart tests above.

checked: python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_ps_live_reliability.py -q — result:
```
10 passed in 0.88s
```

skill-verdict: silent-failure-audit — applied: invoked; ran the skill's Handled/Silently-Absorbed/Unreachable procedure over this issue's actual subject (the `session_verdict` computation chain), since the "error" here is a misclassification silently flowing downstream, not an exception.

canonical: board.py session_end_verdict() (pre-fix, board.py:1237-1282) — the S-shaped site: a verdict string returned with nothing recording that it might be a fallback guess rather than a confirmed terminal state; traced forward to lifecycle._auto_respawn_check() (lifecycle.py:484-527, pre-fix) acting on it directly with no cross-check, and separately to watchdog.diagnose_health() where the only correcting signal (pr_number) could not reach the respawn call chain at all — read/traced in this session

Checked this delivery's own new code for the same pattern: no new `try`/`except` site was added anywhere in this diff — the fix is additive conditional logic on already-computed values, not new fallible-operation handling.

derived: git diff origin/main -- board.py spawn.py lifecycle.py watchdog.py | grep -E '^\+' | grep -iE "\btry\b|\bexcept\b" — result: no matches

The one residual gap the before-landing hunt found (Open findings below) is a liveness-heuristic false-positive, not a caught-and-discarded exception — outside this skill's catalog, in scope for the hunt instead.

skill-verdict: work-in-english — applied: invoked; new code comments (board.py/lifecycle.py/spawn.py/watchdog.py) were written in Korean to match those files' existing near-100%-Korean comment convention, matching this repo's stated project-convention-conflict rule (follow existing file convention). No project-convention conflict found.

## Why

**Why liveness (`_alive(pid)`) was answering a question only the terminal record can answer, established from the code.** `session_end_verdict()` already checks the terminal record *first* — the `session-end` event scan runs before any pid check at all, unchanged by this fix.

canonical: board.py:1287-1288 (unchanged by this diff) — `if any(ev.get("type") == "session-end" ...): return "normal"` runs before the pid branch — read in this session

The bug was never "liveness instead of the terminal record" in general; it is that the terminal record (`session-end`) had not been *written yet* at the moment a poll tick observed the entry, and in that specific gap `session_end_verdict()` fell back to the *wrong* liveness signal (the already-exited claude subprocess) instead of the *right* one (the still-running wrapper process actually driving that tail to completion).

**Why `diagnose_health()` needed the same `verdict in ("normal", "in-progress")` widening, not just the new `wrapper_pid` parameter.** Threading `wrapper_pid` alone changes `session_end_verdict()`'s return value in this window from `crashed` to `in-progress` — but `diagnose_health()`'s pre-existing completion check only recognized `verdict == "normal"`.

canonical: this session's own test run — `test_diagnose_health_completion_without_a_pr_via_wrapper_pid` failed with `AssertionError: 'DEAD-ERRORED' is not None` the first time it ran, against a `wrapper_pid`-threaded `session_end_verdict()` call with no accompanying widening of `diagnose_health()`'s own condition, before the widening below was added

That failure is proof that the general (no-PR) case would have stayed broken, and that reconcile/poll-report could *still* disagree in general (reconcile silent via `wrapper_pid`, poll-report still shouting `DEAD-ERRORED`) had the fix stopped at `session_end_verdict()` alone. Rejected alternative: leave `diagnose_health()`'s condition as `verdict == "normal"` and rely solely on its `pr_number` fallback for the no-PR case too — rejected because a session with no PR yet (most of a session's own lifetime, and every non-`expects_pr` adhoc spawn) would keep hitting `DEAD-ERRORED`/`respawn` in this exact window regardless, reproducing the issue's own bug by a different route.

**Why `[reconcile-poll-disagreement]` was added on top of the direct fix, rather than treating the direct fix as sufficient.** The issue frames the disagreement itself as information: two subsystems answering the same question differently should be reported, not silently resolved by whichever ran last. The direct `wrapper_pid` fix closes the *specific* window this issue names, but `reconcile()` and `diagnose_health()` still derive their verdicts from separately-assembled inputs (`_build_observed()` vs. `diagnose_health()`'s own `pr_index`/`commit_count` parameters) — a future change to either input path could reopen a disagreement this fix does not anticipate. Rejected alternative: gate `_auto_respawn_check()`'s actual respawn call on `diagnose_health()`'s verdict directly (make reconcile subordinate to poll-report) — rejected because the two are computed from genuinely different data lazily supplied by different call sites in `roster_watchdog()` (`diagnose_health()`'s `dead_report` is TTL-cached and may be several ticks stale; `reconcile()`'s `_build_observed()` is always fresh), so silently preferring one over the other trades "reconcile wins" for "poll-report wins" without addressing the issue's own point that *neither* running-last should decide silently.

canonical: watchdog.py:1672-1697 (the ledger-TTL-gated `dead_health` cache vs. the always-fresh `divergences` computed at watchdog.py:1645 each tick) — read in this session

**Why the fix does not widen the lease or lengthen any wait, per the issue's explicit constraint.** `wrapper_pid` is an *identity* check (is the process driving this session's post-processing tail still alive), evaluated once per tick exactly like the pre-existing child-pid check it supplements — it adds no sleep, no timeout, no lease-expiry change anywhere in this diff.

derived: git diff origin/main HEAD -- board.py spawn.py lifecycle.py watchdog.py | grep -iE "lease|timeout|time\.sleep" — result: no matches

## Upstream basis

- `board.py`, `spawn.py`, `lifecycle.py`, `watchdog.py` — same-commit (this delivery's own fix).
- `test/test_reconcile_crash_verdict_race.py` — same-commit (this delivery's own regression tests).
- `test/test_unrecovered_commit_count.py` — pre-existing; read for the `diagnose_health()`/synthetic-roster-entry test fixture convention this delivery's new test file follows.
- `docs/issue-2749/reports/silent-failure-audit-bbfffc81.md` — pre-existing; read for this record's own citation/derived-command shape.
- `events.py:793-816` (`_watch --follow`'s `wrapper_pid` check, issue #224) — pre-existing; the precedent this fix threads into `session_end_verdict()`, not new machinery.
- `docs/issue-2874/reports/silent-failure-audit-e7b244cd/2026-08-30-hunt-reconcile-crash-verdict-race.md` — same-commit (this delivery's own before-landing warrant-hunt record, committed at 039404b0 ahead of this record).

## Open findings

1. **`wrapper_pid` liveness has no process-identity check — found live by this delivery's own before-landing warrant-hunt.**

canonical: docs/issue-2874/reports/silent-failure-audit-e7b244cd/2026-08-30-hunt-reconcile-crash-verdict-race.md, stance-0 FINDING section — read in this session

`alive_fn(wrapper_pid)` is a bare `os.kill(wrapper_pid, 0)` — it proves some process currently holds that pid number, not that it is the *specific* wrapper that was forked for this roster entry. If the real wrapper dies uncleanly (e.g. SIGKILL) before writing `session-end`, and the OS later reissues that exact pid number to an unrelated process before the roster entry is next observed, `session_end_verdict()` reads `in-progress` for a genuine crash — reproduced directly against `board.session_end_verdict()` and `watchdog.diagnose_health()` in the hunt record, with a control run confirming `wrapper_pid` omitted still correctly returns `crashed`.

Not fixed in this delivery: (a) the identical weakness already exists, unfixed, in the precedent this fix threads from (`_watch --follow`'s own `wrapper_pid` check, `events.py:793-816`, issue #224) — this delivery extends an already-accepted technique to three more callers rather than inventing a new risk class; (b) `_watch --follow` bounds the blast radius with a separate stall-timeout backstop that does not depend on `wrapper_pid` at all, which `reconcile()`/`_auto_respawn_check()`/`diagnose_health()` do not have, and adding one would conflict with this issue's own "do not widen the lease or lengthen a wait" constraint; (c) a real fix needs process-identity verification (e.g. `/proc/<pid>` start-time comparison) that exists nowhere in this codebase yet and is a materially larger design decision than this issue's scope. PID reuse is also not permanent — the next tick after the colliding process itself exits self-corrects back to `crashed` — which bounds but does not eliminate the gap. Recommend a follow-up issue covering both `_watch --follow`'s and this delivery's `wrapper_pid` uses together, since they share the exact same gap.

2. None else — the specific disagreement this issue reports (`session-crashed`/`respawn` from reconcile vs. the poll-report status this issue quotes, in the completed-but-lease-still-valid window) is the one closed by the `wrapper_pid` threading above.

derived: python3 -m pytest test/test_reconcile_crash_verdict_race.py -q — result: 9 passed in 0.89s (proves both directions, in-flight-completion and genuine-crash)

## Next steps

None — `loop_state: landed`.
