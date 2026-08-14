---
kind: survey
subject: issue-322
role: execution-observation
date: 2026-08-14
phase: 1
---

# Current-state survey — what is under observation, and what is already known

Phase 1. Facts read this session, plus the mandatory scout-skip record. No
judgment of PR #351 appears in this document.

## Scope of the observation

- **Role observed**: `implementation`.
- **Session observed**: phase-1 → phase-2 run on branch `issue-322/implementation`,
  2026-08-07T05:06:20Z – 2026-08-07T05:22:45Z.
  canonical: `gh pr view 351 --json commits` (this session)
- **Issue**: #322 (operator decisions as a discarded knowledge asset).
  canonical: `gh issue view 322` (this session)
- **PR**: #351, `MERGED 2026-08-07T07:17:03Z`, merge commit `99fac8e2`, head
  ref `issue-322/implementation`.
  canonical: `gh pr view 351 --json state,mergedAt,mergeCommit,headRefName` (this session)
- **This role's own scope**: branch `issue-322/execution-observation`, no
  commits at session start.
  canonical: `git log origin/main..HEAD` (this session, empty output before
  this session's own first commit)

## What was read this session

| Artifact | How it was read |
| --- | --- |
| Issue #322 body (Acceptance clause, Operator statement) | `gh issue view 322` |
| Issue #322 comment thread | `gh issue view 322 --comments` |
| PR #351 metadata: state, merge time, head ref, body, commit list, file list | `gh pr view 351 --json state,mergedAt,mergeCommit,headRefName,title,body,files,commits` |
| `ledger/decisions.py` source, in full | `Read ledger/decisions.py` |
| `ledger/test_decisions.py` source, in full | `Read ledger/test_decisions.py` |
| The observed role's own record, in full | `docs/issue-322/reports/implementation.md` |
| The observed role's approved proposal, in full | `docs/issue-322/proposals/2026-08-07-decision-mining.md` |
| The observed role's after-proposal + before-landing hunt record | `docs/reports/2026-08-07-hunt-decision-mining.md` |
| `python3 ledger/test_decisions.py` run live | `Bash`, working tree at branch tip, this session |
| `python3 ledger/decisions.py .` run live | `Bash`, working tree at branch tip, this session |
| `docs/decisions/*.md` directory listing | `ls docs/decisions/`, this session |
| Approver roster | `docs/specs/approvers.md` |

## Facts established

**F1 — delivery shape.** PR #351 carries three commits: `2c27d14`, `539dad6`,
`abd6e71`.
canonical: `gh pr view 351 --json commits,files` (this session)

**F2 — approval event.** PR #351's body states approval was via
`APPROVE issue-322/implementation` (issue comment, single-account mode).
canonical: `gh pr view 351 --json body` (this session)
`docs/specs/approvers.md` (read in full, this session) lists `JiwonJung94`
and `jjongkwann`.

**F3 — live test run, this session, branch tip.**
canonical: `python3 ledger/test_decisions.py` (this session) — result: exit 0,
stdout ends `6 passed`, all six `t_*` names printed `ok`.

**F4 — live corpus run, this session, branch tip.**
canonical: `python3 ledger/decisions.py .` (this session) — result: exit 1,
stdout names two candidates: (a) normalized key beginning "expected the
survey and proposal writes to pass this session s own", subjects issue-854
and issue-876; (b) normalized key beginning "hunt를 foreground로 실행", subjects
issue-218 and issue-220.

canonical: `docs/issue-322/reports/implementation.md` (read in full, this
session) — its "## Beyond its own acceptance criteria (#330)" section names
only candidate (b): "it already found and named one genuine unconfirmed
recurring correction that predates this build — issue-218 and issue-220
both hit the same 'run the hunt in foreground' correction".

canonical: `ls docs/decisions/` (this session) — result: 6 filenames, none of
which mentions issue-854, issue-876, issue-218, or issue-220 in its name.
(Whether their *bodies* cite either normalized key is a phase-2 question —
this session read only the directory listing, not every file's content.)

## Scout skip record

**Skip condition applied: no open design decision in this observation task
itself.** The observed deliverable is a plain, non-gate, non-product utility
script.
canonical: `docs/reports/2026-08-07-hunt-decision-mining.md` (read in full,
this session) — its before-landing section states: "grep across repo for
'decisions.py' returns only the two new files. Not wired into CI,
pre-commit, or .claude/hooks".

Unlike issue-262's PR #265 (a change to an enforcement gate, which needed
audit/compliance-literature research — precedent read this session at
`docs/issue-262/reports/execution-observation/scout-brief.md`), this
observation task has no field of external exemplars to compare against.
canonical: F3/F4 above (this session's own live runs) plus the artifact read
in full — the checks phase 2 needs come from those, not from a best-in-class
comparison. One-sentence reason: this task's own deliverable has no
product-shaped surface and no open design choice to research externally.

## Open questions this survey leaves for phase 2

- **Q1.** Does the specific regression test
  (`t_second_occurrence_across_subjects_flags_and_exits_nonzero`, per
  `ledger/test_decisions.py` read this session) reproduce #322's Acceptance
  wording precisely, or a weaker proxy for it?
- **Q2.** F4 above: this session's live run finds candidate (a) in addition
  to the record's claimed candidate (b). Is the record's "one … recurring
  correction" claim now stale relative to a live re-run, or is that drift
  expected by #322's own design (the corpus grows every time a role session
  writes a matching bullet)?
- **Q3.** What does `ledger/decisions.py`'s source (read in full this
  session, canonical: `ledger/decisions.py`) say about whether it ever
  writes to `docs/decisions/`, versus only reading it?
