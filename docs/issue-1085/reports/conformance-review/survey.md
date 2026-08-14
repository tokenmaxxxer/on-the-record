---
code_under_review:
  - gates/record_lint.py
  - on-the-record/gates/record_lint.py
  - gates/test_record_lint.py
  - on-the-record/hooks/record-claim-guard.sh
  - docs/issue-1085/reports/implementation.md
type: survey
loop_state: draft
---

## Subject

commit `47b601e0` (issue-1085 phase-2: git-tracked canonical-path gate, #1099), the
`issue-1085/implementation` branch's landed delivery — no conformance-review record exists
yet for this sha (board condition per marketplace conformance-review role spec, issue-521).

## Requirement list (derived from issue #1085's Ask + Acceptance)

1. **Gate check + test** (Acceptance/check): a gate test shows a record citing a nonexistent
   canonical path is rejected at authoring time.
2. **#1062 record correction** (Acceptance/empty-state + Ask 1): re-verify #1062's diagnosis
   with real evidence; if the verdict survives, amend the record in place with corrected
   canonicals.
3. **Root-cause documentation** (Ask 2): determine why `record_lint`/the executed-live gate did
   not catch nonexistent canonical paths; add the check if absent.

Requirement's own upstream: northpole req#3 (실배선 검증 — a record's cited evidence must be
real). Provenance named by the issue: PR #1084 conformance-review survey,
`docs/issue-1062/reports/implementation.md`.

## Per-requirement verdicts (working from commit 47b601e0's diff and issue #1085's text only)

### Req 1 — gate check + test: Present

canonical: gates/record_lint.py (lines 253-293 and 493), read this session — function
`git_tracked_path_reference_check` runs `git log --all --diff-filter=A --name-only -- <path>`
for every backtick-quoted path that exists on disk (so #330's `orphaned_path_reference_check`
would clear it) and refuses the citation when that history is empty. Wired into `lint_record`.

canonical: derived: diff gates/record_lint.py on-the-record/gates/record_lint.py — the two
files are byte-identical, so the mirror carries the same check; its call site inside
`on-the-record/hooks/record-claim-guard.sh` was read in the same session.

canonical: acceptance: python3 -m pytest gates/test_record_lint.py -q — result:
```
................x......                                                  [100%]
24 tests, 1 expected-fail, rest green
```
This is the exact command the issue's own Acceptance/check item asked for, and it is now
registered in the acceptance-commands spec (docs/specs/acceptance-commands.md).

Verdict for requirement 1: satisfied by this commit.

### Req 2 — #1062 record correction: Absent within this commit's own scope

canonical: docs/issue-1085/reports/implementation.md, "Rationale for deviations" and "Open
findings" sections, read this session — the same session that built the gate check attempted
the `docs/issue-1062/reports/implementation.md` edit and was refused by the core plugin's
board-write gate (R4: a `docs/issue-1062/**` write is only permitted from branch
`issue-1062/implementation`). The session logged this as a deviation and an open finding
rather than widening scope, per the SCOPE-EXCEEDED RULE it is bound by. `verdict:
partial-delivery`, `loop_state: scope-undeclared` on that record reflect this honestly.

Separate note for the human reviewer, not part of this verdict: a different subject
(`issue-1062`, not `issue-1085`) later carried the correction on its own branch — commit
`cfeefdff` is on `origin/main` now and rewords the two false pointer citations. That commit
sits outside this review's subject and is mentioned only so the human reviewer does not read
requirement 2's verdict here as "still broken on main today."

### Req 3 — root-cause documentation: Present

canonical: docs/issue-1085/reports/implementation.md, "## Why" section, read this session —
states the mechanism gap plainly: `orphaned_path_reference_check` only tests filesystem
existence at write time, not git-history reachability, so a working-tree-present-but-never-
committed path (the #1062 record's actual defect class) cleared it identically to a properly
committed path. The `git_tracked_path_reference_check` function's own docstring in
gates/record_lint.py restates the same distinction, read earlier in this same session.

## Sampling / scope note

No sampling was needed — the reviewed commit's `code_under_review` list is 4 files, all read
in full this session, plus the record's own prose cross-checked against a live test run.

## What did not work

None.
