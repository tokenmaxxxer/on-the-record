---
proposal: docs/issue-785/proposals/conditional-phase-split.md
---

# Hunt record — conditional-phase-split

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — gate verification checks "named upstream subject's proposal PR merged," which is satisfiable by naming ANY already-merged proposal (unrelated to the current subject's actual work), and even for a genuinely related upstream, "proposal PR merged" is a routine phase-1 event, not a human phase-2 delivery approval — so the chosen mechanism lets a role's own current subject skip its own Approve without any check binding the named upstream subject's content to the current task.
Kind: design-error
Seed: docs/issue-785/proposals/conditional-phase-split.md (## Constraints, ## Rationale, ## What will be done)
cap_seconds: 60
tier: default
diff_stat_lines: n/a (proposal doc, not yet implemented in tokenmaxxxer-core)
started_at: 2026-08-11T16:43:50+09:00
ended_at: 2026-08-11T16:45:10+09:00

### Reproduce
gh pr list --state merged --limit 5 --json number,title,headRefName
# -> includes {"headRefName":"issue-760/implementation","number":783,"title":"feat(issue-760): citation-informed tiering for What did not work"}
# This PR is real, merged, and wholly unrelated to any other subject's work.
# Under the proposal's chosen design, approval-gate.sh's verification step is:
#   "independently confirms via `gh` that the named upstream subject's proposal PR is merged"
# It never checks that the named subject's merged content corresponds to, or
# authorizes, the CURRENT subject's task. A role session (or the orchestrator,
# per its own "judgment call" per point 3) naming TOKENMAXXXER_APPROVED_UPSTREAM=issue-760
# for an unrelated current subject would pass this exact check, since PR #783
# genuinely satisfies "named upstream subject's proposal PR is merged."

### Observed
The design's stated verification predicate is satisfied by an arbitrary,
content-unrelated merged proposal (PR #783), and the proposal text never adds
a check tying the named upstream subject to the current subject's actual
deliverable — so the gate cannot distinguish "genuinely pre-approved delivery"
from "any merged PR I happened to name."

### Expected
The gate verification should require that the named upstream subject's merged
material specifically authorizes/describes the *current* subject's delivery
content (e.g. cross-referencing the current subject/issue number inside the
named upstream proposal, or requiring a human-authored phase-2 Approve record
on the upstream subject — not merely "a PR under that subject name merged"),
otherwise any already-merged, unrelated proposal can be cited to bypass the
current subject's own phase-1 Approve requirement.
