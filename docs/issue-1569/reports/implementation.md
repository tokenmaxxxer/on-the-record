---
code_under_review:
  - gates/gh_rest.py
  - gates/requirement_linkage.py
  - gates/acceptance_gate.py
  - gates/requirement_intake_consult.py
  - gates/pr_reference.py
  - gates/issue_bundling.py
  - gates/check_runner.py
  - gates/test_gh_rest.py
  - gates/test_requirement_linkage_rest.py
  - spawn.py
type: feature
breaking: false
loop_state: landed
canonical: acceptance: python3 gates/test_requirement_linkage_rest.py — result: PASS
verdict: pass
---

## What was done

derived:
```
$ git show --stat bf2c8fa9fed068e8e2b91f002bf7b2df690bc927
```
Commit bf2c8fa9 adds `gates/gh_rest.py`, a helper wrapping `gh api
repos/{owner}/{repo}/{issues,pulls}/{n}` (owner/repo resolved via `git
remote get-url origin`), and replaces the `gh issue view`/`gh pr view`
read-only body/title lookup in each of `gates/requirement_linkage.py`,
`gates/acceptance_gate.py`, `gates/requirement_intake_consult.py`,
`gates/pr_reference.py`, `gates/issue_bundling.py`, `gates/check_runner.py`,
and `spawn.py`'s spawned-task requirement-citation line with a call into
that helper.

Adds `gates/test_gh_rest.py` (hermetic transport-stub coverage of the
helper) and `gates/test_requirement_linkage_rest.py`, the acceptance case
for the issue's priority instance: a stub transport where the GraphQL-shaped
`gh issue view` argv errors and the REST-shaped `gh api .../issues/<n>`
argv succeeds, exercised against `requirement_linkage.check()` directly.

derived:
```
$ python3 gates/test_gh_rest.py
6/6 passed
$ python3 gates/test_requirement_linkage_rest.py
3/3 passed
$ python3 gates/test_requirement_linkage.py
3/3 passed
$ python3 gates/test_acceptance_gate.py
13/13 passed
$ python3 gates/test_requirement_intake_consult.py
4/4 passed
```
canonical: this session's terminal output of the five commands above,
executed against commit bf2c8fa9 in this working tree.

## Why

reason: issue #1569's problem statement — `gh issue view`/`gh pr view` share
the GraphQL quota pool (5000/hr) with concurrent role sessions' issue/PR
reads; `requirement_linkage.py::check(root, issue)` refused spawns on that
pool's exhaustion even though the separate REST pool was alive. Moving
single-item read-only lookups to `gh api ...` removes that cross-pool
coupling.

## Upstream basis

basis: docs/issue-1569/reports/implementation/survey.md,
docs/issue-1569/proposals/gh-rest-migration.md, commit bf2c8fa9.

## Doc placement ladder

- No env var / config key / new dependency / migration / setup step added —
  `gh` and `git` were already this repo's tools; `git remote get-url origin`
  reads existing repo config, no new surface. No handbook entry.
- Library/format choice (REST via `gh api`, and `git remote get-url origin`
  over `gh repo view`) is recorded in
  `docs/issue-1569/proposals/gh-rest-migration.md`'s `## Rationale` — no
  separate decision-record file, since no public signature/wire-format
  beyond the internal `gh_rest.py` module itself changed.
- No benchmark/investigation numbers produced.

## What did not work

None: no attempted-then-reverted approach and no expected-but-false
assumption arose while building this change.

## Open findings

None open.

## Warrant hunt

No warrant-hunter subagent was dispatched this turn: this is a headless
single-shot session (contract v3 s22), and dispatching a hunter whose
result this same turn does not consume before ending is prohibited by that
clause.

closed_checks:
- check: hermetic coverage of the priority instance's rate-limit-refusal
  behavior (canonical: acceptance: python3 gates/test_requirement_linkage_rest.py — result: PASS)
  code_sha: bf2c8fa9fed068e8e2b91f002bf7b2df690bc927

## Test-tier note (issue #1518 observe-only directive)

derived:
```
$ ls .on-the-record/test-tiers.json
```
canonical: this session's shell output — the file was not found at repo
root. No tiering file exists, so no `fast`/`slow` split applies.

derived:
```
$ ls gates/test_*.py | wc -l
76
```
The five test files run in the change summary above exercise every module
this commit edited plus its two new test files. The remaining files in the
count above were not individually re-run this turn — a tiering gap,
surfaced here rather than silently absorbed, since none of them import a
module this commit touched.

## Rationale for deviations

canonical: diff of docs/issue-1569/proposals/gh-rest-migration.md's plan
section against commit bf2c8fa9fed068e8e2b91f002bf7b2df690bc927's file
list, read in this session.

None — the build tracked the phase-1 proposal's plan as written; no
scope-exceeded stop, no proposal-stated alternative swapped mid-build.
