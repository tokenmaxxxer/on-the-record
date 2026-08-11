---
name: acceptance-commands
description: >
  One-time-confirmed acceptance/build+use command per target deliverable
  (issue #914 step 2, mechanism a; mirrors #831's remote-preflight setup
  pattern). acceptance-command-real-run-guard.sh re-runs the recorded
  command at commit time whenever a staged `acceptance: <command> —
  result: PASS|FAIL` citation names it, and refuses the commit if the
  actual re-run does not match the claimed result.
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
to be trusted with a `result: PASS`/`result: FAIL` claim —
`acceptance-command-real-run-guard.sh` refuses a citation naming a
command with no row here (degrade to `UNMEASURED-with-reason` instead).

| target | command | confirmed |
|---|---|---|
| self | `python3 -m pytest -q gates/ on-the-record/hooks/` | 2026-08-12 (issue #914) |
