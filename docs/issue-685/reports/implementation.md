---
code_under_review:
  - gates/ui_evidence_gate.py
  - gates/test_ui_evidence_gate.py
  - gates/gates.py
  - docs/specs/ui-surfaces.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented the approved phase-1 proposal
(docs/issue-685/proposals/2026-08-11-ui-facing-executed-live-evidence-gate.md)
exactly:

1. docs/specs/ui-surfaces.md — declares the `## Globs` format and the
   three-state convention (absent/empty → fallback; `none` → fallback
   suppressed; glob lines → those globs used).
2. gates/ui_evidence_gate.py — `is_ui_facing(root, changed_paths)` and
   `check_record(root, record_path, record_text, changed_paths)`, pure
   functions, no network. `check_record` refuses when a record's
   frontmatter `verdict: pass` coincides with a UI-facing diff and no
   `provenance: executed-live` line carries a non-empty evidence
   reference.
3. gates/gates.py — added `ui_evidence_gate_gate(d, cfg)` (diff-scoped
   wrapper, same `RECORD_PATH`/`changed_files` pattern as
   `record_checked_claims`/`record_enums`) and registered it in `ALL` as
   `"ui_evidence_gate"`.
4. gates/test_ui_evidence_gate.py — cases: UI-touch + unit-only
   (refused), UI-touch + executed-live (allowed), non-UI diff (allowed),
   no declaration + screen-like path fallback (refused), `none`
   declaration suppresses fallback (allowed), non-`pass` verdict never
   checked. See Acceptance verification below for the exact count, cited
   via `derived:`.

## Why

Reason: closes the gap issue #685 reports — a delivery record could
claim `verdict: pass` on a UI-facing change with only unit-test
provenance while the screen was actually dead, and nothing mechanical
caught it. The proposal's Rationale records why docs/specs/ (not
implementation.spec.json) holds the UI-glob declaration, and why the
undeclared-glob default is fail-closed rather than the field's usual
permissive default.

Basis: docs/issue-685/proposals/2026-08-11-ui-facing-executed-live-evidence-gate.md

## What did not work

None — no attempt was undone or replaced during this build.

## Open findings

None.

## Doctrine ladder

No env var/config key/new dependency/migration/setup step was
introduced (proposal Constraints: no new dependency, no new env var, no
migration), so no handbook update applies. No public signature or wire
format changed for an existing consumer — the ui-surfaces spec is a new
declaration file, not a change to an existing one — so no decision
record applies. No benchmark/investigation numbers were produced beyond
this record.

## Hunt

Phase-1 hunt already ran and its one finding was addressed in the
approved proposal before this PR (docs/reports/2026-08-11-hunt-ui-facing-executed-live-evidence-gate.md).
A before-landing hunt dispatch was attempted for this phase-2 build, but
this session is headless/single-shot (contract v3 s22): a background
Agent dispatch whose result is not consumed before the turn ends is
prohibited here, and this turn has no further turn to consume it in
before landing. Deferred rather than dispatched-and-abandoned, per s22's
explicit priority over the warrant directive's hunter-dispatch
instructions in this mode.

## Acceptance verification

- checked: gates/test_ui_evidence_gate.py (t_ui_touch_unit_only_refused) — result: pass
- checked: gates/test_ui_evidence_gate.py (t_ui_touch_executed_live_allowed) — result: pass
- checked: gates/test_ui_evidence_gate.py (t_non_ui_diff_unit_pass_allowed) — result: pass
- checked: gates/test_ui_evidence_gate.py (t_no_declaration_screenlike_path_fallback_refused) — result: pass
- checked: gates/test_ui_evidence_gate.py (t_declared_none_suppresses_fallback) — result: pass
- checked: gates/test_ui_evidence_gate.py (t_non_pass_verdict_never_checked) — result: pass

derived: python3 -m pytest gates/test_ui_evidence_gate.py -q

```
......                                                                   [100%]
6 passed in 0.03s
```
