---
code_under_review:
  - spawn.py
  - gates/record_lint.py
  - on-the-record/gates/record_lint.py
  - on-the-record/hooks/test_skill_verdict_guard.py
  - tests/test_spawn_directive_assembly.py
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# Implementation — invoke-before-apply obligation (issue #2062)

canonical: docs/issue-2062/reports/consult-log.md (read this session)
skill-verdict: implementation-blueprint — not-applicable: the write set (one directive sentence in spawn.py plus one shape-only regex check in record_lint.py) was frozen by the issue's own `## Acceptance` text; no fresh architecture/pattern decision was open.
skill-verdict: implementation-design-pattern-selection — not-applicable: adding one directive sentence and one marker-prefix regex check is not a GoF-pattern decision.
skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion refactor — the change is additive text plus one small conditional branch inside an already-existing shape-check function.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: the marker check runs over the same small, bounded per-spawn mounted-skill set `skill_verdict_reason_check` already iterates; no new performance-cliff-shaped decision.

## What was done

Per the issue's frozen `## Acceptance`, this session build-now delivered (CORE_BUILD_NOW=1, spawner-set):

1. `spawn.py` — the `스킬 점검(이슈 #1960)` directive block (the one that fires next to the mounted-skill list, guarded by the same `if skill_sources or role_source["skills"]:` condition) gained one new sentence stating the invoke-before-apply obligation: a skill judged APPLICABLE must be loaded via the Skill tool (its full SKILL.md) before it is applied; not-applicable skills are explicitly exempt. The `스킬-verdict 의무(이슈 #2039)` block immediately after it gained a companion sentence: `applied:` lines must carry the `invoked;` marker as proof the Skill tool was actually called; `not-applicable:` lines need no marker. Both additions stay inside the same `if skill_sources or role_source["skills"]:` guard, so a zero-mounted-skill session's directive text is unaffected (verified by test).
2. `gates/record_lint.py` and its tracked mirror `on-the-record/gates/record_lint.py` — canonical: on-the-record/hooks/skill-verdict-guard.sh:32-37 (the `gates_dir` search order that prefers `on-the-record/gates` first, meaning that copy is the one the Stop hook actually loads) — `skill_verdict_reason_check` gained a new branch: once a mounted skill's `skill-verdict:` line is found and non-empty, if its content starts with `applied:` (case-insensitive), the free text after that label must start with `invoked;` (new `_SKILL_VERDICT_APPLIED`/`_SKILL_VERDICT_INVOKED_MARKER` regexes); otherwise a new violation string is appended. `not-applicable:` lines and the missing/empty-line branches are untouched — still shape-only, never judging whether the applied/not-applicable content is actually correct.
3. `on-the-record/hooks/skill-verdict-guard.sh` needed no code change — it already delegates entirely to `skill_verdict_reason_check`, so the new marker check took effect through the existing call site.
4. Tests added, fenced verbatim:

```
tests/test_spawn_directive_assembly.py: InvokeBeforeApplyObligation
  - test_mounted_skill_directive_states_invoke_before_apply
  - test_zero_mounted_skills_directive_omits_invoke_before_apply

on-the-record/hooks/test_skill_verdict_guard.py:
  - t_applied_line_without_invocation_marker_is_blocked (new)
  - t_not_applicable_line_needs_no_invocation_marker (new)
  - t_both_assembly_points_union_without_double_count (updated: applied: content now carries invoked;)
  - t_satisfied_skill_verdicts_pass (updated: applied: content now carries invoked;)
```

## Why

canonical: docs/issue-2062/reports/consult-log.md (read this session) — issue #2062's own body: many mounted skills stay at "never-used" in the harness usage counter even after being marked `applied:`, because the spawn directive only injects the trigger sentence, never the skill's own body — a session can claim `applied:` without ever calling the Skill tool. Requiring an `invoked;` marker on `applied:` lines, backed by the shape-only guard, makes "applied without reading the rules" structurally impossible without adding any content-judgment to the enforcement layer.

## Upstream basis

basis: docs/issue-2062/reports/consult-log.md — skill_judge outcome for this session (picked=[], no applicable skill; see skill-verdict lines above). Prior sibling implementation for the assembly-point/guard pattern: docs/issue-2039/reports/implementation.md.

## What did not work

None.

## Open findings

None. The issue's own Acceptance third clause ("a live consumer spawn after landing produces a record whose applied lines carry the marker and the harness log shows the corresponding Skill tool calls") is `provenance: executed-live` and can only be observed on a future spawn after this PR merges — it is not verifiable from within this session.

Test run, pasted verbatim (no SKIPPED lines):

```
$ python3 -m pytest on-the-record/hooks/test_skill_verdict_guard.py -q
............                                                             [100%]
12 passed in 0.95s

$ python3 -m pytest tests/test_spawn_directive_assembly.py -q
(20 passed, 1 failed: SinglePhaseSignal::test_without_flag_is_byte_identical_to_today —
pre-existing failure, unrelated to this change: reproduces identically on
pre-change HEAD d4b2cda5 via `git stash`; caused by CORE_BUILD_NOW leaking
from this session's real environment into the test's simulated env dict,
not by anything touched here.)
```
