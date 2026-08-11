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

## before-landing — stance 1: assume this change and another plugin's rule/gate/hook cancel each other out — find the pair

Verdict: NO FINDING
Seed: spawn.py comment-only diff in role_settings() (permissions.allow block, ~lines 490-540); `git diff --stat spawn.py` → 1 file changed, 29 insertions(+), 6 deletions(-)
cap_seconds: 120
tier: size:21-200
diff_stat_lines: 35
started_at: 2026-08-11T06:35:53Z
ended_at: 2026-08-11T06:38:10Z

Confirmed via `git diff spawn.py` that every changed line is a `#`-prefixed
comment line inside `role_settings()`; no non-comment line differs.

Searched for anything that could "cancel out" against or contradict this
comment: (1) hooks under `on-the-record/hooks/*.sh` / `*.py` — none
reference `permissions` at all (`grep -rln permissions on-the-record/hooks/*.sh
on-the-record/hooks/*.py` → empty), so no hook reads or depends on the
`permissions.allow` list the comment describes; (2) `spawn_cmd()`
(spawn.py:3470-3486) already documents `--permission-mode bypassPermissions`
from issue #700 with matching reasoning ("bypassPermissions 는 훅을 끄지
않는다") — consistent with the new comment, not contradictory; (3) gates
that scan spawn.py's literal source text for substrings
(`tests/test_spawn.py:505` haiku-model check, `tests/test_spawn.py:1027`
headless-preamble check, `tests/test_gates.py:1372` concurrency-primitive
regression guard) all target unrelated regions/substrings, none touch the
edited comment block; `gates/test_hooks_parity.py` and
`gates/record_lint.py` don't parse or assert on comment wording at all —
`record_lint.py` only lints `docs/issue-<n>/reports/**` record files, not
spawn.py comments.

Did find one genuinely stale comment: `tests/test_spawn.py`'s
`WebToolPermissionAccess` class docstring (line ~584) still asserts the
now-superseded claim ("headless 세션은 --permission-mode acceptEdits 로
뜨고 답할 사람이 없어서 permissions.allow 에 규칙이 없는 도구는 별개로
거부된다") that spawn.py's corrected comment explicitly retires. But this
is prose in a docstring, not an assertion — `python3 -m pytest
tests/test_spawn.py -k WebToolPermissionAccess -q` → `3 passed,
398 deselected` regardless of the stale wording, and no gate/lint parses
this docstring's content. No command produces a wrong *output* from this
mismatch — it is stale prose sitting next to now-correct prose, not two
rules whose *effects* collide. Per the reproduction bar, this is not a
finding: no runnable command demonstrates wrong behavior traceable to it.
