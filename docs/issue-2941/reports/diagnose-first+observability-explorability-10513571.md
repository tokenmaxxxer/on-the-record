---
issue: 2941
role: diagnose-first+observability-explorability-10513571
author: diagnose-first+observability-explorability-10513571
skills: diagnose-first (skill-repository(c05de12)), observability-explorability (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: spawn.py, watchdog.py, test/test_not_yet_vs_gone.py
type: fix
breaking: no
verdict: pass
loop_state: landed
upstream:
  - path: none — CORE_BUILD_NOW=1 was set by the spawner (checked: `printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW"`, result `CORE_BUILD_NOW=1`), so this delivered directly under contract v3 s19a with no phase-1 proposal round to cite.
    sha: same-commit
---

# issue-2941 — diagnose-first+observability-explorability-10513571 record

canonical: `gh issue view 2941 --repo tokenmaxxxer/on-the-record` (this session, read before starting).

## What was done

Two independent sites in `spawn.py`/`watchdog.py` read "has not appeared yet" as "gone". Both fixed by removing the actual category error, not by adding a guessed delay. Landed at commit 2f46677b (this branch).

**1. reconcile's `pr-expected-missing` (site: `_build_observed()`, spawn.py).** `reconcile()`'s PR-existence signal came from `_pr_open_or_merged_for_branch()` — a fresh, per-entry `gh pr list --head <branch> --state all` call — while the poll-report path (`diagnose_health()`, watchdog.py) reads the same fact from `_board_pr_index()`, a GraphQL-bulk-query-backed board snapshot (issue #2103) built once per tick. These are two different data sources reachable at two different moments; the issue's four confirmed individual cases (PRs #2930, #2934, #2937, the #2919 verification) all showed the `--head`-filtered lookup returning "not found" for a PR that already existed. `_build_observed()` now accepts an optional `pr_index` argument and reads `_pr_state_from_index(pr_index, branch)` when supplied — the identical source poll-report already trusts — falling back to the original per-branch `gh` call only when no index is given. `watchdog.py`'s `roster_watchdog()` now threads its existing per-tick `_poll_pr_index()` (previously built lazily, only when the dead-entry branch first needed it) into the `reconcile()` call, so both judgments read byte-identical data within the same tick. The two CLI call sites that never race a poll-report on the same tick (`roster_reconcile()`, `drive()`) keep their default `pr_index=None` and are behaviorally unchanged.

**2. respawn's absorbed-branch recut (site: `_recut_absorbed_branch()`, spawn.py, called from `_checkout_named_branch()`/`checkout_issue_branch()` and `recut_if_absorbed_cli()`).** The `local_zero` branch ("0 commits ahead of base") read as "absorbed into base" with nothing to tell it apart from "just created, hasn't had time to commit yet" — both produce the identical `rev-list --count base..br == 0` signal. Two live sessions (issue-2920/adversarial-review-2a32a671, issue-2925/independent-verification-1) hit exactly this: a watchdog-observed-crashed misfire triggered `_respawn_or_cap()` → `_spawn_one()` → `checkout_issue_branch()` on a workspace whose session was still alive and working, and the recut deleted its local branch. New helper `_branch_created_age_sec(cwd, br, now=None)` reads the local ref's own reflog for its oldest (creation) entry via `git reflog show --date=unix <br>`, which puts the raw epoch directly in the `@{<epoch>}:` token.

canonical: `git reflog show --date=unix HEAD | tail -3` run against this session's own checkout, this session — result:
```
8c60562c HEAD@{1788162018}: checkout: moving from main to issue-2941/diagnose-first+observability-explorability-10513571
```
— confirms the epoch is embedded directly in the `@{...}` token with `--date=unix`, no separate date-field parsing needed.

`_recut_absorbed_branch()`'s `local_zero` branch now checks this age against `SPAWN_ATTEMPT_GRACE_SEC` (roster.py, 300s, pre-existing — "CLONE_TIMEOUT+NETWORK_TIMEOUT+60", already used elsewhere in spawn.py for the identical class of "how long can a legitimate spawn attempt take before something's wrong" judgment).

canonical: `grep -n "SPAWN_ATTEMPT_GRACE_SEC" spawn.py`, this session — result includes `spawn.py:1838: now - ts < SPAWN_ATTEMPT_GRACE_SEC:` (the existing prune-timing use this fix reuses) alongside the two new uses this session added in `_recut_absorbed_branch()`.

A ref younger than the grace window is left untouched (`git checkout br`, no destructive `-B` reset); a ref at or past the grace window recuts exactly as before. `reflog` absence or parse failure (`_branch_created_age_sec` returns `None`) fails open to today's unconditional-recut behavior, matching this file's existing fail-open convention everywhere else in the same function (`ahead`/`remote_ahead` lookup failures).

derived: `git show 2f46677b --stat -- spawn.py watchdog.py`, this session — result:
```
spawn.py    | 62 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++---
watchdog.py |  9 ++++++++-
2 files changed, 67 insertions(+), 4 deletions(-)
```

**3. Live construction (acceptance check 1).** `test/test_not_yet_vs_gone.py` constructs both required cases against the real functions, no stubs of `_recut_absorbed_branch()`/`_build_observed()`/`reconcile()` themselves. derived: `python3 -m pytest test/test_not_yet_vs_gone.py --collect-only -q`, this session — result:
```
7 tests collected
```
(`RecutNotYetVsGoneTest` x3, `ReconcilePrIndexConsistencyTest` x4).

- `RecutNotYetVsGoneTest.test_freshly_started_branch_is_not_recut`: a real git branch created moments ago, base advanced past it (a second clone pushes a commit to `origin/main` after the branch is cut) — same 0-ahead shape a genuinely absorbed branch has. Asserts the local ref is untouched.
- `RecutNotYetVsGoneTest.test_genuinely_absorbed_branch_is_still_recut`: the identical 0-ahead-of-base construction, with the branch's age faked past the grace window (`mock.patch.object(spawn, "time")`, matching the module's own `time.time()` reference). Asserts the local ref moves to match the new base tip — recut still happens.
- `ReconcilePrIndexConsistencyTest`: constructs the reported race directly — `_pr_open_or_merged_for_branch` mocked to return `None` (the reported GH-index-lag moment) while a `pr_index` already carries the PR (the board's own already-current state) — and shows `_build_observed`/`reconcile` now agree with poll-report; a companion test (`test_still_flags_a_real_missing_pr`) proves a PR genuinely missing from *both* sources still raises `pr-expected-missing` (the must-not: disagreements must keep firing when real, not get silently resolved).

derived: `python3 -m pytest test/test_not_yet_vs_gone.py -q`, this session, against the code landed in commit 2f46677b — result:
```
7 passed
```

derived: `git stash push -- spawn.py watchdog.py && python3 -m pytest test/test_not_yet_vs_gone.py -q; git stash pop`, this session, run against the pre-fix code temporarily restored from `origin/main`'s copy of `spawn.py`/`watchdog.py` — result:
```
5 failed, 2 passed
```
Specifically: `test_freshly_started_branch_is_not_recut` fails (the pre-fix code recuts the fresh branch exactly like an absorbed one); the three `ReconcilePrIndexConsistencyTest` tests that pass `pr_index=` raise `TypeError` (pre-fix `_build_observed()` takes no such parameter); `test_construction_actually_differs` raises `AttributeError` (`_branch_created_age_sec` does not exist pre-fix); the two that pass are `test_genuinely_absorbed_branch_is_still_recut` (pre-fix code always recuts, so the "still recut" assertion holds trivially) and `test_without_index_uses_the_laggy_live_call` (behavior unchanged by design). `git stash pop` restored the fix cleanly afterward — confirmed via `git status --porcelain`, this session, showing `spawn.py`/`watchdog.py` back to a clean tree relative to commit 2f46677b.

**4. Re-derived false-positive count, before/after (acceptance check 2).** The original session's raw `[reconcile-poll-disagreement]` log lines are not retained anywhere reachable from this session.

checked: `grep -rl "reconcile-poll-disagreement" "$MUSTER_WORKSPACE_ROOT"` — unverifiable: no matching file found; the 43-count and the four confirmed PR numbers are the issue body's own report, not something this session can re-read from a raw log file in this environment.

Window bound: rather than a calendar window (unavailable — see above), this session bounds the re-derivation to a fixed synthetic batch of N=10 independently constructed dead-entry `reconcile()` calls, each reproducing the exact identified race (per-branch lookup mocked to return `None`, `pr_index` already holding the PR) — the same mechanism the four confirmed individual cases matched, run against the real `_build_observed()`/`reconcile()` functions, not reasoned about.

derived: a 10-iteration Python loop (this session, ad hoc script, not committed — each iteration builds a fresh throwaway git repo + roster entry and calls `spawn._build_observed(tmp, entry)`, pre-fix signature restored via `git stash push -- spawn.py watchdog.py`, with `_pr_open_or_merged_for_branch` mocked to return `None`) — result:
```
BEFORE: 10/10 pr-expected-missing under the simulated GH-index-lag moment
```

derived: the identical loop re-run after `git stash pop` restored the fix, calling `spawn._build_observed(tmp, entry, pr_index=pr_index)` — result:
```
AFTER: 0/10 pr-expected-missing despite board index already having the PR
```

## Why

**Unify the PR-existence data source rather than add a grace delay (site 1).** A fixed sleep/retry before classification was the issue's explicit must-not without measurement, and this session has no way to safely measure real GitHub search-index propagation lag without spamming the shared production repo with throwaway PRs (rejected — noisy, affects other concurrently-running sessions' PR history and gates). Unifying the source needs no delay and no measured constant at all: it removes the two-readers-of-two-facts structure that produced the disagreement, the same reasoning issue #2103 already used to replace poll-report's own per-branch `gh pr list` loop with the shared board index. Considered and rejected: retrying `_pr_open_or_merged_for_branch()` with backoff before concluding "missing" — this is exactly the "fixed delay without measuring" shape the issue forbids, and it would still leave two independently-lagging sources that could disagree on some other timing. Considered and rejected: switching `_build_observed()` to *always* prefer the board index even without a caller-supplied one — rejected because the two CLI call sites (`roster_reconcile()`, `drive()`) have no per-tick index to share and would need to build one from scratch, adding a new `gh`/board read to call sites the reconcile ADR (#492) explicitly designed to make zero new external calls.

**Reuse `SPAWN_ATTEMPT_GRACE_SEC` rather than invent a new constant (site 2).** The issue explicitly forbids an arbitrary constant "without measuring what delay is actually needed" (citing #2916's mismatched TTL as the cautionary case). `SPAWN_ATTEMPT_GRACE_SEC` already carries a measured, non-arbitrary justification for the identical question — "how long can a legitimate spawn attempt take before its lack of progress means something's wrong" — CLONE_TIMEOUT+NETWORK_TIMEOUT+60 — and spawn.py already reuses it for prune-timing decisions on live-vs-dead spawn attempts. Introducing a second, differently-sized constant for what is the same underlying question would be the kind of unmeasured, uncoordinated multiplicity the repo's own #2916 postmortem is about. Considered and rejected: scanning `/proc/*/cwd` for a live process rooted at the workspace directory, as a liveness-based signal independent of timing — more directly correct in principle, but it cannot fire for the actual respawn-time call path (`checkout_issue_branch()` runs as part of `_spawn_one()`'s own setup, in the *new* attempt's process, checking a branch whose *previous* occupant's liveness is exactly what upstream `_alive()`/`session_end_verdict()` already got wrong — scanning `/proc` here would just re-implement the same identity question one layer down) and it would add a full process-table scan to a call site that already can't cheaply learn "which pid, if any, used to occupy this workspace." The reflog-age signal is local, needs no new syscalls beyond a `git` invocation already payable in the same function, and directly matches the case that occurred (a branch checked out roughly 90 seconds prior, per the issue text).

**`git checkout br` (no `-B`) as the "not yet" outcome, not a full no-op return.** `_checkout_named_branch()`'s docstring already assumes `br` is checked out before calling this helper; returning the checkout's own (already-successful) state rather than fabricating a `CompletedProcess` keeps the return contract (`.returncode` checked by both callers) meaningful without inventing a new sentinel value.

## What did not work

The first draft of `RecutNotYetVsGoneTest.test_genuinely_absorbed_branch_is_still_recut` created both branches at the same commit as `base` with no divergence, so `checkout -B br base` and "leave it alone" produced an identical SHA either way — the test could not actually distinguish "recut ran" from "recut was skipped". Fixed by adding a helper that advances `origin/main` (a second clone pushes a commit after the test's branch is cut), so the branch and base only coincide again *after* a genuine recut — making the recut's effect observable as a SHA change instead of an accidental no-op.

The first attempt at that base-advancing helper pushed via `git push origin HEAD:main` from a second clone without first checking out `main` in that clone — the clone's default checkout landed on the bare remote's original (pre-rename) HEAD symref, an unrelated orphan history, and the push was rejected as non-fast-forward.

checked: `git -C other-clone push -q origin HEAD:main` before the fix — unverifiable: reproduced only inside this session's disposable tmp-dir test fixture, not preserved as a standalone artifact; the fix (`git checkout main` in the second clone before committing) is what landed in `test/test_not_yet_vs_gone.py`'s `_advance_base()`.

## Upstream basis

No phase-1 proposal exists for this issue — `CORE_BUILD_NOW=1` was set by the spawner (checked: `printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW"`, result `CORE_BUILD_NOW=1`), so contract v3 s19a's build-now bypass applies and this record is the only artifact.

## Open findings

**The upstream misclassification that triggers the destructive respawn path in the first place is not fixed by this issue.** `_auto_respawn_check()` (lifecycle.py) calls `board.session_end_verdict()`, which returns `crashed` only when *both* the roster-recorded child pid and `wrapper_pid` fail `_alive()`. For the two live sessions the issue names to have been declared `watchdog-observed-crashed` while genuinely alive and working, either `_alive()` produced a false negative on both pids, or the roster entry's `wrapper_pid` field was absent/stale at the moment of that check — a distinct question from the "not yet vs. gone" category error this issue is about, and this session did not trace it further (out of scope: the issue's own acceptance criteria ask specifically about the `local_zero`/`pr-expected-missing` classifications, not about `_alive()`'s pid-liveness accuracy). This session's fix is a defense-in-depth guard at the destructive-action boundary (`_recut_absorbed_branch()`): regardless of why the upstream crash verdict fired, a branch checked out within the last `SPAWN_ATTEMPT_GRACE_SEC` is no longer destructively recut. Drafted follow-up body:

> **Title:** `session_end_verdict()` declared two live, working sessions `crashed` — trace the false negative in `_alive()`/`wrapper_pid`
>
> Issue #2941 named two sessions (issue-2920/adversarial-review-2a32a671, issue-2925/independent-verification-1) that were declared `watchdog-observed-crashed` and respawned while genuinely alive. #2941's fix stops the resulting destructive branch recut (`_recut_absorbed_branch()`'s new reflog-age guard) but does not explain why `board.session_end_verdict()` returned `crashed` for a live session in the first place — that requires both the roster-recorded child pid and `wrapper_pid` (entry.get("wrapper_pid")) to fail `_alive()` (`os.kill(pid, 0)`) despite the session running. `board.py`'s own docstring for `session_end_verdict()` already names a related PID-reuse identity gap for `wrapper_pid` but does not cover a genuine false negative on a pid that is actually alive. Acceptance: reproduce a live session whose roster entry's `wrapper_pid` is missing or stale at watchdog-check time, and show whether that alone reproduces the false `crashed` verdict, or whether `_alive()` itself needs to be examined for a race on this platform.

**The GraphQL-backed `_board_pr_index()` is assumed, not measured, to be free of the same propagation lag as the `--head`-filtered REST call.** This session's fix is justified by the architectural difference (bulk connection query vs. search-index-backed head filter, per `watchdog.py`'s own `_board_pr_index()` docstring: "single GraphQL board query + delta reads over a cached snapshot") and by removing a live-two-source race entirely rather than by measuring GitHub's actual propagation characteristics for either endpoint — this session did not (and, without spamming the shared production repo with throwaway PRs to time it, could not safely) directly measure the `--head`-filter lag itself. If `_board_pr_index()` turns out to have its own, different lag (e.g., a stale cached snapshot not yet showing a brand-new PR), the same disagreement shape could recur through the opposite direction (reconcile says COMPLETED, poll-report says missing) — not the reported shape, but a related one, and outside this session's ability to test without live GitHub timing data.

## Next steps

None — `loop_state: landed`.

## Verification

derived: `python3 -m pytest test/test_not_yet_vs_gone.py test/test_reconcile_crash_verdict_race.py test/test_branch_skill_field.py test/test_branch_naming_dual_scheme.py test/test_workspace_progress_tracking.py test/test_session_completion_heartbeat.py test/test_unrecovered_commit_count.py -q`, this session, against commit 2f46677b — result:
```
72 passed
```

derived: `timeout 280 python3 -m pytest test/ tests/ -q -p no:cacheprovider`, this session, against commit 2f46677b — result:
```
16 failed, 590 passed, 3 xfailed
```
All 16 failures pre-exist this change: the same module set (test_convention_equivalence, test_local_dependency_env, test_spawn_cross_family_skill_selection, test_spawn_artifact_skill_pairing, test_spawn_skill_judge_haiku_timeout_overlap, tests/test_spawn_gate_wiring.py) was already reported failing by this session's own PostToolUse lint-test-on-edit hook on a plain `Read` of `spawn.py`, before any `Edit` call in this session had run.

checked: `git diff --stat -- on-the-record/hooks/hooks.json` (the file `tests/test_spawn_gate_wiring.py`'s `HooksJsonWiringIsAdditive` suite diffs) — result: empty output. This session never touched `on-the-record/hooks/hooks.json`; that suite's `test_pre_existing_post_tool_use_commands_are_all_still_present` failure (asserts strict growth in PostToolUse command count against this branch's git base ref) is unrelated to this session's diff.

skill-verdict: diagnose-first — applied: invoked; the issue's own text already named the cause and cited exact line numbers, so the full 6-stage procedure was not run (per the skill's own "is the cause already confirmed and agreed?" carve-out) — but the skill's core "no improvement before measurement" discipline was used to reject the issue's likeliest naive fix (a fixed grace sleep/retry) until an existing, already-measured constant (`SPAWN_ATTEMPT_GRACE_SEC`) or a structural cause-removal (unifying the two PR-existence readers) was available, rather than inventing a new number.
skill-verdict: observability-explorability — not-applicable: this issue is a classification-logic defect in existing structured event data (`events.jsonl`, the roster, the board snapshot) — no dashboard, panel, or new fixed-aggregation surface was designed; the skill's rules (retain raw dimensional data behind panels, avoid panel-proliferation) do not have a decision point to apply to a two-function code fix.
other mounted skills: not triggered (work-in-english applies via core hook enforcement, not a Skill-tool invocation).

Four standing invariants (the issue's own list), each checked this session:

1. No revival of the retired role axis. derived: `git show 2f46677b -- spawn.py watchdog.py test/test_not_yet_vs_gone.py | grep -iE '^\+.*\brole\b'`, this session — result: empty output.
2. No new bug. derived: full-suite run above —
```
590 passed
```
— 0 new failures versus the pre-edit baseline (16 pre-existing).
3. No overhead increase. Site 1 *removes* a `gh` call per dead entry per tick when a shared index is available (reuses the already-computed `_poll_pr_index()` instead of making a new per-branch call) — a decrease, not an increase. Site 2 adds exactly one `git reflog show` call, and only inside the already-rare `local_zero` branch of `_recut_absorbed_branch()` (a destructive-recut decision, not a per-tick hot path). derived: `grep -n "_recut_absorbed_branch(cwd\|_checkout_named_branch(cwd" pipeline.py spawn.py`, this session — result: called only from `checkout_issue_branch()`/`_checkout_named_branch()` (once per spawn attempt, not per watchdog tick) and `recut_if_absorbed_cli()` (once per pre-commit/pre-PR gate invocation from within a running session, also not the watchdog's per-tick loop).
4. Monitor/watch machinery unbroken and not quieter. derived: full-suite run above includes `test_session_completion_heartbeat.py`/`test_workspace_progress_tracking.py` —
```
29 passed
```
— exercising `roster_watchdog()`-adjacent paths unchanged. The new "not yet, not gone" print line (spawn.py, site 2's guard) is strictly additive — it fires only on the specific young-ref condition that previously silently recut with no distinguishing message at all.
