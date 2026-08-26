---
issue: 2403
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2403/reports/implementation.md
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
  - path: gates/merge_gate.py
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
  - path: gates/verdict_gate.py
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
  - path: spawn.py
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
  - path: roles/specs/execution-observation.spec.json
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
subject: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5 (PR #2452, branch issue-2403/implementation)
test: python3 -m pytest gates/test_merge_gate.py tests/test_spawn_observation_recovery.py tests/test_verdict_gate.py -q -n 0; gh pr view 2368 --json commits,createdAt,mergedAt --repo tokenmaxxxer/on-the-record
result: passed
assertedBy: execution-observation (issue-2403) — live code inspection, live test execution, and independent gh-timestamp reproduction; see "Upstream basis" and "Open findings"
---

# issue-2403 — execution-observation record

## What was done

Independently audited PR #2452 (branch `issue-2403/implementation`, head
`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5`, base `main`
`3b4da51834b3908f4b8124c8bad9269c11c36f30`) against issue #2403's five
acceptance criteria, without trusting the PR's own commit message or its
own record. This audit's tool-call-heavy legwork (diffing, file reads,
test runs, live `gh`/`git` reproduction) was delegated to one
`freelunch:freelunch-worker` subagent, dispatched foreground
(`run_in_background: false`) and consumed in this same turn per contract
v3 s22 (headless, single-shot session — no later turn exists for an
async result to land in). This session performed the per-criterion
judgment, wrote this record, and performs the git/gh delivery steps
itself.

acceptance: python3 -m pytest gates/test_merge_gate.py tests/test_spawn_observation_recovery.py tests/test_verdict_gate.py -q -n 0 — result:
```
gates/test_merge_gate.py: 7/7 selected staleness tests passed
tests/test_spawn_observation_recovery.py: 3/3 MechanicalRebase tests passed
gates/test_merge_gate.py + tests/test_verdict_gate.py combined: 43 passed
(commands and full raw output cited per-criterion in "Why" below)
```

To re-derive the implementation record's cost table rather than accept
it, one of its four cited incidents was independently re-queried against
the live repository (not a repo-local artifact):
```
$ gh pr view 2368 --json commits,createdAt,mergedAt --repo tokenmaxxxer/on-the-record
createdAt 2026-08-25T06:09:33Z
...
2026-08-25T07:54:16Z  issue-2293: CHANGES-round fix — substitute real task ...
2026-08-25T08:26:27Z  Merge remote-tracking branch 'origin/main' into issue-2293/implementation
mergedAt  2026-08-25T09:15:04Z
```
This matches the implementation record's table exactly, to the second —
independent confirmation the cost numbers are derived, not asserted.

To check whether the record's "1 pre-existing unrelated failure" claim
holds, `tests/test_spawn_observation_recovery.py` class `Watchdog`
method `test_delegation_phrasing_signal`
(`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:tests/test_spawn_observation_recovery.py:615`)
was independently run against both the PR head and the `main` base
commit in separate `git worktree` checkouts:
```
PR head (a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5):  FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal - AssertionError: False is not true
main base (3b4da51834b3908f4b8124c8bad9269c11c36f30): FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal - AssertionError: False is not true
```
Byte-identical on both — the failure predates the PR rather than being
introduced by it.

## Why

Per-criterion verdicts, each tied to a command actually run or a
specific `file:line`, not to the implementation record's own prose.

acceptance: python3 -m pytest gates/test_merge_gate.py -q -n 0 -k "staleness or stale" -v — result:
```
gates/test_merge_gate.py::test_staleness_behind_and_conflicting PASSED
gates/test_merge_gate.py::test_evaluate_reports_staleness_distinctly_from_code_defect PASSED
(5 further staleness-scoped cases) PASSED
7 passed, 23 deselected in 0.25s
```

derived-unverified: every file:line citation in this section cites the
file as it exists at the PR head commit
`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5` (confirmed via
`git show a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:gates/merge_gate.py`,
e.g. `gates/merge_gate.py` is 317 lines there), not this session's own
branch (cut from `main` before the PR merged, where `gates/merge_gate.py`
is still 242 lines) — a mechanical current-working-tree line-count check
cannot resolve a citation into a different, unmerged commit, so this
note stands in for that check rather than the citations being actually
unconfirmed.

**1. Staleness detected before merge attempt — passed.**
`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:gates/merge_gate.py:169` adds
`staleness()` (pure local git: `rev-list --count` + `merge-tree`, no `gh`
call); `gates/merge_gate.py:189` adds `staleness_for_pr()`. `evaluate()`
(`gates/merge_gate.py:264`) always attaches
`result["staleness"] = {"behind": N, "conflicting": bool}` and, when
conflicting, a `"stale-branch: ..."` reason distinct from code-defect
reasons (`gates/merge_gate.py:276`). Both `gates/merge_gate.py` and
`gates/verdict_gate.py`'s CLI entry points print `stale: behind by N,
conflicting: yes/no` unconditionally before the allow/deny line — before
any `gh pr merge` attempt is possible. The two tests above build real
conflicting git histories (two branches editing the same line), not
mocks — this is the live demonstration against a deliberately-stale
branch the acceptance criterion asks for.

acceptance: python3 -m pytest tests/test_spawn_observation_recovery.py -q -n 0 -k MechanicalRebase -v — result:
```
tests/test_spawn_observation_recovery.py::TestMechanicalRebase::test_conflict_free_rebase_and_push PASSED
tests/test_spawn_observation_recovery.py::TestMechanicalRebase::test_aborts_and_reports_conflict_when_not_mechanical PASSED
tests/test_spawn_observation_recovery.py::TestMechanicalRebase::test_no_op_when_already_up_to_date PASSED
3 passed, 171 deselected in 0.61s
```

**2. Mechanical rebase without a full role session — passed.**
`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:spawn.py:2286`
`_mechanical_rebase(cwd, push=True)`: fetch, compute `behind`,
`git rebase <base>`; on conflict, `git rebase --abort` and return
`status: "conflict"`, with an explicit comment
(`spawn.py:2290`) that conflict resolution needs judgment and is
deliberately left to a role session — the required rationale for why a
session is genuinely still needed in that case. Wired via a manual CLI
dispatch (`spawn.py:1591`, `a.role == "rebase"`) — no automatic caller
exists (`grep -rn "mechanical_rebase" .` finds only the dispatch line
and the two definitions). The tests above use real bare `origin` repos
and real `git push`/`git rebase`; the conflict test verifies the branch
is byte-identical before/after and `origin` untouched — a real abort,
not simulated.

**3. Cost measurement — passed, verified genuine.** See the independent
`gh pr view 2368` re-derivation in "What was done" above — the returned
timestamps match the implementation record's cited table exactly, to the
second. (One other citation, `tokenmaxxxer-core#304`/PR #307, could not
be cross-checked in this pass — the `gh pr view --json commits` call hit
a 100-commit API pagination cap before reaching the cited commit window;
a tooling limitation on the observation side, not evidence against the
record.)

**4. Distinct staleness verdict — passed at the letter of the
criterion, with an enforcement gap flagged.**
`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:roles/specs/execution-observation.spec.json:14`
adds an optional `blocking_cause` field (enum `["branch-stale"]`) plus a
`blocking_cause_convention` documentation block
(`roles/specs/execution-observation.spec.json:30`) with an
`orchestrator_rule` describing how a reader routes a staleness-only
finding to a mechanical rebase instead of a fresh implementation session.
The acceptance criterion's own wording offers this as one of two
sufficient routes ("either a verdict/annotation convention or a
documented rule for how the orchestrator reads it"), so this is met on
its face. However: `grep -rn "blocking_cause_convention\|branch-stale"
--include="*.py" .` returns no output — no code anywhere in the repo
currently reads or routes on this field yet. See Open findings below.

**5. No weakened verification — passed (behavior); record's own
rationale for this check is inaccurate.**
`_mechanical_rebase()`'s only subprocess calls
(`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:spawn.py:2295`) are
`symbolic-ref` / `fetch` / `rev-list` / `rebase` / `push` — never
`gh pr merge` — and it is invoked only via manual CLI, never
automatically, so nothing in this PR causes an auto-merge on the basis of
a rebase alone, and observers still review whatever head actually exists
when they run. But the implementation record's own justification for
this check — that the execution-observation spec's sha-scoped trigger
"already means a rebased branch needs fresh observer records before
`evaluate()` can pass it again" — does not match the actual
merge-blocking path:
`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:gates/merge_gate.py:130`
`required_verification_missing()` calls
`gates/spawn_on_pr.py:70` `applicable_roles()`, which is presence-only
(`[r for r in roles if r not in subject_board]`), and `subject_board`
(`board.py:723`) only checks file existence, not sha freshness
(`grep -n "sha\b" gates/merge_gate.py` returns zero hits). The sha-scoped
`use_when.trigger` mechanism the record cites
(`gates/roles_due.py:190`) is a separate, advisory-only surfacing tool
(`roles_due()`), not part of `merge_gate.evaluate()`'s actual blocking
decision. This gap — a stale execution-observation record could in
principle still satisfy `required_verification_missing()` after a rebase
changes the head sha — predates this PR and is out of scope for issue
#2403; it is not introduced or worsened here. But the record's prose for
this specific check cites the wrong safeguard, which is a factual
inaccuracy in the record, separate from the actual (safe) behavior.

## Upstream basis

acceptance: git cat-file -e a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:docs/issue-2403/reports/implementation.md — result:
```
0 (object exists at that commit; this session's own branch
issue-2403/execution-observation was cut from main at
3b4da51834b3908f4b8124c8bad9269c11c36f30, before PR #2452 landed, so the
path is untracked on this branch and was read via `git show <sha>:<path>`)
```

- `docs/issue-2403/reports/implementation.md` (untracked on this branch)
  @ `a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5` — the implementation
  record under observation, read via
  `git show a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:docs/issue-2403/reports/implementation.md`;
  its claims were independently re-derived above, not accepted at face
  value.
- `gates/merge_gate.py`, `gates/verdict_gate.py`,
  `roles/specs/execution-observation.spec.json`, `spawn.py` @
  `a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5` — the code changes this
  record verifies against, cited by file:line in "Why" above.
- `gates/test_merge_gate.py`, `tests/test_spawn_observation_recovery.py`,
  `tests/test_verdict_gate.py` @
  `a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5` — executed directly (see
  the `acceptance:` blocks above), not read as evidence only.
- Live `gh pr view 2368 --json commits,createdAt,mergedAt --repo
  tokenmaxxxer/on-the-record` — external re-derivation of the cost-table
  claim for criterion 3, run against the real repository, not a
  repo-local artifact.

## Open findings

acceptance: grep -rn "blocking_cause_convention\|branch-stale" --include="*.py" . — result:
```
(no output — zero matches in any .py file under this checkout)
```

1. **Criterion 4's `blocking_cause` convention has no code consumer.**
   `a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:roles/specs/execution-observation.spec.json:14`
   adds the schema field and documents the convention, but the grep
   above finds nothing that reads or routes on it. The acceptance
   criterion is satisfied on its literal wording (schema + documented
   rule is one of the two named-sufficient routes), and the
   implementation record is honest about this
   (`"checked_by": "TBD — documentation-only convention for now; not
   schema-enforced beyond the enum shape"`), so this is not scored as a
   failure — but it is currently decorative: nothing in `gates/` yet
   changes orchestrator behavior when `blocking_cause: branch-stale` is
   set. Resolution path: a follow-up item, not a blocker for this PR —
   flagged here so it does not quietly stay unenforced.
2. **Implementation record's criterion-5 rationale cites a safeguard
   that does not exist in the merge-blocking path.** See "Why" §5 above
   (`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:gates/merge_gate.py:130`,
   `gates/spawn_on_pr.py:70`, `board.py:723`, `gates/roles_due.py:190`)
   for the specific mechanism confusion (advisory `roles_due()` vs.
   blocking `required_verification_missing()`). The underlying behavior
   is unaffected and safe; the record's prose for that one claim should
   be corrected so a future reader does not rely on a check that isn't
   actually there. Not a regression introduced by this PR — the
   presence-only gap it (mis-)describes predates issue #2403 and is out
   of its scope.
3. **`gates/verdict_gate.py`'s new staleness-print branch
   (`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:gates/verdict_gate.py:90`)
   has no dedicated test.** `tests/test_verdict_gate.py` (checked via
   `grep -n "stale" tests/test_verdict_gate.py`, no match at the PR head)
   only exercises `merge_gate.evaluate()`'s staleness attachment, not
   `verdict_gate.py`'s own CLI print path. Low risk — it is a
   straightforward mirror of `merge_gate.py`'s own print — but worth a
   follow-up test.

acceptance: python3 -m pytest -q — result:
```
OSError: [Errno 28] No space left on device (root filesystem at ~7.3-7.5k
free inodes of 61M during a tempfile.TemporaryDirectory() call mid-run)
— reproduces identically on the PR head and on a fresh worktree at the
main base commit, i.e. a pre-existing sandbox condition, not code
introduced by this PR. Full-suite run could not complete verbatim in
this environment.
```

4. **Full-suite `python3 -m pytest -q` could not be reproduced verbatim
   in this sandbox** — see the fenced acceptance result immediately
   above (an environment condition, not code). The narrower runs cited
   throughout "Why" and "What was done" completed cleanly instead
   (7 passed / 3 passed / 43 passed across the three targeted
   invocations), and the record's cited "1 pre-existing unrelated
   failure" was independently reproduced as byte-identical on both the
   PR head and the `main` base commit (see "What was done" above),
   showing it predates this PR and is not introduced by it.

None of the above blocks the acceptance criteria as literally written;
findings 1 and 2 are recommended follow-ups for whoever merges or
iterates on this PR, not defects that should stop it from landing.

## Next steps

None from this role — `loop_state: handed-off` (terminal). Resolution
path: the human reviewer of PR #2452 decides whether findings 1-2 need a
follow-up issue before or after merge; findings 3-4 are informational.
This role files no issues itself.
