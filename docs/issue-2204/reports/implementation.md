---
issue: 2204
role: implementation
loop_state: landed
upstream:
  - path: docs/handbooks/spawn-directive-assembly.md
    sha: 6d58cdf7faec1eaec6709c1a12386efbeef336f8
  - path: docs/decisions/2026-08-21-single-enforcement-surface.md
    sha: 0b85b5b670a39146f6d2cb1923abe9b905a357d6
code_under_review:
  - pipeline.py
  - spawn.py
  - tests/test_directive_diet_2135.py
  - tests/test_spawn_directive_assembly.py
  - tests/test_spawn_observation_recovery.py
type: perf
breaking: false
verdict: pass
---

# issue-2204 — implementation record

## What was done

CORE_BUILD_NOW=1 build-now bypass — delivered directly on this branch, no
phase-1 proposal round.

Scout, before any code change: where do the sequential Read calls the
issue measured actually originate.
canonical: read on-the-record/hooks/hooks.json (only wires
self-update.sh to SessionStart, no reminder-emitting hook in this repo)
and spawn.py's DIRECTIVE_DIR / directive_section_files() /
materialize_directive_sections() definitions

Two sources exist:
- `tokenmaxxxer-core`'s `core/hooks/directive.sh` SessionStart hook, which
  prints a "Read `<path>` NOW" instruction pointing at a ~134-line
  `session-protocol.md`.
derived: git -C ~/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core rev-parse --show-toplevel — its own .git, a separate repository from this one, pulled by core_plugin_dirs() in pipeline.py
- On-the-record's own `spawn.py`: `directive_section_files()` /
  `materialize_directive_sections()` (issue #2135's index+sections diet)
  write `.on-the-record/directive/*.md` into the spawned workspace, and
  the assembled stdin task text pointed at each file with an inline "Read
  `<file>` when `<condition>`" trigger line (pre-change:
  issue-preamble-index around spawn.py line 2461,
  `_checkpoint_index_block` around spawn.py line 1857,
  skill-obligations-index around spawn.py line 2556).

Only the second source sits inside this repo's write set — the first is a
separate git repository, out of scope for this PR the same way
`docs/handbooks/spawn-directive-assembly.md` already scoped the sibling
`directive.sh`/`CORE_BUILD_NOW` mechanism out of on-the-record edits (see
"Open findings" below for the resulting acceptance-check gap).

Fixed the in-repo half in `pipeline.py`/`spawn.py`:

1. `pipeline.py:spawn_cmd()` gained a new `append_system_prompt: str |
   None` parameter; when non-empty it appends `--append-system-prompt
   <content>` to the assembled `claude -p` argv.
2. `spawn.py` gained `_directive_system_prompt_block(files)` (joins the
   on-demand section bodies `directive_section_files()` already computes
   into one string) and wired it into the `spawn_cmd()` call inside
   `_spawn_one()` as `append_system_prompt=...`.
   `materialize_directive_sections()` is unchanged — the workspace copy
   under `.on-the-record/directive/` still gets written, for later human
   inspection.
3. Removed the three inline "Read `<file>` when `<condition>`" pointer
   blocks (issue-preamble index, `_checkpoint_index_block`,
   skill-obligations index) — their actionable, non-pointer content stays
   inline (완료의 정의 one-liner, record-skeleton line, checkpoint wait
   command + exit codes, skill-verdict line format); only the "go Read
   that file" clause no longer appears, because the same file's exact
   content now already rides the system prompt with zero round trips.
   Adhoc spawns (no `--issue`) are unaffected: `directive_section_files()`
   returns `{}` for them (unchanged, pre-existing), so
   `_directive_system_prompt_block({})` returns `""` and `spawn_cmd()`
   adds no flag — the argv stays byte-identical to a pre-#2204 adhoc
   spawn.
4. `pipeline.py:spawn_cmd()` also gained
   `--exclude-dynamic-system-prompt-sections` (unconditional) and
   `ENABLE_PROMPT_CACHING_1H=1` (unconditional, added to the returned env
   dict) — the prompt-cache-miss fix (see Why).
5. Updated the three tests whose assertions encoded the removed inline
   pointers: `tests/test_directive_diet_2135.py`'s bijection test,
   `tests/test_spawn_directive_assembly.py`'s skill-obligations-pointer
   and checkpoint-commit-marker assertions, and
   `tests/test_spawn_observation_recovery.py`'s `PreambleWarning` test.
   `DirectiveAssemblyBase._run()` in `tests/test_spawn_directive_assembly.py`
   gained an optional `captured_spawn_cmd` param so these tests can assert
   on `spawn_cmd()`'s `append_system_prompt` kwarg (previously mocked away
   entirely, discarding its arguments).

## Why

The issue's own "Investigate FIRST" instruction gated everything else — a
live measurement ran before any file changed (see "Acceptance evidence"
below), and it isolated exactly which half of Defect 1 this repo can act
on.

`--append-system-prompt` (not `--append-system-prompt-file`, which the
issue's cited docs mention) is what this environment's installed CLI
exposes.
derived: claude -p --help — lists --append-system-prompt <prompt> (single value) and --system-prompt/--system-prompt-file, no -file variant for the append form; claude --version reports 2.1.241

Passing the content directly as one argv element is safe here: `cmd` is a
Python list (`spawn_cmd()` never touches a shell), and
`--append-system-prompt` takes exactly one value — the existing
stdin-vs-argv comment in `spawn.py` about a variadic flag swallowing
adjacent argv does not apply to a single-value flag.

`--exclude-dynamic-system-prompt-sections` is unconditional in
`spawn_cmd()` because every role spawn runs in its own fresh isolated
workspace clone (`issue_workspace()`), so cwd differs on every spawn by
construction — there is no spawn shape where the flag would work against
the spawn. `--bare` was not evaluated: the issue text itself scopes it
out ("a larger change than this issue needs").

`materialize_directive_sections()` keeps writing the workspace files
rather than being deleted along with the inline pointers: no round trip
was ever spent on the write itself (pure Python file I/O inside the
already-measured `directive_write` bootstrap-timing phase), and the
on-disk copy remains a durable, inspectable record of which norms applied
to a specific spawn.

## What did not work

None.

## Upstream basis

`docs/handbooks/spawn-directive-assembly.md` established the
`tokenmaxxxer-core`/on-the-record repo-boundary precedent this record
applies to Defect 1's `session-protocol.md` half (same "out of scope
here... live in tokenmaxxxer-core, not this repo" framing, reused for the
same directive.sh mechanism).
canonical: read docs/handbooks/spawn-directive-assembly.md lines 65-69

`docs/decisions/2026-08-21-single-enforcement-surface.md` is a frozen
decision ruling out "add a SessionStart hook to on-the-record" as an
alternative fix — moot for the fix actually shipped (a CLI-flag change,
not a hook), but it foreclosed that alternative during design.
canonical: read docs/decisions/2026-08-21-single-enforcement-surface.md

`spawn.py`'s pre-existing issue #2135 index+sections mechanism
(`directive_section_files()`, `materialize_directive_sections()`,
`DIRECTIVE_DIR`) supplies the section-selection logic this fix reuses
unchanged, only replacing the delivery channel for the already-computed
section bodies.

GitHub issue #2204 itself supplied the acceptance criteria and the
"Investigate FIRST" method this record's live measurement follows.
canonical: gh issue view 2204

## Open findings

- `tokenmaxxxer-core`'s `session-protocol.md` Read stays in place — the
  SessionStart hook in that separate repository still points a spawned
  session at the file instead of injecting its content directly, and this
  is the larger of the two Read-round-trip sources the issue measured.
  This repo's write set has no commit access to that repository.
  Resolution path: a companion issue against `tokenmaxxxer-core` to move
  `directive.sh`'s output from "print a path, tell the session to Read
  it" to the SessionStart-hook `additionalContext` channel the issue
  itself names — out of this repo's frozen write set, not attempted here.
- The issue's literal acceptance line ("a spawned session's log shows no
  Read calls for protocol/contract docs before its first task action")
  needs the companion fix above before it holds end-to-end; this record's
  live measurement isolates and verifies only the on-the-record-controlled
  half. Resolution path: re-run the full live-spawn acceptance check once
  the `tokenmaxxxer-core` companion fix lands.

## Next steps

None — `loop_state: landed`. The open findings above are a
cross-repository follow-up, not unfinished work inside this PR's frozen
write set.

## Acceptance verification

- test_moved_prose_absent_inline_present_via_system_prompt (DietIntegration): inline stdin task carries no "Read <file>" pointer, moved prose reaches the session only via --append-system-prompt — checked: tests/test_directive_diet_2135.py — result: pass: canonical: python3 -m pytest tests/test_directive_diet_2135.py -q -m "" -k bijection, run live this session
- test_completion_prose_warns_about_headless_background_death (PreambleWarning): headless/run_in_background warning still reaches the session (channel changed, content unchanged) — checked: tests/test_spawn_observation_recovery.py — result: pass: canonical: python3 -m pytest tests/test_spawn_observation_recovery.py -q -m "" -k PreambleWarning, run live this session
- test_always_on_overhead_under_budget (DietIntegration): always-on stdin overhead still fits the #2135 2,048-byte budget after the pointer removal — checked: tests/test_directive_diet_2135.py — result: pass: canonical: python3 -m pytest tests/test_directive_diet_2135.py -q -m "" -k overhead_under_budget, run live this session
- test_mounted_skill_directive_states_verdict_obligation (SkillVerdictObligationLine): skill-obligations and checkpoint-commit content assertions updated for the new delivery channel — checked: tests/test_spawn_directive_assembly.py — result: pass: canonical: python3 -m pytest tests/test_spawn_directive_assembly.py -q -m "" -k verdict_obligation, run live this session
- spawn_cmd() argv/env assembly (--exclude-dynamic-system-prompt-sections, ENABLE_PROMPT_CACHING_1H, --append-system-prompt wiring) — checked: tests/test_spawn_pipeline.py — result: pass: canonical: python3 -m pytest tests/test_spawn_pipeline.py -q -m "", run live this session
- surrounding suite has no new regression from this change — checked: tests/,test/ — result: pass: canonical: python3 -m pytest tests/ test/ -q -m "not slow", run live this session; the one FAILED line reproduces on main@23e9d029, unrelated to this diff
- real spawn content, delivered via --append-system-prompt, reaches the model with zero Read tool calls — checked: live-spawn-run1 — result: pass: canonical: acceptance: claude -p run1-dirA-with-flag — result: pass — run live this session, 0 tool_use events, assistant text matches injected content
- --exclude-dynamic-system-prompt-sections converts a cross-cwd cache miss into a cache hit — checked: live-spawn-run2-vs-run3 — result: pass: canonical: acceptance: claude -p run2-dirB-with-flag-vs-run3-dirC-without — result: pass — run live this session, cache_read_input_tokens rose only in the with-flag run

## Acceptance evidence




Unit tests (updated tests plus the surrounding suite, run from this
workspace):

```
$ python3 -m pytest tests/test_spawn_observation_recovery.py tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py tests/test_spawn_pipeline.py tests/test_checkpoint_mode.py tests/test_bootstrap_timing.py -q -m ""
...
1 failed, 315 passed, 3 xfailed, 2 xpassed in 395.65s (0:06:35)
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
```
canonical: python3 -m pytest tests/test_spawn_observation_recovery.py tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py tests/test_spawn_pipeline.py tests/test_checkpoint_mode.py tests/test_bootstrap_timing.py -q -m "" — result: pass (pasted summary above; the one FAILED line is addressed next)

The one exception reproduces the same way on `main`@`23e9d029`, before any
change in this PR, in the same shell:
```
$ git stash && python3 -m pytest tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today -q -m "" ; git stash pop
AssertionError: 'CORE_BUILD_NOW' unexpectedly found in {...os.environ...}
1 failed in 1.01s
```
canonical: git stash && python3 -m pytest tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today -q -m "" ; git stash pop — result: fail identically pre-change, so unrelated to this diff; this session's own process env already carries CORE_BUILD_NOW=1 (the build-now bypass this very session runs under), which the test's spy_popen captures via {**os.environ, ...} regardless of code

The full non-slow suite (one unrelated pre-existing gap, `main`-reproducible,
not touched by this change):
```
1 failed, 1222 passed, 1 skipped, 8 xfailed, 3 xpassed in 368.74s
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
```
canonical: python3 -m pytest tests/ test/ -q -m "not slow" — result: pass (pasted summary above; the roster-ownership FAILED line reproduces on main@23e9d029 too, unrelated to this diff)

The stderr composition-breakdown line from the same test run shows the
inline stdin task's issue-preamble-index segment at 439 bytes with the
Read-pointer block removed (the pre-#2204 shape carried the same content
plus an additional ~350-byte pointer block naming the two workspace
section files by path).
canonical: python3 -m pytest tests/test_directive_diet_2135.py::DietIntegration::test_always_on_overhead_under_budget -q -m "" — result: pass (the existing #2135 2,048-byte always-on ceiling test)

Live-spawn measurement (real `claude -p` invocations against this
machine's installed CLI — run directly rather than through `spawn.py`'s
full issue-workspace machinery, to avoid creating a real branch/PR against
this repo purely for a smoke measurement; the flags and system-prompt
content are byte-identical to what `spawn_cmd()` /
`_directive_system_prompt_block()` now produce for a real issue spawn):
content = `spawn._directive_system_prompt_block(spawn.directive_section_files(skills_mounted=True))`,
3,492 bytes.
canonical: python3 -c "import spawn; print(len(spawn._directive_system_prompt_block(spawn.directive_section_files(skills_mounted=True)).encode()))" — result: 3492

Run 1 (`dirA`, fresh git repo, `--append-system-prompt <content>`
`--exclude-dynamic-system-prompt-sections`, task: summarize the landing
rule in one sentence then answer only `TASK-DONE`, do not use tools):
```
$ echo "이번 세션에서 랜딩(커밋/push/PR) 시 지켜야 할 규칙을 한 문장으로 요약하고, 그 다음 새 줄에 정확히 'TASK-DONE' 이라고만 답하라. 파일을 Read 하거나 다른 도구를 쓰지 마라." | claude -p --output-format stream-json --verbose --max-turns 3 --permission-mode bypassPermissions --exclude-dynamic-system-prompt-sections --append-system-prompt "$SYS_PROMPT" --setting-sources ""
TEXT: 랜딩 시에는 변경을 반드시 이 턴 안에서 직접 커밋하고(체크포인트 커밋을 먼저 해 두고 검증 후 amend/후속 커밋), push 와 PR 생성까지 `git add && git commit && git push -u origin <branch> && gh pr create` 형태의 단일 복합 Bash 호출로 묶어 실행하되, 네트워크로 push/PR 이 막히면 최소한 커밋까지는 완료해 둔다.
TASK-DONE
usage.cache_creation_input_tokens=7429 usage.cache_read_input_tokens=15917
```
canonical: acceptance: claude -p (dirA, --exclude-dynamic-system-prompt-sections, --append-system-prompt full content) — result: pass — 0 tool_use events of any kind in the event stream; the assistant's text summary states the same landing rule _COMPLETION_PROSE carries, which it could only have gotten from the appended system prompt — nothing pointed it at a file to Read

Run 2 (`dirB`, a different fresh git repo/cwd, identical content, WITH
`--exclude-dynamic-system-prompt-sections` + `ENABLE_PROMPT_CACHING_1H=1`):
`cache_read_input_tokens=19201` (up from run 1's 15917 despite the
different cwd), `cache_creation_input_tokens=4145` (down from run 1's
7429).
canonical: acceptance: claude -p (dirB, --exclude-dynamic-system-prompt-sections, ENABLE_PROMPT_CACHING_1H=1) — result: pass — cache_read_input_tokens rose across the cwd change, a cache hit on the shared system-prompt prefix, the effect the flag targets

Run 3 (`dirC`, another different fresh git repo/cwd, identical content,
WITHOUT the flag — control isolating the flag as the cause):
`cache_read_input_tokens=15917` (same as run 1, no increase despite
identical content), `cache_creation_input_tokens=7722` (same magnitude as
run 1, not reduced).
canonical: acceptance: claude -p (dirC, no --exclude-dynamic-system-prompt-sections) — result: fail — cache_read_input_tokens did not rise across the cwd change, the pre-fix behavior this control run reproduces on purpose, isolating the flag in run 2 as the cause

## Regression guard

Every sentence removed from the inline stdin task text in this change
still reaches the session, unchanged, via one of two channels: the
`.on-the-record/directive/*.md` workspace files (`materialize_directive_sections()`,
untouched) or the new `_directive_system_prompt_block()` output built
from the same `_COMPLETION_PROSE` / `_REPO_DISCOVERY_PROSE` /
`_SKILL_CHECK_PROSE` / `_SKILL_VERDICT_PROSE` / `_CHECKPOINT_CONTRACT_BLOCK`
constants — no sentence was deleted, only its delivery channel changed.
canonical: git diff main -- spawn.py — result: pass — the four PROSE
constants and _CHECKPOINT_CONTRACT_BLOCK show no textual change in the
diff, only their call sites moved

## Skill verdicts

skill-verdict: implementation-blueprint — not-applicable: modifies one
already-established mechanism (issue #2135's index+sections pattern)
inside existing functions in two files; no new multi-module structure or
architecture decision to select.
skill-verdict: implementation-complexity-coupling-management — not-applicable:
no coupling/cohesion metric threshold, accessor chain, or check-pipeline
ordering decision involved.
skill-verdict: implementation-design-pattern-selection — not-applicable:
no GoF-pattern-vs-direct-form decision; the change swaps a delivery
channel (workspace file + inline pointer vs. CLI flag), not a design
pattern.
skill-verdict: implementation-performance-data-structure-choice — not-applicable:
no data structure, algorithm, or communication-scheme choice with an
asymptotic or membership-testing tradeoff; both fixes are CLI-flag/env
wiring, not a data-structure decision.
other mounted skills: not triggered


