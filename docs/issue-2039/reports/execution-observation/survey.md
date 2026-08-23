---
kind: survey
subject: issue-2039
role: execution-observation
date: 2026-08-23
phase: 1
---

# Current-state survey — what is under observation

## Scope

canonical: gh issue view 2039 --comments (read this session)
Role observed: `implementation`, phase 1 (PR #2042) and phase 2 (PR #2049),
branch `issue-2039/implementation`. This role's own scope: branch
`issue-2039/execution-observation`, no commits at session start.

## What was read this session

`gh issue view 2039 --comments`; `gh pr view 2042 --json state,mergedAt,mergeCommit,headRefName,title,body,reviews,comments,files,commits`; `gh pr view 2049 --json state,mergedAt,mergeCommit,reviews,commits,files`; `gh pr checks 2049`; `git show issue-2039/implementation:docs/issue-2039/reports/implementation.md` (the observed role's phase-2 record — not present on this role's own branch, read via git show against the observed branch ref); `docs/issue-2039/proposals/2026-08-22-per-skill-verdict-obligation.md`; `docs/issue-2039/reports/implementation/survey.md`; `docs/specs/approvers.md`; this role's own prior-practice exemplars `docs/issue-609/reports/execution-observation.md` and `docs/issue-235/reports/execution-observation.md`.

## Facts established

**F1 — delivery shape.**
canonical: gh pr view 2042 --json state,mergedAt,files / gh pr view 2049 --json state,mergedAt,files (read this session)
PR #2042 (phase 1: proposal + survey) state `MERGED`. PR #2049 (phase 2)
state `OPEN`, `mergedAt: null` — not yet merged to main. Both target branch
`issue-2039/implementation`.

derived:
```
gh pr view 2049 --json commits -q '.commits | length'
5
```
PR #2049 carries 5 commits: `d82080a` (phase-1 survey+proposal, imported onto
this branch), `4cb699a` (spawn.py directive line), `fef59a2` (skill-verdict-
guard hook + record_lint check + tests), `a70915b` (phase-2 record),
`306dcb6` (spec rows). `gh pr checks 2049` reports no checks configured on
this branch head.

**F2 — commit trailers.**
canonical: gh pr view 2049 --json commits (read this session)
All 5 commit message bodies carry a `Subject: issue-2039` trailer; none
carries a `Closes`/`Fixes`/`Resolves` keyword in the commit message itself.
Only PR #2049's body text states `Closes #2039` — consistent with the
phase-1/phase-2 trailer-split rule.

**F3 — the approval comment does not exact-match the required string.**
canonical: gh issue view 2039 --comments (read this session)
Issue #2039 carries exactly one comment starting `APPROVE`, posted by
`JiwonJung94` (listed in `docs/specs/approvers.md`, same author as PR #2049 —
single-account path applies):

```
APPROVE issue-2039/implementation
Phase 2 per merged proposal PR #2042, exactly as proposed (shape-only skill-verdict-guard, both assembly points without double-count, zero-skill byte-inert, directive states the obligation).
```

derived:
```
python3 -c "print('APPROVE issue-2039/implementation\nPhase 2 per merged proposal PR #2042, exactly as proposed (shape-only skill-verdict-guard, both assembly points without double-count, zero-skill byte-inert, directive states the obligation).' == 'APPROVE issue-2039/implementation')"
False
```
The comment's entire body is not the exact string `APPROVE
issue-2039/implementation` — it carries a second line of rationale text.
`gh pr view 2049 --json reviews` returns `[]`, so this comment is the sole
candidate approval event.

**F4 — phase 2 proceeded on this comment regardless.**
canonical: gh pr view 2049 --json commits; gh issue view 2039 --comments (read this session, timestamps compared)
Commit `4cb699a` (spawn.py directive) through `306dcb6` (spec rows) all carry
authored timestamps after the approval comment's `createdAt`. No later comment
supersedes or corrects it before phase-2 commits begin.

**F5 — the implementation record does not mention the near-match.**
canonical: git show issue-2039/implementation:docs/issue-2039/reports/implementation.md (read this session)
The observed role's own phase-2 record states phase 2 "opened on the approval
comment" and cites the comment by its issue-comment anchor, with no note that
the comment's body exceeds the required exact string. Its own "Rationale for
deviations" section addresses only a mid-build stale-mirror bug in
`on-the-record/gates/record_lint.py`, not the approval-comment shape.

**F6 — prior practice in this role's own genre.**
canonical: docs/issue-609/reports/execution-observation.md; docs/issue-235/reports/execution-observation.md (read this session)
Two prior execution-observation records in this repo check their observed
role's approval comment against this same exact-string test and report the
result explicitly. In both of those two prior instances the check came back
clean (no near-match).

**F7 — the delivered work's file list lines up with the approved phase-1 plan.**
canonical: docs/issue-2039/proposals/2026-08-22-per-skill-verdict-obligation.md; git show issue-2039/implementation:docs/issue-2039/reports/implementation.md (read this session)
The proposal's build plan lists six items: spawn.py directive line,
`record_lint.py` check, Stop hook, tests, handbook entry, spec rows. The
record's own summary of work lists the same six items by file. This is a
checklist-shape comparison only — phase 2 has not yet re-run the tests or
verified the hook's actual runtime behavior.

## Open questions for phase 2

**Q1.**
canonical: this survey's F3-F5 (this session)
Does the near-exact-match approval comment constitute a genuine
contract-v3-s19 gap that this record must surface as a finding, or is it a
non-substantive wording variance? The mounted contract text is explicit that
"entire body" is exact-string-only and that a near-match must be stated
plainly, so phase 2 leans toward reporting it — the open question is severity
and action-item shape, not whether to report it.

**Q2.**
canonical: gh pr view 2049 --json state,mergedAt (read this session, F1)
Is PR #2049's open, not-merged-to-main status in scope for this observation,
given the invoking task frames the unit as commits landed on
`issue-2039/implementation` rather than merged to main?

**Q3.**
canonical: this survey's F7 (this session)
Beyond the file-list comparison in F7, does the delivered hook actually
enforce what issue #2039 asked — a question phase 2 answers against the
hook's own code and its test assertions, not by re-running them.
