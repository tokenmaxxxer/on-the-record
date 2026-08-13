---
proposal: docs/issue-1156/proposals/per-role-quality-bars.md
---

# Hunt record — per-role-quality-bars

## after-proposal — stance 1: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — anti-circularity identity check compares self-declared role identity, not a real distinct actor, so one operator can produce the diff under one CLAUDE_ROLE and author the passing verdict under another CLAUDE_ROLE in the same session, satisfying `gates/quality_bar.py`'s "author != producer" test while being the same actual account.
Kind: design-error
Seed: docs/issue-1156/proposals/per-role-quality-bars.md ("Anti-circularity" section 4); git show 516b683 --stat
cap_seconds: 60
tier: default (docs-only diff)
diff_stat_lines: 2 files changed (proposal.md, current-state-survey.md), new files
started_at: 2026-08-13T12:26:59+09:00
ended_at: 2026-08-13T12:28:30+09:00

### Reproduce
The proposal states (section 4, "Anti-circularity"):
"The bar-met/bar-not-met record's author identity ... must differ from
the identity that produced the bar-scoped diff being graded.
`gates/quality_bar.py` takes both identities as explicit inputs (never
inferred from prose) and returns `BAR_NOT_MET` ... whenever they match."

But the proposal never specifies where those "explicit inputs" come
from at the hook layer — and the sibling gate it explicitly copies the
shape from (`on-the-record/hooks/merge-allow-gate.sh`) reads the
producing/acting identity straight from the self-declared `CLAUDE_ROLE`
env var:

  grep -n "CLAUDE_ROLE" on-the-record/hooks/merge-allow-gate.sh
  # 136:role = os.environ.get("CLAUDE_ROLE", "")

Concrete bypass sketch, once phase 2 wires this per the stated design:
  1. `CLAUDE_ROLE=ux-engineering` session makes the bar-scoped diff,
     commits it as producer identity "ux-engineering".
  2. Same operator, same terminal, re-execs `CLAUDE_ROLE=accessibility`
     (a different role — trivially settable since it's just an env var,
     no authentication ties it to a distinct actual grader) and writes
     `docs/issue-<n>/reports/accessibility.md` with a `bar-met` verdict
     for the ux-engineering-scoped change.
  3. `gates/quality_bar.py(producer_identity="ux-engineering",
     author_identity="accessibility", ...)` sees identities differ and
     returns `BAR_MET` — the merge is allowed.

### Observed
Design as written treats "role identity differs" as sufficient proof
of independent review, but role identity is exactly the same kind of
self-declared, operator-controlled value (`CLAUDE_ROLE`) the sibling
gate already reads with no cross-check against a real distinct actor
or session/account boundary — so the anti-circularity check can be
satisfied by one operator alone, switching roles between producing and
grading.

### Expected
The anti-circularity design should specify binding the "author
identity" to something an operator cannot unilaterally flip between
two calls in the same control (e.g. a distinct authenticated
account/session, matching the "two-account/single-account approval
distinction" the proposal itself cites as its model) — otherwise the
gate's refusal is defeated by re-running with a different
`CLAUDE_ROLE` value, which the proposal never rules out.

## after-proposal — stance 0: assume the gate/mechanism just touched is bypassable — find the bypass

Verdict: FINDING — "phase-wise" for the 36 roles has no trigger/deadline/tracking artifact, so the self-grading gate never actually binds them; the proposal's own "applies uniformly to all 43" claim is false as written.
Kind: design-error
Seed: git diff docs/issue-1156/proposals/per-role-quality-bars.md (uncommitted working-tree changes, scope extended from 7 to 43 roles)
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: ~200
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:03:00Z

### Reproduce
grep -n "phase-wise" docs/issue-1156/proposals/per-role-quality-bars.md

Six hits (lines 46, 58, 99, 288, 387, 499), none paired with an issue
number, date, or trigger condition. Cross-check what actually gates
self-grading:

grep -n "bar-not-met\|self-grad" docs/issue-1156/proposals/per-role-quality-bars.md

§0 rule 4 ("No self-grading … §4 anti-circularity design applies
identically regardless of which of the 43 roles owns the bar") and §4/§5
only reference the `quality_bar` array and `loop_state.refusal:
bar-not-met` — fields that, per §1/§6/§7, only the 7 landing-order
roles actually receive in this phase. The 36 roles in §7 get a prose
"bar domain" + "source standard" sentence, nothing machine-checkable,
and no `quality_bar`/`bar-not-met` field.

### Observed
The Constraints section states: "This is a decomposition principle
applying uniformly to all 43 roles" (bar-level/no-self-grading/human-
review-checklist rules). But for the 36 roles there is no `quality_bar`
field, no `bar-not-met` state, and therefore §4/§5's anti-self-grading
gate has nothing to attach to — those 36 roles' specs continue to be
self-graded exactly as before this proposal, with no scheduled or
enforced follow-up: "phase-wise" names no issue, no deadline, no gate
that blocks anything if phase 2 for those 36 never lands. Nothing in
the repo (no tracking file, no open sub-issue list) turns "tracked per
role" (line 288) into an actual tracked artifact — it's asserted, not
implemented or even pointed at.

### Expected
Either the uniform-applicability claim should be scoped honestly to
"the 7 landing this phase; 36 pending, gate does not yet apply to
them," or §0/§7 should name a concrete phase-2 tracking mechanism
(e.g., a checklist file or per-role sub-issue enumerated now) so
"phase-wise" isn't an open-ended promise that lets the self-grading
gate silently not-bind 84% of roles indefinitely while the proposal
text claims uniform coverage.

## after-proposal — stance 0 (revision): assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — §0's "no self-grading applies uniformly to all 43" claim has nothing to attach to for the 36 roles named only at domain level in §7: they get no `quality_bar`/`bar-not-met` field, so the anti-circularity gate cannot bind them, and "phase-wise" named no tracking artifact or deadline, leaving the gap open-ended.
Kind: design-error
Seed: docs/issue-1156/proposals/per-role-quality-bars.md (§0, §7); uncommitted working-tree diff (scope-amendment revision, phase-1 PR #1158)
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: 1 file changed, 186 insertions(+), 18 deletions(-) (docs/issue-1156/proposals/per-role-quality-bars.md)

### Fix applied
Added a "Tracking" paragraph to §7: phase 2 records all 36 roles in
`docs/specs/role-invariant-coverage.md` with status
`bar: domain-named, decomposition-pending` (distinct from `bar-met`
and `out-of-scope`), and states explicitly that the anti-circularity
gate does not yet enforce for a role until its own decomposition PR
flips that status to a real `quality_bar` — the gap is now a recorded,
trackable status rather than an unscoped "phase-wise" promise.
