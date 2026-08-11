---
subject: issue-846
kind: adr
status: accepted
---

# ADR — narrow retry-loop-bound.sh's fatigue `allow` to `tool_name != "Bash"`

## Context

`on-the-record/hooks/retry-loop-bound.sh` (issue #507) emits
`permissionDecision: "allow"` at the K-th identical denial regardless of
`tool_name`, keyed only on `(tool_name, target)` retry count and the
prior, unrelated denying gate's reason text. issue #834's before-landing
hunt (its text survives only in the diff of unlanded PR #843; recovered
and independently reproduced in
`docs/issue-846/reports/implementation/survey.md`, "Reproduction on this
branch, before any fix") showed this composes badly with content-aware
`Bash` allow-gates: `spawn-allow-gate.sh` (#834) correctly withholds its
own allow for a command-substitution-in-`cd`-prefix payload, but after 5
denials from an unrelated, state-dependent gate (e.g. `plan-order-guard.sh`
fail-open), `retry-loop-bound.sh`'s independent `allow` becomes the only
permission signal left for that exact call. Issue #846 hands off two
judgments to this decision.

## Judgment 1 — keep the fatigue hook's `allow` at all?

**Decision: keep it, for non-`Bash` tool_names.**

`#507`'s own approved rationale
(`docs/issue-507/proposals/2026-08-08-retry-loop-bound.md`, ## Rationale)
chose allow-with-corrective-context over a pure abort specifically so a
session's next identical retry proceeds with a hint instead of forcing a
second multi-minute retry storm just to surface it — a design answering
`#505`'s measured, `Write`-shaped problem
(`docs/issue-505/reports/implementation.md`: 22-52 identical retries with
no adaptation). Every validated use of this path today
(`on-the-record/hooks/test_retry_loop_bound.py`'s existing fixtures) is
`Write`-shaped; this issue's reproduction never implicates it. Dropping
`allow` everywhere would regress a validated, already-shipped behavior to
fix a risk this ADR's survey shows is specific to `Bash`.

Rejected alternative: switch the whole hook to deny/stop-only. Rejected
because it throws away #507's validated teach-instead-of-reblock value for
every `tool_name`, including the `Write` cases it was built and measured
against, to fix a risk that (per the grep below) does not exist on that
axis today.

## Judgment 2 — if kept, narrow the scope, and where?

**Decision: scope the K-tier `allow` branch out for `tool_name == "Bash"`
categorically, inside `retry-loop-bound.sh` itself. No content re-check.**

The issue named two placements: the fatigue hook re-checking the incoming
command's shape itself (reimplementing `merge-allow-gate.sh`'s/
`spawn-allow-gate.sh`'s `shlex`-based tokenize-then-check-operator-tokens
test), or a shared discriminator function the two gates expose. Both
`merge-allow-gate.sh` and `spawn-allow-gate.sh` are frozen by issue #846's
own scope, so neither gate can be edited to expose a shared function. An
inline reimplementation was rejected too: it creates a third,
independently-maintained copy of that same shape check — this repo's own
history already shows that class of copy drifting (#824's check needed a
deliberate #834 port to reach a second file at all); a third copy inside a
fatigue hook is more surface for the same drift, not a fix for it.

Chosen instead: a categorical `tool_name == "Bash"` scope-out needs no
knowledge of any gate's specific command shape, cannot go stale as
`merge-allow-gate.sh`/`spawn-allow-gate.sh` evolve or as future
`Bash`-scoped content-aware allow-gates are added, and changes no
currently-tested behavior (no existing fixture in
`test_retry_loop_bound.py` used `tool_name = "Bash"` before this change).
The `additionalContext` corrective nudge is kept unconditionally for
`Bash` — informing without granting a permission signal is a pattern
`claim-scan-preflight.sh` already uses on `PreToolUse`, independent of any
specific command match.

## Why `Bash`-only and not every `tool_name`

An after-proposal warrant hunt
(`docs/issue-846/reports/implementation/2026-08-11-hunt-narrow-retry-fatigue-allow-to-non-bash.md`)
found the proposal's first draft asserted the `Bash`-only scope instead of
checking it, and reproduced the same composition shape on `tool_name =
"Write"` using `approval-gate.sh` (a real, shipped `Write|Edit|MultiEdit`
gate with a documented fail-open path). The survey resolved this by
grepping every hook `hooks.json` registers on the `Write|Edit|MultiEdit`
matcher for `permissionDecision` emission:

```
$ grep -n "permissionDecision" on-the-record/hooks/{record-claim-guard,record-tiering-guard,role-spec-reference-guard,call-shape-guard,accumulation-claim-guard,approval-gate,deliverable-guard,retry-loop-bound}.sh
record-claim-guard.sh: 0
record-tiering-guard.sh: 0
role-spec-reference-guard.sh: 0
call-shape-guard.sh: 0
accumulation-claim-guard.sh: 0
approval-gate.sh: 0
deliverable-guard.sh: 0
retry-loop-bound.sh: 2
```

`retry-loop-bound.sh` is the only hook on that matcher group that ever
emits `permissionDecision` at all; `approval-gate.sh` is deny-only by its
own header comment. So no `Write`/`Edit`/`MultiEdit` gate today
deliberately withholds an allow the way `merge-allow-gate.sh`/
`spawn-allow-gate.sh` do for `Bash` — there is nothing on that axis for
`retry-loop-bound.sh`'s independent allow to override. `Bash`-only is
this decision's actual, checked scope. If a `Write`/`Edit`/`MultiEdit`
content-aware allow-gate is added later, this grep is the check to re-run
and this scope-out would need to widen with it.

## Consequences

- `retry-loop-bound.sh`'s K-tier branch for `tool_name == "Bash"` now
  emits `hookSpecificOutput.additionalContext` only — no
  `permissionDecision`/`permissionDecisionReason` — so it can never be the
  sole permission signal for a `Bash` call a content-aware gate is
  withholding allow for. The `2K` abort path is unaffected for every
  `tool_name` (a deny only restricts; it carries none of this risk).
- Every other `tool_name` (all of #507's validated, tested usage) keeps
  the exact allow-with-context behavior shipped and approved under #507.
- If a future `Bash`-scoped content-aware allow-gate is added, or an
  existing `Write`/`Edit`/`MultiEdit` gate grows a deliberate-withhold
  shape, this ADR's scope must be revisited via the grep above.
