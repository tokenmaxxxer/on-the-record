---
status: proposed
files:
  - docs/issue-1124/reports/conformance-review.md
---

## Upstream / basis

Issue #1124. Approved proposal:
`docs/issue-1124/proposals/clean-reconcile-safety.md`. Delivered
implementation: commit b62e57dc, PR #1146,
`docs/issue-1124/reports/implementation.md`. Survey:
`docs/issue-1124/reports/conformance-review/survey.md`.

## Requirement list (extracted, verdict deferred to phase 2)

Requirements below are the review's fixed unit — phase 2 renders one
Present/Surface/Absent/Incorrect/Unverifiable verdict per row, from the
artifact and spec only (issue #1124 body + the delivered code/tests),
not from the builder's implementation.md prose.

1. **R1 — Reconcile tolerates a missing workspace path: skip with a
   note, never crash.** Source: issue body, Requirements bullet 1.
   Check: `_roster_reconcile_unreported` (`spawn.py`) checks
   `Path(work).exists()` right after reading a workspace-index entry's
   `work` field, and on a missing path prints a skip note and
   `continue`s instead of calling into `session_end_verdict`/
   `_issue_comments` — without raising.

2. **R2 — Reconcile keeps reporting every other reachable entry past a
   skipped one.** Source: issue body, Requirements bullet 1 ("its whole
   purpose is recovery, so it must not fail on precisely the state it
   recovers from"). Check: the `continue` at the missing-workspace
   branch sits inside the entry loop, not a structure that exits the
   loop or the function — later entries in the same loop are still
   processed.

3. **R3 — Clean must not delete a session log whose ledger entry has a
   non-landed outcome (refused/error); preserve or archive it.**
   Source: issue body, Requirements bullet 2. Check: `roster_clean`'s
   sibling-file loop consults `_ledger_log_outcomes()` and, for a
   sibling matching a ledger `log` path whose outcome is outside
   `LANDED_OUTCOMES`, moves it to `<work-base>/.archived-logs/` instead
   of unlinking it.

4. **R4 — Workspace directory deletion may stay as-is.** Source: issue
   body, Requirements bullet 2 ("Workspace deletion may stay as-is"),
   proposal Constraints section. Check: `roster_clean`'s
   `shutil.rmtree` call on the workspace directory itself is
   unconditional on the same safety/liveness/dirty checks as before
   this fix — the archive logic touches only sibling files, not the
   workspace directory.

5. **R5 — `LANDED_OUTCOMES` correctly identifies "a commit reached
   origin."** Source: proposal Rationale ("the two outcomes where
   `fail_closed_downgrade` confirms a commit reached origin"). Check:
   direct read of `classify()`'s full outcome vocabulary in `spawn.py`
   against `LANDED_OUTCOMES = {"progressed", "progressed-dirty-tree"}`
   — no other outcome literal that also means "commit reached origin"
   is missing from the set.

6. **R6 — Regression test covers both fixes.** Source: issue body,
   Requirements bullet 3; Acceptance section's four named scenarios.
   Check: `gates/test_clean_reconcile_safety.py`'s
   `CleanReconcileSafetyTest` class contains one test method per
   Acceptance scenario: (a) reconcile over a missing-workspace entry,
   (b) clean over a refused-outcome session, (c) clean over a
   progressed-outcome session, (d) empty state.

7. **R7 — Empty-state no-op.** Source: issue body Acceptance
   ("fresh install with no runs/ledger.jsonl and empty work dir — both
   commands no-op cleanly"). Check: the empty-state test exercises both
   `roster_clean` and `_roster_reconcile_unreported` with no ledger
   file and an empty work directory, and both return without error.

## Out of scope (phase 2 will not re-litigate)

- The "R001" traceability framing named in this session's invocation:
  issue #1124's own body states `infrastructure/no-direct-requirement
  ... R001 is not this issue's target` (survey.md, "Note on the
  invoking framing"). Phase 2 reviews against the issue's own stated
  Requirements/Acceptance text, not R001 — carried as an open finding,
  not a requirement row, since it is a framing discrepancy rather than
  a code-conformance question.
- Retroactive archiving of logs already deleted before this fix, and
  any change to `_workspace_index_put`/`WORKSPACE_INDEX` pruning — both
  named explicitly out of scope by the approved proposal itself; not
  re-litigated here as gaps.
- Code-quality judgment (naming, structure, efficiency) — this role
  renders per-requirement fidelity verdicts only, never a holistic
  quality read.

## Method (phase 2, once approved)

Artifact-only review: phase 2 works from `spawn.py`,
`gates/test_clean_reconcile_safety.py`, and the two spec documents
(issue #1124 body, the approved proposal) only — the builder's
`implementation.md` prose (`Why`, `What did not work`) is not read as
evidence for verdicts; it may be cited only to locate code, never to
substitute for reading the code directly.

## What did not work

None yet — phase 1, no verdicts attempted.

## loop_state

kind: proposal
loop_state: scope-proposed

## Open findings

R1 pattern: the invocation framing that opened this session names
R001 as the requirement issue #1124 cites, while the issue's own body
explicitly disclaims R001 as its target. This discrepancy is recorded
here rather than resolved unilaterally; phase 2's verdicts will be
scoped to the issue's own stated text regardless.

## Next steps

Await approval (`APPROVE issue-1124/conformance-review` per contract
v3 s19, single-account mode). On approval: render the phase-2
per-requirement verdicts (R1-R7 above) in
`docs/issue-1124/reports/conformance-review.md`, using
`review-traceability:finding-record` to write one verdict row per
requirement, and `review-severity:severity-classification` only if a
finding's risk needs explicit weighting.

## Resolution path

Phase 2 resolves R5 by a direct read of `classify()`'s outcome
vocabulary in `spawn.py` (not yet done in phase 1) before assigning a
verdict, and resolves R2 by reading the loop structure around the new
`continue` in `_roster_reconcile_unreported` directly.
