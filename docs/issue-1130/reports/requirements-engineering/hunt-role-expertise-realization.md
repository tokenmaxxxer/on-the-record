---
name: hunt-role-expertise-realization
description: warrant-hunt record for docs/issue-1130/proposals/role-expertise-realization.md
metadata:
  proposal: docs/issue-1130/proposals/role-expertise-realization.md
---

# Warrant hunt — role-expertise-realization proposal

kind: hunt-record
subject: issue-1130

## after-proposal

Dispatched: one background agent (subagent_type warrant-hunter, model sonnet), stance index 0 ("assume the gate just touched is bypassable — find the bypass"), cap 180s, tier default, dispatch count 0.

Result: FINDING. The proposal body's routing-fix section (§3, "Routing-fix proposals, 6 cause-b roles") named `on-the-record/hooks/merge-allow-gate.sh` and four new routing-check hook files (for test-authoring, issue-retrospective, interaction-design, ux-engineering) as phase-2 edit targets, none of which appeared in the frontmatter `files:` write set — a write-set/body mismatch that would let phase-2 exceed the frozen write set under textual cover from an approved proposal.

Resolution: fixed in this same session, before commit — added the five missing paths (`merge-allow-gate.sh`, `test-authoring-spawn-check.sh`, `issue-retrospective-spawn-check.sh`, `interaction-design-spawn-check.sh`, `ux-engineering-spawn-check.sh`) plus their shared test file `test_routing_fix_spawn_checks.py` to the frontmatter `files:` list, and named them explicitly in the body's §3 prose so body and frontmatter now agree.

The hunter agent itself could not write this record directly (board-gate refused a foreign role writing outside its own record area); this record is written by the requirements-engineering session that dispatched it, per contract's own instruction that a role session reports what a hunter finds rather than letting the hunter write cross-role.
