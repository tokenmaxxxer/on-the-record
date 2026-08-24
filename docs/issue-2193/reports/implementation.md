---
issue: 2193
role: implementation
loop_state: landed
upstream:
  - path: watchdog.py:212 (diagnose_health), board.py:1089 (roster_ps), spawn.py:3073 (ensure_pushed call site)
    sha: 855348896e6ce1d80b23720d2f1f307cf9dde210
code_under_review:
  - board.py
  - watchdog.py
  - spawn.py
  - tests/test_spawn_gate_wiring.py
  - tests/test_spawn_observation_recovery.py
type: fix
breaking: none
verdict: pass
---

# issue-2193 — implementation record

## What was done

Investigated the kill mechanism first (issue's "Investigate" section), then addressed the recovery-signal gap it pointed at.

`ensure_pushed()` already exists and already implements the issue's "auto-recovered" option (push branch, open PR if missing).

canonical: relay.py:194-234 (read directly) — docstring "역할이 스스로 push/PR 에 성공했으면 전부 no-op", body pushes then opens PR.

`ensure_pushed()` only runs from inside the same watcher process that ran `proc.wait()` on the spawned child — never from any other process, so a plugin reload that kills that watcher process (process-group teardown) along with the session leaves both `ensure_pushed()` and `roster_remove()` unreached, and the roster entry survives unrecovered.

canonical: spawn.py:3041-3073 (read directly) — `rc = proc.wait()` (3041) -> `roster_remove()` (3042) -> later, same function, `push_result = ensure_pushed(cwd, issue, role)` (3073); both are unreachable if this process's own `proc.wait()` never returns.

Pre-change, `roster_ps()` printed a dead entry once and deleted it, with no PR/commit diagnosis of any kind on that path — matching the issue's "spawn.py ps 는 아무것도 안 보여줬다" symptom.

canonical: `git show 85534889:board.py | sed -n '1089,1110p'` (read directly, before this diff) — the loop calls `_format_roster_row()` then unconditionally `roster_remove()`s every not-alive key; no git/gh call existed there.

Pre-change, `diagnose_health()` only distinguished completion (PR found / verdict normal) from bare `DEAD-ERRORED` — no commit-count signal, so a dead-with-commits entry and a genuinely-errored no-commit entry looked identical.

canonical: `git show 85534889:watchdog.py | sed -n '248,263p'` (read directly) — the `if not alive:` branch reads only `verdict`/`pr_number`, returns `None` or `DEAD-ERRORED`, nothing else.

Change (signal-only side of the issue's either/or acceptance):

- `board.py::_session_commit_count(cwd, before_head, after_head)` — new helper beside `_is_new_commit()`, same landmark, returns the commit count (`git rev-list --count`). Re-exported as `spawn._session_commit_count`.
- `watchdog.py::diagnose_health()` gained optional `commit_count` (default `None`, old callers unaffected). Dead + non-completed + `commit_count > 0` now returns new state `DEAD-UNRECOVERED-COMMITS` (`next_action: "recover-unpushed"`), detail naming branch + count. `commit_count == 0`/omitted keeps old `DEAD-ERRORED`.
- `watchdog.py::roster_watchdog()`'s dead-entry poll-report call site now computes and forwards `commit_count` (same before_head/HEAD landmark `_build_observed()` already reads for `reconcile()`, just counted instead of boolean).
- `board.py::roster_ps()` — right before deleting a dead entry, calls `diagnose_health()` (only if the workspace dir still exists) and prints a `health: DEAD-UNRECOVERED-COMMITS — ...` line when applicable.
- `_format_roster_row()` left untouched — see "What did not work".

## Why

Chose signal-only over auto-recovering by calling `ensure_pushed()` from `roster_ps()`/the watchdog poll, because that would silently start opening PRs from a read-oriented status/poll path — a bigger behavior change than this issue asks for.

canonical: watchdog.py:227-229 (read directly) — `diagnose_health()`'s own docstring: "새 gh/git 호출 타입을 추가하지 않는다(프로포절 제약)". Naming branch + commit count satisfies the acceptance's "or produces a recovery signal" branch without that side effect.

Computed `commit_count` from `(before_head, HEAD)`, not `origin/<branch>..<branch>`, because a dead entry with no PR by definition was never pushed from inside the session — the two counts coincide for this failure mode, and this reuses a landmark already read elsewhere.

canonical: spawn.py:765-768 (`_build_observed()`, read directly) — `after_head = _git_head(work); new_commit = _is_new_commit(work, entry.get("before_head"), after_head)`, the exact landmark reused.

## What did not work

First attempt put the new git/gh calls directly inside `_format_roster_row()`, which broke `tests/test_ps_state_rows.py` with a `FileNotFoundError` from `_pr_open_or_merged_for_branch()`'s `subprocess.run(cwd=root, ...)` against that test's synthetic nonexistent `work` paths.

canonical: `python3 -m pytest tests/test_ps_state_rows.py -q` (first attempt) — result: `4 failed, 1 passed`.

That test file's whole point (issue #1462) is exercising `_format_roster_row()` with synthetic paths and zero real process/network calls — a contract the function's own docstring states.

canonical: board.py:1046-1055 (`_format_roster_row()` docstring, read directly) — "부수효과(roster_remove 등) 없음, 테스트가 실제 프로세스를 띄우지 않고 합성 상태로 직접 부를 수 있는 지점".

Moved the diagnosis into the caller (`roster_ps()`) instead, gated on `Path(work).is_dir()`.

canonical: `python3 -m pytest tests/test_ps_state_rows.py -q` (after the move) — result: `5 passed`.

## Upstream basis

- `spawn.py:3073` / `spawn.py:3041-3042` — the existing single call site of the recovery mechanism the issue's investigation located.
- `relay.py:194` and `gates/recovery_policy.py` — pre-existing recovery machinery this fix deliberately did not duplicate.
- `watchdog.py:212` and `board.py:1089` — the two diagnostic surfaces this fix extends.
- sha: same-commit for all of the above (this record lands in the same commit as the code changes).

## Open findings

Two test failures appear when running the full combined suite (`tests/test_spawn_gate_wiring.py`, `tests/test_spawn_observation_recovery.py`, `tests/test_spawn_board_flows.py`, `tests/test_ps_state_rows.py`), both pre-existing and unrelated to this diff.

canonical: `git stash && python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch -q; git stash pop` — result: `2 failed` on bare HEAD `85534889` with this diff stashed, the identical two assertion failures (CARGO_HOME path mismatch; `[11, 22] != [22]` blocker-list ordering) seen with this diff applied. Neither failing file (relay.py, gates/ci.py, sandbox/muster-cache config) is touched by this diff.

Resolution path: out of this issue's scope; flag for whichever issue owns `_undispositioned_role_prs`/toolchain-cache test stability if either recurs independent of this diff.

## Next steps

None — loop_state is terminal (landed).

## Executed acceptance evidence

Kill-after-commit recovery-signal check (issue #2193's verbatim acceptance): a real subprocess commits inside a real temp git repo, gets killed, is registered as a dead no-PR roster entry, and `spawn.py ps`'s printed output is asserted to contain `DEAD-UNRECOVERED-COMMITS`, the exact commit count (`커밋 1개`), and the branch name.

canonical: `python3 -m pytest tests/test_spawn_observation_recovery.py::KilledMidRunWithCommitIsRecoverable -q` — result: `2 passed`.

Completed-and-pushed regression guard (#2180 misreport): direct `diagnose_health()` calls with a mocked-found PR return `state=None` regardless of `commit_count`, never `DEAD-ERRORED` nor the new state.

canonical: `python3 -m pytest tests/test_spawn_gate_wiring.py::DiagnoseHealth -q` — result: `19 passed`.

Full touched-file regression sweep across all four files that exercise this code path:

canonical: `python3 -m pytest tests/test_spawn_gate_wiring.py tests/test_spawn_observation_recovery.py tests/test_spawn_board_flows.py tests/test_ps_state_rows.py -q` — result: `370 passed, 3 xfailed, 2 xpassed, 2 failed` (the 2 failures are the pre-existing, diff-unrelated ones logged under Open findings; no other regression across all four files).
