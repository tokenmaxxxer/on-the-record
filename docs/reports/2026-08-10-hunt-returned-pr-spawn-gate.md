---
proposal: docs/issue-680/proposals/2026-08-10-returned-pr-spawn-gate.md
---

# Hunt record — returned-pr-spawn-gate

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: NO FINDING
Seed: docs/issue-680/proposals/2026-08-10-returned-pr-spawn-gate.md (proposed write set: spawn.py, test_spawn.py)
cap_seconds: 120
tier: default
diff_stat_lines: ~2 new files, docs-only phase-1 proposal (no code yet)
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:20:00Z

Checked whether the plan's reuse of `gates/ci.py._approved_roles_on_issue`
and the `gh pr list`/`sys.path.insert(gates)` pattern actually holds inside
spawn.py's existing write set, by reading the exact call site it cites
(`require_acceptance_gate` at spawn.py:1012-1035, which already does
`sys.path.insert(gates); import ci as _ci; _ci._approved_roles_on_issue(root, issue)`
today) and the argparse wiring in `main()` (spawn.py:3560-3670,
single flat `ArgumentParser`, not per-subcommand parsers, so a new
`--despite-returned` flag needs exactly one `ap.add_argument(...)` call,
no second parser to touch). Also checked for out-of-file registries that
might need a third file: no ledger-event schema file constrains
`ledger_write()`'s free-form dict (grep for ledger/schema files found
none); `gates/test_hooks_parity.py` only pins `on-the-record/hooks/hooks.json`
against `spawn.self_hosted_hooks()`, which is a PreToolUse hook-injection
concern unrelated to this in-process CLI gate; no gate registry file
(`gates/gates.py` doesn't enumerate a fixed gate list that new gates must
join); `_repo_slug`/`_pr_comments`/`_approvers` all already exist in
spawn.py, no new export needed from `gates/ci.py`.

Found one real gap while looking (the auto-respawn path
`_auto_respawn_check`/`_self_trigger_respawn` -> `_respawn_or_cap` ->
`_spawn_one` at spawn.py:2570-2648 calls `_spawn_one()` directly, bypassing
`main()`'s argparse dispatch entirely, so a gate wired only into
`main()`'s spawn dispatch as the proposal describes would not cover
respawns) — but that gap stays inside spawn.py itself (no external
`.sh`/`.json`/registry file drives auto-respawn; grepped for
`roster_watchdog`/`auto_respawn`/`auto-respawn` in `*.sh`/`*.json`,
no hits), so it is not a third *file* the write set omits, just a second
call site within the same listed file — outside this stance's target
(a path/file the write set doesn't list). No reproduction of a required
third file was found; the reuse plan (gates/ci.py, hooks.json,
gates/gates.py registry, ledger schema) all check out against the
already-listed spawn.py/test_spawn.py write set.
