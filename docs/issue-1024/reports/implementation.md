---
code_under_review:
  - on-the-record/hooks/directive.sh
  - gates/requirement_intake_consult.py
  - gates/test_requirement_intake_consult.py
  - tests/test_spawn.py
type: feature
breaking: false
# canonical: python3 -m pytest tests/test_spawn.py -k intake -v
verdict: pass
loop_state: landed
---

## Summary of work

canonical: docs/issue-1024/proposals/2026-08-12-requirement-intake-validity-consult.md (read this session)

Built the four write-set items listed in the approved phase-1
proposal: the directive text VALIDITY CONSULT block, the new gate
module, its unit tests, and the `tests/test_spawn.py` intake cases.

## Why

Upstream basis: docs/issue-1024/proposals/2026-08-12-requirement-intake-validity-consult.md

## What did not work

None.

## Doc-placement ladder

No env var, config key, new dependency, or migration introduced. No
benchmark/investigation numbers produced. No separate decision doc
needed — the alternative-and-reason content lives in the proposal's own
`## Rationale`.

## Verification run

canonical: python3 gates/test_requirement_intake_consult.py
```
$ python3 gates/test_requirement_intake_consult.py
ok - t_arbitrary_skip_reason_rejected
ok - t_consult_trace_passes
ok - t_neither_flagged
ok - t_skip_trivial_passes
4/4 passed
```

canonical: python3 -m pytest tests/test_spawn.py -k intake -v
```
$ python3 -m pytest tests/test_spawn.py -k intake -v
tests/test_spawn.py::RequirementIntakeValidityConsult::test_intake_with_consult_trace_passes PASSED
tests/test_spawn.py::RequirementIntakeValidityConsult::test_intake_with_skip_trivial_passes PASSED
tests/test_spawn.py::RequirementIntakeValidityConsult::test_intake_without_consult_or_skip_is_flagged PASSED
3 passed, 465 deselected in 0.17s
```

## Open findings

None.

## Hunt

closed_checks:
- after-proposal hunt (canonical: docs/issue-1024/reports/implementation/2026-08-12-hunt-requirement-intake-validity-consult.md, read this session): open-vocabulary skip-reason bypass, closed via the literal `trivial`-only match in `_CONSULT_SKIP`, covered by `t_arbitrary_skip_reason_rejected`.

resolved_findings:
- before-landing hunt (canonical: docs/issue-1024/reports/implementation/2026-08-12-hunt-requirement-intake-validity-consult.md, read this session): `validity-consult: <ref>` accepts any non-whitespace string, since no trace/consult record store exists to validate against. Not a new gap: proposal item 2 already names presence-only checking as "an accepted, known limitation shared with `acceptance_gate.py`'s own `unverifiable:` tag — verifying trace authenticity is out of scope for this gate." No code change; this line records the acknowledgment.
