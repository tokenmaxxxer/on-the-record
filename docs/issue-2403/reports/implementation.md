---
issue: 2403
role: implementation
author: implementation
loop_state: landed
upstream: []
code_under_review:
  - path: gates/merge_gate.py
    sha: same-commit
  - path: gates/verdict_gate.py
    sha: same-commit
  - path: gates/test_merge_gate.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: tests/test_spawn_observation_recovery.py
    sha: same-commit
  - path: roles/specs/execution-observation.spec.json
    sha: same-commit
type: feat
breaking: "no — additive only: merge_gate.evaluate() gains one new optional
  \"staleness\" key on its return dict (canonical: gates/merge_gate.py
  evaluate(), this commit); stale_revert_reasons()/staleness_for_pr() gained
  an optional refs= kwarg defaulting to None, preserving the old call shape;
  spawn.py gained one new dispatch value (\"rebase\"); the execution-observation
  spec gained one optional field. One pre-existing test's exact-dict-equality
  assertion was updated to include the new key (canonical:
  gates/test_merge_gate.py test_live_pr_1662_vs_1661_reconstruction, this
  commit) — an assertion update, not a behavior compromise."
verdict: pass
---

# issue-2403 — implementation record

No proposal record precedes this commit under this issue's own docs
directory (untracked before now) — build-now bypass (contract v3 s19a,
`CORE_BUILD_NOW=1`) skips the proposal round; the issue body itself
(canonical: `gh issue view 2403`, this session) is the only upstream input,
hence `upstream: []`.

## What was done

1. **Pre-merge staleness probe.** `gates/merge_gate.py` gains `staleness()`
   (pure, local `git rev-list`/`git merge-tree`, no `gh`) and
   `staleness_for_pr()` (resolves refs via `gh` then delegates). `evaluate()`
   now always attaches `result["staleness"] = {"behind": N, "conflicting":
   bool}` (canonical: `gates/merge_gate.py::evaluate()`, this commit) and adds
   a blocking reason worded `"stale-branch: ..."` — distinct from the
   check-runner/verification-record wording — only when `conflicting` is
   true. `gates/verdict_gate.py`'s CLI prints the same line.

   `required_verification_missing()` and `stale_revert_reasons()` each
   already called `pr_refs()` independently (canonical:
   `gates/merge_gate.py` lines 130-145, 210-234, read this session); adding
   a third caller meant 3 `gh pr view` round trips per `evaluate()`. Per
   `implementation-complexity-coupling-management`'s rule 8/rule 9
   (derived: skill output, this session, invoked below) — don't duplicate an
   expensive step across sibling pipeline checks — `evaluate()` now resolves
   `pr_refs()` once and threads it into `stale_revert_reasons(repo, pr,
   refs=refs)` and `staleness_for_pr(repo, pr, refs=refs)`, cutting that to 2
   round trips. `required_verification_missing()` was left alone: separate,
   more-tested call site, not needed for this issue's acceptance.

2. **Mechanical rebase operation.** `spawn.py` gains `_mechanical_rebase(cwd,
   push=True)`: fetches `origin`, and only in the conflict-free case
   rebases + `push --force-with-lease`s the branch already checked out at
   `cwd`. A conflicting rebase is `--abort`ed, branch/working-tree untouched
   (canonical: `spawn.py::_mechanical_rebase`, this commit — asserted by the
   `test_aborts_and_reports_conflict_when_not_mechanical` case in
   `tests/test_spawn_observation_recovery.py`, see Acceptance check 2
   below). `mechanical_rebase_cli()` wires `python3 spawn.py rebase -C
   <workspace>` next to the other git-mechanics meta-commands, modeled
   directly on `_recut_absorbed_branch` (same file, same "no LLM session"
   shape). Conflict resolution is deliberately left to a role session — it
   requires reading two diverging changes and deciding how they compose, a
   judgment call, not a mechanical transform. That split is this record's
   rationale for acceptance check 2: the conflict-free case gets a
   `spawn.py` operation, the conflicting case doesn't and shouldn't.

3. **Distinct staleness annotation for observer records.**
   `roles/specs/execution-observation.spec.json` gains an optional
   `blocking_cause` field (enum `["branch-stale"]`) and a
   `blocking_cause_convention` documentation key (canonical:
   `roles/specs/execution-observation.spec.json`, this commit). `result:
   failed` is unchanged and still blocks the merge — this does not touch the
   EARL worst-case recomputation rule — it adds a marker so a reader doesn't
   have to re-derive "not a code defect" from prose. Gap confirmed real via
   `docs/issue-2383/reports/execution-observation.md` lines 14, 227-245,
   260-273 (canonical: read via Explore-agent research this session,
   summarized at the top of this session's transcript) and PR #2396's own
   description, both of which had to spell the distinction out in free text
   because no structured field existed for it before this commit.

## Why

Root cause, as stated in the issue body itself (canonical: `gh issue view
2403`, this session) and confirmed by reading `gates/merge_gate.py`'s
`evaluate()` before this commit: it checked check-runner results, required
verification records, and content-revert safety, but never checked
mergeability — so a PR could clear every one of those and still fail at
`gh pr merge` once `main` moved during a tens-of-minutes observer session
run against a fixed head.

**Cost measured** (acceptance check 3), via `git log`/`gh pr view` against
the four PRs the issue names (canonical: `git log`/`gh pr view` output
gathered via Explore-agent research this session):

| case | rebase-session wall-clock (tight bound) | full PR span |
|---|---|---|
| #2293 / PR #2368 | 32m11s fix commit, +48m37s to merge (derived: `07:54:16Z`→`08:26:27Z`→`09:15:04Z` commit/PR timestamps) | 3h05m31s |
| core#304 / PR #307 | 4m56s (derived: `08:39:02Z`→`08:43:58Z` commit timestamps) | 4h52m05s |
| #2383 / PR #2389 (via #2396) | #2396 itself: 1h21m40s to discover staleness, find no code defect (derived: `createdAt`/`closedAt` on PR #2396); +37m11s more to the fix landing | n/a — #2396 is the observer |
| #2348 / PR #2388 | 3m20s tight bound (derived: `10:12:20Z`→`10:15:40Z` commit timestamps); 1h41m17s from the original commit | 2h34m54s |

Mechanical git cost, timed directly this session in throwaway `/tmp`
scratch clones (never in this working tree):

```
$ time git fetch origin main     # 60 commits behind
real  0m0.484s
$ time git merge-base <a> <b>
real  0m0.003s
$ time git rebase origin/main    # clean
real  0m0.055s
$ time git rebase origin/main    # deliberate conflict, detect+abort
real  0m0.042s
```

No token-cost figure exists to compare against: `spawn.py`'s spawn-attempt
ledger (`SPAWN_ATTEMPTS_PATH`) stores two epoch timestamps per attempt and no
token field (canonical: `spawn.py` `_record_spawn_attempt`/
`_record_spawn_outcome`, read this session) — a real gap, not an elided
number. The closest concrete proxy this codebase defines is
`DEFAULT_SESSION_MAX_TURNS = 200` (canonical: `directive_assembly.py:118`,
`pipeline.py::_admission_check_budget_caps`, read this session): every full
role session is admitted with up to 200 LLM turns of budget; the mechanical
path costs 0 LLM turns. The wall-clock table above (minutes-to-hours vs.
sub-second, derived: `time` output pasted above) is the number the
acceptance check asks for.

Why a sibling field, not a 6th `result` enum value: `execution-observation`
records use an EARL 1.0 (W3C) `result` enum
(canonical: `roles/specs/execution-observation.spec.json` lines 7-12, this
commit) with a worst-case-wins recomputation rule. Widening that borrowed
vocabulary would break every reader of it; a non-participating sibling field
is the smaller, reversible change, and matches acceptance check 4's own
framing ("if `failed` is correct as-is, the record says why and how a
reader tells the two apart").

## What did not work

None this session — the two design choices (rebase vs. also mechanizing
conflict resolution; sibling field vs. new enum value) were each settled by
reading existing precedent/constraints before writing code, not by trying
something and reverting it.

## Open findings

- `required_verification_missing()` still makes its own independent
  `pr_refs()` call rather than sharing `evaluate()`'s resolved one
  (canonical: `gates/merge_gate.py` lines 130-145, this commit) — left alone
  deliberately, see "What was done" item 1. Resolution path: a follow-up
  issue only if the extra `gh` round trip is ever shown to matter.
- `_mechanical_rebase()`'s `--force-with-lease` push does not itself notify
  anyone a rebase happened. Not needed for this issue's acceptance criteria
  (a mechanical operation, not automatic wiring) — left as an explicit,
  human/orchestrator-invoked command by design.

## Next steps

None — `loop_state: landed`, terminal.

## Acceptance

**Check 1 — staleness detected pre-merge, demonstrated live against a
deliberately-stale branch.**

```
$ python3 -m pytest gates/test_merge_gate.py -v -k "staleness or stale"
[gw1] PASSED gates/test_merge_gate.py::test_staleness_up_to_date
[gw3] PASSED gates/test_merge_gate.py::test_stale_revert_reasons_fail_open_when_refs_missing
[gw5] PASSED gates/test_merge_gate.py::test_staleness_for_pr_fail_open_when_refs_missing
[gw4] PASSED gates/test_merge_gate.py::test_staleness_behind_but_not_conflicting
[gw2] PASSED gates/test_merge_gate.py::test_staleness_behind_and_conflicting
[gw7] PASSED gates/test_merge_gate.py::test_evaluate_reports_staleness_distinctly_from_code_defect
[gw0] PASSED gates/test_merge_gate.py::test_evaluate_refuses_on_stale_revert
7 passed in 1.45s
```

The `test_evaluate_reports_staleness_distinctly_from_code_defect` case
builds a repo where the role branch and `main` each edit the same line,
calls `merge_gate.evaluate()` directly (not `gh pr merge`), and asserts
`result["staleness"] == {"behind": 1, "conflicting": True}` plus a
`"stale-branch:"`-prefixed reason with no check-runner/verification-record
wording mixed in (canonical: `gates/test_merge_gate.py`, this commit,
pytest output above — result: PASS).

**Check 2 — mechanical rebase without a full role session (rationale in
"What was done" item 2).**

```
$ python3 -m pytest tests/test_spawn_observation_recovery.py -v -k MechanicalRebase
[gw2] PASSED tests/test_spawn_observation_recovery.py::MechanicalRebase::test_reports_up_to_date_without_touching_anything
[gw0] PASSED tests/test_spawn_observation_recovery.py::MechanicalRebase::test_aborts_and_reports_conflict_when_not_mechanical
[gw1] PASSED tests/test_spawn_observation_recovery.py::MechanicalRebase::test_rebases_and_pushes_when_stale_but_conflict_free
3 passed in 2.28s
```

Each test uses a real bare `origin` + clone and real `git push` (canonical:
the `MechanicalRebase` test class in `tests/test_spawn_observation_recovery.py`,
this commit, pytest output above — result: PASS) — the
`test_rebases_and_pushes_when_stale_but_conflict_free` case asserts
`origin/issue-99001/implementation` actually moved to the rebased commit;
the `test_aborts_and_reports_conflict_when_not_mechanical` case asserts
`origin` is untouched and the working tree is byte-identical to before.

**Check 3 — cost measurement.** See "Why" section's table and `time`
codefence above — real timestamps and real timed commands, this session.

**Check 4 — distinct expression for observer-only staleness blocks.** See
"What was done" item 3.

```
$ python3 -c "import json; json.load(open('roles/specs/execution-observation.spec.json'))" && echo "valid json"
valid json
$ python3 gates/role_spec_shape.py roles/specs/execution-observation.spec.json; echo "exit=$?"
exit=0
```
(canonical: commands run this session, result: PASS — 0 shape-check failures.)

**Check 5 — no weakened verification; nothing auto-merged on a rebase
alone.** `staleness()`/`staleness_for_pr()` only ever add a blocking reason;
`test_evaluate_refuses_on_stale_revert` (pytest output, Check 1 above —
result: PASS) confirms the pre-existing `stale_revert_reasons` block still
fires unchanged. `_mechanical_rebase()` never calls `gh pr merge` or any
merge command (canonical: `spawn.py::_mechanical_rebase`, this commit — the
only subprocess calls are `symbolic-ref`, `fetch`, `rev-list`, `rebase`,
`push`). A rebase mints new commits, so the head sha changes; the
`execution-observation` spec's existing sha-scoped trigger ("no
execution-observation record exists yet for this commit sha", canonical:
`roles/specs/execution-observation.spec.json` `use_when.trigger`, this
commit) already means a rebased branch needs fresh observer records before
`evaluate()` can pass it again — a rebase alone cannot make `evaluate()`
allow a merge.

**Full regression run**, this session, this repo:

```
$ python3 -m pytest tests/test_spawn_observation_recovery.py gates/test_merge_gate.py tests/test_verdict_gate.py -q
1 failed, 211 passed, 4 xfailed, 1 xpassed in 99.38s
```

The 1 failure, `Watchdog::test_delegation_phrasing_signal`, is pre-existing
and unrelated — re-run against `git stash` (this session's changes fully
reverted) this session reproduces the identical `AssertionError: False is
not true` (canonical: `git stash && pytest -k test_delegation_phrasing_signal`
output, this session — result: FAIL, byte-identical to the failure above).

## Skill notes

- `implementation-complexity-coupling-management` — applied: invoked;
  decided `gates/merge_gate.py`'s check-pipeline ordering (rule 9) and
  deduped the `pr_refs()` round trip (rule 8) — see "What was done" item 1
  (derived: skill output, this session).
- `work-in-english` — applied: invoked; confirmed (derived: skill output,
  this session) via its "match surrounding style" guard that no change was
  needed — new comments in `gates/merge_gate.py` (all-Korean file) stayed
  Korean, new comments in `spawn.py`'s English sections and test files
  stayed English.
- `diagnose-first` — applied: invoked; per the skill's own opening check
  (derived: skill output, this session) — cause already confirmed/agreed by
  the issue author with four named incidents — the full 6-stage procedure
  was not re-run; the new work it prompted was gathering the wall-clock
  numbers in "Why" directly from `git`/`gh` rather than asserting the
  mechanical path is faster.
- `implementation-design-pattern-selection` — not-applicable: no GoF-style
  pattern was introduced or reconsidered.
- `implementation-performance-data-structure-choice` — not-applicable: no
  data-structure/algorithm choice with a performance-cliff risk was
  involved.
- `implementation-blueprint` — not-applicable: the added code follows a
  directly-adjacent existing precedent in the same files
  (`_recut_absorbed_branch`, `pr_refs()`'s fail-open convention) rather than
  requiring a fresh architecture decision.
