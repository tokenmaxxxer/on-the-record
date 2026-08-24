---
issue: 2165
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2165/reports/execution-observation/survey.md
    sha: same-commit
  - path: docs/issue-2165/proposals/execution-observation.md
    sha: same-commit
  - path: gates/spawn_on_pr.py
    sha: 1f9601df63f7c4df4431fe67115071ef1c05890a
subject: gates/spawn_on_pr.py @ 1f9601df63f7c4df4431fe67115071ef1c05890a (PR #2170, merged to main)
test: tests/test_spawn_on_pr.py, tests/test_spawn_on_pr_park.py, tests/test_watchdog_local_signals.py, tests/test_watchdog_freshness.py — all four re-run at commit 1f9601df63f7c4df4431fe67115071ef1c05890a
result: passed
assertedBy: issue-2165/execution-observation session, independently re-executed 2026-08-24 in a read-only git worktree (never committed to this branch)
---

# issue-2165 — execution-observation record

## Independence statement

canonical: `gh pr view 2170 --json state,mergedAt,mergeCommit`, executed
live this session — result: `state: MERGED`, `mergedAt:
2026-08-24T09:49:12Z`, `mergeCommit: 1f9601df63f7c4df4431fe67115071ef1c05890a`.

This role did not author or edit the observed artifact this session. All
verdicts below judge PR #2170 (`gates/spawn_on_pr.py`) at that merge commit,
read and independently re-executed this session in a read-only worktree
outside this branch's own tree. No `gates/`, `tests/`, or the
implementation role's own `docs/issue-2165/` paths were staged to this
branch.

## What was done

Per the approved proposal (`docs/issue-2165/proposals/execution-observation.md`),
independently re-executed the commands issue #2165's own Acceptance clause
names, rather than only reading the phase-2 record's own pasted transcript.

canonical: `git worktree add /tmp/wt-2165-obs 1f9601df63f7c4df4431fe67115071ef1c05890a`,
executed live this session — a read-only worktree checked out at PR #2170's
merge commit on `main`, removed from this branch's own tree, never
committed here.

canonical: `python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q`,
executed live this session inside that worktree — the exact command issue
#2165's own Acceptance clause names. result:

```
21 passed in tests/test_spawn_on_pr.py
7 passed in tests/test_spawn_on_pr_park.py
............................                                             [100%]
28 passed in 20.84s
```

canonical: `python3 -m pytest tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py -q`,
executed live this session inside that worktree — the phase-2 record's
stated neighbor sanity check. result:

```
....................                                                     [100%]
20 passed in 19.38s
```

canonical: `git show 1f9601df63f7c4df4431fe67115071ef1c05890a -- gates/spawn_on_pr.py`,
read live this session — confirms `MERGED_SEEN_STATE_REL`,
`load_merged_seen`/`_save_merged_seen`, and the merged-seen check inserted
into `missing_verification()` between `if not missing: continue` and the
first `gh`-dependent call, matching the implementation record's own
line-range citations.

## Why

Basis: `docs/issue-2165/proposals/execution-observation.md`'s Rationale —
re-running the exact named commands in a worktree this role never wrote to
produces a citation this role can stand behind as its own, rather than a
second-hand quote of the implementing role's own claim about itself
(`roles/specs/execution-observation.spec.json`'s `gate_c_status`: two
independent observers re-running the same test set against the same
commit sha should produce the same worst-case verdict).

canonical: `python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py -q`
— result: 0 failed, 0 skipped across all four files (derived: 28 + 20 = 48
passed total, from the two fenced runs under "What was done" above).
`result: passed` in this record's own frontmatter is that worst case.

## Upstream basis

`docs/issue-2165/reports/execution-observation/survey.md` and
`docs/issue-2165/proposals/execution-observation.md` land in this same
commit.

canonical: `git show 1f9601df63f7c4df4431fe67115071ef1c05890a:docs/issue-2165/reports/implementation.md`,
read live this session — that path exists only at PR #2170's merge commit
on `main`, not on this branch; it is the implementation role's own
phase-2 record (`loop_state: landed`, `verdict: pass`).

canonical: `python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q`
(the same command, re-run under "What was done" above) — the implementation
record cites this identical command with the same 28-passed result.

canonical: `gh pr view 2170 --json state,mergedAt,mergeCommit`, executed
live this session (same result as under "Independence statement" above).
This updates the phase-1 survey's own snapshot, which read PR #2170 as
still open.

## Open findings

1. **Acceptance-clause file-naming gap on `tests/test_spawn_on_pr_park.py`**
   (resolution path: `issue-2165/conformance-review`'s own phase-2
   verdict, PR #2177, open, pending its
   `APPROVE issue-2165/conformance-review` phase-2). Issue #2165's own
   Acceptance clause names both `tests/test_spawn_on_pr.py` and
   `tests/test_spawn_on_pr_park.py`, with the parenthetical "(test
   simulating the #513 shape)".

   canonical: `git show 1f9601df63f7c4df4431fe67115071ef1c05890a --stat`,
   read live this session — result: PR #2170's diff touches
   `gates/spawn_on_pr.py` and `tests/test_spawn_on_pr.py` only;
   `tests/test_spawn_on_pr_park.py` is not in the diff.

   canonical: `git log --oneline -- tests/test_spawn_on_pr_park.py`,
   executed live this session inside the worktree — result: last commit
   touching that file is `8ae79dc6` (issue #1476), predating issue #2165
   entirely; the two new regression tests
   (`test_missing_verification_sticky_merged_cache_survives_flaky_reconfirm`,
   `test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks`)
   land in `tests/test_spawn_on_pr.py` instead.

   canonical: `python3 -m pytest tests/test_spawn_on_pr_park.py -q`,
   executed live this session inside the worktree — result: 7 passed,
   0 failed, 0 skipped, unmodified by PR #2170. This does not change this
   record's own `result`: this role's verdict method is mechanical
   worst-case aggregation over what actually ran, not a judgment on
   requirement wording. `issue-2165/conformance-review`'s own survey
   independently flagged the same gap; its own phase-2 will render the
   Present/Surface/Absent/Incorrect verdict on whether this satisfies the
   clause in substance.

2. **Prior stranded-relay on `issue-2165/implementation`** (resolution
   path: none — already resolved). canonical: `gh issue view 2165
   --comments`, read live this session — an earlier attempt on the
   implementation branch failed PR creation ("No commits between main and
   issue-2165/implementation", a `[on-the-record] stranded-relay` comment).

   canonical: `gh pr view 2170 --json state,mergedAt,mergeCommit`,
   executed live this session (same result as under "Independence
   statement" above) — result: MERGED. A later session on the same branch
   succeeded, producing PR #2170. No action needed from this role.

## Next steps

None — `loop_state: handed-off` is this role's own terminal state per
`roles/specs/execution-observation.spec.json`.
