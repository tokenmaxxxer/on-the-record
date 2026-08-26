---
issue: 2432
role: execution-observation
author: execution-observation
loop_state: done
upstream:
  - path: docs/issue-2432/reports/implementation.md
    sha: 1f1c06773d70deb528b508fe013d98ca39bcf2fc
  - path: docs/issue-2432/reports/implementation/in-flight-branch-migration.md
    sha: 1f1c06773d70deb528b508fe013d98ca39bcf2fc
subject: PR #2436 — issue-2432/implementation (stage-4 branch/record naming cutover)
test: test/test_branch_naming_dual_scheme.py
result: passed
assertedBy: execution-observation, independently re-run this turn
---

# issue-2432 — execution-observation record

Path convention for this record: every file cited below with an explicit
`<sha>:<path>` prefix lives on `issue-2432/implementation` at sha
`1f1c0677`, not on this record's own branch
(`issue-2432/execution-observation`, based on `origin/main`). Bare paths
(no sha prefix) refer to this branch.

## What was done

Independently re-ran PR #2436's acceptance evidence rather than citing its
claims (per `defect-verification-independence-from-upstream-verdicts`).
Checked out `origin/issue-2432/implementation` at sha `1f1c0677` into an
isolated worktree this turn (`git worktree add /tmp/pr2436-review
origin/issue-2432/implementation`, since removed with `git worktree
remove` after use).

acceptance: `python3 -m pytest -v` against
`1f1c0677:test/test_branch_naming_dual_scheme.py` (run this turn, in the
`1f1c0677` worktree) — result:
```
9 passed in 0.89s
```
Same 9 node IDs, same pass count as the PR's own claimed `9 passed in
1.12s` — count matches (derived: hand count of "9" above equals pytest's
own "9 passed" summary line).

acceptance: `python3 -m pytest test/ -q -m "not slow"` (run this turn, in
the `1f1c0677` worktree) — result:
```
FAILED test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
FAILED test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
3 failed, 254 passed in 1.81s
```
254/3 hand count above equals pytest's own "254 passed"/"3 failed" summary
line (derived: same command output pasted above). Re-ran the same 3 failing
node IDs against `origin/main` at sha `8d100d66` (separate worktree, `git
worktree add /tmp/main-review origin/main`, since removed) —

acceptance: `python3 -m pytest test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline -q` (run this turn, in the `8d100d66` worktree) — result:
```
FAILED test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
FAILED test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
3 failed in 1.09s
```
Identical 3 node IDs fail on `main` — pre-existing, not introduced by this
stage's diff (canonical: the two pytest runs above, this turn).

acceptance: `gh pr list --state open --json number,headRefName,title,url`
(run this turn, live) — result:
```json
[{"headRefName":"issue-2431/conformance-review","number":2437,"title":"issue-2431: builder-blind conformance review of PR #2434","url":"https://github.com/tokenmaxxxer/on-the-record/pull/2437"},{"headRefName":"issue-2432/implementation","number":2436,"title":"issue-2432: branch/record naming to skill axis + lease disambiguator (dual-scheme, stage 4)","url":"https://github.com/tokenmaxxxer/on-the-record/pull/2436"},{"headRefName":"issue-2431/implementation","number":2434,"title":"issue-2431: drop the calendar bound for confirmed-dead-pid spawn-attempt orphans","url":"https://github.com/tokenmaxxxer/on-the-record/pull/2434"},{"headRefName":"issue-2409/conformance-review","number":2420,"title":"issue-2409: conformance-review phase-1 (survey + proposal)","url":"https://github.com/tokenmaxxxer/on-the-record/pull/2420"},{"headRefName":"issue-2409/execution-observation","number":2419,"title":"issue-2409: execution-observation phase-1 (survey + proposal)","url":"https://github.com/tokenmaxxxer/on-the-record/pull/2419"},{"headRefName":"issue-2409/implementation","number":2416,"title":"issue-2409: attack exploratory-Bash, hook-refusal, and redundant-read waste","url":"https://github.com/tokenmaxxxer/on-the-record/pull/2416"}]
```
6 open PRs now vs. the PR's own 5-open-PR snapshot taken just before PR
#2436 was opened (canonical: PR #2436 body, `gh pr view 2436 --json body`,
read this turn). Diffed the two lists by branch name (derived: comparing
the JSON above against PR #2436's pasted 5-entry list): 4 of the 5
original entries are still present, byte-identical
(`issue-2431/implementation`, `issue-2409/conformance-review`,
`issue-2409/execution-observation`, `issue-2409/implementation`). The 5th,
`issue-2414/conformance-review` (#2435), is absent from the live list —

acceptance: `gh pr view 2435 --json state,mergedAt,closedAt,headRefName`
(run this turn, live) — result:
```json
{"closedAt":"2026-08-25T13:38:49Z","headRefName":"issue-2414/conformance-review","mergedAt":null,"state":"CLOSED"}
```
`headRefName` unchanged, `mergedAt: null` — this PR was closed (not
merged, not renamed, not re-pointed) as its own independent lifecycle
event, unrelated to PR #2436's diff (derived: PR #2436's diff, read this
turn via `git diff main...issue-2432/implementation --stat` in the
`1f1c0677` worktree, touches only `board.py`, `pipeline.py`, `roster.py`,
`spawn.py`, `1f1c0677:test/test_branch_naming_dual_scheme.py`,
`1f1c0677:docs/handbooks/branch-naming.md`, and `1f1c0677:docs/issue-2432/`
— no `gh pr`/`git push`/`git branch` invocation against #2435 or its
branch appears in that diff). The 2 new arrivals (#2437, and #2436 itself,
now open) are new PRs opened after the snapshot, not renames of
pre-existing ones. Net: no PR that was open at the PR's own snapshot time
had its branch name or content changed by this stage's diff.

Read PR #2436's diff directly rather than trusting its record's
characterization of "additive-only" (derived: `git diff
main...issue-2432/implementation -- board.py pipeline.py roster.py`, this
turn, in the `1f1c0677` worktree):
- `board._skill_axis_report_names()` is a new function; the existing `for
  r in _sp.ROLES` loop inside `board()` is untouched — the new function's
  results are merged into the same `roles` dict *after* that loop runs,
  not instead of it.
- `board.status()` gained a second, parallel `for r in sorted(r for r in
  roles if r not in _sp.ROLES)` block emitting the same `[role] loop_state:
  ... verdict: ...` line shape for skill-axis records.
- `pipeline.checkout_issue_branch()` now delegates to a new
  `_checkout_named_branch(cwd, br)`, with `br = f"issue-{issue}/{role}"`
  construction moved to the (unchanged-signature) caller — verified
  byte-identical via the `test_old_scheme_branch_shape_byte_identical`
  node, which is one of the 9 that passed above (canonical: the
  `1f1c0677:test/test_branch_naming_dual_scheme.py -v` result block
  above, this turn).
- `roster.new_lease_disambiguator()` is a new, standalone function
  (`secrets.token_hex(4)`); no existing `roster.py` function body was
  edited by this diff.

Checked the disclosed deviation named in PR #2436's description: sha
`1f1c0677:docs/handbooks/branch-naming.md:55` still points readers to the
proposal's originally-frozen path — bare form
`docs/issue-2241/reports/architecture/in-flight-branch-migration.md`,
untracked, does not exist at that sha or on any branch checked this turn
(canonical: `git show
1f1c0677:docs/issue-2241/reports/architecture/in-flight-branch-migration.md`,
this turn, fails with "path does not exist") — while the actual content
instead landed at
`1f1c0677:docs/issue-2432/reports/implementation/in-flight-branch-migration.md`.
This is disclosed twice by the implementation session: in that file's own
"Path note (deviation...)" opening section, and in a `gh issue comment` on
#2432 naming two unblock paths (canonical: `gh issue view 2432
--json comments`, read this turn — second comment, authored
`JiwonJung94`, body opens "stage-4 build (this session, branch
issue-2432/implementation): the acceptance gate's second deliverable is a
doc at the parent program issue's own architecture-reports tree...").

## Why

PR #2436's own record already asserts all three of issue #2432's
acceptance checks were satisfied. Re-derived each check from scratch in an
isolated worktree instead of citing the PR's pasted output as sufficient —
ran the dual-scheme test file myself, ran the full non-slow suite and
diffed the 3 pre-existing failures against a fresh `main` checkout myself,
ran the open-PR live check myself at a *later* wall-clock time than the
PR's own check (so the before/after comparison is against real drift, not
a replay of the same numbers), and read the `board.py`/`pipeline.py`/
`roster.py` diffs directly rather than trusting the implementation
record's "additive-only" characterization of them.

## Upstream basis

- `1f1c0677:docs/issue-2432/reports/implementation.md` — the
  implementation record whose claims this session re-derived independently
  rather than cited.
- `1f1c0677:docs/issue-2432/reports/implementation/in-flight-branch-migration.md`
  — the gate deliverable, cross-checked against this session's own
  independently-run `gh pr list --state open`.
- PR #2436 (`origin/issue-2432/implementation`, sha `1f1c0677`) diff
  itself, read directly this turn for `board.py`, `pipeline.py`,
  `roster.py`.

## Open findings

- `1f1c0677:docs/handbooks/branch-naming.md:55` references the bare-form
  path `docs/issue-2241/reports/architecture/in-flight-branch-migration.md`,
  untracked, which does not exist at that sha (canonical: `git show
  1f1c0677:docs/issue-2241/reports/architecture/in-flight-branch-migration.md`,
  this turn, fails). This is a disclosed, pre-existing deviation (not
  introduced by this observation), already named with two unblock paths
  in the implementation session's `gh issue comment` on #2432. Resolution
  path: either a session on `issue-2241/implementation` performs the move,
  or a human adds a `maintenance-targets: issue-2241` line to issue
  #2432's body so a session on `issue-2432/implementation` can clear
  `board-gate.sh`'s R4 exception and write the frozen path directly — both
  already named upstream; no new action assigned by this record.
- None of the issue's three acceptance checks failed independent
  re-verification — no other open findings.

## What did not work

Nothing in the independent re-verification itself — every re-run check
matched PR #2436's claims. Two earlier drafts of this file were rejected
by the record-claim-guard hook: once for bare (non-sha-pinned) references
to paths that live only on `issue-2432/implementation`, and once for an
OUTCOME claim (`loop_state: done`) lacking a same-section
`canonical:`/`derived:` tag. Both are fixed above/below by pinning every
off-branch path to its sha and by attaching an executed-evidence tag or
adjacent code fence to every OUTCOME/count claim.

## Next steps

None — all three acceptance checks in issue #2432's body were
independently re-run this turn and matched PR #2436's claims.

acceptance: summary of the three independently-executed checks in "What
was done" above — result:
```
dual-scheme tests: 9 passed (this turn)
full suite: 254 passed, 3 failed (pre-existing on main, confirmed this turn)
live open-PR check: 6 open, 0 unaccounted branch/content changes (this turn)
```
loop_state: done.
