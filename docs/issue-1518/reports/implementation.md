---
code_under_review:
  - gates/test_tier_contract.py
  - tests/test_test_tier_contract.py
  - on-the-record/hooks/test-tier-directive.sh
  - on-the-record/hooks/test_test_tier_directive.py
  - on-the-record/hooks/hooks.json
  - docs/handbooks/operations.md
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
  - docs/specs/reconciled-index.md
type: feature
breaking: false
canonical: "python3 -m pytest tests/test_test_tier_contract.py on-the-record/hooks/test_test_tier_directive.py -v -- result: 6 passed (this session's own live run; full transcript under Acceptance below)"
verdict: pass
loop_state: landed
---

## What was done

Implemented issue #1518's phase-1 design as working code in the same PR
(canonical: `gh issue view 1518 --comments`, this session's own live
read — the issue's one comment is the exact string `APPROVE
issue-1518/implementation`, posted by approvers.md account JiwonJung94;
single-account mode, role-handoff contract v3 s19). Landed on this
branch as commit dc033b2c (canonical: `git log --oneline -1`).

canonical: gates/test_tier_contract.py, committed this branch as dc033b2c

- `gates/test_tier_contract.py`: `load_contract()`/`parse_contract()`
  parse a target repo's `.on-the-record/test-tiers.json` (fast
  command + `budget_seconds`, default 300; optional slow command +
  `trigger_change_classes`); an absent or malformed contract resolves to
  `None`, the same value the no-contract path already handles.
  `select_tier()` picks `"slow"` only when a changed path matches a
  declared trigger glob. `no_contract_gap()` is the req-3
  no-silent-full-run path: a measured-cost + gap-note record for a
  verification role to write into its own record when no contract
  exists.
- `on-the-record/hooks/test-tier-directive.sh`: an observe-only
  `UserPromptSubmit` directive stating the tier-contract policy,
  registered in `on-the-record/hooks/hooks.json`'s `UserPromptSubmit`
  array (req 4 — deployed-hook surface, directive-only, no gating yet),
  and registered in `docs/specs/enforcement-boundary.md` and
  `docs/specs/generated-paths.md` per `gate-registration-guard.sh`.
- `docs/handbooks/operations.md`: a new "Test-tier contract for target
  repos (issue #1518)" subsection next to the existing #1490 pre-merge
  tier table, naming the JSON schema and the no-contract path.
  `docs/specs/reconciled-index.md` regenerated to match
  (`gates/spec_index.py --update`).
- `tests/test_test_tier_contract.py` and
  `on-the-record/hooks/test_test_tier_directive.py`: the acceptance
  tests (three in the module the issue names, one existence-check for
  the directive line's presence in the hook surface).

Verification-role *consumption* (req 2) is delivered at the module
level only — `gates/test_tier_contract.py` is what
execution-observation/conformance-review/pre-merge regression would
call. Wiring the role JSON specs themselves to call it is out of scope
for this proposal's frozen write set (see the proposal's "Out of
scope"); it would touch `roles/*.json`, a different write surface
requiring its own `role_spec_shape.py`-gated review.

The #1493 merge-point naming (req 5) is a design statement, not code:
recorded in the current-state survey's "#1493 merge point" section
(docs/issue-1518/reports/implementation/survey.md) — the contract's
field names (`fast`/`slow`/`budget_seconds`/`trigger_change_classes`,
plus `no_contract_gap()`'s output shape) are what #1493's future
check-run artifact should reuse rather than invent a second convention.

## Why

Generalizes #1490's landed test-tiering discipline (fast tier by
default, budget-bounded, slow tier opt-in) from this one repo into a
file convention any target repo can declare, per the operator's
2026-08-14 consult directive cited in the issue body. Rationale for the
file-vs-`roles/*.json` and JSON-vs-YAML choices is recorded in the
proposal's Rationale section
(docs/issue-1518/proposals/2026-08-15-test-tier-contract.md).

## Upstream / basis

- Based on: #1490's landed shape, `docs/handbooks/operations.md`'s
  pre-merge regression policy table (commit 9e16671e).
- docs/issue-1518/reports/implementation/survey.md
- docs/issue-1518/proposals/2026-08-15-test-tier-contract.md

## Acceptance

checked: python3 -m pytest tests/test_test_tier_contract.py on-the-record/hooks/test_test_tier_directive.py -v — result: pass (canonical: this session's own live run, transcript below)

```
tests/test_test_tier_contract.py::test_slow_trigger_by_change_class PASSED
on-the-record/hooks/test_test_tier_directive.py::t_directive_is_silent_when_orchestrate_off PASSED
tests/test_test_tier_contract.py::test_no_silent_full_run PASSED
tests/test_test_tier_contract.py::test_contract_parse_and_budget PASSED
on-the-record/hooks/test_test_tier_directive.py::t_directive_registered_in_hooks_json PASSED
on-the-record/hooks/test_test_tier_directive.py::t_directive_states_test_tier_contract_policy PASSED
6 passed in 0.87s
```

canonical: `git show dc033b2c --stat` (this session's own commit, this branch)

Per-acceptance-item mapping, each present in the committed test module:

- test_contract_parse_and_budget — fixture yields fast command + budget;
  a malformed contract resolves to the same `None` a no-contract repo
  gets, in the same module.
- test_slow_trigger_by_change_class — a declared trigger path selects
  slow; a non-trigger (docs-only) path stays fast.
- test_no_silent_full_run — no-contract fixture records the measured
  full-run cost plus a gap note, nothing skipped silently.
- Directive line in the deployed hook surface, observe-only,
  existence-checked by test — covered by
  t_directive_registered_in_hooks_json and
  t_directive_states_test_tier_contract_policy in the same module.

## What did not work

None — no attempted approach was undone or replaced during this build.

## Open findings

None.
