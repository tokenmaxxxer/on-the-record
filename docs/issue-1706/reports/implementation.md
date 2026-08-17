---
code_under_review:
  - on-the-record/commands/run.md
  - gates/test_report_contract_directive.py
type: docs
breaking: false
verdict: pass
loop_state: landed
---

# issue-1706: orchestrator report contract, encoded in the directive

## What was done

Added a "보고 계약" (report contract) block to `on-the-record/commands/run.md`
directly under the existing 의미론적 효과 프레이밍 (issue-320) instruction,
stating four obligations layered on top of what `report-framing-check.sh`
already gates:

1. **Lead line** — the first line of a PR/board report states the turn's
   outcome in one sentence, before the enumerated content.
2. **Fixed 4-part order** — 해결된 문제 → 이전 비용 → 새로 가능해진 것 →
   아직 남은 것, always in that order, never interleaved.
3. **Per-claim source ref** — every status/defect claim in any of the four
   parts carries an inline source (PR/issue/commit/measurement).
4. **Bullet cap** — at most 5 bullets per part.

Added `gates/test_report_contract_directive.py`, shaped like the existing
`gates/test_call_shape_and_report_framing_docs.py` /
`gates/test_report_framing_check.py` directive-content tests: it reads
`run.md` and asserts each of the four obligations' key phrases are present,
plus that the contract text appears before the sentence noting
`report-framing-check` only gates the four parts' presence (ordering check
that the contract is stated as an addition, not a restatement).

## Why

Issue #1706: operator feedback that orchestrator reports read as bare
enumerations and fight the framing hook — the hook enforces the four parts'
*presence* but not lead-line, ordering, or evidence linking. This closes
that gap by stating the missing obligations in the directive text the
orchestrator session reads every turn (`run.md`), the same mechanism
issue-320's framing instruction already uses.

## Upstream

Based on: docs/issue-320's existing 프레이밍 instruction in
`on-the-record/commands/run.md` (lines ~161-166) and its paired gate
`gates/test_report_framing_check.py`.

## code_under_review

- on-the-record/commands/run.md
- gates/test_report_contract_directive.py

## Test run

```
$ python3 gates/test_report_contract_directive.py
ok - t_run_md_states_bullet_cap
ok - t_run_md_states_fixed_part_order
ok - t_run_md_states_lead_line_rule
ok - t_run_md_states_per_claim_source_ref
ok - t_run_md_ties_contract_to_report_framing_check
5/5 passed

$ python3 gates/test_report_framing_check.py
ok - t_address_only_reply_blocked
ok - t_empty_message_noop
ok - t_four_element_reply_passes
ok - t_mission_board_has_done_flow_note
ok - t_non_report_reply_noop
ok - t_run_md_has_framing_instruction
6/6 passed

$ python3 gates/test_call_shape_and_report_framing_docs.py
ok - t_run_md_states_flag_consistency_rule
ok - t_run_md_states_report_framing_convention
2/2 passed
```

`report-framing-check.sh` itself was not modified — the acceptance
criterion's "empty state" (hook behavior unchanged) is verified by
`test_report_framing_check.py` passing unmodified against the hook script,
which was not touched.

## What did not work

None.

## Rationale for deviations

None — no deviation from the issue's acceptance criteria occurred.

## Open findings

None.

## Doc placement

- Directive text (the report contract itself) belongs in
  `on-the-record/commands/run.md`, the session-read directive doc — same
  placement as the issue-320 framing instruction it extends. No new
  env var, dependency, or migration was introduced, so no handbook entry
  is required.

## Test-tier note (issue #1518)

`.on-the-record/test-tiers.json` present at repo root; its `fast` tier is
`python3 -m pytest -q -m "not slow"` (budget 300s). The two new/touched
gate files are plain `python3 <file>` scripts run directly above, not
pytest-collected in this session; no `slow`-tier trigger path
(`spawn.py`, `tests/test_spawn.py`, `on-the-record/hooks/*.sh`,
`on-the-record/hooks/test_*.py`) was touched by this change.
