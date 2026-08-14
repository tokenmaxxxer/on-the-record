---
status: proposed
files:
  - on-the-record/hooks/poll-rearm.sh
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/hooks/test_poll_rearm.py
  - on-the-record/monitors/test_poll_heartbeat.py
---

Skip condition: pure bugfix (scout-directive skip condition) — issue #1275 states `validity-consult-skip: trivial`, and the fix is input validation at an existing entry point fully specified by the issue's Requirements section. No design decision is open; scouting round skipped accordingly (survey.md still written per survey-order-directive).

## Request
A monitor/watchdog armed with `root` = a non-git parent directory (no `-C` given) runs `gh issue list` there via `spawn_coverage`, failing "not a git repository" on every 60s tick forever — permanent benign noise instead of one clear failure at arm time.

## Constraints
- Board-repo arming (git repo + registered board) must be completely unchanged.
- Hermetic tests only (existing fake-spawn.py harnesses), no live `gh`/watchdog process.
- Composes with #1245 (silent no-attach in sessions) without depending on it — this is a distinct, earlier guard at explicit arm time.

## Rationale
Two placements for the validation considered:
1. **Chosen**: validate once, at each arm entry point, before any registration side effect — inside `poll_rearm_arm_if_due()` (shared by `directive.sh` and `stop-poll-rearm.sh`) and at the top of `poll-heartbeat.sh` before its tick loop starts. Both already independently default `root` to `pwd -P` (spawn.py's own `-C` default), so both need the same guard.
2. **Rejected**: push the check down into `spawn.py`'s `watchdog` CLI branch itself (refuse inside `roster_watchdog()`/`main()`). Rejected because the noise the issue describes is arm-time noise — a monitor loop started once and then failing repeatedly — and a single loud arm-time refusal (never entering the loop, never launching the background process at all) is a stronger fix than a per-tick internal refusal that would still be a per-tick check, just relocated. Keeping validation at the shell arm sites also means zero registration artifacts are ever created, matching Acceptance's "absence of registration artifacts asserted."

## What will be done
- Add `poll_rearm_validate_root()` to `on-the-record/hooks/poll-rearm.sh`: checks (a) `git -C "$root" rev-parse --is-inside-work-tree`, then (b) `docs/specs/approvers.md` presence; on first failure, prints one `[monitor-arm-refused] root=<path> check=<git-repo|board-registration>: <detail>` line to stderr and returns 1.
- Call it at the top of `poll_rearm_arm_if_due()`, before the `poll-due` call — a refusal returns 1 immediately, with no `poll-due` call, no nohup watchdog, no log write.
- Call it at the top of `poll-heartbeat.sh`, before the `.orchestrate-monitor-alive` marker touch and before the tick loop starts — a refusal exits the script immediately.
- Add hermetic regression tests to both existing test files: non-git root → refused, `check=git-repo`, no artifacts; git root without `docs/specs/approvers.md` → refused, `check=board-registration`; valid board root → arms unchanged.

## Accumulation
One-off validation function added at two existing call sites (not a per-entry repeated-file pattern like `roles/*.json`) — if more arm entry points appear later, each reuses the same shared `poll_rearm_validate_root()` rather than duplicating the check; no further shared helper is needed beyond that.

## Out of scope
- Issue #1245's silent-attach gating in sessions.
- Any change to `roster_watchdog()`'s scan/anomaly logic.

## How you'll know it worked
`python3 on-the-record/hooks/test_poll_rearm.py` and `python3 on-the-record/monitors/test_poll_heartbeat.py` pass, including the new refusal/board cases.
