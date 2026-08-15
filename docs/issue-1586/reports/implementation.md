---
code_under_review:
  - docs/specs/patrol-channel-contract.md
  - on-the-record/hooks/gh-write-allow-gate.sh
  - on-the-record/hooks/test_gh_write_allow_gate.py
type: feature
breaking: false
verdict: pass  # canonical: python3 on-the-record/hooks/test_gh_write_allow_gate.py — 31 passed, 0 failed (this turn)
loop_state: landed
---

canonical: `python3 on-the-record/hooks/test_gh_write_allow_gate.py` — 31 passed, 0 failed (fenced output below, this turn's run)

## What was done

- Wrote the patrol-channel-contract spec doc (new file under
  docs/specs/, this turn), an EARS-pattern spec (same shape as
  docs/specs/upstream-defect-channel.md) stating: the waiver scope
  (patrol channel only), tick-is-approval semantics (a checkbox tick on
  the board issue is the sole trigger for creating a real per-finding
  issue), and the four hard caps from the issue body verbatim. Its
  header cross-references docs/specs/requirement-digest.md and states
  plainly it carries no R-id (`infrastructure/no-direct-requirement`,
  per the issue's own validity-consult line) rather than appending a
  synthetic entry to the auto-generated digest.
- Added `("gh", "issue", "edit")` to `gh-write-allow-gate.sh`'s
  `VERB_SHAPES` tuple — the one verb shape missing for board-issue
  edit-in-place. No other logic in the gate changed; the `cd DIR &&`
  prefix handling, heredoc-substitution carve-out, and operator-token
  check apply to the new shape identically to the existing five.
  Tick-promoted issue creation needed no gate change — it is already
  covered by the pre-existing `gh issue create` shape.
- Added three test cases to `on-the-record/hooks/test_gh_write_allow_gate.py`:
  orchestrator `gh issue edit` gets `allow`; role-session `gh issue
  edit` never gets `allow`; a semicolon-chained `gh issue edit` falls
  through denied.

## Why

Operator decision 2026-08-15 (recorded in the consumer repo's
docs/reports/product/goals.md, per the issue body) waives the
per-issue scribe-confirmation step for the patrol channel only, so the
patrol filer can maintain one living board issue and promote a tick to
a real issue. The gate change is minimal because
`gh-write-allow-gate.sh`'s own design invariant — decision keyed on
command shape only, never on argument text (issue #810 SCOPE EXTENSION
2) — rules out enforcing which issue is "the" board or the hourly/
open-count caps at this layer; those are runtime-state checks that
belong to the patrol-board implementation this issue precedes, not to
a shape-only permission gate.

## Upstream basis

docs/issue-1582/proposals/2026-08-15-tier1-role-patrol-pilot.md and
git commit 655542ec (#1582/#1584 tier-1 patrol queue + trigger guard),
which explicitly scoped queue-to-issue promotion out as a non-goal —
this issue is the contract amendment that precedes building it.

## What did not work

None — no reverted or replaced work this session.

## Doc placement

- New spec doc under docs/specs/ — standing spec (buckets ladder: spec
  doc, same turn as the gate change it documents).
- docs/specs/reconciled-index.md — regenerated via
  `python3 gates/spec_index.py --update`; no diff produced (the index
  only tracks pre-existing rows for drift detection, and does not
  auto-discover newly added spec files).

## Open findings

None.

## Next steps

None — issue #1586's acceptance criteria are both met. The
patrol-board implementation itself (tick-detection, per-issue
promotion, cap enforcement) is a separate, later issue by design (see
"Out of scope" in this issue's own proposal file under
docs/issue-1586/proposals/).

```
  ok  t_backtick_command_substitution_is_unreached
  ok  t_body_curl_substitution_is_not_allowed
  ok  t_body_file_shape_chained_with_semicolon_is_not_allowed
  ok  t_cd_prefixed_invocation_gets_allow
  ok  t_chain_appended_with_pipe_is_not_allowed
  ok  t_chain_prepended_with_semicolon_is_not_allowed
  ok  t_dangerous_substitution_inside_heredoc_shape_is_still_denied
  ok  t_deny_gate_still_wins_when_both_fire
  ok  t_double_quoted_command_substitution_is_unreached
  ok  t_double_quoted_heredoc_delimiter_also_gets_allow
  ok  t_gh_pr_merge_is_not_this_gates_verb
  ok  t_issue_edit_chained_with_semicolon_is_not_allowed
  ok  t_kill_switch_suppresses_allow
  ok  t_non_gh_command_is_untouched
  ok  t_orchestrator_issue_close_gets_allow
  ok  t_orchestrator_issue_comment_gets_allow
  ok  t_orchestrator_issue_create_gets_allow
  ok  t_orchestrator_issue_edit_gets_allow
  ok  t_orchestrator_pr_close_gets_allow
  ok  t_orchestrator_pr_comment_gets_allow
  ok  t_plain_dangerous_command_substitution_still_denied
  ok  t_quoted_heredoc_body_role_session_still_not_allowed
  ok  t_quoted_heredoc_body_substitution_gets_allow
  ok  t_real_body_file_shape_with_R_flag_gets_allow
  ok  t_real_quoted_heredoc_body_with_R_flag_and_markdown_backticks_gets_allow
  ok  t_role_session_issue_edit_never_gets_allow
  ok  t_role_session_never_gets_allow
  ok  t_sensitive_literal_in_body_does_not_falsely_allow_or_block
  ok  t_single_quoted_shell_operator_in_body_does_not_trip_chain_check
  ok  t_unquoted_chained_command_after_verb_is_unreached
  ok  t_unquoted_heredoc_delimiter_is_not_the_benign_shape

31 passed
```

## Resolution path

N/A — no open findings.
