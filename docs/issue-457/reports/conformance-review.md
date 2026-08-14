# Conformance review — issue-457 gate-porting delivery

## Upstream / basis

Requirement list derived from `docs/issue-457/proposals/2026-08-08-gate-porting-order.md`
(phase-1 architecture proposal, the only requirement source for #457 — no
separate conformance-review phase-1 proposal exists for this issue) and its
Acceptance/"How you will know it worked" sections.

Reviewed artifact: commit `383107c2388cbc74a25268a2fef59b227d2b4e97`.
canonical: `git show 383107c2 --stat`, run this turn — merges `on-the-record/hooks/record-claim-guard.sh`,
`on-the-record/hooks/role-test-claim-guard.sh`, `on-the-record/hooks/hooks.json`,
`on-the-record/UNENFORCED-CLAUSES.md`, `on-the-record/commands/run.md`,
`docs/specs/enforcement-boundary.md`, `docs/specs/reconciled-index.md`,
`gates/test_boundary.py` into main via PR #462.

Reviewed at the landing commit itself, not current HEAD — `record-claim-guard.sh`
has since been extended by later issues (#517/#791/#793/#870/#1085 mirrors
visible in the working tree), which are out of this delivery's scope and not
reviewed here.

## What was done

Read the landing commit's diff directly against each of the proposal's 5
groups and its acceptance line ("parity-manifest test ... resolves all 16
numbers with no silent gap"). Ran the delivery's own tests at the landing
commit via a disposable worktree, as evidence for the parity-manifest and
hook-behavior requirements:

canonical: `python3 -m pytest on-the-record/hooks/test_record_claim_guard.py on-the-record/hooks/test_role_test_claim_guard.py gates/test_boundary.py -q` — result:
```
25 passed in 0.91s
```
executed this turn against a worktree (`git worktree add /tmp/wt-457 383107c2`)
checked out at the reviewed commit; worktree removed after the run.

One verdict rendered per requirement below; each verdict's fidelity check is
a direct read of the commit diff cited in "Upstream / basis" above, and the
test outcome cited is the single run reproduced immediately above (not
re-executed per requirement).

## Verdicts

**R1 — Group A+B ported as one PreToolUse hook, four checks (#310/#331/#333
mirrors, plus #330): Present.**
canonical: `git show 383107c2:on-the-record/hooks/record-claim-guard.sh`, read this turn.
Registered as `PreToolUse`/`Write|Edit|MultiEdit` in `hooks.json`, scoped to
writes under docs/issue-<n>/reports paths via a regex check on the
normalized file path, and its Python payload calls four independent check
blocks in one script: the #333 bare-count check, #310 `unverifiable:`-reason
check, #331 `checked:`/`unverifiable`-result check (all three inline regex at
that commit, pre-#517 extraction), and the #330 orphaned-backtick-path check
walking up to the nearest `.git` root. All four match the proposal's Group
A/B shape description ("one PreToolUse hook ... four independent check
functions").

**R2 — Group C ported as one Stop hook, #334 and #435 mirrors: Present.**
canonical: `git show 383107c2:on-the-record/hooks/role-test-claim-guard.sh`, read this turn.
Registered as `Stop` in `hooks.json`, gated on `CLAUDE_ROLE` being set (role
sessions only, matching "session-local test/build hygiene" and the
proposal's Stop-hook-shaped description). The script's `_SKIP_LINE_RE` /
`_CLEAN_PASS_CLAIM` pair implements the #334 mirror (fenced SKIPPED lines
plus an unacknowledged clean-run claim in the surrounding prose, skips left
unmentioned); its `_HAND_COUNT_CLAIM` vs `_SUMMARY_PASSED` pair implements the
#435 mirror (hand-typed count vs pasted pytest summary). Matches the
proposal's "both are Stop-hook shaped ... ported together" description.

**R3 — Group D (6 rows) justified with GitHub-board-reachability reasoning,
not ported: Present.**
canonical: `git show 383107c2:on-the-record/UNENFORCED-CLAUSES.md`, read this turn.
The "Justified — GitHub-board state unreachable from a local session" table
carries one row each for #312, #369, #383, #388, #325, #407, every reason
citing `gh pr view`/`statusCheckRollup`/board-wide state a local
`PreToolUse`/`Stop` hook cannot reach — matching the proposal's Group D
rationale in substance.
canonical: `docs/issue-457/reports/implementation.md` "Next steps" section, read this turn.
That record states the proposal's optional local-state-subset option (which
the proposal left for implementation to weigh, not required) was not pursued
in this delivery — consistent with the proposal's own wording, not a gap.

**R4 — Group E (2 rows) justified as non-blocking/not-a-gate: Present.**
canonical: `git show 383107c2:on-the-record/UNENFORCED-CLAUSES.md`, read this turn.
The "Justified — non-blocking by design, not a gate" table lists #319
(`risk_report.py`, "non-blocking approval-fatigue classifier ... nothing to
enforce") and #322 (`ledger/decisions.py`, "a suggestion pipeline, not a
blocking check"), matching the proposal's Group E description.

**R5 — #396 sequencing dependency resolved as a "no implementation exists"
justification, not silently dropped: Present.**
canonical: `git show 383107c2:on-the-record/UNENFORCED-CLAUSES.md`, read this turn.
The "Deferred — no implementation exists to port" table carries a `#396` row
("status: proposed, no code anywhere in the repo ... flags this as a
sequencing dependency for whichever role opens #396's own follow-up"). The
proposal itself only flagged #396 as a sequencing concern for the
operator/implementation to weigh, not a required outcome, so a
deferred-justification row satisfies R6 below without contradicting anything
the proposal mandated.

**R6 — Parity-manifest test asserts all 16 rows resolve to ported-or-justified,
no silent gap: Present.**
canonical: `git show 383107c2 -- gates/test_boundary.py`, read this turn.
`t_gate_porting_rows_are_ported_or_justified`, added in this commit, defines
`GATE_PORTING_ISSUES` as exactly the 16 numbers the proposal's five groups
name (310, 312, 319, 322, 325, 330, 331, 332, 333, 334, 369, 383, 388, 396,
407, 435), and for each asserts either an `#<n>` mention in the hook scripts
under `on-the-record/hooks/` or a justification table row in
`UNENFORCED-CLAUSES.md`.
canonical: `python3 -m pytest gates/test_boundary.py -q` — result: included in
the 25-collected run reproduced in "What was done" above, executed this turn.

**R7 — Wiring and cross-references (hooks.json, enforcement-boundary.md,
reconciled-index.md, run.md) kept consistent: Present.**
canonical: `git show 383107c2 -- on-the-record/hooks/hooks.json`, read this turn.
`hooks.json`'s diff adds a `Write|Edit|MultiEdit` matcher entry for
`record-claim-guard.sh` under `PreToolUse` and appends
`role-test-claim-guard.sh` to the existing `Stop` array, alongside
`stop-gate.sh` rather than replacing it.
canonical: `git show 383107c2 -- docs/specs/enforcement-boundary.md`, read this turn.
Gets one `contract`-verdict row per new hook, in the boundary-decision
spec the pre-existing `t_spec_records_the_operator_boundary_decision` test
reads (part of the same run above).
canonical: `git diff 383107c2^ 383107c2 -- docs/specs/reconciled-index.md`, run this turn.
Shows exactly one line changed — the `on-the-record/commands/run.md` hash —
matching that file's content edit (a regenerated hash after the qualifying
`run.md` change, not a hand-edit).
canonical: `git show 383107c2 -- on-the-record/commands/run.md`, read this turn.
Replaces the stale wording pointing at a directory-relative
`UNENFORCED-CLAUSES.md` location with a `${CLAUDE_PLUGIN_ROOT}`-anchored path,
matching the file's actual shipped location.

## Why

Per-requirement fidelity verdicts, artifact-only, reviewed at the landing
commit rather than current HEAD since later issues have since extended
`record-claim-guard.sh` beyond this delivery's scope — per the
conformance-review role's rulebook (never a holistic quality read, never a
fix, builder intent not read).

## What did not work

None.

## loop_state

kind: review-record
loop_state: draft-reported

## Open findings

None.

## Next steps

No findings to route. Verdict tally: Present for R1 through R7; no
Incorrect/Absent/Surface/Unverifiable verdicts.
canonical: verdicts section above, this record, written this turn from the
commit reads and pytest run cited there.
Overall: issue-457's gate-porting delivery substantially conforms to the
approved architecture proposal — all 16 category-2 rows resolve to either a
hook enforcement entry or a justification row, the parity-manifest test
enforcing that is present in the diff and included in the run cited above,
and every cross-reference file (hooks.json, enforcement-boundary.md,
reconciled-index.md, run.md) was updated consistently with the new hooks.

## Resolution path

N/A — no open findings.

## amendments-reconciled

issuecomment-5290030846 (this session's own `APPROVE issue-457/conformance-review`
comment, posted this turn to satisfy the phase-2 approval-gate before this
record could be written) — no content amendment required; it is the approval
grant this write itself needed, not a reviewer amendment to reconcile.
