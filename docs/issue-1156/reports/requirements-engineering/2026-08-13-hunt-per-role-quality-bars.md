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
