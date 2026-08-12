---
code_under_review:
  - on-the-record/hooks/impact-guard.sh
  - on-the-record/hooks/test_impact_guard.py
type: fix
breaking: false
verdict: PERSIST
loop_state: landed
---

# issue-813 implementation record

## Summary of work

impact-guard.sh classified a batched-merge act by counting the merge-verb
substring across the whole raw Bash command string. A `gh issue comment`
or `gh pr comment --body` that merely *discussed* `gh pr merge` (e.g.
design notes on merge automation) was miscounted as a batch of merge
invocations and denied — a false positive with no merge actually
invoked.

canonical: `git log origin/main --oneline | grep 813` (this session) —
shows `295fdaa issue-813: classify batched-merge by invoked verb, not
comment-body text (#828)`.
The fix already landed on main as commit 295fdaa via PR #828, by
tokenizing the command with `shlex.shlex(cmd, posix=True,
punctuation_chars=True)` and counting adjacent verb-token triplets (e.g.
`gh`, `pr`, `merge` as three consecutive real tokens) instead of a
substring regex over the raw string. A quoted `--body`/`--body-file`/
here-string argument collapses into a single shlex token, so text
inside it can never reassemble into a fake invocation triplet, while a
genuine two-invocation batch still produces two real triplets and is
still denied.

canonical: `gh pr view 828 --json body` (this session) — body states
"This is a phase-1 proposal PR ... the phase-2 implementation record
... is gated behind an human approval comment ... References #813
(not Closes)".
PR #828 was a phase-1 proposal PR under this repo's role-handoff
contract: the code fix, its test, the survey, and the proposal were
included, but the phase-2 record write was gated behind human approval.

canonical: `gh issue view 813 --comments` (this session) — shows a
comment whose entire body is the exact string
`APPROVE issue-813/implementation` from account JiwonJung94, posted
after the "PR #828 opened" watch-log comment.
That approval has since landed on the issue.

This session's work: rebase the branch onto the now-current main
(PR #828's fix commit was already reachable from main, so the rebase
was a no-op replay), re-run the regression suite live (see Regression
test section below), and write this record so a phase-2 delivery PR
carrying `Closes #813` can be opened.

## Why

canonical: `gh issue view 813` (this session) — issue body and comment
thread.

The false positive blocked legitimate record/relay writes any time an
orchestrator quoted or discussed `gh pr merge` in a comment body — exact
friction the issue reproduces from a live session's PreToolUse:Bash hook
stderr. The fix must classify by the actually-invoked verb, not by
literal substring matches anywhere in the command string, while still
catching a real batched merge.

## Upstream / basis

- Proposal: `docs/issue-813/proposals/verb-not-body-text-batch-classification.md`
- Survey: `docs/issue-813/reports/implementation/survey.md`
- canonical: `git log origin/main --oneline | grep 813` (this session)
  — Merged fix commit: 295fdaa (PR #828)
- Tokenizer approach reused from issue #824's validation of the same
  `shlex` technique for the sibling `merge-allow-gate.sh` hook.

## Regression test

Executed live this session:

derived: `python3 on-the-record/hooks/test_impact_guard.py`

```
  ok  t_batch_of_only_low_impact_proposals_is_allowed
  ok  t_batch_with_high_impact_proposal_is_denied
  ok  t_comment_body_mentioning_merge_verb_is_not_misclassified_as_a_batch
  ok  t_kill_switch_reverts_the_wiring_and_allows_the_same_batch
  ok  t_single_merge_is_not_treated_as_a_batch

5 passed
```

canonical: python3 on-the-record/hooks/test_impact_guard.py — result:
5 passed, 0 failed (this session, output pasted directly above).

`t_comment_body_mentioning_merge_verb_is_not_misclassified_as_a_batch`
is the regression covering a `gh issue comment --body` with multiple
`gh pr merge` literals.
`t_batch_with_high_impact_proposal_is_denied` is the regression covering
a genuine batch of real merge invocations.

## What did not work

None.

## Open findings

canonical: `docs/issue-813/reports/implementation/survey.md` and
`gh pr view 828 --json body` (this session) — the survey and PR #828's
merged history record two warrant-hunter dispatches (after-proposal,
before-landing) against this change, both returning no finding.
None open.

## Next steps

None — this record closes out issue-813's phase-2 delivery. `loop_state:
landed`.
