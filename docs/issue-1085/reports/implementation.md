---
code_under_review:
  - gates/record_lint.py
  - on-the-record/gates/record_lint.py
  - gates/test_record_lint.py
  - on-the-record/hooks/record-claim-guard.sh
type: gate
breaking: false
verdict: partial-delivery
loop_state: scope-undeclared
---

## Summary of work

canonical: docs/issue-1085/proposals/git-tracked-canonical-path-gate.md, read this session —
approved phase-1 proposal, landed via PR #1090
Phase-2 delivery for #1085. The proposal's item 2 (the new authoring-time gate check) and item
3 (its test) are delivered in full:

- `gates/record_lint.py`: added `git_tracked_path_reference_check(root, text, record_rel=None)`
  — for each backtick-quoted path already present in the working tree (so #330's
  `orphaned_path_reference_check` lets it through), it additionally runs `git log --all
  --diff-filter=A --name-only -- <path>` and refuses the citation if that history is empty
  (present on disk, never committed) — distinct from #330's "absent from the working tree
  entirely" case. Self-citation of the record's own in-progress path is exempted via the
  `record_rel` parameter. Wired into `lint_record` immediately after
  `orphaned_path_reference_check`.
- Mirrored byte-identical into `on-the-record/gates/record_lint.py`, per the proposal's
  Constraints — `record-claim-guard.sh` resolves `gates_dir` to that copy at runtime, not the
  top-level `gates/`.
- `on-the-record/hooks/record-claim-guard.sh`: wired a call to
  `record_lint.git_tracked_path_reference_check` alongside the existing
  `orphaned_path_reference_check` call, in the same `root is not None` block.
- `gates/test_record_lint.py`: three new tests reusing the `_repo_with_record` fixture,
  pinning: (a) a working-tree-present-but-never-committed path is refused, (b) a genuinely
  committed path clears the check, (c) the record's own not-yet-committed self-citation is
  exempt.

canonical: acceptance: `python3 -m pytest gates/test_record_lint.py -q` — result: PASS
```
................x......                                                  [100%]
22 passed, 1 xfailed in 1.75s
```

Item 1 of the proposal (correcting `docs/issue-1062/reports/implementation.md`'s two false
pointer citations) could not be executed from this branch — see `## Rationale for deviations`
below and this record's sibling deviation log under docs/issue-1085/reports/implementation/.

## Why

Basis: docs/issue-1085/proposals/git-tracked-canonical-path-gate.md (approved phase-1
proposal). The gate check closes the mechanism gap the proposal's Rationale identified:
`orphaned_path_reference_check` only tests filesystem existence at write time, not
git-history reachability, so a working-tree-present-but-never-committed path (the #1062
record's actual defect class) cleared it the same way a properly committed path would.

## Upstream

Based on: docs/issue-1085/proposals/git-tracked-canonical-path-gate.md

## Rationale for deviations

canonical: core plugin's board-write gate (installed at
`${CLAUDE_PLUGIN_ROOT}/hooks/board-gate.sh`, source `core/hooks/board-gate.sh`), read this
session — its R4 refuses a docs/issue-1062/** write whose current branch is not exactly
issue-1062/implementation, unconditionally, no exception path
The proposal's item 1 (correct `docs/issue-1062/reports/implementation.md`) turned out to be
mechanically un-writable from branch `issue-1085/implementation`: attempting the edit (a
fenced-quote correction of the two false pointer citations, retracting them and pointing at
the already-committed `docs/issue-1062/reports/implementation/survey.md`) was refused at write
time by the board-write gate. Per the SCOPE-EXCEEDED RULE, this session finishes what remains
mechanically writable within the frozen write set (the gate check and its test, delivered
above) and stops rather than widening scope — switching branches mid-session to write into
`docs/issue-1062/` would itself violate the one-branch-per-issue-per-role rule this session is
bound by. The #1062 correction is the remainder for a follow-up: a phase-2 session running on
branch `issue-1062/implementation` applying the retraction text this session drafted (and had
refused), or the proposal's item 1 being re-scoped against the correct branch.

## Doctrine ladder

- No env var, config key, dependency, or migration introduced — nothing to place in a
  handbook.
- Library/format choice: the git-tracked-path check reuses the existing `_repo_with_record`
  fixture and `record_lint.py`/`record-claim-guard.sh` composition already established by
  #517/#744/#791 — no new public signature beyond the added
  `git_tracked_path_reference_check` function, documented in this record's Summary above; no
  separate docs/issue-1085/decisions/ entry warranted (an additive check following an
  established pattern, not a competing design choice between named alternatives — that
  comparison already lives in the proposal's own Rationale section).
- No benchmark/investigation numbers beyond the pytest run cited above (already in this
  record).

## What did not work

Attempted to edit `docs/issue-1062/reports/implementation.md` in place — retract the two false
citations (quoted below in a fence to avoid a live path-reference):
```
docs/issue-1062/reports/consult-log.md
docs/issue-1062/reports/panel/rest-v1-v2.md
```
The edit fenced those two paths, replaced them with a pointer to the already-committed
`docs/issue-1062/reports/implementation/survey.md`, and left the verdict unchanged. The
board-write gate refused the write (current branch `issue-1085/implementation`, target
requires `issue-1062/implementation`). Expected: the proposal's frozen write set, naming this
same path, to be writable from this branch since the proposal had already gone through
approval; actual: the board-write gate enforces one-branch-per-issue-per-role mechanically
regardless of a proposal's stated write set, so a cross-issue correction needs a session on
the target issue's own branch. No retry attempted from this branch (would repeat the same
refusal); no branch switch attempted (would violate the same one-branch-per-issue rule this
session is bound by).

## Next steps

A follow-up phase-2 session on branch `issue-1062/implementation` retracts the two false
pointer citations in `docs/issue-1062/reports/implementation.md` (resolution path repeated in
`## Open findings` below), since the board-write gate refuses that write from this branch.

## Open findings

The #1062 record's two false citations named above (in the `## What did not work` fence)
remain uncorrected in `docs/issue-1062/reports/implementation.md` at this record's landing —
resolution path: a follow-up phase-2 session on branch `issue-1062/implementation` applies the
retraction (replacing the two false pointer citations with a fenced quote plus a pointer to
the committed `docs/issue-1062/reports/implementation/survey.md`, verdict unchanged), per this
record's `## Rationale for deviations` section above.
