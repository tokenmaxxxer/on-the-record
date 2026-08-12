---
proposal: docs/issue-1111/proposals/2026-08-13-product-capture-ownership.md
---

# Hunt record — product-capture-ownership

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — the frozen write set omits `runs/rulebooks/tokenmaxxxer-core/core/hooks/board-gate.sh`, a separate, currently-active PreToolUse gate in this same repo that denies any docs path not in the six standing buckets (_assets, decisions, handbooks, proposals, reports, specs) or a docs/issue-<n>/ tree — so the target file the frozen write set names as its own deliverable is refused by this other gate before `on-the-record/hooks/deliverable-guard.sh`'s exemption is ever reached.
Kind: composition
Seed: docs/issue-1111/proposals/2026-08-13-product-capture-ownership.md (frozen write set: on-the-record/hooks/deliverable-guard.sh, on-the-record/hooks/test_deliverable_guard.py, and a file under a docs/product/ directory)
cap_seconds: 120
tier: default
diff_stat_lines: 3 files changed (proposal, consult-log, survey) + unrelated .pull-check
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:02:00Z

### Reproduce
canonical: live PreToolUse hook denial produced by this session's own Write tool call attempting to create a file under a docs/product/ directory in this checkout, plus `find / -name board-gate.sh` locating the active copy at the path named above.

Attempting a Write tool call whose file_path fell under a directory named "docs" plus "product" in this checkout triggered the board-gate.sh hook with:

PreToolUse:Bash hook error: [${CLAUDE_PLUGIN_ROOT}/hooks/board-gate.sh]: board-gate: docs/product is neither docs/README.md, one of the six standing buckets (_assets, decisions, handbooks, proposals, reports, specs), nor an issue tree (docs/issue-<n>/). (contract v3 s10)

Source: the bucket tuple is defined near the top of `runs/rulebooks/tokenmaxxxer-core/core/hooks/board-gate.sh` (BUCKETS = ("_assets", "decisions", "handbooks", "proposals", "reports", ...)) and the deny message cites contract v3 s10.

### Observed
board-gate.sh unconditionally rejects a write whose path is docs/ followed by product/... as outside the six standing buckets, independent of and prior to whatever `on-the-record/hooks/deliverable-guard.sh` decides — the deliverable-guard exemption the proposal plans to add is never reached for that path in this repo's own live hook stack.

### Expected
For the acceptance criterion (the orchestrator can write the product-capture files that `on-the-record/hooks/product-capture-stopgate.sh` already asks it to write at Stop) to hold end-to-end, the build would also need to touch board-gate.sh's bucket list (or whatever governs contract v3 s10) to admit the product-capture directory as a legal target. That file is not in the proposal's frozen write set.
