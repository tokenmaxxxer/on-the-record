---
proposal: docs/issue-791/proposals/read-before-claim-grounding-gate-implementation.md
---

# Hunt record — read-before-claim-grounding-gate-implementation

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the grounding check the proposal wires only runs at
write-time (`record-claim-guard.sh`'s PreToolUse hook, via `lint_record()`);
nothing in this repo's architecture re-validates it afterward, so a citation
that was verbatim-grounded at commit time silently goes stale the moment the
cited file is later edited/renamed/renumbered, with no mechanism that ever
notices.
Kind: silent-failure
Seed: docs/issue-791/proposals/read-before-claim-grounding-gate-implementation.md
  (build plan: wire `defect_claim_grounding_check` into `lint_record()`'s
  aggregator, `record-claim-guard.sh`'s write-time `bad += ...` list, and
  `record-claim-shape-directive.sh`'s rules list — "no CI, no explicit
  invocation" per req#7) and
  docs/issue-791/proposals/2026-08-11-read-before-claim-grounding-gate.md
  (approved design this build proposal follows verbatim)
cap_seconds: 180
tier: size:>200
diff_stat_lines: 206
started_at: 2026-08-12T02:02:29Z
ended_at: 2026-08-12T02:03:30Z

### Reproduce

```
grep -n "lint_record\b" $(git grep -l "lint_record" -- '*.py' '*.sh')
grep -n "record_lint\." gates/ci.py
```

### Observed

`lint_record()` — the aggregator the four existing full-text checks
(`unverifiable_reason_check`, `checked_claim_reason_check`,
`bare_count_claim_check`, `orphaned_path_reference_check`,
`canonical_source_claim_check`, `outcome_claim_citation_check`) run
through, and the exact function the build proposal says to extend — is
called from exactly three places: `on-the-record/gates/record_lint.py`'s
own CLI `main()` (whole-repo scan mode, invoked by nobody automatically),
and the two hook self-test files
(`on-the-record/hooks/test_record_scaffold.py`). `gates/ci.py` — the
PR/CI-time gate — imports `record_lint` and calls four of its functions
individually (`record_enums`, `record_wellformed_in`,
`record_no_tool_residue_in`, `record_checked_claims`), but never
`lint_record`. So the only caller that ever runs the grounding check
against a real record is `record-claim-guard.sh`, a PreToolUse hook that
fires exactly once, at the moment the record file is written in that
session. Per req#7 (stated as a hard constraint by both proposals: "no
CI... primary path"), this stays the only invocation site — the build
proposal does not add a CI re-check, and none of the existing four
full-text checks it's modeled on have one either.

### Expected

Either: the design should state (and it does not) that a grounded
citation is a point-in-time claim only, valid at write-time and never
re-verified — making "grounded" a claim about the past, not an invariant
the repo maintains; or the design should specify what re-validates a
citation against later changes to the cited file (a periodic re-scan of
existing records' `lint_record()`, wired into CI or a watcher, the way
`record_wellformed_in`/`record_checked_claims` already are for the checks
that *do* get PR-time re-verification). As written, a `git mv`, refactor,
or later edit to a cited file after a defect-claim record is merged
silently unships the very guarantee ("real, in-context, verbatim-matching
content is present") the gate is built to make — with no check, hook, or
CI step anywhere in the repository that will ever notice or re-flag it.
