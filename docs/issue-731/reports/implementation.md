---
code_under_review:
  - on-the-record/commands/run.md
  - gates/test_call_shape_and_report_framing_docs.py
type: doc
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #731

## What was done

Delivered the approved phase-1 proposal
(`docs/issue-731/proposals/2026-08-11-proactive-call-shape-and-report-framing.md`):

- Extended `on-the-record/commands/run.md`'s existing `## 같은 모양의
  재발은 마킹하거나 기계가 잡는다 (#419)` section with an explicit
  proactive statement of the row-7 flag-consistency rule: call sites
  sharing the same `(argv[0], argv[1])` must use the same semantic flag
  shape, stated as something to follow when writing a new call site —
  not only as a description of what `call-shape-guard.sh:153-165`
  catches after the fact.
- Found that row 23's four-element report framing (resolved
  problem / prior cost / newly possible / still broken, issue #320) is
  **already** stated proactively in `run.md` at the `의미론적 효과
  프레이밍` bullet (lines 160-165) — pre-existing from issue #320's own
  delivery, not something this pass needed to add. No edit was needed
  for row 23; verified it's present and cross-referenced by
  `report-framing-check.sh`'s own header comment.
- Added `gates/test_call_shape_and_report_framing_docs.py`, the
  acceptance test named in issue #731 — asserts `run.md` names both
  conventions (`argv[0]`/`argv[1]`/`call-shape-guard.sh` for row 7, the
  four framing-element terms for row 23).

## Why

Both conventions were previously learned only from a gate's deny/block
message, with no proactive documentation a role could read before
hitting the gate. Row 7 is a hard-shape convention (call-shape-guard.sh
denies on violation); row 23 is advisory. Per the issue, both belong in
on-the-record's own docs (not a role rulebook) since they're
call-site/report conventions, not role-specific.

## Upstream

Basis: `docs/issue-731/proposals/2026-08-11-proactive-call-shape-and-report-framing.md`,
approved via `APPROVE issue-731/implementation` (issue #731 comment).

## Doc placement

- [x] `on-the-record/commands/run.md` — proactive convention statement
  (row 7 addition; row 23 already present).
- [x] `gates/test_call_shape_and_report_framing_docs.py` — the
  acceptance-check test named in the issue.

## Rationale for deviations

The approved proposal's `## Out of scope` listed "writing the
acceptance unit test... unless the approver wants it folded in" as
optional. The phase-2 delivery instruction for this session explicitly
asked for that test to be added and run to 0 failures, so it was folded
in as directed. This is the only divergence from `## What will be
done`; the write set otherwise matches the proposal (`run.md`), plus
the one added test file.

## What did not work

None.

## Open findings

None open. The before-landing hunt (stance 0, cap 120s) found the
new run.md text overclaimed `subprocess_call_shape_divergence`'s
coverage — the gate only recognizes list-literal subprocess args, not
tuple-literal ones with identical divergent flags — full repro in
`docs/issue-731/reports/implementation/hunt-2026-08-11-proactive-call-shape-and-report-framing.md`.
Resolved in this record's own commit by qualifying the run.md claim
(list-literal-only recognition, "don't rely on the machine check,
match flag shape before writing") instead of asserting unqualified
mechanical enforcement — no gate/hook logic was touched, consistent
with the proposal's doc-only constraint.

closed_checks:
- doc-overclaim caveat (call-shape-guard list-literal-only recognition) — code_under_review: on-the-record/commands/run.md

## Verification run

derived: `python3 gates/test_call_shape_and_report_framing_docs.py && python3 gates/test_report_framing_check.py && python3 on-the-record/hooks/test_call_shape_guard.py && python3 gates/test_boundary.py`

```
ok - t_run_md_states_flag_consistency_rule
ok - t_run_md_states_report_framing_convention
2/2 passed
ok - t_address_only_reply_blocked
ok - t_empty_message_noop
ok - t_four_element_reply_passes
ok - t_mission_board_has_done_flow_note
ok - t_non_report_reply_noop
ok - t_run_md_has_framing_instruction
6/6 passed
(test_call_shape_guard.py: exit 0)
13/13 passed (test_boundary.py)
```

All 0 failures.
