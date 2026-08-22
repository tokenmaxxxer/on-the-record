---
code_under_review:
  - spawn.py
  - gates/record_lint.py
  - on-the-record/gates/record_lint.py
  - on-the-record/hooks/skill-verdict-guard.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_skill_verdict_guard.py
  - gates/test_record_lint.py
  - tests/test_spawn_directive_assembly.py
  - docs/handbooks/skill-verdict-obligation.md
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# Implementation — per-mounted-skill verdict obligation (issue #2039)

canonical: docs/issue-2039/proposals/2026-08-22-per-skill-verdict-obligation.md (read this session)
skill-verdict: implementation-blueprint — not-applicable: the write set (a Stop hook + one canonical check function + a directive line) was fully frozen by the already-approved phase-1 proposal (PR #2042); no fresh architecture/pattern decision was open in phase 2.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-style pattern decision arose — this is a shape-check regex function plus a transcript-scanning shell hook, mirroring an existing sibling (`deviation-log-guard.sh`) as-is, not a new pattern choice.
skill-verdict: implementation-complexity-coupling-management — not-applicable: the change adds one new hook file and one new canonical function, not a coupling/cohesion refactor of existing code.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: the mounted-skill/verdict-line cross-check operates on a small, bounded per-spawn set (a handful of skill names); no performance-cliff-shaped decision (loop-membership testing at scale, algorithm choice) was involved.
skill-verdict: brand-design-brand-identity-strategy — not-applicable: canonical: this session's own mounted-skill list (see task prompt) — this is internal enforcement-hook infrastructure with no visual/brand asset surface (cross-family match, issue #2001).
skill-verdict: finance-unit-economics-proposal-shape — not-applicable: canonical: this session's own mounted-skill list (see task prompt) — no unit-economics/pricing proposal was written; this deliverable is a shape-only enforcement hook (cross-family match, issue #2001).

## What was done

Each proposal build-plan item, built as specified:

1. `spawn.py` (git sha 4cb699a9) — immediately after the existing #1960 스킬 점검 nudge, when either mounted-skill block fired, appends one new directive line (스킬-verdict 의무, 이슈 #2039) stating the `skill-verdict: <name> — applied: ... | not-applicable: ...` obligation. Guarded by the exact same `if skill_sources or role_source["skills"]:` condition as the #1960 nudge, so a zero-mounted-skill session stays byte-identical.
2. `gates/record_lint.py` and its tracked mirror `on-the-record/gates/record_lint.py` (git sha fef59a27) — added `skill_verdict_reason_check(text, mounted)` (per-name line presence + non-empty-after-dash check) and `record_skill_verdicts_in(work, mounted)` (the `(work, cfg)`-shaped CI/diff-scoped wrapper, following `record_refusal_reasoned`'s existing pattern).
3. `on-the-record/hooks/skill-verdict-guard.sh` (new Stop hook) — reads `transcript_path` off the Stop event JSON, scans the transcript's first user message for the two known mounted-skill line prefixes (`마운트된 스킬(--skills`, `이 역할은 skill-repository(`), extracts and unions the skill names (a name mounted by both assembly points counts once), reads the current branch's own role record file directly, and delegates to `skill_verdict_reason_check` for the shape check. Registered in `on-the-record/hooks/hooks.json`'s `Stop` array immediately after `deviation-log-guard.sh`.
4. Tests added, fenced verbatim:

```
on-the-record/hooks/test_skill_verdict_guard.py:
  t_zero_mounted_skills_is_noop
  t_missing_skill_verdict_line_is_blocked
  t_empty_reason_skill_verdict_line_is_blocked
  t_both_assembly_points_union_without_double_count
  t_satisfied_skill_verdicts_pass
  t_stop_hook_active_emits_nothing
  t_malformed_payload_fails_closed
  t_orchestrate_off_is_noop

gates/test_record_lint.py:
  t_2039_skill_verdict_missing_line_flagged
  t_2039_skill_verdict_empty_reason_flagged
  t_2039_skill_verdict_satisfied_passes
  t_2039_zero_mounted_skills_is_noop

tests/test_spawn_directive_assembly.py:
  SkillVerdictObligationLine::test_mounted_skill_directive_states_verdict_obligation
  SkillVerdictObligationLine::test_zero_mounted_skills_directive_omits_verdict_obligation
```

5. `docs/handbooks/skill-verdict-obligation.md` — short handbook entry stating the obligation and line shape, referenced from the hook's refusal message.
6. `tests/test_spawn_directive_assembly.py` — `SkillVerdictObligationLine` class asserting the new directive line's presence when a skill is mounted (inherits `SkillTriggerLines`' repo/skill-dir fixtures) and its absence for a zero-mounted-skill session.
7. `docs/specs/enforcement-boundary.md` and `docs/specs/generated-paths.md` — spec rows for the new hook, required by `gate-registration-guard.sh`.

## Rationale for deviations

canonical: this session's own diff (git log -p on this branch)
No scope-exceeded stop and no alternative-swap from the proposal's build plan — one implementation detail not spelled out in the proposal surfaced mid-build: `on-the-record/gates/record_lint.py` is a tracked mirror of `gates/record_lint.py` (their commit-subject histories line up per `git log -- on-the-record/gates/record_lint.py` vs `git log -- gates/record_lint.py`) that the `skill-verdict-guard.sh` hook resolves before the repo-root copy — an early commit attempt raised `AttributeError: module 'record_lint' has no attribute 'skill_verdict_reason_check'` when the hook loaded the stale mirror. Fixed inline within the frozen write set by mirroring the same two functions into that copy, not a design change.

## What did not work

An early regex for `_SKILL_VERDICT_LINE` used a character class `[-*]` as the name/reason separator alternative alongside the em dash. `\s*` around that separator matches newlines, so on a real multi-line record the non-greedy name group spanned into the following markdown line for an empty-reason case, and separately a plain `-` inside that same character class truncated a hyphenated skill name (e.g. `implementation-blueprint` cut at its first internal hyphen). Fixed by anchoring the separator to the literal em dash (`—` — the character spawn.py's own directive text and the required line shape always use) and matching per `text.splitlines()` line instead of a whole-text regex relying on `(?m)^...$`.

## Test tier

`.on-the-record/test-tiers.json` declares a fast tier (`pytest -q -m "not slow"`) and a slow tier gated on `spawn.py`/`on-the-record/hooks/*.sh` changes — this diff touches both trigger paths, so both tiers were run.

canonical: acceptance: python3 -m pytest -q -m "not slow" — result: PASS
```
2546 passed, 19 xfailed, 2 xpassed in 43.30s
```

canonical: acceptance: python3 -m pytest -q -m slow — result: PASS
```
111 passed, 1 xfailed, 1 xpassed in 262.51s (0:04:22)
```

## Upstream basis

- docs/issue-2039/proposals/2026-08-22-per-skill-verdict-obligation.md (PR #2042)
- docs/issue-2039/reports/implementation/survey.md

## Open findings

None.
