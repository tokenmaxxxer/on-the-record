---
code_under_review:
  - on-the-record/monitors/test_poll_heartbeat.py
type: fix
breaking: false
canonical: python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q, executed this session
verdict: pass
loop_state: landed
---

Subject: issue-1477

Scout/survey skipped: pure bugfix (rewrite of three stale test bodies
against an already-landed script contract) — no design decision open;
`poll-heartbeat.sh` itself is out of scope per the issue's requirement 2.

## Summary of work

Rewrote the three tests in `on-the-record/monitors/test_poll_heartbeat.py`
that still asserted the pre-#1245/#1280/#1292 contract:

- `t_heartbeat_refuses_to_arm_on_non_git_root`: previously asserted a
  hard `exit 1` + `[monitor-arm-refused]` stderr on a non-git arm-root.
  The #1292 record (docs/issue-1292/reports/implementation.md, "Summary
  of work" section) records that the #1275 non-git `exit 1` was demoted
  to the same sweep-exclusion/dormancy path #1282 built for the
  non-board case — the tick loop always runs regardless of git status,
  and the alive marker is written unconditionally before the sleep
  loop. Rewritten to assert `rc == 0`, no `[monitor-arm-refused]` text,
  the relocated alive marker present, and the watchdog still invoked on
  a due tick.
- `t_heartbeat_skips_attachment_on_non_board_repo`: previously asserted
  no alive marker / no state file / no watchdog log for a non-board git
  repo. The #1280 record (docs/issue-1280/reports/implementation.md,
  frontmatter section) records that the #1245 non-board `exit 0` gate
  was demoted to an `is_board` flag, the tick loop always runs
  regardless of arm-root board status, and the alive marker write moved
  from `$(pwd -P)/.orchestrate-monitor-alive/alive` to
  `~/.claude/tokenmaxxxer/monitor-alive/<sha256(pwd -P)[:24]>/alive`.
  Rewritten to assert the relocated marker exists, the old repo-local
  marker path never gets recreated, and the watchdog still runs —
  `is_board` now only scopes `spawn.py`'s `_board_wide_sweep_all`
  arm-root inclusion, a `spawn.py`-level concern outside this
  fake-`spawn.py` harness.
- `t_heartbeat_attaches_on_board_repo`: kept its due-tick attach shape —
  the #1245 record (docs/issue-1245/reports/implementation.md, bullet
  list section) notes a board target repo falls through unchanged — but
  updated the marker-location assertion to the #1280-relocated path
  instead of the old `<repo>/.orchestrate-monitor-alive/alive`.

Added a shared `_alive_marker_path(home, arm_root)` helper that mirrors
`poll-heartbeat.sh`'s inline `python3 -c` hash derivation
(`sha256(pwd -P).hexdigest()[:24]`, joined under
`~/.claude/tokenmaxxxer/monitor-alive/`); the formula is recorded in the
#1280 record (docs/issue-1280/reports/implementation.md, bullet list
section) and cross-checked here directly against
`on-the-record/monitors/poll-heartbeat.sh`'s `_alive_dir` computation
(`hashlib.sha256(root.encode("utf-8", "surrogatepass")).hexdigest()[:24]`,
read this session) — same encoding, same truncation, same path join
order.

derived: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q`

```
$ python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q
........                                                                 [100%]
8 passed in 0.97s
```

## Why

canonical: on-the-record/monitors/test_poll_heartbeat.py read this
session (pre-edit) plus the three decision records cited above

Issue #1477: the three tests still asserted the OLD contract (repo-local
`.orchestrate-monitor-alive` marker, hard exit on non-git root,
attachment skip on non-board) while `poll-heartbeat.sh` itself was moved
to the new contract by landed decisions #1245, #1280, #1292 — a standing
red on main that desensitizes suite reading. `poll-heartbeat.sh` was not
touched, per the issue's requirement 2; #1466's tick-header/rotation
changes to the same script (`_poll_watchdog_log_append`,
`POLL_WATCHDOG_LOG_MAX_BYTES`, visible in the script body read this
session) are orthogonal to the marker-location/arm-refusal assertions
rewritten here — no test in this file exercises the watchdog-log
tick-header/rotation surface.

## Upstream basis

docs/issue-1245/reports/implementation.md,
docs/issue-1280/reports/implementation.md,
docs/issue-1292/reports/implementation.md

## What did not work

None.

## Open findings

None.
