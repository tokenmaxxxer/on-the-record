---
subject: issue-2093
role: conformance-review
kind: survey
loop_state: surveying
---

# Current-state survey — conformance review of issue #2093

## Scope of this survey

What exists today that a conformance review of issue #2093 would have to
check against, and what does not exist yet. This is phase-1 material: it
names the review surface and its unknowns, and it is the input the review
plan (docs/issue-2093/proposals/conformance-review-plan.md) is drafted
from. No verdict is rendered here.

## 1. What has landed on the branch under review

canonical: `git log --oneline origin/main..origin/issue-2093/implementation`
and `git diff --stat origin/main...origin/issue-2093/implementation`, run in
this workspace at HEAD `934fd631015ba48190d62666a0c353e41ff48912` (main) with
`origin/issue-2093/implementation` at
`d6141ea6944042cf3353664273591e132c90fd7c`.

derived: `git diff --stat origin/main...origin/issue-2093/implementation`

```
 docs/issue-2093/proposals/hook-crash-class-fix.md  | 184 ++++++++++++++++
 docs/issue-2093/reports/implementation.md          | 101 +++++++++
 .../reports/implementation/scout-brief.md          |  86 ++++++++
 docs/issue-2093/reports/implementation/survey.md   | 236 +++++++++++++++++++++
 4 files changed, 607 insertions(+)
```

canonical: the same `git diff --stat` output quoted above.
Two commits: `1245e87d` (phase-1 survey + proposal) and `d6141ea6` (phase-1
record stub carrying skill-verdict lines). The branch carries documents only —
no path under `on-the-record/hooks/`, `gates/`, or `test/` appears in that
diff.

The direct consequence for this review: no target artifact for issue #2093's
three acceptance checks exists on that branch yet.

canonical: `git diff --stat origin/main...origin/issue-2093/implementation`
(quoted above) shows no `on-the-record/hooks/` path.
The conformance test file, the shared-parser test, and the crash-ledger test
are all named in the implementation proposal's `files:` write set as artifacts
its work-item list intends to create, and all three are absent from the diff.
A conformance review run against this branch state can therefore render
verdicts only on the phase-1 artifacts — the proposal's fidelity to the issue
— and must classify the acceptance checks themselves as Absent-pending-phase-2
rather than Unverifiable-through-reviewer-limitation.

## 2. The upstream spec surface

canonical: `gh issue view 2093` and `gh issue view 2093 --comments`, read in
this session.
The requirement source is GitHub issue #2093 itself; there is no
`docs/specs/` entry for it, and the issue's own header reads
`requirement: infrastructure/no-direct-requirement`. The issue carries:

- a **Class evidence** paragraph naming #2092 as one instance,
- a **Scope** section with three numbered design-bearing items (shared
  hook-input library; crash-conformance test; fail-open visibility),
- an **Acceptance** section with three `check:` lines, an `empty state:` line,
  and a `provenance: executed-unit via pytest` line.

Only one spec version is in force — the issue body as of this review, with
3 comments, all orchestration notes: a delegated-judgment open, an
`escalate` verdict, and a session-end note pointing at PR #2095. No
superseded draft appeared in that output, so no version-pin ambiguity applies.

## 3. The hook population the acceptance checks range over

derived: `grep -c '"command"' on-the-record/hooks/hooks.json`

```
58
```

derived: `grep -o '"[A-Za-z]*ToolUse"\|"SessionStart"\|"Stop"\|"UserPromptSubmit"' on-the-record/hooks/hooks.json | sort | uniq -c`

```
      1 "PostToolUse"
      1 "PreToolUse"
      1 "SessionStart"
      1 "Stop"
      1 "UserPromptSubmit"
```

58 registered command entries across 5 events. The same script can appear
under more than one registration with different argv, so "every hook in
hooks.json" (acceptance check 1) is ambiguous between *script files* and
*registration entries*. The implementation proposal resolves it to entries and
says so; this review has to check the delivered test against that same reading
rather than silently substituting the other one.

The corpus dimension is independent of the hook dimension: the issue names
seven edge inputs (tilde cd, heredoc body, nested quotes, unicode, empty
command, 100KB command, missing fields), and the proposal expands that to nine
cases. 58 x 9 is a full cross-product of two independent dimensions — the
review cannot re-execute and eyeball every cell, so it needs a stated sampling
derivation rather than a flat spot-check.

## 4. Known behaviour that a naive review would misread as a defect

canonical: `docs/handbooks/on-the-record.md:8-11`, read in this workspace:
```
`deliverable-guard.sh` fails closed (deny, exit 2) on stdin it cannot
verify — empty stdin, non-JSON stdin, a non-dict JSON payload, or a
payload missing `file_path`/`notebook_path` — not just on the trap-caught
crash paths (issue #287 S4).
```

One guard in the corpus is therefore deliberately fail-closed. A conformance
test asserting "exit code in {0, 2}" has to encode exit 2 as the *declared
expectation* for that hook on garbage input, not as an exemption and not as a
failure. A review that flagged exit 2 there as non-conformance would be
reading the handbook backwards. The implementation proposal already states
this in its `## Constraints`; the review's task is to check that the delivered
test honours it.

## 5. Precedent for the deliverable shape

canonical: `docs/issue-749/reports/conformance-review.md:1-58`, read in this
workspace. It is the nearest landed example of this role's record:
frontmatter (`subject`, `role`, `kind`, `loop_state`), a summary-of-work
heading, a rationale heading, an upstream list, a per-requirement verdict
table with an Evidence column, and an explicit provenance note where the cited
upstream had not landed its own phase-2 record. That last element matters here
for the same reason: issue #2093's implementation record on the implementation
branch is a phase-1 stub, per the §1 diff.

The verdict vocabulary differs across precedents: issue-749 used
MET/PARTIAL/GAP; the conformance-review skill set mounted for this session
names Present / Surface / Absent / Incorrect / Unverifiable. This is an open
choice the review plan has to settle rather than leave implicit.

## 6. Unknowns this survey could not close

- **Phase-2 timing.** Whether the implementation branch's phase-2 code lands
  before this review's phase 2 opens is outside this session's control. The
  review plan has to be written so it degrades honestly if the code is still
  absent at execution time, instead of assuming its presence.
- **PR #2095's review state.** The issue comment stream names the PR; this
  survey did not read its review or approval state, and the plan does not
  depend on it.
- **Whether #2092's instance fix is on main.**
  canonical: `git log --oneline -3`, run in this workspace — the top line is
  `934fd631 issue-2092: expand tilde before using cd-extracted path as
  subprocess cwd (#2094)`. The implementation proposal's `## Constraints`
  states "#2092 has not landed: the only commit anywhere referencing it is a
  one-line consult-trace". Those two do not agree at the commit this session
  reads. Carried forward as a candidate finding for the review proper, not
  rendered as a verdict here.

## Open findings

None rendered — this is a survey, not the review. The third bullet of §6 is
carried forward as a candidate finding for phase 2.
