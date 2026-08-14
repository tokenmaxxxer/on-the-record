---
subject: issue-1080/implementation
---

# Current-state survey — execution-observation for issue-1080/implementation

## Scope

canonical: gh issue view 1080 (read this session)
Observed role: implementation. Observed branch: `issue-1080/implementation`.
Observed issue: #1080 (requirement-drift watchdog infra-tag exception,
citing northpole req#6).

canonical: gh pr view 1096 --json number,title,commits,mergeCommit,mergedAt,files (read this session)
Observed PRs: phase-1 proposal PR #1094 (merged 2026-08-12T07:29:24Z,
commit `d5a46d6c`) and phase-2 delivery PR #1096 (merged
2026-08-12T07:41:05Z, merge commit
`d0bae7adfc18aa771d1b3aa7af03616407894b90`, commits `d5a46d6c`,
`666f61f8`, `bd407dfb`).

canonical: ls docs/issue-1080/reports/ (run this session)
No prior execution-observation record exists for this branch/commit —
`docs/issue-1080/reports/` held only `implementation.md` and
`implementation/` before this session's writes.

## What was read to arrive at this scope, and in what order

canonical: gh issue view 1080, gh issue view 1080 --comments (run this session)
`gh issue view 1080` and `gh issue view 1080 --comments` were read
first — the issue text, its acceptance criteria, and the comment thread
(including the `APPROVE issue-1080/implementation` comment and two
`Judgment opened`/`Verdict: ... escalate` comments from an unrelated
delegated-judgment watcher).

canonical: gh pr list --search 1080 --state all (run this session)
`gh pr list --search 1080 --state all` located PR #1094 and PR #1096,
both listed MERGED in that command's own output.

canonical: gh pr view 1096 --json number,title,commits,mergeCommit,mergedAt,files, gh pr diff 1096 (read this session)
`gh pr view 1096 ...` and `gh pr diff 1096` were read next — the actual
diff and commit SHAs — BEFORE reading the observed role's own record
narrative (fresh-eyes ordering): three commits (`d5a46d6c` phase-1
proposal, `666f61f8` phase-1 after-proposal hunt, `bd407dfb` phase-2
implementation + record), six changed files (`spawn.py`,
`gates/test_requirement_drift.py`, the proposal,
`docs/issue-1080/reports/implementation.md`, and two hunt-record files).

canonical: gh pr diff 1094, gh pr view 1094 --json files (read this session)
`gh pr diff 1094` and `gh pr view 1094 --json files` were read to check
the scout-directive skip statement's placement relative to
proposal-shaped language in the phase-1 proposal PR's own diff.

canonical: spawn.py:2505-2545, gates/requirement_linkage.py:23,49-53 (read directly this session)
The working tree's `spawn.py` (`requirement_drift`) and
`gates/requirement_linkage.py` (`_INFRA_TAG`, `check_issue_body`) were
read directly. The merged code is present because this branch was cut
from `main` after PR #1096's merge — canonical: git log -1 --format=%H
(run this session, shows the branch tip is a descendant of main after
the merge).

canonical: docs/specs/approvers.md (read this session)
`docs/specs/approvers.md` was read to check the `approved-by-human`
trajectory criterion.

Only after all of the above was `docs/issue-1080/reports/implementation.md`
(the observed role's own record) read, per FRESH-EYES ORDERING.

## Diff hunks read (DIFF-SCOPE RULE)

canonical: gh pr diff 1096 (read this session)
From PR #1096's diff:
- `spawn.py` hunk `@@ -2515,6 +2515,16 @@` (new guarded import of
  `requirement_linkage` / `_INFRA_TAG`).
- `spawn.py` hunk `@@ -2525,6 +2535,11 @@` (the `infra_tag in text: continue`
  skip inserted into the `for item in issues + prs:` loop).
- The full new-file diffs for `gates/test_requirement_drift.py`,
  `docs/issue-1080/proposals/2026-08-12-requirement-drift-infra-tag.md`,
  `docs/issue-1080/reports/implementation.md`, and the two hunt-record
  files (entirely new files, so every line is in-scope).

Any citation in this role's later step-level findings that names a
spawn.py line outside these two hunks is context, not evidence, and
will be logged as such rather than cited as a step-level finding.

## What is known so far (facts only, no verdict language)

canonical: gh pr diff 1094 (read this session)
The phase-1 proposal (`docs/issue-1080/proposals/2026-08-12-requirement-drift-infra-tag.md`)
states a scout-directive skip condition inline, before any
`## Request`/proposal-shaped section.

canonical: gh issue view 1080 --comments (read this session), docs/specs/approvers.md (read this session)
A `docs/specs/approvers.md`-listed account (`JiwonJung94`) posted a
comment whose entire body is `APPROVE issue-1080/implementation`
(single-account mode, since the same account authored the PRs per the
commit-author field in `gh pr view 1096 --json commits`).

canonical: docs/issue-1080/reports/implementation/hunt-2026-08-12-requirement-drift-infra-tag.md (read this session via gh pr diff 1094), docs/issue-1080/reports/implementation.md (read this session via gh pr diff 1096)
The phase-1 after-proposal hunt record flagged that the approved
exemption design applies uniformly to PR bodies even though
`_INFRA_TAG` is only enforced/maintained on issue bodies elsewhere in
the codebase, and the implementation record's "Open findings" section
states this was left unresolved by design, for a follow-up.

canonical: docs/issue-1080/reports/implementation/2026-08-12-hunt-requirement-drift-infra-tag.md (read this session via gh pr diff 1096)
The pre-landing warrant hunt found an unguarded import that would have
crashed the whole advisory `_board_wide_sweep` tick; the merged diff's
first hunk above (`spawn.py` `@@ -2515,6 +2515,16 @@`) shows this was
wrapped in try/except before merge.

canonical: acceptance: python3 -m pytest gates/test_requirement_drift.py -v — result: pass (run this session)
```
$ python3 -m pytest gates/test_requirement_drift.py -v
gates/test_requirement_drift.py::test_infra_tagged_item_excluded_from_unreferenced_open PASSED
gates/test_requirement_drift.py::test_untagged_item_still_flagged PASSED
gates/test_requirement_drift.py::test_empty_tagged_items_leaves_drift_output_unchanged PASSED
gates/test_requirement_drift.py::test_enforced_uncited_requirement_not_flagged PASSED
gates/test_requirement_drift.py::test_open_uncited_requirement_still_flagged PASSED
gates/test_requirement_drift.py::test_empty_digest_produces_no_flags PASSED
6 passed in 0.06s
```

No verdict is rendered in this document — verdict-shaped language
belongs to phase 2 and is deferred to the proposal's stated plan below.
