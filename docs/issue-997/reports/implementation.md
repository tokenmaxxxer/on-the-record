---
code_under_review:
  - on-the-record/hooks/test_delegated_judgment_gate.py
type: test
breaking: false
canonical: python3 on-the-record/hooks/test_delegated_judgment_gate.py (this turn) — 26 passed
verdict: pass
loop_state: landed
---

## What was done
canonical: on-the-record/hooks/test_delegated_judgment_gate.py, this session's edits
Extended the 2-role seed fixture in
`on-the-record/hooks/test_delegated_judgment_gate.py` to a 3-role panel,
per the approved proposal
docs/issue-997/proposals/three-role-panel-fixture.md:

- Added `PERFORMANCE_ROLE` (write_scope
  `docs/issue-<n>/reports/performance-engineering.md`, judgment_axes
  `["performance"]`), reusing the already-assigned real axis-owning role
  named in the proposal's Rationale.
- Added `t_three_plus_role_panel_quorum_and_unanimous_support_approves`:
  3-role panel (architecture, security-threat-model,
  performance-engineering), all `supports` — asserts `decision: approve`
  and all three `role:` lines present in the audit record.
- Added `t_three_plus_role_panel_one_contradicts_rejects_with_remediation`:
  same 3-role panel, performance-engineering `contradicts` — asserts
  `decision: reject` and a remediation record routed by target_path glob
  match (`routed_to: architecture`, since the finding's target_path
  matches `ARCHITECTURE_ROLE`'s write_scope glob, not the contradicting
  role — same routing behavior as the pre-existing
  `t_auto_reject_with_finding_and_remediation` test in the same file).

No change to `delegated-judgment-gate.sh` (already role-count-generic)
or to `roles/*.json` (out of scope per proposal).

## Why
Proves `delegated-judgment-gate.sh` renders a full 3+-role panel per
issue #586 acceptance criterion 3 (northpole req#5), closing issue #997.

## Upstream
canonical: docs/issue-997/proposals/three-role-panel-fixture.md (read this session)
Based on: docs/issue-997/proposals/three-role-panel-fixture.md

## What did not work
None.

## Doc-placement ladder
- No env var / config key / new dependency / migration / setup step
  introduced — nothing to add to a handbook.
- No library-or-format choice over a named alternative, and no changed
  public signature/wire format beyond the proposal's own Rationale — no
  new docs/issue-997/decisions/ entry.
- No benchmark/investigation numbers produced — no
  docs/issue-997/reports/ addition beyond this record.

## Acceptance verification
canonical: python3 on-the-record/hooks/test_delegated_judgment_gate.py, run this session (output below)
checked: `python3 on-the-record/hooks/test_delegated_judgment_gate.py` — result: pass

```
$ python3 on-the-record/hooks/test_delegated_judgment_gate.py
  ok  t_all_five_issue_timeline_events_fire_across_reject_flow
  ok  t_auto_approve_single_role
  ok  t_auto_reject_with_finding_and_remediation
  ok  t_escalate_on_empty_corpus
  ok  t_escalate_on_no_quorum
  ok  t_framing_snapshot_baseline_on_delivery_merged_no_prior_records
  ok  t_framing_snapshot_fails_closed_on_unresolvable_citation
  ok  t_framing_snapshot_field_not_found_cites_baseline_not_record
  ok  t_framing_snapshot_on_issue_closed_cites_decision_record
  ok  t_framing_snapshot_on_issue_reopened_cites_role_record
  ok  t_kill_switch_disables_the_gate
  ok  t_loop_bound_exhausted_escalates_at_round_4
  ok  t_missing_origin_main_reports_explicit_outcome
  ok  t_multi_role_panel_quorum_and_unanimous_support_approves
  ok  t_no_import_gates_and_no_checkout_resolve_in_the_hook_source
  ok  t_no_retired_flat_product_path_in_the_hook_source
  ok  t_no_trigger_no_side_effects
  ok  t_non_verdict_comment_not_flagged
  ok  t_partial_support_with_no_opinion_escalates_not_approves
  ok  t_present_origin_main_unchanged_behavior
  ok  t_repeat_contradiction_from_same_role_escalates_before_round_3
  ok  t_review_verdict_in_role_session_not_flagged
  ok  t_review_verdict_with_role_record_citation_not_flagged
  ok  t_review_verdict_without_citation_gets_flagged
  ok  t_three_plus_role_panel_one_contradicts_rejects_with_remediation
  ok  t_three_plus_role_panel_quorum_and_unanimous_support_approves

26 passed
```

## Open findings
None.
