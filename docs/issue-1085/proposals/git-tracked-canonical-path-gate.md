---
status: proposed
files:
  - docs/issue-1062/reports/implementation.md
  - gates/record_lint.py
  - gates/test_record_lint.py
  - on-the-record/gates/record_lint.py
  - docs/issue-1085/reports/implementation.md
---

## Request

The #1037 conformance review (PR #1084) found that
`docs/issue-1062/reports/implementation.md` (verdict `no-defect-found`) cites two evidence
paths that have never existed anywhere in this repo's git history. Re-verify #1062's
diagnosis, correct the record's false citations in place, and add an authoring-time gate check
that rejects a record citing a canonical path that isn't (and never was) tracked in git
history.

## Constraints

- The gate check must run at write time (PreToolUse), matching the existing
  `record-claim-guard.sh` / `orphaned_path_reference_check` composition — not a CI-only,
  after-the-fact scan.
- canonical: docs/issue-1085/reports/hunt-git-tracked-canonical-path-gate finding (this
  session's after-proposal warrant-hunter, `agentId a75e12d5a662a74ff`, reported inline after
  a board-gate write refusal) — `on-the-record/hooks/record-claim-guard.sh` resolves its
  `gates_dir` to `on-the-record/gates` (checked before the top-level `gates/` fallback), so the
  hook actually imports `on-the-record/gates/record_lint.py` at runtime, not `gates/record_lint.py`.
  The two files are today byte-identical, hand-kept-in-sync mirrors with no sync script. The new
  check must land in both, or the hook never executes it.
- Test fixtures use the offline, no-network throwaway-git-repo pattern
  `gates/test_record_lint.py::_repo_with_record` already establishes.
- Per the survey's re-verification, the #1062 verdict itself (`no-defect-found`) is not being
  reopened — its real support (the live `spawn.py consult`/`spawn.py panel` runs) is intact and
  committed in `docs/issue-1062/reports/implementation/survey.md`. Only the two false pointer
  citations in `implementation.md` are corrected.

## Rationale

Considered widening `orphaned_path_reference_check` itself (issue #330) to also require
`git log --all` reachability instead of adding a new function. Rejected: #330's own docstring
and test (`t_orphaned_path_reference_check_false_positives_documented_gap`,
`gates/test_record_lint.py:310`) scope it deliberately to "resolves nowhere in the working
tree" as a narrower, cheaper check than history reachability — a path can legitimately exist on
disk but be pre-stage (about to be committed in the same turn), so folding a `git log`
reachability requirement into that same function would make every not-yet-committed-but-about-
to-be-committed path reference a false positive. A separate, additive check
(`git_tracked_path_reference_check` or similar) that only fires for paths already flagged as
existing-on-disk-but-untracked keeps #330's existing behavior (and its documented gap) intact
while adding the narrower git-history guarantee #1085 asks for.

## What will be done

1. Re-verify #1062: confirmed via `git log --all --diff-filter=A --name-only` that neither
   cited path was ever committed, and confirmed the record's underlying live-run evidence
   (`docs/issue-1062/reports/implementation/survey.md`) is genuinely committed and intact.
   Retract the two false citations in `docs/issue-1062/reports/implementation.md` in place,
   replacing them with pointers to the real, committed evidence — verdict unchanged.
2. Add a new check to `gates/record_lint.py`, wired into `lint_record` and into
   `record-claim-guard.sh`'s existing `orphaned_path_reference_check` call site, that: for each
   backtick-quoted path reference under a `canonical:`/evidence-citation line that IS present
   in the working tree, additionally requires the path appear in
   `git log --all --diff-filter=A --name-only -- <path>` (i.e., was committed at some point) —
   OR is itself the file currently being written (self-citation of the in-progress record is
   not a violation). A path absent from history is refused with a message distinguishing it
   from #330's "never existed on disk at all" case.
3. Add a test in `gates/test_record_lint.py` reusing `_repo_with_record`, pinning: a record
   citing a working-tree-present-but-never-committed path is rejected.

## Out of scope

- Reopening or re-litigating the #1062 verdict itself.
- Retroactively re-linting every existing record in the repo for the same defect class (only
  the #1062 record named by this issue is corrected).
- Changing `orphaned_path_reference_check`'s (#330) existing working-tree-only behavior.

## How you'll know it worked

- `python3 -m pytest gates/test_record_lint.py -q` passes, including the new test that shows a
  record citing a nonexistent-in-history canonical path is rejected at authoring time.
- `docs/issue-1062/reports/implementation.md` no longer cites the two nonexistent paths; its
  verdict (`no-defect-found`) is unchanged and its citations point at real, committed evidence.
