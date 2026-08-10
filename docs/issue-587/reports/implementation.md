---
code_under_review:
  - on-the-record/hooks/delegated-judgment-gate.sh
  - spawn.py
  - test_spawn.py
type: feature
breaking: false
verdict: pending
loop_state: landed
---

# Issue #587 — implementation record (phase 2, remediation round: timeline event 4)

## What was done

Wired issue-timeline event 4 ("Remediation PR merged", `#573` §12) per the approved
remediation-round proposal:

1. `on-the-record/hooks/delegated-judgment-gate.sh`: added `candidate_pr: {pr_ref}` to the
   `remediation-<seq>.md` frontmatter the reject-path already writes (`pr_ref` was already an
   in-scope local variable) — field addition only, no new write path.
2. `spawn.py`: added `_merged_pr_for_branch(root, branch) -> int | None` (MERGED-state-only
   sibling to `_pr_open_or_merged_for_branch`) and `_remediation_merge_sweep(root, issue) -> int`
   (same shape as `_roster_reconcile_unreported`): for each `docs/issue-<n>/decisions/remediation-*.md`
   with `status: open`, resolves `routed_to`'s branch (`issue-<n>/<role>`), checks
   `_merged_pr_for_branch`, and on a merge posts the §12 event-4 line
   (`Remediation merged: PR #<m> resolves round <r> of PR #<n>` + PR link) via `gh issue comment`,
   guarded by a fixed marker read back through `_issue_comments` (idempotent — matches
   `_post_session_end_comment`'s read-then-check pattern).
3. `test_spawn.py`: new `RemediationMergeSweep` class — posts exactly one comment matching the
   §12 format verbatim on a fixture merge; a second sweep with the marker present posts nothing;
   a record whose branch is not (yet) merged posts nothing; `status: escalated`/`resolved` records
   are skipped without a PR lookup at all. Test count is in the confirmation run below.

Per the approved proposal (`docs/issue-587/proposals/implementation-remediation-merged-event.md`,
PR #601, `APPROVE issue-587/implementation`).

## Why

Remediation round (operator-relayed 2026-08-10, e2e verdict FAILED on PR #599's record):
`docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md`'s per-event table row 4
confirmed — by source grep and by an empirical fixture-repo merge — that no shipped code posted
the event-4 comment on a remediation PR's merge. This round closes that gap with the posting
mechanism plus its test, per the operator's remediation-round scope.

## Upstream

docs/issue-587/proposals/implementation-remediation-merged-event.md

## Confirmation run

```
$ python3 -m pytest test_spawn.py -q -k RemediationMergeSweep
....                                                                     [100%]
4 passed in 0.14s
$ python3 -m pytest test_spawn.py -q
355 passed in 24.56s
$ python3 -m pytest gates/test_remediation_spawn.py -q
......                                                                   [100%]
6 passed in 0.03s
$ python3 -m pytest on-the-record/hooks/test_delegated_judgment_gate.py -q
............                                                            [100%]
12 passed in 1.35s
$ python3 -m pytest . -q
929 passed, 2 failed in 43.17s
```

The 2 failures are both pre-existing and unrelated to this round's write set — reproduced via
`git stash` before making any change (`gates/test_boundary.py`, one failure; `test_gates.py`, the
`t_rulebook_version_is_recorded` case) — see `## What did not work` for the reproduction detail.

Manual fixture check (proposal's "how you'll know it worked" step 2, disposable temp-dir pattern
matching the step-3 execution-observation record): a script under this session's scratchpad built
a temp-dir fixture record (`status: open`, `routed_to: implementation`, `round: 1`,
`candidate_pr: 601`, at a path shaped like `docs/issue-<n>/decisions/remediation-1.md` but rooted
under a temp dir, not this repository) with `gh` calls mocked (`_merged_pr_for_branch` returning a
merged PR 605), and called `_remediation_merge_sweep` directly:

```
posted: 1
gh_call_count: 1
BODY: body=[watch] remediation-merged: docs/issue-9999/decisions/remediation-1.md

Remediation merged: PR #605 resolves round 1 of PR #601
https://github.com/acme/repo/pull/605
second_sweep_posted (marker present, expect 0): 0
```

Confirms the event-4 comment posts in §12's exact format on a fixture merge and does not
re-post on a second sweep.

## What did not work

- `python3 -m pytest . -q` on the unmodified pre-change tree (`git stash`) already showed
  `gates/test_boundary.py`'s `t_all_gates_modules_recorded` failing — `remediation_spawn.py` (a
  prior round's file, outside this round's write set) is missing a verdict row in
  `docs/specs/enforcement-boundary.md`. Confirmed pre-existing, not introduced by this round; left
  as-is since that file is outside this round's frozen write set.
- The full-suite run on the changed tree additionally failed `test_gates.py`'s
  `t_rulebook_version_is_recorded`, which asserts the working tree is clean
  (`rulebook_version()` embeds a dirty-tree marker otherwise) — expected on an uncommitted tree,
  not a defect; resolves once this round's changes are committed.

## Rationale for deviations

None — the implementation follows the approved proposal's `## What will be done` exactly.

## Doc placement

- No new env var, config key, dependency, or migration — nothing added to a handbook.
- No library-or-format choice over a named alternative beyond what the proposal's `## Rationale`
  already decided (reuse `spawn.py`'s existing merge-detection/idempotent-comment surface, reject
  a new merge-watcher script, reject wiring detection into the gate itself) — no new `decisions/`
  entry.
- No benchmark/investigation numbers — no `reports/` entry.

## Open findings

None.

## Closed checks

None — no warrant-hunter dispatch completed within this turn (headless single-shot session;
contract v3 s22 takes priority over the warrant directive's dispatch-and-continue instruction when
a result cannot be consumed before the turn ends).

## Next steps

None from this round's scope. `_remediation_merge_sweep` is exposed as a function but not wired
into a periodic caller (a cron-like invocation, a `watch`/`reconcile` CLI subcommand, or the
orchestrator's `run.md` loop) — out of scope per the approved proposal, a `run.md`-contract
decision for a future round.
