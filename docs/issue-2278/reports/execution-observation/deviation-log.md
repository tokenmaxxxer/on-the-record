# Deviation log — issue-2278 (execution-observation role)

- 2026-08-25T10:35:00+09:00 | inline | `pr-preflight.sh` detected issue
  #2278 comment `issuecomment-5403812868` (an operator-frozen systemic/
  no-side-effects acceptance constraint) posted after this session
  started, and required an `amendments-reconciled:` citation in the
  record before allowing `gh pr create` — outside the invoking task's
  literal ask (re-execute the two counterexamples + the missing-path
  FAIL case). Added an "Operator-frozen constraint reconciliation"
  section to `docs/issue-2278/reports/execution-observation.md`
  independently checking PR #2283's diff against each of the comment's
  five named conditions, inside this role's own frozen write set (own
  record file only). Resumed and finished the original task same turn.
