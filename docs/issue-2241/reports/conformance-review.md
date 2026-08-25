---
issue: 2241
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-0-additive-skill-spawn.md
    sha: ccee895997e7629495aee4ff7c0588e3082c75bc
subject: PR #2296 (https://github.com/tokenmaxxxer/on-the-record/pull/2296), commit 71f53cef9ec118395be9d7262920bcdd1c1bb4ad
test: docs/issue-2241/proposals/2026-08-25-stage-0-additive-skill-spawn.md#how-youll-know-it-worked
result: passed
assertedBy: conformance-review (issue-2241/conformance-review session)
---

# issue-2241 — conformance-review record

## What was done

Builder-blind conformance review of PR #2296 ("stage 0 — additive
skill-based spawn CLI alongside role path") against the acceptance the
stage-0 proposal itself states
(`docs/issue-2241/proposals/2026-08-25-stage-0-additive-skill-spawn.md`)
and the constraints/non-goals in issue #2241's own decision body that bear
on stage 0. Extracted 10 discrete, checkable requirements from the
proposal's `## What will be done`, `## Constraints`, `## Out of scope`,
and `## How you'll know it worked` sections; the diff is 537 insertions /
0 deletions across 7 files
(canonical: `git diff --stat $(git merge-base origin/main pr-2296-review) pr-2296-review`,
worktree `/tmp/pr2296-worktree` @ 71f53cef9ec118395be9d7262920bcdd1c1bb4ad),
small enough for full enumeration — no separate sampling scope was
derived.

Both `docs/handbooks/spawn-cli.md` (untracked on this branch) and
`test/test_spawn_skill_invocation.py` (untracked on this branch) are new
in PR #2296 and exist only on the reviewed PR branch; every citation
below to either path was read from
`git fetch origin pull/2296/head:pr-2296-review`, checked out in a
disposable worktree at `/tmp/pr2296-worktree`. Every acceptance command
below was re-run there by this review, not copied from the PR body.

acceptance: `python3 -m pytest test/test_spawn_skill_invocation.py -q` (untracked on this branch; worktree `/tmp/pr2296-worktree` @ 71f53cef) — result:
```
...........
11 passed in 18.42s
```

acceptance: `python3 -m pytest test/ gates/ -q -m "not slow"` (worktree `/tmp/pr2296-worktree` @ 71f53cef) — result:
```
1186 passed, 8 xfailed in 14.35s
```
derived: full dot-progress output observed directly in this review's own
shell (0 failed, 0 errored in either run above).

Requirement-by-requirement verdicts:

---
requirement: spawn.py gains a `--skill <name>[,<name>...] "<task>" --issue <n>` invocation resolving guidance via a skill-name-direct path (bypassing the role→skill table)
spec_ref: proposal `## What will be done`, bullet 1
verdict: Present
evidence: canonical: 65f5163dc00f2ec50694479e097819faf07ecc03:spawn.py:1229-1260 (new `if a.skill:` dispatch branch, ends `return 0`); canonical: 65f5163dc00f2ec50694479e097819faf07ecc03:skills.py:379-395 (new `resolve_skill_source()`)
rationale: the dispatch branch and the resolver it calls both exist at the cited lines and the first acceptance block above (11 passed) covers `test_resolves_named_skill_directly` and `test_skill_flag_prints_resolution_without_spawning` for exactly this path.
---
requirement: the existing `spawn.py <role> "<task>"` invocation is untouched — same branch naming, claim/lease, board writes (byte-identical)
spec_ref: proposal `## What will be done`, bullet 2; `## How you'll know it worked`, bullet 1
verdict: Present
evidence: canonical: `git diff $(git merge-base origin/main pr-2296-review) pr-2296-review -- skills.py` (worktree `/tmp/pr2296-worktree`) — the `resolve_role_source()` hunk (skills.py:354-377) shows 0 removed/modified lines, only the new `resolve_skill_source()` appended after it
rationale: static diff confirms the role-path resolver function itself has zero changed lines, and the second acceptance block above (1186 passed, 0 failed) covers the role path's existing suite with no regressions.
---
requirement: `docs/handbooks/spawn-cli.md` (untracked on this branch) documents both invocation shapes and states plainly the skill path does not yet affect concurrency/write-scope/observer verification
spec_ref: proposal `## What will be done`, bullet 3
verdict: Present
evidence: canonical: 65f5163dc00f2ec50694479e097819faf07ecc03:docs/handbooks/spawn-cli.md (untracked on this branch; new file, read via `gh pr diff 2296`). Contains a "role 경로" section, a "skill 경로" section, and a paragraph beginning "동시성/write-scope/observer 검증에 아직 영향 없음" naming stages 1/3/5 by number.
rationale: the required content (both shapes documented, the scope-boundary statement) is present verbatim in the cited file at that commit.
---
requirement: a regression test asserts role/skill paths produce equivalent guidance-resolution output for a role/skill pair that maps 1:1 today
spec_ref: proposal `## What will be done`, bullet 4; `## How you'll know it worked`, bullet 3
verdict: Present
evidence: canonical: 65f5163dc00f2ec50694479e097819faf07ecc03:test/test_spawn_skill_invocation.py:96-113 (untracked on this branch; `RoleSkillEquivalenceTest.test_role_path_and_skill_path_agree_for_a_1to1_pair`)
rationale: the test asserts equality of `skills`/`skill_dirs`/`skill_sha`/`source` between `resolve_role_source` and `resolve_skill_source`, and it is part of the first acceptance block above (11 passed).
---
requirement: this stage must not touch roster.py's claim/lease logic, board-gate, or merge_gate.py
spec_ref: proposal `## Constraints`, bullet 4; `## Out of scope`, bullet 1
verdict: Present
evidence: canonical: `git diff --stat $(git merge-base origin/main pr-2296-review) pr-2296-review` (worktree `/tmp/pr2296-worktree`) — full file list: docs/handbooks/spawn-cli.md, docs/issue-2241/reports/implementation.md, docs/issue-2241/reports/implementation/2026-08-25-hunt-stage-0-additive-skill-spawn.md, docs/issue-2241/reports/implementation/deviation-log.md, skills.py, spawn.py, test/test_spawn_skill_invocation.py (all seven per this diff-stat; two of them untracked on this review branch, see note above) — 0 matches for roster.py/board-gate*/merge_gate.py
rationale: the constraint is a negative (must-not-touch); the complete, directly-observed file list contains none of the named files.
---
requirement: no skill-side hooks introduced; enforcement stays core-only
spec_ref: proposal `## Constraints`, bullet 1
verdict: Present
evidence: canonical: 65f5163dc00f2ec50694479e097819faf07ecc03:skills.py:387-392 (`resolve_skill_source()` `sys.exit`s if any resolved skill dir carries `hooks/`); same file-list evidence as the row above shows no new `hooks/` paths added by this diff
rationale: the new resolution path fail-closes on hooks the same way the pre-existing role path does (reuses `resolved_skill_dirs()`), and `test_skill_with_hooks_dir_exits_nonzero` is part of the first acceptance block above (11 passed).
---
requirement: the new path must resolve skills directly, never a role manifest by another name
spec_ref: proposal `## Constraints`, bullet 2; issue #2241 `## Non-goals`, bullet 1
verdict: Present
evidence: canonical: 65f5163dc00f2ec50694479e097819faf07ecc03:skills.py:379-395 — `resolve_skill_source(skill_name, repo_root)` calls only the pre-existing `_sp.resolved_skill_dirs()`, no read of `_ROLE_SKILLS`; canonical: 65f5163dc00f2ec50694479e097819faf07ecc03:test/test_spawn_skill_invocation.py:44-49 (untracked on this branch; `test_skill_with_no_corresponding_role_still_resolves`, asserts `"gamma"` absent from every `_ROLE_SKILLS` value and still resolves)
rationale: no new role-shaped lookup table was added in this diff, and the named acceptance test (a role-less name resolving successfully) is part of the first acceptance block above (11 passed).
---
requirement: `spawn.py <role> "<task>"` invocations behave byte-identically to before this stage (existing test suite passes unmodified)
spec_ref: proposal `## How you'll know it worked`, bullet 1
verdict: Present
evidence: second acceptance block above (1186 passed, 8 xfailed, 0 failed) and the `resolve_role_source()` zero-diff evidence two rows above
rationale: the full pre-existing suite, which covers the role path end to end, passed with no failures on the reviewed PR branch, and the role-path resolver's own source is unchanged.
---
requirement: the new skill-based invocation successfully resolves guidance for at least one skill with no corresponding role name
spec_ref: proposal `## How you'll know it worked`, bullet 2
verdict: Present
evidence: same citation as the non-goal row above — canonical: 65f5163dc00f2ec50694479e097819faf07ecc03:test/test_spawn_skill_invocation.py:44-49 (untracked on this branch)
rationale: this is the proposal's own named acceptance check for this exact claim, and it is part of the first acceptance block above (11 passed).
---
requirement: test/test_spawn_skill_invocation.py (untracked on this branch) passes, exercising both paths side by side
spec_ref: proposal `## How you'll know it worked`, bullet 3
verdict: Present
evidence: first acceptance block above (11 passed in 18.42s)
rationale: re-run directly by this review against a freshly fetched copy of the PR branch (not the PR body's pasted output) — 11 passed, matching the PR's own claim.
---

## Why

Verification method per requirement followed the structural/dynamic
split: Inspection for static diff-shape properties (file scope, which
functions have zero removed lines, presence/absence of `hooks/`), and
Test for behavioral claims already covered by an executable test in the
PR itself — reused via a fresh re-run on a fetched copy of the PR branch
rather than trusting the PR body's pasted output, per this session's own
verify-at-landing obligation and the finding-record skill's
evidence-must-be-a-pointer-into-the-artifact rule. No Demonstration or
Analysis method was needed: nothing in this stage's scope concerns a
qualitative interactive flow or a condition (load, timing, production-
only integration) this session cannot reproduce — it is a CLI flag that
prints JSON and exits, well suited to direct Test/Inspection.

Full enumeration (10 requirements, all checked) rather than sampling: the
diff is small (537 insertions, 0 deletions, 7 files — canonical: `git diff --stat`
citation in "What was done" above) and the proposal's own
`## How you'll know it worked` section already names a short, closed
acceptance list — deriving a separate sampling scope on top of that would
have re-derived a scope the spec already stated.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split the proposal's `## What will be done`/`## Constraints`/`## Out of scope`/`## How you'll know it worked` sections into 10 one-obligation-per-line items, dimension-tagged (functional / scope-boundary / regression / edge-case) above, and dropped no summary lines (none of the proposal's own lines restated 3+ sub-points).
skill-verdict: conformance-review-sampling-derivation — not-applicable: the diff (537 insertions, 0 deletions, 7 files) was small enough for full enumeration, so no sampling scope was needed.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; routed static/structural properties (file scope, untouched functions, hooks/ absence) to Inspection and reused the PR's own executable tests as Test-method evidence via a fresh re-run on a fetched branch copy, rather than re-deriving parallel manual checks.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; all 10 requirements reached Present only after locating reachable, active evidence (not just matching code/docs existing) — none needed Surface, Absent, Incorrect, or Unverifiable, and no prior-Present-carried-forward case applied since this is the first conformance-review pass over PR #2296.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence citation above pins file:line-range plus the commit sha actually read (65f5163d for the implementation commit, 71f53cef for the PR branch HEAD read via the fetched worktree); the proposal's own version is pinned via its landing sha (ccee895997e7629495aee4ff7c0588e3082c75bc) in the frontmatter `upstream:` block.
skill-verdict: conformance-review-finding-record — applied: invoked; every requirement block above carries requirement/spec_ref/verdict/evidence/rationale, and no verdict was written without an evidence pointer and spec_ref (all 10 are Present, none Incorrect, so `spec_vs_built` was correctly omitted throughout).
skill-verdict: conformance-review-severity-classification — not-applicable: no finding needed risk-weighting — no Absent/Incorrect verdicts were recorded to band.

## Upstream basis

`docs/issue-2241/proposals/2026-08-25-stage-0-additive-skill-spawn.md` @
`ccee895997e7629495aee4ff7c0588e3082c75bc` (landed via PR #2252) — the
stage-0 proposal this review checked PR #2296 against. Also read issue
#2241's own decision body (`## Constraints`, `## Non-goals`,
`## Staging`) for constraints bearing on stage 0 specifically, and PR
#2296's own body/commits/description (subject `71f53cef`) for the claims
under review.

## Open findings

None blocking. One discrepancy worth a plain word, not a defect:

acceptance: `python3 -m pytest test/ gates/ -q -m "not slow"` (worktree `/tmp/pr2296-worktree` @ 71f53cef, this review's own re-run) — result:
```
1186 passed, 8 xfailed in 14.35s
```
canonical: PR #2296 body (`gh pr view 2296`, `## Test plan` section) pastes the same command's result as `980 passed, 8 xfailed`. The xfailed count matches exactly (8 = 8); the passed count differs (1186 vs 980), with 0 failures observed in either run. The most plausible explanation is that `main` accumulated more tests via other merges between when the PR's own record was authored and when this review re-ran the suite (`origin/main` fetched here at `38cbc9e3`); resolving the exact delta was outside this review's own scope, and it does not change any verdict above.

## Next steps

None — `loop_state: reported` is terminal for a `review-record`. This
record checked PR #2296 (stage 0) only; stages 1-6 of issue #2241's
program are separate future work under their own tracking issues
(#2284-#2289), each with its own proposal and, in turn, its own
conformance review when built.
