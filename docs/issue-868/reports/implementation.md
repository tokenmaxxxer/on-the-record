---
code_under_review:
  - on-the-record/hooks/gh-write-allow-gate.sh
  - on-the-record/hooks/test_gh_write_allow_gate.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

`gh-write-allow-gate.sh` (#856/#859) refused ANY command containing
`` ` ``/`$(`/newline, which safely excludes dangerous substitution but
also denies the real shape a session composes for a multi-line issue
body: `gh issue create --body "$(cat <<'EOF' ... EOF)"` (#868, tracing
PR #867 finding 4). Implemented approach (a) from the issue: taught the
gate's embedded Python guard to recognize the single provably-benign
shape — a command substitution whose entire content is `cat <<'DELIM'`
(or `<<"DELIM"`) with a QUOTED heredoc delimiter — as a structural
exception, collapse it to an inert placeholder, and run the existing
exclusion/tokenization/verb-shape checks unchanged on the rest. Any
other `` ` ``/`$(`/newline shape — including an UNQUOTED heredoc
delimiter, or a second unrelated `$(...)` alongside the benign one —
still exits untouched (denied), exactly as before.

canonical: on-the-record/hooks/gh-write-allow-gate.sh:79-108 (post-change, this session's own edit)
Change lands at on-the-record/hooks/gh-write-allow-gate.sh:79-108: a
`_HEREDOC_SUB_RE` regex match against `cmd`, gated on `len(_subs) == 1
and cmd.count("$(") == 1 and "\`" not in cmd` before the pre-existing
exclusion line runs.

## Why

**Why this shape is provably safe (safety rationale required by #868):**
POSIX shell semantics — quoting any part of a heredoc's delimiter
(`<<'EOF'` or `<<"EOF"`) disables ALL expansion of its body by
construction. The shell never looks for `$(...)`, backticks, or
variables inside a quoted-delimiter heredoc body regardless of what text
it contains, so `cat`'s stdout (the literal body, verbatim) is the only
thing `$(cat <<'DELIM' ... DELIM)` can ever produce — it cannot execute
anything hidden inside the body. This is why `--body-file` (documented
in `gh issue create --help`) and the quoted-heredoc-`cat` idiom are both
safe multi-line-body mechanisms, and why an UNQUOTED delimiter is
explicitly excluded from the exception: an unquoted heredoc's body DOES
undergo normal expansion, so it has no such safety property and stays
denied. The Claude Code PreToolUse `hookSpecificOutput.
permissionDecision` contract is unaffected — this change adds no new
hook event or output shape, only a pre-check ahead of the gate's
existing substitution-exclusion branch.

upstream: docs/issue-868/proposals/quoted-heredoc-body-exception.md,
docs/issue-868/reports/implementation/survey.md

## What did not work

None.

## Doctrine ladder

- No env var, config key, dependency, or migration was added — nothing
  to place in a handbook.
- Library-or-format choice recorded: `docs/issue-868/proposals/quoted-heredoc-body-exception.md`
  (## Rationale — chose (a) structural recognition over (b) docs-only
  `--body-file` steering).
- No benchmark/investigation numbers produced — nothing for
  docs/issue-868/reports/.

## Test results

derived: `python3 on-the-record/hooks/test_gh_write_allow_gate.py`
```
  ok  t_backtick_command_substitution_is_unreached
  ok  t_cd_prefixed_invocation_gets_allow
  ok  t_chain_appended_with_pipe_is_not_allowed
  ok  t_chain_prepended_with_semicolon_is_not_allowed
  ok  t_dangerous_substitution_inside_heredoc_shape_is_still_denied
  ok  t_deny_gate_still_wins_when_both_fire
  ok  t_double_quoted_command_substitution_is_unreached
  ok  t_double_quoted_heredoc_delimiter_also_gets_allow
  ok  t_gh_pr_merge_is_not_this_gates_verb
  ok  t_kill_switch_suppresses_allow
  ok  t_non_gh_command_is_untouched
  ok  t_orchestrator_issue_close_gets_allow
  ok  t_orchestrator_issue_comment_gets_allow
  ok  t_orchestrator_issue_create_gets_allow
  ok  t_orchestrator_pr_close_gets_allow
  ok  t_orchestrator_pr_comment_gets_allow
  ok  t_plain_dangerous_command_substitution_still_denied
  ok  t_quoted_heredoc_body_role_session_still_not_allowed
  ok  t_quoted_heredoc_body_substitution_gets_allow
  ok  t_role_session_never_gets_allow
  ok  t_sensitive_literal_in_body_does_not_falsely_allow_or_block
  ok  t_single_quoted_shell_operator_in_body_does_not_trip_chain_check
  ok  t_unquoted_chained_command_after_verb_is_unreached
  ok  t_unquoted_heredoc_delimiter_is_not_the_benign_shape

24 passed
```
All 18 pre-existing tests pass unmodified; 6 new tests added and green
(no SKIPPED lines in the pasted output above).

canonical: on-the-record/hooks/gh-write-allow-gate.sh (post-change, this session's own edit) + pasted test run above
## Closed checks

closed_checks:
- benign quoted-heredoc `--body` shape allowed for orchestrator — code_under_review: on-the-record/hooks/gh-write-allow-gate.sh
- double-quoted heredoc delimiter variant also allowed — code_under_review: on-the-record/hooks/gh-write-allow-gate.sh
- unquoted heredoc delimiter (`<<EOF`, no quotes) NOT granted the exception, stays denied — code_under_review: on-the-record/hooks/gh-write-allow-gate.sh
- dangerous `$(rm -rf x)` substitution, alone and alongside the benign heredoc shape, stays denied — code_under_review: on-the-record/hooks/gh-write-allow-gate.sh
- role session (`CLAUDE_ROLE` set) never auto-allowed even for the benign shape — code_under_review: on-the-record/hooks/gh-write-allow-gate.sh
- existing 5-verb-shape, `cd &&`, kill-switch, and deny-gate-composition tests unaffected — code_under_review: on-the-record/hooks/gh-write-allow-gate.sh

## Open findings

None.
