---
status: approved
files:
  - on-the-record/hooks/gh-write-allow-gate.sh
  - on-the-record/hooks/test_gh_write_allow_gate.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
  - docs/specs/reconciled-index.md
  - docs/issue-856/reports/implementation/survey.md
  - docs/issue-856/proposals/gh-write-allow-gate.md
  - docs/issue-856/reports/implementation.md
---

## Request

Ship a plugin allow-hook that grants the orchestration session
(`CLAUDE_ROLE` unset) the `gh issue`/`gh pr` write verbs it currently
lacks — `gh issue create`, `gh issue comment`, `gh pr comment`,
`gh issue close`, `gh pr close` — default-on, no manual settings grant,
using the same design as `merge-allow-gate.sh` (#816) and
`spawn-allow-gate.sh` (#823): orchestrator-identity gate, keyed on command
shape not argument text, strict shlex command-shape validation (#834/#842).
Register it in `hooks.json` alongside the other two allow-gates. Role
sessions stay un-auto-allowed; existing deny gates stay authoritative.

## Constraints

- No manual `settings.local.json` grant may be required — default-on via
  the plugin's own `hooks.json`.
- Role sessions (`CLAUDE_ROLE` set) must never be auto-allowed by this
  hook.
- The decision must key on command SHAPE only — no token past the
  matched verb (e.g. a `--body`/comment-text argument) may ever be
  inspected, so a sensitive-looking literal in a comment body can neither
  falsely allow nor falsely block.
- This hook may only ever add a permission signal (`"allow"`); it must
  never itself emit `"deny"`, so an existing deny gate on the same event
  stays authoritative.
- No `landing_readiness.py`/readiness predicate — these are non-destructive
  forge writes (create/comment/close), unlike `gh pr merge`.

## Rationale

Two design shapes were available: (1) extend `merge-allow-gate.sh`'s own
script to also match the five new verbs, or (2) ship a new, separate
`gh-write-allow-gate.sh` file mirroring `spawn-allow-gate.sh`'s shape.

Option (1) was rejected: `merge-allow-gate.sh`'s docstring and structure
are scoped tightly to one destructive verb (`gh pr merge`) with a
readiness predicate (`gates/landing_readiness.py`) that the five verbs in
scope here do not need at all — folding non-destructive create/comment/
close verbs into that same script would force every future reader to
re-derive which of the fused verb sets does or does not carry a readiness
check, and would widen `merge-allow-gate.sh`'s own registered spec row
(`docs/specs/enforcement-boundary.md`) for a design reason (destructive vs.
non-destructive) that has nothing to do with merging. `spawn-allow-gate.sh`
already demonstrates the "no readiness predicate needed" shape for a
different verb family, so a second small file following that exact
precedent is the more legible fit than stretching `merge-allow-gate.sh`'s
scope.

## What will be done

- Add `on-the-record/hooks/gh-write-allow-gate.sh`: `PreToolUse`+`Bash`
  hook, orchestrator-identity-scoped (SessionStart snapshot first, live
  `CLAUDE_ROLE` fallback — identical primitive to the other two
  allow-gates), strict `shlex.shlex(posix=True, punctuation_chars=True)`
  command-shape validation against five recognized verb-token-prefix
  shapes (`gh issue create`, `gh issue comment`, `gh pr comment`,
  `gh issue close`, `gh pr close`), each optionally preceded by a
  `cd DIR &&` prefix, with no chaining/substitution operator token
  anywhere else in the token list. On match: emit
  `hookSpecificOutput.permissionDecision: "allow"` JSON. On any other
  shape: plain `exit 0`, no JSON. `ORCHESTRATE_OFF=1` kill switch, same
  convention as every other gate in this plugin.
- Register the new hook in `on-the-record/hooks/hooks.json`'s
  `PreToolUse`+`Bash` matcher list, after `spawn-allow-gate.sh`.
- Add `on-the-record/hooks/test_gh_write_allow_gate.py` covering: each of
  the five verbs gets `allow` for the orchestrator; a role session never
  gets `allow`; a sensitive-looking literal inside `--body` neither
  falsely allows nor falsely blocks; a stand-in deny gate's exit-code-2
  still stands independent of this gate's own allow decision (composition
  safety, since no existing gate in this repo currently denies these five
  verbs outright — see the survey); a non-gh command is untouched; chained/
  substituted command shapes are left unreached; the kill switch
  suppresses the allow.
- Add registration rows for `gh-write-allow-gate.sh` to
  `docs/specs/enforcement-boundary.md` and `docs/specs/generated-paths.md`,
  and regenerate `docs/specs/reconciled-index.md`
  (`python3 gates/spec_index.py --update`) in the same commit.

## Out of scope

- Any deny-side rule for these five verbs (e.g. denying a batch of `gh
  issue close` calls) — this proposal only adds an allow signal.
- Changing `merge-allow-gate.sh` or `spawn-allow-gate.sh` themselves.
- Any change to `approval-gate.sh` or other role-scoped gates — role
  sessions' existing restrictions are untouched.

## How you'll know it worked

`python3 on-the-record/hooks/test_gh_write_allow_gate.py` passes with no
failures, covering: orchestrator-identity allow for all five verbs;
role-session non-allow; a stand-in deny gate's verdict standing
independent of this gate's allow; sensitive-literal-in-body neither
falsely allowing nor blocking; a non-gh command left untouched. Plus
`python3 gates/test_boundary.py` and `python3 gates/test_generated_paths.py`
both continue to pass after the new hook's spec rows are added.
