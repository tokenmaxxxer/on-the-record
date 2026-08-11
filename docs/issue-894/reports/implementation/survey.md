# issue-894 implementation — current-state survey

kind: survey
canonical: this session's own reads of the files listed below

## Scope

Step 3 of issue #894: implement finding #1's disposition from
docs/issue-894/reports/security-threat-model.md.

canonical: `git show origin/issue-894/security-threat-model:docs/issue-894/reports/security-threat-model.md`
— read live, this session (branch issue-894/security-threat-model, PR #900, not yet merged to
main).

Finding #1 disposition: mitigate — drop `--permission-mode bypassPermissions` from both resume
call sites, and extend the allow-hook set to cover `git fetch` (and any other Bash shape a resume
genuinely needs) under the existing shape-only-validation discipline.

Skip condition: this is a security-threat-model **disposition** already reasoned through by a
separate STRIDE review (finding #1, "mitigate", with a concrete recommendation naming exactly
what to change) — the design decision (drop bypassPermissions, extend allow-hooks) was made in
that record, not open here. Per scout-directive's two skip conditions this leaves no design
decision open to re-litigate; scouting the security-tooling market is not applicable to a fix
whose shape is already specified by an approved threat-model finding.

## Write set (surveyed)

canonical: spawn.py:2231-2270 (`_resume_orchestrator_session`) — read live, this session.
- `spawn.py`: remove `"--permission-mode", "bypassPermissions"` from the `Popen` argv at
  spawn.py:2264.

canonical: harness/driver.py:257-294 (`resume_orchestrator_session`) — read live, this session.
- `harness/driver.py`: same removal from the `subprocess.run` argv at driver.py:287.

canonical: on-the-record/hooks/merge-allow-gate.sh:1-231 — read live, this session.
- a new sibling hook file under `on-the-record/hooks/`, mirroring `merge-allow-gate.sh`'s
  shape-validation primitive (shlex tokenize, fixed verb shape, orchestrator-identity check via
  `session-role-bind.sh`'s snapshot) for `git fetch [<remote>] [<refspec>...]`, optionally
  prefixed by `cd DIR &&`.

canonical: on-the-record/hooks/hooks.json:33-50 — read live, this session.
- `on-the-record/hooks/hooks.json`: register the new hook in the `PreToolUse`/`Bash` matcher
  group, alongside `merge-allow-gate.sh` / `spawn-allow-gate.sh` / `gh-write-allow-gate.sh`.

canonical: on-the-record/hooks/test_spawn_allow_gate.py:1-80 — read live, this session.
- a new test file mirroring that structure (subprocess-driven, env-injected identity/checkout)
  for the new hook.

canonical: tests/test_spawn.py:8995-9016 (`ResumeOrchestratorSessionPermissionMode`) — read
live, this session.
- that class's existing test asserts `bypassPermissions` IS present in the Popen argv; it must
  be rewritten to assert it is ABSENT (and that `--resume`/the nudge text still land correctly).

canonical: harness/test_driver.py:219-241 (`test_resume_orchestrator_session_ok`) — read live,
this session.
- same rewrite in `harness/test_driver.py`.

- this session's own phase-2 implementation record, sibling to this survey file.

## What a resumed orchestrator turn needs (traced)

canonical: spawn.py:2286-2291 (`_maybe_resume_for_ready_pr`) — read live, this session.
The resume nudge is a fixed string: "delegated PR #{pr_number} ({key}) is ready — verify, merge,
rebuild/re-check, and emit the 4-part final_report." Bash shapes this turn issues, traced against
the existing allow-hook set and the security-threat-model record's own finding-#1 fix text:

1. `gh pr merge <n> ...`.
   canonical: on-the-record/hooks/merge-allow-gate.sh:142-153 — read live, this session.
   Already covered by `merge-allow-gate.sh` (requires `landing_readiness.py` READY).
2. `python3 spawn.py ...` (watch/ps/rebuild-adjacent subcommands).
   canonical: on-the-record/hooks/spawn-allow-gate.sh:104-146 — read live, this session.
   Already covered by `spawn-allow-gate.sh`, keyed on shape only (any subcommand/args), not on
   which spawn.py verb.
3. `git fetch [<remote>] [<refspec>]`.
   canonical: `git show origin/issue-894/security-threat-model:docs/issue-894/reports/security-threat-model.md`
   ("extend `spawn-allow-gate.sh` (or add a narrow sibling `git-fetch-allow-gate.sh`) ... for
   `git fetch [<remote>] [<refspec>]`") — read live, this session. Not covered by any existing
   hook; this is the one new hook this survey's write set adds.
4. `gh pr view` / `gh pr list` / `git rebase`.
   canonical: `grep -n "gh pr view\|gh pr list\|git rebase" spawn.py harness/driver.py` — read
   live, this session; the only match is `harness/driver.py`'s `poll_for_pr_ready`, itself a
   `subprocess.run` call made by trusted driver code (not a Bash tool call the resumed LLM turn
   issues, so not subject to PreToolUse hooks). No match inside the resume/nudge/rebuild code
   path proper. Left uncovered per the security-threat-model record's own scoped fix list, which
   names only `git fetch` as the missing shape.

## Existing allow-hook pattern (reused, not reinvented)

canonical: on-the-record/hooks/merge-allow-gate.sh:1-231 — read live, this session.
`merge-allow-gate.sh` (issue #810/#824) is the template: `set -uo pipefail`, `ORCHESTRATE_OFF`
kill switch, payload piped from stdin, a Python heredoc doing (a) `CLAUDE_ROLE` identity
resolution via `session-role-bind.sh`'s `$TMPDIR/otr-role-bind/<session>.json` snapshot first /
live env fallback, (b) `shlex.shlex(cmd, posix=True, punctuation_chars=True)` strict tokenization
rejecting any command containing a backtick/`$(`/newline, matching only a fixed verb shape
(optionally `cd DIR &&`-prefixed) with no operator token in the tail, (c) prints
`{"hookSpecificOutput": {"permissionDecision": "allow", ...}}` on match, bare `exit 0` otherwise
— never emits `"deny"`.

## Re-measurement requirement

canonical: docs/issue-776/reports/implementation.md — read live, this session; the file records
prior harness runs (steady-state re-run history), not one executed in this survey.
acceptance: (none run this session) — result: unverifiable. Removing `bypassPermissions` changes
the resumed orchestrator's actual permission surface, the class of change the #776 harness
measures. This survey did not execute a #776 run against this change; whether the resumed
orchestrator still lands the merge under the narrower permission set is an open question the
implementation record must state as a next step, not something this survey claims.

## Fallback option B (recorded per the task's explicit ask)

canonical: on-the-record/hooks/gh-write-allow-gate.sh:79-84 — read live, this session (states
"the decision is keyed on shape, never on argument text" for all three existing hooks).
If a future #776 re-measure finds a Bash shape that cannot be safely covered by a narrow,
shape-only allow-hook without inspecting argument text, the fallback recorded here is: keep
`bypassPermissions` on the resume call, and add a default-deny fallback hook scoped to the
resumed orchestrator's Bash calls.
canonical: on-the-record/hooks/merge-allow-gate.sh:214-224 (existing `permissionDecision: allow`
JSON shape, the same shape a deny variant would mirror) — read live, this session.
That fallback hook would emit `"permissionDecision": "deny"` for any shape the specific
allow-hooks do not match, reinstating a fail-closed boundary without giving up the bypass. Not
built in this survey's write set: item 3 above is the only gap this survey traced, and it fits
the existing shape-only pattern without needing argument-text inspection.

## Out of scope (per the security-threat-model record's own scoping)

- Finding #3 ($TMPDIR session-bind race) and finding #4 (credential-flow scope) — separate
  mitigate dispositions, separate follow-up work units, not this issue's step-3 fix.
- Step 2 of issue #894 (structural enforcement gate/board-condition requiring a
  security-threat-model record before a trust-boundary change lands) — explicitly a different
  work unit per the security-threat-model record's own "Next steps".
