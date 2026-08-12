---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
# canonical: python3 -m pytest tests/test_spawn.py -q, executed live this session (see Acceptance section)
verdict: pass
loop_state: landed
---

## Summary of work

canonical: `gh issue view 1042`, executed live this session.

Phase-2 delivery for issue #1042, per the merged proposal
`docs/issue-1042/proposals/for-each-ref-branch-check.md`. Replaced the
`git branch -a --list "issue-{n}/*"` call inside
`spawn.py::require_requirement_linkage` (spawn.py:1052-1053) with
`git for-each-ref "refs/heads/issue-{n}/**" "refs/remotes/*/issue-{n}/**"`,
so a remote-only `issue-N/...` branch (fresh clone, another machine's
spawn) is correctly detected as already-spawned instead of being
misread as never-spawned and retroactively blocked.

Added two regression tests to `tests/test_spawn.py`
(`RequireRequirementLinkageRemoteBranch`):
- `test_remote_branch_only_detected_as_already_spawned` — builds an
  origin+clone git repo pair where the issue branch exists only as a
  remote-tracking ref, asserts `require_requirement_linkage` returns
  without raising.
- `test_no_remote_branch_no_local_falls_through_to_requirement_linkage_check`
  — no issue branch anywhere, asserts it falls through to the
  requirement-linkage check and raises `SystemExit` when that check
  fails.

## Why

R001 (multi-session/multi-machine correctness family, per issue
#1042). The prior `git branch -a --list` glob does not match `-a`'s
`remotes/origin/issue-N/...` display prefix, so a remote-only branch
was invisible to the check — observed live on issue-392 (per issue
#1042 body).

## Upstream / basis

docs/issue-1042/proposals/for-each-ref-branch-check.md

## What did not work

During the before-landing warrant hunt (stance 0, bypassability), the
hunter reproduced a gap in the first cut: `git for-each-ref
"refs/heads/issue-{n}/*"` does not cross `/` the way `git branch
--list`'s glob does, so a nested branch name (e.g.
`issue-1042/a/b/c`) would go undetected and the gate would
retroactively (mis)block an already-spawned issue.

canonical: derived reproduction below, executed live this session.

derived: throwaway repo reproduction, executed live this session
```
$ cd /tmp/ferftest && git checkout -q -b issue-1042/a/b/c
$ git for-each-ref "refs/heads/issue-1042/*"
(no output)
$ git branch --list "issue-1042/*"
* issue-1042/a/b/c
$ git for-each-ref "refs/heads/issue-1042/**"
a8ede98c576c05aa53c01eddceb280fa57c0645f commit	refs/heads/issue-1042/a/b/c
```

Fixed by switching the glob suffix from `*` to `**` in both patterns
in spawn.py:1052-1054 (`refs/heads/issue-{n}/**`,
`refs/remotes/*/issue-{n}/**`).

canonical: `python3 -m pytest tests/test_spawn.py -q`, executed live
this session after the `**` fix (see reproduction command below).

derived: `python3 -m pytest tests/test_spawn.py -q`
```
477 passed in 32.71s
```

## Doc placement

No env var / config key / new dependency / migration / setup step
introduced — nothing to place in a handbook. No library-or-format
choice or public-signature change beyond what the proposal already
recorded — nothing new for docs/issue-1042/decisions/. No benchmark or
investigation numbers produced.

## Hunt cadence

- before-landing: docs/issue-1042/reports/implementation/hunt-for-each-ref-branch-check.md
  (this delivery) — stance 0 (bypassability). Finding recorded there;
  fixed inline, see `## What did not work` above.

## Rationale for deviations

canonical: `git for-each-ref "refs/heads/issue-1042/*"` (executed live
this session, see `## What did not work` above for full output).
The proposal's `## What will be done` specified
`refs/heads/issue-{n}/*` / `refs/remotes/*/issue-{n}/*` (single `*`).
canonical: `git for-each-ref "refs/heads/issue-1042/*"` (executed live
this session, see `## What did not work` above for full output).
The before-landing warrant hunt found that pattern does not match
nested branch names the way the replaced `git branch --list` glob did
— reproduced with the commands above. Landed with `**` instead of `*`
in both patterns — same call site, same shape, same write set
(spawn.py only, no widening).

closed_checks:
- check: before-landing warrant hunt, stance 0 (bypassability) — resolved via `**` fix, re-verified with the reproduction command above
  code_sha: (uncommitted at hunt time; file list in code_under_review above)

## Acceptance

canonical: `python3 -m pytest tests/test_spawn.py -k remote_branch`, executed live this session.

checked: `python3 -m pytest tests/test_spawn.py -k remote_branch` — result: pass

derived:
```
$ python3 -m pytest tests/test_spawn.py -k remote_branch -v
tests/test_spawn.py::RequireRequirementLinkageRemoteBranch::test_no_remote_branch_no_local_falls_through_to_requirement_linkage_check PASSED [ 50%]
tests/test_spawn.py::RequireRequirementLinkageRemoteBranch::test_remote_branch_only_detected_as_already_spawned PASSED [100%]
2 passed
```

derived: `python3 -m pytest tests/test_spawn.py -q`, executed live this
session
```
477 passed in 32.71s
```

## Open findings

None open — the one before-landing hunt finding was resolved inline
(see `## What did not work`, `## Rationale for deviations`) and
re-verified against the fix in this same session via the reproduction
command shown above.
