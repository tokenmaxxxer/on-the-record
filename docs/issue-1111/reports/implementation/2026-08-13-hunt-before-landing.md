---
proposal: docs/issue-1111/proposals/2026-08-13-product-capture-ownership.md
---

# Hunt record — product-capture-ownership

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the issue-scoped exemption in deliverable-guard.sh allows a write that board-gate.sh's R3 unconditionally denies for the same orchestrator session, making the docs/issue-<n>/reports/product/<cat>.md path unreachable in a board repo
Kind: composition
Seed: git diff main..HEAD -- on-the-record/hooks/deliverable-guard.sh on-the-record/hooks/product-capture-stopgate.sh
cap_seconds: 180
tier: default
diff_stat_lines: 11 files / 574 insertions (main..HEAD); ~100 lines in the two hook files touched here
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:10:00Z

### Reproduce
```
cd <repo root, on-the-record itself, which has docs/specs/approvers.md>
unset CLAUDE_ROLE
echo '{"tool_name":"Write","tool_input":{"file_path":"docs/issue-1111/reports/product/requirements.md","content":"x"}}' \
  | bash on-the-record/hooks/deliverable-guard.sh; echo "deliverable-guard exit: $?"

echo '{"tool_name":"Write","tool_input":{"file_path":"docs/issue-1111/reports/product/requirements.md","content":"x"}}' \
  | bash runs/rulebooks/tokenmaxxxer-core/core/hooks/board-gate.sh; echo "board-gate exit: $?"
```

### Observed
deliverable-guard.sh exits 0 (ALLOW) via the new `PRODUCT_CAPTURE_ISSUE_RE` exemption added in this
change. board-gate.sh, applied to the identical payload in the identical no-CLAUDE_ROLE orchestrator
session, exits 2 (DENY) with: "a write under docs/issue-<n>/ from a session with no CLAUDE_ROLE. The
board belongs to role sessions; this one carries no rulebook gates. (contract v3 s8/s10)" — board-gate's
R3 denies *any* docs/issue-<n>/... write from a role-less session, with no carve-out for the orchestrator
scribing exemption deliverable-guard just added. This repo is itself a board (docs/specs/approvers.md
exists), so both hooks are live simultaneously on this write.

### Expected
The proposal's exemption in deliverable-guard.sh implicitly assumes that clearing deliverable-guard is
sufficient for the orchestrator's issue-scoped product-capture write to land. It is not: board-gate.sh
(a separate hook layer that governs the same docs/issue-<n>/ tree) maintains no matching exemption for
role-less orchestrator scribing, so the issue-scoped half of product-capture-stopgate.sh's retargeted
write path (docs/issue-<n>/reports/product/<cat>.md) is dead on arrival in any repo where board-gate is
also wired in as a PreToolUse hook alongside deliverable-guard — exactly the situation on-the-record's
own repo is in. Either board-gate.sh needs a matching orchestrator-scribing carve-out, or the proposal
needs to acknowledge this path never actually writes in a board repo.
