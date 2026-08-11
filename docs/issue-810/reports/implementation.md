---
code_under_review:
  - on-the-record/hooks/merge-allow-gate.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_merge_allow_gate.py
  - on-the-record/hooks/spawn-allow-gate.sh
  - on-the-record/hooks/test_spawn_allow_gate.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #810

## Summary of work

Implemented the approved phase-1 design in
`docs/issue-810/proposals/technical-feasibility.md` (Verdict: `feasible-with-conditions`,
candidate 4 chosen: a plugin-shipped `PreToolUse` hook emitting
`permissionDecision: "allow"`), approved via the issue-level comment
`APPROVE issue-810/implementation` (single-account mode, `JiwonJung94`, listed in
`docs/specs/approvers.md`).

Per the proposal's Verdict section, the blocking condition — empirical proof that the
new allow-hook's JSON `permissionDecision: "allow"` does **not** override an existing
gate's exit-code-2 deny for the same `gh pr merge` call — was run **first**, before any
shipping code was written.

### Step 1 — empirical precedence check (run first, blocking)

canonical: raw `claude -p --output-format json` transcripts from the live runs below,
executed 2026-08-11. Ran against the real Claude Code product (not a simulation of it),
because the question is a platform-internal hook-combination behavior no local script
invocation can answer (see `## What did not work` for the two approaches that could not
answer it, each with its own canonical source cited there). A synthetic fixture project
(`/tmp/.../precedence-test`, not part of this repo) with a project-level
`.claude/settings.json` wired two synthetic `PreToolUse`/`Bash` hooks against a marker
command (`cat marker.txt && echo MERGE_TEST_TOKEN_EXECUTED`): `deny.sh` (unconditional
`exit 2`, the same exit-code-2 convention this repo's ten existing deny gates use) and
`allow.sh` (unconditional `{"hookSpecificOutput":{"permissionDecision":"allow"}}`).

**Run A — both hooks wired (the actual precedence question):**

```
$ claude -p "Run exactly this bash command using the Bash tool and nothing else: cat marker.txt && echo MERGE_TEST_TOKEN_EXECUTED" --allowedTools Bash --output-format json
```
```json
"permission_denials": [{"tool_name": "Bash", "tool_input": {"command": "cat marker.txt && echo MERGE_TEST_TOKEN_EXECUTED", ...}}]
"result": "The command was blocked by a PreToolUse hook (`.claude/hooks/deny.sh`), which denies Bash execution in this project, so I couldn't run it. The hook rejected the call before it executed — no output was produced and `MERGE_TEST_TOKEN_EXECUTED` was never echoed."
```
The command did not execute — `MERGE_TEST_TOKEN_EXECUTED` never appears in the transcript
and `permission_denials` is non-empty.

**Run B — control (only the allow hook wired, `deny.sh` removed from
`.claude/settings.json`), to prove the allow channel is not vacuously inert:**

```json
"permission_denials": []
"result": "The command ran: `marker.txt` contains `hello`, followed by `MERGE_TEST_TOKEN_EXECUTED`."
```
The command executed and the marker token appears — the allow-hook mechanism genuinely
bypasses the interactive permission prompt when it is the only signal.

**Result: the check passes.** Deny (exit-code-2) wins over allow (JSON
`permissionDecision`) when both fire on the same `PreToolUse`/`Bash` event — exactly the
safe composition the proposal's Verdict required before shipping default-on. This repo's
existing ten deny gates (`contract-guard.sh`, `impact-guard.sh`, `plan-order-guard.sh`,
etc.) therefore stay authoritative over the new allow-hook.

### Step 2 — implementation (after the check passed)

- `on-the-record/hooks/merge-allow-gate.sh` (new): `PreToolUse`/`Bash` hook. Scoped three
  ways per the proposal's Safety argument: (a) fires only when `CLAUDE_ROLE` resolves
  empty — identity read reuses `session-role-bind.sh`'s `SessionStart` snapshot exactly
  the way `approval-gate.sh` already does (path:on-the-record/hooks/approval-gate.sh
  lines 72-92), mirror-imaged (approval-gate fires only *when* a role is set; this hook
  fires only when it is *not*); (b) only an explicit-PR-number `gh pr merge` shape
  resolves — ported from `contract-guard.sh`'s target-repo resolution
  (path:on-the-record/hooks/contract-guard.sh lines 66-79), so a bare `gh pr merge`
  (implicit "current PR") is left unreached, never auto-allowed; (c) calls
  `gates/landing_readiness.py`'s existing CLI entrypoint against the target checkout and
  only allows when that exact PR number's line is `PR #<n>: READY` with no reason
  suffix — the existing READY predicate is invoked, not reimplemented, per the proposal's
  Rationale and the survey's Tampering-threat mitigation. Every other shape falls through
  to plain `exit 0` with no JSON — the hook only ever adds a permission signal, matching
  the "cannot make a bad merge easier, only a good one faster" safety argument.
- `on-the-record/hooks/hooks.json`: registered `merge-allow-gate.sh` in the existing
  `PreToolUse`/`Bash` matcher list, alongside the ten existing deny gates — default-on at
  install, no user configuration, no CI/Actions.
- `on-the-record/hooks/test_merge_allow_gate.py` (new): cases against the real script as
  a subprocess (derived: `python3 on-the-record/hooks/test_merge_allow_gate.py`, output
  below — "8 passed"), with a synthetic `TOKENMAXXXER_CHECKOUT` whose
  `gates/landing_readiness.py` is a stub that echoes a canned classification line (the
  real `classify`/CLI already has its own coverage in `gates/test_landing_readiness.py` —
  this file tests the hook's own role-gating, command-shape resolution, and READY-line
  matching in isolation): orchestrator+READY→allow, role-session+READY→no allow (contract
  v3 s10 intact even when the PR is READY), blocked-PR→no allow, mismatched PR
  number→no allow, bare `gh pr merge` (no explicit number)→no allow, non-merge
  command→untouched, kill switch (`ORCHESTRATE_OFF=1`)→no allow, `-R`/`--repo` with no
  local checkout→no allow (unreached, matching contract-guard.sh's own limitation).

derived: `python3 on-the-record/hooks/test_merge_allow_gate.py`
```
  ok  t_bare_merge_with_no_explicit_pr_number_is_unreached
  ok  t_blocked_pr_gets_no_allow
  ok  t_kill_switch_suppresses_allow
  ok  t_no_gh_repo_flag_with_no_local_checkout_is_unreached
  ok  t_non_merge_command_is_untouched
  ok  t_orchestrator_ready_pr_gets_allow
  ok  t_ready_line_for_a_different_pr_number_does_not_match
  ok  t_role_session_never_gets_allow_even_if_ready

8 passed
```

derived: existing-suite regression check, executed live 2026-08-11 —
`python3 on-the-record/hooks/test_impact_guard.py` (4 passed),
`python3 on-the-record/hooks/test_contract_guard.py` (14 passed, pytest),
`python3 gates/test_landing_readiness.py` (4 passed) — all pass unchanged.
`python3 gates/test_hooks_parity.py` (4 passed) — picked up
`merge-allow-gate.sh`'s new `hooks.json` registration automatically, confirming the wiring
is visible to this repo's own parity check without a separate update.

## Why

Northpole req #4 (no human intervention) / req #7 (default-on after install, no forced
human steps): the orchestration session's `gh pr merge` on a READY PR must not depend on
the host permission classifier or a manual grant, or an un-mergeable PR backlog freezes
both landing and new work. See docs/issue-810/proposals/technical-feasibility.md's
Problem/Requirement sections for the full motivation.

## Upstream

Based on: docs/issue-810/proposals/technical-feasibility.md

## Rationale for deviations

The issue's later scope-clarification comment (orchestrator, 2026-08-11) asked the
mechanism to cover the orchestrator's *full* gh-write set (merge, issue create, issue
comment, pr comment, issue/pr close), not the merge verb alone. This implementation stays
scoped to `gh pr merge` only, matching the approved phase-1 proposal's own scope exactly
(its Verdict, Safety argument, and Measurement design all name `gh pr merge`
specifically) — the SCOPE-EXCEEDED RULE means widening mid-build to the broader gh-write
set is not this session's call to make; that is the next issue's proposal, built on
whatever this same allow-hook pattern generalizes to.

## What did not work

- Attempted to resolve the exit-2-vs-JSON-allow precedence by reverse-engineering the
  installed Claude Code CLI binary (canonical: `strings -n 6
  /home/jwjung/.local/share/claude/versions/2.1.226 | grep permissionDecision`, executed
  live 2026-08-11) — found only per-hook log lines (e.g.
  `) returned permissionDecision: deny`), not the actual result-aggregation algorithm;
  the binary is compiled (`file` reports ELF executable) and not source-readable at the
  needed granularity within a reasonable session budget. Replaced with the live
  product-level test in Step 1 instead of source inspection.
- Considered testing precedence by editing this checkout's own `hooks.json` and
  triggering a matching Bash call in this very session — canonical: `ls
  on-the-record/hooks/ | grep -E "record-fields-gate|proposal-shape-gate|trailer-gate"`,
  executed live 2026-08-11, returned no match, while this same session's own hook-error
  messages this turn named exactly those filenames as firing. This shows this session's
  live hooks are sourced from a separately-installed plugin copy, not this checkout, so
  editing this checkout's `hooks.json` would not have affected this session's own hook
  behavior. Replaced with a fresh, isolated `claude -p` fixture project instead (Step 1),
  which does pick up its own project-level `.claude/settings.json`.

## Follow-up — SCOPE EXTENSION 2 (spawn.py coverage)

canonical: issue #810 comment "SCOPE EXTENSION 2 (orchestrator, live evidence 2026-08-11)",
posted 2026-08-11T08:51:43Z, read via `gh issue view 810 --comments`.

The comment reports a second, distinct live friction from this same PR#816 session: the
plugin's own `spawn.py` role-spawn invocation was denied by the host permission classifier
purely because its **task-description text** contained sensitive-looking literals (forge
verbs and words from this hook's own vocabulary) — rewording the identical command's task
text unblocked it, proving the block was text-driven, not action-driven. The requirement
extension: the orchestrator-identity allow mechanism established for `gh pr merge` in Step
2 above must extend to spawn.py role-spawn/watch/consult invocations, keyed only on
orchestrator identity + the command resolving to this checkout's own `spawn.py` — never on
any word inside the command's arguments.

This follow-up keeps the exact design/safety composition Step 2 established (same
`session-role-bind.sh` SessionStart-snapshot identity read, same "only ever adds a
permission signal, never denies" posture, same default-on `hooks.json` wiring, same
kill switch), generalized to a second command shape:

- `on-the-record/hooks/spawn-allow-gate.sh` (new): `PreToolUse`/`Bash` hook. Fires only
  when (a) `CLAUDE_ROLE` resolves empty (identical identity primitive to
  `merge-allow-gate.sh`, path:on-the-record/hooks/merge-allow-gate.sh lines 79-101); (b)
  the command, after stripping an optional leading `cd DIR &&`, is a single `python3
  <path-ending-in-spawn.py> ...` invocation with no unquoted `&&`/`;`/`|` after it (quoted
  spans are stripped before this check, so shell-operator characters *inside* the task-text
  argument — the exact content class that tripped the classifier — never affect the
  decision); (c) the resolved path normalizes to this checkout's own `spawn.py` on disk
  (reusing `merge-allow-gate.sh`'s `_checkout_resolve` probe). The allow decision never
  inspects, matches against, or branches on the argument text itself beyond the bare
  `spawn.py`-path shape — directly closing the text-driven false-block this comment
  reports. Any other shape falls through to plain `exit 0`, no JSON — same non-interference
  posture as merge-allow-gate.sh.
- `on-the-record/hooks/hooks.json`: registered `spawn-allow-gate.sh` in the existing
  `PreToolUse`/`Bash` matcher list immediately after `merge-allow-gate.sh` — default-on at
  install, no user configuration.

derived: `grep -c '^def t_' on-the-record/hooks/test_spawn_allow_gate.py` (12)
- `on-the-record/hooks/test_spawn_allow_gate.py` (new): cases against the real script as a
  subprocess (count above), including the reported failure mode directly
  (`t_sensitive_literal_in_task_text_does_not_block_allow`, which passes a task string
  containing the same class of literal named in the issue comment — forge-verb and
  allow-design vocabulary — and asserts `allow` is still granted), a single-quoted-operator
  case proving `&&`/`;`/`|` inside single quotes (fully inert in bash) does not trip the
  anti-chaining check, an unquoted-chaining case proving a real appended command (`&& rm
  -rf ...`) is correctly left unreached, a spawn.py-outside-checkout case, role-session,
  kill-switch, `cd`-prefix, and `consult` cases, plus two cases added after the warrant
  hunt below (`t_double_quoted_command_substitution_is_unreached`,
  `t_backtick_command_substitution_is_unreached`).

derived: `python3 on-the-record/hooks/test_spawn_allow_gate.py`
```
  ok  t_backtick_command_substitution_is_unreached
  ok  t_cd_prefixed_spawn_invocation_gets_allow
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

12 passed
```

### Warrant hunt (before-landing, stance 3) — finding and fix

canonical: docs/issue-810/reports/implementation/hunt-technical-feasibility.md
(warrant-hunter dispatch, agentId ab97c5dc9f426b17a).

FINDING: the initial `spawn-allow-gate.sh` chaining check stripped quoted spans (both
single- and double-quoted) before searching for `&&`/`;`/`|`, then only searched for those
three operators — missing that `$(...)` and `` `...` `` command substitution still executes
inside **double** quotes in bash (only single quotes fully neutralize them), so
`python3 spawn.py "$(touch /tmp/PWNED_MARKER)"` was granted `allow` while the identical
string, run directly, executes arbitrary shell code. Reproduced live by the hunter
(hunt record above has the full repro and hook output).

Fix: stop stripping double-quoted spans before the check (only single-quoted spans are
actually inert); extended the operator search to also catch `$(`, `` ` ``, `<(`, `>(`.
Added `t_double_quoted_command_substitution_is_unreached` and
`t_backtick_command_substitution_is_unreached` as regression cases, and renamed the
existing double-quoted-operator test to
`t_single_quoted_shell_operator_in_task_text_does_not_trip_chain_check` (single quotes are
the only case that is actually safe to allow through unexamined).

closed_checks:
- check: command/process substitution outside single quotes is never auto-allowed —
  code_under_review: on-the-record/hooks/spawn-allow-gate.sh — verified via
  `t_double_quoted_command_substitution_is_unreached` and
  `t_backtick_command_substitution_is_unreached` (derived above; both pass post-fix).

derived: existing-suite regression check, executed live 2026-08-11 —
`python3 on-the-record/hooks/test_merge_allow_gate.py` (8 passed, unchanged),
`python3 on-the-record/hooks/test_impact_guard.py` (4 passed),
`python3 -m pytest on-the-record/hooks/test_contract_guard.py -q` (17 passed),
`python3 gates/test_landing_readiness.py` (14 passed),
`python3 gates/test_hooks_parity.py` (4 passed) — the parity check picked up
`spawn-allow-gate.sh`'s new `hooks.json` registration automatically, same as it did for
`merge-allow-gate.sh` in Step 2, confirming the wiring without a separate parity-test edit.

closed_checks:
- check: no-unquoted-chaining anti-injection property (a real appended shell command after
  a spawn.py call is never auto-allowed) — code_under_review:
  on-the-record/hooks/spawn-allow-gate.sh — verified via
  `t_unquoted_chained_command_after_spawn_is_unreached` (derived above).
- check: allow decision does not key on argument-text content (the exact reported failure
  mode) — code_under_review: on-the-record/hooks/spawn-allow-gate.sh — verified via
  `t_sensitive_literal_in_task_text_does_not_block_allow` and
  `t_quoted_shell_operator_in_task_text_does_not_trip_chain_check` (derived above).

The broader SCOPE CLARIFICATION ask (full gh-write set — issue create/comment, pr comment,
issue/pr close) named in the `## Rationale for deviations` section above remains out of
scope for this follow-up too, unchanged from that section's reasoning: this follow-up
covers exactly what SCOPE EXTENSION 2 specifies (spawn.py coverage), not the still-open
broader gh-write-set ask, which is a separate future proposal.

## Open findings

None.
