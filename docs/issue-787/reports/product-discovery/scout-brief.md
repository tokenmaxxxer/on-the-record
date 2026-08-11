# Scout brief — issue #787

Mode: batched-sequential (single-session file reads; no parallel dispatch used — stated per
scout-directive's fallback-disclosure rule). Stages used: 1 (no deepening needed — the current-state
survey's own reading of `deliverable-guard.sh` already located the load-bearing gap; a second round
would not change any build decision, so JUDGE POINT 2 stopped here).

## Why external exemplars were not swept

This deliverable is an internal enforcement-mechanism design against this repo's own PreToolUse/
UserPromptSubmit hook API, scoped entirely by what that API can observe (tool name, tool_input,
cwd, session_id) — there is no external product category (IDE, CI gate, linter) whose "best-in-class"
shape transfers directly, because the object under design is this repo's own contract-enforcement
gate family, not a market-facing product surface. Per scout-directive's own routing rule ("non-CI
roles scout the best of their own deliverable's kind — a feasibility probe scouts prior art"), the
comparable-system sweep here is this repo's own strongest precedent gates, read directly:

- `on-the-record/hooks/deliverable-guard.sh` — the exact precedent: PreToolUse deny-and-redirect,
  gated on CLAUDE_ROLE absence, already implements the target policy ("deliverables are role work").
- `on-the-record/hooks/delegation-post-gate.sh` — same deny-and-explain shape, applied to a
  different surface (self-approval citation), confirms the repo's standard PreToolUse gate pattern:
  fail-open on parse failure, `ORCHESTRATE_OFF` kill switch, `deny(msg, hint)` with a machine-
  greppable metric line.
- `on-the-record/hooks/session-role-bind.sh` — the session-scoped, unforgeable state-file pattern
  (`<session_id>.json` snapshot written at SessionStart, first-observation-wins) every identity check
  in this repo's gates already relies on instead of trusting a live env var.

Sources: on-the-record/hooks/deliverable-guard.sh, on-the-record/hooks/delegation-post-gate.sh,
on-the-record/hooks/session-role-bind.sh, on-the-record/hooks/directive.sh, on-the-record/hooks/hooks.json
(all read directly this session).

## Must-bes this repo's own gate family already establishes

- Deny-and-redirect, never deny-and-silence: every examined gate's `deny()` includes an exact next
  action (e.g. `spawn.py <role> ... --issue <n>`), not just a refusal.
- Fail-open on hook infra failure (bad JSON, no python3), fail-closed only on a positively-identified
  policy violation — `deliverable-guard.sh` is the one deliberate exception (fails closed on missing
  `file_path`, per its own issue #287 S4 note), because silently allowing an unverifiable write is
  worse than a false deny there.
- A single, repo-wide `ORCHESTRATE_OFF` kill switch, checked first in every gate.
- Role identity resolved from the SessionStart snapshot first, live env var only as fallback — never
  the reverse, because the env var is session-writable and the snapshot is not.

## Adopt / skip for this issue's mechanism

- **Adopt**: extend `deliverable-guard.sh` in place (same file, same deny-and-redirect shape, same
  kill switch) rather than building a new UserPromptSubmit classifier — the current-state survey
  found the classifier route carries a real false-positive risk on chat/questions that the existing
  tool-call-gated design does not.
- **Skip**: a brand-new state-file layer duplicating `session-role-bind.sh`'s snapshot mechanism —
  `deliverable-guard.sh` already reads that exact snapshot for role identity; no new session-state
  plumbing is needed for this issue's fix.

## Gap line

The field's must-be this repo's own gates already meet: deny-and-redirect PreToolUse enforcement,
unforgeable role identity, a kill switch. Missing: the one precondition that lets
`deliverable-guard.sh` engage at all on an ordinary (non-self-hosted) target repo — its tree-pattern
and `approvers.md`-presence checks assume the target repo already looks like `on-the-record` itself.
