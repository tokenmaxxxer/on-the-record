---
name: acceptance-commands
description: >
  One-time-confirmed acceptance/build+use command per target deliverable
  (issue #914 step 2, mechanism a; mirrors #831's remote-preflight setup
  pattern). acceptance-command-real-run-guard.sh re-runs the recorded
  command at commit time whenever a staged acceptance-outcome citation
  names it, and refuses the commit if the actual re-run does not match
  the claimed result (pass or fail).
---

# Acceptance commands — per-target real-run verification

Adding a row here IS the one-time confirmation event (the durable,
git-tracked equivalent of #831's `ledger_write({"event":
"acceptance_command_confirmed", ...})` — a PreToolUse hook has no
access to spawn.py's orchestrator-side `runs/ledger.jsonl`, so the
confirmation lives as a row in this file instead, discoverable the same
way `docs/specs/approvers.md`/`docs/specs/enforcement-boundary.md` rows
already are). `command` must match an `acceptance:` citation's command
text verbatim (after stripping surrounding backticks) for that citation
to be trusted with a pass/fail result claim —
`acceptance-command-real-run-guard.sh` refuses a citation naming a
command with no row here (degrade to `UNMEASURED-with-reason` instead).

| target | command | confirmed |
|---|---|---|
| self | `python3 -m pytest -q gates/ on-the-record/hooks/` | 2026-08-12 (issue #914) |
| gates/test_record_lint.py | `python3 -m pytest gates/test_record_lint.py -q` | 2026-08-12 (issue #1085) |
| gates/test_upstream_finding_channel.py | `python3 -m pytest gates/test_upstream_finding_channel.py on-the-record/hooks/test_upstream_defect_scope_guard.py -q` | 2026-08-13 (issue #1131) |
| ~~interaction-design/playbook/02-... (rulebook checkout)~~ | SUPERSEDED 2026-08-24 (#2141): the command replayed a path inside a retired rulebook checkout (#1955) via `gates/playbook_depth_gate.py`, itself retired in the same sweep — row kept as data, never re-run | 2026-08-13 (issue #1174) |
| on-the-record/hooks/pr-base-guard.sh | `python3 -m pytest tests/test_pr_base_guard.py -v` | 2026-08-14 (issue #1461) |
| tests/test_spawn_observation_recovery.py::Watchdog | `python3 -m pytest 'tests/test_spawn_observation_recovery.py::Watchdog' -q` | 2026-08-24 (#2141 re-record; was tests/test_spawn.py::Watchdog, split by #2105) |
| gates/test_patrol_board.py | `python3 -m pytest gates/test_patrol_board.py -q` | 2026-08-15 (issue #1588) |
| tests/test_verdict_gate.py | `python3 -m pytest tests/test_verdict_gate.py -v` | 2026-08-16 (issue #1669) |
| tests/test_spawn_consult_panel.py::ReconcilePrExpectedMissingRecoveryPolicy | `python3 -m pytest tests/test_spawn_consult_panel.py -k ReconcilePrExpectedMissingRecoveryPolicy -q` | 2026-08-24 (#2141 re-record; was tests/test_spawn.py, split by #2105) |
| tests/test_spawn_consult_panel.py::Reconcile-family | `python3 -m pytest tests/test_spawn_consult_panel.py -k Reconcile -q` | 2026-08-24 (#2141 re-record; was tests/test_spawn.py, split by #2105) |
| self (fast tier) | `python3 -m pytest -q -m "not slow"` | 2026-08-16 (issue #1678) |
| self (slow tier) | `python3 -m pytest -q -m slow` | 2026-08-16 (issue #1678) |
| gates/test_boundary.py::issue-492-reconcile-markers | `python3 -m pytest gates/test_boundary.py -q -k "492 or reconcile"` | 2026-08-16 (issue #1678) |
| tests/test_spawn_directive_assembly.py (excl. pre-existing #1981 env-flake) | `python3 -m pytest tests/test_spawn_directive_assembly.py -q -o addopts="" -k "not test_without_flag_is_byte_identical_to_today"` | 2026-08-22 (issue #1981) |
| gates/test_watch_rearm_registry.py | `python3 -m pytest gates/test_watch_rearm_registry.py -v -o addopts=''` | 2026-08-22 (issue #1975) |
| tests/test_supersession_shape.py | `python3 -m pytest tests/test_supersession_shape.py -q` | 2026-09-02 (issue #3050) |
| gates/probe_supersession_marker.py | `python3 gates/probe_supersession_marker.py` | 2026-09-02 (issue #3050) |
| tests/test_failed_no_commit_reconcile.py | `python3 -m pytest tests/test_failed_no_commit_reconcile.py -q` | 2026-09-02 (issue #3050) |
| tests/ (full suite, -x) | `python3 -m pytest tests/ -q -x` | 2026-09-02 (issue #3050) -- 5 pre-existing failures unrelated to this repo's own board.py/spawn.py/supersession.py population, see docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4.md's "Open findings"; `-x` makes the real exit code non-zero, so cite result: FAIL honestly rather than PASS |
