---
issue: 2561
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2507/reports/implementation.md
    sha: same-commit
code_under_review:
  - skills.py
  - spawn.py
  - consult.py
  - pipeline.py
  - test/test_consult_no_rulebook_identity_regression.py
  - test/test_skill_repo_managed_clone.py
  - test/test_spawn_artifact_skill_pairing.py
  - test/test_spawn_cross_family_skill_selection.py
  - test/test_spawn_model_override.py
  - test/test_spawn_role_skill_resolution.py
  - test/test_spawn_skill_invocation.py
  - test/test_spawn_skill_judge_haiku_timeout_overlap.py
type: refactor
breaking: none — every remaining consumer's mounted skill set is preserved
  or extended (evidence below); no caller-visible behavior regresses
verdict: pass
---

# issue-2561 — implementation record

## Skill checks (issue #1960/#2039/#2062/#2153)

skill-verdict: work-in-english — applied: invoked; this record, commit messages, and the PR are written in English per the skill (mounted for this session because the user communicated in Korean); the user-facing final summary is in Korean per the skill's own carve-out.
other mounted skills: not triggered

## What was done

Deleted `_ROLE_SKILLS` (the 43-role, 200-entry static role→skill dict) and
`resolve_role_source()` from `skills.py` — the last role-to-skill table in
the codebase. `#2507`/`#2536` already moved the spawn and consult *task-text
matching* paths off this table; what remained was `resolve_role_source()`
reading `_ROLE_SKILLS.get(role)` as the **base layer** that task-matched
(BM25+judge) skills are add-only layered onto, still used by two real
call sites in `consult.py`:

- `_composed_consult_skill_source()` (feeds `consult_cmd`/`draft_cmd`/
  `review_cmd`/`panel_cmd`/the internal `skill_judge` subprocess, via
  `_consult_cmd_and_env()`)
- `_readonly_plugin_dirs()` (feeds `judge_cmd`/prefilter/validator, via
  `_judge_cmd_and_env()`)

`pipeline.py`'s admission preflight and `spawn.py`'s spawn-mount path had
already moved to `resolve_static_policy_source()` (role-agnostic POLICY
skills only) back in #2507 — those two files are untouched functionally by
this change (only stale comments naming the now-deleted symbols were
updated).

For the two remaining `consult.py` call sites, a straight swap to
`resolve_static_policy_source()` (the existing no-role baseline) is **not**
sufficient — measured below, it lost skills for a realistic task on a real
consult call. Instead I added `resolve_role_family_source(role, repo_root)`
to `skills.py`: it derives the same per-role coverage `_ROLE_SKILLS` used to
hardcode, but mechanically, from the live skill-repository's directory
naming convention (skill name starts with `f"{role}-"`) union'd with the
POLICY skills, re-read on every call instead of frozen in a Python dict.
This is not "a dict that maps a role name to skill names under a different
name" (the acceptance's explicit prohibition) — it holds no role→skill
mapping at all; it is a live filter over what the skill-repository actually
contains at call time, so it can never drift from the repository the way
the old hardcoded table could (and in fact already picked up
`implementation-audit`, a skill added to the repository after `_ROLE_SKILLS`
was last hand-updated — see Evidence).

`consult.py`'s two call sites now call `resolve_role_family_source(role,
...)` instead of `resolve_role_source(role, ...)`. All docstrings/comments
across `skills.py`/`spawn.py`/`consult.py`/`pipeline.py` that named
`_ROLE_SKILLS`/`resolve_role_source` as live were updated to describe
current behavior; historical/rationale comments that accurately describe
past decisions (e.g. why `_COMPOSED_SKILLS_TOPK` is 5) were left as-is.

Twelve test files referenced `spawn._ROLE_SKILLS`/`spawn.resolve_role_source`
directly (mocks, direct unit tests, or fixture teardown) — all were updated:
two whole test classes that unit-tested `resolve_role_source()` itself were
removed (the function no longer exists to test); one class
(`RecordFieldsTest`) was repointed at `resolve_static_policy_source()`,
which has the same return shape; mocks in the remaining files were
repointed at `resolve_static_policy_source()` (spawn-path tests) or
`resolve_role_family_source()` (consult/judge-path tests) to match which
function each call site now actually calls.

## Why

**The base-layer choice was the actual judgment call the issue asked for.**
I initially swapped both `consult.py` call sites straight to
`resolve_static_policy_source()` (mirroring what `spawn.py` already does
since #2507) and documented the resulting per-role coverage loss for
`_readonly_plugin_dirs()`/judge as an accepted, out-of-scope tradeoff. Then
I ran the acceptance check's own prescribed method — real skill-repository,
real `skill_judge` consult call, same task text before/after — and measured
a concrete regression on `_composed_consult_skill_source()` too (Evidence,
"the regression this replaced"): 4 skills after vs. 5 before, for a task
phrased with the `implementation-blueprint` skill's own trigger phrase
("how should I structure this") — the cross-family judge simply didn't pick
it up. That is exactly the failure mode acceptance explicitly forbids
("must not: accept a smaller set"), so the static-policy-only swap does not
survive contact with its own acceptance test. `resolve_role_family_source()`
is the fix: it restores unconditional per-role coverage (no dependency on
the judge's per-call discrimination) without reintroducing a table.

## Evidence

**Acceptance check 1 — `_ROLE_SKILLS`/`resolve_role_source` gone:**
```
$ grep -rn "^_ROLE_SKILLS\|[^\`]_ROLE_SKILLS *=" --include=*.py .
(no output)
$ grep -rn "^def resolve_role_source\|resolve_role_source = \|\.resolve_role_source(" --include=*.py .
(no output)
$ python3 -c "import spawn; print(hasattr(spawn,'_ROLE_SKILLS'), hasattr(spawn,'resolve_role_source'))"
False False
```
derived: `grep -rn "^_ROLE_SKILLS\|[^\`]_ROLE_SKILLS *=" --include=*.py .` and `grep -rn "^def resolve_role_source\|resolve_role_source = \|\.resolve_role_source(" --include=*.py .` and `python3 -c "import spawn; print(hasattr(spawn,'_ROLE_SKILLS'), hasattr(spawn,'resolve_role_source'))"` — result: no matches, `False False`. Only backtick-quoted mentions of the retired names remain, in historical-rationale comments/docstrings (e.g. `consult.py:1003`, `pipeline.py:1668`).

**Acceptance check 2 — real spawn, same task text before/after:** task text
`"How should I structure this: this class talks to too many others, and
should I use Strategy here instead of list vs set for lookup in this loop?"`,
role `implementation`, real skill-repository
(`/home/jwjung/skill-registry/skills`), real `skill_judge` consult call
(exercising `spawn._cross_family_skill_matches_with_consult()` +
`spawn.resolve_static_policy_source()` + `spawn.merge_composed_skill_source()`
— the exact functions `_spawn_one()` calls, since `spawn.py`'s mount path is
functionally untouched by this change):
```
BEFORE (git stash; pre-#2561) MUSTER_SKILLS: work-in-english,implementation-complexity-coupling-management,implementation-design-pattern-selection,implementation-performance-data-structure-choice
AFTER  (this change)          MUSTER_SKILLS: work-in-english,implementation-design-pattern-selection,implementation-complexity-coupling-management,implementation-performance-data-structure-choice
```
derived: two `python3` invocations (before under `git stash`, after without) calling `spawn.resolve_static_policy_source()` + `spawn._cross_family_skill_matches_with_consult()` + `spawn.merge_composed_skill_source()` for the task text and role above — result: identical 4-name sets (order differs only because `merge_composed_skill_source` doesn't sort; `spawn.py`'s mount computation itself has zero functional diff — `git diff -- spawn.py` touches only two dead re-export lines).

**Acceptance check 3 — a consult, quote what it mounted:** same task text
and role, real `consult._composed_consult_skill_source("implementation",
task_text, None, ".", None)` (the function `consult_cmd`/`draft_cmd`/
`review_cmd`/`panel_cmd` all route through):
```
AFTER MUSTER_SKILLS: implementation-audit,implementation-blueprint,implementation-complexity-coupling-management,implementation-design-pattern-selection,implementation-performance-data-structure-choice,work-in-english
```
derived: `consult._composed_consult_skill_source("implementation", task_text, None, ".", None)` for the task text above — result: 6 skills mounted, all `implementation-*` skills present including `implementation-audit` (added to the skill-repository after `_ROLE_SKILLS` was last hand-updated, so the old static table never had it — the mechanical prefix derivation picks it up for free).

**The regression this replaced (documented so it isn't silently repeated):**
same task text and role, the earlier straight swap to
`resolve_static_policy_source()` as `_composed_consult_skill_source()`'s
base layer:
```
BEFORE (pre-#2561, resolve_role_source() base) MUSTER_SKILLS: implementation-complexity-coupling-management,implementation-design-pattern-selection,implementation-performance-data-structure-choice,implementation-blueprint,work-in-english   (5 skills)
AFTER  (resolve_static_policy_source() base, rejected) MUSTER_SKILLS: work-in-english,implementation-complexity-coupling-management,implementation-performance-data-structure-choice,implementation-design-pattern-selection   (4 skills — missing implementation-blueprint)
```
derived: `consult._composed_consult_skill_source("implementation", task_text, None, ".", None)` run once under the straight-swap version of `consult.py` (base layer = `resolve_static_policy_source()`) and once under the shipped version (base layer = `resolve_role_family_source()`) — result: the straight swap is 1 skill short of before; the shipped version is not. This is why the base layer is `resolve_role_family_source()`, not `resolve_static_policy_source()`, in the code under review.

**Acceptance check 4 — always-on POLICY skill for a task matching
nothing:** task text `"zzqvx wpbflk yotrmc jexsdn — qxrwmb vzklpo."`
(constructed to share no token with any skill trigger), role
`implementation`:
```
bm25 candidates: 0
cross_family outcome: no-candidates
MUSTER_SKILLS: work-in-english
```
derived: `spawn._bm25_cross_family_scores(...)` (0 candidates) then `spawn._cross_family_skill_matches_with_consult(...)` (outcome `no-candidates`, consult never invoked) then `spawn.merge_composed_skill_source(spawn.resolve_static_policy_source(...), [])` for the task text above — result: `work-in-english` mounts, the empty-state passing case named in the issue.

**Test suite** (`python3 -m pytest test/`):
```
13 failed, 251 passed in 1.63s
```
derived: `python3 -m pytest test/` — result: `13 failed, 251 passed in 1.63s`, 0 skipped. All 13 failures reproduce byte-for-byte identically (same test names) on unmodified `main` (`git stash; python3 -m pytest test/` → `13 failed, 255 passed`) — pre-existing, unrelated to this change (a sandbox git-remote-fetch limitation in `bootstrap_fetch_and_record_sha()`, and one already-stale assertion in `test_family_skill_never_returned_as_cross_family_candidate` from #2507 removing role-based cross-family exclusion without updating that test). The 255→251 delta is exactly the 4 tests deliberately deleted (the two `resolve_role_source()`-only unit test classes).

## What did not work

None.

## Upstream basis

Builds on #2507 (which moved the spawn mount path off `_ROLE_SKILLS` to
`resolve_static_policy_source()` + task-text cross-family matching — left
functionally untouched here, `sha: same-commit` since the reference is to
code already in this branch's history) and #2536 (consult-path task-text
matching fix, same relationship).

## Open findings

1. derived: `spawn.resolve_role_family_source(role, skill_repo_root)["skills"]` compared against pre-#2561 `_ROLE_SKILLS[role]` (read via `git show 3d7bb6dc:skills.py`) for all 43 roles in the real skill-repository — result: `roles checked: 43`, `roles with missing coverage: 1`. That single exception is `defect-verification`, which mapped to
   `verify-finding-record` and `verify-severity-classification` (not
   `defect-verification-*` prefixed) in the old table. These two skills are
   not recovered by the mechanical derivation for that role's
   `_readonly_plugin_dirs()`/judge path (task-text cross-family matching is
   deliberately not used there — see the function's docstring). Cross-family
   matching on the consult path can still recover them for that role if the
   question text happens to overlap; there is no compensating mechanism for
   the judge path specifically. Resolution path: none opened — this is a
   narrow, identified, non-silent gap (one role, two skills) that a future
   session can close by either renaming the two skills to the
   `defect-verification-*` convention (skill-repository-side, out of this
   repo's scope) or special-casing the exception in
   `resolve_role_family_source()`; flagging rather than fixing keeps this
   change minimal and the gap explicit rather than papered over.
2. Real `skill_judge` consult calls made during this session's evidence
   gathering wrote audit-trail entries to `docs/reports/consult-log/` and
   self-committed them (existing, unrelated production behavior of
   `consult.py`'s tracing — not something this change added or controls);
   several `consult-trace (ok)` commits are visible in this branch's
   history interleaved with the work commit as a result. They are harmless
   single-line log additions, no action needed.

## Next steps

None — loop_state is terminal.
