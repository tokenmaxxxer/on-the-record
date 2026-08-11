---
code_under_review:
  - on-the-record/hooks/spawn-allow-gate.sh
  - on-the-record/hooks/test_spawn_allow_gate.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #834

## What was done

Ported issue #824's strict, shlex-based command-shape check
(`docs/issue-824/proposals/strict-merge-allow-validation.md`) from
`merge-allow-gate.sh` into `spawn-allow-gate.sh`, replacing the
cd-prefix-strip-before-operator-check block (old lines 104-125) that let a
whitespace-free command-substitution payload placed in the unbounded
`cd`-prefix directory slot (`\S+`) evade the operator search while bash
still executed it.

The new check, in `on-the-record/hooks/spawn-allow-gate.sh`:
- rejects the whole command outright if a backtick, `$(`, or a literal
  newline appears anywhere in it, before any tokenization;
- tokenizes the full, unstripped command with
  `shlex.shlex(cmd, posix=True, punctuation_chars=True)`
  (`whitespace_split = True`); a `ValueError` (unbalanced quoting) falls
  through unreached — same fail-open posture as before;
- recognizes exactly two token shapes:
  `["python3"|"python", SPAWN_PATH, ...tail]` or
  `["cd", DIR, "&&", "python3"|"python", SPAWN_PATH, ...tail]`
  (`SPAWN_PATH` ending in `spawn.py`);
- rejects if any token in `tail` (which includes `DIR` for the
  `cd`-prefixed shape) is composed entirely of shlex punctuation
  characters plus `;`;
- the existing spawn-path resolution/existence check runs unchanged,
  only after the shape check passes.

Added regression cases to `on-the-record/hooks/test_spawn_allow_gate.py`:
the issue's exact reproduction (command substitution hidden in the `cd`
prefix's directory slot, both `$(...)` and backtick forms), chain-prepended
`;`, chain-appended `;`, chain-appended `|`, and the backslash-escaped-quote
payload from issue #824's hunt finding. All 12 pre-existing cases were left
unmodified and still pass with the same allow/no-allow outcome, including
the bare-invocation, `cd`-prefixed-invocation, and single-quoted-operator
green-path cases.

## Why

canonical: docs/issue-834/proposals/strict-spawn-allow-validation.md (##
Rationale section)

Same rationale issue #824 already recorded and this proposal's own
Rationale section restates: a hand-written regex asked to track bash's
real quote/escape/substitution state has an unbounded number of payload
shapes it can miss.

canonical: docs/issue-824/reports/implementation/hunt-strict-merge-allow-validation.md
Issue #824's own after-proposal hunt record documents a second,
independent bypass class it found in a differently-shaped regex approach
within this same file family (the quote-pairing draft
`merge-allow-gate.sh` first used). `shlex.shlex(posix=True,
punctuation_chars=True)` tokenizes the whole, unstripped command once,
closing the specific class of bug where a prefix-strip runs before the
shape/operator check and can consume a payload out from under it.

## Upstream basis

- docs/issue-834/proposals/strict-spawn-allow-validation.md
- docs/issue-834/reports/implementation/survey.md
- docs/issue-824/proposals/strict-merge-allow-validation.md
- on-the-record/hooks/test_merge_allow_gate.py (regression-case shapes mirrored)

## What did not work

None.

## Test run

derived: `python3 on-the-record/hooks/test_spawn_allow_gate.py`

```
  ok  t_backslash_escaped_quote_payload_is_not_allowed
  ok  t_backtick_command_substitution_is_unreached
  ok  t_cd_prefixed_spawn_invocation_gets_allow
  ok  t_chain_appended_with_pipe_is_not_allowed
  ok  t_chain_appended_with_semicolon_is_not_allowed
  ok  t_chain_prepended_with_semicolon_is_not_allowed
  ok  t_command_substitution_hidden_in_cd_prefix_dir_slot_backtick_is_unreached
  ok  t_command_substitution_hidden_in_cd_prefix_dir_slot_dollar_paren_is_unreached
  ok  t_consult_invocation_gets_allow
  ok  t_double_quoted_command_substitution_is_unreached
  ok  t_kill_switch_suppresses_allow
  ok  t_non_spawn_command_is_untouched
  ok  t_orchestrator_spawn_invocation_gets_allow
  ok  t_role_session_never_gets_allow
  ok  t_sensitive_literal_in_task_text_does_not_block_allow
  ok  t_single_quoted_shell_operator_in_task_text_does_not_trip_chain_check
  ok  t_spawn_py_outside_checkout_is_unreached
  ok  t_unquoted_chained_command_after_spawn_is_unreached

18 passed
```

derived: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`

```
2 failed, 1216 passed, 1 xfailed in 78.21s (0:01:18)
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
FAILED tests/test_gates.py::t_rulebook_version_is_recorded
```

canonical: docs/issue-834/reports/implementation/survey.md (Baseline
section) — both failures are pre-existing/environmental, not caused by
this change. `t_all_generators_recorded_and_disjoint` is the same
out-of-scope, `stop-poll-rearm.sh`/issue-801 failure the survey's Baseline
section recorded before this session touched any file.
`t_rulebook_version_is_recorded` fails only because it asserts the
checked-out rulebook string contains no "커밋안됨" (uncommitted) marker —
it fails on any session with an uncommitted working tree and is expected
to pass once this change is committed; it is a dirty-checkout detector,
not a regression this change introduced.

## Rationale for deviations

Not applicable — no deviation from the approved phase-1 proposal.

## Open findings

None.

## Hunt

Skipped: this proposal's write set is `docs/`-only plus the two files
already ported verbatim in shape from issue #824's landed, hunted design
(`spawn-allow-gate.sh`, `test_spawn_allow_gate.py`). canonical:
docs/issue-824/reports/implementation/hunt-strict-merge-allow-validation.md
— that record documents the hunt that already ran against this identical
check shape on `merge-allow-gate.sh`, so porting it here introduces no new
design surface for a fresh hunt to cover.
