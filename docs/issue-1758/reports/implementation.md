---
code_under_review:
  - spawn.py
  - test/test_spawn_role_skill_resolution.py
type: feature
breaking: false
verdict: unverifiable
loop_state: landed
---

## What was done

canonical: spawn.py (this branch's working tree, as edited this turn)

Implemented the approved phase-1 proposal
(docs/issue-1758/proposals/role-skill-resolution.md, approved via
APPROVE issue-1758/implementation) in spawn.py and a new test file:

- `_role_source_allowlist(root)`: reads
  docs/specs/role-source-allowlist.json under root; `{}` if absent.
- `resolve_role_source(role, root, repo_root)`: unmapped role returns
  rulebook source with empty skill_dirs/skills/skill_sha; mapped role
  resolves named skills via #1742's `resolved_skill_dirs()`, then
  `sys.exit()`s (before workspace/branch mutation) if any resolved
  skill dir contains `hooks/`.
- `_spawn_one()`: calls `resolve_role_source()` at the point `--skills`
  already resolves. A mapped role sets `plugins = []` (skips
  `plugin_dirs()`/rulebook `checkout_version()`); its skill dirs merge
  additively into the `--plugin-dir` list `--skills` already builds.
  Unmapped-role `plugins`/`skill_dirs` construction is untouched.
- `_role_source_roster_fields(role_source, rulebook_sha)`: wired into
  both roster-entry sites; `resolution_source` always present,
  `resolution_rulebook_sha` (unmapped) or `resolution_skills`/
  `resolution_skill_sha` (mapped) alongside it.
- test/test_spawn_role_skill_resolution.py (new): allowlist-helper
  tests, mapped-role resolution, two refusal cases (unknown skill name,
  skill dir with `hooks/`), mount-layout assertions (no rulebook
  plugin dir for a mapped role; byte-identical spawn_cmd() argv/env for
  an unmapped role), `_spawn_one()`-level refusal-before-workspace
  cases with stubbed `issue_workspace`/`checkout_issue_branch`, and
  roster record-fields shape for mapped/unmapped/empty-state.

canonical: this turn's own pytest run below

derived:
```
$ python3 -m pytest test/test_spawn_role_skill_resolution.py -q
14 passed in 0.83s
```

canonical: this turn's own pytest run below (the #1742 sibling suite)

derived:
```
$ python3 -m pytest test/test_spawn_skills_mount.py -q
11 passed in 0.84s
```

Test-tier contract (issue #1518): .on-the-record/test-tiers.json's fast
tier is `python3 -m pytest -q -m "not slow"`.

canonical: this turn's own pytest run below

derived:
```
$ timeout 300 python3 -m pytest -q -m "not slow"
2 failed, 2323 passed, 18 xfailed, 3 xpassed in 35.60s
FAILED tests/test_gh_quota_guard.py::test_sweep_call_budget
FAILED tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts
```

canonical: this turn's own `git stash`/pytest/`git stash pop` run below,
against the unmodified tree

The same two tests fail identically with this change's diff stashed
out:

derived:
```
$ git stash && python3 -m pytest -q tests/test_gh_quota_guard.py::test_sweep_call_budget "tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts"; git stash pop
AssertionError: 407 gh calls for 400 subjects: [...]
AssertionError: 1 != 0
```

They pre-date this write set.

## Why

basis: docs/issue-1758/proposals/role-skill-resolution.md (approved)

## What did not work

None — the approach in the approved proposal implemented without
detours.

## Open findings

None.

## Doc placement

No env var, config key, new dependency, migration, or setup step was
introduced (docs/specs/role-source-allowlist.json is a data file the
mechanism reads if present; per the proposal's Out of scope, this issue
ships the mechanism only, not the file). No public signature/wire
format changed for an existing caller. Nothing required doctrine-ladder
placement.

## Rationale for deviations

canonical: docs/issue-1758/proposals/role-skill-resolution.md's plan
section (5 numbered items), compared against code_under_review above

The delivered write set follows that section's five numbered items —
no scope-exceeded stop, no alternative swap.
