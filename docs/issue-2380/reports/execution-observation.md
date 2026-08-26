---
issue: 2380
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2380/reports/implementation.md
    sha: 296cc92acc68ccbeb63fa757720137dbaea86256
subject: issue-2380
test: gates/test_merge_gate.py -q (gates/merge_gate.py _exempt_own_role, required_verification_missing, evaluate)
result: passed
assertedBy: execution-observation
---

# issue-2380 — execution-observation record

## What was done

canonical: `gates/merge_gate.py` / `gates/test_merge_gate.py` /
`gates/spawn_on_pr.py` at `origin/issue-2380/implementation` sha
`296cc92acc68ccbeb63fa757720137dbaea86256`, diffed against `main` this
session (`git diff main origin/issue-2380/implementation --
gates/merge_gate.py gates/test_merge_gate.py`) and read directly, not
taken from the implementation record's own prose.

Independent execution-observation of PR #2444
(`issue-2380/implementation`). The diff changes `_exempt_own_role()`
from dropping only `own_role` out of `missing` to, when `own_role in
spawn_on_pr.PR_TRIGGERED_ROLES`, dropping every role in
`PR_TRIGGERED_ROLES`:

```python
if own_role in spawn_on_pr.PR_TRIGGERED_ROLES:
    return [r for r in missing if r not in spawn_on_pr.PR_TRIGGERED_ROLES]
return [r for r in missing if r != own_role]
```

`gates/spawn_on_pr.py` line 39 defines
`PR_TRIGGERED_ROLES = ("execution-observation", "conformance-review")`
— exactly the sibling pair issue #2380 reports as deadlocking, and
branches outside that set (e.g. `<subject>/implementation`) fall through
to the unchanged single-role-drop path.

I fetched `origin/issue-2380/implementation` and added a detached
worktree at `/tmp/pr2444-worktree` to run its code without touching my
own branch, then ran the PR's own claimed unit-test command myself:

acceptance: `python3 -m pytest gates/test_merge_gate.py -q` (run from
`/tmp/pr2444-worktree`, checked out at
`origin/issue-2380/implementation`) — result:
```
...........................                                              [100%]
27 passed in 12.20s
```

derived: independent check, not reusing any assertion from the PR's own
test file — ran directly against `_exempt_own_role()` in
`gates/merge_gate.py` in the same worktree via `python3 -c '...'` —
result:
```
execution-observation PR sees missing = []
conformance-review PR sees missing = []
implementation PR (control) sees missing = ['execution-observation', 'conformance-review']
OK: neither sibling blocks on the other; control unaffected
```

acceptance: `python3 -m pytest -q` (full suite, same worktree) — result:
```
15 failed, 2118 passed, 23 xfailed, 2371 errors in 450.23s (0:07:30)
```
canonical: this session's own tool transcript — the errored tests were
all in `on-the-record/hooks/test_deliverable_guard.py` and
`on-the-record/hooks/test_deviation_log_guard.py` (meta-tests of this
plugin's own hooks, branch-name/session-context dependent), not in
`gates/`. This does not match the PR body's claimed
`1005 passed, 8 xfailed`, and I do not treat it as a confirmed
regression: the worktree I ran it from was added `--detach` (no named
`issue-<n>/<role>` branch), which is exactly the precondition several of
those hook tests parse for, and the run also overlapped a period of host
`/tmp` resource contention (see below) that could itself perturb
collection. See Open findings — this is an unresolved discrepancy, not
a confirmed defect in the PR's fix.

canonical: this session's own tool transcript (repeated Bash tool
calls, each returning `ENOSPC: no space left on device, open
'/tmp/claude-1000/.../tasks/*.output'`, both during and after the
full-suite run above, recurring intermittently for the rest of this
session including a `hunt-guard.sh` failure to create
`.git/warrant` on the actual repo filesystem). This persisted across
many retries, cleared briefly once (a `df -h` succeeded, showing 84G
free on `/`, `91%` used), then recurred; Read/Write/Edit tool calls kept
working throughout. This is consistent with host-wide `/tmp` resource
contention shared across concurrently-running sessions on this box, not
something caused by or specific to the PR's fix.

## Why

canonical: `gates/test_merge_gate.py` diff (same sha as above),
specifically
`t_required_verification_missing_exempts_the_observer_pr_that_supplies_it`,
whose pre-fix assertion `missing == ["conformance-review"]` is direct
evidence, in the test suite itself, that #2233's fix still required the
sibling role.

Acceptance criterion 1 (`required_verification_missing()`/`evaluate()`
exempting a PR that is itself one of the two required observer records
from demanding its sibling be pre-merged) is satisfied: the condition
is exactly `own_role in spawn_on_pr.PR_TRIGGERED_ROLES`, verified by
reading the diff directly (What was done, above) rather than by taking
the PR description's word for it.

Acceptance criterion 2 (a regression test spawning two sibling observer
PRs against the same issue, confirming neither is blocked by the
other's absence from `main`) is satisfied by
`t_issue_2380_sibling_observer_prs_neither_blocks_on_the_other` (unit,
directly on `required_verification_missing()`) and
`t_issue_2380_sibling_observer_prs_evaluate_end_to_end` (through
`evaluate()`), both included in the 27-passed run above, and both
re-derived independently in the `derived:` block above rather than
taken on the PR's word.

Acceptance criterion 3 (the manual release-eng-consult override no
longer necessary for a normal same-cycle observer pair) is a structural
consequence of AC1/AC2 holding, not a separate code path: since
`required_verification_missing()` now returns `[]` for either sibling
PR when only the other is open (unmerged) — confirmed directly in the
`derived:` block above — `evaluate()`'s missing-verification-record
reason no longer fires for that pair, which is exactly the condition
that forced the manual override 3x in the session issue #2380 reports.

The operator-frozen constraint (issue #2380 comment, 2026-08-25: must
hold generically for any consumer repo, no added per-spawn overhead, no
new conflict surfaces, no stall/deadlock modes, no consumer-tree
pollution) holds by inspection of the same diff cited in What was done:
the change is confined to branch logic inside the existing pure
function `_exempt_own_role`, adds no new I/O, config, or state file, and
`PR_TRIGGERED_ROLES` is already a repo-generic constant defined
upstream in `gates/spawn_on_pr.py`, not something specific to this
self-hosted checkout.

## What did not work

canonical: this session's own tool transcript (ENOSPC failures, same
occurrence cited in What was done). The full-suite reproduction did
complete once (result pasted in What was done) but with a very
different profile than the PR's claimed `1005 passed, 8 xfailed`,
plausibly a worktree/detached-HEAD and host-resource-contention
artifact rather than a defect in the fix — I could not get a clean
apples-to-apples re-run before repeated ENOSPC failures blocked further
Bash tool calls for the rest of the session.

## Upstream basis

- docs/issue-2380/reports/implementation.md, sha
  `296cc92acc68ccbeb63fa757720137dbaea86256` (PR #2444,
  `issue-2380/implementation` -> `main`)
- gates/merge_gate.py, gates/test_merge_gate.py, gates/spawn_on_pr.py at
  the same sha, diffed against `main` directly

## Open findings

1. canonical: this session's own tool transcript (full-suite result and
   ENOSPC failures, both cited in What was done). The full-suite run
   (`python3 -m pytest -q`) produced `15 failed, 2118 passed, 23
   xfailed, 2371 errors`, not the PR body's claimed `1005 passed, 8
   xfailed`; every errored test was in `on-the-record/hooks/` meta-test
   files unrelated to `gates/merge_gate.py`, consistent with running
   from a detached-HEAD worktree rather than a fix regression, but I
   was not able to get a clean re-run to confirm that explanation before
   the session's Bash tool access became unreliable (`/tmp` ENOSPC).
   resolution path: re-run `python3 -m pytest -q` from a proper
   `issue-2380/implementation`-named checkout (not a detached worktree)
   once the host's `/tmp` contention clears, and confirm the count
   matches the PR's claim; the targeted `gates/test_merge_gate.py -q`
   run (this record's `test:` field, 27 passed) is independently
   confirmed above and covers every assertion the three acceptance
   criteria name, so this is a completeness gap on the broader suite,
   not a doubt about the fix itself.

## Next steps

canonical: the `acceptance:`/`derived:` blocks in What was done (27
passed run and independent `_exempt_own_role()` re-derivation). None —
the acceptance-criteria-level verification (this record's purpose) is
done and passed; the one open item above is a full-suite completeness
check blocked by host infrastructure, not by anything in the fix.
