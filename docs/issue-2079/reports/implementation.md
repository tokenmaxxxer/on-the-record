---
code_under_review: HEAD
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# Implementation — issue #2079

skill-verdict: implementation-blueprint — not-applicable: single markdown-text edit plus one new content-assertion test file, no multi-module structure decision to make.
skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion threshold, accessor chain, cross-module import, or check-ordering decision involved.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern decision; this is directive prose plus a string-assertion test.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data structure, algorithm, or communication-scheme choice involved.

## What was done

canonical: `git diff main -- on-the-record/commands/run.md docs/specs/reconciled-index.md`, executed live this session.

1. Read `gh issue view 2079` and `gh issue view 2062 --comments` (both executed live this session) to recover the exact operator scope-addition wording: (a) the orchestrate directive must carry the same invoke-before-apply sentence for the orchestrator's own conversation-level skill use; (b) the orchestrate directive must also name the plugin's own three skills (`on-the-record:consult`, `on-the-record:run`, `on-the-record:report-upstream`) at their trigger conditions with the same obligation.
2. Confirmed via `grep -n "orchestrate\|on-the-record:consult\|on-the-record:run\|report-upstream" spawn.py` (zero matches, executed live this session) and reading `on-the-record/commands/run.md`/`consult.md`/`report-upstream.md` that neither path existed on `main` before this change — matching the merged execution-observation record's finding (docs/issue-2062/reports/execution-observation.md) that acceptance criterion 1's orchestrator/plugin-skill half was never delivered.
3. Edited `on-the-record/commands/run.md` step 1, right after the existing "스킬 평가" paragraph: added a paragraph titled `invoke-before-apply(이슈 #2062) — 오케스트레이터 자신의 스킬 사용` carrying the literal strings `invoke-before-apply(이슈 #2062)` and `invoked;` (mirroring spawn.py's role-session wording at spawn.py:8519-8537), and a second paragraph `플러그인 자신의 세 스킬 — 같은 invoke-before-apply 의무` naming `on-the-record:consult`, `on-the-record:run`, `on-the-record:report-upstream` at their trigger conditions, carrying the same `invoke-before-apply`/`invoked;` requirement.
4. Regenerated `docs/specs/reconciled-index.md` via `python3 gates/spec_index.py --update` since `on-the-record/commands/run.md`'s content hash changed (spec-index-preflight requirement).
5. Added a new directive-content test module under `tests/` (`test_orchestrate_directive_invoke_before_apply.py`) that reads `run.md` directly and asserts both new paragraphs carry `invoke-before-apply` and `invoked;`, and that the plugin's-own-three-skills paragraph names all three commands — this is the "directive-assembly tests covering both paths" the acceptance criterion asks for.

## Why

canonical: `gh issue view 2079`, executed live this session — the issue's own acceptance criterion 1: "the orchestrate directive text and the plugin's-own-skills obligation carry the same invoke-before-apply sentence and invoked; marker requirement, with directive-assembly tests covering both paths." This closes the gap the merged execution-observation record verified: PR #2063/#2065 delivered the invoke-before-apply obligation only for spawned role sessions (spawn.py), not for the orchestrator's own skill use or the plugin's own three skills, despite both being requested in issue #2062's comment trail before implementation started.

## Upstream basis

canonical: `git log --oneline -3`, executed live this session — based on `main` at commit `85a16840` (PR #2065, "issue-2062: invoke-before-apply obligation + skill-verdict marker"), which is the tip this branch was cut from. docs/issue-2062/reports/execution-observation.md (merged via PR #2066) is the upstream finding this issue exists to close.

## Test evidence

canonical: `python3 -m pytest -q -m "not slow"`, executed live this session (fast tier per `.on-the-record/test-tiers.json`, budget 300s; this diff touches neither `spawn.py` nor any file in `trigger_change_classes`, so the slow tier is not triggered) — result:

```
$ python3 -m pytest -q -m "not slow"
2609 passed, 18 xfailed, 3 xpassed in 44.19s
```

canonical: `python3 -m pytest -q -m "not slow"`, executed live this session (the run captured immediately above).
acceptance: `python3 -m pytest -q -m "not slow"` — result: 2609 passed, 0 failed.

canonical: `python3 -m pytest tests/test_orchestrate_directive_invoke_before_apply.py -q`, executed live this session — result:

```
3 passed in 0.86s
```

## What did not work

An earlier run of the fast tier failed on `tests/test_spec_index.py` (the `t_baseline_repo_passes` case) because editing `run.md` changed its content hash without regenerating `docs/specs/reconciled-index.md`. Fixed by running `python3 gates/spec_index.py --update` and re-running the fast tier (see Test evidence above, second run is the reported one).

## Open findings

None.

## Next steps

None — loop_state is terminal.

## Resolution path

Not applicable — loop_state is terminal (`landed`).
