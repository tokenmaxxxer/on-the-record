---
issue: 2451
role: conformance-review
author: conformance-review
loop_state: closed
upstream:
  - path: docs/issue-2451/reports/implementation.md
    sha: b9656656c214a3ac802eeba32e0a605620ee1dc1
subject: PR #2470 (issue-2451/implementation, commit b9656656c214a3ac802eeba32e0a605620ee1dc1)
test: manual re-derivation of both executable acceptance checks (see requirement blocks below)
result: passed
assertedBy: conformance-review (builder-blind, independent session)
---

# issue-2451 — conformance-review record

## What was done

canonical: `gh issue view 2451 --repo tokenmaxxxer/on-the-record` (read
this session); `gh pr diff 2470 --repo tokenmaxxxer/on-the-record` (read
this session); `b9656656c214a3ac802eeba32e0a605620ee1dc1:docs/issue-2451/reports/implementation.md`
(read this session, only after this session's own independent
re-derivation below).

Builder-blind conformance review of PR #2470
(`issue-2451/implementation`, head commit
`b9656656c214a3ac802eeba32e0a605620ee1dc1`) against the three acceptance
checks stated verbatim in issue #2451. Each check was extracted as its
own requirement, given its own verification method, and independently
re-executed by this session rather than trusted from the PR description:

- **REQ-1** (directive diff) — Inspection.
- **REQ-2** (backfill cleanup) — Demonstration/Test.
- **REQ-3** (next merge observed with `--delete-branch`) — Analysis
  (forward-looking; not yet executable).

Full evidence and command output for each is in its own requirement
block below.

## Why

`merge-gates.md` is the directive orchestrator sessions actually read
before every `gh pr merge` call, so REQ-1's check is exactly "does the
diff add the instruction there, in the pre-merge-steps section, in the
existing bullets' voice" — a static/structural property, hence
Inspection rather than re-running any code. REQ-2 is an executed-live
cleanup with a concrete before/after count the issue itself demands be
re-derived and reported, not just cited from the builder's record, so
this review re-ran the exact cross-reference against the live remote
independently rather than accepting the PR body's numbers at face
value. REQ-3 names a future event ("the next `gh pr merge` call") that
literally cannot have happened yet — PR #2470 is still open, so it is
itself the first merge candidate this directive would apply to —
declaring it Present or Absent now would be a fabricated guess in
either direction; Unverifiable with the named future-evidence location
is the only honest verdict per this session's
`conformance-review-verdict-assignment` skill rule 3.

## Upstream basis

canonical: `gh issue view 2451 --repo tokenmaxxxer/on-the-record` (read
this session) — canonical source for the three acceptance checks below.

- `b9656656c214a3ac802eeba32e0a605620ee1dc1:docs/issue-2451/reports/implementation.md`
  — the builder's record, consulted only after this session's own
  independent re-derivation of REQ-1 and REQ-2, to compare (not adopt)
  its reported before/after counts.
- `gh pr diff 2470 --repo tokenmaxxxer/on-the-record`, same commit sha
  — direct evidence for REQ-1.
- Live queries this session ran directly against
  `tokenmaxxxer/on-the-record` (`gh pr list`, `git ls-remote --heads
  origin`, `gh pr view`) — direct evidence for REQ-2 and REQ-3,
  executed fresh this session rather than reusing the builder's
  captured output.

---

requirement: "merge-gates.md diff shows an explicit instruction to pass --delete-branch on every gh pr merge call."
spec_ref: issue #2451, Acceptance bullet 1
verdict: Present
evidence: |
  acceptance: `gh pr diff 2470 --repo tokenmaxxxer/on-the-record` — result:
  ```diff
  +- DELETE-BRANCH ON MERGE (issue #2451): every `gh pr merge` call MUST pass
  +  `--delete-branch`. The repo's `deleteBranchOnMerge` setting does not
  +  reliably cover API/CLI-driven merges — this session directly observed
  +  merged PRs (e.g. #2439, #2413) whose head branch survived without it.
  +  Omitting the flag leaves stray `issue-<n>/<role>` branches on the
  +  remote after merge.
  ```
  acceptance: `git show origin/main:on-the-record/directive/merge-gates.md | grep -n DELETE-BRANCH; echo "exit:$?"` — result:
  ```
  exit:1
  ```
  (no match on `main` — confirms the bullet is a genuine net-new
  addition carried only on the PR branch, not already present)
rationale: The diff both exists and reads as an unconditional MUST
  instruction covering "every gh pr merge call," matching the check's
  wording exactly, and is absent from `main` pre-merge; this is a
  static/structural presence check (Inspection), fully satisfied.

---

requirement: "Backfill cleanup: before/after cross-reference of gh pr list --state merged headRefName against git ls-remote --heads drops to zero, without deleting any branch a still-open PR (including a recut PR reusing the same branch name) points at."
spec_ref: issue #2451, Acceptance bullet 2
verdict: Present
evidence: |
  acceptance: independent re-derivation this session, `gh pr list --repo tokenmaxxxer/on-the-record --state merged --json headRefName,number --limit 2000` × `git ls-remote --heads origin` × `gh pr list --state open --json headRefName,number`, set-difference (merged ∩ remote-heads) − open — result:
  ```
  merged PR count: 1507
  remote heads count: 33
  stray count: 0
  ```
  This matches the builder's claimed AFTER figure
  (`b9656656c214a3ac802eeba32e0a605620ee1dc1:docs/issue-2451/reports/implementation.md`,
  "AFTER stray count: 0"), independently reproduced rather than trusted.

  acceptance: `gh pr list --repo tokenmaxxxer/on-the-record --state all --head <branch>` run once per each of the 11 branches the builder's record claims were deleted — result:
  ```
  issue-1978/implementation:           #1987 CLOSED, #1985 MERGED, #1983 CLOSED, #1980 CLOSED, #1979 MERGED
  issue-2001/implementation:           #2005 CLOSED, #2003 MERGED, #2002 MERGED
  issue-2156/conformance-review:       #2162 MERGED
  issue-2186/implementation:           #2192 MERGED
  issue-2187/implementation:           #2191 MERGED
  issue-2227/execution-observation:    #2346 MERGED
  issue-2274/conformance-review:       #2316 MERGED
  issue-2293/execution-observation:    #2374 MERGED, #2361 CLOSED
  issue-2413/conformance-review:       #2428 CLOSED, #2423 MERGED
  issue-2413/execution-observation:    #2427 CLOSED, #2424 MERGED
  issue-2414/conformance-review:       #2435 CLOSED, #2426 MERGED
  ```
  No PR under any of these 11 branch names is in state OPEN — confirms
  none was a live recut-branch (#2402) case at review time.

  Could not independently re-derive the builder's claimed BEFORE count
  (11) since the branches are already deleted and the prior remote
  state is not separately recorded outside the builder's own record —
  this one sub-figure is taken on the builder's word, but the check's
  pass/fail condition (AFTER == 0, no still-open-PR branch touched) is
  independently reproduced above either way.
rationale: The live, independently-executed cross-reference returns
  zero strays right now, and the exclusion condition is independently
  confirmed to hold for every specific branch the builder claims to
  have deleted — this is Demonstration/Test-grade evidence, not a
  restatement of the PR body.

---

requirement: "After this issue lands, this orchestrator session's (or a future session's) next gh pr merge call is observed to include --delete-branch and the resulting branch is confirmed deleted via git ls-remote immediately after."
spec_ref: issue #2451, Acceptance bullet 3
verdict: Unverifiable
evidence: |
  acceptance: `gh pr view 2470 --repo tokenmaxxxer/on-the-record --json state,mergeable` — result:
  ```
  {"mergeable":"MERGEABLE","state":"OPEN"}
  ```
  PR #2470 — the vehicle for this very directive change, and the first
  merge this directive would apply to — is still OPEN as of this
  review. No `gh pr merge` call has been made against this repo since
  the directive bullet was authored, so there is no merge event yet to
  observe. The missing evidence is specifically: the next actual
  `gh pr merge --repo tokenmaxxxer/on-the-record ...` invocation and a
  `git ls-remote --heads origin` check run immediately after it.
rationale: This check is explicitly forward-looking in the issue's own
  wording ("after this issue lands... is observed"); asserting Present
  or Absent now, before any qualifying merge event has occurred, would
  be a guess in either direction rather than evidence. Per
  conformance-review-verdict-assignment rule 3, the honest verdict is
  Unverifiable with the missing-evidence location named, not a
  favorable Present.

## Open findings

None. REQ-3's Unverifiable status is not an open finding to resolve by
this review — it resolves itself the moment a qualifying `gh pr merge`
call happens and is checked (evidence: same `gh pr view 2470 --json
state,mergeable` block above showing OPEN today), which by the issue's
own design is a future/other-session event, not something this review
can force or simulate without actually merging a PR (out of scope for
a conformance-review session per this repo's role-handoff contract).

## Next steps

derived: from the two requirement blocks above — REQ-1's `gh pr diff
2470` / `git show origin/main:...` result, and REQ-2's `gh pr list` ×
`git ls-remote --heads origin` result, both re-run by this session
(see acceptance blocks above).

REQ-1 and REQ-2 both independently re-derived Present per those blocks;
REQ-3 (evidence: `gh pr view 2470 --json state,mergeable` → `OPEN`,
same requirement block above) remains a standing forward observation
for whichever session executes the next real `gh pr merge` against
this repo. No further action is queued for this conformance-review
session itself, and `loop_state` is set to the terminal value `closed`
in this record's own frontmatter above.

derived: this session's own Skill-tool invocation log this turn — six
`Skill` tool calls this session (conformance-review-requirement-extraction,
conformance-review-verification-method-selection,
conformance-review-verdict-assignment,
conformance-review-traceability-and-evidence,
conformance-review-finding-record, implementation-audit) — cross-checked
against the mounted-skill list in this session's own prompt for the
three marked not-applicable below.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split the issue's Acceptance section into REQ-1/REQ-2/REQ-3 one-obligation-per-line, kept REQ-3 as its own item rather than merging it into REQ-2 despite both concerning branch deletion
skill-verdict: conformance-review-verification-method-selection — applied: invoked; assigned Inspection to REQ-1 (static diff-presence), Demonstration/Test to REQ-2 (live re-executed cross-reference), Analysis to REQ-3 (condition not yet reproducible — the merge event hasn't happened)
skill-verdict: conformance-review-verdict-assignment — applied: invoked; REQ-1/REQ-2 Present only after independent re-derivation (not surface-matched from the PR body), REQ-3 Unverifiable with the specific missing future-evidence location named rather than a favorable guess
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; each requirement block above cites the exact commands re-run and the commit sha (b9656656c214a3ac802eeba32e0a605620ee1dc1) the evidence was checked against
skill-verdict: conformance-review-finding-record — applied: invoked; wrote one --- delimited block per requirement above with requirement/spec_ref/verdict/evidence/rationale, refusing none since evidence was locatable for all three
skill-verdict: implementation-audit — applied: invoked; this session's own identity (a fresh conformance-review session, distinct from the implementation session whose commit is b9656656c214a3ac802eeba32e0a605620ee1dc1) is the basis for treating its re-derivation above as independent rather than self-review
skill-verdict: conformance-review-sampling-derivation — not-applicable: issue #2451's Acceptance section (canonical: `gh issue view 2451`, quoted in Upstream basis above) lists exactly 3 checks total, full enumeration performed, no sampling scope needed
skill-verdict: conformance-review-severity-classification — not-applicable: no defect finding exists in this record to risk-weight — both executable checks above resolved Present, not a defect
skill-verdict: implementation-design-pattern-selection — not-applicable: the diff inspected in REQ-1's block above is a single directive-text bullet addition, not a code abstraction/GoF-pattern site
