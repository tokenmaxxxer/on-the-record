---
code_under_review:
  - on-the-record/hooks/report-framing-check.sh
  - on-the-record/commands/run.md
  - gates/test_report_framing_check.py
  - on-the-record/hooks/test_report_framing_check_live.py
  - docs/specs/reconciled-index.md
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# Implementation — skills-utilization report element (issue #2044)

canonical: docs/handbooks/skill-verdict-obligation.md (read this session)
skill-verdict: implementation-blueprint — not-applicable: the write set (one regex-gated element added to an existing shell+embedded-python Stop hook, plus a directive paragraph) was fully determined by the frozen issue text — no fresh architecture/module-boundary decision was open.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-style pattern decision arose — the added check is a same-shape sibling of the hook's own existing four ELEMENTS regex entries, extended in place.
skill-verdict: implementation-complexity-coupling-management — not-applicable: the change adds one conditional dict entry and a bounded docs/issue-<n>/reports/ scan to an existing single-purpose hook; not a coupling/cohesion refactor of existing code.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: the repo scan walks a small, bounded set of docs/issue-<n>/reports/**/*.md files per report turn (a handful of files at most); no performance-cliff-shaped decision was involved.
skill-verdict: upstream-defect-report-convention — not-applicable: cross-family match (issue #2001) via keyword overlap with "report"; this change is an internal hook/directive edit, not an upstream defect filing.
skill-verdict: conformance-review-severity-classification — not-applicable: cross-family match (issue #2001); no review-role risk-weighting of a recorded finding was involved — this is direct implementation, not review.

## What was done

1. `on-the-record/hooks/report-framing-check.sh` — added a fifth,
   conditionally-required framing element, `skills-utilization`, to the
   existing four issue-320 elements. Gating: the hook now reads its own
   `pwd -P` as `REPO`, extracts every `이슈 #<n>` cited in the reply, and
   for each walks `docs/issue-<n>/reports/**/*.md` looking for a line
   matching the same `skill-verdict:` line shape issue #2039's
   `skill-verdict-guard.sh`/`record_lint.py` already canonicalize. If any
   such line exists under a cited issue's `reports/` tree, the reply is
   a >=1-mounted-skill delivery and must also match a loose "스킬 ...
   (적용|not-applicable|해당없|미해당|사용)" pattern (shape-only, same
   posture as the existing four elements — never judges whether the
   stated applied/not-applicable content is correct). A repo-scan error
   (missing dir, unreadable file) degrades to "not mounted", never to a
   refusal. A reply citing only zero-skill issues is byte-unaffected —
   `ELEMENTS` never gains the fifth key, so `missing` cannot name it.
2. `on-the-record/commands/run.md` — added a "스킬 활용 요약 —
   skills-utilization" paragraph immediately before the existing "링크
   의무" paragraph, in the same 의미론적 효과 프레이밍 block the four
   issue-320 elements live in. States: the element applies only when the
   role session mounted >=1 skill; its content must be sourced from the
   role record's `skill-verdict: <name> — applied: ... |
   not-applicable: ...` lines (docs/handbooks/skill-verdict-obligation.md)
   and never invented by the orchestrator; zero-mounted-skill work is
   unaffected; and names which hook enforces it.
3. Tests, fenced verbatim:

```
gates/test_report_framing_check.py:
  t_mounted_skill_delivery_without_utilization_blocked
  t_mounted_skill_delivery_with_utilization_passes
  t_zero_skill_delivery_unaffected

on-the-record/hooks/test_report_framing_check_live.py:
  t_mounted_skill_delivery_without_utilization_is_blocked
  t_mounted_skill_delivery_with_utilization_is_silent
  t_zero_skill_delivery_is_unaffected
```

   Both suites' new "mounted" cases cite issue #2039, whose own landed
   record (`docs/issue-2039/reports/implementation.md`) already carries
   real `skill-verdict:` lines — reused rather than inventing a fixture
   record, so the test exercises the actual repo scan. The "zero-skill"
   case cites issue #320, whose `reports/` tree carries no
   `skill-verdict:` line. Both test harnesses' hook-invoking helper now
   sets `cwd=<repo root>` on the subprocess call so the hook's `pwd -P`
   resolves to the real tree being scanned.
4. `docs/specs/reconciled-index.md` — regenerated via
   `python3 gates/spec_index.py --update` because `run.md` is a tracked
   spec file (`spec-index-preflight.sh` requirement).

## Rationale for deviations

None — build matched the issue text as scoped; no scope-exceeded stop
and no alternative-swap occurred.

## What did not work

An earlier version of the "mounted, no utilization" test fixture message
used the sentence "마운트된 스킬이 실제로 적용됐는지 아무도 확인할 수
없는 비용을 치렀는데" — which itself matches the new `skills-utilization`
regex (스킬 ... 적용), so that fixture did not actually exercise a
missing-element case; the hook's response for it was silent rather than
a block. Reworded to "마운트된 스킬이 실제로 쓰였는지" (drops "적용") so
the fixture omits the element its test name claims to be missing.

## Test tier

`.on-the-record/test-tiers.json` declares a fast tier (`pytest -q -m "not
slow"`) and a slow tier gated on `on-the-record/hooks/*.sh` /
`on-the-record/hooks/test_*.py` changes — this diff touches both trigger
paths, so both tiers were run. The slow-tier run in this session's own
shell carries a leaked `CORE_BUILD_NOW=1` from the spawning environment,
which one unrelated pre-existing test
(`SinglePhaseSignal::test_without_flag_is_byte_identical_to_today`)
asserts is absent from a subprocess env it builds — re-run with that var
unset to isolate it as session-environment leakage, not a regression
from this diff.

canonical: acceptance: python3 -m pytest -q -m "not slow" — result: PASS
```
2566 passed, 19 xfailed, 2 xpassed in 39.14s
```

canonical: acceptance: env -u CORE_BUILD_NOW python3 -m pytest -q -m slow — result: PASS
```
111 passed, 1 xfailed, 1 xpassed in 265.73s (0:04:25)
```

## Upstream basis

- Issue #2044 (Acceptance section, frozen)
- docs/handbooks/skill-verdict-obligation.md (issue #2039)
- docs/issue-2039/reports/implementation.md (skill-verdict line shape and gates/record_lint.py's `skill_verdict_reason_check`, reused as the shape reference)

## Open findings

None.
