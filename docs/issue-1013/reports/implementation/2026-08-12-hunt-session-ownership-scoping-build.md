---
proposal: docs/issue-1013/proposals/session-ownership-scoping-build.md
---

# Hunt record — session-ownership-scoping-build

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — the proposal's frontmatter write set (`spawn.py`, `tests/test_spawn.py`) omits `docs/issue-1013/reports/implementation.md`, a file the proposal's own "What will be done" section commits the build to writing ("`docs/issue-1013/reports/implementation.md` recording the build").
Kind: design-error
Seed: docs/issue-1013/proposals/session-ownership-scoping-build.md (new, untracked)
cap_seconds: 120
tier: default
diff_stat_lines: new file, 130 lines
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
grep -n '^files:' -A3 docs/issue-1013/proposals/session-ownership-scoping-build.md
grep -n 'reports/implementation.md' docs/issue-1013/proposals/session-ownership-scoping-build.md
```

### Observed
The frontmatter lists only:
```
files:
  - spawn.py
  - tests/test_spawn.py
```
but the "What will be done" section's last bullet reads: "`docs/issue-1013/reports/implementation.md` recording the build." No hook in `on-the-record/hooks/` actually cross-checks a Write/Edit tool call's path against the proposal's declared `files:` frontmatter list (confirmed by grepping all hooks for any parse of a proposal's `files:` key against tool_input paths — none exists; `approval-gate.sh` only checks a fixed `docs/issue-<n>/reports/<role>.md` pattern independent of any proposal's declared write set). So the mechanical gate happens to admit the report write anyway, but the proposal's own accounting of its write set is internally inconsistent: it authorizes and later performs a write to a path it never declared as in-scope.

### Expected
The `files:` frontmatter should list every path the proposal's own body commits to writing, including `docs/issue-1013/reports/implementation.md`, so the declared write set actually matches the work the proposal authorizes.
