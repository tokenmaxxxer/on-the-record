# Current-state survey — issue #653

## Scout: skipped
Skip condition: the issue text mandates reuse of #577's existing round-scoped
phase-2 signal ("Distinguish phase-1 from phase-2 using the SAME signal #577's
fix uses, not a re-invention") — this leaves no external-field design decision
open to scout. It is a compose-existing-mechanism task, not a novel design.

## Deployed surface today

- `on-the-record/hooks/pr-preflight.sh` (PreToolUse on `Bash`, matches
  `gh pr create|edit`) already ports `check_body`/`_plan_from_body` inline and
  already `deny()`s a phase-2 PR body missing `Closes #<n>`, naming the exact
  hint (`'Closes #<n>' (or Fixes/Resolves #<n>) in the PR body`). Wired in
  `hooks.json:34`.
- `on-the-record/hooks/contract-guard.sh` (PreToolUse on `Bash`, matches
  `gh pr merge`) denies the same class at merge time, and — per #577 — scopes
  its `phase2` determination to APPROVE comments **newer than the PR's own
  head branch's first commit** (`contract-guard.sh:119-165`), so a prior
  round's approval cannot gate a new round's phase-1 PR.
- `pr-preflight.sh`'s own `phase2` determination (`pr-preflight.sh:114-119`)
  has **no such round-scoping** — it treats any matching APPROVE comment on
  the issue as phase-2, unconditionally. This is the literal #577 defect,
  un-composed, sitting in a second location contract-guard.sh already fixed
  in one location.
- Claude Code `PreToolUse` hooks in this deployment only return
  `permissionDecision: allow|deny` (+ reason/additionalContext) — no hook in
  this repo emits an `updatedInput`/command-rewrite field, and none of
  `pr-preflight.sh`/`contract-guard.sh`/`claim-scan-preflight.sh`/
  `retry-loop-bound.sh` mutate the intercepted Bash command. There is no
  deployed mechanism to rewrite `gh pr create ...` in flight to inject a
  trailer.
- `pr-preflight.sh` reads `--body-file <path>` content on the hook's own
  filesystem at check time (`pr-preflight.sh:60-69`), *before* the underlying
  Bash command has run. A body file written in the same compound command
  (`printf ... > f && gh pr create --body-file f`) or via `$()`
  process-substitution-then-write does not exist yet when the hook reads it,
  so `open()` fails and the hook fails open (exits 0, no check performed).
  This is a second, independent gap alongside the missing round-scoping —
  either can let a bad phase-2 body through preflight uncaught, later
  surfacing only as `contract-guard.sh`'s merge-time deny (the "body-edit-
  then-merge workaround" the issue describes).

## Why auto-attach is not viable on this surface

Auto-attach ("rewrite the command to inject the trailer before it runs")
would need the hook framework to return a modified tool input for `Bash`.
No hook in this deployed plugin does that, and nothing in `hooks.json`'s
schema usage here supports it. Composing a full command-rewrite path is out
of scope for a zero-install, no-Actions hook (the issue's own constraint) —
it would require parsing arbitrary shell quoting/heredocs and re-serializing
a `gh pr create` invocation without breaking it, a strictly larger and more
fragile surface than the refusal path that already exists. Design leans on
**hardening the pre-create refusal**, not adding auto-attach.

## Gap this issue must close

1. Port `contract-guard.sh`'s round-scoped signal
   (`first_commit_at` check) into `pr-preflight.sh`'s `phase2` determination,
   so both hooks share one signal computation, per #653's explicit compose
   requirement.
2. Fix the body-file-read-before-write race so preflight's existing deny
   actually fires instead of failing open on the common
   `--body-file` pattern.
