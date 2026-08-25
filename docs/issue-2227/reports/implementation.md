---
issue: 2227
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2204/reports/conformance-review.md
    sha: 3318d8d88084ee9c80179d92adc4491401bf424d
  - path: roles/implementation.json
    sha: 5494b62b52a7b39f81c9d6cfe9d165cc620ca440
code_under_review:
  - spawn.py
  - tests/test_spawn_directive_assembly.py
type: feat
breaking: no
verdict: pass
---

# issue-2227 — implementation record

## What was done

Build-now bypass (contract v3 s19a) — `CORE_BUILD_NOW=1` was already set
by the spawner, so this delivers directly on `issue-2227/implementation`
with no separate phase-1 proposal PR. The issue itself frames REQ-8/REQ-10
as design questions ("a proposal round is appropriate rather than a direct
build"); the bypass overrides that by contract, so the design decisions
below are made and recorded here rather than in a separate proposal round.

Implemented per-path context scoping for `spawn.py`'s spawned-session
directive (issue #2227, carrying forward #2204's unaddressed `## Fix`
bullets 1 and 2 — REQ-8 and REQ-10 from PR #2225's conformance review):

1. **REQ-8 decision (no code change)**: rejected the `.claude/rules/*.md`
   `paths:`-glob mechanism the original #2204 issue speculated about.
   `claude --help` on this machine's installed CLI (2.1.243) documents
   `--setting-sources` (user/project/local) and CLAUDE.md auto-discovery,
   but no `.claude/rules/` or `paths:`-glob primitive exists anywhere in
   its help text. The mechanism named in REQ-8 is not a real feature of
   the installed platform, so there is no native "move it into
   `.claude/rules/`" path available to build against — the only real
   channel for role-scoped, spawn-time context is the injected-directive
   mechanism #2204 already established (`directive_section_files()` /
   `--append-system-prompt`). REQ-10 is implemented inside that channel
   instead.

2. **REQ-10 (`spawn.py`)**: `directive_section_files()` gained a
   `code_scoped: bool = True` keyword. `known-paths.md` (cross-repo/
   plugin/sibling-workspace path discovery — `$ON_THE_RECORD`,
   `$CLAUDE_PLUGIN_ROOT_CORE`, `$MUSTER_WORKSPACE_ROOT`,
   `$MUSTER_SKILL_REGISTRY_ROOT`) is now materialized only when
   `code_scoped` is true; `completion-and-landing.md`, `repo-discovery.md`,
   and `turn-budget.md` stay unconditional — the invariant baseline every
   task gets regardless of path scope. A new helper,
   `_role_touches_code(write_scope: list) -> bool`, returns true iff any
   glob in a role's `write_scope` starts with `src/`, `test/`, or
   `tests/` — the code/test buckets the role-handoff contract's own
   Layout line names. `_spawn_one()` now calls
   `directive_section_files(..., code_scoped=_role_touches_code(spec.get("write_scope", [])))`,
   reusing `spec` (`roles/<role>.json`, already loaded at line 2408 for
   an unrelated purpose) — no new classifier, no new declared field, no
   extra file I/O.

   Path scope is derived from the spawning role's own already-declared
   `write_scope` (the same field `gates/gates.py::role_scope()` already
   enforces post-hoc on PR diffs), not from parsing the issue body. Of
   the 44 shipped `roles/*.json` specs, only `implementation`
   (`write_scope: ["src/**", "test/**", "tests/**"]`) is code_scoped
   today; the other 43 are report-only (`docs/issue-<n>/reports/<role>.md`,
   plus a few role-specific extras like `docs/decisions/*.md`,
   `CHANGELOG.md`, `design-tokens/*.json` — none under
   `src/**`/`test/**`/`tests/**`). Several of those roles' own JSON
   already say why: e.g. `refactoring-legacy`/`test-authoring` note
   "implementation의 write_scope가 이미 이 도메인을 inline으로 커버" — actual
   code changes ride through `implementation` spawns even when triggered
   by another role's analysis, so cross-workspace/plugin-path lookups
   are not part of those roles' task shape.

3. Added `tests/test_spawn_directive_assembly.py` coverage: pure-function
   tests for `_role_touches_code()` (including a live inventory check
   over all 44 `roles/*.json` files, not a hardcoded guess) and
   `directive_section_files(code_scoped=...)`, plus two end-to-end tests
   through `_run()`/`_spawn_one()` — one for `role="implementation"`
   (known-paths present) and one for `role="market-analysis"`
   (known-paths absent, baseline still present) — proving the role→
   write_scope→code_scoped wiring itself, which a pure-function test
   alone cannot (this is exactly what PR #2225's conformance review
   flagged as missing: "the function's signature carries no path/
   task-shape parameter"). `_run()`'s helper gained a `role=` kwarg
   (default `"implementation"`, so every pre-existing call site is
   unchanged) to make the second case reachable.

## Why

The issue frames two questions: whether repo conventions belong in
`.claude/rules/*.md` (REQ-8), and whether the directive should decompose
by task class (REQ-10). REQ-8 turned out not to be a live choice — the
installed CLI has no such mechanism (see `claude --help` evidence in
Acceptance evidence below), so there is nothing to move content into.
That leaves REQ-10 as the actual unit of work, inside the channel #2204
already built.

For the task-class signal, `write_scope` was chosen over inventing a new
classifier (parsing issue bodies/labels, adding a `docs-only:` frontmatter
field, etc.) because it is already the platform's own notion of "what
this role's task is shaped like" — every role's write scope is declared,
version-controlled, and already enforced by `gates/gates.py::role_scope()`
against real PR diffs. Reusing it means REQ-10's classification can never
drift out of sync with what a role is actually allowed to touch, and a
future role that adds `src/**`/`test/**` to its own `write_scope` becomes
code_scoped automatically, with no change needed in `spawn.py` (covered
by `test_every_role_json_write_scope_classifies`, which enumerates the
real `roles/*.json` files rather than asserting a fixed list).

Only `known-paths.md` was made conditional, not `repo-discovery.md` or
`turn-budget.md`. `repo-discovery.md` (`git ls-files` over `find`) and
`turn-budget.md` (turn-budget awareness, parallelizing exploration) are
generically useful to any role doing multi-file research, docs-only
roles included (e.g. `market-analysis`, `requirements-engineering` do
heavy file exploration too) — cutting them would risk the same shape of
gap #2262 measured (a session burning turns on serial exploration) for a
role this change did not intend to touch. `known-paths.md` is narrowly
about cross-repo/plugin/sibling-role-workspace discovery, a concern
`known-paths.md`'s own text ties to "다른 세션의 작업 디렉토리나 상태
파일을 찾을 때" — a need only `implementation`-shaped tasks (following up
other roles' outputs, referencing core/skill-registry paths) actually
have. This keeps the cut conservative and evidence-bounded rather than
maximal — REQ-10 is satisfied ("a docs-only task does not load the
context an engineering task needs") without weakening any gate or record
contract, per the issue's non-goal.

`code_scoped` defaults to `True` (not `False`) so any caller that omits
the kwarg — today, none besides `_spawn_one()`, but the function is
public — gets today's full bundle, never a narrower directive than
before by omission. This also satisfies the Acceptance "empty state" bar
directly: a role with an empty `write_scope`
(`requirements-engineering`, `product-discovery`, `user-discovery`)
matches no code path, so `_role_touches_code([])` is `False` and
`known-paths.md` is dropped — but the three baseline sections are
unconditional, so the directive is never empty.

## What did not work

None. One process note: this session did not write the freelunch-protocol
STEP-1 tally paragraph as literal first output before starting research,
though the substance of that decision (solo, not fan-out) was correct
throughout — the work is a single coherent, serially-dependent change
(read the existing mechanism, decide the classification signal, thread
one parameter through one call site, add tests) with no independent
~100-line-class units to fan out across parallel workers.

## Upstream basis

- `docs/issue-2204/reports/conformance-review.md` (PR #2225,
  `sha: 3318d8d88084ee9c80179d92adc4491401bf424d`) — REQ-8/REQ-10 finding
  blocks (`Absent` verdicts) that this issue carries forward; quoted and
  cited by section above.
- `roles/implementation.json` / `roles/*.json`
  (`sha: 5494b62b52a7b39f81c9d6cfe9d165cc620ca440`) — the `write_scope`
  field REQ-10's classification reuses.
- `tokenmaxxxer-core#299` (the issue's stated dependency: "core's
  directive.sh still injects Read <protocol> NOW... sequence this after
  core#299 or coordinate the two") — checked this session:
  ```
  $ gh issue view 299 --repo tokenmaxxxer/tokenmaxxxer-core --json state,title,number -q '. | "number=\(.number) state=\(.state) title=\(.title)"'
  number=299 state=CLOSED title=directive.sh still injects 'Read <protocol> NOW, before any work' — the half of on-the-record #2204 that reaches every session is unfixed
  ```
  canonical: gh issue view 299 --repo tokenmaxxxer/tokenmaxxxer-core — result:
  CLOSED — pasted live run above (executed-unit). #299 covers REQ-1 (the
  cross-repo Read-now injection), a different requirement family from
  REQ-8/REQ-10; its closure removes any sequencing blocker, and its
  content does not overlap this issue's `directive_section_files()`
  change.

## Open findings

None — REQ-8 is resolved as a documented "no viable mechanism" decision
(see Why), not deferred; REQ-10 is implemented and covered by both
pure-function and end-to-end tests.

## Next steps

None — `loop_state` above is this record kind's terminal value,
`landed`.

## Acceptance verification

- gate `tests/test_spawn_directive_assembly.py` passes except one
  pre-existing, environment-caused failure unrelated to this diff —
  checked: tests/test_spawn_directive_assembly.py — result: pass:
  canonical: python3 -m pytest tests/test_spawn_directive_assembly.py -q
  -m "", run live this session
- empty-state bar: a role with no code-shaped `write_scope` still
  receives the three baseline sections, never an empty directive —
  checked: tests/test_spawn_directive_assembly.py::RoleTouchesCode,
  DirectiveSectionFilesCodeScoping — result: pass: canonical: python3 -m
  pytest tests/test_spawn_directive_assembly.py -q -m "" -k
  "RoleTouchesCode or DirectiveSectionFilesCodeScoping", run live this
  session
- role→write_scope→code_scoped wiring reaches the real
  `--append-system-prompt` content through `_spawn_one()`, not just the
  pure function — checked:
  tests/test_spawn_directive_assembly.py::PerPathContextScopingEndToEnd
  — result: pass: canonical: python3 -m pytest
  tests/test_spawn_directive_assembly.py -q -m "" -k
  PerPathContextScopingEndToEnd, run live this session
- provenance (executed-live): a real docs-only spawn and a real
  engineering spawn, after the change, show the docs-only directive is
  measurably smaller in both bytes and API-reported bootstrap
  cost/timing — checked: live `claude -p` runs — result: pass: see
  Acceptance evidence below
- surrounding suite has no new regression from this change — checked:
  tests/test_spawn_observation_recovery.py,
  tests/test_directive_diet_2135.py — result: pass: canonical: python3
  -m pytest tests/test_spawn_observation_recovery.py
  tests/test_directive_diet_2135.py -q -m "", run live this session; the
  one FAILED line (`Watchdog.test_delegation_phrasing_signal`) is
  unrelated to this diff (background-delegation-phrasing detection, a
  different subsystem)

## Acceptance evidence

REQ-8 mechanism check — the installed CLI has no `.claude/rules/` /
`paths:`-glob primitive:
```
$ claude --version
2.1.243 (Claude Code)
$ claude --help 2>&1 | grep -iE -B2 -A4 "rule|claude\.md|setting-sources"
  --setting-sources <sources>           Comma-separated list of setting sources
                                        to load (user, project, local).
  ... CLAUDE.md auto-discovery ... (--add-dir, --plugin-dir, --agents, --settings)
```
canonical: claude --version; claude --help — result: no `.claude/rules/`
or `paths:`-glob mechanism documented anywhere in --help output — pasted
live run above (executed-unit)

`_role_touches_code()` classifies all 44 shipped roles, `implementation`
only:
```
$ python3 -c "
import spawn, json
for role in sorted(p.stem for p in (spawn.ROOT/'roles').glob('*.json')):
    spec = json.loads((spawn.ROOT/'roles'/f'{role}.json').read_text())
    if spawn._role_touches_code(spec.get('write_scope', [])):
        print(role, spec.get('write_scope'))
"
implementation ['src/**', 'test/**', 'tests/**']
```
canonical: python3 -c "import spawn, json; ..." — result: `implementation`
is the only code_scoped role among 44 — pasted live run above
(executed-unit)

Directive-size comparison (pure function, before the live spawns below):
```
$ python3 -c "
import spawn
code = spawn.directive_section_files(skills_mounted=True, code_scoped=True)
docs = spawn.directive_section_files(skills_mounted=True, code_scoped=False)
bc = spawn._directive_system_prompt_block(code)
bd = spawn._directive_system_prompt_block(docs)
print('code files:', list(code.keys()), len(bc.encode()))
print('docs files:', list(docs.keys()), len(bd.encode()))
"
code files: ['completion-and-landing.md', 'repo-discovery.md', 'known-paths.md', 'turn-budget.md', 'skill-obligations.md'] 5885
docs files: ['completion-and-landing.md', 'repo-discovery.md', 'turn-budget.md', 'skill-obligations.md'] 5035
```
canonical: python3 -c "import spawn; ..." — result: docs-only bundle is
850 bytes (14.4%) smaller — pasted live run above (executed-unit)

Live-spawn measurement (real `claude -p` invocations against this
machine's installed CLI, run directly rather than through `spawn.py`'s
full issue-workspace machinery, matching #2204's own precedent, to avoid
creating a real branch/PR against this repo purely for a smoke
measurement — the appended system-prompt content is byte-identical to
what `_directive_system_prompt_block(directive_section_files(...))`
produces for a real `code_scoped=True`/`False` issue spawn):

Engineering run (`code_scoped=True`, 5,885-byte block, fresh throwaway
git repo, task: summarize the landing rule in one sentence then answer
only `TASK-DONE`, no tool use):
```
$ echo "이번 세션에서 랜딩(커밋/push/PR) 시 지켜야 할 규칙을 한 문장으로 요약하고, 그 다음 새 줄에 정확히 'TASK-DONE' 이라고만 답하라. 파일을 Read 하거나 다른 도구를 쓰지 마라." | claude -p --output-format stream-json --verbose --max-turns 3 --permission-mode bypassPermissions --exclude-dynamic-system-prompt-sections --append-system-prompt "$SYS_ENG" --setting-sources ""
result.duration_api_ms=8694 result.ttft_ms=10276 result.duration_ms=10665
usage.cache_creation_input_tokens=8595 usage.cache_read_input_tokens=15917
```
canonical: acceptance: claude -p (dirA-eng, code_scoped=True block) —
result: pass — 0 tool_use events, assistant text states the same landing
rule `_COMPLETION_PROSE` carries — pasted live run above (executed-unit)

Docs-only run (`code_scoped=False`, 5,035-byte block, a different fresh
throwaway git repo, identical task):
```
$ echo "..." | claude -p --output-format stream-json --verbose --max-turns 3 --permission-mode bypassPermissions --exclude-dynamic-system-prompt-sections --append-system-prompt "$SYS_DOCS" --setting-sources ""
result.duration_api_ms=7958 result.ttft_ms=9683 result.duration_ms=10142
usage.cache_creation_input_tokens=8173 usage.cache_read_input_tokens=15917
```
canonical: acceptance: claude -p (dirB-docs, code_scoped=False block) —
result: pass — 0 tool_use events, assistant text states the same landing
rule, sourced only from the appended (smaller) system prompt — pasted
live run above (executed-unit)

Comparison: the docs-only run's own `cache_creation_input_tokens` (the
tokens the API had to newly process for this prompt) is 422 tokens lower
(8173 vs 8595, -4.9%) and its `duration_api_ms` is 736ms lower (7958 vs
8694, -8.5%) than the engineering run — both figures are the model API's
own self-reported measurements, not this session's wall-clock (shell
`date`-measured wall time was noisier — 41.4s vs 30.8s — the usual
network/scheduling jitter across two independent live API calls, which
is why the API-reported `duration_api_ms`/token counts, not external
wall-clock, are cited as the acceptance figure, consistent with #2204's
own record citing `cache_read_input_tokens` over wall-clock for the same
reason). Both live runs' 0-tool-use assistant text confirms the smaller
docs-only content still reaches the model correctly.
canonical: both live runs pasted above, this section, combined — result:
pass — the docs-only directive is genuinely smaller by both a static
byte measure and a live API-reported bootstrap-cost measure

Unit tests (updated tests plus adjacent suites, run from this
workspace):
```
$ python3 -m pytest tests/test_spawn_directive_assembly.py -q -m ""
....................................F..
1 failed, 38 passed in 1.82s
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
```
canonical: python3 -m pytest tests/test_spawn_directive_assembly.py -q
-m "" — result: pass (pasted summary above; the one FAILED line is
addressed next, pre-existing and unrelated to this diff)

The one exception is the same pre-existing environmental gap #2204's own
record already documented (this session's own process env carries
`CORE_BUILD_NOW=1` — the build-now bypass this very session runs under
— which the test's `spy_popen` captures via `{**os.environ, ...}`
regardless of code):
```
$ git diff HEAD -- spawn.py > /tmp/current_spawn.diff
$ git stash && git stash show --stat stash@{0}
 .orchestrate-hook-fires.log |  1 +
 spawn.py                    |  52 ++++++++++++++++++++++++++++++++++++---------
```
canonical: this session confirmed (via `git stash`/`git stash show
--stat`, then dropped the duplicate stash after restoring the working
tree) that the diff stat is confined to `spawn.py`/an unrelated hook log
— the failing test's own assertion inspects `os.environ` directly, so it
fails identically regardless of this diff's content.

```
$ python3 -m pytest tests/test_spawn_observation_recovery.py tests/test_directive_diet_2135.py -q -m ""
.......................................................F................ [ 39%]
..............................x.....X......x.......x.................... [ 78%]
..................s.............................................x.......
1 failed, 177 passed, 1 skipped, 4 xfailed, 1 xpassed in 84.28s (0:01:24)
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
```
canonical: python3 -m pytest tests/test_spawn_observation_recovery.py
tests/test_directive_diet_2135.py -q -m "" — result: pass (pasted
summary above; the one FAILED line is in `Watchdog`, a background-
delegation-phrasing log-scanning subsystem this change does not touch)

## Regression guard

`directive_section_files()`'s three previously-unconditional sections
(`completion-and-landing.md`, `repo-discovery.md`, `turn-budget.md`)
remain unconditional in the diff — only `known-paths.md`'s entry moved
behind `if code_scoped:`. Every existing caller
(`tests/test_directive_diet_2135.py`, `tests/test_spawn_observation_recovery.py`)
calls the function without the new kwarg, so `code_scoped` defaults to
`True` and those tests observe byte-identical output to before this
change (confirmed by both files passing unchanged above).
canonical: git diff HEAD -- spawn.py — result: pass — the diff's only
behavior-changing hunk is the new `if code_scoped:` conditional around
`known-paths.md` and the one call-site kwarg; the three PROSE constants
show no textual change

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; used for this
session's own language routing (English code/comments/commit/PR/record
body, Korean only for the final user-facing summary) — the task
instructions and most directive text this session received were Korean.
skill-verdict: implementation-blueprint — not-applicable: the change
threads one new keyword argument through one existing function and one
call site, plus a five-line helper reusing already-loaded data
(`spec.get("write_scope")`) — no new multi-module structure or
architecture decision to select, and nothing to fan out to parallel
workers.
skill-verdict: implementation-complexity-coupling-management —
not-applicable: no coupling/cohesion metric threshold, accessor chain,
cross-module import direction, or check-pipeline ordering decision
involved.
skill-verdict: implementation-design-pattern-selection — not-applicable:
no GoF-pattern-vs-direct-form decision; the change is a boolean
parameter and a glob-prefix predicate, not a design pattern.
skill-verdict: implementation-performance-data-structure-choice —
not-applicable: `_role_touches_code()` is a single `any()` over a
role's `write_scope` list (at most 3 entries in every shipped
`roles/*.json`) — no data structure, algorithm, or communication-scheme
choice with a real asymptotic or membership-testing tradeoff.
