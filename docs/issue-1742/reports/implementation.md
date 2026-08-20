---
code_under_review:
  - spawn.py
  - test/test_spawn_skills_mount.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

canonical: spawn.py and test/test_spawn_skills_mount.py, commit 3f77c122
on this branch (diff against ffcfa599)

Implemented `spawn.py --skills a,b,c` per the approved phase-1 proposal
(docs/issue-1742/proposals/skills-mount.md, approved via APPROVE
issue-1742/implementation):

- `_skill_repo_root()`: resolves the skill-repository checkout via
  `MUSTER_SKILL_REPO` env, else `$TOKENMAXXXER_RULEBOOKS/skill-repository`
  (spawn.py, mirrors `_core_candidates()`).
- `resolved_skill_dirs(skills_csv, repo_root)`: parses the comma-separated
  name list, resolves each to `<repo_root>/<name>`, and `sys.exit()`s
  (fail-closed, listing available names) on any unknown name or a missing
  repo root — called from the top of `_spawn_one()`, before any
  workspace/branch mutation.
- `skill_repo_sha(repo_root)`: `git rev-parse --short=7 HEAD`, same shape
  as `rulebook_version()`.
- `spawn_cmd(...)` gained two optional trailing params, `skill_dirs` and
  `skill_repo_sha_value`, following the `resolved_role_model(cli_model=None)`
  precedent — falsy/`None` leaves argv/env construction unchanged
  line-for-line; when present, appends one `--plugin-dir` per skill dir
  after the existing rulebook + core dirs and sets `MUSTER_SKILLS` /
  `MUSTER_SKILL_REPO_SHA` in the env dict.
- `--skills` added to the shared argparse parser (`main()`), threaded
  through `_spawn_one(..., skills=a.skills)`.
- Requirement 3 (record fields): `skills` + `skills_sha` added to both
  `roster_register(...)` call sites (the fork-child early stub and the
  post-`Popen()` registration) only when `--skills` is used — omitted
  keys otherwise, so the no-flag JSON shape is unchanged. The co-injected
  `task` string gets one appended paragraph naming the skill list + sha,
  appended after the existing paragraph so the no-flag `task` string
  stays byte-identical.
- `test/test_spawn_skills_mount.py` (new; canonical: test run below):
  byte-identical no-flag `spawn_cmd()` argv+env diff, valid `--skills
  a,b` mount (plugin-dir ordering + env fields), unknown-name
  fail-closed via `_spawn_one()` with `issue_workspace()`/
  `checkout_issue_branch()` stubbed to prove neither is called, and
  record-fields coverage for the roster dict shape / task string /
  `skill_repo_sha()` helper.

canonical: spawn.py commit 3f77c122, `resolved_skill_dirs()`

No managed-clone bootstrap was added — when no local skill-repository
checkout resolves, `--skills` fails closed via `resolved_skill_dirs()`'s
`sys.exit(...)`, per the proposal's Rationale.

## Why

canonical: docs/issue-1742/proposals/skills-mount.md ## Rationale

Per the approved proposal's Rationale: reuse the two in-repo proven
patterns the issue names (rulebook `--plugin-dir` mount shape,
`resolved_role_model(cli_model=None)` optional-trailing-param
precedence) — no new external mechanism, no managed-clone bootstrap for
skill-repository.

## Upstream

basis: docs/issue-1742/proposals/skills-mount.md (approved)

## Test run

derived: `python3 -m pytest test/test_spawn_skills_mount.py -v`
```
11 passed in 0.86s
```

canonical: `python3 -m pytest -q -m "not slow" test/test_spawn_model_override.py test/test_spawn_skills_mount.py` — executed live this session, output below
acceptance: python3 -m pytest -q -m "not slow" test/test_spawn_model_override.py test/test_spawn_skills_mount.py — result: pass, no regression alongside the new tests
```
17 passed in 0.81s
```

## What did not work

None.

## Open findings

None.

## Accumulation

No new accumulation beyond what the proposal's own `## Accumulation`
section already covers (two roster-register dict literals, two new
keys each, bounded per the proposal's stated non-pre-emption rationale).
