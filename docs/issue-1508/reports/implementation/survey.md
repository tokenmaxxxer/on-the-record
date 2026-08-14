# Survey: local-first session observability (issue #1508)

derived: `grep -n "gh \|subprocess.run(\[\"gh\"" spawn.py`

## Signal inventory — wired vs assumed

Per-session health path (`watchdog_check_one` spawn.py:2404, `diagnose_health`
spawn.py:2560):

- log mtime silence (signal 1) — WIRED, local only (spawn.py:2419-2425).
- events.jsonl-derived log content scan: background-delegation phrasing
  (signal 2), structural denied-tool-call count (signal 3) — WIRED, local
  only (spawn.py:2427-2465).
- workspace commit presence (signal 4, `git rev-list --count`) — WIRED,
  local `git` subprocess, not `gh` (spawn.py:2467-2476).
- watcher pid aliveness + identity (`_watcher_looks_real`/`_alive`, signal 5)
  — WIRED, local `/proc` + `os.kill(pid, 0)` (spawn.py:2478-2499).
- watcher heartbeat/log-silence (signal 6, issue #1497-adjacent
  `watcher_armed_at`) — WIRED, local mtime comparison (spawn.py:2500-2521).
- deadlock signature (`_deadlock_signature`, events.jsonl tail) — WIRED,
  local only (spawn.py:2529-2559).

canonical: spawn.py:2404-2524 (`watchdog_check_one` body, read this
session) — no `"gh"` token appears in that range, so the consult caveat
("current wiring unverified") resolves to: all six anomaly signals are
already local-only.

## gh calls actually on the per-session watchdog path

`diagnose_health` (spawn.py:2560) is the one place a live per-session
diagnosis reaches `gh`, and only on one branch:

canonical: spawn.py:2580-2593 (`diagnose_health`, read this session) —
`not alive` (session process dead) calls
`_pr_open_or_merged_for_branch(root, branch)` (spawn.py:1162), which runs
its own `gh pr list --head <branch> --state all --json number,state`
(spawn.py:1165-1166) — one dedicated gh call per dead session per tick,
not routed through the #1498 bulk index.

This is a gap: `_pr_open_or_merged_for_branch` is a PR-state confirmation
(in scope for gh), but it bypasses the #1498 bulk query defined at
gates/closure_sweep.py:91-124 (`_pr_index_all`) that already exists for
the same purpose and rides the #1498 budget/floor/backoff. Every other
roster entry hitting this branch in the same tick repeats its own
per-branch `gh pr list` call instead of sharing one bulk fetch.

## Board-sweep gh calls (separate mechanism, already covered by #1498)

canonical: spawn.py:2866-2955 (`_board_wide_sweep`, read this session) —
this function already gates its three gh-calling signals (spawn-on-pr,
closure-sweep, spawn-coverage) behind #1498's rate-limit floor, sweep
backoff, and `call_budget = 8` (spawn.py:2887, 2897-2898, 2954-2956) — out
of scope for this issue's rework, cited only to distinguish it from the
per-session gap above.

## Direction for the proposal

Thread an optional pre-fetched bulk PR index (from
`_pr_index_all` at gates/closure_sweep.py:91) through `diagnose_health`,
so a caller scanning the whole roster in one tick can fetch the bulk index
once and hand it down rather than letting each dead-entry diagnosis run
its own `gh pr list`. No index supplied (unit tests, standalone calls)
keeps today's per-branch fallback — this is scoping input for the
proposal, not a built or executed change.
