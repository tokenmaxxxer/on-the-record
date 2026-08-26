# issue-2561 — execution-observation current-state survey

## Subject

PR #2564 (branch `issue-2561/implementation`, "remove `_ROLE_SKILLS` and
`resolve_role_source`, the last role-to-skill table").

acceptance: `gh pr view 2564 --json state,mergedAt` — result:
```
{"state":"OPEN","mergedAt":null}
```
acceptance: `gh issue view 2561 --json state,closed` — result:
```
{"closed":false,"state":"OPEN"}
```
canonical: this session's own turn, `approval-gate.sh`'s PreToolUse refusal
text on an attempted execution-surface write, quoted verbatim: "approval-gate:
neither the PR for issue-2561/execution-observation nor issue #2561 carries
an approval from a listed human approver (jiwonjung94, jjongkwann): no
Approve review on an open PR, and no issue comment that is exactly 'APPROVE
issue-2561/execution-observation'." No `CORE_BUILD_NOW`/`CORE_CHECKPOINT`
env stamp is set — derived: `printenv | grep -E "^CORE_|^CLAUDE_ROLE"` —
result: `CLAUDE_ROLE=execution-observation` only. So the two-session default
applies: this survey + the accompanying proposal are this session's entire
output; the record (`docs/issue-2561/reports/execution-observation.md`,
pre-written skeleton, `loop_state: running`) is phase-2 and waits for the
Approve.

## What the implementation PR claims (from its own record)

`docs/issue-2561/reports/implementation.md` lands on branch
`issue-2561/implementation`, untracked from this checkout's working tree
(this session sits on `issue-2561/execution-observation`) — read instead
via `gh pr diff 2564` (the diff embeds the new file's full content). It
claims, with its own `derived:`-tagged commands (quoted here for context,
independently re-run in the next section — not relied on as this survey's
own evidence):

1. `_ROLE_SKILLS`/`resolve_role_source` gone (grep + `hasattr`, no matches).
2. Real spawn, same task text before/after: 4-skill set, order differs only
   (spawn's mount path functionally untouched — `git diff -- spawn.py`
   removes only a dead re-export line).
3. Real consult call mounts 6 skills incl. `implementation-audit` (not in
   the old static table).
4. Always-on POLICY skill (`work-in-english`) for a token-disjoint task.
5. `resolve_role_family_source()` (new, table-free, derives per-role
   coverage from the skill-repository's `f"{role}-"` directory-name
   convention) matches/exceeds the old `_ROLE_SKILLS[role]` for 42 of the
   43 roles it checked; the sole gap is `defect-verification` (old table
   mapped it to `verify-finding-record`/`verify-severity-classification`,
   which don't follow the `defect-verification-*` prefix) — logged as an
   Open finding, not silently dropped.
6. `python3 -m pytest test/`: 13 failed, 251 passed; identical 13 failures
   reproduce on unmodified `main` via `git stash`; the 255-to-251 delta
   (derived: 255-251=4) is the 4 tests deliberately deleted (two
   `resolve_role_source()`-only unit test classes).
7. A deviation log entry documents a same-session design pivot: the author
   first tried swapping `consult.py`'s two call sites straight to the
   pre-existing `resolve_static_policy_source()` (role-agnostic POLICY-only
   baseline), measured a real skill-count regression (5 to 4, missing
   `implementation-blueprint`) against the acceptance's own prescribed
   method, and only then wrote `resolve_role_family_source()` instead.

## Independent re-derivation performed this session

Cloned the repo to a scratch worktree outside this session's own tree
(`/tmp/obs2561`, deleted after use) and checked out
`origin/issue-2561/implementation` there — independently of anything the
implementation record cites. This role's own branch,
`issue-2561/execution-observation`, carries no code changes throughout —
canonical: `git status` at session start showed only the untracked
`docs/issue-2561/` skeleton.

**Check 1 — symbols gone**, re-run against the checked-out branch:
acceptance: `grep -rn "^_ROLE_SKILLS\|[^\`]_ROLE_SKILLS *=" --include=*.py .` and `grep -rn "^def resolve_role_source\|resolve_role_source = \|\.resolve_role_source(" --include=*.py .` and `python3 -c "import spawn; print(hasattr(spawn,'_ROLE_SKILLS'), hasattr(spawn,'resolve_role_source'))"` — result:
```
(no grep matches for either pattern)
False False
```

**Check 3 — consult mount**, re-run directly, same task text as the PR
record:
acceptance: `python3 -c "import spawn, consult; print(sorted(consult._composed_consult_skill_source('implementation', TASK, None, '.', None)['skills']))"` — result:
```
implementation-audit,implementation-blueprint,implementation-complexity-coupling-management,implementation-design-pattern-selection,implementation-performance-data-structure-choice,work-in-english
```
Matches the PR's claimed 6-skill set exactly.

**Check 4 — always-on POLICY skill for a token-disjoint task**
(`"zzqvx wpbflk yotrmc jexsdn — qxrwmb vzklpo."`):
acceptance: `python3 -c "..._bm25_cross_family_scores/_cross_family_skill_matches_with_consult/merge_composed_skill_source..."` — result:
```
outcome: no-candidates
MUSTER_SKILLS: work-in-english
```
Matches.

**Check 2 — spawn path, live-judge non-determinism observed**: re-ran the
identical live-judge call twice in a row on the implementation branch —
acceptance: `python3 -c "...resolve_static_policy_source + _cross_family_skill_matches_with_consult + merge_composed_skill_source..."` run twice — result:
```
run1: implementation-complexity-coupling-management,implementation-performance-data-structure-choice,work-in-english
run2: implementation-complexity-coupling-management,implementation-design-pattern-selection,work-in-english
```
Both runs returned 3 skills, each a *different* 3-skill composition, and
neither reproduced the PR record's claimed 4-skill set
(`work-in-english,implementation-complexity-coupling-management,implementation-design-pattern-selection,implementation-performance-data-structure-choice`).
This is judge non-determinism (a real BM25+LLM-judge subprocess call
executes on every invocation), not a code regression: `spawn.py`'s own
diff is a static fact independent of any live call —
canonical: `docs/issue-2561/reports/implementation.md` (untracked from
this checkout, cited via `gh pr diff 2564`) itself states "`git diff --
spawn.py` only removes two dead re-export lines," and this survey's own
read of the same diff (`/tmp/pr2564.diff` lines 632-653, this session's
own fetch) confirms it: the only removed line touching behavior is
`_ROLE_SKILLS = skills._ROLE_SKILLS` (a dead re-export nothing in
`spawn.py`'s mount computation reads), plus one added
`resolve_role_family_source = skills.resolve_role_family_source` re-export
also unused by the mount path. So the spawn path's *code* is provably
unchanged regardless of what any single live judge invocation returns; the
PR's own before/after comparison via one live call each is evidence of the
same order of magnitude, not a byte-reproducible experiment, and its record
text doesn't claim more than that ("order differs only").

**Check 5 — role-family coverage vs. the old table**: pulled `_ROLE_SKILLS`
from `git show 3d7bb6dc:skills.py` (last commit with the table present) and
compared, for all 43 roles in that table, `old_set` against
`set(resolve_role_family_source(role, root)["skills"])` —
acceptance: `python3 -c "<comparison script>"` — result:
```
roles checked: 43
exact/covered (old_set subset of new_set): 42
mismatches: [('defect-verification', ['verify-finding-record', 'verify-severity-classification'])]
```
Matches the PR's Open finding precisely, both in which role and which two
skill names.

acceptance: same script, testing strict set-equality (`new_set == old_set`) instead of subset — result:
```
exact matches: 0
```
Every one of the 42 "covered" roles has extra names in `new_set` beyond
`old_set` (chiefly `work-in-english`, which the new function always unions
in as the POLICY skill, unlike most old table entries) — this is a
superset relationship (never fewer skills than the old table), consistent
with the acceptance's "must not: accept a smaller set," not a
contradiction of it. `skills.py`'s own docstring wording ("43개 역할 중
41개에서 옛 `_ROLE_SKILLS[role]` 과 정확히 같은 커버리지") is loosely
worded for a strict-equality reading (0, not 41) but accurate for the
subset/coverage reading this survey's independent script measured (42) —
a documentation wording nit, not a functional gap.

**Check 6 — test suite, relative comparison in one controlled clone**: ran
the 8 changed test files (`test_consult_no_rulebook_identity_regression.py`,
`test_skill_repo_managed_clone.py`, `test_spawn_artifact_skill_pairing.py`,
`test_spawn_cross_family_skill_selection.py`, `test_spawn_model_override.py`,
`test_spawn_role_skill_resolution.py`, `test_spawn_skill_invocation.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`) at the implementation
commit, then at the immediate pre-#2561 parent commit (`51cf22ea`,
confirmed via a `hasattr` probe — derived:
`python3 -c "import spawn; print(hasattr(spawn,'_ROLE_SKILLS'))"` — result:
`True`, i.e. the table is still present there) in the *same* scratch
clone/environment:

acceptance: `python3 -m pytest -q <the 8 files>` at `8d8f2797` (implementation) — result:
```
12 failed, 58 passed in 1.19s
```
acceptance: same command at `51cf22ea` (pre-#2561) — result:
```
12 failed, 62 passed in 1.20s
```
The 12 failing test names are byte-identical between the two runs (all fail
on the same unrelated cause — a `pipeline.py` branch-checkout helper's `git
fetch` against a remote named `origin` that, in this throwaway scratch
clone, isn't a real fetchable remote: an artifact of the clone, reproduced
identically on both commits, therefore not attributable to this PR's diff).
The passed-count delta between the two runs (derived: 62-58=4) matches the
PR record's claimed 4 deliberately-deleted tests. This scratch clone's
absolute counts (12 failed/58-62 passed) don't match the PR record's own
claimed absolute counts (13 failed/251 passed) because the two sandboxes
have different `origin` remote configurations, so a different subset of
environment-dependent tests fails in each — the full-suite absolute counts
aren't independently reproducible from this session's environment, but the
*relative* claim this check exists to verify (no new failures introduced
by the diff; 4 fewer tests because 4 were deleted) is independently
confirmed above.

## Roles/paths this survey expects the eventual record to touch

`docs/issue-2561/reports/execution-observation.md` only (record already
scaffolded on disk by the spawner) — no code, no other role's files. This
is a read-only verification role; nothing under `src/`, `test/`, or
`docs/issue-2561/reports/implementation*` is this role's to write.

## Open question this phase-1 proposal must decide

Whether the acceptance-relevant claims (checks 1, 3, 4, 5, and the static
`spawn.py`-diff argument for check 2) are reproducible enough to support
a favorable verdict in the eventual record, given that check 2's
live-judge comparison specifically is inherently non-deterministic and was
not independently reproduced with the same 4-skill composition across two
re-runs. The acceptance criteria in the issue are fixed and this survey
re-derived each one directly rather than choosing among competing
verification approaches; the only judgment call is how to characterize
check 2's non-reproducibility in the eventual record, addressed in the
proposal's Rationale.
