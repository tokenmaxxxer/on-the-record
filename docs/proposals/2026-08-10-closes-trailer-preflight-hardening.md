---
status: proposed
files:
  - docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md
---

## Intent
Rewrite the phase-1 architecture proposal for issue #653 per the
orchestrator's relayed feedback (issue #653 comment 5236513161,
2026-08-10): five real recurrences show refusal-hardening alone can't
help a session that's structurally incapable of writing the trailer, so
the ADR now adopts "the merge broker (`contract-guard.sh`, at `gh pr
merge` time) attaches/corrects `Closes #<n>` itself before allowing the
merge" as the primary mechanism, judged by: a decided merge must never
deadlock even if the session never writes the trailer.

## Constraints
- This turn only rewrites the phase-1 ADR document
  (`docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md`);
  it does not touch `on-the-record/hooks/*` — that's phase-2, gated on
  approval per role-handoff contract v3 s19.
- Zero-install, no GitHub Actions (issue's stated constraint).
- Must reuse #577's round-scoped phase-2 signal, not re-invent it.
- Auto-attach via rewriting the intercepted `Bash` tool input is still
  ruled out on this deployed surface — but the revised design below does
  not need that capability; it acts via a plain `gh pr edit` side effect
  inside `contract-guard.sh`, not input rewriting. See the rewritten ADR
  itself for the full rationale.

## Will do (this turn)
Rewrite `docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md`
in place: revised Context (record the orchestrator feedback and the
deadlock-freedom judgment criterion), revised Decision (auto-attach/correct
`Closes #<n>` in `contract-guard.sh` at `gh pr merge` time,
falling back to deny only if the `gh pr edit` write itself fails; downgrade
`pr-preflight.sh` hardening to out-of-scope/deferred), revised Alternatives
(add refusal-hardening-only as a rejected alternative with the evidence
that killed it), revised C4 and Hand-off to match. `survey.md` is kept
as-is per the orchestrator's instruction — its recorded facts still hold.

## Out of scope
- Any actual code change to `on-the-record/hooks/*` — phase-2, gated on
  approval per contract v3 s19.
- Auto-attach via rewriting the intercepted `Bash` command itself.
- CI/Actions-based enforcement.

## How we'll know it worked
The rewritten ADR states an auto-attach-at-merge mechanism that satisfies
the orchestrator's own stated judgment criterion in its Decision section
in plain terms: a decided merge does not deadlock even if the session
never writes the trailer. The phase-2 fixture test (once approved and
implemented) will drive a phase-2 merge attempt with a missing/wrong Closes
trailer and assert the merged PR body ends up correct without any edit
from the calling session.

## What did not work
(none — this turn only rewrites the proposal document)
