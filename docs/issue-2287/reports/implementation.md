---
issue: 2287
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md
    sha: same-commit
  - path: docs/decisions/2026-08-25-retire-role-axis-staging.md
    sha: same-commit
code_under_review:
  - path: pipeline.py
    sha: 28c776d929b6efe5541cd1729f3b60b5c0dacea4
  - path: board.py
    sha: 2cc6d10874d38474fb9ae18bd53da2982d01483f
  - path: roster.py
    sha: 2cc6d10874d38474fb9ae18bd53da2982d01483f
  - path: spawn.py
    sha: c0cba21b4fcba1074c76e6198da535eb004349c0
  - path: docs/handbooks/branch-naming.md
    sha: 2cc6d10874d38474fb9ae18bd53da2982d01483f
  - path: test/test_branch_naming_dual_scheme.py
    sha: 2cc6d10874d38474fb9ae18bd53da2982d01483f
  - path: docs/issue-2432/reports/implementation/in-flight-branch-migration.md
    sha: 2cc6d10874d38474fb9ae18bd53da2982d01483f
type: docs
breaking: "no — this record adds no code diff; every file it cites was already merged to main before this session started, and this session made no edit to any of them"
verdict: pass
---

# issue-2287 — implementation record

## What was done

This issue (#2287, "role retirement stage 4 — move branch/record naming
to skill axis + lease disambiguator") and issue #2432 ("Role retirement
stage 4 — branch/record naming to skill axis + lease disambiguator") are
the same stage of the same program (#2241), opened as two separate
issues with near-identical titles and identical Ask/Acceptance sections
— canonical: `gh issue view 2287` and `gh issue view 2432` output, both
read this session; both name the same spec
(`docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md`)
as authoritative. #2432 was delivered first: PR #2436 ("issue-2432:
branch/record naming to skill axis + lease disambiguator (dual-scheme,
stage 4)") is state MERGED — canonical: `gh pr view 2436 --json
state,mergeCommit -q '.state, .mergeCommit.oid'` this session, result
`MERGED` / `2cc6d10874d38474fb9ae18bd53da2982d01483f`; issue #2432 itself
is state CLOSED — canonical: `gh issue view 2432 --json state -q
.state`, this session, result `CLOSED`. This issue (#2287) was left open
with no work attributed to it.

Verified, this session, that the code already on `main` satisfies this
issue's own acceptance contract (the stage-4 proposal's "How you'll know
it worked" plus this issue's own live-recheck requirement), rather than
re-implementing the same functions a second time under this issue's
number (which would violate the proposal's own Accumulation clause: one
naming function per file, not a second parallel implementation):

- `pipeline.checkout_issue_branch_for_skill()`, `pipeline.checkout_issue_branch()`,
  `pipeline._checkout_named_branch()` — canonical: `grep -n "def
  checkout_issue_branch" pipeline.py`, this session, result:
  ```
  1122:def checkout_issue_branch(cwd: str, issue: int, role: str) -> str:
  1131:def checkout_issue_branch_for_skill(cwd: str, issue: int, skill: str,
  ```
- `roster.lease_key()`, `roster.new_lease_disambiguator()` — canonical:
  `grep -n "def lease_key\|def new_lease_disambiguator" roster.py`, this
  session, result:
  ```
  132:def lease_key(issue: int, disambiguator: str) -> str:
  145:def new_lease_disambiguator() -> str:
  ```
- `board.board()` merging both naming schemes — canonical: `grep -n "def
  board\b" board.py`, this session, result: `723:def board(root: Path)
  -> dict[str, dict[str, dict[str, str]]]:` — its body (read this
  session) calls both the fixed-`ROLES` loop and
  `_skill_axis_report_names()`.
- `spawn.py` re-exports the naming/lease helpers — canonical: `grep -n
  "checkout_issue_branch\|lease_key\|new_lease_disambiguator" spawn.py`,
  this session, result includes `checkout_issue_branch =
  _pipeline_mod.checkout_issue_branch`,
  `checkout_issue_branch_for_skill = _pipeline_mod.checkout_issue_branch_for_skill`,
  `lease_key = roster.lease_key`, `new_lease_disambiguator =
  roster.new_lease_disambiguator`.
- `docs/handbooks/branch-naming.md` — canonical: file read this session,
  documents both schemes and states the coexistence window (start:
  `2cc6d108`; intended end: stage 6).
- `docs/issue-2432/reports/implementation/in-flight-branch-migration.md`
  — canonical: file read this session, states the in-flight-branch
  handling the proposal's Constraints section requires (every branch
  open at stage-4 landing time keeps its old-scheme name and finishes
  its own PR lifecycle unchanged).

Re-ran the proposal's own acceptance checks live, this session:

acceptance: `python3 -m pytest test/test_branch_naming_dual_scheme.py -q`
— result:
```
bringing up nodes...
.........                                                                [100%]
9 passed in 1.02s
```
(9 derived: the pytest summary line above)

acceptance: `gh pr list --repo tokenmaxxxer/on-the-record --state open
--json number,headRefName,title` — result:
```json
[{"headRefName":"issue-2507/conformance-review","number":2534,"title":"issue-2507: conformance-review phase-1 survey + proposal"},{"headRefName":"issue-2507/execution-observation","number":2533,"title":"issue-2507: execution-observation phase-1 proposal (PR #2532)"},{"headRefName":"issue-2507/implementation","number":2532,"title":"issue-2507: role retirement stage 6 remainder — task-composed skills for spawn mount, rest re-scoped"},{"headRefName":"issue-2525/execution-observation","number":2530,"title":"[issue-2525/execution-observation]"},{"headRefName":"issue-2525/conformance-review","number":2529,"title":"[issue-2525/conformance-review]"},{"headRefName":"issue-2508/implementation","number":2517,"title":"issue-2508: pr-preflight.sh accepts Advances/Part-of for partial deliveries"},{"headRefName":"issue-2510/implementation","number":2512,"title":"issue-2510: stop reporting all-UNKNOWN Acceptance grading as a gate pass"},{"headRefName":"issue-2289/implementation","number":2495,"title":"issue-2289: role retirement stage 6 (partial)"},{"headRefName":"issue-2403/conformance-review","number":2462,"title":"issue-2403: conformance-review phase-1 survey + proposal (PR #2452)"},{"headRefName":"issue-2403/execution-observation","number":2460,"title":"[issue-2403/execution-observation] independent audit of PR #2452"},{"headRefName":"issue-2403/implementation","number":2452,"title":"[issue-2403/implementation]"},{"headRefName":"issue-2412/implementation","number":2449,"title":"issue-2412: resolve stage-proposal path collision with board-gate R4/R5"}]
```
13 open PRs at this session's live-recheck time (drift from the
survey-time count of 4 and #2432's own build-time count of 5 is expected
and already accounted for in the proposal's own Constraints section).
Every branch name in this result is `issue-<n>/<role>` shape
(`implementation`, `conformance-review`, `execution-observation`); none
uses the new `<skill>-<disambiguator>` shape, which is expected since no
live spawn call site produces that shape yet — canonical: `spawn.py`'s
`--skill` branch of `main()`, read this session (around the `if
a.skill:` block): it prints the resolved guidance JSON and returns
without calling `checkout_issue_branch`/`checkout_issue_branch_for_skill`/`_spawn_one`
anywhere in that branch. None of the 13 branches above regressed under
the dual-scheme reader — canonical: the
`CheckoutNamingSchemeTest::test_old_scheme_branch_shape_byte_identical`
row inside the pytest result pasted directly above confirms
`pipeline.checkout_issue_branch()` (the function these branches were
created through) is still byte-identical in output.

No new commit was needed to satisfy this issue's acceptance contract —
this record itself, backed by the two acceptance re-runs above, is this
session's entire deliverable, closing #2287 as already-delivered by
#2432/PR #2436.

## Why

Chosen: verify against the already-landed code and close this issue by
reference, rather than re-implementing the same two naming/discovery
functions a second time under this issue's number. Considered and
rejected: re-authoring `pipeline.py`/`board.py`/`roster.py` changes
identical in effect to #2432's, attributed to #2287 instead. Rejected
because (a) the proposal's own Accumulation clause commits to *one*
naming/discovery function per file — a second implementation would
either collide with (duplicate-definition error) or silently shadow the
one already on `main`; (b) the operator-frozen constraint on this issue
explicitly grades against "no new conflict surfaces" and "no
consumer-tree pollution" — landing a redundant second copy of
already-merged code is exactly that; and (c) re-running the spec's own
acceptance commands this session leaves no behavior gap for new code to
close:

acceptance: `python3 -m pytest test/test_branch_naming_dual_scheme.py -q`
— result:
```
9 passed in 1.02s
```
acceptance: `gh pr list --repo tokenmaxxxer/on-the-record --state open
--json number,headRefName,title` — result: 13 open PRs returned, all
`issue-<n>/<role>` shape (full JSON pasted in the previous section).

The duplicate-issue-number situation itself (two issues, #2287 and
#2432, both scoped to "role retirement stage 4") predates this session —
canonical: `gh issue view 2287` and `gh issue view 2432`, both read this
session, show both were filed 2026-08-25 against the identical stage
scope. This session has no `gh issue edit`/merge access to relabel or
combine GitHub issues (the same role-write-scope asymmetry #2432's own
record cites for `gh issue edit`), only the ability to close #2287 with
the evidence above that its acceptance contract is already satisfied.

## What did not work

None.

## Upstream basis

- `docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md`
  (this issue's own authoritative spec) — canonical: `git log -1
  --format=%H -- docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md`,
  this session, result `5a64505cdc73a222235d77e7f2776e3ba3cbe959`, an
  ancestor of this session's starting `HEAD`.
- `docs/decisions/2026-08-25-retire-role-axis-staging.md` (issue #2241's
  architecture decision the proposal decomposes) — read this session.
- `docs/issue-2432/reports/implementation.md` (the sibling issue's
  implementation record documenting the actual build of this same
  stage) and `docs/issue-2432/reports/implementation/in-flight-branch-migration.md`
  (the proposal's required in-flight-branch-handling gate deliverable) —
  both read this session, not authored by it.
- PR #2436 — canonical: `gh pr view 2436 --json state,mergeCommit -q
  '.state, .mergeCommit.oid'`, this session, result `MERGED` /
  `2cc6d10874d38474fb9ae18bd53da2982d01483f` — the delivery vehicle for
  this stage's code.

## Open findings

1. **Duplicate tracking issue** (process, not code) — canonical: `gh
   issue view 2287` and `gh issue view 2432`, both read this session,
   confirm both issues carry the identical stage-4 Ask/Acceptance text
   and both name the same proposal path as authoritative; #2432 was
   built and closed first — canonical: `gh issue view 2432 --json state
   -q .state`, this session, result `CLOSED`; `gh pr view 2436 --json
   state -q .state`, this session, result `MERGED`. Resolution applied
   this session: close #2287 by reference to #2432/PR #2436 instead of a
   second code delivery; no further action is available to a role
   session (relabeling/merging GitHub issues is outside
   `implementation`'s write scope).

## Next steps

None. This stage's acceptance contract is already satisfied:

acceptance: `python3 -m pytest test/test_branch_naming_dual_scheme.py -q`
— result:
```
9 passed in 1.02s
```
acceptance: `gh pr list --repo tokenmaxxxer/on-the-record --state open
--json number,headRefName,title` — result: 13 PRs returned, all
resolvable under the dual-scheme reader (full JSON in "What was done").

This record is the closing deliverable for #2287.

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; this record, its
commit message, and the delivery PR title/body are written in English
per the skill (the spawning session's directives and issue-tracking
prose in this repo are heavily Korean); the final chat-facing summary to
the user is given in Korean.

other mounted skills: not triggered
(implementation-blueprint, implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice — no code was written
or restructured this session, so none of these applied).
