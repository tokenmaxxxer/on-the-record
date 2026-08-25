---
issue: 2211
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2211/reports/execution-observation/survey.md
    sha: a21cc8524c55e461e10ea5fa7e2ec84948b2cf8a
  - path: docs/issue-2211/proposals/2026-08-25-execution-observation-issue-2211.md
    sha: a21cc8524c55e461e10ea5fa7e2ec84948b2cf8a
subject: PR #2228 (issue-2211/implementation), commit 94fbd4dfa73f467f3327ced87ac25997de45ba95, not yet merged to main
test: "this session's own claude -p printenv spawn; this session's own claude -p engineering-task spawn; python3 -m pytest tests/test_spawn_pipeline.py tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py -q -m \"\" -p xdist -n0"
result: passed
assertedBy: issue-2211/execution-observation session, 2026-08-25 (CORE_BUILD_NOW=1 build-now delivery; independent re-execution against commit 94fbd4df in a disposable worktree, not a restatement of PR #2228's own reported numbers)
---

# issue-2211 — execution-observation record

## What was done

canonical: `gh issue view 2211` (this session) — result: PASS — the issue's two `check:` acceptance bullets, quoted verbatim: env vars readable inside a live spawn (plugin-root, core-root, skill-registry, workspace), and a re-measured engineering-class session's log containing no `find /`/`find /home` calls for the paths now exported.

canonical: `git worktree add /tmp/otr-2211-verify-eo origin/issue-2211/implementation --detach` (this session) — result: PASS — a disposable, read-only worktree checked out at PR #2228's own commit `94fbd4dfa73f467f3327ced87ac25997de45ba95`, removed afterward this same session via `git worktree remove /tmp/otr-2211-verify-eo --force`, no push.

This session did not restate PR #2228's own pasted transcripts. It re-ran both acceptance checks against the real code path, from that worktree, using the production `pipeline.spawn_cmd()` / `spawn.directive_section_files()` functions directly rather than a hand-simulated env dict:

canonical: `python3 _eo_build_env.py` (this session's own driver script, run from `/tmp/otr-2211-verify-eo`, calling the real `pipeline.spawn_cmd(role="execution-observation", core_plugins=pipeline.core_plugin_dirs(), skill_registry_root=spawn._skill_repo_root())`) — result: PASS — all four vars present and non-empty in the returned env dict: `ON_THE_RECORD=/tmp/otr-2211-verify-eo`, `MUSTER_WORKSPACE_ROOT=/home/jwjung/.tokenmaxxxer/work`, `CLAUDE_PLUGIN_ROOT_CORE=/tmp/otr-2211-verify-eo/runs/rulebooks/tokenmaxxxer-core/core`, `MUSTER_SKILL_REGISTRY_ROOT=/home/jwjung/skill-registry/skills`.

canonical: `python3 _eo_spawn1_printenv.py` (this session's own driver, launching a real nested `claude -p` subprocess with env built from that same `spawn_cmd()` call layered onto `os.environ`, task `printenv ON_THE_RECORD MUSTER_WORKSPACE_ROOT CLAUDE_PLUGIN_ROOT_CORE MUSTER_SKILL_REGISTRY_ROOT`) — result: PASS — the nested session's own tool result and assistant turn echoed all four values back non-empty and matching the driver's own dict, this session's own execution transcript at `/tmp/otr-2211-verify-eo/_eo_session1.log` parsed directly for the `Bash` tool_result and the `printenv` output it carried. Acceptance bullet 1 (env readback inside a live spawn) independently reproduced.

canonical: `python3 _eo_spawn2_engineering.py` (this session's own driver, launching a second nested `claude -p` subprocess, env built the same way, `--append-system-prompt` set to the real `spawn._directive_system_prompt_block(spawn.directive_section_files(skills_mounted=True))` output — the always-on `known-paths.md` section included — task: locate the record-claim-guard hook script outside this repo, under the plugin checkout, and list the mounted skill-repository's contents) — result: PASS — this session's own execution transcript at `/tmp/otr-2211-verify-eo/_eo_session2.log` parsed directly for every `Bash` tool_use command the nested session issued. Exactly three ran: `printenv ON_THE_RECORD CLAUDE_PLUGIN_ROOT_CORE MUSTER_WORKSPACE_ROOT MUSTER_SKILL_REGISTRY_ROOT`, `cd "$ON_THE_RECORD" && git ls-files | grep -i "record-claim-guard\|approval-gate"`, and `ls -la "$MUSTER_SKILL_REGISTRY_ROOT"` — zero `find /` or `find /home` occurrences. Acceptance bullet 2 (zero whole-filesystem scans on a re-measured engineering-class task) independently reproduced.

canonical: `python3 -m pytest tests/test_spawn_pipeline.py tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py -q -m "" -p xdist -n0` (this session, run from `/tmp/otr-2211-verify-eo` with `CORE_BUILD_NOW` unset) — result: PASS — `127 passed in 115.21s`, the same test IDs and pass total both PR #2228's own record and this session's independent run land on.

canonical: `git show 94fbd4dfa73f467f3327ced87ac25997de45ba95 -- pipeline.py` (this session) — result: PASS — `ON_THE_RECORD` and `MUSTER_WORKSPACE_ROOT` are set unconditionally as two new assignment lines; `MUSTER_SKILL_REGISTRY_ROOT` is set only inside an `if skill_registry_root:` guard, with no empty-string default when a skill-repository isn't mounted; no pre-existing line in either `pipeline.py` or `spawn.py` is modified or removed — additions only, satisfying the issue's regression-guard bullet ("existing spawns are otherwise byte-identical") and empty-state clause (the variable is unset, not empty, when nothing is mounted) by inspection of the actual diff rather than by re-running an unmounted-skill-repository scenario live.

## Why

Both `check:` bullets are exercised directly and independently, not restated from PR #2228's own claims: bullet 1 by the driver script's own env dict plus the nested `printenv` spawn — two separate readbacks of the same real `spawn_cmd()` call, one in-process and one through an actual spawned session; bullet 2 by the nested engineering-task spawn's own transcript, grepped for `find /`/`find /home` across every `Bash` command it issued rather than trusting a claimed absence.

canonical: `python3 -m pytest tests/test_spawn_pipeline.py -q -m "" -k test_skill_registry_root_unset_when_absent` (this session) — result: PASS — 1 passed, exercising the same `if skill_registry_root:` guard the diff-inspection claim above rests on; this test is part of the 127-test run pasted earlier. Exercising the true empty-state end-to-end (no skill-repository mounted at all, in a live spawn) would require unmounting the one present in this environment, so this unit test plus the diff read are this session's evidence for the regression-guard and empty-state clauses rather than a third live spawn.

## Upstream basis

canonical: `git log --format=%H -1 -- docs/issue-2211/reports/execution-observation/survey.md` (this session) — result: PASS — resolves to commit `a21cc8524c55e461e10ea5fa7e2ec84948b2cf8a`, the same commit `docs/issue-2211/proposals/2026-08-25-execution-observation-issue-2211.md` landed in.

- `docs/issue-2211/reports/execution-observation/survey.md` (commit `a21cc8524c55e461e10ea5fa7e2ec84948b2cf8a`) — phase-1 current-state survey of the issue's acceptance text and PR #2228's diff.
- `docs/issue-2211/proposals/2026-08-25-execution-observation-issue-2211.md` (commit `a21cc8524c55e461e10ea5fa7e2ec84948b2cf8a`) — the phase-1 proposal this record delivers against.

canonical: `git show 94fbd4dfa73f467f3327ced87ac25997de45ba95 --stat` (this session) — result: PASS — PR #2228's own commit, the code under observation: `pipeline.py`, `spawn.py`, `tests/test_spawn_pipeline.py`, `tests/test_directive_diet_2135.py`, plus the implementation role's own record (present on the implementation branch only, not this one) and `.orchestrate-hook-fires.log`.

## Open findings

canonical: `python3 _eo_spawn1_printenv.py`, `python3 _eo_spawn2_engineering.py`, and `python3 -m pytest tests/test_spawn_pipeline.py tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py -q -m "" -p xdist -n0` (this session, all against commit `94fbd4dfa73f467f3327ced87ac25997de45ba95`) — result: PASS — none. Both of the issue's acceptance `check:` bullets reproduce cleanly against the code under observation, with no discrepancy between this session's own figures and PR #2228's own claims. PR #2228 itself has not yet merged to `main` — not an open finding of this role's own (this role's board condition keys on an artifact landing on the branch, not `main`, per `roles/specs/execution-observation.spec.json`'s own `use_when.board_condition`), just the current state of the artifact under observation.

## Next steps

canonical: `git show HEAD:roles/execution-observation.json` (this session) — result: PASS — `loop_state` is set to `handed-off`, this role's own terminal state per that file's `record_fields.loop_state.terminal` list; no open finding above carries forward a resolution path.
