files:
  - docs/issue-2507/reports/execution-observation.md

## Request

Independently verify PR #2532 (`issue-2507/implementation`) against issue
#2507's four acceptance checks, and record the result in
`docs/issue-2507/reports/execution-observation.md`.

## Constraints

Scout/survey skip: this task has no open design decision — phase 2's
verification procedure is dictated entirely by issue #2507's own four
acceptance-check bullets, not a choice among approaches. Per the
scout-directive and survey-order-directive skip conditions ("the spec
literally leaves no design decision open"), scouting and a separate
current-state survey file are skipped; the pre-proposal investigation
below stands in their place.

- `printenv CORE_BUILD_NOW` in this session's own environment returns
  nothing (exit 1) — checked live. Contract v3 s19a's build-now bypass is
  spawner-set, never self-granted, and this session's spawner did not set
  it. `CORE_CHECKPOINT` is likewise unset (checked live, exit 1).
- approval-gate.sh mechanically confirmed this: a live `Edit` attempt on
  the record file's "What was done" section was denied — verbatim:
  "neither the PR for issue-2507/execution-observation nor issue #2507
  carries an approval from a listed human approver (jiwonjung94,
  jjongkwann): no Approve review on an open PR, and no issue comment that
  is exactly 'APPROVE issue-2507/execution-observation'... phase 2 waits
  for the human. (contract v3 s19)".
- Issue #2507 is OPEN (`gh issue view 2507`) and PR #2532
  (`issue-2507/implementation`) is OPEN, not merged (`gh pr list --search
  2507`) — the OBSERVER_ROLES closed-issue exemption in approval-gate.sh
  (issue-295) never reaches evaluation here; the base issue-open
  precondition already applies unconditionally.
- Scope: this role writes only `docs/issue-2507/reports/execution-observation.md`
  (contract's per-role record-area restriction) — no code changes, no
  other role's files.

## Rationale

Alternative considered: proceed directly into phase-2 verification work
this session, reasoning that every precedent execution-observation PR
found in this repo's history (#2521, #2518, #2499, #2249, #2524 —
`gh pr list --search execution-observation`) delivered as a single PR
with no separate phase-1 proposal, so this task "obviously" also runs
build-now.

Rejected because: (a) `printenv CORE_BUILD_NOW` in this session's own
environment returns nothing — the bypass is spawner-set per session, and
this session's spawner did not set it, regardless of what sibling
sessions for other issues received (PR #2524's own commit trailer reads
"Proposal: build-now bypass (CORE_BUILD_NOW=1, contract v3 s19a)",
confirming its session *did* have the stamp — this one does not); (b) a
live probe (an actual `Edit` attempt on the record file) was mechanically
denied by approval-gate.sh with the standard phase-2-waits-for-human
refusal, not a bypass-shaped allow. Two independent signals agree this
specific session runs the two-phase default. Assuming build-now from
precedent alone would have produced an unauthorized phase-2 write,
discovered only after investing the verification work — worse than
spending one phase-1 round trip now.

## What will be done

Phase 1 (this PR): state the verification plan below, commit, open the
PR referencing #2507 as a plain reference (no Closes trailer), then stop
— contract v3 s19's default two-session flow.

Phase 2 (after a human Approve — a PR review Approve from a
jiwonjung94/jjongkwann account different from this PR's author, or an
issue comment whose entire body is exactly `APPROVE
issue-2507/execution-observation`): independently re-verify PR #2532
against issue #2507's four acceptance checks:

1. Re-derive the 8-item deferred-remainder disposition from the code
   directly (not trusted from the implementation record's own claims),
   confirm each of the 8 items is either changed or re-scoped with a
   stated reason, and confirm none is silently dropped.
2. Run at least two live `spawn.py <role> "<task>" --issue <n>`
   invocations of different task shapes from a workspace NOT on
   `issue-2507/implementation` (avoiding the branch-collision risk the
   implementation record's own "unverifiable" finding flagged for its own
   session), quoting the resolved skill list from each spawn's own
   output.
3. Collect `bootstrap_timing` totals from at least 5 such spawns and
   compare against the pre-change baseline already stated in repo
   history/the implementation record.
4. Run `grep -rn "roles/" --include=*.py --include=*.sh` and a
   `CLAUDE_ROLE` grep against the merged tree, and name every survivor as
   intentional or not.

Record the full result, evidence, and verdict in
`docs/issue-2507/reports/execution-observation.md`.

## Out of scope

- Modifying any `src/`, `test/`, or non-record docs file.
- Merging, approving, or closing PR #2532 or issue #2507 — exclusively
  human acts.
- Re-litigating the implementation session's scope decision (7-of-8 items
  re-scoped rather than removed) beyond checking whether its stated
  reasons hold up under independent re-derivation; this role verifies, it
  does not re-propose the deferred-remainder's disposition.

## How you'll know it worked

- `docs/issue-2507/reports/execution-observation.md` exists with all
  required record-shape frontmatter/sections filled from real, executed
  evidence (not summary), and states pass/fail on all four of issue
  #2507's acceptance checks.
- Each of the required live spawn/skill-composition demonstrations quotes
  real command output, not a paraphrase.
- The `bootstrap_timing` comparison states plainly whether overhead grew,
  with real before/after numbers cited.
- The two grep commands' outputs are pasted verbatim with every hit named
  as an intentional survivor or not.
