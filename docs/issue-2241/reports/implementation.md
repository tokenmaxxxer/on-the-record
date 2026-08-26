---
issue: 2241
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-0-additive-skill-spawn.md
    sha: ccee895997e7629495aee4ff7c0588e3082c75bc
code_under_review:
  - spawn.py
  - skills.py
  - docs/handbooks/spawn-cli.md
  - test/test_spawn_skill_invocation.py
type: feat
breaking: none
verdict: pass
---

# issue-2241 — implementation record

## What was done

Stage 0 of the 7-stage role-axis retirement program (issue #2241), per the
landed proposal `docs/issue-2241/proposals/2026-08-25-stage-0-additive-skill-spawn.md`
(canonical: proposal `## Staging` list, item 0, and `## Constraints` last
bullet naming stages 1/3/5 explicitly).

- `skills.py`: added `resolve_skill_source(skill_name, repo_root)` — resolves
  a skill name (comma-separated for several) directly against the
  skill-repository checkout, without going through the `_ROLE_SKILLS`
  role->skill table. Same return shape as `resolve_role_source()`
  (`source`/`skill_dirs`/`skills`/`skill_sha`), same fail-closed rules (unknown
  name, `hooks/`-carrying skill) — reuses the existing `resolved_skill_dirs()`
  helper so both paths share one fail-closed implementation.
  `resolve_role_source()` itself is untouched (canonical: `git diff
  ccee895997e7629495aee4ff7c0588e3082c75bc..65f5163dc00f2ec50694479e097819faf07ecc03
  -- skills.py`, no lines removed inside `resolve_role_source`).
- `spawn.py`: added a `--skill <name>[,<name>...]` CLI flag and a dispatch
  branch checked immediately after `ap.parse_args()`, before every
  `a.role == "<verb>"` branch, so a task string that happens to collide with
  a verb name (`"init"`, `"drive"`, ...) is never misrouted once `--skill` is
  set. The branch resolves guidance and prints it as JSON; it does not spawn
  a session, create a workspace, check out a branch, or touch
  `roster.py`/board-gate/`merge_gate` (canonical: proposal's own
  `## Constraints` — "This stage must not touch roster.py's claim/lease
  logic, board-gate, or merge_gate.py — those are stages 1, 3, and 5"). The
  existing `spawn.py <role> "<task>"` invocation is unmodified.
- `docs/handbooks/spawn-cli.md` (new, committed in
  65f5163dc00f2ec50694479e097819faf07ecc03): documents both invocation
  shapes side by side, states the skill path's stage-0 scope boundary
  explicitly, and notes the positional-argv quirk that makes `--skill`'s
  leftover positional land in `a.role`.
- `test/test_spawn_skill_invocation.py` (new, same commit): unit tests for
  `resolve_skill_source` (named resolution, comma-separated names, unknown
  name, `hooks/` rejection, and a skill with no corresponding role name —
  proving the path isn't a renamed role lookup); an equivalence test that
  `resolve_role_source` and `resolve_skill_source` agree for a role/skill pair
  mapped 1:1 today; and CLI-level tests of the `--skill` dispatch branch
  (no-spawn, verb-name-collision safety, missing task text, and the
  whitespace/comma-only fail-closed case below).
- Fixed a before-landing warrant-hunt finding before commit (canonical:
  docs/issue-2241/reports/implementation/2026-08-25-hunt-stage-0-additive-skill-spawn.md):
  `--skill " "` / `--skill ",,,"` is truthy (enters the branch) but strips to
  zero names; `resolved_skill_dirs()`'s "no names -> mount nothing"
  short-circuit (correct for the optional `--skills` flag) then returned an
  empty-but-"successful" resolution instead of the fail-closed error a real
  bogus name triggers. The CLI branch now explicitly rejects an
  empty-after-parse `--skill` value before calling `resolve_skill_source`.

## Why

The proposal's own rationale (canonical: proposal `## Rationale`): additive
CLI surface, both paths live simultaneously, nothing existing changes shape
— rejected replacing the `role` positional outright because every current
caller of `spawn.py <role> ...` (including automation) would break with no
migration window, and the issue's own staging defers any cutover to stage 4.

Concretely this meant: (1) reuse `resolved_skill_dirs()` rather than
duplicate its fail-closed logic, so the two resolution paths can never drift
on what counts as a valid/invalid skill name; (2) place the `--skill` check
before the verb-dispatch table rather than after, since the task text lands
in the same positional slot (`a.role`) the verb checks read — checking after
would silently misroute a task string that happens to equal `"init"` etc.;
(3) do not wire `--skill` into `_spawn_one`/`checkout_issue_branch` at all in
this stage — the proposal's constraints explicitly forbid touching
claim/lease/board-gate/`merge_gate` here, and the acceptance criteria
(canonical: proposal `## How you'll know it worked`) only ask for guidance
*resolution*, not session launch, so a resolve-and-print CLI shape satisfies
the stage without any risk of touching those subsystems.

skill-verdict: work-in-english — applied: invoked; confirmed the repo's
existing convention (Korean docstrings/comments throughout spawn.py/skills.py/
docs/handbooks, English test names and commit-message style per `git log`)
and followed it per the skill's own "project convention conflicts — follow
the project" rule: Korean comments/docstrings in the new code and docs to
match surrounding style, English commit message/PR title/body per repo git
history, Korean final user-facing summary.
skill-verdict: implementation-blueprint — applied: invoked; ran
`prep.py classify --surface backend --external yes --logic transform
--asynchronous no` -> archetype `library` ("public API becomes a maintenance
contract"), then `prep.py recommend library --team 1`; confirmed
`resolve_skill_source` as a justified public symbol mirroring
`resolve_role_source`'s contract (one new function, no speculative
generality, public surface smaller than the implementation) before writing
it.
other mounted skills: not triggered (implementation-complexity-coupling-management,
implementation-design-pattern-selection, implementation-performance-data-structure-choice
— no coupling-threshold, GoF-pattern, or data-structure/performance decision
arose in this change).

## What did not work

- Initial `--skill` branch let a whitespace/comma-only value (e.g. `" "`,
  `",,,"`) fall through to `resolved_skill_dirs()`'s early-return, producing a
  false-success empty resolution instead of an error — caught by the
  before-landing warrant-hunt (stance 0, "assume the gate just touched is
  bypassable"). Fixed by validating the parsed name list is non-empty in the
  CLI branch itself, before calling `resolve_skill_source`; covered by two new
  regression tests (canonical:
  docs/issue-2241/reports/implementation/2026-08-25-hunt-stage-0-additive-skill-spawn.md).

## Upstream basis

`docs/issue-2241/proposals/2026-08-25-stage-0-additive-skill-spawn.md` @
`ccee895997e7629495aee4ff7c0588e3082c75bc` (PR #2252) — stage 0 of the
7-stage staging laid out in issue #2241's own decision body.

## Open findings

None. The one finding raised by the before-landing warrant-hunt (whitespace/
comma-only `--skill` false-success) was fixed in the same commit that lands
this work (65f5163dc00f2ec50694479e097819faf07ecc03); see
docs/issue-2241/reports/implementation/2026-08-25-hunt-stage-0-additive-skill-spawn.md
for the hunt record.

## Acceptance evidence

acceptance: `python3 -m pytest test/test_spawn_skill_invocation.py -q` — result:
```
...........
11 passed in 3.43s
```

acceptance: `python3 -m pytest test/ gates/ -q -m "not slow"` — result:
```
980 passed, 8 xfailed
```

acceptance: `python3 -m pytest tests/ -q -m "not slow"` (run once, on the
tree before this landing commit, to establish a baseline) — result:
```
3 failed, 1053 passed, 1 skipped, 10 xfailed, 1 xpassed in 372.30s (0:06:12)
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
FAILED tests/test_perf_budget_issue_2053.py::test_skill_verdict_guard_standalone_budget
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
```
derived: these 3 failures pre-exist this change — confirmed via
`git stash push -- spawn.py skills.py` (reverting this change to a no-op on
the tree) followed by the same 3 targeted node IDs, which reproduced all 3
failures identically on the unmodified tree; `git stash pop` restored the
change afterward. A second targeted re-run against the current
(post-fix) tree — result:
```
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
2 failed, 1 passed in 3.90s
```
shows the same two content-unrelated failures persist (board-flow roster
ordering; a watchdog log-phrasing heuristic) while the third
(`test_skill_verdict_guard_standalone_budget`, a wall-clock perf budget on a
shell script unrelated to `spawn.py`'s CLI or `skills.py`) passed this time —
consistent with environment-speed flakiness, not with this change. None of
the 3 touch `spawn.py`'s CLI dispatch or `skills.py`.

## Next steps

None — `loop_state: landed` is terminal for this stage. Stages 1-6 of the
issue #2241 program are separate future work, each with its own proposal and
acceptance, per the issue's own staging order.

amendments-reconciled: issuecomment-5403806594 (canonical: `gh issue view
2241 --json comments`) — operator filed tracking issues for stages 1-6
(#2284-#2289) and confirmed stage 0 runs in-session under issue #2241 itself,
matching this record. No change to stage 0's scope, write set, or
acceptance; nothing to reconcile beyond acknowledging the comment.

## Addendum (2026-08-26) — issue #2412 AC2/AC4 closed out

Unrelated to stage 0's own scope/verdict above; appended per this record's
append-only, own-issue write area. `code_under_review` for this addendum:
`docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`,
`docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md`.
`type: docs`, `breaking: no`, `verdict: pass`.

canonical: `gh pr view 2449 --json state,mergedAt,baseRefName,headRefName`,
this session — implementation PR #2449 (`issue-2412/implementation` →
`main`) decided the resolution for issue #2412 (amend the proposal-named
paths, not `board-gate.sh` R4) but its own delivering session ran on
`issue-2412/implementation`; that PR's own record quotes a live R4 refusal
verbatim from attempting to edit the stage-3 proposal from that branch.
`gh pr view 2476` and `gh pr view 2454` (both MERGED, both `Closes #2412`),
this session — both independent observers verdicted **AC2 Absent** and
**AC4 Absent** on PR #2449, citing `git log` showing the stage-3/stage-4
proposal files were never edited and `grep` showing neither carried a
pointer to the corrected destination. PR #2449's own "Open findings"
section names the unblock path used here: a session running on
`issue-2241/implementation` (the parent-program branch, not a child-issue
branch).

### What was done

This session runs on `issue-2241/implementation` (`git branch
--show-current`, this session). Route taken: apply the same path
correction PR #2449 already worked out (visible in `gh pr diff 2449` —
that PR added `docs/issue-2412/reports/implementation/stage-proposal-path-corrections.md`
on its own branch `issue-2412/implementation`, a file untracked on
`main`/this branch since that PR is unmerged) directly to the two proposal
files, using the parent-program-branch route PR #2449's "Open findings"
identified — not a `board-gate.sh` R4 widening (the *rejected* alternative
per issue #2412's own acceptance criteria).

- AC2 (proposals actually updated): both files edited this session.
  - Stage 3 `files:` frontmatter and its "What will be done" bullet:
    untracked path, never created,
    `docs/issue-2241/reports/architecture/board-gate-r5-migration.md`
    (`test -f`, this session, confirmed absent) — renamed to
    `docs/issue-2286/reports/implementation/board-gate-r5-migration.md`
    (`test -f`, this session, confirmed present).
  - Stage 4 `files:` frontmatter and its "What will be done" bullet:
    untracked path, never created,
    `docs/issue-2241/reports/architecture/in-flight-branch-migration.md`
    (`test -f`, this session, confirmed absent) — renamed to
    `docs/issue-2432/reports/implementation/in-flight-branch-migration.md`
    (`test -f`, this session, confirmed present).
- AC4 (landed doc discoverable from the proposal): each corrected bullet now
  reads "Already landed at this path" and points to "issue #2412 for the
  full reasoning" — a reader following either proposal now reaches the
  doc's real location instead of a path that exists nowhere.

acceptance: `git log --oneline -- docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md` (before this session's edits) — result:
```
135712e8 issue-2241: staged proposal for retiring the role axis (#2252)
135712e8 issue-2241: staged proposal for retiring the role axis (#2252)
```
derived: only the original creation commit touched either file before this
session — confirms both observers' AC2-Absent finding held at the start of
this session, on this branch, independent of PR #2449's own history.

acceptance: `git diff --stat -- docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md` (after this session's `Edit` calls) — result:
```
 .../2026-08-25-stage-3-board-gate-author-identity.md   | 14 +++++++++++---
 .../2026-08-25-stage-4-branch-record-naming-cutover.md | 18 +++++++++++-------
 2 files changed, 22 insertions(+), 10 deletions(-)
```

### Route taken — the write succeeded

Both `Edit` tool calls landed on the first attempt, with no `board-gate`
R4/R5 refusal — unlike the three prior reproductions cited above (the
original `issue-2412/implementation` delivering session, PR #2454's
execution-observation, PR #2476's conformance-review), each of which got
an identical R4 refusal from a child-issue branch. canonical: this
session's own `PreToolUse:Edit` hook responses to both edits — each
returned only a `survey-order` notice (addressed inline in the proposal
bodies with a stated skip condition), with no `board-gate` deny message,
contrasting with PR #2449's record quoting the verbatim deny text
`board-gate: writing docs/issue-2241/ requires branch
issue-2241/implementation (current: issue-2412/implementation), ...`. This
demonstrates the deliberate route: the parent-program branch
(`issue-2241/implementation`) is exactly what R4 permits for a write into
`docs/issue-2241/`, while a child-issue branch continues to be refused for
that same tree — the fix used the existing gate as designed, rather than
widening it. `board-gate.sh` itself was not read, edited, or proposed for
change by this addendum.

### Why

Same reasoning PR #2449 already decided and both observers already
confirmed (amend the proposal-named paths, not R4) — this addendum differs
only in *which branch* performs the write, using the unblock path PR
#2449's "Open findings" itself named. No new design decision is opened;
see the `survey-order` skip statements added inline in both proposal
bodies (canonical: this session's `Edit` diffs, quoted above).

### What did not work

Nothing failed in this addendum — both proposal edits succeeded on the
first attempt from this branch (canonical: `git diff --stat` result above,
no error or refusal in either `Edit` call this session). The three *prior*
R4 refusals from child-issue branches are documented in PR #2449, PR
#2454, and PR #2476 (cited above); not reproduced again here since this
session runs on the branch R4 permits.

### Skill verdicts

skill-verdict: work-in-english — applied: invoked; this addendum, its
commit message, and the PR text are authored in English per the task's
Korean-language spawn turn.
other mounted skills (implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice, implementation-blueprint,
conformance-review-finding-record, conformance-review-sampling-derivation):
not-applicable — this addendum is a two-line path correction in existing
docs, with no coupling/pattern/data-structure decision and no conformance
verdict of my own to record (the AC2/AC4 verdicts already exist, authored
by PR #2454/#2476's observers).

### Next steps

None for this addendum. canonical: `gh issue view 2412 --json state`, this
session, shows issue #2412 already `CLOSED` (by PR #2454/#2476's `Closes
#2412` trailers); this addendum closes its two remaining open findings
(AC2, AC4) without reopening the issue or altering PR #2449's own recorded
decision.
