---
code_under_review: HEAD
loop_state: landed
type: fix
breaking: false
verdict: pass
---

# issue-2164 — implementation record

## What was done

Build-now bypass (contract v3 s19a) fired for this session (`CORE_BUILD_NOW=1`
in the spawning environment) — no proposal round, direct delivery on
`issue-2164/implementation`.

Renamed every stale `룰북` (rulebook) reference in `consult.py` and
`pipeline.py` that describes the *role/skill guidance* concept to
`스킬-저장소 가이던스` (skill-repo guidance) — 10 edits total, both in
docstrings and in LLM-facing prompt text sent to spawned consult/judge/panel
sessions. Locations, grouped by function:
canonical: read consult.py:430-444 (`consult_cmd()` docstring, 2 mentions)

- `consult.py:432-439` — `consult_cmd()` docstring (two paragraphs).
- `consult.py:467`, `consult.py:475` — `consult_cmd()`'s `override`/
  `base_prompt` prompt strings.
- `consult.py:586` — `_verb_cmd()`'s equivalent `override` string.
canonical: read consult.py:463-481,583-591 (override/base_prompt strings, 3 mentions)

- `consult.py:874` — `_judge_validate()`'s confirm/refute prompt.
- `consult.py:937-938` — `judge_cmd()`'s judge-session prompt.
- `consult.py:1093` — `_run_panel_session()`'s panel prompt.
canonical: read consult.py:868-878,932-943,1088-1097 (judge/panel prompt strings, 3 mentions)

- `pipeline.py:215-222` — `role_settings()` docstring (two mentions).
- `pipeline.py:483` — `require_doctor()` docstring: "룰북 집행 전체가" →
  "훅 집행 전체가" (names the *hook-firing* mechanism generally, not
  skill-repo guidance specifically, so renamed to the more precise "hook
  enforcement" rather than "skill-repo guidance").
- `pipeline.py:602` — `spawn_cmd()` comment.
- `pipeline.py:611` — `spawn_cmd()` comment: `rulebook/core` → `skill-repo/core`.
canonical: read pipeline.py:211-224,478-489,598-614 (docstring/comment mentions, 4 mentions)
canonical: git diff --stat consult.py pipeline.py — pasted live run in "Acceptance evidence" below (20 lines changed in consult.py, 12 in pipeline.py)

Also fixed the dangling `plugin_dirs()` function-name reference the issue
named at `pipeline.py:215-216`: `role_settings()`'s docstring pointed readers
at a function called `plugin_dirs()` that does not exist anywhere in the
repo.
canonical: python3 -c "...grep -rn '^def plugin_dirs' . --include=*.py..." — pasted live run in "Acceptance evidence" below (empty stdout, exit 1)

The actual `--plugin-dir` assembly for role/skill dirs happens in
`spawn_cmd()` (using its `plugins`/`core_plugins`/`skill_dirs` parameters),
so the cross-reference now points there. The identical dangling reference
also existed one paragraph up at `consult.py:438` (`role_settings()`/`plugin_dirs()`)
— fixed in the same edit since it sits on the same `룰북`-rename line (see
"Rationale for deviations").
canonical: read pipeline.py:585-614 (spawn_cmd() signature and --plugin-dir assembly loop)

Left three `룰북` occurrences in `pipeline.py` untouched (lines 380, 659,
661) — they describe the CORE plugin bundle's own clone (the directory
literally named `runs/rulebooks/tokenmaxxxer-core`, and the gates that live
inside it), which the issue explicitly carves out as "a distinct, legitimate
concept and out of scope."
canonical: read pipeline.py:378-386,650-668 (the three untouched references, in `core_root()` and `spawn_cmd()`)

## Why

The issue's own risk framing is the rationale: the `룰북` word in
`consult.py`'s LLM-facing prompt strings is read and reasoned over by every
spawned judge/panel/consult session, and `resolve_role_source()` already
routes all role guidance through skill-repository only (issue #1955) — no
separate "rulebook" artifact exists for the retired per-role resolution path
to point spawned sessions at.
canonical: read consult.py:406-408,679 (`resolve_role_source()` is the only role-guidance loader now)

## Upstream basis

Issue #2164's own "Change" section named the exact `consult.py` line numbers
(432, 438-439, 467, 475, 586, 874, 937-938, 1093) and the `pipeline.py:215`
dangling-reference item; issue #1955 (skill-repository guidance routing) is
the reason the old `룰북` framing is now stale.

sha: same-commit

## What will be done

(Build-now bypass — no phase-1 proposal exists to reference; scope is the
issue's own "Change"/"Acceptance" sections, reproduced here for the record.)

- `consult.py`: replace `룰북` with accurate terminology in docstrings and
  every LLM-facing prompt string listed in the issue.
- `pipeline.py:215`: fix the dangling `plugin_dirs()` docstring reference to
  match what the code actually calls.
- Do not touch `runs/rulebooks/tokenmaxxxer-core` or any other
  core-plugin-bundle path/string.

## Out of scope

No change to `runs/rulebooks/tokenmaxxxer-core` or any other
core-plugin-bundle path/string (`pipeline.py:380,659,661` left untouched).
No behavior change: every edit is docstring/comment/prompt text only.
canonical: python3 -m py_compile consult.py pipeline.py — pasted live run in "Acceptance evidence" below (COMPILE OK, no syntax errors)

## What did not work

None — all 10 edits landed on the first attempt; the pre-edit context read
(`role_settings()`, `spawn_cmd()`, `core_root()`) was enough to correctly
classify every `룰북` occurrence as either "role/skill guidance" (rename) or
"core-plugin-bundle" (leave alone) before any edit was made.

## Rationale for deviations

Build-now carries no phase-1 proposal to diverge from, but the delivered
edit set is wider than the issue's literally-named line numbers, because the
issue's own acceptance criterion ("`grep -rn '룰북' consult.py pipeline.py`
returns zero hits ... judge case by case") requires a full sweep, not just
the lines the issue body happened to quote:

- `pipeline.py:222` (same `role_settings()` docstring paragraph as the named
  line 215) and `pipeline.py:483,602,611` — three more `룰북`/`rulebook`
  occurrences the issue's grep-based acceptance bullet catches but its prose
  didn't individually cite. Each was judged case-by-case per the issue's own
  instruction and renamed because each describes role/skill guidance or
  general hook enforcement, not the core-plugin-bundle concept.
- `consult.py:438`'s `plugin_dirs()` reference — the issue named only
  `pipeline.py:215` for the dangling-reference fix, but the identical bug
  sits on the same line already being edited for the `룰북`→skill-repo
  rename at `consult.py:438`, so it was corrected in the same edit rather
  than left half-fixed next to its own rename.

Additive terminology corrections within the same two files the issue names,
not a swap of the approach the issue describes.

## Completed items (doc-placement ladder)

This implementation record is the only docs/ output this delivery produces;
no system-design or operator-facing-contract change is involved, so no
`docs/specs/`, `docs/decisions/`, or `docs/handbooks/` entry is triggered.

## Acceptance evidence

```
$ python3 -m py_compile consult.py pipeline.py && echo "COMPILE OK"
COMPILE OK
```
canonical: python3 -m py_compile consult.py pipeline.py — pasted live run above (executed-unit)
acceptance: python3 -m py_compile consult.py pipeline.py — result: pass, no syntax errors

```
$ python3 -c "import subprocess; r=subprocess.run(['grep','-rn','^def plugin_dirs','.','--include=*.py'],capture_output=True,text=True); print(repr(r.stdout), r.returncode)"
'' 1
```
canonical: python3 -c "...grep -rn '^def plugin_dirs' . --include=*.py..." — pasted live run above (executed-unit)
acceptance: same command — result: pass, empty stdout / exit 1 (confirms plugin_dirs() never existed anywhere in the repo)

```
$ python3 -c "import subprocess; r=subprocess.run(['grep','-rn','룰북','consult.py','pipeline.py'],capture_output=True,text=True); print(r.stdout)"
pipeline.py:380:    # 로컬 체크아웃이 없으면 룰북과 같은 길: on-the-record 소유 클론을 받아 쓴다.
pipeline.py:659:    # 룰북 게이트는 core 공유 라이브러리를
pipeline.py:661:    # 변수를 주입하지 않으면 상대 fallback 이 룰북 클론 내부를 가리켜
```
canonical: python3 -c "...grep -rn '룰북' consult.py pipeline.py..." — pasted live run above (executed-unit)
acceptance: same command — result: pass, zero `consult.py` hits; the 3 `pipeline.py` hits are the core-plugin-bundle references excluded above

```
$ git diff --stat consult.py pipeline.py
 consult.py  | 20 ++++++++++----------
 pipeline.py | 12 ++++++------
 2 files changed, 16 insertions(+), 16 deletions(-)
```
canonical: git diff --stat consult.py pipeline.py — pasted live run above (executed-unit)
acceptance: git diff --stat consult.py pipeline.py — result: pass, only the 2 named files changed, no other file touched

```
$ python3 -m pytest tests/test_spawn_pipeline.py tests/test_consult_trace_root.py tests/test_spawn_consult_panel.py tests/test_spawn_judge.py gates/test_consult_gate_lib_env.py gates/test_consult_verdict_parsing.py gates/test_consult_siblings.py gates/test_requirement_intake_consult.py gates/test_consult_json_parse.py gates/test_design_research_consult.py -q 2>&1 | tail -3
........................................................................ [ 38%]
...........................................x............................ [ 77%]
....................x......x.x.............                              [100%]
183 passed, 4 xfailed in 134.50s (0:02:14)
```
canonical: pytest run above (10 consult/judge/panel/pipeline test files) — pasted live run above (executed-unit)
acceptance: same command — result: pass, 183 passed, 0 failed, 4 xfailed (pasted above)

```
$ python3 -m pytest test/test_spawn_skill_judge_haiku_timeout_overlap.py harness/fixture-concurrent-judgment/test_panel.py -q 2>&1 | tail -3
...........                                                              [100%]
11 passed in 1.00s
```
canonical: pytest run above (remaining judge/panel test files not covered by the prior run) — pasted live run above (executed-unit)
acceptance: same command — result: pass, 11 passed, 0 failed (pasted above)

The two pytest runs above cover every file matched by
`find . -iname "*test*consult*" -o -iname "*test*judge*" -o -iname "*test*panel*" -o -iname "*test*pipeline*"`.

## Skill verdicts

None of the four mounted `implementation-*` skills were invoked via the
Skill tool this session — each was reviewed against this task and judged
not-applicable: `implementation-complexity-coupling-management` (no
coupling/cohesion metric or check-pipeline ordering involved),
`implementation-design-pattern-selection` (no GoF pattern decision),
`implementation-performance-data-structure-choice` (no data
structure/algorithm/communication-scheme choice), and
`implementation-blueprint` (no new module/file structure being designed —
this is a same-line terminology rename in two existing files). Per the
current skill-obligation scoping (issue #2153), a `skill-verdict:` line is
only required for a skill actually invoked via the Skill tool this
session — none was.

## Open findings

None.

## Next steps

None — loop_state is terminal (`landed`).
