---
code_under_review:
  - docs/issue-705/reports/implementation.md
type: docs
breaking: false
# canonical: gh pr view 710 --json state,mergedAt,url,title
verdict: pass
loop_state: landed
---

## What was done

No new code changes in this repo this turn.

canonical: cat docs/issue-705/proposals/2026-08-11-align-post-pr-record-guidance-with-gates.md (Out of scope section)
```
- Editing the plugin files themselves in this PR (they live in other
  repos; this proposal documents and authorizes the change, the actual
  edit is a separate cross-repo unit once approved).
```
The proposal's own Out of scope section places the plugin-directive
edits (`warrant`, `coding`, `record-shape` directive.sh files) in the
`tokenmaxxxer-core`/`tokenmaxxxer-implementation` repos.

canonical: git rev-parse --abbrev-ref HEAD
```
issue-705/implementation
```
This session's branch/write scope is `on-the-record`'s
`issue-705/implementation`, a different repo than the two named above.

canonical: gh pr view 710 --json state,mergedAt,url,title
```
{"mergedAt":"2026-08-11T02:16:29Z","state":"MERGED","title":"docs(issue-705): survey + proposal to align post-PR record guidance with gates","url":"https://github.com/tokenmaxxxer/on-the-record/pull/710"}
```
PR #710 carries the phase-1 survey and proposal that make up this
proposal's entire in-scope write set.

canonical: gh pr view 979 --json state,mergedAt,url,title
```
{"mergedAt":"2026-08-12T02:45:18Z","state":"MERGED","title":"docs(issue-705): product-discovery phase-1 — issue closed by PR #710, scope staleness follow-up","url":"https://github.com/tokenmaxxxer/on-the-record/pull/979"}
```
A separate `product-discovery` session (branch
`issue-705/product-discovery`) reached the same conclusion
independently in PR #979, and registered a narrower follow-up
hypothesis (reused-branch staleness in `checkout_issue_branch`) instead
of the invoking prompt's unverified framing.

## Why

canonical: gh issue view 705 --json comments -q '.comments[].body' (2nd comment)
```
APPROVE issue-705/implementation
```
That comment opened phase 2 for this branch, following PR #710's merge
recorded above.

canonical: cat docs/issue-705/proposals/2026-08-11-align-post-pr-record-guidance-with-gates.md (files: frontmatter)
```
files:
  - docs/issue-705/reports/implementation/survey.md
  - docs/issue-705/proposals/2026-08-11-align-post-pr-record-guidance-with-gates.md
```
The approved proposal's frozen write set names only these two paths.
The proposal's Out of scope section (quoted above) places the
plugin-directive edits outside this write set and outside this repo, so
the SCOPE-EXCEEDED rule applies: this record stops at what the frozen
write set covers and reports rather than widening into another repo.

## What did not work

None.

## Rationale for deviations

canonical: cat docs/issue-705/proposals/2026-08-11-align-post-pr-record-guidance-with-gates.md (Out of scope section, quoted above)
The approved proposal names three plugin-directive edits under "What
will be" performed next. This record does not perform them — the
proposal's own Out of scope section already places them in the
`tokenmaxxxer-core`/`tokenmaxxxer-implementation` repos, outside this
session's branch and write scope. This restates the proposal's own
stated boundary; it is not a new scope call made mid-build.

## Open findings

canonical: cat docs/issue-705/reports/implementation/hunt-align-post-pr-record-guidance-with-gates.md (Verdict line)
```
Verdict: FINDING — the proposal's chosen fix (shape 2: warrant interpolates "the calling role's record directory" from the role's own rulebook) is built on a directory that does not exist
```
None open in this repo. The phase-1 hunt raised one design-error
finding against the proposal's Rationale: the "record directory" it
interpolates is not a fact any surveyed rulebook declares. That finding
concerns the cross-repo fix's design and sits with whichever
`tokenmaxxxer-core`/`tokenmaxxxer-implementation` role session performs
the plugin-directive edit, outside this repo's write scope — so it is
not carried forward as an open finding of this record.
