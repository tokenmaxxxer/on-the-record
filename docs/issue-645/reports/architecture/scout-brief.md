# Scout brief — issue #645 (PreToolUse refusal of blocking foreground calls)

Mode: internal sweep (non-product deliverable — the artifact under design
*is* a hook in `on-the-record/hooks/`; the strongest comparables already
live there, same rationale as #600's brief). Stages used: 1 (sweep only;
the four hits below converge on one shape and one scoping pattern, so
judge point 1 already saturated — no deepening needed).

## Must-bes (what every comparable enforcement hook here does)
- Kill switch (`ORCHESTRATE_OFF`) and session-type scoping, both checked
  first, before any payload parsing (`retry-loop-bound.sh`,
  `approval-gate.sh`, `impact-guard.sh`).
- Stated fail posture, explicit in a comment, never implicit — fail-open
  is the house default for a parse/state/infra error on an
  additive-safety check (`retry-loop-bound.sh`'s trap, `approval-gate.sh`'s
  `gh` lookup failure); fail-closed is reserved for the trap's own
  unexpected-exit-code case, not for "I could not read the payload."
- Deny with `{"decision":"block"}` and a reason string naming the exact
  rule violated and, where the check has one, the compliant alternative
  (`impact-guard.sh`, `decision-queue-stopgate.sh`).
- Ships as a single self-contained `python3 -c`/heredoc block inside the
  `.sh`, zero external imports — zero-install constraint, matches #600's
  brief finding.

## Performance axes (where they compete / how they differ)
1. **Scoping direction**: orchestrator-only
   (`retry-loop-bound.sh`: `[ -z "${CLAUDE_ROLE:-}" ]`) vs. role-only
   (`approval-gate.sh`: `[ -n "${CLAUDE_ROLE:-}" ]`). #645 needs the
   first — the issue's own text states role sessions are non-interactive
   and exempt.
2. **Detection surface**: command-text regex only (`impact-guard.sh`
   counts `gh pr merge` occurrences in `tool_input.command`;
   `contract-guard.sh`/`pr-preflight.sh` regex the same field) vs.
   state-plus-text conjunction (#600's `decision-queue-stopgate.sh`
   extension, conjoining `decision_queue` state with reply text). No
   existing hook reads a *third* kind of signal — a boolean already
   present on the same `tool_input` object
   (`run_in_background`) — though the shape of "conjoin two independent
   fields from the same payload, neither sufficient alone" is exactly
   #600's adopted gaming-resistance model, transplanted from text+state
   to shape+flag.
3. **Gaming resistance ceiling**: every deployed `Bash`-matcher hook here
   tops out at command-*text* matching — `impact-guard.sh`,
   `contract-guard.sh`, `pr-preflight.sh`, `claim-scan-preflight.sh`,
   `spec-index-preflight.sh` all regex or substring-match the literal
   command string. None parses/executes the shell to resolve aliasing,
   `eval`, indirection through a variable, or a renamed copy of a target
   binary. This is a repo-wide, already-accepted ceiling, not a gap
   specific to #645 — the honest scoping this issue's acceptance
   criteria ask for is "this check inherits the same ceiling as every
   sibling Bash-matcher hook," not a claim of AST-level shell parsing.

## Adopt / skip
- **Adopt**: `retry-loop-bound.sh`'s exact orchestrator-only gate
  (`[ -z "${CLAUDE_ROLE:-}" ]`, checked immediately after
  `ORCHESTRATE_OFF`, before `cat` reads stdin) — the one hook in this
  repo already scoped the direction #645 needs; reuse verbatim rather
  than reinvent.
- **Adopt**: `impact-guard.sh`'s deny-with-named-alternative message
  shape — the issue's acceptance criterion 1 requires the refusal message
  name the background alternative, and this is the one deployed hook
  whose denial reason already does that (names the batch rule, not just
  "denied").
- **Adopt**: #600's conjunction gaming-resistance model (two independent
  fields, neither sufficient alone, closing the single-field gap) —
  transplanted here as (blocking command-shape regex match) AND
  (`tool_input.run_in_background` is not `true`). A shape-only check
  (deny any `spawn.py watch --follow`, regardless of backgrounding)
  would be wrong on its face — it would refuse the *compliant* backgrounded
  call the issue itself demands as the alternative. The flag is not
  optional; it is the only signal separating "legitimate background use"
  (must pass) from "blocking foreground use" (must refuse) for the same
  command text.
- **Skip**: shell-AST-level command parsing to defeat renaming/aliasing/
  `eval` indirection — no comparable hook in this repo attempts it; adding
  it here would be new scope beyond every sibling check's accepted
  ceiling, and the issue's own text says to scope the bypass honestly
  rather than close it.
- **Skip**: a brand-new persisted-state store. The check needs nothing
  beyond the single stdin payload already delivered per `PreToolUse`
  event (`tool_input.command`, `tool_input.run_in_background`,
  `session_id` for message-only purposes) — no comparable in this repo
  invents fresh state to catch a single-call shape (contrast
  `retry-loop-bound.sh`, which legitimately needs state because it counts
  *repetition* across calls; #645's check is a single-call verdict).

## Gap line
The current state (survey above) has the scoping pattern (adopt from
`retry-loop-bound.sh`) and the deny-with-alternative message pattern
(adopt from `impact-guard.sh`) already proven elsewhere in this repo. It
has **no** hook that reads `tool_input.run_in_background` at all, and
**no** enumerated blocking-call shape set. Both are the gap this issue's
proposal closes; neither requires inventing a new hook mechanism — only a
new command joining the existing `PreToolUse`+`Bash` matcher group in
`hooks.json`.

Sources (internal, no web fetch — same rationale as #600's brief, the
artifact under design lives in this repo, not an external market):
- on-the-record/hooks/retry-loop-bound.sh
- on-the-record/hooks/impact-guard.sh
- on-the-record/hooks/approval-gate.sh
- on-the-record/hooks/decision-queue-stopgate.sh (and its #600 proposal,
  docs/issue-600/proposals/2026-08-10-close-turn-on-decision-wait.md)
- on-the-record/hooks/hooks.json
- on-the-record/commands/run.md, "턴 예산 규칙 (#535)" section
- on-the-record/hooks/directive.sh (~74-90, bounded-wait / watch --follow)
