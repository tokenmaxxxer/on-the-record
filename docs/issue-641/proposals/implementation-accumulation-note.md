---
status: approved
files:
  - on-the-record/commands/run.md
  - on-the-record/hooks/delegated-judgment-gate.sh
  - on-the-record/hooks/test_delegated_judgment_gate.py
  - docs/specs/reconciled-index.md
  - docs/issue-641/reports/implementation.md
---

# Proposal — issue #641: phase-2 implementation (run.md boundary + detector + spec-index)

**Scout/survey skip record**: skipped. Skip condition: the spec leaves no design decision
open — `docs/issue-641/proposals/architecture.md` (already approved, PR #646 merged)
already made every design decision this phase executes (exact run.md insertion point and
text, exact firing-condition shape and trigger vocabulary, exact file to extend). This note
exists only to carry a filled `## Accumulation` field for `accumulation-claim-guard.sh`
alongside the already-decided phase-2 work; there is no design decision left to survey.

## Request

Implement the approved `docs/issue-641/proposals/architecture.md` design: the run.md
review-is-role-work boundary text, the seventh `delegated-judgment-gate.sh` firing
condition (orchestrator-authored `gh pr/issue comment` carrying review-verdict-shaped
language without a role-record citation), its tests, and the spec-index regeneration.

## Constraints

Reuse the shipped machinery only (`conformance-review`, the judgment-axis panel,
`open_decision_item` triage) — no new review mechanism. The detector stays advisory
(fail-open, comment-only), per the architecture proposal's stated detectability verdict.

## Rationale

Considered adding a brand-new standalone hook for the detector instead of extending
`delegated-judgment-gate.sh`. Rejected: the file already owns orchestrator-issued `gh`
command inspection (the #597 sixth firing condition is the identical shape — a `gh`
subcommand match, a lexical body check, an advisory audit comment) and a second hook
duplicating that plumbing (payload parsing, `_gh` helper, branch/CLAUDE_ROLE checks) would
itself be the kind of accumulation this note exists to account for, with no offsetting
benefit — same file, same firing-condition pattern, per the architecture proposal's own
"extend `delegated-judgment-gate.sh`" instruction.

## What will be done

- `run.md` gains the 경계 subsection at the exact point identified in the architecture
  proposal (before the four-item summary requirement, after 2단계 머지 sub-bullet).
- `delegated-judgment-gate.sh` gains a seventh firing condition: `gh pr comment`/`gh issue
  comment` in a CLAUDE_ROLE-unset (orchestrator) session, lexical verdict-vocabulary match
  without a citation, advisory-only audit comment on a hit.
- `test_delegated_judgment_gate.py` gains four tests for the new condition (flagged,
  cited-so-not-flagged, role-session-so-not-flagged, non-verdict-so-not-flagged).
- `docs/specs/reconciled-index.md` regenerated via `gates/spec_index.py --update`.
- `docs/issue-641/reports/implementation.md` written as the phase-2 record.

## Out of scope

The Stop-hook transcript-level channel-bypass closer (chat-only critique, `gh api`
comment posting) — architecture.md leaves this as a future, differently-shaped mechanism,
not decided in this phase.

## How you'll know it worked

`python3 on-the-record/hooks/test_delegated_judgment_gate.py` passes including the four
new tests; the repo's existing full suite (gates + hooks tests) still passes;
`docs/specs/reconciled-index.md` reflects the run.md change.

## Accumulation

`test_delegated_judgment_gate.py` already carries well over the shape-1 threshold of
inline `subprocess.run`/`gh`-stub call sites (one call site per test case — the established
style every prior firing condition's tests already use, starting with #573's own tests and
extended by #597's sixth condition). This phase's four new tests for the seventh firing
condition follow that same one-call-per-test shape rather than introducing a new pattern.
Accepted amortization: the file is expected to keep growing by one test function per future
firing condition; the shared `_run_cmd`/`_stub_gh_with_stdin` helpers (already introduced by
#597) are reused rather than re-inlined, so growth stays additive test functions, not
duplicated call-site boilerplate. No new accumulation shape is introduced by this phase.
