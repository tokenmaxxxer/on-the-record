---
code_under_review:
  - spawn.py
  - test/test_skill_repo_managed_clone.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# issue-1789 phase-2 implementation record

## What was done

Delivered the approved phase-1 proposal
(`docs/issue-1789/proposals/managed-clone-skill-repo-fallback.md`,
canonical: docs/issue-1789/proposals/managed-clone-skill-repo-fallback.md):
extended `_skill_repo_root()` (spawn.py) with a third managed-clone
fallback so a mapped-role spawn with neither `MUSTER_SKILL_REPO` nor the
sibling clone set no longer fails closed (canonical: commit 5be121ecbac2d22a11f19269deb8d4336a9ef971,
`spawn.py`).

1. Added `_skill_repo_valid(d)` (spawn.py:5147-5152, canonical:
   commit 5be121ecbac2d22a11f19269deb8d4336a9ef971) — the same
   non-empty-non-dot-subdirectory bar `resolved_skill_dirs()` already
   applies to every `_skill_repo_root()` return value, reused so the
   managed-clone path is validated identically to env/sibling.
2. Added `_skill_repo_managed_root()` (spawn.py:5155-5184, canonical:
   commit 5be121ecbac2d22a11f19269deb8d4336a9ef971) — the five-step
   managed-clone sequence from the proposal (validity check ->
   pull-if-stale-else-reuse -> clone-if-absent -> validity-recheck),
   reusing `_locked_rulebook_dir`, `_run_net`, `_pull_is_fresh`/
   `_mark_pulled`, `CLONE_TIMEOUT`, and the
   `ROOT/"runs"/"rulebooks"/<name>` managed area exactly as
   `core_root()`/`rulebook_checkout()` already do (canonical:
   spawn.py:5422-5464, spawn.py:279-324).
3. `_skill_repo_root()` (spawn.py:5187-5203, canonical: commit
   5be121ecbac2d22a11f19269deb8d4336a9ef971) now falls through to
   `_skill_repo_managed_root()` only after both env and sibling checks
   miss.
4. Updated the fail-closed message in `resolved_skill_dirs()`
   (spawn.py:5215-5217, canonical: commit
   5be121ecbac2d22a11f19269deb8d4336a9ef971) to name the managed-clone
   attempt as a third source. Audited `resolve_role_source()`
   (spawn.py:5388-5402) and every other `sys.exit` site reachable via
   `_skill_repo_root() is None`: `resolved_skill_dirs()` is the only
   such site (canonical: `grep -n "skill-repository 체크아웃을 못" spawn.py`
   — one match, at spawn.py:5215); `resolved_skill_sources()`'s
   per-name "unknown skill" message is a different, unconditional
   fail-closed unrelated to `_skill_repo_root()` returning `None`
   specifically, so it was left unchanged.
5. Updated `_skill_repo_root()`'s docstring to describe the new
   three-source order.

## Rationale for deviations

The proposal's Rationale/What-will-be-done sections describe the
managed clone as returning the repository checkout root directly (the
way `core_root()` returns its checkout root). The live dry-run below
(canonical: this record's own "Live dry-run" section, executed this
turn) showed the real `skill-repository` repo, and the two other
resolvable sources in this environment (`MUSTER_SKILL_REPO` and the
`$TOKENMAXXXER_RULEBOOKS/skill-repository` sibling), all resolve to the
checkout's `skills/` subdirectory, not the checkout root — the root
also holds `docs/`, `scripts/`, `install.sh`, which are not skill
names. `_skill_repo_managed_root()` therefore validates and returns
`d / "skills"`, not `d`, matching what env/sibling already resolve to.
This satisfies proposal requirement 2 ("must yield identical skill
resolution ... as an env-pointed checkout of the same commit") more
precisely than the proposal's literal wording anticipated — returning
`d` itself would have broken every mapped role in the managed-clone
case, since none of the allowlisted skill names exist at the checkout
root. This is a corrected implementation detail discovered while
running the live dry-run below, not a scope change: `spawn.py` and
`test/test_skill_repo_managed_clone.py` remain the only files touched,
and the five-step sequence, resolution order, and fail-closed semantics
are unchanged from the proposal.

## Why

Structural fix per issue #1789 (canonical: `gh issue view 1789`, read
this turn): skill-repository is now public, so mapped-role spawns
without a hand-set `MUSTER_SKILL_REPO` should not fail closed — they
fall back to the same on-the-record-owned managed clone
`core_root()`/`rulebook_checkout()` already use for the
on-the-record/core checkouts.

## Upstream basis

- 9fb3ee8b13c26574a10b7b3c1094b9270c99b183 (phase-1 survey + proposal;
  canonical: `gh pr view 1793 --json state,mergedAt` — state MERGED)
- `docs/issue-1789/proposals/managed-clone-skill-repo-fallback.md`

## Test evidence

`test/test_skill_repo_managed_clone.py` covers all four acceptance-check
cases (fresh managed clone + resolution, fail-closed naming all three
sources, env-set no-invoke, sibling-present no-invoke) — derived:

```
$ python3 -m pytest -q test/test_spawn_role_skill_resolution.py test/test_spawn_skills_mount.py test/test_skill_repo_managed_clone.py
..................................................                       [100%]
50 passed in 1.08s
```
(canonical: pytest run executed this turn, output pasted above verbatim)

Per-case coverage:
- `ManagedCloneFreshTest::test_managed_clone_runs_and_resolves` — env
  scrubbed, sibling absent, managed area fresh: managed clone runs
  (mocked `_run_net`), root resolves to
  `.../runs/rulebooks/skill-repository/skills`.
- `ManagedCloneFreshTest::test_resolve_role_source_reports_skill_repo`
  — same setup, `resolve_role_source()` reports `source=skill-repo`
  with a non-`None` `skill_sha`.
- `ManagedCloneFailClosedTest::test_all_three_sources_unavailable_fails_closed`
  — clone unreachable + no pre-existing managed clone: `_skill_repo_root()`
  is `None`, `resolved_skill_dirs()` raises `SystemExit` whose message
  names `MUSTER_SKILL_REPO`, `TOKENMAXXXER_RULEBOOKS/skill-repository`,
  and "관리 클론" (managed clone).
- `EnvSetNoNetworkTouchTest::test_env_resolves_without_invoking_managed_clone`
  — `MUSTER_SKILL_REPO` set: `_run_net` (the managed-clone helper's git
  entry point) is asserted `not_called()`.
- `SiblingPresentNoNetworkTouchTest::test_sibling_resolves_without_invoking_managed_clone`
  — sibling present: same not-invoked assertion.

No SKIPPED lines appear in the pasted pytest output above.

## Live dry-run (acceptance check 1)

Run with `MUSTER_SKILL_REPO` and `TOKENMAXXXER_RULEBOOKS` both unset (no
env, no sibling), against a fresh managed-clone area
(`runs/rulebooks/skill-repository` removed beforehand), no mocking —
real network clone of `https://github.com/tokenmaxxxer/skill-repository.git`
— derived:

```
$ rm -rf runs/rulebooks/skill-repository runs/rulebooks/skill-repository.lock runs/ttl-markers
$ env -u MUSTER_SKILL_REPO -u TOKENMAXXXER_RULEBOOKS python3 -c "
import spawn
from pathlib import Path
root = spawn._skill_repo_root()
print('skill_repo_root:', root)
print('is_dir:', root.is_dir() if root else None)
rs = spawn.resolve_role_source('implementation', Path('.'), root)
print('source:', rs['source'])
print('skills:', rs['skills'])
print('skill_sha:', rs['skill_sha'])
"
[skill-repo] skill-repository 를 받는 중
skill_repo_root: /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1789-implementation/runs/rulebooks/skill-repository/skills
is_dir: True
source: skill-repo
skills: ['implementation-complexity-coupling-management', 'implementation-design-pattern-selection', 'implementation-performance-data-structure-choice', 'implementation-blueprint']
skill_sha: ad577a4
```
(canonical: command executed this turn, output pasted above verbatim)

`skill_sha` (`ad577a4`) matches this session's own `MUSTER_SKILL_REPO_SHA`
env value (canonical: `env | grep MUSTER_SKILL_REPO_SHA`, read this
turn — `MUSTER_SKILL_REPO_SHA=ad577a4`), confirming the managed clone
resolved to the same commit an env-pointed checkout of
`skill-repository` would.

## What did not work

None.

## Open findings

None.
