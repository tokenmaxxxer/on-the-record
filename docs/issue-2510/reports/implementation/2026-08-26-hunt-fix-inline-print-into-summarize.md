---
proposal: docs/issue-2510/proposals/2026-08-26-fix-inline-print-into-summarize.md
---

# Hunt record — fix-inline-print-into-summarize

## after-proposal — stance 1: summarize()'s branch logic could produce a wrong/misleading message for a verdict-count combination not considered, and whether other modules depend on the exact old string/exit-code

Verdict: FINDING — summarize() conflates "0 gradable criteria" with "graded, all UNKNOWN" when advisory is empty but empty_state is False (unknown==total is vacuously true at total==0)
Kind: design-error
Seed: gates/requirement_met.py summarize() (new function replacing main()'s inline print logic), gates/test_requirement_met.py t_summarize_* fixtures
cap_seconds: unspecified (standalone invocation, no dispatcher-provided cap)
tier: default
diff_stat_lines: ~65 (gates/requirement_met.py) + new t_summarize_* fixtures in gates/test_requirement_met.py
started_at: 2026-08-26T00:00:00Z
ended_at: 2026-08-26T00:30:00Z

### Reproduce
```
python3 -c "
import gates.requirement_met as rm
result = {'empty_state': False, 'blocking_reasons': [], 'advisory': []}
print(rm.summarize(result))
"
```

### Observed
```
('미채점 (전부 UNKNOWN) — 0개 기준 중 실제로 검증된 것이 없다. 차단 사유는 없지만 이건 게이트 통과가 아니다.', 0)
```
canonical: this session's own execution of the `python3 -c` command above, run 2026-08-26 from the repo root against the current worktree state of gates/requirement_met.py (commit 9c59a0988).

### Expected
For total == 0 (no criteria in advisory) with empty_state False, the function should not silently report "채점했지만 전부 UNKNOWN" (graded, all UNKNOWN) for a set of zero graded items — that's the exact "no criteria" vs "criteria graded, nothing verified" conflation issue #2231/#2510 exist to keep distinct. summarize()'s docstring claims to fully partition the space into three branches (empty_state / blocked / graded-none-met), but total==0 falls vacuously into the all-UNKNOWN branch instead of a distinct outcome.

Caveat on liveness: with the current check()/grade() implementation this exact input cannot arise from a real gh-backed run — grade() only returns empty_state=False when items (and therefore criteria/advisory) is non-empty (gates/requirement_met.py:391-401), and check()'s two other advisory=[] paths (gh body/diff fetch failure, gates/requirement_met.py:499-507) always set blocked=True, routing to the "blocked" branch before reaching this one. So this is not reachable today via `python3 gates/requirement_met.py <issue> <pr>`; it is a latent gap in summarize()'s stated contract as a pure function (already exercised directly with hand-built dicts by the new unit tests, not only through check()), not an observed CLI-level regression.

acceptance: grep -rn "게이트 통과" --include=*.py --include=*.md --include=*.sh . | grep -v "gates/requirement_met.py\|gates/test_requirement_met.py" — result:
```
gates/acceptance_gate.py:270:        print("게이트 통과")
gates/design_research_consult.py:79:        print("게이트 통과")
directive_assembly.py:217:    "게이트 통과 모양(이슈 #2479): 아래 두 게이트는 거절되면 커밋을 못 "
gates/acceptance_authoring_rule.py:118:        print("게이트 통과")
gates/assumption_ledger.py:132:        print("게이트 통과")
gates/ci.py:699:        print("게이트 통과")
gates/pr_reference.py:119:        print("게이트 통과")
gates/requirement_intake_consult.py:75:        print("게이트 통과")
gates/artifact_smoke_rule.py:234:        print("게이트 통과")
gates/issue_bundling.py:137:        print("게이트 통과")
(remainder: historical docs/issue-*/reports/*.md prose only, no other .py module parses requirement_met.py's stdout or exit code besides gates/ci.py's `requirement_met.check(...)["blocked"]`, untouched by this diff)
```
This confirms no other module string-matches requirement_met.py's own stdout, and the new "게이트 통과 아님 —" / "미채점 (전부 UNKNOWN) —" strings neither equal nor start with the legacy pass prefix "게이트 통과 (" — so the composition/collision angles named in the prompt did not reproduce; the total==0 vacuous-truth gap above is the one finding that did.
