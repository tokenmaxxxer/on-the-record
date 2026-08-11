---
proposal: docs/issue-742/proposals/confirm-bypasspermissions-baseline.md
---

# Hunt record — confirm-bypasspermissions-baseline

## after-proposal — stance 0: assume the gate just touched is bypassable, find the bypass

Verdict: NO FINDING
Seed: docs/issue-742/reports/implementation/survey.md, docs/issue-742/proposals/confirm-bypasspermissions-baseline.md (docs-only diff)
cap_seconds: 60
tier: size:docs-only
diff_stat_lines: 2 files created (survey.md, proposal), docs-only
started_at: 2026-08-11T06:24:18Z
ended_at: 2026-08-11T06:25:10Z

Grepped spawn.py directly for every `["claude", ...]` subprocess invocation
(`grep -n '\["claude"' spawn.py`) rather than trusting survey.md's line
citations. Found 8 call sites total:

- L326 `ensure_rulebook()` warm-up — builds its own ad hoc `warm` settings
  dict (marketplace registration only), does not call `role_settings()`,
  input is literal `"ok"`. Not real role work, no permissions.allow to be
  inert.
- L584/595/596/603 `update()` — `claude plugin ...` subcommands, no `-p`
  session at all.
- L715 `ensure_installed()` warm-up — also doesn't call `role_settings()`
  (takes settings path as a plain arg); confirmed via
  `grep -n "ensure_installed("` that this function has zero call sites
  anywhere in spawn.py (dead code, not reachable from the spawn CLI path).
- L3344 `_claude_version()` — `claude --version`, not a session.
- L3406 `doctor()` probe — real `claude -p` session but with a throwaway
  temp "probe" plugin and hardcoded `echo ok` task, no `--settings`/
  `role_settings()` involved at all (no permissions.allow object exists
  in this call to be inert or not).
- L3465 `spawn_cmd()` — has `--permission-mode bypassPermissions`
  (survey's central claim).
- L3588 `consult_cmd()` — has `--permission-mode bypassPermissions` too.

Checked the respawn path separately since it's a distinct trigger
(watchdog/self-trigger, not the initial CLI invocation): grepped
`_respawn_or_cap`/`_auto_respawn_check`/`_self_trigger_respawn` and
confirmed both call into `_spawn_one()` (L2619, L2687), which builds its
`cmd` via `spawn_cmd()` at L4468 — same bypassPermissions path, no
separate cmd construction.

Also checked L3883 (`--dry-run` path calling `role_settings()` directly)
— this only prints the settings JSON, never spawns a `claude` process, so
it's not a role-spawn code path at all.

No third call site spawns a real role session outside spawn_cmd()/
consult_cmd(). The survey's "only these two do real role work" claim
holds under direct reading of spawn.py, not just its own citations. No
bypass found for stance 0's target claim.
