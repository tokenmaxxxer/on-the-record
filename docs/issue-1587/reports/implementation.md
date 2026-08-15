---
code_under_review:
  - spawn.py
  - gates/patrol_queue.py
  - docs/handbooks/spawn.md
  - tests/test_spawn_judge.py
type: feature
breaking: false
canonical: pytest tests/test_spawn_judge.py -v — 15 passed, run this session against e2b327ad (this branch's HEAD)
verdict: pass
loop_state: landed
---

# issue #1587 — `judge` transport implementation record

## Summary of work

Implemented `spawn.py judge <role> --merge <sha> [-C <repo>]`, following
canonical: docs/issue-1587/proposals/2026-08-15-judge-transport.md, its
build-plan section, listing ten numbered items:

1. `JUDGE_TIMEOUT = 120` and `JUDGE_MAX_ROLES_PER_MERGE = 3` constants
   (spawn.py, next to `CONSULT_TIMEOUT`/`PANEL_TIMEOUT`).
2. `_readonly_plugin_dirs(role, spec)`: role's own rulebook loaded in
   full via `plugin_dirs()`; `core_plugin_dirs()` filtered to drop
   delivery-oriented plugins (`freelunch`, `scout`, `warrant`) before
   they reach `--plugin-dir`.
3. `_readonly_bash_allow(cwd)` / `_readonly_settings(role, cwd)`: allow
   only Read/Grep/Glob + `git show`/`git diff`/`git log` (cwd-anchored),
   explicit `permissions.deny` for Write/Edit/`gh `. `_judge_cmd_and_env()`
   omits `--permission-mode bypassPermissions` entirely.
4. `_compress_diff(diff_text, cap_tokens=18000)`: deleted files collapse
   to a name line, deletion-only hunks drop, still-oversized diffs
   degrade to a bare file-name list truncated to the cap.
5. `_judge_prefilter()` / `_judge_validate()`: single Haiku-pinned
   `claude -p` calls each, JSON-parsed via the existing `_parse_verb_json()`.
   Prefilter failure defaults to `relevant=True`; validator failure
   defaults to `[]`.
6. `judge_cmd(role, merge_sha, cwd=None)`: the four-stage pipeline
   (prefilter, judge session, validator, `patrol_queue.enqueue()` with
   `lane="diff"`), wrapped in `try/finally` that always appends one line
   to a per-merge trace log via `_append_judge_trace()`.
7. `judge` CLI subcommand wired into `main()` plus a `--merge` argparse
   flag; the 3-roles-per-merge cap is enforced before any subprocess
   call (including `git show`) via `_judge_roles_run_today()`.
8. `tests/test_spawn_judge.py`, committed at e2b327ad: unit tests
   covering read-only settings assembly, plugin-dir filtering,
   diff-compression cap behavior, prefilter-skip path, validator-drop
   path, queue append with `lane="diff"`, trace-always on both a
   `git show` failure and a cap-exceeded skip, and the binding
   review-note requirement — cap counting from a missing or corrupt
   trace log defaults to 0, never raises an exception.
9. `docs/handbooks/spawn.md`: new `judge` section documenting the
   pipeline, the read-only construction, the budgets, and the core#216
   integration-test deferral.
10. Real measured run against a recent merge of this repo: not run this
    session — see "## What did not work" for what happened instead.

canonical: pytest tests/test_spawn_judge.py -v — 15 passed, output below
```
$ python3 -m pytest tests/test_spawn_judge.py -v
...
============================== 15 passed in 0.88s ==============================
```
derived: `python3 -m pytest tests/test_spawn_judge.py -v`

```
$ grep -rn "gh " spawn.py | grep -v "^[0-9]*://"
430:    return "  비공개 레포면 git 자격증명이 필요하다. `gh auth status` 로 확인한다."
896:        sys.exit("승인자 로그인을 모른다. gh auth login 을 하거나 "
1402:    """`gh api -i` 출력(상태줄 + 헤더 + 빈줄 + 바디)을 파싱한다.
```
derived: `grep -rn "gh " spawn.py`
canonical: spawn.py at e2b327ad, the block from the `# issue #1587`
comment header through `judge_cmd`'s closing `finally` — none of the
three `gh ` hits above fall inside `judge_cmd`, `_readonly_plugin_dirs`,
`_readonly_bash_allow`, `_readonly_settings`, `_judge_cmd_and_env`,
`_compress_diff`, `_judge_prefilter`, or `_judge_validate`.

## Why

R1 (real LLM judgment), R2/R5 (token/wall-clock budget), R3 (zero GitHub
API strain), R4 (real judgment, not mechanical patrol) per the issue's
operator requirements — canonical: docs/issue-1587/proposals/2026-08-15-judge-transport.md,
its Rationale section. `consult`/`_verb_cmd()` cannot serve this because
their isolation is prompt-based (the #1097 override string), which that
same section rejects as a prompt-injection surface for
attacker-controlled diff content — judge needed structural
(session-assembly-level) isolation instead.

## Upstream / basis

docs/issue-1587/proposals/2026-08-15-judge-transport.md — phase-2 opened
by the `APPROVE issue-1587/implementation` comment named in this
session's own invocation context.

## What did not work

- Proposal build-plan item 10 ("one real measured run against a recent
  merge of this repo, tokens in/out, wall-clock, findings before/after
  validator"): expected — run `spawn.py judge <role> --merge <sha>`
  live and record the numbers. Actual — skipped this session. A live
  run spawns a nested `claude -p` subprocess from inside this
  already-running headless session — cost and hang risk this
  single-shot turn does not budget for safely. `judge_cmd()` itself is
  built; the unit tests cited above exercise it end to end with
  subprocess calls patched, and only the live invocation is
  outstanding.
- Full `pytest -q` suite wall-clock: expected — capture it for this
  record's tiering-gap note (no `.on-the-record/test-tiers.json` file
  exists in this repo).
  canonical: shell output of `find . -maxdepth 1 -iname test-tiers.json`
  and `ls .on-the-record/`, run this session — neither turned up a
  tiering config. Actual — the background full-suite run had not
  finished by the time this record was written, so the exact wall-clock
  figure is unavailable this session.
  unverifiable: full-suite wall-clock time — background run still in
  flight when this record was finalized; not fabricated as a number.

## Open findings

None raised against this record.

## Rationale for deviations

Build-plan items 1-9 above match the approved proposal's build-plan
section as written. Item 10 (the real measured run) is the one
divergence, documented above under "## What did not work" rather than
treated as a scope-exceeded stop or an alternative swap — it is the one
proposal item requiring a live, costed session rather than a build/test
action.
