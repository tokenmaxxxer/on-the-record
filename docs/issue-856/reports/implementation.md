---
code_under_review:
  - on-the-record/hooks/gh-write-allow-gate.sh
  - on-the-record/hooks/test_gh_write_allow_gate.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
  - docs/specs/reconciled-index.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Added `on-the-record/hooks/gh-write-allow-gate.sh`, a new default-on
`PreToolUse`+`Bash` allow-gate that grants
`hookSpecificOutput.permissionDecision: "allow"` for the five gh issue/pr
write verbs the orchestrator session lacked: `gh issue create`,
`gh issue comment`, `gh pr comment`, `gh issue close`, `gh pr close`. It
mirrors `merge-allow-gate.sh` (#816) and `spawn-allow-gate.sh` (#823):
SessionStart-snapshot-first orchestrator-identity check (`CLAUDE_ROLE`
unset), strict `shlex.shlex(posix=True, punctuation_chars=True)`
command-shape tokenization (issue #824/#834 design) matched against the
five verb-token-prefix shapes (each optionally preceded by `cd DIR &&`),
with no token past the matched verb ever inspected — the decision is keyed
on shape only, never on `--body`/comment text. Unlike `merge-allow-gate.sh`
there is no `landing_readiness.py` readiness predicate, since these five
verbs are non-destructive (create/comment/close, not merge) — matching
`spawn-allow-gate.sh`'s simpler shape.

Registered the hook in `on-the-record/hooks/hooks.json`'s `PreToolUse`+
`Bash` matcher list, immediately after `spawn-allow-gate.sh`.

Added `on-the-record/hooks/test_gh_write_allow_gate.py`, covering: each of
the five verbs gets `allow` for the orchestrator; a `cd DIR &&`-prefixed
invocation still allows; a role session never gets `allow`; a
sensitive-looking literal inside `--body` (gate-design vocabulary) neither
falsely allows nor falsely blocks; unquoted chaining (`&&`, `;`, `|`) and
command/process substitution (`$(...)`, backticks) are all left unreached
(no allow); a single-quoted shell operator inside `--body` does not trip
the chain check; a non-gh command and `gh pr merge` (owned by
`merge-allow-gate.sh`, a distinct verb) are both untouched; the
`ORCHESTRATE_OFF=1` kill switch suppresses the allow; and a stand-in deny
gate (in the same JSON/exit-code shape a real deny hook uses) still
returns exit-code-2 independent of this gate's own allow decision on the
identical command, proving the composition-safety claim without coupling
to another gate's unrelated preconditions.

canonical: docs/issue-856/reports/implementation/survey.md ("Existing deny gates over the same `gh` surface")
The survey found no existing gate in this repo currently denies these five
verbs outright, which is why the composition test uses a stand-in deny
gate rather than a real one.

Registered the new hook's spec rows in `docs/specs/enforcement-boundary.md`
and `docs/specs/generated-paths.md`, and regenerated
`docs/specs/reconciled-index.md` via `python3 gates/spec_index.py --update`
in the same commit — required by `gate-registration-guard.sh` and
`spec-index-preflight.sh` respectively.

## Why

canonical: docs/issue-856/proposals/gh-write-allow-gate.md
Per the approved proposal at docs/issue-856/proposals/gh-write-allow-gate.md:
a fresh orchestrator session had every `gh` write call denied by the host
permission classifier (measured in the #855 harness re-run — "every gh
call (issue create, list, view) is denied by the permission mode in this
session"), the unbuilt half of #810 SCOPE EXTENSION 2. The on-the-record
model requires the orchestrator to create issues and comment to relay
decisions, so without this the loop cannot run on a fresh install without
a manual permission grant.

## Upstream / basis

Based on: docs/issue-856/proposals/gh-write-allow-gate.md (this issue's
own approved phase-1 proposal), mirroring the design of
on-the-record/hooks/merge-allow-gate.sh (#816) and
on-the-record/hooks/spawn-allow-gate.sh (#823), reusing the strict
shlex command-shape validation from issue #824/#834.

## Test run

derived: `python3 on-the-record/hooks/test_gh_write_allow_gate.py`
```
  ok  t_backtick_command_substitution_is_unreached
  ok  t_cd_prefixed_invocation_gets_allow
  ok  t_chain_appended_with_pipe_is_not_allowed
  ok  t_chain_prepended_with_semicolon_is_not_allowed
  ok  t_deny_gate_still_wins_when_both_fire
  ok  t_double_quoted_command_substitution_is_unreached
  ok  t_gh_pr_merge_is_not_this_gates_verb
  ok  t_kill_switch_suppresses_allow
  ok  t_non_gh_command_is_untouched
  ok  t_orchestrator_issue_close_gets_allow
  ok  t_orchestrator_issue_comment_gets_allow
  ok  t_orchestrator_issue_create_gets_allow
  ok  t_orchestrator_pr_close_gets_allow
  ok  t_orchestrator_pr_comment_gets_allow
  ok  t_role_session_never_gets_allow
  ok  t_sensitive_literal_in_body_does_not_falsely_allow_or_block
  ok  t_single_quoted_shell_operator_in_body_does_not_trip_chain_check
  ok  t_unquoted_chained_command_after_verb_is_unreached

18 passed
```

derived: `python3 gates/test_boundary.py`
```
13/13 passed
```

derived: `python3 gates/test_generated_paths.py`
```
4/4 passed
```

## What did not work

None.

## Open findings

None outstanding at landing.
