# Current-state survey — issue-1017 conformance-review

## Board condition (issue-521)

derived: gh pr list --state all --search "head:issue-1017/implementation" --json number,state,mergedAt,mergeCommit,title

```
[{"mergeCommit":{"oid":"834c1d5c02f58faf46290615596813a7085fe4a4"},"mergedAt":"2026-08-12T04:30:54Z","number":1026,"state":"MERGED","title":"issue-1017 phase-2: requirement linkage anchor"},{"mergeCommit":{"oid":"a5d8c924c1066606d299b6822e5b295164cd20f5"},"mergedAt":"2026-08-12T04:16:17Z","number":1020,"state":"MERGED","title":"issue-1017 phase-1: requirement linkage anchor proposal"}]
```

PR #1026 (commit 834c1d5c02f58faf46290615596813a7085fe4a4) is the phase-2 delivery commit landed on main.

canonical: find docs/issue-1017/proposals docs/issue-1017/reports -type f (this worktree, before this session's writes) — result below shows no conformance-review record path under docs/issue-1017/reports/:
```
docs/issue-1017/proposals/2026-08-12-requirement-linkage-anchor.md
docs/issue-1017/reports/implementation.md
docs/issue-1017/reports/implementation/survey.md
docs/issue-1017/reports/implementation/hunt-2026-08-12-requirement-linkage-anchor.md
```
The board condition (implementation commit landed, no conformance-review record yet) holds — this is the intended trigger for this session.

## Spec under review

Issue #1017's body (Ask section) is the spec, serving requirement R001 (docs/specs/requirements.md — dilution of user-stated requirements as the record grows). Three asks, each with sub-criteria in the issue's own Acceptance section:

1. Issue-drafting anchor — new-issue draft flagged when it cites no requirement ID and carries no infrastructure/no-direct-requirement tag.
2. Spawn anchor — spawn task text carries the requirement linkage from its issue.
3. Digest closes the loop — drift guard's uncited-live print becomes a concrete next-action line (which requirement, what its digest entry says).

Acceptance section names additional criteria: linkage-check test cases in gates/test_requirement_digest.py for the untagged and tagged-infrastructure cases; a no-flag expectation for the valid-linkage/tag case; a provenance requirement that the watchdog tick output be quoted in this review's own record.

## Delivered artifact (PR #1026, commit 834c1d5c02f58faf46290615596813a7085fe4a4)

canonical: git show 834c1d5c --stat

```
docs/issue-1017/reports/implementation.md          | 164 +++++++++++++++++++++
.../hunt-2026-08-12-requirement-linkage-anchor.md  |  42 ++++++
docs/specs/enforcement-boundary.md                 |   1 +
gates/requirement_linkage.py                       |  92 ++++++++++++
gates/test_requirement_digest.py                   |  32 ++++
gates/test_requirement_linkage.py                  |  46 ++++++
spawn.py                                            | 101 ++++++++++++-
7 files changed, 473 insertions(+), 5 deletions(-)
```

This survey locates the write surfaces named above; the requirement verdicts they satisfy or fail belong to the proposal's requirement list, checked next.

## Scout

Skip condition: this is a conformance check against a spec (issue #1017's own Ask/Acceptance text) that leaves no open design decision for the reviewer — the review's job is to map delivered code to already-stated acceptance criteria, not to design anything. No scout run; skip recorded per scout-directive.
