---
code_under_review:
  - on-the-record/hooks/poll-rearm.sh
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/hooks/test_poll_rearm.py
  - on-the-record/monitors/test_poll_heartbeat.py
type: fix
breaking: false
verdict: unverifiable
loop_state: landed
---

canonical: `python3 on-the-record/hooks/test_poll_rearm.py` and `python3 on-the-record/monitors/test_poll_heartbeat.py` (this session's own live run; full output under Acceptance verification below)

## What was done
Added `poll_rearm_validate_root()` to `on-the-record/hooks/poll-rearm.sh`: checks root is a git repo, then that `docs/specs/approvers.md` exists (the on-the-record board marker) — first failure wins, printing one `[monitor-arm-refused] root=<path> check=<git-repo|board-registration>: <detail>` line to stderr and returning 1. Called it at the top of `poll_rearm_arm_if_due()` (shared by `directive.sh` and `stop-poll-rearm.sh`) before any `poll-due` call. Added six hermetic regression tests across the two existing test files covering: non-git root refusal (no artifacts), git-root-without-board refusal, and unchanged arming on a valid board root.

`poll-heartbeat.sh`'s own arm path uses a plain inline git-repo check (not the combined `poll_rearm_validate_root()`) so it composes with #1245's separate board-attachment gate — see the Merge reconciliation section below.

## Why
requirement: northpole req#4 (observability signals must be truthful) — docs/specs/northpole.md. A monitor armed on the wrong root previously produced permanent per-tick "not a git repository" noise instead of one clear refusal, forcing the operator to hand-diagnose an arm-time misconfiguration.

## Upstream
Based on: docs/issue-1275/proposals/monitor-arm-root-validation.md

## Acceptance verification
canonical: `python3 on-the-record/hooks/test_poll_rearm.py` and `python3 on-the-record/monitors/test_poll_heartbeat.py` — this session's own live run, output below
checked: both suites — result: pass

```
$ python3 on-the-record/hooks/test_poll_rearm.py
10/10 passed
$ python3 on-the-record/monitors/test_poll_heartbeat.py
8/8 passed
```

verdict: unverifiable — the acceptance-relevant paths (non-git refusal + no-artifacts, board-marker-missing refusal, board-root unchanged arming) are covered by the hermetic tests above; no live `gh`/watchdog process or real monitor session was exercised, per the issue's own Acceptance which asks for a hermetic test.

canonical: `git log origin/main --oneline -- on-the-record/monitors/poll-heartbeat.sh` and this branch's `git rebase origin/main` conflict output, both read this session
## Merge reconciliation with #1245 (PR #1252, merged to main first)
#1245 (PR #1252, commit c490bc4) landed on main ahead of this branch and added its own separate "skip silently if the target repo is not an on-the-record board" gate at the same spot in `poll-heartbeat.sh`'s arm path that this issue's git-repo/board-registration refusal occupies, conflicting in `on-the-record/monitors/poll-heartbeat.sh` and `on-the-record/monitors/test_poll_heartbeat.py`. Rebased this branch onto `origin/main` (keeps this commit scoped to issue-1275's own files rather than folding in unrelated main-only issue docs) and resolved the conflict.

canonical: `on-the-record/monitors/poll-heartbeat.sh` (post-rebase working tree, read this session)
Composed both to hold in the documented priority order: `ORCHESTRATE_OFF` -> `CHECKOUT`-unresolvable -> #1275 root validation (git-repo check only, loud `[monitor-arm-refused]` refusal + `exit 1`, no artifacts) -> #1245 board gate (silent `poll tick: skipped (target repo is not an on-the-record board)` + `exit 0`, no artifacts) -> alive marker. `poll-heartbeat.sh`'s own arm path now runs a plain inline `git -C "$(pwd -P)" rev-parse --is-inside-work-tree` check (mirroring `poll_rearm_validate_root`'s git-repo branch) instead of calling the combined `poll_rearm_validate_root()`, so a git-repo-but-no-board root keeps #1245's original silent-skip UX rather than #1275's loud refusal message. `poll_rearm_validate_root()` itself in `on-the-record/hooks/poll-rearm.sh` is untouched and still used as-is by `poll_rearm_arm_if_due()` (directive.sh/stop-poll-rearm.sh), which keep the combined loud-refusal behavior for both checks.

canonical: `on-the-record/monitors/test_poll_heartbeat.py` (post-rebase working tree, read this session)
Reconciled the test file: kept both `t_heartbeat_refuses_to_arm_on_non_git_root` (#1275) and `t_heartbeat_skips_attachment_on_non_board_repo` / `t_heartbeat_attaches_on_board_repo` (#1245). The latter two fixtures previously created a target repo directory without `git init`-ing it; under the composed order a non-git fixture now hits #1275's git-repo check first instead of reaching the board-registration check the test intended to exercise, so both fixtures now `git init -q` the target repo before running, matching the realistic case (an actual git checkout missing/carrying `docs/specs/approvers.md`).

canonical: `python3 on-the-record/hooks/test_poll_rearm.py && python3 on-the-record/monitors/test_poll_heartbeat.py` — this session's own live run after the rebase, fenced under Acceptance verification above
Both suites were rerun on the rebased working tree; see that fenced block for the per-suite counts.

## What did not work
None.

## Open findings
None.

## closed_checks
- name: non-git-root-refused-no-artifacts
  code_sha: HEAD (working tree at time of test run)
- name: board-root-unchanged-arming
  code_sha: HEAD (working tree at time of test run)
- name: merge-reconciliation-both-suites-rerun-clean
  code_sha: HEAD (post-rebase working tree with origin/main)
